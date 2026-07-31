# BAKE.md — the daily bakes, run by GitHub Actions (morning 5:05 AM PT, evening 3:35 PM PT)

This file is the complete operating spec for baking davidsdailybread.com,
which is baked twice daily:

- the **morning edition** (cron 12:05 UTC): straight news on tech, markets,
  and science, plus the reader sections. Steps 1-9 below.
- the **evening edition** (cron 22:35 UTC): the Field Guide. Trending tools
  and trending workflows for everyday people, and nothing else: no news
  after dark (news belongs to the morning). See "The evening bake" below.

Each bake runs in GitHub Actions (`.github/workflows/ddb-bake.yml`): the runner
checks out the repo, resolves the edition date and slot, and invokes a Claude
session whose prompt says only follow this file. The workflow, not the session,
commits and pushes; a Claude session has no repository write credential and
would die on `git push` with HTTP 403.
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
   `404.html`, `templates/`, `BRAND.md`, or this file during a bake. The
   **morning** bake writes ONLY: `index.html`, `tech.html`, `markets.html`,
   `science.html`, `editions/<date>-morning.html`, `archive.html` (marked list
   only, via the script), `archive.json`, `feed.xml`, `bakery-state.json`, and
   (restock only) `kings-satchel.json`. The **evening** bake writes ONLY:
   `index.html`, `editions/<date>-evening.html`, `archive.html` (marked list
   only), `archive.json`, and `feed.xml`; it never touches the category pages,
   the reader state, the satchel, or `counter.csv`.
5. **Work from the fresh clone only.** Never read site state from the live
   davidsdailybread.com (the CDN serves stale files for hours).
6. The email newsletter is retired. Never add subscribe links or email CTAs.
7. **The lead title feeds X.** Each edition's archive `lead` (= the lead
   story's title) is auto-posted to @DavidDailyBread by the DAICC pipeline
   with fail-closed gates: keep every lead title self-contained and roughly
   **130 characters or fewer**. An over-length lead means the X post is
   SKIPPED, not truncated (the evening template tops out around a 146-char
   lead); an em dash also fails the gate, but rule 1 already bans those.

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

This run has a **slot** (morning or evening) and one of two **modes**, and the
workflow tells you both:

- **morning + daily** — the normal morning news bake for today: research news
  from the last ~24 hours and run the reader sections per the `--plan` output
  (steps 1-8 below).
- **evening + daily** — the trends bake for today: follow "The evening bake"
  section below. Never run `--plan`; render with `--slot evening`.
- **backfill** (either slot) — reconstructing an edition that was never
  published, for a past date. Research only material published on or in the 24
  hours before that date (use dated search terms, verify each item's
  publication date, never use anything published after the edition date), and
  skip the reader sections entirely: do not run `--plan`, omit `reader` from
  `content.json`, and do not touch `kings-satchel.json` or `bakery-state.json`
  (those days had no live reader interaction and inventing one would be
  dishonest). Render with `--slot <slot>`.

Steps 1-9 below are the **morning** bake. The evening bake replaces steps 1-3
with its own section and skips the satchel restock; render, review, accuracy
pass, and report (steps 4, 5, 5A, 9) apply to both slots.

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

**4. Render.** `python3 ddb_session_bake.py --render --content content.json --date <date> --slot <slot>`
(`--slot` defaults to morning.) The script validates, renders every page,
updates archive + feed + state, and self-checks. If it fails, fix content.json
and re-run; never hand-patch output.

**5. Review like an editor.** Open the rendered `index.html` and read it. Check:
the lead reads like front-page news, deks are grounded and non-generic, links
point where they claim, the date is right. Fix content.json and re-render if not.

**5A. Accuracy pass.** This step is required before handoff and applies to both
slots. Go back through the edition one item at a time and check each claim
against the source you actually fetched in this run, working from the fetched
text rather than from memory:

- every item traces to a URL you fetched, and the link resolves to the story it
  claims;
- every number, quote, date, name, and price appears in that fetched text. Where
  you only had the headline, the item stays at headline level and carries no
  specifics;
- evening only: each item shows WHERE it is trending, read from the cited page,
  and any popularity figure (stars, upvotes, views) is read from that page too;
- the lead title is self-contained and about 130 characters or fewer, so the X
  gate passes;
- nothing reader-visible contains an em dash.

If an item fails and the source cannot settle it, drop the item and re-render.
If dropping takes a section under its 2-story minimum, stop and report that
plainly per step 9. A bake that halts and says why is a good outcome; an edition
published with an unverified fact is not. Say in your step 9 report that the
accuracy pass ran, and what it changed or dropped.

**6. Publish — the workflow's job, not yours.** Do NOT commit or push. When your
render is clean and reviewed, your job is done; stop there. The workflow takes
over and guards the result before it ships:

- It fails the run unless the slot's edition file `editions/<date>-<slot>.html`
  exists.
- On **backfill** it reverts `index.html`, `tech.html`, `markets.html`,
  `science.html`, `bakery-state.json`, and `kings-satchel.json` so a
  reconstructed edition never displaces the current front page.
- It checks every changed path against the slot's allowlist and fails on
  anything else. Morning: `index.html`, the three section pages, `archive.html`,
  `archive.json`, `feed.xml`, `bakery-state.json`, `kings-satchel.json`,
  `counter.csv`, and `editions/<date>-morning|evening.html`. Evening (tighter):
  ONLY `index.html`, `archive.html`, `archive.json`, `feed.xml`, and
  `editions/<date>-evening.html`.
- It confirms `archive.json` carries this slot's entry, then commits in the
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

**9. Report.** End with a short summary: date, slot, lead headline, story count
per section, which reader sections ran (morning only), verification result. On
ANY failure, say plainly what failed and what state the repo was left in; never
push a partial or unverified edition, and never mark a failed bake as success.

## The evening bake (`--slot evening`)

The evening edition is a different loaf, and since 2026-07-30 (per David) it
carries NO NEWS AT ALL. News is the morning's job, full stop. The evening is
the Field Guide: exactly two sections, the trending TOOLS people started
using today and the trending WORKFLOWS people are following along with. An
announcement, a launch story, a price change, a policy fight, or an industry
debate is news; it belongs to the morning even if it is trending everywhere.
The evening test for every item: could a regular person ACT on this tonight,
by installing the tool or following the workflow? If not, it does not run.
The reader to serve is the average person, not the insider: if an item only
matters to an ML engineer, it loses its slot to one that helps everyone. All
hard rules above apply unchanged.

**E1. Research.** Using web search and fetches, gather TODAY'S trend material
(last ~24 hours preferred; ~48 is acceptable when something is clearly still
rising) from the open web: tech press, blogs and newsletters, Hacker News,
Reddit, GitHub trending, product announcement pages, video/tutorial writeups,
and press coverage OF viral X/social posts. You have no X/Twitter access and
that is deliberate: a viral post reaches you through coverage about it, and
that coverage is your citable source. The two sections:

- **tools** (the shelf) — new or newly upgraded tools, apps, and features an
  everyday person could start using TONIGHT, and that people are actually
  picking up right now. Each shelf item must show WHERE it is trending in
  the cited source (GitHub trending, Hacker News front page, a subreddit
  lighting up, press coverage of a viral post); if you cannot show where,
  it is not trending and it does not go on the shelf. Capture what it does,
  what it costs (say if there is a free tier), where it runs, and one honest
  caveat, which the blurb must carry. Real availability only: never present
  waitlist-only vaporware as usable, never invent pricing. The shelf-foot
  line "no waitlists, no vaporware" is a standing promise; keep it true.
- **workflows** (the recipes) — concrete ways people are using tools to do
  something better, written up so a non-expert could follow along: a how-to,
  a recipe, a clever pipeline from a blog or video that is making the
  rounds. Say what it accomplishes, list the 2-4 things you need in order
  to try it, and give an honest time estimate.

Up to 6 items per section, best first, minimum 2, never pad. Fetch each
source's text before writing about it; the morning's rule holds here with
extra force: no figure survives that was not read in the article itself, and
popularity numbers (stars, upvotes, views) only as read from the cited page,
never from memory.

**E2. Write the edition** into `content.json`. The evening schema is its own
(NOT the morning card shape), and there is NO `reader` key (the Counter
feeds the morning only; the renderer refuses an evening `reader`):

```json
{
  "date": "YYYY-MM-DD",
  "lead":   {"section": "tools|workflows", "title": "...", "url": "https://...",
             "badge": "Trending tool|Trending workflow",
             "standfirst": "one punchy editorial sentence",
             "body": "2-4 sentences of grounded, factual writing",
             "note": "OPTIONAL handwritten margin aside, <=40 chars, e.g. worth an evening"},
  "cards":  {"tools":     [{"name": "short shelf name, <=60 chars", "url": "https://...",
                            "cost": "Free | Free tier | $N/mo (as read, <=32 chars)",
                            "kind": "what/where it runs, <=32 chars",
                            "seen": "where it is trending, <=32 chars",
                            "blurb": "one factual sentence; must carry the honest caveat"},
                           "... 2-6, best first"],
             "workflows": [{"title": "...", "url": "https://...",
                            "dek": "<b>Two-to-four-word lead-in</b> rest of one factual sentence.",
                            "needs": ["2-4 short items, <=40 chars each"],
                            "time": "honest estimate chip, <=24 chars"},
                           "... 2-6, best first"]},
  "glance": {"tools": "one <=20-word roundup sentence", "workflows": "..."}
}
```

Lead ("Start here tonight"): the single most useful-to-everyone item of the
day; usefulness beats hype. It is one of the two sections' items promoted to
the top, and its `title` doubles as the archive lead (X rules apply, hard
rule 7). `lead.note` is the only handwritten aside on the page: use it when
a short warm nudge fits (worth an evening, try this first); omit it freely.
Voice: the same straight factual journalism as the morning, no bread
metaphors in the writing; workflow deks open with a `<b>bold lead-in</b>`;
tool blurbs are plain text (no markup) and each carries its caveat.

**E3. Render, review, report.**
`python3 ddb_session_bake.py --render --content content.json --date <date> --slot evening`
then review it like an editor (step 5), run the step 5A accuracy pass, and
finish with the step 9 report.
The renderer builds the shelf tiles and recipe cards from the JSON; the
template (templates/evening.html, the Field Guide layout) is never edited at
bake time. The evening bake never runs `--plan`, never writes the category
pages, and never touches `kings-satchel.json`, `bakery-state.json`, or
`counter.csv`; the workflow's evening allowlist enforces this.

## Ops notes

- `/archive.json` and the `/editions/…` URLs are a public contract: the DAICC
  distribution pipeline reads them daily (morning and evening digest runs, from
  raw.githubusercontent.com). Never change their shape or paths without
  David's sign-off BEFORE deploying. `edition` values are `morning` and
  `evening`; downstream readers ground each digest in its own slot.
- **Publishing runs in GitHub Actions**, not in a Claude session, and the push
  authenticates with the workflow's built-in `GITHUB_TOKEN`. There is NO
  personal access token anywhere in this pipeline. A Claude session has no
  repository write credential and cannot push (it 403s); that is why the bake
  lives in `.github/workflows/ddb-bake.yml`.
- **Claude authenticates** inside the runner from the repository secret
  `CLAUDE_CODE_OAUTH_TOKEN` (created with `claude setup-token`), with
  `ANTHROPIC_API_KEY` as a fallback. If neither secret is set the bake step
  stops with a clear error before doing any work.
- The workflow fires twice daily: 12:05 UTC for the morning (5:05 AM Pacific
  during daylight time, 20 minutes after counter-sync at 11:45 UTC) and
  22:35 UTC for the evening (3:35 PM Pacific during daylight time). GitHub
  cron fires late, not never (lag up to ~2-3 hours observed); both times are
  "no earlier than". **When US daylight time ends (early November) BOTH bake
  crons AND the counter-sync cron need a +1 hour nudge** to stay at their
  Pacific times.
- **To bake a specific date or slot by hand**, dispatch the workflow: in the
  repo's Actions tab open "Daily bake", click "Run workflow", set the `date`
  input to `YYYY-MM-DD` (blank means today in New York) and pick the `slot`
  (morning is the default). A past date runs in backfill mode automatically.
  You can also override the `model` input there. The standing target is
  **`claude-opus-5`** ($5 / $25 per MTok), which is the workflow default and is
  the model that produced the first clean evening edition on 2026-07-30.
  `claude-sonnet-5` is cheaper but its safeguard classifier flagged this prompt
  twice that same day, so it is not a safe fallback for the evening slot.
  `claude-fable-5` ($10 / $50 per MTok, double Opus 5) is a case-by-case
  escalation only, never the standing default, and any bake that uses it is
  noted with its reason in the HQ ops log.
- The morning schedule and this spec were set up 2026-07-17 when David
  simplified the pipeline to one daily morning bake; the Spark/Hermes pipeline
  and the Buttondown newsletter are retired. The bake moved into GitHub
  Actions on 2026-07-29 to fix the unattended `git push` 403. The evening
  edition returned 2026-07-30 (per David) with the trends identity, making
  the site twice-daily again.
