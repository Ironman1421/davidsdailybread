#!/usr/bin/env python3
"""Regression gates for paused public intake and newsletter activation."""

from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
import unittest

import ddb_satchel


ROOT = Path(__file__).resolve().parents[1]
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
ENDPOINT_PATTERNS = {
    "HTML form": re.compile(r"<form\b", re.IGNORECASE),
    "Google Form": re.compile(r"docs\.google\.com/forms|formResponse", re.IGNORECASE),
    "Google Sheet": re.compile(r"docs\.google\.com/spreadsheets|pub\?output=csv", re.IGNORECASE),
    "Buttondown embed": re.compile(r"buttondown[^\s\"']*embed-subscribe", re.IGNORECASE),
    "GitHub Issue intake": re.compile(
        r"github\.com/[^\s\"']*/issues/new|(?:href|action)=[\"'][^\"']*issues/new",
        re.IGNORECASE,
    ),
}
PUBLISHABLE_TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".svg", ".txt", ".xml"}
NON_READER_ROOTS = {
    ".github",
    "distribution",
    "docs",
    "newsletter",
    "operations",
    "supabase",
    "templates",
    "tests",
    "youtube",
}


def reader_facing_text_surfaces() -> list[Path]:
    paths = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLISHABLE_TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts[0].startswith(".") or relative.parts[0] in NON_READER_ROOTS:
            continue
        paths.append(path)
    return sorted(paths)


def intake_scannable_surfaces() -> list[Path]:
    # Templates are scanned because they generate the next reader-facing
    # edition, even though they are not navigation surfaces themselves.
    return reader_facing_text_surfaces() + sorted((ROOT / "templates").glob("*.html"))


class IntakePauseTest(unittest.TestCase):
    maxDiff = None

    def test_publishable_surfaces_have_zero_submission_endpoints(self):
        failures = []
        for path in intake_scannable_surfaces():
            text = path.read_text(encoding="utf-8")
            for label, pattern in ENDPOINT_PATTERNS.items():
                if pattern.search(text):
                    failures.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual([], failures)

    def test_publishable_output_has_zero_email_addresses(self):
        failures = []
        for path in intake_scannable_surfaces():
            if EMAIL_RE.search(path.read_text(encoding="utf-8")):
                failures.append(str(path.relative_to(ROOT)))
        self.assertEqual([], failures)

    def test_counter_snapshot_is_absent_and_ignored(self):
        self.assertFalse((ROOT / "counter.csv").exists())
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("counter.csv", ignored)
        self.assertIn("counter.csv.new", ignored)

    def test_pages_architecture_is_unchanged_and_boundary_deferral_is_explicit(self):
        self.assertTrue((ROOT / ".nojekyll").exists())
        self.assertFalse((ROOT / "_config.yml").exists())
        contract = json.loads(
            (ROOT / "operations" / "reader-intake-pause.contract.json").read_text(
                encoding="utf-8"
            )
        )
        repository = contract["repository"]
        self.assertFalse(repository["pagesArchitectureChanged"])
        self.assertTrue(repository["internalStateExclusionDeferred"])

    def test_counter_sync_is_a_verifiable_read_only_noop(self):
        workflow = (ROOT / ".github" / "workflows" / "counter-sync.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("name: Counter sync (paused)", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("No reader data was fetched or written", workflow)
        for forbidden in (
            "schedule:",
            "cron:",
            "contents: write",
            "actions/checkout",
            "curl ",
            "wget ",
            "http://",
            "https://",
            "counter.csv",
            "git add",
            "git commit",
            "git push",
            "upload-artifact",
        ):
            self.assertNotIn(forbidden, workflow)
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
            source = path.read_text(encoding="utf-8")
            for intake_source in (
                "counter.csv",
                "docs.google.com/forms",
                "docs.google.com/spreadsheets",
                "formResponse",
                "embed-subscribe",
                "issues/new",
            ):
                self.assertNotIn(intake_source, source, str(path.relative_to(ROOT)))

    def test_legacy_counter_ingestion_fails_closed_without_endpoint(self):
        source = (ROOT / "ddb_satchel.py").read_text(encoding="utf-8")
        session_source = (ROOT / "ddb_session_bake.py").read_text(encoding="utf-8")
        self.assertNotIn("docs.google.com", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("counter.csv", session_source)
        self.assertNotIn("load_csv_rows", session_source)
        self.assertNotIn("fetch_csv", session_source)
        with self.assertRaisesRegex(RuntimeError, "network ingestion is disabled"):
            ddb_satchel.fetch_csv(Path("unused"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, "legacy Counter rendering is disabled"):
                ddb_satchel.fill_reader_sections(Path(tmp), Path(tmp) / "counter.csv")

    def test_closure_pages_preserve_chronicles_exports_without_controls(self):
        chronicles = (ROOT / "chronicles.html").read_text(encoding="utf-8")
        subscribe = (ROOT / "subscribe.html").read_text(encoding="utf-8")
        self.assertIn("Reader slips are resting", chronicles)
        self.assertIn("Newsletter signup, activation, and sending are paused", subscribe)
        for control in ("askBtn", "kingBtn", "pinBtn"):
            self.assertNotIn(f'id="{control}"', chronicles)
        for export_control in ("downloadBtn", "pdfBtn", "emailBtn", "copyBtn"):
            self.assertEqual(1, chronicles.count(f'id="{export_control}"'))
        self.assertNotIn("<form", subscribe.lower())

    def test_future_generated_chrome_states_both_pauses(self):
        templates = sorted((ROOT / "templates").glob("*.html"))
        for path in templates:
            text = path.read_text(encoding="utf-8")
            self.assertIn('href="/subscribe.html">Email paused</a>', text)
            self.assertIn("Your private notes remain on this device", text)
            self.assertNotIn("anything to set down?", text)
        home = (ROOT / "templates" / "home.html").read_text(encoding="utf-8")
        self.assertIn("New pins are temporarily closed", home)
        self.assertNotIn("pinned by readers at", home)

    def test_pause_contract_blocks_every_external_mutation(self):
        contract = json.loads(
            (ROOT / "operations" / "reader-intake-pause.contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("approved-local-change-not-deployed", contract["status"])
        self.assertFalse(contract["deploymentAuthorized"])
        self.assertFalse(contract["deployed"])
        self.assertTrue(all(value is False for value in contract["externalCutover"].values()))
        self.assertFalse(contract["repository"]["counterCsvTrackedAtTip"])
        self.assertTrue(contract["repository"]["counterCsvHistoryPreserved"])
        self.assertFalse(contract["repository"]["counterCsvHistoryRewriteAuthorized"])

    def test_external_checklist_is_prepared_and_entirely_unchecked(self):
        checklist = (ROOT / "docs" / "EXTERNAL_INTAKE_CUTOVER_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        for system in ("## Buttondown", "## Google Form", "## Google Sheet", "## GitHub Issues"):
            self.assertIn(system, checklist)
        self.assertNotRegex(checklist, r"(?im)^- \[[xX]\]")
        self.assertIn("execution is not authorized", checklist)


if __name__ == "__main__":
    unittest.main()
