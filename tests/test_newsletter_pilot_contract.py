#!/usr/bin/env python3
"""Machine-readable guards for the founder-paused newsletter plan."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "operations" / "newsletter-pilot.contract.json"


class NewsletterPilotContractTest(unittest.TestCase):
    def setUp(self):
        self.text = CONTRACT_PATH.read_text(encoding="utf-8")
        self.contract = json.loads(self.text)

    def test_historical_scope_is_frozen_under_founder_pause(self):
        contract = self.contract
        self.assertEqual(2, contract["version"])
        self.assertEqual("founder-paused-no-activation", contract["status"])
        self.assertEqual("frozen-historical-plan", contract["pilot"]["status"])
        decision = contract["founderDecision"]
        self.assertFalse(decision["newsletterSendingAuthorized"])
        self.assertFalse(decision["activationWorkAuthorized"])
        self.assertTrue(decision["explicitReversalRequired"])
        self.assertTrue(decision["preserveLiveSignupPageState"])
        self.assertEqual(4, contract["pilot"]["issueCount"])
        self.assertEqual(1, contract["pilot"]["maximumIssuesPerWeek"])
        self.assertEqual("disabled", contract["pilot"]["sendMode"])
        self.assertEqual("manual-only", contract["pilot"]["historicalSendMode"])
        self.assertEqual(4, contract["pilot"]["pauseAfterIssue"])
        self.assertIsNone(contract["pilot"]["firstSendDate"])
        self.assertIsNone(contract["pilot"]["sendDay"])
        self.assertIsNone(contract["pilot"]["sendTime"])

    def test_every_activation_capability_is_false(self):
        activation = self.contract["activation"]
        self.assertTrue(activation)
        self.assertTrue(all(value is False for value in activation.values()))
        self.assertFalse(self.contract["provider"]["externalMutationAuthorized"])
        self.assertFalse(self.contract["provider"]["privateModeVerified"])

        privacy = self.contract["privacy"]
        self.assertFalse(privacy["subscriberAddressesAllowedInRepository"])
        self.assertFalse(privacy["subscriberAddressesAllowedInGitHubActions"])
        self.assertFalse(privacy["subscriberAddressesAllowedInSupabase"])
        self.assertFalse(privacy["recipientLevelDataMayBeCommitted"])
        self.assertNotIn("gmail.com", self.text)

        budget = self.contract["budget"]
        self.assertEqual(0, budget["maximumMonthlyUsd"])
        self.assertFalse(budget["paidAddOnsAllowed"])
        self.assertTrue(budget["stopBeforeCharge"])

    def test_signup_state_is_preserved_but_all_activation_is_blocked(self):
        signup = self.contract["signup"]
        self.assertTrue(signup["currentLiveStatePreserved"])
        self.assertFalse(signup["changesAuthorized"])
        self.assertFalse(signup["presenceAuthorizesSending"])
        sending = self.contract["sending"]
        self.assertFalse(sending["enabled"])
        self.assertFalse(sending["activationWorkEnabled"])
        self.assertFalse(sending["draftingEnabled"])
        self.assertFalse(sending["testSendsEnabled"])
        self.assertFalse(sending["providerConfigurationEnabled"])
        self.assertTrue(sending["explicitFounderReversalRequired"])
        self.assertFalse(sending["dailyBakeMaySend"])
        self.assertFalse(sending["githubActionsMaySend"])
        self.assertIn(
            "founder-direction-no-newsletter-or-activation-work",
            sending["blockedBy"],
        )

    def test_template_carries_four_stages_and_send_checklist(self):
        template = (ROOT / "newsletter" / "weekly-ledger.md").read_text(encoding="utf-8")
        self.assertIn("frozen historical template", template)
        self.assertIn("explicitly reverses the newsletter pause", template)
        for stage in ("## 1. Start", "## 2. Browse", "## 3. Do", "## 4. Rest"):
            self.assertIn(stage, template)
        for gate in ("valid postal address", "unsubscribe control", "$0"):
            self.assertIn(gate, template)
        self.assertNotIn("—", template)


if __name__ == "__main__":
    unittest.main()
