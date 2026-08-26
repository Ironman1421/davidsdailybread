# Reviewed morning research handoff

The normal daily morning edition begins with one date-bound
`ddb-reviewed-morning-handoff-v1` packet completed before the 4:40 AM Pacific
bake. The packet is an editorial input. It explicitly does not authorize
publication.

## Two-stage sequence

1. X Manager combines bounded, already-available X observations with a
   versioned source manifest. It triggers no paid read and emits one
   deterministically ordered `x-manager-morning-candidate-ledger-v1` advisory
   ledger.
2. DDB checks the ledger sources independently, performs a bounded gap sweep
   across technology, markets, and science, and gives every ledger and gap
   candidate exactly one selected, hold, or reject decision.
3. DDB writes the reviewed packet before 4:40 AM. Every selected story includes
   verified non-X sources and complete editorial lineage.
4. The daily morning bake consumes a present, valid, unexpired packet's
   selected set for writing, Scripture pairing, rendering, and its final
   accuracy pass. It does not search for more candidates on that preferred
   path. If the packet is missing, stale, invalid, or unreachable, the bake
   fails open to BAKE.md's normal independent source ladder and still authors
   the ordinary scheduled morning edition.

X Manager uses the advisory `morning-news-v1` discovery rule. DDB's final
morning rule is `morning-editorial-v1`: 30% substance, 25% source authority,
20% verification depth, 15% freshness, and 10% reader relevance. The evening
Field Guide remains on `editorial-fit-v1` without alteration.

David approved this fail-open bake consumption on 2026-08-26. August 24, 25,
and 26 morning editions are not backfilled. Backfills keep their date-bounded
historical research procedure because no same-day reviewed packet can honestly
be reconstructed after the fact.

The August 5 Muse Code fixture is permanent regression evidence. X Manager
must label that signal `mustReview`, and DDB must record its explicit morning
disposition even when it is not selected.
