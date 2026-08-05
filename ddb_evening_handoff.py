#!/usr/bin/env python3
"""Validate, fetch, or upload the unified DDB reviewed evening handoff."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib import error, parse, request
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "ddb-reviewed-evening-handoff-v1"
NOON_SCHEMA_VERSION = "x-manager-noon-research-v2"
EDITORIAL_RULE = {
    "version": "editorial-fit-v1",
    "weights": {
        "leverage": 0.4,
        "broadApplicability": 0.3,
        "repeatability": 0.2,
        "trendStrength": 0.1,
    },
    "gates": {
        "leverage": 65,
        "broadApplicability": 60,
        "repeatability": 50,
        "trendStrength": 45,
        "total": 60,
    },
}
AUTHORITY = {
    "editorialSelectionFinal": True,
    "publicationApproved": False,
    "selectionOwner": "David's Daily Bread",
    "publicationOwner": "existing-bake-workflow",
}
NOON_AUTHORITY = {
    "advisoryOnly": True,
    "verificationRequired": True,
    "publicationApproved": False,
    "maySelectForDdb": False,
    "mayPublish": False,
    "finalSelectionOwner": "David's Daily Bread",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
MAX_PACKET_VALIDITY_SECONDS = 18 * 60 * 60
PACIFIC = ZoneInfo("America/Los_Angeles")


class HandoffValidationError(ValueError):
    """Raised when a reviewed packet violates the transport contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None


def _calendar_date(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _non_x_https_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = parse.urlsplit(value)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and host != "x.com"
        and not host.endswith(".x.com")
        and host != "twitter.com"
        and not host.endswith(".twitter.com")
    )


def _x_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = parse.urlsplit(value)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return parsed.scheme == "https" and (
        host == "x.com"
        or host.endswith(".x.com")
        or host == "twitter.com"
        or host.endswith(".twitter.com")
    )


def _require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")


def _validate_research(research: Any, errors: list[str]) -> None:
    if not isinstance(research, dict):
        errors.append("research must be an object")
        return
    manager = research.get("xManager")
    ddb = research.get("ddb")
    if not isinstance(manager, dict):
        errors.append("research.xManager is required")
    else:
        if _timestamp(manager.get("completedAt")) is None:
            errors.append("research.xManager.completedAt must be an ISO UTC timestamp")
        if not SHA256_RE.fullmatch(str(manager.get("artifactSha256", ""))):
            errors.append("research.xManager.artifactSha256 must be a lowercase SHA-256")
        for input_name in ("xPro", "xRadar"):
            source = manager.get(input_name)
            if not isinstance(source, dict) or source.get("used") is not True:
                errors.append(f"research.xManager.{input_name}.used must be true")
                continue
            if _timestamp(source.get("observedAt")) is None:
                errors.append(
                    f"research.xManager.{input_name}.observedAt must be an ISO UTC timestamp"
                )
            _require_string(
                source.get("context"), f"research.xManager.{input_name}.context", errors
            )
    if not isinstance(ddb, dict):
        errors.append("research.ddb is required")
    else:
        if _timestamp(ddb.get("completedAt")) is None:
            errors.append("research.ddb.completedAt must be an ISO UTC timestamp")
        for flag in (
            "independentWebResearch",
            "primarySourcesChecked",
            "trendEvidenceChecked",
        ):
            if ddb.get(flag) is not True:
                errors.append(f"research.ddb.{flag} must be true")


def _validate_selected(item: Any, section: str, path: str, errors: list[str]) -> None:
    if not isinstance(item, dict):
        errors.append(f"{path} must be an object")
        return
    for field in ("id", "title", "summary", "seen", "action", "caveat"):
        _require_string(item.get(field), f"{path}.{field}", errors)
    uncertainty = item.get("uncertainty")
    if (
        not isinstance(uncertainty, list)
        or not uncertainty
        or any(not isinstance(note, str) or not note.strip() for note in uncertainty)
    ):
        errors.append(f"{path}.uncertainty must contain at least one honest limitation")
    if item.get("section") != section:
        errors.append(f"{path}.section must be {section}")
    for field in ("officialUrl", "trendUrl"):
        if not _non_x_https_url(item.get(field)):
            errors.append(f"{path}.{field} must be a non-X HTTPS URL")

    scores = item.get("editorialScores")
    score_keys = (
        "leverage",
        "broadApplicability",
        "repeatability",
        "trendStrength",
        "total",
    )
    if not isinstance(scores, dict):
        errors.append(f"{path}.editorialScores is required")
    else:
        usable_scores = True
        for key in score_keys:
            value = scores.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
                usable_scores = False
                errors.append(
                    f"{path}.editorialScores.{key} must be an integer from 0 to 100"
                )
        if usable_scores:
            calculated = int(
                scores["leverage"] * 0.4
                + scores["broadApplicability"] * 0.3
                + scores["repeatability"] * 0.2
                + scores["trendStrength"] * 0.1
                + 0.5
            )
            if scores["total"] != calculated:
                errors.append(
                    f"{path}.editorialScores.total must equal the 40/30/20/10 weighted score"
                )
            for key in score_keys:
                if scores[key] < EDITORIAL_RULE["gates"][key]:
                    errors.append(
                        f"{path}.editorialScores.{key} does not meet the editorial gate"
                    )
        if (
            scores.get("shelfEligible") is not True
            or scores.get("ruleVersion") != EDITORIAL_RULE["version"]
        ):
            errors.append(
                f"{path}.editorialScores must be shelf-eligible under editorial-fit-v1"
            )

    verification = item.get("verification")
    if not isinstance(verification, dict):
        errors.append(f"{path}.verification is required")
    else:
        if _timestamp(verification.get("officialSourceCheckedAt")) is None:
            errors.append(f"{path}.verification.officialSourceCheckedAt is invalid")
        if _timestamp(verification.get("trendSourceCheckedAt")) is None:
            errors.append(f"{path}.verification.trendSourceCheckedAt is invalid")
        claims = verification.get("claimsVerified")
        if (
            not isinstance(claims, list)
            or not claims
            or any(not isinstance(claim, str) or not claim.strip() for claim in claims)
        ):
            errors.append(f"{path}.verification.claimsVerified must be non-empty")

    lineage = item.get("sourceLineage")
    if not isinstance(lineage, dict):
        errors.append(f"{path}.sourceLineage is required")
    else:
        candidate_ids = lineage.get("xManagerCandidateIds")
        if not isinstance(candidate_ids, list) or any(
            not isinstance(candidate_id, str) or not candidate_id.strip()
            for candidate_id in candidate_ids or []
        ):
            errors.append(f"{path}.sourceLineage.xManagerCandidateIds must be an array")
        source_urls = lineage.get("ddbSourceUrls")
        if (
            not isinstance(source_urls, list)
            or len(source_urls) < 2
            or any(not _non_x_https_url(url) for url in source_urls)
        ):
            errors.append(
                f"{path}.sourceLineage.ddbSourceUrls must contain at least two non-X HTTPS URLs"
            )


def _validate_decisions(items: Any, decision: str, path: str, errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append(f"{path} must be an array")
        return
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        for field in ("id", "title", "reason"):
            _require_string(item.get(field), f"{item_path}.{field}", errors)
        if item.get("section") not in {"tools", "workflows"}:
            errors.append(f"{item_path}.section must be tools or workflows")
        if item.get("decision") != decision:
            errors.append(f"{item_path}.decision must be {decision}")
        scores = item.get("editorialScores")
        score_keys = (
            "leverage",
            "broadApplicability",
            "repeatability",
            "trendStrength",
            "total",
        )
        if (
            not isinstance(scores, dict)
            or any(
                isinstance(scores.get(key), bool)
                or not isinstance(scores.get(key), int)
                or not 0 <= scores[key] <= 100
                for key in score_keys
            )
            or not isinstance(scores.get("shelfEligible"), bool)
            or scores.get("ruleVersion") != EDITORIAL_RULE["version"]
        ):
            errors.append(
                f"{item_path}.editorialScores must preserve the complete editorial decision"
            )
        else:
            calculated = int(
                scores["leverage"] * 0.4
                + scores["broadApplicability"] * 0.3
                + scores["repeatability"] * 0.2
                + scores["trendStrength"] * 0.1
                + 0.5
            )
            if scores["total"] != calculated:
                errors.append(f"{item_path}.editorialScores.total is inconsistent")
        uncertainty = item.get("uncertainty")
        if (
            not isinstance(uncertainty, list)
            or not uncertainty
            or any(not isinstance(note, str) or not note.strip() for note in uncertainty)
        ):
            errors.append(
                f"{item_path}.uncertainty must preserve the decision's limitations"
            )
        lineage = item.get("sourceLineage")
        if (
            not isinstance(lineage, dict)
            or not isinstance(lineage.get("xManagerCandidateIds"), list)
            or any(
                not isinstance(candidate_id, str) or not candidate_id.strip()
                for candidate_id in lineage.get("xManagerCandidateIds", [])
            )
            or not isinstance(lineage.get("ddbSourceUrls"), list)
            or any(
                not _non_x_https_url(url)
                for url in lineage.get("ddbSourceUrls", [])
            )
        ):
            errors.append(
                f"{item_path}.sourceLineage must preserve X and DDB research lineage"
            )


def validate_packet(
    packet: Any,
    *,
    expected_date: str | None = None,
    now: datetime | None = None,
    require_fresh: bool = True,
) -> None:
    """Raise HandoffValidationError unless packet is bake-ready for one date."""

    errors: list[str] = []
    target_date: Any = None
    if not isinstance(packet, dict):
        raise HandoffValidationError(["packet must be a JSON object"])
    if packet.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if packet.get("status") != "ready":
        errors.append("status must be ready")
    edition = packet.get("targetEdition")
    if not isinstance(edition, dict):
        errors.append("targetEdition is required")
    else:
        target_date = edition.get("date")
        if not _calendar_date(target_date):
            errors.append("targetEdition.date must be YYYY-MM-DD")
        if packet.get("packetId") != f"{target_date}-evening":
            errors.append("packetId must match targetEdition.date and evening slot")
        if edition.get("slot") != "evening":
            errors.append("targetEdition.slot must be evening")
        if edition.get("timeZone") != "America/Los_Angeles":
            errors.append("targetEdition.timeZone must be America/Los_Angeles")
        if expected_date is not None and target_date != expected_date:
            errors.append(f"targetEdition.date must be {expected_date}")

    reviewed_at = _timestamp(packet.get("reviewedAt"))
    expires_at = _timestamp(packet.get("expiresAt"))
    if reviewed_at is None or expires_at is None:
        errors.append("reviewedAt and expiresAt must be ISO UTC timestamps")
    else:
        now = now or datetime.now(timezone.utc)
        if expires_at <= reviewed_at:
            errors.append("expiresAt must be after reviewedAt")
        if (expires_at - reviewed_at).total_seconds() > MAX_PACKET_VALIDITY_SECONDS:
            errors.append("packet validity window cannot exceed 18 hours")
        if require_fresh and expires_at <= now:
            errors.append("packet has expired")
        if reviewed_at.timestamp() > now.timestamp() + 5 * 60:
            errors.append("reviewedAt cannot be in the future")
        if _calendar_date(target_date) and reviewed_at.astimezone(PACIFIC).date().isoformat() != target_date:
            errors.append(
                "reviewedAt must fall on targetEdition.date in America/Los_Angeles"
            )

    _validate_research(packet.get("research"), errors)
    research = packet.get("research")
    if (
        reviewed_at is not None
        and isinstance(research, dict)
        and isinstance(research.get("xManager"), dict)
        and isinstance(research.get("ddb"), dict)
    ):
        x_completed_at = _timestamp(research["xManager"].get("completedAt"))
        ddb_completed_at = _timestamp(research["ddb"].get("completedAt"))
        if x_completed_at is not None and ddb_completed_at is not None:
            if x_completed_at > ddb_completed_at:
                errors.append("X Manager research must complete before DDB's combined review")
            if (reviewed_at - x_completed_at).total_seconds() > 6 * 60 * 60:
                errors.append(
                    "X Manager research cannot be more than six hours old at review time"
                )
            ddb_review_age = (reviewed_at - ddb_completed_at).total_seconds()
            if ddb_review_age < -5 * 60 or ddb_review_age > 60 * 60:
                errors.append("DDB research must complete within one hour before reviewedAt")
    if packet.get("editorialRule") != EDITORIAL_RULE:
        errors.append("editorialRule must preserve the exact 40/30/20/10 rule and gates")
    selection = packet.get("selection")
    if not isinstance(selection, dict):
        errors.append("selection is required")
    else:
        for section in ("tools", "workflows"):
            items = selection.get(section)
            if not isinstance(items, list) or not 2 <= len(items) <= 6:
                errors.append(f"selection.{section} must contain 2 to 6 items")
            else:
                for index, item in enumerate(items):
                    _validate_selected(
                        item, section, f"selection.{section}[{index}]", errors
                    )
    _validate_decisions(packet.get("holds"), "hold", "holds", errors)
    _validate_decisions(packet.get("rejections"), "reject", "rejections", errors)
    if packet.get("authority") != AUTHORITY:
        errors.append(
            "authority must make DDB selection final while withholding publication approval"
        )
    if errors:
        raise HandoffValidationError(errors)


def validate_noon_packet(packet: Any, *, expected_date: str | None = None) -> None:
    """Validate X Manager's completed-or-blocked advisory research record."""

    errors: list[str] = []
    target_date: Any = None
    if not isinstance(packet, dict):
        raise HandoffValidationError(["noon packet must be a JSON object"])
    if packet.get("schemaVersion") != NOON_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {NOON_SCHEMA_VERSION}")
    status = packet.get("status")
    if status not in {"completed", "blocked"}:
        errors.append("status must be completed or blocked")
    edition = packet.get("targetEdition")
    if not isinstance(edition, dict):
        errors.append("targetEdition is required")
    else:
        target_date = edition.get("date")
        if not _calendar_date(target_date):
            errors.append("targetEdition.date must be YYYY-MM-DD")
        if expected_date is not None and target_date != expected_date:
            errors.append(f"targetEdition.date must be {expected_date}")
        if edition.get("slot") != "evening":
            errors.append("targetEdition.slot must be evening")
        if edition.get("timeZone") != "America/Los_Angeles":
            errors.append("targetEdition.timeZone must be America/Los_Angeles")
    created_at = _timestamp(packet.get("createdAt"))
    if created_at is None:
        errors.append("createdAt must be an ISO UTC timestamp")
    elif (
        _calendar_date(target_date)
        and created_at.astimezone(PACIFIC).date().isoformat() != target_date
    ):
        errors.append(
            "createdAt must fall on targetEdition.date in America/Los_Angeles"
        )
    if packet.get("producer") != "X Manager, Tools and Workflows":
        errors.append("producer must be X Manager, Tools and Workflows")
    if packet.get("authority") != NOON_AUTHORITY:
        errors.append("noon authority must remain advisory and non-publishing")

    inputs = packet.get("researchInputs")
    if not isinstance(inputs, dict):
        errors.append("researchInputs is required")
    else:
        completed_observations: list[datetime] = []
        for input_name in ("xPro", "xRadar"):
            source = inputs.get(input_name)
            if not isinstance(source, dict) or source.get("requested") is not True:
                errors.append(f"researchInputs.{input_name}.requested must be true")
                continue
            _require_string(source.get("context"), f"researchInputs.{input_name}.context", errors)
            if status == "completed":
                if source.get("used") is not True:
                    errors.append(f"researchInputs.{input_name}.used must be true")
                observed_at = _timestamp(source.get("observedAt"))
                if observed_at is None:
                    errors.append(
                        f"researchInputs.{input_name}.observedAt must prove current use"
                    )
                else:
                    completed_observations.append(observed_at)
        monitor = inputs.get("xMonitor")
        if not isinstance(monitor, dict):
            errors.append("researchInputs.xMonitor is required")
        else:
            _require_string(monitor.get("context"), "researchInputs.xMonitor.context", errors)
            if status == "completed":
                if monitor.get("used") is not True:
                    errors.append("researchInputs.xMonitor.used must be true")
                monitor_observed_at = _timestamp(monitor.get("observedAt"))
                if monitor_observed_at is None:
                    errors.append("researchInputs.xMonitor.observedAt must prove current use")
                else:
                    completed_observations.append(monitor_observed_at)
            if not isinstance(monitor.get("newPaidRunTriggered"), bool):
                errors.append("researchInputs.xMonitor.newPaidRunTriggered must be boolean")
        if status == "completed" and inputs.get("primarySourcesChecked") is not True:
            errors.append("researchInputs.primarySourcesChecked must be true")
        if status == "completed" and created_at is not None:
            for observed_at in completed_observations:
                age_seconds = (created_at - observed_at).total_seconds()
                if age_seconds < -5 * 60 or age_seconds > 6 * 60 * 60:
                    errors.append(
                        "completed X Pro, X Radar, and monitor observations must be "
                        "within six hours before createdAt"
                    )
                    break

    candidates = packet.get("candidates")
    if not isinstance(candidates, dict):
        errors.append("candidates is required")
    else:
        for section in ("tools", "workflows"):
            items = candidates.get(section)
            if not isinstance(items, list):
                errors.append(f"candidates.{section} must be an array")
                continue
            if status == "completed" and not items:
                errors.append(f"candidates.{section} must not be empty when completed")
            for index, item in enumerate(items):
                path = f"candidates.{section}[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{path} must be an object")
                    continue
                for field in ("id", "title", "summary", "action", "caveat"):
                    _require_string(item.get(field), f"{path}.{field}", errors)
                if item.get("section") != section:
                    errors.append(f"{path}.section must be {section}")
                primary_urls = item.get("primarySourceUrls")
                if (
                    not isinstance(primary_urls, list)
                    or not primary_urls
                    or any(not _non_x_https_url(url) for url in primary_urls)
                ):
                    errors.append(f"{path}.primarySourceUrls must contain non-X HTTPS URLs")
                x_urls = item.get("xPostUrls")
                if (
                    not isinstance(x_urls, list)
                    or not x_urls
                    or any(not _x_url(url) for url in x_urls)
                ):
                    errors.append(f"{path}.xPostUrls must contain X post URLs")
                if _timestamp(item.get("observedAt")) is None:
                    errors.append(f"{path}.observedAt must be an ISO UTC timestamp")
                uncertainty = item.get("uncertainty")
                if (
                    not isinstance(uncertainty, list)
                    or not uncertainty
                    or any(not isinstance(note, str) or not note.strip() for note in uncertainty)
                ):
                    errors.append(f"{path}.uncertainty must be non-empty")
                scores = item.get("editorialScores")
                if not isinstance(scores, dict):
                    errors.append(f"{path}.editorialScores is required")
                else:
                    score_keys = (
                        "leverage",
                        "broadApplicability",
                        "repeatability",
                        "trendStrength",
                        "total",
                    )
                    if all(
                        isinstance(scores.get(key), int)
                        and not isinstance(scores.get(key), bool)
                        and 0 <= scores[key] <= 100
                        for key in score_keys
                    ):
                        calculated = int(
                            scores["leverage"] * 0.4
                            + scores["broadApplicability"] * 0.3
                            + scores["repeatability"] * 0.2
                            + scores["trendStrength"] * 0.1
                            + 0.5
                        )
                        if scores["total"] != calculated:
                            errors.append(f"{path}.editorialScores.total is inconsistent")
                    else:
                        errors.append(f"{path}.editorialScores values must be 0 to 100")
                    if scores.get("ruleVersion") != "editorial-fit-v1" or not isinstance(
                        scores.get("shelfEligible"), bool
                    ):
                        errors.append(f"{path}.editorialScores metadata is invalid")
                if item.get("verificationStatus") not in {
                    "primary-source-checked",
                    "needs-ddb-verification",
                }:
                    errors.append(f"{path}.verificationStatus is invalid")

    for decision_name in ("holds", "rejections"):
        decisions = packet.get(decision_name)
        if not isinstance(decisions, list):
            errors.append(f"{decision_name} must be an array")
    blocked_reasons = packet.get("blockedReasons")
    if not isinstance(blocked_reasons, list):
        errors.append("blockedReasons must be an array")
    elif status == "completed" and blocked_reasons:
        errors.append("completed noon packets cannot have blockedReasons")
    elif status == "blocked" and not blocked_reasons:
        errors.append("blocked noon packets must explain the blocker")
    if errors:
        raise HandoffValidationError(errors)


def _load_packet(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HandoffValidationError(["packet must be a JSON object"])
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sites_headers(token_env: str) -> dict[str, str]:
    token = os.environ.get(token_env, "")
    if not token:
        raise RuntimeError(f"required environment variable {token_env} is unavailable")
    return {"OAI-Sites-Authorization": f"Bearer {token}"}


def fetch_packet(
    base_url: str,
    target_date: str,
    output: Path,
    sites_token_env: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Fetch a reviewed packet, writing a non-blocking fallback on any error."""

    query = parse.urlencode({"date": target_date, "slot": "evening"})
    endpoint = f"{base_url.rstrip('/')}/api/ddb-handoff?{query}"
    try:
        req = request.Request(endpoint, headers=_sites_headers(sites_token_env))
        with request.urlopen(req, timeout=30) as response:
            body = response.read(128 * 1024 + 1)
        if len(body) > 128 * 1024:
            raise RuntimeError("reviewed handoff exceeded 128 KiB")
        payload = json.loads(body)
        validate_packet(payload, expected_date=target_date, now=now)
        _write_json(output, payload)
        return True
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        HandoffValidationError,
        error.URLError,
    ) as exc:
        reason = type(exc).__name__.lower()
        _write_json(
            output,
            {
                "schemaVersion": SCHEMA_VERSION,
                "available": False,
                "targetEdition": {"date": target_date, "slot": "evening"},
                "reason": reason,
            },
        )
        return False


def upload_packet(
    base_url: str,
    packet_path: Path,
    write_token_env: str,
    sites_token_env: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate and privately upload DDB's final reviewed packet."""

    packet = _load_packet(packet_path)
    validate_packet(packet, now=now)
    write_token = os.environ.get(write_token_env, "")
    if not write_token:
        raise RuntimeError(f"required environment variable {write_token_env} is unavailable")
    body = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    headers = _sites_headers(sites_token_env)
    headers.update(
        {
            "Authorization": f"Bearer {write_token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        }
    )
    req = request.Request(
        f"{base_url.rstrip('/')}/api/ddb-handoff",
        data=body,
        headers=headers,
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        receipt = json.loads(response.read(64 * 1024))
    if receipt.get("packetId") != packet["packetId"] or receipt.get("stored") is not True:
        raise RuntimeError("handoff store returned an invalid receipt")
    return receipt


def artifact_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input", type=Path, required=True)
    validate_parser.add_argument("--date")

    noon_parser = subparsers.add_parser("validate-noon")
    noon_parser.add_argument("--input", type=Path, required=True)
    noon_parser.add_argument("--date")

    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("--base-url", required=True)
    fetch_parser.add_argument("--date", required=True)
    fetch_parser.add_argument("--output", type=Path, required=True)
    fetch_parser.add_argument(
        "--sites-token-env", default="X_MONITOR_SITES_BYPASS_TOKEN"
    )

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("--base-url", required=True)
    upload_parser.add_argument("--input", type=Path, required=True)
    upload_parser.add_argument("--write-token-env", default="DDB_HANDOFF_WRITE_TOKEN")
    upload_parser.add_argument(
        "--sites-token-env", default="X_MONITOR_SITES_BYPASS_TOKEN"
    )

    digest_parser = subparsers.add_parser("sha256")
    digest_parser.add_argument("--input", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            packet = _load_packet(args.input)
            validate_packet(packet, expected_date=args.date)
            print(f"Validated {packet['packetId']} ({SCHEMA_VERSION})")
        elif args.command == "validate-noon":
            packet = _load_packet(args.input)
            validate_noon_packet(packet, expected_date=args.date)
            print(
                f"Validated X Manager noon packet for "
                f"{packet['targetEdition']['date']} ({packet['status']})"
            )
        elif args.command == "fetch":
            available = fetch_packet(
                args.base_url, args.date, args.output, args.sites_token_env
            )
            if available:
                print(f"Reviewed evening handoff ready for {args.date}")
            else:
                print(
                    "::warning::Reviewed evening handoff unavailable; "
                    "continuing with BAKE.md's normal source ladder."
                )
        elif args.command == "upload":
            receipt = upload_packet(
                args.base_url,
                args.input,
                args.write_token_env,
                args.sites_token_env,
            )
            print(f"Stored reviewed evening handoff {receipt['packetId']}")
        else:
            print(artifact_sha256(args.input))
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, error.URLError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
