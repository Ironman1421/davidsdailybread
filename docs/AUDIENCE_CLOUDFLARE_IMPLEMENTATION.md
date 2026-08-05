# Cloudflare audience endpoint local implementation

Status: provider-specific local implementation only; unprovisioned and disabled

Decision owner: David Friedhof

Last reconciled: 2026-07-31

## Authority boundary

David approved Cloudflare Workers + D1 for local implementation and an
unprovisioned canary plan on 2026-07-31. He did not approve an account, provider
terms, resource, identifier, endpoint, operator, credential, DNS change,
provisioning, canary execution, deployment, activation, production collection,
baseline start, or spend.

`operations/audience-measurement.contract.json` is the current operating state.
`audience/cloudflare/canary-plan.json` is the machine-readable plan. The
checked-in Wrangler template is intentionally non-deployable: it disables
`workers.dev`, preview URLs, and observability; contains placeholder database
and rate-limit identifiers; declares no route or Cron Trigger; omits the canary
secret; and sets the audience mode to `disabled`.

## Local components

| Artifact | Responsibility |
|---|---|
| `worker.mjs` | Canary-only HTTP wrapper, exact-origin CORS, secret gate, bounded JSON parsing, Pacific receipt date, verified-bot signal, registration limiter, D1 transitions, aggregate read boundary, and purge handler. |
| `schema.sql` | Strict short-lived visitor rows, immutable identity, ordered-date constraints, aggregate counters maintained by triggers, and expiry index. |
| `worker.test.mjs` | Provider-parity fixtures for fail-closed configuration, HTTP rejection, ordered/idempotent transitions, aggregates, bot/rate rejection, Pacific rollover, and purge survival. |
| `wrangler.unprovisioned.jsonc` | Disabled placeholder configuration that cannot identify or expose a real resource. |
| `canary-plan.json` | Approved plan scope, closed authority fields, preconditions, adversarial cases, and required evidence. |

The Worker accepts only `POST /v1/transition` from the two proposed canonical
origins, with no query string and an `application/json` body of at most 512
bytes. Diagnostic requests also require a canary secret whose SHA-256 digest is
installed through a future provider secret boundary. The response contains
only `decision`, `reason`, and `transition`.

The Worker recognizes exactly one enabled mode, `canary`. It contains no
production mode. Missing D1, limiter, hostname, secret digest, bot-control
verification, logging verification, retention verification, enabled purge
control, or control revision fails closed before a database transition.

## D1 behavior

The raw monthly browser token is converted to the definition-and-month-domain-
separated SHA-256 digest already defined in `audience/collector.mjs`. D1 stores
only that digest, month, first receipt date, optional returned and qualified
receipt dates, and the fixed 35-day expiry date. It stores no event body, page,
URL, referrer, name, email address, note, submission, IP address, location,
device property, or fingerprint.

Each transition is one conditional prepared statement. D1's change count
distinguishes acceptance from replay; a bounded row read classifies a failed
condition. Database constraints and triggers enforce immutable visitor keys,
ordered distinct days, idempotency, and monotonic aggregate counts. Purging
participant rows leaves monthly aggregates intact.

The registration limiter uses one date-scoped class key, not an IP, token, or
device value. This limits gross registration bursts without persisting a reader
identifier in application storage, but Cloudflare describes the limiter as
local, permissive, and eventually consistent. The canary must verify its actual
metadata and retention behavior before it can be approved.

## Canary boundary

The unprovisioned plan proposes a locked diagnostic `workers.dev` endpoint so
the website DNS does not change. That route is not eligible for production and
has no hostname yet. No public template imports the browser adapter, its config
remains `enabled: false` with `endpoint: null`, and canary evidence is always a
partial diagnostic report that cannot count toward the first 1,000.

Before the plan can run, David must separately approve a reviewed commit,
account and resource provisioning, provider terms/DPA, operator and failure
owner, exact endpoint, credential boundary, privacy and opt-out presentation,
metadata/logging/backup/deletion evidence, bot and rate controls, and canary
execution. A successful canary still does not authorize deployment, public
integration, production collection, or a baseline month.

## Current primary references

- [D1 Workers Binding API](https://developers.cloudflare.com/d1/worker-api/)
- [D1 prepared statements](https://developers.cloudflare.com/d1/worker-api/prepared-statements/)
- [Workers Rate Limiting binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)
- [Workers Request `cf` properties](https://developers.cloudflare.com/workers/runtime-apis/request/)
- [Workers routes and domains](https://developers.cloudflare.com/workers/configuration/routing/)
- [Worker Custom Domain prerequisites](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/)

These references were rechecked on 2026-07-31. Recheck them before any external
authorization because platform interfaces and provider behavior can change.
