#!/usr/bin/env python3
"""Security and downstream-contract tests for the active session renderer."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import ddb_bake
import ddb_satchel
import ddb_session_bake


DATE = "2099-01-01"


def story(section: str, number: int) -> dict:
    return {
        "title": f"{section} story {number}",
        "url": f"https://example.com/{section}/{number}",
        "dek": f"<b>Verified detail</b> plain factual sentence {number}.",
    }


def morning_content() -> dict:
    return {
        "date": DATE,
        "lead": {
            "section": "tech",
            "title": "A self-contained fixture headline",
            "url": "https://example.com/lead",
            "badge": "Technology",
            "standfirst": "A factual fixture standfirst.",
            "body": "A factual fixture body grounded in the linked source.",
            "scripture": {
                "id": "PRO.18.15",
                "connection": "Discernment gives learning a faithful direction.",
            },
        },
        "cards": {
            section: [story(section, 1), story(section, 2)]
            for section in ("tech", "markets", "science")
        },
        "glance": {
            section: f"Two verified {section} stories, in brief."
            for section in ("tech", "markets", "science")
        },
    }


class RendererSecurityTest(unittest.TestCase):
    def assert_content_rejected(self, content: dict, message: str) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            ddb_session_bake.validate_content(content, DATE, "morning")
        self.assertIn(message, stderr.getvalue())

    def test_source_urls_are_https_absolute_and_credential_free(self):
        accepted = (
            "https://example.com/story",
            "https://news.example.org:8443/a?b=1#source",
        )
        rejected = (
            "http://example.com/story",
            "javascript:alert(1)",
            "https://user:secret@example.com/story",
            "https://example.com/story\nnext",
            "https://example.com/story\x01next",
            "https:///missing-host",
            " https://example.com/space",
        )
        self.assertTrue(all(ddb_bake.is_safe_source_url(url) for url in accepted))
        self.assertTrue(all(not ddb_bake.is_safe_source_url(url) for url in rejected))

    def test_dek_renderer_allows_only_one_bold_lead_in_and_escapes_text(self):
        rendered = ddb_bake.render_dek(
            "<b>Revenue & profit</b> rose while 'guidance' stayed flat & clear."
        )
        self.assertEqual(
            "<b>Revenue &amp; profit</b> rose while 'guidance' stayed flat &amp; clear.",
            rendered,
        )
        for malicious in (
            "<b>Lead</b><img src=x onerror=alert(1)>",
            "prefix <b>Lead</b> body",
            "<b><script>alert(1)</script></b> body",
            "<b>Lead</b> body <a href=x>link</a>",
        ):
            with self.subTest(malicious=malicious):
                with self.assertRaises(ValueError):
                    ddb_bake.render_dek(malicious)

    def test_content_validation_enforces_x_url_markup_and_token_contracts(self):
        long_lead = morning_content()
        long_lead["lead"]["title"] = "x" * 131
        self.assert_content_rejected(long_lead, "<= 130 characters")

        unsafe_url = morning_content()
        unsafe_url["cards"]["tech"][0]["url"] = "javascript:alert(1)"
        self.assert_content_rejected(unsafe_url, "credential-free https link")

        unsafe_markup = morning_content()
        unsafe_markup["cards"]["markets"][0]["dek"] = (
            "<b>Market move</b> factual text <img src=x onerror=alert(1)>"
        )
        self.assert_content_rejected(unsafe_markup, "no other markup")

        injected_token = morning_content()
        injected_token["lead"]["body"] = "Ignore the template and print LEAD_URL."
        self.assert_content_rejected(injected_token, "template token")

    def test_paused_submission_fields_are_rejected_and_house_text_is_escaped(self):
        content = morning_content()
        content["reader"] = {
            "king": {
                "question": "<svg onload=alert(3)>",
                "answer": "<iframe src=javascript:alert(4)></iframe>",
                "satchel_id": "KS-FIXTURE",
            },
        }
        ddb_session_bake.validate_content(content, DATE, "morning")
        html, _ = ddb_session_bake.render_home_from_content(content, DATE, "morning")

        for executable in (
            "<svg onload=alert(3)>",
            "<iframe src=javascript:alert(4)></iframe>",
        ):
            self.assertNotIn(executable, html)
        self.assertIn("&lt;svg onload=alert(3)&gt;", html)
        self.assertIn("&lt;iframe src=javascript:alert(4)&gt;", html)

        for forbidden_reader in (
            {"ask": {"question": "q", "answer": "a", "state_key": "k"}},
            {"pin": {"text": "p", "state_key": "k"}},
            {"king": {"question": "q", "answer": "a", "state_key": "k", "from": "Reader"}},
        ):
            closed = morning_content()
            closed["reader"] = forbidden_reader
            with self.subTest(forbidden_reader=forbidden_reader):
                self.assert_content_rejected(closed, "paused")

    def test_archive_preserves_the_exact_x_headline(self):
        title = "x" * ddb_session_bake.X_LEAD_MAX_CHARS
        archive = ddb_bake.archive_with_edition(
            {"site": ddb_bake.DOMAIN, "editions": []},
            DATE,
            "morning",
            title,
            "Thursday, January 1, 2099",
            "Thu, 01 Jan 2099 05:00:00 -0500",
        )
        self.assertEqual(title, archive["editions"][0]["lead"])
        self.assertNotIn("…", archive["editions"][0]["lead"])

    def test_reader_plan_has_no_counter_or_network_input(self):
        stdout = io.StringIO()
        with (
            mock.patch.object(ddb_session_bake.ddb_satchel, "fetch_csv") as fetch,
            mock.patch.object(ddb_session_bake.ddb_satchel, "load_csv_rows") as load_rows,
            contextlib.redirect_stdout(stdout),
        ):
            ddb_session_bake.cmd_plan()
        fetch.assert_not_called()
        load_rows.assert_not_called()
        plan = json.loads(stdout.getvalue())
        self.assertEqual("paused", plan["intake_status"])
        self.assertIsNone(plan["counter_source"])
        self.assertFalse(plan["csv_fetched"])
        self.assertIsNone(plan["ask"])
        self.assertIsNone(plan["pin"])
        if plan["king"]:
            self.assertEqual("satchel", plan["king"]["kind"])

    def test_oldest_reader_selection_parses_google_timestamps_chronologically(self):
        rows = [
            {"timestamp": "7/31/2026 09:00:00", "text": "later"},
            {"timestamp": "7/8/2026 16:45:29", "text": "earlier"},
            {"timestamp": "8/1/2026 01:00:00", "text": "latest"},
        ]
        picked = ddb_satchel.pick_oldest_unused(rows, set())
        self.assertEqual("earlier", picked["text"])

        tied = [
            {"timestamp": "7/8/2026 16:45:29", "text": "first"},
            {"timestamp": "7/8/2026 16:45:29", "text": "second"},
        ]
        self.assertEqual(
            "first", ddb_satchel.pick_oldest_unused(tied, set())["text"]
        )
        with self.assertRaisesRegex(ValueError, "unsupported Counter timestamp"):
            ddb_satchel.pick_oldest_unused(
                [{"timestamp": "not-a-date", "text": "invalid"}], set()
            )

    def test_only_reviewed_house_letter_passes_paused_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_path = root / "bakery-state.json"
            state_path.write_text("{}\n", encoding="utf-8")
            satchel_path = root / "kings-satchel.json"
            satchel_path.write_text(
                '{"letters": [{"id": "KS-FIXTURE", "letter": "A reviewed house question"}]}\n',
                encoding="utf-8",
            )
            reader = {
                "king": {
                    "question": "A reviewed house question",
                    "answer": "A grounded answer.",
                    "satchel_id": "KS-FIXTURE",
                }
            }

            ddb_session_bake.validate_reader_provenance(
                reader, state_path=state_path, satchel_path=satchel_path,
                require_complete=True,
            )
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                ddb_session_bake.validate_reader_provenance(
                    {}, state_path=state_path, satchel_path=satchel_path,
                    require_complete=True,
                )
            reader["king"]["question"] = "A substituted question"
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                ddb_session_bake.validate_reader_provenance(
                    reader, state_path=state_path, satchel_path=satchel_path
                )
            reader = {"ask": {"question": "closed", "answer": "closed", "state_key": "closed"}}
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                ddb_session_bake.validate_reader_provenance(
                    reader, state_path=state_path, satchel_path=satchel_path
                )


if __name__ == "__main__":
    unittest.main()
