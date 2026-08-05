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
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-01"  # far future: can never collide with a real edition
RETRY_DATE = "2099-01-02"
SATCHEL_DATE = "2099-01-03"


def card(n, section):
    return {
        "title": f"{section.capitalize()} fixture story {n}",
        "url": f"https://example.com/{section}/{n}",
        "dek": f"<b>Fixture lead-in</b> grounded one-sentence dek number {n}.",
        "scripture": {
            "id": "PRO.18.15",
            "connection": "We can seek knowledge carefully as we consider this story.",
        },
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
            "scripture": {
                "id": "PRO.18.15",
                "connection": "We can give learning a faithful direction through discernment.",
            },
        },
        "cards": {s: [card(1, s), card(2, s)] for s in sections},
        "glance": {s: f"Fixture {s} roundup sentence." for s in sections},
    }


def tool(n):
    return {
        "name": f"Fixture tool {n}",
        "url": f"https://example.com/tools/{n}",
        "trend_url": f"https://example.com/trends/tools/{n}",
        "cost": "Free",
        "kind": "Fixture kind",
        "seen": "GitHub trending",
        "blurb": f"One factual fixture sentence number {n}, caveat included.",
    }


def workflow(n):
    return {
        "title": f"Fixture workflow {n}",
        "url": f"https://example.com/workflows/{n}",
        "trend_url": f"https://example.com/trends/workflows/{n}",
        "seen": "Hacker News front page",
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
            "trend_url": "https://example.com/trends/lead",
            "seen": "Product Hunt No. 1",
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


def render(repo: Path, content: dict, slot: str, mode: str = "daily",
           date: str = DATE):
    cj = repo / "content.json"
    cj.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [sys.executable, "ddb_session_bake.py", "--render",
         "--content", "content.json", "--date", date, "--slot", slot,
         "--mode", mode],
        cwd=repo, capture_output=True, text=True)
    cj.unlink()
    return r


def render_with_state_write_failure(repo: Path, content: dict, date: str):
    cj = repo / "content.json"
    cj.write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    script = """
from pathlib import Path
import sys
import ddb_session_bake

original = ddb_session_bake.ddb_bake._atomic_replace_bytes
def fail_state(path, payload):
    if path.name == "bakery-state.json":
        raise OSError("injected state write failure")
    original(path, payload)

ddb_session_bake.ddb_bake._atomic_replace_bytes = fail_state
ddb_session_bake.cmd_render(Path("content.json"), sys.argv[1], "morning", "daily")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, date],
        cwd=repo, capture_output=True, text=True,
    )
    cj.unlink()
    return result


def install_house_fixtures(repo: Path) -> None:
    (repo / "bakery-state.json").write_text(
        json.dumps({
            "note": "Fixture state",
            "answeredQuestions": [],
            "postedPins": [],
            "kingLetters": [],
            "usedSatchelLetters": [],
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    (repo / "kings-satchel.json").write_text(
        json.dumps({
            "note": "Fixture satchel",
            "letters": [
                {
                    "id": "KS-001",
                    "added": "2098-12-01",
                    "letter": "First fixture house letter",
                },
                {
                    "id": "KS-002",
                    "added": "2098-12-02",
                    "letter": "Second fixture house letter",
                },
            ],
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def reader_content_from_plan(repo: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "ddb_session_bake.py", "--plan"],
        cwd=repo, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["intake_status"] == "paused"
    assert plan["ask"] is None and plan["pin"] is None
    king = plan.get("king")
    if not king:
        return {}
    assert king["kind"] == "satchel"
    return {
        "king": {
            "question": king["letter"],
            "answer": "A warm fixture answer grounded in the reviewed house letter.",
            "satchel_id": king["id"],
        }
    }


with tempfile.TemporaryDirectory() as td:
    repo = Path(td) / "site"
    shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", "content.json"))
    install_house_fixtures(repo)

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
    assert (
        "News and Scripture each morning. Practical tools each evening. Loved by God."
        in html
    )
    assert "aspect-ratio: 1124 / 330" in html
    assert "transform: translateX(3.4%)" in html
    assert 'class="masthead next-format"' in html
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
    assert '<div class="r-top"><h3>Fixture workflow 1</h3><div class="r-meta">' in html, (
        "workflow cards must match the shelf hierarchy: headline, metadata, brief"
    )
    assert ".recipe .r-top { display: flex; flex-direction: column;" in html
    assert html.count('class="shelf-card"') == 2, "shelf tile count wrong"
    assert html.count('class="recipe"') == 2, "recipe card count wrong"
    assert (
        '<span class="time">An afternoon</span>'
        '<span class="requirement">A fixture thing</span>'
        '<span class="trend">Hacker News front page</span>' in html
    ), "workflow pills must match the shelf order: blue, gray, gold"
    assert "You need" not in html, "the old workflow requirements row leaked"
    assert "Hacker News front page" in html, "workflow trend evidence missing"
    assert "Product Hunt No. 1" in html, "lead trend evidence missing"
    for old in ("Trending tonight", "Workflows worth knowing", "CARD_T1"):
        assert old not in html, f"old three-section layout leaked: {old!r}"
    for kicker in ("Reader questions", "Letters to the King", "Crumb Board"):
        assert kicker not in html, f"reader section {kicker!r} leaked into the evening"
    assert 'class="scripture-inline"' not in html, (
        "morning Scripture pairing leaked into the evening"
    )

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
    assert all(item["trend_url"] != item["url"] for item in catalog["tools"][:2])
    assert all(item["seen"] == "Hacker News front page"
               for item in catalog["workflows"][:2])

    stable_evening = tree_hashes(repo)
    time.sleep(1.1)
    repeated_evening = render(repo, ev, "evening")
    assert repeated_evening.returncode == 0, (
        "same-edition evening retry failed:\n"
        f"{repeated_evening.stdout}\n{repeated_evening.stderr}"
    )
    assert tree_hashes(repo) == stable_evening, (
        "same-edition evening retry must be byte-stable"
    )

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

    # --- every new evening item carries independent trend evidence ----------
    missing_evidence = evening_content()
    del missing_evidence["cards"]["workflows"][0]["trend_url"]
    r = render(repo, missing_evidence, "evening")
    assert r.returncode != 0, "evening workflow without trend evidence must fail"
    assert "trend_url must be a non-empty string" in (r.stdout + r.stderr)

    direct_x = evening_content()
    direct_x["cards"]["tools"][0]["trend_url"] = "https://x.com/example/status/1"
    r = render(repo, direct_x, "evening")
    assert r.returncode != 0, "direct X sourcing must remain closed"
    assert "direct X/Twitter sources are closed" in (r.stdout + r.stderr)

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
    morning_html = (repo / "index.html").read_text(encoding="utf-8")
    assert "Morning edition," in morning_html
    assert morning_html.count('class="scripture-inline"') == 7
    assert "Proverbs 18:15 &middot; BSB" in morning_html
    assert "Scripture accompanies each story for the reader's reflection." in morning_html
    assert (
        "News and Scripture each morning. Practical tools each evening. Loved by God."
        in morning_html
    )
    for section in ("tech", "markets", "science"):
        category_html = (repo / f"{section}.html").read_text(encoding="utf-8")
        assert category_html.count('class="scripture-inline"') == 2
    for generated in (
        repo / "index.html",
        repo / "editions" / f"{DATE}-morning.html",
        repo / "tech.html",
        repo / "markets.html",
        repo / "science.html",
        repo / "archive.html",
        repo / "feed.xml",
    ):
        assert not any(
            line.endswith((" ", "\t"))
            for line in generated.read_text(encoding="utf-8").splitlines()
        ), f"generated trailing whitespace in {generated.name}"

    # --- same-edition daily retries survive advanced reader state -----------
    retry = content_for(("tech", "markets", "science"), "tech", "Technology")
    retry["date"] = RETRY_DATE
    retry["reader"] = reader_content_from_plan(repo)
    state_before_partial = (repo / "bakery-state.json").read_bytes()
    partial = render_with_state_write_failure(repo, retry, RETRY_DATE)
    assert partial.returncode != 0, "state-write failure injection did not fire"
    assert (repo / "bakery-state.json").read_bytes() == state_before_partial
    assert (repo / "editions" / f"{RETRY_DATE}-morning.html").is_file()
    first = render(repo, retry, "morning", "daily", RETRY_DATE)
    assert first.returncode == 0, (
        "retry after partial state-write failure failed:\n"
        f"{first.stdout}\n{first.stderr}"
    )
    state_after_first = (repo / "bakery-state.json").read_bytes()
    changed_retry = copy.deepcopy(retry)
    changed_retry["lead"]["body"] = "A corrected factual fixture body grounded in the link."
    if changed_retry["reader"].get("king"):
        changed_retry["reader"]["king"]["answer"] += " A corrected closing sentence."
    corrected = render(repo, changed_retry, "morning", "daily", RETRY_DATE)
    assert corrected.returncode == 0, (
        "same-edition correction failed after bakery-state.json advanced:\n"
        f"{corrected.stdout}\n{corrected.stderr}"
    )
    assert (repo / "bakery-state.json").read_bytes() == state_after_first, (
        "same-edition correction must not consume reader state twice"
    )
    after_first = tree_hashes(repo)
    # A new wall-clock second exposes timestamp/pubDate churn if the retry is
    # not anchored to the already-rendered edition.
    time.sleep(1.1)
    second = render(repo, changed_retry, "morning", "daily", RETRY_DATE)
    assert second.returncode == 0, (
        "same-edition retry failed after bakery-state.json advanced:\n"
        f"{second.stdout}\n{second.stderr}"
    )
    after_second = tree_hashes(repo)
    assert after_second == after_first, "same-edition retry must be byte-stable"

    wrong_claim = copy.deepcopy(changed_retry)
    wrong_claim["reader"] = reader_content_from_plan(repo)
    before_wrong_claim = tree_hashes(repo)
    refused = render(repo, wrong_claim, "morning", "daily", RETRY_DATE)
    assert refused.returncode != 0, "retry must refuse a different reader claim"
    assert tree_hashes(repo) == before_wrong_claim, "refused retry must write nothing"

    satchel = content_for(("tech", "markets", "science"), "tech", "Technology")
    satchel["date"] = SATCHEL_DATE
    satchel["reader"] = reader_content_from_plan(repo)
    assert set(satchel["reader"]) == {"king"}
    assert "satchel_id" in satchel["reader"]["king"]
    satchel_first = render(repo, satchel, "morning", "daily", SATCHEL_DATE)
    assert satchel_first.returncode == 0, satchel_first.stderr
    satchel_state = (repo / "bakery-state.json").read_bytes()
    satchel_retry = render(repo, satchel, "morning", "daily", SATCHEL_DATE)
    assert satchel_retry.returncode == 0, satchel_retry.stderr
    assert (repo / "bakery-state.json").read_bytes() == satchel_state

print("PASS: two-slot renderer honors the evening write set, keeps morning "
      "Scripture scoped to the full lead story, and retries byte-stably")
