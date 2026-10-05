"""One production chain case for whole-vector admission and ranked-PC prefixes."""
from copy import deepcopy
import unittest

from test_battle_person_stage_baseline_12003 import normalize
from test_battle_person_provider192_stage_chain_12003 import provider192_frame
from test_battle_person_following_2920b50_12003 import (
    FIELD, following2920b50_source, availability, operand, preflight_only,
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


def following_frame():
    raw = provider192_frame()
    leaf = following2920b50_source()[FIELD]
    # Other held source leaves already observe the current1B0 component.
    # Registry fallback can still be selected with its570 raw ID undemanded.
    leaf["own_1b0_570"]["component_present"] = True

    def use_prowess_values(value):
        if isinstance(value, dict):
            if "keys_u16" in value:
                value["keys_u16"] = [5 if key != 65535 else key for key in value["keys_u16"]]
                value["values_q64"] = [item * 1000 for item in value["values_q64"]]
            for item in value.values():
                use_prowess_values(item)
        elif isinstance(value, list):
            for item in value:
                use_prowess_values(item)

    use_prowess_values(leaf)
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"][FIELD] = leaf
    return raw


class PersonFollowingStageChain12003Tests(unittest.TestCase):
    def test_entire_preflight_controls_contiguous_attribute_fold_and_skill_projection(self):
        raw = following_frame()
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
        self.assertEqual(result.stage, "post2920B50_pre291CC76")
        self.assertEqual(result.context.aggregate_properties.values_q64, (20707450,))
        self.assertEqual(result.context.weighted_count, 73)
        self.assertEqual(skills.raw_points, (6, 6, 6, 6, 6, 213))
        self.assertEqual(skills.final_cache_points, (6, 6, 6, 6, 6, 120))
        requests = result.independent_stage_outputs[FIELD]
        self.assertEqual(len(requests), 8)
        self.assertEqual([row.source_ordinal for row in requests], [0] * 6 + [1] * 2)
        self.assertEqual([row.first_row_index for row in requests[:6]], [0, 0, 0, 1, 1, 1])
        self.assertEqual([row.weight_q64 for row in requests], [Q] * 8)
        normalized = person["current_context_source_inputs"][FIELD]
        self.assertIs(requests[0].base_property_block,
                      normalized["list_1c8_50"]["rows"][0]["attributes"][0]["pc"]["property_block"])

        rejected_raw = deepcopy(raw)
        for occurrence in leaf_of(rejected_raw)["list_1c8_50"]["rows"]:
            occurrence.update(preflight_all_valid=False)
            occurrence["attributes"] = occurrence["attributes"][:2]
            for row in occurrence["attributes"]:
                preflight_only(row)
            occurrence["attributes"][1].update(definition_magic_u32=0, preflight_valid=False)
        _, rejected, rejected_skills = evaluate(rejected_raw)
        self.assertTrue(rejected.ready, rejected.missing_inputs)
        self.assertEqual(rejected.stage, result.stage)
        self.assertEqual(rejected.context.aggregate_properties.values_q64, (13507450,))
        self.assertEqual(rejected.context.weighted_count, 67)
        self.assertEqual(rejected_skills.raw_points, (6, 6, 6, 6, 6, 141))
        self.assertEqual(rejected_skills.final_cache_points, (6, 6, 6, 6, 6, 120))
        self.assertEqual(len(rejected.independent_stage_outputs[FIELD]), 2)
        self.assertEqual(rejected.independent_stage_outputs[FIELD + ".list_1c8_50"], ())

        unread_raw = deepcopy(rejected_raw)
        leaf = leaf_of(unread_raw)
        leaf.update(availability(False, "preflight_unread"))
        leaf["list_1c8_50"].update(availability(False, "preflight_unread"))
        for occurrence in leaf["list_1c8_50"]["rows"]:
            occurrence.update(availability(False, "preflight_unread"))
            occurrence.update(preflight_ready=False, preflight_all_valid=None)
            occurrence["attributes"][1].update(definition_magic_u32=None, preflight_valid=None, reason="preflight_unread")
        _, unread, unread_skills = evaluate(unread_raw)
        self.assertFalse(unread.ready)
        self.assertEqual(unread.stage, "postCarrierWeighted630_pre291CC71")
        self.assertEqual(unread.context.aggregate_properties.values_q64, (9007450,))
        self.assertEqual(unread.context.weighted_count, 65)
        self.assertEqual(unread_skills.final_cache_points, (6, 6, 6, 6, 6, 96))
        self.assertEqual(unread.independent_stage_outputs[FIELD], ())
        self.assertEqual(unread.independent_stage_outputs[FIELD + ".list_1c8_50.occurrence0.attribute0"], ())
        self.assertEqual(len(unread.independent_stage_outputs[FIELD + ".own_1b0_570"]), 2)

        cold_raw = deepcopy(raw)
        leaf = leaf_of(cold_raw)
        leaf.update(availability(False, "ranked_default_initialization_result"))
        leaf["list_1c8_50"].update(availability(False, "ranked_default_initialization_result"))
        # The repeated list ID resolves the same physical attribute vector.
        for occurrence in leaf["list_1c8_50"]["rows"]:
            occurrence.update(availability(False, "ranked_default_initialization_result"))
            occurrence["attributes"][1].update(rank_raw_i32=0, index_raw_i32=-1,
                ranked_count_raw=None, ranked_array_present=None, selection="uninitialized_default_5d68fb0",
                selected_row_identity="ranked_default:5d68fb0", ranked_default_init_guard_raw=0,
                pc=operand(), ready=False, reason="ranked_default_initialization_result")
        _, cold, cold_skills = evaluate(cold_raw)
        self.assertFalse(cold.ready)
        self.assertEqual(cold.stage, "post2920B50_list_1c8_50_occurrence0_attribute0_preAttribute1")
        self.assertEqual(cold.context.aggregate_properties.values_q64, (10107450,))
        self.assertEqual(cold.context.weighted_count, 66)
        self.assertEqual(cold_skills.final_cache_points, (6, 6, 6, 6, 6, 107))
        self.assertEqual(len(cold.independent_stage_outputs[FIELD]), 1)
        self.assertEqual(len(cold.independent_stage_outputs[FIELD + ".list_1c8_50.occurrence0.attribute2"]), 1)
        self.assertEqual(len(cold.independent_stage_outputs[FIELD + ".list_1c8_50.occurrence1.attribute0"]), 1)
        self.assertEqual(len(cold.independent_stage_outputs[FIELD + ".own_1b0_570"]), 2)
        self.assertFalse(result.source_ledger["following_2920b50_cold_ranked_default_assumed_empty"])
        self.assertFalse(result.source_ledger["current_final_context_used_as_default"])
        self.assertFalse(result.full_person_preparation_ready)
        self.assertFalse(result.full_entry_ready)
        self.assertEqual(raw, original)
        self.assertEqual(prior.context.aggregate_properties.values_q64, (2 * Q,))
        OBSERVATIONS.update(ready_stage=result.stage, ready_skills=skills.final_cache_points,
            ready_raw_skills=skills.raw_points, actual_caps_preserved=True,
            source_requests=8, materialized_weighted_rows=73, family_request_counts=[6, 2],
            known_invalid_stage=rejected.stage, known_invalid_skills=rejected_skills.final_cache_points,
            known_invalid_raw_skills=rejected_skills.raw_points,
            earlier_valid_attributes_suppressed_by_entire_preflight=True,
            unknown_preflight_stage=unread.stage, unknown_preflight_skills=unread_skills.final_cache_points,
            unknown_preflight_releases_no_attributes=True,
            cold_ranked_stage=cold.stage, cold_ranked_skills=cold_skills.final_cache_points,
            independently_ready_own_requests=2, cold_ranked_default_not_fabricated=True,
            conditional_on_observed_source_values=True, full_person_preparation_ready=False, full_entry_ready=False)


if __name__ == "__main__":
    unittest.main()
