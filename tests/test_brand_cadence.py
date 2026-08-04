#!/usr/bin/env python3
"""Regression tests for David's current brand statement and honest cadence copy.

Cadence truth since 2026-07-30: baked twice daily (morning news edition +
evening trends edition). The obsolete promises below are the RETIRED
single-morning-cadence claims from the 2026-07-17..07-29 era.
"""

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
    ROOT / "BAKE.md",
    ROOT / "ddb_bake.py",
    ROOT / "ddb_synth.py",
    ROOT / "templates" / "home.html",
    ROOT / "templates" / "evening.html",
    ROOT / "templates" / "category.html",
)

# These identify RETIRED active delivery promises, not historical edition
# labels. Since 2026-07-30 the site is honestly baked twice daily again
# (morning news + evening trends), so the obsolete claims are the
# one-morning-edition-only promises of the 2026-07-17..07-29 era.
OBSOLETE_PROMISES = (
    re.compile(r"\bno evening edition\b", re.IGNORECASE),
    re.compile(r"\bone edition each morning\b", re.IGNORECASE),
    re.compile(r"\bovens still fire every morning\b", re.IGNORECASE),
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
        # Truth since 2026-07-30 (per David): baked TWICE daily by GitHub
        # Actions: the morning news edition (reviewed house-satchel material
        # only while public intake is paused) and the evening trends edition
        # (trending / new tools / workflows, no reader sections). Newsletter
        # signup and activation are paused.
        brand = (ROOT / "BRAND.md").read_text(encoding="utf-8")
        self.assertIn("twice daily", brand.lower())
        self.assertIn("evening edition", brand.lower())

        subscribe = (ROOT / "subscribe.html").read_text(encoding="utf-8")
        self.assertIn(BRAND, subscribe)
        self.assertIn("Newsletter signup, activation, and sending are paused", subscribe)
        self.assertIn("No new addresses are being collected", subscribe)
        self.assertNotIn("<form", subscribe.lower())
        self.assertNotIn("buttondown", subscribe.lower())
        self.assertNotIn("Evening delivery is in testing", subscribe)
        self.assertNotIn("newsletter has been retired", subscribe.lower())

        chronicles = (ROOT / "chronicles.html").read_text(encoding="utf-8")
        self.assertIn(BRAND, chronicles)
        self.assertIn("Reader slips are resting", chronicles)
        self.assertIn("all four export options still work", chronicles)
        self.assertNotIn("formResponse", chronicles)
        self.assertNotIn("Evening delivery is in testing", chronicles)

        evening_template = (ROOT / "templates" / "evening.html").read_text(encoding="utf-8")
        self.assertIn(BRAND, evening_template)
        for kicker in ("Reader questions", "Letters to the King", "Crumb Board"):
            self.assertNotIn(kicker, evening_template)

        # Historical labels stay: past evening editions remain in the archive.
        archive = (ROOT / "archive.html").read_text(encoding="utf-8")
        self.assertIn("Evening</span>", archive)
        self.assertIn('href="/subscribe.html">Email paused</a>', archive)

    def test_letters_to_the_king_identifies_the_biblical_david(self):
        home = (ROOT / "templates" / "home.html").read_text(encoding="utf-8")
        brand = (ROOT / "BRAND.md").read_text(encoding="utf-8")

        self.assertIn("&ndash; David, son of Jesse", home)
        self.assertIn(
            "Letters answered in the voice of the biblical King David.", home
        )
        self.assertNotIn("David, King in Jerusalem", home)
        self.assertIn("– David, son of Jesse", brand)


if __name__ == "__main__":
    unittest.main()
