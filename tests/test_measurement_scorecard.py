#!/usr/bin/env python3
"""Acceptance tests for the aggregate-only operating scorecard."""

from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from measurement.scorecard import (
    ScorecardError,
    build_daily_scorecard,
    build_weekly_scorecard,
    load_dictionary,
    load_observation,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
MEASUREMENT = ROOT / "measurement"
BASELINE = MEASUREMENT / "observations" / "2026-08-02.json"
FIXTURES = ROOT / "tests" / "fixtures" / "measurement"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class MeasurementScorecardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dictionary = load_dictionary()
        cls.archive = read_json(ROOT / "archive.json")["editions"]
        cls.baseline = load_observation(BASELINE, cls.dictionary)

    def test_closed_schema_accepts_baseline_and_fixtures(self):
        schema = read_json(MEASUREMENT / "observation.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        paths = [BASELINE] + sorted((FIXTURES / "week").glob("*.json"))
        for path in paths:
            with self.subTest(path=path):
                errors = sorted(validator.iter_errors(read_json(path)), key=str)
                self.assertEqual([], errors)

    def test_august_2_baseline_uses_actual_events_and_keeps_north_star_unknown(self):
        scorecard = build_daily_scorecard(
            self.baseline, self.archive, self.dictionary
        )
        operations = scorecard["operations"]
        self.assertEqual(924.545, operations["dispatch_to_site_latency_seconds"]["value"])
        self.assertEqual(1199.0, operations["dispatch_to_x_latency_seconds"]["value"])
        self.assertEqual(1.0, operations["edition_success_rate"]["value"])
        self.assertEqual(1.0, operations["telegram_success_rate"]["value"])
        self.assertEqual(1.0, operations["watchdog_success_rate"]["value"])
        self.assertEqual("unknown", scorecard["northStar"]["state"])
        self.assertEqual("not_authorized", scorecard["northStar"]["reason"])
        self.assertTrue(scorecard["privacy"]["aggregateOnly"])
        self.assertFalse(scorecard["privacy"]["piiCollected"])

        evening = next(
            item for item in scorecard["editions"] if item["slot"] == "evening"
        )
        self.assertFalse(evening["due"])
        self.assertEqual(
            "not_due",
            evening["metrics"]["edition_success"]["state"],
        )

    def test_last_known_x_floor_is_dated_and_not_claimed_as_current(self):
        scorecard = build_daily_scorecard(
            self.baseline, self.archive, self.dictionary
        )
        followers = scorecard["audience"]["x_followers"]
        self.assertEqual("observed", followers["state"])
        self.assertEqual(5, followers["value"])
        self.assertEqual("2026-07-31T19:53:41Z", followers["observedAt"])
        self.assertIn("not a current August 2 count", followers["note"])

    def test_missing_destination_is_unknown_not_zero_or_failure(self):
        observation = copy.deepcopy(self.baseline)
        morning = observation["editions"][0]
        morning["site"] = {
            "state": "unknown",
            "reason": "missing_public_verification",
        }
        scorecard = build_daily_scorecard(observation, self.archive, self.dictionary)
        latency = scorecard["operations"]["dispatch_to_site_latency_seconds"]
        success = scorecard["operations"]["edition_success_rate"]
        self.assertEqual("unknown", latency["state"])
        self.assertIsNone(latency["value"])
        self.assertEqual("unknown", success["state"])
        self.assertIsNone(success["value"])

    def test_exact_slot_archive_match_is_required_for_edition_success(self):
        without_morning = [
            item
            for item in self.archive
            if not (
                item.get("date") == "2026-08-02"
                and item.get("edition") == "morning"
            )
        ]
        scorecard = build_daily_scorecard(
            self.baseline, without_morning, self.dictionary
        )
        metric = scorecard["editions"][1]["metrics"]["edition_success"]
        self.assertEqual("observed", metric["state"])
        self.assertFalse(metric["value"])
        self.assertFalse(metric["archiveExactMatch"])

    def test_out_of_order_timestamp_fails_closed(self):
        observation = copy.deepcopy(self.baseline)
        observation["editions"][0]["site"]["occurredAt"] = "2026-08-02T11:39:59Z"
        with self.assertRaisesRegex(ScorecardError, "precedes actual dispatch"):
            build_daily_scorecard(observation, self.archive, self.dictionary)

    def test_weekly_fixture_has_complete_coverage_and_deterministic_percentiles(self):
        observations = [
            load_observation(path, self.dictionary)
            for path in sorted((FIXTURES / "week").glob("*.json"))
        ]
        archive = read_json(FIXTURES / "archive.json")["editions"]
        scorecard = build_weekly_scorecard(
            observations,
            date(2099, 1, 7),
            archive,
            self.dictionary,
            [],
        )
        site = scorecard["operations"]["dispatch_to_site_latency_seconds"]
        x_metric = scorecard["operations"]["dispatch_to_x_latency_seconds"]
        self.assertEqual("observed", site["state"])
        self.assertEqual(780.0, site["value"])
        self.assertEqual(960.0, site["p95"])
        self.assertEqual(7, site["sampleCount"])
        self.assertEqual(1080.0, x_metric["value"])
        self.assertEqual(1260.0, x_metric["p95"])
        self.assertEqual(1.0, scorecard["operations"]["edition_success_rate"]["value"])
        explicit_zero = scorecard["audience"]["x_impressions_7d"]
        self.assertEqual("observed", explicit_zero["state"])
        self.assertEqual(0, explicit_zero["value"])

    def test_missing_weekly_day_is_visible_and_rates_are_partial(self):
        paths = sorted((FIXTURES / "week").glob("*.json"))
        observations = [load_observation(path, self.dictionary) for path in paths[1:]]
        archive = read_json(FIXTURES / "archive.json")["editions"]
        scorecard = build_weekly_scorecard(
            observations,
            date(2099, 1, 7),
            archive,
            self.dictionary,
            ["2099-01-01"],
        )
        rate = scorecard["operations"]["edition_success_rate"]
        self.assertEqual("partial", rate["state"])
        self.assertEqual("incomplete_coverage", rate["reason"])
        self.assertEqual({"observed": 6, "expected": 7}, rate["dayCoverage"])
        self.assertEqual(["2099-01-01"], scorecard["period"]["missingDates"])

    def test_manual_validator_rejects_unexpected_pii_field(self):
        observation = copy.deepcopy(read_json(BASELINE))
        observation["audience"][0]["emailAddress"] = "reader@example.com"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observation.json"
            write_json(path, observation)
            with self.assertRaisesRegex(ScorecardError, "aggregate-only contract"):
                load_observation(path, self.dictionary)

    def test_first_party_metric_is_rejected_while_authority_is_false(self):
        observation = copy.deepcopy(read_json(BASELINE))
        metric = observation["audience"][0]
        metric.update(
            {
                "state": "observed",
                "value": 1,
                "observedAt": observation["capturedAt"],
                "sourceRef": "fixture:unauthorized-first-party-value",
                "reason": None,
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observation.json"
            write_json(path, observation)
            with self.assertRaisesRegex(ScorecardError, "unauthorized"):
                load_observation(path, self.dictionary)

    def test_rolling_metric_must_match_exact_seven_day_window(self):
        observation = copy.deepcopy(read_json(BASELINE))
        observation["audience"][0]["periodStart"] = "2026-07-28"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "observation.json"
            write_json(path, observation)
            with self.assertRaisesRegex(ScorecardError, "exact seven-day window"):
                load_observation(path, self.dictionary)

    def test_future_event_and_invalid_workflow_result_fail_closed(self):
        future = copy.deepcopy(read_json(BASELINE))
        future["editions"][0]["site"]["occurredAt"] = "2026-08-02T19:00:00Z"
        invalid_workflow = copy.deepcopy(read_json(BASELINE))
        invalid_workflow["editions"][0]["workflow"]["conclusion"] = "green"
        invalid_http = copy.deepcopy(read_json(BASELINE))
        invalid_http["editions"][0]["site"]["httpStatus"] = 700
        with tempfile.TemporaryDirectory() as tmp:
            for name, value, message in (
                ("future.json", future, "later than capturedAt"),
                ("workflow.json", invalid_workflow, "recognized workflow result"),
                ("http.json", invalid_http, "between 100 and 599"),
            ):
                path = Path(tmp) / name
                write_json(path, value)
                with self.subTest(name=name), self.assertRaisesRegex(
                    ScorecardError, message
                ):
                    load_observation(path, self.dictionary)

    def test_success_receipts_cannot_precede_actual_dispatch(self):
        for field in ("telegram", "watchdog"):
            observation = copy.deepcopy(read_json(BASELINE))
            observation["editions"][0][field]["occurredAt"] = (
                "2026-08-02T04:40:09-07:00"
            )
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"{field}.json"
                write_json(path, observation)
                with self.subTest(field=field), self.assertRaisesRegex(
                    ScorecardError, "cannot precede actual dispatch"
                ):
                    load_observation(path, self.dictionary)

    def test_manual_validator_matches_schema_note_types(self):
        cases = []
        top = copy.deepcopy(read_json(BASELINE))
        top["notes"] = 42
        cases.append(("top", top))
        event = copy.deepcopy(read_json(BASELINE))
        event["editions"][0]["site"]["note"] = 42
        cases.append(("event", event))
        audience = copy.deepcopy(read_json(BASELINE))
        audience["audience"][0]["note"] = 42
        cases.append(("audience", audience))
        with tempfile.TemporaryDirectory() as tmp:
            for name, observation in cases:
                path = Path(tmp) / f"{name}.json"
                write_json(path, observation)
                with self.subTest(name=name), self.assertRaisesRegex(
                    ScorecardError, "must be a string"
                ):
                    load_observation(path, self.dictionary)

    def test_weekly_rolling_metric_requires_week_ending_snapshot(self):
        paths = sorted((FIXTURES / "week").glob("*.json"))[:-1]
        observations = [load_observation(path, self.dictionary) for path in paths]
        archive = read_json(FIXTURES / "archive.json")["editions"]
        scorecard = build_weekly_scorecard(
            observations,
            date(2099, 1, 7),
            archive,
            self.dictionary,
            ["2099-01-07"],
        )
        self.assertEqual("unknown", scorecard["northStar"]["state"])
        self.assertEqual(
            "missing_week_ending_snapshot", scorecard["northStar"]["reason"]
        )
        self.assertEqual("2099-01-01", scorecard["northStar"]["periodStart"])
        self.assertEqual("2099-01-07", scorecard["northStar"]["periodEnd"])

    def test_daily_cli_is_reproducible_and_reports_exact_baseline(self):
        argv = [
            "daily",
            "--date",
            "2026-08-02",
            "--observations",
            str(BASELINE),
            "--archive",
            str(ROOT / "archive.json"),
            "--format",
            "json",
        ]
        outputs = []
        for _ in range(2):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(0, main(argv))
            outputs.append(stdout.getvalue())
        self.assertEqual(outputs[0], outputs[1])
        parsed = json.loads(outputs[0])
        self.assertEqual(
            924.545,
            parsed["operations"]["dispatch_to_site_latency_seconds"]["value"],
        )

    def test_cli_validation_failure_is_visible(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = main(
                [
                    "daily",
                    "--date",
                    "2026-08-03",
                    "--observations",
                    str(BASELINE),
                ]
            )
        self.assertEqual(1, result)
        self.assertIn("does not match requested date", stderr.getvalue())

    def test_experiment_template_has_seven_days_and_explicit_decision_thresholds(self):
        ledger = read_json(
            MEASUREMENT / "experiments" / "seven-day-ledger.template.json"
        )
        self.assertTrue(ledger["isTemplate"])
        self.assertEqual(7, ledger["window"]["days"])
        self.assertEqual(7, len(ledger["dailyChecks"]))
        self.assertEqual(7, ledger["primaryDecision"]["minimumObservedDays"])
        self.assertEqual(">=", ledger["primaryDecision"]["passThreshold"]["operator"])
        self.assertEqual("<=", ledger["primaryDecision"]["failThreshold"]["operator"])
        self.assertEqual("inconclusive", ledger["primaryDecision"]["unknownBehavior"])
        self.assertFalse(ledger["authority"]["externalActionAuthorized"])
        self.assertFalse(ledger["authority"]["spendAuthorized"])
        self.assertEqual(0, ledger["authority"]["maximumSpendUsd"])
        guardrails = {item["metricId"]: item for item in ledger["guardrails"]}
        self.assertTrue(set(guardrails).issubset(self.dictionary["byId"]))
        self.assertEqual("p95", guardrails["dispatch_to_site_latency_seconds"]["statistic"])
        self.assertEqual("p95", guardrails["dispatch_to_x_latency_seconds"]["statistic"])
        kill_rules = {item["id"] for item in ledger["killRules"]}
        self.assertEqual(
            {"privacy_boundary_breach", "unsupported_claim"}, kill_rules
        )


if __name__ == "__main__":
    unittest.main()
