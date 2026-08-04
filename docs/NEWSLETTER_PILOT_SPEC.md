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

Preserve the existing live `/subscribe.html` state unless David approves a site
change. Local research, information architecture, consent-flow design, provider
comparison, and non-networked interface prototypes are authorized. The form's
presence, a new signup, completion of an old gate, or silence does not authorize
issue drafting, send testing, provider configuration, list operations,
credentialing, scheduling, or sending. The website and RSS remain the canonical,
complete record.

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

- The current live signup page is preserved, not newly activated by this spec.
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
