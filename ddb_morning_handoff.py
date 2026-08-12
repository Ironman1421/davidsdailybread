#!/usr/bin/env python3
"""Validate and fetch the date-bound reviewed morning research packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
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
LEDGER_SCORE_RULE = {
    "version": "morning-news-v1",
    "statement": "Morning relevance first, public significance second, freshness third, corroboration fourth.",
    "weights": {
        "morningRelevance": 0.3,
        "publicSignificance": 0.35,
        "freshness": 0.2,
        "corroboration": 0.15,
    },
    "mustReviewGate": 70,
}
LEDGER_AUTHORITY = {
    "advisoryOnly": True,
    "editorialSelectionFinal": False,
    "publicationApproved": False,
    "mayPublish": False,
    "publicationOwner": "existing-morning-bake-workflow",
}
MUST_REVIEW_REASON = (
    "Official major launch exceeds the morning-news-v1 must-review gate."
)
_CATEGORY_PATTERNS = {
    "technology": (
        re.compile(r"\b(?:ai|artificial intelligence|code|coding|developer|software|model|agent|tool|app|chip|cloud)\b", re.I),
        re.compile(r"\b(?:launch|release|ship|announce|introduce|available)\b", re.I),
    ),
    "markets": (
        re.compile(r"\b(?:market|stock|shares?|index|bond|yield|funding|acquisition|merger|earnings|ipo)\b", re.I),
        re.compile(r"\b(?:economy|economic|inflation|jobs|revenue|valuation|investor)\b", re.I),
    ),
    "science": (
        re.compile(r"\b(?:science|scientist|research|study|discovery|space|climate|physics|biology|medicine)\b", re.I),
        re.compile(r"\b(?:trial|peer-reviewed|journal|nasa|experiment|evidence)\b", re.I),
    ),
}


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
    is_x = host in {"x.com", "twitter.com"} or host.endswith(
        (".x.com", ".twitter.com")
    )
    return allow_x or not is_x


def _x_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = parse.urlparse(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.netloc.lower() in {"x.com", "www.x.com"}
        and parsed.path.startswith("/")
    )


def _exact_keys(value: dict[str, Any], expected: set[str], path: str, errors: list[str]) -> None:
    missing = expected - set(value)
    extra = set(value) - expected
    if missing:
        errors.append(f"{path} is missing: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{path} has unknown fields: {', '.join(sorted(extra))}")


def _integer(value: Any, *, minimum: int = 0, maximum: int | None = None) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= minimum
        and (maximum is None or value <= maximum)
    )


def _js_round(value: float) -> int:
    return int(value + 0.5)


def _normalized(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).strip().split())


def _expected_ledger_scores(item: dict[str, Any], generated_at: datetime, lookback: int) -> dict[str, Any]:
    text = f"{_normalized(item.get('title'))} {_normalized(item.get('summary'))}"
    patterns = _CATEGORY_PATTERNS[item["category"]]
    morning_relevance = min(100, max(0, _js_round(45 + sum(bool(pattern.search(text)) for pattern in patterns) * 20)))
    public_significance = min(
        100,
        max(
            0,
            _js_round(
                30
                + int(item.get("officialAnnouncement") is True) * 25
                + int(item.get("majorLaunch") is True) * 35
            ),
        ),
    )
    published_at = _timestamp(item.get("publishedAt"))
    age_hours = max(0.0, (generated_at - published_at).total_seconds() / 3600) if published_at else lookback
    freshness = min(100, max(0, _js_round(100 * (1 - age_hours / lookback))))
    corroboration = min(100, max(0, _js_round(35 + min(2, len(set(item.get("sourceIds", []))) - 1) * 25)))
    total = _js_round(
        morning_relevance * 0.3
        + public_significance * 0.35
        + freshness * 0.2
        + corroboration * 0.15
    )
    return {
        "morningRelevance": morning_relevance,
        "publicSignificance": public_significance,
        "freshness": freshness,
        "corroboration": corroboration,
        "total": total,
        "ruleVersion": "morning-news-v1",
    }


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
    _exact_keys(
        ledger,
        {"schemaVersion", "ledgerId", "generatedAt", "targetEdition", "sourceManifest", "boundedInputs", "scoringRule", "candidates", "authority"},
        "ledger",
        errors,
    )
    if ledger.get("schemaVersion") != LEDGER_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {LEDGER_SCHEMA_VERSION}")
    target_date = _validate_target(ledger.get("targetEdition"), expected_date, errors)
    if isinstance(ledger.get("targetEdition"), dict):
        _exact_keys(ledger["targetEdition"], {"date", "slot", "timeZone"}, "targetEdition", errors)
    generated_at = _timestamp(ledger.get("generatedAt"))
    if generated_at is None:
        errors.append("generatedAt must be an ISO UTC timestamp")
    elif target_date and generated_at.astimezone(PACIFIC).date().isoformat() != target_date:
        errors.append("generatedAt must fall on the target Pacific date")
    manifest = ledger.get("sourceManifest")
    if not isinstance(manifest, dict):
        errors.append("sourceManifest is required")
    else:
        _exact_keys(manifest, {"version", "sha256"}, "sourceManifest", errors)
        if manifest.get("version") != "x-manager-morning-source-manifest-v1":
            errors.append("sourceManifest.version must be x-manager-morning-source-manifest-v1")
        if not re.fullmatch(r"[a-f0-9]{64}", str(manifest.get("sha256", ""))):
            errors.append("sourceManifest.sha256 must be a lowercase SHA-256")
    bounds = ledger.get("boundedInputs")
    if not isinstance(bounds, dict):
        errors.append("boundedInputs is required")
    else:
        _exact_keys(bounds, {"newPaidRunTriggered", "paidPostReads", "sourceArtifacts", "recordsReceived", "recordsConsidered", "caps"}, "boundedInputs", errors)
        if bounds.get("newPaidRunTriggered") is not False:
            errors.append("boundedInputs.newPaidRunTriggered must be false")
        if bounds.get("paidPostReads") != 0:
            errors.append("boundedInputs.paidPostReads must be zero")
        for field in ("sourceArtifacts", "recordsReceived", "recordsConsidered"):
            if not _integer(bounds.get(field)):
                errors.append(f"boundedInputs.{field} must be a non-negative integer")
        caps = bounds.get("caps")
        if not isinstance(caps, dict):
            errors.append("boundedInputs.caps is required")
            caps = {}
        else:
            _exact_keys(caps, {"maxPaidRuns", "maxPaidPostReads", "maxSourceArtifacts", "maxInputRecords", "maxCandidatesPerCategory", "maxLookbackHours"}, "boundedInputs.caps", errors)
        if caps.get("maxPaidRuns") != 0 or caps.get("maxPaidPostReads") != 0:
            errors.append("boundedInputs paid-run and paid-read caps must be zero")
        for field in ("maxSourceArtifacts", "maxInputRecords", "maxCandidatesPerCategory", "maxLookbackHours"):
            if not _integer(caps.get(field), minimum=1):
                errors.append(f"boundedInputs.caps.{field} must be a positive integer")
        if _integer(bounds.get("recordsReceived")) and _integer(bounds.get("recordsConsidered")) and bounds["recordsConsidered"] > bounds["recordsReceived"]:
            errors.append("recordsConsidered cannot exceed recordsReceived")
        if _integer(bounds.get("recordsReceived")) and _integer(caps.get("maxInputRecords"), minimum=1) and bounds["recordsReceived"] > caps["maxInputRecords"]:
            errors.append("recordsReceived exceeds maxInputRecords")
        if _integer(bounds.get("sourceArtifacts")) and _integer(caps.get("maxSourceArtifacts"), minimum=1) and bounds["sourceArtifacts"] > caps["maxSourceArtifacts"]:
            errors.append("sourceArtifacts exceeds maxSourceArtifacts")
    if ledger.get("scoringRule") != LEDGER_SCORE_RULE:
        errors.append("scoringRule must preserve the exact morning-news-v1 contract")
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
            _exact_keys(item, {"rank", "candidateId", "category", "title", "summary", "xPostUrl", "authorUsername", "publishedAt", "observedAt", "sourceIds", "officialAnnouncement", "majorLaunch", "scores", "mustReview", "mustReviewReason", "verificationRequired", "advisoryOnly"}, path, errors)
            if not _integer(item.get("rank"), minimum=1):
                errors.append(f"{path}.rank must be a positive integer")
            for field in ("candidateId", "title", "summary", "authorUsername"):
                _require_string(item.get(field), f"{path}.{field}", errors)
            ids.append(item.get("candidateId"))
            if not re.fullmatch(r"xmc-[a-f0-9]{20}", str(item.get("candidateId", ""))):
                errors.append(f"{path}.candidateId is invalid")
            if item.get("category") not in BEATS:
                errors.append(f"{path}.category must be technology, markets, or science")
            if not _x_url(item.get("xPostUrl")):
                errors.append(f"{path}.xPostUrl must be an exact x.com HTTPS URL")
            published_at = _timestamp(item.get("publishedAt"))
            observed_at = _timestamp(item.get("observedAt"))
            if published_at is None or observed_at is None:
                errors.append(f"{path}.publishedAt and observedAt must be ISO UTC timestamps")
            elif generated_at is not None and _integer(caps.get("maxLookbackHours"), minimum=1):
                age = (generated_at - published_at).total_seconds()
                if age < 0 or age > caps["maxLookbackHours"] * 3600:
                    errors.append(f"{path}.publishedAt must be within the bounded lookback")
            for field in ("officialAnnouncement", "majorLaunch", "mustReview"):
                if not isinstance(item.get(field), bool):
                    errors.append(f"{path}.{field} must be boolean")
            source_ids = item.get("sourceIds")
            if not isinstance(source_ids, list) or not source_ids or any(not isinstance(value, str) or not value for value in source_ids) or len(source_ids) != len(set(source_ids)):
                errors.append(f"{path}.sourceIds must be a non-empty unique string array")
            if item.get("verificationRequired") is not True or item.get("advisoryOnly") is not True:
                errors.append(f"{path} must require verification and remain advisory")
            if item.get("category") in BEATS and generated_at is not None and _integer(caps.get("maxLookbackHours"), minimum=1):
                expected_scores = _expected_ledger_scores(item, generated_at, caps["maxLookbackHours"])
                if item.get("scores") != expected_scores:
                    errors.append(f"{path}.scores must equal the derived morning-news-v1 scores")
                expected_must_review = item.get("officialAnnouncement") is True and item.get("majorLaunch") is True and expected_scores["total"] >= LEDGER_SCORE_RULE["mustReviewGate"]
                if item.get("mustReview") is not expected_must_review:
                    errors.append(f"{path}.mustReview must reflect official major-launch semantics")
                expected_reason = MUST_REVIEW_REASON if expected_must_review else None
                if item.get("mustReviewReason") != expected_reason:
                    errors.append(f"{path}.mustReviewReason is inconsistent")
            identity = "\n".join((str(item.get("category", "")), _normalized(item.get("title")).lower(), str(item.get("xPostUrl", "")).lower()))
            expected_id = f"xmc-{hashlib.sha256(identity.encode()).hexdigest()[:20]}"
            if item.get("candidateId") != expected_id:
                errors.append(f"{path}.candidateId must be derived deterministically")
    if len(ids) != len(set(ids)):
        errors.append("candidate IDs must be unique")
    if isinstance(candidates, list):
        expected_order = sorted(
            candidates,
            key=lambda item: (
                -int(item.get("mustReview") is True),
                -int(item.get("scores", {}).get("total", -1)) if isinstance(item.get("scores"), dict) else 1,
                -(_timestamp(item.get("publishedAt")).timestamp() if _timestamp(item.get("publishedAt")) else float("-inf")),
                str(item.get("candidateId", "")),
            ),
        )
        if candidates != expected_order:
            errors.append("candidates must follow mustReview desc, total desc, publishedAt desc, candidateId asc")
        if isinstance(bounds, dict) and isinstance(caps, dict) and _integer(caps.get("maxCandidatesPerCategory"), minimum=1):
            for beat in BEATS:
                if sum(item.get("category") == beat for item in candidates if isinstance(item, dict)) > caps["maxCandidatesPerCategory"]:
                    errors.append(f"candidate count exceeds the {beat} category cap")
            unique_sources = {
                source
                for item in candidates
                if isinstance(item, dict)
                for source in item.get("sourceIds", [])
                if isinstance(source, str)
            }
            if _integer(bounds.get("sourceArtifacts")) and bounds["sourceArtifacts"] < len(unique_sources):
                errors.append("sourceArtifacts cannot be smaller than candidate source lineage")
            if _integer(bounds.get("recordsConsidered")) and bounds["recordsConsidered"] < len(candidates):
                errors.append("recordsConsidered cannot be smaller than the candidate count")
        expected_ledger_id = f"x-manager-morning-{target_date}-{hashlib.sha256(chr(10).join(str(item.get('candidateId', '')) for item in candidates).encode()).hexdigest()[:16]}"
        if ledger.get("ledgerId") != expected_ledger_id:
            errors.append("ledgerId must be derived from the ordered candidate IDs")
    if not re.fullmatch(r"x-manager-morning-\d{4}-\d{2}-\d{2}-[a-f0-9]{16}", str(ledger.get("ledgerId", ""))):
        errors.append("ledgerId has an invalid shape")
    if ledger.get("authority") != LEDGER_AUTHORITY:
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
