from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.war_contract import normalize_armies  # noqa: E402


def _army(
    status: str, count: int | None, route: list[int],
    target: int | None = None,
) -> dict[str, object]:
    return {
        "army_id": 81,
        "owner_character_id": 707,
        "current_province_id": 1,
        "route_province_ids": route,
        "route_read_status": status,
        "route_source_count": count,
        "move_target_observable": target is not None,
        "move_target_province_id": target,
        "controllable": True,
    }


class ArmyRouteReadStatusContractTests(unittest.TestCase):
    def test_valid_empty_is_distinct_from_invalid_header(self) -> None:
        empty = normalize_armies([_army("complete_empty", 0, [])])[0]
        invalid = normalize_armies([_army("invalid_header", None, [])])[0]
        self.assertEqual(empty["route_read_status"], "complete_empty")
        self.assertEqual(empty["route_source_count"], 0)
        self.assertEqual(invalid["route_read_status"], "invalid_header")
        self.assertIsNone(invalid["route_source_count"])

    def test_paused_complete_and_running_target_only_are_distinct(self) -> None:
        full = normalize_armies(
            [_army("complete_nonempty", 3, [4, 5, 3], 3)]
        )[0]
        target_only = normalize_armies(
            [_army("target_only", 3, [], 3)]
        )[0]
        self.assertEqual(len(full["route_province_ids"]), 3)
        self.assertEqual(target_only["route_province_ids"], [])
        self.assertEqual(target_only["route_source_count"], 3)

    def test_inconsistent_status_or_count_fails_closed(self) -> None:
        malformed = (
            _army("complete_empty", 0, [4]),
            _army("complete_nonempty", 3, [4, 3], 3),
            _army("unresolved_entry", 3, [], 3),
            _army("invalid_header", 3, []),
            _army("target_only", 0, [], 3),
        )
        for row in malformed:
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    normalize_armies([row])
        missing_count = _army("complete_empty", 0, [])
        missing_count.pop("route_source_count")
        with self.assertRaises(ValueError):
            normalize_armies([missing_count])
        unhashable_status = _army("invalid_header", None, [])
        unhashable_status["route_read_status"] = {"unexpected": True}
        with self.assertRaises(ValueError):
            normalize_armies([unhashable_status])
        hidden_target = _army("complete_empty", 0, [])
        hidden_target["move_target_province_id"] = 3
        with self.assertRaises(ValueError):
            normalize_armies([hidden_target])


if __name__ == "__main__":
    unittest.main()
