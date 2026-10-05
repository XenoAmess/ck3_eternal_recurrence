"""One new actual provider -> government -> six-skill integration."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import frame, normalize
from test_battle_person_2922070_stage_chain_12003 import ready_source
from test_battle_person_conference_stage_chain_12003 import conference, middle
from test_battle_person_tail_stage_chain_12003 import pc, Q, ACTOR
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainResult12003, STOP_STAGE_12003,
    continue_current_person_stage_chain_tail_12003, project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}


def provider():
    return {"status": "available", "ready": True, "character_id": ACTOR,
        "provider_present": True, "provider_identity": "loaded-provider",
        "carrier_present": True, "key_2f8_raw": -7, "denominator_5c68ce8_raw": 0,
        "bucket_index_raw": 42949, "provider_count_1204_raw": 42950,
        "provider_array_present": True, "selection": "provider_bucket_11f8",
        "selected_definition_identity": "actual-bucket42949", "selected_magic_raw": 0x4744624F,
        "admitted": True, "property_identity": "actual-bucket42949:PC40",
        "property_block": pc(7 * Q), "reason": None}


def provider_frame():
    raw = frame()
    section = ready_source()
    section["conference_24b1d00"] = conference()
    section["middle_helpers_291f260_291fb10"] = middle()
    section["provider_bucket_291c5b2"] = provider()
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"] = section
    return raw


class PersonProviderStageChain12003Tests(unittest.TestCase):
    def test_actual_provider_selection_rejoins_government_and_missing_pc_preserves_prefix(self):
        raw = provider_frame()
        original = deepcopy(raw)
        explicit = NativeModifierContext12003(PropertyContainer12003((5,), (2 * Q,), 1), (), 0)
        prior = PersonStageChainResult12003(ACTOR, STOP_STAGE_12003, explicit, True, (),
            {"input": "explicit_pre467_logical_context", "historical_frame_claim": False},
            {STOP_STAGE_12003: explicit}, {})

        def evaluate(source):
            person = normalize(source)
            result = continue_current_person_stage_chain_tail_12003(person, prior,
                character_full_id=ACTOR, through_stage="government_870_a30")
            skills = project_stage_chain_six_skills_12003(result,
                from_raw_numeric_inputs_12003(person["raw_numeric_inputs"]))
            self.assertTrue(skills.calculation_ready, skills.missing_inputs)
            return person, result, skills

        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, "postGovernmentA30_pre291C620")
        self.assertEqual(result.context.aggregate_properties.values_q64, (34 * Q,))
        self.assertEqual(result.context.weighted_count, 15)
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 40))
        self.assertEqual(result.source_ledger["first_contiguous_observation_dependency"],
                         "qualifier_repeated_contribution")
        request, = result.independent_stage_outputs["signed2F8_provider_bucket"]
        observed = person["current_context_source_inputs"]["provider_bucket_291c5b2"]
        self.assertEqual((request.source_name, request.first_row_index, request.row_count, request.weight_q64),
                         ("291c5b2_provider_bucket40", 42949, 1, Q))
        self.assertEqual(request.definition_identity, "actual-bucket42949:PC40")
        self.assertIs(request.base_property_block, observed["property_block"])
        self.assertEqual(observed["denominator_5c68ce8_raw"], 0)
        self.assertEqual(len(result.independent_stage_outputs["government_870_a30"]), 2)

        fallback_raw = deepcopy(raw)
        fallback = fallback_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["provider_bucket_291c5b2"]
        fallback.update(denominator_5c68ce8_raw=1, bucket_index_raw=-7,
            provider_count_1204_raw=None, provider_array_present=None,
            selection="native_fallback_5d1e0b0", selected_definition_identity="actual-fallback",
            property_identity="actual-fallback:PC40", property_block=pc(-4 * Q))
        _, fallback_result, fallback_skills = evaluate(fallback_raw)
        self.assertTrue(fallback_result.ready, fallback_result.missing_inputs)
        self.assertEqual(fallback_result.stage, result.stage)
        self.assertEqual(fallback_result.context.aggregate_properties.values_q64, (23 * Q,))
        self.assertEqual(fallback_skills.final_cache_points, (6, 6, 6, 6, 6, 29))
        self.assertEqual(fallback_result.independent_stage_outputs["signed2F8_provider_bucket"][0].first_row_index, 0)

        null_raw = deepcopy(raw)
        null_provider = null_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["provider_bucket_291c5b2"]
        null_provider.update(carrier_present=False, key_2f8_raw=None, denominator_5c68ce8_raw=None,
            bucket_index_raw=0, provider_count_1204_raw=1,
            selected_definition_identity="actual-bucket0", property_identity="actual-bucket0:PC40")
        null_person, null_result, null_skills = evaluate(null_raw)
        self.assertTrue(null_result.ready, null_result.missing_inputs)
        self.assertEqual(null_result.stage, result.stage)
        self.assertEqual(null_skills.final_cache_points, skills.final_cache_points)
        self.assertIsNone(null_person["current_context_source_inputs"]["provider_bucket_291c5b2"]["denominator_5c68ce8_raw"])

        partial_raw = deepcopy(raw)
        partial_provider = partial_raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"]["provider_bucket_291c5b2"]
        partial_provider.update(status="partial", ready=False, property_block=None,
                                reason="selected_provider_PC_unavailable")
        _, partial, partial_skills = evaluate(partial_raw)
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, "post291F260_pre291C558")
        self.assertEqual(partial.context.aggregate_properties.values_q64, (24 * Q,))
        self.assertEqual(partial_skills.final_cache_points, (6, 6, 6, 6, 6, 30))
        self.assertEqual(len(partial.independent_stage_outputs["government_870_a30"]), 2)
        self.assertTrue(any("signed2F8_provider_bucket" in gap for gap in partial.missing_inputs))
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertFalse(result.source_ledger["all_tail_source_stream_ready"])
        self.assertTrue(result.source_ledger["conditional_on_observed_source_values"])
        self.assertFalse(result.source_ledger["291f260_weights_recomputed_from_assembled_context"])
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            denominator_zero_selected_index=42949, signed_fallback_skills=fallback_skills.final_cache_points,
            null_carrier_skills=null_skills.final_cache_points, all_selection_branches_rejoin_government=True,
            partial_stage=partial.stage, partial_skills=partial_skills.final_cache_points,
            independent_government_preserved=True, next_source_stage="qualifier_repeated_contribution",
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
