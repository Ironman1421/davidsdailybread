# Scheduled publisher identity and main-protection specification

Status: approved design, not provisioned
Machine-readable contract: `operations/publishing.contract.json`

## Decision

There is one scheduled writer to `main`: a custom GitHub App named
`ddb-publisher`, displayed as `ddb-publisher[bot]`. `counter-sync` is retired;
the private reader broker has no repository permission. The normal
`GITHUB_TOKEN` becomes read-only and cannot bypass the `main` ruleset.

The App is installed only on `Ironman1421/davidsdailybread`. Its only optional
repository permission is Contents: read and write; GitHub's required Metadata
permission remains read-only. Do not grant Actions, Administration, Secrets,
Workflows, Issues, Pull requests, Pages, or organization permissions. The App
does not need webhooks, user authorization, an OAuth callback, or access to any
other repository.

## Identity matrix

| Identity | Authority | May bypass `main`? | Credential exposure |
| --- | --- | --- | --- |
| `github-actions[bot]` | Read checkout and orchestrate | No | Per-run built-in token, `contents: read` |
| Editorial Claude process | Research, write, and render in author job | No | Claude credential only; no GitHub App key or token |
| `ddb-reader-broker` | Reserve/finalize/release one private reader plan and private handoff | No GitHub authority | Edge Function broker secret in trusted steps only |
| `ddb-publisher[bot]` | Push one validated generated commit | Yes, sole bypass | One-hour installation token minted in publisher job |
| `Ironman1421` | Pull requests and ruleset administration | No routine bypass | Human account; rule edits are break glass |
| GitHub Pages and Dependabot | Read/deploy or open PRs | No | Provider-managed, no direct push |

## Job isolation and publish protocol

The target workflow has three jobs on separate fresh GitHub-hosted runners:

1. `prepare-reader-plan` reserves a morning plan and creates one-use private
   handoff capabilities. It has no publisher key. Evening and backfill runs
   produce a no-reader reservation receipt.
2. `author-edition` checks out the captured base SHA with
   `persist-credentials: false`, fetches only the selected plan, runs Claude and
   the deterministic renderer, validates candidate output, builds a manifest,
   and uploads one bundle to the private handoff. It never receives a
   repository-write token. Its output and logs do not contain reader data.
3. `validate-and-publish` starts on a fresh runner, checks out `main` without
   credentials, privately downloads the bundle, verifies its digest, base SHA,
   edition ID, file allowlist, no-symlink rule, renderer tests, and archive
   contract. It aborts if remote `main` changed. Only then does it mint the App
   installation token, create one atomic commit, push, verify the exact remote
   SHA, and finalize the reader batch.

The publisher never rebases generated output over a changed base. A stale base
fails and is retried as a fresh bake. On any failure before a verified remote
push, an `always()` cleanup releases the reservation; lease expiry is the
second safety net. If the push succeeds but store finalization fails, retry only
finalization against the verified edition and SHA; never bake or push again.

No unpublished reader payload or generated bundle uses a normal Actions
artifact. Anyone with read access to a public repository can access its
artifacts. The current bake therefore withholds raw model output from Actions
logs, creates diagnostics only on failure, and uploads only a whitelist-built
summary with no reader or model payload. The private-store cutover must preserve
that boundary.

## GitHub App setup

Create the App under the `Ironman1421` account:

- name/slug: `ddb-publisher` if available;
- homepage: the production site;
- webhook: inactive;
- user authorization: inactive;
- repository permission: Contents read/write, Metadata read;
- account and organization permissions: none;
- installation: selected repository only,
  `Ironman1421/davidsdailybread`.

Store the App client ID as repository variable
`DDB_PUBLISHER_CLIENT_ID`. Create a `production-publish` GitHub Environment
whose deployment branch is exactly `main`, and store the complete private key
there as environment secret `DDB_PUBLISHER_PRIVATE_KEY`. Only the publisher job
declares this environment. Never commit either value. Rotate the key on
exposure, on maintainer departure, and at least annually; delete the old key
after a canary proves the new one.

The workflow uses
`actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1`
and explicitly requests only `permission-contents: write`. The action is pinned
to the reviewed v3 commit current on 2026-07-31. Dependabot may propose a new
commit, but upgrading requires a normal reviewed PR and green tests.

Mint the token after all uncredentialed checks. Do not put it in the remote URL,
arguments, files, artifacts, or model environment. Configure git authentication
through a masked, transient credential helper and remove it in an `always()`
step. Keep checkout credential persistence disabled. Allow the token action to
revoke the installation token at job end.

Use the App's bot identity for author and committer. Obtain its numeric bot user
ID through GitHub's API and set the noreply address documented by the token
action. One edition produces one commit so the remote SHA is the publication
receipt and store-finalization key.

## `main` ruleset

Create an active repository branch ruleset targeting only `refs/heads/main`.
Evaluate mode is not assumed because it is unavailable on many non-Enterprise
plans. Before activation, prove the App token on a temporary branch and confirm
the integration is selectable as the bypass actor. The active rules are:

- require a pull request for every non-bypass change;
- require `gate`, `Analyze (python)`, and
  `Analyze (javascript-typescript)`;
- require all review conversations resolved;
- require linear history;
- block branch deletion and force pushes; and
- allow exactly one bypass actor: the `ddb-publisher` GitHub App integration,
  mode `always`.

Do not give a bypass to the repository owner, administrator role,
`github-actions[bot]`, a deploy key, a PAT, Counter sync, Dependabot, Claude, or
Pages. The human break-glass procedure is to edit or temporarily disable the
ruleset in GitHub's audit trail, repair through a named incident branch, then
restore and verify the rules. It is not a standing bypass.

Required approvals begin at zero because this is currently a solo personal
repository and a self-approval is not independent review. Requiring one now
would deadlock ordinary PRs without improving safety. As soon as a second
trusted maintainer with write access accepts review duty, change the contract
and ruleset to one approval, dismiss stale approvals, and require approval of
the most recent reviewable push.

Ruleset activation is blocked until the actual App integration ID exists. Save
the exported ruleset JSON and compare it with
`operations/publishing.contract.json` after every governance change.

## Canary and acceptance tests

Before active protection:

1. Merge the private-store and split-workflow implementation by the current PR
   path while `main` is still unprotected.
2. Disable `counter-sync` and set repository Actions defaults to read-only.
3. Install the App, add its variable/secret, and run a dry-run publisher that
   mints a token but performs no push.
4. Prove the App can push a disposable canary branch, delete that branch, then
   create and activate the `main` ruleset with the App integration as its sole
   bypass actor.
5. Run one non-reader evening canary through `ddb-publisher[bot]`; verify the
   bot actor, one commit, exact base SHA, remote receipt, Pages deployment, and
   token revocation.
6. Run one supervised morning canary; verify one private plan, no public
   payload in logs/artifacts, exact provenance, remote receipt, finalization,
   and handoff deletion.
7. Activate the ruleset. Attempt and document: owner direct push rejected,
   built-in `GITHUB_TOKEN` push rejected, Counter writer absent, failing PR
   rejected, green PR accepted, publisher canary accepted, force push rejected,
   and branch deletion rejected.

If the publisher App is unavailable, fail closed and alert. Do not weaken the
ruleset or fall back to a PAT or writable `GITHUB_TOKEN`. A missed edition is
safer and recoverable through supervised `workflow_dispatch` using the same
App identity.

## Primary references

- [GitHub ruleset rules and bypass actors](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub App installation tokens](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-an-installation-access-token-for-a-github-app)
- [GitHub App authentication in Actions](https://docs.github.com/en/enterprise-cloud@latest/apps/creating-github-apps/authenticating-with-a-github-app/making-authenticated-api-requests-with-a-github-app-in-a-github-actions-workflow)
- [Fresh runner boundary per Actions job](https://docs.github.com/en/actions/get-started/understand-github-actions)
- [Workflow artifact access](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)
- [`actions/create-github-app-token`](https://github.com/actions/create-github-app-token)
