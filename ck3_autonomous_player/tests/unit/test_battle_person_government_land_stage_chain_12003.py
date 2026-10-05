"""Government/first-Land known-zero stages keep the explicit context and skills."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_classifier_stage_chain_12003 import classifier_frame
from test_battle_person_following_312a950_12003 import (
    FIELD, following312a950_source, availability, operand,
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


def government_land_frame():
    raw = classifier_frame()
    leaf = following312a950_source()[FIELD]
    # This held frame already has no death component and a living component.
    leaf["government_source"].update(selection="living_1c0_3f8", government_identity="government:living")
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD] = leaf
    return raw


class PersonGovernmentLandStageChain12003Tests(unittest.TestCase):
    def test_known_zero_stage_advances_and_missing_mode3_retains_actual_prior_and_skills(self):
        raw = government_land_frame()
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
        self.assertEqual(result.stage, "postGovernmentLand312A950_pre291CD92")
        self.assertEqual(result.context.aggregate_properties.values_q64, (8707450,))
        self.assertEqual(result.context.weighted_count, 74)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 93))
        self.assertEqual(result.independent_stage_outputs[FIELD], ())
        observed = next(row for row in result.source_ledger["ordered_tail_stages"]
                        if row["stage"] == FIELD)["following_312a950_observation"]
        self.assertEqual(observed["stage_selection"], "first_land_nonnegative")
        self.assertEqual(observed["government_source"]["selection"], "living_1c0_3f8")
        self.assertEqual(observed["first_land_source"]["selection"], "living_1c0")
        self.assertIsNone(observed["first_land_source"]["death_present"])
        self.assertIsNone(observed["mode3_classifier"])
        self.assertIsNone(observed["provider_selection"])

        bit_false = deepcopy(raw)
        leaf = leaf_of(bit_false)
        leaf["government_source"]["flags_raw_u32"] = 0
        leaf.update(character_state_present=None, first_land_source=None, land_resolution=None,
                    stage_selection="government_bit29_false")
        _, skipped, skipped_skills = evaluate(bit_false)
        self.assertTrue(skipped.ready, skipped.missing_inputs)
        self.assertEqual(skipped.stage, result.stage)
        self.assertEqual(skipped.context, result.context)
        self.assertEqual(skipped_skills.final_cache_points, skills.final_cache_points)

        invalid = deepcopy(raw)
        leaf = leaf_of(invalid)
        leaf["land_resolution"].update(magic_u32=0, full_id_raw=None, admitted=False, balance_raw_q64=None)
        leaf["stage_selection"] = "first_land_invalid"
        _, rejected, rejected_skills = evaluate(invalid)
        self.assertTrue(rejected.ready, rejected.missing_inputs)
        self.assertEqual(rejected.stage, result.stage)
        self.assertEqual(rejected.context, result.context)
        self.assertEqual(rejected_skills.final_cache_points, skills.final_cache_points)

        missing_resolver = deepcopy(raw)
        leaf = leaf_of(missing_resolver)
        leaf.update(availability(False, "land_registry_unavailable"), stage_selection=None)
        leaf["land_resolution"].update(availability(False, "land_registry_unavailable"), selection=None,
            selected_full_id_raw=None, object_identity=None, magic_u32=None, full_id_raw=None,
            admitted=None, balance_raw_q64=None)
        _, unavailable, unavailable_skills = evaluate(missing_resolver)
        self.assertFalse(unavailable.ready)
        self.assertEqual(unavailable.stage, "post2BCA620_pre291CCD7")
        self.assertEqual(unavailable.context, result.context)
        self.assertEqual(unavailable_skills.final_cache_points, skills.final_cache_points)
        self.assertTrue(any("land_registry_unavailable" in item for item in unavailable.missing_inputs))

        negative_raw = deepcopy(raw)
        leaf = leaf_of(negative_raw)
        leaf.update(availability(False, "mode3_income_2bca580"), stage_selection="negative_land_mode3_income_unobserved")
        leaf["land_resolution"]["balance_raw_q64"] = -1
        leaf["mode3_classifier"] = {**availability(False, "mode3_income_2bca580"), "income_q64": None,
                                   "index_raw_i32": None}
        leaf["provider_selection"] = {**availability(False, "mode3_income_2bca580"), "provider_loaded": True,
            "count_raw": None, "selection": None, "definition_identity": None,
            "definition_magic_u32": None, "admitted": None, "pc": operand()}
        _, negative, negative_skills = evaluate(negative_raw)
        self.assertFalse(negative.ready)
        self.assertEqual(negative.stage, unavailable.stage)
        self.assertEqual(negative.context, result.context)
        self.assertEqual(negative_skills.final_cache_points, skills.final_cache_points)
        self.assertEqual(negative.independent_stage_outputs[FIELD], ())
        self.assertTrue(any("mode3_income_2bca580" in item for item in negative.missing_inputs))
        negative_observed = next(row for row in negative.source_ledger["ordered_tail_stages"]
                                 if row["stage"] == FIELD)["following_312a950_observation"]
        self.assertTrue(negative_observed["provider_selection"]["provider_loaded"])
        self.assertIsNone(negative_observed["mode3_classifier"]["income_q64"])
        self.assertFalse(result.source_ledger["following_312a950_negative_mode3_income_implemented"])
        self.assertFalse(result.source_ledger["following_312a950_gold_income_substituted"])
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            ready_context_q64=8707450, materialized_weighted_rows=74, source_requests=0,
            known_zero_retains_previous_context=True, government_selection="living_1c0_3f8",
            first_land_selection="living_1c0", undemanded_death_source=None,
            bit_false_and_invalid_land_advance_same_stage=True,
            missing_land_stage=unavailable.stage, negative_mode3_stage=negative.stage,
            negative_mode3_skills=negative_skills.final_cache_points,
            actual_prefetched_provider_retained=True, precise_mode3_reason_preserved=True,
            no_gold_income_substitution=True, conditional_on_observed_source_values=True,
            full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
