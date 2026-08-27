"""Refresh the dynamic values in the profile SVG templates.

Adapted from Andrew6rant/Andrew6rant's today.py.  The SVG artwork and layout
stay in the templates; this script only replaces text in elements with stable
IDs and refreshes the per-repository LOC cache.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any

import requests
from lxml import etree


ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
USER_NAME = os.environ.get("USER_NAME", "proffitteoy")
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"
CACHE_PATH = Path("cache") / f"{hashlib.sha256(USER_NAME.encode()).hexdigest()}.txt"
SVG_PATHS = (Path("light_mode.svg"), Path("dark_mode.svg"))


def graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    for attempt in range(5):
        try:
            response = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=HEADERS,
                timeout=60,
            )
            if response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
                payload = response.json()
                if payload.get("errors"):
                    raise RuntimeError(payload["errors"])
                return payload["data"]
        except requests.RequestException:
            if attempt == 4:
                raise
        if attempt == 4:
            response.raise_for_status()
        time.sleep(2**attempt)
    raise RuntimeError("GitHub GraphQL request failed")


def account_data() -> tuple[str, int]:
    query = """
    query($login: String!) {
      user(login: $login) {
        id
        followers { totalCount }
      }
    }
    """
    user = graphql(query, {"login": USER_NAME})["user"]
    return user["id"], int(user["followers"]["totalCount"])


def repositories(affiliations: list[str], owner_id: str) -> list[dict[str, Any]]:
    query = """
    query($login: String!, $ownerId: ID!, $affiliations: [RepositoryAffiliation!], $cursor: String) {
      user(login: $login) {
        repositories(
          first: 100
          after: $cursor
          ownerAffiliations: $affiliations
          orderBy: {field: NAME, direction: ASC}
        ) {
          nodes {
            nameWithOwner
            stargazerCount
            defaultBranchRef {
              target {
                ... on Commit { history(author: {id: $ownerId}) { totalCount } }
              }
            }
          }
          pageInfo { hasNextPage endCursor }
        }
      }
    }
    """
    result: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        connection = graphql(
            query,
            {
                "login": USER_NAME,
                "ownerId": owner_id,
                "affiliations": affiliations,
                "cursor": cursor,
            },
        )["user"]["repositories"]
        result.extend(connection["nodes"])
        if not connection["pageInfo"]["hasNextPage"]:
            return result
        cursor = connection["pageInfo"]["endCursor"]


def repository_loc(owner_id: str, name_with_owner: str) -> tuple[int, int, int]:
    owner, name = name_with_owner.split("/", 1)
    query = """
    query($owner: String!, $name: String!, $authorId: ID!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $cursor, author: {id: $authorId}) {
                nodes {
                  additions
                  deletions
                  author { user { id } }
                }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
      }
    }
    """
    additions = deletions = commits = 0
    cursor: str | None = None
    while True:
        repository = graphql(
            query,
            {"owner": owner, "name": name, "authorId": owner_id, "cursor": cursor},
        )["repository"]
        branch = repository and repository["defaultBranchRef"]
        if not branch:
            return additions, deletions, commits
        history = branch["target"]["history"]
        for commit in history["nodes"]:
            author = commit.get("author") or {}
            user = author.get("user") or {}
            if user.get("id") == owner_id:
                commits += 1
                additions += int(commit["additions"])
                deletions += int(commit["deletions"])
        if not history["pageInfo"]["hasNextPage"]:
            return additions, deletions, commits
        cursor = history["pageInfo"]["endCursor"]


def load_cache() -> dict[str, tuple[int, int, int, int]]:
    cache: dict[str, tuple[int, int, int, int]] = {}
    if not CACHE_PATH.exists():
        return cache
    for line in CACHE_PATH.read_text(encoding="utf-8").splitlines():
        try:
            identifier, total, commits, additions, deletions = line.split("\t")
            if "/" in identifier:
                identifier = hashlib.sha256(identifier.encode()).hexdigest()
            cache[identifier] = (
                int(total),
                int(commits),
                int(additions),
                int(deletions),
            )
        except ValueError:
            continue
    return cache


def write_cache(cache: dict[str, tuple[int, int, int, int]]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        "".join(
            f"{name}\t{total}\t{commits}\t{additions}\t{deletions}\n"
            for name, (total, commits, additions, deletions) in sorted(cache.items())
        ),
        encoding="utf-8",
    )


def refresh_cache(
    owner_id: str, repo_nodes: list[dict[str, Any]]
) -> tuple[int, int, int]:
    old_cache = load_cache()
    new_cache: dict[str, tuple[int, int, int, int]] = {}
    for repository in repo_nodes:
        name = repository["nameWithOwner"]
        identifier = hashlib.sha256(name.encode()).hexdigest()
        branch = repository.get("defaultBranchRef")
        total = int(branch["target"]["history"]["totalCount"]) if branch else 0
        cached = old_cache.get(identifier)
        if cached and cached[0] == total:
            new_cache[identifier] = cached
            continue
        print(f"Refreshing LOC cache: {name}", flush=True)
        additions, deletions, commits = repository_loc(owner_id, name)
        new_cache[identifier] = (total, commits, additions, deletions)
        write_cache(new_cache)

    write_cache(new_cache)
    commits = sum(item[1] for item in new_cache.values())
    additions = sum(item[2] for item in new_cache.values())
    deletions = sum(item[3] for item in new_cache.values())
    return commits, additions, deletions


def dotted_value(root: etree._Element, element_id: str, value: int | str, width: int) -> None:
    text = f"{value:,}" if isinstance(value, int) else str(value)
    value_node = root.find(f".//*[@id='{element_id}']")
    dots_node = root.find(f".//*[@id='{element_id}_dots']")
    if value_node is None or dots_node is None:
        raise RuntimeError(f"Missing SVG nodes for {element_id}")
    value_node.text = text
    remaining = max(2, width - len(text))
    dots_node.text = " " + "." * remaining + " "


def plain_value(root: etree._Element, element_id: str, value: int | str) -> None:
    node = root.find(f".//*[@id='{element_id}']")
    if node is None:
        raise RuntimeError(f"Missing SVG node for {element_id}")
    node.text = f"{value:,}" if isinstance(value, int) else str(value)


def update_svg(path: Path, values: dict[str, int | str]) -> None:
    tree = etree.parse(str(path))
    root = tree.getroot()
    widths = {
        "repo_data": 28,
        "contrib_data": 21,
        "star_data": 28,
        "commit_data": 26,
        "follower_data": 24,
        "loc_data": 12,
    }
    for element_id, width in widths.items():
        dotted_value(root, element_id, values[element_id], width)
    plain_value(root, "loc_add", values["loc_add"])
    plain_value(root, "loc_del", values["loc_del"])
    tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=True)


def main() -> None:
    owner_id, followers = account_data()
    owned = repositories(["OWNER"], owner_id)
    all_accessible = repositories(
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"], owner_id
    )
    commits, additions, deletions = refresh_cache(owner_id, all_accessible)
    values: dict[str, int | str] = {
        "repo_data": len(owned),
        "contrib_data": len(all_accessible),
        "star_data": sum(int(repo["stargazerCount"]) for repo in owned),
        "commit_data": commits,
        "follower_data": followers,
        "loc_data": additions - deletions,
        "loc_add": additions,
        "loc_del": deletions,
    }
    for svg_path in SVG_PATHS:
        update_svg(svg_path, values)
    print(f"Updated {', '.join(map(str, SVG_PATHS))} for {USER_NAME}")


if __name__ == "__main__":
    main()
