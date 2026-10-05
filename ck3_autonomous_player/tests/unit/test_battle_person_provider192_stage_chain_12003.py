"""One genuine provider/list source chain -> signed tail weights -> six skills."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_after_gated_stage_chain_12003 import after_gated_frame
from test_battle_person_provider192_and2920850_12003 import (
    FIELD, FAMILIES, provider192_and2920850_source, availability,
)
from test_battle_person_tail_stage_chain_12003 import Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def provider192_frame():
    raw = after_gated_frame()
    leaf = provider192_and2920850_source()[FIELD]
    leaf["rite"]["first_key_b4_raw"] = 7

    def use_prowess_key(value):
        if isinstance(value, dict):
            if "keys_u16" in value:
                value["keys_u16"] = [5 if key != 65535 else key for key in value["keys_u16"]]
            for item in value.values():
                use_prowess_key(item)
        elif isinstance(value, list):
            for item in value:
                use_prowess_key(item)

    use_prowess_key(leaf)
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD] = leaf
    return raw


class PersonProvider192StageChain12003Tests(unittest.TestCase):
    def test_ordered_slots_descriptor_prefix_signed_weights_and_skills_join_production(self):
        raw = provider192_frame()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="carrier_weighted630")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "postCarrierWeighted630_pre291CC71")
        self.assertEqual(result.context.aggregate_properties.values_q64, (9007450,))
        self.assertEqual(result.context.weighted_count, 65)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 96))
        requests = result.independent_stage_outputs[FIELD]
        self.assertEqual(len(requests), 25)
        self.assertEqual([row.source_ordinal for row in requests], [0] + [1] * 20 + [2] * 4)
        self.assertEqual([row.base_property_block["values_q64"] for row in requests[1:11]],
                         [[101], [102], [103], [104], [501], [501], [501], [502], [503], [504]])
        self.assertEqual([row.first_row_index for row in requests[1:21]], [0] * 10 + [1] * 10)
        self.assertEqual(requests[-1].base_property_block["keys_count"], 0)
        normalized = person["current_context_source_inputs"][FIELD]
        self.assertEqual(normalized["mapped_default_guard_raw"], 0)
        self.assertIs(requests[6].base_property_block,
                      normalized["list_168"]["rows"][0]["nested_rows"][0]["mapped_family"]["rows"][1]["property_block"])
        weighted = result.independent_stage_outputs["carrier_weighted630"]
        self.assertEqual([row.weight_q64 for row in weighted], [0, -Q, 2 * Q])
        self.assertEqual([row.definition_identity for row in weighted[:2]], ["weighted:duplicate"] * 2)
        self.assertEqual([row.weight_q64 for row in result.context.weighted_rows[-3:]], [0, -Q, 2 * Q])

        partial_raw = deepcopy(raw)
        leaf = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD]
        leaf.update(availability(False, "selected_pc_pointer_null"))
        branch = leaf["list_168"]
        branch.update(availability(False, "selected_pc_pointer_null"), mapped_ready=False)
        occurrence = branch["rows"][0]
        occurrence.update(mapped_ready=False, ready=False, reason="selected_pc_pointer_null")
        header = occurrence["nested_rows"][0]["mapped_family"]
        header.update(availability(False, "selected_pc_pointer_null"))
        header["rows"][1].update(property_identity=None, property_block=None, reason="selected_pc_pointer_null")
        _, partial, partial_skills = evaluate(partial_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "post2920850_list_168_occurrence0_nested0_descriptor0_preDescriptor1")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (8600911,))
        self.assertEqual(partial.context.weighted_count, 44)
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 92))
        self.assertEqual(len(partial.independent_stage_outputs[FIELD]), 6)
        self.assertEqual(len(partial.independent_stage_outputs[FIELD + ".list_168.occurrence0.nested0.descriptor2"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs[FIELD + ".list_168.occurrence0.slot5"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs[FIELD + ".list_168.occurrence1.slot0"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs[FIELD + ".list_180"]), 4)
        self.assertEqual(len(partial.independent_stage_outputs["carrier_weighted630"]), 3)
        ledger = next(item for item in partial.source_ledger["ordered_tail_stages"] if item["stage"] == FIELD)
        descriptor_parts = [row for row in ledger["provider192_family_stages"][1]["verified_parts"]
                            if "nested0.descriptor" in row["part"] and "occurrence0" in row["part"]]
        self.assertEqual([row["in_contiguous_family_prefix"] for row in descriptor_parts], [True, False, False, False])
        self.assertFalse(result.source_ledger["current_final_context_used_as_default"])
        self.assertFalse(result.source_ledger["provider192_native_evaluation_equivalence_claimed"])
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            source_requests=25, materialized_weighted_rows=65, three_family_request_counts=[1, 20, 4],
            four_direct_slots_precede_nested_descriptors=True,
            mapped_PC_qualified_with_unused_guard_zero=True, signed_weighted630=[0, -Q, 2 * Q],
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            partial_provider_requests=6, independent_later_list_requests=4,
            independent_signed630_requests=3, next_source_stage="291CC71_2920B50",
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
