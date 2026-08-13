#!/usr/bin/env python3
"""Regression tests for the Daily bake changed-file trust boundary."""

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
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

    def test_rejected_model_controlled_path_is_not_echoed(self):
        marker = "PRIVATE_READER_PAYLOAD"
        for change in (Change(" M", marker), Change("R ", marker)):
            with self.subTest(change=change), self.assertRaises(GuardError) as raised:
                validate_changes([Change("??", EXPECTED), change], DATE, "morning")
            self.assertNotIn(marker, str(raised.exception))

    def test_evening_accepts_only_its_catalog_and_exact_edition(self):
        expected = f"editions/{DATE}-evening.html"
        paths = validate_changes(
            [
                Change(" M", "index.html"),
                Change(" M", "evening-catalog.json"),
                Change("??", expected),
            ],
            DATE,
            "evening",
        )
        self.assertEqual([expected, "evening-catalog.json", "index.html"], paths)

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
        self.assertIn('git add -- "$path"', workflow)
        self.assertIn('changed-files.txt', workflow)
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

    def test_manual_recovery_can_force_same_day_backfill_safeguards(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("recovery_mode:", workflow)
        self.assertIn("options: [auto, backfill]", workflow)
        self.assertIn("IN_RECOVERY_MODE: ${{ github.event.inputs.recovery_mode }}", workflow)
        self.assertIn('RECOVERY_MODE="${IN_RECOVERY_MODE:-auto}"', workflow)
        self.assertIn('if [ "$EVENT_NAME" != "workflow_dispatch" ]', workflow)
        self.assertIn('MODE=backfill', workflow)
        self.assertIn("mode == 'daily'", workflow)
        self.assertIn('if [ "${MODE}" = "backfill" ]; then', workflow)

    def test_publish_verification_uses_git_ref_and_exact_public_edition(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        verify = workflow.split("- name: Verify the publish", 1)[1].split(
            "\n      - name:", 1
        )[0]

        self.assertIn("git ls-remote --exit-code origin refs/heads/main", verify)
        self.assertIn("https://davidsdailybread.com/editions/${D}-${SLOT}.html", verify)
        self.assertIn("distribution/telegram_notification.py verify-live", verify)
        self.assertIn("--archive archive.json --date \"$D\" --slot \"$SLOT\"", verify)
        self.assertIn('if [ "$remote_sha" != "$published_sha" ]', verify)
        mismatch = verify.split('if [ "$remote_sha" != "$published_sha" ]', 1)[1].split(
            "fi", 1
        )[0]
        self.assertIn("exit 1", mismatch)
        self.assertNotIn("raw.githubusercontent.com", verify)
        self.assertNotIn("sleep 20", verify)

    def test_bake_diagnostics_are_failure_only_and_payload_free(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text(
            encoding="utf-8"
        )
        author = workflow.split("\n  author-edition:\n", 1)[1].split(
            "\n  validate-and-publish:\n", 1
        )[0]
        collect = author.split("- name: Collect failure diagnostics", 1)[1].split(
            "\n      - name:", 1
        )[0]
        upload = author.split("- name: Upload failure diagnostics", 1)[1].split(
            "\n\n  validate-and-publish:", 1
        )[0]

        for step in (collect, upload):
            self.assertIn("if: failure()", step)
        self.assertIn("content-summary.json", collect)
        self.assertNotIn("cp -f content.json", collect)
        self.assertNotIn("bake-log.txt", collect)
        self.assertNotIn('tee "$RUNNER_TEMP/bake-log.txt"', author)
        self.assertNotIn("content.json\n", upload)
        self.assertNotIn("bake-log", upload)

        script = collect.split("<<'PY'\n", 1)[1].rsplit("\n          PY", 1)[0]
        script = textwrap.dedent(script)
        markers = {
            "reader": "PRIVATE_READER_PAYLOAD",
            "model": "UNPUBLISHED_MODEL_COPY",
            "url": "https://secret.example/SENSITIVE_URL",
            "state": "PRIVATE_STATE_KEY",
        }
        content = {
            "date": DATE,
            "lead": {
                "section": "tech",
                "title": markers["model"],
                "url": markers["url"],
                "body": markers["model"],
            },
            "cards": {"tech": [{"title": markers["model"]}]},
            "reader": {
                "ask": {
                    "question": markers["reader"],
                    "state_key": markers["state"],
                }
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "content.json").write_text(json.dumps(content), encoding="utf-8")
            output = root / "content-summary.json"
            env = os.environ.copy()
            env.update({"EDITION_DATE": DATE, "SLOT": "morning", "MODE": "daily"})
            completed = subprocess.run(
                [sys.executable, "-", str(output)],
                input=script,
                text=True,
                cwd=root,
                env=env,
                capture_output=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            serialized = output.read_text(encoding="utf-8")
            for marker in markers.values():
                self.assertNotIn(marker, serialized)
            summary = json.loads(serialized)
            self.assertEqual("valid", summary["contentStatus"])
            self.assertEqual({"tech": 1}, summary["cardCounts"])
            self.assertEqual(["ask"], summary["readerSectionsPresent"])


if __name__ == "__main__":
    unittest.main()
