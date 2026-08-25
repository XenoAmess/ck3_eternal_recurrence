from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import (
    CK3_FIXED_POINT_SCALE,
    MAX_ARMY_STRENGTH_REQUEST_IDS,
    QUERY_ARMY_STRENGTHS_CAPABILITY,
    QUERY_ARMY_STRENGTHS_STEP,
    army_strength_query_status,
    army_strength_scope,
    is_native_war_step,
    normalize_army_strength_request_ids,
    normalize_army_strengths,
)


def _army(army_id: int) -> dict[str, object]:
    return {"army_id": army_id}


def _scope_snapshot() -> dict[str, object]:
    return {
        "player_armies": [_army(11), _army(15)],
        "active_wars": [
            {
                "war_id": 101,
                "allied_armies": [_army(11), _army(12)],
                "enemy_armies": [_army(13)],
            },
            {
                "war_id": 102,
                "allied_armies": [],
                "enemy_armies": [_army(12), _army(14)],
            },
        ],
    }


def _available_row(
    army_id: int,
    role: str,
    war_ids: list[int],
    *,
    regiment_count: int = 3,
    current: int = 1_200,
    maximum: int = 1_500,
    base_power_raw: int = 180_000_000,
) -> dict[str, object]:
    return {
        "status": "available",
        "army_id": army_id,
        "native_carmy_id": army_id + 1_000,
        "scope_role": role,
        "war_ids": war_ids,
        "regiment_count": regiment_count,
        "current_soldiers": current,
        "maximum_soldiers": maximum,
        "ai_base_power_raw": base_power_raw,
        "ai_base_power_scale": CK3_FIXED_POINT_SCALE,
        "unavailable_reason": None,
    }


def _unavailable_row(
    army_id: int,
    role: str,
    war_ids: list[int],
) -> dict[str, object]:
    return {
        "status": "unavailable",
        "army_id": army_id,
        "native_carmy_id": army_id + 1_000,
        "scope_role": role,
        "war_ids": war_ids,
        "regiment_count": None,
        "current_soldiers": None,
        "maximum_soldiers": None,
        "ai_base_power_raw": None,
        "ai_base_power_scale": CK3_FIXED_POINT_SCALE,
        "unavailable_reason": "regiment_generation_mismatch",
    }


class ArmyStrengthContractTests(unittest.TestCase):
    def test_frozen_capability_and_step_are_native_only(self) -> None:
        self.assertEqual(
            QUERY_ARMY_STRENGTHS_CAPABILITY,
            "game.command.query-army-strengths-v1",
        )
        self.assertEqual(QUERY_ARMY_STRENGTHS_STEP, "query-army-strengths-v1")
        self.assertTrue(is_native_war_step(QUERY_ARMY_STRENGTHS_STEP))

    def test_scope_is_stable_deduplicated_and_relation_derived(self) -> None:
        self.assertEqual(
            army_strength_scope(_scope_snapshot()),
            [
                {"army_id": 11, "scope_role": "player", "war_ids": [101]},
                {"army_id": 15, "scope_role": "player", "war_ids": []},
                {
                    "army_id": 12,
                    "scope_role": "active_war_ally",
                    "war_ids": [101, 102],
                },
                {
                    "army_id": 13,
                    "scope_role": "active_war_enemy",
                    "war_ids": [101],
                },
                {
                    "army_id": 14,
                    "scope_role": "active_war_enemy",
                    "war_ids": [102],
                },
            ],
        )

    def test_request_ids_are_explicit_bounded_and_never_deduplicated(self) -> None:
        self.assertEqual(normalize_army_strength_request_ids([13, 11]), [13, 11])
        invalid = [
            None,
            [],
            [0],
            [-1],
            [True],
            [2**31],
            [11, 11],
            list(range(1, MAX_ARMY_STRENGTH_REQUEST_IDS + 2)),
        ]
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_army_strength_request_ids(value)

    def test_available_zero_is_not_unavailable(self) -> None:
        scope = [{"army_id": 11, "scope_role": "player", "war_ids": []}]
        row = _available_row(
            11,
            "player",
            [],
            regiment_count=0,
            current=0,
            maximum=0,
            base_power_raw=0,
        )
        normalized = normalize_army_strengths([row], expected_scope=scope)
        self.assertEqual(normalized[0]["current_soldiers"], 0)
        self.assertEqual(normalized[0]["ai_base_power_raw"], 0)
        self.assertEqual(army_strength_query_status(normalized), "available")

    def test_partial_requires_atomic_null_aggregates_and_reason(self) -> None:
        scope = [
            {"army_id": 11, "scope_role": "player", "war_ids": [101]},
            {
                "army_id": 13,
                "scope_role": "active_war_enemy",
                "war_ids": [101],
            },
        ]
        rows = [
            _available_row(11, "player", [101]),
            _unavailable_row(13, "active_war_enemy", [101]),
        ]
        normalized = normalize_army_strengths(rows, expected_scope=scope)
        self.assertEqual(army_strength_query_status(normalized), "partial")
        self.assertIsNone(normalized[1]["current_soldiers"])

        partial_value = _unavailable_row(13, "active_war_enemy", [101])
        partial_value["current_soldiers"] = 1
        missing_reason = _unavailable_row(13, "active_war_enemy", [101])
        missing_reason["unavailable_reason"] = None
        for row in (partial_value, missing_reason):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    normalize_army_strengths([row])

    def test_strict_schema_rejects_scope_drift_and_fake_metrics(self) -> None:
        scope = [
            {
                "army_id": 13,
                "scope_role": "active_war_enemy",
                "war_ids": [101],
            }
        ]
        wrong_role = _available_row(13, "active_war_ally", [101])
        wrong_wars = _available_row(13, "active_war_enemy", [102])
        fake_probability = _available_row(13, "active_war_enemy", [101])
        fake_probability["win_probability"] = 0.75
        wrong_scale = _available_row(13, "active_war_enemy", [101])
        wrong_scale["ai_base_power_scale"] = 1
        duplicate = [
            _available_row(13, "active_war_enemy", [101]),
            _available_row(13, "active_war_enemy", [101]),
        ]
        for rows in (
            [wrong_role],
            [wrong_wars],
            [fake_probability],
            [wrong_scale],
            duplicate,
        ):
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    normalize_army_strengths(rows, expected_scope=scope)


if __name__ == "__main__":
    unittest.main()
