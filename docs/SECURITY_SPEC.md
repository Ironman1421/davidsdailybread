# Security and privacy specification

Status: active
Last threat-model review: 2026-07-31

## Assets

- integrity of published journalism and archives;
- GitHub, Anthropic, Google Forms/Sheets, domain, and social credentials;
- unpublished reader submissions and signatures;
- availability of both daily editions;
- downstream distribution state, including deduplication and analytics.

## Trust boundaries

The following are untrusted input even when produced by a model or collaborator:

- fetched pages, headlines, source URLs, and social trend material;
- every field in model-authored `content.json`;
- reader questions, letters, pins, and signatures;
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
   what the product needs to publish. Its approved private-store design is not
   yet provisioned.
3. The X adapter named in `BAKE.md` is outside the accessible repositories, so
   its credential handling, idempotency, and metrics cannot yet be audited.
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
