# Audience measurement privacy copy draft

Status: local draft only; not approved for publication and not evidence that
measurement is active

Decision owner: David Friedhof

Last reconciled: 2026-07-31

## Purpose

This is proposed reader-visible language for the local-first measurement design
in `docs/AUDIENCE_ANALYTICS_DECISION.md`. It cannot be finalized until David
approves the endpoint/operator, actual infrastructure data handling, retention,
and opt-out presentation. It is not loaded by a public page.

## Short notice draft

> We use privacy-limited audience measurement to learn whether readers return.
> Your browser keeps a random code that changes monthly and sends only three
> possible progress signals: first visit, return, and qualified return. We do
> not send the pages you read, your notes, submission text, name, email address,
> or an activity timeline. You can opt out and erase the browser's measurement
> state at any time.

This copy may appear only after every statement is verified against the
approved production boundary. If infrastructure handles IP addresses
transiently for delivery or abuse prevention, the final notice must say so
plainly and describe the non-retention behavior accurately.

## Expanded explanation draft

> David's Daily Bread measures returning readership without building reader
> profiles. A random browser code is scoped to one calendar month and is not
> connected to an account, subscriber, reader submission, advertising ID, or
> activity on another site. Your browser decides locally whether you visited on
> three days and had two engaged sessions. It sends only first-visit,
> returned-visit, and qualified-return signals. The collector replaces the code
> with a month-specific digest, accepts those signals only in order on separate
> server days, and keeps only the short-lived state needed to prevent double
> counting. Aggregate monthly counts may be kept; participant-level state is
> deleted under the approved retention schedule.
>
> The measurement does not transmit page paths, URLs, referrers, search terms,
> note text, reader-submission content, names, email addresses, active-time
> traces, precise location, advertising identifiers, or device fingerprints.
> It is a browser-level estimate, so one person using several browsers may be
> counted more than once and several people sharing a browser may be counted
> together.

The final version must insert the approved collector-row deletion period,
operator identity or privacy contact, and an accurate explanation of any
provider processing required by law or the selected infrastructure.

## Control labels

Recommended plain labels:

- preference: **Private audience measurement**;
- enabled state: **Allow anonymous return measurement**;
- opt-out action: **Turn off and erase measurement state**;
- post-action confirmation: **Audience measurement is off on this browser.**

Do not use a manipulative confirm dialog, a prechecked consent claim where
consent is legally required, or language suggesting the reader will lose site
access by opting out. The site must remain fully readable with measurement off.

## Required verification before approval

- The notice appears before or alongside first initialization as required by
  the selected legal and infrastructure boundary.
- The control is keyboard reachable, screen-reader named, and usable without a
  member account.
- Opting out before initialization creates no month token and sends nothing.
- Opting out afterward stops timers and delivery, erases persistent qualifier
  and session state, and does not restore the prior token on opt-in.
- The endpoint, CDN, host, logs, traces, backups, rate limiter, and bot controls
  make every data-handling statement true.
- The published privacy contact and deletion period are verified, not invented.

Any mismatch between copy and actual handling blocks the canary.
