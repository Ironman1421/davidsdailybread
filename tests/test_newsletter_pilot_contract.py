#!/usr/bin/env python3
"""Machine-readable guards for newsletter strategy with operations disabled."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "operations" / "newsletter-pilot.contract.json"


class NewsletterPilotContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_strategy_is_active_and_historical_pilot_is_not_operational(self):
        contract = self.contract
        self.assertEqual(3, contract["version"])
        self.assertEqual("strategy-active-operations-disabled", contract["status"])
        self.assertEqual(
            "historical-format-not-active-pilot", contract["pilot"]["status"]
        )
        decision = contract["founderDecision"]
        self.assertTrue(decision["strategyWorkAuthorized"])
        self.assertTrue(decision["localProductIntegrationPrototypesAuthorized"])
        self.assertFalse(decision["newsletterSendingAuthorized"])
        self.assertFalse(decision["activationWorkAuthorized"])
        self.assertTrue(decision["scopedOperationalApprovalRequired"])
        self.assertTrue(decision["preserveCurrentFailClosedSignupPageState"])
        self.assertEqual(4, contract["pilot"]["issueCount"])
        self.assertEqual(1, contract["pilot"]["maximumIssuesPerWeek"])
        self.assertEqual("disabled", contract["pilot"]["sendMode"])
        self.assertEqual("manual-only", contract["pilot"]["historicalSendMode"])
        self.assertEqual(4, contract["pilot"]["pauseAfterIssue"])
        self.assertIsNone(contract["pilot"]["firstSendDate"])
        self.assertIsNone(contract["pilot"]["sendDay"])
        self.assertIsNone(contract["pilot"]["sendTime"])
        self.assertEqual(["Start", "Browse", "Do", "Rest"], contract["editorialFlow"])

    def test_consent_privacy_and_budget_fail_closed(self):
        consent = self.contract["consent"]
        self.assertTrue(consent["freshSignupsOnly"])
        self.assertFalse(consent["importRetiredList"])
        self.assertFalse(consent["reactivateRetiredList"])
        self.assertTrue(consent["confirmationRequiredBeforeActive"])

        privacy = self.contract["privacy"]
        self.assertIsNone(privacy["publicContact"])
        self.assertTrue(privacy["verifiedContactRequiredBeforeReopen"])
        self.assertFalse(privacy["forwardingDestinationStoredInRepository"])
        self.assertFalse(privacy["subscriberAddressesAllowedInRepository"])
        self.assertNotIn("gmail.com", CONTRACT_PATH.read_text(encoding="utf-8"))

        budget = self.contract["budget"]
        self.assertEqual(0, budget["maximumMonthlyUsd"])
        self.assertEqual(100, budget["maximumActiveSubscribersOnFreePlan"])
        self.assertFalse(budget["paidAddOnsAllowed"])
        self.assertTrue(budget["stopBeforeCharge"])

    def test_fail_closed_signup_state_is_preserved_and_activation_is_blocked(self):
        signup = self.contract["signup"]
        self.assertTrue(signup["currentFailClosedStatePreserved"])
        self.assertFalse(signup["collectsAddresses"])
        self.assertFalse(signup["providerEndpointPresent"])
        self.assertFalse(signup["changesAuthorized"])
        self.assertFalse(signup["presenceAuthorizesSending"])
        sending = self.contract["sending"]
        self.assertFalse(sending["enabled"])
        self.assertFalse(sending["activationWorkEnabled"])
        self.assertFalse(sending["draftingEnabled"])
        self.assertFalse(sending["testSendsEnabled"])
        self.assertFalse(sending["providerConfigurationEnabled"])
        self.assertTrue(sending["scopedFounderOperationalApprovalRequired"])
        self.assertFalse(sending["dailyBakeMaySend"])
        self.assertFalse(sending["githubActionsMaySend"])
        self.assertIn(
            "founder-direction-strategy-only-no-operational-pilot",
            sending["blockedBy"],
        )

    def test_template_carries_four_stages_and_send_checklist(self):
        template = (ROOT / "newsletter" / "weekly-ledger.md").read_text(encoding="utf-8")
        self.assertIn("historical format, not an active pilot", template)
        self.assertIn("approves a scoped operational pilot", template)
        for stage in ("## 1. Start", "## 2. Browse", "## 3. Do", "## 4. Rest"):
            self.assertIn(stage, template)
        for gate in ("valid postal address", "unsubscribe control", "$0"):
            self.assertIn(gate, template)
        self.assertNotIn("—", template)


if __name__ == "__main__":
    unittest.main()
