#!/usr/bin/env python3
"""Validate and fetch the date-bound reviewed morning research packet."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request
from zoneinfo import ZoneInfo


LEDGER_SCHEMA_VERSION = "x-manager-morning-candidate-ledger-v1"
PACKET_SCHEMA_VERSION = "ddb-reviewed-morning-handoff-v1"
PACIFIC = ZoneInfo("America/Los_Angeles")
MORNING_RULE = {
    "version": "morning-editorial-v1",
    "weights": {
        "substance": 0.30,
        "sourceAuthority": 0.25,
        "verificationDepth": 0.20,
        "freshness": 0.15,
        "readerRelevance": 0.10,
    },
    "gates": {
        "substance": 60,
        "sourceAuthority": 60,
        "verificationDepth": 55,
        "freshness": 45,
        "readerRelevance": 50,
        "total": 58,
    },
}
AUTHORITY = {
    "editorialSelectionFinal": True,
    "publicationApproved": False,
    "selectionOwner": "David's Daily Bread",
    "publicationOwner": "existing-bake-workflow",
}
BEATS = ("technology", "markets", "science")
DECISIONS = ("selected", "hold", "reject")


class MorningHandoffValidationError(ValueError):
    """Raised when a ledger or reviewed packet violates its contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _calendar_date(value: Any) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat() == value
    except ValueError:
        return False


def _https_url(value: Any, *, allow_x: bool = True) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = parse.urlparse(value)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    host = (parsed.hostname or "").lower().removeprefix("www.")
    return allow_x or host not in {"x.com", "twitter.com"}


def _require_string(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")


def _validate_target(target: Any, expected_date: str | None, errors: list[str]) -> str | None:
    if not isinstance(target, dict):
        errors.append("targetEdition is required")
        return None
    target_date = target.get("date")
    if not _calendar_date(target_date):
        errors.append("targetEdition.date must be YYYY-MM-DD")
    if expected_date is not None and target_date != expected_date:
        errors.append(f"targetEdition.date must be {expected_date}")
    if target.get("slot") != "morning":
        errors.append("targetEdition.slot must be morning")
    if target.get("timeZone") != "America/Los_Angeles":
        errors.append("targetEdition.timeZone must be America/Los_Angeles")
    return target_date if isinstance(target_date, str) else None


def _validate_morning_scores(scores: Any, path: str, errors: list[str], *, selected: bool) -> None:
    if not isinstance(scores, dict):
        errors.append(f"{path} is required")
        return
    dimensions = tuple(MORNING_RULE["weights"])
    values: dict[str, int] = {}
    for key in (*dimensions, "total"):
        value = scores.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            errors.append(f"{path}.{key} must be an integer from 0 to 100")
        else:
            values[key] = value
    if len(values) == 6:
        total = int(sum(values[key] * MORNING_RULE["weights"][key] for key in dimensions) + 0.5)
        if values["total"] != total:
            errors.append(f"{path}.total must match morning-editorial-v1 weights")
        meets = all(values[key] >= MORNING_RULE["gates"][key] for key in dimensions)
        meets = meets and values["total"] >= MORNING_RULE["gates"]["total"]
        if scores.get("eligible") is not meets:
            errors.append(f"{path}.eligible must reflect the morning gates")
        if selected and not meets:
            errors.append(f"{path} must be eligible for a selected story")
    if scores.get("ruleVersion") != "morning-editorial-v1":
        errors.append(f"{path}.ruleVersion must be morning-editorial-v1")


def validate_candidate_ledger(ledger: Any, *, expected_date: str | None = None) -> None:
    errors: list[str] = []
    if not isinstance(ledger, dict):
        raise MorningHandoffValidationError(["ledger must be a JSON object"])
    if ledger.get("schemaVersion") != LEDGER_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {LEDGER_SCHEMA_VERSION}")
    target_date = _validate_target(ledger.get("targetEdition"), expected_date, errors)
    generated_at = _timestamp(ledger.get("generatedAt"))
    if generated_at is None:
        errors.append("generatedAt must be an ISO UTC timestamp")
    elif target_date and generated_at.astimezone(PACIFIC).date().isoformat() != target_date:
        errors.append("generatedAt must fall on the target Pacific date")
    manifest = ledger.get("sourceManifest")
    if not isinstance(manifest, dict):
        errors.append("sourceManifest is required")
    else:
        _require_string(manifest.get("version"), "sourceManifest.version", errors)
        if not re.fullmatch(r"[a-f0-9]{64}", str(manifest.get("sha256", ""))):
            errors.append("sourceManifest.sha256 must be a lowercase SHA-256")
    bounds = ledger.get("boundedInputs")
    if not isinstance(bounds, dict):
        errors.append("boundedInputs is required")
    else:
        if bounds.get("newPaidRunTriggered") is not False:
            errors.append("boundedInputs.newPaidRunTriggered must be false")
        if bounds.get("paidPostReads") != 0:
            errors.append("boundedInputs.paidPostReads must be zero")
        caps = bounds.get("caps")
        if not isinstance(caps, dict) or caps.get("maxPaidRuns") != 0 or caps.get("maxPaidPostReads") != 0:
            errors.append("boundedInputs paid-run and paid-read caps must be zero")
    candidates = ledger.get("candidates")
    ids: list[str] = []
    if not isinstance(candidates, list):
        errors.append("candidates must be an array")
    else:
        ranks = [item.get("rank") for item in candidates if isinstance(item, dict)]
        if ranks != list(range(1, len(candidates) + 1)):
            errors.append("candidates must carry deterministic contiguous ranks")
        for index, item in enumerate(candidates):
            path = f"candidates[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object")
                continue
            for field in ("candidateId", "title", "summary"):
                _require_string(item.get(field), f"{path}.{field}", errors)
            ids.append(item.get("candidateId"))
            if item.get("category") not in BEATS:
                errors.append(f"{path}.category must be technology, markets, or science")
            if not _https_url(item.get("xPostUrl")):
                errors.append(f"{path}.xPostUrl must be an HTTPS URL")
            if item.get("verificationRequired") is not True or item.get("advisoryOnly") is not True:
                errors.append(f"{path} must require verification and remain advisory")
            if item.get("mustReview") is True:
                _require_string(item.get("mustReviewReason"), f"{path}.mustReviewReason", errors)
    if len(ids) != len(set(ids)):
        errors.append("candidate IDs must be unique")
    if ledger.get("scoringRule", {}).get("version") != "morning-news-v1":
        errors.append("scoringRule.version must be morning-news-v1")
    if ledger.get("authority") != {"advisoryOnly": True, "editorialSelectionFinal": False, "publicationApproved": False, "mayPublish": False, "publicationOwner": "existing-morning-bake-workflow"}:
        errors.append("ledger authority must remain advisory and non-publishing")
    if errors:
        raise MorningHandoffValidationError(errors)


def validate_packet(
    packet: Any,
    *,
    expected_date: str | None = None,
    now: datetime | None = None,
    require_fresh: bool = True,
) -> None:
    errors: list[str] = []
    if not isinstance(packet, dict):
        raise MorningHandoffValidationError(["packet must be a JSON object"])
    if packet.get("schemaVersion") != PACKET_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {PACKET_SCHEMA_VERSION}")
    target_date = _validate_target(packet.get("targetEdition"), expected_date, errors)
    if packet.get("packetId") != f"{target_date}-morning":
        errors.append("packetId must match the target date and morning slot")
    reviewed_at = _timestamp(packet.get("reviewedAt"))
    expires_at = _timestamp(packet.get("expiresAt"))
    now = now or datetime.now(timezone.utc)
    if reviewed_at is None or expires_at is None:
        errors.append("reviewedAt and expiresAt must be ISO UTC timestamps")
    else:
        if target_date and reviewed_at.astimezone(PACIFIC).date().isoformat() != target_date:
            errors.append("reviewedAt must fall on the target Pacific date")
        if expires_at <= reviewed_at or expires_at - reviewed_at > timedelta(hours=8):
            errors.append("packet validity must be greater than zero and at most eight hours")
        if require_fresh and expires_at <= now:
            errors.append("packet has expired")
        deadline = datetime.combine(reviewed_at.astimezone(PACIFIC).date(), datetime.min.time(), PACIFIC).replace(hour=4, minute=40)
        if reviewed_at.astimezone(PACIFIC) >= deadline:
            errors.append("reviewedAt must be before the 4:40 AM Pacific bake")
    if packet.get("editorialRule") != MORNING_RULE:
        errors.append("editorialRule must equal the distinct morning-editorial-v1 rule")
    ledger_lineage = packet.get("xManagerLedger")
    if not isinstance(ledger_lineage, dict):
        errors.append("xManagerLedger is required")
    else:
        if ledger_lineage.get("schemaVersion") != LEDGER_SCHEMA_VERSION:
            errors.append(f"xManagerLedger.schemaVersion must be {LEDGER_SCHEMA_VERSION}")
        if not re.fullmatch(r"[a-f0-9]{64}", str(ledger_lineage.get("artifactSha256", ""))):
            errors.append("xManagerLedger.artifactSha256 must be a lowercase SHA-256")
        ledger_generated_at = _timestamp(ledger_lineage.get("generatedAt"))
        if ledger_generated_at is None:
            errors.append("xManagerLedger.generatedAt must be an ISO UTC timestamp")
        elif reviewed_at is not None and ledger_generated_at > reviewed_at:
            errors.append("X Manager ledger must be generated before DDB review")
    verification = packet.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification is required")
    else:
        if verification.get("independentFromXManager") is not True:
            errors.append("verification.independentFromXManager must be true")
        sweep = verification.get("gapSweep")
        if not isinstance(sweep, dict):
            errors.append("verification.gapSweep is required")
        else:
            for beat in BEATS:
                record = sweep.get(beat)
                if not isinstance(record, dict) or record.get("completed") is not True:
                    errors.append(f"verification.gapSweep.{beat}.completed must be true")
                elif not isinstance(record.get("maximumSources"), int) or record["maximumSources"] < 1:
                    errors.append(f"verification.gapSweep.{beat}.maximumSources must be positive")
    source_ids = packet.get("sourceCandidateIds")
    if not isinstance(source_ids, list) or any(not isinstance(item, str) for item in source_ids):
        errors.append("sourceCandidateIds must be an array of strings")
        source_ids = []
    must_review_ids = packet.get("mustReviewCandidateIds")
    if not isinstance(must_review_ids, list) or any(not isinstance(item, str) for item in must_review_ids):
        errors.append("mustReviewCandidateIds must be an array of strings")
        must_review_ids = []
    if set(must_review_ids) - set(source_ids):
        errors.append("mustReviewCandidateIds must come from the X Manager ledger")
    gap_ids = packet.get("gapCandidateIds")
    if not isinstance(gap_ids, list) or any(not isinstance(item, str) for item in gap_ids):
        errors.append("gapCandidateIds must be an array of strings")
        gap_ids = []
    if set(source_ids) & set(gap_ids):
        errors.append("ledger and gap candidate IDs must be disjoint")
    decisions: list[dict[str, Any]] = []
    for decision in DECISIONS:
        items = packet.get("decisions", {}).get(decision) if isinstance(packet.get("decisions"), dict) else None
        if not isinstance(items, list):
            errors.append(f"decisions.{decision} must be an array")
            continue
        for index, item in enumerate(items):
            path = f"decisions.{decision}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{path} must be an object")
                continue
            decisions.append(item)
            for field in ("id", "title", "reason"):
                _require_string(item.get(field), f"{path}.{field}", errors)
            if item.get("decision") != decision:
                errors.append(f"{path}.decision must be {decision}")
            if item.get("beat") not in BEATS:
                errors.append(f"{path}.beat is invalid")
            _validate_morning_scores(item.get("scores"), f"{path}.scores", errors, selected=decision == "selected")
            urls = item.get("verifiedSourceUrls")
            if not isinstance(urls, list) or not urls or any(not _https_url(url, allow_x=False) for url in urls):
                errors.append(f"{path}.verifiedSourceUrls must contain non-X HTTPS URLs")
    decision_ids = [item.get("id") for item in decisions]
    if len(decision_ids) != len(set(decision_ids)):
        errors.append("every candidate may receive only one disposition")
    all_candidate_ids = set(source_ids) | set(gap_ids)
    if all_candidate_ids - set(decision_ids):
        errors.append("every ledger and gap candidate must receive selected, hold, or reject")
    if set(decision_ids) - all_candidate_ids:
        errors.append("every disposition must trace to a ledger or gap candidate")
    if set(must_review_ids) - set(decision_ids):
        errors.append("every must-review candidate must receive an explicit disposition")
    selected_items = packet.get("decisions", {}).get("selected", [])
    if isinstance(selected_items, list):
        for beat in BEATS:
            beat_count = sum(item.get("beat") == beat for item in selected_items if isinstance(item, dict))
            if not 2 <= beat_count <= 6:
                errors.append(f"selected {beat} stories must contain 2 to 6 items")
    if packet.get("authority") != AUTHORITY:
        errors.append("authority must withhold publication approval")
    if errors:
        raise MorningHandoffValidationError(errors)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_packet(base_url: str, target_date: str, output: Path, sites_token_env: str, *, now: datetime | None = None) -> bool:
    query = parse.urlencode({"date": target_date, "slot": "morning"})
    endpoint = f"{base_url.rstrip('/')}/api/ddb-handoff?{query}"
    try:
        token = os.environ.get(sites_token_env, "")
        if not token:
            raise RuntimeError(f"required environment variable {sites_token_env} is unavailable")
        req = request.Request(endpoint, headers={"OAI-Sites-Authorization": f"Bearer {token}"})
        with request.urlopen(req, timeout=30) as response:
            body = response.read(256 * 1024 + 1)
        if len(body) > 256 * 1024:
            raise RuntimeError("reviewed morning packet exceeded 256 KiB")
        payload = json.loads(body)
        validate_packet(payload, expected_date=target_date, now=now)
        _write_json(output, payload)
        return True
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, error.URLError):
        _write_json(output, {
            "schemaVersion": PACKET_SCHEMA_VERSION,
            "available": False,
            "targetEdition": {"date": target_date, "slot": "morning"},
            "reason": "reviewed-morning-packet-unavailable",
        })
        return False


def upload_packet(
    base_url: str,
    packet_path: Path,
    write_token_env: str,
    sites_token_env: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate and upload a reviewed morning packet to the private handoff store."""

    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    validate_packet(payload, now=now)
    write_token = os.environ.get(write_token_env, "")
    sites_token = os.environ.get(sites_token_env, "")
    if not write_token:
        raise RuntimeError(f"required environment variable {write_token_env} is unavailable")
    if not sites_token:
        raise RuntimeError(f"required environment variable {sites_token_env} is unavailable")
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = request.Request(
        f"{base_url.rstrip('/')}/api/ddb-handoff",
        data=body,
        headers={
            "Authorization": f"Bearer {write_token}",
            "OAI-Sites-Authorization": f"Bearer {sites_token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        receipt = json.loads(response.read(64 * 1024))
    if receipt.get("packetId") != payload["packetId"] or receipt.get("stored") is not True:
        raise RuntimeError("handoff store returned an invalid receipt")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    ledger = commands.add_parser("validate-ledger")
    ledger.add_argument("--input", type=Path, required=True)
    ledger.add_argument("--date")
    packet = commands.add_parser("validate")
    packet.add_argument("--input", type=Path, required=True)
    packet.add_argument("--date")
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--base-url", required=True)
    fetch.add_argument("--date", required=True)
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument("--sites-token-env", default="X_MONITOR_SITES_BYPASS_TOKEN")
    upload = commands.add_parser("upload")
    upload.add_argument("--base-url", required=True)
    upload.add_argument("--input", type=Path, required=True)
    upload.add_argument("--write-token-env", default="DDB_HANDOFF_WRITE_TOKEN")
    upload.add_argument("--sites-token-env", default="X_MONITOR_SITES_BYPASS_TOKEN")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-ledger":
            validate_candidate_ledger(json.loads(args.input.read_text()), expected_date=args.date)
            print(f"Validated morning candidate ledger for {args.date or 'packet date'}")
        elif args.command == "validate":
            validate_packet(json.loads(args.input.read_text()), expected_date=args.date)
            print(f"Validated reviewed morning packet for {args.date or 'packet date'}")
        elif args.command == "fetch":
            available = fetch_packet(args.base_url, args.date, args.output, args.sites_token_env)
            print("Reviewed morning packet ready" if available else "::error::Reviewed morning packet unavailable")
            return 0 if available else 1
        else:
            receipt = upload_packet(
                args.base_url, args.input, args.write_token_env, args.sites_token_env
            )
            print(f"Stored reviewed morning handoff {receipt['packetId']}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
