# David's Daily Bread

A news briefing on technology, markets, and science. Loved by God. One edition is baked fresh each morning and published at [davidsdailybread.com](https://davidsdailybread.com). Evening delivery remains in testing.

## How it works

- A bake pipeline (`ddb_bake.py`) aggregates news into a draft, then fills a fixed newspaper-style template from that draft and publishes here via GitHub Pages.
- `index.html` — the latest edition.
- `editions/` — every past edition, dated (e.g. `2026-07-07-morning.html`).
- `archive.html` — the browsable "bread box" of past editions.
- `archive.json` — machine-readable manifest the scheduled task reads to append new editions.
- `CNAME` — custom domain for GitHub Pages.

## Publishing an edition (what the scheduled task does)

1. Fetch `archive.json` from the live site, add the new edition entry.
2. Regenerate `index.html` (new content, same fixed template) and `archive.html`.
3. Upload the dated copy to `editions/`, and `index.html` + `archive.html` + `archive.json` to the root.
