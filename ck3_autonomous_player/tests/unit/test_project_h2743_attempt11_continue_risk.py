"""The H2743 receipt projection preserves same-frame and no-action gates."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
SCRIPT = ROOT / "native_bridge/research/project_h2743_attempt11_continue_risk.py"
spec = importlib.util.spec_from_file_location("project_h2743_attempt11_continue_risk", SCRIPT)
assert spec is not None and spec.loader is not None
projector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projector)


def fixture() -> tuple[dict[str, object], dict[str, object]]:
    frame = {"snapshot_id": "native:3", "revision": 4, "native_revision": 3,
             "date_raw": 53217264, "episode_run_id": "native-29829-2bc2d599f7f9",
             "connection_generation": 1}
    digest = "A" * 64
    result = {"status": "baseline_only_material_unavailable", "cleanup_proven": True,
              "gameplay_action_submitted": False, "before_snapshot_sha256": digest,
              "war_id": 16777231, "frame": frame}
    snapshot = {**{key: value for key, value in frame.items() if key != "connection_generation"},
                "diagnostics": {"connection_generation": 1},
                "played_character": {"character_id": 29829},
                "active_wars": [{"war_id": 16777231, "player_side": "defender",
                                 "player_is_primary_war_leader": True,
                                 "primary_opponent_character_id": 30097,
                                 "player_relative_war_score": -12,
                                 "enemy_armies": [{"army_id": 50331920,
                                                   "current_province_id": 2628,
                                                   "army_state": "sieging",
                                                   "siege_province_in_player_subrealm": True,
                                                   "siege_days_left": 1}]}]}
    return result, snapshot


class Attempt11RiskProjectionTests(unittest.TestCase):
    def test_same_frame_siege_timer_is_only_an_estimate(self) -> None:
        result, snapshot = fixture()
        receipt = projector.project(result, snapshot, "A" * 64)
        observation = receipt["observation"]
        self.assertEqual(observation["siege"]["completion_estimate_raw"], 53217288)
        self.assertFalse(observation["siege"]["completion_upper_bound_proven"])
        self.assertEqual(observation["contact"]["status"], "typed_unavailable")
        self.assertIsNone(observation["continuation_loss_upper_raw"])
        self.assertIsNone(observation["action_literal"])

    def test_changed_frame_source_or_siege_fails_closed(self) -> None:
        original_result, original_snapshot = fixture()
        mutations = (
            ({**original_result, "cleanup_proven": False}, original_snapshot, "A" * 64),
            (original_result, original_snapshot, "B" * 64),
            (original_result, {**original_snapshot, "date_raw": 53217288}, "A" * 64),
            (original_result, {**original_snapshot, "active_wars": []}, "A" * 64),
        )
        for result, snapshot, digest in mutations:
            with self.subTest(result=result, digest=digest):
                with self.assertRaises(ValueError):
                    projector.project(result, snapshot, digest)
        snapshot = copy.deepcopy(original_snapshot)
        snapshot["active_wars"][0]["enemy_armies"][0]["siege_days_left"] = None
        with self.assertRaises(ValueError):
            projector.project(original_result, snapshot, "A" * 64)


if __name__ == "__main__":
    unittest.main()
