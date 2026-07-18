#!/usr/bin/env python3
"""Regression tests for targeted archive standing-page regeneration."""

from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

import ddb_bake

ROOT = Path(__file__).resolve().parents[1]


def permanent_feature_failures(html: str) -> list[str]:
    colophon = html.split('<div class="colophon">', 1)[-1].split("</div>", 1)[0]
    checks = {
        "RSS alternate": '<link rel="alternate" type="application/rss+xml"' in html,
        # Newsletter retired 2026-07-17 per David: no subscribe CTA may return.
        "no Buttondown reference": "buttondown" not in html.lower(),
        "no subscribe CTA": 'class="sub-cta"' not in html and 'class="sub-btn"' not in html,
        "colophon RSS": 'href="/feed.xml">RSS</a>' in colophon,
        "page notes localStorage": (
            'data-note-key="page:archive"' in html
            and "ddb-note:page:archive" in html
            and "localStorage" in html
        ),
        "Aa toolbar": '>Aa</button>' in html and 'id="notes-tools"' in html,
    }
    return [name for name, present in checks.items() if not present]


class ArchiveStandingPageTest(unittest.TestCase):
    maxDiff = None

    def test_editions_update_preserves_every_byte_outside_stable_markers(self):
        before = (
            "standing shell before\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            "stale editions\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_END}\n"
            "standing shell after\n"
        )
        archive = {
            "editions": [
                {
                    "dateHuman": "Monday, July 13, 2026",
                    "edition": "morning",
                    "file": "editions/2026-07-13-morning.html",
                    "lead": "A fresh lead",
                }
            ]
        }

        after = ddb_bake.update_archive_html(before, archive)

        expected_list = (
            '<li><span class="when"><a href="editions/2026-07-13-morning.html">Monday, July 13, 2026</a></span>'
            '<span class="ed">Morning</span><span class="lede">A fresh lead</span></li>'
        )
        self.assertEqual(
            before.split(ddb_bake.ARCHIVE_EDITIONS_START, 1)[0],
            after.split(ddb_bake.ARCHIVE_EDITIONS_START, 1)[0],
        )
        self.assertEqual(
            before.split(ddb_bake.ARCHIVE_EDITIONS_END, 1)[1],
            after.split(ddb_bake.ARCHIVE_EDITIONS_END, 1)[1],
        )
        self.assertEqual(
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n{expected_list}\n{ddb_bake.ARCHIVE_EDITIONS_END}",
            after.split("standing shell before\n", 1)[1].split("\nstanding shell after", 1)[0],
        )

    def test_permanent_features_survive_manifest_mutation(self):
        current = (ROOT / "archive.html").read_text(encoding="utf-8")
        mutated_archive = {
            "editions": [
                {
                    "dateHuman": "Monday, July 13, 2026",
                    "edition": "morning",
                    "file": "editions/2026-07-13-morning.html?fresh=1&kind=test",
                    "lead": "Fresh <lead> & a \"quote\"",
                }
            ]
        }

        regenerated = ddb_bake.update_archive_html(current, mutated_archive)

        self.assertIn("Fresh &lt;lead&gt; &amp; a &quot;quote&quot;", regenerated)
        for surface, html in (("current", current), ("regenerated", regenerated)):
            with self.subTest(surface=surface):
                self.assertEqual([], permanent_feature_failures(html))

    def test_missing_marker_fails_closed(self):
        malformed = f"shell\n{ddb_bake.ARCHIVE_EDITIONS_START}\nstale\n"

        with self.assertRaisesRegex(ValueError, "exactly one start and end marker"):
            ddb_bake.update_archive_html(malformed, {"editions": []})

    def test_duplicate_markers_fail_closed(self):
        duplicate_start = (
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_END}"
        )
        duplicate_end = (
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_END}\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_END}"
        )

        for malformed in (duplicate_start, duplicate_end):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "exactly one start and end marker"):
                    ddb_bake.update_archive_html(malformed, {"editions": []})

    def test_reversed_markers_fail_closed(self):
        malformed = (
            f"shell\n{ddb_bake.ARCHIVE_EDITIONS_END}\nstale\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\ntail"
        )

        with self.assertRaisesRegex(ValueError, "start marker must precede end marker"):
            ddb_bake.update_archive_html(malformed, {"editions": []})

    def test_malformed_archive_files_are_not_written(self):
        malformed_pages = {
            "missing": b"standing archive without markers\r\n",
            "duplicate": (
                f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
                f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
                f"{ddb_bake.ARCHIVE_EDITIONS_END}\n"
            ).encode(),
            "reversed": (
                f"{ddb_bake.ARCHIVE_EDITIONS_END}\n"
                f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            ).encode(),
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "archive.html"
            for case, original in malformed_pages.items():
                with self.subTest(case=case):
                    path.write_bytes(original)
                    with self.assertRaises(ValueError):
                        ddb_bake.update_archive_file(path, {"editions": []})
                    self.assertEqual(original, path.read_bytes())

    def test_bake_preflights_archive_markers_before_any_site_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            drafts = root / "drafts"
            site.mkdir()
            drafts.mkdir()
            draft = drafts / "2099-01-02-am.md"
            draft.write_text("fixture draft\n", encoding="utf-8")
            existing = {
                "archive.html": "standing archive with malformed end marker\n",
                "archive.json": json.dumps({"editions": []}) + "\n",
                "feed.xml": "<rss>old</rss>\n",
                "index.html": "old index\n",
                "tech.html": "old tech\n",
                "markets.html": "old markets\n",
                "science.html": "old science\n",
            }
            for name, content in existing.items():
                (site / name).write_text(content, encoding="utf-8")
            before = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            data = {section: [] for section in ddb_bake.SECTIONS}
            meta = {
                "lead_title": "A new lead",
                "ranked_cards": {section: [] for section in ddb_bake.SECTIONS},
            }
            def render_with_state_mutation(*_args, **_kwargs):
                (site / "bakery-state.json").write_text(
                    '{"unexpected":"render side effect"}\n', encoding="utf-8"
                )
                return "new edition", meta

            render_probe = mock.Mock(side_effect=render_with_state_mutation)
            with (
                mock.patch.object(ddb_bake, "SITE", site),
                mock.patch.object(ddb_bake, "EDITIONS", site / "editions"),
                mock.patch.object(ddb_bake, "DRAFTS", drafts),
                mock.patch.object(ddb_bake, "CSV_PATH", root / "missing.csv"),
                mock.patch.object(ddb_bake, "parse_draft", return_value=data),
                mock.patch.object(ddb_bake, "render_home", render_probe),
                mock.patch.object(sys, "argv", ["ddb_bake.py", "--slot", "am", "--date", "2099-01-02"]),
            ):
                with self.assertRaisesRegex(ValueError, "exactly one start and end marker"):
                    ddb_bake.main()
            render_probe.assert_not_called()
            after = {
                path.relative_to(root): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertFalse((site / "editions").exists())

    def test_archive_replacement_is_failure_atomic(self):
        original = (
            "prefix\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_START}\n"
            "old editions\n"
            f"{ddb_bake.ARCHIVE_EDITIONS_END}\n"
            "suffix\n"
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "archive.html"
            path.write_bytes(original)
            real_write_bytes = Path.write_bytes

            def partial_temp_write(target: Path, payload: bytes) -> int:
                if target != path:
                    with target.open("wb") as handle:
                        handle.write(payload[:11])
                    raise OSError("simulated disk full")
                return real_write_bytes(target, payload)

            with mock.patch.object(Path, "write_bytes", new=partial_temp_write):
                with self.assertRaisesRegex(OSError, "simulated disk full"):
                    ddb_bake.update_archive_file(path, {"editions": []})
            self.assertEqual(original, path.read_bytes())
            self.assertEqual([path], list(Path(tmp).iterdir()))

    def test_current_archive_is_byte_coherent_with_manifest(self):
        archive_bytes = (ROOT / "archive.html").read_bytes()
        archive_data = ddb_bake.read_archive_json(ROOT / "archive.json")

        regenerated = ddb_bake.update_archive_html(
            archive_bytes.decode("utf-8"), archive_data
        ).encode("utf-8")

        self.assertEqual(archive_bytes, regenerated)


if __name__ == "__main__":
    unittest.main()
