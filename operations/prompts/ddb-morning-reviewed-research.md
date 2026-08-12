# DDB reviewed morning research

Produce the date-bound reviewed packet before 4:40 AM Pacific. This is
editorial preparation only and grants no publication authority.

1. Validate the X Manager ledger with `ddb_morning_handoff.py validate-ledger`.
2. Independently fetch and verify each plausible candidate from non-X primary
   sources. X observations are discovery lineage, never factual authority.
3. Perform a bounded source-manifest gap sweep for technology, markets, and
   science. Do not exceed the packet's recorded `maximumSources` per beat.
4. Apply the politics-free rule and `morning-editorial-v1` scoring. Give every
   ledger candidate and every gap candidate exactly one selected, hold, or
   reject decision. Never omit a `mustReview` candidate.
5. Preserve verified non-X sources and complete editorial lineage for selected
   stories. The bake owns writing and Scripture pairing.
6. Validate the completed packet with `ddb_morning_handoff.py validate`, then
   use `ddb_morning_handoff.py upload` to write it to the existing private
   handoff store before 4:40 AM.

Stop if the ledger or packet is late, stale, malformed, or incomplete. Do not
publish, invoke the bake, refresh X, trigger paid reads, or substitute
open-ended research.
