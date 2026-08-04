# Audience endpoint and operator recommendation

Status: provider selected for local implementation and an unprovisioned canary
plan only; no account, terms, DNS change, provisioning, deployment, credential,
canary execution, collection, activation, baseline, or spend authorized

Decision owner: David Friedhof

Last reviewed: 2026-07-31

## Recommendation

David selected an isolated Cloudflare Worker plus D1 database for
provider-specific local implementation and an unprovisioned canary plan on
2026-07-31. The local implementation uses the checked-in collector as its
behavior oracle, executes each state transition as an atomic conditional D1
operation, requires disabled request observability, and implements a scheduled
purge path for expired participant-level rows.

This selection is not external authorization. The machine-readable provider is
`cloudflare-workers-d1`, while the endpoint, operator, account, database,
namespace, and reviewed commit remain `null`; provisioning, canary execution,
deployment, activation, production, and baseline fields remain `false` in
`operations/audience-measurement.contract.json`,
`audience/cloudflare/canary-plan.json`, and `audience/monthly-ledger.json`.

## Why this is the leading candidate

| Requirement | Cloudflare Worker + D1 fit | Remaining proof |
|---|---|---|
| Narrow public endpoint | A Worker can accept the exact POST envelope without a general analytics SDK. | Exact CORS, content-type, body-size, origin, response, and error contracts require an approved wrapper and canary. |
| Ordered, concurrent-safe state | D1 prepared statements and atomic batches can implement conditional insert/update transitions without reading an entire month into application memory. | Adversarial concurrency and replay tests must prove parity with `audience/collector.mjs`. |
| Short-lived participant rows | Cron Triggers can invoke a scheduled purge; D1 deletes count as writes. | The approved row lifetime, deletion receipt, backup behavior, and operator must be verified. |
| No customer-visible raw request logs | Workers invocation logs can be explicitly disabled; application code can contain no console logging and tracing can remain disabled. | Cloudflare's underlying service-log and IP-metadata handling still requires DPA, privacy-notice, and retention review. |
| Abuse boundary | A Cloudflare-zone WAF rate rule can count transiently by IP, and the Free plan exposes a Verified Bot rule field. | Free-plan controls are limited, rate limiting can fail open during infrastructure overload, and advanced Bot Management is Enterprise-only. The canary must prove the chosen control without persisting a fingerprint. |
| Early scale and cost | Current Free limits are far above the expected transition volume around the first 1,000; the Paid Workers plan currently starts at $5/month. | `$0` is still spend/terms authority and must be explicitly approved. Abuse can consume free limits and cause fail-closed measurement gaps. |

Primary documentation reviewed:

- [Workers pricing and Free/Paid request limits](https://developers.cloudflare.com/workers/platform/pricing/)
- [Workers platform limits and fail behavior](https://developers.cloudflare.com/workers/platform/limits/)
- [D1 pricing and Free-plan behavior](https://developers.cloudflare.com/d1/platform/pricing/)
- [D1 atomic batch and consistency API](https://developers.cloudflare.com/d1/worker-api/d1-database/)
- [Workers Logs and disabling invocation logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/)
- [Cron Triggers](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
- [WAF rate-limiting availability](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- [Cloudflare DPA](https://www.cloudflare.com/cloudflare-customer-dpa/)
  and [GDPR/IP-log explanation](https://www.cloudflare.com/trust-hub/gdpr/)

These capabilities and prices can change and must be rechecked immediately
before any external authorization.

## DNS and route reality

A read-only DNS check on 2026-07-31 found `davidsdailybread.com` authoritative
nameservers at Porkbun and the public site resolving to GitHub Pages. Cloudflare
requires an active Cloudflare zone for a Worker Custom Domain, and its Free/Pro
setup requires Cloudflare to be the primary authoritative DNS provider. A
partial CNAME setup that leaves authoritative DNS elsewhere currently requires
Business or Enterprise. Cloudflare documents `workers.dev` as a convenient
starting endpoint but recommends a route or Custom Domain for production.

Therefore:

- an approved canary could evaluate a locked-down `workers.dev` endpoint without
  changing the website's DNS, if David explicitly accepts that scope;
- a branded production endpoint would require either a separately reviewed
  authoritative-DNS migration or a paid partial-zone option; and
- no DNS migration should be bundled into analytics approval. It needs an
  exported-record inventory, TTL plan, mail/domain verification review,
  rollback procedure, and post-change resolution checks of the GitHub Pages
  apex and `www` records.

Primary routing documentation:

- [Workers routes and domains](https://developers.cloudflare.com/workers/configuration/routing/)
- [Worker Custom Domain prerequisites](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)
- [`workers.dev` purpose and limitations](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)
- [Cloudflare primary DNS setup](https://developers.cloudflare.com/dns/zone-setups/full-setup/)
- [Partial CNAME setup availability](https://developers.cloudflare.com/dns/zone-setups/partial-setup/)

## Implemented local shape

The provider-specific wrapper is isolated in `audience/cloudflare/`. It has no
deployment workflow, account identifier, route, credential, or production mode.
The local shape is:

1. exact-origin CORS and POST-only routing;
2. reject a query string, body over the narrow approved maximum, wrong content
   type, wrong encoding, missing/extra JSON field, or unsupported version before
   application logging;
3. derive the Pacific receipt date at the Worker;
4. compute the definition-and-month-domain-separated SHA-256 token digest;
5. execute one atomic conditional D1 transition and return only the exact
   decision contract;
6. update aggregate operational counters without request identifiers;
7. emit no console output, persist no Worker invocation log or trace, and set
   preview and `workers.dev` exposure to the approved environment only;
8. run a scheduled purge and aggregate-close receipt under
   `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md`; and
9. fail closed on unavailable storage, invalid clock, deletion failure, limit
   exhaustion, or configuration drift.

The implementation must not copy the in-memory collector state into a single
shared blob and perform read-modify-write. Concurrent requests could lose or
misorder transitions. D1 must enforce transition predicates atomically at the
database boundary, with the pure collector tests reused as behavioral fixtures.

## Why Supabase is not the first choice here

Supabase remains the approved design provider for the separate private reader
store, but that does not make it the right audience endpoint or authorize a
project. The hosted Edge Function documentation says invocation views include
request/response data such as headers and body, and the platform logging docs
describe automatic Edge Function network logs with Cloudflare request metadata.
Current Free pricing includes one day of API/database log retention.

That default is a poor fit for a payload containing a raw month token. A
dedicated project, private schema, transactional database routine, Cron purge,
and no link to reader-store data would be required, yet the provider-level
invocation logging question would remain. Supabase should move ahead of
Cloudflare only if primary documentation and a canary prove that raw envelope
bodies and IP metadata can be excluded from retained logs at every hosted
boundary.

Primary documentation reviewed:

- [Supabase Edge Function logging](https://supabase.com/docs/guides/functions/logging)
- [Supabase platform logging sources](https://supabase.com/docs/guides/telemetry/logs)
- [Supabase Cron](https://supabase.com/docs/guides/cron)
- [Supabase Edge Function limits](https://supabase.com/docs/guides/functions/limits)
- [Supabase Edge Function usage pricing](https://supabase.com/docs/guides/platform/manage-your-usage/edge-function-invocations)
- [Supabase plan and log-retention comparison](https://supabase.com/pricing)
- [Supabase 2026 breaking-change index](https://supabase.com/changelog?types=breaking-change)

The 2026 changelog was reviewed as required. Its current Edge Function change
concerns nested function-to-function rate limits and does not resolve inbound
invocation-log privacy.

## Founder decisions still required

Before any external action, David must separately:

1. authorize Cloudflare account and resource provisioning;
2. name the account owner, operator, failure owner, and reviewed commit;
3. approve provider terms/DPA and verify metadata, logging, backup, and deletion
   behavior;
4. approve the exact `workers.dev` diagnostic endpoint, canary secret boundary,
   bot/rate controls, privacy, retention, exclusions, kill switch, and evidence
   plan; and
5. explicitly authorize canary execution with a zero-dollar spend ceiling.

Production deployment, public browser integration, collection, and baseline
start remain later separate approvals even after a successful canary.
