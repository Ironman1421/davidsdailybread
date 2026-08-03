# David's Daily Bread product specification

Status: active production contract
Owner: David Friedhof
Last reconciled: 2026-08-01

## Purpose and source precedence

David's Daily Bread is a founder-led Christian media and learning project. Its
current product is a twice-daily, source-linked website for everyday readers,
combining trustworthy technology coverage, practical learning, and quiet
Christian reflection. It earns attention through useful compression and earns
trust by making every factual item traceable.

David retains final control over mission, theology, editorial direction,
partnerships, product direction, channels, and monetization. The publisher may
remain faceless; David is not required to appear on camera. The current proof
goal is the first 1,000 genuinely engaged people who return for faith,
technology, prayer, and service. Larger reach remains an aspiration, not an
instruction to outrun trust, moderation, or founder direction.

When sources disagree, use this order:

1. `FOUNDER_DOCTRINE.md` for mission, founder authority, strategic direction,
   and paused initiatives.
2. `BRAND.md` for brand, voice, art, typography, and reader-visible house law.
3. This file for the product shape and public promises.
4. `docs/DISTRIBUTION_SPEC.md` for channel, adapter, rights, and measurement law.
5. `BAKE.md` for the daily editorial and publishing procedure.
6. Tests for executable contracts. A test that contradicts the five documents
   above is a defect, not permission to change the product.

The public `Ironman1421/davidsdailybread` repository is the active production
source. The private `ddb-ops` and `ddb-engineering` repositories preserve useful
history, but their Mac, Spark, Buttondown, and once-daily plans are not current
operating authority unless deliberately migrated into this repository. The
former weekly email pilot is paused and guarded by
`docs/NEWSLETTER_PILOT_SPEC.md`.

## Edition contracts

### Morning edition

- Cadence: daily, dispatched at 4:40 AM Pacific, with a delayed 4:45 AM
  DST-safe GitHub backup, targeting reader-ready publication near 5:00 AM
  Pacific (8:00 AM Eastern).
- Job: straight, politics-free news from the prior day in technology, business
  and markets, and science. Exclude partisan politics, political personalities,
  elections, culture-war disputes, war, diplomacy, sanctions, tariffs, and
  geopolitical maneuvering. Completed rules may run only for their direct,
  practical effect without political framing.
- Shape: one lead across all beats, then 2 to 6 cards in each of the three beats.
- Scripture: every morning story ends with the compact inline Scripture for
  Reflection treatment, on the front page and category pages. The editor
  selects a repository-owned identifier; the renderer supplies exact verified
  BSB text, reference, translation label, and Bible link. A required brief
  connection guides the reader using readers, we, us, or our. It never assigns
  divine approval, condemnation, judgment, prophecy, or biblical meaning to the
  people or event. Data-only sections, navigation, and the evening edition are
  excluded.
- Reader features: at most one Ask the Baker question, one Letter to the King,
  and one Crumb Board pin. While new intake is paused, only the frozen existing
  queue may supply reader material, selected oldest first; a house letter may
  fill the King slot only when no reader letter waits. Reopening submissions
  requires a verified private boundary and David's explicit approval.
- Category pages are morning-owned and must not be changed by an evening bake.

### Evening edition

- Cadence: daily, dispatched at 2:40 PM Pacific, with a delayed 2:45 PM
  DST-safe GitHub backup, targeting reader-ready publication near 3:00 PM
  Pacific (6:00 PM Eastern).
- Job: a Field Guide of things an everyday reader can act on that night.
- Shape: one useful lead, 2 to 6 trending tools, and 2 to 6 practical workflows.
- Presentation: the July 31 Field Guide format with one useful lead, a two-column
  tool shelf and workflow lane, then Keep and Ponder with Mary of Nazareth as
  its recurring biblical presence: a reviewed KJV passage, a release prompt,
  and a short prayer selected deterministically. Mary is not used as an invented
  first-person advice voice, and the prayer is addressed to God.
- A tool must be available now, show where it is trending, state price and
  platform, and carry an honest caveat.
- A workflow must state what it accomplishes, 2 to 4 prerequisites, and an
  honest time estimate.
- `/tools.html` and `/workflows.html` are searchable standing libraries backed
  by a bounded, source-linked `/evening-catalog.json`. The evening's top links
  open those pages instead of scrolling within the current edition.
- No news section, reader-submission section, category-page write, or
  reader-state write. Keep and Ponder with Mary of Nazareth is reviewed product
  copy, not mail.

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
- While intake is paused, the renderer rejects questions, pins, names,
  signatures, and submission-derived bookkeeping keys. A reviewed house letter
  must match its satchel identifier and text exactly; only deterministic
  house-style em-dash normalization is allowed.
- The lead title is self-contained, at most 130 characters, and stored exactly
  in `archive.json`. This is the input contract for downstream distribution.

## Distribution contracts

- Website: GitHub Pages from `main`.
- Archive: `/archive.json` and `/editions/YYYY-MM-DD-{morning|evening}.html` are
  public APIs. Their paths and field meanings require an explicit migration.
- RSS: `/feed.xml` contains the same ordered edition set as `archive.json`.
- Evening catalog: daily evening bakes may prepend their exact validated cards
  to `/evening-catalog.json`, deduplicate by source URL, and retain at most 180
  entries per library. Backfills must not change the catalog.
- X: Spark's guarded `daicc-ddb-autopost` service is the sole active canonical
  broadcaster. The GitHub replacement remains disabled and kill-switched; the
  two lanes must never be enabled together. Either may consume an edition's
  exact archive lead only under `docs/DISTRIBUTION_SPEC.md`. The production
  observation is recorded in `docs/OPERATIONS_EVIDENCE_2026-08-01.md`.
  Credible-account replies are
  the primary near-term X acquisition strategy; each is approved by David and
  manually posted under `docs/X_REPLY_PLAYBOOK.md`.
- YouTube: the initial discovery channel is a faceless vertical-video format,
  tested voice-led against caption-led and always grounded in a canonical
  edition.
- Distribution measurements validate against
  `distribution/metrics.schema.json`; unknown metrics are null, never zero.
- Published X replies validate separately against
  `distribution/x-replies.schema.json`; unposted drafts are not committed.
- Email: newsletter sending and all activation work are paused. Preserve the
  current `/subscribe.html` state, but do not draft, test, schedule, send,
  configure, credential, import, or advance the former pilot's gates. Work may
  resume only after David explicitly reverses the decision and the governing
  documents, machine-readable contract, and tests are reconciled.
- Reader intake: do not reactivate a public submission path, fetch new Counter
  rows, provision or deploy the Supabase reader store, alter the external Google
  form or Sheet, delete the frozen queue, or rewrite history. Reopening requires
  a verified private boundary and David's explicit approval.

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
- Spark schedules in `America/Los_Angeles`. GitHub backup schedules use tested
  PDT/PST candidate pairs and an offset gate; no manual daylight-saving edit is
  required. Installation evidence is recorded in
  `docs/OPERATIONS_EVIDENCE_2026-08-01.md`.

## Product measures

Track separately for morning and evening:

- on-time publish rate and failed-bake reason;
- source-link resolution and post-publication correction count;
- unique readers, returning-reader rate, engaged time, and RSS follows;
- reader-intake state and, when intake is explicitly reopened, slips submitted,
  wait time, and publish rate;
- distribution posts attempted, skipped, duplicated, and successfully published;
- X replies approved and published, reply impressions, target-author
  interactions, approval latency, profile-visit windows, and follower deltas;
- impressions, shares, profile visits, follows, and site visits per edition.

Follower count is a reach metric, not a quality substitute. Corrections,
retention, shares per impression, and returning readers are guardrail metrics.
