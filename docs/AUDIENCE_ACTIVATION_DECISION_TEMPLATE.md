# Audience measurement founder decision template

Status: provider/local-plan decision recorded; external provisioning, canary
execution, production collection, and spend remain unapproved

Decision owner: David Friedhof

## How to use this record

David selected Cloudflare Workers + D1 for provider-specific local
implementation and approved an unprovisioned canary plan on 2026-07-31. Replace
the remaining `UNDECIDED` values only with reviewed evidence in a dedicated
pull request. Keep every external gate in
`operations/audience-measurement.contract.json`,
`audience/cloudflare/canary-plan.json`, and the aggregate ledger closed until
the corresponding approval is explicit.

Provider selection, canary authorization, and production activation are three
separate decisions. Approval of one does not imply the next.

`docs/AUDIENCE_ENDPOINT_RECOMMENDATION.md` records Cloudflare Workers + D1 as
the locally selected provider and the account, route, privacy, logging, and
operator questions that still block external action.

## Implementation decision

| Decision | Required record |
|---|---|
| Endpoint/provider | `cloudflare-workers-d1`, local implementation only; endpoint unset |
| Operator and failure owner | `UNDECIDED` |
| Owning repository and hosting account | `UNDECIDED` |
| Proposed origin and route | Canonical site origins with a diagnostic `workers.dev` route; hostname unset and execution unapproved |
| Monthly spend ceiling | `$0`; no spend authorized |
| Credential owner and least-privilege scope | `UNDECIDED` |
| Monitoring and on-call path | `UNDECIDED` |
| Kill switch and removal owner | `UNDECIDED` |

Attach primary documentation for current pricing, data handling, retention,
logging, subprocessors, deletion, availability, and applicable provider terms.
Do not treat a free tier as approval to accept terms or create an account.

## Reader privacy decision

| Control | Required record |
|---|---|
| Exact reader-visible explanation | `UNDECIDED`; review `docs/AUDIENCE_PRIVACY_COPY_DRAFT.md` |
| Exact opt-out label and placement | `UNDECIDED` |
| Opt-out verification steps | `UNDECIDED` |
| Cryptographically random token generator | `UNDECIDED` |
| Approved collector-row lifetime, maximum 35 days | `UNDECIDED` |
| Aggregate retention | `UNDECIDED` |
| Deletion job and verification owner | `UNDECIDED` |
| CDN/host IP retention disabled evidence | `UNDECIDED` |
| Application, error, trace, firewall, and backup logging evidence | `UNDECIDED` |

The implementation remains unacceptable if it fingerprints readers, retains
raw IP, logs request bodies or tokens, accepts arbitrary event properties, or
links measurement state to names, email addresses, reader submissions,
newsletter records, accounts, advertising IDs, or cross-site behavior.

## Exclusion decision

| Exclusion | Exact implementation and verification |
|---|---|
| Known bots | `UNDECIDED` |
| Synthetic monitors | `UNDECIDED` |
| Preview and render checks | `UNDECIDED` |
| David and authorized internal operators | `UNDECIDED` |
| Registration-rate abuse | `UNDECIDED` |

Rate and bot controls may use request data transiently. They may not persist a
raw IP address or create a device fingerprint. Challenge or edge-control
providers are part of the external boundary and require the same review.

## Coverage decision

Record the exact implementation and test evidence for:

- current morning and evening editions;
- archived morning and evening editions;
- archive, tools, and workflows pages;
- standing canonical pages included in the approved coverage claim;
- month rotation and Pacific daylight-saving boundaries;
- visible, recently active reading time;
- the six meaningful-action integrations, including proof that local note and
  editorial-slip content never enters measurement; and
- opt-out before initialization, opt-out after initialization, kill switch,
  removal, and deletion.

Any omitted canonical page class makes the month partial unless the approved
measurement definition explicitly excludes that class before the month begins.

## Canary-plan approval and execution gate

The unprovisioned plan in `audience/cloudflare/canary-plan.json` is approved.
Canary execution remains unapproved until David provides an explicit statement
naming the reviewed commit and external scope. A sufficient later authorization
is:

> I approve the implementation recorded at commit `UNDECIDED` for a diagnostic
> canary only, using provider/account `UNDECIDED`, operator `UNDECIDED`, and a
> maximum spend of `UNDECIDED`. I do not yet authorize production collection or
> an official baseline month.

Run the canary exactly under `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md`. Record the
receipt and every failure or limitation without committing visitor-level data.

## Production and baseline authorization

This section remains unapproved until the canary is successful and David gives
a second explicit statement naming the reviewed evidence and start boundary. A
sufficient authorization is:

> I approve production audience measurement at commit `UNDECIDED`, with the
> controls and operator recorded here, beginning `UNDECIDED` Pacific. I approve
> a maximum monthly spend of `UNDECIDED`. The first official baseline may begin
> only at the next complete Pacific calendar-month boundary after every gate is
> verified.

If the approved time is not the first instant of a Pacific calendar month, the
remainder of that month is partial and cannot qualify.

## Separate growth prerequisites

This measurement decision does not resolve the public reader-intake exposure or
production-branch ownership gaps. David must separately approve and verify
their dispositions before deliberately increasing participation. It also does
not reverse any paused initiative in `FOUNDER_DOCTRINE.md`.
