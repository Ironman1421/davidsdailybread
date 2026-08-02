# Measurement scorecard

Status: local measurement MVP

Owner: David Friedhof

Authority: `FOUNDER_DOCTRINE.md` in the project root is authoritative. The
current proof goal is the first 1,000 genuinely engaged people who return for
faith, technology, prayer, and service. Older follower-growth targets are not
the north star for this scorecard. Newsletter sending, new-reader intake, and
first-party return collection remain paused.

## North star and honest proxy stages

The north star is **genuinely engaged returning people in a rolling seven-day
window**. A person qualifies only after a declared meaningful action on at
least two separate days. Passive page loads do not qualify. No authorized
first-party method exists yet, so the value is `unknown`, with reason
`not_authorized`. `measurement/authority.json` enforces that boundary in the
command. An observed first-party return value is rejected while its repository
authorization flag is false.

The scorecard reports proxy stages without pretending that a lower stage proves
a higher one:

1. Canonical availability: the exact edition is verifiably live.
2. Discovery delivery: the exact edition reached an approved discovery channel.
3. Platform engagement and return: dated aggregate metrics entered from a
   platform. Each platform stays separate because people can overlap.
4. First-party return proxy: a future, explicitly authorized aggregate site
   measure. This is currently unknown.
5. North star: genuinely engaged returning people. This is currently unknown.

Delivery, impressions, clicks, followers, subscribers, and platform returning
viewers are evidence stages. None is renamed as engaged returning people.

## Metric dictionary

The machine-readable dictionary is
`measurement/metric_dictionary.json`. Every output includes a state, value,
unit, coverage, reason, and evidence references. Formulas below apply to the
daily or seven-day scorecard window unless stated otherwise.

| Metric | Formula | Accepted source | Cadence | Owner | Unknown-state behavior |
| --- | --- | --- | --- | --- | --- |
| Dispatch-to-site latency | Median of exact public verification time minus actual dispatch time; also report p95 and sample count | Spark or GitHub actual dispatch event plus exact public-page verification | Daily, weekly | David Friedhof | Unknown unless both actual timestamps exist. Never substitute schedule, render, commit, or an older edition. |
| Dispatch-to-X latency | Median of verified exact-edition X publication time minus actual dispatch time; also report p95 and sample count | Spark X send event or repository X read-back receipt | Daily, weekly | David Friedhof | Unknown unless both actual timestamps exist. A skipped lane is not success. |
| Edition success rate | Successful exact workflow and archive entry and HTTP 200 exact-title page divided by observed due outcomes | `archive.json`, GitHub run, exact public-page check | Daily, weekly | David Friedhof | Unknown when no due outcome is observed; partial when coverage is incomplete. |
| Telegram receipt success rate | Exact-edition receipts with `status=sent` divided by observed due outcomes | Redacted GitHub Telegram receipt artifact | Daily, weekly | David Friedhof | Unknown without the exact receipt; partial with incomplete coverage. |
| Watchdog success rate | `exact_edition_present` results divided by observed due watchdog outcomes | Spark watchdog journal or normalized receipt | Daily, weekly | David Friedhof | Unknown without exact date and slot evidence; partial with incomplete coverage. |
| Genuinely engaged returning people | Distinct people with qualifying engagement on at least two separate days in the rolling seven-day window | Future authorized first-party aggregate; provider aggregates remain separate | Weekly | David Friedhof | `unknown:not_authorized` until David approves a method. Never sum overlapping platforms. |
| First-party returning readers | Privacy-preserving aggregate readers seen on at least two separate days | Future authorized first-party aggregate only | Weekly | David Friedhof | `unknown:not_authorized`; do not use cookies, fingerprints, IPs, local notes, or intake data. |
| X followers | Dated aggregate account count | Manual X account metric or checked-in last-known baseline | Weekly | David Friedhof | Unknown without a dated source. Stale values keep their old timestamp and last-known label. |
| X impressions | Provider-reported rolling seven-day aggregate | Manual X analytics aggregate | Weekly | David Friedhof | Unknown when absent. Missing is not zero. |
| X link clicks | Provider-reported rolling seven-day aggregate | Manual X analytics aggregate | Weekly | David Friedhof | Unknown when absent. Do not infer from impressions or reactions. |
| YouTube subscribers | Dated aggregate channel count | Manual YouTube Studio aggregate | Weekly | David Friedhof | Unknown when absent. Missing is not zero. |
| YouTube returning viewers | Provider-reported returning viewers for the exact seven-day window | Manual YouTube Studio aggregate | Weekly | David Friedhof | Unknown unless exposed and entered for the exact window. |
| RSS subscribers | Aggregate count from an authorized RSS source, if one exists | Manual authorized aggregate | Weekly | David Friedhof | Unknown when the public feed exposes no count. Do not estimate from availability or requests. |

Every rolling seven-day audience metric carries `periodStart` and `periodEnd`.
The command requires a six-day difference and an end date equal to the daily
observation date. A weekly report rejects a stale window rather than presenting
it as the requested week. An observed zero is valid only when its dated
aggregate source explicitly says zero. Missing values remain null. Weekly rates
and latency summaries are marked `partial` when any due outcome or observation
day is missing.

## Offline commands

The scorecard has no network client and writes nothing by default. It reads a
closed, aggregate-only observation JSON file and the repository archive.

```sh
python3 measurement/scorecard.py daily \
  --date 2026-08-02 \
  --observations measurement/observations/2026-08-02.json \
  --archive archive.json \
  --format markdown
```

The current observation directory intentionally contains only the evidenced
August 2 snapshot. Therefore the production weekly command reports six missing
days and partial coverage:

```sh
python3 measurement/scorecard.py weekly \
  --week-ending 2026-08-02 \
  --observations-dir measurement/observations \
  --archive archive.json \
  --format json
```

A complete synthetic seven-day fixture exercises full weekly aggregation:

```sh
python3 measurement/scorecard.py weekly \
  --week-ending 2099-01-07 \
  --observations-dir tests/fixtures/measurement/week \
  --archive tests/fixtures/measurement/archive.json \
  --format json
```

## August 2 baseline

Snapshot time: 2026-08-02 11:56:50 Pacific, before the evening dispatch window.
Only the morning edition was due.

| Measure | August 2 result | Evidence |
| --- | ---: | --- |
| Dispatch-to-site latency | 924.545 seconds (15m 24.545s) | Actual Spark dispatch at 04:40:10 PT; exact public page verified HTTP 200 with its exact title at 04:55:34.544572 PT in GitHub run 30746214924 |
| Dispatch-to-X latency | 1,199 seconds (19m 59s) | Same actual dispatch; active Spark X lane recorded exact morning send at 05:00:09 PT |
| Edition success | 1/1 due, pass | Successful run, exact `archive.json` entry, exact public page and title verified |
| Telegram success | 1/1 due, pass | Redacted artifact 8833117521 recorded `status=sent` at 04:55:35.842446 PT |
| Watchdog result | 1/1 due, pass | Spark morning watchdog recorded `exact_edition_present` at 05:15:06 PT |
| Genuinely engaged returning people | Unknown | First-party return measurement is not authorized |
| First-party returning readers | Unknown | First-party return measurement is not authorized |
| X followers | Last-known floor: 5 as of July 31 | `distribution/ledger.json`; this is not claimed as the current August 2 count |
| X impressions and link clicks | Unknown | No dated provider aggregate entered |
| YouTube subscribers and returning viewers | Unknown | No dated provider aggregate entered |
| RSS subscribers | Unknown | Public RSS does not expose a subscriber count |

The evening edition is `not_due`, not failed, because the snapshot predates its
14:40 Pacific dispatch window.

## Evidence normalization and privacy boundary

Normalize only the minimum aggregate fields in
`measurement/observation.schema.json`:

- Public pages: exact edition ID, verification timestamp, HTTP status, and
  exact-title result.
- GitHub: run conclusion, step timestamp, run or artifact reference, and
  redacted exact-edition receipt status.
- Spark: exact edition ID, event type, event timestamp, and status from the
  trigger, active X lane, or watchdog journal.
- Platforms: dated aggregate counts entered manually. No exports containing
  audience identities are accepted. Rolling metrics must name the exact start
  and end dates.

Do not ingest `counter.csv`, reader submissions, full bake `content.json`, local
notes, IP addresses, user agents, email addresses, chat IDs, cookies, device
identifiers, or provider credentials. Full bake logs can contain reader
material, so the measurement input uses run metadata and redacted operational
receipts only.

The schema is closed with `additionalProperties: false`, and the command also
rejects unexpected fields without requiring a schema library. This prevents an
accidental personal-data field from quietly becoming part of the scorecard.
It also rejects future-dated evidence, events outside the observation's Pacific
date, invalid workflow conclusions, out-of-range HTTP statuses, and observed
first-party return metrics while `measurement/authority.json` remains false.

## Seven-day experiment decisions

Copy `measurement/experiments/seven-day-ledger.template.json` for each local
experiment and replace its template identifiers and dates before use. The
template declares one changed variable, a seven-day window, zero authorized
spend, minimum 7/7 daily coverage, an explicit primary pass and fail threshold,
and reliability and privacy guardrails.

A decision is:

- `pass` only with complete required coverage, a primary result meeting the
  pass threshold, and every guardrail passing;
- `fail` with complete coverage when the primary result meets the fail
  threshold or any guardrail fails;
- `inconclusive` when the primary metric is unknown, unauthorized, or below
  minimum coverage or sample size.

An inconclusive experiment does not authorize collection, publication,
activation, sending, provisioning, or spend.
