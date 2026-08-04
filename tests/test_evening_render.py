#!/usr/bin/env python3
"""Regression test for the two-slot renderer (2026-07-30 evening restoration;
Field Guide layout later the same day).

Renders a fixture EVENING edition (Field Guide: tools + workflows only) in a
throwaway copy of the repo and asserts the evening write-set contract: index
takeover + edition file + archive + feed ONLY. No category pages, no reader
state, no satchel, no counter. Then renders a fixture MORNING edition and
asserts the morning path still writes category pages and carries the Morning
label. Also asserts the renderer refuses an evening content.json that
smuggles in a reader key or a trending (news) section.

Standalone: python3 tests/test_evening_render.py  (no env needed; stdlib only)
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-01"  # far future: can never collide with a real edition


def card(n, section):
    return {
        "title": f"{section.capitalize()} fixture story {n}",
        "url": f"https://example.com/{section}/{n}",
        "dek": f"<b>Fixture lead-in</b> grounded one-sentence dek number {n}.",
    }


def content_for(sections, lead_section, badge):
    return {
        "date": DATE,
        "lead": {
            "section": lead_section,
            "title": "Fixture lead headline",
            "url": "https://example.com/lead",
            "badge": badge,
            "standfirst": "One punchy fixture sentence.",
            "body": "Two grounded fixture sentences. Both trace to the link.",
        },
        "cards": {s: [card(1, s), card(2, s)] for s in sections},
        "glance": {s: f"Fixture {s} roundup sentence." for s in sections},
    }


def tool(n):
    return {
        "name": f"Fixture tool {n}",
        "url": f"https://example.com/tools/{n}",
        "cost": "Free",
        "kind": "Fixture kind",
        "seen": "GitHub trending",
        "blurb": f"One factual fixture sentence number {n}, caveat included.",
    }


def workflow(n):
    return {
        "title": f"Fixture workflow {n}",
        "url": f"https://example.com/workflows/{n}",
        "dek": f"<b>Fixture lead-in</b> grounded one-sentence dek number {n}.",
        "needs": ["A fixture thing", "Another fixture thing"],
        "time": "An afternoon",
    }


def evening_content():
    """The Field Guide schema (2026-07-30): tools + workflows only, no news."""
    return {
        "date": DATE,
        "lead": {
            "section": "tools",
            "title": "Fixture lead headline",
            "url": "https://example.com/lead",
            "badge": "Trending tool",
            "standfirst": "One punchy fixture sentence.",
            "body": "Two grounded fixture sentences. Both trace to the link.",
            "note": "worth an evening",
        },
        "cards": {"tools": [tool(1), tool(2)],
                  "workflows": [workflow(1), workflow(2)]},
        "glance": {"tools": "Fixture tools roundup sentence.",
                   "workflows": "Fixture workflows roundup sentence."},
    }


def tree_hashes(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def render(repo: Path, content: dict, slot: str, mode: str = "daily"):
    cj = repo / "content.json"
    cj.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "ddb_session_bake.py", "--render",
         "--content", "content.json", "--date", DATE, "--slot", slot,
         "--mode", mode],
        cwd=repo, capture_output=True, text=True)
    cj.unlink()
    return r


with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "site"
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "content.json"))

    before = tree_hashes(repo)

    # --- evening render obeys the evening write set -------------------------
    ev = evening_content()
    r = render(repo, ev, "evening")
    assert r.returncode == 0, f"evening render failed:\n{r.stdout}\n{r.stderr}"
    assert f"BAKE OK: {DATE} evening" in r.stdout, r.stdout

    after = tree_hashes(repo)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    expected = {"index.html", f"editions/{DATE}-evening.html",
                "archive.html", "archive.json", "feed.xml",
                "evening-catalog.json"}
    assert changed == expected, f"evening write set wrong: {sorted(changed ^ expected)}"

    html = (repo / "editions" / f"{DATE}-evening.html").read_text(encoding="utf-8")
    assert html == (repo / "index.html").read_text(encoding="utf-8"), "index takeover missing"
    assert "Evening edition," in html
    for label in ("Start here tonight", "The tool shelf", "The workflows",
                  "no waitlists, no vaporware", "Keep and Ponder",
                  "Mary of Nazareth",
                  "Guided by the biblical witness of Mary of Nazareth.",
                  "Keep", "Ponder", "Entrust"):
        assert label in html, f"missing Field Guide label {label!r}"
    assert 'class="journey-step"' not in html
    assert 'class="step-number"' not in html
    assert 'href="/tools.html"' in html and 'href="/workflows.html"' in html
    assert 'href="#shelf"' not in html and 'href="#workflows"' not in html
    assert "worth an evening" in html, "lead.note margin aside missing"
    assert html.count('class="shelf-card"') == 2, "shelf tile count wrong"
    assert html.count('class="recipe"') == 2, "recipe card count wrong"
    assert "You need" in html and "An afternoon" in html, "recipe meta missing"
    for old in ("Trending tonight", "Workflows worth knowing", "CARD_T1"):
        assert old not in html, f"old three-section layout leaked: {old!r}"
    for kicker in ("Reader questions", "Letters to the King", "Crumb Board"):
        assert kicker not in html, f"reader section {kicker!r} leaked into the evening"

    archive = json.loads((repo / "archive.json").read_text(encoding="utf-8"))
    entry = [e for e in archive["editions"]
             if e["date"] == DATE and e["edition"] == "evening"]
    assert len(entry) == 1 and entry[0]["file"] == f"editions/{DATE}-evening.html"
    assert "Evening edition" in (repo / "feed.xml").read_text(encoding="utf-8")

    catalog = json.loads((repo / "evening-catalog.json").read_text(encoding="utf-8"))
    assert catalog["version"] == 1
    assert [item["name"] for item in catalog["tools"][:2]] == [
        "Fixture tool 1", "Fixture tool 2"
    ]
    assert [item["title"] for item in catalog["workflows"][:2]] == [
        "Fixture workflow 1", "Fixture workflow 2"
    ]
    assert all(item["date"] == DATE for item in catalog["tools"][:2])

    # --- the lead.note is optional: omitting it strips the margin aside -----
    quiet = evening_content()
    del quiet["lead"]["note"]
    r = render(repo, quiet, "evening")
    assert r.returncode == 0, f"note-less evening render failed:\n{r.stdout}\n{r.stderr}"
    html = (repo / "index.html").read_text(encoding="utf-8")
    assert 'class="margin-note"' not in html, "empty lead.note must strip the aside"

    # --- an evening content.json smuggling a reader key is refused ----------
    bad = evening_content()
    bad["reader"] = {"ask": {"question": "q", "answer": "a", "state_key": "k"}}
    r = render(repo, bad, "evening")
    assert r.returncode != 0, "evening render must refuse a reader key"
    assert "no reader sections" in (r.stdout + r.stderr)

    # --- a trending (news) cards section is refused: no news after dark -----
    news = evening_content()
    news["cards"]["trending"] = [card(1, "trending"), card(2, "trending")]
    r = render(repo, news, "evening")
    assert r.returncode != 0, "evening render must refuse a trending section"
    assert "retired" in (r.stdout + r.stderr)

    # --- morning render still writes the morning set ------------------------
    before = tree_hashes(repo)
    mo = content_for(("tech", "markets", "science"), "tech", "Technology")
    # This mechanics fixture intentionally carries no live reader plan, so it
    # uses backfill mode. Daily mode separately requires exact plan provenance.
    r = render(repo, mo, "morning", "backfill")
    assert r.returncode == 0, f"morning render failed:\n{r.stdout}\n{r.stderr}"
    assert f"BAKE OK: {DATE} morning" in r.stdout, r.stdout

    after = tree_hashes(repo)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    for must in ("index.html", f"editions/{DATE}-morning.html",
                 "tech.html", "markets.html", "science.html",
                 "archive.html", "archive.json", "feed.xml"):
        assert must in changed, f"morning render did not write {must}"
    assert not changed - {"index.html", f"editions/{DATE}-morning.html",
                          "tech.html", "markets.html", "science.html",
                          "archive.html", "archive.json", "feed.xml",
                          "bakery-state.json"}, f"unexpected morning writes: {changed}"
    assert "Morning edition," in (repo / "index.html").read_text(encoding="utf-8")

print("PASS: two-slot renderer honors the evening write set, refuses evening "
      "reader sections, and leaves the morning bake intact")
