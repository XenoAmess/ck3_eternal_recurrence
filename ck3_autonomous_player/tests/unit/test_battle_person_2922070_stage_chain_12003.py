"""One new actual2922070 normalizer -> ordered tail -> skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import frame, normalize
from test_battle_person_tail_stage_chain_12003 import source, pc, Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}
FULL_ID = -2147483639


def helper_2922070():
    # Singleton lists require no comparator operand; the full generation bits
    # survive membership and source mapping instead of becoming an array index.
    return {
        "status": "available", "ready": True, "gate_ready": True,
        "collection_ready": True, "rows_ready": True, "character_id": ACTOR,
        "government_selection": "character_land_1c0_3f8", "government_identity": "government5",
        "government_mode_4d6_raw": 5, "character_land_present": True,
        "subject_identity": "subject", "subject_magic_c_raw": 0, "subject_id_8_raw": None,
        "admitted": True, "reason": None,
        "walk_nodes": [{"native_index": 0, "character_identity": "self",
            "header_selection": "character_land_218", "count_c_raw": 0,
            "array_present": False, "edges": [], "reason": None}],
        "characters": [{"native_index": 0, "include_self": True, "input_id_raw": None,
            "character_id_18_raw": None, "first_key_158_raw": None, "owner_id_160_raw": None,
            "selection": None, "character_identity": "self",
            "first_selection": None, "first_identity": None, "owner_selection": None,
            "owner_identity": None, "government_selection": None, "government_identity": None,
            "top_character_identity": None, "top_government_selection": None,
            "top_government_identity": None, "government_mask_40_raw": None,
            "top_government_mask_40_raw": None, "admitted": True, "reason": None}],
        "character_order": [0],
        "membership_rows": [{"native_index": 0, "character_index": 0,
            "first_key_158_raw": FULL_ID, "first_id_10_raw": FULL_ID,
            "first_selection": "registry_full_id_10", "first_identity": "first:full-generation",
            "header_selection": "character_land_1e0", "count_c_raw": 1,
            "array_present": True, "admitted": True, "appended": True, "reason": None,
            "scans": [{"native_index": 0, "requested_id_raw": FULL_ID,
                "selection": "registry_full_id_10", "object_identity": "membership:full-generation",
                "gate_32_raw": 1, "reason": None}]}],
        "output_ids": [FULL_ID],
        "rows": [{"native_index": 0, "input_index": 0, "requested_id_raw": FULL_ID,
            "selected_id_10_raw": None, "selection": "registry_full_id_10",
            "source_identity": "source:full-generation", "type_280_raw": 2,
            "definition_identity": "definition:BA0", "definition_magic_38_raw": 0x4744624F,
            "count_214_raw": 2, "requested_index_228_raw": 4, "selected_index_raw": 1,
            "table_identity": "actual-inline-table208", "property_identity": "actual-BA0-index1",
            "property_block": pc(7 * Q), "admitted": True, "reason": None}],
    }


def ready_source():
    section = source()
    prefix = section["tail_prefix_2753860_2922530"]
    prefix.update(status="available", ready=True, reason=None)
    empty = {"keys_count": 0, "values_count": 0, "keys_u16": [], "values_q64": [], "reason": None}
    prefix["helper_2922530"] = {
        "status": "available", "ready": True, "first_key_158_raw": ACTOR,
        "first_selection": "registry_full_id_10", "first_identity": "first2530",
        "definition_identity": "definition2530", "definition_magic_38_raw": 0x4744624F,
        "admitted": True, "type_280_raw": 2, "owner_id_160_raw": ACTOR,
        "character_id_18_raw": ACTOR, "reason": None,
        "rows": [{"native_index": i, "admitted": True, "definition_identity": "definition2530",
            "count_214_raw": count, "requested_index_228_raw": requested, "selected_index_raw": selected,
            "table_identity": "table2530", "property_identity": "2530:" + str(i),
            "property_block": block, "reason": None}
            for i, (count, requested, selected, block) in enumerate((
                (0, 0, -1, empty), (1, -1, 0, pc(2 * Q)), (1, 3, 0, pc(-Q))))],
    }
    section["helper_2922070"] = helper_2922070()
    return section


class Person2922070StageChain12003Tests(unittest.TestCase):
    def test_real_2922070_releases_contiguous_2530_and_preserves_missing_row_frontier(self):
        raw = frame()
        raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"] = ready_source()
        original = deepcopy(raw)
        person = normalize(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})
        result = continue_current_person_stage_chain_tail_12003(person, prior,
            character_full_id=ACTOR, through_stage="2922530")
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "post2922530_pre291C4E2")
        self.assertEqual(result.context.aggregate_properties.values_q64, (13 * Q,))
        self.assertEqual(result.context.weighted_count, 4)
        self.assertEqual([row["stage"] for row in result.source_ledger["ordered_tail_stages"]
                          if row["folded_into_contiguous_context"]], ["2753860", "2922070", "2922530"])
        self.assertEqual(result.source_ledger["first_contiguous_observation_dependency"], "conference24B1D00")
        helper = person["current_context_source_inputs"]["helper_2922070"]
        self.assertTrue(helper["ready"])
        self.assertEqual(helper["output_ids"], [FULL_ID])
        self.assertIsNone(helper["rows"][0]["selected_id_10_raw"])
        emitted = result.independent_stage_outputs["2922070"]
        self.assertEqual((emitted[0].source_name, emitted[0].weight_q64), ("2922070_ba0", Q))
        self.assertIs(emitted[0].base_property_block, helper["rows"][0]["property_block"])
        self.assertEqual(len(result.independent_stage_outputs["2922530"]), 3)
        self.assertEqual(result.independent_stage_outputs["2922530"][0].base_property_block["keys_count"], 0)
        numeric = from_raw_numeric_inputs_12003(person["raw_numeric_inputs"])
        projected = project_stage_chain_six_skills_12003(result, numeric)
        self.assertTrue(projected.calculation_ready, projected.missing_inputs)
        self.assertEqual(projected.final_cache_points, (6, 6, 6, 6, 6, 19))

        partial_raw = deepcopy(raw)
        partial = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["helper_2922070"]
        partial.update(status="partial", ready=False, rows_ready=False, reason="demanded_BA0_unavailable")
        partial["rows"][0].update(property_block=None, reason="demanded_BA0_unavailable")
        partial_person = normalize(partial_raw)
        blocked = continue_current_person_stage_chain_tail_12003(partial_person, prior,
            character_full_id=ACTOR, through_stage="2922530")
        self.assertFalse(blocked.ready)
        self.assertEqual(blocked.stage, "post2753860_pre291C4D2")
        self.assertEqual(blocked.context.aggregate_properties.values_q64, (5 * Q,))
        self.assertTrue(any("helper_2922070" in gap for gap in blocked.missing_inputs))
        self.assertEqual(blocked.source_ledger["first_contiguous_observation_dependency"], "2922070")
        self.assertEqual(len(blocked.independent_stage_outputs["2922530"]), 3)
        blocked_numeric = from_raw_numeric_inputs_12003(partial_person["raw_numeric_inputs"])
        blocked_skills = project_stage_chain_six_skills_12003(blocked, blocked_numeric)
        self.assertTrue(blocked_skills.calculation_ready)
        self.assertEqual(blocked_skills.final_cache_points, (6, 6, 6, 6, 6, 11))
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["all_tail_source_stream_ready"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=projected.final_cache_points,
            partial_stage=blocked.stage, partial_skills=blocked_skills.final_cache_points,
            output_full_id=helper["output_ids"][0], admitted_empty_2530_request_preserved=True,
            next_source_stage=result.source_ledger["first_contiguous_observation_dependency"],
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
