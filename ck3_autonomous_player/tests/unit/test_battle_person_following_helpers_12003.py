"""One actual normalizer -> two bounded numerical helpers -> six-skill case."""
from copy import deepcopy
import json
import unittest

from test_battle_person_stage_baseline_12003 import ACTOR, Q, frame, normalize
from _following_2921350_fixture import (
    following2921350_positive_leaf, following2921350_cold_leaf,
    following2921350_zero_leaf,
)
from following_2921020_fixture_inputs import (
    build_following2921020_positive_leaf, build_following2921020_nonowner_leaf,
)
from xar_autoplayer.simulation.battle_person_stage_chain_12003 import (
    PersonStageChainStart12003, continue_explicit_person_following_stages_12003,
    project_stage_chain_six_skills_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, PropertyContainer12003, from_raw_numeric_inputs_12003,
)

OBSERVATIONS = {}
INCOMING, AFTER1350, AFTER1020 = (
    "post2920D60_pre291CD9D", "post2921350_pre291CDA8", "post2921020_pre291CDB3")


def following_frame(first=None, second=None):
    raw = frame()
    raw["character_observations"][0]["current_person_state"]["current_context_source_inputs"] = {
        "status": "partial", "ready": False, "character_id": ACTOR,
        "branch_291e210": None, "reason": "earlier_actual_sources_not_observed",
        "following_2921350": following2921350_positive_leaf() if first is None else first,
        "following_2921020": build_following2921020_positive_leaf() if second is None else second,
    }
    return raw


class FollowingHelpers12003Tests(unittest.TestCase):
    def test_source_order_zero_and_local_gaps_join_explicit_stage_and_skills(self):
        # This is an explicit supplied fixture stage, not a fabricated proof
        # that the missing Diac admission executed or that held A became B.
        baseline = PersonStageChainStart12003(ACTOR,
            NativeModifierContext12003(PropertyContainer12003((2,), (2 * Q,), 1), (), 0),
            stage=INCOMING, source_provenance={
                "input_kind": "explicit_fixture_post2920D60_logical_context",
                "model_identity": "fresh_B", "held_model_identity": "held_A",
                "historical_stage_observed": False, "earlier_admission_proved": False,
            })

        def evaluate(raw, start=baseline):
            person = normalize(raw)
            result = continue_explicit_person_following_stages_12003(person, start_baseline=start)
            skills = (None if result.context is None else project_stage_chain_six_skills_12003(
                result, from_raw_numeric_inputs_12003(person["raw_numeric_inputs"])))
            return person, result, skills

        raw = following_frame()
        original = deepcopy(raw)
        person, result, skills = evaluate(raw)
        self.assertTrue(result.ready, result.missing_inputs)
        self.assertEqual(result.stage, AFTER1020)
        self.assertEqual(result.context.aggregate_properties.keys_u16, (0, 1, 2, 4, 5))
        self.assertEqual(result.context.aggregate_properties.values_q64, (-3 * Q, Q, 2 * Q, -Q, 11 * Q))
        first = result.independent_stage_outputs["2921350"]
        second = result.independent_stage_outputs["2921020"]
        self.assertEqual(len(first), 2)  # Duplicate Provinces survive Title-pointer dedup.
        self.assertEqual(first[0].base_property_block["keys_u16"], [0, 5, 65535])
        self.assertEqual(first[0].base_property_block["values_q64"], [-4 * Q, 8 * Q, -3 * Q])
        self.assertEqual(first[1].base_property_block["values_q64"], [0])
        self.assertEqual([request.weight_q64 for request in second], [Q, -2 * Q, 0, Q])
        self.assertEqual([request.first_row_index for request in second[:3]], [0, 2, 3])
        self.assertEqual(result.context.weighted_count, 6)
        self.assertTrue(skills.calculation_ready, skills.missing_inputs)
        self.assertEqual(skills.final_cache_points, (3, 7, 8, 6, 5, 17))
        self.assertFalse(person["current_context_source_inputs"]["ready"])
        self.assertTrue(person["current_context_source_inputs"]["following_2921350"]["ready"])
        self.assertTrue(person["current_context_source_inputs"]["following_2921020"]["ready"])
        self.assertEqual(raw, original)
        self.assertEqual(person["raw_numeric_inputs"]["context"],
                         original["character_observations"][0]["current_person_state"]["raw_numeric_inputs"]["context"])
        self.assertFalse(raw["battle_terminal_transition_ready"])

        _, cold, cold_skills = evaluate(following_frame(first=following2921350_cold_leaf()))
        self.assertFalse(cold.ready)
        self.assertEqual(cold.stage, INCOMING)
        self.assertEqual(len(cold.independent_stage_outputs["2921350.group0"]), 1)
        self.assertNotIn("2921350.group1", cold.independent_stage_outputs)
        self.assertEqual(len(cold.independent_stage_outputs["2921020"]), 4)
        self.assertEqual(cold_skills.final_cache_points, (6, 6, 8, 6, 6, 6))

        _, zero, zero_skills = evaluate(following_frame(
            first=following2921350_zero_leaf(), second=build_following2921020_nonowner_leaf()))
        self.assertTrue(zero.ready, zero.missing_inputs)
        self.assertEqual(zero.independent_stage_outputs["2921350"], ())
        self.assertEqual(len(zero.independent_stage_outputs["2921020"]), 1)
        self.assertEqual(zero.context.weighted_count, 1)  # Actual present zero key is one occurrence.
        self.assertEqual(zero_skills.final_cache_points, (6, 6, 8, 6, 6, 6))

        diagnostic = build_following2921020_nonowner_leaf()
        diagnostic.update(status="partial", ready=False, reason="rank_diagnostic_3f7ab90_result",
            rank_raw_i8=-1, tier_selection="diagnostic_3f7ab90_outcome_unobserved",
            selected_row_identity=None, composite_ready=False)
        for name in ("base_pc", "tier_pc"):
            diagnostic[name] = {"property_identity": None, "property_block": None,
                                "reason": "rank_diagnostic_3f7ab90_result"}
        _, partial, partial_skills = evaluate(following_frame(second=diagnostic))
        self.assertFalse(partial.ready)
        self.assertEqual(partial.stage, AFTER1350)
        self.assertEqual(partial_skills.final_cache_points, (2, 6, 8, 6, 6, 14))

        _, missing, _ = evaluate(raw, PersonStageChainStart12003(ACTOR, None, stage=INCOMING))
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.context)
        self.assertEqual(len(missing.independent_stage_outputs["2921350"]), 2)
        self.assertEqual(len(missing.independent_stage_outputs["2921020"]), 4)
        _, final_as_prior, _ = evaluate(raw, PersonStageChainStart12003(ACTOR,
            person["raw_numeric_inputs"]["context"], stage="current_final"))
        self.assertFalse(final_as_prior.ready)
        self.assertIsNone(final_as_prior.context)

        for value in (result, cold, zero, partial, missing, final_as_prior):
            self.assertFalse(value.full_person_preparation_ready)
            self.assertFalse(value.full_entry_ready)
            self.assertFalse(value.native_write_performed)
            self.assertFalse(value.source_ledger["current_final_context_used_as_default"])
            self.assertFalse(value.source_ledger["fresh_installed_stage_identity_inferred"])

        OBSERVATIONS.update({
            "normalizer": "normalize_battle_terminal_transition_v1",
            "character_full_id": ACTOR, "positive_frontier": result.stage,
            "outer_request_counts": [len(first), len(second)],
            "six_skills": list(skills.final_cache_points),
            "cold_actual_frontier": cold.stage, "cold_group0_independently_available": True,
            "diagnostic_actual_frontier": partial.stage,
            "zero_stage_ready": zero.ready, "zero_present_key_occurrences": zero.context.weighted_count,
            "explicit_stage_without_historical_or_admission_proof": True,
            "current_final_prior": False, "original_query_readiness_unchanged": True,
            "native_qualification_live_full_entry": False,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
