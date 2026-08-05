# Newsletter retention option specification

Status: strategy and local integration planning active; operations disabled
Owner: David Friedhof
Last reconciled: 2026-08-04

## Controlling decision

David authorized newsletter strategy and local product-integration prototypes
as part of the durable-moat direction on 2026-08-04. The newsletter is a
candidate owned retention path back to canonical work. The previously approved
four-week Buttondown plan remains a guarded historical design, not an active
pilot or a queue of operational next steps.

Preserve the current fail-closed `/subscribe.html` state unless David approves
a site change. Local research, information architecture, consent-flow design,
provider comparison, and non-networked interface prototypes are authorized.
No public form or provider endpoint is present, and no new address is collected.
Completion of an old gate, local prototype, or silence does not authorize issue
drafting, send testing, provider configuration, list operations, credentialing,
scheduling, or sending. The website and RSS remain the canonical, complete
record.

## Frozen historical format

The former working title was **The Weekly Loaf**. Its proposed Editorial Ledger
used this Guided Path:

1. **Start:** one development worth understanding first, with its canonical
   edition source.
2. **Browse:** a short shelf of the week's strongest reporting and tools.
3. **Do:** one practical workflow a reader can carry into the coming week.
4. **Rest:** a brief spiritual exhale that is distinct from Letters to the King.

Do not fill, update, test, or schedule this template without a scoped operational
pilot approval. Any future issue must link to canonical pages rather than copy a
whole edition, preserve factual sources, contain no reader-visible em dash, and
use reviewed Rest material rather than fabricated reader mail.

## Signup and data boundary

- The current fail-closed signup page is preserved, not reopened by this spec.
- `/subscribe.html` contains no form, email input, provider endpoint, or public
  email address and collects no new address.
- Buttondown remains only the historical provider named by the frozen pilot.
  This document does not authorize account access or provider mutation.
- The repository, GitHub Actions, Supabase, logs, and public ledgers do not
  receive subscriber email addresses.
- Subscriber exports are not committed, attached to issues, or placed in normal
  artifacts. Buttondown is the system of record for the pilot list.
- A verified privacy contact is required before any signup surface can reopen.
  Do not add or guess a public address as part of local prototype work.
- Every issue provides the provider unsubscribe control. A privacy or deletion
  request is acknowledged and completed within seven days.

## Operational gate

Strategy and local product-integration prototypes are active. Operational work
remains disabled regardless of whether a former gate could be completed. Do not:

1. Draft or update an issue.
2. Choose a send date or time.
3. Configure or test a postal footer, sender identity, Reply-To, or unsubscribe
   flow for sending readiness.
4. Send a test or production email.
5. Add newsletter credentials, automation, paid features, or provider services.
6. Import, reactivate, export, or otherwise operate on a subscriber list for a
   future send.

The daily bake must never draft, schedule, or send email, and no newsletter
credential belongs in GitHub Actions. An operational pilot may begin only after
David approves its exact role, issue package, operator, provider state, consent
and privacy boundary, cost ceiling, test plan, schedule, rollback, and sending
gate, with the machine-readable contract and tests reconciled in one reviewed
change.

## Historical operating loop

The former select, draft, test, verify, send, and measure loop is frozen. It is
preserved in repository history and `newsletter/weekly-ledger.md` for context,
not as authorized work.

## Activation rule

The 2026-08-04 decision resumed strategy and local product-integration planning.
Only a later scoped decision from David can authorize issue drafting or any
provider, list, test-send, schedule, credential, or production-send operation.
Silence and completed local work do not activate the pilot.
