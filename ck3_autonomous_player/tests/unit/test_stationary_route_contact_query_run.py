from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.stationary_route_contact_query_run import (
    QUERY_STEP,
    _exact_h3928_paused_subject,
    _exact_one_appended_query,
    _same_frame,
)


def _snapshot() -> dict[str, object]:
    return {
        "paused": True,
        "map_ready": True,
        "date_raw": 53219928,
        "episode_run_id": "native-29829-2bc2d599f7f9",
        "played_character": {"character_id": 29829, "alive": True},
        "episode_character_id": 29829,
        "route_contact_horizon_supported": True,
        "player_armies": [{
            "army_id": 83886367,
            "controllable": True,
            "current_province_id": 2610,
            "move_target_province_id": None,
            "route_province_ids": [],
            "army_state": "regular",
            "in_combat": False,
            "retreating": False,
        }],
        "active_wars": [{
            "war_id": 16777231,
            "enemy_armies": [
                {"army_id": 50331920, "retreating": False},
                {"army_id": 83886484, "retreating": False},
            ],
        }],
    }


class StationaryRouteContactReadOnlyTests(unittest.TestCase):
    def test_readiness_and_snapshot_connection_generation_match(self) -> None:
        frame = {
            "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
            "date_raw": 53219928, "paused": True, "map_ready": True,
            "episode_run_id": "native-29829-2bc2d599f7f9",
        }
        readiness = {**frame, "connection_generation": 1}
        snapshot = {**frame, "diagnostics": {"connection_generation": 1}}
        self.assertTrue(_same_frame(readiness, snapshot))
        snapshot["diagnostics"]["connection_generation"] = 2
        self.assertFalse(_same_frame(readiness, snapshot))

    def test_fixed_query_and_exact_stationary_scope(self) -> None:
        self.assertEqual(
            QUERY_STEP,
            "query-route-contact-horizon-v1-83886367-to-2610-h-2-50331920-83886484",
        )
        self.assertTrue(_exact_h3928_paused_subject(_snapshot()))
        for field, value in (
            ("date_raw", 53219952),
            ("route_contact_horizon_supported", False),
            ("episode_run_id", "different"),
        ):
            wrong = _snapshot()
            wrong[field] = value
            self.assertFalse(_exact_h3928_paused_subject(wrong))
        moving = _snapshot()
        moving["player_armies"][0]["route_province_ids"] = [2614]
        self.assertFalse(_exact_h3928_paused_subject(moving))
        incomplete = _snapshot()
        incomplete["active_wars"][0]["enemy_armies"].pop()
        self.assertFalse(_exact_h3928_paused_subject(incomplete))

    def test_exactly_one_matching_query_row_is_required(self) -> None:
        before = {"native_command_history": [{"command": "restore-checkpoint"}]}
        result = {"step": QUERY_STEP, "accepted": True}
        after = copy.deepcopy(before)
        after["native_command_history"].append({
            "command": QUERY_STEP, "ok": True, "result": result,
        })
        self.assertTrue(_exact_one_appended_query(before, after, result))
        after["native_command_history"].append({
            "command": "advance-route-contact-horizon-v1-...", "ok": True,
        })
        self.assertFalse(_exact_one_appended_query(before, after, result))


if __name__ == "__main__":
    unittest.main()
