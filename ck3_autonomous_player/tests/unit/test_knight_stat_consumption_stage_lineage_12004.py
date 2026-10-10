"""One new same-Ci wire -> strict normalizer -> production consumer case.

The source case is synthetic. The retained Native66/continuation14 operand and
two-PC vector is input data, not a replay of its producer or numerical matrix.
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.bridge.knight_stat_consumption_contract_12004 import (
    normalize_knight_stat_consumption_12004,
)
from xar_autoplayer.simulation.knight_stat_consumption_12004 import (
    project_knight_stat_consumption_12004,
)
from xar_autoplayer.simulation.battle_person_six_stage_postimage_12004 import (
    compose_captured_six_stage_postimage_12004,
)
from xar_autoplayer.simulation.battle_entry_person_stage_join_12004 import (
    join_owned_person_postimage_to_knight_stage_12004,
)


KEYS = list(range(0xC1, 0xCA))
RETURNS = (0x2C06B03, 0x2C06B51, 0x2C06B8D, 0x2C06BC4, 0x2C06BFB,
           0x2C06C32, 0x2C06C69, 0x2C06CA0, 0x2C06CD7)
OPERANDS = (100000, 0, 0, -200000, -300000, 0, 400000, -500000, 600000)
VALUES = (-25000, 0, 0, -10000, 0, 0, 0, 0, 0)
SELECTED, LINKED = 0x04000002, 0x03000001
CONTEXT, OTHER_CONTEXT, MODEL, OWNER, THREAD = 0x22345010, 0x32345010, 0x22345000, 0x12345000, 4242


def _pc(identity, values, *, aggregate=False):
    return {
        "ready": True, "reason": None, "admitted": True,
        "identity": hex(identity), "count_i32": len(KEYS),
        "properties": {"keys_u16": KEYS.copy(), "values_q64": [str(value) for value in values]},
        "weight_q100000": None if aggregate else "0",
    }


def _owned_capture():
    skip = {"ready": True, "reason": None, "admitted": False, "identity": None,
            "count_i32": None, "properties": None, "weight_q100000": None}
    return {
        "schema": "xar.ck3.person-native-six-stage-capture-12004-v1",
        "build_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
        "configured": True, "capture_observed": True, "capture_complete": True,
        "ready": True, "raw_counts_ready": True, "reason": None, "capture_sequence": 1,
        "capture_date_raw": 53236632, "capture_thread_id": THREAD, "query_thread_id": THREAD,
        "character_id": SELECTED, "character_identity": hex(OWNER),
        "context_identity": hex(CONTEXT), "source_return_rva": "0x291cea9",
        "source_stage": "ordered_six_attribute_native_calls", "historical_capture": True,
        "actual_model_write_performed": False, "full_helper_ready": False,
        "stages": [{"index": i, "observed": True, "raw_count_i32": 0,
                    "first_append_observed": False, "second_append_observed": False,
                    "first_pc": deepcopy(skip), "second_pc": deepcopy(skip)} for i in range(6)],
        "pre_six_aggregate": {
            "observed": True, "source_stage": "before_first_count_callback", "context_pc_offset": 0x68,
            "pc": _pc(CONTEXT + 0x68, VALUES, aggregate=True)},
        "post_six_aggregate": {
            "observed": True, "source_stage": "same_thread_capture_completion", "context_pc_offset": 0x68,
            "pc": _pc(CONTEXT + 0x68, VALUES, aggregate=True)},
        "aggregate_postimage_inputs_ready": True, "aggregate_postimage_comparison_ready": True,
        "preparation_model": {
            "observed": True, "ready": True, "reason": None, "model_identity": hex(MODEL),
            "owner_character_identity": hex(OWNER), "owner_character_id": SELECTED,
            "owner_matches_capture": True, "context_offset": 0x10, "owner_offset": 8,
            "source_stage": "before_first_count_callback"},
    }


def _wire():
    contexts = []
    for i, key in enumerate(KEYS):
        matching = key != 0xC5
        context = CONTEXT if matching else OTHER_CONTEXT
        values = list(VALUES)
        if not matching:
            values[4] = 15000
        contexts.append({
            "property_key": key, "caller_return_rva": str(RETURNS[i]),
            "selected_character_id": SELECTED, "selected_character_identity": hex(OWNER),
            "context_identity": hex(context), "operand_raw": str(OPERANDS[i]),
            "consumed_pc": _pc(context + 0x68, values),
            "preparation_capture_sequence": "1", "preparation_model_identity": hex(MODEL),
            "preparation_context_identity": hex(CONTEXT), "preparation_owner_character_id": SELECTED,
            "context_matches_preparation": matching, "owner_matches_preparation": True,
            "pc_matches_preparation_post": matching, "reason": None,
            "preparation_stage_lineage": {
                "schema": "xar.ck3.entry-selected-receiver-stage-12004-v1",
                "property_key": key, "consumed_return_rva": str(RETURNS[i]),
                "exact_consumed_callsite": True, "exact_capture_build": True,
                "observation_stage": "actual_effectiveness_context_return",
                "preparation_stage": "paused_same_thread_six_stage_completion",
                "linked_character_id": LINKED, "linked_character_identity": "0x13345000",
                "selected_character_id": SELECTED, "selected_character_identity": hex(OWNER),
                "getter_context_identity": hex(context), "preparation_capture_observed": True,
                "preparation_capture_complete": True, "preparation_raw_counts_ready": True,
                "preparation_stage_observed_mask": 0x3F, "preparation_capture_sequence": "1",
                "preparation_source_return_rva": str(0x291CEA9),
                "preparation_capture_thread_id": THREAD, "preparation_completion_thread_id": THREAD,
                "consumption_thread_id": THREAD, "preparation_character_identity": hex(OWNER),
                "preparation_model_identity": hex(MODEL), "preparation_context_identity": hex(CONTEXT),
                "preparation_owner_character_identity": hex(OWNER), "preparation_owner_character_id": SELECTED,
                "capture_sequence_matches_record": True, "exact_preparation_source_return": True,
                "selected_matches_capture_identity": True, "selected_matches_capture_id": True,
                "selected_matches_model_owner_identity": True, "selected_matches_model_owner_id": True,
                "getter_matches_capture_context": matching, "getter_matches_preparation_model_inline": matching,
                "completion_on_consumption_thread": True, "completed_post_pc_matches_consumed": matching,
                "completed_preparation_lineage_proven": matching,
                "reason": None if matching else "consumed_preparation_receiver_unmatched_or_missing",
            },
            "preparation_capture_at_consumption": _owned_capture(),
        })
    return {
        "schema": "xar.ck3.knight-stat-consumption-12004-v1",
        "build_version": CK3_12004.game_version, "executable_sha256": CK3_12004.executable_sha256,
        "configured": True, "observer_installed": False, "oldest_available_sequence": "1",
        "latest_sequence": "1", "overwritten_events": "0", "reason": None,
        "events": [{
            "sequence": "1", "thread_id": THREAD, "observed_date_raw": 53236632,
            "wrapper_caller_return_rva": str(0x2634509), "origin": "bridge_query_scratch",
            "regiment_id": 0x06000004, "target_province_id": 101,
            "linked_character_id": LINKED, "linked_character_identity": "0x13345000",
            "linked_prowess_points": 3, "loaded_damage_multiplier": 100,
            "loaded_toughness_multiplier": 10, "output_cache_identity": "0x42345000",
            "native_return_identity": "0x42345000", "contexts": contexts,
            "observed_output": {"ready": False, "max_size": None, "reason": "synthetic_output_unobserved",
                "siege_value_raw": None, "damage_raw": None, "toughness_raw": None,
                "pursuit_raw": None, "screen_raw": None},
            "entry_association_proven": False, "capture_reason": None,
        }],
    }


class KnightStageLineageProduction12004Tests(unittest.TestCase):
    def test_same_ci_owned_wire_reaches_actual_per_ci_consumer(self):
        wire = _wire()
        original = deepcopy(wire)
        normalized = normalize_knight_stat_consumption_12004(wire)
        rows = normalized["events"][0]["contexts"]
        self.assertEqual(rows[0]["preparation_stage_lineage"]["preparation_capture_sequence"], 1)
        self.assertEqual(rows[0]["preparation_stage_lineage"]["getter_context_identity"], CONTEXT)
        with patch("xar_autoplayer.simulation.battle_person_six_stage_postimage_12004.compose_captured_six_stage_postimage_12004",
                   wraps=compose_captured_six_stage_postimage_12004) as composer, patch(
                "xar_autoplayer.simulation.battle_entry_person_stage_join_12004.join_owned_person_postimage_to_knight_stage_12004",
                wraps=join_owned_person_postimage_to_knight_stage_12004) as adapter:
            projection = project_knight_stat_consumption_12004(wire)["events"][0]
            self.assertEqual(composer.call_count, 1)
            self.assertEqual(adapter.call_count, 1)
        joined = tuple(key for key in KEYS if key != 0xC5)
        self.assertEqual(projection["preparation_stage_join"]["historical_property_keys"], joined)
        self.assertEqual(projection["preparation_stage_join"]["unmatched_property_keys"], (0xC5,))
        self.assertEqual(projection["source_stage"], "actual4_consumed_ci_with_owned_six_stage_postimage")
        self.assertEqual(projection["operand_raw"], OPERANDS)
        self.assertEqual(projection["property_inputs"][0]["branch"], "owned_historical_postimage_selected_at_consumed_ci")
        self.assertEqual(projection["property_inputs"][4]["branch"], "actual_consumed_pc_mode0")
        self.assertEqual(projection["property_inputs"][4]["context_identity"], OTHER_CONTEXT)
        self.assertEqual(projection["property_inputs"][4]["lookups"][0]["value_q64"], 15000)
        self.assertFalse(projection["preparation_stage_join"]["later_current_query_used"])
        for claim in ("entry_association_proven", "historical_stage_equivalence_proven",
                      "actual_model_write_performed", "full_person_ready", "full_entry_ready"):
            self.assertFalse(projection[claim])
        self.assertEqual(wire, original)

        # The old producer omitted both new fields. Absence is retained through
        # normalization and the existing numerical path remains the consumer.
        legacy = deepcopy(wire)
        for row in legacy["events"][0]["contexts"]:
            row.pop("preparation_stage_lineage")
            row.pop("preparation_capture_at_consumption")
        legacy_normalized = normalize_knight_stat_consumption_12004(legacy)
        self.assertTrue(all("preparation_stage_lineage" not in row and
                            "preparation_capture_at_consumption" not in row
                            for row in legacy_normalized["events"][0]["contexts"]))
        old = project_knight_stat_consumption_12004(legacy)["events"][0]
        self.assertNotIn("preparation_stage_join", old)
        self.assertEqual(old["operand_raw"], projection["operand_raw"])
        self.assertEqual(old["modifier_raw"], projection["modifier_raw"])
        self.assertEqual(old["source_stage"], "native_wrapper_consumed_per_ci_contexts")

        # These new wire facts must agree with the exact retained source, rather
        # than a role-wide prepared classification or an unrelated completion.
        wrong_thread = deepcopy(wire)
        wrong_thread["events"][0]["contexts"][0]["preparation_stage_lineage"]["consumption_thread_id"] += 1
        with self.assertRaisesRegex(ValueError, "receiver or thread"):
            normalize_knight_stat_consumption_12004(wrong_thread)
        wrong_pc = deepcopy(wire)
        wrong_pc["events"][0]["contexts"][0]["preparation_capture_at_consumption"]["post_six_aggregate"]["pc"]["properties"]["values_q64"][0] = "999"
        with self.assertRaisesRegex(ValueError, "exact owned post PC"):
            normalize_knight_stat_consumption_12004(wrong_pc)


if __name__ == "__main__":
    unittest.main()
