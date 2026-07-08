# README Image Strategy

This profile README favors local SVG snapshots for important visuals.
External generated images are convenient, but they can fail when the upstream
service is down, rate-limited, blocked by a network path, or held behind a stale
GitHub image proxy cache.

## Rules

1. Keep essential visual assets in `assets/generated/`.
2. Use relative paths from `README.md`, for example `./assets/generated/profile-banner.svg`.
3. Avoid external image services for core layout, repo cards, and profile summary cards.
4. Use external badges only when the data must be live and the README still reads well if the image is missing.
5. Prefer SVG files without scripts, external fonts, or remote image references.

## Troubleshooting

1. If an image is blank, open the raw asset path and confirm it is not a `404`.
2. Check filename casing. GitHub paths are case-sensitive.
3. Validate SVG/XML before pushing.
4. If the image was just changed but GitHub still shows the old version, wait for the CDN cache to expire or change the filename, for example `profile-banner-v2.svg`.
5. If the failing image is external, replace it with a local snapshot unless the live data is truly required.
