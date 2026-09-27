from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    DIPLOMACY_QUERY_STEP,
    parse_player_lifestyle_diplomacy_targets_private_v1,
    query_player_lifestyle_diplomacy_targets_private_v1,
)


def frame() -> dict[str, object]:
    return {
        "paused": True, "snapshot_id": "native:3", "native_revision": 3,
        "date_raw": 53368176, "played_character_id": 36403,
        "episode_run_id": "native-36403-2b4b233056bd",
    }


def response() -> dict[str, object]:
    progress = {
        "presence": "present", "source": "exact_native_getters",
        "xp_total_raw": 500000, "xp_within_level_raw": 500000,
        "xp_per_level": 1000, "unspent_perk_points": 1,
        "used_perk_points": 2,
    }
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": "life-read-1", "ok": True,
        "result": {
            "step": DIPLOMACY_QUERY_STEP, "private_build": True,
            "advertised": False, "read_only": True, "policy_scoped": True,
            "status": "observed", **{key: value for key, value in frame().items()
                                      if key != "paused"},
            "focus": {
                "target_key": "diplomacy_foreign_affairs_focus",
                "status": "observed_native_illegal", "native_legal": False,
                "lifestyle_key": "diplomacy_lifestyle",
                "target_lifestyle_progress": progress,
            },
            "perk": {
                "target_key": "thoughtful_perk",
                "status": "observed_native_legal", "native_legal": True,
                "lifestyle_key": "diplomacy_lifestyle",
                "target_perk_owned": False,
                **{key: progress[key] for key in (
                    "xp_total_raw", "xp_within_level_raw", "xp_per_level",
                    "unspent_perk_points", "used_perk_points")},
            },
        },
    }


def parse(value: dict[str, object], after: dict[str, object] | None = None) -> dict[str, object]:
    return parse_player_lifestyle_diplomacy_targets_private_v1(
        value, expected_request_id="life-read-1", source_frame=frame(),
        independent_after_frame=after or frame(),
    )


class Driver:
    allow_private_lifestyle_formal_trial = True
    command_timeout_seconds = 1.0

    def __init__(self) -> None:
        self.endpoint = self
        self.state = self
        self.last_request: dict[str, object] | None = None

    def take_snapshot(self) -> dict[str, object]:
        return {**frame(), "map_ready": True, "revision": 4,
                "played_character": {"character_id": 36403}}

    def send(self, request: dict[str, object]) -> None:
        self.last_request = request

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        value = response()
        value["request_id"] = request_id
        return value


class DiplomacyTargetObservationTests(unittest.TestCase):
    def test_independent_frame_and_cross_target_progress(self) -> None:
        driver = Driver()
        result = query_player_lifestyle_diplomacy_targets_private_v1(
            driver, expected_revision=4)
        self.assertEqual(result["status"], "observed")
        self.assertIs(result["focus"]["native_legal"], False)
        self.assertIs(result["perk"]["native_legal"], True)
        self.assertEqual(driver.last_request["step"], DIPLOMACY_QUERY_STEP)
        self.assertEqual(driver.last_request["expected_revision"], 3)

    def test_unavailable_progress_is_not_a_zero_point(self) -> None:
        value = response()
        value["result"]["status"] = "unavailable"
        value["result"]["focus"]["target_lifestyle_progress"] = {
            "presence": "unavailable", "reason": "target_native_getters_unavailable",
        }
        self.assertEqual(parse(value)["status"], "source_unavailable")

    def test_drift_and_inconsistent_progress_rejected(self) -> None:
        changed = frame()
        changed["native_revision"] = 4
        self.assertEqual(parse(response(), changed)["status"], "red")
        value = response()
        value["result"]["perk"]["unspent_perk_points"] = 0
        self.assertEqual(parse(value)["status"], "red")


if __name__ == "__main__":
    unittest.main()
