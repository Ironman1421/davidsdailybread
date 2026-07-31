# Canonical X broadcast adapter runbook

Status: implementation ready, production disabled
Owner: David Friedhof
Runtime: the `x-broadcast` job in `.github/workflows/ddb-bake.yml`
Failure surface: the Daily bake run in GitHub Actions

## Scope and non-scope

The adapter publishes at most one canonical link broadcast for a newly
published morning or evening edition. Its source is the exact matching entry in
`archive.json`: date, slot, file, and lead must all agree. The post shape is:

```text
Morning edition: {exact archive lead}

Read the full briefing: https://davidsdailybread.com/editions/{editionId}.html
```

The evening label is `Evening edition`. The text is never truncated or model
rewritten. Backfills are not posted. Replies, mentions, hashtags, source cards,
likes, follows, reposts, quote posts, trends, media, editing, and deletion are
outside this adapter and receive no credential path.

The implementation uses only the official X API v2. X documents `POST
/2/tweets` for creation, user-context authentication, `GET /2/tweets/{id}` for
read-back, weighted character counting, rate-limit headers, and error classes:

- [Create a Post](https://docs.x.com/x-api/posts/create-post)
- [Get Post by ID](https://docs.x.com/x-api/posts/get-post-by-id)
- [Get a user's Posts](https://docs.x.com/x-api/users/get-posts)
- [Counting characters](https://docs.x.com/fundamentals/counting-characters)
- [Rate limits](https://docs.x.com/x-api/fundamentals/rate-limits)
- [Response codes and errors](https://docs.x.com/x-api/fundamentals/response-codes-and-errors)
- [Automation rules](https://help.x.com/en/rules-and-policies/x-automation)
- [Authenticity policy](https://help.x.com/en/rules-and-policies/authenticity)

Recheck those primary sources during every material provider upgrade.

## Authority and credential boundary

The untrusted editorial session and the canonical site publisher never receive
X credentials. A successful `bake` job hands only its resolved date, slot, and
mode to a separate `x-broadcast` job on a fresh runner. That job checks out
`main` with persisted credentials disabled and has only `contents: read` and
`actions: read`. X secrets are exposed only to its single provider step through
the protected `x-broadcast-production` GitHub environment.

The environment owns four OAuth 1.0a user-context secrets for an X app with
read and write Post permission, authorized only by `@DavidDailyBread`:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

Repository or environment variables are non-secret controls:

- `X_EXPECTED_USER_ID`: the numeric user ID read from X, never guessed;
- `X_EXPECTED_USERNAME`: exactly `DavidDailyBread`;
- `DDB_X_BROADCAST_ENABLED`: only `true` enables mutation;
- `DDB_X_BROADCAST_KILL_SWITCH`: only explicit `false` permits the live step;
  missing or any other value is treated as active and skips mutation.

Do not add X secrets at repository scope. Do not put credentials in URLs,
workflow inputs, artifacts, shell arguments, issue text, prompts, or logs.

## Provisioning and canary

Provisioning is an external owner action and was not performed by this change:

1. In X's developer console, create or select one app owned by David and grant
   the minimum user-context read/write Post permission. Do not grant Direct
   Message access. Record any plan price before accepting it; no spend is
   authorized by this repository.
2. Authorize only `@DavidDailyBread`. Obtain its numeric user ID through X's
   official interface or API and verify the username and ID together.
3. In GitHub, create the `x-broadcast-production` environment, restrict it to
   `main`, add the four secrets there, and add the four variables above. Start
   with `DDB_X_BROADCAST_ENABLED=false` and
   `DDB_X_BROADCAST_KILL_SWITCH=true`.
4. Run this offline preview and compare it byte for byte with the matching
   archive entry:

   ```bash
   python3 distribution/x_broadcast.py preview \
     --archive archive.json --date YYYY-MM-DD --slot morning
   ```

5. Exercise the workflow dry-run path with no X secrets exposed. Review the
   attempt artifact, confirm `mutationAttempts` is zero, then have a reviewer
   change the kill switch to `false`. Keep enablement `false` until the next
   intended live edition.
6. For the first live edition only, set enablement to `true`, watch the run, and
   independently open the provider receipt URL. Confirm the text, author,
   expanded canonical URL, and archive entry. If any differ, set the kill switch
   immediately.

The adapter remains disabled until all six steps are complete. Enabling it is
authorization for canonical edition broadcasts only, not for any other X
action.

## Idempotency and receipts

The key is `ddb:x:canonical:{editionId}:v1`. Before mutation the job checks:

1. the committed bootstrap and reconciliation state at
   `distribution/x-broadcast-state.json`;
2. non-expired GitHub Actions artifacts named
   `x-broadcast-receipt-{editionId}` or
   `x-broadcast-reservation-{editionId}`;
3. the authenticated account's latest 100 original Posts, read through X's
   official user-Posts endpoint and matched on author, complete non-URL text,
   and expanded canonical URL.

The manual recovery post for `2026-07-31-morning` is recorded with its actual
provider ID and URL and no invented publication time. The cutover watermark
refuses that edition and everything earlier. The next eligible edition is
`2026-07-31-evening`.

A successful create is not success until a provider read-back proves the post
ID, configured author ID, non-URL text, canonical expanded URL, and provider
publication time. Before X credentials are loaded, the workflow must first
upload a durable reservation artifact; failure to upload it stops the job
before mutation. The job later uploads a blocking provider receipt. A timeout
or 5xx after the POST is ambiguous and is never retried automatically; it also
writes a blocking `needs_reconciliation` receipt so a rerun cannot duplicate a
post that may exist. Attempts and receipts are retained for 90 days. Existing
edition refusal in the bake is the historical backstop after artifact expiry.
The provider-timeline preflight is the duplicate backstop if a receipt artifact
upload itself failed. A recovered exact provider Post is recorded and no new
mutation occurs.

A reservation remains a block even when a run crashes before posting or X
returns a definite non-mutation error. Reconcile through X's official API. If
no post exists, clear the reservation artifact ID only through the reviewed
`clearedRemoteArtifactIds` process below. This deliberate friction prevents a
blind retry from turning an uncertain run into a duplicate.

If an ambiguous receipt exists, inspect X manually. If the post exists, retain
the block and record the provider URL in the distribution ledger. If X and its
official API both prove no post exists, clear only that artifact ID by a
reviewed pull request adding it to `clearedRemoteArtifactIds`. Include the run
URL and evidence in the PR. Never delete an artifact or receipt merely to force
a retry.

## Retry and failure behavior

Read-only identity/read-back calls retry transient network, 429, and 5xx errors
at most three times with bounded exponential delay and jitter. A POST retries
only an explicit 429 rejection. It does not retry a timeout, network loss, or
5xx because delivery is ambiguous. Authentication and policy responses 401 and
403 are permanent and never retry.

A broadcast failure happens after the canonical site push and cannot roll it
back or delay it. The Actions run fails visibly after uploading the redacted
attempt and any blocking receipt. Provider bodies and authorization values are
not stored. Logs and attempt errors redact configured secret values.

## Emergency disable and credential incident

1. Set `DDB_X_BROADCAST_KILL_SWITCH=true` in the protected environment. The
   kill switch is checked before credential loading or provider access.
2. Disable the X app or revoke its access tokens in X's developer console.
3. Preserve the workflow run URL, attempt artifact, receipt artifact, edition
   ID, commit SHA, and any provider post URL.
4. Rotate all four environment secrets. Never commit replacements.
5. Determine whether a post exists before any retry. Add a regression test for
   the failure mode and merge a reviewed forward fix before reenabling.

Keep GitHub Actions failure notifications enabled for the repository owner.
No external monitoring destination has been provisioned; adding one is a
separate decision and credential boundary.
