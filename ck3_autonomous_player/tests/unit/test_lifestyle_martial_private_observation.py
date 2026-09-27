from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    MARTIAL_QUERY_STEP,
    parse_player_lifestyle_focus_private_v1,
    query_player_lifestyle_martial_authority_private_v1,
)


def frame() -> dict[str, object]:
    return {
        "paused": True, "snapshot_id": "native:3", "native_revision": 3,
        "date_raw": 53217264, "played_character_id": 29829,
        "episode_run_id": "native-29829-test",
    }


def response() -> dict[str, object]:
    return {
        "type": "command_result", "protocol_version": 1,
        "request_id": "life-martial-read-1", "ok": True,
        "result": {
            "step": MARTIAL_QUERY_STEP, "private_build": True,
            "advertised": False, "read_only": True, "policy_scoped": True,
            "status": "observed_native_illegal",
            "episode_run_id": frame()["episode_run_id"],
            "snapshot_id": "native:3", "target_key": "martial_authority_focus",
            "native_legal": False, "scanned_database_rows": 23,
            "target_lifestyle_key": "martial_lifestyle",
            "target_lifestyle_progress": {
                "presence": "present", "source": "exact_native_getters",
                "xp_total_raw": 700000, "xp_within_level_raw": 700000,
                "xp_per_level": 1000, "unspent_perk_points": 0,
                "used_perk_points": 0,
            },
        },
    }


def parse(value: dict[str, object], after: dict[str, object] | None = None) -> dict[str, object]:
    return parse_player_lifestyle_focus_private_v1(
        value, expected_request_id="life-martial-read-1", source_frame=frame(),
        independent_after_frame=after or frame(),
        query_step=MARTIAL_QUERY_STEP, target_key="martial_authority_focus",
        lifestyle_key="martial_lifestyle",
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
                "played_character": {"character_id": 29829}}

    def send(self, request: dict[str, object]) -> None:
        self.last_request = request

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        value = response()
        value["request_id"] = request_id
        return value


class MartialTargetObservationTests(unittest.TestCase):
    def test_current_actor_switch_illegal_with_target_progress(self) -> None:
        driver = Driver()
        result = query_player_lifestyle_martial_authority_private_v1(
            driver, expected_revision=4)
        self.assertEqual(result["status"], "observed")
        self.assertIs(result["native_legal"], False)
        self.assertEqual(result["target_lifestyle_progress"]["xp_total_raw"], 700000)
        self.assertEqual(driver.last_request["step"], MARTIAL_QUERY_STEP)
        self.assertEqual(driver.last_request["expected_revision"], 3)

    def test_legal_result_is_observation_not_action(self) -> None:
        value = response()
        value["result"]["status"] = "observed_native_legal"
        value["result"]["native_legal"] = True
        self.assertEqual(parse(value)["status"], "observed")
        self.assertIs(parse(value)["native_legal"], True)

    def test_unavailable_progress_and_frame_drift(self) -> None:
        value = response()
        value["result"]["target_lifestyle_progress"] = {
            "presence": "unavailable", "reason": "target_native_getters_unavailable",
        }
        self.assertEqual(parse(value)["status"], "target_progress_unavailable")
        changed = frame()
        changed["date_raw"] += 1
        self.assertEqual(parse(response(), changed)["status"], "red")

    def test_wrong_target_cannot_be_promoted(self) -> None:
        value = response()
        value["result"]["target_key"] = "stewardship_wealth_focus"
        self.assertEqual(parse(value)["status"], "red")


if __name__ == "__main__":
    unittest.main()
