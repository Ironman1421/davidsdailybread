# Morning Receipts script and storyboard template

TEMPLATE ONLY. Do not treat this file as a real episode, source, script, or
approval. Replace every `{{PLACEHOLDER}}` from a verified, already-published
morning edition. Do not paste current journalism into this template.

## Production header

- Video record ID: `{{YV_ID}}`
- Edition ID: `{{YYYY_MM_DD_MORNING}}`
- Canonical edition URL: `{{CREDENTIAL_FREE_HTTPS_URL}}`
- Exact archive lead: `{{EXACT_ARCHIVE_LEAD}}`
- Selected edition item: `{{ITEM_LOCATOR}}`
- Format ID: `morning_receipts`
- Market/language: `US` / `en-US`
- Assigned pilot mode: `{{recurring_human_narrator_OR_caption_only}}`
- Evidence manifest ID: `{{YEV_ID}}`
- Asset manifest ID: `{{YAM_ID}}`
- Experiment/cell/assignment IDs: `{{YEXP_ID}}` / `{{YCELL_ID}}` / `{{YASN_ID}}`
- Internal runtime target: `45-60 seconds`
- Planned public window class: `{{WINDOW_CLASS}}`
- External cost USD: `0` unless `{{SEPARATE_WRITTEN_AUTHORIZATION_REFERENCE}}` is present

## Pre-script gates

- [ ] Canonical morning edition is already public.
- [ ] Every factual phrase planned below has a retrieval receipt and locator.
- [ ] This is original analysis, not an article/news-feed read-aloud, headline
      roll, generic slideshow, or mechanically filled template.
- [ ] Public variant was assigned before results; the alternate cut will not be
      published.
- [ ] All planned visuals are original, commissioned, licensed, YouTube Audio
      Library under reviewed terms, or verified public domain.
- [ ] No press footage, broadcast footage, article screenshot, social-video clip,
      or unlicensed music is planned.
- [ ] Voice mode is caption-only or the properly contracted recurring human.
      Synthetic narration and cloned voice are prohibited in the initial pilot.

## One-sentence editorial spine

What changed: `{{ORIGINAL_PLAIN_LANGUAGE_CHANGE}}`

Why it matters: `{{ORIGINAL_BOUNDED_CONSEQUENCE}}`

What remains uncertain: `{{SUPPORTED_CAVEAT_OR_NEXT_CHECK}}`

If these three lines do not form a distinct, useful story, stop rather than fill
the template.

## Locked factual payload

| Claim ID | Exact final claim | Retrieval receipt ID(s) | Locator | Delivery |
| --- | --- | --- | --- | --- |
| `{{YC_001}}` | `{{EXACT_ORIGINAL_CLAIM}}` | `{{YRR_IDS}}` | `{{SECTION_TABLE_OR_PARAGRAPH}}` | `{{spoken/on_screen/description}}` |
| `{{YC_002}}` | `{{EXACT_ORIGINAL_CLAIM}}` | `{{YRR_IDS}}` | `{{SECTION_TABLE_OR_PARAGRAPH}}` | `{{spoken/on_screen/description}}` |

Add rows until every fact is bound. Delete unused rows. Zero unsupported claims
may remain.

## Short storyboard and script

### 0:00 to 0:03, consequential change

- Visual: `{{ORIGINAL_FRANCHISE_SLATE_AND_CHANGE_GRAPHIC}}`
- Human narrator script: `{{ONE_ORIGINAL_SENTENCE_STATING_THE_CHANGE}}`
- Caption-only designed text: `{{EQUIVALENT_CONCISE_CHANGE_CAPTION}}`
- Claim IDs: `{{CLAIM_IDS}}`
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

### 0:03 to 0:12, who did what and when

- Visual: `{{ORIGINAL_SOURCE_CARD_NOT_A_PAGE_SCREENSHOT}}`
- Human narrator script: `{{ACTOR_ACTION_DATE_IN_ORIGINAL_WORDS}}`
- Caption-only designed text: `{{EQUIVALENT_PACED_ACTOR_ACTION_DATE}}`
- On-screen source attribution: `{{SOURCE_NAME_AND_SHORT_LOCATOR}}`
- Claim IDs: `{{CLAIM_IDS}}`
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

### 0:12 to 0:28, receipt

- Visual: `{{ORIGINAL_DIAGRAM_NUMBER_TREATMENT_OR_LICENSED_VISUAL}}`
- Human narrator script: `{{EXPLAIN_PRIMARY_RECEIPT_AND_CONTEXT}}`
- Caption-only designed text sequence: `{{EQUIVALENT_VISUAL_EXPLANATION}}`
- Claim IDs: `{{CLAIM_IDS}}`
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

### 0:28 to 0:45, why it matters

- Visual: `{{ORIGINAL_CONSEQUENCE_GRAPHIC}}`
- Human narrator script: `{{BOUNDED_EVERYDAY_READER_CONSEQUENCE}}`
- Caption-only designed text sequence: `{{EQUIVALENT_CONSEQUENCE_EXPLANATION}}`
- Claim IDs: `{{CLAIM_IDS}}`
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

### 0:45 to 0:55, caveat or next check

- Visual: `{{ORIGINAL_CAVEAT_CARD}}`
- Human narrator script: `{{SUPPORTED_UNCERTAINTY_CAVEAT_OR_NEXT_CHECK}}`
- Caption-only designed text: `{{EQUIVALENT_CAVEAT_CAPTION}}`
- Claim IDs: `{{CLAIM_IDS}}`
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

### 0:55 to 1:00, canonical receipt

- Visual: `{{ORIGINAL_DDB_EDITION_AND_SOURCE_CARD}}`
- Human narrator script: `{{PLAIN_POINTER_TO_CANONICAL_EDITION_AND_SOURCES}}`
- Caption-only designed text: `{{EQUIVALENT_EDITION_POINTER}}`
- Do not ask for engagement.
- Asset IDs/timecodes: `{{ASSET_IDS_AND_FINAL_TIMECODES}}`

## Matched-cut comparison

The two local cuts must preserve:

- exact claim set and source cards;
- hook intent and narrative order;
- target duration within three seconds;
- equivalent visual and editing effort;
- the same music/no-music choice and licensed mix, excluding narration;
- the same publishing-window class.

Only `{{ASSIGNED_MODE}}` may become public. Mark the alternate
`evaluation_only_never_publish` and delete it under the local retention rule.

## Description template

```text
Morning Receipts: {{ORIGINAL_TITLE}}

{{TWO_SENTENCE_ORIGINAL_SUMMARY}}

Read the canonical morning edition and complete source list:
{{CANONICAL_EDITION_URL}}

Sources reviewed:
{{PRIMARY_SOURCE_NAME}}: {{PRIMARY_SOURCE_URL}}
{{ADDITIONAL_SOURCE_NAME_IF_NEEDED}}: {{ADDITIONAL_SOURCE_URL}}

{{ALTERED_OR_SYNTHETIC_DISCLOSURE_CONTEXT_IF_NEEDED}}
```

Do not add a correction block to a clean initial description. If a correction
is later required, follow `docs/YOUTUBE_PILOT_RUNBOOK.md` and put the official
English `Correction:` or `Corrections:` section after any chapters.

## SRT and final review

- SRT path: `{{EN_US_SRT_PATH}}`
- SRT SHA-256: `{{SRT_SHA256}}`
- Final video SHA-256: `{{VIDEO_SHA256}}`
- Altered/synthetic Studio selection: `{{Yes_OR_No}}`
- Disclosure rationale: `{{HUMAN_RATIONALE}}`
- Rights reviewer/time: `{{HUMAN_AND_UTC_TIME}}`
- Evidence reviewer/time: `{{HUMAN_AND_UTC_TIME}}`
- Caption reviewer/time: `{{HUMAN_AND_UTC_TIME}}`
- Private-upload reviewer/time: `{{HUMAN_AND_UTC_TIME}}`
- Accountable final human approval/time: `{{HUMAN_AND_UTC_TIME}}`

Silence, an automated check, or a model response is not final approval.
