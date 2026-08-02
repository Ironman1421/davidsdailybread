#!/usr/bin/env python3
"""Acceptance tests for exact daily Telegram publication receipts."""

from __future__ import annotations

import json
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib import error

from distribution.telegram_notification import (
    AmbiguousMutationError,
    DuplicateError,
    HttpResponse,
    LiveReadinessError,
    ReadbackError,
    TelegramProvider,
    ValidationError,
    assert_not_duplicate,
    build_package,
    execute_notification,
    hydrate_github_receipt,
    main,
    verify_live_edition,
    write_reservation,
)


ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-08-02"
EDITION_ID = f"{DATE}-morning"
LEAD = "A verified morning lead from the canonical archive."
EVENING_ID = f"{DATE}-evening"
EVENING_LEAD = "A practical evening path from the canonical archive."


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def state_value(*, cleared: list[str] | None = None) -> dict[str, object]:
    return {
        "clearedRemoteArtifactIds": cleared or [],
        "cutoverAfterEditionId": "2026-08-01-morning",
        "receipts": [],
        "version": 1,
    }


class FakeProvider:
    def __init__(self, package, *, result=None, error=None):
        self.package = package
        self.result = result
        self.error = error
        self.mutation_attempts = 0
        self.sent_text = None

    def send_message(self, text):
        self.mutation_attempts += 1
        self.sent_text = text
        if self.error:
            raise self.error
        return self.result or {
            "message_id": 42,
            "chat": {"id": 123456789},
            "text": self.package.text,
        }


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, url, *, body, headers, timeout, method="POST"):
        self.calls.append((method, url, body, headers, timeout))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class LivePageResponse:
    def __init__(self, status, body):
        self.status = status
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body


class NotificationFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.archive = self.root / "archive.json"
        self.state = self.root / "state.json"
        self.receipts = self.root / "receipts"
        self.attempts = self.root / "attempts"
        self.reservation = self.root / "reservation.json"
        write_json(
            self.archive,
            {
                "editions": [
                    {
                        "date": DATE,
                        "edition": "morning",
                        "file": f"editions/{EDITION_ID}.html",
                        "lead": LEAD,
                    },
                    {
                        "date": DATE,
                        "edition": "evening",
                        "file": f"editions/{EVENING_ID}.html",
                        "lead": EVENING_LEAD,
                    },
                    {
                        "date": "2026-08-01",
                        "edition": "morning",
                        "file": "editions/2026-08-01-morning.html",
                        "lead": "Yesterday's edition must never be substituted.",
                    },
                    {
                        "date": "2026-08-01",
                        "edition": "evening",
                        "file": "editions/2026-08-01-evening.html",
                        "lead": "An exact evening entry after the morning cutover.",
                    },
                ]
            },
        )
        write_json(self.state, state_value())
        self.package = build_package(self.archive, DATE, "morning")
        write_reservation(
            self.package,
            state_path=self.state,
            receipt_dir=self.receipts,
            output_path=self.reservation,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def execute(self, provider, **overrides):
        values = {
            "enabled": True,
            "kill_switch": False,
            "dry_run": False,
            "expected_chat_id": "123456789",
        }
        values.update(overrides)
        return execute_notification(
            self.package,
            state_path=self.state,
            receipt_dir=self.receipts,
            attempt_dir=self.attempts,
            reservation_path=self.reservation,
            provider_factory=lambda: provider,
            **values,
        )


class PackageContractTest(NotificationFixture):
    def test_package_is_exact_and_deterministic(self):
        self.assertEqual(EDITION_ID, self.package.edition_id)
        self.assertEqual(LEAD, self.package.lead)
        self.assertEqual(
            f"https://davidsdailybread.com/editions/{EDITION_ID}.html",
            self.package.canonical_url,
        )
        self.assertIn("Sunday, August 2, 2026 morning edition is live", self.package.text)
        self.assertIn(LEAD, self.package.text)
        self.assertNotIn("Yesterday's edition", self.package.text)
        self.assertIn(f"Open the live edition: {self.package.canonical_url}", self.package.text)
        self.assertEqual(1, self.package.text.count(self.package.canonical_url))
        self.assertEqual("telegram-morning-receipt-v1", self.package.format_id)
        self.assertEqual(
            f"ddb:telegram:morning-receipt:{EDITION_ID}:v1",
            self.package.idempotency_key,
        )

    def test_evening_package_is_exact_and_links_directly_to_the_live_edition(self):
        package = build_package(self.archive, DATE, "evening")
        self.assertEqual(EVENING_ID, package.edition_id)
        self.assertEqual(EVENING_LEAD, package.lead)
        self.assertEqual(
            f"https://davidsdailybread.com/editions/{EVENING_ID}.html",
            package.canonical_url,
        )
        self.assertIn("Sunday, August 2, 2026 evening edition is live", package.text)
        self.assertIn(f"Open the live edition: {package.canonical_url}", package.text)
        self.assertNotIn(LEAD, package.text)
        self.assertEqual("telegram-evening-receipt-v1", package.format_id)
        self.assertEqual(
            f"ddb:telegram:evening-receipt:{EVENING_ID}:v1",
            package.idempotency_key,
        )

    def test_missing_exact_date_never_falls_back_to_latest(self):
        for slot in ("morning", "evening"):
            with self.subTest(slot=slot), self.assertRaises(ValidationError):
                build_package(self.archive, "2026-08-03", slot)

    def test_unknown_slot_fails_closed(self):
        with self.assertRaises(ValidationError):
            build_package(self.archive, DATE, "noon")

    def test_wrong_file_and_duplicate_exact_entry_fail_closed(self):
        value = json.loads(self.archive.read_text())
        value["editions"][0]["file"] = "editions/wrong.html"
        write_json(self.archive, value)
        with self.assertRaises(ValidationError):
            build_package(self.archive, DATE, "morning")

        value["editions"][0]["file"] = f"editions/{EDITION_ID}.html"
        value["editions"].append(dict(value["editions"][0]))
        write_json(self.archive, value)
        with self.assertRaises(ValidationError):
            build_package(self.archive, DATE, "morning")

    def test_cutover_blocks_the_reported_august_first_message(self):
        old = build_package(self.archive, "2026-08-01", "morning")
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(old, self.state, self.receipts)

        evening = build_package(self.archive, "2026-08-01", "evening")
        assert_not_duplicate(evening, self.state, self.receipts)

    def test_current_archive_contains_the_exact_august_first_edition(self):
        current = build_package(ROOT / "archive.json", "2026-08-01", "morning")
        self.assertEqual("2026-08-01-morning", current.edition_id)

    def test_live_readiness_requires_the_exact_public_edition_title(self):
        expected = (
            "<title>David's Daily Bread – Morning edition, "
            "Sunday, August 2, 2026</title>"
        ).encode()
        calls = []

        def opener(req, timeout):
            calls.append((req.full_url, timeout))
            return LivePageResponse(200, expected)

        verify_live_edition(self.package, opener=opener, sleeper=lambda _delay: None)
        self.assertEqual([(self.package.canonical_url, 10)], calls)

    def test_live_readiness_retries_without_creating_a_delivery_receipt(self):
        responses = [
            LivePageResponse(404, b"not found"),
            LivePageResponse(200, b"wrong edition"),
        ]
        delays = []

        def opener(_req, timeout):
            self.assertEqual(10, timeout)
            return responses.pop(0)

        with self.assertRaises(LiveReadinessError):
            verify_live_edition(
                self.package,
                attempts=2,
                delay_seconds=3,
                opener=opener,
                sleeper=delays.append,
            )
        self.assertEqual([3], delays)
        self.assertFalse(self.receipts.exists())

    def test_live_readiness_reports_an_http_error_truthfully(self):
        def opener(req, timeout):
            self.assertEqual(10, timeout)
            raise error.HTTPError(
                req.full_url,
                404,
                "Not Found",
                {},
                io.BytesIO(b"not found"),
            )

        with self.assertRaisesRegex(LiveReadinessError, "HTTP 404"):
            verify_live_edition(
                self.package,
                attempts=1,
                opener=opener,
                sleeper=lambda _delay: None,
            )


class ExecutionTest(NotificationFixture):
    def test_success_requires_provider_readback_and_writes_receipt(self):
        provider = FakeProvider(self.package)
        self.assertEqual("sent", self.execute(provider))
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        attempt = json.loads((self.attempts / f"{EDITION_ID}-attempt.json").read_text())
        self.assertEqual("sent", receipt["status"])
        self.assertEqual(42, receipt["providerMessageId"])
        self.assertEqual(1, attempt["mutationAttempts"])
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(self.package, self.state, self.receipts)

    def test_evening_success_uses_its_own_receipt_and_direct_link(self):
        package = build_package(self.archive, DATE, "evening")
        receipts = self.root / "evening-receipts"
        attempts = self.root / "evening-attempts"
        reservation = self.root / "evening-reservation.json"
        write_reservation(
            package,
            state_path=self.state,
            receipt_dir=receipts,
            output_path=reservation,
        )
        provider = FakeProvider(package)
        status = execute_notification(
            package,
            state_path=self.state,
            receipt_dir=receipts,
            attempt_dir=attempts,
            reservation_path=reservation,
            enabled=True,
            kill_switch=False,
            dry_run=False,
            expected_chat_id="123456789",
            provider_factory=lambda: provider,
        )
        self.assertEqual("sent", status)
        receipt = json.loads((receipts / f"{EVENING_ID}.json").read_text())
        self.assertEqual("sent", receipt["status"])
        self.assertIn(package.canonical_url, provider.sent_text)

    def test_kill_disabled_and_dry_run_never_construct_provider(self):
        for expected, overrides in (
            ("skipped_kill_switch", {"kill_switch": True}),
            ("skipped_disabled", {"enabled": False}),
            ("dry_run", {"enabled": False, "dry_run": True}),
        ):
            with self.subTest(expected=expected):
                constructed = []
                status = execute_notification(
                    self.package,
                    state_path=self.state,
                    receipt_dir=self.root / expected / "receipts",
                    attempt_dir=self.root / expected / "attempts",
                    reservation_path=self.root / "missing.json",
                    enabled=overrides.get("enabled", True),
                    kill_switch=overrides.get("kill_switch", False),
                    dry_run=overrides.get("dry_run", False),
                    expected_chat_id="",
                    provider_factory=lambda: constructed.append(True),
                )
                self.assertEqual(expected, status)
                self.assertEqual([], constructed)

    def test_ambiguous_response_writes_block_and_is_not_retried(self):
        provider = FakeProvider(
            self.package,
            error=AmbiguousMutationError("delivery is unknown"),
        )
        with self.assertRaises(AmbiguousMutationError):
            self.execute(provider)
        self.assertEqual(1, provider.mutation_attempts)
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("needs_reconciliation", receipt["status"])

    def test_wrong_chat_or_text_blocks_reconciliation(self):
        for result in (
            {"message_id": 9, "chat": {"id": 999999999}, "text": self.package.text},
            {"message_id": 9, "chat": {"id": 123456789}, "text": "wrong"},
        ):
            with self.subTest(result=result):
                receipts = self.root / f"mismatch-{result['chat']['id']}-{len(result['text'])}"
                with self.assertRaises(ReadbackError):
                    execute_notification(
                        self.package,
                        state_path=self.state,
                        receipt_dir=receipts,
                        attempt_dir=receipts / "attempts",
                        reservation_path=self.reservation,
                        enabled=True,
                        kill_switch=False,
                        dry_run=False,
                        expected_chat_id="123456789",
                        provider_factory=lambda: FakeProvider(self.package, result=result),
                    )
                receipt = json.loads((receipts / f"{EDITION_ID}.json").read_text())
                self.assertEqual("needs_reconciliation", receipt["status"])


class ProviderAndDurabilityTest(NotificationFixture):
    def test_provider_200_returns_exact_result(self):
        body = json.dumps(
            {
                "ok": True,
                "result": {
                    "message_id": 42,
                    "chat": {"id": 123456789},
                    "text": self.package.text,
                },
            }
        ).encode()
        transport = ScriptedTransport([HttpResponse(200, body)])
        provider = TelegramProvider(
            "123456789:abcdefghijklmnopqrstuvwxyzABCDEFGH_123456",
            "123456789",
            transport=transport,
        )
        self.assertEqual(42, provider.send_message(self.package.text)["message_id"])
        self.assertEqual("POST", transport.calls[0][0])
        self.assertNotIn(b"123456789:abcdefghijklmnopqrstuvwxyz", transport.calls[0][2])

    def test_timeout_and_5xx_are_ambiguous_and_never_retried(self):
        for response in (TimeoutError("timeout"), HttpResponse(500, b"{}")):
            with self.subTest(response=response):
                provider = TelegramProvider(
                    "123456789:abcdefghijklmnopqrstuvwxyzABCDEFGH_123456",
                    "123456789",
                    transport=ScriptedTransport([response]),
                )
                with self.assertRaises(AmbiguousMutationError):
                    provider.send_message("hello")
                self.assertEqual(1, provider.mutation_attempts)

    def test_github_artifact_hydrates_a_duplicate_block(self):
        body = json.dumps(
            {
                "artifacts": [
                    {
                        "id": 77,
                        "name": f"telegram-notification-receipt-{EDITION_ID}",
                        "expired": False,
                        "workflow_run": {"id": 88},
                    }
                ]
            }
        ).encode()
        transport = ScriptedTransport([HttpResponse(200, body)])
        found = hydrate_github_receipt(
            repository="Ironman1421/davidsdailybread",
            edition_id=EDITION_ID,
            token="github-secret",
            state_path=self.state,
            output_dir=self.receipts,
            transport=transport,
        )
        self.assertTrue(found)
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(self.package, self.state, self.receipts)
        self.assertEqual("GET", transport.calls[0][0])
        self.assertEqual("Bearer github-secret", transport.calls[0][3]["Authorization"])

    def test_cleared_remote_artifact_does_not_block(self):
        write_json(self.state, state_value(cleared=["77"]))
        receipt = HttpResponse(
            200,
            json.dumps(
                {
                    "artifacts": [
                        {
                            "id": 77,
                            "name": f"telegram-notification-receipt-{EDITION_ID}",
                            "expired": False,
                        }
                    ]
                }
            ).encode(),
        )
        found = hydrate_github_receipt(
            repository="Ironman1421/davidsdailybread",
            edition_id=EDITION_ID,
            token="github-secret",
            state_path=self.state,
            output_dir=self.receipts,
            transport=ScriptedTransport([receipt, HttpResponse(200, b'{"artifacts":[]}')]),
        )
        self.assertFalse(found)


class WorkflowContractTest(unittest.TestCase):
    def test_backup_schedules_are_pacific_and_dst_safe(self):
        bake = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text()
        counter = (ROOT / ".github" / "workflows" / "counter-sync.yml").read_text()
        self.assertIn("TZ=America/Los_Angeles date +%F", bake)
        self.assertNotIn("America/New_York", bake)
        bake_slots = {
            "morning": ("45 11 * * *", "45 12 * * *"),
            "evening": ("45 21 * * *", "45 22 * * *"),
        }
        for cron in (*bake_slots["morning"], *bake_slots["evening"]):
            self.assertIn(cron, bake)
        expected_bake_mappings = {
            "-0700": {"45 11 * * *", "45 21 * * *"},
            "-0800": {"45 12 * * *", "45 22 * * *"},
        }
        for offset, active_schedules in expected_bake_mappings.items():
            for slot, schedules in bake_slots.items():
                active = [
                    schedule
                    for schedule in schedules
                    if f"'{offset}:{schedule}'" in bake
                ]
                self.assertEqual(
                    1,
                    len(active),
                    f"{offset} must activate exactly one {slot} backup",
                )
                self.assertIn(active[0], active_schedules)

        self.assertIn("active: ${{ steps.cfg.outputs.active }}", bake)
        self.assertIn("needs.bake.outputs.active == 'true'", bake)
        self.assertNotIn("schedule:", counter)
        self.assertNotIn("cron:", counter)

    def test_bake_backups_survive_both_dst_transition_days(self):
        counter = (ROOT / ".github" / "workflows" / "counter-sync.yml").read_text()
        bake = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text()
        self.assertNotIn("date -d", counter)
        self.assertNotIn("TZ=", counter)
        self.assertIn("TARGET_CLOCK=04:45:00", bake)
        self.assertIn("TARGET_CLOCK=14:45:00", bake)
        self.assertIn('date -d "$TODAY $TARGET_CLOCK" +%z', bake)

    def test_workflow_is_duplicate_safe_and_credentials_are_isolated(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text()
        bake = workflow.split("\n  bake:\n", 1)[1].split("\n  x-broadcast:\n", 1)[0]
        telegram = workflow.split("\n  telegram-publication-receipt:\n", 1)[1]
        self.assertIn("Treat an existing edition as a successful no-op", bake)
        self.assertIn("already_exists: ${{ steps.existing.outputs.exists }}", bake)
        for name in (
            "Install Claude Code",
            "Bake (research, write, render)",
            "Guard the changed files",
            "Publish",
            "Verify the publish",
        ):
            following = bake.split(f"- name: {name}", 1)[1].split("\n      - name:", 1)[0]
            self.assertIn("if: steps.existing.outputs.exists != 'true'", following)
        self.assertIn("environment: telegram-notification-production", telegram)
        self.assertIn("actions: read", telegram)
        self.assertIn("contents: read", telegram)
        self.assertIn("persist-credentials: false", telegram)
        self.assertIn("hydrate-github-receipt", telegram)
        self.assertNotIn("needs.bake.outputs.slot == 'morning'", telegram)
        self.assertIn('SLOT: ${{ needs.bake.outputs.slot }}', telegram)
        self.assertIn('--slot "$SLOT"', telegram)
        self.assertIn("${EDITION_DATE}-${SLOT}", telegram)
        self.assertIn(
            "telegram-notification-receipt-${{ needs.bake.outputs.date }}-${{ needs.bake.outputs.slot }}",
            telegram,
        )
        before_live = telegram.split("- name: Run live exact edition notification", 1)[0]
        self.assertNotIn("secrets.TELEGRAM_", before_live)
        self.assertIn("DDB_TELEGRAM_NOTIFY_KILL_SWITCH != 'false'", before_live)
        self.assertIn("Persist mutation reservation before loading Telegram credentials", before_live)
        self.assertIn("if-no-files-found: error", before_live)
        readiness_position = telegram.index("Wait for exact public edition URL")
        reservation_position = telegram.index("Prepare duplicate-blocking mutation reservation")
        self.assertLess(readiness_position, reservation_position)
        readiness = telegram.split("- name: Wait for exact public edition URL", 1)[1].split(
            "\n      - name:", 1
        )[0]
        self.assertIn("verify-live", readiness)
        self.assertNotIn("secrets.TELEGRAM_", readiness)

    def test_existing_edition_backup_skips_telegram_job_and_artifacts(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text()
        x_job = workflow.split("\n  x-broadcast:\n", 1)[1].split(
            "\n  telegram-publication-receipt:\n", 1
        )[0]
        telegram = workflow.split("\n  telegram-publication-receipt:\n", 1)[1]
        guard = "needs.bake.outputs.already_exists != 'true'"

        self.assertIn(guard, x_job.split("\n    runs-on:", 1)[0])
        self.assertIn(guard, telegram.split("\n    runs-on:", 1)[0])
        self.assertIn("Run live exact edition notification", telegram)
        self.assertIn("Upload redacted Telegram attempt", telegram)
        self.assertIn("Upload blocking Telegram receipt", telegram)

    def test_contract_and_runbook_require_both_slots_and_clickable_exact_links(self):
        contract = json.loads(
            (ROOT / "operations" / "telegram-notification.contract.json").read_text()
        )
        self.assertEqual(["morning", "evening"], contract["trigger"]["dailySlots"])
        self.assertTrue(
            contract["sourceContract"]["messageIncludesDirectCanonicalEditionUrl"]
        )
        self.assertFalse(contract["sourceContract"]["latestOlderFallbackAllowed"])

        runbook = (ROOT / "docs" / "TELEGRAM_NOTIFICATION_RUNBOOK.md").read_text()
        distribution = (ROOT / "docs" / "DISTRIBUTION_SPEC.md").read_text()
        normalized_runbook = " ".join(runbook.split())
        self.assertIn("morning or evening publish", normalized_runbook)
        self.assertIn("direct canonical edition URL", normalized_runbook)
        self.assertIn("`--slot evening`", runbook)
        self.assertIn("direct HTTPS URL", distribution)

    def test_cli_defaults_to_kill_switch_on(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive.json"
            write_json(
                archive,
                {
                    "editions": [
                        {
                            "date": DATE,
                            "edition": "morning",
                            "file": f"editions/{EDITION_ID}.html",
                            "lead": LEAD,
                        }
                    ]
                },
            )
            with patch.dict(os.environ, {}, clear=True):
                result = main(
                    [
                        "run",
                        "--archive",
                        str(archive),
                        "--date",
                        DATE,
                        "--slot",
                        "morning",
                        "--state",
                        str(ROOT / "distribution" / "telegram-notification-state.json"),
                        "--receipt-dir",
                        str(root / "receipts"),
                        "--attempt-dir",
                        str(root / "attempts"),
                        "--reservation",
                        str(root / "missing.json"),
                    ]
                )
            self.assertEqual(0, result)
            attempt = json.loads((root / "attempts" / f"{EDITION_ID}-attempt.json").read_text())
            self.assertEqual("skipped_kill_switch", attempt["status"])

    def test_cli_dry_run_records_dry_run_while_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "archive.json"
            write_json(
                archive,
                {
                    "editions": [
                        {
                            "date": DATE,
                            "edition": "morning",
                            "file": f"editions/{EDITION_ID}.html",
                            "lead": LEAD,
                        }
                    ]
                },
            )
            environment = {
                "DDB_TELEGRAM_NOTIFY_ENABLED": "false",
                "DDB_TELEGRAM_NOTIFY_KILL_SWITCH": "false",
            }
            with patch.dict(os.environ, environment, clear=True):
                result = main(
                    [
                        "run",
                        "--archive",
                        str(archive),
                        "--date",
                        DATE,
                        "--slot",
                        "morning",
                        "--state",
                        str(ROOT / "distribution" / "telegram-notification-state.json"),
                        "--receipt-dir",
                        str(root / "receipts"),
                        "--attempt-dir",
                        str(root / "attempts"),
                        "--reservation",
                        str(root / "missing.json"),
                        "--dry-run",
                    ]
                )
            self.assertEqual(0, result)
            attempt = json.loads((root / "attempts" / f"{EDITION_ID}-attempt.json").read_text())
            self.assertEqual("dry_run", attempt["status"])
            self.assertEqual(0, attempt["mutationAttempts"])


if __name__ == "__main__":
    unittest.main()
