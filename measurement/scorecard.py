#!/usr/bin/env python3
"""Offline, aggregate-only daily and weekly scorecards for David's Daily Bread."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = Path(__file__).with_name("metric_dictionary.json")
DEFAULT_AUTHORITY = Path(__file__).with_name("authority.json")
VALID_STATES = {"observed", "unknown", "not_due", "not_applicable"}
SLOTS = {"morning", "evening"}
FIRST_PARTY_METRICS = {
    "genuinely_engaged_returning_people_7d",
    "first_party_returning_readers_7d",
}


class ScorecardError(ValueError):
    """Raised when normalized observations are incomplete or contradictory."""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScorecardError(f"cannot read JSON from {path}: {exc}") from exc


def _require_keys(
    value: Mapping[str, Any],
    required: Iterable[str],
    optional: Iterable[str],
    where: str,
) -> None:
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - set(value))
    extra = sorted(set(value) - allowed)
    if missing:
        raise ScorecardError(f"{where} is missing required fields: {', '.join(missing)}")
    if extra:
        raise ScorecardError(
            f"{where} contains fields outside the aggregate-only contract: {', '.join(extra)}"
        )


def _parse_datetime(value: Any, where: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ScorecardError(f"{where} must be a non-empty ISO 8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ScorecardError(f"{where} is not a valid ISO 8601 timestamp: {value}") from exc
    if parsed.tzinfo is None:
        raise ScorecardError(f"{where} must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def _parse_date(value: Any, where: str) -> date:
    if not isinstance(value, str):
        raise ScorecardError(f"{where} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ScorecardError(f"{where} must be YYYY-MM-DD") from exc


def _validate_event(event: Any, kind: str, where: str) -> None:
    if not isinstance(event, dict):
        raise ScorecardError(f"{where} must be an object")
    state = event.get("state")
    if state not in VALID_STATES:
        raise ScorecardError(f"{where}.state must be one of {sorted(VALID_STATES)}")
    if "note" in event and not isinstance(event["note"], str):
        raise ScorecardError(f"{where}.note must be a string")
    common = {"state", "occurredAt", "sourceRef", "reason", "note"}
    specific = {
        "dispatch": set(),
        "site": {"httpStatus", "exactTitleVerified"},
        "workflow": {"conclusion"},
        "x": {"status"},
        "telegram": {"status"},
        "watchdog": {"result"},
    }[kind]
    allowed = common | specific if state == "observed" else common
    _require_keys(event, {"state"}, allowed - {"state"}, where)
    if state == "observed":
        if kind != "workflow" or event.get("occurredAt") is not None:
            _parse_datetime(event.get("occurredAt"), f"{where}.occurredAt")
        if not isinstance(event.get("sourceRef"), str) or not event["sourceRef"]:
            raise ScorecardError(f"{where}.sourceRef is required when state is observed")
        if event.get("reason") is not None:
            raise ScorecardError(f"{where}.reason must be null or absent when observed")
        required_by_kind = {
            "dispatch": (),
            "site": ("httpStatus", "exactTitleVerified"),
            "workflow": ("conclusion",),
            "x": ("status",),
            "telegram": ("status",),
            "watchdog": ("result",),
        }[kind]
        for field in required_by_kind:
            if field not in event:
                raise ScorecardError(f"{where}.{field} is required when state is observed")
        if kind == "site":
            if (
                not isinstance(event["httpStatus"], int)
                or isinstance(event["httpStatus"], bool)
                or not 100 <= event["httpStatus"] <= 599
            ):
                raise ScorecardError(f"{where}.httpStatus must be between 100 and 599")
            if not isinstance(event["exactTitleVerified"], bool):
                raise ScorecardError(f"{where}.exactTitleVerified must be boolean")
        if kind == "workflow" and event["conclusion"] not in {
            "success",
            "failure",
            "cancelled",
            "timed_out",
        }:
            raise ScorecardError(f"{where}.conclusion is not a recognized workflow result")
        if kind in {"x", "telegram"} and (
            not isinstance(event["status"], str) or not event["status"]
        ):
            raise ScorecardError(f"{where}.status must be a non-empty string")
        if kind == "watchdog" and (
            not isinstance(event["result"], str) or not event["result"]
        ):
            raise ScorecardError(f"{where}.result must be a non-empty string")
    else:
        if event.get("occurredAt") is not None:
            raise ScorecardError(f"{where}.occurredAt must be null or absent when not observed")
        if event.get("sourceRef") is not None:
            raise ScorecardError(f"{where}.sourceRef must be null or absent when not observed")
        if not isinstance(event.get("reason"), str) or not event["reason"]:
            raise ScorecardError(f"{where}.reason is required when state is {state}")


def load_dictionary(path: Path = DEFAULT_DICTIONARY) -> Dict[str, Any]:
    value = _load_json(path)
    if not isinstance(value, dict):
        raise ScorecardError("metric dictionary must be an object")
    _require_keys(
        value,
        {"version", "northStarMetricId", "proxyStages", "metrics"},
        set(),
        "metric dictionary",
    )
    if value["version"] != 1:
        raise ScorecardError("unsupported metric dictionary version")
    metrics = value["metrics"]
    if not isinstance(metrics, list) or not metrics:
        raise ScorecardError("metric dictionary metrics must be a non-empty array")
    by_id: Dict[str, Any] = {}
    for index, metric in enumerate(metrics):
        where = f"metric dictionary metrics[{index}]"
        if not isinstance(metric, dict):
            raise ScorecardError(f"{where} must be an object")
        _require_keys(
            metric,
            {
                "id",
                "label",
                "category",
                "unit",
                "formula",
                "sources",
                "cadence",
                "owner",
                "unknownBehavior",
            },
            {"window"},
            where,
        )
        metric_id = metric["id"]
        if not isinstance(metric_id, str) or not metric_id:
            raise ScorecardError(f"{where}.id must be a non-empty string")
        if metric_id in by_id:
            raise ScorecardError(f"duplicate metric id: {metric_id}")
        by_id[metric_id] = metric
    if value["northStarMetricId"] not in by_id:
        raise ScorecardError("northStarMetricId is absent from metrics")
    if not isinstance(value["proxyStages"], list) or not value["proxyStages"]:
        raise ScorecardError("metric dictionary proxyStages must be a non-empty array")
    seen_stages = set()
    for index, stage in enumerate(value["proxyStages"]):
        where = f"metric dictionary proxyStages[{index}]"
        if not isinstance(stage, dict):
            raise ScorecardError(f"{where} must be an object")
        _require_keys(
            stage,
            {"stage", "label", "interpretation", "metricIds"},
            set(),
            where,
        )
        if not isinstance(stage["stage"], int) or stage["stage"] < 1:
            raise ScorecardError(f"{where}.stage must be a positive integer")
        if stage["stage"] in seen_stages:
            raise ScorecardError(f"duplicate proxy stage: {stage['stage']}")
        seen_stages.add(stage["stage"])
        if not isinstance(stage["metricIds"], list) or not stage["metricIds"]:
            raise ScorecardError(f"{where}.metricIds must be a non-empty array")
        missing_metrics = [item for item in stage["metricIds"] if item not in by_id]
        if missing_metrics:
            raise ScorecardError(
                f"{where} references unknown metrics: {', '.join(missing_metrics)}"
            )
    value["byId"] = by_id
    return value


def load_authority(path: Path = DEFAULT_AUTHORITY) -> Dict[str, Any]:
    value = _load_json(path)
    if not isinstance(value, dict):
        raise ScorecardError(f"{path} must contain an object")
    _require_keys(
        value,
        {
            "version",
            "firstPartyReturnMeasurementAuthorized",
            "authorizedAt",
            "decisionRef",
        },
        set(),
        str(path),
    )
    if value["version"] != 1:
        raise ScorecardError(f"{path} has unsupported authority version")
    authorized = value["firstPartyReturnMeasurementAuthorized"]
    if not isinstance(authorized, bool):
        raise ScorecardError(
            f"{path}.firstPartyReturnMeasurementAuthorized must be boolean"
        )
    if not isinstance(value["decisionRef"], str) or not value["decisionRef"]:
        raise ScorecardError(f"{path}.decisionRef must be a non-empty string")
    if authorized:
        _parse_datetime(value["authorizedAt"], f"{path}.authorizedAt")
    elif value["authorizedAt"] is not None:
        raise ScorecardError(f"{path}.authorizedAt must be null while unauthorized")
    return value


def load_observation(
    path: Path,
    dictionary: Mapping[str, Any],
    authority: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if authority is None:
        authority = load_authority()
    value = _load_json(path)
    if not isinstance(value, dict):
        raise ScorecardError(f"{path} must contain an object")
    _require_keys(
        value,
        {"version", "date", "capturedAt", "timezone", "editions", "audience"},
        {"notes"},
        str(path),
    )
    if value["version"] != 1:
        raise ScorecardError(f"{path} has unsupported observation version")
    if "notes" in value and not isinstance(value["notes"], str):
        raise ScorecardError(f"{path}.notes must be a string")
    observation_date = _parse_date(value["date"], f"{path}.date")
    captured_at = _parse_datetime(value["capturedAt"], f"{path}.capturedAt")
    if value["timezone"] != "America/Los_Angeles":
        raise ScorecardError(f"{path}.timezone must be America/Los_Angeles")
    if captured_at.astimezone(ZoneInfo(value["timezone"])).date() != observation_date:
        raise ScorecardError(f"{path}.capturedAt must fall on the observation date")
    if not isinstance(value["editions"], list):
        raise ScorecardError(f"{path}.editions must be an array")
    seen_editions = set()
    for index, edition in enumerate(value["editions"]):
        where = f"{path}.editions[{index}]"
        if not isinstance(edition, dict):
            raise ScorecardError(f"{where} must be an object")
        _require_keys(
            edition,
            {
                "editionId",
                "slot",
                "due",
                "dispatch",
                "site",
                "workflow",
                "x",
                "telegram",
                "watchdog",
            },
            set(),
            where,
        )
        slot = edition["slot"]
        if slot not in SLOTS:
            raise ScorecardError(f"{where}.slot must be morning or evening")
        expected_id = f"{value['date']}-{slot}"
        if edition["editionId"] != expected_id:
            raise ScorecardError(f"{where}.editionId must be {expected_id}")
        if expected_id in seen_editions:
            raise ScorecardError(f"duplicate edition observation: {expected_id}")
        seen_editions.add(expected_id)
        if not isinstance(edition["due"], bool):
            raise ScorecardError(f"{where}.due must be boolean")
        for kind in ("dispatch", "site", "workflow", "x", "telegram", "watchdog"):
            _validate_event(edition[kind], kind, f"{where}.{kind}")
            occurred_at = edition[kind].get("occurredAt")
            if edition[kind]["state"] == "observed" and occurred_at is not None:
                occurred = _parse_datetime(occurred_at, f"{where}.{kind}.occurredAt")
                if occurred > captured_at:
                    raise ScorecardError(
                        f"{where}.{kind}.occurredAt cannot be later than capturedAt"
                    )
                if occurred.astimezone(ZoneInfo(value["timezone"])).date() != observation_date:
                    raise ScorecardError(
                        f"{where}.{kind}.occurredAt must fall on the observation date"
                    )
        if edition["dispatch"]["state"] == "observed":
            dispatched_at = _parse_datetime(
                edition["dispatch"]["occurredAt"], f"{where}.dispatch.occurredAt"
            )
            for kind in ("site", "x", "telegram", "watchdog"):
                event = edition[kind]
                if event["state"] != "observed":
                    continue
                occurred_at = _parse_datetime(
                    event["occurredAt"], f"{where}.{kind}.occurredAt"
                )
                if occurred_at < dispatched_at:
                    raise ScorecardError(
                        f"{where}.{kind}.occurredAt cannot precede actual dispatch"
                    )
        if not edition["due"]:
            for kind in ("dispatch", "site", "workflow", "x", "telegram", "watchdog"):
                if edition[kind]["state"] not in {"not_due", "not_applicable"}:
                    raise ScorecardError(
                        f"{where}.{kind}.state cannot be {edition[kind]['state']} when due is false"
                    )

    if not isinstance(value["audience"], list):
        raise ScorecardError(f"{path}.audience must be an array")
    known_ids = set(dictionary["byId"])
    seen_metrics = set()
    for index, metric in enumerate(value["audience"]):
        where = f"{path}.audience[{index}]"
        if not isinstance(metric, dict):
            raise ScorecardError(f"{where} must be an object")
        _require_keys(
            metric,
            {
                "metricId",
                "state",
                "value",
                "unit",
                "observedAt",
                "periodStart",
                "periodEnd",
                "sourceRef",
                "reason",
            },
            {"note"},
            where,
        )
        metric_id = metric["metricId"]
        if metric_id not in known_ids:
            raise ScorecardError(f"{where}.metricId is not in the metric dictionary: {metric_id}")
        if metric_id in seen_metrics:
            raise ScorecardError(f"duplicate audience metric: {metric_id}")
        seen_metrics.add(metric_id)
        if dictionary["byId"][metric_id]["category"] != "audience":
            raise ScorecardError(f"{where}.metricId is not an audience metric")
        if metric["unit"] != dictionary["byId"][metric_id]["unit"]:
            raise ScorecardError(f"{where}.unit does not match the metric dictionary")
        if "note" in metric and not isinstance(metric["note"], str):
            raise ScorecardError(f"{where}.note must be a string")
        window = dictionary["byId"][metric_id].get("window")
        if window == "rolling_7d":
            period_start = _parse_date(metric["periodStart"], f"{where}.periodStart")
            period_end = _parse_date(metric["periodEnd"], f"{where}.periodEnd")
            if period_end != observation_date or (period_end - period_start).days != 6:
                raise ScorecardError(
                    f"{where} must cover the exact seven-day window ending {observation_date}"
                )
        elif window == "point_in_time":
            if metric["periodStart"] is not None or metric["periodEnd"] is not None:
                raise ScorecardError(
                    f"{where}.periodStart and periodEnd must be null for point-in-time metrics"
                )
        state = metric["state"]
        if state not in VALID_STATES:
            raise ScorecardError(f"{where}.state must be one of {sorted(VALID_STATES)}")
        if state == "observed":
            number = metric["value"]
            if isinstance(number, bool) or not isinstance(number, (int, float)) or number < 0:
                raise ScorecardError(f"{where}.value must be a non-negative number")
            observed_at = _parse_datetime(metric["observedAt"], f"{where}.observedAt")
            if observed_at > captured_at:
                raise ScorecardError(f"{where}.observedAt cannot be later than capturedAt")
            if not isinstance(metric["sourceRef"], str) or not metric["sourceRef"]:
                raise ScorecardError(f"{where}.sourceRef is required when observed")
            if metric["reason"] is not None:
                raise ScorecardError(f"{where}.reason must be null when observed")
            if (
                metric_id in FIRST_PARTY_METRICS
                and not authority["firstPartyReturnMeasurementAuthorized"]
            ):
                raise ScorecardError(
                    f"{where} cannot be observed while first-party return "
                    "measurement is unauthorized"
                )
        else:
            if metric["value"] is not None:
                raise ScorecardError(f"{where}.value must be null when state is {state}")
            if metric["observedAt"] is not None or metric["sourceRef"] is not None:
                raise ScorecardError(
                    f"{where}.observedAt and sourceRef must be null when state is {state}"
                )
            if not isinstance(metric["reason"], str) or not metric["reason"]:
                raise ScorecardError(f"{where}.reason is required when state is {state}")
    return value


def _archive_entries(path: Path) -> List[Mapping[str, Any]]:
    archive = _load_json(path)
    if not isinstance(archive, dict) or not isinstance(archive.get("editions"), list):
        raise ScorecardError(f"{path} does not contain an editions array")
    return archive["editions"]


def _archive_exact(entries: Sequence[Mapping[str, Any]], edition_id: str, slot: str) -> bool:
    day = edition_id[:10]
    expected_file = f"editions/{edition_id}.html"
    return any(
        entry.get("date") == day
        and entry.get("edition") == slot
        and entry.get("file") == expected_file
        for entry in entries
    )


def _event_reason(event: Mapping[str, Any], fallback: str) -> str:
    return str(event.get("reason") or fallback)


def _unknown_metric(
    unit: str,
    reason: str,
    expected: int = 1,
    observed: int = 0,
    state: str = "unknown",
) -> Dict[str, Any]:
    return {
        "state": state,
        "value": None,
        "unit": unit,
        "reason": reason,
        "coverage": {"observed": observed, "expected": expected},
        "sourceRefs": [],
    }


def _observed_metric(
    value: Any,
    unit: str,
    source_refs: Iterable[str],
    expected: int = 1,
    observed: int = 1,
    state: str = "observed",
    reason: Optional[str] = None,
    **extra: Any,
) -> Dict[str, Any]:
    result = {
        "state": state,
        "value": value,
        "unit": unit,
        "reason": reason,
        "coverage": {"observed": observed, "expected": expected},
        "sourceRefs": sorted(set(ref for ref in source_refs if ref)),
    }
    result.update(extra)
    return result


def _latency(
    edition: Mapping[str, Any],
    destination: str,
    unit: str = "seconds",
) -> Dict[str, Any]:
    dispatch = edition["dispatch"]
    endpoint = edition[destination]
    if not edition["due"]:
        return _unknown_metric(unit, "edition_not_due", state="not_due")
    if dispatch["state"] != "observed":
        return _unknown_metric(unit, _event_reason(dispatch, "dispatch_unknown"))
    if endpoint["state"] != "observed":
        return _unknown_metric(unit, _event_reason(endpoint, f"{destination}_unknown"))
    if destination == "site" and not (
        endpoint.get("httpStatus") == 200 and endpoint.get("exactTitleVerified") is True
    ):
        return _unknown_metric(unit, "site_not_verified")
    if destination == "x" and endpoint.get("status") not in {
        "published",
        "existing_provider_post",
        "sent",
    }:
        return _unknown_metric(unit, "x_not_published")
    start = _parse_datetime(dispatch["occurredAt"], "dispatch.occurredAt")
    finish = _parse_datetime(endpoint["occurredAt"], f"{destination}.occurredAt")
    seconds = (finish - start).total_seconds()
    if seconds < 0:
        raise ScorecardError(
            f"{edition['editionId']} {destination} timestamp precedes actual dispatch"
        )
    return _observed_metric(
        round(seconds, 3),
        unit,
        (dispatch.get("sourceRef"), endpoint.get("sourceRef")),
    )


def _edition_success(
    edition: Mapping[str, Any], archive_entries: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    if not edition["due"]:
        return _unknown_metric("boolean", "edition_not_due", state="not_due")
    workflow = edition["workflow"]
    site = edition["site"]
    if workflow["state"] != "observed":
        return _unknown_metric("boolean", _event_reason(workflow, "workflow_unknown"))
    if workflow.get("conclusion") != "success":
        return _observed_metric(False, "boolean", (workflow.get("sourceRef"),))
    if site["state"] != "observed":
        return _unknown_metric("boolean", _event_reason(site, "site_verification_unknown"))
    exact = _archive_exact(archive_entries, edition["editionId"], edition["slot"])
    succeeded = bool(
        exact and site.get("httpStatus") == 200 and site.get("exactTitleVerified") is True
    )
    return _observed_metric(
        succeeded,
        "boolean",
        (workflow.get("sourceRef"), site.get("sourceRef"), "archive.json"),
        archiveExactMatch=exact,
    )


def _status_success(
    edition: Mapping[str, Any],
    field: str,
    success_values: Iterable[str],
) -> Dict[str, Any]:
    if not edition["due"]:
        return _unknown_metric("boolean", "edition_not_due", state="not_due")
    event = edition[field]
    if event["state"] != "observed":
        return _unknown_metric("boolean", _event_reason(event, f"{field}_unknown"))
    key = "result" if field == "watchdog" else "status"
    return _observed_metric(
        event.get(key) in set(success_values),
        "boolean",
        (event.get("sourceRef"),),
    )


def build_edition_report(
    edition: Mapping[str, Any], archive_entries: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    return {
        "editionId": edition["editionId"],
        "slot": edition["slot"],
        "due": edition["due"],
        "metrics": {
            "dispatch_to_site_latency_seconds": _latency(edition, "site"),
            "dispatch_to_x_latency_seconds": _latency(edition, "x"),
            "edition_success": _edition_success(edition, archive_entries),
            "telegram_success": _status_success(edition, "telegram", {"sent"}),
            "watchdog_success": _status_success(
                edition, "watchdog", {"exact_edition_present"}
            ),
        },
        "observedStates": {
            name: edition[name]["state"]
            for name in ("dispatch", "site", "workflow", "x", "telegram", "watchdog")
        },
    }


def _aggregate_latency(
    editions: Sequence[Mapping[str, Any]],
    metric_id: str,
    missing_dates: Sequence[str],
) -> Dict[str, Any]:
    due = [edition for edition in editions if edition["due"]]
    metrics = [edition["metrics"][metric_id] for edition in due]
    observed_metrics = [metric for metric in metrics if metric["state"] == "observed"]
    expected = len(due)
    if not due and not missing_dates:
        return _unknown_metric("seconds", "no_editions_due", 0, 0, state="not_due")
    if not observed_metrics:
        reason = "missing_observation_days" if missing_dates else "no_observed_latency"
        return _unknown_metric("seconds", reason, expected, 0)
    values = sorted(float(metric["value"]) for metric in observed_metrics)
    p95_index = max(0, math.ceil(0.95 * len(values)) - 1)
    complete = len(observed_metrics) == expected and not missing_dates
    state = "observed" if complete else "partial"
    reason = None if complete else "incomplete_coverage"
    return _observed_metric(
        round(float(statistics.median(values)), 3),
        "seconds",
        (ref for metric in observed_metrics for ref in metric["sourceRefs"]),
        expected=expected,
        observed=len(observed_metrics),
        state=state,
        reason=reason,
        statistic="median",
        p95=round(values[p95_index], 3),
        sampleCount=len(values),
    )


def _aggregate_rate(
    editions: Sequence[Mapping[str, Any]],
    metric_id: str,
    missing_dates: Sequence[str],
) -> Dict[str, Any]:
    due = [edition for edition in editions if edition["due"]]
    metrics = [edition["metrics"][metric_id] for edition in due]
    observed_metrics = [metric for metric in metrics if metric["state"] == "observed"]
    expected = len(due)
    if not due and not missing_dates:
        return _unknown_metric("ratio", "no_editions_due", 0, 0, state="not_due")
    if not observed_metrics:
        reason = "missing_observation_days" if missing_dates else "no_observed_outcomes"
        return _unknown_metric("ratio", reason, expected, 0)
    passed = sum(1 for metric in observed_metrics if metric["value"] is True)
    complete = len(observed_metrics) == expected and not missing_dates
    state = "observed" if complete else "partial"
    reason = None if complete else "incomplete_coverage"
    return _observed_metric(
        round(passed / len(observed_metrics), 6),
        "ratio",
        (ref for metric in observed_metrics for ref in metric["sourceRefs"]),
        expected=expected,
        observed=len(observed_metrics),
        state=state,
        reason=reason,
        numerator=passed,
        denominator=len(observed_metrics),
    )


def _audience_snapshot(
    observation: Mapping[str, Any],
    dictionary: Mapping[str, Any],
    required_window_end: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    supplied = {metric["metricId"]: metric for metric in observation["audience"]}
    result: Dict[str, Dict[str, Any]] = {}
    for metric_id, definition in dictionary["byId"].items():
        if definition["category"] != "audience":
            continue
        metric = supplied.get(metric_id)
        rolling = definition.get("window") == "rolling_7d"
        if rolling and required_window_end and observation["date"] != required_window_end:
            result[metric_id] = _unknown_metric(
                definition["unit"], "missing_week_ending_snapshot", 1, 0
            )
            result[metric_id]["periodStart"] = (
                date.fromisoformat(required_window_end) - timedelta(days=6)
            ).isoformat()
            result[metric_id]["periodEnd"] = required_window_end
            continue
        if metric is None:
            result[metric_id] = _unknown_metric(
                definition["unit"], "not_in_observation", 1, 0
            )
            if rolling:
                end = required_window_end or observation["date"]
                result[metric_id]["periodStart"] = (
                    date.fromisoformat(end) - timedelta(days=6)
                ).isoformat()
                result[metric_id]["periodEnd"] = end
            else:
                result[metric_id]["periodStart"] = None
                result[metric_id]["periodEnd"] = None
            continue
        if metric["state"] != "observed":
            result[metric_id] = _unknown_metric(
                metric["unit"], metric["reason"], 1, 0, state=metric["state"]
            )
            if metric.get("note"):
                result[metric_id]["note"] = metric["note"]
            result[metric_id]["periodStart"] = metric["periodStart"]
            result[metric_id]["periodEnd"] = metric["periodEnd"]
            continue
        result[metric_id] = _observed_metric(
            metric["value"],
            metric["unit"],
            (metric["sourceRef"],),
            observedAt=metric["observedAt"],
            periodStart=metric["periodStart"],
            periodEnd=metric["periodEnd"],
        )
        if metric.get("note"):
            result[metric_id]["note"] = metric["note"]
    return result


def _proxy_stages(
    dictionary: Mapping[str, Any],
    operations: Mapping[str, Any],
    audience: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    combined = dict(operations)
    combined.update(audience)
    stages = []
    for stage in dictionary["proxyStages"]:
        stages.append(
            {
                "stage": stage["stage"],
                "label": stage["label"],
                "interpretation": stage["interpretation"],
                "metrics": {
                    metric_id: combined.get(
                        metric_id,
                        _unknown_metric(
                            dictionary["byId"][metric_id]["unit"],
                            "not_computable_for_period",
                        ),
                    )
                    for metric_id in stage["metricIds"]
                },
            }
        )
    return stages


def _operations(
    edition_reports: Sequence[Mapping[str, Any]],
    missing_dates: Sequence[str],
    observed_days: int = 1,
    expected_days: int = 1,
) -> Dict[str, Any]:
    result = {
        "dispatch_to_site_latency_seconds": _aggregate_latency(
            edition_reports, "dispatch_to_site_latency_seconds", missing_dates
        ),
        "dispatch_to_x_latency_seconds": _aggregate_latency(
            edition_reports, "dispatch_to_x_latency_seconds", missing_dates
        ),
        "edition_success_rate": _aggregate_rate(
            edition_reports, "edition_success", missing_dates
        ),
        "telegram_success_rate": _aggregate_rate(
            edition_reports, "telegram_success", missing_dates
        ),
        "watchdog_success_rate": _aggregate_rate(
            edition_reports, "watchdog_success", missing_dates
        ),
    }
    for metric in result.values():
        metric["dayCoverage"] = {
            "observed": observed_days,
            "expected": expected_days,
        }
    return result


def build_daily_scorecard(
    observation: Mapping[str, Any],
    archive_entries: Sequence[Mapping[str, Any]],
    dictionary: Mapping[str, Any],
) -> Dict[str, Any]:
    editions = [
        build_edition_report(edition, archive_entries)
        for edition in sorted(observation["editions"], key=lambda item: item["slot"])
    ]
    operations = _operations(editions, [])
    audience = _audience_snapshot(
        observation,
        dictionary,
        required_window_end=observation["date"],
    )
    north_star = audience[dictionary["northStarMetricId"]]
    return {
        "version": 1,
        "period": {
            "kind": "daily",
            "date": observation["date"],
            "capturedAt": observation["capturedAt"],
            "timezone": observation["timezone"],
        },
        "northStar": {
            "metricId": dictionary["northStarMetricId"],
            **north_star,
        },
        "proxyStages": _proxy_stages(dictionary, operations, audience),
        "operations": operations,
        "audience": audience,
        "editions": editions,
        "privacy": {
            "aggregateOnly": True,
            "piiCollected": False,
            "cookiesUsed": False,
            "fingerprintingUsed": False,
        },
    }


def _date_range(week_ending: date) -> List[date]:
    return [week_ending - timedelta(days=offset) for offset in range(6, -1, -1)]


def build_weekly_scorecard(
    observations: Sequence[Mapping[str, Any]],
    week_ending: date,
    archive_entries: Sequence[Mapping[str, Any]],
    dictionary: Mapping[str, Any],
    missing_dates: Sequence[str],
) -> Dict[str, Any]:
    ordered = sorted(observations, key=lambda item: item["date"])
    editions = [
        build_edition_report(edition, archive_entries)
        for observation in ordered
        for edition in sorted(observation["editions"], key=lambda item: item["slot"])
    ]
    operations = _operations(
        editions,
        missing_dates,
        observed_days=len(ordered),
        expected_days=7,
    )
    if ordered:
        latest = ordered[-1]
        audience = _audience_snapshot(
            latest,
            dictionary,
            required_window_end=week_ending.isoformat(),
        )
        captured_at = max(item["capturedAt"] for item in ordered)
    else:
        audience = {}
        for metric_id, definition in dictionary["byId"].items():
            if definition["category"] != "audience":
                continue
            metric = _unknown_metric(definition["unit"], "no_observations_in_window")
            if definition.get("window") == "rolling_7d":
                metric["periodStart"] = (week_ending - timedelta(days=6)).isoformat()
                metric["periodEnd"] = week_ending.isoformat()
            else:
                metric["periodStart"] = None
                metric["periodEnd"] = None
            audience[metric_id] = metric
        captured_at = None
    north_star = audience[dictionary["northStarMetricId"]]
    return {
        "version": 1,
        "period": {
            "kind": "weekly",
            "startDate": (week_ending - timedelta(days=6)).isoformat(),
            "endDate": week_ending.isoformat(),
            "capturedAt": captured_at,
            "timezone": "America/Los_Angeles",
            "daysLoaded": len(ordered),
            "daysExpected": 7,
            "missingDates": list(missing_dates),
        },
        "northStar": {
            "metricId": dictionary["northStarMetricId"],
            **north_star,
        },
        "proxyStages": _proxy_stages(dictionary, operations, audience),
        "operations": operations,
        "audience": audience,
        "editions": editions,
        "privacy": {
            "aggregateOnly": True,
            "piiCollected": False,
            "cookiesUsed": False,
            "fingerprintingUsed": False,
        },
    }


def _metric_text(metric: Mapping[str, Any]) -> str:
    if metric["state"] not in {"observed", "partial"}:
        return f"unknown ({metric['reason']})"
    value = metric["value"]
    unit = metric["unit"]
    if unit == "ratio":
        rendered = f"{100 * float(value):.1f}%"
    elif unit == "seconds":
        rendered = f"{float(value):.3f} s"
    elif unit == "boolean":
        rendered = "pass" if value else "fail"
    else:
        rendered = f"{value} {unit}"
    if metric["state"] == "partial":
        rendered += " (partial)"
    return rendered


def render_markdown(scorecard: Mapping[str, Any], dictionary: Mapping[str, Any]) -> str:
    period = scorecard["period"]
    if period["kind"] == "daily":
        title = f"Daily scorecard: {period['date']}"
    else:
        title = f"Weekly scorecard: {period['startDate']} to {period['endDate']}"
    lines = [f"# {title}", ""]
    lines.append(
        "North star, genuinely engaged returning people: "
        + _metric_text(scorecard["northStar"])
    )
    lines.extend(
        [
            "",
            "## Operations",
            "",
            "| Metric | Result | Coverage |",
            "| --- | ---: | ---: |",
        ]
    )
    for metric_id, metric in scorecard["operations"].items():
        label = dictionary["byId"][metric_id]["label"]
        coverage = metric["coverage"]
        day_coverage = metric["dayCoverage"]
        lines.append(
            f"| {label} | {_metric_text(metric)} | "
            f"{coverage['observed']}/{coverage['expected']} outcomes; "
            f"{day_coverage['observed']}/{day_coverage['expected']} days |"
        )
    lines.extend(
        [
            "",
            "## Audience and return proxies",
            "",
            "| Metric | Result | Observed at |",
            "| --- | ---: | --- |",
        ]
    )
    for metric_id, metric in scorecard["audience"].items():
        label = dictionary["byId"][metric_id]["label"]
        observed_at = metric.get("observedAt") or "unknown"
        lines.append(f"| {label} | {_metric_text(metric)} | {observed_at} |")
    lines.extend(["", "## Edition evidence", ""])
    for edition in scorecard["editions"]:
        if not edition["due"]:
            lines.append(f"- {edition['editionId']}: not due at capture time")
            continue
        metrics = edition["metrics"]
        lines.append(
            f"- {edition['editionId']}: site "
            f"{_metric_text(metrics['dispatch_to_site_latency_seconds'])}; "
            f"X {_metric_text(metrics['dispatch_to_x_latency_seconds'])}; "
            f"edition {_metric_text(metrics['edition_success'])}; "
            f"Telegram {_metric_text(metrics['telegram_success'])}; "
            f"watchdog {_metric_text(metrics['watchdog_success'])}"
        )
    if period["kind"] == "weekly" and period["missingDates"]:
        lines.extend(["", "Missing observation dates: " + ", ".join(period["missingDates"])])
    lines.extend(
        [
            "",
            "Privacy: aggregate-only observations; no PII, cookies, or fingerprinting.",
        ]
    )
    return "\n".join(lines) + "\n"


def _emit(scorecard: Mapping[str, Any], output_format: str, dictionary: Mapping[str, Any]) -> None:
    if output_format == "json":
        print(json.dumps(scorecard, indent=2, sort_keys=True))
    else:
        print(render_markdown(scorecard, dictionary), end="")


def _daily_command(args: argparse.Namespace) -> int:
    dictionary = load_dictionary(args.dictionary)
    authority = load_authority()
    observation = load_observation(args.observations, dictionary, authority)
    if observation["date"] != args.date:
        raise ScorecardError(
            f"observation date {observation['date']} does not match requested date {args.date}"
        )
    scorecard = build_daily_scorecard(
        observation, _archive_entries(args.archive), dictionary
    )
    _emit(scorecard, args.format, dictionary)
    return 0


def _weekly_command(args: argparse.Namespace) -> int:
    dictionary = load_dictionary(args.dictionary)
    authority = load_authority()
    ending = _parse_date(args.week_ending, "--week-ending")
    observations = []
    missing = []
    for day in _date_range(ending):
        path = args.observations_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing.append(day.isoformat())
            continue
        observation = load_observation(path, dictionary, authority)
        if observation["date"] != day.isoformat():
            raise ScorecardError(f"{path} date does not match its filename")
        observations.append(observation)
    scorecard = build_weekly_scorecard(
        observations,
        ending,
        _archive_entries(args.archive),
        dictionary,
        missing,
    )
    _emit(scorecard, args.format, dictionary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build offline, aggregate-only David's Daily Bread scorecards."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    daily = subparsers.add_parser("daily", help="build one daily scorecard")
    daily.add_argument("--date", required=True)
    daily.add_argument("--observations", type=Path, required=True)
    daily.add_argument("--archive", type=Path, default=ROOT / "archive.json")
    daily.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    daily.add_argument("--format", choices=("json", "markdown"), default="markdown")
    daily.set_defaults(handler=_daily_command)

    weekly = subparsers.add_parser("weekly", help="build a seven-day scorecard")
    weekly.add_argument("--week-ending", required=True)
    weekly.add_argument("--observations-dir", type=Path, required=True)
    weekly.add_argument("--archive", type=Path, default=ROOT / "archive.json")
    weekly.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    weekly.add_argument("--format", choices=("json", "markdown"), default="markdown")
    weekly.set_defaults(handler=_weekly_command)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ScorecardError as exc:
        print(f"scorecard error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
