#!/usr/bin/env python3
"""Contract checks for the standing evening libraries and reviewed rest set."""

import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DDB_SITE_DIR", str(ROOT))

import ddb_bake  # noqa: E402


EM_DASH = re.compile(r"—|&mdash;|&#0*8212;|&#x0*2014;", re.IGNORECASE)


class EveningLibraryTest(unittest.TestCase):
    def test_standing_pages_have_brand_navigation_and_accessible_search(self):
        for section, filename, canonical in (
            ("tools", "tools.html", "https://davidsdailybread.com/tools.html"),
            ("workflows", "workflows.html", "https://davidsdailybread.com/workflows.html"),
        ):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("Loved by God", text)
                self.assertIn('class="masthead-art" src="/header-art.png"', text)
                self.assertIn(f'<link rel="canonical" href="{canonical}">', text)
                self.assertIn(f'<body data-library-section="{section}">', text)
                self.assertIn('href="/tools.html"', text)
                self.assertIn('href="/workflows.html"', text)
                self.assertIn('id="librarySearch" type="search"', text)
                self.assertIn('id="libraryCount" aria-live="polite"', text)
                self.assertIn('src="/evening-library.js"', text)
                self.assertNotRegex(text, EM_DASH)

    def test_library_renderer_uses_safe_dom_and_credential_free_fetch(self):
        script = (ROOT / "evening-library.js").read_text(encoding="utf-8")
        self.assertIn('fetch("/evening-catalog.json"', script)
        self.assertIn('credentials: "omit"', script)
        self.assertIn('url.protocol === "https:"', script)
        self.assertIn("!url.username && !url.password", script)
        self.assertIn("textContent", script)
        self.assertNotIn("innerHTML", script)
        self.assertNotRegex(script, EM_DASH)

    def test_catalog_is_bounded_source_linked_and_schema_complete(self):
        catalog = json.loads((ROOT / "evening-catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(1, catalog["version"])
        expected = {
            "tools": {"date", "name", "url", "cost", "kind", "seen", "blurb"},
            "workflows": {"date", "title", "url", "dek", "needs", "time"},
        }
        for section, fields in expected.items():
            items = catalog[section]
            self.assertTrue(items)
            self.assertLessEqual(len(items), 180)
            urls = []
            for item in items:
                self.assertEqual(fields, set(item))
                self.assertRegex(item["date"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(ddb_bake.is_safe_source_url(item["url"]))
                self.assertIsNone(EM_DASH.search(json.dumps(item, ensure_ascii=False)))
                urls.append(item["url"])
            self.assertEqual(len(urls), len(set(urls)))

    def test_rest_entries_are_complete_reviewed_text(self):
        rest = json.loads((ROOT / "evening-rest.json").read_text(encoding="utf-8"))
        self.assertEqual(1, rest["version"])
        self.assertGreaterEqual(len(rest["entries"]), 7)
        for entry in rest["entries"]:
            self.assertEqual({"receive", "reference", "release", "rest"}, set(entry))
            self.assertRegex(entry["reference"], r", KJV$")
            for value in entry.values():
                self.assertIsInstance(value, str)
                self.assertTrue(value.strip())
                self.assertIsNone(EM_DASH.search(value))


if __name__ == "__main__":
    unittest.main()
