# DDB-PC-013 checkout reconciliation, 2026-08-04

Status: complete

Owner and approver: David Friedhof

Approval evidence: task message, "Approve DDB-PC-013: preserve and reconcile
the dirty Spark and local checkouts without deleting user-owned work. Do not
merge or deploy."

Audited method: the fresh-staging checkout procedure and verification gates in
`docs/PRODUCTION_HOST_REPOSITORY_HYGIENE_AUDIT_2026-08-02.md` at preserved
commit `f7f076c5a480e2c19ef6dd3ec12bdf5fb4661859`.

## Local checkout preservation

Four dirty local worktrees were preserved without modifying, resetting, or
deleting their source directories:

| Worktree | Dirty paths | Disposition |
| --- | ---: | --- |
| Primary Documents checkout on `codex/founder-operating-doctrine` | 76 | Full working-tree snapshot plus tracked patch and untracked manifest |
| `codex/dual-architecture-tests` worktree | 7 | Full working-tree snapshot plus tracked patch and untracked manifest |
| Detached Codex worktree `0b08` | 62 | Full working-tree snapshot plus tracked patch and untracked manifest |
| `codex/evening-ui-options` worktree | 27 | Full working-tree snapshot plus tracked patch and untracked manifest |

The recovery set is:

`/Users/davidfriedhof/Documents/DDB-preservation/DDB-PC-013/20260804T163244Z`

It is 18 MB, includes a repository-wide all-refs Git bundle and the complete
worktree inventory, and has a verified `SHA256SUMS` manifest with SHA-256:

`88c226d31c56f55803095cee3ff0447957529bc3d776730253d9c7911a8941a3`

Clean local worktrees remain in place and are represented by their Git refs in
the bundle. No pre-existing local branch, worktree, untracked file, or user
artifact was deleted.

While reconciliation was in progress, the separate X-profile task added a
tracked `og-card.png` change and untracked `x-banner.png`, increasing the
primary checkout to 78 dirty paths. Those later bytes and the then-current Git
refs were captured without interruption in a supplemental 9.2 MB recovery set:

`/Users/davidfriedhof/Documents/DDB-preservation/DDB-PC-013/20260804T165400Z-supplemental-primary`

Its verified `SHA256SUMS` manifest has SHA-256:

`5afa8665ac5d93fa591e36ac8fe34cf6f0e25a78ab9f6bdb74323d48d47dca3b`

## Spark preservation and canonical source

The Spark recovery set is:

`/home/david/.local/state/ddb-pc-013/20260804T163244Z`

It is 84 MB and contains full restricted working-tree snapshots, tracked
patches, untracked manifests, and Git bundles for:

- the 68-path dirty `/home/david/daicc-phase1` checkout;
- the 11-path dirty historical DDB scratch mirror; and
- the clean but stale `/home/david/hq/daily-bread` public mirror.

Its verified `SHA256SUMS` manifest has SHA-256:

`bc65b3003cf5b14e4d98a321113a30c2ff951b543621c42760d259aae1828dd2`

The original dirty checkout also remains intact at
`/home/david/daicc-phase1.preserved-ddb-pc-013-20260804T163244Z`. Nothing was
deleted or reset.

The canonical private checkout at `/home/david/daicc-phase1` is now a fresh
`main` checkout at
`13334a89112cc9dd084ba5168d836bed4e8ef4c8`, exactly equal to private remote
`main`, with zero Git-status paths. A total of 1,737 nonconflicting runtime-only
files were carried forward and locally excluded from Git; any path that became
tracked in private `main` was taken from the reviewed remote source instead.

## Runtime continuity

The active Telegram bridge contained a local credential-path correction that
was not yet in private `main`. Its reviewed bytes were preserved as a locally
excluded, tripwire-covered runtime file, and a systemd drop-in points the
existing service to it. The bridge was not restarted: PID `1257868` remained
active before and after checkout reconciliation.

Private `main` tracks `scripts/ddb-autopost.sh` without an executable bit even
though the production unit invokes it. A local systemd drop-in now runs that
exact tracked script through `/usr/bin/bash`; no posting logic or schedule
changed, and the service was not started or restarted.

The reblessed fleet tripwire covers 50 classified source, runtime, secret, unit,
and drop-in files. The immediate ordinary tripwire check and full manifest
verification passed.

## Source, service, and no-op verification

- all 23 audited DDB config, script, service, and timer files match private
  source `13334a89112cc9dd084ba5168d836bed4e8ef4c8` by independent Git blob hash;
- `systemd-analyze --user verify` passes for the DDB fleet, the effective
  autopost unit, and the Telegram bridge unit;
- 44 private-repository tests, the guarded X publisher's 12 offline self-tests,
  the shared OAuth/parser self-test, and shell syntax checks pass;
- 29 targeted public-repository governance, intake-pause, renderer-security,
  and brand-cadence tests pass on the Mac;
- exact-edition trigger canaries for `2026-08-04-morning` and
  `2026-08-03-evening` report successful no-ops;
- exact-edition watchdog canaries for the same editions report
  `exact_edition_present` and send no alert;
- the Telegram bridge is active on its unchanged PID, all DDB services retain
  successful last results, and there are zero failed user units;
- the former Counter timer remains disabled and inactive; and
- no public repository merge, site deployment, workflow dispatch, Telegram
  alert, X post, newsletter action, reader-intake change, provider provisioning,
  credential change, network change, or service restart occurred.

## Observation and sealed post-state

The two ordinary scheduled tripwire runs required after the reviewed rebaseline
completed successfully at `2026-08-04T09:52:16-07:00` and
`2026-08-04T10:02:21-07:00`. Both returned result `success` with exit status 0,
left no drift signature, and retained a valid 50-entry manifest.

The final restricted post-state is sealed at:

`/home/david/.local/state/ddb-pc-013/20260804T170236Z-post`

It contains the canonical and remote heads, empty Git status, independent
23-file source/deployment hashes, effective drop-ins, service and timer state,
tripwire observation, systemd verification, and exact-edition no-op outputs.
Its verified `SHA256SUMS` manifest has SHA-256:

`f488557e74f5bd1d3e9cc424213bfce4dc9cbd55c30ac451ef8cf9d22df885c1`
