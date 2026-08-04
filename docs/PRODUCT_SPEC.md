# David's Daily Bread product specification

Status: active production contract
Owner: David Friedhof
Last reconciled: 2026-08-04

## Purpose and source precedence

David's Daily Bread is a founder-led Christian media and learning project. Its
current production product is a twice-daily, source-linked website for everyday
readers, combining trustworthy technology coverage, practical learning, and
quiet Christian reflection. The active roadmap grows it into a carefully
moderated Christian learning, prayer, and service network. It earns attention
through useful compression and earns trust by making every factual item
traceable.

The publisher may remain faceless. A consistent off-camera voice may be used
when it improves retention, but David is not required to appear on camera. The
first proof goal is 1,000 genuinely engaged people who return for faith,
technology, prayer, and service. This is the first gate, not the ceiling.
Larger reach must compound trust and usefulness rather than outrun moderation
or founder direction.

When sources disagree, use this order:

1. `FOUNDER_DOCTRINE.md` for mission, founder authority, strategic direction,
   authorized local work, and production boundaries.
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
former weekly email pilot is not an active send plan. Newsletter retention
planning is active, while issue drafting, provider operations, and sending
remain disabled under `docs/NEWSLETTER_PILOT_SPEC.md`.

## Durable-moat product contract

`docs/GROWTH_ROADMAP.md` is the active phased roadmap. Product decisions should
strengthen at least one of these assets without weakening another:

- trust through sourcing, theology, privacy, and responsible moderation;
- a daily rhythm of learning, reflection, prayer, and service;
- reader-owned personal history;
- trusted relationships;
- useful contributions and earned helpfulness reputation; and
- distribution back to the canonical home.

The installable web app is the first app target. Native iOS and Android work is
evidence-gated by a platform capability the web app cannot adequately provide.
A desktop app is a later decision based on demonstrated study, Chronicles,
creation, or moderation needs.

Accounts are optional infrastructure for durable personal value, not a wall
around canonical journalism. Guest reading remains available. Personal notes,
prayer journals, saved material, and spiritual history are private by default,
portable, and deletable within any plainly disclosed public-record boundary.

Social features are released from private to broader scope: personal value,
trusted circles, bounded moderated cohorts, then any wider surface. Open posting
and private/direct messaging may be built and tested locally, but remain
production-disabled until their specific roadmap gates are approved. Private
messaging is optional and may be omitted permanently.

## Edition contracts

### Morning edition

- Cadence: daily, scheduled no earlier than 5:05 AM Pacific during daylight time.
- Job: straight news from the prior day in technology, business and markets,
  and science.
- Shape: one lead across all beats, then 2 to 6 cards in each of the three beats.
- Reader features: at most one Ask the Baker question, one Letter to the King,
  and one Crumb Board pin. While public intake is closed, only the frozen existing
  queue may supply reader material, selected oldest first; a house letter may
  fill the King slot only when no reader letter waits. Reopening submissions
  requires a verified private boundary and David's explicit approval.
- Category pages are morning-owned and must not be changed by an evening bake.

### Evening edition

- Cadence: daily, scheduled no earlier than 3:35 PM Pacific during daylight time.
- Job: a Field Guide of things an everyday reader can act on that night.
- Shape: one useful lead, 2 to 6 trending tools, and 2 to 6 practical workflows.
- Presentation: the July 31 Field Guide format with one useful lead, a two-column
  tool shelf and workflow lane, then Keep and Ponder with Mary of Nazareth as
  its recurring biblical
  presence: a reviewed KJV passage, a release prompt, and a short prayer selected
  deterministically. Mary is not used as an invented first-person advice voice,
  and the prayer is addressed to God.
- A tool must be available now, show where it is trending, state price and
  platform, and carry an honest caveat.
- A workflow must state what it accomplishes, 2 to 4 prerequisites, and an
  honest time estimate.
- `/tools.html` and `/workflows.html` are searchable standing libraries backed
  by a bounded, source-linked `/evening-catalog.json`. The evening's top links
  open those pages instead of scrolling within the current edition.
- No news section, reader-submission section, category-page write, or
  reader-state write. Keep and Ponder with Mary of Nazareth is reviewed
  product copy, not mail.

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
- Reader questions, pin text, names, signatures, selection order, and
  bookkeeping keys must match the committed Counter/satchel plan; the
  editorial model may write replies but may not alter or substitute a
  submission. Only deterministic house-style em-dash normalization is allowed.
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
- X: the unlocated Claude Cowork-era process is retired as authority. A
  replacement distributor may consume each edition's exact archive lead only
  after it satisfies `docs/DISTRIBUTION_SPEC.md`. Credible-account replies are
  the primary near-term X acquisition strategy; each is approved by David and
  manually posted under `docs/X_REPLY_PLAYBOOK.md`.
- YouTube: the initial discovery channel is a faceless vertical-video format,
  tested voice-led against caption-led and always grounded in a canonical
  edition.
- Distribution measurements validate against
  `distribution/metrics.schema.json`; unknown metrics are null, never zero.
- Published X replies validate separately against
  `distribution/x-replies.schema.json`; unposted drafts are not committed.
- Email: strategy and local product-integration prototypes are active. Preserve
  the current `/subscribe.html` state, but do not draft an issue, test a send,
  schedule, send, configure the provider, operate on a list, or install a
  credential. Any external activation requires a scoped founder decision and a
  reconciled contract.
- Reader intake: private-boundary implementation and reopening preparation are
  active roadmap work. Public intake remains closed. The approved interim local
  site change removes the three public submission controls and makes Counter
  sync a no-op while preserving private browser notes and the four Chronicles
  exports. Deployment, external Google form/Sheet changes, data migration,
  legacy queue deletion, private-store provisioning, and history rewriting
  remain separately gated.

## Community and app release contract

- Local research, design, implementation, and testing are authorized across all
  roadmap phases.
- A completed local feature is not production approval.
- Every external release names the exact reviewed commit or package, provider,
  operator, data classes, retention and deletion behavior, moderation coverage,
  cost ceiling, measurement window, kill switch, rollback, and incident path.
- Public is never the default audience for a prayer, journal entry, personal
  history item, or trusted-circle contribution.
- A participation surface includes clear rules, consent, report and removal
  paths, rate limits, and blocking wherever relationships exist.
- No feature may sell or license personal or spiritual data, use it for
  behavioral advertising, or create a cross-site identity graph.
- No notification may reveal sensitive prayer text on a lock screen by default.
- The product must not promise continuous moderation or emergency response.
  Crisis and medical copy must direct people to appropriate immediate or
  professional help without presenting the product as a substitute.

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

The official first-1,000 milestone is measured on the canonical website under
`docs/AUDIENCE_MEASUREMENT_SPEC.md`. Social, RSS, and public-participation
signals are supporting evidence and are not added to the website total because
the same person may appear in more than one channel. Until approved
instrumentation produces a complete month, the audience baseline is unknown,
not zero.

Track separately for morning and evening:

- on-time publish rate and failed-bake reason;
- source-link resolution and post-publication correction count;
- unique readers, returning-reader rate, engaged time, and RSS follows;
- reader-intake state and, when intake is approved and operating, slips
  submitted, wait time, and publish rate;
- distribution posts attempted, skipped, duplicated, and successfully published;
- X replies approved and published, reply impressions, target-author
  interactions, approval latency, profile-visit windows, and follower deltas;
- impressions, shares, profile visits, follows, and site visits per edition.

As roadmap features become separately activated, also track by surface and
cohort:

- account activation, export, deletion, recovery, and session-revocation health;
- saved personal value without inspecting private content;
- trusted-circle return, invitation acceptance, helpful contributions, and
  constructive responses;
- report volume, block use, queue age, removals, appeals, repeat abuse,
  moderator load, privacy requests, and incidents; and
- voluntarily shared prayer and service outcomes in aggregate.

Follower count is a reach metric, not a quality substitute. Corrections,
retention, shares per impression, and returning readers are guardrail metrics.
Raw time-on-site, posting volume, streaks, and notification opens are not
success when they reduce well-being, privacy, trust, or mission value.
