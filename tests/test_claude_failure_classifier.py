#!/usr/bin/env python3
"""Regression tests for payload-free Claude CLI failure classification."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ddb_claude_failure_classifier import classify_file, classify_text


ROOT = Path(__file__).resolve().parents[1]
CLASSIFIER = ROOT / "ddb_claude_failure_classifier.py"
WORKFLOW = ROOT / ".github" / "workflows" / "ddb-bake.yml"


class ClaudeFailureClassifierTest(unittest.TestCase):
    def test_strict_signatures_map_to_controlled_categories(self):
        cases = {
            "authentication_error: OAuth token expired": "authentication",
            "credit balance is too low": "billing_or_quota",
            "rate_limit_error: too many requests": "rate_limit",
            "permission_error: model claude-opus-5 not available": "authorization_or_model_access",
            "invalid_request_error: prompt is too long": "request_rejected",
            "overloaded_error: service unavailable": "provider_unavailable",
            "request failed with ECONNRESET": "network",
            "unknown option --unsafe-example": "cli_configuration",
            "editor stopped before producing content": "unknown",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(expected, classify_text(raw))

    def test_cli_emits_only_the_category_and_never_raw_input(self):
        marker = "SECRET_TOKEN_AND_UNPUBLISHED_MODEL_OUTPUT"
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "bake.log"
            log.write_text(
                f"{marker}\nrate_limit_error: too many requests\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(CLASSIFIER), str(log)],
                text=True,
                capture_output=True,
                check=True,
            )
        self.assertEqual("rate_limit\n", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertNotIn(marker, completed.stdout)

    def test_missing_input_fails_closed_without_path_disclosure(self):
        missing = Path("/private/SECRET_VALUE/does-not-exist.log")
        self.assertEqual("classifier_error", classify_file(missing))
        completed = subprocess.run(
            [sys.executable, str(CLASSIFIER), str(missing)],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual("classifier_error\n", completed.stdout)
        self.assertEqual("", completed.stderr)
        self.assertNotIn(str(missing), completed.stdout + completed.stderr)

    def test_workflow_pins_classifier_and_uploads_only_controlled_result(self):
        import hashlib

        workflow = WORKFLOW.read_text(encoding="utf-8")
        digest = hashlib.sha256(CLASSIFIER.read_bytes()).hexdigest()
        author = workflow.split("\n  author-edition:\n", 1)[1].split(
            "\n  validate-and-publish:\n", 1
        )[0]
        upload = author.split("- name: Upload failure diagnostics", 1)[1]

        self.assertIn(f"{digest}  ddb_claude_failure_classifier.py", author)
        self.assertIn("bake-failure-classification.json", upload)
        self.assertNotIn("bake-log.txt", upload)
        self.assertNotIn("content.json\n", upload)
        self.assertIn('rm -f "$RUNNER_TEMP/bake-log.txt"', author)
        self.assertIn("raw model output is withheld", author)


if __name__ == "__main__":
    unittest.main()
