# David's Daily Bread — Brand (single source of truth)

This file is the canonical brand definition for **all** David's Daily Bread surfaces:
the website (davidsdailybread.com), the email newsletter (Buttondown), Chronicles,
the subscribe page, and any future page or tool. If a color, font, or rule here
disagrees with anything else, **this file wins**. Change the brand by editing this
file (and `brand.css`) — nowhere else.

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

> Note (2026-07-09): `#c8a24a` gold / `#0e0e12` bg is the canonical palette (the live
> site's). The older `#d2a53f` / `#121116` / Georgia-serif palette from early drafts
> and the og-card is deprecated for interfaces — the og-card image itself stays as-is.

## Typography

- **Headlines & body prose:** `'Newsreader', Georgia, serif`
- **UI, labels, navigation (tracked-out uppercase):** `'Inter', -apple-system, system-ui, sans-serif`
- **Handwritten (reader notes, Crumb Board pins):** `'Caveat', cursive`
- **The King's voice (Letters to the King, updated 2026-07-09 per David):** answer
  text in `'IM Fell English', 'Cormorant Garamond', Georgia, serif` (antique, royal);
  his signature line ("– David, King in Jerusalem") in `'Cinzel', 'Cormorant Garamond', Georgia, serif`
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
- **`/og-card.png`** (1200×630) is the social/share card (`og:image`) and the email
  header image in Buttondown. Web pages use header-art; social previews and email
  headers use og-card. Never substitute other art.

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
  as reader mail.

## Permanent features (never remove)

- **Subscribe button** (added 2026-07-09): every page ends with the `.sub-cta` line
  ("We Deliver") and the `.sub-btn` pill linking
  to https://buttondown.com/davidsdailybread, directly above the colophon; every
  colophon also carries the RSS and Subscribe text links.
- **Chronicles exports** (2026-07-08): chronicles.html's four note-export buttons
  (Download .md, PDF, email, copy) are hardwired. Never remove or rebuild them;
  edit chronicles.html only from the current live/main version.
- **Notes boxes:** every story card and every page carries localStorage notes with
  the Aa personalization toolbar.
- **Reader features:** Ask the Baker, Letters to the King, The Crumb Board —
  submissions come from the chronicles page. Letters to the King is backstopped by
  the house satchel (`/kings-satchel.json`), restocked weekly by the satchel-steward
  scheduled task; used letters are tracked in `bakery-state.json` (`usedSatchelLetters`)
  and never repeat.
- **RSS:** `/feed.xml`, prepended every bake; the RSS `<link rel="alternate">` tag
  stays in every page head.
- **Selah line:** the "Selah – anything to set down?" vault-door chronicles button
  on the home page footer.

## Where the code lives

- **Page templates:** `/templates/home.html` and `/templates/category.html` in this
  repo. The twice-daily bake fetches them from
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
- **Email design:** configured in Buttondown (Settings → Design → Email): accent
  `#c8a24a`, header image og-card, Modern template. No code in the email body —
  each edition's email is a short Markdown digest.
- **Standing pages** (`/chronicles.html`, `/archive.html`, `/subscribe` assets) are
  NOT rebuilt by the bake. Edit them only from the current live/main version.

## Checklist for any new surface

1. Start from `brand.css` tokens (or copy a template's `:root` block).
2. Masthead: header-art.png at top; og-card.png as `og:image`.
3. Fonts per Typography above.
4. Links/accents in gold; secondary accents steel; badges copper.
5. Baker's voice on public-facing chrome; straight news in content.
6. No em dashes anywhere readers can see (House style above).
