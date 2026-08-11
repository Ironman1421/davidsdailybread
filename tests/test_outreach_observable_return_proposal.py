"""Fail-closed checks for the DDB-PC-028 observable-return proposal."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = ROOT / "operations" / "outreach-observable-return-proposal.json"
DOCUMENT_PATH = ROOT / "docs" / "OUTREACH_OBSERVABLE_RETURN_PROPOSAL.md"


class ObservableReturnProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
        cls.document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def test_proposal_is_not_execution_authority(self):
        self.assertEqual("proposal-only-not-authority", self.proposal["status"])
        self.assertEqual("DDB-PC-028", self.proposal["programItem"])
        path = self.proposal["recommendedPath"]
        for field in ("selected", "implemented", "validated", "activated"):
            self.assertFalse(path[field])
        self.assertIn("creates no execution authority", self.document)

    def test_declared_event_is_exact_url_click_not_a_person_or_page_load(self):
        path = self.proposal["recommendedPath"]
        self.assertEqual("x_exact_edition_url_link_click", path["id"])
        self.assertEqual("Link clicks", path["providerMetricLabel"])
        self.assertEqual("Clicks on a URL in the post", path["providerDefinition"])
        self.assertFalse(path["countsPeople"])
        self.assertFalse(path["provesPageLoad"])
        self.assertFalse(path["provesRepeatReader"])
        self.assertFalse(path["officialFirst1000Metric"])

    def test_existing_zero_is_evidence_but_not_current_validation(self):
        evidence = self.proposal["existingEvidence"]
        self.assertEqual(
            "operations/x-outreach-readiness-receipt.json",
            evidence["readinessReceipt"],
        )
        self.assertEqual("available", evidence["postActivityAnalytics"])
        self.assertEqual(0, evidence["displayedLinkClicks"])
        self.assertFalse(evidence["evidenceIsCurrentValidation"])

    def test_url_boundary_accepts_only_bare_immutable_evening_editions(self):
        boundary = self.proposal["urlBoundary"]
        pattern = re.compile(boundary["canonicalPattern"])
        self.assertIsNotNone(
            pattern.fullmatch(
                "https://davidsdailybread.com/editions/2026-08-11-evening.html"
            )
        )
        for invalid in (
            "https://davidsdailybread.com/",
            "https://davidsdailybread.com/editions/2026-08-11-morning.html",
            "https://davidsdailybread.com/editions/2026-08-11-evening.html?utm_source=x",
            "https://davidsdailybread.com/editions/2026-08-11-evening.html#return",
            "https://example.com/editions/2026-08-11-evening.html",
        ):
            with self.subTest(url=invalid):
                self.assertIsNone(pattern.fullmatch(invalid))
        for field, value in boundary.items():
            if field.endswith("Authorized"):
                self.assertFalse(value)

    def test_repository_receipt_is_aggregate_only(self):
        allowed = set(self.proposal["repositoryReceiptAllowlist"])
        prohibited = set(self.proposal["prohibitedRepositoryData"])
        self.assertIn("aggregateValue", allowed)
        self.assertIn("restrictedEvidenceSha256", allowed)
        self.assertIn("viewer-or-clicker-identity", prohibited)
        self.assertIn("ip-address", prohibited)
        self.assertIn("row-level-export", prohibited)
        self.assertIn("provider-credential", prohibited)
        self.assertTrue(allowed.isdisjoint(prohibited))

    def test_read_only_validation_cannot_mutate_provider_state(self):
        validation = self.proposal["validation"]
        self.assertEqual("one-read-only-existing-post-preflight", validation["mode"])
        self.assertTrue(validation["metricAvailabilityMustPreexist"])
        self.assertTrue(validation["explicitDisplayedZeroProvesObservability"])
        self.assertFalse(validation["explicitDisplayedZeroProvesReturnOccurred"])
        for field, value in validation.items():
            if field.endswith("Authorized"):
                self.assertFalse(value)

    def test_proposal_authorizes_no_external_action(self):
        authority = self.proposal["externalActionsAuthorized"]
        self.assertEqual(0, authority["spendUsd"])
        for field, value in authority.items():
            if field != "spendUsd":
                self.assertFalse(value, field)

    def test_failure_remains_blocked_and_rejects_proxy_substitutes(self):
        failure = self.proposal["failureBehavior"]
        self.assertTrue(failure["selectedPathRemainsNull"])
        self.assertTrue(failure["campaignReadinessRemainsBlocked"])
        self.assertTrue(failure["siteReturnRemainsUnknown"])
        self.assertFalse(failure["campaignClockStarts"])
        for substitute in (
            "impressions",
            "profile-visits",
            "permalink-clicks",
            "rss-intent",
            "public-page-availability",
        ):
            self.assertIn(substitute, failure["invalidSubstituteMetrics"])

    def test_document_contains_separate_approval_boundaries(self):
        self.assertIn("Implementation and read-only validation approval", self.document)
        self.assertIn("Exact-head release approval", self.document)
        self.assertIn("Campaign activation approval", self.document)
        self.assertIn("Not proposed or requested here", self.document)


if __name__ == "__main__":
    unittest.main()
