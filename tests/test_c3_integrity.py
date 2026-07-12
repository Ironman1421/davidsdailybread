#!/usr/bin/env python3
"""C3 integrity tests for mechanical history repair and isolated rendering."""

from collections import Counter
import difflib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import ddb_bake
import ddb_satchel
import ddb_synth
from tests.test_c3_brand_pages import audit_page

ROOT = Path(__file__).resolve().parents[1]
BASE = "2211e98"
HISTORICAL_REPAIRS = (
    "editions/2026-07-07-morning.html",
    "editions/2026-07-07-evening.html",
    "editions/2026-07-08-morning.html",
    "editions/2026-07-08-evening.html",
)
EM_DASH = re.compile(r"—|&mdash;|&#0*8212;|&#x0*2014;", re.IGNORECASE)
TOKEN = re.compile(
    r"\b(?:DATELINE_DATE|READTIME|TIMESTAMP|LEAD_[A-Z0-9_]+|CARD_[A-Z0-9_]+|"
    r"CAT_[A-Z0-9_]+|GLANCE_[A-Z0-9_]+|EXP_[A-Z0-9_]+|RQ1_[A-Z0-9_]+|"
    r"KQ1_[A-Z0-9_]+|PIN1_[A-Z0-9_]+|__ACTIVE_[A-Z0-9_]+__)\b"
)


class DocumentFacts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.hrefs = []
        self.visible = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ("head", "style", "script", "template"):
            self.hidden += 1
        if tag == "a":
            self.hrefs.append(values.get("href"))

    def handle_endtag(self, tag):
        if tag in ("head", "style", "script", "template") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.visible.append(data)


def parse_facts(text):
    parser = DocumentFacts()
    parser.feed(text)
    visible = " ".join(" ".join(parser.visible).split())
    numbers = re.findall(r"\d+(?:[.,]\d+)*(?:%|B|M)?", visible)
    return Counter(parser.hrefs), numbers


def git_text(revision, path):
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"], cwd=ROOT, text=True
    )


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.edition_links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        href = values.get("href") or ""
        if tag == "a" and href.startswith("editions/"):
            self.edition_links.append(href)


class C3IntegrityTest(unittest.TestCase):
    maxDiff = None

    def test_historical_repairs_are_mechanical_and_fact_preserving(self):
        for relative in HISTORICAL_REPAIRS:
            with self.subTest(page=relative):
                before = git_text(BASE, relative)
                after = (ROOT / relative).read_text(encoding="utf-8")
                before_links, before_numbers = parse_facts(before)
                after_links, after_numbers = parse_facts(after)

                expected_links = before_links.copy()
                if relative.endswith("2026-07-07-morning.html"):
                    expected_links["/"] += 1  # official masthead home link
                self.assertEqual(expected_links, after_links)
                self.assertEqual(before_numbers, after_numbers)
                self.assertNotRegex(after, EM_DASH)

                matcher = difflib.SequenceMatcher(
                    a=before.splitlines(), b=after.splitlines(), autojunk=False
                )
                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    if tag == "equal":
                        continue
                    old_lines = before.splitlines()[i1:i2]
                    new_lines = after.splitlines()[j1:j2]
                    if not old_lines:  # the only pure insertion is masthead CSS
                        self.assertTrue(relative.endswith("2026-07-07-morning.html"))
                        self.assertTrue(
                            all("masthead-art" in line for line in new_lines), new_lines
                        )
                        continue
                    for line in old_lines:
                        allowed_legacy_header = (
                            relative.endswith("2026-07-07-morning.html")
                            and ("class=\"motif\"" in line or "class=\"wordmark\"" in line)
                        )
                        self.assertTrue(
                            EM_DASH.search(line) or allowed_legacy_header,
                            f"non-mechanical historical change in {relative}: {line}",
                        )

    def test_archive_and_feed_retain_the_same_manifest(self):
        archive = json.loads((ROOT / "archive.json").read_text(encoding="utf-8"))
        entries = archive["editions"]
        files = [entry["file"] for entry in entries]
        self.assertEqual(len(files), len(set(files)))
        self.assertEqual(
            files,
            [
                entry["file"]
                for entry in sorted(
                    entries,
                    key=lambda entry: (
                        entry["date"],
                        0 if entry["edition"] == "morning" else 1,
                    ),
                    reverse=True,
                )
            ],
        )
        self.assertTrue(all((ROOT / path).is_file() for path in files))

        archive_html = (ROOT / "archive.html").read_text(encoding="utf-8")
        self.assertEqual(ddb_bake.render_archive_html(archive), archive_html)
        links = LinkParser()
        links.feed(archive_html)
        self.assertEqual(files, links.edition_links)

        feed = ET.parse(ROOT / "feed.xml").getroot()
        items = feed.findall("./channel/item")
        feed_paths = [urlparse(item.findtext("link", "")).path.lstrip("/") for item in items]
        self.assertEqual(files, feed_paths)
        for entry, item in zip(entries, items):
            self.assertEqual(
                f"https://davidsdailybread.com/{entry['file']}",
                item.findtext("guid"),
            )
            self.assertIn(entry["dateHuman"], item.findtext("title", ""))
            self.assertIn(entry["lead"], item.findtext("title", ""))

    def test_all_em_dash_encodings_are_sanitized(self):
        sample = "alpha — beta &mdash; gamma &#8212; delta &#x2014; omega"
        expected = "alpha, beta, gamma, delta, omega"
        self.assertEqual(expected, ddb_synth.strip_em_dashes(sample))
        self.assertEqual(expected, ddb_satchel.strip_em_dashes(sample))
        self.assertEqual(expected, ddb_bake._esc_text(sample))

    def test_fresh_isolated_scratch_bake_is_c3_clean(self):
        with tempfile.TemporaryDirectory(prefix="ddb-c3-scratch-") as tmp:
            scratch = Path(tmp) / "site"
            shutil.copytree(
                ROOT,
                scratch,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            drafts = scratch / "scratch-drafts"
            drafts.mkdir()
            draft = """## Tech
- [Alpha — source title](https://example.test/tech)
  <sub>Example · Jul 12 01:00</sub>
## Markets
- [Market source title](https://example.test/markets)
  <sub>Example · Jul 12 01:00</sub>
## Science
- [Science source title](https://example.test/science)
  <sub>Example · Jul 12 01:00</sub>
"""
            (drafts / "2099-01-01-am.md").write_text(draft, encoding="utf-8")
            runner = r'''
from pathlib import Path
import sys
import ddb_bake

ddb_bake.DRAFTS = Path("scratch-drafts")

def cards(items, count):
    return [
        {
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "dek": "<b>Grounded test</b> with no changed source facts.",
        }
        for item in items[:count]
    ]

ddb_bake.build_ranked_cards = cards
ddb_bake.ddb_synth.synthesize_lead = lambda candidates: {
    "section": candidates[0]["section"],
    "title": candidates[0]["title"],
    "url": candidates[0]["url"],
    "badge": "Scratch — test",
    "standfirst": "A deterministic — standfirst.",
    "body": "A deterministic &#8212; body.",
}
ddb_bake.ddb_synth.synthesize_glance = (
    lambda section, titles: ddb_bake.ddb_synth.strip_em_dashes(
        section + " — " + titles[0]
    )
)
ddb_bake.ddb_satchel.fill_reader_sections = lambda *args, **kwargs: {}
sys.argv = ["ddb_bake.py", "--slot", "am", "--date", "2099-01-01"]
ddb_bake.main()
'''
            env = os.environ.copy()
            env["DDB_SITE_DIR"] = str(scratch)
            result = subprocess.run(
                [sys.executable, "-c", runner],
                cwd=scratch,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("Done. Edition: am", result.stdout)

            pages = sorted(scratch.glob("*.html")) + sorted(
                (scratch / "editions").glob("*.html")
            )
            failures = []
            for page in pages:
                problems = audit_page(page)
                if problems:
                    failures.append(f"{page.relative_to(scratch)}: {problems}")
                text = page.read_text(encoding="utf-8")
                unresolved = TOKEN.findall(text)
                if unresolved:
                    failures.append(
                        f"{page.relative_to(scratch)} unresolved: {unresolved}"
                    )
            self.assertEqual([], failures)

            scratch_archive = json.loads(
                (scratch / "archive.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                ddb_bake.render_archive_html(scratch_archive),
                (scratch / "archive.html").read_text(encoding="utf-8"),
            )
            ET.parse(scratch / "feed.xml")


if __name__ == "__main__":
    unittest.main()
