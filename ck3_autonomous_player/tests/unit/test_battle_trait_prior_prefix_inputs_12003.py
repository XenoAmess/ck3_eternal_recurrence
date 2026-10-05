"""One production current-prefix fixture with source-shaped synthetic inputs.

Actor/date/revision anchor the recorded v81 observation, without a new frame.
Native selector outcomes are explicit inputs, not a reimplementation of880430.
"""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
    normalize_battle_terminal_transition_v1,
)
from xar_autoplayer.simulation.battle_trait_context_branch_12003 import (
    compose_current_prior_context_prefix_12003,
)

ACTOR = 29829
DATE = 53262000
REVISION = 3
Q = 100000


def _block(*rows):
    return {"rows": [{"key": key, "value_raw": value} for key, value in rows]}


def _current_prefix():
    return {
        "available": True,
        "reason": None,
        "character_full_id": ACTOR,
        "base_property_block": _block((10, 0)),
        "common_property_blocks": [
            _block((11, -2 * Q)), _block(), _block((0xFFFF, -Q)),
        ],
        "selector": {
            "available": True,
            "uses_18f8_source": True,
            "selected_header_offset": 0x18F8,
        },
        "selected_property_blocks": [_block((12, 3 * Q)), _block()],
    }


def _frame(prefix, *, include_extension=True):
    state = {
        "scope": "current_character",
        "effective_prowess": {
            "status": "available", "points": 8, "unavailable_reason": None,
        },
        "injury_traits": {
            "status": "available",
            "flags": dict.fromkeys((
                "wounded_1", "wounded_2", "wounded_3", "maimed", "one_legged",
                "one_eyed", "disfigured", "incapable",
            ), False),
            "wounded_rank": 0,
            "unavailable_reason": None,
            "wounded_rank_unavailable_reason": None,
        },
    }
    if include_extension:
        state["current_prior_context_inputs"] = prefix
    return {
        "schema_version": 1,
        "contract_stage": BATTLE_TERMINAL_TRANSITION_V1_CONTRACT_STAGE,
        "status": "available", "unavailable_reason": None,
        "battle_terminal_transition_ready": False,
        "snapshot_revision": REVISION, "observed_date_raw": DATE,
        "prior_combat_id": -1, "subject_public_cunit_id": -1,
        "terminal_journal": {
            "requested_after_sequence": None,
            "oldest_available_sequence": 0, "latest_sequence": 0,
            "event_sequence": None, "event_status": "not_observed",
        },
        "prior": None, "removal": None, "subject": None, "successor": None,
        "character_observations": [{
            "character_id": ACTOR, "status": "none",
            "actual_jailer_character_id": -1, "alive": True,
            "current_person_state": state,
        }],
    }


def _normalize(prefix, *, include_extension=True):
    return normalize_battle_terminal_transition_v1(
        _frame(prefix, include_extension=include_extension),
        expected_prior_combat_id=None,
        expected_subject_public_cunit_id=None,
        expected_after_terminal_sequence=None,
        expected_observed_date_raw=DATE,
        expected_snapshot_revision=REVISION,
        expected_character_ids=[ACTOR],
    )


def _person(normalized):
    return normalized["character_observations"][0]["current_person_state"]


def _requests(result):
    return [{
        "source_group": row.source_group,
        "native_index": row.native_index,
        "native_order": row.native_order,
        "weight_q64": row.weight_q64,
        "count": row.properties.count,
        "keys_u16": list(row.properties.keys_u16),
        "values_q64": list(row.properties.values_q64),
    } for row in result.contributions]


class BattleTraitPriorPrefix12003ProductionFixtureTests(unittest.TestCase):
    captured_results = []

    def test_current_observed_selector_prefix_preserves_order_empty_and_partial(self):
        found = _current_prefix()
        before = deepcopy(found)
        normalized = _normalize(found)
        leaf = _person(normalized)["current_prior_context_inputs"]
        self.assertEqual(leaf, found)
        self.assertEqual(normalized["snapshot_revision"], REVISION)
        self.assertEqual(normalized["observed_date_raw"], DATE)
        self.assertFalse(normalized["battle_terminal_transition_ready"])

        result = compose_current_prior_context_prefix_12003(leaf)
        expected = [
            {"source_group": "base", "native_index": 0, "native_order": 0,
             "weight_q64": Q, "count": 1, "keys_u16": [10], "values_q64": [0]},
            {"source_group": "common", "native_index": 0, "native_order": 1,
             "weight_q64": Q, "count": 1, "keys_u16": [11], "values_q64": [-2 * Q]},
            {"source_group": "common", "native_index": 2, "native_order": 3,
             "weight_q64": Q, "count": 1, "keys_u16": [0xFFFF], "values_q64": [-Q]},
            {"source_group": "selected", "native_index": 0, "native_order": 4,
             "weight_q64": Q, "count": 1, "keys_u16": [12], "values_q64": [3 * Q]},
        ]
        self.assertEqual(_requests(result), expected)
        self.assertEqual(result.character_full_id, ACTOR)
        self.assertTrue(result.contributions_ready)
        self.assertTrue(result.ready)
        self.assertEqual(result.status, "computed")
        self.assertEqual(result.missing_inputs, ())
        self.assertEqual(result.ledger["actual_selector_observation"], found["selector"])
        empty_blocks = [row for row in result.ledger["branches"]
                        if row["branch"] == "native_count_zero_skip"]
        self.assertEqual([(row["source_group"], row["native_index"], row["native_order"])
                          for row in empty_blocks], [("common", 1, 2), ("selected", 1, 5)])
        self.assertEqual(found, before)

        # The native caller normalizes return==fresh_end to null, choosing19A0.
        # Only the observed chosen blocks are published/consumed, not both arrays.
        end = deepcopy(found)
        end["selector"].update(uses_18f8_source=False, selected_header_offset=0x19A0)
        end["selected_property_blocks"] = [_block((13, -3 * Q)), _block()]
        end_result = compose_current_prior_context_prefix_12003(
            _person(_normalize(end))["current_prior_context_inputs"])
        expected_end = deepcopy(expected)
        expected_end[-1].update(keys_u16=[13], values_q64=[-3 * Q])
        self.assertEqual(_requests(end_result), expected_end)
        self.assertTrue(end_result.ready)
        self.assertEqual(end_result.ledger["actual_selector_observation"], end["selector"])

        # A zero-length selected source is known empty, not a source failure.
        empty = deepcopy(end)
        empty["selected_property_blocks"] = []
        empty_result = compose_current_prior_context_prefix_12003(
            _person(_normalize(empty))["current_prior_context_inputs"])
        self.assertTrue(empty_result.ready)
        self.assertEqual(_requests(empty_result), expected[:3])

        # Missing block at ordinal2 preserves all known later native indices and
        # requests. It must not be collapsed into a successfully read empty block.
        failed_block = deepcopy(found)
        failed_block["available"] = False
        failed_block["reason"] = "current_common_property_block_read_failed"
        failed_block["common_property_blocks"][1] = None
        partial = compose_current_prior_context_prefix_12003(
            _person(_normalize(failed_block))["current_prior_context_inputs"])
        self.assertFalse(partial.ready)
        self.assertEqual(partial.status, "partial")
        self.assertEqual(_requests(partial), expected)
        self.assertIn("common_property_blocks[1]", partial.missing_inputs)

        old_state = _person(_normalize(None, include_extension=False))
        explicit_null_state = _person(_normalize(None))
        self.assertNotIn("current_prior_context_inputs", old_state)
        self.assertIn("current_prior_context_inputs", explicit_null_state)
        self.assertIsNone(explicit_null_state["current_prior_context_inputs"])
        missing = compose_current_prior_context_prefix_12003(
            explicit_null_state["current_prior_context_inputs"])
        self.assertFalse(missing.ready)
        self.assertEqual(missing.contributions, ())
        self.assertTrue(missing.missing_inputs)

        self.assertFalse(result.full_pre291C204_materialized_context_ready)
        self.assertFalse(result.full_future_context_ready)
        self.assertFalse(result.native_write_performed)
        self.assertEqual(result.actual_game_days_advanced, 0)
        self.assertFalse(result.ledger["aggregate_reconstructed"])
        self.assertFalse(result.ledger["selector_membership_recomputed"])
        self.assertEqual(_person(normalized)["effective_prowess"]["points"], 8)
        self.captured_results.append({
            "character_full_id": ACTOR,
            "source_coordinate_anchor": {"snapshot_revision": REVISION, "observed_date_raw": DATE},
            "found_selector": dict(found["selector"]),
            "found_requests": _requests(result),
            "end_selector": dict(end["selector"]),
            "end_requests": _requests(end_result),
            "empty_selected_ready": empty_result.ready,
            "empty_selected_requests": _requests(empty_result),
            "partial_known_requests_retained": _requests(partial),
            "partial_missing_inputs": list(partial.missing_inputs),
            "legacy_absent_and_explicit_null_distinct": True,
            "null_missing_inputs": list(missing.missing_inputs),
            "current_effective_prowess_preserved": 8,
            "nonempty_ffff_weighted_request_retained": True,
            "actual_880430_calls": 0,
            "operand_provenance": "source-shaped synthetic current native-selector/property-block inputs",
            "new_native_frame": False,
            "full_pre291C204_materialized_context_ready": False,
            "full_future_context_ready": False,
            "Entry_refresh_claimed": False,
        })


if __name__ == "__main__":
    unittest.main()
