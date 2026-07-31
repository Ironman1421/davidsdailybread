#!/usr/bin/env python3
"""DDB session bake — the daily 5:00 AM Claude scheduled task's renderer.

Since 2026-07-17 the bake is driven by a Claude cloud session (spec: /BAKE.md).
The SESSION does everything editorial: researching the news, choosing the lead,
writing standfirst/body/deks/glance lines, answering reader mail in the house
personas. This script does everything MECHANICAL, deterministically, with no
model calls anywhere:

  --plan
      Read the committed Counter CSV snapshot (reader submissions), bakery-state.json and
      kings-satchel.json from the working tree, and print a JSON "reader plan":
      exactly which submission (or house-satchel letter) the session must write
      replies for today, plus the satchel inventory. Never mutates state.

  --render --content content.json --date YYYY-MM-DD [--slot morning|evening]
      Render the edition from the session-authored content JSON: home page,
      editions/ file, archive.json, archive.html (marked list only), feed.xml,
      plus (morning only) the three category pages and bakery-state.json.
      The evening slot renders the trends edition in the Field Guide layout
      (two sections only, tools + workflows, spec: /BAKE.md "The evening
      bake"): no news, no reader sections, no category pages, no state
      writes. Validates the output (no leftover
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

# Sections per edition slot. The MORNING template keeps the positional token
# machinery (CARD_T/M/S, EXP_T/M/S, GLANCE_TECH/MARKETS/SCIENCE mapping onto
# tech/markets/science). The EVENING (Field Guide layout, 2026-07-30) has its
# own token set: GLANCE_TOOLS/GLANCE_WORKFLOWS, SHELF_ITEMS/RECIPE_ITEMS
# (item HTML built here, not in the template), and an optional LEAD_NOTE.
SLOTS = ("morning", "evening")
SLOT_SECTIONS = {
    "morning": ("tech", "markets", "science"),
    "evening": ("tools", "workflows"),
}
SLOT_LABEL = {"morning": "Morning edition", "evening": "Evening edition"}
SLOT_TEMPLATE = {"morning": "home.html", "evening": "evening.html"}
MORNING_BADGES = {
    "tech": "Technology",
    "markets": "Business & markets",
    "science": "Science",
}
X_LEAD_MAX_CHARS = 130
SECTIONS = SLOT_SECTIONS["morning"]  # legacy alias
_PREFIXES = ("T", "M", "S")
_GLANCE_TOKENS = ("GLANCE_TECH", "GLANCE_MARKETS", "GLANCE_SCIENCE")
EM_DASH_RE = re.compile(r"—|&mdash;|&#0*8212;|&#x0*2014;", re.IGNORECASE)

# Every token family the templates carry. Post-render, none may survive.
LEFTOVER_TOKEN_RE = re.compile(
    r"\b(LEAD_(URL|BADGE|HEADLINE|STANDFIRST|BODY)"
    r"|CARD_[TMS][12]_(URL|HEADLINE|DEK)"
    r"|CAT_[1-6]_(URL|HEADLINE|DEK)"
    r"|EXP_[TMS][123]_(URL|TEXT)"
    r"|GLANCE_(TECH|MARKETS|SCIENCE|TOOLS|WORKFLOWS)"
    r"|SHELF_ITEMS|RECIPE_ITEMS|LEAD_NOTE"
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

    # counter-sync owns network ingestion.  Planning reads the committed,
    # reviewable snapshot only so a bake cannot mutate reader input behind the
    # workflow's changed-file gate.
    rows = ddb_satchel.classify(ddb_satchel.load_csv_rows(csv_path)) if csv_path.exists() else {
        "asks": [], "king_letters": [], "pins": []
    }

    plan: dict = {
        "counter_source": "committed counter.csv",
        "csv_fetched": False,  # retained for older bake-session consumers
        "ask": None,
        "king": None,
        "pin": None,
    }

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


def validate_content(c: dict, date: str, slot: str) -> None:
    _require(isinstance(c, dict), "content root must be an object")
    sections = SLOT_SECTIONS[slot]
    _require(c.get("date") == date, f"content date {c.get('date')!r} != --date {date!r}")
    lead = c.get("lead") or {}
    _require(isinstance(lead, dict), "lead must be an object")
    for k in ("section", "title", "url", "badge", "standfirst", "body"):
        _require(isinstance(lead.get(k), str) and bool(lead[k].strip()),
                 f"lead.{k} must be a non-empty string")
    _require(lead["section"] in sections,
             f"lead.section {lead['section']!r} invalid for the {slot} edition")
    _require(ddb_bake.is_safe_source_url(lead["url"]),
             "lead.url must be an absolute credential-free https link")
    _require(len(lead["title"]) <= X_LEAD_MAX_CHARS,
             f"lead.title must be <= {X_LEAD_MAX_CHARS} characters for the X contract")

    def require_dek(value: object, path: str) -> None:
        try:
            ddb_bake.render_dek(value)
        except ValueError as exc:
            fail(f"{path}: {exc}")

    cards = c.get("cards") or {}
    _require(isinstance(cards, dict), "cards must be an object")
    if slot == "evening":
        _require(lead["badge"] in ("Trending tool", "Trending workflow"),
                 f"evening lead.badge must be 'Trending tool' or 'Trending workflow', "
                 f"got {lead['badge']!r}")
        _require(lead.get("note") is None or isinstance(lead.get("note"), str),
                 "lead.note must be a string when present")
        note = (lead.get("note") or "").strip()
        _require(len(note) <= 40, "lead.note is a short handwritten aside; keep it under 40 chars")
        _require(set(cards) == set(sections),
                 f"evening cards must be exactly {set(sections)}, got {set(cards)} "
                 "(news has no evening slot; the trending stories section is retired)")
        tools = cards.get("tools") or []
        _require(isinstance(tools, list), "cards.tools must be a list")
        _require(2 <= len(tools) <= 6, f"cards.tools: need 2-6 items, got {len(tools)}")
        for i, t in enumerate(tools):
            _require(isinstance(t, dict), f"cards.tools[{i}] must be an object")
            for k in ("name", "url", "cost", "kind", "seen", "blurb"):
                _require(isinstance(t.get(k), str) and bool(t[k].strip()),
                         f"cards.tools[{i}].{k} must be a non-empty string")
            _require(ddb_bake.is_safe_source_url(t["url"]),
                     f"cards.tools[{i}].url must be an absolute credential-free https link")
            _require(len(t["name"]) <= 60, f"cards.tools[{i}].name too long for a shelf tile")
            for k in ("cost", "kind", "seen"):
                _require(len(t[k]) <= 32, f"cards.tools[{i}].{k} too long for a tag chip")
        flows = cards.get("workflows") or []
        _require(isinstance(flows, list), "cards.workflows must be a list")
        _require(2 <= len(flows) <= 6, f"cards.workflows: need 2-6 items, got {len(flows)}")
        for i, w in enumerate(flows):
            _require(isinstance(w, dict), f"cards.workflows[{i}] must be an object")
            for k in ("title", "url", "dek", "time"):
                _require(isinstance(w.get(k), str) and bool(w[k].strip()),
                         f"cards.workflows[{i}].{k} must be a non-empty string")
            _require(ddb_bake.is_safe_source_url(w["url"]),
                     f"cards.workflows[{i}].url must be an absolute credential-free https link")
            require_dek(w["dek"], f"cards.workflows[{i}].dek")
            _require(len(w["time"]) <= 24, f"cards.workflows[{i}].time too long for a chip")
            needs = w.get("needs") or []
            _require(isinstance(needs, list),
                     f"cards.workflows[{i}].needs must be a list")
            _require(2 <= len(needs) <= 4
                     and all(isinstance(n, str) and n.strip() for n in needs),
                     f"cards.workflows[{i}].needs: 2-4 short non-empty strings")
            _require(all(len(str(n)) <= 40 for n in needs),
                     f"cards.workflows[{i}].needs entries must stay short (<=40 chars)")
    else:
        _require(lead["badge"] == MORNING_BADGES[lead["section"]],
                 f"morning lead.badge for {lead['section']!r} must be "
                 f"{MORNING_BADGES[lead['section']]!r}")
        _require(set(cards) == set(sections),
                 f"morning cards must be exactly {set(sections)}, got {set(cards)}")
        for s in sections:
            items = cards.get(s) or []
            _require(isinstance(items, list), f"cards.{s} must be a list")
            _require(2 <= len(items) <= 6, f"cards.{s}: need 2-6 items, got {len(items)}")
            for i, item in enumerate(items):
                _require(isinstance(item, dict), f"cards.{s}[{i}] must be an object")
                for k in ("title", "url", "dek"):
                    _require(isinstance(item.get(k), str) and bool(item[k].strip()),
                             f"cards.{s}[{i}].{k} must be a non-empty string")
                _require(ddb_bake.is_safe_source_url(item["url"]),
                         f"cards.{s}[{i}].url must be an absolute credential-free https link")
                require_dek(item["dek"], f"cards.{s}[{i}].dek")

    glance = c.get("glance") or {}
    _require(isinstance(glance, dict), "glance must be an object")
    _require(set(glance) == set(sections),
             f"glance must be exactly {set(sections)}, got {set(glance)}")
    for s in sections:
        _require(isinstance(glance.get(s), str) and bool(glance[s].strip()),
                 f"glance.{s} must be a non-empty string")
        _require(len(glance[s].split()) <= 20,
                 f"glance.{s} must be <=20 words")

    def scan(obj, path="content"):
        if isinstance(obj, str):
            _require(not EM_DASH_RE.search(obj), f"em dash found in {path} (house style forbids them)")
            _require(not LEFTOVER_TOKEN_RE.search(obj),
                     f"template token found in {path}; refusing ambiguous rendered output")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")
    scan(c)

    if slot == "evening":
        _require(not (c.get("reader") or {}),
                 "evening editions carry no reader sections; omit the reader key "
                 "(the Counter feeds the morning edition only)")
        return

    reader = c.get("reader") or {}
    _require(isinstance(reader, dict), "reader must be an object")
    king = reader.get("king")
    if king:
        _require(isinstance(king, dict), "reader.king must be an object")
        _require(isinstance(king.get("question"), str) and bool(king["question"].strip()),
                 "reader.king.question missing")
        _require(isinstance(king.get("answer"), str) and bool(king["answer"].strip()),
                 "reader.king.answer missing")
        _require((isinstance(king.get("state_key"), str) and bool(king["state_key"]))
                 or (isinstance(king.get("satchel_id"), str) and bool(king["satchel_id"])),
                 "reader.king needs state_key (reader mail) or satchel_id (house letter)")
        _require(bool(king.get("state_key")) != bool(king.get("satchel_id")),
                 "reader.king must have exactly one of state_key or satchel_id")
        if king.get("state_key"):
            _require(isinstance(king.get("from"), str) and bool(king["from"].strip()),
                     "reader.king.from is required for reader mail")
    ask = reader.get("ask")
    if ask:
        _require(isinstance(ask, dict), "reader.ask must be an object")
        _require(isinstance(ask.get("question"), str) and bool(ask["question"].strip())
                 and isinstance(ask.get("answer"), str) and bool(ask["answer"].strip())
                 and isinstance(ask.get("state_key"), str) and bool(ask["state_key"]),
                 "reader.ask needs question + answer + state_key")
    pin = reader.get("pin")
    if pin:
        _require(isinstance(pin, dict), "reader.pin must be an object")
        _require(isinstance(pin.get("text"), str) and bool(pin["text"].strip())
                 and isinstance(pin.get("state_key"), str) and bool(pin["state_key"]),
                 "reader.pin needs text + state_key")
        _require(pin.get("sig_name") is None or isinstance(pin.get("sig_name"), str),
                 "reader.pin.sig_name must be a string when present")


def validate_reader_provenance(reader: dict, csv_path: Path | None = None,
                               state_path: Path | None = None,
                               satchel_path: Path | None = None,
                               require_complete: bool = False) -> None:
    """Bind reader-visible submissions to the committed Counter and satchel.

    Replies remain editorial model output, but the quoted question, sender,
    signature, selection order, and bookkeeping key may not be invented or
    swapped. Pin text may differ because the product explicitly permits a
    light typo copyedit.
    """
    csv_path = csv_path or REPO / "counter.csv"
    state_path = state_path or REPO / "bakery-state.json"
    satchel_path = satchel_path or REPO / "kings-satchel.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    rows = ddb_satchel.classify(ddb_satchel.load_csv_rows(csv_path))

    expected_ask = ddb_satchel.pick_oldest_unused(
        rows["asks"], set(state.get("answeredQuestions", []))
    )
    ask = reader.get("ask")
    if require_complete:
        _require(bool(ask) == bool(expected_ask),
                 "reader.ask must match whether the plan has a waiting question")
    if ask:
        expected = expected_ask
        _require(expected is not None, "reader.ask has no waiting Counter source")
        _require(ask["state_key"] == ddb_satchel.dedup_key(expected),
                 "reader.ask.state_key does not match the oldest waiting Counter question")
        _require(ask["question"] == ddb_satchel.strip_em_dashes(expected["text"]),
                 "reader.ask.question does not match its Counter source")

    expected_king = ddb_satchel.pick_oldest_unused(
        rows["king_letters"], set(state.get("kingLetters", []))
    )
    unused_house_letters = [
        letter for letter in ddb_satchel.load_satchel(satchel_path)
        if letter.get("id") not in set(state.get("usedSatchelLetters", []))
    ]
    king = reader.get("king")
    if require_complete:
        _require(bool(king) == bool(expected_king or unused_house_letters),
                 "reader.king must match whether the plan has reader or house mail")
    if king and king.get("state_key"):
        expected = expected_king
        _require(expected is not None, "reader.king has no waiting Counter source")
        _require(king["state_key"] == ddb_satchel.dedup_key(expected),
                 "reader.king.state_key does not match the oldest waiting Counter letter")
        letter = expected["text"][len(ddb_satchel.KING_PREFIX):].strip()
        _require(king["question"] == ddb_satchel.strip_em_dashes(letter),
                 "reader.king.question does not match its Counter source")
        _require(king["from"] == ddb_satchel.strip_em_dashes(expected["name"]),
                 "reader.king.from does not match its Counter source")
    elif king:
        _require(expected_king is None,
                 "reader.king cannot use a house letter while reader mail waits")
        expected = next(
            (letter for letter in unused_house_letters
             if letter.get("id") == king["satchel_id"]),
            None,
        )
        _require(expected is not None, "reader.king.satchel_id is not in kings-satchel.json")
        _require(king["question"] == ddb_satchel.strip_em_dashes(expected["letter"]),
                 "reader.king.question does not match its house letter")

    expected_pin = ddb_satchel.pick_oldest_unused(
        rows["pins"], set(state.get("postedPins", []))
    )
    pin = reader.get("pin")
    if require_complete:
        _require(bool(pin) == bool(expected_pin),
                 "reader.pin must match whether the plan has a waiting pin")
    if pin:
        expected = expected_pin
        _require(expected is not None, "reader.pin has no waiting Counter source")
        _require(pin["state_key"] == ddb_satchel.dedup_key(expected),
                 "reader.pin.state_key does not match the oldest waiting Counter pin")
        _require((pin.get("sig_name") or "Anonymous")
                 == ddb_satchel.strip_em_dashes(expected["name"]),
                 "reader.pin.sig_name does not match its Counter source")


def _evening_shelf_html(tools: list[dict]) -> str:
    """Build the tool-shelf tiles (Field Guide left lane) as template-ready HTML."""
    esc, esc_text = ddb_bake._esc, ddb_bake._esc_text
    out = []
    for t in tools:
        out.append(
            '        <div class="shelf-card"><a href="{u}">\n'
            '          <h3>{n}</h3>\n'
            '          <div class="shelf-tags"><span class="tagchip cost">{c}</span>'
            '<span class="tagchip">{k}</span><span class="tagchip seen">{s}</span></div>\n'
            '          <p>{b}</p>\n'
            '        </a></div>'.format(
                u=esc(t["url"]), n=esc_text(t["name"]), c=esc_text(t["cost"]),
                k=esc_text(t["kind"]), s=esc_text(t["seen"]), b=esc_text(t["blurb"])))
    return "\n".join(out)


def _evening_recipes_html(flows: list[dict]) -> str:
    """Build the workflow recipe cards (Field Guide right lane), each with its
    own notes block keyed by the story URL, as template-ready HTML."""
    esc, esc_text = ddb_bake._esc, ddb_bake._esc_text
    out = []
    for w in flows:
        needs = '<span class="dot">&middot;</span>'.join(
            esc_text(str(n)) for n in w["needs"])
        out.append(
            '        <article class="recipe"><a class="card-link" href="{u}">\n'
            '          <div class="r-top"><h3>{t}</h3><span class="time">{tm}</span></div>\n'
            '          <p class="dek">{d}</p>\n'
            '          <div class="needs"><b>You need</b>{nd}</div>\n'
            '        </a></article>\n'
            '        <div class="notes" data-note-key="{u}"><span class="pen">&#9998;</span>'
            '<textarea rows="1" placeholder="Notes&hellip;" aria-label="Notes on this story">'
            '</textarea><button class="notes-close" type="button" title="Close notes" '
            'aria-label="Close notes">&times;</button></div>'.format(
                u=esc(w["url"]), t=esc_text(w["title"]), tm=esc_text(w["time"]),
                d=ddb_bake.render_dek(w["dek"]), nd=needs))
    return "\n".join(out)


def render_evening_from_content(c: dict, date: str) -> tuple[str, str]:
    """Render the Field Guide evening edition (layout adopted 2026-07-30):
    lead pick, two-row glance, tool shelf, workflow recipes. Returns
    (html, lead_title)."""
    template = (REPO / "templates" / SLOT_TEMPLATE["evening"]).read_text(encoding="utf-8")
    esc, esc_text = ddb_bake._esc, ddb_bake._esc_text
    label = SLOT_LABEL["evening"]

    hd = ddb_bake.human_date(date)
    html = template.replace("EDITION, DATELINE_DATE", f"{label}, {hd}")
    html = html.replace("DATELINE_DATE", hd)
    html = html.replace("EDITION", label)

    lead = c["lead"]
    html = html.replace("LEAD_URL", esc(lead["url"]))
    html = html.replace("LEAD_BADGE", esc_text(lead["badge"]))
    html = html.replace("LEAD_HEADLINE", esc_text(lead["title"]))
    html = html.replace("LEAD_STANDFIRST", esc_text(lead["standfirst"]))
    html = html.replace("LEAD_BODY", esc_text(lead["body"]))
    note = str(lead.get("note") or "").strip()
    html = ddb_bake.fill_or_strip_section(
        html, "<!--LEAD_NOTE_START-->", "<!--LEAD_NOTE_END-->",
        {"LEAD_NOTE": esc_text(note)}, ["LEAD_NOTE"])

    tools, flows = c["cards"]["tools"], c["cards"]["workflows"]
    html = html.replace("GLANCE_TOOLS", esc_text(c["glance"]["tools"]))
    html = html.replace("GLANCE_WORKFLOWS", esc_text(c["glance"]["workflows"]))
    html = html.replace("SHELF_ITEMS", _evening_shelf_html(tools))
    html = html.replace("RECIPE_ITEMS", _evening_recipes_html(flows))

    readtime = ddb_bake.compute_readtime(
        lead["standfirst"], lead["body"],
        *[t["blurb"] for t in tools],
        *[w["dek"] + " " + " ".join(str(n) for n in w["needs"]) for w in flows],
    )
    html = html.replace("READTIME", readtime)
    html = html.replace("TIMESTAMP", ddb_bake.compute_timestamp_et(datetime.now(timezone.utc)))
    return html, lead["title"]


def render_home_from_content(c: dict, date: str, slot: str) -> tuple[str, str]:
    """Mirror ddb_bake.render_home's token operations exactly, sourcing all
    editorial content from the session-authored JSON instead of model calls.
    The evening slot routes to render_evening_from_content (its own template
    and token set). Returns (html, lead_title)."""
    if slot == "evening":
        return render_evening_from_content(c, date)
    template = (REPO / "templates" / SLOT_TEMPLATE[slot]).read_text(encoding="utf-8")
    esc, esc_text = ddb_bake._esc, ddb_bake._esc_text
    sections = SLOT_SECTIONS[slot]
    label = SLOT_LABEL[slot]

    hd = ddb_bake.human_date(date)
    html = template.replace("EDITION, DATELINE_DATE", f"{label}, {hd}")
    html = html.replace("DATELINE_DATE", hd)
    html = html.replace("EDITION", label)

    lead = c["lead"]
    html = html.replace("LEAD_URL", esc(lead["url"]))
    html = html.replace("LEAD_BADGE", esc_text(lead["badge"]))
    html = html.replace("LEAD_HEADLINE", esc_text(lead["title"]))
    html = html.replace("LEAD_STANDFIRST", esc_text(lead["standfirst"]))
    html = html.replace("LEAD_BODY", esc_text(lead["body"]))

    for pos, s in enumerate(sections):
        p = _PREFIXES[pos]
        items = c["cards"][s]
        for i in (1, 2):
            if i <= len(items):
                card = items[i - 1]
                html = html.replace(f"CARD_{p}{i}_URL", esc(card["url"]))
                html = html.replace(f"CARD_{p}{i}_HEADLINE", esc_text(card["title"]))
                html = html.replace(f"CARD_{p}{i}_DEK", ddb_bake.render_dek(card["dek"]))
            else:
                pattern = re.compile(
                    r'<div class="stack"><article class="card story-card"><a class="card-link" href="CARD_'
                    + p + str(i) + r'_URL">.*?</div></div>', re.DOTALL)
                html = pattern.sub("", html)

    for pos, s in enumerate(sections):
        p = _PREFIXES[pos]
        top3 = c["cards"][s][:3]
        html = html.replace(_GLANCE_TOKENS[pos], esc_text(c["glance"][s]))
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
    tokens["RQ1_Q"] = esc_text(ask["question"]) if ask else ""
    tokens["RQ1_A"] = esc_text(ask["answer"]) if ask else ""
    king = reader.get("king")
    if king:
        tokens["KQ1_Q"] = esc_text(king["question"])
        tokens["KQ1_FROM"] = ("From the Baker's own shelf" if king.get("satchel_id")
                              else f"From {esc_text(king.get('from', 'a reader'))}")
        tokens["KQ1_A"] = esc_text(king["answer"])
    else:
        tokens["KQ1_Q"] = tokens["KQ1_FROM"] = tokens["KQ1_A"] = ""
    pin = reader.get("pin")
    if pin:
        tokens["PIN1_TEXT"] = esc_text(pin["text"])
        tokens["PIN1_SIG"] = f"– {esc_text(pin.get('sig_name') or 'Anonymous')}"
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
        *[card["dek"] for s in sections for card in c["cards"][s]],
    )
    html = html.replace("READTIME", readtime)
    html = html.replace("TIMESTAMP", ddb_bake.compute_timestamp_et(datetime.now(timezone.utc)))
    return html, lead["title"]


def verify_rendered_outputs(outputs: dict[Path, str]) -> None:
    """Validate all candidate reader-visible outputs before any file changes."""
    for p, text in outputs.items():
        m = LEFTOVER_TOKEN_RE.search(text)
        _require(m is None, f"{p.name}: leftover template token {m.group() if m else ''!r}")
        if p.suffix in (".html", ".xml"):
            _require(not EM_DASH_RE.search(text), f"{p.name}: em dash in published output")
        if p.name.endswith(".html") and p.name != "404.html":
            _require('src="/header-art.png"' in text or "feed" in p.name,
                     f"{p.name}: masthead art missing")


def verify_output(paths: list[Path]) -> None:
    """Compatibility wrapper for callers validating files already on disk."""
    verify_rendered_outputs({p: p.read_text(encoding="utf-8") for p in paths})


def state_with_reader(reader: dict) -> dict:
    """Return updated reader bookkeeping without mutating the working tree."""
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
    return state


def update_state(reader: dict) -> None:
    """Compatibility wrapper for the retired direct-write helper."""
    state_path = REPO / "bakery-state.json"
    state_path.write_text(
        json.dumps(state_with_reader(reader), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def cmd_render(content_path: Path, date: str, slot: str, bake_mode: str = "daily") -> None:
    try:
        content = json.loads(content_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail(f"cannot read content JSON: {e}")

    validate_content(content, date, slot)
    if slot == "morning":
        reader = content.get("reader") or {}
        if bake_mode == "backfill":
            _require(not reader, "backfill editions must omit reader sections")
        else:
            validate_reader_provenance(reader, require_complete=True)

    archive_html_path = REPO / "archive.html"
    ddb_bake.validate_archive_file(archive_html_path)  # fail closed before any write

    html, lead_title = render_home_from_content(content, date, slot)

    editions = REPO / "editions"
    edition_path = editions / f"{date}-{slot}.html"
    outputs: dict[Path, str] = {
        edition_path: html,
        REPO / "index.html": html,
    }
    written = [edition_path, REPO / "index.html"]
    if slot == "morning":
        # Category pages belong to the morning news bake only; the evening
        # (trends) edition never rewrites tech/markets/science.
        for s in SLOT_SECTIONS["morning"]:
            cards = [
                {"title": card["title"], "url": card["url"],
                 "dek": ddb_satchel.strip_em_dashes(card["dek"])}
                for card in content["cards"][s]
            ]
            cat_html = ddb_bake.render_category(s, cards)
            cat_path = REPO / f"{s}.html"
            outputs[cat_path] = cat_html
            written.append(cat_path)

    from zoneinfo import ZoneInfo
    now_et = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
    pub_date = now_et.strftime("%a, %d %b %Y %H:%M:%S %z")
    archive_json_path = REPO / "archive.json"
    archive_data = ddb_bake.archive_with_edition(
        ddb_bake.read_archive_json(archive_json_path), date, slot, lead_title,
        ddb_bake.human_date(date), pub_date,
    )
    outputs[archive_json_path] = json.dumps(
        archive_data, indent=2, ensure_ascii=False
    ) + "\n"
    current_archive_html = archive_html_path.read_text(encoding="utf-8")
    outputs[archive_html_path] = ddb_bake.update_archive_html(
        current_archive_html, archive_data
    )
    outputs[REPO / "feed.xml"] = ddb_bake.render_feed_xml(archive_data)
    written += [archive_html_path, REPO / "feed.xml"]

    if slot == "morning" and bake_mode == "daily":
        # Reader-content bookkeeping is a morning concern; the evening bake
        # and historical backfills leave reader state untouched.
        state_path = REPO / "bakery-state.json"
        outputs[state_path] = json.dumps(
            state_with_reader(content.get("reader") or {}),
            indent=2,
            ensure_ascii=False,
        ) + "\n"

    # All validation happens before the first replace.  Each destination is
    # then installed from a fully written sibling temp file.
    verify_rendered_outputs({
        path: text for path, text in outputs.items()
        if path.suffix in (".html", ".xml")
    })
    editions.mkdir(exist_ok=True)
    for path, text in outputs.items():
        ddb_bake._atomic_replace_bytes(path, text.encode("utf-8"))
    print(f"BAKE OK: {date} {slot} · lead: {lead_title}")
    for p in written:
        print(f"  wrote {p.relative_to(REPO)}")
    wrote_state = slot == "morning" and bake_mode == "daily"
    print("  wrote archive.json" + (", bakery-state.json" if wrote_state else ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--render", action="store_true")
    ap.add_argument("--content", type=Path, help="content JSON (render mode)")
    ap.add_argument("--date", help="YYYY-MM-DD edition date (render mode)")
    ap.add_argument("--slot", choices=SLOTS, default="morning",
                    help="which edition to render: morning (news; the default) or "
                         "evening (Field Guide: trending tools + workflows only, "
                         "no news, no reader sections, no category pages). "
                         "--plan is a morning-only concern.")
    ap.add_argument("--mode", choices=("daily", "backfill"),
                    default=os.environ.get("DDB_MODE", "daily"),
                    help="daily or historical reconstruction mode (default: DDB_MODE or daily)")
    ap.add_argument("--csv", type=Path, default=REPO / "counter.csv",
                    help="Counter CSV path. Default: the repo's committed copy, kept "
                         "fresh by .github/workflows/counter-sync.yml. Planning reads "
                         "this snapshot and never refreshes it.")
    args = ap.parse_args()

    if args.plan:
        cmd_plan(args.csv)
    else:
        if not args.content or not args.date:
            fail("--render requires --content and --date")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
            fail(f"bad --date {args.date!r}")
        cmd_render(args.content, args.date, args.slot, args.mode)


if __name__ == "__main__":
    main()
