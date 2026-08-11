# Privacy-safe observable return path proposal

Status: proposal only; not implementation, release, or activation authority

Owner and final approver: David Friedhof

Program item: `DDB-PC-028`

Machine-readable proposal:
`operations/outreach-observable-return-proposal.json`

## Recommendation

Use an **exact-post X URL-link-click aggregate receipt** as the lean campaign's
minimum observable return path.

The declared event is one provider-reported **Link click** on the exact URL in
an individually approved X source card derived from an already-published
evening Field Guide. X defines a Link click as a click on a URL in the post in
its official Post Activity Dashboard documentation:
<https://business.x.com/en/help/campaign-measurement-and-analytics/tweet-activity-dashboard>.

This is the narrowest available path that can observe movement from the
approved discovery surface toward the canonical publication without adding a
site tracker, identifier, cookie, email form, community feature, provider,
endpoint, or paid service.

It is a campaign acquisition signal only. It is not a unique visitor, verified
page load, repeat visit, RSS follow, subscriber, qualified engaged returning
reader, or first-1,000 measurement. X impressions, profile visits, permalink
clicks, expands, reactions, follower changes, and public page availability do
not satisfy this event.

## Why this path fits the current boundary

- The source card already must contain one exact immutable evening-edition URL.
- The existing X readiness record says post analytics are available and records
  an explicitly displayed zero Link clicks for the pinned exact-edition post.
  That dated evidence makes this path plausible but does not replace the
  implementation preflight. The preflight must verify that the existing
  account still exposes the Link clicks metric without registering for another
  product, creating an ads account, accepting terms, changing settings, or
  spending money.
- David's Daily Bread records only a provider-reported nonnegative aggregate
  count and the public post and edition references needed to audit it.
- No code executes in a reader's browser and no request is sent to a new DDB
  service.
- The official first-1,000 collector and
  `measurement/authority.json:firstPartyReturnMeasurementAuthorized` remain
  unchanged and false.

X may process activity under its own existing service boundary. This proposal
does not claim otherwise. It prevents DDB from receiving or retaining X's
row-level audience data and authorizes no export, API access, advertising
pixel, promoted post, or account mutation.

## Exact event and evidence contract

Proposed event ID: `x_exact_edition_url_link_click`

A receipt may record only:

1. the public X post URL and post identifier;
2. the exact immutable DDB evening-edition URL, with no query string or
   fragment;
3. the source edition ID and its published timestamp;
4. the provider metric label `Link clicks`;
5. the displayed aggregate integer, including an explicitly displayed zero;
6. the metric window and manual capture timestamp;
7. David Friedhof as the human operator;
8. a restricted evidence reference and SHA-256, if a screenshot is retained;
9. validation status, limitation text, and any correction reference.

The public repository must reject and never store names, handles other than the
public DDB account, viewer or clicker identities, IP addresses, user agents,
cookies, device identifiers, referrers, locations, demographic fields,
row-level exports, provider credentials, recovery material, or screenshot
bytes. Evidence containing account chrome or nonaggregate data stays in
restricted local storage and is referenced only by a content hash.

Every approved source card must use the bare canonical edition URL:
`https://davidsdailybread.com/editions/YYYY-MM-DD-evening.html`. UTM parameters,
redirectors controlled by DDB, URL shorteners added by DDB, fragments, pixels,
and tracking tokens are prohibited. X's normal display or redirect behavior
does not authorize DDB to create another redirect or identifier.

## Implementation scope proposed for separate approval

The implementation change would be limited to:

- add a closed JSON Schema for the aggregate receipt;
- add an empty campaign receipt ledger or a receipt directory with no live
  observations;
- add deterministic semantic validation binding one public X post to one exact
  immutable evening-edition URL and rejecting forbidden fields;
- update `operations/outreach-campaign.contract.json` and its schema so this is
  the selected but not-yet-validated path;
- update the campaign specification and measurement scorecard language without
  changing the official first-1,000 definition;
- add tests for URL binding, aggregate-only storage, unknown-state behavior,
  explicit-zero handling, disabled authority, and fail-closed rollback; and
- create separate implementation and read-only validation receipt templates.

It would not modify templates, rendered pages, JavaScript, service workers,
feeds, DNS, Cloudflare, GitHub Pages settings, Spark, the X broadcaster, X
credentials, X account settings, email, newsletter code, community code, or
the first-1,000 collector.

## Read-only validation required before readiness

Implementation alone does not make the return path ready. A separate read-only
validation must use one existing public DDB X post that already contains one
exact immutable edition URL and must establish all of the following:

1. The correct `@DavidDailyBread` account is open through the official X UI.
2. The existing post analytics surface displays the exact `Link clicks` metric
   for that one post without an account, plan, settings, terms, ads, credential,
   or spend change.
3. The public post contains exactly one DDB URL and it resolves to its exact
   immutable edition, not the homepage or another slot.
4. A displayed nonnegative integer can be transcribed into the proposed closed
   receipt and validated. An explicitly displayed zero proves metric
   observability; it does not prove a return occurred.
5. No screenshot bytes, row-level export, identity, credential, or additional
   provider field enters the repository.

If the metric is missing, renamed without an equivalent official definition,
available only after account mutation or terms acceptance, inseparable from
multiple URLs, or exposed only through row-level data, validation fails and the
campaign remains blocked.

## Campaign use after a later activation

Only after implementation release, successful read-only validation, a current
X readiness receipt, and David's exact campaign activation approval may the
operator record source-card Link clicks. Capture each approved source card at
one declared age, proposed as 24 hours after publication, and again at the
campaign's declared close only if X still exposes the same cumulative metric.

The core-proof return result is:

- `observed` when X explicitly displays at least one Link click for an approved
  source card with complete URL binding and evidence;
- `observed_zero` only when X explicitly displays zero for the declared window;
- `unknown` when the metric, window, source binding, or evidence is absent or
  ambiguous; and
- `invalid` when privacy, URL, authority, or correction validation fails.

Counts may be summed only across disjoint exact source cards when each receipt
has complete coverage. They are events, not people. Do not deduplicate, infer a
page view, or combine them with impressions, replies, followers, RSS, or the
first-1,000 ledger.

## Stop and rollback

Before campaign activation, any validation failure leaves `selectedPath` null,
`readinessStatus` blocked, site return unknown, and the campaign clock not
started.

After a later activation, stop campaign source-card preparation immediately if
the Link clicks metric disappears, changes meaning, requires new account or ads
state, cannot be tied to the exact URL, exposes prohibited data, or conflicts
with a correction. Preserve the smallest aggregate incident receipt, mark the
affected value unknown or invalid, and request review. Do not replace it with
impressions or another proxy.

Rollback removes only the selected-path authority and receipt-writing code in
a reviewed forward change. There is no site tag, cookie, endpoint, database,
provider resource, DNS record, or reader state to remove.

## Proposed approval sequence

### 1. Implementation and read-only validation approval

Exact wording:

> Approve DDB-PC-028 observable-return implementation: implement the
> exact-post X URL-link-click aggregate receipt described in
> `docs/OUTREACH_OBSERVABLE_RETURN_PROPOSAL.md`, and perform one read-only
> validation against an existing `@DavidDailyBread` post with an exact
> immutable edition URL. Use only the already available official X analytics
> surface; store only the closed aggregate receipt and restricted evidence
> hash; do not post, reply, change an account or credential, register for ads,
> accept terms, export row-level data, activate site analytics, email, or a
> community feature, provision or deploy anything, merge, spend money, or
> start the campaign clock. Report the exact local commit and validation
> result for separate release approval.

### 2. Exact-head release approval

This wording can be completed only after implementation and validation:

> Approve release of the DDB-PC-028 observable-return implementation at exact
> commit `COMMIT_SHA`, with diff SHA-256 `DIFF_SHA256`: push its clean branch,
> open a pull request, require the hosted x86_64 Merge gate, and merge only if
> every required check passes for that exact head. Do not activate the
> campaign, post or reply on X, change any account or provider state, activate
> analytics, email, community features, or personal-data collection, deploy a
> new service, spend money, or start the campaign clock.

### 3. Campaign activation approval

Not proposed or requested here. It remains a later decision requiring a
current X readiness receipt, a released and validated return path, exact start
and end timestamps, approved source-card and reply boundaries, stop rules, and
an exact activation receipt.

## Current decision

This proposal creates no execution authority. No return path is selected,
implemented, validated, released, or activated by this document. The campaign
remains blocked and its clock remains not started.
