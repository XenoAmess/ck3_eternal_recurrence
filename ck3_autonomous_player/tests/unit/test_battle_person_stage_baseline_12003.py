"""One normalizer -> explicit stage assembly -> existing six-skill integration."""
from copy import deepcopy
import json
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.simulation.battle_trait_materialized_prefix_12003 import (
    PersonStageStartBaseline12003,
    assemble_person_stage_prefix_and_branch_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    compute_six_skill_cache_from_native_inputs_12003,
)

Q, ACTOR, DATE, REVISION = 100000, 29829, 53262000, 3
OBSERVATIONS = {}


def properties(*rows):
    return {"keys_u16": [key for key, _ in rows],
            "values_q64": [value for _, value in rows], "count": len(rows)}


def block(*rows):
    return {"rows": [{"key": key, "value_raw": value} for key, value in rows]}


def context(*rows, weighted_count=0):
    return {"aggregate_properties": properties(*rows),
            "weighted_count": weighted_count,
            "weighted_rows": ([] if weighted_count == 0 else [{
                "native_index": 0, "weight_q64": Q, "properties": properties(*rows)}])}


def frame():
    prefix = {
        "available": True, "reason": None, "character_full_id": ACTOR,
        "base_property_block": block((5, -Q)),
        "common_property_blocks": [block((0, 0)), block()],
        "selector": {"available": True, "uses_18f8_source": False,
                     "selected_header_offset": 0x19A0},
        "selected_property_blocks": [block((4, 3 * Q))],
    }
    branch = {
        "status": "available", "ready": True, "character_id": ACTOR,
        "flag14": True, "selected_index": 2,
        "selected_property_block": properties((5, 4 * Q)),
        "group_counts": [2, 0, 3, 1, 0, 0, 1],
        "group_property_blocks": [properties((5, -Q)), None,
                                  properties((0, Q)), properties(), None, None,
                                  properties((4, -Q), (65535, 99 * Q))],
        "unavailable_reason": None,
    }
    numeric = {
        "status": "available", "raw_numeric_inputs_ready": True,
        "character_id": ACTOR, "scratch_present": True,
        "context_source": "model_inline", "unavailable_reason": None,
        "base_points": [6] * 6, "caps": [120] * 6,
        "prowess_adjustment": 0, "category_counts": [0] * 4,
        "scratch_factor_numerator": 0, "scratch_factor_denominator": 1,
        # A stored final operand deliberately differs from both modeled stages.
        "context": context((5, 99 * Q), weighted_count=1),
    }
    state = {
        "scope": "current_character",
        "effective_prowess": {"status": "available", "points": 8,
                              "unavailable_reason": None},
        "injury_traits": {
            "status": "available", "flags": dict.fromkeys((
                "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
                "one_eyed", "disfigured", "incapable"), False),
            "wounded_rank": 0, "unavailable_reason": None,
            "wounded_rank_unavailable_reason": None,
        },
        "current_prior_context_inputs": prefix, "context_branch_inputs": branch,
        "raw_numeric_inputs": numeric,
    }
    return {
        "schema_version": 1, "contract_stage": BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
        "status": "available", "unavailable_reason": None,
        "battle_terminal_transition_ready": False,
        "snapshot_revision": REVISION, "observed_date_raw": DATE,
        "prior_combat_id": -1, "subject_public_cunit_id": -1,
        "terminal_journal": {"requested_after_sequence": None, "oldest_available_sequence": 0,
                             "latest_sequence": 0, "event_sequence": None,
                             "event_status": "not_observed"},
        "prior": None, "removal": None, "subject": None, "successor": None,
        "character_observations": [{"character_id": ACTOR, "status": "none",
                                    "actual_jailer_character_id": -1, "alive": True,
                                    "current_person_state": state}],
    }


def normalize(value):
    result = normalize_battle_terminal_transition_v1(
        value, expected_prior_combat_id=None, expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None, expected_observed_date_raw=DATE,
        expected_snapshot_revision=REVISION, expected_character_ids=[ACTOR])
    return result["character_observations"][0]["current_person_state"]


def numerical(person, assembled):
    raw = deepcopy(person["raw_numeric_inputs"])
    raw["context"] = assembled.context
    return compute_six_skill_cache_from_native_inputs_12003(raw)


class BattlePersonStageBaseline12003Tests(unittest.TestCase):
    def test_normalized_sources_join_explicit_reset_stage_and_skill_kernel(self):
        original = frame()
        frozen = deepcopy(original)
        person = normalize(original)
        baseline = PersonStageStartBaseline12003(
            character_full_id=ACTOR, kind="modeled_new_reset",
            entering_counts=(0, 2, 2), context=context((5, 2 * Q), (65535, 11 * Q)),
            source_provenance={"input_kind": "explicit_synthetic_retained_aggregate_stage"})
        retained = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline=baseline)
        self.assertTrue(retained.ready, retained.missing_inputs)
        retained_skills = numerical(person, retained)
        self.assertTrue(retained_skills.calculation_ready, retained_skills.missing_inputs)
        self.assertEqual(retained_skills.final_cache_points, (9, 6, 6, 6, 8, 9))
        self.assertEqual(retained.pre291C204_context["aggregate_properties"],
                         properties((0, 0), (4, 3 * Q), (5, Q), (65535, 11 * Q)))
        self.assertEqual(retained.context["aggregate_properties"],
                         properties((0, 3 * Q), (4, 2 * Q), (5, 3 * Q), (65535, 11 * Q)))
        self.assertEqual([row["weight_q64"] for row in retained.context["weighted_rows"]],
                         [Q, Q, Q, Q, 2 * Q, 3 * Q, Q])

        # Current final count is an explicit operand of a proposed NEW reset.
        # Its 99Q final value is never used as a preprefix aggregate.
        cleared = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline=PersonStageStartBaseline12003(
                character_full_id=ACTOR, kind="modeled_new_reset", entering_counts=(1, 1, 1)))
        self.assertTrue(cleared.ready, cleared.missing_inputs)
        self.assertEqual(numerical(person, cleared).final_cache_points, (9, 6, 6, 6, 8, 7))
        self.assertFalse(cleared.historical_stage_observed)

        # A group can be the first nonempty writer. This exercises the newly
        # closed empty-copy nonunit scale, its decomposed multiply, duplicate
        # keys and FFFF, through the same normalizer and existing numeric kernel.
        first_group_frame = deepcopy(original)
        first = first_group_frame["character_observations"][0]["current_person_state"]
        first["current_prior_context_inputs"].update(
            base_property_block=block(), common_property_blocks=[], selected_property_blocks=[])
        first["context_branch_inputs"].update(
            flag14=False, selected_index=None, selected_property_block=None,
            group_counts=[2, 0, 0, 0, 0, 0, 0],
            group_property_blocks=[properties((5, 4000000000), (5, -Q), (65535, 3 * Q))] + [None] * 6)
        first_person = normalize(first_group_frame)
        scaled = assemble_person_stage_prefix_and_branch_12003(
            first_person["current_prior_context_inputs"], first_person["context_branch_inputs"],
            stage_start_baseline=PersonStageStartBaseline12003(
                character_full_id=ACTOR, kind="modeled_new_reset", entering_counts=(-1, None, None)))
        self.assertTrue(scaled.ready, scaled.missing_inputs)
        self.assertEqual(scaled.context["aggregate_properties"],
                         properties((5, 8000000000), (5, -2 * Q), (65535, 6 * Q)))
        scaled_skills = numerical(first_person, scaled)
        self.assertTrue(scaled_skills.calculation_ready, scaled_skills.missing_inputs)
        self.assertEqual(scaled_skills.raw_points[5], 80006)
        self.assertEqual(scaled_skills.final_cache_points[5], 120)

        # The retained branch needs the aggregate; zero rows alone cannot supply it.
        missing = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline=PersonStageStartBaseline12003(
                character_full_id=ACTOR, kind="modeled_new_reset", entering_counts=(0, 2, 2)))
        self.assertFalse(missing.ready)
        self.assertIsNone(missing.context)
        self.assertIn("stage_start_baseline.context", missing.missing_inputs)
        final_as_prior = assemble_person_stage_prefix_and_branch_12003(
            person["current_prior_context_inputs"], person["context_branch_inputs"],
            stage_start_baseline={"stage": "current_final", "kind": "explicit_post_reset_logical_context",
                                  "context": person["raw_numeric_inputs"]["context"]})
        self.assertFalse(final_as_prior.ready)
        self.assertIsNone(final_as_prior.context)
        self.assertEqual(original, frozen)
        self.assertEqual(person["effective_prowess"]["points"], 8)
        self.assertFalse(retained.full_future_context_ready)
        self.assertFalse(retained.native_write_performed)
        self.assertEqual(retained.actual_game_days_advanced, 0)
        OBSERVATIONS.update({
            "input_kind": "source_conditioned_synthetic_production_normalizer_integration",
            "character_full_id": ACTOR, "normalizer_used": True,
            "retained_aggregate_skills": list(retained_skills.final_cache_points),
            "new_reset_cleared_skills": list(numerical(person, cleared).final_cache_points),
            "first_group_scaled_prowess_raw": scaled_skills.raw_points[5],
            "first_group_scaled_prowess_final": scaled_skills.final_cache_points[5],
            "missing_retained_aggregate_partial": not missing.ready,
            "current_final_prior_unavailable": not final_as_prior.ready,
            "current_prowess_preserved": 8, "full_future_context_ready": False,
            "historical_stage_observed": False, "native_writes_game_days": 0,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
