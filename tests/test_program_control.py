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

    def test_exactly_one_active_item_matches_active_id(self):
        active = [
            item for item in self.control["items"] if item["status"] == "in_progress"
        ]

        self.assertEqual(1, len(active))
        self.assertEqual(self.control["activeItemId"], active[0]["id"])

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

    def test_instruction_files_point_to_the_canonical_state_source(self):
        for relative_path in ("AGENTS.md", "CLAUDE.md"):
            text = (ROOT / relative_path).read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            self.assertIn("operations/program-control.json", text)
            self.assertIn("sole source of truth", normalized)


if __name__ == "__main__":
    unittest.main()
