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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DDB = Path.home() / "ddb"
# Site repo can be either ~/ddb/site-mirror (if cloned) or ~/davidsdailybread
_candidate_sites = [
    Path.home() / "davidsdailybread",
    Path.home() / "ddb" / "site-mirror",
]
SITE = None
for _s in _candidate_sites:
    if (_s / "templates" / "home.html").exists():
        SITE = _s
        break
if SITE is None:
    raise RuntimeError("No site repo found. Clone to ~/davidsdailybread or ~/ddb/site-mirror")
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
SECTION_LABELS = {s: s.capitalize() for s in SECTIONS}

# Maximum cards per section in the glance and story-grid
GLANCE_COUNT = 3        # shown above "see more"
GRID_COUNT = 10          # shown in the two-column grid per section


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
                title = m.group(1).strip()
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


def pick_lead(items: list[dict]) -> dict:
    """Pick the lead story — first item in the Tech section (highest priority)."""
    return items[0] if items else {"title": "No story available", "url": "#", "source": "", "raw": ""}


def pick_cards(items: list[dict], count: int) -> list[dict]:
    """Pick up to `count` cards from a section, skipping the lead."""
    return items[1:count + 1]


def truncate_url(url: str, max_len: int = 60) -> str:
    """Truncate a URL for display."""
    if len(url) <= max_len:
        return url
    # Try to cut at a path segment boundary
    mid = url[:max_len - 3]
    last_slash = mid.rfind("/")
    if last_slash > 20:
        return url[:last_slash + 1] + "…"
    return url[:max_len - 3] + "…"


# ---------------------------------------------------------------------------
# HTML Generation
# ---------------------------------------------------------------------------

def generate_lead_html(lead: dict) -> str:
    """Generate the lead card HTML block."""
    return f"""
      <div class="card lead-card">
        <span class="badge">{lead['source']}</span>
        <h1>{_esc(lead['title'])}</h1>
        <p class="standfirst">A twice-daily briefing on technology, markets, and science.</p>
        <p class="lead-body"><a href="{_esc(lead['url'])}" target="_blank" rel="noopener">{_esc(lead['title'])}</a></p>
      </div>
"""


def generate_story_card(card: dict, index: int, section_label: str) -> str:
    """Generate a story card HTML block."""
    url_trunc = truncate_url(card['url'], 60)
    return f"""
      <div class="card story-card">
        <span class="num">{index}</span>
        <h3><a class="card-link" href="{_esc(card['url'])}" target="_blank" rel="noopener">{_esc(card['title'])}</a></h3>
        <p>{_esc(card['source'])} · {_esc(card['raw'])}</p>
      </div>
"""


def generate_section_html(title: str, slug: str, cards: list[dict]) -> str:
    """Generate a section (Tech/Markets/Science) with cards."""
    card_blocks = "\n".join(
        generate_story_card(c, i + 1, title) for i, c in enumerate(cards)
    )
    return f"""
    <div class="section">
      <a href="{_esc(slug)}.html" class="col-head">
        {title} <span class="arrow">\u2192</span>
      </a>
      <div class="card-grid">{card_blocks}</div>
    </div>
"""


def generate_glance_html(data: dict[str, list[dict]]) -> str:
    """Generate the glance section (top 3 per section)."""
    groups = []
    for s in SECTIONS:
        cards = data.get(s, [])[:GLANCE_COUNT]
        if not cards:
            continue
        all_cards = data[s]
        extra_cards = all_cards[GLANCE_COUNT:]
        items = "\n".join(
            f'<li><span class="tag">{SECTION_LABELS.get(s, "")}</span> <a href="{_esc(c["url"])}" target="_blank" rel="noopener">{_esc(c["title"])}</a></li>'
            for c in cards
        )
        extra_items = None
        if extra_cards:
            extra_items = "\n".join(
                f'<li><span class="rank">{GLANCE_COUNT + i + 1}</span> <a href="{_esc(c["url"])}" target="_blank" rel="noopener">{_esc(c["title"])}</a></li>'
                for i, c in enumerate(extra_cards)
            )

        group = f"""
      <div class="glance-grp">
        <div class="glance-grp-head">{SECTION_LABELS.get(s, s.title())}</div>
        <ul>{items}</ul>"""
        if extra_items:
            group += f"""
        <div class="glance-more">
          <div class="glance-more-inner">
            <ul>{extra_items}</ul>
          </div>
        </div>"""
        group += "\n      </div>"
        groups.append(group)

    return "\n".join(groups)


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (text.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
              .replace("'", "&#39;"))


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


def update_archive(path: Path, edition_date: str, edition_type: str, lead: dict, human_date: str) -> None:
    """Add or update the edition entry in archive.json (idempotent)."""
    data = read_archive_json(path)
    slug = f"{edition_type}-evening" if edition_type == "pm" else f"{edition_type}-morning"
    edition_key = f"{edition_date}-{slug}"
    file_name = f"editions/{edition_date}-{slug}.html"

    # Remove existing entry for same date+edition (idempotent)
    data["editions"] = [
        e for e in data["editions"]
        if not (e["date"] == edition_date and e["edition"] == slug)
    ]

    data["editions"].append({
        "date": edition_date,
        "edition": slug,
        "dateHuman": human_date,
        "file": file_name,
        "lead": lead["title"][:100] + ("…" if len(lead["title"]) > 100 else ""),
    })

    write_archive_json(path, data)


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


def render_home(date_str: str, slot: str, data: dict[str, list[dict]],
                 csv_path: Path, dry_run: bool = False) -> str:
    """Read home.html template and fill in edition content."""
    template_path = TEMPLATES / "home.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    html = template_path.read_text(encoding="utf-8")

    edition_type = "morning" if slot == "am" else "evening"
    label = slot_label(slot)
    hd = human_date(date_str)

    # Title
    html = html.replace(
        "<title>David's Daily Bread – EDITION, DATELINE_DATE</title>",
        f"<title>David's Daily Bread – {label} edition, {hd}</title>",
    )
    html = html.replace(
        "<meta property=\"og:title\" content=\"David's Daily Bread – EDITION, DATELINE_DATE\">",
        f"<meta property=\"og:title\" content=\"David's Daily Bread – {label} edition, {hd}\">",
    )
    html = html.replace(
        "<meta property=\"og:description\" content=\"A twice-daily briefing on technology, markets, and science, baked fresh every morning and evening.\">",
        f"<meta property=\"og:description\" content=\"David's Daily Bread – a twice-daily briefing on technology, markets, and science, baked fresh every morning and evening.\">",
    )

    # Date in dateline
    html = html.replace("DATELINE_DATE", hd)

    # Edition badge
    html = html.replace("{{EDITION}}", label)
    html = html.replace("{{DATELINE_DATE}}", hd)

    # Build the lead
    all_items: list[dict] = []
    for s in SECTIONS:
        all_items.extend(data.get(s, []))

    lead = pick_lead(all_items) if all_items else None

    if lead:
        # Replace lead card placeholders
        html = html.replace("{{LEAD_HEADLINE}}", _esc(lead["title"]))
        html = html.replace("{{LEAD_BADGE}}", _esc(lead["source"]))
        html = html.replace("{{LEAD_STANDFIRST}}", f"<a href=\"{_esc(lead['url'])}\" target=\"_blank\" rel=\"noopener\">{_esc(lead['title'])}</a>")
        html = html.replace("{{LEAD_BODY}}", f"<a href=\"{_esc(lead['url'])}\" target=\"_blank\" rel=\"noopener\">{_esc(lead['title'])}</a>")
        html = html.replace("{{LEAD_URL}}", _esc(lead["url"]))
    else:
        html = html.replace("{{LEAD_HEADLINE}}", "No edition available")
        html = html.replace("{{LEAD_BADGE}}", "—")
        html = html.replace("{{LEAD_STANDFIRST}}", "")
        html = html.replace("{{LEAD_BODY}}", "")
        html = html.replace("{{LEAD_URL}}", "#")

    # Build section cards
    # Cards: first GLANCE_COUNT per section go in glance, rest in grid
    tech_cards = data.get("tech", [])
    markets_cards = data.get("markets", [])
    science_cards = data.get("science", [])

    # Grid: up to GRID_COUNT per section (minus lead if it's from tech)
    tech_grid = tech_cards[1:GRID_COUNT + 1] if tech_cards else []
    markets_grid = markets_cards[:GRID_COUNT]
    science_grid = science_cards[:GRID_COUNT]

    html = html.replace("{{CARD_T1}}", generate_story_card(tech_grid[0], 1, "Tech") if len(tech_grid) > 0 else '')
    html = html.replace("{{CARD_T2}}", generate_story_card(tech_grid[1], 2, "Tech") if len(tech_grid) > 1 else '')
    html = html.replace("{{CARD_T3}}", generate_story_card(tech_grid[2], 3, "Tech") if len(tech_grid) > 2 else '')
    html = html.replace("{{CARD_M1}}", generate_story_card(markets_grid[0], 1, "Markets") if len(markets_grid) > 0 else '')
    html = html.replace("{{CARD_M2}}", generate_story_card(markets_grid[1], 2, "Markets") if len(markets_grid) > 1 else '')
    html = html.replace("{{CARD_M3}}", generate_story_card(markets_grid[2], 3, "Markets") if len(markets_grid) > 2 else '')
    html = html.replace("{{CARD_S1}}", generate_story_card(science_grid[0], 1, "Science") if len(science_grid) > 0 else '')
    html = html.replace("{{CARD_S2}}", generate_story_card(science_grid[1], 2, "Science") if len(science_grid) > 1 else '')
    html = html.replace("{{CARD_S3}}", generate_story_card(science_grid[2], 3, "Science") if len(science_grid) > 2 else '')

    # Glance section: top items from each section
    html = html.replace("{{GLANCE}}", generate_glance_html(data))

    # Sections with all cards in grid view
    tech_section = generate_section_html("Technology", "tech", tech_cards) if tech_cards else ""
    markets_section = generate_section_html("Markets", "markets", markets_cards) if markets_cards else ""
    science_section = generate_section_html("Science", "science", science_cards) if science_cards else ""

    html = html.replace("{{TECH_SECTION}}", tech_section)
    html = html.replace("{{MARKETS_SECTION}}", markets_section)
    html = html.replace("{{SCIENCE_SECTION}}", science_section)

    # Footer: edition info
    html = html.replace("{{FOOTER_EDITION}}", f"{label} edition, {hd}")
    html = html.replace("{{FOOTER_TOTAL}}", str(sum(len(v) for v in data.values())))

    html = fill_reader_sections(html, csv_path, dry_run)

    return html


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

    # Render
    html = render_home(args.date, args.slot, data, csv_path=CSV_PATH, dry_run=args.dry_run)

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

    # Update archive.json (from working tree, never CDN)
    archive_path = SITE / "archive.json"
    lead = pick_lead([d for items in data.values() for d in items]) if any(data.values()) else None
    if lead:
        update_archive(archive_path, args.date, edition_type, lead, date_human)
        print(f"updated {archive_path}")

    print(f"Done. Edition: {args.slot} · {args.date} · {total_items} items")


if __name__ == "__main__":
    main()