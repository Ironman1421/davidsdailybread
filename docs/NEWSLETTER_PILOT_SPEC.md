# Weekly newsletter pilot specification

Status: signup approved; sending blocked pending activation gates
Owner: David Friedhof
Last reconciled: 2026-07-31

## Decision

David approved a four-week email pilot using Buttondown. It sends at most one
manual issue per week and pauses after issue four for a keep, change, or stop
decision. This is a new, consented list. No retired subscriber list is imported,
reactivated, or treated as permission.

The pilot has a hard monthly spend cap of $0. It must stop before a charge, paid
add-on, or subscriber count above the provider's free allowance. The website and
RSS remain the canonical, complete record; email is a weekly selection, not a
replacement for either daily edition.

## Editorial Ledger and Guided Path

The working title is **The Weekly Loaf**. Each issue is an Editorial Ledger that
uses the approved Guided Path:

1. **Start:** one development worth understanding first, with its canonical
   edition source.
2. **Browse:** a short shelf of the week's strongest reporting and tools.
3. **Do:** one practical workflow a reader can carry into the coming week.
4. **Rest:** a brief spiritual exhale that is distinct from Letters to the King.

The issue links to canonical pages rather than copying a whole edition. Every
factual statement keeps its source, reader-visible copy contains no em dash, and
the Rest section uses reviewed material rather than fabricated reader mail.

## Signup and data boundary

- `/subscribe.html` posts an email address directly to the official Buttondown
  embedded-subscribe endpoint for `davidsdailybread`.
- Buttondown double opt-in remains required. A submitted address is not an
  active subscriber until the reader confirms it.
- The repository, GitHub Actions, Supabase, logs, and public ledgers do not
  receive subscriber email addresses.
- Subscriber exports are not committed, attached to issues, or placed in normal
  artifacts. Buttondown is the system of record for the pilot list.
- `privacy@davidsdailybread.com` is the verified public privacy contact. Its
  private forwarding destination is deliberately not recorded here.
- Every issue provides the provider unsubscribe control. A privacy or deletion
  request is acknowledged and completed within seven days.

## Sending gate

Signup may reopen after the reviewed site change merges. Sending remains disabled
until all of the following are recorded as complete:

1. A valid physical postal address is configured in Buttondown and appears in a
   test footer. Use a street address, registered post office box, or registered
   private mailbox. Do not invent or publish a placeholder.
2. The first send date and Pacific time are chosen.
3. Issue 1 is drafted from canonical editions using
   `newsletter/weekly-ledger.md` and its links are checked.
4. A test email is received and reviewed on desktop and mobile, including the
   unsubscribe control, sender identity, postal address, and Reply-To behavior.
5. The confirmed subscriber count is within the free allowance and no paid
   feature or upgrade is enabled.

Production sends are manual in Buttondown during the pilot. The daily bake must
never draft, schedule, or send an email, and no newsletter credential belongs in
GitHub Actions.

## Weekly operating loop

1. Record the issue number and planned manual send window.
2. Select only material already published in canonical editions since the prior
   issue.
3. Fill the Guided Path template, preserve source links, and run the house-style
   check.
4. Send a test to the owner, inspect desktop and mobile, and correct the draft.
5. Reconfirm the postal footer, unsubscribe control, subscriber count, and $0
   provider state.
6. Manually send once. Never retry an ambiguous send until Buttondown delivery
   state has been inspected.
7. Record aggregate counts only: confirmed subscribers, unsubscribes, complaints,
   direct replies, and any provider metrics actually available. Unknown values
   remain null, never zero. Do not commit recipient-level data.

## Stop and decision rules

Stop before sending when consent is ambiguous, the postal footer is missing,
the preview has an unsupported claim or broken canonical link, the provider
would charge money, or an earlier send has ambiguous status. Stop the pilot
immediately for a send to an unconfirmed or imported address, a substantiated
consent complaint, or exposed subscriber data.

After issue four, pause. Record the aggregate results and David's explicit
decision to keep, change, or stop. Silence does not extend the pilot.
