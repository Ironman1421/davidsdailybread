# Unified X Manager-to-DDB evening handoff

Status: production active; daily packets remain fail-closed when readiness
evidence is unavailable

## Why this replaces the old 2:40 flow

The old bake refreshed X Manager and fetched a discovery export at 2:40 PM.
That reopened research after DDB's intended combined review. The unified path
makes one editorial decision and hands that decision—not the raw candidate
queue—to the bake.

## Daily mechanics (Pacific time)

1. **12:45 PM — X Manager.** Research X Pro, X Radar, the budget-guarded
   monitor, and primary sources. Immediately before closing the handoff, run
   one final X Pro and X Radar delta check, reconcile late additions into the
   candidate decisions, and record timestamped proof. Close the JSON candidate
   record and Markdown audit memo by 1:35 PM. Neither file decides what runs.
2. **1:40 PM — DDB.** Read the exact X Manager artifact and hash while doing
   DDB's own broader web research. Independently verify official and trend
   sources. In this same pass, score every candidate at 40% leverage, 30% broad
   applicability, 20% repeatability, and 10% trend strength and record the
   final selected/hold/reject set.
3. **By 2:25 PM — private handoff.** Validate the
   `ddb-reviewed-evening-handoff-v1` JSON and upload it to X Manager's private
   `/api/ddb-handoff` store. The packet is bound to one date, expires, and says
   `publicationApproved: false`.
4. **2:40 PM — bake.** Fetch that exact date's reviewed packet. On the normal
   path, perform final source-accuracy, copy, and rendering work only. Do not
   refresh X, fetch the discovery export, do candidate research, or change the
   selected set.

The handoff is a durable D1 record rather than a direct task-to-task message.
The X Manager research remains a JSON-plus-Markdown local audit artifact; DDB's
final reviewed JSON is the only artifact the cloud bake consumes.

## Failure behavior

The fetch helper validates schema version, edition date and slot, expiry,
research attestations, the exact scoring rule and gates, source lineage, item
counts, and authority. A missing credential, network error, 404, stale packet,
or invalid packet becomes an explicit runner-local `available: false` record.
The bake then follows `BAKE.md`'s normal non-X source ladder. The fallback never
calls X Manager and never pads an edition.

## Operator commands

Validate a proposed packet locally:

```bash
python3 ddb_evening_handoff.py validate \
  --input /path/to/YYYY-MM-DD-reviewed-evening-handoff.json \
  --date YYYY-MM-DD
```

Upload it privately after both required environment variables are configured:

```bash
python3 ddb_evening_handoff.py upload \
  --base-url https://signal-ai-radar.fluxcognition.chatgpt.site \
  --input /path/to/YYYY-MM-DD-reviewed-evening-handoff.json
```

The helper reads `DDB_HANDOFF_WRITE_TOKEN` and
`X_MONITOR_SITES_BYPASS_TOKEN`; it never prints either value.

## Production receipt and future-change gate

David approved exact DDB head
`b7016408daeda0f2eabbfb91a43c20470df9311c` and X Manager head
`089adafa114789f940b929d8549f9da4f30a6098`. DDB PR 50 merged as
`5e040b8a8dd6228b9bbe2f968b5889d51bee9db8`; the reviewed D1 migration,
dedicated write credential, private canary, and the two in-place 12:45 PM and
1:40 PM automations were verified. The 2:40 PM bake remained unchanged.

This handoff is evening editorial discovery only. It grants no authority to
reuse X Manager's API read budget, deck, monitor, scoring, or targets for
outreach. A future change to deployment, migration, credentials, automation,
timing, or bake behavior requires its own reviewed heads and approval.
