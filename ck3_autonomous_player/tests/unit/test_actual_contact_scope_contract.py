from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.actual_contact_contract import (
    QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY,
    normalize_actual_contact_scope,
    parse_query_actual_contact_scope_step,
    query_actual_contact_scope_step,
)
from xar_autoplayer.bridge.native_driver import _action_steps
from xar_autoplayer.bridge.mcp_server import _ck3_query_actual_contact_scope


def _scope(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "contract_stage": "production_exact_current_province",
        "status": "available",
        "scope_kind": "pre_contact_prediction",
        "snapshot_revision": 17,
        "date_raw": 53176104,
        "subject_army_id": 11,
        "subject_native_carmy_id": 101,
        "subject_owner_character_id": 7,
        "target_province_id": 2585,
        "province_unit_army_ids": [11, 31, 41],
        "province_combat_ids": [51, 71],
        "stored_order_policy": "numeric_full_id",
        "transition_kind": "create_new",
        "selected_combat_id": None,
        "selected_combat_array_index": None,
        "join_side": None,
        "defender_seed_character_id": 19,
        "initiator_is_defender": False,
        "adjacency_kind_raw": 2,
        "loser_excluded_native_carmy_ids": [303],
        "opponent_army_ids": [31, 41],
        "attacker_army_ids": [11],
        "defender_army_ids": [31, 41],
        "actual_contact_scope_ready": True,
        "combat_v3_participant_scope_ready": True,
    }
    value.update(overrides)
    return value


class ActualContactScopeContractTests(unittest.TestCase):
    def normalize(self, value: object) -> dict[str, object]:
        return normalize_actual_contact_scope(
            value,
            expected_subject_army_id=11,
            expected_target_province_id=2585,
            expected_date_raw=53176104,
            expected_snapshot_revision=17,
        )

    def test_step_is_canonical_and_current_province_bound(self) -> None:
        step = query_actual_contact_scope_step(11, 2585)
        self.assertEqual(step, "query-actual-contact-scope-v1-11-at-2585")
        self.assertEqual(
            parse_query_actual_contact_scope_step(step), (11, 2585)
        )
        for malformed in (
            "query-actual-contact-scope-v1-011-at-2585",
            "query-actual-contact-scope-v1-11-at-0",
            "query-actual-contact-scope-v1-11-at-2585-at-7",
            "query-actual-contact-scope-v1-2147483648-at-2585",
        ):
            self.assertIsNone(parse_query_actual_contact_scope_step(malformed))

    def test_create_new_preserves_native_order_and_side_polarity(self) -> None:
        self.assertEqual(self.normalize(_scope()), _scope())
        defender = _scope(
            initiator_is_defender=True,
            attacker_army_ids=[31, 41],
            defender_army_ids=[11],
        )
        self.assertEqual(self.normalize(defender), defender)

        raw_duplicate = _scope(
            opponent_army_ids=[31, 31, 41],
            defender_army_ids=[31, 41],
        )
        self.assertEqual(self.normalize(raw_duplicate), raw_duplicate)

    def test_join_existing_requires_saved_index_and_predicted_join_side(self) -> None:
        join = _scope(
            transition_kind="join_existing",
            selected_combat_id=71,
            selected_combat_array_index=1,
            join_side="defender",
            defender_seed_character_id=None,
            initiator_is_defender=False,
            adjacency_kind_raw=0,
            opponent_army_ids=[],
            attacker_army_ids=[31],
            defender_army_ids=[41, 11],
        )
        self.assertEqual(self.normalize(join), join)
        bad = copy.deepcopy(join)
        bad["selected_combat_array_index"] = 0
        with self.assertRaisesRegex(ValueError, "join projection"):
            self.normalize(bad)
        reordered = copy.deepcopy(join)
        reordered["defender_army_ids"] = [11, 41]
        with self.assertRaisesRegex(ValueError, "join projection"):
            self.normalize(reordered)

    def test_zero_strength_none_clears_seed_and_combat_v3_scope(self) -> None:
        none = _scope(
            transition_kind="none",
            defender_seed_character_id=None,
            adjacency_kind_raw=0,
            opponent_army_ids=[],
            attacker_army_ids=[],
            defender_army_ids=[],
            combat_v3_participant_scope_ready=False,
        )
        self.assertEqual(self.normalize(none), none)
        leaked_seed = copy.deepcopy(none)
        leaked_seed["defender_seed_character_id"] = 19
        with self.assertRaisesRegex(ValueError, "no-transition payload"):
            self.normalize(leaked_seed)

    def test_post_contact_observation_preserves_actual_combat_order(self) -> None:
        observed = _scope(
            scope_kind="post_contact_observation",
            transition_kind="in_combat",
            selected_combat_id=71,
            selected_combat_array_index=1,
            join_side=None,
            defender_seed_character_id=None,
            initiator_is_defender=False,
            adjacency_kind_raw=0,
            loser_excluded_native_carmy_ids=[],
            opponent_army_ids=[],
            attacker_army_ids=[31, 11],
            defender_army_ids=[41],
        )
        self.assertEqual(self.normalize(observed), observed)

        wrong_phase = copy.deepcopy(observed)
        wrong_phase["scope_kind"] = "pre_contact_prediction"
        with self.assertRaisesRegex(ValueError, "phase predicate"):
            self.normalize(wrong_phase)

        missing_subject = copy.deepcopy(observed)
        missing_subject["attacker_army_ids"] = [31]
        with self.assertRaisesRegex(ValueError, "in-combat observation"):
            self.normalize(missing_subject)

    def test_rejects_null_readiness_unsorted_storage_and_forged_sides(self) -> None:
        for field, replacement in (
            ("actual_contact_scope_ready", None),
            ("province_unit_army_ids", [31, 11, 41]),
            ("defender_army_ids", [31, 11]),
            ("snapshot_revision", 18),
        ):
            malformed = _scope()
            malformed[field] = replacement
            with self.assertRaises(ValueError):
                self.normalize(malformed)

    def test_paused_snapshot_advertises_each_current_controllable_scope(self) -> None:
        steps = _action_steps(
            [QUERY_ACTUAL_CONTACT_SCOPE_CAPABILITY],
            player_armies=[
                {
                    "army_id": 11,
                    "current_province_id": 2585,
                    "controllable": True,
                },
                {
                    "army_id": 12,
                    "current_province_id": 3000,
                    "controllable": False,
                },
            ],
            paused=True,
        )
        self.assertEqual(
            steps, ["query-actual-contact-scope-v1-11-at-2585"]
        )

    def test_official_mcp_facade_preserves_scope_and_revision(self) -> None:
        service = Mock()
        service.query_actual_contact_scope.return_value = {
            "actual_contact_scope": _scope()
        }
        result = _ck3_query_actual_contact_scope(
            service, 11, 2585, expected_revision=9
        )
        self.assertEqual(result["actual_contact_scope"]["subject_army_id"], 11)
        service.query_actual_contact_scope.assert_called_once_with(
            11, 2585, expected_revision=9
        )


if __name__ == "__main__":
    unittest.main()
