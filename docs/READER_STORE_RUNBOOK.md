# Private reader-store operator runbook

Status: local foundation implemented, deployment blocked

## Founder pause and authority boundary

New reader intake is paused. Local verification may continue, but no Supabase
account, project, resource, link, credential, remote migration, deployment,
canary, traffic, or activation is authorized. Do not link, migrate, deploy,
canary, or send site traffic unless David first records an explicit reversal in
the repository and the affected doctrine, specifications, contract, and tests
are reconciled.

The former technical launch gates below are retained as historical design
requirements. Satisfying either one does not authorize provisioning or
deployment.

## Former technical launch gates

Do not link, migrate, deploy, canary, or send site traffic until both of these
facts are real and independently verified:

1. a dedicated Supabase project exists solely for reader mail; and
2. a working privacy-contact address at the project domain exists and is shown
   in the form and public correction/removal instructions.

This repository deliberately contains neither a project reference nor a
privacy-contact value. Do not substitute the primary site database, a personal
address, a guessed address, or a placeholder. The current Google form/workflow
remains unchanged until the full cutover checklist is approved.

## Foundation inventory

- `supabase/config.toml`: Postgres 17 local stack, non-exposed
  `reader_private` schema, three JWT-free functions with their own application
  authentication, and private `bake-handoffs` bucket declaration.
- `supabase/migrations/20260731210001_reader_private_foundation.sql`: types,
  tables, constraints, indexes, forced RLS, execute-only database boundary,
  transactional lifecycle functions, retention function, and daily database
  retention schedule.
- `supabase/functions/reader-submit`: exact-origin public ingestion with
  Turnstile, consent, normalization, limits, one-time deletion token, and safe
  responses.
- `supabase/functions/reader-delete`: token-hash deletion for unpublished
  payloads and a publication-boundary response.
- `supabase/functions/reader-plan`: broker-authenticated reserve, authorize,
  finalize, release, private signed handoff, deletion, and cleanup operations.
- `supabase/tests/database`: pgTAP schema, privilege, lifecycle, retention, and
  idempotency checks.
- `supabase/tests/concurrency`: local Postgres locking and race checks.
- `supabase/functions/tests`: runtime-independent Edge validation tests.

The implementation was checked against the Supabase changelog and current
official guidance on 2026-07-31. Relevant sources are [API security](https://supabase.com/docs/guides/api/securing-your-api),
[custom schemas](https://supabase.com/docs/guides/api/using-custom-schemas),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[Edge database connections](https://supabase.com/docs/guides/functions/connect-to-postgres),
[CORS](https://supabase.com/docs/guides/functions/cors),
[function secrets](https://supabase.com/docs/guides/functions/secrets),
[function tests](https://supabase.com/docs/guides/functions/unit-test),
[Postgres SSL enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement),
[private buckets](https://supabase.com/docs/guides/storage/buckets/fundamentals),
[signed uploads](https://supabase.com/docs/reference/javascript/file-buckets-createsigneduploadurl),
[signed downloads](https://supabase.com/docs/reference/javascript/file-buckets-createsignedurl),
[local CLI workflow](https://supabase.com/docs/guides/local-development/cli-workflows),
and the [changelog](https://supabase.com/changelog.md).

## Local verification

Prerequisites are Node 22 or newer and a running Docker-compatible container
runtime. The local stack has development credentials, no TLS, and no rate
limiting; never expose it to another network.

From a clean checkout:

```sh
npm ci
npm exec -- supabase --version
npm exec -- supabase start
npm run supabase:reset
npm run test:reader-db
npm exec -- supabase db lint --local --schema reader_private --level error --fail-on error
npm exec -- supabase migration list --local
npm exec -- supabase db diff --local --schema reader_private
```

The version must be `2.111.0`. The final diff must be empty. Obtain the local
database URL with `npm exec -- supabase status -o env`, keep that output out of
logs, and run the concurrency suite only against a loopback host:

```sh
DDB_READER_TEST_DATABASE_URL="$DB_URL" npm run test:reader-concurrency
```

The concurrency test refuses any non-local hostname. Run the non-container
gates as well:

```sh
npm run test:reader-edge
npm run test:reader-types
npm run check:reader-format
npm run check:reader-lint
python3 -m pytest tests/test_reader_store_foundation.py -q
```

To serve Edge Functions locally, create an uncommitted login role that is a
member of `reader_edge`, is not superuser, and does not bypass RLS. Put its
pooled local URL and only synthetic local values in
`supabase/functions/.env.local`, which is gitignored. Set
`DDB_READER_DATABASE_SSL_MODE=disable` only for a URL whose hostname is
loopback (`localhost`, `127.0.0.0/8`, or `::1`); the function rejects this mode
for every other hostname. Leave `DDB_READER_DATABASE_SSL_CA` unset in this
local-only mode. Never use the local `postgres` administrator URL as
`DDB_READER_DATABASE_URL` for a function canary. Delete the temporary login
after the test.

If Docker/Postgres is unavailable, the TypeScript, lint, formatting, Python,
and static security gates remain useful, but they do not replace `db reset`,
pgTAP, database lint, concurrency, or advisors. Record those database checks as
not run, not passed.

### Verification record for this foundation PR

Worktree record: on 2026-07-31 the non-container checks passed locally: Edge
unit tests, Deno type checking, Deno format/lint, reader-store Python static
gates, product-contract tests, JSON parsing, `git diff --check`, and `npm
audit`. Supabase CLI 2.111.0 was invoked, but `supabase start` stopped before
any container or database change because neither Docker nor Podman exists on
the host. This worktree therefore does not claim local migration replay,
pgTAP, database lint, live `FOR UPDATE SKIP LOCKED` concurrency, local Storage
integration, or local Edge-to-Postgres integration.

Authoritative CI record: the PR-event Merge gate for exact head
`d7086e735a2d8a4638853810f69c396c03a1e3ae` passed on 2026-07-31. That isolated
GitHub runner completed a clean migration replay, pgTAP 91/91, database lint,
and the concurrency/locking suite, in addition to 57 repository tests and the
Edge/source gates. The PR-event CodeQL run also passed for both Python and
JavaScript/TypeScript. A superseded duplicate push gate for the same SHA was
cancelled before its database work; it is not evidence of failure. These are
CI results for that exact SHA, not local worktree results and not results for
later amendments. Every amended head must pass a fresh PR-event Merge gate and
CodeQL before integration.

Security and performance advisors remain unrun because there is no dedicated
project and this lane must not connect to another project. Local Storage and
Edge-to-Postgres integration also remain unverified. Those checks remain
mandatory before any canary or cutover.

## Secret and configuration inventory

| Name | Kind and consumer | Required handling |
| --- | --- | --- |
| `DDB_READER_DATABASE_URL` | Secret pooled Postgres URL used by all three functions | Login must only inherit `reader_edge`; use the dashboard-provided transaction pooler hostname; rotate on exposure |
| `DDB_READER_DATABASE_SSL_MODE` | Non-secret function config | Use `verify-full` remotely; `disable` is accepted only for loopback development URLs |
| `DDB_READER_DATABASE_SSL_CA` | Secret-store PEM CA certificate used by the Postgres client | Required remotely; download it from the dedicated project's Database SSL settings, preserve the PEM newlines, never commit or log it, and update it when the project CA changes |
| `DDB_READER_BROKER_TOKEN` | Secret bearer token used by trusted workflow steps and `reader-plan` | 32 to 256 random characters; rotate on exposure and at least every 180 days |
| `DDB_TURNSTILE_SECRET_KEY` | Secret used only by `reader-submit` | Scope to the production widget/hostnames; rotate on exposure |
| `DDB_READER_STORAGE_SECRET_KEY` | Dedicated-project Supabase secret key used only by handoff code | Never expose to browsers, logs, artifacts, or author/model processes; rotate on exposure |
| `DDB_READER_SUBMIT_ENABLED` | Ingestion kill switch | Only the exact string `true` enables ingestion |
| `DDB_READER_DELETE_ENABLED` | Deletion kill switch | Keep enabled during ordinary ingestion shutdowns |
| `DDB_READER_PLAN_ENABLED` | Plan and handoff kill switch | Only the exact string `true` enables broker operations |
| `SUPABASE_URL` | Platform-provided non-secret project URL | Verify it belongs to the dedicated project |

Do not use legacy `SUPABASE_SERVICE_ROLE_KEY` in this implementation. Do not
put secret values on a command line, in shell history, in an Actions output, or
in a repository `.env` file. Use a protected temporary env file outside the
checkout when the later operator runs `supabase secrets set --env-file`, then
securely remove it.

## Frozen dedicated-project migration

These steps are historical future-operator notes, not authorization to perform
them. They remain frozen until David explicitly reverses the pause.

1. Verify the project owner, project reference, Postgres major version 17,
   isolation purpose, backup policy, region, and privacy-contact launch gate.
2. Create a random-password login role with `NOSUPERUSER NOCREATEDB
   NOCREATEROLE NOREPLICATION NOBYPASSRLS`; grant it membership in the
   migration-owned non-login `reader_edge` role. Never grant it table access.
3. Link only after reading the project reference back from the dedicated
   project: `npm exec -- supabase link --project-ref "$PROJECT_REF"`.
4. Review `npm exec -- supabase db push --linked --dry-run`; it must list only
   the reader foundation migration. Apply with
   `npm exec -- supabase db push --linked` in the approved window.
5. Create the declared private bucket with
   `npm exec -- supabase seed buckets --linked`. Verify it is private, capped
   at 10 MiB, and accepts only the two contract MIME types.
6. Download the dedicated project's CA certificate from Database SSL settings.
   Set `DDB_READER_DATABASE_SSL_MODE=verify-full`, and set the complete PEM as
   `DDB_READER_DATABASE_SSL_CA` with the other secrets through an
   out-of-repository protected env file. Leave all three enable switches absent
   or `false`. The runtime must reject a missing or malformed CA instead of
   weakening certificate or hostname verification.
7. Deploy exactly `reader-submit`, `reader-delete`, and `reader-plan` with the
   checked-in config. Do not use `--prune` during the first deployment.
8. Run pgTAP, database lint, security advisors, performance advisors, and
   `npm exec -- supabase db diff --linked --schema reader_private`. Require an
   empty diff and retain redacted results.

The migration intentionally does not create a login password or a real secret.
It creates only the non-login privilege role. The Edge connection verifies at
runtime that its login is a non-superuser member of that role and lacks
`BYPASSRLS`.

## Frozen canary sequence

Do not run this sequence while the founder pause is active. It is retained only
to preserve the reviewed design for a possible future decision.

Keep the public form on its current path throughout the canary.

1. With every switch false, prove all functions return `service_disabled` to
   otherwise valid authenticated requests.
2. Enable deletion and submission for a controlled test window. Submit only
   synthetic text through the real allowed origin and a correctly configured
   Turnstile action. Verify the response returns one deletion token and no
   table, queue, hash, or neighboring-row data.
3. Verify `anon`, `authenticated`, and the Edge login cannot select, insert,
   update, or delete any private table or invoke a non-allowlisted routine.
4. Submit two synthetic items per kind with known times. Prove oldest-first
   selection, at most one per kind, same-edition retry, lease expiry, release,
   reserved deletion, authorize/delete race behavior, digest binding, exact
   edition/SHA finalization, and idempotent finalization.
5. Upload one synthetic bundle through the signed upload capability with cache
   control `0` and no upsert. Prove the author cannot list/read, the publisher
   URL expires after 60 seconds, the exact object is deleted after use, and an
   abandoned object is removed before six hours.
6. Run `reader_private.run_retention` against synthetic aged rows. Verify 90,
   30, 30, and 365-day behavior without breaking current non-personal receipts.
7. Review Function, Postgres, Storage, and gateway logs. They may contain only
   opaque request IDs, safe event codes, opaque object IDs, and state
   transitions. Search explicitly for every synthetic body, byline, deletion
   token, signed URL, broker token, and bundle digest; all searches must be
   empty where the value is secret or reader-authored.
8. Configure the handoff cleanup scheduler to call the authenticated
   `cleanup-handoffs` operation at least hourly. Store its broker credential in
   the platform secret store, not SQL text, and alert on a missed six-hour SLA.
9. Keep the switches false after the canary. Public cutover still requires the
   verified privacy contact, form copy, maintenance window, and separate
   workflow integration review.

## Retention operations

The migration schedules `reader_private.run_retention()` daily at 04:17 UTC via
the named pg_cron job `ddb-reader-retention-daily`. Monitor `cron.job_run_details`
for failure, but do not expose its unrestricted rows to browser roles. The job:

- expires and erases pending payloads after 90 days;
- erases rejected and published private payloads after 30 days;
- removes terminal private receipts after 365 days; and
- emits only a non-personal completion event.

Handoff cleanup is deliberately an authenticated Storage operation because the
Storage schema is not an application-write API. Schedule `cleanup-handoffs`
outside the migration after the broker secret exists. Alert if the job fails or
the oldest object approaches six hours. Never delete Storage metadata directly
with SQL.

## Kill switch and incident handling

For suspected abuse, reader-data exposure, or unsafe publishing state:

1. set `DDB_READER_SUBMIT_ENABLED=false` and
   `DDB_READER_PLAN_ENABLED=false` immediately;
2. keep `DDB_READER_DELETE_ENABLED=true` unless the deletion endpoint itself is
   compromised;
3. stop the affected scheduled workflow without deleting evidence;
4. preserve only opaque IDs, timestamps, run URL, edition ID, and commit SHA;
5. rotate the affected broker, database, Storage, or Turnstile secret outside
   git; and
6. reconcile every expired `publishing` batch against remote `main` before any
   release. Never release a publishing batch merely because its lease expired.

An absent switch fails closed. Do not work around the kill switch with direct
table writes or a service-role browser client.

## Rollback and recovery

Before cutover, rollback means leaving all switches false, reverting the caller
through a normal pull request, and leaving the inert dedicated schema available
for diagnosis. Do not republish the Google Sheet or recommit a reader queue.

After any reader data exists, do not apply a destructive down migration. Fix
forward, restore from the dedicated-project backup if necessary, and preserve
deletion/retention duties. Dropping the schema, bucket, cron job, role, or
project requires a separately reviewed data-disposition plan and explicit
operator approval. A database rollback cannot retract a public edition or git
history.

For a failed migration before data collection:

1. keep the switches false;
2. capture the migration error and current migration list;
3. restore the empty dedicated project from its pre-migration snapshot or
   replace it with another verified empty dedicated project;
4. correct the forward migration on a new branch; and
5. repeat the complete local and canary verification.

Never run `db reset --linked`, never test against production data, and never
repair migration history merely to make the list appear green.
