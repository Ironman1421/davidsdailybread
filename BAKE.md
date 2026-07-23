# BAKE.md — the daily bake, run by a Claude scheduled task at 5:00 AM Pacific

This file is the complete operating spec for baking davidsdailybread.com.
The scheduled task's prompt says only: clone the repo, read this file, follow it.
Everything editorial is YOUR job as the session (research, judgment, writing).
Everything mechanical is `ddb_session_bake.py`'s job (rendering, archive, feed,
state). Do not hand-edit rendered pages; do not bypass the script.

## Hard rules (from BRAND.md, which wins all conflicts)

0. The brand statement is exactly **Loved by God**. It already lives in the
   templates and feed copy; never rephrase or remove it.
1. **No em dashes** in anything a reader sees. Rewrite with comma, colon,
   semicolon, period, or parentheses. The renderer refuses content containing them.
2. **Every fact traces to its source link.** No invented numbers, quotes, or
   details. If you could not fetch an article's text, write conservatively from
   the headline alone.
3. **`/header-art.png` is the only top-of-page art.** The templates handle this;
   never change art references.
4. **Never edit** `chronicles.html`, `secret-menu.html`, `subscribe.html`,
   `404.html`, `templates/`, `BRAND.md`, or this file during a bake. The bake
   writes ONLY: `index.html`, `tech.html`, `markets.html`, `science.html`,
   `editions/<date>-morning.html`, `archive.html` (marked list only, via the
   script), `archive.json`, `feed.xml`, `bakery-state.json`, and (restock only)
   `kings-satchel.json`.
5. **Work from the fresh clone only.** Never read site state from the live
   davidsdailybread.com (the CDN serves stale files for hours).
6. The email newsletter is retired. Never add subscribe links or email CTAs.

## The bake, step by step

**0. Setup.** Clone the public repo anonymously over plain HTTPS. There is no
token anywhere, by design: unattended publishing authenticates through the
Claude GitHub App at push time (never embed, request, or echo credentials):

    git clone --depth 10 https://github.com/Ironman1421/davidsdailybread.git site
    cd site && git config user.name "DDB Baker" && git config user.email "bake@davidsdailybread.com"

Edition date = today in America/New_York (the site's clock): `TZ=America/New_York date +%F`.
If `editions/<date>-morning.html` already exists on main, today is already baked: STOP and report that instead of double-baking.

**1. Reader plan.** `python3 ddb_session_bake.py --plan` → JSON telling you which
reader submission to answer (`ask`), which letter the King replies to (`king`,
either reader mail or a house-satchel draw), and which Crumb Board pin to post
(`pin`). Null means that section stays empty today; never invent submissions.
Reader submissions come from `counter.csv` in the clone, committed daily at
4:45 AM Pacific by `.github/workflows/counter-sync.yml` (this sandbox cannot
reach docs.google.com, so the committed copy is the source; a "CSV fetch failed"
warning from the script is expected and harmless).

**2. Research.** Using web search, gather TODAY'S real news (last ~24 hours,
reputable primary sources) for the three sections: **tech** (AI, chips, software,
the industry), **markets** (stocks, deals, earnings, macro), **science** (space,
physics, medicine, discovery). You need up to 6 stories per section, ranked by
substance. For each story capture the real article URL and fetch the article
text to ground your writing. Drop stories you cannot verify. Fewer than 6 solid
stories in a section is fine (minimum 2); never pad with weak or stale items.

**3. Write the edition** into `content.json`:

```json
{
  "date": "YYYY-MM-DD",
  "lead":   {"section": "tech|markets|science", "title": "...", "url": "https://...",
             "badge": "Technology|Business & markets|Science",
             "standfirst": "one punchy editorial sentence",
             "body": "2-4 sentences of real synthesized news writing, grounded facts"},
  "cards":  {"tech": [{"title": "...", "url": "https://...",
                       "dek": "<b>Two-to-four-word lead-in</b> rest of one factual sentence."},
                      "... up to 6 per section, best first"],
             "markets": ["..."], "science": ["..."]},
  "glance": {"tech": "one <=20-word roundup sentence", "markets": "...", "science": "..."},
  "reader": {"ask":  {"question": "...", "answer": "...", "state_key": "<from plan>"},
             "king": {"question": "...", "from": "<name, reader mail only>", "answer": "...",
                      "state_key": "<from plan>"  ,  "satchel_id": "<instead, if satchel draw>"},
             "pin":  {"text": "...", "sig_name": "...", "state_key": "<from plan>"}}
}
```

Editorial voice (BRAND.md): the news itself is straight factual journalism, no
bread metaphors. Lead: pick the single most substantive story across ALL
sections (impact beats recency; a routine photo-of-the-day loses to real news).
Deks: one sentence, opening `<b>bold lead-in</b>`. Reader sections: **Ask the
Baker** answers are factual with exactly one bread/baking analogy. **Letters to
the King** replies are the historical King David: poetic, warm, biblical
register with a wink, factually sound. **Crumb Board** pins get a light typo
copyedit only, never a rewrite; `pin.text` is the corrected pin. Copy `state_key`
/ `satchel_id` values from the plan verbatim. Reader sections that were null in
the plan are omitted or null here.

**4. Render.** `python3 ddb_session_bake.py --render --content content.json --date <date>`
The script validates, renders every page, updates archive + feed + state, and
self-checks. If it fails, fix content.json and re-run; never hand-patch output.

**5. Review like an editor.** Open the rendered `index.html` and read it. Check:
the lead reads like front-page news, deks are grounded and non-generic, links
point where they claim, the date is right. Fix content.json and re-render if not.

**6. Publish.** Two commits, matching house convention, then push:

    git add index.html tech.html markets.html science.html editions/ bakery-state.json kings-satchel.json
    git commit -m "Morning edition <Weekday>, <Month> <D>, <YYYY>"
    git add archive.html archive.json feed.xml
    git commit -m "Archive: <Weekday>, <Month> <D>, <YYYY> Morning edition"
    git push origin main

If push is rejected (non-fast-forward), fetch and rebase once and push again;
if it still fails, stop and report rather than force-pushing. The push
authenticates through the Claude GitHub App (no tokens, by design); if
authentication is unavailable, leave the commits local and report per step 9
so David can publish manually.

**7. Verify.** Fetch
`https://raw.githubusercontent.com/Ironman1421/davidsdailybread/main/archive.json`
and confirm today's entry (raw is the truth; the live CDN may lag a few minutes,
that is fine and only worth a soft note).

**8. Satchel restock (only when the plan reported `satchel_unused` < 3).**
Append new letters to `kings-satchel.json` (same schema, next `KS-0NN` ids,
target 16 total unused) BEFORE step 6 so they ride in the edition commit.
House letters are timeless questions a reader might ask the King, in the same
warm register as the existing ones. Never delete or edit existing letters.

**9. Report.** End with a short summary: date, lead headline, story count per
section, which reader sections ran, verification result. On ANY failure, say
plainly what failed and what state the repo was left in; never push a partial
or unverified edition, and never mark a failed bake as success.

## Ops notes

- `/archive.json` and the `/editions/…` URLs are a public contract: the DAICC
  distribution pipeline reads them daily at 05:35 PT (from
  raw.githubusercontent.com). Never change their shape or paths without
  David's sign-off BEFORE deploying.
- The scheduled task fires at 12:00 UTC (5:00 AM Pacific during daylight time).
  When US daylight time ends (early November) the task and the counter-sync
  workflow cron both need a +1 hour nudge to stay at their Pacific times.
- The schedule and this spec were set up 2026-07-17 when David simplified the
  pipeline: one daily morning bake by a Claude scheduled task; the Spark/Hermes
  pipeline and the Buttondown newsletter are retired.
