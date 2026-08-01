#!/usr/bin/env python3
"""Regression tests for the Daily bake changed-file trust boundary."""

from pathlib import Path
import hashlib
import unittest

from ddb_workflow_guard import Change, GuardError, validate_changes


ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-01"
EXPECTED = f"editions/{DATE}-morning.html"


class WorkflowGuardTest(unittest.TestCase):
    def test_accepts_only_the_exact_new_edition_and_slot_files(self):
        paths = validate_changes(
            [
                Change(" M", "index.html"),
                Change(" M", "archive.json"),
                Change("??", EXPECTED),
            ],
            DATE,
            "morning",
        )
        self.assertEqual(["archive.json", EXPECTED, "index.html"], paths)

    def test_rejects_tampered_or_deleted_historical_edition(self):
        for status in (" M", " D", "D ", "M "):
            with self.subTest(status=status), self.assertRaises(GuardError):
                validate_changes(
                    [
                        Change("??", EXPECTED),
                        Change(status, "editions/2098-12-31-evening.html"),
                    ],
                    DATE,
                    "morning",
                )

    def test_rejects_staged_deleted_renamed_or_missing_expected_output(self):
        invalid_sets = (
            [Change("A ", EXPECTED)],
            [Change(" D", "index.html"), Change("??", EXPECTED)],
            [Change("R ", "index.html"), Change("??", EXPECTED)],
            [Change(" M", "index.html")],
        )
        for changes in invalid_sets:
            with self.subTest(changes=changes), self.assertRaises(GuardError):
                validate_changes(changes, DATE, "morning")

    def test_workflow_pins_guard_bytes_and_stages_no_editions_directory(self):
        guard = ROOT / "ddb_workflow_guard.py"
        digest = hashlib.sha256(guard.read_bytes()).hexdigest()
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"{digest}  ddb_workflow_guard.py", workflow)
        self.assertIn('git add "$EXPECTED_EDITION"', workflow)
        self.assertNotIn(
            "git add index.html tech.html markets.html science.html editions ",
            workflow,
        )

    def test_installer_artifact_stays_outside_the_checkout(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('--pack-destination "$RUNNER_TEMP"', workflow)
        self.assertIn('package_path="${RUNNER_TEMP}/${package}"', workflow)
        self.assertIn('npm install -g "${package_path}"', workflow)
        self.assertNotIn('npm install -g "./${package}"', workflow)


if __name__ == "__main__":
    unittest.main()
