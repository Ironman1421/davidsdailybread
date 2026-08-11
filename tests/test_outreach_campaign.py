#!/usr/bin/env python3
"""Executable boundaries for the lean core-proof outreach campaign."""

from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def semantic_errors(contract, receipt, reply_ledger):
    errors = []
    readiness = contract["readinessWindow"]
    if parse_time(readiness["mustCompleteBy"]) - parse_time(
        readiness["startedAt"]
    ) > timedelta(hours=48):
        errors.append("readiness window exceeds 48 hours")

    window = contract["campaignWindow"]
    if window["status"] == "not_started":
        if window["startsAt"] is not None:
            errors.append("not-started campaign has a start")
        if window["endsAt"] is not None:
            errors.append("not-started campaign has an end")
        if window["activationReceipt"] is not None:
            errors.append("not-started campaign has an activation receipt")
    else:
        if not window["activationReceipt"]:
            errors.append("campaign clock starts without exact activation receipt")
        if not window["startsAt"] or not window["endsAt"]:
            errors.append("campaign clock starts without exact window")
        if contract["status"] != "active":
            errors.append("campaign clock starts while campaign is blocked")

    return_gate = contract["returnPathGate"]
    if window["status"] != "not_started" and return_gate["status"] != "ready":
        errors.append("campaign clock starts without a ready observable return path")
    if return_gate["status"] == "ready":
        if not return_gate["observable"]:
            errors.append("ready return path is not observable")
        for field in ("selectedPath", "implementationReceipt", "validationReceipt"):
            if not return_gate[field]:
                errors.append(f"ready return path lacks {field}")

    if contract["status"] != "active":
        for field, value in contract["externalActions"].items():
            if field == "spendAuthorizedUsd":
                if value != 0:
                    errors.append("inactive campaign authorizes spend")
            elif value:
                errors.append(f"inactive campaign authorizes {field}")

    x = contract["x"]
    baseline = reply_ledger["strategyBaseline"]
    if x["enforcedPublishedReplyCap"] != baseline["dailyPublishedReplyCap"]:
        errors.append("campaign and reply-ledger caps disagree")
    if x["staffedApprovalWindows"] != baseline["staffedApprovalWindows"]:
        errors.append("campaign and reply-ledger staffing disagree")
    if x["replyPlanMaximumOnStaffedDay"] > 4 or x["fifthReplyAuthorized"]:
        errors.append("campaign permits a fifth reply")

    security = receipt["security"]
    password_mfa_ready = (
        security["passwordCredentialStatus"] == "present"
        and security["passwordResetProtectionEnabled"]
        and security["passwordResetProtectionDisposition"] == "enabled"
        and any(
            security[field]
            for field in (
                "textMessageMfaEnabled",
                "authenticationAppMfaEnabled",
                "securityKeyMfaEnabled",
            )
        )
    )
    passwordless_passkey_ready = (
        security["passkeyEnabled"]
        and security["passkeyVerifiedInOfficialUi"]
        and security["passwordCredentialStatus"]
        == "operator_reports_never_created"
        and not security["passwordResetProtectionEnabled"]
        and security["passwordResetProtectionDisposition"]
        == "not_applicable_without_password"
    )
    security_ready = password_mfa_ready or passwordless_passkey_ready
    links_ready = all(
        receipt["canonicalBroadcasts"][slot]["immutableEditionDestination"]
        for slot in ("latestMorning", "latestEvening")
    )
    if receipt["security"]["status"] == "ready" and not security_ready:
        errors.append("X security claims ready without a valid credential posture")
    if receipt["status"] == "ready" and not (security_ready and links_ready):
        errors.append("X receipt claims ready without security and immutable links")
    if x["readinessStatus"] == "ready" and receipt["status"] != "ready":
        errors.append("campaign claims X ready while receipt is blocked")

    deferred = contract["deferredChannels"]
    if deferred["generatedMediaAuthorized"]:
        errors.append("campaign authorizes generated media")
    for name in ("geminiOmni", "youtube"):
        channel = deferred[name]
        if channel["status"] != "deferred" or channel["activationGateEligible"]:
            errors.append(f"{name} is not fully deferred")
        for field, value in channel.items():
            if field.endswith("Authorized") and value:
                errors.append(f"{name} authorizes {field}")

    return errors


class OutreachCampaignContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(
            ROOT / "operations" / "outreach-campaign.contract.json"
        )
        cls.contract_schema = load_json(
            ROOT / "operations" / "schemas" / "outreach-campaign-v1.schema.json"
        )
        cls.receipt = load_json(
            ROOT / "operations" / "x-outreach-readiness-receipt.json"
        )
        cls.receipt_schema = load_json(
            ROOT / "operations" / "schemas" / "x-outreach-readiness-v1.schema.json"
        )
        cls.reply_ledger = load_json(ROOT / "distribution" / "x-replies.json")
        cls.contract_validator = Draft202012Validator(
            cls.contract_schema, format_checker=FormatChecker()
        )

    def test_schemas_and_current_records_validate(self):
        for schema in (self.contract_schema, self.receipt_schema):
            Draft202012Validator.check_schema(schema)
        self.contract_validator.validate(self.contract)
        Draft202012Validator(
            self.receipt_schema, format_checker=FormatChecker()
        ).validate(self.receipt)
        self.assertEqual(
            [], semantic_errors(self.contract, self.receipt, self.reply_ledger)
        )

    def test_public_campaign_and_clock_are_fail_closed(self):
        self.assertEqual(
            "readiness-active-public-campaign-blocked", self.contract["status"]
        )
        self.assertEqual("not_started", self.contract["campaignWindow"]["status"])
        self.assertEqual(0, self.contract["readinessWindow"]["cashBudgetUsd"])
        for field, value in self.contract["externalActions"].items():
            with self.subTest(field=field):
                self.assertIn(value, (False, 0))

    def test_evening_field_guide_is_the_acquisition_franchise(self):
        franchise = self.contract["acquisitionFranchise"]
        self.assertEqual("evening-field-guide", franchise["id"])
        self.assertEqual("evening", franchise["eligibleEditionSlot"])
        self.assertEqual("edition-derived-x-source-card", franchise["sourceCardType"])
        self.assertTrue(franchise["exactImmutableEditionUrlRequired"])
        self.assertFalse(franchise["morningSourceCardsAuthorized"])
        self.assertEqual(1, self.contract["x"]["sourceCardsPerCalendarDay"])

    def test_observable_return_path_is_ready_but_campaign_stays_blocked(self):
        gate = self.contract["returnPathGate"]
        self.assertEqual("ready", gate["status"])
        self.assertTrue(gate["observable"])
        self.assertEqual("x_exact_edition_url_link_click", gate["selectedPath"])
        self.assertEqual(
            "operations/outreach-observable-return-implementation-receipt.json",
            gate["implementationReceipt"],
        )
        self.assertEqual(
            "operations/outreach-observable-return-validation-receipt.json",
            gate["validationReceipt"],
        )
        self.assertTrue(gate["requiredBeforeCampaignClockStarts"])
        self.assertIn("rss-follow-intent", gate["disallowedSubstitutes"])
        self.assertIn("unknown-site-return", gate["disallowedSubstitutes"])
        self.assertTrue(all(value is False for value in gate["privacyBoundary"].values()))
        self.assertEqual("unknown", self.contract["diagnostics"]["siteReturnStatus"])
        self.assertEqual(
            "readiness-active-public-campaign-blocked", self.contract["status"]
        )

    def test_manual_reply_range_is_zero_through_four(self):
        x = self.contract["x"]
        self.assertEqual(0, x["replyPlanMinimumOnStaffedDay"])
        self.assertEqual(4, x["replyPlanMaximumOnStaffedDay"])
        self.assertEqual(4, x["enforcedPublishedReplyCap"])
        self.assertFalse(x["fifthReplyAuthorized"])
        self.assertTrue(x["manualOfficialUiPostingOnly"])

    def test_gemini_youtube_and_generated_media_are_deferred(self):
        deferred = self.contract["deferredChannels"]
        self.assertFalse(deferred["generatedMediaAuthorized"])
        for name in ("geminiOmni", "youtube"):
            with self.subTest(channel=name):
                self.assertEqual("deferred", deferred[name]["status"])
                self.assertFalse(deferred[name]["activationGateEligible"])
                for field, value in deferred[name].items():
                    if field.endswith("Authorized"):
                        self.assertFalse(value)

    def test_schema_and_semantics_reject_authority_drift(self):
        paid = deepcopy(self.contract)
        paid["readinessWindow"]["cashBudgetUsd"] = 1
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(paid)

        fifth = deepcopy(self.contract)
        fifth["x"]["replyPlanMaximumOnStaffedDay"] = 5
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(fifth)

        media = deepcopy(self.contract)
        media["deferredChannels"]["generatedMediaAuthorized"] = True
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(media)

        unsafe_return = deepcopy(self.contract)
        unsafe_return["returnPathGate"]["privacyBoundary"]["rawIpStored"] = True
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(unsafe_return)

        premature_clock = deepcopy(self.contract)
        premature_clock["campaignWindow"]["status"] = "active"
        premature_clock["campaignWindow"]["startsAt"] = "2026-08-12T00:00:00Z"
        self.contract_validator.validate(premature_clock)
        errors = semantic_errors(premature_clock, self.receipt, self.reply_ledger)
        self.assertIn("campaign clock starts without exact activation receipt", errors)
        self.assertIn("campaign clock starts without exact window", errors)
        self.assertIn("campaign clock starts while campaign is blocked", errors)

    def test_governing_prose_names_the_machine_law(self):
        paths = (
            "FOUNDER_DOCTRINE.md",
            "BRAND.md",
            "docs/OUTREACH_CAMPAIGN.md",
            "docs/PRODUCT_SPEC.md",
            "docs/DISTRIBUTION_SPEC.md",
            "docs/CLAUDE_CODE_MARKETING_HANDOFF.md",
        )
        prose = "\n".join(
            (ROOT / path).read_text(encoding="utf-8") for path in paths
        )
        for phrase in (
            "lean core-proof",
            "evening Field Guide",
            "privacy-safe observable return path",
            "zero through four",
            "Gemini Omni",
            "YouTube",
            "deferred",
        ):
            self.assertIn(phrase, prose)
        self.assertIn("public campaign blocked", prose)
        self.assertIn("The 2026-08-02 seven-day", prose)


if __name__ == "__main__":
    unittest.main()
