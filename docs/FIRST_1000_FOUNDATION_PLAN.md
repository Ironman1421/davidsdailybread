# Foundation for the first 1,000

Status: active local work package; external actions remain separately gated

Owner and final decision-maker: David Friedhof

Last reconciled: 2026-08-07

## Outcome

Build a trustworthy, measurable path to the first 1,000 genuinely engaged
returning people as Phase 0 and Phase 1 of the durable-moat roadmap, without
weakening reader privacy, sourcing, moderation, or founder control.

The twice-daily product already supplies substantial content. The immediate
work is to make the mission clear, protect the trust boundary, measure return
honestly, and learn which approved discovery activity produces durable website
readership.

## Workstream 1: governing continuity

- Land the founder doctrine and reconcile lower-level mission, roadmap,
  newsletter, distribution, security, contract, and test language.
- Keep `BRAND.md` authoritative for reader-visible rules and `BAKE.md`
  authoritative for an approved bake session.
- Preserve the rule that local work and recommendations do not authorize
  publishing, sending, spending, provisioning, partnerships, or new governance.

Exit: `main` contains one coherent hierarchy and CI enforces its material
boundaries.

## Workstream 2: reader trust prerequisite

`docs/AUDIT_2026-07-31.md` identifies the public waiting-reader queue and
signatures as a high-severity privacy risk. The private reader-store design is
not deployed, and this plan does not authorize its provisioning.

David approved the interim site change on 2026-07-31 and authorized continued
private-boundary implementation on 2026-08-04: locally remove the three
public submission paths and make Counter sync a no-op until a private boundary
is verified. That approval explicitly excludes deployment, external Google
form or Sheet changes, queue deletion, and history rewriting. The target change
is recorded in `operations/reader-intake-pause.contract.json`. Existing reader
content must not be copied into analytics, prompts, logs, public metrics, or
growth experiments.

The same approval discipline applies to the unprotected production-branch gap
identified in the audit. Design documents are not proof that a ruleset, GitHub
App, or private handoff has been provisioned.

Exit: reader-intake exposure and production-branch ownership have explicit,
verified dispositions rather than design-only status.

## Workstream 3: audience measurement

- Use `docs/AUDIENCE_MEASUREMENT_SPEC.md` as the exact milestone definition.
- Keep `audience/monthly-ledger.json` at `implementation-selected` with no
  months until approved production evidence exists. Unknown measures remain
  `null`, never zero.
- Use the initial read-only capability review in
  `docs/AUDIENCE_ANALYTICS_DECISION.md` and recheck primary provider
  documentation immediately before any selection.
- Cloudflare Workers + D1 is approved for provider-specific local implementation
  and an unprovisioned canary plan only. Request David's separate explicit
  approval before any account, service, DNS change, credential, provider terms,
  provisioning, canary execution, deployment, activation, or spend.
- Use `docs/AUDIENCE_MEASUREMENT_RUNBOOK.md` for the separately approved canary,
  activation, monthly close, purge, kill-switch, and incident sequence.
- After an approved canary, collect one complete calendar month before setting
  the first numerical growth rung.

Exit: a complete, reproducible monthly baseline exists without collecting
unnecessary personal data.

## Workstream 4: mission clarity and return paths

- State the approved mission on both homepage templates:
  "Grow in faith. Understand technology wisely. Pray for one another. Use what
  you learn in service to others."
- Preserve **Loved by God** as the exact brand statement.
- Keep the archive, RSS, morning edition, evening Field Guide, tools, and
  workflows as the active return paths.
- Newsletter retention strategy and local integration prototypes may proceed,
  but do not use the preserved signup page as a campaign, draft an issue, or
  perform provider or sending operations.

Exit: a first-time reader can accurately describe the promise and find a clear
way back to canonical work.

## Workstream 5: one measured discovery loop

The normal rule is to begin one approved acquisition loop after a complete
measurement baseline starts. David approved one narrow exception on 2026-08-06:
a zero-dollar, 30-day pre-baseline learning campaign may run after its 48-hour
readiness gates and exact activation receipt complete. It uses RSS plus X-native
and manual aggregate diagnostics, leaves site return unknown, and cannot claim
qualified returning readers or progress toward the first 1,000.

The campaign's primary acquisition candidate is the existing X reply workflow:

- research from canonical, source-linked editions;
- prepare only replies that pass the existing quality and safety gates;
- obtain David's exact, item-level approval;
- post manually through the approved X interface; and
- measure site visits and later website return without treating impressions or
  follower count as the goal.

The existing daily reply cap is a ceiling, not a quota. No automated replies,
new credential, new channel, paid amplification, or publishing action is
authorized by this plan. Exact campaign actions remain item-gated by
`docs/OUTREACH_CAMPAIGN.md`.

Exit: at least one discovery format shows repeatable evidence of bringing people
back to the canonical website without a safety, policy, correction, or
moderation failure.

## First review

After the first complete measured month, record:

- qualified engaged returning readers and the larger unique-reader funnel;
- which canonical paths readers returned to;
- useful RSS and approved social evidence that can be measured safely;
- corrections, unsupported claims, moderation load, reader-intake incidents,
  production failures, and known measurement gaps; and
- David's decision for the first evidence-based numerical rung.

Do not invent a target from an unknown baseline. Reforecast from measured
behavior while the 1,000-person milestone and its two-consecutive-month rule
remain unchanged.
