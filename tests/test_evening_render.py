#!/usr/bin/env python3
"""Regression test for the two-slot renderer (2026-07-30 evening restoration).

Renders a fixture EVENING edition in a throwaway copy of the repo and asserts
the evening write-set contract: index takeover + edition file + archive + feed
ONLY. No category pages, no reader state, no satchel, no counter. Then renders
a fixture MORNING edition and asserts the morning path still writes category
pages and carries the Morning label. Also asserts the renderer refuses an
evening content.json that smuggles in a reader key.

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


def tree_hashes(root: Path) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def render(repo: Path, content: dict, slot: str):
    cj = repo / "content.json"
    cj.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "ddb_session_bake.py", "--render",
         "--content", "content.json", "--date", DATE, "--slot", slot],
        cwd=repo, capture_output=True, text=True)
    cj.unlink()
    return r


with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "site"
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "content.json"))

    before = tree_hashes(repo)

    # --- evening render obeys the evening write set -------------------------
    ev = content_for(("trending", "tools", "workflows"), "tools", "New tools")
    r = render(repo, ev, "evening")
    assert r.returncode == 0, f"evening render failed:\n{r.stdout}\n{r.stderr}"
    assert f"BAKE OK: {DATE} evening" in r.stdout, r.stdout

    after = tree_hashes(repo)
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    expected = {"index.html", f"editions/{DATE}-evening.html",
                "archive.html", "archive.json", "feed.xml"}
    assert changed == expected, f"evening write set wrong: {sorted(changed ^ expected)}"

    html = (repo / "editions" / f"{DATE}-evening.html").read_text(encoding="utf-8")
    assert html == (repo / "index.html").read_text(encoding="utf-8"), "index takeover missing"
    assert "Evening edition," in html
    for label in ("Trending tonight", "New tools", "Workflows worth knowing"):
        assert label in html, f"missing evening section label {label!r}"
    for kicker in ("Reader questions", "Letters to the King", "Crumb Board"):
        assert kicker not in html, f"reader section {kicker!r} leaked into the evening"

    archive = json.loads((repo / "archive.json").read_text(encoding="utf-8"))
    entry = [e for e in archive["editions"]
             if e["date"] == DATE and e["edition"] == "evening"]
    assert len(entry) == 1 and entry[0]["file"] == f"editions/{DATE}-evening.html"
    assert "Evening edition" in (repo / "feed.xml").read_text(encoding="utf-8")

    # --- an evening content.json smuggling a reader key is refused ----------
    bad = dict(ev)
    bad["reader"] = {"ask": {"question": "q", "answer": "a", "state_key": "k"}}
    r = render(repo, bad, "evening")
    assert r.returncode != 0, "evening render must refuse a reader key"
    assert "no reader sections" in (r.stdout + r.stderr)

    # --- morning render still writes the morning set ------------------------
    before = tree_hashes(repo)
    mo = content_for(("tech", "markets", "science"), "tech", "Technology")
    r = render(repo, mo, "morning")
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
