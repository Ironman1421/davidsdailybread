# Audience measurement activation and monthly-close runbook

Status: Cloudflare local implementation and unprovisioned canary plan prepared;
all external actions and production activation blocked

Owner and final decision-maker: David Friedhof

Last reconciled: 2026-07-31

## Purpose

This runbook describes how a future approved operator could canary, activate,
close, and stop the first-1,000 measurement system defined in
`docs/AUDIENCE_MEASUREMENT_SPEC.md`. Cloudflare Workers + D1 is selected for
local implementation only. This runbook does not approve an endpoint, account,
operator, credential, DNS change, provider terms, privacy notice, production
script, spend, provisioning, deployment, or canary execution.

The repository remains `implementation-selected`, not installed or measuring.
The checked-in browser configuration
is disabled and has no endpoint. No public template imports the adapter.
`operations/audience-measurement.contract.json` is the machine-readable current
operating state and records each activation gate as closed.

## Prepared local components

| Boundary | Repository artifact | Data behavior |
|---|---|---|
| Browser qualifier | `audience/qualifier.mjs` | Keeps month-scoped visit days, the first two engaged sessions, bounded unfinished active time, and sent-transition state locally. |
| Disabled browser boundary | `audience/browser-adapter.mjs` and `audience/browser-adapter.config.json` | Defaults off; has no endpoint or built-in transport; counts only visible, recently active time; supports the closed action allowlist and local opt-out erasure. |
| Transition contract | `audience/transition.schema.json` | Permits only version, definition version, calendar month, transition, and month token. |
| Collector core | `audience/collector.mjs` | Hashes the token with its month so even accidental token reuse cannot link months, enforces ordered transitions on distinct server receipt days, applies bot and registration gates, and is idempotent. It has no transport, provider, storage, or logging implementation. |
| Aggregate close | `audience/reporting.mjs` | Produces monthly counts and mandatory limitations without raw tokens, token digests, visitor rows, or event rows, then provides an empty state for an approved purge operation. |
| Cloudflare canary-only wrapper | `audience/cloudflare/worker.mjs` and `audience/cloudflare/schema.sql` | Enforces exact HTTP, canary-secret, Pacific receipt-date, rate, bot, conditional-transition, aggregate, and purge boundaries without a production mode. |
| Unprovisioned plan | `audience/cloudflare/canary-plan.json` and `wrangler.unprovisioned.jsonc` | Records the approved plan while keeping every account, identifier, endpoint, secret, route, trigger, execution, deployment, and activation field absent or disabled. |
| Public aggregate record | `audience/monthly-ledger.json` | Remains empty and not measured until approved production evidence exists. |

Passing local contracts proves the shape and behavior of these pure components.
It does not prove that a future edge, endpoint, datastore, logging stack, or
deployment preserves the same guarantees.

## Founder activation record required

Before any external action, one reviewed repository change must record all of
the following with David's explicit approval:

`docs/AUDIENCE_ACTIVATION_DECISION_TEMPLATE.md` is the unapproved worksheet for
that record.

1. the endpoint technology, operator, repository, hosting account, and failure
   owner;
2. the exact approved origin and route, with no credential or secret committed;
3. the approved monthly cost ceiling, including `$0` when applicable;
4. the reader-visible privacy explanation and the exact opt-out control;
5. browser-token lifetime, collector-row deletion deadline of no more than 35
   days, aggregate retention, and verified deletion owner;
   the token generator must use at least 128 bits of cryptographic randomness
   and may not derive input from browser, device, or network characteristics;
6. transient IP handling at the CDN, host, application, logs, errors, traces,
   backups, rate limiter, and bot-control boundary, with retained raw IP
   disabled;
7. the known-bot, preview, render, synthetic-monitor, and David/internal-traffic
   exclusions;
8. credential ownership, least-privilege access, monitoring, incident path,
   kill switch, and complete removal procedure;
9. the approved implementation diff for every canonical page class; and
10. David's authorization to provision, canary, and later enable production
    collection as separate recorded decisions.

An approval of the architecture is not an approval to provision it. A canary
approval is not an approval to begin the official baseline.

## Endpoint wrapper contract

The local Cloudflare wrapper, before any separately approved canary, must:

- accept only `POST` requests with the exact transition JSON schema and a
  bounded body size;
- reject query parameters, form bodies, arbitrary properties, invalid content
  types, and malformed encodings before application logging;
- derive `receivedDate` at the trusted server boundary in
  `America/Los_Angeles`; never accept a client-supplied receipt date;
- compute `registrationAllowed` and `knownBot` outside the envelope, using
  request data only transiently and without retaining raw IP or a device
  fingerprint;
- avoid logging request bodies, raw month tokens, token digests, headers,
  referrers, full URLs, or rejected payloads;
- retain only the collector fields required to deduplicate the three monthly
  transitions and operational aggregate error counters;
- return only a bounded decision needed for idempotent client retry; and
- fail closed when storage, clock, bot controls, schema validation, or the
  deletion job is unhealthy.

The wrapper must not trust a `qualified` envelope as evidence by itself. The
collector state machine must observe first-seen, returned, and qualified on
ordered, distinct server receipt days.

## Planned canary sequence, not authorized to run

The sequence below is the approved unprovisioned plan. It may run only after
David separately authorizes provisioning and canary execution for a named
reviewed commit, account, operator, endpoint, and evidence boundary:

1. Keep the public adapter disabled and confirm the kill switch prevents every
   delivery attempt.
2. Deploy the endpoint wrapper without integrating the site. Confirm access,
   application, error, trace, firewall, and provider logs contain no forbidden
   request data.
3. Exercise the valid fixture and adversarial cases: extra fields, free text,
   invalid tokens, unknown transitions, direct qualification, same-day replay,
   out-of-order delivery, duplicate delivery, cross-month delivery, known bots,
   blocked registration, excessive body size, and wrong content type.
4. Confirm accepted and duplicate responses permit retry without double count;
   rejected responses remain pending locally.
5. Verify month rollover at both sides of the Pacific-time boundary, including
   daylight-saving behavior.
6. Verify hidden tabs and tabs idle for more than 30 seconds add no active time;
   verify two separate engaged sessions and three separate visit days are
   required locally.
7. Verify the opt-out prevents initialization, removes both local qualifier and
   session state, and produces no delivery. Verify opting back in creates a new
   month-scoped token rather than restoring old state.
8. Verify synthetic monitors, previews, David/internal traffic, and known bots
   do not enter visitor aggregates. Record exclusion counts only if the
   approved boundary exposes safe aggregates; otherwise keep them `null`.
9. Generate a `partial` canary report, confirm it contains no token, digest,
   visitor row, event row, URL, or reader content, and verify its source receipt
   from aggregate counts.
10. Exercise the purge and deletion path, then inspect primary storage, logs,
    traces, backups, and provider consoles for expired visitor-level state.
11. Test the kill switch and full removal procedure. The canary is unsuccessful
    if disabling requires a code emergency or leaves collection active on any
    canonical surface.

Canary evidence is diagnostic only. It never enters a `complete` monthly record
and never counts toward the milestone.

## Baseline start gate

David must separately approve production activation after the canary. Begin the
first possible baseline only at 00:00 on the first calendar day of a month in
`America/Los_Angeles`. If activation, coverage, exclusions, notice, opt-out, or
processing begins late, the month is `partial`.

Before activation, verify coverage for both current-edition templates, every
archived edition class, the archive, tools and workflows libraries, standing
pages, and any canonical reader path that the approved implementation claims to
cover. Do not use the paused newsletter as a retention path.

## Monthly close

After the last day of the reporting month:

1. Confirm there was no material outage, missing page class, definition change,
   exclusion failure, privacy-control failure, or unreviewed implementation
   change. Otherwise mark the month `partial` and name the limitation.
2. Freeze the month, reproduce the three aggregate funnel counts from the
   approved source, and create an opaque aggregate receipt identifier. Do not
   place a secret URL, token, query string, or provider credential in the
   receipt field.
3. Create the report through `audience/reporting.mjs`. The minimal transition
   protocol leaves engaged-session totals and median active seconds as `null`;
   do not derive or invent them.
4. Reconcile into a founder-approved `measuring` ledger and validate the schema
   and business rules in x86_64 CI. Commit only aggregate counts, supporting
   aggregate evidence, safe exclusion aggregates, and limitations.
5. After receipt verification, overwrite the expired collector state with the
   purged state and complete the approved deletion procedure within 35 days.
6. Review the resulting pull request for participant rows, digests, tokens,
   request data, URLs with queries, reader content, secrets, and unsupported
   milestone language before merge.

A single complete month at or above 1,000 is progress, not achievement. Only
two consecutive complete months at or above 1,000 may set the milestone to
`achieved`.

## Stop and incident conditions

Disable collection immediately when any of these occurs:

- unexpected envelope properties or reader text reach storage or logs;
- raw IP, a device fingerprint, a credential, or a month token is retained at
  an unapproved boundary;
- opt-out, month rotation, deletion, exclusion, idempotency, or the kill switch
  fails;
- a collector clock or time-zone error could alter visit-day ordering;
- coverage is materially incomplete or counts cannot be reproduced; or
- cost, provider terms, operator ownership, or implementation changes outside
  David's approved record.

Preserve only safe aggregate evidence needed for diagnosis, rotate affected
credentials outside git, mark the month partial, document the incident, add a
regression contract, and require David's explicit reactivation approval.

## Current legitimate blockers

Local architecture and contracts can be prepared without crossing an external
boundary. Cloudflare is selected locally, but external work cannot proceed
until David approves the account/operator, endpoint, provider terms, privacy
notice and opt-out presentation, retention and logging controls, exclusion
implementation, credentials, provisioning, and canary execution for a reviewed
commit. Production collection and baseline start require later approvals. The
reader-intake closure is prepared locally but not deployed, and the
production-branch ownership disposition also remains a prerequisite to
deliberately increasing participation.
