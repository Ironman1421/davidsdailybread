# Minimum viable safety and faster delivery

Status: approved direction, pending protected-main release

Owner: David Friedhof

Program item: `DDB-PC-031`

Machine-readable contract:
`operations/minimum-viable-safety.contract.json`

## Decision

Use the least process that materially protects readers, the publication,
credentials, privacy, money, and recovery. Availability and the twice-daily
cadence are safety properties. Routine recovery must not become a separate
governance project.

The controller owns three lanes:

1. Routine operations stay outside the project queue. Scheduled bakes and their
   exact canonical X broadcasts have priority. Bounded stale-run cancellation
   and one exact-commit Pages rebuild are standing-authorized recovery actions.
2. Local work permits up to three approved items at once, each on its own clean
   branch. It may research, implement, test, push a branch, and open a pull
   request. It may not merge or change live state.
3. Production mutation permits one change at a time. A routine operation may
   acquire this lane without becoming a queued program item and preempts a
   queued project release.

Only the controller changes queue state or assigns items. Parallel work does
not authorize workers to select their own successors.

## Standing-authorized operations

### Scheduled publication

A normal morning or evening bake may run without per-edition approval when it
follows `BAKE.md`, preserves idempotency, uses the protected publisher, and
passes its existing validation. A publication failure is an incident to recover
from, not proof that more approval layers are needed.

### Stale-run cancellation

The controller or a reviewed watchdog may cancel pending or queued publication
runs after 15 minutes only when a run is superseded or is blocking a newer
nominal slot, its exact state is known, and no publisher credential or ambiguous
write is active. Older runs are cancelled before the newest nominal slot. A
merely slow run with no newer blocked slot is not cancelled. An active or
ambiguous write is not routine and must stop for reconciliation. Routine
recovery does not backfill an expired slot.

### Pages recovery

When a validated commit is on `main` but the matching public edition, homepage,
archive, or RSS is absent or stale, the controller may request one Pages rebuild
for that exact commit. It then verifies the exact edition, homepage,
`archive.json`, and `feed.xml`. A second rebuild, target mismatch, or ambiguous
result escalates.

### Canonical X broadcast

The active canonical broadcaster may publish one deterministic post for each
newly published edition after the exact edition URL is publicly ready. The post
must use the immutable dated URL and existing idempotency and kill-switch
controls. This authority excludes backfills, replies, quotes, likes, follows,
campaign originals, generated media, account changes, and broadcaster
migration.

### Bounded low-risk release

A low-risk release may merge through the protected pull-request path without a
second exact-SHA approval when all of these are true:

- the change stays within the existing architecture and public contracts;
- it changes no credential, permission, ruleset, provider, provider terms,
  schedule, spending, personal or spiritual data boundary, email operation,
  community surface, public reply, generated media, theology, or public brand;
- the complete diff is reviewed and the required Merge gate and CodeQL checks
  are green;
- no bake or other production mutation is active when the merge begins;
- a concrete rollback is available through the protected path; and
- the affected public or operational surface passes its post-merge health
  check.

If classification is uncertain, the change is not low risk.

## Explicit approval boundaries

David's explicit approval remains mandatory for:

- spending or a paid-plan change;
- credentials, authentication, account security, permissions, or recovery
  material;
- a new provider, provider provisioning, or acceptance of provider terms;
- collection, migration, exposure, retention, or deletion of personal or
  spiritual data;
- email drafting, testing, list operation, scheduling, or sending;
- community, account, prayer-sharing, contribution, or private-message
  activation;
- context-sensitive public replies or other noncanonical public interactions;
- generated-media inputs, generation, or publication;
- theology, Scripture policy, or public brand changes; and
- destructive or difficult-to-reverse actions.

The outreach campaign remains inactive. This decision does not satisfy or
replace its activation receipt.

## Evidence and escalation

Routine work records one concise receipt containing the target, action, result,
health check, and rollback state. Do not create approval-only commits or repeat
the same evidence across multiple files. Preserve more evidence only for an
incident, a sensitive decision, or a failed bounded recovery.

Stop and escalate when a target is ambiguous, a health check fails after the
one allowed recovery, a proposed action crosses a sensitive boundary, or the
production lane cannot be proven idle.
