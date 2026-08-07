# Security and privacy specification

Status: active
Last threat-model review: 2026-08-07

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
- For every morning story's Scripture, accept only a verified catalog identifier
  and a required reader-directed plain-text connection from `content.json`.
  Reject claims of divine approval, condemnation, judgment, or fulfilled
  prophecy. Supply exact BSB text, reference, translation label, and Bible link
  from the repository-owned catalog, never from model-authored fields.
- Reject political and geopolitical framing in morning editorial fields before
  rendering. Do not scan source URLs or renderer-owned Scripture text.
- Treat published history as immutable during a bake. Permit exactly one new
  `editions/<date>-<slot>.html` path, reject staged/deleted/renamed or prior-
  edition changes, and stage only the exact expected edition.
- While public intake is paused, reject Ask the Baker, reader Letter, and Crumb
  Board fields before rendering or updating state. Only reviewed house-satchel
  material may enter a new edition.

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
  keep Counter sync retired as a repository writer, and install the repository-only
  `ddb-publisher` GitHub App defined in `docs/PUBLISHER_IDENTITY_SPEC.md`.
- Protect `main` with required CI and review rules while granting only
  `ddb-publisher[bot]` an explicit bypass. The built-in `GITHUB_TOKEN`, reader
  broker, model, human owner, deploy keys, PATs, Dependabot, and Pages have no
  routine bypass.
- Mint the publisher token only after uncredentialed validation. Never hand an
  untrusted editorial process and a later publisher credential the same runner.

### Reader privacy

- New Ask the Baker, Letters to the King, and Crumb Board intake is closed until
  a private boundary is verified and David explicitly reopens it. The deployed
  site closure, retired Counter writer, removed tip-level `counter.csv`, and
  preserved Chronicles exports remain production truth. Do not reactivate
  submission controls, alter external intake providers, delete the frozen
  queue, or rewrite history while the pause is active.
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
- The current fail-closed `/subscribe.html` state collects no address and has
  no provider endpoint. Local retention strategy and product-integration
  prototypes may proceed, but no drafting, sending test, provider operation,
  list operation, credentialing, address collection, activation, or sending is
  authorized.
- The Supabase reader-store foundation may be implemented and tested locally.
  No project, resource, link, remote migration, Edge Function, canary, traffic,
  or deployment is authorized without David's scoped approval of the exact
  external step and a reconciled repository decision.
- Cloudflare Workers + D1 audience measurement remains local and unprovisioned.
  No account, resource, endpoint, route, credential, canary, deployment,
  collection, baseline, or spend is authorized.

### Accounts, prayer, and community

Local architecture, implementation, and testing are authorized. Before any
external account or community activation, the exact release must prove all
applicable controls below:

- Guest access remains available for canonical public reading. Account-required
  features collect only fields required for their stated purpose.
- Notes, saved material, prayer journals, answered-prayer markers, service
  reflections, and relationship data are private by default. Public is never a
  preselected audience.
- Every shared item records the reader-selected audience and enforces it at the
  server boundary. Client-side hiding is not authorization.
- Readers can export personal data, delete eligible private data, revoke other
  sessions, leave a circle, and understand any public-record boundary.
- Passwords, sessions, recovery secrets, invitation tokens, encryption keys,
  prayer text, and deletion tokens never enter logs, analytics, prompts, URLs,
  repository history, or ordinary artifacts.
- Every relationship surface has report, block, leave, remove, rate-limit,
  audit, and kill-switch behavior. Public contributions also require moderator
  queues, appeals, and anti-evasion controls.
- The service never promises continuous monitoring or emergency care. Direct
  messaging requires a separate abuse, age-safety, encryption, retention,
  reporting, and incident-response decision and may remain omitted.

### Installable web app

- The manifest, service worker, and install layer reuse canonical URLs. They do
  not create an app-only edition, archive, correction record, or account path.
- The service worker handles only same-origin GET requests. HTML navigations and
  canonical data use network-first behavior with the browser HTTP cache bypassed
  so online corrections replace prior cached responses before display.
- Only successful, non-redirected, same-origin basic responses without
  `no-store` may be cached. Query strings and fragments are not persisted, and
  runtime caches are bounded.
- Cache cleanup deletes only cache names owned by the `ddb-pwa-` prefix. It does
  not touch browser `localStorage`, existing `ddb-note:*` or
  `ddb-note-style:*` keys, Chronicles exports, or other origins.
- A new worker waits until the reader chooses refresh. Install prompts are
  reader-initiated. Each new cache generation revalidates shell assets before
  activation. Push, notification, background-sync, analytics, and
  external-provider APIs remain absent and unauthorized in this package.

### Distribution

- Every channel adapter needs an edition-scoped idempotency key, a length and
  character gate, a durable attempt ledger, bounded retries, and provider
  read-back before reporting success.
- Content generation and provider posting are separate authorities. A source
  page, model response, or repository issue must never be able to request a
  credentialed post directly.
- Gemini Omni campaign generation accepts only already-public canonical DDB
  inputs and rights-cleared assets. Master prompts, watchlists, unpublished
  strategy, credentials, private analytics, reader material, and unpublished
  editions never enter the consumer provider. Verify the exact approved Google
  account and plan, use a temporary chat or Keep Activity off, submit no
  feedback containing campaign material, preserve provider watermarking,
  disclose material AI generation, and keep the full provenance record outside
  the public repository. Provider upload and generation require separate exact
  input-package approval; publication requires separate exact final-package
  approval.

## Current exceptions requiring closure

1. The external legacy Counter sheet and repository history retain more reader
   queue exposure than the target design permits. The tip copy is removed and
   public site intake is closed, but the private store remains unprovisioned and
   external form, Sheet, migration, deletion, and history actions remain gated.
2. The repository-owned X canonical-broadcast adapter is implemented with a
   separate read-only post-bake job, durable receipt artifacts, read-back, and
   a kill switch. It remains production-disabled pending environment and
   credential provisioning plus a reviewed canary.
3. Public pages rely on inline JavaScript and third-party font/PDF CDNs without a
   strong Content Security Policy or fully local assets.
4. Repository-level Dependabot alerts are disabled. Version-update PRs are
   configured, but the owner must enable vulnerability alerts in GitHub.
5. X account security is ready through a passkey verified in the official UI.
   David reports that the account has always been passwordless, so the
   password-dependent reset-protection control is not applicable without
   creating an additional credential. The unsaved change was discarded. X
   campaign readiness remains blocked because the latest observed morning and
   evening Spark post links resolved to the mutable homepage instead of exact
   edition pages.

Exceptions are tracked work, not accepted permanent architecture.

Closed control: `main` is protected by active ruleset 20451115. The repository-
only `ddb-publisher` App is the sole bypass actor; the built-in token, model,
human owner, PATs, deploy keys, Dependabot, and Pages have no routine bypass.

## Incident response

For a suspected bad publish, exposed secret, or reader-data leak:

1. Stop the affected scheduled workflow without deleting evidence.
2. Preserve the run URL, commit SHA, generated artifact, and provider receipt.
3. Revoke or rotate affected credentials outside git.
4. Remove public data through a reviewed forward fix; rewrite history only after
   the exact exposure and recovery implications are understood.
5. Publish a correction when reader-visible facts changed.
6. Add a regression test reproducing the failure before resuming automation.
