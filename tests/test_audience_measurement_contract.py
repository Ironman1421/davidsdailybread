#!/usr/bin/env python3
"""Executable contract for the privacy-safe first-1,000 measurement plan."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from audience.validate_ledger import business_rule_errors


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "audience" / "measurement.schema.json"
LEDGER_PATH = ROOT / "audience" / "monthly-ledger.json"
TRANSITION_SCHEMA_PATH = ROOT / "audience" / "transition.schema.json"
TRANSITION_FIXTURE_PATH = ROOT / "audience" / "fixtures" / "transition.valid.json"
ADAPTER_SCHEMA_PATH = ROOT / "audience" / "browser-adapter.schema.json"
ADAPTER_CONFIG_PATH = ROOT / "audience" / "browser-adapter.config.json"
OPERATING_CONTRACT_PATH = ROOT / "operations" / "audience-measurement.contract.json"
CLOUDFLARE_PLAN_PATH = ROOT / "audience" / "cloudflare" / "canary-plan.json"
CLOUDFLARE_PLAN_SCHEMA_PATH = (
    ROOT / "audience" / "cloudflare" / "canary-plan.schema.json"
)
READER_INTAKE_CONTRACT_PATH = (
    ROOT / "operations" / "reader-intake-pause.contract.json"
)


def complete_month(period: str, qualified: int) -> dict:
    year, month = (int(value) for value in period.split("-"))
    next_period = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )
    return {
        "period": period,
        "definitionVersion": 1,
        "measurementStatus": "complete",
        "coverageStatus": "complete",
        "capturedAt": f"{next_period.isoformat()}T08:00:00Z",
        "sourceReceipt": f"aggregate-receipt-{period}",
        "metrics": {
            "uniqueVisitors": qualified + 300,
            "returningVisitors": qualified + 100,
            "qualifiedEngagedReturningReaders": qualified,
            "engagedSessions": qualified * 2,
            "medianActiveSecondsPerEngagedSession": 92.5,
        },
        "supportingEvidence": {
            "rssFollows": None,
            "rssRepeatRetrievals": None,
            "constructiveSocialParticipants": None,
            "editorialSlipsSubmitted": 3,
            "repeatPublicDiscussionParticipants": None,
        },
        "exclusions": {
            "knownBots": 40,
            "internalVisits": 8,
            "syntheticMonitorVisits": 60,
        },
        "limitations": [
            "A privacy-safe browser visitor is a proxy for a person across devices."
        ],
    }


class AudienceMeasurementContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def test_schema_and_not_measured_baseline_validate(self):
        Draft202012Validator.check_schema(self.schema)
        self.validator.validate(self.ledger)
        self.assertEqual([], business_rule_errors(self.ledger))
        self.assertEqual("implementation-selected", self.ledger["operatingState"])
        self.assertEqual("not-measured", self.ledger["milestoneEvidence"]["status"])
        self.assertEqual([], self.ledger["months"])

    def test_transition_envelope_is_narrow_and_rejects_free_text(self):
        schema = json.loads(TRANSITION_SCHEMA_PATH.read_text(encoding="utf-8"))
        fixture = json.loads(TRANSITION_FIXTURE_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        validator.validate(fixture)
        self.assertEqual(
            {"version", "definitionVersion", "month", "transition", "token"},
            set(fixture),
        )
        for forbidden_field in ("noteText", "submissionContent", "page", "ip"):
            unsafe = {**fixture, forbidden_field: "forbidden"}
            with self.assertRaises(ValidationError):
                validator.validate(unsafe)

        invalid_transition = {**fixture, "transition": "arbitrary-free-text"}
        with self.assertRaises(ValidationError):
            validator.validate(invalid_transition)

        for source_path in (
            ROOT / "audience" / "qualifier.mjs",
            ROOT / "audience" / "browser-adapter.mjs",
            ROOT / "audience" / "collector.mjs",
            ROOT / "audience" / "reporting.mjs",
        ):
            source = source_path.read_text(encoding="utf-8")
            for forbidden_primitive in (
                "fetch(",
                "XMLHttpRequest",
                "sendBeacon",
                "WebSocket",
            ):
                self.assertNotIn(forbidden_primitive, source)
        for template_path in (
            ROOT / "templates" / "home.html",
            ROOT / "templates" / "evening.html",
        ):
            template = template_path.read_text(encoding="utf-8")
            self.assertNotIn("audience/qualifier", template)
            self.assertNotIn("audience/browser-adapter", template)

    def test_browser_adapter_configuration_is_disabled_and_endpoint_free(self):
        schema = json.loads(ADAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))
        config = json.loads(ADAPTER_CONFIG_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(config)
        self.assertFalse(config["enabled"])
        self.assertIsNone(config["endpoint"])

        unsafe = {**config, "enabled": True, "endpoint": "/collect"}
        with self.assertRaises(ValidationError):
            Draft202012Validator(schema).validate(unsafe)

    def test_operating_contract_records_every_activation_gate_as_closed(self):
        contract = json.loads(OPERATING_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            "provider-selected-local-implementation-only",
            contract["operatingStatus"],
        )
        self.assertEqual("cloudflare-workers-d1", contract["provider"])
        self.assertTrue(contract["providerSelectionApproved"])
        self.assertTrue(contract["localProviderSpecificImplementationAuthorized"])
        self.assertTrue(contract["unprovisionedCanaryPlanAuthorized"])
        self.assertIsNone(contract["endpoint"])
        self.assertIsNone(contract["operator"])
        for field in (
            "reviewedCommit",
            "measurementAccount",
            "workerName",
            "d1DatabaseId",
            "rateLimitNamespaceId",
        ):
            self.assertIsNone(contract[field])
        for field in (
            "providerTermsAcceptanceAuthorized",
            "providerTermsAccepted",
            "credentialInstallationAuthorized",
            "credentialInstalled",
            "dnsChangeAuthorized",
            "dnsChanged",
            "externalProvisioningAuthorized",
            "canaryExecutionAuthorized",
            "deploymentAuthorized",
            "activationAuthorized",
            "productionCollectionAuthorized",
            "baselineStartAuthorized",
        ):
            self.assertFalse(contract[field])
        self.assertEqual(0, contract["spendAuthorizedUsd"])
        self.assertFalse(contract["browser"]["enabled"])
        self.assertFalse(contract["browser"]["publicTemplateIntegration"])
        self.assertTrue(contract["collector"]["httpWrapperImplementedLocally"])
        self.assertTrue(
            contract["collector"]["persistentStoreSchemaImplementedLocally"]
        )
        self.assertFalse(contract["collector"]["persistentStoreProvisioned"])
        self.assertFalse(contract["collector"]["providerConfigurationInstalled"])
        self.assertFalse(contract["collector"]["persistentStoreImplemented"])
        self.assertTrue(contract["retention"]["deletionJobImplementedLocally"])
        self.assertFalse(contract["retention"]["deletionJobProvisioned"])
        self.assertFalse(contract["retention"]["deletionJobImplemented"])
        for field in (
            "knownBotControlVerifiedExternally",
            "registrationRateControlVerifiedExternally",
            "syntheticMonitorControlVerifiedExternally",
            "previewAndRenderControlVerifiedExternally",
            "internalTrafficControlVerifiedExternally",
        ):
            self.assertFalse(contract["exclusions"][field])
        self.assertGreaterEqual(len(contract["activationBlockers"]), 10)

    def test_cloudflare_canary_plan_is_approved_only_as_unprovisioned_plan(self):
        schema = json.loads(CLOUDFLARE_PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))
        plan = json.loads(CLOUDFLARE_PLAN_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(plan)
        self.assertEqual("approved-plan-only-unprovisioned", plan["status"])
        self.assertEqual("cloudflare-workers-d1", plan["provider"])
        self.assertEqual(0, plan["spendAuthorizedUsd"])
        for field in (
            "externalProvisioningAuthorized",
            "canaryExecutionAuthorized",
            "deploymentAuthorized",
            "activationAuthorized",
            "productionCollectionAuthorized",
            "baselineStartAuthorized",
        ):
            self.assertFalse(plan[field])
        for field in (
            "reviewedCommit",
            "accountOwner",
            "operator",
            "cloudflareAccountId",
            "workerName",
            "d1DatabaseId",
            "rateLimitNamespaceId",
            "endpoint",
        ):
            self.assertIsNone(plan[field])
        self.assertFalse(plan["routeProposal"]["productionEligible"])
        self.assertIsNone(plan["routeProposal"]["hostname"])

    def test_cloudflare_local_store_is_narrow_atomic_and_not_deployable(self):
        worker = (ROOT / "audience" / "cloudflare" / "worker.mjs").read_text(
            encoding="utf-8"
        )
        sql = (ROOT / "audience" / "cloudflare" / "schema.sql").read_text(
            encoding="utf-8"
        )
        wrangler = (
            ROOT / "audience" / "cloudflare" / "wrangler.unprovisioned.jsonc"
        ).read_text(encoding="utf-8")
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

        for required in (
            "INSERT OR IGNORE INTO audience_visitors",
            "returned_date IS NULL",
            "first_seen_date < ?4",
            "qualified_date IS NULL",
            "returned_date < ?4",
            "DDB_AUDIENCE_MODE === \"canary\"",
            "DDB_LOGGING_DISABLED_VERIFIED",
            "DDB_RETENTION_CONTROL_VERIFIED",
            "DDB_PURGE_ENABLED",
            "DDB_CANARY_SECRET_SHA256",
        ):
            self.assertIn(required, worker)
        self.assertNotIn('DDB_AUDIENCE_MODE === "production"', worker)
        for forbidden in (
            "console.",
            "cf-connecting-ip",
            "CF-Connecting-IP",
            'headers.get("Referer")',
            'headers.get("User-Agent")',
            'headers.get("Cookie")',
        ):
            self.assertNotIn(forbidden, worker)

        for required in (
            "PRIMARY KEY (definition_version, month, token_digest)",
            "audience_visitor_identity_immutable",
            "audience_first_seen_aggregate",
            "audience_returning_aggregate",
            "audience_qualified_aggregate",
            "expires_on = date(first_seen_date, '+35 days')",
        ):
            self.assertIn(required, sql)
        for forbidden in (
            "raw_token",
            "ip_address",
            "user_agent",
            "referrer",
            "page_url",
            "reader_text",
        ):
            self.assertNotIn(forbidden, sql.lower())

        for required in (
            '"workers_dev": false',
            '"preview_urls": false',
            '"enabled": false',
            '"DDB_AUDIENCE_MODE": "disabled"',
            '"database_id": "UNPROVISIONED"',
            '"namespace_id": "UNPROVISIONED"',
        ):
            self.assertIn(required, wrangler)
        for forbidden in ('"routes"', '"crons"', '"DDB_CANARY_SECRET_SHA256"'):
            self.assertNotIn(forbidden, wrangler)
        self.assertFalse(any("wrangler" in script for script in package["scripts"].values()))

    def test_milestone_definition_is_exact(self):
        definition = self.ledger["milestoneDefinition"]
        self.assertEqual("canonical-website", definition["officialCountSurface"])
        self.assertEqual(1000, definition["targetQualifiedReaders"])
        self.assertEqual(3, definition["minimumDistinctVisitDays"])
        self.assertEqual(2, definition["minimumEngagedSessions"])
        self.assertEqual(60, definition["minimumActiveReadingSeconds"])
        self.assertEqual(2, definition["consecutiveQualifyingMonthsRequired"])
        self.assertEqual(
            "supporting-evidence-only-not-added-to-website-total",
            definition["crossChannelCountPolicy"],
        )

    def test_docs_record_local_provider_selection_and_keep_external_actions_gated(self):
        specification = (ROOT / "docs" / "AUDIENCE_MEASUREMENT_SPEC.md").read_text(
            encoding="utf-8"
        )
        decision = (ROOT / "docs" / "AUDIENCE_ANALYTICS_DECISION.md").read_text(
            encoding="utf-8"
        )
        foundation = (ROOT / "docs" / "FIRST_1000_FOUNDATION_PLAN.md").read_text(
            encoding="utf-8"
        )
        runbook = (ROOT / "docs" / "AUDIENCE_MEASUREMENT_RUNBOOK.md").read_text(
            encoding="utf-8"
        )
        endpoint = (ROOT / "docs" / "AUDIENCE_ENDPOINT_RECOMMENDATION.md").read_text(
            encoding="utf-8"
        )
        specification = " ".join(specification.split())
        decision = " ".join(decision.split())
        foundation = " ".join(foundation.split())
        runbook = " ".join(runbook.split())
        endpoint = " ".join(endpoint.split())
        for required in (
            "two consecutive complete calendar months",
            "at least three separate calendar days",
            "at least two engaged sessions",
            "at least 60 seconds of active reading",
            "Supporting evidence is never added",
        ):
            self.assertIn(required, specification)
        for required in (
            "Cloudflare Workers + D1 is the selected provider for local implementation",
            "No account, resource, provider terms acceptance",
            "not installed or measuring",
            "canary execution still require review and David's explicit approval",
        ):
            self.assertIn(required, decision)
        self.assertIn("high-severity privacy risk", foundation)
        self.assertIn("does not authorize its provisioning", foundation)
        for required in (
            "does not approve an endpoint, account, operator, credential",
            "David's explicit approval",
            "not authorized to run",
            "two consecutive complete months",
        ):
            self.assertIn(required, runbook)
        for required in (
            "provider selected for local implementation",
            "no account, terms, DNS change, provisioning, deployment, credential",
            "machine-readable provider is `cloudflare-workers-d1`",
            "Why Supabase is not the first choice here",
        ):
            self.assertIn(required, endpoint)

    def test_privacy_and_activation_fail_closed(self):
        privacy = self.ledger["privacy"]
        for forbidden in (
            "participantLevelRowsAllowedInRepository",
            "namesCollected",
            "emailAddressesCollected",
            "noteTextCollected",
            "readerSubmissionContentCollected",
            "rawIpAddressRetentionAllowed",
            "preciseLocationCollected",
            "advertisingIdentifiersCollected",
            "crossSiteTrackingAllowed",
            "fingerprintingAllowed",
            "queryStringsOrFragmentsStored",
        ):
            self.assertFalse(privacy[forbidden])
        self.assertTrue(privacy["readerVisibleNoticeRequired"])
        self.assertTrue(privacy["optOutRequired"])
        self.assertTrue(privacy["unknownIsNullNeverZero"])

        instrumentation = self.ledger["instrumentation"]
        self.assertEqual("cloudflare-workers-d1", instrumentation["provider"])
        self.assertTrue(instrumentation["providerApprovedByDavid"])
        self.assertFalse(instrumentation["externalProvisioningAuthorized"])
        self.assertFalse(instrumentation["productionCollectionEnabled"])
        self.assertEqual(0, instrumentation["spendAuthorizedUsd"])

        unsafe = deepcopy(self.ledger)
        unsafe["privacy"]["namesCollected"] = True
        with self.assertRaises(ValidationError):
            self.validator.validate(unsafe)

        provisioned = deepcopy(self.ledger)
        provisioned["instrumentation"]["externalProvisioningAuthorized"] = True
        with self.assertRaises(ValidationError):
            self.validator.validate(provisioned)

    def test_interim_reader_intake_change_is_local_closed_and_non_destructive(self):
        contract = json.loads(READER_INTAKE_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(2, contract["version"])
        self.assertEqual("roadmap-active-public-intake-closed", contract["status"])
        self.assertTrue(contract["localImplementationAuthorized"])
        self.assertTrue(contract["reopeningPreparationAuthorized"])
        self.assertTrue(contract["localImplementationPrepared"])
        self.assertFalse(contract["deploymentAuthorized"])
        self.assertFalse(contract["deployed"])
        self.assertFalse(contract["targetSiteAcceptsNewSubmissions"])
        self.assertFalse(contract["targetSiteContainsGoogleFormEndpoint"])
        self.assertEqual("paused-no-write", contract["counterSyncTargetState"])
        for field in (
            "privateStoreProvisioningAuthorized",
            "liveDataMigrationAuthorized",
            "externalGoogleFormDeactivationAuthorized",
            "externalGoogleFormDeactivated",
            "publishedSheetUnpublishAuthorized",
            "publishedSheetUnpublished",
            "existingQueueDeletionAuthorized",
            "repositoryHistoryRewriteAuthorized",
        ):
            self.assertFalse(contract[field])
        self.assertEqual(
            ["download-markdown", "pdf", "email", "copy"],
            contract["chroniclesExportsPreserved"],
        )

    def test_two_consecutive_complete_target_months_are_required(self):
        achieved = deepcopy(self.ledger)
        achieved["updatedAt"] = "2026-10-01T08:00:00Z"
        achieved["operatingState"] = "measuring"
        achieved["instrumentation"] = {
            "status": "collecting",
            "provider": "approved-provider-fixture",
            "providerApprovedByDavid": True,
            "externalProvisioningAuthorized": True,
            "productionCollectionEnabled": True,
            "spendAuthorizedUsd": 0,
            "activationDate": "2026-08-01",
            "sourceReceipt": "founder-approval-fixture",
        }
        achieved["months"] = [
            complete_month("2026-08", 1000),
            complete_month("2026-09", 1004),
        ]
        achieved["milestoneEvidence"] = {
            "status": "achieved",
            "achievedAt": "2026-10-01T08:00:00Z",
            "qualifyingMonths": ["2026-08", "2026-09"],
        }
        self.validator.validate(achieved)
        self.assertEqual([], business_rule_errors(achieved))

        minimal_aggregate = deepcopy(achieved)
        for report in minimal_aggregate["months"]:
            report["metrics"]["engagedSessions"] = None
            report["metrics"]["medianActiveSecondsPerEngagedSession"] = None
            report["limitations"].append(
                "The minimal transition protocol does not transmit total engaged sessions."
            )
        self.validator.validate(minimal_aggregate)
        self.assertEqual([], business_rule_errors(minimal_aggregate))

        undisclosed_unknown = deepcopy(minimal_aggregate)
        undisclosed_unknown["months"][0]["limitations"] = [
            "A browser visitor is only a proxy for a person."
        ]
        self.assertIn(
            "2026-08 must disclose why engaged sessions are unknown",
            business_rule_errors(undisclosed_unknown),
        )

        captured_too_early = deepcopy(achieved)
        captured_too_early["months"][0]["capturedAt"] = "2026-08-31T20:00:00Z"
        self.assertIn(
            "2026-08 complete report was captured before month end",
            business_rule_errors(captured_too_early),
        )

        secret_bearing_receipt = deepcopy(achieved)
        secret_bearing_receipt["months"][0]["sourceReceipt"] = (
            "https://provider.example/report?token=forbidden"
        )
        with self.assertRaises(ValidationError):
            self.validator.validate(secret_bearing_receipt)

        nonconsecutive = deepcopy(achieved)
        nonconsecutive["months"][1] = complete_month("2026-10", 1004)
        nonconsecutive["milestoneEvidence"]["qualifyingMonths"] = [
            "2026-08",
            "2026-10",
        ]
        self.assertIn(
            "milestone evidence months must be consecutive",
            business_rule_errors(nonconsecutive),
        )

    def test_social_support_cannot_make_999_website_readers_equal_1000(self):
        below_target = deepcopy(self.ledger)
        below_target["operatingState"] = "measuring"
        below_target["months"] = [
            complete_month("2026-08", 999),
            complete_month("2026-09", 999),
        ]
        for report in below_target["months"]:
            report["supportingEvidence"]["constructiveSocialParticipants"] = 5000
        below_target["milestoneEvidence"] = {
            "status": "achieved",
            "achievedAt": "2026-10-01T08:00:00Z",
            "qualifyingMonths": ["2026-08", "2026-09"],
        }
        errors = business_rule_errors(below_target)
        self.assertIn(
            "milestone evidence references a partial or below-target month",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
