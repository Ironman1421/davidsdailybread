# DDB-PC-028 evening broadcast audit, 2026-08-11

Status: diagnosis complete; recovery not authorized or executed  
Scope: read-only evidence for `2026-08-09-evening`  
Account: `@DavidDailyBread`  
Canonical broadcaster: Spark `daicc-ddb-autopost`

## Conclusion

`2026-08-09-evening` was not broadcast because it was published on August 10
as a prior-day backfill, while both available canonical X paths intentionally
exclude that case:

- the repository `x-broadcast` job runs only when the bake mode is `daily`;
- Spark's live `ddb_autopost.py` path always selects the host's current date,
  and its `--date` override is dry-run-only.

This was a fail-closed scope decision, not a failed X send. Neither path made a
provider mutation attempt for the August 9 evening backfill.

## Immutable evidence

### Canonical publication

- Daily bake run
  [31424346810](https://github.com/Ironman1421/davidsdailybread/actions/runs/31424346810)
  resolved `2026-08-09 evening (backfill)` from protected authorization base
  `5b2fc4df86638a6c1ca20b722159fd1c35bf4f8e`.
- The publisher created exact main commit
  `69c544c4f4f91f2ac133587152d567983f3aded1` at
  `2026-08-10T19:49:15Z` and verified the immutable public URL.
- The run's Canonical X broadcast job `93577759693` was skipped. The run has
  no X attempt or receipt artifact.
- The workflow at the captured base requires
  `needs.prepare-reader-plan.outputs.mode == 'daily'` before starting the X
  job. The backfill therefore stopped at the job boundary, before environment
  controls, credentials, or provider access.

### Spark selection boundary

- Private command-center main remains exact commit
  `1335841e9bda3c38e67c2c7b53ba996935942a83`, the same source previously
  installed and verified on Spark.
- The reviewed live implementation SHA-256 is
  `d49983234c1c8c3293144a6a2758e5600a0d00cba4003ef7d54cb8553521644a`.
- Its live poll uses `date.today()`, looks up only `(today, morning)` and
  `(today, evening)`, and rejects `--date` unless `--dry-run` is also present.
- Its timer fires at `:00` and `:30` during the Pacific morning and evening
  windows. It contains no live prior-day or latest-edition fallback.

### Official X read-back

- A read-only exact-title search on the signed-in correct account returned no
  result for the August 9 evening lead containing `myNoise`.
- The adjacent exact August 10 morning post is
  `https://x.com/DavidDailyBread/status/2086935643888996644`. Official X shows
  `3:00 PM · Aug 10, 2026`.
- That post uses Spark's deterministic August 10 morning opener, `First loaf
  of the day`, and its timestamp is exactly the first Pacific evening timer
  tick. This is consistent with Spark selecting August 10 at 3:00 PM: it found
  the newly published August 10 morning edition and could not select the prior
  day's August 9 evening edition.

## Causal sequence

1. The August 9 evening edition did not exist during its normal August 9
   broadcast window.
2. David later authorized canonical site publication of that named edition.
3. The August 10 manual Daily bake correctly classified it as `backfill`.
4. The repository X job skipped by its explicit daily-only condition.
5. Spark's next live poll selected August 10, not August 9. It posted the
   available August 10 morning edition at 3:00 PM and had no August 10 evening
   edition to post.
6. No mechanism had authority to create a prior-day X backfill, so the August
   9 evening edition remained absent from X.

## Ruled out

- **Immutable-link regression:** the installed reviewed source already derives
  an exact dated URL, and later Spark posts use exact edition destinations.
- **X API rejection or ambiguous delivery:** the repository X job never
  started, there is no backfill X attempt artifact, and official X contains no
  matching post.
- **Duplicate, length, or content gate:** Spark never selected the August 9
  entry on August 10, so edition-specific gates were not reached.
- **Broadcaster migration:** Spark remained canonical; the repository adapter
  remained its disabled replacement path.

## Evidence limitation

The current Spark journal was not re-read during this audit because the Mac's
existing Tailscale backend was stopped: mDNS did not resolve and the stored
Tailscale address timed out. The audit did not start Tailscale or change any
local or remote network state. This prevents a fresh journal corroboration but
does not change the causal finding, which is established by the captured
workflow condition, exact private source, publication mode, artifact absence,
and official X timestamps.

## Proposed recovery boundary

Do not replay `2026-08-09-evening`. A late historical post is outside both
standing broadcaster contracts, would require a new one-item public-action
exception, and is unnecessary to test the normal path.

The smallest safe recovery is:

1. Keep DDB-PC-028 X readiness and the campaign clock blocked.
2. Make no broadcaster, timer, credential, provider, workflow, environment, or
   account change.
3. Let the next ordinary same-day evening edition use the already authorized
   canonical publication and Spark broadcast path.
4. After that edition is due, perform a separately authorized read-only check
   for one `@DavidDailyBread` post whose expanded URL exactly equals that
   edition's immutable URL.
5. If the exact post exists, refresh the X readiness receipt against the new
   latest due evening edition. This does not activate the campaign.
6. If it does not exist, stop. Reconnect to Spark only under a separately
   scoped read-only observation, preserve its timer and journal evidence, and
   propose any repair for separate implementation and activation approval.

A manual August 9 X post, an automated backfill feature, or enabling the
repository replacement broadcaster are explicitly outside this recovery
boundary. Each would require a new exact approval and duplicate-prevention
review.

## Actions not performed

No post, reply, replay, provider write API call, account change,
credential access or change, broadcaster or timer change, service operation,
workflow dispatch, deployment, spend, campaign activation, or campaign-clock
start occurred.
