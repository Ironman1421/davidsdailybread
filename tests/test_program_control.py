#!/usr/bin/env python3
"""Executable invariants for the single-controller execution queue."""

from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATH = ROOT / "operations" / "program-control.json"


class ProgramControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))

    def test_single_controller_policy_is_explicit(self):
        control = self.control
        policy = control["executionPolicy"]

        self.assertEqual("single-controller-serial-execution", control["mode"])
        self.assertEqual(1, policy["maximumInProgress"])
        self.assertFalse(policy["workerMaySelectNext"])
        self.assertFalse(policy["workerMayAddQueueItems"])
        self.assertFalse(policy["discoveredWorkIsExecutionAuthority"])
        self.assertIn("lowest-sequence pending item", policy["selectionRule"])
        self.assertIn("Do not invent substitute work", policy["noEligibleItemRule"])

    def test_queue_has_contiguous_unique_order_and_valid_dependencies(self):
        items = self.control["items"]
        ids = [item["id"] for item in items]
        sequences = [item["sequence"] for item in items]
        by_id = {item["id"]: item for item in items}

        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(list(range(1, len(items) + 1)), sequences)
        self.assertEqual(len(items), len(by_id))

        for item in items:
            for dependency in item["dependencies"]:
                self.assertIn(dependency, by_id)
                self.assertLess(by_id[dependency]["sequence"], item["sequence"])

    def test_active_item_or_explicit_halt_matches_selection_rule(self):
        items = self.control["items"]
        by_id = {item["id"]: item for item in items}
        active = [
            item for item in items if item["status"] == "in_progress"
        ]
        eligible = [
            item
            for item in items
            if item["status"] == "pending"
            and all(by_id[dependency]["status"] == "complete" for dependency in item["dependencies"])
            and (
                item["authorization"]["type"] == "none"
                or item["authorization"].get("granted") is True
            )
        ]

        self.assertLessEqual(len(active), self.control["executionPolicy"]["maximumInProgress"])
        if active:
            self.assertEqual(self.control["activeItemId"], active[0]["id"])
            later_eligible = [item for item in eligible if item["sequence"] < active[0]["sequence"]]
            self.assertEqual([], later_eligible)
        else:
            self.assertIsNone(self.control["activeItemId"])
            self.assertEqual([], eligible)
            self.assertEqual("no_eligible_item", self.control["halt"]["type"])
            self.assertEqual([], self.control["halt"]["eligibleItemIds"])
            self.assertIn("explicit approval", self.control["halt"]["reason"])

    def test_states_completion_evidence_and_pauses_are_valid(self):
        allowed = set(self.control["states"])

        for item in self.control["items"]:
            self.assertIn(item["status"], allowed)
            if item["status"] == "complete":
                self.assertTrue(item.get("completionGate"))
                self.assertTrue(item.get("completedAt"))
                self.assertTrue(item.get("evidence"))
            if item["status"] == "paused_by_doctrine":
                self.assertTrue(item.get("pauseAuthority"))
                self.assertFalse(item["authorization"].get("granted", False))

    def test_external_mutations_require_david_approval(self):
        for item in self.control["items"]:
            if item["externalMutation"]:
                self.assertIn(
                    item["authorization"]["type"],
                    {"explicit_david", "explicit_david_reversal"},
                )
                self.assertIn("granted", item["authorization"])

    def test_completed_checkout_and_control_cleanup_stay_closed(self):
        by_id = {item["id"]: item for item in self.control["items"]}

        for item_id in ("DDB-PC-013", "DDB-PC-014"):
            item = by_id[item_id]
            self.assertEqual("complete", item["status"])
            self.assertTrue(item["authorization"]["granted"])
            self.assertTrue(item["completedAt"])
            self.assertTrue(item["evidence"])
            halt_reason = self.control["halt"]["reason"] if self.control["halt"] else ""
            self.assertNotIn(item_id, halt_reason)

        checkout_record = (
            ROOT / "docs" / "CHECKOUT_RECONCILIATION_2026-08-04.md"
        ).read_text(encoding="utf-8")
        repository_map = (ROOT / "docs" / "REPOSITORY_MAP.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("DDB-PC-013 checkout reconciliation", checkout_record)
        self.assertIn(
            "f488557e74f5bd1d3e9cc424213bfce4dc9cbd55c30ac451ef8cf9d22df885c1",
            checkout_record,
        )
        self.assertIn("CHECKOUT_RECONCILIATION_2026-08-04.md", repository_map)
        self.assertIn("former Spark Counter timer was disabled", repository_map)

    def test_instruction_files_point_to_the_canonical_state_source(self):
        for relative_path in ("AGENTS.md", "CLAUDE.md"):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            self.assertIn("operations/program-control.json", text)
            self.assertIn("sole source of truth", normalized)


if __name__ == "__main__":
    unittest.main()
