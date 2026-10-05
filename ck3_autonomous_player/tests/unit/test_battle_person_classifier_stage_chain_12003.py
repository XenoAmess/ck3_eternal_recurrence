"""One actual classifier/provider source chain -> signed skill contribution."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_following_stage_chain_12003 import following_frame
from test_battle_person_following_2bca620_12003 import (
    FIELD, following2bca620_source, availability, operand,
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


def classifier_frame():
    raw = following_frame()
    leaf = following2bca620_source()[FIELD]
    leaf["provider_selection"]["pc"]["property_block"].update(keys_u16=[5, 65535], values_q64=[-120 * Q, 0])
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD] = leaf
    return raw


class PersonClassifierStageChain12003Tests(unittest.TestCase):
    def test_actual_provider_signed_PC_empty_skip_and_missing_income_join_stage_and_skills(self):
        raw = classifier_frame()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def leaf_of(source):
            return source["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD]

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage=FIELD)
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "post2BCA620_pre291CCD7")
        self.assertEqual(result.context.aggregate_properties.values_q64, (8707450,))
        self.assertEqual(result.context.weighted_count, 74)
        self.assertEqual(skills.raw_points, (6, 6, 6, 6, 6, 93))
        self.assertEqual(skills.final_cache_points, skills.raw_points)
        requests = result.independent_stage_outputs[FIELD]
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].weight_q64, Q)
        self.assertIs(requests[0].base_property_block,
                      person["current_context_source_inputs"][FIELD]["provider_selection"]["pc"]["property_block"])
        ledger = next(row for row in result.source_ledger["ordered_tail_stages"] if row["stage"] == FIELD)
        observed = ledger["following_2bca620_observation"]
        self.assertEqual(observed["classifier"]["index_raw_i32"], -1)
        self.assertEqual(observed["provider_selection"]["count_raw"], -1)
        self.assertEqual(observed["provider_selection"]["selection"], "provider_1690_equality_sentinel")

        empty_raw = deepcopy(raw)
        empty_provider = leaf_of(empty_raw)["provider_selection"]
        empty_provider.update(count_raw=0, selection="global_fallback_5d1e0b0",
            definition_identity="actual_global_fallback", pc=operand("actual_global_fallback:inline40"))
        _, empty, empty_skills = evaluate(empty_raw)
        self.assertTrue(empty.ready, empty.missing_inputs)
        self.assertEqual(empty.stage, result.stage)
        self.assertEqual(empty.context.aggregate_properties.values_q64, (20707450,))
        self.assertEqual(empty.context.weighted_count, 73)
        self.assertEqual(empty_skills.raw_points[5], 213)
        self.assertEqual(empty_skills.final_cache_points[5], 120)
        self.assertEqual(len(empty.independent_stage_outputs[FIELD]), 1)
        self.assertEqual(empty.independent_stage_outputs[FIELD][0].base_property_block["keys_count"], 0)

        rejected_raw = deepcopy(raw)
        leaf_of(rejected_raw)["provider_selection"].update(definition_magic_u32=0, admitted=False, pc=operand())
        _, rejected, rejected_skills = evaluate(rejected_raw)
        self.assertTrue(rejected.ready, rejected.missing_inputs)
        self.assertEqual(rejected.stage, result.stage)
        self.assertEqual(rejected.context, empty.context)
        self.assertEqual(rejected_skills.final_cache_points, empty_skills.final_cache_points)
        self.assertEqual(rejected.independent_stage_outputs[FIELD], ())

        negative_raw = deepcopy(raw)
        leaf = leaf_of(negative_raw)
        leaf.update(availability(False, "negative_balance_income_2bca4e0"))
        leaf["balance_source"].update(balance_raw_q64=-Q, numeric_balance_q64=-Q)
        leaf["classifier"].update(availability(False, "negative_balance_income_2bca4e0"),
            selection="negative_balance_income_unobserved", index_raw_i32=None)
        leaf["provider_selection"].update(availability(False, "classifier_unavailable"), count_raw=None,
            selection=None, definition_identity=None, definition_magic_u32=None, admitted=None, pc=operand())
        _, negative, negative_skills = evaluate(negative_raw)
        self.assertFalse(negative.ready)
        self.assertEqual(negative.stage, "post2920B50_pre291CC76")
        self.assertEqual(negative.context, empty.context)
        self.assertEqual(negative_skills.final_cache_points, empty_skills.final_cache_points)
        self.assertEqual(negative.independent_stage_outputs[FIELD], ())
        self.assertTrue(any("negative_balance_income_2bca4e0" in item for item in negative.missing_inputs))
        self.assertFalse(result.source_ledger["following_2bca620_negative_balance_implemented"])
        self.assertFalse(result.source_ledger["following_2bca620_cached_income_substituted"])
        self.assertFalse(result.source_ledger["current_final_context_used_as_default"])
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            ready_context_q64=8707450, materialized_weighted_rows=74, source_requests=1,
            negative_count_equality_sentinel_selected=True, signed_PC_changes_projected_skill=True,
            empty_request_preserved=True, empty_weighted_rows=73, rejected_magic_requests=0,
            negative_balance_stage=negative.stage, negative_balance_skills=negative_skills.final_cache_points,
            precise_negative_income_reason_preserved=True, cached_income_not_substituted=True,
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
