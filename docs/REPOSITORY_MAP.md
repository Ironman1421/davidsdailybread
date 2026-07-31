# Repository and ownership map

Last reconciled: 2026-07-31

| Repository | Current role | Authority |
|---|---|---|
| `Ironman1421/davidsdailybread` | Live site, renderer, templates, workflows, archive, RSS | Production source of truth |
| `Ironman1421/ddb-ops` | July 9 to 14 strategy, approvals, experiments, migration history | Historical context; materially stale |
| `Ironman1421/ddb-engineering` | Retired Spark pipeline, Buttondown path, acceptance harness, handoff log | Preserved engineering history; no deployment authority |
| `Ironman1421/davids-ai-command-center` | General multi-agent bootstrap and profiles | No DDB distribution implementation found |
| `Ironman1421/hermes-canonical` | Hermes profiles and general skills | Platform configuration, not the active bake |

Claude Cowork is not a repository and is no longer an authority for this
project. Useful ideas from old conversations must be deliberately reconstructed
in version-controlled specs, code, and tests before use.

## Known ownership gaps

- The external X poster referenced by `BAKE.md` is not in any accessible DDB or
  command-center repository; its last known design context lived in Claude
  Cowork, which is retired for this project.
- Social analytics now have a checked-in schema, but no live ledger, automated
  snapshots, or weekly scorecard.
- Branch protection and workflow bypass ownership are not documented as code.
- Reader-submission storage has no privacy owner or retention policy.
- YouTube, TikTok, Instagram, and LinkedIn adapters do not yet have repositories,
  credentials boundaries, acceptance tests, or named operators.

New operational components must have a repository, named owner, on-call/failure
path, secret boundary, idempotency contract, metrics, and a tested disable switch
before they become unattended production dependencies.
