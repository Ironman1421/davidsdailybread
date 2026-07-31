# David's Daily Bread product specification

Status: active production contract
Owner: David Friedhof
Last reconciled: 2026-07-31

## Purpose and source precedence

David's Daily Bread is a twice-daily, source-linked briefing for everyday
readers. It earns attention through useful compression and earns trust by
making every factual item traceable.

The publisher is faceless. A consistent off-camera voice may be used when it
improves retention, but David is not required to appear on camera. The active
audience goal is 1,000,000 combined followers across approved platforms in six
months, from a documented floor of five X followers on 2026-07-31.

When sources disagree, use this order:

1. `BRAND.md` for brand, voice, art, typography, and reader-visible house law.
2. This file for the product shape and public promises.
3. `docs/DISTRIBUTION_SPEC.md` for channel, adapter, rights, and measurement law.
4. `BAKE.md` for the daily editorial and publishing procedure.
5. Tests for executable contracts. A test that contradicts the four documents
   above is a defect, not permission to change the product.

The public `Ironman1421/davidsdailybread` repository is the active production
source. The private `ddb-ops` and `ddb-engineering` repositories preserve useful
history, but their Mac, Spark, Buttondown, and once-daily plans are not current
operating authority unless deliberately migrated into this repository.

## Edition contracts

### Morning edition

- Cadence: daily, scheduled no earlier than 5:05 AM Pacific during daylight time.
- Job: straight news from the prior day in technology, business and markets,
  and science.
- Shape: one lead across all beats, then 2 to 6 cards in each of the three beats.
- Reader features: at most one Ask the Baker question, one Letter to the King,
  and one Crumb Board pin. Waiting reader submissions are selected oldest first;
  a house letter may fill the King slot only when no reader letter waits.
- Category pages are morning-owned and must not be changed by an evening bake.

### Evening edition

- Cadence: daily, scheduled no earlier than 3:35 PM Pacific during daylight time.
- Job: a Field Guide of things an everyday reader can act on that night.
- Shape: one useful lead, 2 to 6 trending tools, and 2 to 6 practical workflows.
- A tool must be available now, show where it is trending, state price and
  platform, and carry an honest caveat.
- A workflow must state what it accomplishes, 2 to 4 prerequisites, and an
  honest time estimate.
- No news section, reader section, category-page write, or reader-state write.

## Shared editorial contracts

- Every factual item links to a source actually reviewed during that bake.
- Facts, figures, quotations, dates, prices, and popularity claims must be
  supported by the cited source text. Unsettled claims are removed.
- Journalism is plain and factual. Bread language belongs to product chrome,
  not news copy.
- No reader-visible em dash.
- Source links are absolute, credential-free HTTPS URLs.
- The only editorial HTML fragment is one leading `<b>plain text</b>` phrase in
  a card dek. All other editorial and reader content is plain text and escaped.
- Reader questions, names, signatures, selection order, and bookkeeping keys
  must match the committed Counter/satchel plan; the editorial model may write
  replies and lightly copyedit a pin, but may not substitute a submission.
- The lead title is self-contained, at most 130 characters, and stored exactly
  in `archive.json`. This is the input contract for downstream distribution.

## Distribution contracts

- Website: GitHub Pages from `main`.
- Archive: `/archive.json` and `/editions/YYYY-MM-DD-{morning|evening}.html` are
  public APIs. Their paths and field meanings require an explicit migration.
- RSS: `/feed.xml` contains the same ordered edition set as `archive.json`.
- X: the unlocated Claude Cowork-era process is retired as authority. A
  replacement distributor may consume each edition's exact archive lead only
  after it satisfies `docs/DISTRIBUTION_SPEC.md`.
- YouTube: the initial discovery channel is a faceless vertical-video format,
  tested voice-led against caption-led and always grounded in a canonical
  edition.
- Distribution measurements validate against
  `distribution/metrics.schema.json`; unknown metrics are null, never zero.
- Email is retired. No signup or delivery promise may return without a new
  product decision and migration plan.

## Reliability and release contract

- Scheduled publication fails closed on unverifiable content, invalid output,
  an unexpected changed path, or an existing edition for the same date and slot.
- A bake session has no repository write credential. The workflow alone commits
  and pushes after its guard passes.
- Interactive changes use a branch and pull request. CI must render both slots
  and run the complete contract suite before merge.
- The renderer validates all candidate public output before replacing any file.
- Daily reader content is provenance-checked against committed input before any
  reader state or public file changes; historical backfills cannot include it.
- Daylight-saving schedule changes are an operational risk until the schedule is
  made timezone-aware or a tested seasonal runbook owns the change.

## Product measures

Track separately for morning and evening:

- on-time publish rate and failed-bake reason;
- source-link resolution and post-publication correction count;
- unique readers, returning-reader rate, engaged time, and RSS follows;
- reader slips submitted, wait time, and publish rate;
- distribution posts attempted, skipped, duplicated, and successfully published;
- impressions, shares, profile visits, follows, and site visits per edition.

Follower count is a reach metric, not a quality substitute. Corrections,
retention, shares per impression, and returning readers are guardrail metrics.
