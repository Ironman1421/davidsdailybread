# Repository and ownership map

Last reconciled: 2026-08-01

| Repository | Current role | Authority |
|---|---|---|
| `Ironman1421/davidsdailybread` | Live site, renderer, templates, workflows, archive, RSS | Production source of truth |
| `Ironman1421/ddb-ops` | July 9 to 14 strategy, approvals, experiments, migration history | Historical context; materially stale |
| `Ironman1421/ddb-engineering` | Retired Spark pipeline, Buttondown path, acceptance harness, handoff log | Preserved engineering history; no deployment authority |
| `Ironman1421/davids-ai-command-center` | Spark-owned Counter and edition workflow triggers, both-slot watchdogs, active guarded X autoposter, plus general multi-agent bootstrap and profiles | Operational timing and the current X adapter; never editorial or site-publishing authority |
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
- Reader-submission storage has no privacy owner or retention policy.
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
the public repository's existing Counter Sync and Daily bake
`workflow_dispatch` endpoints and inspect the exact-date archive contract. They
may not compose editions, choose the latest available edition, push site
content, or receive the editorial model secret. The Pacific schedule is Counter
Sync at 12:30 AM, morning at 3:00 AM, morning watchdog at 5:15 AM, evening at
1:00 PM, and evening watchdog at 3:30 PM. These starts target reader-ready
publication near 5:00 AM and 3:00 PM Pacific. GitHub's paired PDT/PST schedules
remain delayed backups for Counter Sync and both bakes.
The merged commit, installed-unit verification, and no-op canaries are recorded
in `docs/OPERATIONS_EVIDENCE_2026-08-01.md`.

## Standing evening surfaces

- `templates/evening.html`: approved July 31 Field Guide edition, with Keep and
  Ponder below the tool shelf and workflows.
- `evening-rest.json`: reviewed Keep and Ponder material, selected by date.
- `evening-catalog.json`: bounded tools and workflows catalog updated only by a
  successful daily evening render.
- `tools.html` and `workflows.html`: standing searchable library pages.

## Weekly email pilot

The active four-week pilot is deliberately manual and owned in this repository
by `docs/NEWSLETTER_PILOT_SPEC.md`, `operations/newsletter-pilot.contract.json`,
and `newsletter/weekly-ledger.md`. Buttondown is the subscriber system of
record. The retired `ddb-engineering` Buttondown automation is not authority and
is not being restored.
