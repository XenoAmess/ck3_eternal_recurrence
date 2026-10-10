"""One new input-join case; explicit synthetic lineage, retained native operands.

The two-PC/C5 distinction and literal operands reuse the qualified Native66
fixture vector. The historical postimage is supplied directly as already
composed data. No composer, stat arithmetic, native producer or MCP is replayed.
"""
from copy import deepcopy
import json
import unittest

from xar_autoplayer.simulation.battle_entry_person_stage_join_12004 import (
    join_owned_person_postimage_to_knight_stage_12004,
)


KEYS = tuple(range(0xC1, 0xCA))
OPERANDS = (100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000)
HISTORICAL_VALUES = (-25000, 0, 0, -10000, 0, 0, 0, 0, 0)
SELECTED, LINKED = 0x04000002, 0x03000001
C, MODEL, OWNER = 0x22345010, 0x22345000, 0x12345000
OTHER_C = 0x32345010


def _inputs():
    # Independent historical composer/owner inputs; never derived from a
    # current-context observation or recomputed from the append requests.
    postimage = {
        "keys_u16": list(KEYS), "values_q64": list(HISTORICAL_VALUES),
        "composition_kind": "captured_pre_six_aggregate_and_natural_appends",
        "historical_postimage_ready": True, "pre_six_baseline_observed": True,
        "completion_observation_ready": True, "completion_matches_composition": True,
        "character_id": SELECTED, "capture_sequence": 1,
        "capture_date_raw": 53236632, "capture_thread_id": 4242,
        "context_identity": hex(C), "baseline_pc_identity": hex(C + 0x68),
        "completion_pc_identity": hex(C + 0x68),
    }
    owner = {
        "character_id": SELECTED, "capture_sequence": 1,
        "capture_date_raw": 53236632, "capture_thread_id": 4242,
        "context_identity": hex(C), "model_identity": hex(MODEL),
        "owner_character_identity": hex(OWNER), "owner_character_id": SELECTED,
        "owner_matches_capture": True, "context_offset": 0x10, "owner_offset": 8,
        "source_stage": "before_first_original_count_callback",
        "historical_capture": True, "actual_model_write_performed": False,
        "full_helper_ready": False,
    }
    contexts = []
    for index, key in enumerate(KEYS):
        joined = index != 4
        actual_c = C if joined else OTHER_C
        actual_values = list(HISTORICAL_VALUES)
        if not joined:
            actual_values[4] = 15000
        contexts.append({
            "property_key": key, "operand_raw": OPERANDS[index],
            "selected_character_id": SELECTED, "selected_character_identity": OWNER,
            "context_identity": actual_c, "preparation_capture_sequence": 1,
            "preparation_model_identity": MODEL, "preparation_context_identity": C,
            "preparation_owner_character_id": SELECTED,
            "context_matches_preparation": joined, "owner_matches_preparation": True,
            "pc_matches_preparation_post": joined,
            "consumed_pc": {
                "ready": True, "identity": actual_c + 0x68, "count_i32": 9,
                "reason": None, "weight_q100000": 0,
                "properties": {"keys_u16": list(KEYS), "values_q64": actual_values},
            },
            "preparation_stage_lineage": {
                # This source-defined conditional witness is synthetic input
                # for this new Python seam, not a newly observed native event.
                "completed_preparation_lineage_proven": joined,
                "exact_consumed_callsite": True,
                "preparation_capture_complete": True,
                "completion_on_consumption_thread": True,
                "completed_post_pc_matches_consumed": joined,
            },
        })
    event = {
        "sequence": 1, "thread_id": 4242, "observed_date_raw": 53236632,
        "linked_character_id": LINKED, "linked_prowess_points": 3,
        "loaded_damage_multiplier": 100, "loaded_toughness_multiplier": 10,
        "contexts": contexts, "origin": "bridge_query_scratch",
        "wrapper_caller_return_rva": 0x2634509, "output_cache_identity": 0x42345000,
        "entry_association_proven": False, "physical_entry_writeback": None,
    }
    return postimage, owner, event


class EntryPersonStageJoin12004Tests(unittest.TestCase):
    def test_owned_pc_selected_per_ci_with_unmatched_native_pc_and_operands_retained(self):
        postimage, owner, event = _inputs()
        original = deepcopy((postimage, owner, event))
        result = join_owned_person_postimage_to_knight_stage_12004(postimage, owner, event)
        stage = result.inputs.effectiveness
        self.assertEqual(result.historical_property_keys, tuple(key for key in KEYS if key != 0xC5))
        self.assertEqual(result.unmatched_property_keys, (0xC5,))
        self.assertEqual(stage.stage, "actual4_consumed_ci_with_owned_six_stage_postimage")
        self.assertEqual(stage.context.aggregate_properties.keys_u16, KEYS)
        self.assertEqual(stage.context.aggregate_properties.values_q64,
                         (-25000, None, None, -10000, 15000, None, 0, 0, 0))
        self.assertEqual(stage.operand_raw, OPERANDS)
        self.assertEqual(result.inputs.linked_character_full_id, LINKED)
        self.assertEqual(stage.selected_character_full_id, SELECTED)
        self.assertNotEqual(LINKED, SELECTED)
        self.assertEqual((result.inputs.linked_prowess_points,
                          result.inputs.loaded_damage_multiplier,
                          result.inputs.loaded_toughness_multiplier), (3, 100, 10))
        self.assertEqual(result.property_inputs[3]["lookups"][0]["value_q64"], -10000)
        self.assertEqual(result.property_inputs[4]["branch"], "actual_consumed_pc_mode0")
        self.assertEqual(result.property_inputs[4]["context_identity"], OTHER_C)
        self.assertEqual(result.property_inputs[4]["lookups"][0]["value_q64"], 15000)
        self.assertEqual((postimage, owner, event), original)
        self.assertEqual(result.source_ledger["origin"], "bridge_query_scratch")
        self.assertFalse(result.source_ledger["entry_association_proven"])
        self.assertFalse(result.source_ledger["original_entry_invocation_inferred"])
        self.assertFalse(result.source_ledger["all_effectiveness_properties_joined"])
        self.assertFalse(result.full_person_ready)
        self.assertFalse(result.full_entry_ready)

        # Existing packets genuinely lack this new leaf. They keep the original
        # per-Ci numerical consumer usable rather than gaining a readiness gate.
        legacy_event = deepcopy(event)
        for row in legacy_event["contexts"]:
            row.pop("preparation_stage_lineage")
        legacy_original = deepcopy(legacy_event)
        legacy = join_owned_person_postimage_to_knight_stage_12004(postimage, owner, legacy_event)
        self.assertEqual(legacy.historical_property_keys, ())
        self.assertEqual(legacy.unmatched_property_keys, KEYS)
        self.assertEqual(legacy.inputs.effectiveness.context.aggregate_properties,
                         stage.context.aggregate_properties)
        self.assertEqual(legacy.inputs.effectiveness.operand_raw, OPERANDS)
        self.assertEqual(legacy.inputs.effectiveness.stage, "native_wrapper_consumed_per_ci_contexts")
        self.assertEqual(legacy_event, legacy_original)
        print(json.dumps({
            "status": "GREEN", "new_adapter_validation_methods": 1,
            "conditional_historical_properties_joined": 8,
            "unmatched_distinct_context_properties_retained": 1,
            "legacy_absent_lineage_original_inputs_retained": True,
            "original_operands_unchanged": True,
            "lineage_inputs": "explicit_synthetic_source_case",
            "composer_invocations": 0, "stat_arithmetic_invocations": 0,
            "native_FIRST_invocations": 0, "old_MCP_consumer_invocations": 0,
            "game_sdk_calls": 0, "full_person_ready": False,
            "full_entry_ready": False, "new_g2_credit": 0,
        }))


if __name__ == "__main__":
    unittest.main()
