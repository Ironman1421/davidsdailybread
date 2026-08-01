# Repository and ownership map

Last reconciled: 2026-08-01

| Repository | Current role | Authority |
|---|---|---|
| `Ironman1421/davidsdailybread` | Live site, renderer, templates, workflows, archive, RSS | Production source of truth |
| `Ironman1421/ddb-ops` | July 9 to 14 strategy, approvals, experiments, migration history | Historical context; materially stale |
| `Ironman1421/ddb-engineering` | Retired Spark pipeline, Buttondown path, acceptance harness, handoff log | Preserved engineering history; no deployment authority |
| `Ironman1421/davids-ai-command-center` | Spark-owned DDB workflow trigger and morning watchdog, plus general multi-agent bootstrap and profiles | Operational timing authority only; never editorial or publishing authority |
| `Ironman1421/hermes-canonical` | Hermes profiles and general skills | Platform configuration, not the active bake |

Claude Cowork is not a repository and is no longer an authority for this
project. Useful ideas from old conversations must be deliberately reconstructed
in version-controlled specs, code, and tests before use.

## Known ownership gaps

- The missing external X poster has been replaced by the repository-owned
  canonical broadcaster and runbook. Its main-only production environment
  exists with publishing disabled and the kill switch engaged, but it has no X
  secrets or expected-account identity until the app and account are verified.
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

## Morning timing boundary

The canonical bake and publish remain in `Ironman1421/davidsdailybread`.
Spark's reviewed components in `Ironman1421/davids-ai-command-center` may invoke
that repository's existing `workflow_dispatch` endpoint and inspect the public
exact-date archive contract. They may not compose editions, choose the latest
available edition, push site content, or receive the editorial model secret.
GitHub's scheduled morning workflow remains a delayed backup trigger.

## Standing evening surfaces

- `templates/evening.html`: approved Editorial Ledger and Guided Path edition.
- `evening-rest.json`: reviewed spiritual closing material, selected by date.
- `evening-catalog.json`: bounded tools and workflows catalog updated only by a
  successful daily evening render.
- `tools.html` and `workflows.html`: standing searchable library pages.

## Weekly email pilot

The active four-week pilot is deliberately manual and owned in this repository
by `docs/NEWSLETTER_PILOT_SPEC.md`, `operations/newsletter-pilot.contract.json`,
and `newsletter/weekly-ledger.md`. Buttondown is the subscriber system of
record. The retired `ddb-engineering` Buttondown automation is not authority and
is not being restored.
