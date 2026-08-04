# X Monitor discovery bridge

Status: approved and connected for daily evening discovery

Owner system: X Manager, Tools and Workflows

Consumer: the David's Daily Bread evening bake

## Purpose

The bridge gives the evening Field Guide a durable, cloud-hosted discovery
signal from X without giving the editorial session an X credential. It remains
a lead generator only. Every published tool and workflow still needs the
independent factual and trend evidence required by `BAKE.md`.

## Runtime flow

1. An active daily evening bake requests `/api/trends` from the private X
   Manager site. X Manager applies its own daily cooldown, per-run cap, monthly
   read ceiling, duplicate-run reservation, and durable D1 storage.
2. The bake requests `/api/discovery-export`, validates the
   `x-monitor-discovery-v1` shape, and saves it only in the runner's temporary
   directory.
3. The editorial prompt points to that temporary snapshot. The machine
   credential is not present in the editorial step, and the X bearer token
   never leaves X Manager.
4. The editor may investigate candidates, but an X URL is never accepted as
   the factual source or the citable trend source in published content.

The GitHub backup clock runs in the cloud, so this path does not depend on the
Spark or any personal computer remaining awake. A manual daily evening dispatch
uses the same path. Morning and backfill bakes do not request X Monitor.

## Authentication boundary

The private Sites machine credential is stored as the GitHub Actions secret
`X_MONITOR_SITES_BYPASS_TOKEN`. It is loaded only by the snapshot preparation
step. Rotate it from the X Manager Sites control plane and replace the GitHub
secret together; generating a new token invalidates the previous token.

## Failure behavior

The bridge fails open for editorial discovery. A missing credential, network
failure, unavailable refresh, empty result, or invalid export produces a small
local fallback snapshot and a workflow warning. The bake then uses its normal
Hacker News, GitHub Trending, Product Hunt, Reddit, press, official product,
and tutorial sources. X Monitor cannot block an otherwise valid edition.

The X Manager budget and cooldown remain authoritative. The bake must never
add a force-refresh bypass or receive the X bearer token.

## Verification

- Confirm the workflow log reports the number of tool and workflow candidates.
- Confirm the editorial step receives only the temporary snapshot path.
- Confirm published `url` and `trend_url` values are independently fetched,
  non-X sources that satisfy `BAKE.md`.
- Confirm X Manager retains the monitor run and candidates across a page
  refresh.
