"""Source-derived fresh B and held A join actual normalized prefix/branch inputs.

Only fixture builders are imported from the earlier module. Its tests are not
discovered or rerun by this case. No native constructor or game is executed.
"""
from copy import deepcopy
import json
import unittest

from test_battle_person_stage_baseline_12003 import (
    ACTOR, Q, block, context, frame, normalize, numerical, properties,
)
from xar_autoplayer.simulation.battle_trait_materialized_prefix_12003 import (
    PersonStageStartBaseline12003,
    assemble_person_stage_prefix_and_branch_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    SOURCE_EXE_SHA256_12003,
)

OBSERVATIONS = {}

# Normal-return numeric postimages proved before this test was written:
# 291BE63 ->24387E0 ->11E1350 /CA1870 /CA18F0. The last slot20 leaf
# changes only data/capacity after each constructor's capacity/count QWORD0.
FRESH_COUNTS = (0, 0, 0)
INITIALIZED_HEADERS = {
    "weighted": {"count_model_offset": "1C", "count": 0,
                 "data_model_offset": "30", "capacity": 4,
                 "final_target": "896B80"},
    "keys": {"count_model_offset": "84", "count": 0,
             "data_model_offset": "98", "capacity": 32,
             "final_target": "86E150"},
    "values": {"count_model_offset": "EC", "count": 0,
               "data_model_offset": "100", "capacity": 32,
               "final_target": "86E150"},
}


class FreshConstructorBaseline12003Tests(unittest.TestCase):
    def test_distinct_fresh_model_joins_normalized_prefix_branch_and_skills(self):
        raw = frame()
        state = raw["character_observations"][0]["current_person_state"]
        held_context = context((0, 12 * Q), (5, 40 * Q))
        state["raw_numeric_inputs"]["context"] = held_context
        state["current_prior_context_inputs"].update(
            base_property_block=block((0, -Q), (5, 2 * Q)),
            common_property_blocks=[block((1, Q)), block((1, Q))],
            selected_property_blocks=[block((4, 3 * Q))],
        )
        state["context_branch_inputs"].update(
            selected_property_block=properties((5, -Q)),
            group_counts=[2, 0, 1, 0, 0, 0, 0],
            group_property_blocks=[properties((5, 3 * Q)), None,
                                   properties((0, 2 * Q)), None, None, None, None],
        )
        frozen = deepcopy(raw)
        person = normalize(raw)
        observed = deepcopy(person)
        owner = person["raw_numeric_inputs"]["character_id"]
        self.assertEqual(owner, ACTOR)
        self.assertEqual(person["current_prior_context_inputs"]["character_full_id"], owner)
        self.assertEqual(person["context_branch_inputs"]["character_id"], owner)

        # B's empty input follows the actual constructor-return numeric source.
        # A's current context is neither copied into B nor renamed prior state.
        source = {
            "input_kind": "source_derived_frozen_fixture_fresh_model",
            "source_exe_sha256": SOURCE_EXE_SHA256_12003,
            "source_stage": "post24387E0_fresh_context",
            "constructor_calls": ("291BE63->24387E0", "24387ED->11E1350",
                                  "24387F6->CA1870", "2438802->CA18F0"),
            "normal_return": True,
            "construction_model_identity": "fixture_fresh_B",
            "held_current_model_identity": "fixture_held_A",
            "character_full_id": owner,
            "copied_owner_source": "cached2A43BE0 newmodel8=oldmodel8",
            "initialized_headers": deepcopy(INITIALIZED_HEADERS),
            "actual_paused_observation": False,
        }
        fresh_baseline = PersonStageStartBaseline12003(
            character_full_id=owner, stage="post_291C010_pre_prefix",
            kind="modeled_new_reset", entering_counts=FRESH_COUNTS,
            context=None, source_provenance=source,
        )
        fresh = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline=fresh_baseline,
        )
        self.assertTrue(fresh.ready, fresh.missing_inputs)
        self.assertEqual(fresh.character_full_id, owner)
        self.assertEqual(fresh.ledger["prefix_ledger"]["explicit_stage_start_baseline"]
                         ["input_source"], source)
        self.assertEqual(fresh.pre291C204_context["aggregate_properties"],
                         properties((0, -Q), (1, 2 * Q), (4, 3 * Q), (5, 2 * Q)))
        self.assertEqual(fresh.context["aggregate_properties"],
                         properties((0, Q), (1, 2 * Q), (4, 3 * Q), (5, 7 * Q)))
        self.assertEqual([row["weight_q64"] for row in fresh.context["weighted_rows"]],
                         [Q, Q, Q, Q, Q, 2 * Q, Q])
        fresh_skills = numerical(person, fresh)
        self.assertTrue(fresh_skills.calculation_ready, fresh_skills.missing_inputs)
        self.assertEqual(fresh_skills.final_cache_points, (7, 8, 6, 6, 9, 13))

        # This is a separately declared NEW numeric reset of held A. Its
        # weighted0 leaves nonempty aggregate intact; it is not B's prior stage
        # and does not assert that this was any historical preparation state.
        retained = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline=PersonStageStartBaseline12003(
                character_full_id=owner, stage="post_291C010_pre_prefix",
                kind="modeled_new_reset", entering_counts=(0, 2, 2),
                context=deepcopy(person["raw_numeric_inputs"]["context"]),
                source_provenance={
                    "input_kind": "separately_modeled_new_reset_of_held_A",
                    "construction_model_identity": "fixture_held_A",
                    "character_full_id": owner,
                    "historical_stage_observed": False,
                    "used_as_fresh_B_prior": False,
                },
            ),
        )
        self.assertTrue(retained.ready, retained.missing_inputs)
        self.assertEqual(retained.context["aggregate_properties"],
                         properties((0, 13 * Q), (1, 2 * Q), (4, 3 * Q), (5, 47 * Q)))
        retained_skills = numerical(person, retained)
        self.assertTrue(retained_skills.calculation_ready, retained_skills.missing_inputs)
        self.assertEqual(retained_skills.final_cache_points, (19, 8, 6, 6, 9, 53))

        self.assertEqual(raw, frozen)
        self.assertEqual(person, observed)
        self.assertEqual(person["raw_numeric_inputs"]["context"], held_context)
        self.assertEqual(person["effective_prowess"]["points"], 8)
        self.assertFalse(raw["battle_terminal_transition_ready"])
        for result in (fresh, retained):
            self.assertEqual(result.ledger["stage_order"][-1], "post291D1D0_pre291C209")
            self.assertFalse(result.ledger["current_final_context_used_as_default"])
            self.assertFalse(result.ledger["Entry_refresh_claim"])
            self.assertFalse(result.full_future_context_ready)
            self.assertFalse(result.historical_stage_observed)
            self.assertFalse(result.native_write_performed)
            self.assertEqual(result.actual_game_days_advanced, 0)

        OBSERVATIONS.update({
            "input_kind": "source_derived_frozen_synthetic_production_compound_case",
            "normalizer": "normalize_battle_terminal_transition_v1",
            "character_full_id": owner,
            "distinct_model_identities": ["fixture_held_A", "fixture_fresh_B"],
            "fresh_initial_counts": list(FRESH_COUNTS),
            "fresh_header_postimages": INITIALIZED_HEADERS,
            "fresh_bounded_aggregate": fresh.context["aggregate_properties"],
            "fresh_six_skills": list(fresh_skills.final_cache_points),
            "separately_modeled_retained_A_skills": list(retained_skills.final_cache_points),
            "current_context_and_prowess_preserved": True,
            "bounded_stop_stage": "post291D1D0_pre291C209",
            "current_final_as_fresh_prior": False,
            "full_future_context_ready": False,
            "Entry_refresh_claim": False,
            "new_native_or_paused_frame": False,
            "new_production_glue_needed": False,
            "native_writes_game_days_advanced": 0,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
