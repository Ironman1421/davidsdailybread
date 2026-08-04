#!/usr/bin/env python3
"""Validate the aggregate first-1,000 audience ledger and milestone evidence."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "audience" / "measurement.schema.json"
LEDGER_PATH = ROOT / "audience" / "monthly-ledger.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _month_number(period: str) -> int:
    year, month = period.split("-", 1)
    return int(year) * 12 + int(month)


def business_rule_errors(ledger: dict[str, Any]) -> list[str]:
    """Return milestone-consistency failures not expressible in JSON Schema."""

    errors: list[str] = []
    definition = ledger["milestoneDefinition"]
    target = definition["targetQualifiedReaders"]
    minimum_sessions = definition["minimumEngagedSessions"]
    required_consecutive = definition["consecutiveQualifyingMonthsRequired"]

    reports = ledger["months"]
    periods = [report["period"] for report in reports]
    if len(periods) != len(set(periods)):
        errors.append("monthly report periods must be unique")
    if periods != sorted(periods):
        errors.append("monthly reports must be stored in ascending period order")

    reports_by_period = {report["period"]: report for report in reports}
    qualifying_periods: list[str] = []

    for report in reports:
        if report["measurementStatus"] != "complete":
            continue
        metrics = report["metrics"]
        unique = metrics["uniqueVisitors"]
        returning = metrics["returningVisitors"]
        qualified = metrics["qualifiedEngagedReturningReaders"]
        engaged_sessions = metrics["engagedSessions"]

        captured = datetime.fromisoformat(
            report["capturedAt"].replace("Z", "+00:00")
        ).astimezone(ZoneInfo(definition["reportingTimeZone"]))
        captured_period = f"{captured.year:04d}-{captured.month:02d}"
        if _month_number(captured_period) <= _month_number(report["period"]):
            errors.append(
                f"{report['period']} complete report was captured before month end"
            )

        if not (qualified <= returning <= unique):
            errors.append(
                f"{report['period']} must satisfy qualified <= returning <= unique"
            )
        if (
            engaged_sessions is not None
            and engaged_sessions < qualified * minimum_sessions
        ):
            errors.append(
                f"{report['period']} has too few engaged sessions for its qualified readers"
            )
        if engaged_sessions is None and not any(
            "total engaged sessions" in limitation
            for limitation in report["limitations"]
        ):
            errors.append(
                f"{report['period']} must disclose why engaged sessions are unknown"
            )
        if qualified >= target:
            qualifying_periods.append(report["period"])

    qualifying_pairs = [
        pair
        for pair in zip(qualifying_periods, qualifying_periods[1:])
        if _month_number(pair[1]) - _month_number(pair[0]) == 1
    ]

    evidence = ledger["milestoneEvidence"]
    evidence_periods = evidence["qualifyingMonths"]
    if evidence["status"] == "achieved":
        if len(evidence_periods) != required_consecutive:
            errors.append(
                "achieved milestone evidence must name exactly two qualifying months"
            )
        elif any(period not in reports_by_period for period in evidence_periods):
            errors.append("milestone evidence references an absent monthly report")
        elif any(period not in qualifying_periods for period in evidence_periods):
            errors.append(
                "milestone evidence references a partial or below-target month"
            )
        elif any(
            _month_number(later) - _month_number(earlier) != 1
            for earlier, later in zip(evidence_periods, evidence_periods[1:])
        ):
            errors.append("milestone evidence months must be consecutive")
    elif qualifying_pairs:
        errors.append(
            "ledger contains two consecutive qualifying months but milestone is not achieved"
        )

    return errors


def validate_ledger(
    ledger: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_errors = [
        error.message for error in sorted(validator.iter_errors(ledger), key=str)
    ]
    if schema_errors:
        return schema_errors
    return business_rule_errors(ledger)


def main() -> int:
    schema = load_json(SCHEMA_PATH)
    ledger = load_json(LEDGER_PATH)
    errors = validate_ledger(ledger, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: audience monthly ledger satisfies schema and milestone rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
