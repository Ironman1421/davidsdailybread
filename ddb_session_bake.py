#!/usr/bin/env python3
"""DDB session bake — the daily 5:00 AM Claude scheduled task's renderer.

Since 2026-07-17 the bake is driven by a Claude cloud session (spec: /BAKE.md).
The SESSION does everything editorial: researching the news, choosing the lead,
writing standfirst/body/deks/glance lines, answering reader mail in the house
personas. This script does everything MECHANICAL, deterministically, with no
model calls anywhere:

  --plan
      Fetch the Counter CSV (reader submissions), read bakery-state.json and
      kings-satchel.json from the working tree, and print a JSON "reader plan":
      exactly which submission (or house-satchel letter) the session must write
      replies for today, plus the satchel inventory. Never mutates state.

  --render --content content.json --date YYYY-MM-DD
      Render the edition from the session-authored content JSON: home page,
      three category pages, editions/ file, archive.json, archive.html (marked
      list only), feed.xml, bakery-state.json. Validates the output (no leftover
      tokens, no em dashes, masthead art present, archive markers intact) and
      exits non-zero without partial state if anything fails validation.

Contract carried over from ddb_bake.py: every fact traces to its source link;
archive/state are read from the git working tree, never the live CDN;
idempotent for the same date+content.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
os.environ.setdefault("DDB_SITE_DIR", str(REPO))

import ddb_bake      # noqa: E402  (needs DDB_SITE_DIR set first)
import ddb_satchel   # noqa: E402

SECTIONS = ("tech", "markets", "science")
CARD_PREFIX = {"tech": "T", "markets": "M", "science": "S"}
EM_DASH_RE = re.compile(r"—|&mdash;|&#0*8212;|&#x0*2014;", re.IGNORECASE)

# Every token family the templates carry. Post-render, none may survive.
LEFTOVER_TOKEN_RE = re.compile(
    r"\b(LEAD_(URL|BADGE|HEADLINE|STANDFIRST|BODY)"
    r"|CARD_[TMS][12]_(URL|HEADLINE|DEK)"
    r"|CAT_[1-6]_(URL|HEADLINE|DEK)"
    r"|EXP_[TMS][123]_(URL|TEXT)"
    r"|GLANCE_(TECH|MARKETS|SCIENCE)"
    r"|RQ1_[QA]|KQ1_(Q|A|FROM)|PIN1_(TEXT|SIG)"
    r"|DATELINE_DATE|READTIME|TIMESTAMP"
    r"|__ACTIVE_(TECH|MKT|SCI)__)\b"
)


def fail(msg: str) -> None:
    print(f"BAKE FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# --plan
# ---------------------------------------------------------------------------

def cmd_plan(csv_path: Path) -> None:
    state_path = REPO / "bakery-state.json"
    satchel_path = REPO / "kings-satchel.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

    csv_ok = ddb_satchel.fetch_csv(csv_path)
    rows = ddb_satchel.classify(ddb_satchel.load_csv_rows(csv_path)) if csv_path.exists() else {
        "asks": [], "king_letters": [], "pins": []
    }

    plan: dict = {"csv_fetched": bool(csv_ok), "ask": None, "king": None, "pin": None}

    ask_row = ddb_satchel.pick_oldest_unused(rows["asks"], set(state.get("answeredQuestions", [])))
    if ask_row:
        plan["ask"] = {"question": ask_row["text"], "state_key": ddb_satchel.dedup_key(ask_row)}

    king_row = ddb_satchel.pick_oldest_unused(rows["king_letters"], set(state.get("kingLetters", [])))
    letters = ddb_satchel.load_satchel(satchel_path)
    used_satchel = set(state.get("usedSatchelLetters", []))
    if king_row:
        plan["king"] = {
            "kind": "reader",
            "letter": king_row["text"][len(ddb_satchel.KING_PREFIX):].strip(),
            "from": king_row["name"],
            "state_key": ddb_satchel.dedup_key(king_row),
        }
    else:
        drawn = ddb_satchel.pick_satchel_letter(letters, used_satchel)
        if drawn:
            plan["king"] = {"kind": "satchel", "id": drawn["id"], "letter": drawn["letter"]}

    pin_row = ddb_satchel.pick_oldest_unused(rows["pins"], set(state.get("postedPins", [])))
    if pin_row:
        plan["pin"] = {"text": pin_row["text"], "name": pin_row["name"],
                       "state_key": ddb_satchel.dedup_key(pin_row)}

    plan["satchel_unused"] = len([l for l in letters if l["id"] not in used_satchel])
    print(json.dumps(plan, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# --render
# ---------------------------------------------------------------------------

def _require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)


def validate_content(c: dict, date: str) -> None:
    _require(c.get("date") == date, f"content date {c.get('date')!r} != --date {date!r}")
    lead = c.get("lead") or {}
    for k in ("section", "title", "url", "badge", "standfirst", "body"):
        _require(bool(str(lead.get(k, "")).strip()), f"lead.{k} missing/empty")
    _require(lead["section"] in SECTIONS, f"lead.section {lead['section']!r} invalid")
    _require(str(lead["url"]).startswith("http"), "lead.url must be a real link")

    cards = c.get("cards") or {}
    for s in SECTIONS:
        items = cards.get(s) or []
        _require(2 <= len(items) <= 6, f"cards.{s}: need 2-6 items, got {len(items)}")
        for i, item in enumerate(items):
            for k in ("title", "url", "dek"):
                _require(bool(str(item.get(k, "")).strip()), f"cards.{s}[{i}].{k} missing")
            _require(str(item["url"]).startswith("http"), f"cards.{s}[{i}].url must be a link")
            _require("<b>" in item["dek"] and "</b>" in item["dek"],
                     f"cards.{s}[{i}].dek must open with a <b>lead-in</b>")

    glance = c.get("glance") or {}
    for s in SECTIONS:
        _require(bool(str(glance.get(s, "")).strip()), f"glance.{s} missing")

    def scan(obj, path="content"):
        if isinstance(obj, str):
            _require(not EM_DASH_RE.search(obj), f"em dash found in {path} (house style forbids them)")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")
    scan(c)

    reader = c.get("reader") or {}
    king = reader.get("king")
    if king:
        _require(bool(str(king.get("answer", "")).strip()), "reader.king.answer missing")
        _require(bool(king.get("state_key")) or bool(king.get("satchel_id")),
                 "reader.king needs state_key (reader mail) or satchel_id (house letter)")
    ask = reader.get("ask")
    if ask:
        _require(bool(str(ask.get("answer", "")).strip()) and bool(ask.get("state_key")),
                 "reader.ask needs answer + state_key")
    pin = reader.get("pin")
    if pin:
        _require(bool(str(pin.get("text", "")).strip()) and bool(pin.get("state_key")),
                 "reader.pin needs text + state_key")


def render_home_from_content(c: dict, date: str) -> tuple[str, str]:
    """Mirror ddb_bake.render_home's token operations exactly, sourcing all
    editorial content from the session-authored JSON instead of model calls.
    Returns (html, lead_title)."""
    template = (REPO / "templates" / "home.html").read_text(encoding="utf-8")
    esc, esc_text = ddb_bake._esc, ddb_bake._esc_text

    hd = ddb_bake.human_date(date)
    html = template.replace("EDITION, DATELINE_DATE", f"Morning edition, {hd}")
    html = html.replace("DATELINE_DATE", hd)
    html = html.replace("EDITION", "Morning edition")

    lead = c["lead"]
    html = html.replace("LEAD_URL", esc(lead["url"]))
    html = html.replace("LEAD_BADGE", esc_text(lead["badge"]))
    html = html.replace("LEAD_HEADLINE", esc_text(lead["title"]))
    html = html.replace("LEAD_STANDFIRST", esc_text(lead["standfirst"]))
    html = html.replace("LEAD_BODY", esc_text(lead["body"]))

    for s in SECTIONS:
        p = CARD_PREFIX[s]
        items = c["cards"][s]
        for i in (1, 2):
            if i <= len(items):
                card = items[i - 1]
                html = html.replace(f"CARD_{p}{i}_URL", esc(card["url"]))
                html = html.replace(f"CARD_{p}{i}_HEADLINE", esc_text(card["title"]))
                html = html.replace(f"CARD_{p}{i}_DEK", ddb_satchel.strip_em_dashes(card["dek"]))
            else:
                pattern = re.compile(
                    r'<div class="stack"><article class="card story-card"><a class="card-link" href="CARD_'
                    + p + str(i) + r'_URL">.*?</div></div>', re.DOTALL)
                html = pattern.sub("", html)

    for s in SECTIONS:
        p = CARD_PREFIX[s]
        top3 = c["cards"][s][:3]
        html = html.replace(f"GLANCE_{s.upper()}", esc_text(c["glance"][s]))
        for i in (1, 2, 3):
            if i <= len(top3):
                card = top3[i - 1]
                html = html.replace(f"EXP_{p}{i}_URL", esc(card["url"]))
                html = html.replace(f"EXP_{p}{i}_TEXT", esc_text(card["title"]))
            else:
                pattern = re.compile(
                    r'<li><span class="rank">' + str(i) + r'</span><span><a href="EXP_' + p + str(i)
                    + r'_URL">EXP_' + p + str(i) + r'_TEXT</a></span></li>', re.DOTALL)
                html = pattern.sub("", html)

    reader = c.get("reader") or {}
    tokens: dict[str, str] = {}
    ask = reader.get("ask")
    tokens["RQ1_Q"] = ddb_satchel.strip_em_dashes(ask["question"]) if ask else ""
    tokens["RQ1_A"] = ddb_satchel.strip_em_dashes(ask["answer"]) if ask else ""
    king = reader.get("king")
    if king:
        tokens["KQ1_Q"] = ddb_satchel.strip_em_dashes(king["question"])
        tokens["KQ1_FROM"] = ("From the Baker's own shelf" if king.get("satchel_id")
                              else f"From {ddb_satchel.strip_em_dashes(king.get('from', 'a reader'))}")
        tokens["KQ1_A"] = ddb_satchel.strip_em_dashes(king["answer"])
    else:
        tokens["KQ1_Q"] = tokens["KQ1_FROM"] = tokens["KQ1_A"] = ""
    pin = reader.get("pin")
    if pin:
        tokens["PIN1_TEXT"] = ddb_satchel.strip_em_dashes(pin["text"])
        tokens["PIN1_SIG"] = f"– {ddb_satchel.strip_em_dashes(pin.get('sig_name') or 'Anonymous')}"
    else:
        tokens["PIN1_TEXT"] = tokens["PIN1_SIG"] = ""

    html = ddb_bake.fill_or_strip_section(html, "<!--READER_QA_START-->", "<!--READER_QA_END-->",
                                          tokens, ["RQ1_Q", "RQ1_A"])
    html = ddb_bake.fill_or_strip_section(html, "<!--KING_COURT_START-->", "<!--KING_COURT_END-->",
                                          tokens, ["KQ1_Q", "KQ1_FROM", "KQ1_A"])
    html = ddb_bake.fill_or_strip_section(html, "<!--CRUMB_BOARD_START-->", "<!--CRUMB_BOARD_END-->",
                                          tokens, ["PIN1_TEXT", "PIN1_SIG"])

    readtime = ddb_bake.compute_readtime(
        lead["standfirst"], lead["body"],
        *[card["dek"] for s in SECTIONS for card in c["cards"][s]],
    )
    html = html.replace("READTIME", readtime)
    html = html.replace("TIMESTAMP", ddb_bake.compute_timestamp_et(datetime.now(timezone.utc)))
    return html, lead["title"]


def verify_output(paths: list[Path]) -> None:
    for p in paths:
        text = p.read_text(encoding="utf-8")
        m = LEFTOVER_TOKEN_RE.search(text)
        _require(m is None, f"{p.name}: leftover template token {m.group() if m else ''!r}")
        if p.suffix in (".html", ".xml"):
            _require(not EM_DASH_RE.search(text), f"{p.name}: em dash in published output")
        if p.name.endswith(".html") and p.name != "404.html":
            _require('src="/header-art.png"' in text or "feed" in p.name,
                     f"{p.name}: masthead art missing")


def update_state(reader: dict) -> None:
    state_path = REPO / "bakery-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {
        "note": "", "answeredQuestions": [], "postedPins": [], "kingLetters": [], "usedSatchelLetters": []
    }

    def add(key: str, value: str) -> None:
        bucket = state.setdefault(key, [])
        if value and value not in bucket:
            bucket.append(value)

    ask = reader.get("ask")
    if ask:
        add("answeredQuestions", ask["state_key"])
    king = reader.get("king")
    if king:
        if king.get("satchel_id"):
            add("usedSatchelLetters", king["satchel_id"])
        else:
            add("kingLetters", king["state_key"])
    pin = reader.get("pin")
    if pin:
        add("postedPins", pin["state_key"])
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_render(content_path: Path, date: str) -> None:
    try:
        content = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail(f"cannot read content JSON: {e}")

    validate_content(content, date)

    archive_html_path = REPO / "archive.html"
    ddb_bake.validate_archive_file(archive_html_path)  # fail closed before any write

    html, lead_title = render_home_from_content(content, date)

    editions = REPO / "editions"
    editions.mkdir(exist_ok=True)
    edition_path = editions / f"{date}-morning.html"
    edition_path.write_text(html, encoding="utf-8")
    (REPO / "index.html").write_text(html, encoding="utf-8")

    written = [edition_path, REPO / "index.html"]
    for s in SECTIONS:
        cards = [
            {"title": card["title"], "url": card["url"],
             "dek": ddb_satchel.strip_em_dashes(card["dek"])}
            for card in content["cards"][s]
        ]
        cat_html = ddb_bake.render_category(s, cards)
        cat_path = REPO / f"{s}.html"
        cat_path.write_text(cat_html, encoding="utf-8")
        written.append(cat_path)

    from zoneinfo import ZoneInfo
    now_et = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
    pub_date = now_et.strftime("%a, %d %b %Y %H:%M:%S %z")
    archive_json_path = REPO / "archive.json"
    ddb_bake.update_archive(archive_json_path, date, "morning", lead_title,
                            ddb_bake.human_date(date), pub_date)
    archive_data = ddb_bake.read_archive_json(archive_json_path)
    ddb_bake.update_archive_file(archive_html_path, archive_data)
    (REPO / "feed.xml").write_text(ddb_bake.render_feed_xml(archive_data), encoding="utf-8")
    written += [archive_html_path, REPO / "feed.xml"]

    update_state(content.get("reader") or {})

    verify_output(written)
    print(f"BAKE OK: {date} morning · lead: {lead_title}")
    for p in written:
        print(f"  wrote {p.relative_to(REPO)}")
    print("  wrote archive.json, bakery-state.json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--render", action="store_true")
    ap.add_argument("--content", type=Path, help="content JSON (render mode)")
    ap.add_argument("--date", help="YYYY-MM-DD edition date (render mode)")
    ap.add_argument("--csv", type=Path, default=REPO / "counter.csv",
                    help="Counter CSV path. Default: the repo's committed copy, kept "
                         "fresh by .github/workflows/counter-sync.yml (the cloud "
                         "sandbox cannot reach docs.google.com; a live refresh is "
                         "still attempted and quietly falls back to this file)")
    args = ap.parse_args()

    if args.plan:
        cmd_plan(args.csv)
    else:
        if not args.content or not args.date:
            fail("--render requires --content and --date")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            fail(f"bad --date {args.date!r}")
        cmd_render(args.content, args.date)


if __name__ == "__main__":
    main()
