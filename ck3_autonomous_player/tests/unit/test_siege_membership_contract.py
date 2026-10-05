"""Offline fixtures for the actual Province membership identity wire."""
from __future__ import annotations

import unittest

from xar_autoplayer.bridge.siege_membership_contract import (
    normalize_siege_province_unit_occurrences,
)
from xar_autoplayer.bridge.war_contract import (
    normalize_objective_province_states,
    normalize_province_local_siege_result,
    query_province_local_siege_step,
)
from xar_autoplayer.bridge.war_occupation_targets_contract import (
    normalize_war_occupation_targets_v1,
)


def siege() -> dict[str, object]:
    return {
        "siege_id": 486539314,
        "besieging_army_id": 184549452,
        "player_army_besieging": True,
        "progress_fraction": {"raw": 44145, "scale": 100000},
        "current_work": {"raw": 24279868, "scale": 100000},
        "total_work": {"raw": 55000000, "scale": 100000},
        "days_left": 319,
        "eligible_regiment_siege_work": {"raw": 85800, "scale": 100000},
        "highest_eligible_siege_tier": 0,
        "province_unit_occurrences": [
            {"occurrence_index": 0, "public_unit_id": 0, "native_carmy_id": 0,
             "eligible": True, "qualified_regiment_ids": []},
            {"occurrence_index": 1, "public_unit_id": 268435481, "native_carmy_id": 100,
             "eligible": True, "qualified_regiment_ids": [184549917, 184549917]},
            {"occurrence_index": 2, "public_unit_id": 101, "native_carmy_id": 102,
             "eligible": False, "qualified_regiment_ids": []},
            {"occurrence_index": 3, "public_unit_id": 268435481, "native_carmy_id": 100,
             "eligible": True, "qualified_regiment_ids": [184549917, 184549917]},
            {"occurrence_index": 4, "public_unit_id": 103, "native_carmy_id": None,
             "eligible": None, "qualified_regiment_ids": None},
        ],
    }


def objective() -> dict[str, object]:
    return {
        "province_id": 3711, "occupation_observable": True,
        "is_occupied": False, "occupying_character_id": None,
        "fort_level": 6, "garrison_size": 500, "besieging_strength": 2883,
        "siege_observable": True, "active_siege": siege(),
    }


def occupation() -> dict[str, object]:
    row = objective()
    row.update(
        holding_title_id=1352, county_title_id=1351,
        legal_holder_character_id=32309, territory_side="defender",
        occupier_side="none", counted_occupied_by_opposing_side=False,
    )
    return {
        "schema": "xar.ck3.war-occupation-targets.v1", "schema_version": 1,
        "game_version": "1.20.0.3",
        "executable_sha256": "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6",
        "available": True, "status": "available", "collection_complete": True,
        "unavailable_reason": None, "war_id": 117440524,
        "actor_character_id": 29829, "player_side": "attacker",
        "primary_attacker_character_id": 29829,
        "primary_defender_character_id": 32309,
        "snapshot_revision": 140, "date_raw": 53265168,
        "side_counts": [
            {"territory_side": side, "eligible": 1, "occupied": 0,
             "native_candidate_count": 1, "collection_complete": True}
            for side in ("attacker", "defender")
        ],
        "rows": [row],
    }


def normalize_occupation(value: dict[str, object]) -> dict[str, object]:
    return normalize_war_occupation_targets_v1(
        value, expected_war_id=117440524, expected_actor_character_id=29829,
        expected_snapshot_revision=140, expected_date_raw=53265168,
        expected_player_side="attacker",
    )


class SiegeMembershipContractTests(unittest.TestCase):
    def test_occurrences_survive_objective_local_and_occupation_paths(self) -> None:
        state = objective()
        expected = state["active_siege"]["province_unit_occurrences"]
        result = normalize_objective_province_states([state], objective_province_ids=[3711])
        self.assertEqual(result[0]["active_siege"]["province_unit_occurrences"], expected)
        step = query_province_local_siege_step(3711)
        local = normalize_province_local_siege_result({
            "step": step, "accepted": True, "status": "available", "query_sequence": 1,
            "snapshot_revision": 140, "date_raw": 53265168,
            "province_state": state, "backend_id": "native-headless",
        }, expected_step=step, expected_province_id=3711,
           expected_snapshot_revision=140, expected_date_raw=53265168)
        self.assertEqual(local["province_state"]["active_siege"]["province_unit_occurrences"], expected)
        rich = normalize_occupation(occupation())["rows"][0]["active_siege"]
        self.assertEqual(rich["province_unit_occurrences"], expected)
        self.assertEqual(rich["highest_eligible_siege_tier"], 0)
        self.assertEqual(rich["eligible_regiment_siege_work"], {"raw": 85800, "scale": 100000})

    def test_legacy_absence_unreadable_null_empty_and_qualified_empty_stay_distinct(self) -> None:
        for value in (None, []):
            raw = occupation()
            raw["rows"][0]["active_siege"]["province_unit_occurrences"] = value
            actual = normalize_occupation(raw)["rows"][0]["active_siege"]
            self.assertEqual(actual["province_unit_occurrences"], value)
        raw = occupation()
        del raw["rows"][0]["active_siege"]["province_unit_occurrences"]
        self.assertNotIn("province_unit_occurrences", normalize_occupation(raw)["rows"][0]["active_siege"])
        row = {"occurrence_index": 0, "public_unit_id": 0, "native_carmy_id": 0,
               "eligible": True, "qualified_regiment_ids": None}
        self.assertEqual(normalize_siege_province_unit_occurrences([row], name="fixture"), [row])
        row["qualified_regiment_ids"] = []
        self.assertEqual(normalize_siege_province_unit_occurrences([row], name="fixture"), [row])

    def test_typed_identity_and_qualification_errors_reach_rich_consumer(self) -> None:
        mutations = [
            ("occurrence_index", True), ("occurrence_index", 1),
            ("public_unit_id", True), ("native_carmy_id", -1),
            ("native_carmy_id", None), ("eligible", 1),
            ("qualified_regiment_ids", [True]),
            ("qualified_regiment_ids", [2**31]),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                raw = occupation()
                raw["rows"][0]["active_siege"]["province_unit_occurrences"][0][field] = value
                with self.assertRaises(ValueError):
                    normalize_occupation(raw)
        for eligible in (False, None):
            raw = occupation()
            row = raw["rows"][0]["active_siege"]["province_unit_occurrences"][1]
            row["eligible"] = eligible
            with self.assertRaises(ValueError):
                normalize_occupation(raw)


if __name__ == "__main__":
    unittest.main()
