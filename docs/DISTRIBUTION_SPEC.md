# Distribution and measurement specification

Status: active design; provider adapters pending
Last reconciled: 2026-07-31

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

This repository owns the canonical edition and channel-neutral distribution
contract. A separate private adapter repository is allowed only when its owner,
secret boundary, deployment, disable switch, and link back to this contract are
documented in `docs/REPOSITORY_MAP.md`.

## Channel roles

### Website and RSS

The website, archive, and RSS are the canonical record. Social posts are derived
packages and never become the only copy of an edition or correction.

### X

- Role: authority, source receipts, expert conversation, and site referral.
- At most one automatic canonical broadcast per edition.
- At most one additional edition-derived source card, useful fact, or question;
  it requires human review and must add distinct value.
- Replies, quote posts, trend participation, likes, and follows are never
  automated.
- The replacement adapter must pass the acceptance contract below before it can
  receive credentials.

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
