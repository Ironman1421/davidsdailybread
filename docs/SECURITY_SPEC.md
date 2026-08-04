# Security and privacy specification

Status: active
Last threat-model review: 2026-08-04

## Assets

- integrity of published journalism and archives;
- GitHub, Anthropic, Google Forms/Sheets, domain, and social credentials;
- unpublished reader submissions and signatures;
- future account credentials, sessions, personal archives, prayer content,
  relationship graphs, safety reports, and moderation records;
- availability of both daily editions;
- downstream distribution state, including deduplication and analytics.

## Trust boundaries

The following are untrusted input even when produced by a model or collaborator:

- fetched pages, headlines, source URLs, and social trend material;
- every field in model-authored `content.json`;
- reader questions, letters, pins, and signatures;
- account profile fields, personal-history imports, prayers, invitations,
  reports, blocks, appeals, and community contributions;
- repository issues, commit messages, pull-request text, and workflow inputs;
- third-party packages, GitHub Actions, CDNs, and remote scripts.

## Required controls

### Rendering

- Publish only absolute, credential-free HTTPS source URLs.
- Escape all reader and editorial plain text at the final output boundary.
- Parse the single permitted dek markup shape; never pass arbitrary model HTML.
- Validate the complete candidate output before writing generated files.
- Reject unresolved template tokens, forbidden punctuation, wrong slot schemas,
  and over-length distribution headlines.
- Treat published history as immutable during a bake. Permit exactly one new
  `editions/<date>-<slot>.html` path, reject staged/deleted/renamed or prior-
  edition changes, and stage only the exact expected edition.
- Bind selected reader questions, letters, names, signatures, and state keys to
  the committed Counter/satchel records before rendering or updating state.

### Automation and credentials

- Give the editorial agent no push credential. Preserve checkout credential
  isolation until the guarded publish step.
- Use least-privilege, repository-scoped secrets. Never place a token in a URL
  that can be printed, an artifact, generated content, or repository history.
- Pin third-party Actions and CLI dependencies to reviewed immutable versions;
  upgrades require a normal pull request and green render tests.
- Run CodeQL for Python and browser JavaScript on pull requests, `main`, and a
  weekly schedule; use Dependabot PRs to review pinned Action upgrades.
- Set explicit workflow permissions and serialize every workflow that can write
  `main` or shared generated state.
- Before protecting `main`, split authoring and publishing onto fresh runners,
  retire Counter sync as a repository writer, and install the repository-only
  `ddb-publisher` GitHub App defined in `docs/PUBLISHER_IDENTITY_SPEC.md`.
- Protect `main` with required CI and review rules while granting only
  `ddb-publisher[bot]` an explicit bypass. The built-in `GITHUB_TOKEN`, reader
  broker, model, human owner, deploy keys, PATs, Dependabot, and Pages have no
  routine bypass.
- Mint the publisher token only after uncredentialed validation. Never hand an
  untrusted editorial process and a later publisher credential the same runner.

### Reader privacy

- Private-boundary implementation and reopening preparation for Ask the Baker,
  Letters to the King, and Crumb Board are active roadmap work. Public intake
  remains closed until the private boundary is verified and David approves the
  exact cutover. The approved local interim page removes the Google form
  endpoint and submission controls, preserves browser-local notes and all four
  exports, and turns Counter sync into a no-op. Deployment, external form/Sheet
  changes, data migration, legacy queue deletion, and history rewriting remain
  unauthorized.
- Tell submitters that their text and signature may be public and prohibit
  sensitive information.
- Do not expose the full unpublished queue in a public repository or a
  published-to-web spreadsheet. Move ingestion to a private store and export
  only the selected, consented item needed for publication.
- Do not place unpublished reader content in the logs or normal artifacts of a
  public GitHub repository. Use the private handoff and retention controls in
  `docs/READER_STORE_SPEC.md`.
- Define retention and deletion behavior before collecting email addresses,
  account identifiers, or analytics tied to a person.
- The existing `/subscribe.html` state is preserved while newsletter strategy
  and local product prototypes proceed. Any address submitted there posts
  directly to Buttondown with double opt-in; subscriber addresses remain in
  Buttondown and may not enter this repository, GitHub Actions, Supabase, logs,
  or public metrics. No issue drafting, send testing, provider configuration,
  list operation, credentialing, activation, or sending is authorized. Privacy
  requests use the verified `privacy@davidsdailybread.com` contact and complete
  within seven days.
- Audience measurement follows `docs/AUDIENCE_MEASUREMENT_SPEC.md`. Production
  collection is disabled until David approves the provider, exact payload,
  retention, reader notice, opt-out, owner, credential boundary, and budget.
  Names, email addresses, note text, submission content, retained raw IP
  addresses, precise location, advertising identifiers, cross-site tracking,
  and fingerprinting are forbidden.
- The local audience prototype remains absent from public templates and its
  checked-in browser configuration remains `enabled: false` with no endpoint.
  Any approved collector must derive server receipt days, reject unordered or
  same-day milestone transitions, domain-separate token digests by month, avoid
  request-body and identifier logging, and purge participant-level state after
  aggregate close under `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md`.
- The selected Cloudflare Worker + D1 implementation remains local and
  canary-only in code. Its checked-in template is disabled, contains
  unprovisioned identifiers, has no route or Cron Trigger, disables observability
  and previews, and accepts no production mode. External provider metadata and
  control behavior still require canary evidence before any production claim.

### Accounts, prayer, and community

The 2026-08-04 founder decision authorizes architecture, local implementation,
and testing across the roadmap. Before any external account or community
activation, the exact release must prove all applicable controls below:

- Guest access remains available for canonical public reading. Account-required
  features collect only fields required for their stated purpose.
- Personal notes, saved material, prayer journals, answered-prayer markers,
  service reflections, and relationship data are private by default. Public is
  never a preselected audience.
- Every shared item records the reader-selected audience and enforces it at the
  server boundary. A client-side hidden state is not authorization.
- Readers can export their personal data, delete eligible private data, revoke
  other sessions, leave a circle, and understand what cannot be removed from an
  already published public record.
- Passwords, recovery secrets, session tokens, invitation tokens, encryption
  keys, and raw deletion tokens never enter logs, analytics, prompts, URLs,
  repository history, or ordinary artifacts.
- Prayer and spiritual data may not be sold, licensed, used for behavioral
  advertising, joined to a cross-site identity graph, or included in general
  product analytics.
- Notifications use opaque event identifiers where practical and exclude
  sensitive prayer text from lock-screen payloads by default.
- Every relationship surface has report, block, leave, remove, invitation,
  rate-limit, audit, and kill-switch behavior. Public contribution surfaces
  also require moderator queues, appeals, and anti-evasion controls.
- Community rules prohibit identifying details about other people, financial
  solicitation, romantic recruitment, coercion, targeted harassment,
  political campaigning disguised as prayer, and medical claims that replace
  professional care.
- The service never promises continuous monitoring or emergency response.
  Crisis flows provide reviewed routes to immediate help, minimize disclosure,
  and do not present volunteers or the product as clinicians or emergency
  services.
- Age eligibility, guardian consent where applicable, grooming prevention,
  moderator access, evidence preservation, law-enforcement request handling,
  and jurisdictional obligations require a dedicated review before trusted
  circles or direct messaging can activate.
- Private/direct messaging requires a separate abuse, age-safety, encryption,
  retention, moderation-access, reporting, and incident-response decision. It
  is not required to ship the network.

Every live release needs a named operator, data map, retention schedule,
deletion and export tests, authorization tests, abuse and rate-limit tests,
backup and restore evidence, rollback, incident path, cost ceiling, reader
notice, and David's approval of the exact reviewed package.

### Distribution

- Every channel adapter needs an edition-scoped idempotency key, a length and
  character gate, a durable attempt ledger, bounded retries, and provider
  read-back before reporting success.
- Content generation and provider posting are separate authorities. A source
  page, model response, or repository issue must never be able to request a
  credentialed post directly.

## Current exceptions requiring closure

1. `main` is not protected even though repository policy calls CI the merge
   gate. Its approved identity/ruleset design is not yet provisioned.
2. The Counter sheet and committed `counter.csv` expose the reader queue beyond
   what the product needs to publish. A local interim closure is prepared, but
   it is not deployed, the external form and Sheet remain unchanged, and the
   approved private-store design is not provisioned.
3. The repository-owned X canonical-broadcast adapter is implemented with a
   separate read-only post-bake job, durable receipt artifacts, read-back, and
   a kill switch. It remains production-disabled pending environment and
   credential provisioning plus a reviewed canary.
4. Public pages rely on inline JavaScript and third-party font/PDF CDNs without a
   strong Content Security Policy or fully local assets.
5. Repository-level Dependabot alerts are disabled. Version-update PRs are
   configured, but the owner must enable vulnerability alerts in GitHub.
6. The current public-repository diagnostic artifact can include `content.json`
   and a raw model log. Treat both as unpublished reader data during the private
   store cutover; the target design prohibits this transfer.

Exceptions are tracked work, not accepted permanent architecture.

## Incident response

For a suspected bad publish, exposed secret, or reader-data leak:

1. Stop the affected scheduled workflow without deleting evidence.
2. Preserve the run URL, commit SHA, generated artifact, and provider receipt.
3. Revoke or rotate affected credentials outside git.
4. Remove public data through a reviewed forward fix; rewrite history only after
   the exact exposure and recovery implications are understood.
5. Publish a correction when reader-visible facts changed.
6. Add a regression test reproducing the failure before resuming automation.
