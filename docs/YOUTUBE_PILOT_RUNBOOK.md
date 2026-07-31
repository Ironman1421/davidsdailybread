# YouTube pilot operator runbook

Status: disabled until channel and baseline blockers are resolved
Applies to: U.S.-English Morning Receipts and Tonight's Field Guide pilot

## Hard stop at initialization

Read `docs/YOUTUBE_PILOT_SPEC.md` and the five ledgers before doing anything in
YouTube Studio. Stop if `youtube/ledgers/experiment.json` says `disabled`, if the
channel handle or baseline is `null`, or if a requested action lacks authority.

This runbook does not authorize an account, channel, upload, narrator contact,
vendor contact, credential, contract, license, or spend. The initial repository
state is deliberately disabled. Only David can provide the missing channel and
baseline, authorize a specific expense, and release external operation.

Never use reader submissions, private data, personal account data, credentials,
cookies, private analytics, or unpublished material in scripts, prompts,
fixtures, recordings, logs, or committed receipts.

## 1. Open a production record

1. Confirm the canonical edition is already public and copy its edition ID,
   canonical credential-free HTTPS URL, exact archive lead, and selected item.
2. Choose exactly one franchise. Morning Receipts explains a change and its
   significance. Tonight's Field Guide demonstrates an action and its caveat.
3. Create the evidence, asset, production, and experiment-cell IDs before the
   script. Do not reserve or infer a YouTube video ID.
4. Confirm the precommitted mode assignment. Produce both matched cuts for local
   comparison, but mark only the assigned cut as publish-eligible.
5. Record internal production time. Leave external cost at zero unless a
   separate written authorization receipt exists.

## 2. Review claims and retrieval receipts

For every factual spoken phrase, caption, number, date, price, popularity claim,
and demonstrated result:

1. retrieve the primary official source when available;
2. record requested and resolved credential-free HTTPS URLs, UTC retrieval time,
   HTTP outcome, content type, and content SHA-256;
3. attach a precise page, section, table, paragraph, or timestamp locator;
4. write a short original support summary, not copied article prose;
5. bind the exact final script or on-screen claim to its receipt IDs;
6. remove any claim that a human reviewer cannot verify.

The reviewer reads the source itself. A model's assertion that a source supports
a claim is not evidence. The evidence gate permits zero unsupported claims.

## 3. Perform rights review

Inventory the final timeline, including narration, music, images, footage,
graphics, fonts, templates, screen recordings, and sound effects. For every
asset, record owner/creator, source class, source URL when applicable, rights
basis, license or contract reference, territory, term, commercial/YouTube scope,
reviewer, and every final start/end timecode.

Stop on `unknown`, "found online," a missing term, missing commercial scope, or
an unreviewed permission. Do not use press footage, broadcast footage, article
screenshots, social-video clips, or unlicensed music in this pilot. Do not rely
on a copyright exception without a separate documented legal review.

For the recurring human narrator, store only a non-sensitive contract receipt
and reviewed scope in the public repository. Do not commit the agreement,
address, tax/payment details, contact information, voice sample, or credentials.
Confirm the agreement covers recurring commercial YouTube narration, editing,
territory, term, and the assigned cut before recording.

## 4. Record a clean-account demonstration

This step applies to Tonight's Field Guide screen recordings.

1. Use an already-authorized sanitized demo or clean account. This runbook does
   not authorize creating one.
2. Start from a fresh browser profile or equivalent clean local application
   state with sync disabled. Do not sign into a personal profile.
3. Disable notifications and hide bookmarks, extensions, password managers,
   other tabs, menu-bar identifiers, recent files, and desktop contents.
4. Use invented non-personal fixture data labeled as a demo. Never use a real
   reader, email, contact, document, analytics panel, credential, or customer.
5. Record only the needed application region. Avoid address-bar query strings,
   account avatars, billing pages, API keys, tokens, and cookie dialogs that
   expose identifiers.
6. Review the full recording frame by frame, crop only after review, and record
   its content hash and timecodes in the asset manifest.
7. Delete rejected raw takes under the local retention policy. Do not upload raw
   screen recordings as CI artifacts or commit them to the public repository.

## 5. Lock script, storyboard, and cuts

Use the matching file in `youtube/templates/`. Keep both cuts equivalent in
claim payload, hook intent, duration band, visual effort, source cards, and
publishing-window class. Only voice mode changes.

Run the originality review against the full channel context:

- no article or news-feed read-aloud;
- no headline roll, silent slideshow, or generic scrolling-text video;
- no mechanically swapped names and numbers;
- no near-duplicate public alternate cut;
- clear original analysis for Morning Receipts;
- clear original demonstration for Tonight's Field Guide.

Record the final video SHA-256. Any edit after approval invalidates later gates.

## 6. Build and verify en-US captions/SRT

1. Transcribe the locked cut, including meaningful non-speech audio cues.
2. Set the original video language to English (United States).
3. Use sequential SRT cue numbers and `HH:MM:SS,mmm --> HH:MM:SS,mmm` timecodes.
4. Keep cues synchronized, readable on mobile, and out of important picture
   regions. Split on natural phrase boundaries.
5. For caption-only, retain burned-in designed text and also upload the complete
   SRT accessibility track.
6. A human proofreads names, figures, punctuation, and claim wording against the
   evidence-approved script and locked picture.
7. Record the SRT path, hash, reviewer, and review time. Regenerate and rereview
   it after any cut change.

## 7. Review altered or synthetic disclosure

Open the current official altered/synthetic policy linked from the pilot spec.
A human answers the Studio disclosure for the exact locked video:

1. list every generative or material alteration used in script, image, audio,
   video, music, or editing assistance;
2. determine whether the output realistically makes a person act/speak, alters
   a real event/place, or depicts a realistic scene that did not occur;
3. select `Yes` when required and record the rationale;
4. select `No` only with a recorded rationale;
5. stop if a proposed asset manufactures a quote, event, demonstration, source
   artifact, synthetic anchor, or cloned/synthetic initial narrator.

Disclosure does not cure deception, missing rights, or an unsupported claim.

## 8. Private upload and read-back checks

This section remains blocked until David supplies the channel and authorizes the
specific upload. Private is the first allowed visibility; unlisted is not a
substitute for the private review gate.

1. Confirm the kill switch is released for this exact video and the
   idempotency key has no prior provider receipt.
2. Upload through the official YouTube Studio UI as `Private`; automation does
   not receive a publish credential in the pilot.
3. Set title, description, en-US language, audience setting, thumbnail, captions,
   source links, canonical edition link, and altered/synthetic selection.
4. Wait for processing. Review the 1080x1920 result on phone and desktop,
   captions, text safe zones, audio levels, first frame, ending, and links.
5. Review YouTube copyright/checks results and any restriction. A clean automated
   check does not replace the rights manifest. Stop on a claim or uncertainty.
6. Review the current advertiser-friendly checklist for video, title, thumbnail,
   description, and tags. Record the human result and any context.
7. Compare the provider read-back with the approved final hash and metadata.
8. Record the private video ID/URL and private-check receipt. Keep visibility
   private until the accountable human final approval names this exact package.
9. If approved for public release, perform one final read-back, publish manually,
   and record provider ID/URL/time/operator. Never report success from a click
   alone.

## 9. Final human approval

The approver checks the exact video hash, evidence manifest, asset manifest,
SRT, thumbnail, title, description, disclosure selection, private playback,
copyright/checks result, advertiser-friendly review, assignment cell, schedule,
and cumulative authorized/committed cost.

Approval is explicit, time-bound to the exact package, and recorded by name and
UTC time. Silence is rejection. A changed byte, changed description, new asset,
new claim, new channel, expired rights term, or changed policy state voids it.

## 10. Capture metric snapshots

Schedule a 24-hour and seven-day snapshot from the actual public time. In
YouTube Studio Advanced Mode, use the exact video and UTC/date-range context.
Record:

- views (starts/replays), engaged views, and stayed-to-watch;
- watch time, average view duration, and average percentage viewed;
- subscribers gained, shares, and returning viewers when exposed;
- capture time, operator, analytics source/receipt, and availability status.

Unknown or not-yet-available metrics are `null`, never invented and never written
as zero. A measured zero may be recorded only with a captured provider receipt.
Preserve privacy: do not commit a screenshot or export containing viewer-level,
account, revenue, or unrelated channel data. Store a redacted receipt reference
and content hash when the raw artifact belongs outside the public repository.

Do not compare raw Shorts views as though they were engaged views. Calculate
subscribers and shares per 1,000 engaged views only when the denominator is
present and nonzero.

## 11. Handle corrections and replacements

1. Engage the kill switch for the affected video or pilot.
2. Preserve the public URL, video ID, publish receipt, metrics, final hash, and
   the report that identified the problem.
3. Correct the canonical edition/correction record first.
4. Classify severity and identify every active package that repeated the claim.
5. For an eligible in-place correction, place this section after chapters:

   ```text
   Correction:
   0:35 Plain explanation of what was wrong and what is correct.
   ```

6. Read back the description and record the exact correction block. Use
   `Corrections:` when there is more than one entry.
7. A material correction, unsupported claim, rights problem, privacy exposure,
   or misleading edit stays stopped while a human decides whether to unlist,
   remove, or replace. Do not silently delete and repost for performance.
8. A replacement gets a new ID and receipt. Add a relationship that preserves
   the original receipt and reason, then rerun every gate.

## 12. Kill switch

Engage the kill switch immediately on any spec stop condition, including:

- unsupported or unsettled claim;
- missing/unknown asset right or copyright challenge;
- missing/invalid final approval;
- synthetic or cloned initial narrator;
- material correction, policy warning, strike, or ad-suitability uncertainty;
- private data, reader content, identifier, or credential exposure;
- duplicate or wrong-cell public variant;
- actual plus committed external cost that could exceed USD 2,500;
- loss of channel control, unexpected account state, or idempotency conflict.

With the switch engaged: create no upload, publish, replacement, edit, deletion,
contract, purchase, or vendor communication; preserve evidence; stop scheduled
work; and notify David through the separately approved incident channel. This
repository does not invent that channel. Resume only after the defect is fixed,
receipts are complete, all gates rerun, and David records a release.

For credential or privacy exposure, also follow `docs/SECURITY_SPEC.md`: preserve
evidence, revoke/rotate outside git, make a reviewed forward fix, and add a
regression test before resuming.

## 13. Evaluate the Short gate

After both voice-mode cells in one franchise have at least five eligible public
Shorts and complete or explicitly unavailable snapshots, apply the predeclared
rule in `docs/YOUTUBE_PILOT_SPEC.md`. Record `pass`, `extend`, or `stop` without
changing thresholds after seeing results.

Only a passing receipt plus human `longFormReleased: true` permits long-form
work. An `extend`, missing baseline, missing snapshot, or unresolved guardrail
keeps long-form blocked. YPP eligibility and raw view count are not this gate.
