# David's Daily Bread — Brand (reader-visible source of truth)

This file is the canonical brand definition for **all** David's Daily Bread surfaces:
the website (davidsdailybread.com), Chronicles, and any future page or tool. If a color, font, or rule here
disagrees with anything else, **this file wins**. Change the brand by editing this
file (and `brand.css`) — nowhere else. `FOUNDER_DOCTRINE.md` separately governs
mission, ownership, strategic direction, and paused initiatives.

## Brand statement and current cadence

- **Loved by God** is the exact current public brand statement and tagline.
- The exact public mission line is: **Grow in faith. Understand technology
  wisely. Pray for one another. Use what you learn in service to others.** It
  complements **Loved by God** and does not replace the tagline.
- Current operating truth (updated 2026-08-01, per David): the site is **baked
  twice daily** in GitHub Actions, dispatched by Spark's Pacific-time clock
  with DST-safe GitHub backup schedules (spec: `/BAKE.md`, deployment evidence:
  `/docs/OPERATIONS_EVIDENCE_2026-08-01.md`). The **morning
  edition** targets reader-ready publication near 5:00 AM Pacific (8:00 AM
  Eastern). It is straight news on technology, markets, and science, and carries
  the reader sections. The **evening edition** targets reader-ready publication
  near 3:00 PM Pacific (6:00 PM Eastern). It is the Field Guide: trending tools
  and practical workflows for everyday people, and NO news of any kind (news is
  the morning's job). Its
  presentation uses the **July 31 Field Guide** format: one useful lead, a
  two-column tool shelf and workflow lane, then Keep and Ponder with Mary of
  Nazareth below the actionable material. It carries no reader submissions or
  reader-state interaction.
  A delayed trigger is safe because an exact edition is published at most once.
  The website and `/feed.xml` remain the complete, canonical delivery surfaces.
- **Newsletter sending PAUSED (2026-07-31, per David):** preserve the current
  live `/subscribe.html` state, but do not draft, test, schedule, send,
  configure, credential, or advance the former pilot. A new explicit founder
  decision is required before activation work resumes. The website and
  `/feed.xml` remain the complete, canonical delivery surfaces.
- Edition history: evening editions ran 2026-07-07 through 2026-07-14, were
  retired in the 2026-07-17 simplification (one morning edition), and were
  restored 2026-07-30 with the trends identity; later that same day the
  evening dropped its trending-stories section and adopted the two-section
  Field Guide (tools + workflows, no news). Historical edition labels and
  layouts in the archive record what was published on those days; leave
  them intact.

## Palette (canonical)

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0e0e12` | Page background |
| `--panel` | `#16151a` | Paper/card panel background |
| `--ink` | `#ece7db` | Body text |
| `--muted` | `#a7a08f` | Secondary text |
| `--faint` | `#6f6a60` | Tertiary text, labels |
| `--line` | `#28272e` | Hairline borders |
| `--line-strong` | `#3a3941` | Stronger borders |
| `--gold` | `#c8a24a` | Accent: links, highlights, buttons |
| `--gold-soft` | `#8f7538` | Accent borders, hover underlines |
| `--steel` | `#6f9fce` | Secondary accent (editions, numbering) |
| `--steel-soft` | `#456f9c` | Secondary accent, soft |
| `--marker` | `#b9772a` | Copper: badges, signatures |
| `--rose` | `#d98c9d` | Mary of Nazareth: name, posture, floral accents |

> Note (2026-07-09): `#c8a24a` gold / `#0e0e12` bg is the canonical palette (the live
> site's). The older `#d2a53f` / `#121116` / Georgia-serif palette from early drafts
> and the og-card is deprecated for interfaces — the og-card image itself stays as-is.

## Typography

- **Headlines & body prose:** `'Newsreader', Georgia, serif`
- **UI, labels, navigation (tracked-out uppercase):** `'Inter', -apple-system, system-ui, sans-serif`
- **Handwritten (reader notes, Crumb Board pins):** `'Caveat', cursive`
- **The King's voice (Letters to the King, updated 2026-08-01 per David):** answer
  text in `'IM Fell English', 'Cormorant Garamond', Georgia, serif` (antique, royal);
  his signature line ("– David, son of Jesse") in `'Cinzel', 'Cormorant Garamond', Georgia, serif`
  (Roman-capital, regal). The letter itself (the reader's words, the `summary`) stays Newsreader.
- Google Fonts load: Caveat 600/700 · Cinzel 600 · Cormorant Garamond 500/600/700 · IM Fell English regular + italic · Inter 400–700 · Newsreader 400–600 + italics

## House style (IMPERATIVE, per David 2026-07-09)

- **NO EM DASHES, ever, in any published content.** Never use the em dash character
  ("—" or `&mdash;`) in any edition: not in headlines, deks, lead bodies, glance lines,
  Baker answers, King letters, Crumb Board handling, page titles, meta tags, the RSS
  feed, or the newsletter email. Readers have come to associate em dashes with
  AI-written text. Rewrite the sentence instead: use a comma, colon, semicolon,
  period, or parentheses. Where a pure visual separator is genuinely needed
  (title tags, attribution and signature lines, footer labels), use an en dash
  ("–" / `&ndash;`) or a middot ("·" / `&middot;`). This applies to every current
  and future surface. (This file is internal and exempt; everything readers see is not.)
- **Light copyedit of reader slips:** quietly correct obvious spelling and typo
  errors in printed reader questions, King letters, and Crumb Board pins
  (e.g. "Everylasting" becomes "Everlasting"). Never change meaning, voice, or wording
  beyond the correction; when in doubt, print as written.

## Art (standing rules — IMPERATIVE)

- **`/header-art.png`** (1124×418, bg `#16151a`) is the official masthead. It MUST
  appear at the very top of EVERY web page (`<img class="masthead-art" src="/header-art.png">`).
  No other art at the top of any page, ever, unless David explicitly says so.
  Never regenerate, rename, or re-upload it — just reference it.
- **`/og-card.png`** (1200×630) is the social/share card (`og:image`). Web pages use
  header-art; social previews use og-card. Never substitute other art.

## Voice

- **The public site** speaks in the baker's voice — bread metaphors welcome
  ("baked fresh", "first out of the oven", "the full loaf").
- **The news content itself** (articles, deks, email digest body) is real,
  substantive news — no bread metaphors inside the journalism.
- **Ask the Baker** answers: factual, one bread/baking analogy per answer.
- **Letters to the King**: the historical King David persona — poetic, warm,
  biblical register with a wink; factually sound beneath the poetry. When no reader
  letters are waiting, the bake answers ONE letter from the house satchel
  (`/kings-satchel.json`), credited "From the Baker's own shelf" — never presented
  as reader mail. The public section footer says, "Letters answered in the voice of
  the biblical King David."
- **Keep and Ponder with Mary of Nazareth:** the evening's distinct spiritual
  relief after the practical material. Mary is the recurring host and spiritual
  presence only after the trending tools and workflows have finished. She is
  presented through her biblical witness, not through invented first-person
  advice or revelation, and the prayers remain addressed to God. The section
  follows Keep, Ponder, Entrust: one short KJV passage, one release prompt, and
  one prayer. The name and movement are shaped by Luke 2:19. It is contemplative
  product copy selected deterministically from a reviewed repository set, never
  reader mail and never a second Letters to the King. Its visual signature is a
  restrained frame of realistic blush-pink and ivory flowers. The flowers stay
  small and sparse at the card border so Mary and Keep and Ponder remain the
  focus. Mary's name and the Luke 2:19 posture line use `--rose`, never steel or
  gold.

## Permanent features (never remove)

- **Existing weekly email link:** its 2026-07-31 live state is preserved while
  newsletter work is paused. It does not authorize drafting, activation, or
  sending. RSS and the archive remain permanent.
- **Chronicles exports** (2026-07-08): chronicles.html's four note-export buttons
  (Download .md, PDF, email, copy) are hardwired. Never remove or rebuild them;
  edit chronicles.html only from the current live/main version.
- **Notes boxes:** every story card and every page carries localStorage notes with
  the Aa personalization toolbar.
- **Morning Scripture pairings:** every full morning-edition story ends with the
  approved compact inline "Scripture for Reflection" treatment. The current
  morning format has one full lead story; its other cards are briefs and do not
  receive pairings. The verse is exact, verified Berean Standard Bible text
  selected by repository identifier, followed by a linked reference and an
  optional brief editorial connection. Category pages, data-only material,
  navigation, and the evening edition are excluded. The evening's Keep and
  Ponder passage remains KJV.
- **Reader features:** Ask the Baker, Letters to the King, and The Crumb Board
  remain editorial features, but new public submissions are temporarily paused
  until a private intake boundary is verified and David explicitly approves
  reopening. Existing reviewed reader material may still appear. Letters to the
  King is backstopped by the house satchel (`/kings-satchel.json`), restocked
  weekly by the satchel-steward scheduled task; used letters are tracked in
  `bakery-state.json` (`usedSatchelLetters`) and never repeat.
- **RSS:** `/feed.xml`, prepended every bake; the RSS `<link rel="alternate">` tag
  stays in every page head.
- **Evening libraries:** `/tools.html` and `/workflows.html` are standing,
  searchable pages backed by `/evening-catalog.json`. The evening masthead links
  open these pages; they never masquerade as in-page anchor links.
- **Selah line:** the footer points to Chronicles for private, on-device notes
  and says those notes remain on the reader's device. It does not invite a
  public submission while intake is paused.

## Where the code lives

- **Page templates:** `/templates/home.html`, `/templates/evening.html`, and
  `/templates/category.html` in this
  repo. The bake fetches them from
  `https://raw.githubusercontent.com/Ironman1421/davidsdailybread/main/templates/…`
  and replaces ONLY the content tokens (EDITION, LEAD_*, CARD_*, CAT_*, etc.).
  Restyling happens by editing the templates here — never inside the bake prompt.
- **Repo state the bake reads** (`bakery-state.json`, `archive.json`, `kings-satchel.json`,
  `feed.xml`, templates): ALWAYS fetch from `raw.githubusercontent.com/.../main/...`,
  never from the live davidsdailybread.com copy — the GitHub Pages CDN serves stale
  files for hours (cause of the 2026-07-09 duplicate King letter incident).
- **Design tokens:** `/brand.css` (reference stylesheet for new pages, e.g. Chronicles
  or one-off pages; the bake templates carry their full CSS inline for email-safe,
  self-contained archive editions).
- **Standing pages** (`/chronicles.html`, `/archive.html`, `/subscribe.html`) are
  NOT rebuilt by the bake. Edit them only from the current live/main version.

## Checklist for any new surface

1. Start from `brand.css` tokens (or copy a template's `:root` block).
2. Masthead: header-art.png at top; og-card.png as `og:image`.
3. Fonts per Typography above.
4. Links/accents in gold; secondary accents steel; badges copper.
5. Baker's voice on public-facing chrome; straight news in content.
6. No em dashes anywhere readers can see (House style above).
