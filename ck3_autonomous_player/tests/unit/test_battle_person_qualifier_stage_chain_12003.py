"""One new normalized qualifier repeat stream -> stage -> six-skill case."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_provider_stage_chain_12003 import provider_frame
from test_battle_person_tail_stage_chain_12003 import pc, Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def qualifier():
    a, b = 0x1000, 0x2000
    a_evaluations, b_evaluations = [], []
    for index, (a_id, b_id) in enumerate(zip((0xAB000001, 0xCD000001, 0xAB000001),
                                            (5, 5, 0xFFFFFFFF))):
        a_evaluations.append({"native_index": index, "object": 0x7000 + index * 0x100,
            "candidate_count_raw_i32": 1, "candidate_array_present": True,
            "candidates": [{"native_index": 0, "definition_object": a,
                "relationship_count_raw_i32": None, "relationship_array_present": None,
                "relationships": None}], "id_u32": a_id})
        b_evaluations.append({"native_index": index, "object": 0x7000 + index * 0x100,
            "candidate_count_raw_i32": 1, "candidate_array_present": True,
            "candidates": [{"native_index": 0, "definition_object": a,
                "relationship_count_raw_i32": 1, "relationship_array_present": True,
                "relationships": [{"native_index": 0, "marker_u8": 7,
                                    "definition_object": None}]}], "id_u32": b_id})
    definitions = []
    for index, pointer, evaluations, ids, value in (
            (0, a, a_evaluations, [0xAB000001, 0xCD000001], 2 * Q),
            (1, b, b_evaluations, [5], -Q),
            (2, a, deepcopy(a_evaluations), [0xAB000001, 0xCD000001], 2 * Q)):
        definitions.append({"native_index": index, "definition_object": pointer, "ready": True,
            "scratch_evaluations": evaluations, "accepted_ids_u32": ids, "repeat_count": len(ids),
            "properties": pc(value), "reason": None})
    return {"status": "available", "ready": True, "character_id": ACTOR,
        "manager_object": 0x5000, "definition_count_raw_i32": 3, "definition_array_present": True,
        "scratch_present": True, "scratch_count_raw_i32": 3,
        "fallback_definition_object": b, "definitions": definitions, "reason": None}


class PersonQualifierStageChain12003Tests(unittest.TestCase):
    def test_repeated_units_preserve_manager_order_and_partial_definition_frontier(self):
        raw = provider_frame()
        raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["qualifier_28bc0d0"] = qualifier()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="qualifier_repeated_contribution")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "postQualifierContribution_pre291C6CF")
        self.assertEqual(result.context.aggregate_properties.values_q64, (41 * Q,))
        self.assertEqual(result.context.weighted_count, 20)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 47))
        self.assertEqual(result.source_ledger["first_contiguous_observation_dependency"], "291FB10")
        requests = result.independent_stage_outputs["qualifier_repeated_contribution"]
        self.assertEqual([row.source_ordinal for row in requests], [0, 1, 2, 3, 4])
        self.assertEqual([row.first_row_index for row in requests], [0, 0, 1, 2, 2])
        self.assertEqual([row.definition_identity for row in requests], [0x1000, 0x1000, 0x2000, 0x1000, 0x1000])
        self.assertEqual([row.weight_q64 for row in requests], [Q] * 5)
        self.assertEqual([row.row_count for row in requests], [1] * 5)
        normalized = person["current_context_source_inputs"]["qualifier_28bc0d0"]
        self.assertEqual(normalized["definitions"][0]["accepted_ids_u32"], [0xAB000001, 0xCD000001])
        for request in requests:
            self.assertIs(request.base_property_block,
                          normalized["definitions"][request.first_row_index]["properties"])

        partial_raw = deepcopy(raw)
        partial_leaf = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["qualifier_28bc0d0"]
        partial_leaf.update(status="partial", ready=False, reason="definition1_PC_unavailable")
        partial_leaf["definitions"][1].update(ready=False, properties=None,
                                               reason="definition1_PC_unavailable")
        _, partial, partial_skills = evaluate(partial_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "postQualifierDefinition0_pre291C655")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (38 * Q,))
        self.assertEqual(partial.context.weighted_count, 17)
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 44))
        self.assertEqual(len(partial.independent_stage_outputs["qualifier_repeated_contribution"]), 2)
        self.assertEqual(len(partial.independent_stage_outputs["qualifier_repeated_contribution.2"]), 2)
        self.assertEqual(len(partial.independent_stage_outputs["carrier_weighted630"]), 3)
        ledger = next(row for row in partial.source_ledger["ordered_tail_stages"]
                      if row["stage"] == "qualifier_repeated_contribution")
        self.assertEqual([row["in_contiguous_definition_prefix"] for row in ledger["qualifier_definition_stages"]],
                         [True, False, False])
        self.assertTrue(any("qualifier_repeated_contribution" in gap for gap in partial.missing_inputs))
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["all_tail_source_stream_ready"])
        self.assertTrue(result.source_ledger["conditional_on_observed_source_values"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            repeated_unit_request_indices=[row.first_row_index for row in requests],
            full_dword_generation_ids=normalized["definitions"][0]["accepted_ids_u32"],
            duplicate_manager_definition_preserved=True, partial_stage=partial.stage,
            partial_skills=partial_skills.final_cache_points, later_definition_independently_ready=True,
            next_source_stage="291FB10", conditional_on_observed_source_values=True,
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
