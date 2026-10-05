"""One new literal/composed-temporary stage -> six-skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_provider_stage_chain_12003 import provider_frame
from test_battle_person_qualifier_stage_chain_12003 import qualifier
from test_battle_person_list_stage_chain_12003 import list_source, ready_fb10
from test_battle_person_gated_temporary_tail_12003 import (
    FIELD, availability, gated_temporary_source, named, pc as source_pc, prefix,
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


def gated_frame():
    raw = provider_frame()
    section = raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]
    section["qualifier_28bc0d0"] = qualifier()
    section["middle_helpers_291f260_291fb10"].update(
        status="available", ready=True, reason=None, helper_291fb10=ready_fb10())
    section["list_predicate_2530dd0"] = list_source()
    leaf = gated_temporary_source()[FIELD]
    for branch in (leaf["prefix_1398"], leaf["delta_prefix_1420_14a8"]["prefix"]):
        for row in branch["rows"]:
            row["property_block"]["keys_u16"][0] = 5
    for row in leaf["list"]["rows"]:
        row["property_block"]["keys_u16"][0] = 5
    section[FIELD] = leaf
    return raw


class PersonGatedStageChain12003Tests(unittest.TestCase):
    def test_literal_temporaries_compose_once_and_preserve_empty_and_partial_frontiers(self):
        raw = gated_frame()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="gated_temporary_tail")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "postGatedTemporaryAndList_pre291C9D8")
        self.assertEqual(result.context.aggregate_properties.values_q64, (52 * Q,))
        self.assertEqual(result.context.weighted_count, 29)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 58))
        requests = result.independent_stage_outputs["gated_temporary_tail"]
        self.assertEqual([row.source_ordinal for row in requests], [0, 1, 2, 2])
        self.assertEqual([row.weight_q64 for row in requests], [Q] * 4)
        self.assertEqual(requests[0].base_property_block, source_pc((5, 2 * Q), (65535, -2 * Q)))
        self.assertEqual(requests[1].base_property_block, source_pc((5, 5 * Q), (65535, 0)))
        normalized = person["current_context_source_inputs"][FIELD]
        self.assertEqual(normalized["refresh_168"]["fresh_rank_raw"], 0)
        self.assertEqual(normalized["delta_prefix_1420_14a8"]["weight_source"]["raw_fixed_q64"], -250000)
        for index in range(2):
            self.assertIs(requests[index + 2].base_property_block,
                          normalized["list"]["rows"][index]["property_block"])

        dynamic_raw = deepcopy(raw)
        dynamic = dynamic_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD]
        dynamic.update(availability(False, "temporary_delta_missing"))
        dynamic["refresh_168"] = {**availability(False, "dynamic_tree_requires_current_result"),
            "source": named(0x168, kind="dynamic_tree_requires_current_result"),
            "minimum_q64": None, "maximum_q64": None, "clamped_q64": None, "threshold_count": None,
            "threshold_array_present": None, "thresholds_consumed_q64": None, "fresh_rank_raw": None}
        dynamic["delta_prefix_1420_14a8"] = {**availability(False, "fresh_rank_missing"),
            "delta_raw": None, "absolute_delta_raw": None, "header_selection": None,
            "weight_source": named(0x170), "prefix": prefix(ready=False, reason="fresh_rank_missing")}
        _, partial, partial_skills = evaluate(dynamic_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "postGatedPrefix1398_pre291C892")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (47 * Q,))
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 53))
        self.assertEqual(len(partial.independent_stage_outputs["gated_temporary_tail"]), 1)
        self.assertEqual(len(partial.independent_stage_outputs["gated_temporary_tail.list"]), 2)
        row = next(row for row in partial.source_ledger["ordered_tail_stages"] if row["stage"] == "gated_temporary_tail")
        self.assertEqual([item["in_contiguous_family_prefix"] for item in row["gated_temporary_family_stages"]],
                         [True, False, False])
        self.assertTrue(any("gated_temporary_tail_291c7a7.delta_prefix_1420_14a8" in gap
                            for gap in partial.missing_inputs))

        zero_raw = deepcopy(raw)
        zero = zero_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD]
        zero["selected_f8_raw"] = 0
        zero["prefix_1398"] = prefix(0, rows=zero["prefix_1398"]["rows"][:1], header=2)
        zero["delta_prefix_1420_14a8"] = {**availability(), "delta_raw": 0,
            "absolute_delta_raw": None, "header_selection": "zero_delta",
            "weight_source": named(0x170), "prefix": prefix()}
        zero_person, zero_result, zero_skills = evaluate(zero_raw)
        self.assertTrue(zero_result.ready, zero_result.missing_inputs)
        self.assertEqual(zero_result.stage, "postGatedTemporaryAndList_pre291C9D8")
        self.assertEqual(zero_result.context.aggregate_properties.values_q64, (46 * Q,))
        self.assertEqual(zero_result.context.weighted_count, 28)
        self.assertEqual(zero_skills.final_cache_points, (6, 6, 6, 6, 6, 52))
        zero_requests = zero_result.independent_stage_outputs["gated_temporary_tail"]
        self.assertEqual(len(zero_requests), 4)
        self.assertEqual(zero_requests[1].base_property_block, source_pc())
        self.assertEqual(len(zero_result.independent_stage_outputs["gated_temporary_tail.delta_prefix_1420_14a8"]), 1)
        self.assertIsNone(zero_person["current_context_source_inputs"][FIELD]["delta_prefix_1420_14a8"]["weight_source"]["value_q64"])
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["gated_temporary_cached_FC_used"])
        self.assertFalse(result.source_ledger["gated_temporary_native_evaluation_equivalence_claimed"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            composed_temporaries_are_two_outer_unit_requests=True, signed_inner_weight_q64=-250000,
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            dynamic_rank_not_replaced_by_cached_FC=True, independent_list_requests=2,
            zero_delta_skills=zero_skills.final_cache_points,
            empty_delta_source_occurrence_preserved=True, unused_slot170_not_required=True,
            next_source_stage="291C9D8_326A8E0_2920310",
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
