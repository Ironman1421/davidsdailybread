#!/usr/bin/env python3
"""Executable invariants for the single-controller execution lanes."""

from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATH = ROOT / "operations" / "program-control.json"
SAFETY_CONTRACT_PATH = (
    ROOT / "operations" / "minimum-viable-safety.contract.json"
)
PUBLISHING_CONTRACT_PATH = ROOT / "operations" / "publishing.contract.json"
X_BROADCAST_CONTRACT_PATH = ROOT / "operations" / "x-broadcast.contract.json"


class ProgramControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))

    def test_single_controller_laned_policy_is_explicit(self):
        control = self.control
        policy = control["executionPolicy"]
        lanes = policy["lanes"]

        self.assertEqual("single-controller-laned-execution", control["mode"])
        self.assertNotIn("activeItemId", control)
        self.assertEqual(3, lanes["local_work"]["maximumInProgress"])
        self.assertFalse(lanes["local_work"]["productionMutationAllowed"])
        self.assertEqual(1, lanes["production_mutation"]["maximumInProgress"])
        self.assertFalse(lanes["routine_operations"]["queueParticipation"])
        self.assertTrue(lanes["routine_operations"]["usesProductionMutationLock"])
        self.assertFalse(policy["workerMaySelectNext"])
        self.assertFalse(policy["workerMayAddQueueItems"])
        self.assertFalse(policy["discoveredWorkIsExecutionAuthority"])
        self.assertIn("Within each project lane", policy["selectionRule"])
        self.assertIn("Routine operations remain outside", policy["selectionRule"])
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

        self.assertEqual(27, by_id["DDB-PC-031"]["sequence"])
        self.assertEqual(28, by_id["DDB-PC-028"]["sequence"])
        self.assertIn("DDB-PC-031", by_id["DDB-PC-028"]["dependencies"])

    def test_active_items_match_lane_capacity_and_selection_rule(self):
        items = self.control["items"]
        by_id = {item["id"]: item for item in items}
        project_lanes = ("local_work", "production_mutation")
        active_by_lane = {
            lane: [
                item
                for item in items
                if item["status"] == "in_progress"
                and item.get("executionLane") == lane
            ]
            for lane in project_lanes
        }
        eligible = [
            item
            for item in items
            if item["status"] == "pending"
            and item.get("executionLane") in project_lanes
            and all(by_id[dependency]["status"] == "complete" for dependency in item["dependencies"])
            and (
                item["authorization"]["type"] == "none"
                or item["authorization"].get("granted") is True
            )
        ]

        active_ids = self.control["activeItemIds"]
        self.assertEqual(
            active_ids["local_work"],
            [item["id"] for item in active_by_lane["local_work"]],
        )
        production = active_by_lane["production_mutation"]
        self.assertEqual(
            active_ids["production_mutation"],
            production[0]["id"] if production else None,
        )

        for lane in project_lanes:
            capacity = self.control["executionPolicy"]["lanes"][lane][
                "maximumInProgress"
            ]
            active = active_by_lane[lane]
            lane_eligible = [
                item for item in eligible if item["executionLane"] == lane
            ]
            self.assertLessEqual(len(active), capacity)
            if active:
                self.assertEqual(
                    [],
                    [
                        item
                        for item in lane_eligible
                        if item["sequence"] < min(a["sequence"] for a in active)
                    ],
                )
            if len(active) < capacity:
                self.assertEqual([], lane_eligible)

        if not any(active_by_lane.values()):
            self.assertEqual([], eligible)
            self.assertEqual("no_eligible_item", self.control["halt"]["type"])
            self.assertEqual([], self.control["halt"]["eligibleItemIds"])
            self.assertIn("explicit approval", self.control["halt"]["reason"])
        else:
            self.assertIsNone(self.control["halt"])

    def test_states_completion_evidence_and_pauses_are_valid(self):
        allowed = set(self.control["states"])

        for item in self.control["items"]:
            self.assertIn(item["status"], allowed)
            if item["status"] in {"pending", "in_progress"}:
                self.assertIn(
                    item.get("executionLane"),
                    {"local_work", "production_mutation"},
                )
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

    def test_minimum_viable_safety_contract_preserves_useful_boundaries(self):
        contract = json.loads(SAFETY_CONTRACT_PATH.read_text(encoding="utf-8"))
        standing = contract["standingAuthority"]

        self.assertEqual("DDB-PC-031", contract["programItem"])
        self.assertEqual(3, contract["lanes"]["local_work"]["maximumInProgress"])
        self.assertEqual(
            1,
            contract["lanes"]["production_mutation"]["maximumInProgress"],
        )
        self.assertFalse(contract["lanes"]["routine_operations"]["queueParticipation"])
        for operation in (
            "scheduledBake",
            "staleRunCancellation",
            "pagesRebuild",
            "canonicalXBroadcast",
            "boundedLowRiskRelease",
        ):
            self.assertTrue(standing[operation]["authorized"])

        self.assertEqual(1, standing["pagesRebuild"]["maximumPerExactCommit"])
        self.assertEqual(15, standing["staleRunCancellation"]["staleAfterMinutes"])
        self.assertTrue(
            standing["staleRunCancellation"][
                "requiresSupersededOrBlockingNewerNominalSlot"
            ]
        )
        self.assertFalse(
            standing["boundedLowRiskRelease"]["separateExactShaApprovalRequired"]
        )
        self.assertFalse(contract["outreachCampaignActivated"])

        publishing = json.loads(
            PUBLISHING_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        x_broadcast = json.loads(
            X_BROADCAST_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(
            "operations/minimum-viable-safety.contract.json",
            publishing["routineAuthority"]["contract"],
        )
        self.assertTrue(
            publishing["routineAuthority"]["scheduledBakesStandingAuthorized"]
        )
        self.assertEqual(
            1,
            publishing["routineAuthority"]["pagesRecovery"][
                "maximumRebuildsPerExactCommit"
            ],
        )
        self.assertTrue(
            x_broadcast["authority"][
                "activeCanonicalBroadcasterStandingAuthorized"
            ]
        )
        self.assertFalse(x_broadcast["authority"]["outreachCampaignIncluded"])

        explicit = set(contract["explicitApprovalRequired"])
        expected_fragments = {
            "spending",
            "credential",
            "provider",
            "personal-or-spiritual-data",
            "email",
            "community",
            "public-reply",
            "generated-media",
            "theology",
            "destructive",
        }
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in value for value in explicit), fragment)

        doctrine = (ROOT / "FOUNDER_DOCTRINE.md").read_text(encoding="utf-8")
        self.assertIn("Minimum viable safety and delivery authority", doctrine)
        self.assertIn(
            "The outreach campaign remains inactive", " ".join(doctrine.split())
        )

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
            self.assertIn("minimum-viable-safety.contract.json", text)
            self.assertIn("production", normalized)
            self.assertIn("local", normalized)


if __name__ == "__main__":
    unittest.main()
