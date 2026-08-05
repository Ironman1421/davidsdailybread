# X account awareness and control-plane boundary

Status: designed; external reconciliation and publishing remain disabled

Owner: David Friedhof

## Decision

The David's Daily Bread repository is the system of record for DDB content,
brand rules, posting authority, provider receipts, replies, and distribution
metrics. The separate X Manager and Radar application is a read-only control
plane and research system. It may display DDB records and submit candidates for
review, but it does not own DDB history and it cannot publish for DDB.

The machine-readable boundary is
`operations/x-account-awareness.contract.json`.

## Why the boundary matters

The website, archive, and RSS are canonical. X posts are derived distribution
packages. Moving DDB's posting rules or publication history into a general X
research application would split authority, weaken correction handling, and
allow a monitoring failure to become a publishing failure.

The X Manager may cache DDB records for display. Every cached record must retain
its DDB source and freshness time, and the interface must describe that copy as
a mirror rather than the canonical record.

## Current authoritative records

- `archive.json`: canonical edition identity, URL, and lead.
- `distribution/x-broadcast-state.json`: bootstrap and recovered canonical X
  receipts.
- `distribution/ledger.json`: permanent edition-derived distribution records
  and metric snapshots.
- `distribution/x-replies.json`: published reply strategy baseline, receipts,
  and outcome snapshots.
- `operations/x-broadcast.contract.json`: protected publisher controls.

The current permanent edition distribution ledger has no post entries. That is
an explicit coverage gap, not evidence that no DDB posts exist.

## Required awareness loop

1. DDB creates or resolves the source record before posting.
2. The approved posting path records a pre-mutation reservation when the
   existing broadcast contract requires one.
3. A successful provider mutation is read back from X.
4. DDB records the exact text, provider post ID and URL, publication time,
   source record, operator, and activity class.
5. Replies remain in their separate public reply ledger because they have a
   different approval and measurement contract.
6. The X Manager reads the DDB records and presents a combined account view.
7. A future read-only reconciliation compares the provider timeline with the
   ledgers and flags unmatched activity in either direction.

Reconciliation never deletes, edits, reposts, or retries. An ambiguous or
unmatched item goes to David for review.

## Integration direction

The X Manager reads only public or explicitly exposed DDB operational records.
It does not receive the DDB X write token. A future read-only X credential must
be separately authorized, use the official API, verify the exact account, and
remain incapable of posting.

Radar discoveries stay in the research system until David chooses one for a
DDB editorial package. Selection is not publication approval. The chosen item
must still pass the DDB source, brand, editorial, rights, and publishing gates.

## Activation gates

This design does not authorize a provider connection, credential installation,
scheduled reconciliation, deployment, spend, reply, or post. Live account
reconciliation requires all conditions listed in the machine-readable contract
and a separate explicit decision from David.
