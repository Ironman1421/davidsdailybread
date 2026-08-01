# Production operations evidence, 2026-08-01

Status: recorded deployment observation
Owner: David Friedhof
Observer: Codex, using NVIDIA Sync's SSH identity over the Spark's verified
Tailscale address

This record supports the current operations claims in the product and
distribution specifications. It contains no credential values.

## Spark scheduling control plane

- Private repository PR
  [`Ironman1421/davids-ai-command-center#3`](https://github.com/Ironman1421/davids-ai-command-center/pull/3)
  passed 22 local contract tests and a Claude cross-model review, then merged as
  commit `c366130d7bd81cc3b63ddff33ae09d524e0c586b` at 17:13 UTC.
- The merged scripts and ten systemd unit files were copied through a private
  staging directory, matched against their local SHA-256 hashes, backed up per
  file, installed, and accepted by `systemd-analyze --user verify`.
- `daicc-ddb-counter-sync.timer`, both edition-trigger timers, and both watchdog
  timers are enabled. Their next schedules resolved as 04:30, 05:00, 07:15,
  15:30, and 18:00 Pacific, respectively. The legacy
  `daicc-nightly-dailybread.timer` remains disabled.
- A live Counter canary completed GitHub workflow run `30710011755` successfully
  and wrote an exact `2026-08-01` success marker. The installed morning trigger
  and watchdog then both returned exact-edition successful no-ops for the
  already-published August 1 morning edition.
- Past-edition checks for the July 31 evening slot also returned exact-edition
  no-ops. No test sent Telegram or dispatched an edition early.
- The dedicated GitHub and Telegram environment files were verified as mode
  `0600`, owned by `david:david`, without printing their contents.
- Deployment staging is
  `/home/david/ddb-resilient-staging-20260801T171604Z`; the recoverable per-file
  backup and deployment manifest are under
  `/home/david/backups/ddb-resilient-20260801T171604Z`.

## X ownership observation

- `daicc-ddb-autopost.timer` was both enabled and active on Spark.
- Its August 1 journal recorded one successful exact morning post at 07:10
  Pacific, followed by `already-posted` no-ops. The same runs reported the
  absent evening edition without substituting older content.
- The GitHub X broadcaster remains disabled and kill-switched. Therefore the
  Spark service is the one observed active canonical X lane. Enabling the GitHub
  lane requires a separate migration that disables Spark first.

## Connectivity observation

NVIDIA Sync's stored `spark-e1d1.local` route reported the Spark disconnected
because local mDNS was unavailable. Tailscale reported `spark-e1d1` online, and
NVIDIA Sync's existing SSH identity connected successfully over that verified
Tailscale route. The saved Sync route was not rewritten during this deployment.
