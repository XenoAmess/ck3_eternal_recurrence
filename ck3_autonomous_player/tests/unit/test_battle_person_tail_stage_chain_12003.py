"""One new actual tail normalizer -> bounded continuation -> skill case."""
from copy import deepcopy
from dataclasses import replace
import unittest

from test_battle_person_stage_baseline_12003 import frame, normalize
from test_battle_person_tail_direct_12003 import source as direct_source
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

Q, ACTOR = 100000, 29829
OBSERVATIONS = {}


def pc(value):
    return {"keys_count": 1, "values_count": 1, "keys_u16": [5],
            "values_q64": [value], "reason": None}


def source():
    result = direct_source()
    direct = result["tail_direct_291c5b7_291cc49"]
    government = direct["government_870_a30"]
    government["property_870"] = pc(Q)
    government["property_a30"] = pc(2 * Q)
    weighted = direct["carrier_weighted630"]["rows"]
    for row, weight in zip(weighted, (0, -Q, 2 * Q)):
        row.update(property_block=pc(4 * Q), weight_q64=weight)
    helper = {
        "status": "available", "ready": True, "reason": None,
        "first_key_158_raw": ACTOR, "land_field_1f8_raw": 0, "owner_key_1e0_raw": ACTOR,
        "owner_id_160_raw": ACTOR, "character_id_18_raw": ACTOR,
        "initial_relation_key_c8_raw": None, "last_character_id_18_raw": None,
        "caller_gate_218_raw": 1, "caller_gate_218_recheck_raw": 1, "government_mode_80c_raw": 2,
        "first_selection": "registry_full_id_10", "first_identity": "first",
        "definition_identity": "definition275", "definition_pointer_260_identity": "pointer:equal",
        "government_selection": "character_land_1c0_3f8", "government_identity": "government",
        "predicate_pointer_selection": "government_800", "predicate_pointer_identity": "pointer:equal",
        "owner_selection": "registry_full_id_10", "owner_identity": "owner",
        "initial_relation_selection": None, "initial_relation_identity": None,
        "property_identity": "275pc", "caller_admitted": True, "character_land_present": True,
        "predicate_admitted": True, "owner_admitted": True, "relation_rows": None,
        "property_block": pc(3 * Q),
    }
    later = {"status": "unavailable", "ready": False, "first_key_158_raw": None,
        "first_selection": None, "first_identity": None, "definition_identity": None,
        "definition_magic_38_raw": None, "admitted": None, "type_280_raw": None,
        "owner_id_160_raw": None, "character_id_18_raw": None, "rows": None,
        "reason": "helper_2922530_inputs_unobserved"}
    result["tail_prefix_2753860_2922530"] = {
        "status": "partial", "ready": False, "character_id": ACTOR,
        "helper_2753860": helper, "helper_2922530": later,
        "reason": "later_2922530_inputs_unobserved",
    }
    return result


class PersonTailStageChain12003Tests(unittest.TestCase):
    def test_real_275_stage_advances_without_crossing_missing_2922070(self):
        raw = frame()
        state = raw["character_observations"][0]["current_person_state"]
        state["current_context_source_inputs"] = source()
        original = deepcopy(raw)
        person = normalize(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})
        continued = continue_current_person_stage_chain_tail_12003(person, prior, character_full_id=ACTOR)
        self.assertTrue(continued.ready, continued.missing_inputs)
        self.assertEqual(continued.stage, "post2753860_pre291C4D2")
        self.assertEqual(continued.context.aggregate_properties.values_q64, (5 * Q,))
        self.assertEqual(continued.context.weighted_count, 1)
        self.assertFalse(continued.source_ledger["all_tail_source_stream_ready"])
        self.assertFalse(continued.full_person_preparation_ready)
        self.assertFalse(continued.full_entry_ready)
        self.assertFalse(person["current_context_source_inputs"]["tail_prefix_2753860_2922530"]["ready"])
        self.assertEqual(len(continued.independent_stage_outputs["government_870_a30"]), 2)
        weights = [row.weight_q64 for row in continued.independent_stage_outputs["carrier_weighted630"]]
        self.assertEqual(weights, [0, -Q, 2 * Q])
        self.assertEqual([row.definition_identity for row in continued.independent_stage_outputs["carrier_weighted630"][:2]],
                         ["weighted:duplicate", "weighted:duplicate"])
        self.assertTrue(any("2922070" in gap for gap in continued.source_ledger["future_tail_missing_inputs"]))
        numeric = from_raw_numeric_inputs_12003(person["raw_numeric_inputs"])
        projected = project_stage_chain_six_skills_12003(continued, numeric)
        self.assertTrue(projected.calculation_ready, projected.missing_inputs)
        self.assertEqual(projected.final_cache_points, (6, 6, 6, 6, 6, 11))

        extended = continue_current_person_stage_chain_tail_12003(person, prior,
            character_full_id=ACTOR, through_stage="2922530")
        self.assertFalse(extended.ready)
        self.assertEqual(extended.stage, continued.stage)
        self.assertEqual(extended.context, continued.context)
        self.assertTrue(any("2922070" in gap for gap in extended.missing_inputs))
        self.assertEqual(len(extended.independent_stage_outputs["government_870_a30"]), 2)

        earlier = replace(prior, ready=False, stage="post291E210_pre291C28D",
            missing_inputs=("291D460:actual_input_missing",), stage_contexts={"post291E210_pre291C28D": explicit})
        blocked = continue_current_person_stage_chain_tail_12003(person, earlier, character_full_id=ACTOR)
        self.assertFalse(blocked.ready)
        self.assertEqual(blocked.stage, earlier.stage)
        self.assertEqual(blocked.context, explicit)
        self.assertEqual(len(blocked.independent_stage_outputs["2753860"]), 1)
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=continued.stage, ready_skills=projected.final_cache_points,
            extended_stage=extended.stage, extended_ready=extended.ready,
            earlier_gap_stage=blocked.stage, independent_stored_weights=weights,
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
