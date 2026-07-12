#!/usr/bin/env python3
"""DDB bake — transform an aggregated draft into a rendered website edition.

Reads:
  - ~/ddb/drafts/YYYY-MM-DD-{am,pm}.md  (aggregated headlines with source links)
  - site/templates/home.html            (template with {{TOKEN}} placeholders)

Writes:
  - site/editions/YYYY-MM-DD-{am,pm}.html  (dated edition)
  - site/index.html                        (latest edition, overwrites)
  - site/archive.html                      (updated archive listing)
  - site/archive.json                      (updated manifest, from working tree)

Contract:
  - Every headline in the edition traces back to its source link — no
    summarization, no inference, no hallucination.
  - The draft is raw material; the bake produces the published edition.
  - archive.json is read from the git working tree, NOT from the live site.
  - Idempotent: running twice for the same slot with the same inputs
    produces identical output (no double-appending).

Usage:
    ddb_bake.py --slot {am,pm} [--date YYYY-MM-DD] [--outdir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import ddb_satchel
import ddb_synth

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DDB = Path.home() / "ddb"
# Site repo can be either ~/ddb/site-mirror (if cloned) or ~/davidsdailybread.
# DDB_SITE_DIR overrides both — for testing against a scratch copy so a real
# (non-dry-run) bake never touches the actual tracked working tree.
SITE = None
if os.environ.get("DDB_SITE_DIR"):
    SITE = Path(os.environ["DDB_SITE_DIR"])
else:
    for _s in (Path.home() / "davidsdailybread", Path.home() / "ddb" / "site-mirror"):
        if (_s / "templates" / "home.html").exists():
            SITE = _s
            break
if SITE is None or not (SITE / "templates" / "home.html").exists():
    raise RuntimeError("No site repo found. Clone to ~/davidsdailybread or ~/ddb/site-mirror, or set DDB_SITE_DIR")
TEMPLATES = SITE / "templates"
EDITIONS = SITE / "editions"
DRAFTS = DDB / "drafts"

# Google Form response export (Ask the Baker / Letters to the King / Crumb
# Board). Not yet delivered to the Spark — see ddb_satchel.py docstring.
CSV_PATH = Path(os.environ.get("DDB_SATCHEL_CSV", str(DDB / "satchel-responses.csv")))

# Domain for canonical URLs and og:image
DOMAIN = "https://davidsdailybread.com"
OG_IMAGE = f"{DOMAIN}/og-card.png"
HEADER_ART = f"{DOMAIN}/header-art.png"

# Sections map: draft section name -> template section order
SECTIONS = ["tech", "markets", "science"]


def human_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to 'Thursday, July 9, 2026'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A, %B %-d, %Y")


def slot_label(slot: str) -> str:
    return {"am": "Morning", "pm": "Evening"}[slot]


# ---------------------------------------------------------------------------
# Parsing: draft markdown -> structured data
# ---------------------------------------------------------------------------

# Pattern: - [Title](URL)  \n  <sub>Source · Month D HH:MM</sub>
HEADLINE_RE = re.compile(
    r"^-\s+\[([^\]]+)\]\(([^)]+)\)\s*\n\s*<sub>([^<]+)</sub>", re.MULTILINE
)


def parse_draft(path: Path) -> dict[str, list[dict]]:
    """Parse a draft file into sections with headline data.

    Returns {"tech": [{title, url, source, date_str}], ...}
    """
    text = path.read_text(encoding="utf-8")
    result: dict[str, list[dict]] = {s: [] for s in SECTIONS}

    current_section: str | None = None
    lines = text.splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect section header: "## Tech", "## Markets", "## Science"
        section_match = re.match(r"^##\s+(Tech|Markets|Science)\s*$", stripped, re.IGNORECASE)
        if section_match:
            current_section = section_match.group(1).lower()
            i += 1
            continue

        if current_section is None or current_section not in SECTIONS:
            i += 1
            continue

        # Headlines span two lines: "- [Title](URL)  \n  <sub>Source</sub>"
        # Check if this line starts a headline and the next is a sub
        if i + 1 < len(lines):
            next_stripped = lines[i + 1].strip()
            combined = stripped + "\n" + next_stripped
            m = HEADLINE_RE.match(combined)
            if m:
                title = ddb_synth.strip_em_dashes(m.group(1).strip())
                url = m.group(2).strip()
                source_part = m.group(3).strip()

                # Parse source from "Source Name · Jul 09 10:04"
                sp = re.split(r"\s*\u00b7\s*", source_part)
                source_name = sp[0].strip() if sp else "Unknown"

                result[current_section].append({
                    "title": title,
                    "url": url,
                    "source": source_name,
                    "raw": source_part,
                })
                i += 2  # skip both lines
                continue

        i += 1

    return result




def _esc(text: str) -> str:
    """HTML-escape a string for use inside a quoted attribute value."""
    return (text.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
              .replace("'", "&#39;"))


def _esc_text(text: str) -> str:
    """Apply house punctuation and escape HTML/XML text-node content."""
    text = ddb_synth.strip_em_dashes(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _esc_archive_text(text: str) -> str:
    """Keep archive.html's historical quote encoding byte-stable."""
    return _esc_text(text).replace('"', "&quot;").replace("'", "&#x27;")


# ---------------------------------------------------------------------------
# Archive management
# ---------------------------------------------------------------------------

def read_archive_json(path: Path) -> dict:
    """Read archive.json from the git working tree (source of truth)."""
    if not path.exists():
        return {"site": DOMAIN, "editions": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_archive_json(path: Path, data: dict) -> None:
    """Write archive.json to the working tree."""
    data["editions"] = sorted(data["editions"], key=lambda e: (e["date"], 0 if e["edition"] == "morning" else 1), reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def update_archive(path: Path, edition_date: str, edition_type: str, lead_title: str,
                    human_date: str, pub_date: str) -> None:
    """Add or update the edition entry in archive.json (idempotent).

    edition_type is "morning" or "evening" — matches the real archive.json
    schema exactly (confirmed against the live file). The prior version
    compared edition_type against "pm" (a value it never actually holds,
    since callers already normalize to "morning"/"evening"), which silently
    produced a bogus "evening-morning" slug/filename on every PM bake.

    pub_date (RFC 2822, e.g. "Fri, 10 Jul 2026 05:15:00 -0400") is a new
    field the Mac's archive.json never wrote — additive, ignored by any
    consumer that doesn't know it. Backfills feed.xml's pubDate for entries
    baked here instead of falling back to a nominal slot time.
    """
    data = read_archive_json(path)
    file_name = f"editions/{edition_date}-{edition_type}.html"

    # Remove existing entry for same date+edition (idempotent)
    data["editions"] = [
        e for e in data["editions"]
        if not (e["date"] == edition_date and e["edition"] == edition_type)
    ]

    data["editions"].append({
        "date": edition_date,
        "edition": edition_type,
        "dateHuman": human_date,
        "file": file_name,
        "lead": lead_title[:100] + ("…" if len(lead_title) > 100 else ""),
        "pubDate": pub_date,
    })

    write_archive_json(path, data)


# ---------------------------------------------------------------------------
# archive.html / feed.xml regeneration (deterministic, from archive.json)
# ---------------------------------------------------------------------------

ARCHIVE_HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Past editions – David's Daily Bread</title>
<meta name="description" content="Every past edition of David's Daily Bread – a twice-daily briefing on technology, markets, and science.">
<link rel="canonical" href="https://davidsdailybread.com/archive.html">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="David's Daily Bread">
<meta property="og:title" content="Past editions – David's Daily Bread">
<meta property="og:description" content="Every past edition of David's Daily Bread, kept warm.">
<meta property="og:url" content="https://davidsdailybread.com/archive.html">
<meta property="og:image" content="https://davidsdailybread.com/og-card.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600;700&family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Newsreader:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
<style>
:root { --bg:#0e0e12; --panel:#16151a; --ink:#ece7db; --muted:#a7a08f; --faint:#6f6a60; --line:#28272e; --line-strong:#3a3941; --gold:#c8a24a; --gold-soft:#8f7538; --steel:#6f9fce; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: 'Inter', -apple-system, system-ui, sans-serif; -webkit-font-smoothing: antialiased; font-size: 15px; line-height: 1.6; background-image: radial-gradient(130% 70% at 50% 0%, rgba(200,162,74,0.06), transparent 62%); }
.paper { max-width: 860px; margin: 30px auto; background: var(--panel); padding: 44px 52px 34px; border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 16px 50px rgba(0,0,0,0.5); }
.masthead { text-align: center; }
.masthead-art-link { display: block; }
.masthead-art { display: block; width: 100%; max-width: 560px; height: auto; margin: 0 auto; }
.tagline { font-size: 10.5px; font-weight: 500; letter-spacing: 4px; text-transform: uppercase; color: var(--faint); margin-top: 8px; }
.dateline { position: relative; border-top: 2px solid var(--line-strong); border-bottom: 2px solid var(--line-strong); padding: 8px 0; margin-top: 16px; }
.dateline::before { content:""; position:absolute; left:0; right:0; top:5px; height:1px; background: linear-gradient(90deg, transparent, var(--gold-soft), transparent); }
.dateline-row { display: flex; justify-content: center; font-size: 11.5px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--muted); }
ol.editions { list-style: none; margin: 26px 0 0; padding: 0; }
ol.editions li { display: flex; align-items: baseline; gap: 16px; padding: 12px 4px; border-bottom: 1px solid var(--line); }
ol.editions .when { flex: none; min-width: 220px; font-family: 'Newsreader', Georgia, serif; font-size: 16px; }
ol.editions .when a { color: var(--ink); text-decoration: none; }
ol.editions .when a:hover { color: var(--gold); }
ol.editions .ed { flex: none; min-width: 70px; font-size: 10.5px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--steel); }
ol.editions .lede { font-size: 13px; color: var(--muted); }
.empty { margin-top: 26px; color: var(--muted); font-family: 'Newsreader', Georgia, serif; font-style: italic; text-align: center; }
.colophon { text-align: center; font-size: 10.5px; letter-spacing: 2px; text-transform: uppercase; color: var(--faint); border-top: 1px solid var(--line); margin-top: 26px; padding-top: 14px; }
.colophon a { color: var(--muted); text-decoration: none; border-bottom: 1px solid var(--line-strong); }
.colophon a:hover { color: var(--gold); border-bottom-color: var(--gold-soft); }
@media (max-width: 640px) {
.paper { padding: 30px 22px; margin: 12px; }
ol.editions li { flex-wrap: wrap; gap: 6px 12px; }
ol.editions .when { min-width: 0; }
ol.editions .lede { flex-basis: 100%; }
}
</style>
</head>
<body>
<div class="paper">
<header class="masthead">
<a class="masthead-art-link" href="/"><img class="masthead-art" src="/header-art.png" alt="David's Daily Bread" width="1124" height="418"></a>
<div class="tagline">Past editions &middot; kept warm</div>
<div class="dateline"><div class="dateline-row"><span>The bread box</span></div></div>
</header>
<ol class="editions" id="editions">
"""

ARCHIVE_HTML_TAIL = """</ol>
<div class="colophon"><a href="/">&larr; Latest edition</a></div>
</div>
</body>
</html>
"""


def render_archive_html(archive_data: dict) -> str:
    """Purely mechanical transform of archive.json — no model involved."""
    items = []
    for e in archive_data.get("editions", []):
        items.append(
            f'<li><span class="when"><a href="{_esc(e["file"])}">{_esc_archive_text(e["dateHuman"])}</a></span>'
            f'<span class="ed">{_esc_archive_text(e["edition"].capitalize())}</span>'
            f'<span class="lede">{_esc_archive_text(e["lead"])}</span></li>'
        )
    body = "\n".join(items) if items else '<div class="empty">No editions yet.</div>'
    return ARCHIVE_HTML_HEAD + body + "\n" + ARCHIVE_HTML_TAIL


def render_feed_xml(archive_data: dict) -> str:
    """RSS 2.0 feed, purely mechanical from archive.json. pubDate reuses each
    edition's own compiled timestamp if present (backfilled from the ET
    compile time at bake time), else falls back to a nominal slot time."""
    items = []
    for e in archive_data.get("editions", []):
        slot_word = "morning's" if e["edition"] == "morning" else "evening's"
        label = e["edition"].capitalize()
        pub_date = e.get("pubDate") or _nominal_pub_date(e["date"], e["edition"])
        items.append(f"""<item>
<title>{_esc_text(f'{label} edition – {e["dateHuman"]}: {e["lead"]}')}</title>
<link>{DOMAIN}/{e["file"]}</link>
<guid isPermaLink="true">{DOMAIN}/{e["file"]}</guid>
<pubDate>{pub_date}</pubDate>
<description>{_esc_text(f'Lead story: {e["lead"]}. Plus the {slot_word} top stories in technology, markets, and science.')}</description>
</item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
<title>David's Daily Bread</title>
<link>{DOMAIN}/</link>
<description>A twice-daily briefing on technology, markets, and science, baked fresh every morning and evening.</description>
<language>en-us</language>
<atom:link href="{DOMAIN}/feed.xml" rel="self" type="application/rss+xml"/>
<image>
<url>{OG_IMAGE}</url>
<title>David's Daily Bread</title>
<link>{DOMAIN}/</link>
</image>
""" + "\n".join(items) + "\n</channel>\n</rss>\n"


def _nominal_pub_date(date_str: str, edition_type: str) -> str:
    """Fallback RFC-2822 pubDate for archive entries written before pubDate
    tracking existed (e.g. by the Mac). Nominal 05:15/19:15 ET."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    hour = 5 if edition_type == "morning" else 19
    dt = dt.replace(hour=hour, minute=15)
    return dt.strftime("%a, %d %b %Y %H:%M:%S -0400")


def compute_timestamp_et(now_utc: datetime) -> str:
    """'Friday, July 10, 2026 at 5:15 AM ET' — matches the real colophon format."""
    from zoneinfo import ZoneInfo
    et = now_utc.astimezone(ZoneInfo("America/New_York"))
    return et.strftime("%A, %B %-d, %Y at %-I:%M %p ET")


def compute_readtime(*text_blocks: str, wpm: int = 200) -> str:
    """'≈ 4 min read' — word count over the real editorial prose, not markup."""
    words = sum(len(re.sub(r"<[^>]+>", " ", t).split()) for t in text_blocks if t)
    minutes = max(1, round(words / wpm))
    return f"&#8776; {minutes} min read"


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def fill_or_strip_section(html: str, start_marker: str, end_marker: str,
                           tokens: dict[str, str], keys: list[str]) -> str:
    """Fill a reader-content section's tokens, or remove the whole block
    (between the HTML comment markers) if the section had nothing to show."""
    if all(tokens.get(k, "") == "" for k in keys):
        pattern = re.compile(
            re.escape(start_marker) + r".*?" + re.escape(end_marker) + r"\n?",
            re.DOTALL,
        )
        return pattern.sub("", html)
    for k in keys:
        html = html.replace(k, tokens.get(k, ""))
    return html


def fill_reader_sections(html: str, csv_path: Path, dry_run: bool) -> str:
    tokens = ddb_satchel.fill_reader_sections(SITE, csv_path, write_state=not dry_run)
    html = fill_or_strip_section(html, "<!--READER_QA_START-->", "<!--READER_QA_END-->",
                                  tokens, ["RQ1_Q", "RQ1_A"])
    html = fill_or_strip_section(html, "<!--KING_COURT_START-->", "<!--KING_COURT_END-->",
                                  tokens, ["KQ1_Q", "KQ1_FROM", "KQ1_A"])
    html = fill_or_strip_section(html, "<!--CRUMB_BOARD_START-->", "<!--CRUMB_BOARD_END-->",
                                  tokens, ["PIN1_TEXT", "PIN1_SIG"])
    return html


# Static per-category chrome — confirmed against the real committed pages,
# not generated per-bake (same tagline/description every day by design).
CATEGORY_META = {
    "tech": {
        "slug": "tech", "title": "Technology", "hero": "Technology",
        "sub": "AI, chips, and the machines reshaping the world.",
        "desc": "The day's most important stories in technology and artificial intelligence.",
    },
    "markets": {
        "slug": "markets", "title": "Business &amp; Markets", "hero": "Business &amp; Markets",
        "sub": "Stocks, deals, and the forces moving the economy.",
        "desc": "The day's most important stories in business and markets.",
    },
    "science": {
        "slug": "science", "title": "Science", "hero": "Science",
        "sub": "Space, physics, and the frontiers of discovery.",
        "desc": "The day's most important stories in science and discovery.",
    },
}


def render_category(section: str, cards: list[dict]) -> str:
    """Render one category page (tech.html/markets.html/science.html) from
    up to 6 ranked+dek'd cards. cards[i] must have title/url/dek (bolded
    lead-in already applied to dek's HTML)."""
    template_path = TEMPLATES / "category.html"
    html = template_path.read_text(encoding="utf-8")
    meta = CATEGORY_META[section]

    html = html.replace("TITLE", meta["title"]).replace("DESC", _esc(meta["desc"]))
    html = html.replace("SLUG", meta["slug"])
    html = html.replace("HERO", meta["hero"]).replace("SUB", meta["sub"])

    for sec_key, token in (("tech", "__ACTIVE_TECH__"), ("markets", "__ACTIVE_MKT__"), ("science", "__ACTIVE_SCI__")):
        html = html.replace(token, ' class="active"' if sec_key == section else "")

    for i in range(1, 7):
        if i <= len(cards):
            c = cards[i - 1]
            html = html.replace(f"CAT_{i}_URL", _esc(c["url"]))
            html = html.replace(f"CAT_{i}_HEADLINE", _esc_text(c["title"]))
            html = html.replace(f"CAT_{i}_DEK", c["dek"])
        else:
            # Fewer than 6 stories today — drop the empty card slot's whole <div class="stack">…</div>.
            pattern = re.compile(
                r'<div class="stack"><article class="card story-card"><a class="card-link" href="CAT_' + str(i) +
                r'_URL">.*?</div></div>',
                re.DOTALL,
            )
            html = pattern.sub("", html)

    return html


SECTION_GLANCE_LABEL = {"tech": "technology", "markets": "business and markets", "science": "science"}
CARD_TOKEN_PREFIX = {"tech": "T", "markets": "M", "science": "S"}


def build_ranked_cards(items: list[dict], count: int) -> list[dict]:
    """Fetch + synthesize a dek for the top `count` items (already
    rank-ordered by the aggregator). Returns [{title, url, source, dek}]."""
    cards = []
    for item in items[:count]:
        article_text = ddb_synth.fetch_article_text(item["url"])
        dek = ddb_synth.synthesize_dek(item["title"], item["url"], item["source"], article_text)
        cards.append({"title": item["title"], "url": item["url"], "source": item["source"], "dek": dek})
    return cards


def render_home(date_str: str, slot: str, data: dict[str, list[dict]],
                 csv_path: Path, dry_run: bool = False) -> tuple[str, dict]:
    """Read home.html template and fill in edition content.

    Returns (html, meta) — meta carries {"lead_title": ..., "ranked_cards":
    {section: [...]}} so main() can reuse the same synthesized cards for
    the category pages instead of re-fetching/re-synthesizing, and record
    the real lead title in archive.json.
    """
    template_path = TEMPLATES / "home.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    html = template_path.read_text(encoding="utf-8")

    label = slot_label(slot)
    hd = human_date(date_str)

    html = html.replace("EDITION, DATELINE_DATE", f"{label} edition, {hd}")
    html = html.replace("DATELINE_DATE", hd)
    html = html.replace("EDITION", f"{label} edition")

    # Rank + synthesize top 6 cards per section once; home reuses the top 2,
    # category pages (built by main()) reuse all 6 — no duplicate model calls.
    ranked_cards = {s: build_ranked_cards(data.get(s, []), 6) for s in SECTIONS}

    # Front-page lead: judged across a WIDE pool per section (titles only,
    # no fetch) so the pick isn't biased toward whatever's simply first —
    # see synthesize_lead's docstring for why a narrow pool failed in testing.
    candidates = [
        {"section": s, "title": item["title"], "url": item["url"], "source": item["source"]}
        for s in SECTIONS for item in data.get(s, [])[:8]
    ]
    if candidates:
        lead = ddb_synth.synthesize_lead(candidates)
    else:
        lead = {"section": "tech", "title": "No edition available", "url": "#",
                "badge": "Update", "standfirst": "", "body": ""}

    for field in ("title", "badge", "standfirst", "body"):
        lead[field] = ddb_synth.strip_em_dashes(lead[field])

    html = html.replace("LEAD_URL", _esc(lead["url"]))
    html = html.replace("LEAD_BADGE", _esc_text(lead["badge"]))
    html = html.replace("LEAD_HEADLINE", _esc_text(lead["title"]))
    html = html.replace("LEAD_STANDFIRST", _esc_text(lead["standfirst"]))
    html = html.replace("LEAD_BODY", _esc_text(lead["body"]))

    # Home cards: top 2 per section (matches the real template's 2-card sections).
    for s in SECTIONS:
        p = CARD_TOKEN_PREFIX[s]
        for i in (1, 2):
            if i <= len(ranked_cards[s]):
                c = ranked_cards[s][i - 1]
                html = html.replace(f"CARD_{p}{i}_URL", _esc(c["url"]))
                html = html.replace(f"CARD_{p}{i}_HEADLINE", _esc_text(c["title"]))
                html = html.replace(f"CARD_{p}{i}_DEK", c["dek"])
            else:
                pattern = re.compile(
                    r'<div class="stack"><article class="card story-card"><a class="card-link" href="CARD_' + p + str(i) +
                    r'_URL">.*?</div></div>',
                    re.DOTALL,
                )
                html = pattern.sub("", html)

    # "At a glance": one synthesized roundup sentence + expanded top-3 links, per section.
    for s in SECTIONS:
        p = CARD_TOKEN_PREFIX[s]
        top3 = ranked_cards[s][:3]
        glance_text = ddb_synth.synthesize_glance(SECTION_GLANCE_LABEL[s], [c["title"] for c in top3]) if top3 else ""
        html = html.replace(f"GLANCE_{s.upper()}", _esc_text(glance_text))
        for i in (1, 2, 3):
            if i <= len(top3):
                c = top3[i - 1]
                html = html.replace(f"EXP_{p}{i}_URL", _esc(c["url"]))
                html = html.replace(f"EXP_{p}{i}_TEXT", _esc_text(c["title"]))
            else:
                pattern = re.compile(r'<li><span class="rank">' + str(i) + r'</span><span><a href="EXP_' + p + str(i) +
                                      r'_URL">EXP_' + p + str(i) + r'_TEXT</a></span></li>', re.DOTALL)
                html = pattern.sub("", html)

    readtime_text = compute_readtime(
        lead["standfirst"], lead["body"],
        *[c["dek"] for s in SECTIONS for c in ranked_cards[s]],
    )
    html = html.replace("READTIME", readtime_text)
    html = html.replace("TIMESTAMP", compute_timestamp_et(datetime.now(timezone.utc)))

    html = fill_reader_sections(html, csv_path, dry_run)

    meta = {"lead_title": lead["title"], "ranked_cards": ranked_cards}
    return html, meta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="DDB bake: draft -> published HTML")
    parser.add_argument("--slot", required=True, choices=["am", "pm"])
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--outdir", default=None, help="Output directory (testing)")
    parser.add_argument("--dry-run", action="store_true", help="Render to temp dir, no writes")
    args = parser.parse_args()

    draft_path = DRAFTS / f"{args.date}-{args.slot}.md"
    if not draft_path.exists():
        print(f"ERROR: draft not found: {draft_path}", file=sys.stderr)
        sys.exit(1)

    # Parse draft
    data = parse_draft(draft_path)
    total_items = sum(len(v) for v in data.values())

    if total_items == 0:
        print(f"WARNING: draft has no parseable items: {draft_path}", file=sys.stderr)

    edition_type = "morning" if args.slot == "am" else "evening"
    date_human = human_date(args.date)
    now_utc = datetime.now(timezone.utc)

    # Render (also synthesizes deks/glance/lead — real model calls, not free)
    html, meta = render_home(args.date, args.slot, data, csv_path=CSV_PATH, dry_run=args.dry_run)

    output_filename = f"{args.date}-{edition_type}.html"

    if args.dry_run:
        import tempfile
        tmpdir = Path(tempfile.mkdtemp())
        outpath = tmpdir / output_filename
        outpath.write_text(html, encoding="utf-8")
        print(f"Dry run: rendered to {outpath}")
        print(f"  Draft: {draft_path} ({total_items} items)")
        for s in SECTIONS:
            print(f"  {s}: {len(data[s])} items")
        print(f"  Lead: {meta['lead_title']}")
        return

    # Write files (site dir must be the git repo root)
    EDITIONS.mkdir(exist_ok=True)
    outpath = EDITIONS / output_filename
    outpath.write_text(html, encoding="utf-8")
    print(f"wrote {outpath} · {total_items} items")

    # Write edition as the latest (index.html)
    index_path = SITE / "index.html"
    index_path.write_text(html, encoding="utf-8")
    print(f"updated {index_path}")

    # Category pages reuse the SAME synthesized cards render_home already
    # built — no duplicate fetches or model calls.
    for s in SECTIONS:
        cat_html = render_category(s, meta["ranked_cards"][s])
        (SITE / f"{s}.html").write_text(cat_html, encoding="utf-8")
        print(f"updated {SITE / f'{s}.html'}")

    # Update archive.json (from working tree, never CDN), then regenerate
    # archive.html and feed.xml from it — both were previously never touched.
    archive_path = SITE / "archive.json"
    from zoneinfo import ZoneInfo
    pub_date = now_utc.astimezone(ZoneInfo("America/New_York")).strftime("%a, %d %b %Y %H:%M:%S %z")
    if meta["lead_title"] and meta["lead_title"] != "No edition available":
        update_archive(archive_path, args.date, edition_type, meta["lead_title"], date_human, pub_date)
        print(f"updated {archive_path}")

    archive_data = read_archive_json(archive_path)
    (SITE / "archive.html").write_text(render_archive_html(archive_data), encoding="utf-8")
    print(f"updated {SITE / 'archive.html'}")
    (SITE / "feed.xml").write_text(render_feed_xml(archive_data), encoding="utf-8")
    print(f"updated {SITE / 'feed.xml'}")

    print(f"Done. Edition: {args.slot} · {args.date} · {total_items} items")


if __name__ == "__main__":
    main()