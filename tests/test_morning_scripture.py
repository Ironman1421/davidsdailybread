#!/usr/bin/env python3
"""Contract tests for the approved morning-only Scripture pairing."""

import contextlib
import io
import json
from pathlib import Path
import unittest

import ddb_scripture
import ddb_session_bake


ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-01"
SAMPLE_VERSE = (
    "The heart of the discerning acquires knowledge, and the ear of the wise "
    "seeks it out."
)
SAMPLE_CONNECTION = (
    "We can approach new tools with discernment, careful listening, and a "
    "continuing desire to understand."
)


def card(section: str, number: int) -> dict:
    return {
        "title": f"{section} brief {number}",
        "url": f"https://example.com/{section}/{number}",
        "dek": f"<b>Verified detail</b> factual brief number {number}.",
        "scripture": {
            "id": "PRO.18.15",
            "connection": "We can seek knowledge carefully as we consider this story.",
        },
    }


def morning_content() -> dict:
    return {
        "date": DATE,
        "lead": {
            "section": "tech",
            "title": "Libraries Offer Free AI Training for Job Seekers",
            "url": "https://example.com/libraries-ai-training",
            "badge": "Technology",
            "standfirst": "Libraries are helping job seekers use AI responsibly.",
            "body": (
                "Public libraries are testing free workshops that teach job seekers "
                "how to use artificial intelligence responsibly. Participants learn "
                "how to research careers, improve résumés, prepare for interviews, "
                "and recognize inaccurate information."
            ),
            "scripture": {
                "id": "PRO.18.15",
                "connection": SAMPLE_CONNECTION,
            },
        },
        "cards": {
            section: [card(section, 1), card(section, 2)]
            for section in ("tech", "markets", "science")
        },
        "glance": {
            section: f"Two verified {section} stories, in brief."
            for section in ("tech", "markets", "science")
        },
    }


class MorningScriptureTest(unittest.TestCase):
    def assert_rejected(self, content: dict, message: str, slot: str = "morning") -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            ddb_session_bake.validate_content(content, DATE, slot)
        self.assertIn(message, stderr.getvalue())

    def test_catalog_records_verified_public_domain_bsb_source(self):
        raw = json.loads(ddb_scripture.CATALOG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(1, raw["version"])
        self.assertEqual("Berean Standard Bible", raw["translation"]["name"])
        self.assertEqual("BSB", raw["translation"]["label"])
        self.assertEqual("Public domain", raw["translation"]["license"])
        self.assertEqual(
            "https://bereanbible.com/bsb.txt", raw["translation"]["sourceUrl"]
        )
        self.assertEqual(
            "2ac3af1de52d4e68261cba91d85c320b7eadc6560e830d99e591767b8ff5ca96",
            raw["translation"]["sourceSha256"],
        )
        self.assertEqual(81, len(raw["verses"]))
        self.assertEqual(len(raw["verses"]), len({verse["id"] for verse in raw["verses"]}))
        for verse in raw["verses"]:
            self.assertNotIn("—", verse["text"])
            self.assertTrue(verse["url"].startswith("https://www.bible.com/bible/3034/"))

    def test_sample_verse_is_exact_and_renderer_owns_its_words(self):
        verse = ddb_scripture.load_catalog()["byId"]["PRO.18.15"]
        self.assertEqual("Proverbs 18:15", verse["reference"])
        self.assertEqual(SAMPLE_VERSE, verse["text"])
        self.assertEqual(
            "https://www.bible.com/bible/3034/PRO.18.15.BSB", verse["url"]
        )

        content = morning_content()
        ddb_session_bake.validate_content(content, DATE, "morning")
        html, _ = ddb_session_bake.render_home_from_content(
            content, DATE, "morning"
        )

        self.assertEqual(7, html.count('class="scripture-inline"'))
        self.assertIn(
            "News and Scripture each morning. Practical tools each evening. Loved by God.",
            html,
        )
        self.assertNotIn('class="product-rhythm"', html)
        self.assertIn("aspect-ratio: 1124 / 330", html)
        self.assertIn("transform: translateX(3.4%)", html)
        self.assertIn(".story-card a.card-link { height: auto; }", html)
        self.assertIn("Scripture for Reflection", html)
        self.assertIn(f"&ldquo;{SAMPLE_VERSE}&rdquo;", html)
        self.assertIn("Proverbs 18:15 &middot; BSB", html)
        self.assertIn(SAMPLE_CONNECTION, html)
        self.assertIn('target="_blank" rel="noopener noreferrer"', html)
        self.assertIn("opens in a new tab", html)

    def test_morning_requires_an_identifier_and_rejects_authored_verse_fields(self):
        missing = morning_content()
        del missing["lead"]["scripture"]
        self.assert_rejected(missing, "lead.scripture must be an object")

        unknown = morning_content()
        unknown["lead"]["scripture"]["id"] = "PRO.99.99"
        self.assert_rejected(unknown, "not in the verified BSB catalog")

        injected = morning_content()
        injected["lead"]["scripture"]["text"] = "A model-authored paraphrase"
        self.assert_rejected(injected, "may contain only id and connection")

    def test_every_story_requires_a_reader_directed_plain_text_connection(self):
        missing = morning_content()
        del missing["cards"]["tech"][0]["scripture"]
        self.assert_rejected(missing, "must contain only title, url, dek, and scripture")

        immediate = morning_content()
        del immediate["lead"]["scripture"]["connection"]
        self.assert_rejected(immediate, "connection must be a non-empty string")

        markup = morning_content()
        markup["lead"]["scripture"]["connection"] = "<b>Generated emphasis</b>"
        self.assert_rejected(markup, "must be plain text")

        event_directed = morning_content()
        event_directed["lead"]["scripture"]["connection"] = (
            "Discernment gives learning a faithful direction."
        )
        self.assert_rejected(event_directed, "must guide the reader")

        endorsement = morning_content()
        endorsement["cards"]["markets"][0]["scripture"]["connection"] = (
            "God approves this company, so we should support it."
        )
        self.assert_rejected(endorsement, "must not claim divine approval")

    def test_political_and_geopolitical_framing_is_rejected(self):
        partisan = morning_content()
        partisan["lead"]["title"] = "Trump Calls Off Iran Strikes as Oil Retreats"
        self.assert_rejected(partisan, "politics-free morning policy rejects lead.title")

        conflict = morning_content()
        conflict["cards"]["markets"][0]["dek"] = (
            "<b>Oil retreats</b> after a ceasefire changed market expectations."
        )
        self.assert_rejected(conflict, "politics-free morning policy rejects cards.markets[0].dek")

        practical_rule = morning_content()
        practical_rule["cards"]["tech"][0]["title"] = (
            "New Data Rule Changes Small-Business Reporting"
        )
        ddb_session_bake.validate_content(practical_rule, DATE, "morning")

    def test_evening_and_non_story_templates_remain_outside_the_feature(self):
        self.assertNotIn(
            "scripture-inline",
            (ROOT / "templates/evening.html").read_text(encoding="utf-8"),
        )
        category_template = (ROOT / "templates/category.html").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "scripture-inline",
            category_template,
        )
        generic_link_height = ".card a.card-link { display: block;"
        story_link_height = ".story-card a.card-link { height: auto; }"
        self.assertIn(story_link_height, category_template)
        self.assertLess(
            category_template.index(generic_link_height),
            category_template.index(story_link_height),
        )

        evening = {
            "date": DATE,
            "lead": {
                "section": "tools",
                "title": "Fixture tool",
                "url": "https://example.com/tool",
                "trend_url": "https://example.com/trends/lead",
                "seen": "Product Hunt No. 1",
                "badge": "Trending tool",
                "standfirst": "A useful fixture.",
                "body": "A grounded fixture body.",
                "scripture": {"id": "PRO.18.15"},
            },
            "cards": {
                "tools": [
                    {
                        "name": f"Tool {number}",
                        "url": f"https://example.com/tool/{number}",
                        "trend_url": f"https://example.com/trends/tool/{number}",
                        "cost": "Free",
                        "kind": "Web app",
                        "seen": "GitHub trending",
                        "blurb": "A factual fixture with a caveat.",
                    }
                    for number in (1, 2)
                ],
                "workflows": [
                    {
                        "title": f"Workflow {number}",
                        "url": f"https://example.com/workflow/{number}",
                        "trend_url": f"https://example.com/trends/workflow/{number}",
                        "seen": "Hacker News front page",
                        "dek": "<b>Try this</b> grounded factual guidance.",
                        "needs": ["One thing", "Another thing"],
                        "time": "Thirty minutes",
                    }
                    for number in (1, 2)
                ],
            },
            "glance": {
                "tools": "Two useful tools.",
                "workflows": "Two practical workflows.",
            },
        }
        self.assert_rejected(evening, "evening lead must not contain scripture", "evening")

        del evening["lead"]["scripture"]
        august_3_html, _ = ddb_session_bake.render_evening_from_content(
            evening, "2026-08-03"
        )
        august_4_html, _ = ddb_session_bake.render_evening_from_content(
            evening, "2026-08-04"
        )
        subtitle = (
            "News and Scripture each morning. Practical tools each evening. "
            "Loved by God."
        )
        self.assertNotIn(subtitle, august_3_html)
        self.assertNotIn('class="masthead next-format"', august_3_html)
        self.assertIn(subtitle, august_4_html)
        self.assertIn('class="masthead next-format"', august_4_html)

    def test_catalog_search_returns_exact_candidates_without_authoring_text(self):
        result = ddb_scripture.search_catalog("knowledge discernment learning")
        self.assertEqual("BSB", result["label"])
        self.assertEqual("PRO.18.15", result["matches"][0]["id"])
        self.assertEqual(SAMPLE_VERSE, result["matches"][0]["text"])


if __name__ == "__main__":
    unittest.main()
