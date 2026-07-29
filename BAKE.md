# BAKE.md — the daily bake, run by GitHub Actions at 5:05 AM Pacific

This file is the complete operating spec for baking davidsdailybread.com.
The bake runs in GitHub Actions (`.github/workflows/ddb-bake.yml`): the runner
checks out the repo, resolves the edition date, and invokes a Claude session
whose prompt says only follow this file. The workflow, not the session, commits
and pushes; a Claude session has no repository write credential and would die on
`git push` with HTTP 403.
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

**0. Setup — nothing to do.** The GitHub Actions runner has already done it.
The repo is checked out in the current working directory on branch `main`, and
the edition date has already been resolved and handed to you. So:

- Do NOT clone anything; work from this checkout.
- Do NOT run `git config` to set a git identity.
- Do NOT run any git command that writes (`add`, `commit`, `push`, `checkout`,
  `reset`, …). The workflow owns all of that after you finish.
- Use the date you were handed VERBATIM (`--date <date>`). Do not compute it
  yourself; the runner already did (`TZ=America/New_York date +%F`, or a
  dispatched date). If `editions/<date>-morning.html` already exists, the
  workflow refuses the run before you start, so you will never double-bake.

This run is one of two **modes**, and the workflow tells you which:

- **daily** — the normal morning bake for today: research news from the last
  ~24 hours and run the reader sections per the `--plan` output (steps 1-8 below).
- **backfill** — reconstructing a morning edition that was never published, for
  a past date. Research only news published on or in the 24 hours before that
  date (use dated search terms, verify each story's publication date, never use
  a story published after the edition date), and skip the reader sections
  entirely: do not run `--plan`, omit `reader` from `content.json`, and do not
  touch `kings-satchel.json` or `bakery-state.json` (those days had no live
  reader interaction and inventing one would be dishonest).

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

**6. Publish — the workflow's job, not yours.** Do NOT commit or push. When your
render is clean and reviewed, your job is done; stop there. The workflow takes
over and guards the result before it ships:

- It fails the run unless `editions/<date>-morning.html` exists.
- On **backfill** it reverts `index.html`, `tech.html`, `markets.html`,
  `science.html`, `bakery-state.json`, and `kings-satchel.json` so a
  reconstructed morning never displaces the current front page.
- It checks every changed path against an allowlist (`index.html`, the three
  section pages, `archive.html`, `archive.json`, `feed.xml`, `bakery-state.json`,
  `kings-satchel.json`, `counter.csv`, and `editions/<date>-morning|evening.html`)
  and fails on anything else.
- It confirms `archive.json` carries this morning's entry, then commits in the
  house style (edition commit, then the `Archive:` commit), rebases on `main`
  (counter-sync may have pushed while you baked), and pushes.

**7. Verify — also the workflow's job.** After pushing, the workflow polls
`https://raw.githubusercontent.com/Ironman1421/davidsdailybread/main/archive.json`
until the edition date appears (raw is the truth; the live CDN may lag a few
minutes, which the workflow logs as a soft warning, not a failure).

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
- **Publishing runs in GitHub Actions**, not in a Claude session, and the push
  authenticates with the workflow's built-in `GITHUB_TOKEN`. There is NO
  personal access token anywhere in this pipeline. A Claude session has no
  repository write credential and cannot push (it 403s); that is why the bake
  lives in `.github/workflows/ddb-bake.yml`.
- **Claude authenticates** inside the runner from the repository secret
  `CLAUDE_CODE_OAUTH_TOKEN` (created with `claude setup-token`), with
  `ANTHROPIC_API_KEY` as a fallback. If neither secret is set the bake step
  stops with a clear error before doing any work.
- The workflow fires at 12:05 UTC (5:05 AM Pacific during daylight time,
  20 minutes after counter-sync at 11:45 UTC). **When US daylight time ends
  (early November) the `ddb-bake` cron AND the counter-sync cron both need a
  +1 hour nudge** to stay at their Pacific times.
- **To bake a specific date by hand**, dispatch the workflow: in the repo's
  Actions tab open "Daily bake", click "Run workflow", and set the `date`
  input to `YYYY-MM-DD` (blank means today in New York). A past date runs in
  backfill mode automatically. You can also override the `model` input there.
- The schedule and this spec were set up 2026-07-17 when David simplified the
  pipeline: one daily morning bake; the Spark/Hermes pipeline and the Buttondown
  newsletter are retired. It moved into GitHub Actions on 2026-07-29 to fix the
  unattended `git push` 403.
