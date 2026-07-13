#!/usr/bin/env python3
"""Regression tests for David's current brand statement and honest cadence copy."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

import ddb_bake

ROOT = Path(__file__).resolve().parents[1]
BRAND = "Loved by God"
CANONICAL_SOURCES = (
    ROOT / "README.md",
    ROOT / "BRAND.md",
    ROOT / "ddb_bake.py",
    ROOT / "ddb_synth.py",
    ROOT / "templates" / "home.html",
    ROOT / "templates" / "category.html",
)

# These identify active delivery promises, not historical edition labels. In
# particular, "Evening edition" and honest evening testing/preference language
# remain valid.
OBSOLETE_PROMISES = (
    re.compile(r"\btwice[\s-]+daily\b", re.IGNORECASE),
    re.compile(
        r"\b(?:every|each)\s+morning(?:[^.\n<]{0,80})?\band evening\b",
        re.IGNORECASE,
    ),
)


class DescriptionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.descriptions: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        values = {name.lower(): (value or "") for name, value in attrs}
        surface = values.get("name", "").lower() or values.get("property", "").lower()
        if surface in ("description", "og:description"):
            self.descriptions.append((surface, values.get("content", "")))


def public_html_pages() -> list[Path]:
    return sorted(ROOT.glob("*.html")) + sorted((ROOT / "editions").glob("*.html"))


def assert_no_obsolete(test: unittest.TestCase, path: Path, text: str) -> None:
    for promise in OBSOLETE_PROMISES:
        match = promise.search(text)
        test.assertIsNone(
            match,
            (
                f"{path.relative_to(ROOT)} retains obsolete active cadence promise: "
                f"{match.group(0)!r}"
            )
            if match
            else "",
        )


class BrandCadenceTest(unittest.TestCase):
    maxDiff = None

    def test_every_public_html_description_uses_exact_brand_statement(self):
        pages = public_html_pages()
        self.assertTrue(pages)
        failures = []
        for page in pages:
            text = page.read_text(encoding="utf-8")
            assert_no_obsolete(self, page, text)
            parser = DescriptionParser()
            parser.feed(text)
            if not parser.descriptions:
                failures.append(f"{page.relative_to(ROOT)}: no description metadata")
                continue
            for surface, description in parser.descriptions:
                if BRAND not in description:
                    failures.append(
                        f"{page.relative_to(ROOT)}:{surface}: missing {BRAND!r}: "
                        f"{description!r}"
                    )
                if "loved by god" in description.lower() and BRAND not in description:
                    failures.append(
                        f"{page.relative_to(ROOT)}:{surface}: wrong capitalization"
                    )
                if re.search(r"\b(?:a|an)\s+loved by god\b", description, re.IGNORECASE):
                    failures.append(
                        f"{page.relative_to(ROOT)}:{surface}: awkward brand grammar"
                    )
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_feed_description_uses_brand_and_retains_historical_edition_labels(self):
        feed_path = ROOT / "feed.xml"
        text = feed_path.read_text(encoding="utf-8")
        assert_no_obsolete(self, feed_path, text)
        channel = ET.fromstring(text).find("channel")
        self.assertIsNotNone(channel)
        assert channel is not None
        description = channel.findtext("description", "")
        self.assertIn(BRAND, description)
        item_titles = [item.findtext("title", "") for item in channel.findall("item")]
        self.assertTrue(any("Morning edition" in title for title in item_titles))
        self.assertTrue(any("Evening edition" in title for title in item_titles))

    def test_canonical_generators_templates_docs_and_house_style_are_current(self):
        for path in CANONICAL_SOURCES:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                assert_no_obsolete(self, path, text)
                self.assertIn(BRAND, text)

        archive = ddb_bake.read_archive_json(ROOT / "archive.json")
        current_archive = (ROOT / "archive.html").read_text(encoding="utf-8")
        rendered_archive = ddb_bake.update_archive_html(current_archive, archive)
        rendered_feed = ddb_bake.render_feed_xml(archive)
        self.assertIn(BRAND, rendered_archive)
        self.assertIn(BRAND, rendered_feed)
        for pattern in OBSOLETE_PROMISES:
            self.assertNotRegex(rendered_archive, pattern)
            self.assertNotRegex(rendered_feed, pattern)

    def test_current_operating_truth_is_explicit_without_erasing_history(self):
        subscribe = (ROOT / "subscribe.html").read_text(encoding="utf-8")
        self.assertIn(BRAND, subscribe)
        self.assertIn("One edition each morning", subscribe)
        self.assertIn("Evening delivery is in testing", subscribe)
        self.assertIn("future preference", subscribe)

        chronicles = (ROOT / "chronicles.html").read_text(encoding="utf-8")
        self.assertIn(BRAND, chronicles)
        self.assertIn("one morning edition", chronicles.lower())
        self.assertIn("evening", chronicles.lower())
        self.assertIn("testing", chronicles.lower())
        self.assertIn("4:45 AM", chronicles)

        archive = (ROOT / "archive.html").read_text(encoding="utf-8")
        self.assertIn("Evening</span>", archive)


if __name__ == "__main__":
    unittest.main()
