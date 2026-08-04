# David's Daily Bread

A founder-led Christian media and learning project helping believers grow in
faith, understand technology wisely, pray for one another, and use what they
learn in service to others. Its current website includes a morning briefing on
technology, markets, and science plus an evening Field Guide to useful AI and
technology. Loved by God. Baked fresh twice daily and published at
[davidsdailybread.com](https://davidsdailybread.com) via GitHub Pages. See
`FOUNDER_DOCTRINE.md` for the governing direction.

## How it works

**GitHub Actions** (`.github/workflows/ddb-bake.yml`) fires two bakes daily,
morning news at 12:05 UTC and evening trends at 22:35 UTC, each driving a
Claude session that follows **`/BAKE.md`** (the complete operating spec). The
session does the editorial work: researching, choosing the lead, writing every
dek and glance line, and (mornings) answering reader mail in the house
personas. `ddb_session_bake.py` does the mechanical work deterministically:
template fill, category pages (morning only), the bounded evening catalog,
archive, RSS, and state. Two
commits per bake ("Morning edition ..." or "Evening edition ..." then
"Archive: ..."), pushed to `main`; Pages redeploys.

- `templates/` — page templates; ALL design changes happen here, never at bake time.
- `index.html` — the latest edition; `tech/markets/science.html` — category pages.
- `editions/` — every past edition, dated. `archive.html` / `archive.json` — the bread box.
- `tools.html` / `workflows.html` — searchable evening libraries backed by
  `evening-catalog.json`.
- `feed.xml` — complete RSS delivery. The current `subscribe.html` state is
  preserved. Newsletter strategy is active, but provider activation and
  sending remain disabled.
- `counter.csv` — the frozen existing reader queue. Public intake is closed and
  `.github/workflows/counter-sync.yml` is a no-op pending a verified private
  boundary and David's explicit reopening approval.
- `bakery-state.json` / `kings-satchel.json` — reader-content bookkeeping and
  the King's house letters.
- `BRAND.md` — brand source of truth; `brand.css` — design tokens.
- `FOUNDER_DOCTRINE.md` — source of truth for mission, founder authority,
  strategic direction, authorized local work, and production boundaries.
- `docs/PRODUCT_SPEC.md` — current product and distribution contract;
  `docs/SECURITY_SPEC.md` — trust boundaries and required controls;
  `docs/DISTRIBUTION_SPEC.md` — channel, adapter, voice, rights, and measurement law;
  `docs/GROWTH_ROADMAP.md` — the phased durable-moat roadmap for distribution,
  apps, accounts, personal history, prayer, participation, and later expansion;
  `docs/AUDIENCE_MEASUREMENT_SPEC.md` — the exact first-1,000 qualification,
  privacy, aggregation, and evidence contract;
  `docs/AUDIENCE_ANALYTICS_DECISION.md` — the analytics architecture decision
  and the remaining founder gates after local-only provider selection;
  `docs/AUDIENCE_CLOUDFLARE_IMPLEMENTATION.md` — the isolated canary-only Worker
  and D1 implementation, disabled configuration, and authority boundary;
  `docs/FIRST_1000_FOUNDATION_PLAN.md` — the sequenced trust, measurement,
  mission-clarity, and discovery work package;
  `docs/X_REPLY_PLAYBOOK.md` — manually approved, reply-led X growth law;
  `docs/READER_STORE_SPEC.md` — approved private reader-store and cutover design;
  `docs/PUBLISHER_IDENTITY_SPEC.md` — approved scheduled identity and `main`
  ruleset design;
  `docs/NEWSLETTER_PILOT_SPEC.md` — active retention-planning option with
  issue drafting, provider activation, list operations, and sending disabled;
  `docs/AUDIT_2026-07-31.md` — takeover findings and open decisions.
- `operations/*.contract.json` — machine-readable desired state for the private
  reader boundary, protected publishing path, X broadcaster, newsletter gate,
  closed public reader intake, durable-moat phases, and selected-but-uninstalled
  audience boundary; these are not live credentials or proof that any external
  activation gate is complete.
- `distribution/metrics.schema.json` / `distribution/ledger.json` — the
  machine-readable measurement contract and current baseline/post ledger.
- `audience/measurement.schema.json` / `audience/monthly-ledger.json` — the
  privacy-safe website-return measurement contract and not-yet-measured
  baseline for the first 1,000.
- `audience/qualifier.mjs` / `audience/transition.schema.json` — the local-only,
  dependency-free qualification state machine and narrow transition envelope;
  they have no network implementation and are not loaded by the website.
- `audience/browser-adapter.mjs` / `audience/browser-adapter.config.json` — the
  disabled, endpoint-free, non-integrated browser boundary and opt-out behavior.
- `audience/collector.mjs` / `audience/reporting.mjs` — pure ordered collector
  and aggregate-only monthly-close prototypes; neither provisions a service.
- `audience/cloudflare/` — the local Cloudflare Worker + D1 wrapper, schema,
  disabled placeholder configuration, and unprovisioned canary plan. It has no
  account, resource identifier, route, secret, deployment, or production mode.
- `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md` — the founder-gated canary,
  activation, close, purge, kill-switch, and incident procedure.
- `docs/AUDIENCE_ACTIVATION_DECISION_TEMPLATE.md` — the partially completed
  evidence record for the selected local provider and the still-closed external
  measurement gates.
- `docs/AUDIENCE_PRIVACY_COPY_DRAFT.md` — unapproved short/expanded notice and
  opt-out language to verify against a future selected infrastructure boundary.
- `docs/AUDIENCE_ENDPOINT_RECOMMENDATION.md` — the local-only Cloudflare
  Worker+D1 decision, Supabase comparison, and remaining account, canary,
  DNS, privacy, and activation blockers; it provisions nothing.
- `operations/durable-moat-roadmap.contract.json` — the active phase,
  authorization, privacy, moderation, and external-activation boundary.
- `operations/reader-intake-pause.contract.json` — the active private-cutover
  work and closed-public-intake state with explicit no-deploy, no-delete, and
  no-external-change gates.
- `distribution/x-reply-approval-card.schema.json` — the private, transient
  per-candidate approval-card contract; no real draft cards are committed.
- `distribution/x-replies.schema.json` / `distribution/x-replies.json` — the
  published X reply contract and blocked five-follower manual-strategy baseline.
- `ddb_bake.py` / `ddb_satchel.py` / `ddb_synth.py` — the previous Spark-era
  pipeline; `ddb_session_bake.py` reuses their tested render/state helpers.
- `tests/` — regression tests for brand law, archive integrity, and standing pages.

Standing pages (`chronicles.html`, `archive.html`, `subscribe.html`,
`secret-menu.html`, `404.html`) are never regenerated by the bake; edit them
only from the current `main` version.
