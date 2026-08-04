# Repository and ownership map

Last reconciled: 2026-08-04

`FOUNDER_DOCTRINE.md` governs mission, ownership, strategic direction,
authorized local work, and production boundaries. Repository ownership never
transfers David's final control.

| Repository | Current role | Authority |
|---|---|---|
| `Ironman1421/davidsdailybread` | Live site, renderer, templates, workflows, archive, RSS | Production source of truth |
| `Ironman1421/ddb-ops` | July 9 to 14 strategy, approvals, experiments, migration history | Historical context; materially stale |
| `Ironman1421/ddb-engineering` | Retired Spark pipeline, Buttondown path, acceptance harness, handoff log | Preserved engineering history; no deployment authority |
| `Ironman1421/davids-ai-command-center` | Spark-owned edition workflow triggers, both-slot watchdogs, active guarded X autoposter and X Monitor, plus general multi-agent bootstrap and profiles | Operational timing and the current X adapter; never editorial or site-publishing authority. Counter dispatch is retired while intake is closed. |
| `Ironman1421/hermes-canonical` | Hermes profiles and general skills | Platform configuration, not the active bake |

Claude Cowork is not a repository and is no longer an authority for this
project. Useful ideas from old conversations must be deliberately reconstructed
in version-controlled specs, code, and tests before use.

## Known ownership gaps

- Spark's guarded `daicc-ddb-autopost` service is the current canonical X lane.
  The repository-owned broadcaster and runbook are a replacement path whose
  main-only environment remains disabled and kill-switched. Activating it is a
  separately reviewed credential migration that must first disable Spark's
  lane so the two publishers can never duplicate an edition.
- Social analytics now have a checked-in schema, but no live ledger, automated
  snapshots, or weekly scorecard.
- Branch protection and workflow bypass ownership are not documented as code.
- Reader-submission storage has an approved private design but no provisioned
  project or named operator. Site-side intake closure is deployed; external
  provider state, migration, deletion, and history work remain gated.
- YouTube now has repository-owned pilot specifications, templates, schemas,
  baseline ledgers, validation, and a named owner in this repository. It still
  has no live upload adapter or credential boundary. TikTok, Instagram, and
  LinkedIn adapters do not yet have repositories, credential boundaries,
  acceptance tests, or named operators.

New operational components must have a repository, named owner, on-call/failure
path, secret boundary, idempotency contract, metrics, and a tested disable switch
before they become unattended production dependencies.

## Edition timing boundary

The canonical bake and publish remain in `Ironman1421/davidsdailybread`.
Spark's reviewed components in `Ironman1421/davids-ai-command-center` may invoke
the public repository's Daily bake `workflow_dispatch` endpoint and inspect the
exact-date archive contract. While reader intake is paused, they must not invoke
Counter Sync. Existing Counter scheduling is implementation state to reconcile,
not authority to fetch or commit new reader rows. They
may not compose editions, choose the latest available edition, push site
content, or receive the editorial model secret. The Pacific schedule is morning
at 4:40 AM, morning watchdog at 5:15 AM, evening at
2:40 PM, and evening watchdog at 3:30 PM. These starts target reader-ready
publication near 5:00 AM and 3:00 PM Pacific. GitHub's paired PDT/PST schedules
remain delayed backups for both bakes. The existing Counter Sync schedule is
not an approved backup while the founder pause is active.
The merged commit, installed-unit verification, and no-op canaries are recorded
in `docs/OPERATIONS_EVIDENCE_2026-08-01.md`.

## Standing evening surfaces

- `templates/evening.html`: approved July 31 Field Guide edition with Mary of
  Nazareth below the tool shelf and workflows.
- `evening-rest.json`: reviewed Keep and Ponder material, selected by date.
- `evening-catalog.json`: bounded tools and workflows catalog updated only by a
  successful daily evening render.
- `tools.html` and `workflows.html`: standing searchable library pages.

## Durable-moat product direction

`docs/GROWTH_ROADMAP.md` and
`operations/durable-moat-roadmap.contract.json` govern the phased expansion
from canonical publication to an installable web app, accounts, personal
history, moderated prayer and participation, native mobile, and later
institutional or desktop decisions. All phases are authorized for local work.
No phase is authorized for external deployment or activation by that decision
alone.

## Newsletter retention option

Strategy and local product-integration prototypes are active. The former
four-week pilot is not an active send plan. Its fail-closed signup page is preserved,
and issue drafting, testing, configuration, credentialing, list operations,
activation, and sending remain unauthorized. `docs/NEWSLETTER_PILOT_SPEC.md`,
`operations/newsletter-pilot.contract.json`, and
`newsletter/weekly-ledger.md` retain the guarded plan and historical template.
The retired `ddb-engineering` Buttondown automation is not authority and is not
being restored.

## First 1,000 audience measurement

`docs/AUDIENCE_MEASUREMENT_SPEC.md` defines the official privacy-safe website
return milestone. `audience/measurement.schema.json`,
`audience/monthly-ledger.json`, and `audience/validate_ledger.py` enforce the
aggregate record. `audience/qualifier.mjs`, `audience/collector.mjs`, and
`audience/reporting.mjs` are pure local reference state machines.
`audience/browser-adapter.mjs` is a bounded, disabled-by-default adapter with a
checked-in `enabled: false`, `endpoint: null` configuration and no built-in
transport or public-template integration. `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md`
owns canary, monthly close, purge, and stop procedures. Cloudflare Workers + D1
is selected for provider-specific local implementation and an unprovisioned
canary plan. `audience/cloudflare/` contains the canary-only wrapper, D1 schema,
disabled placeholder configuration, tests, and plan. The current state is
`implementation-selected`: no account, endpoint, operator, resource ID,
credential, route, trigger, canary execution, deployment, production script,
external provisioning, baseline, or spend is authorized.
`docs/AUDIENCE_ANALYTICS_DECISION.md` owns the separate founder gates for any
future external implementation and activation.

## Unprovisioned reader-store design

The Supabase reader store may be implemented and verified locally. No account,
project, resource, credential, endpoint, link, canary, deployment, activation,
live migration, DNS change, or spend is authorized without a scoped decision
from David.
