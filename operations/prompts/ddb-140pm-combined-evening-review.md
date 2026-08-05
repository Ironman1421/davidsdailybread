# DDB 1:40 PM combined evening review

Run once for today's evening edition in `America/Los_Angeles`. This is the only
candidate-selection pass before the bake. Target a validated private packet by
2:25 PM Pacific; the bake remains at 2:40 PM Pacific.

1. Read `FOUNDER_DOCTRINE.md`, `BAKE.md`, `BRAND.md`, and
   `operations/tools-workflows-research-handoff.contract.json`.
2. Read X Manager's exact
   `coordination/ddb/YYYY-MM-DD-tools-workflows-research.json` and matching
   Markdown memo. Require schema `x-manager-noon-research-v2`, the exact target
   date, and `status: completed`. If it says `blocked`, or X Pro and X Radar are
   not both recorded as used, do not manufacture a completed X handoff and do
   not upload a reviewed packet. Record the blocker so the 2:40 PM bake takes
   its explicit fallback path.
   Validate the machine record first with
   `python3 ddb_evening_handoff.py validate-noon --input <path> --date YYYY-MM-DD`.
3. Require `closingDeltaCheck.attempted: true`, `completed: true`, sources
   exactly `xPro` and `xRadar`, a current `observedAt`, and an explicit
   `changesFound` value. Confirm the delta check occurred after the initial X
   Pro and X Radar observations and within 30 minutes before X Manager closed
   the artifact. If late items were found, require the JSON and Markdown memo
   to show how they were added, held, or rejected before accepting the handoff.
4. Hash the X Manager JSON with SHA-256. Preserve that hash, X Pro observation,
   X Radar observation, closing-delta proof, and candidate IDs in the reviewed
   packet.
5. In this same session, perform DDB's own broader web research. Treat every X
   item as advisory. Independently fetch non-X official factual sources and
   non-X citable trend sources for every plausible item. DDB may add an
   independently discovered candidate with an empty `xManagerCandidateIds`
   list, but it must still have at least two DDB-checked source URLs.
6. Score each candidate using exactly 40% leverage, 30% broad applicability,
   20% repeatability, and 10% trend strength. Apply the gates in the shared
   contract. Make one selected, hold, or reject decision. Select 2–6 tools and
   2–6 workflows; never pad.
7. Write one `ddb-reviewed-evening-handoff-v1` JSON packet. Preserve honest
   caveats and uncertainty, source-check timestamps, verified claims, source
   lineage, all hold/reject reasons, and the fixed authority block with
   `publicationApproved: false`. Set a bounded expiry after the evening bake
   window.
8. Validate locally:

   ```bash
   python3 ddb_evening_handoff.py validate \
     --input /path/to/YYYY-MM-DD-reviewed-evening-handoff.json \
     --date YYYY-MM-DD
   ```

9. When production transport has received separate authorization and its two
   environment variables already exist, upload the validated packet with
   `ddb_evening_handoff.py upload` by 2:25 PM Pacific. Report the packet ID and
   receipt. Never log a token, publish an edition, or tell the bake to research
   again.

On the normal path, the next actor is the 2:40 PM bake and its only candidate
input is this reviewed packet. Do not queue X Manager research after this
review.
