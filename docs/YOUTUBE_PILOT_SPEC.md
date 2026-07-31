# YouTube pilot foundation specification

Status: design-ready, externally blocked
Owner: David Friedhof
First market: United States, English (`en-US`)
Last policy verification: 2026-07-31

## Purpose and authority

This specification turns a canonical David's Daily Bread edition into an
original YouTube video package with claim receipts, asset rights, human review,
and measurable outcomes. It does not authorize a channel, upload, credential,
contract, purchase, or external account change.

`BRAND.md`, `docs/PRODUCT_SPEC.md`, and `docs/DISTRIBUTION_SPEC.md` remain the
editorial and distribution authorities. This document owns the bounded YouTube
pilot procedure and its machine-readable records.

Accepted pilot decisions:

- The first market is U.S. English.
- The initial comparison is one properly contracted recurring human narrator
  versus a caption-only cut.
- No synthetic narrator, cloned voice, or synthetic anchor may be used in the
  initial pilot.
- The external pilot planning ceiling is exactly USD 2,500 total. It is a design
  constraint, not permission to spend. Spend defaults to zero and needs separate
  written authorization from David before any commitment.
- The YouTube channel handle, channel ID, subscriber baseline, historical view
  baseline, and historical engaged-view baseline are unknown blockers. They
  remain `null`; they must not be invented and this work must not create them.
- Long-form production begins only after the five-post Short winner gate passes
  and a human releases it.
- No unlicensed press, broadcast, article-screenshot, social-video, or music
  asset may be used. This pilot is stricter: third-party press footage,
  broadcast footage, article screenshots, and social-video clips are excluded
  even if a use argument might be available.

## Current external blockers

Publishing and account mutation are disabled until David supplies or confirms:

1. the existing YouTube channel handle and channel ID;
2. a dated YouTube Studio baseline receipt;
3. any proposed narrator engagement and a reviewed contract receipt;
4. any proposed expense and its separate written authorization.

These are blockers to external operation, not blockers to templates, local
validation, or repository review.

## Official YouTube policy basis

The following primary YouTube or Google pages were checked on 2026-07-31. Their
requirements can change, so an operator rechecks them before the first private
upload and at each experiment gate.

- [Channel monetization policies](https://support.google.com/youtube/answer/1311392?hl=en): YouTube renamed "repetitious content" to "inauthentic content" on 2025-07-15. Repetitive or mass-produced template content, low-value slideshows or scrolling text, and readings of material from websites or news feeds can be ineligible. Reused-content review is channel-wide and remains separate from copyright permission.
- [Altered or synthetic content disclosure](https://support.google.com/youtube/answer/14328491?hl=en): realistic, meaningful alteration or generation requires the Studio disclosure. Script help, caption creation, and minor production assistance alone do not necessarily require it. The final selection is a recorded human review, never an assumption made by a tool.
- [Copyright on YouTube](https://support.google.com/youtube/answer/2797466?hl=en): permission, a verified license, a verified copyright exception, or verified public-domain status is still required. Monetization reused-content review can fail even when permission exists.
- [Advertiser-friendly content guidelines](https://support.google.com/youtube/answer/6162278?hl=en): title, thumbnail, description, tags, Short, and video content all enter ad-suitability review. News context does not automatically make graphic or sensitive material suitable for all advertisers.
- [Shorts creation and view-count definitions](https://support.google.com/youtube/answer/10059070?hl=en): Shorts may be up to three minutes. Since 2025-03-31, a public Short view counts a start or replay with no minimum watch time; the prior metric remains in Analytics as engaged views.
- [YouTube content performance metrics](https://support.google.com/youtube/answer/12220281?hl=en): engaged views count viewers who stayed beyond the initial seconds and exclude loops; stayed-to-watch, average view duration, and average percentage viewed must be interpreted from engaged views for Shorts.
- [Edit video settings and correction syntax](https://support.google.com/youtube/answer/57404?hl=en): the description uses the English token `Correction:` or `Corrections:`, then a timestamp and explanation on a separate line, after chapters.
- [YPP overview and eligibility](https://support.google.com/youtube/answer/72851?hl=en): ad-revenue eligibility currently requires 1,000 subscribers plus either 4,000 valid public long-form watch hours in 12 months or 10 million valid public Shorts views in 90 days, followed by channel review. Shorts-feed watch hours do not count toward the 4,000-hour route.
- [Expanded YPP overview](https://support.google.com/youtube/answer/13429240?hl=en): in eligible regions, earlier fan-funding and Shopping access currently starts at 500 subscribers, three valid public uploads in 90 days, and either 3,000 valid public watch hours in 12 months or 3 million valid public Shorts views in 90 days.

YPP numbers are platform eligibility rules, not pilot success benchmarks. The
duration targets, cell sizes, comparison thresholds, and cost controls below
are internal planning assumptions, not YouTube promises or benchmarks.

## Two distinct franchise jobs

### Morning Receipts

Morning Receipts answers: **What changed, what proves it, and why does it
matter?** It is a compact piece of original analysis derived from one morning
edition item. It must not become a list of headlines, a publisher's article
read aloud, an automated news-feed video, or a montage of borrowed news clips.

Required Short storyboard:

| Internal target | Job | Picture and evidence |
| --- | --- | --- |
| 0:00 to 0:03 | State the consequential change in original words | Franchise slate plus original text or graphic |
| 0:03 to 0:12 | Name the actor, action, and date | Original source card with source name and short locator, never a page screenshot |
| 0:12 to 0:28 | Explain the strongest primary-source receipt | Original diagram, number treatment, or licensed visual |
| 0:28 to 0:45 | Explain why an everyday reader should care | Original analysis and one bounded consequence |
| 0:45 to 0:55 | State uncertainty, caveat, or next check | On-screen caveat tied to a claim receipt |
| 0:55 to 1:00 | Point to the canonical edition and sources | Plain source/edition card without an engagement demand |

Release rejection examples include a headline roll, article text used as the
script, generic stock clips with captions, or the same framing with only names
and numbers swapped.

### Tonight's Field Guide

Tonight's Field Guide answers: **What can an everyday reader use or try tonight,
how, at what cost, and with what caveat?** It is derived from one evening tool or
workflow. It is not a recap of what happened in the news.

Required Short storyboard:

| Internal target | Job | Picture and evidence |
| --- | --- | --- |
| 0:00 to 0:03 | Promise one concrete, bounded outcome | Franchise slate plus finished-state preview |
| 0:03 to 0:12 | Name the tool or workflow and who it is for | Original title card; show price/platform receipt in text |
| 0:12 to 0:32 | Demonstrate two to four steps | Sanitized original screen recording or original diagram |
| 0:32 to 0:45 | Verify the result | Clean-account output with no private or reader data |
| 0:45 to 0:55 | State price, prerequisite, privacy issue, or failure mode | Explicit caveat supported by a current receipt |
| 0:55 to 1:00 | Give the next action and canonical edition | Plain source/edition card without an engagement demand |

A release fails if it reports a launch without a usable action, shows a logged-in
personal account, hides a price or material prerequisite, or substitutes a
promotional claim for a demonstrated result.

## Short and long-form boundaries

YouTube permits Shorts up to three minutes. The pilot uses an **internal** target
of 45 to 60 seconds, vertical 9:16, with like-length cuts inside each comparison.
Exceeding 60 seconds requires a written exception in the production receipt;
exceeding three minutes is not a Short.

Long-form is an **internal** target of 6 to 10 minutes and must synthesize a
recurring theme, demonstrate a workflow deeply, or reconcile multiple primary
receipts. It must never be a longer reading of one edition. No outline, script,
recording, narrator booking, or upload for long-form begins until:

1. at least five eligible public Shorts exist in each voice-mode cell for the
   franchise being evaluated;
2. the predeclared Short winner rule passes with no guardrail failure;
3. the gate receipt names the winning franchise and mode;
4. a human final approver sets `longFormReleased` to true.

## Source package and evidence

Each candidate starts from one already-published canonical edition. Video work
must never delay or weaken the edition. Before script approval, create a claim
manifest that binds every factual spoken phrase, caption, number, date, price,
demonstrated result, and popularity claim to one or more retrieval receipts.

A retrieval receipt contains requested and resolved credential-free HTTPS URLs,
retrieval time, status, content type, content hash, and a locator. The claim
record stores the exact final claim, a short original support summary, and the
receipt IDs. Keep any supporting excerpt minimal; do not copy current journalism
into a template or ledger. Unsupported or unsettled claims are removed.

The canonical edition is the editorial starting point, not sufficient proof by
itself. Prefer the primary filing, product documentation, research paper, public
agency release, or direct official statement when available. A human evidence
reviewer approves the complete claim set.

## Asset provenance and rights

Every visual, audio, font, template, narration segment, and screen recording in
the final timeline appears in the asset manifest with final start/end timecodes.
Allowed source classes are original capture, original graphic, commissioned
work, licensed stock, licensed music, YouTube Audio Library material under its
current terms, and verified public-domain material. `unknown`, "found online,"
and unrecorded verbal permission are not rights bases.

For narration, the public repository stores only a non-sensitive contract
receipt/reference and the reviewed commercial scope, not a person's contract,
address, tax information, voice sample, or payment details. The agreement must
cover YouTube, commercial use, the pilot territory and term, edits, and the
specific recurring-human use. Silence is not permission.

Pilot visuals default to original typography, diagrams, source cards, and
sanitized first-party screen recordings. Do not use press or broadcast footage,
article screenshots, social-video clips, or unlicensed music. Unknown rights
stop publication.

## Script and production rules

- Use the repository templates in `youtube/templates/`.
- Write original synthesis in U.S. English; do not paste article prose.
- Both voice modes use the same factual payload, hook intent, duration band,
  visual effort, source package, and publishing-window class.
- Caption-only means a paced original visual explanation, not silent scrolling
  text or a slideshow. It still receives a full SRT file for accessibility.
- The recurring-human mode uses only the contracted recurring narrator named by
  a rights receipt. It does not use a clone, text-to-speech stand-in, synthetic
  anchor, or another person's voice.
- Material source attribution appears on screen, and the canonical edition plus
  source links appear in the description.
- No personal, reader, credential, cookie, account, or private analytics data
  may enter scripts, prompts, fixtures, recordings, logs, or committed receipts.

## Review and release gates

All gates fail closed and record the named human reviewer and time:

1. **Edition gate:** canonical URL, edition ID, exact lead, and selected item
   match the published archive.
2. **Evidence gate:** every final factual claim is verified against retained
   retrieval receipts; zero unsupported claims are allowed.
3. **Originality gate:** the piece supplies original analysis or demonstration,
   materially varies by episode, and is not feed-to-video or read-aloud output.
4. **Rights gate:** every final-timeline asset has a verified rights basis and
   timecodes; zero unknown-rights assets are allowed.
5. **Narration gate:** caption-only or properly contracted recurring human;
   synthetic and cloned narration are false.
6. **Safety and ads gate:** Community Guidelines and the complete current
   advertiser-friendly checklist are reviewed in context.
7. **AI disclosure gate:** a human records `Yes` or `No` in line with the current
   Studio question and explains the decision.
8. **Caption gate:** en-US captions and SRT are proofread against the locked cut.
9. **Private-upload gate:** copyright checks, restrictions, metadata, thumbnail,
   captions, disclosure, source links, mobile safe zones, and playback pass while
   private. A private upload is not authorization to publish.
10. **Final approval gate:** an accountable human approves the exact final hash,
    description, thumbnail, and planned publication. Automation cannot self-approve.

## Thirty-day comparison

The experiment clock does not start until the channel baseline is captured.
The maximum planned window is 30 calendar days. The single changed variable is
voice mode within each franchise.

Four comparison cells are planned:

| Franchise | Cell | Public sample floor |
| --- | --- | ---: |
| Morning Receipts | recurring contracted human narrator | 5 eligible Shorts |
| Morning Receipts | caption-only | 5 eligible Shorts |
| Tonight's Field Guide | recurring contracted human narrator | 5 eligible Shorts |
| Tonight's Field Guide | caption-only | 5 eligible Shorts |

For each source package, production creates both cuts for effort and quality
review, but a precommitted balanced assignment chooses only one variant for
public release. The other cut stays local/transient and is deleted under the
production retention rule. This avoids publishing near-duplicate videos and
keeps each public post in exactly one cell. Assignment must be balanced across
weekday, window class, franchise, duration, and topic as practical. Do not change
the assignment after seeing results.

Snapshots are scheduled at 24 hours and seven days. Raw starts/replays are
diagnostic. The primary comparison metric is subscribers gained per 1,000
engaged views. Secondary metrics are stayed-to-watch, average percentage viewed,
shares per 1,000 engaged views, returning viewers, production minutes, and
corrections.

## Internal success, extend, and stop rules

These are predeclared **internal planning assumptions**, not platform benchmarks:

- A cell is eligible only after five policy-compliant public Shorts have both
  snapshots or a documented metrics-unavailable receipt.
- A voice-mode winner needs at least a 15 percent lift in the median primary
  metric versus the other mode.
- The candidate winner may not have a relative decline greater than 10 percent
  in median stayed-to-watch or greater than 20 percent in median shares per
  1,000 engaged views.
- Both modes must retain zero unsupported claims, zero unknown-rights assets,
  zero material corrections, and zero policy incidents.
- If the lift is smaller, metrics are unavailable, or guardrails conflict, the
  decision is `extend`, not a claimed win. Extension still cannot release
  long-form without a later passing gate.
- Immediate `stop` conditions are an unsupported published claim, unknown-rights
  asset, missing human final approval, synthetic or cloned initial narration,
  material correction, copyright strike/claim that challenges the rights basis,
  policy warning, exposure of private data or credentials, duplicate public
  variant, or actual plus committed external cost above USD 2,500.

Success means the comparison completed with auditable receipts and one genuine
winner under this rule. It does not mean YPP eligibility or growth is forecast.

## Cost boundary

The exact external pilot planning ceiling is **USD 2,500 total**. The repository
baseline sets `spendAuthorized` to false and `authorizedSpendUsd` to 0. Estimates
and quotes are planning inputs only. Any narrator, editor, license, music,
template, or measurement expense requires a separate proposal with deliverable,
owner, maximum, measurement window, kill rule, and David's written approval.

Committed plus paid external cost is counted against the ceiling. Internal labor
hours are measured separately and are not assigned an invented cash value. The
runbook's kill switch engages before a commitment could cross the ceiling.

## Corrections and replacements

Correct the canonical edition record first. Then update every active video that
repeated the claim when the platform allows it. Preserve the original publish
receipt. Never delete and repost to improve metrics.

For an in-place YouTube description correction, put `Correction:` or
`Corrections:` after video chapters, followed on a separate line by the timestamp
and a plain explanation. Record the exact block and its read-back receipt. A
material error stops the pilot and normally requires unlisting or removing the
video while a human chooses a forward correction. A replacement receives a new
video ID and idempotency key, links back to the original in the corrections
ledger, and never erases the original receipt or metrics.

## Repository artifacts

- `youtube/schemas/claim-evidence.schema.json` and
  `youtube/ledgers/claim-evidence.json`
- `youtube/schemas/asset-provenance.schema.json` and
  `youtube/ledgers/asset-provenance.json`
- `youtube/schemas/corrections.schema.json` and
  `youtube/ledgers/corrections.json`
- `youtube/schemas/video-receipts.schema.json` and
  `youtube/ledgers/video-receipts.json`
- `youtube/schemas/experiment.schema.json` and
  `youtube/ledgers/experiment.json`
- `youtube/templates/morning-receipts.md` and
  `youtube/templates/tonights-field-guide.md`
- `docs/YOUTUBE_PILOT_RUNBOOK.md`

The ledgers are intentionally empty. No episode, platform ID, narrator identity,
contract, channel value, metric, or expense has been invented.
