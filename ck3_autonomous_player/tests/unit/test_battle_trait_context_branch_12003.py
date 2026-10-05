"""One source-conditioned production fixture for the bounded 291D1D0 branch.

The branch operands and pre291C204 materialized context are synthetic. Actor and
observation coordinates reuse the v81 recorded frame; this is not a fresh frame,
native execution, full future context, or an Entry refresh assertion.
"""

from copy import deepcopy
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.simulation.battle_trait_context_branch_12003 import (
    compose_context_branch_12003,
)


ACTOR = 29829
OBSERVED_DATE = 53262000
OBSERVED_REVISION = 3
Q = 100000


def _block(keys, values):
    return {"count": len(keys), "keys_u16": keys, "values_q64": values}


def _branch_inputs():
    return {
        "character_id": ACTOR,
        "flag14": True,
        "selected_index": 2,
        "selected_property_block": _block([10, 11], [0, -2 * Q]),
        "group_counts": [2, 0, -1, 1, 0, 0, 3],
        "group_property_blocks": [
            _block([10, 11], [-Q, 0]), None, None,
            _block([], []), None, None, _block([11], [-Q]),
        ],
        "status": "available",
        "ready": True,
        "unavailable_reason": None,
    }


def _character_frame(branch):
    injury_keys = (
        "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
        "one_eyed", "disfigured", "incapable",
    )
    return {
        "schema_version": 1,
        "contract_stage": BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
        "status": "available",
        "unavailable_reason": None,
        "battle_terminal_transition_ready": False,
        "snapshot_revision": OBSERVED_REVISION,
        "observed_date_raw": OBSERVED_DATE,
        "prior_combat_id": -1,
        "subject_public_cunit_id": -1,
        "terminal_journal": {
            "requested_after_sequence": None,
            "oldest_available_sequence": 0,
            "latest_sequence": 0,
            "event_sequence": None,
            "event_status": "not_observed",
        },
        "prior": None, "removal": None, "subject": None, "successor": None,
        "character_observations": [{
            "character_id": ACTOR,
            "status": "none",
            "actual_jailer_character_id": -1,
            "alive": True,
            "current_person_state": {
                "scope": "current_character",
                "effective_prowess": {
                    "status": "available", "points": 8,
                    "unavailable_reason": None,
                },
                "injury_traits": {
                    "status": "available",
                    "flags": dict.fromkeys(injury_keys, False),
                    "wounded_rank": 0,
                    "unavailable_reason": None,
                    "wounded_rank_unavailable_reason": None,
                },
                "context_branch_inputs": branch,
            },
        }],
    }


def _normalize(branch):
    return normalize_battle_terminal_transition_v1(
        _character_frame(branch),
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=OBSERVED_DATE,
        expected_snapshot_revision=OBSERVED_REVISION,
        expected_character_ids=[ACTOR],
    )


def _leaf(frame):
    return frame["character_observations"][0]["current_person_state"][
        "context_branch_inputs"]


def _rows(result):
    return [{
        "source_label": row.source_label,
        "native_order": row.native_order,
        "weight_q64": row.weight_q64,
        "group_count": row.group_count,
        "count": row.properties.count,
        "keys_u16": list(row.properties.keys_u16),
        "values_q64": list(row.properties.values_q64),
    } for row in result.contributions]


class BattleTraitContextBranch12003ProductionFixtureTests(unittest.TestCase):
    captured_results = []

    def test_prepared_government_branch_preserves_values_order_and_stage_gaps(self):
        # These are actual stage operands in the source domain, supplied by the
        # fixture rather than inferred from current final context or trait name.
        baseline = {
            "aggregate_properties": _block([10, 11], [Q, 3 * Q]),
            "weighted_rows": [{
                "native_index": 0,
                "properties": _block([10, 11], [Q, 3 * Q]),
                "weight_q64": Q,
            }],
            "weighted_count": 1,
        }
        baseline_before = deepcopy(baseline)
        branch = _branch_inputs()
        frame = _normalize(branch)
        leaf = _leaf(frame)
        self.assertEqual(leaf, branch)
        self.assertEqual(frame["snapshot_revision"], OBSERVED_REVISION)
        self.assertEqual(frame["observed_date_raw"], OBSERVED_DATE)
        self.assertFalse(frame["battle_terminal_transition_ready"])
        self.assertEqual(frame["character_observations"][0]["character_id"], ACTOR)

        projected = compose_context_branch_12003(leaf, prior_context=baseline)
        expected_rows = [
            {"source_label": "selected", "native_order": 0, "weight_q64": Q,
             "group_count": None, "count": 2, "keys_u16": [10, 11],
             "values_q64": [0, -2 * Q]},
            {"source_label": "group0", "native_order": 1, "weight_q64": 2 * Q,
             "group_count": 2, "count": 2, "keys_u16": [10, 11],
             "values_q64": [-Q, 0]},
            {"source_label": "group6", "native_order": 7, "weight_q64": 3 * Q,
             "group_count": 3, "count": 1, "keys_u16": [11],
             "values_q64": [-Q]},
        ]
        self.assertEqual(_rows(projected), expected_rows)
        self.assertEqual(projected.character_id, ACTOR)
        self.assertTrue(projected.contributions_ready)
        self.assertEqual(projected.missing_inputs, ())
        self.assertEqual(projected.status, "computed")
        self.assertTrue(projected.context_combination_ready)
        aggregate = projected.combined_context.aggregate_properties
        # Q + (0*1) + (-Q*2) = -Q; 3Q + (-2Q*1) + 0 - Q*3 = -2Q.
        self.assertEqual(aggregate.keys_u16, (10, 11))
        self.assertEqual(aggregate.values_q64, (-Q, -2 * Q))
        self.assertEqual(projected.combined_context.weighted_count, 4)
        self.assertEqual(baseline, baseline_before)
        branches = {row["source_label"]: row for row in projected.ledger["branches"]}
        self.assertEqual(branches["group2"]["branch"], "count_nonpositive_skip")
        self.assertEqual(branches["group2"]["group_count"], -1)
        self.assertEqual(branches["group3"]["branch"], "property_empty_skip")

        absent_stage = compose_context_branch_12003(leaf)
        self.assertEqual(_rows(absent_stage), expected_rows)
        self.assertTrue(absent_stage.contributions_ready)
        self.assertIsNone(absent_stage.combined_context)
        self.assertFalse(absent_stage.context_combination_ready)
        self.assertEqual(absent_stage.context_missing_inputs,
                         ("prior_context_pre291C204",))

        # Initial government false does not imply the fresh per-record getters
        # were false. The independently prepared positive counts remain active.
        later_government = deepcopy(branch)
        later_government.update(flag14=False, selected_index=None,
                                selected_property_block=None)
        no_selected = compose_context_branch_12003(_leaf(_normalize(later_government)))
        self.assertTrue(no_selected.contributions_ready)
        self.assertEqual(_rows(no_selected), expected_rows[1:])

        # Unsupported source categories have no native clamp/skip branch. The
        # producer marks its seven counters unknown while preserving selection.
        category_gap = deepcopy(branch)
        category_gap.update(
            group_counts=[None] * 7, group_property_blocks=[None] * 7,
            status="partial", ready=False,
            unavailable_reason="context_branch_category_outside_0_6",
        )
        gap_leaf = _leaf(_normalize(category_gap))
        partial = compose_context_branch_12003(gap_leaf)
        self.assertEqual(_rows(partial), expected_rows[:1])
        self.assertFalse(partial.contributions_ready)
        self.assertEqual(partial.status, "partial")
        self.assertEqual(partial.missing_inputs,
                         tuple(f"group_counts[{i}]" for i in range(7)))
        self.assertEqual(gap_leaf["group_counts"], [None] * 7)
        self.assertEqual(gap_leaf["unavailable_reason"],
                         "context_branch_category_outside_0_6")

        # Reading/contribution composition never promotes Entry/future readiness.
        self.assertFalse(projected.native_write_performed)
        self.assertFalse(projected.full_future_context_ready)
        self.assertEqual(projected.actual_game_days_advanced, 0)
        self.assertEqual(frame["character_observations"][0]["current_person_state"][
            "effective_prowess"]["points"], 8)
        self.captured_results.append({
            "character_id": ACTOR,
            "source_coordinate": {"snapshot_revision": OBSERVED_REVISION,
                                  "observed_date_raw": OBSERVED_DATE},
            "current_effective_prowess_preserved": 8,
            "ordered_contributions": expected_rows,
            "combined_aggregate_keys_u16": list(aggregate.keys_u16),
            "combined_aggregate_values_q64": list(aggregate.values_q64),
            "combined_weighted_count": projected.combined_context.weighted_count,
            "absent_prior_stage_missing": list(absent_stage.context_missing_inputs),
            "initial_false_group_labels": [r.source_label for r in no_selected.contributions],
            "unsupported_category_known_selection_retained": _rows(partial),
            "unsupported_category_missing": list(partial.missing_inputs),
            "operand_provenance": "synthetic source-conditioned prepared inputs",
            "new_native_frame": False,
            "full_future_context_ready": False,
            "Entry_refresh_claimed": False,
            "native_collector_counter_wrap_executed": False,
        })


if __name__ == "__main__":
    unittest.main()
