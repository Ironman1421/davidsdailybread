# David's Daily Bread product specification

Status: active production contract
Owner: David Friedhof
Last reconciled: 2026-08-07

## Purpose and source precedence

David's Daily Bread is a founder-led Christian media and learning project. Its
current product is a twice-daily, source-linked website for everyday readers:
news and Scripture each morning, an evening Field Guide with useful tools and
workflows, and the exact public brand statement **Loved by God**. The active
roadmap grows it into a carefully moderated Christian learning, prayer, and
service network. It earns attention through useful compression and earns trust
by making every factual item traceable.

David retains final control over mission, theology, editorial direction,
partnerships, product direction, channels, and monetization. The publisher may
remain faceless; David is not required to appear on camera. The current proof
goal is the first 1,000 genuinely engaged people who return for faith,
technology, prayer, and service. Larger reach remains an aspiration, not an
instruction to outrun trust, moderation, or founder direction.

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
former weekly email pilot is not an active send plan. Local retention strategy
and product-integration prototypes may proceed, while issue drafting, provider
operations, address collection, activation, and sending remain disabled under
`docs/NEWSLETTER_PILOT_SPEC.md`.

The lean core-proof outreach learning campaign is governed by
`docs/OUTREACH_CAMPAIGN.md` and
`operations/outreach-campaign.contract.json`. The evening Field Guide is its
acquisition franchise. The campaign clock remains blocked until one
privacy-safe observable return path is implemented and validated. Email,
analytics, community features, generated media, provisioning, deployment,
spending, and public campaign actions remain inactive.

## Durable-moat product contract

`docs/GROWTH_ROADMAP.md` is the active phased roadmap. Product decisions should
strengthen trust, daily ritual, reader-owned personal history, relationships,
useful contributions, or distribution back to the canonical home without
weakening another asset.

The installable web app is the first app target. It is the existing responsive
website made installable and mobile-capable, not a separate editorial product
or a generic Christian feature suite. The website, archive, RSS, edition paths,
source receipts, and corrections remain canonical. Native iOS and Android work
is evidence-gated by a platform capability the web app cannot adequately
provide; a desktop app is a later evidence-gated decision.

Accounts are optional infrastructure for durable personal value, not a wall
around canonical journalism. Guest reading remains available. Personal notes,
prayer journals, saved material, and spiritual history are private by default,
portable, and deletable within any plainly disclosed public-record boundary.

Social features release from private to broader scope: personal value, trusted
circles, bounded moderated cohorts, then any wider surface. Open posting and
private or direct messaging may be built and tested locally, but remain
production-disabled until their specific roadmap gates are approved. Private
messaging is optional and may be omitted permanently.

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
- Reader features: while public intake is closed, Ask the Baker and Crumb Board
  are empty and reader letters are rejected. At most one reviewed house-satchel
  Letter to the King may run. Reopening reader submissions requires a verified
  private boundary and David's explicit approval.
- Category pages are morning-owned and must not be changed by an evening bake.

### Evening edition

- Cadence: daily, dispatched at 2:40 PM Pacific, with a delayed 2:45 PM
  DST-safe GitHub backup, targeting reader-ready publication near 3:00 PM
  Pacific (6:00 PM Eastern).
- Job: a force-multiplier Field Guide of broadly useful productivity tools and
  repeatable workflows an everyday reader can act on that night.
- Shape: one useful lead, 2 to 6 trending tools, and 2 to 6 practical workflows.
- Presentation: the July 31 Field Guide format with one useful lead, a two-column
  tool shelf and workflow lane, then Keep and Ponder with Mary of Nazareth as
  its recurring biblical presence: a reviewed KJV passage, a release prompt,
  and a short prayer selected deterministically. Mary is not used as an invented
  first-person advice voice, and the prayer is addressed to God.
- A tool must be available now, show where it is trending, state price and
  platform, carry an honest caveat, and plausibly improve recurring work.
- A workflow must state what it accomplishes, 2 to 4 prerequisites, and an
  honest time estimate. It must be a reusable operating routine, not merely a
  one-time project or clever trick.
- Every tool and workflow must serve a broad share of ordinary readers and
  provide recurring or compounding leverage by saving time, improving output,
  supporting earning, strengthening communication, or reducing mental load.
  Trend evidence proves current interest only; it never rescues a narrow
  novelty, amusement, demo, or niche hobby item.
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
- Outreach learning campaign: after exact activation, at most one individually
  approved evening Field Guide source card may run per day. Qualified replies
  remain individually approved and manual, with an absolute range of zero to
  four per staffed day. A fifth reply requires a new founder amendment. Every
  source card links to its exact immutable evening edition. The 30-day campaign
  may report only declared proxy and observable-return evidence, never the
  official first-1,000 milestone.
- Gemini Omni, YouTube, and every generated-media lane are deferred from the
  lean core-proof campaign. Their planning artifacts convey no activation or
  publication authority.
- Distribution measurements validate against
  `distribution/metrics.schema.json`; unknown metrics are null, never zero.
- Published X replies validate separately against
  `distribution/x-replies.schema.json`; unposted drafts are not committed.
- Email: local retention strategy and product-integration prototypes are
  authorized. Preserve the current fail-closed `/subscribe.html` state, but do
  not collect addresses, draft an issue, test a send, schedule, send, configure
  a provider, operate on a list, install a credential, or activate the former
  pilot. External operations require a scoped founder decision and reconciled
  contract.
- Reader intake: the site-side closure is deployed and must remain fail-closed.
  Private-boundary implementation and reopening preparation are authorized
  locally. Do not reactivate a public submission path, fetch or recommit Counter
  rows, provision or deploy the Supabase reader store, alter external intake
  providers, delete the frozen queue, or rewrite history. Reopening requires a
  verified private boundary and David's explicit approval.

## Community and app release contract

- Local research, design, implementation, and testing are authorized across all
  roadmap phases. A completed local feature is not production approval.
- Every external release names the exact reviewed commit or package, provider,
  operator, data classes, retention and deletion behavior, moderation coverage,
  cost ceiling, measurement window, kill switch, rollback, and incident path.
- Public is never the default audience for a prayer, journal entry, personal
  history item, or trusted-circle contribution.
- Participation surfaces require clear rules, consent, report and removal paths,
  rate limits, and blocking wherever relationships exist.
- Personal or spiritual data may not be sold, licensed, used for behavioral
  advertising, or joined into a cross-site identity graph.
- Notifications exclude sensitive prayer text from lock-screen payloads by
  default. The product never promises continuous moderation or emergency care.

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

The official first-1,000 milestone is measured on the canonical website under
`docs/AUDIENCE_MEASUREMENT_SPEC.md`. Social, RSS, and participation signals are
supporting evidence and are not added to that total. Until approved
instrumentation produces a complete month, the audience baseline is unknown,
not zero.

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

As roadmap features become separately activated, also track account export,
deletion, recovery, session revocation, saved personal value without inspecting
private content, relationship health, moderation workload, privacy requests,
incidents, and voluntarily shared prayer or service outcomes in aggregate.

Follower count is a reach metric, not a quality substitute. Corrections,
retention, shares per impression, and returning readers are guardrail metrics.
Raw time-on-site, posting volume, streaks, and notification opens are not
success when they reduce well-being, privacy, trust, or mission value.
