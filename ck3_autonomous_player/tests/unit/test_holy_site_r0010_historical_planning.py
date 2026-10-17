from __future__ import annotations
import hashlib
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from xar_autoplayer.holy_site_planning_knowledge import query_holy_site_planning_knowledge_v1


class HolySiteR0010HistoricalPlanningTests(unittest.TestCase):
    def case(self, action, case_id):
        result = query_holy_site_planning_knowledge_v1(action)
        self.assertFalse(result["state_observed"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["native_legality"])
        return next(c for c in result["knowledge"]["historical_case_evidence"] if c["case_id"] == case_id)

    def test_scoped_history_is_discoverable_without_granting_current_permission(self):
        for action, cid in (("promote", "faith-e01-r9-grade-cache-boundary-20261017"),
                            ("enshrine_relic", "faith-e01-r0010-enshrine-recipient-cache-20261017"),
                            ("abandon", "faith-e01-r0010-shared-site14-exit-20261017")):
            with self.subTest(action=action):
                case = self.case(action, cid)
                self.assertFalse(case["current_state_observed"])
                self.assertFalse(case["current_world_state_observed"])
                self.assertIsNone(case["native_legality"])
                self.assertFalse(case["action_ready"])
                self.assertEqual(case["machine_id"], "4-8e1c2f1861")
                raw = (PROJECT_ROOT.parent / case["record_path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), case["record_sha256"])

    def test_replacement_and_shared_exit_preserve_observation_boundaries(self):
        swap = self.case("enshrine_relic", "faith-e01-r0010-direct-relic-replacement-20261017")["observed"]
        self.assertEqual(swap["after"]["old_artifact237_character_owner_id"], 15893)
        self.assertNotEqual(swap["actor_id"], swap["county_holder_id"])
        self.assertEqual(swap["piety_before_after"], [2250, 2250])
        self.assertFalse(swap["actual_opinion_after_observed"])
        self.assertFalse(swap["actual_cb_grant_observed"])
        exit_case = self.case("abandon", "faith-e01-r0010-shared-site14-exit-20261017")["observed"]
        self.assertFalse(exit_case["current_native_evaluation_after"]["is_active"])
        self.assertEqual(exit_case["current_native_evaluation_after"]["active_artifact_rarity_sum"], 0)
        self.assertTrue(exit_case["world_cached_after"]["is_active"])
        self.assertEqual(exit_case["world_cached_after"]["total_active_artifact_rarity"], 2)
        self.assertTrue(exit_case["current_native_evaluation_after"]["cache_evaluation_disagreement"])
        self.assertFalse(exit_case["all_benefits_zero_observed"])
        self.assertFalse(exit_case["ui_refresh_observed"])
        self.assertFalse(exit_case["last_associated_faith_abandon_tested"])

    def test_history_mutation_and_unsupported_build_do_not_leak(self):
        cid = "faith-e01-r0010-shared-site14-exit-20261017"
        case = self.case("abandon", cid)
        case["observed"]["world_cached_after"]["is_active"] = False
        self.assertTrue(self.case("abandon", cid)["observed"]["world_cached_after"]["is_active"])
        foreign = query_holy_site_planning_knowledge_v1("abandon", ck3_build="1.20.1")
        self.assertIsNone(foreign["knowledge"])
        self.assertFalse(foreign["state_observed"])
        self.assertFalse(foreign["action_ready"])
        self.assertIsNone(foreign["native_legality"])


    def test_final_faith_exit_uses_independent_owner_and_preserves_site_object(self):
        cid = "faith-e01-r0011-sole-faith-exit-return-20261017"
        for action in ("create", "abandon"):
            case = self.case(action, cid)
            self.assertFalse(case["current_state_observed"])
            self.assertFalse(case["current_world_state_observed"])
            self.assertIsNone(case["native_legality"])
            self.assertFalse(case["action_ready"])
            raw = (PROJECT_ROOT.parent / case["record_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), case["record_sha256"])
            observed = case["observed"]
            self.assertEqual(observed["faith_site_count_chain"], [6, 7, 6])
            self.assertTrue(observed["site_object_still_available_after"])
            self.assertEqual(observed["site_associated_faith_ids_after"], [])
            self.assertEqual(observed["site_artifact_ids_after"], [])
            self.assertEqual(observed["independent_actual_character_owner_id"], 15893)
            self.assertIsNone(observed["holy_site_owner_id_after"])
            self.assertTrue(observed["player_owned_reference_member_after"])
            self.assertTrue(observed["player_inventory_contains237_after"])
            self.assertFalse(observed["player_equipped237_after"])
            self.assertFalse(observed["receiver_role_empirically_distinguished"])
            self.assertFalse(observed["initial_open_predispatch_rejection_is_business_rejection"])
            self.assertEqual(observed["successful_abandon_confirm_count"], 1)
            self.assertFalse(observed["last_exit_action_recorded"])


if __name__ == "__main__":
    unittest.main()
