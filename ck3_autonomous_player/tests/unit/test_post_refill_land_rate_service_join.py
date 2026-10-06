from __future__ import annotations
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.service import GameplayBridgeService


def data_snapshot(fraction: int = 10000) -> dict:
    records = []
    for record_index, chunk_index in enumerate([0, 1, 2, 3, 4, 5, 6, 0]):
        current, maximum = (80, 100) if chunk_index == 0 else (0, 0)
        records.append({
            "status": "available", "unavailable_reason": None,
            "record_index": record_index, "persistent_regiment_id": 50001,
            "chunk_index": chunk_index, "chunk_army_regiment_id": 11001,
            "current_soldiers": current, "maximum_soldiers": maximum,
            "effective_current_soldiers": current, "state_raw": 0,
            "native_can_replenish": True, "native_chunk_can_replenish": chunk_index == 0,
            "persistent_monthly_replenishment_fraction_raw": 90000,
            "persistent_monthly_replenishment_fraction_scale": 100000,
            "persistent_prepared_replenishment_fraction_raw": fraction,
            "persistent_prepared_replenishment_fraction_scale": 100000,
        })
    return {"source": "native_all_data_records", "army_regiment_id": 11001,
            "status": "available", "ready": True, "native_data_record_count": 8,
            "unavailable_reason": None, "native_loss_writer_skipped": False,
            "loss_writer_admission_unavailable_reason": None, "records": records}


def row() -> dict:
    regiment = {"stored_index": 0, "army_regiment_id": 11001, "status": "available",
                "unavailable_reason": None, "current_soldiers": 160, "maximum_soldiers": 200,
                "native_supply_loss_eligible": True, "replenishment_records_v1": data_snapshot()}
    occurrences = [{"stored_index": index, "army_id": 11, "status": "available",
                    "unavailable_reason": None, "owner_character_id": 33388,
                    "included": True, "inclusion_basis": "same_owner", "native_carmy_id": 12,
                    "native_eligible_current_soldiers": 160, "regiments": [deepcopy(regiment)]}
                   for index in range(2)]
    return {
        "status": "available", "army_id": 11, "native_carmy_id": 12, "scope_role": "player",
        "war_ids": [], "regiment_count": 0, "current_soldiers": 160, "maximum_soldiers": 200,
        "ai_base_power_raw": 0, "ai_base_power_scale": 100000, "unavailable_reason": None,
        "current_supply_change_monthly_raw": 700000, "current_supply_change_monthly_scale": 100000,
        "current_land_resupply_v1": {
            "source": "native_current_province_land_resupply", "status": "available",
            "unavailable_reason": None, "current_observation_ready": True, "province_id": 1,
            "owner_character_id": 33388, "native_land_branch_applicable": True,
            "native_resupply_eligible": True, "loaded_gain_raw": 700000, "scale": 100000,
        },
        "current_land_supply_rate_inputs_v1": {
            "source": "native_current_province_land_supply_rate_inputs", "status": "available",
            "unavailable_reason": None, "current_observation_ready": True, "province_id": 1,
            "subject_army_id": 11, "subject_carmy_id": 12, "owner_character_id": 33388,
            "commander_raw_full_id": 777, "commander_resolved_full_id": 777,
            "commander_used_native_fallback": False, "native_land_branch_applicable": True,
            "native_province_component_applicable": False, "province_component_raw": 0,
            "commander_modifier_1a9_raw": 0, "loaded_excess_slope_raw": 1000,
            "loaded_min_loss_raw": 50000, "loaded_max_loss_raw": 200000,
            "loaded_divisor_floor_raw": 100000, "scale": 100000,
        },
        "current_province_supply_contributors_v1": {
            "source": "native_current_province_mode0", "status": "available",
            "unavailable_reason": None, "current_usage_ready": True, "contributors_ready": True,
            "province_id": 1, "subject_army_id": 11, "subject_carmy_id": 12,
            "owner_character_id": 33388, "native_province_unit_count": 2,
            "native_supply_limit_soldiers": 340, "native_supply_usage_soldiers": 320,
            "soldiers_scale": 1, "occurrences": occurrences,
        },
    }


class MemoryRoute(GameplayBridgeService):
    """Only backend boundaries are replaced; production query method is inherited."""
    def __init__(self, source: dict) -> None:
        self.source = source
        self.calls = []

    def snapshot(self) -> dict:
        return {"paused": True, "revision": 42, "native_revision": 7, "date_raw": 10000,
                "snapshot_id": "offline-join", "backend_id": "pure-memory-fixture",
                "player_armies": [{"army_id": 11}], "active_wars": [],
                "diagnostics": {"hello": {"game_version": "1.20.0.3"}}}

    def capabilities(self) -> dict:
        return {"action_steps": ["query-army-strengths-v1"]}

    def execute_step(self, step: str, *, expected_revision: int | None = None) -> dict:
        self.calls.append((step, expected_revision))
        return {"status": "available", "army_strengths": [deepcopy(self.source)],
                "native_readiness": {"current_strength": True, "full_monthly": False}}


class PostRefillLandRateServiceJoinTests(unittest.TestCase):
    def test_nonempty_physical_refill_duplicate_usage_and_independent_service_results(self) -> None:
        outputs = {}

        def query(name: str, source: dict) -> dict:
            before = deepcopy(source)
            service = MemoryRoute(source)
            result = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(service.calls, [("query-army-strengths-v1", 42)])
            self.assertEqual(result["status"], "available")
            self.assertEqual(result["scope_status"], "available")
            self.assertEqual(result["native_readiness"], {"current_strength": True, "full_monthly": False})
            self.assertFalse(result["loss_allocation_requests_v1"][0]["applied_loss_ready"])
            self.assertEqual(source, before)
            derived = result["same_input_conditional_post_refill_land_supply_rate_v1"][0]
            self.assertFalse(derived["actual_after"])
            self.assertFalse(derived["actual_post_stage_observed"])
            self.assertFalse(derived["full_monthly_supply_change_ready"])
            outputs[name] = result
            return derived

        value = query("nonempty-physical-duplicate", row())
        self.assertTrue(value["conditional_full_land_rate_ready"])
        self.assertEqual(value["conditional_supply_usage_soldiers"], 360)
        self.assertEqual(value["conditional_post_refill_supply_rate_raw"], -50000)
        self.assertEqual(value["current_observed_total_rate_raw"], 700000)
        usage = value["same_input_conditional_province_supply_usage_v1"]
        self.assertEqual(usage["current_contributor_sum_soldiers"], 320)
        self.assertEqual([item["stored_index"] for item in usage["occurrences"]], [0, 1])
        physical = usage["physical_refill"]["physical_chunks"][0]
        self.assertEqual((physical["same_input_q"], physical["physical_add_count"], physical["current_soldiers"]),
                         (10, 1, 90))
        self.assertEqual(len(physical["data_occurrences"]), 2)
        self.assertEqual(usage["physical_refill"]["regiment_refreshes"][0]["current_soldiers"], 180)
        self.assertEqual(value["same_input_conditional_full_land_supply_rate_v1"]["gain_component_raw"], 0)

        zero_q = row()
        for occurrence in zero_q["current_province_supply_contributors_v1"]["occurrences"]:
            occurrence["regiments"][0]["replenishment_records_v1"] = data_snapshot(0)
        value = query("known-zero-refill-request", zero_q)
        self.assertEqual((value["conditional_supply_usage_soldiers"], value["conditional_post_refill_supply_rate_raw"]),
                         (320, 700000))

        empty = row()
        family = empty["current_province_supply_contributors_v1"]
        family.update(native_province_unit_count=0, native_supply_usage_soldiers=0, occurrences=[])
        empty["current_land_resupply_v1"].update(native_resupply_eligible=False, loaded_gain_raw=0)
        empty["current_supply_change_monthly_raw"] = 0
        value = query("known-empty-zero", empty)
        self.assertTrue(value["conditional_full_land_rate_ready"])
        self.assertEqual((value["conditional_supply_usage_soldiers"], value["conditional_post_refill_supply_rate_raw"]), (0, 0))

        missing = row()
        for occurrence in missing["current_province_supply_contributors_v1"]["occurrences"]:
            occurrence["regiments"][0]["replenishment_records_v1"] = None
        value = query("missing-refill-DATA", missing)
        self.assertFalse(value["conditional_usage_ready"])
        self.assertIsNone(value["conditional_supply_usage_soldiers"])
        self.assertIsNone(value["same_input_conditional_full_land_supply_rate_v1"])
        self.assertIsNone(value["conditional_post_refill_supply_rate_raw"])
        self.assertEqual(value["current_observed_total_rate_raw"], 700000)
        self.assertTrue(value["current_resupply_inputs_v1"]["current_observation_ready"])
        self.assertTrue(value["current_land_rate_inputs_v1"]["current_observation_ready"])

        partial = row()
        partial["current_land_supply_rate_inputs_v1"].update(status="unavailable", current_observation_ready=False,
            unavailable_reason="loaded_slot_unavailable", loaded_divisor_floor_raw=None)
        value = query("partial-independent-raw", partial)
        self.assertTrue(value["conditional_usage_ready"])
        self.assertFalse(value["conditional_full_land_rate_ready"])
        self.assertEqual(value["conditional_supply_usage_soldiers"], 360)
        self.assertEqual(value["current_resupply_inputs_v1"]["loaded_gain_raw"], 700000)

        fleet = row()
        fleet["current_land_resupply_v1"].update(status="not_land", current_observation_ready=False,
            owner_character_id=None, native_land_branch_applicable=False, native_resupply_eligible=None)
        fleet["current_land_supply_rate_inputs_v1"].update(status="not_land", current_observation_ready=False,
            owner_character_id=None, native_land_branch_applicable=False,
            native_province_component_applicable=None, province_component_raw=None, commander_modifier_1a9_raw=None)
        value = query("fleet-independent-usage", fleet)
        self.assertTrue(value["conditional_usage_ready"])
        self.assertFalse(value["conditional_full_land_rate_ready"])
        self.assertEqual(value["current_observed_total_rate_raw"], 700000)

        legacy = row()
        del legacy["current_land_supply_rate_inputs_v1"]
        value = query("legacy-new-family-absent", legacy)
        self.assertFalse(value["conditional_full_land_rate_ready"])
        self.assertIsNone(value["current_land_rate_inputs_v1"])
        self.assertEqual(outputs["legacy-new-family-absent"]["army_strengths"][0]["current_supply_change_monthly_raw"], 700000)
        if target := os.environ.get("XAR_POST_REFILL_JOIN_OUTPUT"):
            with Path(target).open('x', encoding='utf-8') as handle:
                json.dump(outputs, handle, ensure_ascii=False, indent=2)
                handle.write('\n')


if __name__ == "__main__":
    unittest.main()
