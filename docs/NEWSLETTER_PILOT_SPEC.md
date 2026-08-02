# Weekly newsletter pilot specification

Status: paused by founder; signup state preserved; no activation work authorized
Owner: David Friedhof
Last reconciled: 2026-07-31

## Controlling decision

David paused newsletter sending and all related activation work on 2026-07-31.
The previously approved four-week Buttondown plan is retained below only as a
guarded historical design. It is not an active pilot or a queue of next steps.

Preserve the existing live `/subscribe.html` state unless David approves a site
change. The form's presence, a new signup, completion of an old gate, or silence
does not authorize drafting, testing, configuration, credentialing, scheduling,
or sending. The website and RSS remain the canonical, complete record.

## Frozen historical format

The former working title was **The Weekly Loaf**. Its proposed Editorial Ledger
used this Guided Path:

1. **Start:** one development worth understanding first, with its canonical
   edition source.
2. **Browse:** a short shelf of the week's strongest reporting and tools.
3. **Do:** one practical workflow a reader can carry into the coming week.
4. **Rest:** a brief spiritual exhale that is distinct from Letters to the King.

Do not fill, update, test, or schedule this template while the pause is active.
If David explicitly restarts the work, any issue must link to canonical pages
rather than copying a whole edition, preserve factual sources, contain no
reader-visible em dash, and use reviewed Rest material rather than fabricated
reader mail.

## Signup and data boundary

- The current live signup page is preserved, not newly activated by this spec.
- `/subscribe.html` posts an email address directly to the official Buttondown
  embedded-subscribe endpoint for `davidsdailybread`.
- Buttondown double opt-in remains required. A submitted address is not an
  active subscriber until the reader confirms it.
- The repository, GitHub Actions, Supabase, logs, and public ledgers do not
  receive subscriber email addresses.
- Subscriber exports are not committed, attached to issues, or placed in normal
  artifacts. Buttondown remains the system of record for existing addresses.
- `privacy@davidsdailybread.com` is the verified public privacy contact. Its
  private forwarding destination is deliberately not recorded here.
- Privacy and deletion requests remain duties during the pause.

## No-activation gate

Sending and activation work remain disabled because of the founder's controlling
decision, regardless of whether any former operational gate could be completed.
Do not:

1. Draft or update an issue.
2. Choose a send date or time.
3. Configure or test a postal footer, sender identity, Reply-To, or unsubscribe
   flow for sending readiness.
4. Send a test or production email.
5. Add newsletter credentials, automation, paid features, or provider services.
6. Import, reactivate, export, or otherwise operate on a subscriber list for a
   future send.

The daily bake must never draft, schedule, or send email, and no newsletter
credential belongs in GitHub Actions. Work may resume only after David explicitly
reverses the pause and the founder doctrine, this specification, the
machine-readable contract, and tests are reconciled in one reviewed change.

## Historical operating loop

The former select, draft, test, verify, send, and measure loop is frozen. It is
preserved in repository history and `newsletter/weekly-ledger.md` for context,
not as authorized work.

## Resume rule

Only a new explicit decision from David can resume newsletter planning or
activation. That decision must define the intended role of email, consent and
privacy boundary, operating owner, budget, and sending gate. Silence does not
resume the plan.
