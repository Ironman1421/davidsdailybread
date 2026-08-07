#!/usr/bin/env python3
"""Executable boundaries for the zero-dollar outreach learning campaign."""

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
    if parse_time(readiness["mustCompleteBy"]) - parse_time(readiness["startedAt"]) > timedelta(hours=48):
        errors.append("readiness window exceeds 48 hours")

    if contract["campaignWindow"]["status"] == "not_started":
        if contract["campaignWindow"]["startsAt"] is not None:
            errors.append("not-started campaign has a start")
        if contract["campaignWindow"]["endsAt"] is not None:
            errors.append("not-started campaign has an end")
        if contract["campaignWindow"]["activationReceipt"] is not None:
            errors.append("not-started campaign has an activation receipt")

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
    if x["fifthReplyAuthorized"]:
        errors.append("fifth reply is authorized")

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
    if security["status"] == "ready" and not security_ready:
        errors.append("X security claims ready without a valid credential posture")
    links_ready = all(
        receipt["canonicalBroadcasts"][slot]["immutableEditionDestination"]
        for slot in ("latestMorning", "latestEvening")
    )
    if receipt["status"] == "ready" and not (security_ready and links_ready):
        errors.append("X receipt claims ready without security and immutable links")
    if x["readinessStatus"] == "ready" and receipt["status"] != "ready":
        errors.append("campaign claims X ready while receipt is blocked")

    omni = contract["geminiOmni"]
    account = omni["accountBoundary"]
    if account["status"] != "verified":
        if omni["generationAuthorized"] or account["providerUploadAuthorized"]:
            errors.append("unverified Omni account permits generation or upload")
    if omni["publicationAuthorized"] and not omni["generationAuthorized"]:
        errors.append("Omni publication enabled without generation authority")

    return errors


class OutreachCampaignContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_json(ROOT / "operations" / "outreach-campaign.contract.json")
        cls.contract_schema = load_json(
            ROOT / "operations" / "schemas" / "outreach-campaign-v1.schema.json"
        )
        cls.receipt = load_json(
            ROOT / "operations" / "x-outreach-readiness-receipt.json"
        )
        cls.receipt_schema = load_json(
            ROOT / "operations" / "schemas" / "x-outreach-readiness-v1.schema.json"
        )
        cls.media_schema = load_json(
            ROOT / "operations" / "schemas" / "outreach-media-provenance-v1.schema.json"
        )
        cls.reply_ledger = load_json(ROOT / "distribution" / "x-replies.json")
        cls.contract_validator = Draft202012Validator(
            cls.contract_schema, format_checker=FormatChecker()
        )

    def test_schemas_and_current_records_validate(self):
        for schema in (self.contract_schema, self.receipt_schema, self.media_schema):
            Draft202012Validator.check_schema(schema)
        self.contract_validator.validate(self.contract)
        Draft202012Validator(
            self.receipt_schema, format_checker=FormatChecker()
        ).validate(self.receipt)
        self.assertEqual([], semantic_errors(self.contract, self.receipt, self.reply_ledger))

    def test_public_campaign_is_fail_closed(self):
        self.assertEqual(
            "readiness-active-public-campaign-blocked", self.contract["status"]
        )
        self.assertEqual("not_started", self.contract["campaignWindow"]["status"])
        self.assertEqual(0, self.contract["readinessWindow"]["cashBudgetUsd"])
        for field, value in self.contract["externalActions"].items():
            with self.subTest(field=field):
                self.assertIn(value, (False, 0))

    def test_rss_and_diagnostics_do_not_claim_return(self):
        conversion = self.contract["primaryConversion"]
        self.assertEqual("rss_follow_intent", conversion["id"])
        self.assertEqual("rss", conversion["returnPath"])
        self.assertFalse(conversion["observable"])
        self.assertFalse(conversion["emailCollectionAuthorized"])
        diagnostics = self.contract["diagnostics"]
        self.assertEqual("unknown", diagnostics["siteReturnStatus"])
        self.assertFalse(diagnostics["siteInstrumentationActivated"])
        self.assertTrue(diagnostics["officialFirst1000CollectorSeparate"])
        self.assertFalse(diagnostics["officialFirst1000CollectorActivated"])

    def test_x_readiness_records_real_blockers_and_preserves_cap(self):
        self.assertEqual("blocked", self.receipt["status"])
        security = self.receipt["security"]
        self.assertFalse(security["authenticationAppMfaEnabled"])
        self.assertFalse(security["textMessageMfaEnabled"])
        self.assertFalse(security["securityKeyMfaEnabled"])
        self.assertTrue(security["passkeyEnabled"])
        self.assertTrue(security["passkeyVerifiedInOfficialUi"])
        self.assertEqual(
            "operator_reports_never_created", security["passwordCredentialStatus"]
        )
        self.assertFalse(security["passwordResetProtectionEnabled"])
        self.assertEqual(
            "not_applicable_without_password",
            security["passwordResetProtectionDisposition"],
        )
        self.assertEqual("ready", security["status"])
        self.assertNotIn(
            "x-two-factor-authentication-disabled", self.contract["x"]["blockers"]
        )
        self.assertNotIn(
            "x-password-reset-protection-disabled", self.contract["x"]["blockers"]
        )
        self.assertTrue(
            self.receipt["profile"]["pinnedPost"]["immutableEditionDestination"]
        )
        self.assertFalse(
            self.receipt["canonicalBroadcasts"]["latestMorning"]["immutableEditionDestination"]
        )
        self.assertFalse(
            self.receipt["canonicalBroadcasts"]["latestEvening"]["immutableEditionDestination"]
        )
        self.assertEqual(4, self.contract["x"]["enforcedPublishedReplyCap"])
        self.assertFalse(self.contract["x"]["fifthReplyAuthorized"])

    def test_omni_boundary_is_private_rights_clean_and_blocked(self):
        omni = self.contract["geminiOmni"]
        self.assertEqual("Gemini Apps", omni["product"])
        self.assertEqual("Gemini Omni video generation", omni["feature"])
        self.assertFalse(omni["generationAuthorized"])
        self.assertFalse(omni["publicationAuthorized"])
        self.assertTrue(omni["privacyBoundary"]["publicCanonicalInputsOnly"])
        self.assertTrue(omni["privacyBoundary"]["restrictedInformationProhibited"])
        self.assertFalse(omni["rightsBoundary"]["voiceCloningAuthorized"])
        self.assertEqual(
            "restricted-outside-public-repository",
            omni["provenanceBoundary"]["storageClass"],
        )
        self.assertTrue(
            omni["disclosureBoundary"]["materialAiGenerationDisclosureRequired"]
        )

    def test_schema_and_semantics_reject_authority_drift(self):
        paid = deepcopy(self.contract)
        paid["readinessWindow"]["cashBudgetUsd"] = 1
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(paid)

        fifth = deepcopy(self.contract)
        fifth["x"]["fifthReplyAuthorized"] = True
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(fifth)

        unsafe = deepcopy(self.contract)
        unsafe["geminiOmni"]["privacyBoundary"]["restrictedInformationProhibited"] = False
        with self.assertRaises(ValidationError):
            self.contract_validator.validate(unsafe)

        active_action = deepcopy(self.contract)
        active_action["externalActions"]["xReplyAuthorized"] = True
        self.contract_validator.validate(active_action)
        self.assertIn(
            "inactive campaign authorizes xReplyAuthorized",
            semantic_errors(active_action, self.receipt, self.reply_ledger),
        )

    def test_governing_prose_names_the_machine_law(self):
        outreach = (ROOT / "docs" / "OUTREACH_CAMPAIGN.md").read_text(encoding="utf-8")
        doctrine = (ROOT / "FOUNDER_DOCTRINE.md").read_text(encoding="utf-8")
        distribution = (ROOT / "docs" / "DISTRIBUTION_SPEC.md").read_text(
            encoding="utf-8"
        )
        marketing = (ROOT / "docs" / "CLAUDE_CODE_MARKETING_HANDOFF.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "one additional original, edition-derived X post",
            "four remains the machine-enforced ceiling",
            "Gemini Omni",
            "RSS",
            "site return",
        ):
            self.assertIn(phrase, "\n".join((outreach, doctrine, distribution, marketing)))
        self.assertIn("public campaign blocked", outreach)
        self.assertIn("outreach learning campaign", doctrine)
        self.assertIn("The 2026-08-02 seven-day", marketing)


if __name__ == "__main__":
    unittest.main()
