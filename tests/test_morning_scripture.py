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
    "Learning new tools is valuable when it is accompanied by discernment, "
    "careful listening, and a continuing desire to understand."
)


def card(section: str, number: int) -> dict:
    return {
        "title": f"{section} brief {number}",
        "url": f"https://example.com/{section}/{number}",
        "dek": f"<b>Verified detail</b> factual brief number {number}.",
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

        self.assertEqual(1, html.count('class="scripture-inline"'))
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

    def test_connection_is_optional_plain_text_and_briefs_cannot_receive_pairings(self):
        immediate = morning_content()
        del immediate["lead"]["scripture"]["connection"]
        ddb_session_bake.validate_content(immediate, DATE, "morning")
        html, _ = ddb_session_bake.render_home_from_content(
            immediate, DATE, "morning"
        )
        self.assertNotIn('class="scripture-connection"', html)

        markup = morning_content()
        markup["lead"]["scripture"]["connection"] = "<b>Generated emphasis</b>"
        self.assert_rejected(markup, "must be plain text")

        brief = morning_content()
        brief["cards"]["tech"][0]["scripture"] = {"id": "PRO.18.15"}
        self.assert_rejected(brief, "briefs do not receive Scripture pairings")

    def test_evening_and_non_story_templates_remain_outside_the_feature(self):
        for relative in ("templates/evening.html", "templates/category.html"):
            self.assertNotIn(
                "scripture-inline",
                (ROOT / relative).read_text(encoding="utf-8"),
            )

        evening = {
            "date": DATE,
            "lead": {
                "section": "tools",
                "title": "Fixture tool",
                "url": "https://example.com/tool",
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

    def test_catalog_search_returns_exact_candidates_without_authoring_text(self):
        result = ddb_scripture.search_catalog("knowledge discernment learning")
        self.assertEqual("BSB", result["label"])
        self.assertEqual("PRO.18.15", result["matches"][0]["id"])
        self.assertEqual(SAMPLE_VERSE, result["matches"][0]["text"])


if __name__ == "__main__":
    unittest.main()
