"""One affected public stored-state path; synthetic, without native writes."""
from __future__ import annotations

import copy
import json
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.simulation.battle_trait_current_stored_context_12003 import (
    project_current_stored_context_state_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    compute_six_skill_cache_from_native_inputs_12003,
)

Q = 100000
ACTOR = 29829
DATE = 53262000
OBSERVATIONS = {}


def array(address, capacity, count, items):
    return {"data_address": address, "capacity_raw": capacity, "count": count, "items": items}


def normalized(frame):
    return normalize_battle_terminal_transition_v1(
        frame,
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=DATE,
        expected_snapshot_revision=1,
        expected_character_ids=[ACTOR],
    )


class BattleTraitCurrentStoredContext12003Tests(unittest.TestCase):
    def test_stored_context_value_and_independent_reset_projection(self):
        # These are source-shaped synthetic current observations, not a new live
        # frame. The distinct old fallback remains in the same production frame.
        old_raw = {
            "status": "available", "raw_numeric_inputs_ready": True,
            "character_id": ACTOR, "scratch_present": True,
            "context_source": "fallback_static", "unavailable_reason": None,
            "base_points": [11] * 6, "caps": [61, 62, 63, 64, 65, 66],
            "prowess_adjustment": 0, "category_counts": [0] * 4,
            "scratch_factor_numerator": 0, "scratch_factor_denominator": 1,
            "context": {
                "aggregate_properties": {"keys_u16": [5], "values_q64": [8 * Q], "count": 1},
                "weighted_rows": [], "weighted_count": 0,
            },
        }
        stored = {
            "available": True, "reason": None, "character_full_id": ACTOR,
            "scratch_present": True, "scratch_address": 0x2800,
            "model_present": True, "model_address": 0x3000,
            "context_address": 0x3010, "owner_address": 0x2000,
            "owner_character_full_id": ACTOR, "bound_to_requested_character": True,
            "pending_raw": 0, "owned_count_raw": 0,
            "weighted": array(0, 4, 0, []),
            "key_array": array(0x4000, 8, 2, [4, 5]),
            "value_array": array(0x5000, 4, 2, [0, -2 * Q]),
            "reset_input": {"weighted_count_nonzero": False},
        }
        person = {
            "scope": "current_character",
            "effective_prowess": {"status": "available", "points": 0, "unavailable_reason": None},
            "injury_traits": {
                "status": "available",
                "flags": {key: False for key in (
                    "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
                    "one_eyed", "disfigured", "incapable",
                )},
                "wounded_rank": 0, "wounded_rank_unavailable_reason": None,
                "unavailable_reason": None,
            },
            "raw_numeric_inputs": old_raw,
            "current_stored_context_state": stored,
        }
        frame = {
            "schema_version": 1, "contract_stage": "production_exact_battle_terminal_transition",
            "status": "available", "unavailable_reason": None,
            "battle_terminal_transition_ready": False, "snapshot_revision": 1,
            "observed_date_raw": DATE, "prior_combat_id": -1, "subject_public_cunit_id": -1,
            "terminal_journal": {
                "requested_after_sequence": None, "oldest_available_sequence": 0,
                "latest_sequence": 0, "event_sequence": None, "event_status": "not_observed",
            },
            "prior": None, "removal": None, "subject": None, "successor": None,
            "character_observations": [{
                "character_id": ACTOR, "status": "none", "actual_jailer_character_id": -1,
                "alive": True, "current_person_state": person,
            }],
        }
        query = normalized(frame)
        current = query["character_observations"][0]["current_person_state"]
        self.assertFalse(query["battle_terminal_transition_ready"])
        self.assertEqual(current["raw_numeric_inputs"], old_raw)
        self.assertEqual(current["effective_prowess"]["points"], 0)
        origin = {"snapshot_revision": query["snapshot_revision"],
                  "observed_date_raw": query["observed_date_raw"],
                  "input_kind": "source_conditioned_synthetic_current"}
        projected = project_current_stored_context_state_12003(
            current["current_stored_context_state"], source_provenance=origin,
        )
        self.assertTrue(projected.numeric_context_ready)
        self.assertEqual(projected.character_full_id, ACTOR)
        self.assertEqual(projected.observed_state, stored)
        self.assertEqual(projected.raw_context_projection, {
            "aggregate_properties": {"keys_u16": [4, 5], "values_q64": [0, -2 * Q], "count": 2},
            "weighted_rows": [], "weighted_count": 0,
        })
        reset = projected.reset_input_projection
        self.assertEqual(reset["current_counts_i32"], (0, 2, 2))
        self.assertEqual(reset["direct_after_counts_i32"], (0, 2, 2))
        self.assertFalse(reset["weighted_count_nonzero"])
        self.assertTrue(reset["counts_projection_ready"])
        for field in ("native_reset_called", "cleanup_completion_inferred",
                      "completed_reset_admission_constructed", "historical_stage_inferred"):
            self.assertFalse(reset[field])

        # The existing numerical ingress consumes only the new stored context;
        # old fallback8Q and cached EC0 remain observations, not substitutions.
        numerical_inputs = copy.deepcopy(current["raw_numeric_inputs"])
        numerical_inputs["context"] = projected.raw_context_projection
        numerical_inputs["context_source"] = "model_inline"
        numerical = compute_six_skill_cache_from_native_inputs_12003(numerical_inputs)
        self.assertTrue(numerical.calculation_ready)
        self.assertEqual(numerical.character_id, ACTOR)
        self.assertEqual(numerical.raw_points, (11, 11, 11, 11, 11, 9))
        self.assertEqual(numerical.final_cache_points, (11, 11, 11, 11, 11, 9))
        self.assertEqual(current["raw_numeric_inputs"]["context"]["aggregate_properties"]["values_q64"], [8 * Q])

        # Unequal native header counts are valid independent observations. They
        # are not paired into a fabricated numerical property container.
        unequal_frame = copy.deepcopy(frame)
        unequal_state = unequal_frame["character_observations"][0]["current_person_state"]["current_stored_context_state"]
        unequal_state["value_array"] = array(0x5000, 4, 3, [0, -2 * Q, 99 * Q])
        unequal = project_current_stored_context_state_12003(
            normalized(unequal_frame)["character_observations"][0]["current_person_state"]["current_stored_context_state"],
        )
        self.assertTrue(unequal.observed_state["available"])
        self.assertEqual(unequal.observed_state["key_array"]["count"], 2)
        self.assertEqual(unequal.observed_state["value_array"]["count"], 3)
        self.assertFalse(unequal.numeric_context_ready)
        self.assertIsNone(unequal.raw_context_projection)
        self.assertEqual(unequal.reset_input_projection["direct_after_counts_i32"], (0, 2, 3))

        # Production negative-count shape has available=False, but its actual
        # scalar count still closes the independent !=0 direct reset branch.
        negative_frame = copy.deepcopy(unequal_frame)
        negative_state = negative_frame["character_observations"][0]["current_person_state"]["current_stored_context_state"]
        negative_state.update(available=False, reason="negative_weighted_active_extent",
                              weighted=array(0x6000, 4, -3, None),
                              reset_input={"weighted_count_nonzero": True})
        negative_leaf = normalized(negative_frame)["character_observations"][0]["current_person_state"]["current_stored_context_state"]
        negative = project_current_stored_context_state_12003(negative_leaf)
        self.assertFalse(negative.observed_state["available"])
        self.assertEqual(negative.observed_state["weighted"]["count"], -3)
        self.assertIsNone(negative.observed_state["weighted"]["items"])
        self.assertEqual(negative.observed_state["key_array"]["items"], [4, 5])
        self.assertEqual(negative.observed_state["value_array"]["count"], 3)
        self.assertFalse(negative.numeric_context_ready)
        self.assertIsNone(negative.raw_context_projection)
        self.assertTrue(negative.reset_input_projection["predicate_ready"])
        self.assertTrue(negative.reset_input_projection["counts_projection_ready"])
        self.assertTrue(negative.reset_input_projection["weighted_count_nonzero"])
        self.assertEqual(negative.reset_input_projection["direct_after_counts_i32"], (0, 0, 0))
        self.assertFalse(negative.reset_input_projection["cleanup_completion_inferred"])

        # A real observed owner mismatch survives without replacement by AE0.
        mismatch_frame = copy.deepcopy(frame)
        mismatch_state = mismatch_frame["character_observations"][0]["current_person_state"]["current_stored_context_state"]
        mismatch_state.update(owner_character_full_id=30111, bound_to_requested_character=False)
        mismatch = project_current_stored_context_state_12003(
            normalized(mismatch_frame)["character_observations"][0]["current_person_state"]["current_stored_context_state"],
        )
        self.assertEqual(mismatch.observed_state["owner_character_full_id"], 30111)
        self.assertFalse(mismatch.observed_state["bound_to_requested_character"])
        self.assertTrue(mismatch.numeric_context_ready)
        self.assertEqual(mismatch.raw_context_projection, projected.raw_context_projection)

        OBSERVATIONS.update({
            "input_kind": "source_conditioned_synthetic_current", "character_id": ACTOR,
            "input_frame": origin, "observed_current_EC": 0, "old_fallback_key5_Q": 8,
            "stored_aggregate": projected.raw_context_projection["aggregate_properties"],
            "current_weighted_count": 0, "current_counts": list(reset["current_counts_i32"]),
            "direct_count_projection_with_weighted_zero": list(reset["direct_after_counts_i32"]),
            "modeled_raw_points": list(numerical.raw_points),
            "modeled_final_cache_points": list(numerical.final_cache_points),
            "independent_pair_counts": [2, 3], "unequal_pair_numeric_ready": False,
            "negative_weighted_count": -3, "negative_leaf_available": False,
            "negative_direct_projection_ready": True, "negative_direct_counts": [0, 0, 0],
            "negative_full_numeric_ready": False, "mismatched_owner_id_preserved": 30111,
            "cleanup_completion_inferred": False, "historical_preprefix_inferred": False,
            "old_fallback_replaced": False, "native_write_performed": False,
            "native_EC_parity_claimed": False, "full_future_context_ready": False,
            "Entry_ready": False, "actual_game_days_advanced": 0,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
