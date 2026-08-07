# Outreach and marketing operating handoff

Status: DDB-PC-028 readiness active; public campaign blocked

Owner and final approver: David Friedhof

Assigned role: campaign preparation operator (tool-neutral)

Effective: 2026-08-07

The 2026-08-02 seven-day, YouTube-first sprint is superseded. The active work is
the 48-hour readiness reconciliation and separately activated 30-day outreach
campaign in `docs/OUTREACH_CAMPAIGN.md` and
`operations/outreach-campaign.contract.json`.

## Your assignment

Operate the marketing lane for David's Daily Bread without assigning authority
to a particular model or tool. Build a measurable discovery system around the
twice-daily publication while the production program controller owns pipeline,
security, reliability, deployment, and repository releases.

Your job is to turn canonical editions into useful, native marketing packages,
learn which formats earn durable attention, and report honest evidence. Your
goal is not maximum posting volume. Your goal is a repeatable path toward the
first 1,000 genuinely engaged people who return to the website.

Begin with research, planning, source packages, scripts, storyboards, approval
cards, and scorecards. External actions remain separately gated. Do not publish,
upload, create or alter an account, contact a vendor, spend money, install a
credential, or interact with another person unless David explicitly approves
that exact action.

## Read before doing any work

Read these files completely and in this order:

1. `/AGENTS.md`
2. `/FOUNDER_DOCTRINE.md`
3. `/CLAUDE.md`
4. `/BRAND.md`
5. `/docs/PRODUCT_SPEC.md`
6. `/docs/GROWTH_ROADMAP.md`
7. `/docs/FIRST_1000_FOUNDATION_PLAN.md`
8. `/docs/DISTRIBUTION_SPEC.md`
9. `/docs/AUDIENCE_MEASUREMENT_SPEC.md`
10. `/docs/X_REPLY_PLAYBOOK.md`
11. `/docs/YOUTUBE_PILOT_SPEC.md`
12. `/docs/YOUTUBE_PILOT_RUNBOOK.md`
13. `/youtube/ledgers/experiment.json`
14. `/distribution/ledger.json`

Authority order:

1. `FOUNDER_DOCTRINE.md` governs mission, ownership, strategy, authorized local
   work, and production boundaries.
2. `BRAND.md` governs anything a reader or viewer can see.
3. `PRODUCT_SPEC.md` governs the product promise.
4. `DISTRIBUTION_SPEC.md` governs channel, rights, approval, and measurement.
5. Channel-specific specifications and runbooks govern their bounded workflow.

If two lower-level files disagree, do not choose silently. Record the conflict
and hand it to Codex for repository reconciliation.

## Current project truth

- David's Daily Bread is a founder-led Christian media and learning project.
- The exact public mission is: **Grow in faith. Understand technology wisely.
  Pray for one another. Use what you learn in service to others.**
- The exact brand statement is: **Loved by God**.
- The website, archive, and RSS are the permanent canonical home.
- Social channels are for discovery and discussion. They point toward durable
  canonical work and do not replace it.
- The morning edition covers technology, markets, and science.
- The evening edition is a practical Field Guide of tools and workflows, then
  Keep and Ponder with Mary of Nazareth.
- David may remain entirely off camera.
- The active proof goal is the first 1,000 genuinely engaged returning people.
  The former one-million-followers-in-six-months target is not active.
- Followers, views, and impressions are reach evidence. They are not the
  official first-1,000 count.
- Newsletter strategy is active; issue drafting, provider activation, list
  operations, and sending remain disabled.
- New Ask the Baker, Letters to the King, and Crumb Board submissions are
  paused. Never route marketing traffic to the old intake surfaces.
- Local durable-moat research and product work are active across community,
  accounts, participation, apps, and private-messaging safety design. Marketing
  may research positioning and demand, but may not open or promise a surface.
- Cloudflare, Supabase, paid media, vendors, and new credentials are not
  authorized by this handoff.

## Division of responsibility

### Campaign preparation role owns

- audience and competitor research using lawful, public sources;
- channel positioning and native format strategy;
- selection of already-published canonical editions for repurposing;
- original hooks, scripts, storyboards, captions, descriptions, and thumbnail
  concepts;
- claim manifests and source receipts for marketing copy;
- asset-rights planning and provenance records;
- private draft packages and exact human approval cards;
- organic experiment design and content calendars;
- manual metric-entry preparation and marketing analysis;
- a concise weekly marketing report with recommendations.

### Production program controller owns

- bake and publication pipeline code;
- GitHub Actions, Pages, Spark, scheduling, watchdogs, and distribution adapters;
- security, credentials, secret boundaries, branch protection, and deployment;
- website templates and repository contract changes outside the marketing lane;
- production analytics infrastructure and first-party audience measurement;
- integration, CI, pull requests, releases, and incident repair.

### David owns

- final mission, theology, editorial direction, channels, and monetization;
- approval of every new channel, external surface, public post, upload, reply, account mutation,
  purchase, vendor contact, partnership, and credential;
- approval of the exact final creative package before publication;
- moderation decisions and all scoped production-activation decisions.

When marketing needs code or infrastructure, write a short handoff containing:

1. requested outcome;
2. reason and expected measurable benefit;
3. exact affected files or system;
4. acceptance criteria;
5. risk and rollback;
6. whether a live action needs David's approval.

Do not implement work from the Codex lane yourself.

## Channel sequence

Do not launch everywhere at once.

### 1. X: gated discovery channel

The automated canonical edition post belongs to the pipeline. After exact
campaign activation, the marketing lane adds at most one approved original post
per day plus qualified manually approved replies. Two weekly Gemini Omni pieces
consume the one-original-post slot.

- Do not scrape, script, automate, or use headless browsing against X.
- A human may supply an exact public parent-post URL or scout through the
  official X interface.
- For every candidate, follow `/docs/X_REPLY_PLAYBOOK.md` exactly.
- Each reply requires David's approval of the exact parent URL and exact text.
- Approval expires after 60 minutes and becomes void if context changes.
- Silence is rejection.
- Default and enforceable maximum: four published replies per day across two
  staffed windows. The campaign may seek three to five on staffed days, but a
  fifth remains unauthorized until the machine baseline and third staffed
  window are separately reconciled and approved.
- The cap is a ceiling, not a quota.
- For the first 30 operating days, proactive replies carry no DDB link unless
  the parent author asks for the source or a factual claim requires it.
- Do not like, follow, quote-post, message, or publish on David's behalf without
  exact separate approval.

The preparation role may research supporting sources and prepare private approval cards. Do
not commit unpublished reply drafts to the public repository.

### 2. Gemini Omni: gated X media lane

Gemini Omni is a video-generation feature in Gemini Apps. It is not the
YouTube experiment and does not authorize a Google account, plan upgrade,
provider upload, generation, or publication. After its exact account and
privacy boundary is verified and David approves the exact input package, it may
produce two weekly pieces from already-published editions. Each consumes the
day's one-original-X-post slot, validates a private provenance record, discloses
material AI generation, preserves watermarks, and receives exact final-package
approval before publication.

### 3. YouTube: separate disabled short-video laboratory

The official known channel is David's Daily Bread at `@DavidDailyBreadTV`.
The channel is currently disabled for pilot operation. Subscriber and historical
view baselines are unknown, not zero. Publishing, account mutation, narrator
engagement, and spending are disabled.

Use two initial franchises only:

1. **Morning Receipts**: what changed, what proves it, and why it matters.
2. **Tonight's Field Guide**: what an everyday person can use tonight, how to
   use it, what it costs, and the honest caveat.

Initial video constraints:

- U.S. English;
- vertical 9:16;
- internal duration target of 45 to 60 seconds;
- original analysis or demonstration, never a news-feed read-aloud;
- original graphics, typography, diagrams, and sanitized first-party screen
  recordings by default;
- no press footage, broadcast footage, article screenshots, social clips, or
  unlicensed music;
- material source attribution on screen and canonical edition/source links in
  the description;
- no synthetic narrator, cloned voice, synthetic anchor, or impersonation;
- a recurring human narrator requires a reviewed commercial contract and
  separate approval;
- caption-only must still be a paced visual explanation, not scrolling text;
- unknown rights or unsupported claims stop the package.

The specific YouTube pilot specification and experiment ledger govern the
sample design. They currently require five eligible public Shorts in each of
four franchise-by-voice-mode cells before a winner can be declared. Only one
variant from a matched source package may be released publicly. Flag the older
`DISTRIBUTION_SPEC.md` reference to ten archived stories for Codex to reconcile
if it remains inconsistent with the specific pilot contract.

Do not start the 30-day experiment clock until an authoritative YouTube metrics
baseline is captured and David authorizes the first exact private upload.

### 4. Instagram Reels or TikTok: one platform after a YouTube winner

Do not open or alter either account and do not prepare a launch campaign yet.
First produce a current, source-linked comparison of Instagram Reels and TikTok
covering:

- audience and mission fit;
- native pacing and safe-zone requirements;
- caption and accessibility behavior;
- link/referral limitations;
- music and asset-rights implications;
- analytics needed for the existing scorecard;
- moderation burden and platform safety;
- production effort needed to make a native cut;
- current official policy constraints.

Recommend one platform only after a YouTube format wins across the required
sample. Never upload a watermarked copy from another platform. David must
approve the selected channel and every account mutation or publication.

## Marketing quality law

Every reader-visible or viewer-visible package must satisfy all of these:

- no em dash character anywhere;
- plain, factual, source-grounded claims;
- no invented quote, demonstration, person, event, statistic, price, or trend;
- no article prose copied into a script;
- no generic AI hype, engagement bait, fabricated urgency, or follower promise;
- no request to like, subscribe, repost, or comment unless David approves that
  exact call to action for the experiment;
- no private reader material, credentials, personal accounts, analytics
  exports, cookies, or identifying data in prompts, drafts, recordings, logs,
  fixtures, or committed artifacts;
- no invented first-person speech from Mary of Nazareth or King David;
- prayer remains addressed to God;
- every asset has a known rights basis before publication;
- captions are proofread and meaningful visuals receive accessibility text;
- a correction updates the canonical record first, then affected channel
  packages under the applicable runbook.

## The measurable marketing system

The north-star milestone remains the canonical website's qualified engaged
returning readers under `/docs/AUDIENCE_MEASUREMENT_SPEC.md`. Social evidence is
reported beside it and never added to it.

### Weekly input measures

- source editions reviewed;
- candidates accepted and rejected;
- scripts and storyboards completed;
- packages that cleared evidence and rights review;
- packages presented to David;
- approval rate and median approval latency;
- production minutes per eligible package;
- public posts by platform, only when separately authorized;
- 24-hour and seven-day snapshots captured on time.

### Outcome measures

For short video, record when the platform exposes them:

- views or starts;
- engaged views;
- stayed-to-watch rate;
- average view duration;
- average percentage viewed;
- shares per 1,000 engaged views;
- subscribers or followers gained per 1,000 engaged views;
- returning viewers;
- profile visits and canonical-site clicks.

For X replies, record:

- impressions, likes, child replies, and reposts;
- reply-level profile clicks and direct follows when available;
- target-author interaction;
- approval latency and discovery-to-publish latency;
- hidden-reply or probable-spam disposition;
- 24-hour and seven-day snapshots.

### Non-negotiable guardrails

The allowed count for each is zero:

- unsupported published claims;
- unknown-rights published assets;
- private-data or credential exposures;
- material corrections;
- duplicate posts or uploads;
- policy incidents;
- unapproved spend;
- unapproved account or publication mutations.

Unknown measurements are `null`, never zero. Do not infer causation from an
account-level follower change. Do not declare a winning format before its
predeclared sample and snapshots are complete.

## Active 48-hour and 30-day sequence

1. Select RSS as the zero-cost return path and preserve email closure.
2. Select X-native and manual aggregate diagnostics; leave RSS follows, site
   return, and first-1,000 progress unknown.
3. Record the read-only X account, operator, security, profile, pinned post,
   broadcast permalink, Premium, and analytics receipt.
4. Stop readiness when X MFA, password-reset protection, or immutable link
   checks fail. Repairing an account or the Spark broadcaster requires its own
   scoped approval.
5. Verify the exact Gemini Omni account and plan without accepting terms,
   upgrading, uploading, or generating. Record provider, privacy, rights,
   disclosure, provenance, correction, and removal law.
6. Reconcile governing documents, contract, ledgers, schema, and tests on a
   clean branch. Report the exact head for separate release approval.
7. After merge and exact activation, run 30 calendar days with one additional
   original X post daily, up to four qualified replies on staffed days, and two
   weekly Omni releases inside the original-post slot.
8. Review on days 7, 14, and 21; decide continue, extend, modify, or stop on day
   30. Change at most one declared variable at a time.

## Superseded historical seven-day sprint (do not execute)

This section preserves the 2026-08-02 handoff history. It is not current
execution authority and does not start a public clock.

### Day 1: establish the board

1. Verify repository state. Do not reset, discard, or mix with the existing
   dirty founder branch. Use an isolated worktree or fresh branch from current
   `origin/main`.
2. Read every governing file listed above.
3. Create `marketing/OPERATING_BOARD.md` containing Backlog, In production,
   Awaiting David, Approved, Published, Measuring, Learned, and Stopped.
4. Record known channel states and unknown baselines without inventing values.
5. List every decision or external authorization needed from David.

### Day 2: build the candidate slate

1. Review recent published morning and evening editions.
2. Rank at least ten Morning Receipts candidates and ten Tonight's Field Guide
   candidates using usefulness, evidence strength, visual potential, freshness,
   rights feasibility, and production effort.
3. Reject any candidate that needs unavailable rights, private data, weak
   sources, or a misleading demonstration.
4. Select the top two candidates from each franchise for local development.

### Days 3 and 4: create four draft source packages

For two morning and two evening candidates, create:

- canonical edition ID and URL;
- target audience and one-sentence job;
- three hook options with one recommended hook;
- 45-to-60-second original script;
- timed storyboard;
- on-screen source cards and caveat;
- caption-only visual plan and SRT draft;
- matched human-narration script plan, without contacting or simulating a
  narrator;
- title, description, source links, and thumbnail concept;
- claim-evidence checklist;
- asset-rights checklist;
- estimated production minutes;
- exact unresolved blockers.

Use the existing files in `/youtube/templates/`. Do not write fabricated events
into the YouTube ledgers.

### Day 5: prepare the X reply lane

1. Read the complete X reply playbook and schemas.
2. Prepare a reusable private approval-card workflow.
3. If David supplies current parent-post URLs, research and draft only
   candidates that clear every hard gate and score threshold.
4. If no URLs are supplied, prepare the scouting rubric and wait. Do not scrape
   X or invent live opportunities.

### Day 6: compare the next channel

Complete the source-linked Instagram Reels versus TikTok comparison. Recommend
which one should follow YouTube if the YouTube winner gate eventually passes.
Do not create either account or produce a public launch asset.

### Day 7: report and reforecast

Deliver a one-page founder report:

- completed deliverables versus plan;
- production time and approval bottlenecks;
- known baseline and remaining unknowns;
- strongest two candidate packages and why;
- channel recommendation;
- guardrail incidents, including zero if measured and verified;
- next seven-day experiment;
- exact decisions requested from David;
- exact engineering requests for Codex.

## Historical definition of done for the superseded handoff

The marketing foundation is ready for David's first approval review when all of
the following are true:

1. The operating board and channel-state baseline exist.
2. Twenty candidates are ranked with explicit rejection reasons.
3. Four complete local source packages exist, two per franchise.
4. Every claim and planned asset has a verification or unresolved-blocker state.
5. No private data, unknown-rights asset, or unsupported claim entered a final
   package.
6. The X reply workflow is ready for exact parent URLs and exact-text approval.
7. The Instagram-versus-TikTok recommendation is backed by current official
   sources.
8. The weekly scorecard can report inputs, outcomes, guardrails, and unknowns.
9. No external mutation or spend occurred.
10. Claude reports the next three actions in priority order.

## Required session report

At the end of every Claude Code marketing session, report exactly these
sections:

### Completed

List tangible files or packages finished.

### Measured

List counts, elapsed production time, baseline changes, and experiment results.
Use `null` for unavailable metrics.

### Awaiting David

List exact approvals or decisions. Never convert silence into approval.

### Handoff to Codex

List any pipeline, infrastructure, security, repository-contract, or deployment
work needed, with measurable acceptance criteria.

### Next three actions

Give three concrete actions in priority order.

## Current start command

Use this instruction after opening Claude Code in the repository:

> Read `docs/OUTREACH_CAMPAIGN.md`,
> `operations/outreach-campaign.contract.json`, and this handoff completely.
> Execute only the active DDB-PC-028 readiness work assigned by the program
> controller on a clean branch. Do not publish, upload, generate, post, reply,
> follow, like, message, alter accounts, accept provider terms, install
> credentials, activate tracking, collect data, spend, deploy, or merge. Stop at
> every exact approval boundary and report the immutable implementation head.
