#!/usr/bin/env python3
"""Machine-readable gates for the approved four-week newsletter pilot."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "operations" / "newsletter-pilot.contract.json"


class NewsletterPilotContractTest(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_scope_cadence_and_guided_path_are_exact(self):
        contract = self.contract
        self.assertEqual(1, contract["version"])
        self.assertEqual("signup-approved-sending-blocked", contract["status"])
        self.assertEqual(4, contract["pilot"]["issueCount"])
        self.assertEqual(1, contract["pilot"]["maximumIssuesPerWeek"])
        self.assertEqual("manual-only", contract["pilot"]["sendMode"])
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
        self.assertEqual("privacy@davidsdailybread.com", privacy["publicContact"])
        self.assertTrue(privacy["contactVerified"])
        self.assertFalse(privacy["forwardingDestinationStoredInRepository"])
        self.assertFalse(privacy["subscriberAddressesAllowedInRepository"])
        self.assertNotIn("gmail.com", CONTRACT_PATH.read_text(encoding="utf-8"))

        budget = self.contract["budget"]
        self.assertEqual(0, budget["maximumMonthlyUsd"])
        self.assertEqual(100, budget["maximumActiveSubscribersOnFreePlan"])
        self.assertFalse(budget["paidAddOnsAllowed"])
        self.assertTrue(budget["stopBeforeCharge"])

    def test_signup_is_ready_but_sending_is_blocked(self):
        self.assertTrue(self.contract["signup"]["enabledAfterMerge"])
        sending = self.contract["sending"]
        self.assertFalse(sending["enabled"])
        self.assertFalse(sending["dailyBakeMaySend"])
        self.assertFalse(sending["githubActionsMaySend"])
        self.assertIn(
            "valid-physical-postal-address-not-configured",
            sending["blockedBy"],
        )
        self.assertIn("desktop-and-mobile-test-not-approved", sending["blockedBy"])

    def test_template_carries_four_stages_and_send_checklist(self):
        template = (ROOT / "newsletter" / "weekly-ledger.md").read_text(encoding="utf-8")
        for stage in ("## 1. Start", "## 2. Browse", "## 3. Do", "## 4. Rest"):
            self.assertIn(stage, template)
        for gate in ("valid postal address", "unsubscribe control", "$0"):
            self.assertIn(gate, template)
        self.assertNotIn("—", template)


if __name__ == "__main__":
    unittest.main()
