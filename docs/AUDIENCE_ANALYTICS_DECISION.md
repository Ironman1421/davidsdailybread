# Audience analytics architecture decision

Status: Cloudflare Workers + D1 selected for local implementation and an
unprovisioned canary plan only; all external activity and production collection
unauthorized

Decision owner: David Friedhof

Last reconciled: 2026-07-31

## Decision

David's Daily Bread will measure the first 1,000 through aggregate, privacy-safe
website return behavior under `docs/AUDIENCE_MEASUREMENT_SPEC.md`. It will not
build an identity graph, require member accounts, combine people across social
platforms, or count followers as returning readers.

Cloudflare Workers + D1 is the selected provider for local implementation and
an unprovisioned canary plan. No account, resource, provider terms acceptance,
credential, endpoint, canary execution, deployment, activation, production
script, cookie, baseline start, or spend is approved. The repository state is
`implementation-selected`, not installed or measuring.

## Required implementation shape

Any proposed implementation must:

1. support the exact three-visit-days and two-engaged-sessions monthly rule;
2. measure active visible time without treating an idle open tab as reading;
3. accept only the closed meaningful-action event allowlist;
4. use no fingerprinting, advertising ID, cross-site tracking, note text,
   submission content, name, email address, raw stored IP address, or precise
   location;
5. rotate any approved first-party pseudonymous visitor identifier within 35
   days and never link it to a reader or subscriber record;
6. exclude known bots, synthetic monitors, previews, render checks, and internal
   traffic;
7. strip URL query strings and fragments before storage;
8. provide aggregate export or API receipts sufficient to reproduce each
   monthly ledger entry;
9. provide a working opt-out, a reader-visible privacy explanation, a deletion
   schedule, and a tested kill switch; and
10. operate with a David-approved owner, cost ceiling, credential boundary, and
    failure path.

## Hosting constraints and implementation classes

The current site is static GitHub Pages. The repository contains no website
analytics script and GitHub Pages does not supply a repository-owned audience
event ledger. A qualifying implementation therefore requires a separately
approved measurement boundary.

Candidate classes for a later read-only comparison are:

- edge or CDN-side aggregate measurement, if the current domain path supports
  the required engagement events and privacy controls;
- a privacy-focused hosted analytics service with aggregate export, short
  retention, and the required visitor and custom-event semantics; or
- a narrowly scoped first-party collection endpoint operated by an approved
  owner.

Self-hosting is not the default recommendation because it adds a new service,
security surface, uptime responsibility, and operating cost. A nominally
"cookieless" tool is not automatically acceptable if it recreates visitors by
hashing network and device characteristics in a way that functions as
fingerprinting.

## Read-only capability review, 2026-07-31

The following review used current provider documentation without creating an
account, accepting terms, provisioning resources, or installing credentials.

| Candidate | Useful capability | Fit for the official milestone |
|---|---|---|
| GitHub repository traffic | Fourteen days of repository visitors, referrers, and popular repository content | Not website audience measurement and not sufficient for a calendar-month return cohort |
| Cloudflare Web Analytics | Free privacy-first page-view and performance analytics, bot exclusion, no query-string logging | Useful secondary diagnostics, but its current documentation says custom events are not supported, so it cannot apply the exact engagement rule |
| Plausible | Page views, sessions, duration, outbound and custom events, and aggregate API access | Not sufficient for the official count because its documented visitor identity resets across days; one person visiting on several days is counted separately |
| PostHog | Custom events, configurable persistence, cookie lifetime, opt-out defaults, property filtering, and identified-only person profiles | Technically capable, but its defaults are broader than this contract and would require a locked-down configuration, retention review, provider approval, and canary |
| Local-first qualification with a narrow aggregate endpoint | Keeps visit-day, active-time, and meaningful-action state in the reader's browser and sends only bounded milestone-state transitions | Preferred architecture for founder review because it minimizes collected behavior while implementing the exact rule; it still requires approved code, an endpoint owner, provisioning, notice, opt-out, and deletion controls |

Primary documentation reviewed:

- [GitHub repository traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository)
- [Cloudflare Web Analytics overview](https://developers.cloudflare.com/web-analytics/about/)
  and [feature FAQ](https://developers.cloudflare.com/web-analytics/faq/)
- [Plausible metric definitions](https://plausible.io/docs/metrics-definitions),
  [custom events](https://plausible.io/docs/custom-event-goals), and
  [Stats API](https://plausible.io/docs/stats-api)
- [PostHog JavaScript configuration](https://posthog.com/docs/libraries/js/config)

These findings can change. Recheck the primary documentation before any
external provisioning or canary-execution decision.

`docs/AUDIENCE_ENDPOINT_RECOMMENDATION.md` records the provider decision: an
isolated Cloudflare Worker + D1 is approved for provider-specific local code and
an unprovisioned canary plan only. Provider-level IP/log retention, account
ownership, terms, route, credentials, operator, and canary execution still
require review and David's explicit approval. Supabase is not the first choice
for this payload because its current hosted Edge Function documentation
describes automatic invocation request/response and edge metadata logs.

## Preferred architecture for founder review

The current recommendation is a small local-first qualifier with a narrow
aggregate endpoint, not a general analytics SDK running with broad defaults.
The browser would:

1. create one random, month-scoped first-party pseudonymous token;
2. keep distinct visit days, engaged-session count, active visible time, and
   allowlisted meaningful-action state locally;
3. send at most one `first-seen`, one `returned`, and one `qualified` transition
   for that token and definition version during the month; and
4. delete or rotate the token no later than 35 days.

The endpoint would accept only the token, month, definition version, and one of
those three transition names. It would reject arbitrary properties and free
text, hash the token for deduplication, avoid retaining request IP or precise
location, delete pseudonymous rows within the approved short retention window,
and retain only aggregate monthly counts and operational error totals.

The endpoint must not treat a browser envelope as proof by itself. Client code
is observable and can be replayed. A production collector must register
`first-seen` before `returned`, register `returned` before `qualified`, enforce
distinct server receipt days in the reporting time zone, make every transition
idempotent, and reject direct, out-of-order, cross-month, duplicate-token, and
impossibly rapid qualification attempts. Token-registration rate limits and bot
controls may use request data transiently, but raw IP or device fingerprints
must not be persisted. Any challenge or edge-control provider requires the same
founder approval and reader-notice review as the collector itself.

This design intentionally does not transmit note text, submission content,
pages read, source URLs, active-time traces, or a raw clickstream. It also makes
the cross-device limitation visible rather than creating an identity graph to
hide it. The endpoint technology is selected locally. The account, endpoint,
route, operator, credential boundary, and every external action remain unset
and unapproved.

`audience/qualifier.mjs`, `audience/transition.schema.json`,
`audience/collector.mjs`, and `audience/reporting.mjs` are pure local reference
components for qualification, collection, and aggregate close.
`audience/browser-adapter.mjs` is the disabled browser boundary: its checked-in
configuration has no endpoint, its source contains no built-in transport, and
no public template loads it. `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md` defines the
separate activation, canary, close, purge, and stop gates. These artifacts are a
prototype, not production collection. `audience/cloudflare/` contains the local
canary-only Worker, D1 schema, intentionally non-deployable configuration, and
machine-readable plan. It has no external identifiers or production mode.

## Provider comparison record

Before a provider recommendation, record for each candidate:

- exact visitor and session definitions;
- active-time and custom-event support;
- identifier, IP, cookie, fingerprinting, and cross-site behavior;
- data location, subprocessors, retention, deletion, opt-out, and export;
- bot and internal-traffic controls;
- script weight, page-performance impact, availability, and kill switch;
- pricing, free-tier limits, upgrade behavior, and maximum proposed spend; and
- whether a full aggregate month can be independently reconciled.

Unknown answers remain blockers, not assumed approvals.

## Founder activation gate

Production measurement remains disabled until a reviewed repository change
records all of the following:

- David's explicit approval of the reviewed commit for external provisioning
  and canary execution (local provider implementation is already approved);
- the approved monthly spend, including `$0` when no spend is authorized;
- the reader-visible privacy notice and opt-out behavior;
- the exact event payload with fixtures proving that free text and personal data
  are rejected;
- the raw-event deletion period and aggregate retention rule;
- the authorized operator, secret owner, monitoring, kill switch, and removal
  path;
- coverage of both bake templates and every standing canonical page; and
- a canary report proving internal, bot, preview, and synthetic-monitor
  exclusions before the first baseline month begins.

Installing a script, creating an account, changing DNS, adding credentials, or
accepting provider terms is external provisioning and requires David's explicit
approval. Research and local prototypes do not cross that gate.
