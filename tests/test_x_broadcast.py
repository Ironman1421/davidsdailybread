#!/usr/bin/env python3
"""Acceptance tests for the repository-owned canonical X broadcaster."""

from __future__ import annotations

from contextlib import redirect_stderr
import io
import json
import logging
from pathlib import Path
import tempfile
import unittest

from distribution.x_broadcast import (
    AmbiguousMutationError,
    DuplicateError,
    EditionPackage,
    HttpResponse,
    OAuth1Signer,
    PermanentProviderError,
    ReadbackError,
    Redactor,
    ValidationError,
    XApiProvider,
    assert_not_duplicate,
    build_package,
    execute_broadcast,
    hydrate_github_receipt,
    main,
    verify_readback,
    write_durable_reservation,
    x_weighted_length,
)


ROOT = Path(__file__).resolve().parents[1]
DATE = "2099-01-01"
SLOT = "morning"
EDITION_ID = f"{DATE}-{SLOT}"
LEAD = "A precise, source-linked test lead"
POST_ID = "1234567890123456789"
USER_ID = "987654321"
USERNAME = "DavidDailyBread"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def archive_value(lead: object = LEAD, *, file: str | None = None) -> dict:
    return {
        "editions": [
            {
                "date": DATE,
                "edition": SLOT,
                "file": file or f"editions/{EDITION_ID}.html",
                "lead": lead,
            }
        ]
    }


def state_value(*, receipts: list[dict] | None = None, cleared: list[str] | None = None) -> dict:
    return {
        "version": 1,
        "cutoverAfterEditionId": "2026-07-31-morning",
        "receipts": receipts or [],
        "clearedRemoteArtifactIds": cleared or [],
    }


class FakeProvider:
    def __init__(self, package: EditionPackage) -> None:
        self.package = package
        self.mutation_attempts = 0
        self.identity_calls = 0
        self.create_calls = 0
        self.read_calls = 0
        self.timeline_calls = 0

    def verify_identity(self):
        self.identity_calls += 1
        return {"id": USER_ID, "username": USERNAME}

    def create_post(self, text):
        self.mutation_attempts += 1
        self.create_calls += 1
        return {"id": POST_ID, "text": text}

    def find_existing_post(self, package):
        self.timeline_calls += 1
        return None

    def read_post(self, post_id):
        self.read_calls += 1
        return {
            "id": post_id,
            "author_id": USER_ID,
            "created_at": "2099-01-01T13:00:00.000Z",
            "text": self.package.text.replace(self.package.canonical_url, "https://t.co/AbCdEf1234"),
            "entities": {"urls": [{"expanded_url": self.package.canonical_url}]},
        }


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


class BroadcastFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.archive = self.root / "archive.json"
        self.state = self.root / "state.json"
        self.receipts = self.root / "receipts"
        self.attempts = self.root / "attempts"
        write_json(self.archive, archive_value())
        write_json(self.state, state_value())
        self.package = build_package(self.archive, DATE, SLOT)
        self.log_stream = io.StringIO()
        self.logger = logging.getLogger(f"test.x.{id(self)}")
        self.logger.handlers = [logging.StreamHandler(self.log_stream)]
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        self.tmp.cleanup()

    def execute(self, factory, **overrides):
        options = {
            "state_path": self.state,
            "receipt_dir": self.receipts,
            "attempt_dir": self.attempts,
            "enabled": True,
            "kill_switch": False,
            "dry_run": False,
            "provider_factory": factory,
            "expected_user_id": USER_ID,
            "expected_username": USERNAME,
            "redactor": Redactor(),
            "logger": self.logger,
        }
        options.update(overrides)
        return execute_broadcast(self.package, **options)


class CanonicalPackageTest(BroadcastFixture):
    def test_preview_is_deterministic_and_uses_exact_archive_lead_and_url(self):
        again = build_package(self.archive, DATE, SLOT)
        self.assertEqual(self.package, again)
        self.assertEqual(LEAD, self.package.lead)
        self.assertEqual(
            f"https://davidsdailybread.com/editions/{EDITION_ID}.html",
            self.package.canonical_url,
        )
        self.assertEqual(
            f"Morning edition: {LEAD}\n\nRead the full briefing: {self.package.canonical_url}",
            self.package.text,
        )
        self.assertEqual(x_weighted_length(self.package.text), self.package.weighted_length)
        self.assertLessEqual(self.package.weighted_length, 280)

    def test_weighted_length_uses_23_for_urls_and_two_for_cjk(self):
        self.assertEqual(1 + 1 + 23 + 1 + 2, x_weighted_length("a https://example.com/very/long 路"))

    def test_invalid_content_and_archive_mismatch_fail_closed(self):
        invalid = (
            "unsafe — dash",
            "mention @someone",
            "hashtag #trend",
            "embedded https://example.com",
            "embedded http://example.com",
            "embedded www.example.com",
            "embedded example.com",
            "embedded example.com, with punctuation",
            "line\nbreak",
            "e\u0301",
            "界" * 130,
        )
        for lead in invalid:
            with self.subTest(lead=lead[:20]):
                write_json(self.archive, archive_value(lead))
                with self.assertRaises(ValidationError):
                    build_package(self.archive, DATE, SLOT)
        write_json(self.archive, archive_value(file="editions/wrong.html"))
        with self.assertRaisesRegex(ValidationError, "exactly one exact"):
            build_package(self.archive, DATE, SLOT)


class BroadcastExecutionTest(BroadcastFixture):
    def test_success_writes_verified_receipt_and_attempt(self):
        provider = FakeProvider(self.package)
        status = self.execute(lambda: provider)

        self.assertEqual("published", status)
        self.assertEqual(
            (1, 1, 1, 1),
            (
                provider.identity_calls,
                provider.timeline_calls,
                provider.create_calls,
                provider.read_calls,
            ),
        )
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("published", receipt["status"])
        self.assertTrue(receipt["readBackVerified"])
        self.assertEqual(POST_ID, receipt["platformPostId"])
        self.assertEqual(self.package.text, receipt["postText"])
        attempt = json.loads((self.attempts / f"{EDITION_ID}-attempt.json").read_text())
        self.assertEqual("published", attempt["status"])
        self.assertEqual(1, attempt["mutationAttempts"])

    def test_duplicate_receipt_refuses_provider_construction(self):
        write_json(
            self.state,
            state_value(receipts=[{"editionId": EDITION_ID, "platformPostId": POST_ID}]),
        )
        status = self.execute(lambda: self.fail("provider must not be constructed"))
        self.assertEqual("refused_duplicate", status)
        attempt = json.loads((self.attempts / f"{EDITION_ID}-attempt.json").read_text())
        self.assertEqual(0, attempt["mutationAttempts"])

    def test_disabled_dry_run_and_kill_switch_never_construct_provider(self):
        cases = (
            ({"enabled": False}, "skipped_disabled"),
            ({"dry_run": True}, "dry_run"),
            ({"kill_switch": True}, "skipped_kill_switch"),
            ({"kill_switch": True, "dry_run": True}, "skipped_kill_switch"),
        )
        for index, (overrides, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                attempt_dir = self.root / f"attempts-{index}"
                status = self.execute(
                    lambda: self.fail("provider must not be constructed"),
                    attempt_dir=attempt_dir,
                    **overrides,
                )
                self.assertEqual(expected, status)
                attempt = json.loads((attempt_dir / f"{EDITION_ID}-attempt.json").read_text())
                self.assertEqual(0, attempt["mutationAttempts"])

    def test_timeout_is_not_retried_and_writes_blocking_reconciliation(self):
        package = self.package

        class TimeoutProvider(FakeProvider):
            def create_post(self, text):
                self.mutation_attempts += 1
                self.create_calls += 1
                raise AmbiguousMutationError("timeout after request body was sent")

        provider = TimeoutProvider(package)
        with self.assertRaises(AmbiguousMutationError):
            self.execute(lambda: provider)
        self.assertEqual(1, provider.create_calls)
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("needs_reconciliation", receipt["status"])
        self.assertIsNone(receipt["platformPostId"])
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(self.package, state_value(), self.receipts)

    def test_exact_provider_timeline_match_refuses_duplicate_mutation(self):
        package = self.package

        class ExistingProvider(FakeProvider):
            def find_existing_post(self, package):
                self.timeline_calls += 1
                return self.read_post(POST_ID)

        provider = ExistingProvider(package)
        status = self.execute(lambda: provider)
        self.assertEqual("refused_provider_duplicate", status)
        self.assertEqual(0, provider.create_calls)
        self.assertEqual(0, provider.mutation_attempts)
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("existing_provider_post", receipt["status"])
        self.assertEqual(POST_ID, receipt["platformPostId"])
        self.assertTrue(receipt["readBackVerified"])
        self.assertIsNone(receipt["automated"])

    def test_provider_response_mismatch_and_readback_failure_block_retry(self):
        package = self.package

        class MismatchProvider(FakeProvider):
            def read_post(self, post_id):
                value = dict(super().read_post(post_id))
                value["text"] = "wrong https://t.co/AbCdEf1234"
                return value

        mismatch = MismatchProvider(package)
        with self.assertRaises(ReadbackError):
            self.execute(lambda: mismatch)
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("needs_reconciliation", receipt["status"])
        self.assertEqual(POST_ID, receipt["platformPostId"])

        self.receipts = self.root / "receipts-second"

        class ReadFailureProvider(FakeProvider):
            def read_post(self, post_id):
                raise ReadbackError("read-back unavailable", provider_post_id=post_id)

        failed = ReadFailureProvider(package)
        with self.assertRaises(ReadbackError):
            self.execute(lambda: failed)
        receipt = json.loads((self.receipts / f"{EDITION_ID}.json").read_text())
        self.assertEqual("needs_reconciliation", receipt["status"])
        self.assertEqual(POST_ID, receipt["platformPostId"])

    def test_error_logs_and_attempts_redact_secret_values(self):
        secret = "top-secret-token-value"

        class LeakyProvider(FakeProvider):
            def verify_identity(self):
                raise PermanentProviderError(
                    f"Authorization: {secret}; oauth_token={secret}", status=401
                )

        with self.assertRaises(PermanentProviderError):
            self.execute(
                lambda: LeakyProvider(self.package), redactor=Redactor([secret])
            )
        attempt_text = (self.attempts / f"{EDITION_ID}-attempt.json").read_text()
        self.assertNotIn(secret, attempt_text)
        self.assertNotIn(secret, self.log_stream.getvalue())
        self.assertIn("[REDACTED]", attempt_text)


class ProviderRetryTest(unittest.TestCase):
    def provider(self, transport, *, sleeper=lambda _delay: None):
        return XApiProvider(
            signer=OAuth1Signer("api", "api-secret", "token", "token-secret"),
            expected_user_id=USER_ID,
            expected_username=USERNAME,
            transport=transport,
            max_attempts=3,
            sleeper=sleeper,
            jitter=lambda: 0.0,
            redactor=Redactor(["api-secret", "token-secret"]),
        )

    def test_429_retries_with_bound_and_jitter_hook(self):
        delays = []
        transport = ScriptedTransport(
            [
                HttpResponse(429, {}, b'{"title":"rate limited"}'),
                HttpResponse(201, {}, b'{"data":{"id":"123","text":"hello"}}'),
            ]
        )
        provider = self.provider(transport, sleeper=delays.append)
        result = provider.create_post("hello")
        self.assertEqual("123", result["id"])
        self.assertEqual(2, len(transport.calls))
        self.assertEqual(2, provider.mutation_attempts)
        self.assertEqual([0.75], delays)

    def test_401_and_403_are_permanent_and_never_retry(self):
        for status in (401, 403):
            with self.subTest(status=status):
                transport = ScriptedTransport(
                    [HttpResponse(status, {}, b'{"title":"denied"}')]
                )
                provider = self.provider(transport)
                with self.assertRaises(PermanentProviderError):
                    provider.create_post("hello")
                self.assertEqual(1, len(transport.calls))
                self.assertEqual(1, provider.mutation_attempts)

    def test_post_timeout_is_ambiguous_and_never_retried(self):
        transport = ScriptedTransport([TimeoutError("socket timed out")])
        provider = self.provider(transport)
        with self.assertRaises(AmbiguousMutationError):
            provider.create_post("hello")
        self.assertEqual(1, len(transport.calls))
        self.assertEqual(1, provider.mutation_attempts)

    def test_get_timeout_retries_and_recovers_with_bounded_delay(self):
        delays = []
        transport = ScriptedTransport(
            [
                TimeoutError("temporary read timeout"),
                HttpResponse(
                    200,
                    {},
                    json.dumps(
                        {"data": {"id": USER_ID, "username": USERNAME}}
                    ).encode(),
                ),
            ]
        )
        provider = self.provider(transport, sleeper=delays.append)
        identity = provider.verify_identity()
        self.assertEqual(USER_ID, identity["id"])
        self.assertEqual(2, len(transport.calls))
        self.assertEqual([0.75], delays)
        self.assertEqual(0, provider.mutation_attempts)


class ReceiptHydrationAndWorkflowTest(BroadcastFixture):
    def test_github_artifact_metadata_hydrates_duplicate_block(self):
        body = json.dumps(
            {
                "artifacts": [
                    {
                        "id": 42,
                        "name": f"x-broadcast-receipt-{EDITION_ID}",
                        "expired": False,
                        "workflow_run": {"id": 99},
                    }
                ]
            }
        ).encode()
        transport = ScriptedTransport([HttpResponse(200, {}, body)])
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
            assert_not_duplicate(self.package, state_value(), self.receipts)
        auth = transport.calls[0][2]["Authorization"]
        self.assertEqual("Bearer github-secret", auth)

    def test_cleared_remote_artifact_does_not_block(self):
        write_json(self.state, state_value(cleared=["42"]))
        body = json.dumps(
            {
                "artifacts": [
                    {
                        "id": 42,
                        "name": f"x-broadcast-receipt-{EDITION_ID}",
                        "expired": False,
                    }
                ]
            }
        ).encode()
        found = hydrate_github_receipt(
            repository="Ironman1421/davidsdailybread",
            edition_id=EDITION_ID,
            token="github-secret",
            state_path=self.state,
            output_dir=self.receipts,
            transport=ScriptedTransport(
                [
                    HttpResponse(200, {}, body),
                    HttpResponse(200, {}, b'{"artifacts":[]}'),
                ]
            ),
        )
        self.assertFalse(found)

    def test_durable_reservation_blocks_rerun_after_runner_crash(self):
        reservation = self.root / "reservation.json"
        write_durable_reservation(
            self.package,
            state_path=self.state,
            receipt_dir=self.receipts,
            output_path=reservation,
        )
        value = json.loads(reservation.read_text())
        self.assertEqual("reserved_before_mutation", value["status"])
        self.assertEqual(EDITION_ID, value["editionId"])

        receipt_lookup = HttpResponse(200, {}, b'{"artifacts":[]}')
        reservation_lookup = HttpResponse(
            200,
            {},
            json.dumps(
                {
                    "artifacts": [
                        {
                            "id": 77,
                            "name": f"x-broadcast-reservation-{EDITION_ID}",
                            "expired": False,
                            "workflow_run": {"id": 101},
                        }
                    ]
                }
            ).encode(),
        )
        hydrated = self.root / "crash-rerun-receipts"
        found = hydrate_github_receipt(
            repository="Ironman1421/davidsdailybread",
            edition_id=EDITION_ID,
            token="github-secret",
            state_path=self.state,
            output_dir=hydrated,
            transport=ScriptedTransport([receipt_lookup, reservation_lookup]),
        )
        self.assertTrue(found)
        stub = json.loads((hydrated / f"remote-{EDITION_ID}.json").read_text())
        self.assertEqual(f"x-broadcast-reservation-{EDITION_ID}", stub["artifactName"])
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(self.package, state_value(), hydrated)

    def test_workflow_keeps_credentials_in_separate_read_only_job(self):
        workflow = (ROOT / ".github" / "workflows" / "ddb-bake.yml").read_text()
        x_job = workflow.split("\n  x-broadcast:\n", 1)[1]
        bake_job = workflow.split("\n  bake:\n", 1)[1].split("\n  x-broadcast:\n", 1)[0]
        self.assertIn("needs: bake", x_job)
        self.assertIn("environment: x-broadcast-production", x_job)
        self.assertIn("actions: read", x_job)
        self.assertIn("contents: read", x_job)
        self.assertIn("persist-credentials: false", x_job)
        self.assertIn("hydrate-github-receipt", x_job)
        self.assertIn("continue-on-error: true", x_job)
        self.assertIn("X_ACCESS_TOKEN_SECRET: ${{ secrets.X_ACCESS_TOKEN_SECRET }}", x_job)
        self.assertNotIn("X_ACCESS_TOKEN", bake_job)
        self.assertIn("needs.bake.outputs.date", x_job)
        self.assertIn("needs.bake.outputs.slot", x_job)
        before_live = x_job.split("- name: Run live canonical X broadcast", 1)[0]
        self.assertNotIn("secrets.X_", before_live)
        self.assertIn("KILL_SWITCH != 'false'", before_live)
        self.assertIn("--dry-run", before_live)
        reservation_position = x_job.index("Persist mutation reservation before loading X credentials")
        live_position = x_job.index("Run live canonical X broadcast")
        self.assertLess(reservation_position, live_position)
        self.assertIn("x-broadcast-reservation-", before_live)
        self.assertIn("if-no-files-found: error", before_live)

    def test_runbook_requires_a_real_dry_run_and_resets_one_edition_canary(self):
        runbook = (ROOT / "docs" / "X_BROADCAST_RUNBOOK.md").read_text()
        normalized = " ".join(runbook.split())
        self.assertIn(
            "Keep enablement `false`, then have a reviewer change the kill switch to `false`",
            normalized,
        )
        self.assertIn("`status` to be exactly `dry_run`", normalized)
        self.assertIn("A `skipped_kill_switch` attempt is not a dry run", normalized)
        self.assertIn(
            "set the kill switch to `true` first and then set enablement to `false`",
            normalized,
        )
        self.assertIn(
            "Continuous activation requires a separate explicit authorization",
            normalized,
        )

        contract = json.loads(
            (ROOT / "operations" / "x-broadcast.contract.json").read_text()
        )
        self.assertEqual(
            "selected-branch:main",
            contract["provisioning"]["githubEnvironmentBranchPolicy"],
        )
        self.assertFalse(contract["provisioning"]["githubEnvironmentSecretsInstalled"])
        self.assertTrue(contract["enablement"]["oneEditionCanaryResetsKillSwitchFirst"])
        self.assertTrue(contract["enablement"]["oneEditionCanaryResetsEnabledSecond"])
        self.assertTrue(
            contract["enablement"]["continuousActivationRequiresSeparateApproval"]
        )

    def test_bootstrap_receipt_blocks_known_manual_recovery_post(self):
        state = json.loads(
            (ROOT / "distribution" / "x-broadcast-state.json").read_text()
        )
        receipt = state["receipts"][0]
        self.assertEqual("2026-07-31-morning", receipt["editionId"])
        self.assertEqual("2083305538469994808", receipt["platformPostId"])
        self.assertEqual(
            "https://x.com/DavidDailyBread/status/2083305538469994808",
            receipt["platformPostUrl"],
        )
        self.assertIsNone(receipt["publishedAt"])
        package = build_package(ROOT / "archive.json", "2026-07-31", "morning")
        with self.assertRaises(DuplicateError):
            assert_not_duplicate(package, state, self.receipts)

    def test_cli_preview_has_no_time_or_provider_state(self):
        output_one = io.StringIO()
        output_two = io.StringIO()
        from contextlib import redirect_stdout

        argv = ["preview", "--archive", str(self.archive), "--date", DATE, "--slot", SLOT]
        with redirect_stdout(output_one):
            self.assertEqual(0, main(argv))
        with redirect_stdout(output_two):
            self.assertEqual(0, main(argv))
        self.assertEqual(output_one.getvalue(), output_two.getvalue())


class ReadbackContractTest(BroadcastFixture):
    def test_wrong_author_url_or_text_is_rejected(self):
        provider = FakeProvider(self.package)
        created = provider.create_post(self.package.text)
        baseline = provider.read_post(POST_ID)
        cases = (
            {**baseline, "author_id": "1"},
            {**baseline, "text": "wrong https://t.co/AbCdEf1234"},
            {**baseline, "entities": {"urls": [{"expanded_url": "https://example.com"}]}},
        )
        for readback in cases:
            with self.subTest(readback=readback):
                with self.assertRaises(ReadbackError):
                    verify_readback(self.package, created, readback, USER_ID)


if __name__ == "__main__":
    unittest.main()
