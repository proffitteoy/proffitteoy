"""Incrementally refresh GitHub metrics in the profile SVG templates.

Run ``initialize_profile.py`` once to build the v2 cache.  Normal scheduled
runs execute this file and fetch only commits newer than each repository's
cached author-commit OID.
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
CACHE_VERSION = "# profile-cache-v2"
CACHE_PATH = Path("cache") / f"{hashlib.sha256(USER_NAME.encode()).hexdigest()}.txt"
SVG_PATHS = (Path("light_mode.svg"), Path("dark_mode.svg"))

# author_total, displayed_commits, additions, deletions, newest_author_commit_oid
CacheEntry = tuple[int, int, int, int, str]


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
                ... on Commit {
                  history(first: 1, author: {id: $ownerId}) {
                    totalCount
                    nodes { oid }
                  }
                }
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


def repository_state(repository: dict[str, Any]) -> tuple[int, str]:
    branch = repository.get("defaultBranchRef")
    if not branch:
        return 0, "-"
    history = branch["target"]["history"]
    nodes = history["nodes"]
    return int(history["totalCount"]), nodes[0]["oid"] if nodes else "-"


def repository_history_page(
    owner_id: str, name_with_owner: str, cursor: str | None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    owner, name = name_with_owner.split("/", 1)
    query = """
    query($owner: String!, $name: String!, $authorId: ID!, $cursor: String) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $cursor, author: {id: $authorId}) {
                nodes { oid additions deletions }
                pageInfo { hasNextPage endCursor }
              }
            }
          }
        }
      }
    }
    """
    repository = graphql(
        query,
        {"owner": owner, "name": name, "authorId": owner_id, "cursor": cursor},
    )["repository"]
    branch = repository and repository["defaultBranchRef"]
    if not branch:
        return [], {"hasNextPage": False, "endCursor": None}
    history = branch["target"]["history"]
    return history["nodes"], history["pageInfo"]


def scan_repository(owner_id: str, name_with_owner: str) -> CacheEntry:
    additions = deletions = commits = 0
    newest_oid = "-"
    cursor: str | None = None
    while True:
        nodes, page_info = repository_history_page(owner_id, name_with_owner, cursor)
        if newest_oid == "-" and nodes:
            newest_oid = nodes[0]["oid"]
        commits += len(nodes)
        additions += sum(int(commit["additions"]) for commit in nodes)
        deletions += sum(int(commit["deletions"]) for commit in nodes)
        if not page_info["hasNextPage"]:
            return commits, commits, additions, deletions, newest_oid
        cursor = page_info["endCursor"]


def scan_new_commits(
    owner_id: str, name_with_owner: str, previous_oid: str
) -> tuple[int, int, int, str, bool]:
    additions = deletions = commits = 0
    newest_oid = "-"
    cursor: str | None = None
    while True:
        nodes, page_info = repository_history_page(owner_id, name_with_owner, cursor)
        if newest_oid == "-" and nodes:
            newest_oid = nodes[0]["oid"]
        for commit in nodes:
            if commit["oid"] == previous_oid:
                return commits, additions, deletions, newest_oid, True
            commits += 1
            additions += int(commit["additions"])
            deletions += int(commit["deletions"])
        if not page_info["hasNextPage"]:
            return commits, additions, deletions, newest_oid, previous_oid == "-"
        cursor = page_info["endCursor"]


def load_cache() -> tuple[bool, dict[str, CacheEntry]]:
    cache: dict[str, CacheEntry] = {}
    if not CACHE_PATH.exists():
        return False, cache
    lines = CACHE_PATH.read_text(encoding="utf-8").splitlines()
    versioned = bool(lines and lines[0] == CACHE_VERSION)
    for line in lines[1:] if versioned else lines:
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) not in {5, 6}:
            continue
        identifier, total, commits, additions, deletions = fields[:5]
        newest_oid = fields[5] if len(fields) == 6 else "-"
        if "/" in identifier:
            identifier = hashlib.sha256(identifier.encode()).hexdigest()
        cache[identifier] = (
            int(total),
            int(commits),
            int(additions),
            int(deletions),
            newest_oid,
        )
    return versioned, cache


def write_cache(cache: dict[str, CacheEntry]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(
        f"{identifier}\t{total}\t{commits}\t{additions}\t{deletions}\t{newest_oid}\n"
        for identifier, (total, commits, additions, deletions, newest_oid) in sorted(
            cache.items()
        )
    )
    CACHE_PATH.write_text(f"{CACHE_VERSION}\n{body}", encoding="utf-8")


def initialize_cache(
    owner_id: str, repo_nodes: list[dict[str, Any]]
) -> dict[str, CacheEntry]:
    cache: dict[str, CacheEntry] = {}
    for repository in repo_nodes:
        name = repository["nameWithOwner"]
        identifier = hashlib.sha256(name.encode()).hexdigest()
        print(f"Initial scan: {name}", flush=True)
        entry = scan_repository(owner_id, name)
        expected_total, expected_oid = repository_state(repository)
        if entry[0] != expected_total or entry[4] != expected_oid:
            raise RuntimeError(f"Repository changed during initial scan: {name}")
        cache[identifier] = entry
        write_cache(cache)
    return cache


def increment_cache(
    owner_id: str, repo_nodes: list[dict[str, Any]]
) -> dict[str, CacheEntry]:
    versioned, old_cache = load_cache()
    if not versioned:
        raise RuntimeError(
            "Incremental cache is not initialized; run initialize_profile.py once."
        )

    current_identifiers = {
        hashlib.sha256(repository["nameWithOwner"].encode()).hexdigest()
        for repository in repo_nodes
    }
    cache = {
        identifier: entry
        for identifier, entry in old_cache.items()
        if identifier in current_identifiers
    }

    for repository in repo_nodes:
        name = repository["nameWithOwner"]
        identifier = hashlib.sha256(name.encode()).hexdigest()
        current_total, current_oid = repository_state(repository)
        previous = cache.get(identifier)

        if previous and previous[0] == current_total and previous[4] == current_oid:
            continue

        if previous and current_total > previous[0]:
            delta_commits, delta_add, delta_del, newest_oid, found_marker = (
                scan_new_commits(owner_id, name, previous[4])
            )
            expected_delta = current_total - previous[0]
            if found_marker and delta_commits == expected_delta:
                cache[identifier] = (
                    current_total,
                    previous[1] + delta_commits,
                    previous[2] + delta_add,
                    previous[3] + delta_del,
                    newest_oid,
                )
                print(
                    f"Incremented {name}: +{delta_commits} commits, "
                    f"+{delta_add} lines, -{delta_del} lines",
                    flush=True,
                )
                write_cache(cache)
                continue

        reason = "new repository" if previous is None else "history changed"
        print(f"Rebuilding {name} ({reason})", flush=True)
        entry = scan_repository(owner_id, name)
        if entry[0] != current_total or entry[4] != current_oid:
            raise RuntimeError(f"Repository changed during refresh: {name}")
        cache[identifier] = entry
        write_cache(cache)

    write_cache(cache)
    return cache


def dotted_value(
    root: etree._Element, element_id: str, value: int | str, width: int
) -> None:
    text = f"{value:,}" if isinstance(value, int) else str(value)
    value_node = root.find(f".//*[@id='{element_id}']")
    dots_node = root.find(f".//*[@id='{element_id}_dots']")
    if value_node is None or dots_node is None:
        raise RuntimeError(f"Missing SVG nodes for {element_id}")
    value_node.text = text
    dots_node.text = " " + "." * max(2, width - len(text)) + " "


def plain_value(root: etree._Element, element_id: str, value: int | str) -> None:
    node = root.find(f".//*[@id='{element_id}']")
    if node is None:
        raise RuntimeError(f"Missing SVG node for {element_id}")
    node.text = f"{value:,}" if isinstance(value, int) else str(value)


def update_svg(path: Path, values: dict[str, int]) -> None:
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


def update_profile(
    cache: dict[str, CacheEntry], owned: list[dict[str, Any]], all_repos: list[dict[str, Any]], followers: int
) -> None:
    commits = sum(entry[1] for entry in cache.values())
    additions = sum(entry[2] for entry in cache.values())
    deletions = sum(entry[3] for entry in cache.values())
    values = {
        "repo_data": len(owned),
        "contrib_data": len(all_repos),
        "star_data": sum(int(repository["stargazerCount"]) for repository in owned),
        "commit_data": commits,
        "follower_data": followers,
        "loc_data": additions - deletions,
        "loc_add": additions,
        "loc_del": deletions,
    }
    for svg_path in SVG_PATHS:
        update_svg(svg_path, values)


def initialize() -> None:
    owner_id, followers = account_data()
    owned = repositories(["OWNER"], owner_id)
    all_repos = repositories(
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"], owner_id
    )
    cache = initialize_cache(owner_id, all_repos)
    update_profile(cache, owned, all_repos, followers)
    print(f"Initialized profile cache for {USER_NAME}")


def daily_update() -> None:
    owner_id, followers = account_data()
    owned = repositories(["OWNER"], owner_id)
    all_repos = repositories(
        ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"], owner_id
    )
    cache = increment_cache(owner_id, all_repos)
    update_profile(cache, owned, all_repos, followers)
    print(f"Incrementally updated profile for {USER_NAME}")


if __name__ == "__main__":
    daily_update()
