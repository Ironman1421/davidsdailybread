#!/usr/bin/env python3
"""Regression coverage for Chronicles masthead and note-metadata boundaries."""

from pathlib import Path
import json
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SUBTITLE = (
    "News and Scripture each morning. Practical tools each evening. Loved by God."
)
EXPORT_CONTROLS = ("downloadBtn", "pdfBtn", "emailBtn", "copyBtn")


def css_rule(text: str, selector: str) -> str:
    match = re.search(
        rf"(?m)^\s*{re.escape(selector)}\s*\{{([^}}]+)\}}", text
    )
    if not match:
        raise AssertionError(f"missing CSS selector: {selector}")
    return " ".join(match.group(1).split())


class ChroniclesMetadataTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.chronicles = (ROOT / "chronicles.html").read_text(encoding="utf-8")

    def test_chronicles_masthead_matches_current_cropped_treatment(self):
        home = (ROOT / "templates" / "home.html").read_text(encoding="utf-8")
        for selector in (
            ".masthead-art-link",
            ".masthead-art",
            ".format-line",
            ".tagline",
        ):
            with self.subTest(selector=selector):
                self.assertEqual(
                    css_rule(home, selector), css_rule(self.chronicles, selector)
                )
        for declaration in (
            "max-width: 640px",
            "aspect-ratio: 1124 / 330",
            "overflow: hidden",
            "transform: translateX(3.4%)",
        ):
            with self.subTest(declaration=declaration):
                self.assertIn(declaration, home)
                self.assertIn(declaration, self.chronicles)
        self.assertIn(
            '<img class="masthead-art" src="/header-art.png"', self.chronicles
        )
        self.assertEqual(1, self.chronicles.count(SUBTITLE))

    def test_archive_and_subscribe_use_separate_style_namespace(self):
        for name in ("archive.html", "subscribe.html"):
            page = (ROOT / name).read_text(encoding="utf-8")
            slug = Path(name).stem
            with self.subTest(page=name):
                self.assertIn(
                    f"var fontKey = 'ddb-note-style:page:{slug}';", page
                )
                self.assertIn("var legacyFontKey = key + ':font';", page)
                self.assertNotIn("var fontKey = key + ':font';", page)

    def test_chronicles_excludes_legacy_font_metadata_and_preserves_notes(self):
        collection = self.chronicles.split("// 1. Collect notes from localStorage", 1)[
            1
        ].split("// Stories first, page notes last.", 1)[0]
        self.assertIn("LEGACY_FONT_SUFFIX", collection)
        self.assertIn("ddb-note-style:", collection)
        self.assertIn("LEGACY_FONT_KEYS[raw] && FONT_NAMES[val]", collection)
        self.assertIn("localStorage.setItem(styleKey, val)", collection)
        self.assertNotIn("localStorage.removeItem", collection)
        self.assertRegex(
            collection,
            re.compile(
                r"if \(val && val\.trim\(\)\) \{ notes\.push\(\{ key: raw, text: val \}\); \}"
            ),
        )

    def test_collection_migrates_only_known_font_values_without_mutation(self):
        collection = self.chronicles.split("// 1. Collect notes from localStorage", 1)[
            1
        ].split("// Stories first, page notes last.", 1)[0]
        initial = {
            "ddb-note:page:archive": "A genuine archive reflection",
            "ddb-note:page:archive:font": "serif",
            "ddb-note:https://example.com/story:font": "hand",
            "ddb-note:page:subscribe:font": "hand",
            "ddb-note-style:page:subscribe": "sans",
        }
        program = f"""
const values = new Map(Object.entries({json.dumps(initial)}));
const localStorage = {{
  get length() {{ return values.size; }},
  key(index) {{ return Array.from(values.keys())[index] || null; }},
  getItem(key) {{ return values.has(key) ? values.get(key) : null; }},
  setItem(key, value) {{ values.set(key, String(value)); }},
  removeItem(key) {{ values.delete(key); }}
}};
var PREFIX = 'ddb-note:';
var LEGACY_FONT_SUFFIX = ':font';
var LEGACY_FONT_KEYS = {{
  'page:home:font': true, 'page:tech:font': true, 'page:markets:font': true,
  'page:science:font': true, 'page:archive:font': true,
  'page:subscribe:font': true, 'page:offline:font': true
}};
var FONT_NAMES = {{ hand: true, serif: true, sans: true }};
{collection}
process.stdout.write(JSON.stringify({{ notes, storage: Object.fromEntries(values) }}));
"""
        result = subprocess.run(
            ["node", "-e", program],
            check=True,
            capture_output=True,
            text=True,
        )
        observed = json.loads(result.stdout)

        self.assertEqual(
            [
                {
                    "key": "page:archive",
                    "text": "A genuine archive reflection",
                },
                {
                    "key": "https://example.com/story:font",
                    "text": "hand",
                },
            ],
            observed["notes"],
        )
        self.assertEqual(
            "serif", observed["storage"]["ddb-note-style:page:archive"]
        )
        self.assertEqual(
            "sans", observed["storage"]["ddb-note-style:page:subscribe"]
        )
        for key, value in initial.items():
            with self.subTest(key=key):
                self.assertEqual(value, observed["storage"][key])

    def test_all_four_exports_and_their_behaviors_remain(self):
        for control_id in EXPORT_CONTROLS:
            with self.subTest(control=control_id):
                self.assertEqual(1, self.chronicles.count(f'id="{control_id}"'))
        for control_id in ("downloadBtn", "pdfBtn", "copyBtn"):
            self.assertIn(f"{control_id}.addEventListener", self.chronicles)
        for behavior in (
            "text/markdown;charset=utf-8",
            "window.jspdf.jsPDF",
            "navigator.clipboard.writeText",
            "mailto:?subject=",
        ):
            with self.subTest(behavior=behavior):
                self.assertIn(behavior, self.chronicles)


if __name__ == "__main__":
    unittest.main()
