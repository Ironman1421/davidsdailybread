#!/usr/bin/env python3
"""Validate the aggregate-only DDB-PC-028 observable-return boundary."""

from datetime import datetime
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "operations/schemas/outreach-observable-return-receipt-v1.schema.json"
RECEIPT_PATH = ROOT / "operations/outreach-observable-return-validation-receipt.json"
LEDGER_PATH = ROOT / "operations/outreach-observable-return-ledger.json"
CAMPAIGN_PATH = ROOT / "operations/outreach-campaign.contract.json"
AUTHORITY_PATH = ROOT / "measurement/authority.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def semantic_errors(receipt, ledger, campaign, authority):
    errors = []
    post_match = re.fullmatch(
        r"https://x\.com/DavidDailyBread/status/([0-9]+)",
        receipt["publicXPostUrl"],
    )
    if not post_match or post_match.group(1) != receipt["publicXPostId"]:
        errors.append("public X post URL and identifier disagree")

    edition_match = re.fullmatch(
        r"https://davidsdailybread\.com/editions/"
        r"([0-9]{4}-[0-9]{2}-[0-9]{2}-(?:morning|evening))\.html",
        receipt["exactEditionUrl"],
    )
    if not edition_match or edition_match.group(1) != receipt["editionId"]:
        errors.append("edition URL and edition identifier disagree")
    parsed_edition = urlparse(receipt["exactEditionUrl"])
    if parsed_edition.query or parsed_edition.fragment:
        errors.append("edition URL contains a query string or fragment")

    if parse_time(receipt["periodStart"]) > parse_time(receipt["periodEnd"]):
        errors.append("metric period ends before it starts")
    if receipt["periodEnd"] != receipt["capturedAt"]:
        errors.append("metric period end and capture timestamp disagree")
    if parse_time(receipt["editionPublishedAt"]) > parse_time(receipt["capturedAt"]):
        errors.append("validation predates the source edition")

    evidence_hash = receipt["restrictedEvidenceSha256"]
    if evidence_hash == "0" * 64:
        errors.append("restricted evidence hash is a placeholder")

    if ledger != {
        "version": 1,
        "status": "inactive-campaign-not-started",
        "programItem": "DDB-PC-028",
        "receiptSchema": "operations/schemas/outreach-observable-return-receipt-v1.schema.json",
        "campaignActivationReceipt": None,
        "entries": [],
    }:
        errors.append("campaign receipt ledger is not the exact inactive empty ledger")

    gate = campaign["returnPathGate"]
    if gate["status"] != "ready":
        errors.append("campaign return path gate is not ready")
    if gate["selectedPath"] != "x_exact_edition_url_link_click":
        errors.append("campaign selected path disagrees with the receipt")
    if not gate["observable"]:
        errors.append("campaign selected path is not observable")
    if gate["implementationReceipt"] != (
        "operations/outreach-observable-return-implementation-receipt.json"
    ):
        errors.append("campaign implementation receipt path disagrees")
    if gate["validationReceipt"] != (
        "operations/outreach-observable-return-validation-receipt.json"
    ):
        errors.append("campaign validation receipt path disagrees")
    if any(gate["privacyBoundary"].values()):
        errors.append("campaign return privacy boundary activates collection")

    if campaign["campaignWindow"]["status"] != "not_started":
        errors.append("campaign clock has started")
    if any(
        value != 0 if field == "spendAuthorizedUsd" else value
        for field, value in campaign["externalActions"].items()
    ):
        errors.append("campaign authorizes an external action")
    if campaign["diagnostics"]["siteInstrumentationActivated"]:
        errors.append("site instrumentation is activated")
    if campaign["diagnostics"]["siteReturnStatus"] != "unknown":
        errors.append("link clicks are misrepresented as known site return")
    if authority["firstPartyReturnMeasurementAuthorized"]:
        errors.append("official first-party return measurement is activated")

    return errors


def validate_current():
    schema = load_json(SCHEMA_PATH)
    receipt = load_json(RECEIPT_PATH)
    ledger = load_json(LEDGER_PATH)
    campaign = load_json(CAMPAIGN_PATH)
    authority = load_json(AUTHORITY_PATH)
    Draft202012Validator.check_schema(schema)
    errors = [
        error.message
        for error in Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(receipt)
    ]
    errors.extend(semantic_errors(receipt, ledger, campaign, authority))
    return sorted(errors)


def main():
    errors = validate_current()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("observable-return receipt and fail-closed boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
