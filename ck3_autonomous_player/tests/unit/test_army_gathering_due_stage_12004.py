from copy import deepcopy
import unittest

from army_gathering_due_stage_12004 import (
    COMBAT_MAGIC, ENTRY_KIND, EXE_SHA256,
    project_army_gathering_due_stage_12004 as project,
    reuse_native_empty_gathering_queue,
)


def base(count=0, ids=None):
    return {
        "game_version": "1.20.0.4", "exe_sha256": EXE_SHA256,
        "entry_kind": ENTRY_KIND, "entry_frame_id": "capture7:cleanup-return",
        "manager_identity": "primary-A", "capture_identity": "capture7",
        "entry_state_complete": True,
        "prior_stage_receipt": {"complete_returned_frame": True,
            "returned_frame_id": "capture7:cleanup-return", "manager_identity": "primary-A",
            "capture_identity": "capture7", "source": "2A98C90:no-op-callback-return"},
        "prior_physical_writes": [{"physical_token": "Regi-fallback-alias",
            "offset": 0x1C, "size": 8, "value": 0xFFFFFFFF029C77F8}],
        "entry_state": {
            "primary_queue_158": {"physical_token": "primary-A", "data_token": "queue-storage",
                "signed_count": count, "backing_ids": [19, -1] if ids is None else ids},
            "physical_chunks": {"Regi-fallback-alias:2": {"current": 61,
                "maximum": 100, "owner": -1, "ordinal": 2, "association": 73,
                "flag14": 1, "state": 3, "date1c": 0xFFFFFFFF029C77F8}},
            "primary30_original_occurrences": ["Regi-fallback-alias", "Regi-fallback-alias"],
            "army_rosters": {"Army-A": ["ArRg-X", "ArRg-X"]},
            "table170_and_caches": {"ArRg-X": {"current": 61, "max": 100}},
            "date_pointer_full_qword": 0xD4A3000000000018,
        },
    }


def combat_stage():
    stage = base(3, [0x1000001, 0x2000001, 0x1000001, 999])
    state = stage["entry_state"]
    state.update({
        "army_registry": {"present": True, "slot_limit": 2,
            "slots": {"1": "Army-A"}, "fallback_token": "Army-fallback"},
        "army_objects": {"Army-A": {"full_id": 0x1000001, "combat_full_id": 0x1000002},
            "Army-fallback": {"full_id": -1, "combat_full_id": 0x2000002}},
        "combat_registry": {"present": True, "slot_limit": 3,
            "slots": {"2": "Combat-A"}, "fallback_token": "Combat-fallback"},
        "combat_objects": {"Combat-A": {"full_id": 0x1000002, "magic": COMBAT_MAGIC},
            "Combat-fallback": {"full_id": 77, "magic": COMBAT_MAGIC}},
    })
    return stage


class GatheringDueStageTests(unittest.TestCase):
    def assert_preserved(self, entry, returned):
        expected = deepcopy(entry)
        expected["primary_queue_158"].update(signed_count=0, count_basis="derived_actual4_return")
        self.assertEqual(returned, expected)

    def test_empty_preserves_cleanup_alias_rosters_caches_and_raw_date(self):
        stage = base()
        original = deepcopy(stage)
        result = project(stage)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["direct_write_effects"], [])
        self.assertEqual(result["physical_write_effects"], stage["prior_physical_writes"])
        self.assert_preserved(stage["entry_state"], result["returned_state"])
        self.assertEqual(stage, original)
        result["returned_state"]["physical_chunks"].clear()
        self.assertEqual(stage, original)

    def test_negative_only_normalizes_count_and_keeps_unread_backing_ids(self):
        stage = base(-9)
        result = project(stage)
        self.assertEqual(result["entry_count_exact"], -9)
        self.assertEqual(result["direct_write_effects"][0]["store_executed"], True)
        self.assert_preserved(stage["entry_state"], result["returned_state"])
        self.assertEqual(result["returned_state"]["primary_queue_158"]["backing_ids"], [19, -1])

    def test_all_combat_uses_generation_fallback_and_keeps_original_occurrences(self):
        stage = combat_stage()
        result = project(stage)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["branch"], "all_valid_combat")
        self.assertEqual([row["army_physical_token"] for row in result["queue_occurrences"]],
                         ["Army-A", "Army-fallback", "Army-A"])
        self.assertEqual([row["combat_used_fallback"] for row in result["queue_occurrences"]],
                         [False, True, False])
        self.assert_preserved(stage["entry_state"], result["returned_state"])
        self.assertFalse(result["returned_provenance"]["noncombat_refresh_executed"])
        self.assertFalse(result["actual_post_stage_observed"])

    def test_noncombat_never_drains_count_or_returns_invented_refresh_frame(self):
        for field, value in (("magic", 0xFFFFFFFF), ("full_id", -1)):
            stage = combat_stage()
            stage["entry_state"]["combat_objects"]["Combat-fallback"][field] = value
            original = deepcopy(stage)
            result = project(stage)
            self.assertEqual(result["status"], "partial")
            self.assertFalse(result["complete_returned_frame"])
            self.assertIsNone(result["returned_state"])
            self.assertEqual(result["direct_write_effects"], [])
            self.assertIn("24E8100", " ".join(result["next_native_producer_entrances"]))
            self.assertEqual(stage, original)

    def test_missing_physical_slot_is_not_fallback_or_no_effect_evidence(self):
        stage = combat_stage()
        del stage["entry_state"]["army_registry"]["slots"]["1"]
        result = project(stage)
        self.assertEqual(result["missing_inputs"], ["reached_registry_slot"])
        self.assertIsNone(result["returned_state"])

    def test_existing_native_empty_reader_retains_zero_negative_uncertainty(self):
        stage = base()
        reader = {"source": "monthly_first_removal_cleanup_inputs_v1.id_lists.158",
            "available": True, "ids": [], "entry_frame_id": stage["entry_frame_id"],
            "manager_identity": stage["manager_identity"], "capture_identity": stage["capture_identity"]}
        result = reuse_native_empty_gathering_queue(reader, stage)
        self.assertEqual(result["status"], "ready")
        self.assertIsNone(result["entry_count_exact"])
        self.assertIsNone(result["direct_write_effects"][0]["store_executed"])
        self.assertEqual(result["returned_state"]["primary_queue_158"]["backing_ids"], [19, -1])
        contradictory = base(1, [19])
        with self.assertRaises(ValueError):
            reuse_native_empty_gathering_queue(reader, contradictory)
        reader["entry_frame_id"] = "independent-current-query"
        with self.assertRaises(ValueError):
            reuse_native_empty_gathering_queue(reader, stage)

    def test_partial_predecessor_and_incomplete_original_queue_remain_unavailable(self):
        stage = base()
        stage["prior_stage_receipt"]["complete_returned_frame"] = False
        self.assertIsNone(project(stage)["returned_state"])
        stage = combat_stage()
        stage["entry_state"]["primary_queue_158"]["backing_ids"] = [0x1000001]
        self.assertEqual(project(stage)["missing_inputs"], ["all_original_primary158_queue_occurrences"])

    def test_exact_build_and_coherent_predecessor_are_required(self):
        for field, value in (("exe_sha256", "old"), ("entry_kind", "current-army-query")):
            stage = base()
            stage[field] = value
            with self.assertRaises(ValueError):
                project(stage)
        stage = base()
        stage["prior_stage_receipt"]["capture_identity"] = "other-capture"
        with self.assertRaises(ValueError):
            project(stage)


if __name__ == "__main__":
    unittest.main()
