# BAKE.md — the daily bakes (reader-ready near 5:00 AM PT and 3:00 PM PT)

This file is the complete operating spec for baking davidsdailybread.com,
which is baked twice daily:

- the **morning edition** (Spark dispatch at 4:40 AM Pacific): politics-free
  news and Scripture, paired story by story across tech, markets, and science,
  plus reviewed house-satchel material when the plan selects it.
  New reader intake is paused. Steps 1-9 below.
- the **evening edition** (Spark dispatch at 2:40 PM Pacific): the Field Guide.
  Broadly useful productivity tools, repeatable practical workflows, and a
  short Keep and Ponder closing for everyday people, with no news after dark
  (news belongs to the morning). See "The evening bake" below.

The production starts target reader-ready publication near 5:00 AM Pacific
(8:00 AM Eastern) and 3:00 PM Pacific (6:00 PM Eastern). GitHub also carries
delayed backup schedules at 4:45 AM and 2:45 PM Pacific. Recent production
evidence puts a full bake at roughly 9 to 14 minutes, so these starts preserve
a small delivery allowance without publishing hours before the stated windows.
Each backup uses paired UTC candidates plus an offset gate so exactly one is
active across daylight and standard time without a manual seasonal edit.

Each bake runs in GitHub Actions (`.github/workflows/ddb-bake.yml`): the runner
checks out the repo, resolves the edition date and slot, and invokes a Claude
session whose prompt says only follow this file. The workflow, not the session,
commits and pushes; a Claude session has no repository write credential and
would die on `git push` with HTTP 403.
Everything editorial is YOUR job as the session (research, judgment, writing).
Everything mechanical is `ddb_session_bake.py`'s job (rendering, archive, feed,
state). Do not hand-edit rendered pages; do not bypass the script.

## Hard rules (from FOUNDER_DOCTRINE.md and BRAND.md)

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
   `index.html`, `editions/<date>-evening.html`, `evening-catalog.json`,
   `archive.html` (marked list only), `archive.json`, and `feed.xml`; it never
   touches the category pages, the reader state, or the satchel.
   Backfills do not update `evening-catalog.json`.
5. **Work from the fresh clone only.** Never read site state from the live
   davidsdailybread.com (the CDN serves stale files for hours).
6. Newsletter strategy and local product-integration prototypes may proceed
   outside a bake, but operations remain disabled. The templates preserve their
   current link to the fail-closed `/subscribe.html`; a bake never drafts,
   tests, schedules, sends, imports, configures, credentials, or receives
   newsletter data.
7. **The lead title is the X distribution contract.** Each edition's archive
   `lead` (= the lead story's title) is eligible for a canonical post to
   @DavidDailyBread. Spark's guarded `daicc-ddb-autopost` service is the sole
   active canonical broadcaster. The repository broadcaster is a reviewed
   replacement path but remains disabled and kill-switched; never activate both
   lanes. Both are governed by `docs/DISTRIBUTION_SPEC.md`, and the editorial
   session never receives X credentials. The active-lane observation is recorded
   in `docs/OPERATIONS_EVIDENCE_2026-08-01.md`. Keep every lead title self-contained and
   **130 characters or fewer**. An over-length lead is skipped, never truncated
   (the evening template tops out around a 146-character lead); an em dash also
   fails the gate, but rule 1 already bans those.
8. **Morning Scripture is renderer-owned BSB text.** Every morning story gets
   one identifier from the verified repository catalog and one required,
   reader-directed connection sentence. Never type, generate, rewrite, combine,
   simplify, or paraphrase the verse, reference, translation label, or Bible
   link. Scripture guides the reader's response. It never blesses, condemns,
   diagnoses, or assigns biblical meaning to a person, company, government, or
   news event. Never claim divine endorsement, judgment, or fulfilled prophecy.
   If a pairing feels forced or risky, reject the story. The evening's reviewed
   KJV Keep and Ponder format remains unchanged.
9. **Morning news is politics-free.** Exclude stories centered on politicians,
   parties, elections, campaigns, polling, partisan disputes, culture-war
   disputes, war, diplomacy, sanctions, tariffs, or geopolitical maneuvering.
   Political personalities never lead. A completed government rule may run only
   when it directly changes technology, markets, or science, and the story is
   framed around the practical effect rather than the political contest or
   personality.

## The bake, step by step

**0. Setup — nothing to do.** The GitHub Actions runner has already done it.
The repo is checked out in the current working directory on branch `main`, and
the edition date has already been resolved and handed to you. So:

- Do NOT clone anything; work from this checkout.
- Do NOT run `git config` to set a git identity.
- Do NOT run any git command that writes (`add`, `commit`, `push`, `checkout`,
  `reset`, …). The workflow owns all of that after you finish.
- Use the date you were handed VERBATIM (`--date <date>`). Do not compute it
  yourself; the runner already did (`TZ=America/Los_Angeles date +%F`, or a
  dispatched date). If `editions/<date>-morning.html` already exists, the
  workflow refuses the run before you start, so you will never double-bake.

This run has a **slot** (morning or evening) and one of two **modes**, and the
workflow tells you both:

- **morning + daily** — the normal morning news bake for today: research news
  from the last ~24 hours and run `--plan` only for reviewed house-satchel
  material. Public Ask the Baker, reader Letter, and Crumb Board intake is
  paused (steps 1-8 below).
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

**1. Reviewed-material plan.** `python3 ddb_session_bake.py --plan` → JSON that
may select one reviewed house-satchel letter for the King. While public reader
intake is paused, `ask` and `pin` are always null, and `king` is either a house
letter or null. The plan reads only `kings-satchel.json` and
`bakery-state.json`; it has no Counter, network, or public-submission input and
never mutates state. Never invent a submission or add submission-derived fields.

**2. Research.** Using web search, gather TODAY'S real, politics-free news (last ~24 hours)
for the three sections: **tech** (AI, chips, software, the industry), **markets**
(stocks, deals, earnings, macro), **science** (space, physics, medicine,
discovery). Use this source order: the original primary source or first-party
announcement first; original reporting with named evidence second; reputable
secondary coverage only when it adds necessary verification or context. An
aggregator may help discovery but is not the preferred final source when the
underlying report is available. You need up to 6 stories per section, ranked by
substance, source authority, verification depth, freshness, and reader relevance,
in that order. For each story capture the real article URL and fetch the article
text to ground your writing. Drop stories you cannot verify. Fewer than 6 solid
stories in a section is fine (minimum 2); never pad with weak or stale items.
Apply hard rule 9 before ranking. A political or geopolitical story remains
excluded even when it moves markets.

**3. Select Scripture pairings and write the edition** into `content.json`.
The lead and every card receive a pairing. For each story, search the verified
catalog with a few themes from the reader's appropriate response, for example:

```sh
python3 ddb_session_bake.py --scripture-catalog --scripture-query "wisdom discernment learning"
```

Choose the most meaningful candidate and copy only its `id` into that story's
`scripture.id`. The renderer supplies the exact BSB wording, reference,
translation label, and Bible.com link from `scripture/bsb-verses.json`. Add one
required brief plain-text `connection` sentence using readers, we, us, or our.
The sentence must guide the reader's reflection, not interpret the news event as
an act or judgment of God. Do not force a pairing. Reject the story instead.

Then write `content.json`:

```json
{
  "date": "YYYY-MM-DD",
  "lead":   {"section": "tech|markets|science", "title": "...", "url": "https://...",
             "badge": "Technology|Business & markets|Science",
             "standfirst": "one punchy editorial sentence",
             "body": "2-4 sentences of real synthesized news writing, grounded facts",
             "scripture": {"id": "PRO.18.15",
                            "connection": "We can seek wisdom as we consider this story."}},
  "cards":  {"tech": [{"title": "...", "url": "https://...",
                       "dek": "<b>Two-to-four-word lead-in</b> rest of one factual sentence.",
                       "scripture": {"id": "PRO.18.15",
                                     "connection": "We can seek wisdom as we consider this story."}},
                      "... up to 6 per section, best first"],
             "markets": ["..."], "science": ["..."]},
  "glance": {"tech": "one <=20-word roundup sentence", "markets": "...", "science": "..."},
  "reader": {"king": {"question": "...", "answer": "...",
                      "satchel_id": "<from the reviewed house-satchel plan>"}}
}
```

Editorial voice (BRAND.md): the news itself is straight factual journalism, no
bread metaphors. Lead: pick the single most substantive story across ALL
sections (impact beats recency; a routine photo-of-the-day loses to real news).
Deks: one sentence, opening `<b>bold lead-in</b>`. A selected house-satchel
**Letter to the King** reply uses the historical King David voice: poetic, warm,
biblical register with a wink, factually sound. Copy its `question` and
`satchel_id` from the plan verbatim. Do not add `ask`, `pin`, `state_key`,
`from`, or any other submission-derived field while intake is paused.

**4. Render.** `python3 ddb_session_bake.py --render --content content.json --date <date> --slot <slot> --mode <daily|backfill>`
(`--slot` defaults to morning.) The script validates, renders every page,
updates archive + feed + state, and self-checks. If it fails, fix content.json
and re-run; never hand-patch output.

**5. Review like an editor.** Open the rendered `index.html` and read it. Check:
the lead reads like front-page news, deks are grounded and non-generic, links
point where they claim, the date is right, every story has Scripture for
Reflection, and no political or geopolitical framing slipped through. Fix
content.json and re-render if not.

**5A. Accuracy pass.** This step is required before handoff and applies to both
slots. Go back through the edition one item at a time and check each claim
against the source you actually fetched in this run, working from the fetched
text rather than from memory:

- every item traces to a URL you fetched, and the link resolves to the story it
  claims;
- every number, quote, date, name, and price appears in that fetched text. Where
  you only had the headline, the item stays at headline level and carries no
  specifics;
- morning only: every story's Scripture identifier came from the verified
  catalog, every rendered wording and reference matches that catalog exactly,
  every connection is reader-directed and respectful, and no pairing assigns
  biblical meaning or divine approval, condemnation, or judgment to the event;
- morning only: every story passes the politics-free rule, including the ban on
  war and diplomacy even when either is market-moving;
- evening only: fetch each item's factual `url` and separate `trend_url`; verify
  product facts, pricing, and availability from the factual source, and verify
  the `seen` label plus every popularity figure from the trend source;
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
  and `editions/<date>-morning|evening.html`. Evening (tighter):
  ONLY `index.html`, `archive.html`, `archive.json`, `feed.xml`, and
  `editions/<date>-evening.html`.
- It confirms `archive.json` carries this slot's entry, then commits in the
  house style (edition commit, then the `Archive:` commit), rebases on `main`
  to incorporate any newer published edition, and pushes.

**7. Verify — also the workflow's job.** After pushing, the workflow compares
the pushed commit with GitHub's authoritative `refs/heads/main`, then checks the
exact public edition URL and title on davidsdailybread.com. A delayed public
page is a soft warning after a bounded retry; verification never polls the raw
GitHub content CDN.

**8. Satchel restock (only when the plan reported `satchel_unused` < 3).**
Append new letters to `kings-satchel.json` (same schema, next `KS-0NN` ids,
target 16 total unused) BEFORE step 6 so they ride in the edition commit.
House letters are timeless questions a reader might ask the King, in the same
warm register as the existing ones. Never delete or edit existing letters.

**9. Report.** End with a short summary: date, slot, lead headline, story count
per section, whether a reviewed house letter ran (morning only), verification result. On
ANY failure, say plainly what failed and what state the repo was left in; never
push a partial or unverified edition, and never mark a failed bake as success.

## The evening bake (`--slot evening`)

The evening edition is a different loaf, and since 2026-07-30 (per David) it
carries NO NEWS AT ALL. News is the morning's job, full stop. The evening is
the Field Guide: exactly two sections, broadly useful productivity TOOLS and
repeatable WORKFLOWS that multiply what an everyday person can get done. An
announcement, a launch story, a price change, a policy fight, or an industry
debate is news; it belongs to the morning even if it is trending everywhere.
The evening test for every item: could a regular person ACT on this tonight,
by installing the tool or following the workflow, and then reuse the value in
ordinary life or work? If not, it does not run.
The reader to serve is the average person, not the insider: if an item only
matters to an ML engineer, it loses its slot to one that helps everyone. All
hard rules above apply unchanged.

**Force-multiplier gate.** Apply this before trend ranking. Every candidate
must satisfy all four tests:

1. **Broad utility:** it helps a substantial share of ordinary readers rather
   than one location, device hack, specialist role, or niche hobby.
2. **Repeatability:** it is useful daily or weekly, establishes a reusable
   operating routine, or creates compounding value after setup.
3. **Concrete leverage:** it saves time, improves output, supports earning,
   strengthens communication, or reduces mental load.
4. **Actionability:** it is available now and can be adopted with a reasonable
   amount of setup by a non-expert.

Reject one-off crafts and builds, amusements, games, art experiments, demos,
novelty websites, location-specific curiosities, and clever tricks with no
recurring payoff. Trend evidence validates present interest; it never makes a
candidate pass this gate. If fewer than two candidates in a section pass, keep
researching or stop the bake. Never lower the gate to fill the page.

The approved presentation is the July 31 Field Guide format: one useful lead,
the tool shelf and workflows in two lanes, then Keep and Ponder with Mary of
Nazareth as its recurring biblical presence below all actionable material. Its
material is selected by the renderer from the reviewed `evening-rest.json` set.
It presents the reviewed receive, release, and rest material as Keep, Ponder,
and Entrust, and is not reader mail. The masthead links to the standing
`/tools.html` and `/workflows.html` libraries, which read the bounded
`evening-catalog.json`; the links do not scroll to sections in the edition.

**E1. Reviewed handoff or fallback research.** The normal daily-evening path
starts from the runner-local `ddb-reviewed-evening-handoff-v1` packet named in
the run prompt. That packet is the output of one 1:40 PM editorial pass in
which DDB reads X Manager's 12:45 PM research and final X delta proof, performs
its own broader web research, independently verifies every candidate, and makes the final
selected/hold/reject decision. DDB applies this exact Editorial Fit rule:
40% leverage, 30% broad applicability, 20% repeatability, and 10% trend
strength. A selected item must also clear the standing force-multiplier gates.

When the packet has `status: ready`, its `selection.tools` and
`selection.workflows` arrays are editorially final for this edition. Do not
search for additional candidates, refresh X Manager, call `/api/trends` or
`/api/discovery-export`, substitute an item, or rerank the set. Fetch each
selected item's non-X `officialUrl` and `trendUrl` for the final accuracy pass,
correct unsupported copy without changing the selection, then map the packet
into `content.json`. The packet explicitly has
`authority.publicationApproved: false`; it supplies editorial selection, never
publication authority.

If the local handoff explicitly reports `available: false` because the packet
was missing, stale, invalid, or unreachable, use the following normal non-X
source ladder as a fail-open exception. Gather TODAY'S trend material (last ~24 hours preferred;
~48 is acceptable when something is clearly still rising):

1. Discover and prove the trend with a citable Hacker News, GitHub Trending,
   Product Hunt, Reddit, or reputable press page.
2. Verify a tool's capabilities, pricing, platform, and present availability on
   its official product, repository, or documentation page.
3. Ground a workflow in a substantive, followable tutorial, blog, newsletter,
   video write-up, or reputable technology report.

Keep the factual source and trend source separate in `content.json`, and fetch
both. You have no direct X/Twitter access. Do not scrape X through unofficial
tools, mirrors, search snippets, or workarounds. The 2:40 bake never asks X
Manager to research again: X Manager's contribution is already represented in
the reviewed packet, or the bake uses the non-X fallback ladder without it. An
X post never satisfies the factual `url` or citable `trend_url`. Never fail or
pad an edition merely because the reviewed packet was unavailable. The two
sections:

- **tools** (the shelf) — productivity tools, apps, and features an everyday
  person could start using TONIGHT, and that people are actually picking up
  right now. Favor research, writing, communication,
  planning, automation, knowledge capture, sales, marketing, finance, and
  recurring administration. Its `url` is the official product, repository, or
  documentation page used for factual verification. Its `trend_url` is the
  citable page proving the `seen` label. If you cannot prove where it is
  trending, it does not go on the shelf. Capture what it does, what it costs
  (say if there is a free tier), where it runs, and one honest caveat, which the
  blurb must carry. Real availability only: never present waitlist-only vaporware
  as usable, never invent pricing. The shelf-foot line "no waitlists, no
  vaporware" is a standing promise; keep it true.
- **workflows** (the recipes) — repeatable ways people are using tools to do
  recurring work better, written up so a non-expert could follow along: an
  operating routine, a reusable recipe, or a durable pipeline from a blog or
  video that is making the rounds. One-time projects do not qualify. Its `url`
  is the substantive how-to or tutorial, and its `trend_url`
  proves the reader-visible `seen` label. Say what it accomplishes, list the 2-4
  things you need in order to try it, put the primary requirement first for the
  gray card pill, and give an honest time estimate.

Up to 6 items per section, minimum 2, never pad. Among candidates that pass the
force-multiplier gate and factual verification, rank by force-multiplying
utility, broad applicability, repeatability, verified trend strength, and ease
of adoption, in that order. Novelty is not a ranking benefit. Fetch both URLs
for every item before writing about it; the morning's rule holds here with
extra force: no figure survives that was not read in the article itself, and
popularity numbers (stars, upvotes, views) only as read from the cited trend
page, never from memory.

**E2. Write the edition** into `content.json`. The evening schema is its own
(NOT the morning card shape), and there is NO `reader` key (the renderer
refuses an evening `reader`):

```json
{
  "date": "YYYY-MM-DD",
  "lead":   {"section": "tools|workflows", "title": "...", "url": "https://...",
             "trend_url": "https://...", "seen": "verified trend source, <=32 chars",
             "badge": "Trending tool|Trending workflow",
             "standfirst": "one punchy editorial sentence",
             "body": "2-4 sentences of grounded, factual writing",
             "note": "OPTIONAL handwritten margin aside, <=40 chars, e.g. worth an evening"},
  "cards":  {"tools":     [{"name": "short shelf name, <=60 chars", "url": "https://...",
                            "trend_url": "https://...",
                            "cost": "Free | Free tier | $N/mo (as read, <=32 chars)",
                            "kind": "what/where it runs, <=32 chars",
                            "seen": "where it is trending, <=32 chars",
                            "blurb": "one factual sentence; must carry the honest caveat"},
                           "... 2-6, best first"],
             "workflows": [{"title": "...", "url": "https://...",
                            "trend_url": "https://...",
                            "seen": "where it is trending, <=32 chars",
                            "dek": "<b>Two-to-four-word lead-in</b> rest of one factual sentence.",
                            "needs": ["2-4 short items, <=40 chars each"],
                            "time": "honest estimate chip, <=24 chars"},
                           "... 2-6, best first"]},
  "glance": {"tools": "one <=20-word roundup sentence", "workflows": "..."}
}
```

Lead ("Start here tonight"): the single most useful-to-everyone item of the
day; durable leverage beats hype. It is one of the two sections' items promoted
to the top, and its `title` doubles as the archive lead (X rules apply, hard
rule 7). `lead.note` is the only handwritten aside on the page: use it when
a short warm nudge fits (worth an evening, try this first); omit it freely.
Voice: the same straight factual journalism as the morning, no bread
metaphors in the writing; workflow deks open with a `<b>bold lead-in</b>`;
tool blurbs are plain text (no markup) and each carries its caveat.

**E3. Render, review, report.**
`python3 ddb_session_bake.py --render --content content.json --date <date> --slot evening --mode <daily|backfill>`
then review it like an editor (step 5), run the step 5A accuracy pass, and
finish with the step 9 report.
The renderer builds the shelf tiles and recipe cards from the JSON; the
template (`templates/evening.html`, the July 31 Field Guide layout) is never edited
at bake time. A daily render prepends the validated cards to
`evening-catalog.json`, deduplicates by exact source URL, and keeps at most 180
items per library. A backfill leaves the catalog unchanged. The evening bake
never runs `--plan`, never writes the category pages, and never touches
`kings-satchel.json` or `bakery-state.json`; the workflow's
evening allowlist enforces this.

## Ops notes

- `/archive.json` and the `/editions/…` URLs are a public distribution contract.
  Never change their shape or paths without David's sign-off BEFORE deploying.
  `edition` values are `morning` and `evening`; every replacement adapter must
  ground a post in its exact slot and canonical URL.
- **Publishing runs in GitHub Actions**, not in a Claude session, and the push
  authenticates with the workflow's built-in `GITHUB_TOKEN`. There is no
  personal access token in the publishing path. Spark holds a separate,
  fine-grained dispatch-only token for the clock and watchdog path; it cannot
  push site content. A Claude session has no repository write credential and
  cannot push (it 403s); that is why the bake lives in
  `.github/workflows/ddb-bake.yml`.
- **Claude authenticates** inside the runner from the repository secret
  `CLAUDE_CODE_OAUTH_TOKEN` (created with `claude setup-token`), with
  `ANTHROPIC_API_KEY` as a fallback. If neither secret is set the bake step
  stops with a clear error before doing any work.
- Spark is the primary Pacific-time clock for the approved bakes: morning at
  4:40 AM and evening at 2:40 PM. Those starts target reader-ready publication
  near 5:00 AM and 3:00 PM Pacific. GitHub retains delayed bake backups at 4:45
  AM and 2:45 PM. Every bake backup has a PDT/PST UTC pair and an offset gate,
  so exactly one candidate is active and no daylight-saving edit is required.
  The exact-edition guard makes delayed or duplicate bake triggers successful
  no-ops. Counter Sync is a read-only no-op while new reader intake is paused;
  it has no schedule or data endpoint and is not permission to reactivate one.
- **To bake a specific date or slot by hand**, dispatch the workflow: in the
  repo's Actions tab open "Daily bake", click "Run workflow", set the `date`
  input to `YYYY-MM-DD` (blank means today in Pacific time) and pick the `slot`
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
  and its automated Buttondown path are retired. The later four-week manual
  Buttondown plan was paused by David on 2026-07-31; its live signup page is
  preserved, but no activation work or sending is authorized. The bake moved into GitHub
  Actions on 2026-07-29 to fix the unattended `git push` 403. The evening
  edition returned 2026-07-30 (per David) with the trends identity, making
  the site twice-daily again.
