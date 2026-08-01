# Distribution and measurement specification

Status: active; canonical X adapter implementation ready but production disabled
Last reconciled: 2026-08-01

## Decisions and authority

- The six-month goal is 1,000,000 combined followers across approved platforms.
- The documented starting floor is five X followers. Unknown platform baselines
  are recorded as unknown and treated as zero only for planning math.
- The publisher is faceless. Voice-led output is permitted as an experiment;
  David does not need to appear on camera.
- Budget is flexible but value-gated. No spend is implied or authorized by this
  specification.
- Claude Cowork conversations and artifacts are historical context, not
  operational authority. Production code, prompts, credentials boundaries,
  tests, and runbooks must live in a named GitHub repository.
- Credible-account replies are the primary near-term X acquisition strategy.
  David approves every reply individually and replies are manually posted.
- X reply operations start with two manual approval/posting windows and a hard
  cap of four published replies per day. A third window and six/day are disabled
  unless David separately approves and staffs them.

This repository owns the canonical edition and channel-neutral distribution
contract. A separate private adapter repository is allowed only when its owner,
secret boundary, deployment, disable switch, and link back to this contract are
documented in `docs/REPOSITORY_MAP.md`.

## Channel roles

### Website and RSS

The website, archive, and RSS are the canonical record. Social posts are derived
packages and never become the only copy of an edition or correction.

### Owner Telegram receipts

- Role: private, post-publication receipts telling David that the exact current
  morning or evening edition is live. They are not a reader distribution
  channel or a second edition.
- The receipt is derived deterministically from the exact date, slot, file, and
  lead in `archive.json`. It never asks a model to choose or summarize an
  edition and never substitutes the latest older edition.
- Each receipt includes the direct HTTPS URL for its exact live edition so the
  destination is clickable from Telegram.
- Before any reservation or credential load, the adapter requires the exact
  public URL to return HTTP 200 with the edition's exact expected HTML title.
  If the exact slot is not publicly live, the receipt fails closed. Spark's
  separate morning and evening watchdogs may send truthful not-ready alerts
  after their deadlines, but those alerts contain no older story content.
- The repository adapter is `distribution/telegram_notification.py`; its
  operating and recovery boundary is `docs/TELEGRAM_NOTIFICATION_RUNBOOK.md`.

### Weekly email pilot

- Role: a weekly retention and usefulness test, not a complete copy of the
  twice-daily paper.
- Scope: four manual Buttondown issues, at most one per week, then pause for an
  explicit keep, change, or stop decision.
- Format: Editorial Ledger with the Guided Path Start, Browse, Do, Rest.
- Consent: fresh double opt-in only. No retired list is imported or reactivated.
- Budget: $0. Stop before a charge or paid add-on and before the provider's free
  subscriber allowance is exceeded.
- The daily bake and GitHub Actions cannot send email or receive subscriber
  addresses. Activation and operations follow `docs/NEWSLETTER_PILOT_SPEC.md`.

### X

- Role: authority, source receipts, expert conversation, and site referral.
- At most one automatic canonical broadcast per edition.
- At most one additional edition-derived source card, useful fact, or question;
  it requires human review and must add distinct value.
- Replies are read-only scouted and AI-assisted drafted, then individually
  approved by David and posted through X's official interface. No API
  credential is installed for replies.
- Read-only scouting means a human using X Search or an existing X List.
  Browser scripting, scraping, headless or automated X browsing, and DOM
  automation are prohibited. A future official read-only API requires its own
  reviewed authorization and may not post.
- Quote posts, trend participation, likes, and follows are never automated.
- The replacement adapter must pass the acceptance contract below before it can
  receive credentials.
- Spark's guarded `daicc-ddb-autopost` service is the sole active canonical
  broadcaster. The repository-owned replacement is
  `distribution/x_broadcast.py`, operated by the separate post-bake job and
  `docs/X_BROADCAST_RUNBOOK.md`. Its named GitHub environment exists with a
  main-only policy, publishing disabled, and the kill switch engaged. A future
  migration must verify account identity, least-privilege credentials, and a
  canary, then disable Spark before enabling GitHub. The active Spark observation
  is recorded in `docs/OPERATIONS_EVIDENCE_2026-08-01.md`.

### X reply approval contract

`docs/X_REPLY_PLAYBOOK.md` is the operating authority. Approval is bound to one
parent URL and the exact proposed text, expires after 60 minutes, and is void
when context changes. Silence is rejection. Every factual assertion has a
fetched supporting source, every reply adds one distinct form of value, and no
reply asks for engagement.

Every candidate validates privately against
`distribution/x-reply-approval-card.schema.json`, clears BREAD at 9/10 or
better, and has an opportunity score of at least 75/100. Priority tiers control
review order only. The card includes target-verification provenance,
profile-conversion readiness, Premium and analytics availability, exact scope,
and operator/security checks. Any failed hard check rejects the candidate even
when its numeric scores pass.

The default is two staffed manual windows and no more than four published
replies per day, measured in Pacific time. Six/day requires a separately
approved and staffed third window plus an updated machine-readable baseline; it
is currently disabled. Never fill a quota with a weaker candidate. A proactive
target needs at least 72 hours between DDB replies and may receive no more than
two in a rolling 14 days.

The first 30 operating days prohibit DDB links in proactive replies unless the
parent author requests the source or the claim would otherwise be
unverifiable. The profile and pinned post perform conversion. Never send
duplicative replies, target an account repeatedly for its size, or use replies
to insert the brand into unrelated attention.

Only published replies enter `distribution/x-replies.json`, validated against
`distribution/x-replies.schema.json`. The public ledger records the parent,
target tier and verification basis, beat, reply shape, BREAD and opportunity
scores, exact approved text, supporting sources, receipt, operator and policy
checks, manual hidden/probable-spam inspections, account capabilities, and
outcome snapshots. Unposted drafts stay in a private transient queue for at
most 24 hours and are never committed here.

When X exposes them, reply-level user profile clicks and direct follows are the
primary conversion fields. Account-window profile visits and follower changes
remain secondary attribution and are never presented as caused by one reply.
Missing analytics are `null`, never zero. Shape comparisons require at least
eight measured observations per compared shape and control target tier,
discovery window, opportunity-score band, and opportunity quality. Volume may
not scale before at least 50 replies have complete measurement.

The manual boundary may change only after X grants written approval for the
specific AI-powered reply use case, a reviewed adapter proves policy and safety
controls, and David approves the contract change. A general X API credential or
approval of one reply is not permission to automate another.

### YouTube

- Role: initial discovery engine and later long-form trust engine.
- Publish one morning and one evening vertical when the source package is ready;
  never delay or weaken the canonical edition to fill a video quota.
- Initial format lab: ten archived stories, each cut once with consistent
  off-camera narration and once as caption-led/no-narration. Hold hook, duration,
  visuals, and publishing window as stable as practical.
- Select on engaged views, retention, subscribers per 1,000 engaged views,
  shares, and returning viewers. Raw Shorts starts are diagnostic, not the win
  condition.
- Long-form starts only after a short franchise shows repeatable viewer return.

### Additional short-video platforms

Do not launch everywhere at once. Add one approved platform after a YouTube
format wins across at least five posts. Recut natively for its pacing, safe
zones, caption behavior, music rights, and analytics; do not upload a watermarked
copy from another platform.

## Faceless identity and rights

- Use one recognizable visual system: masthead mark, source-card grammar,
  typography, color, motion language, and franchise labels.
- Voice modes are `voice` and `caption_only`. A recurring human narrator or a
  licensed synthetic voice requires documented commercial rights. A cloned or
  impersonated voice requires David's separate written approval.
- Record the owner and license for music, footage, images, fonts, narration, and
  templates. Unknown rights block publication.
- Put material source attribution on screen and link the canonical edition in
  the description or post.
- Synthetic media must not manufacture a person, quote, event, demonstration,
  or source artifact.

## Edition source package

Every distributed item carries:

- `editionId`: `YYYY-MM-DD-morning` or `YYYY-MM-DD-evening`;
- canonical edition URL and the exact `archive.json` lead;
- `platform`, provider post ID/URL, `formatId`, and hook variant;
- voice mode, automation flag, publication time, and operator;
- source/rights manifest for non-site assets;
- edition-scoped idempotency key and provider read-back receipt;
- spend in USD, if any;
- 24-hour and seven-day metric snapshots.

The machine-readable ledger must validate against
`distribution/metrics.schema.json`. Missing analytics are `null`, never zero.
X replies use their separate published-reply ledger because they are
conversation-derived rather than edition-derived. Follower deltas use an
explicit attribution label and are never presented as causal without provider
evidence.

## Adapter acceptance contract

Before any provider credential is installed, an adapter must demonstrate:

1. preview and dry-run modes that perform no provider mutation;
2. least-privilege secrets that never enter logs, prompts, artifacts, URLs, or
   repository history;
3. exact edition-scoped idempotency and duplicate refusal;
4. platform length, media, accessibility, URL, and prohibited-character gates;
5. bounded retries with jitter and no retry on permanent policy/auth failures;
6. provider read-back before success is recorded;
7. durable attempt, receipt, and metric records;
8. a tested kill switch and credential-revocation runbook;
9. fixture tests for success, duplicate, timeout, rate limit, invalid auth,
   invalid content, and partial media upload;
10. a named repository, owner, runtime, and failure-notification destination.

This acceptance contract currently authorizes edition broadcasts only. It does
not authorize reply posting through an API.

## Experiment and budget contract

- Each experiment changes one named variable where practical and declares its
  hypothesis, sample, decision date, maximum spend, and kill rule in advance.
- Organic evidence precedes paid amplification. A paid test includes an
  unamplified holdout and measures incremental qualified followers, engaged
  viewers, and returning viewers.
- Contractors are purchased for measurable throughput or specialist quality,
  not follower promises.
- David approves every new spending band. See `docs/GROWTH_ROADMAP.md` for the
  proposed bands and release evidence.

## Failure and correction behavior

- A failed social post never rolls back or delays the canonical site edition.
- A correction updates the canonical correction record first, then every active
  channel package that repeated the claim when provider editing allows it.
- Never silently delete and repost solely to improve metrics. Preserve the
  original receipt and record the reason for any deletion or replacement.
