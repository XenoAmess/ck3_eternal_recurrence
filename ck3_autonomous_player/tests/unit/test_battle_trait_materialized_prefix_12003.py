"""One source-conditioned materialized prefix case; no native writes or parity claim."""
from __future__ import annotations

import json
import unittest

from xar_autoplayer.simulation.battle_trait_context_branch_12003 import (
    compose_current_prior_context_prefix_12003,
    from_current_prior_context_inputs_12003,
)
from xar_autoplayer.simulation.battle_trait_materialized_prefix_12003 import (
    materialize_current_prior_context_prefix_12003,
)
from xar_autoplayer.simulation.battle_trait_numeric_inputs_12003 import (
    compute_six_skill_cache_from_native_inputs_12003,
)

Q = 100000
OBSERVATIONS = {}


def block(*rows):
    return {"rows": [{"key": key, "value_raw": value} for key, value in rows]}


class BattleTraitMaterializedPrefix12003Tests(unittest.TestCase):
    def test_materialized_prefix_changes_six_skill_input(self):
        # Source-shaped synthetic operands, anchored to an original observed
        # identity. These values are not a fresh native frame or a native pair.
        actor = 29829
        source = {
            "character_id": actor,
            "snapshot_revision": 3,
            "observed_date_raw": 53262000,
            "provenance": "synthetic_operands_with_original_observation_anchor",
        }
        prior_leaf = {
            "available": True,
            "reason": None,
            "character_full_id": actor,
            "base_property_block": block((5, 0), (0xFFFF, 7 * Q)),
            "common_property_blocks": [
                block((5, -2 * Q), (7, 0)),
                block(),
                block((4, -Q), (5, 6 * Q), (0xFFFF, 99 * Q)),
            ],
            "selector": {
                "available": True,
                "uses_18f8_source": True,
                "selected_header_offset": 0x18F8,
            },
            "selected_property_blocks": [],
        }
        prefix = compose_current_prior_context_prefix_12003(
            from_current_prior_context_inputs_12003(prior_leaf, source_provenance=source)
        )
        self.assertTrue(prefix.contributions_ready)
        self.assertEqual(prefix.character_full_id, actor)
        self.assertEqual([row.native_order for row in prefix.contributions], [0, 1, 3])

        # Cleanup is explicitly admitted. Pre-reset count effects alone do not
        # prove this state; unknown physical capacities do not block logical data.
        completed_reset = {
            "admitted_completed": True,
            "active_counts": (0, 0, 0),
            "source_provenance": {
                **source,
                "model_stage": "explicit_completed_reset_logical_empty",
                "native_cleanup_completion_observed": False,
            },
            "storage_diagnostics": None,
        }
        materialized = materialize_current_prior_context_prefix_12003(
            prefix,
            completed_reset_state=completed_reset,
            pre_reset_counts=(1, 7, 7),
        )
        self.assertTrue(materialized.materialized_prefix_ready)
        self.assertEqual(materialized.missing_inputs, ())
        context = materialized.raw_context_projection
        self.assertIsNotNone(context)
        # First empty-destination copy preserves FFFF. Subsequent nonempty folds
        # skip that row, so 99Q never changes the original 7Q sentinel value.
        # Existing key5 merges -2Q+6Q; new key7 retains zero, and key4 inserts -Q.
        self.assertEqual(context["aggregate_properties"], {
            "keys_u16": [4, 5, 7, 0xFFFF],
            "values_q64": [-Q, 4 * Q, 0, 7 * Q],
            "count": 4,
        })
        self.assertEqual(context["weighted_count"], 3)
        self.assertEqual(
            [row["properties"]["keys_u16"] for row in context["weighted_rows"]],
            [[5, 0xFFFF], [5, 7], [4, 5, 0xFFFF]],
        )
        self.assertEqual(
            [row["properties"]["values_q64"] for row in context["weighted_rows"]],
            [[0, 7 * Q], [-2 * Q, 0], [-Q, 6 * Q, 99 * Q]],
        )
        self.assertEqual([row["weight_q64"] for row in context["weighted_rows"]], [Q] * 3)

        # Published numerical ingress consumes the actual writer output. It must
        # not sum the aggregate and retained weighted requests twice.
        raw_inputs = {
            "status": "available",
            "raw_numeric_inputs_ready": True,
            "character_id": actor,
            "context_source": "model_inline",
            "unavailable_reason": None,
            "base_points": [6, 6, 6, 6, 6, 6],
            "caps": [77, 79, 81, 83, 85, 120],
            "prowess_adjustment": 0,
            "scratch_present": True,
            "category_counts": [0, 0, 0, 0],
            "scratch_factor_numerator": 0,
            "scratch_factor_denominator": 1,
            "context": context,
        }
        numerical = compute_six_skill_cache_from_native_inputs_12003(raw_inputs)
        self.assertTrue(numerical.calculation_ready)
        self.assertEqual(numerical.missing_inputs, ())
        self.assertEqual(numerical.character_id, actor)
        self.assertEqual(numerical.raw_points, (6, 6, 6, 6, 5, 10))
        self.assertEqual(numerical.final_cache_points, (6, 6, 6, 6, 5, 10))
        self.assertEqual(raw_inputs["base_points"][5], 6)
        self.assertEqual(source["observed_date_raw"], 53262000)

        # The same requested production prefix cannot become a complete state
        # merely because the direct pre-reset stores would clear all counts.
        not_admitted = materialize_current_prior_context_prefix_12003(
            prefix,
            completed_reset_state={**completed_reset, "admitted_completed": False},
            pre_reset_counts=(1, 7, 7),
        )
        self.assertFalse(not_admitted.materialized_prefix_ready)
        self.assertIsNone(not_admitted.raw_context_projection)
        self.assertTrue(not_admitted.missing_inputs)

        OBSERVATIONS.update({
            "character_id": actor,
            "original_source_anchor": source,
            "input_kind": "source_conditioned_synthetic",
            "prefix_native_orders": [0, 1, 3],
            "materialized_aggregate": context["aggregate_properties"],
            "retained_weighted_count": context["weighted_count"],
            "modeled_raw_points": list(numerical.raw_points),
            "modeled_final_cache_points": list(numerical.final_cache_points),
            "affected_prowess_base": 6,
            "affected_prowess_from_materialized_prefix": 10,
            "pre_reset_count_clear_without_cleanup_admission_ready": False,
            "observed_current_EC_reference": 8,
            "observed_current_EC_replaced": False,
            "native_materialized_context_observed": False,
            "native_write_performed": False,
            "physical_allocator_parity": False,
            "full_future_context_ready": False,
            "Entry_cache_timing_ready": False,
            "fresh_native_frame_created": False,
            "actual_game_days_advanced": 0,
        })
        print(json.dumps(OBSERVATIONS, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
