# First 1,000 audience measurement specification

Status: active measurement definition; instrumentation not selected or
authorized

Owner and final decision-maker: David Friedhof

Last reconciled: 2026-07-31

## Purpose and authority

This specification defines the evidence required to say that David's Daily
Bread has reached 1,000 genuinely engaged returning people. It implements
`FOUNDER_DOCTRINE.md`, `docs/PRODUCT_SPEC.md`, and
`docs/GROWTH_ROADMAP.md`. It does not authorize an analytics provider, external
service, credential, cookie, production script, publishing change, or spend.

The website is the official milestone surface because it is the permanent
canonical home. RSS, approved social channels, reader submissions, and public
discussion supply important supporting evidence, but they are not added to the
website count. This prevents the same person from being counted once on the
website and again on every channel they use.

## Official milestone

The milestone is achieved only after two consecutive complete calendar months
each contain at least 1,000 qualified engaged returning readers.

A qualified engaged returning reader is one privacy-safe distinct website
visitor who, within one calendar month in `America/Los_Angeles`:

1. visits the canonical website on at least three separate calendar days; and
2. has at least two engaged sessions.

An engaged session satisfies at least one of these conditions:

- at least 60 seconds of active reading while the page is visible; or
- at least one allowlisted meaningful action: opening an edition from the
  archive, opening a tools or workflows library item, following a reviewed
  source, opening the RSS feed, creating or updating a local note, or completing
  an editorial-slip submission.

Automated monitors, known bots, preview and render checks, and David's or an
operator's identified internal traffic are excluded. A follower, impression,
single visit, idle tab, unconfirmed RSS estimate, or one-time public interaction
does not satisfy the milestone.

## What the count means

The count is a behavior-based proxy for people, not an identity registry. A
privacy-safe implementation cannot perfectly reconcile one person across
devices or several people sharing a device. Every monthly report must disclose
that limitation and use the phrase **qualified engaged returning readers** for
the measured value.

The public claim "1,000 genuinely engaged returning people" may be made only
when the machine-readable ledger reports two consecutive qualifying months and
the measurement coverage for both is complete. A traffic spike, inferred value,
partial month, or value copied from a social dashboard cannot satisfy the rule.

## Privacy boundary

Measurement must be aggregate-first and collect no more than is required for
the monthly qualification rule.

- Do not collect names, email addresses, note text, reader-submission content,
  raw IP addresses, precise location, advertising identifiers, or cross-site
  browsing data.
- Do not fingerprint a reader from device, font, canvas, network, or browser
  characteristics.
- If a first-party pseudonymous visitor identifier is approved, it must rotate
  no later than 35 days, must not be linked to an account or contact record, and
  must not be committed to this repository.
- Strip query strings and fragments before recording page paths. Reject any
  event property that could contain free text or credentials.
- Retain only aggregate monthly results in the public repository. Raw or
  visitor-level events require a documented deletion period and may never enter
  GitHub logs, build artifacts, prompts, issues, or public ledgers.
- Unknown values are `null`, never zero. Inferred values must be labeled and
  cannot qualify a month.
- A reader-visible privacy explanation and a working opt-out are required
  before production collection begins.

## Measurement coverage

A month is `complete` only when:

- approved instrumentation was active from the first through the last day of
  the month on the current edition, archived editions, standing pages, and the
  tools and workflows libraries;
- the active-reading clock stopped whenever the document was hidden or the
  browser reported no qualifying activity;
- the meaningful-action event list was closed to the exact allowlist above and
  no text payload was accepted;
- documented bot, synthetic-monitor, preview, and internal-traffic exclusions
  were applied consistently;
- any material outage, tag omission, processing failure, or definition change
  was absent; and
- an aggregate source receipt can reproduce the reported counts.

A month with a known gap is `partial`. A partial month may guide diagnosis but
cannot qualify toward the milestone. The first numerical growth rung is set
only after the first complete baseline month.

## Monthly record

`audience/monthly-ledger.json` is the aggregate public record and validates
against `audience/measurement.schema.json`. Each completed month records:

- unique visitors, returning visitors, and qualified engaged returning readers;
- engaged-session totals and median active seconds only when the approved
  measurement boundary exposes those aggregates; the minimal transition
  protocol intentionally leaves both `null` and discloses that limitation;
- excluded bots, internal visits, and synthetic-monitor visits when the
  measurement system exposes those counts;
- supporting RSS, social, editorial-intake, and public-discussion evidence only
  when privacy-safe data actually exists; and
- the aggregate receipt, capture time, coverage status, and any limitation.

No row-level visitor data belongs in the ledger. Supporting evidence is never
added to the official website count.

The local reference qualifier in `audience/qualifier.mjs` may emit only the
`first-seen`, `returned`, and `qualified` envelopes defined by
`audience/transition.schema.json`. The envelope contains only the contract and
definition versions, calendar month, transition name, and month-scoped token.
It contains no path, URL, referrer, active-time trace, note text, submission
content, name, email address, IP address, device field, or arbitrary property.
The future collector must fail closed on direct or out-of-order qualification
and must use distinct server receipt days so replayed client envelopes cannot
create an immediate returning-reader milestone.

`audience/reporting.mjs` is the aggregate-only reconciliation boundary. A
monthly report may contain counts and limitations but never raw tokens, token
digests, visitor rows, event rows, or free text collected from readers. After a
report receipt is verified, the approved operator must replace the expired
collector state with the purged state and preserve only the aggregate report.

## Activation and change control

`docs/AUDIENCE_ANALYTICS_DECISION.md` defines the provider-selection and
activation gate. David must explicitly approve the provider, privacy behavior,
retention, reader notice, operating owner, budget, and production installation
before collection begins.

A future change to the qualification thresholds, channel-counting rule, privacy
boundary, or consecutive-month requirement must update this specification, the
schema, the ledger definition, and tests together. Historical monthly records
retain the definition version under which they were captured.
