# David's Daily Bread

A twice-daily news briefing — technology, markets, and science — baked fresh every morning (~5 AM) and evening (~10 PM) and published at [davidsdailybread.com](https://davidsdailybread.com).

## How it works

- A scheduled Claude task gathers the news twice a day, fills a fixed newspaper-style template, and publishes here via GitHub Pages.
- `index.html` — the latest edition.
- `editions/` — every past edition, dated (e.g. `2026-07-07-morning.html`).
- `archive.html` — the browsable "bread box" of past editions.
- `archive.json` — machine-readable manifest the scheduled task reads to append new editions.
- `CNAME` — custom domain for GitHub Pages.

## Publishing an edition (what the scheduled task does)

1. Fetch `archive.json` from the live site, add the new edition entry.
2. Regenerate `index.html` (new content, same fixed template) and `archive.html`.
3. Upload the dated copy to `editions/`, and `index.html` + `archive.html` + `archive.json` to the root.
