# README Image Strategy

This profile README keeps the main visual as a local PNG and avoids generated
SVG wrappers or decorative snapshot cards. External generated images are
convenient, but they can fail when the upstream service is down, rate-limited,
blocked by a network path, or held behind a stale GitHub image proxy cache.

## Rules

1. Keep the essential hero image in `assets/generated/profile-studio.png`.
2. Use the PNG directly from `README.md`; do not wrap it in another generated image.
3. Avoid external image services for core layout, repo cards, and profile summary cards.
4. Build project cards with Markdown/HTML tables instead of generated SVG images.
5. If the PNG is intentionally converted later, keep the result clear and free of extra text, badges, overlays, scripts, external fonts, or remote image references.

## Troubleshooting

1. If an image is blank, open the raw asset path and confirm it is not a `404`.
2. Check filename casing. GitHub paths are case-sensitive.
3. If the image was just changed but GitHub still shows the old version, wait for the CDN cache to expire or change the filename, for example `profile-studio-v2.png`.
4. If the failing image is external, replace it with local Markdown/HTML content unless the live data is truly required.
