"""One new actual FB10 -> ordered predicate list -> six-skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_provider_stage_chain_12003 import provider_frame
from test_battle_person_qualifier_stage_chain_12003 import qualifier
from test_battle_person_tail_stage_chain_12003 import pc, Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def ready_fb10():
    preferred = {"status": "available", "ready": True, "native_index": 0,
        "requested_full_id_raw": None, "full_id_raw": 77, "owner_full_id_raw": ACTOR,
        "character_full_id_raw": ACTOR, "modifier_count": 0, "selection": "land_1c0",
        "context_identity": "actual-preferred-subc", "terminal_property_identity": "actual-terminal-PC",
        "admitted": True, "owner_matches": True, "modifier_array_present": None,
        "token_array_present": None, "magic_raw": 0x5362436F, "modifier_rows": [],
        "terminal_property_block": pc(Q), "reason": None}
    helper = {"status": "available", "ready": True, "land_present": True, "reason": None,
        "preferred": {"status": "available", "ready": True, "header_selection": "land_1c0",
            "count": 1, "array_present": None, "rows": [preferred], "reason": None}}
    for name in ("list_218", "list_248"):
        helper[name] = {"status": "available", "ready": True, "header_selection": "character_" + name,
            "count": 0, "array_present": False, "rows": [], "reason": None}
    return helper


def list_source():
    rows = []
    for index, key, value in ((0, 0xAB000001, 2 * Q), (1, 0xFFFFFFFF, None),
                              (2, 0xAB000001, 2 * Q), (3, 0xCD000001, -Q), (4, 0, 0)):
        sentinel = key == 0xFFFFFFFF
        magic = None if sentinel else 0 if index == 0 else 0x4744624F
        rows.append({"native_index": index, "key_u32": key, "ready": True,
            "resolution_selection": None if sentinel else "registry_full_id",
            "selected_object": None if sentinel else 0x9000 if key == 0xAB000001 else 0xA000 + index * 0x100,
            "selected_full_id_u32": None if sentinel else key, "used_fallback": None if sentinel else False,
            "predicate_receiver": None if sentinel else 0xD000 + index * 0x100,
            "magic_u32": magic, "condition_count_raw_i32": None if sentinel or index == 0 else 0,
            "predicate_result": None if sentinel else True, "pc_selection": None if sentinel else "selected_d8",
            "scope_inputs": None, "properties": None if sentinel else pc(value), "reason": None})
    return {"status": "available", "ready": True, "character_id": ACTOR,
        "scratch_present": True, "header_selection": "held_scratch_458", "default_header_guard_raw": 0,
        "source_array_present": True, "source_count_raw": 5, "rows": rows, "reason": None}


class PersonListStageChain12003Tests(unittest.TestCase):
    def test_actual_fb10_and_list_occurrences_preserve_scripted_row_frontier(self):
        raw = provider_frame()
        section = raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]
        section["qualifier_28bc0d0"] = qualifier()
        middle = section["middle_helpers_291f260_291fb10"]
        middle.update(status="available", ready=True, reason=None, helper_291fb10=ready_fb10())
        section["list_predicate_2530dd0"] = list_source()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="list2530DD0")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "postList2530DD0_pre291C7A7")
        self.assertEqual(result.context.aggregate_properties.values_q64, (45 * Q,))
        self.assertEqual(result.context.weighted_count, 25)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 51))
        self.assertEqual(len(result.independent_stage_outputs["291FB10"]), 1)
        requests = result.independent_stage_outputs["list2530DD0"]
        self.assertEqual([row.first_row_index for row in requests], [0, 2, 3, 4])
        self.assertEqual([row.source_ordinal for row in requests], [0, 1, 2, 3])
        self.assertEqual([row.definition_identity for row in requests[:2]], [0x9000, 0x9000])
        self.assertEqual([row.weight_q64 for row in requests], [Q] * 4)
        self.assertEqual(len(result.independent_stage_outputs["list2530DD0.1"]), 0)
        self.assertEqual(len(result.independent_stage_outputs["list2530DD0.4"]), 1)
        normalized = person["current_context_source_inputs"]["list_predicate_2530dd0"]
        self.assertEqual(normalized["default_header_guard_raw"], 0)
        self.assertTrue(normalized["ready"])
        for request in requests:
            self.assertIs(request.base_property_block, normalized["rows"][request.first_row_index]["properties"])

        partial_raw = deepcopy(raw)
        partial_leaf = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["list_predicate_2530dd0"]
        partial_leaf.update(status="partial", ready=False, reason="nonempty_scoped_trigger_evaluation")
        row = partial_leaf["rows"][2]
        row.update(ready=False, condition_count_raw_i32=-7, predicate_result=None,
            pc_selection=None, properties=None, reason="nonempty_scoped_trigger_evaluation",
            scope_inputs={"root_scope_kind_u32": 4, "root_character_full_id_u32": ACTOR,
                "named_scope_kind_u32": 31, "named_selected_full_id_u32": 0xAB000001,
                "named_binding_key_i32": -17, "trigger_object": row["predicate_receiver"] + 0x110,
                "trigger_vtable": 0x140055550, "trigger_evaluator_function": 0x140099990})
        partial_person, partial, partial_skills = evaluate(partial_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "postList2530DD0Row1_preRow2")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (44 * Q,))
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 50))
        self.assertEqual(len(partial.independent_stage_outputs["list2530DD0"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs["list2530DD0.3"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs["list2530DD0.4"]), 1)
        scope = partial_person["current_context_source_inputs"]["list_predicate_2530dd0"]["rows"][2]["scope_inputs"]
        self.assertEqual((scope["root_character_full_id_u32"], scope["named_selected_full_id_u32"]),
                         (ACTOR, 0xAB000001))
        self.assertEqual(scope["trigger_evaluator_function"], 0x140099990)
        self.assertTrue(any("list2530DD0" in gap for gap in partial.missing_inputs))
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["all_tail_source_stream_ready"])
        self.assertTrue(result.source_ledger["conditional_on_observed_source_values"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            original_request_row_indices=[request.first_row_index for request in requests],
            duplicate_id_occurrences_preserved=True, zero_id_is_a_real_request=True,
            unused_default_guard_zero_does_not_remove_held_source=True,
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            independent_later_rows_preserved=True, nonzero_scripted_predicate_not_guessed=True,
            distinct_root_named_scope_ids_preserved=True,
            next_source_stage="intervening_lists_flags_temp_helpers_thresholds",
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
