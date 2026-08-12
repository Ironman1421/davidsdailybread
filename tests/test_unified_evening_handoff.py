from copy import deepcopy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from jsonschema import Draft202012Validator, FormatChecker

from ddb_evening_handoff import (
    HandoffValidationError,
    fetch_packet,
    upload_packet,
    validate_noon_packet,
    validate_packet,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/ddb-reviewed-evening-handoff.valid.json"
SCHEMA_PATH = ROOT / "operations/schemas/ddb-reviewed-evening-handoff-v1.schema.json"
NOW = datetime(2026, 8, 4, 21, 30, tzinfo=timezone.utc)


def noon_packet():
    def candidate(section):
        return {
            "id": f"x-{section}-one",
            "section": section,
            "title": f"Example {section}",
            "summary": "Advisory research candidate.",
            "primarySourceUrls": [f"https://example.com/{section}"],
            "xPostUrls": [f"https://x.com/example/status/{1 if section == 'tools' else 2}"],
            "observedAt": "2026-08-04T19:20:00Z",
            "action": "Try one bounded repeatable task.",
            "caveat": "DDB must verify this independently.",
            "uncertainty": ["No hands-on trial was performed."],
            "editorialScores": {
                "leverage": 80,
                "broadApplicability": 70,
                "repeatability": 70,
                "trendStrength": 60,
                "total": 73,
                "shelfEligible": True,
                "ruleVersion": "editorial-fit-v1",
            },
            "verificationStatus": "primary-source-checked",
        }

    return {
        "schemaVersion": "x-manager-noon-research-v2",
        "status": "completed",
        "targetEdition": {
            "date": "2026-08-04",
            "slot": "evening",
            "timeZone": "America/Los_Angeles",
        },
        "createdAt": "2026-08-04T20:35:00Z",
        "producer": "X Manager, Tools and Workflows",
        "researchInputs": {
            "xPro": {
                "requested": True,
                "used": True,
                "observedAt": "2026-08-04T19:50:00Z",
                "context": "Tools + workflows watch columns",
            },
            "xRadar": {
                "requested": True,
                "used": True,
                "observedAt": "2026-08-04T20:00:00Z",
                "context": "Focused Radar searches",
            },
            "xMonitor": {
                "used": True,
                "observedAt": "2026-08-04T20:05:00Z",
                "newPaidRunTriggered": False,
                "context": "Read the guarded durable export",
            },
            "primarySourcesChecked": True,
        },
        "closingDeltaCheck": {
            "attempted": True,
            "completed": True,
            "observedAt": "2026-08-04T20:30:00Z",
            "sources": ["xPro", "xRadar"],
            "changesFound": True,
            "context": "Final X Pro and Radar pass added one late candidate.",
        },
        "candidates": {
            "tools": [candidate("tools")],
            "workflows": [candidate("workflows")],
        },
        "holds": [],
        "rejections": [],
        "blockedReasons": [],
        "authority": {
            "advisoryOnly": True,
            "verificationRequired": True,
            "publicationApproved": False,
            "maySelectForDdb": False,
            "mayPublish": False,
            "finalSelectionOwner": "David's Daily Bread",
        },
    }


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit=-1):
        return self.payload if limit < 0 else self.payload[:limit]


class UnifiedEveningHandoffTest(unittest.TestCase):
    def setUp(self):
        self.packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_matches_shared_schema_and_runtime_validator(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())

        self.assertEqual([], list(validator.iter_errors(self.packet)))
        validate_packet(self.packet, expected_date="2026-08-04", now=NOW)

    def test_noon_contract_requires_current_x_pro_x_radar_or_blocked_status(self):
        schema = json.loads(
            (
                ROOT
                / "operations/schemas/x-manager-noon-research-v2.schema.json"
            ).read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        completed = noon_packet()
        self.assertEqual([], list(validator.iter_errors(completed)))
        validate_noon_packet(completed, expected_date="2026-08-04")

        invalid = deepcopy(completed)
        invalid["researchInputs"]["xRadar"]["used"] = False
        self.assertNotEqual([], list(validator.iter_errors(invalid)))
        with self.assertRaisesRegex(HandoffValidationError, "xRadar.used"):
            validate_noon_packet(invalid, expected_date="2026-08-04")

        missing_delta = deepcopy(completed)
        del missing_delta["closingDeltaCheck"]
        self.assertNotEqual([], list(validator.iter_errors(missing_delta)))
        with self.assertRaisesRegex(HandoffValidationError, "closingDeltaCheck"):
            validate_noon_packet(missing_delta, expected_date="2026-08-04")

        stale_delta = deepcopy(completed)
        stale_delta["closingDeltaCheck"]["observedAt"] = "2026-08-04T19:45:00Z"
        with self.assertRaisesRegex(HandoffValidationError, "after the initial X Pro"):
            validate_noon_packet(stale_delta, expected_date="2026-08-04")

        blocked = deepcopy(completed)
        blocked["status"] = "blocked"
        blocked["blockedReasons"] = ["Signed-in X Radar was unavailable."]
        blocked["candidates"] = {"tools": [], "workflows": []}
        blocked["researchInputs"]["primarySourcesChecked"] = False
        for name in ("xPro", "xRadar"):
            blocked["researchInputs"][name]["used"] = False
            blocked["researchInputs"][name]["observedAt"] = None
        blocked["researchInputs"]["xMonitor"]["used"] = False
        blocked["researchInputs"]["xMonitor"]["observedAt"] = None
        blocked["closingDeltaCheck"]["completed"] = False
        blocked["closingDeltaCheck"]["observedAt"] = None
        blocked["closingDeltaCheck"]["changesFound"] = None
        blocked["closingDeltaCheck"]["context"] = (
            "Final X Pro and Radar delta check could not complete because Radar was unavailable."
        )
        self.assertEqual([], list(validator.iter_errors(blocked)))
        validate_noon_packet(blocked, expected_date="2026-08-04")

    def test_schedule_contract_keeps_the_pipeline_close_to_the_bake(self):
        contract = json.loads(
            (
                ROOT / "operations/tools-workflows-research-handoff.contract.json"
            ).read_text(encoding="utf-8")
        )

        self.assertEqual("America/Los_Angeles", contract["targetEdition"]["timeZone"])
        self.assertEqual(
            {
                "xManagerResearchStartsLocal": "12:45:00",
                "xManagerPacketReadyByLocal": "13:35:00",
                "ddbCombinedReviewStartsLocal": "13:40:00",
                "reviewedPacketReadyByLocal": "14:25:00",
                "bakeStartsLocal": "14:40:00",
                "selectionPasses": 1,
            },
            contract["coordination"],
        )
        self.assertTrue(contract["producer"]["closingDeltaCheckRequired"])
        self.assertEqual(
            "research-tools-and-workflows-for-ddb-evening-edition",
            contract["automationBindings"]["xManager"]["id"],
        )
        self.assertEqual(
            "/Users/davidfriedhof/Documents/X Manager, Tools and Workflows",
            contract["automationBindings"]["xManager"]["repositoryPath"],
        )
        self.assertEqual(
            "review-x-manager-research-for-ddb-evening-edition",
            contract["automationBindings"]["ddb"]["id"],
        )
        self.assertTrue(contract["automationBindings"]["updateExistingOnly"])
        self.assertFalse(contract["automationBindings"]["duplicatesAllowed"])

        prompt = (
            ROOT / "operations/prompts/ddb-140pm-combined-evening-review.md"
        ).read_text(encoding="utf-8")
        self.assertIn("1:40 PM", prompt)
        self.assertIn("2:25 PM", prompt)
        self.assertIn("closingDeltaCheck", prompt)

    def test_validator_rejects_wrong_date_expiry_x_sources_and_failed_gates(self):
        wrong_date = deepcopy(self.packet)
        wrong_date["targetEdition"]["date"] = "2026-08-05"
        with self.assertRaises(HandoffValidationError):
            validate_packet(wrong_date, expected_date="2026-08-04", now=NOW)

        with self.assertRaisesRegex(HandoffValidationError, "expired"):
            validate_packet(
                self.packet,
                expected_date="2026-08-04",
                now=datetime(2026, 8, 5, 8, tzinfo=timezone.utc),
            )

        x_source = deepcopy(self.packet)
        x_source["selection"]["tools"][0]["trendUrl"] = "https://x.com/example/status/1"
        with self.assertRaisesRegex(HandoffValidationError, "non-X HTTPS"):
            validate_packet(x_source, now=NOW)

        for source_url in (
            "https://api.x.com/example/status/1",
            "https://News.Twitter.Com:443/example/status/1",
        ):
            x_subdomain = deepcopy(self.packet)
            x_subdomain["selection"]["tools"][0]["officialUrl"] = source_url
            with self.assertRaisesRegex(HandoffValidationError, "non-X HTTPS"):
                validate_packet(x_subdomain, now=NOW)

        failed_gate = deepcopy(self.packet)
        failed_gate["selection"]["tools"][0]["editorialScores"]["leverage"] = 20
        with self.assertRaisesRegex(HandoffValidationError, "editorial gate"):
            validate_packet(failed_gate, now=NOW)

        unbounded = deepcopy(self.packet)
        unbounded["expiresAt"] = "2026-08-06T21:20:00Z"
        with self.assertRaisesRegex(HandoffValidationError, "18 hours"):
            validate_packet(unbounded, now=NOW)

        missing_delta = deepcopy(self.packet)
        del missing_delta["research"]["xManager"]["closingDeltaCheck"]
        with self.assertRaisesRegex(HandoffValidationError, "closingDeltaCheck"):
            validate_packet(missing_delta, now=NOW)

    def test_fetch_writes_valid_packet_or_explicit_nonblocking_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "handoff.json"
            with mock.patch.dict(os.environ, {"SITES_TOKEN": "sites-secret"}), mock.patch(
                "ddb_evening_handoff.request.urlopen",
                return_value=FakeResponse(self.packet),
            ) as urlopen:
                self.assertTrue(
                    fetch_packet(
                        "https://private.example",
                        "2026-08-04",
                        output,
                        "SITES_TOKEN",
                        now=NOW,
                    )
                )
            fetched_request = urlopen.call_args.args[0]
            self.assertIn("date=2026-08-04&slot=evening", fetched_request.full_url)
            self.assertEqual(
                "Bearer sites-secret",
                fetched_request.headers["Oai-sites-authorization"],
            )
            self.assertEqual(self.packet, json.loads(output.read_text(encoding="utf-8")))

            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertFalse(
                    fetch_packet(
                        "https://private.example",
                        "2026-08-04",
                        output,
                        "MISSING_TOKEN",
                    )
                )
            fallback = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(fallback["available"])
            self.assertEqual("2026-08-04", fallback["targetEdition"]["date"])

    def test_upload_validates_before_sending_and_keeps_tokens_out_of_output(self):
        with tempfile.TemporaryDirectory() as directory:
            packet_path = Path(directory) / "handoff.json"
            packet_path.write_text(json.dumps(self.packet), encoding="utf-8")
            receipt = {"stored": True, "packetId": "2026-08-04-evening"}
            stdout = io.StringIO()
            with mock.patch.dict(
                os.environ,
                {"WRITE_TOKEN": "write-secret", "SITES_TOKEN": "sites-secret"},
            ), mock.patch(
                "ddb_evening_handoff.request.urlopen",
                return_value=FakeResponse(receipt),
            ) as urlopen, mock.patch("sys.stdout", stdout):
                result = upload_packet(
                    "https://private.example",
                    packet_path,
                    "WRITE_TOKEN",
                    "SITES_TOKEN",
                    now=NOW,
                )
            sent_request = urlopen.call_args.args[0]
            self.assertEqual(receipt, result)
            self.assertEqual("Bearer write-secret", sent_request.headers["Authorization"])
            self.assertEqual(
                "Bearer sites-secret",
                sent_request.headers["Oai-sites-authorization"],
            )
            self.assertNotIn("write-secret", stdout.getvalue())
            self.assertNotIn("sites-secret", stdout.getvalue())

    def test_reviewed_packet_round_trips_from_private_upload_to_bake_fetch(self):
        stored = {}

        def transport(req, timeout):
            self.assertEqual(30, timeout)
            if req.get_method() == "POST":
                stored.update(json.loads(req.data))
                return FakeResponse(
                    {"stored": True, "packetId": stored["packetId"]}
                )
            self.assertEqual("2026-08-04", stored["targetEdition"]["date"])
            return FakeResponse(stored)

        with tempfile.TemporaryDirectory() as directory:
            packet_path = Path(directory) / "reviewed.json"
            fetched_path = Path(directory) / "bake-input.json"
            packet_path.write_text(json.dumps(self.packet), encoding="utf-8")
            with mock.patch.dict(
                os.environ,
                {"WRITE_TOKEN": "write-secret", "SITES_TOKEN": "sites-secret"},
            ), mock.patch(
                "ddb_evening_handoff.request.urlopen", side_effect=transport
            ):
                upload_packet(
                    "https://private.example",
                    packet_path,
                    "WRITE_TOKEN",
                    "SITES_TOKEN",
                    now=NOW,
                )
                self.assertTrue(
                    fetch_packet(
                        "https://private.example",
                        "2026-08-04",
                        fetched_path,
                        "SITES_TOKEN",
                        now=NOW,
                    )
                )
            self.assertEqual(
                self.packet,
                json.loads(fetched_path.read_text(encoding="utf-8")),
            )


def test_evening_bake_consumes_only_the_final_reviewed_packet():
    workflow = (ROOT / ".github/workflows/ddb-bake.yml").read_text(encoding="utf-8")
    handoff_step = workflow.split(
        "- name: Prepare DDB-reviewed evening handoff", 1
    )[1].split("- name: Install Claude Code", 1)[0]
    bake_step = workflow.split("- name: Bake (research, write, render)", 1)[1].split(
        "- name: Guard the changed files", 1
    )[0]

    assert "needs.prepare-reader-plan.outputs.slot == 'evening'" in handoff_step
    assert "needs.prepare-reader-plan.outputs.mode == 'daily'" in handoff_step
    assert "ddb_evening_handoff.py fetch" in handoff_step
    assert "--date \"$EDITION_DATE\"" in handoff_step
    assert "secrets.X_MONITOR_SITES_BYPASS_TOKEN" in handoff_step
    assert "/api/trends" not in handoff_step
    assert "/api/discovery-export" not in handoff_step

    assert "X_MONITOR_SITES_BYPASS_TOKEN" not in bake_step
    assert "DDB_REVIEWED_HANDOFF_PATH" in bake_step
    assert "final editorial set" in bake_step
    assert "Do not discover, add, substitute, rerank" in bake_step
    assert "normal source ladder as the fail-open exception" in bake_step


def test_bake_spec_preserves_single_selection_pass_and_publication_authority():
    bake = (ROOT / "BAKE.md").read_text(encoding="utf-8")
    normalized = " ".join(bake.split())

    assert "40% leverage, 30% broad applicability" in normalized
    assert "selected/hold/reject decision" in normalized
    assert "Do not" in normalized and "rerank the set" in normalized
    assert "publicationApproved: false" in normalized
    assert "normal non-X source ladder" in normalized
