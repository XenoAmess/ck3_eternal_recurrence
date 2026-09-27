from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
    MARTIAL_QUERY_STEP,
    parse_player_lifestyle_focus_private_v1,
    query_player_lifestyle_martial_authority_private_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.native_auto_run import _compact_plan


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


class OpeningDriver:
    allow_private_lifestyle_formal_trial = True
    initial_lifestyle_focus_gate_stage = "await_submit"

    def __init__(self) -> None:
        self.martial_calls = 0
        self.focus_presence = "present"
        self.state = {
            **frame(), "revision": 4, "map_ready": True,
            "played_character": {"character_id": 29829},
        }

    def take_snapshot(self) -> dict[str, object]:
        return dict(self.state)

    def query_player_lifestyle_current_state_private_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        assert expected_revision == 4
        return {
            "status": "available",
            "source_frame": {
                "snapshot_id": self.state["snapshot_id"],
                "revision": 4, "native_revision": 3,
                "date_raw": self.state["date_raw"],
                "player_character_id": 29829,
            },
            "snapshot": {
                "readiness": {"current_focus_ready": True,
                              "lifestyle_progress_ready": True},
                "current_focus": (
                    {"presence": "absent"} if self.focus_presence == "absent"
                    else {"presence": "present", "key": "stewardship_wealth_focus",
                          "lifestyle_key": "stewardship_lifestyle"}
                ),
                "current_lifestyle_progress": (
                    {"presence": "absent"} if self.focus_presence == "absent"
                    else {"presence": "present",
                          "lifestyle_key": "stewardship_lifestyle",
                          "xp_total_raw": 58750000,
                          "xp_within_level_raw": 58750000,
                          "xp_per_level": 1000,
                          "unspent_perk_points": 0, "used_perk_points": 7}
                ),
            },
        }

    def query_player_lifestyle_martial_authority_private_v1(
        self, *, expected_revision: int,
    ) -> dict[str, object]:
        assert expected_revision == 4
        self.martial_calls += 1
        return {
            "status": "observed", "native_legal": False,
            "target_key": "martial_authority_focus",
            "target_lifestyle_key": "martial_lifestyle",
            "target_lifestyle_progress": response()["result"]
                                         ["target_lifestyle_progress"],
            "source_frame": {key: self.state.get(key) for key in (
                "snapshot_id", "native_revision", "date_raw",
                "episode_run_id",
            )} | {"played_character_id": 29829},
        }


class OpeningMartialHookTests(unittest.TestCase):
    def test_once_per_episode_report_preserves_action_step(self) -> None:
        driver = OpeningDriver()
        service = GameplayBridgeService(driver)
        planned = {
            "snapshot_id": "native:3", "revision": 4,
            "plan": {"selected_step": "life-advance"},
        }
        with mock.patch.object(service, "_observe_opening_lifestyle_perks_v1",
                               return_value={"status": "observed"}):
            first = service._plan_initial_lifestyle_focus_first_v1(
                planned, {"query-campaign-root-context-v1"})["plan"]
            second = service._plan_initial_lifestyle_focus_first_v1(
                planned, {"query-campaign-root-context-v1"})["plan"]
        self.assertEqual(driver.martial_calls, 1)
        self.assertEqual(first["selected_step"], "query-campaign-root-context-v1")
        self.assertEqual(second["selected_step"], first["selected_step"])
        report = _compact_plan(first)
        self.assertEqual(report["opening_lifestyle_observation"]["status"],
                         "verified_existing")
        martial = report["opening_lifestyle_martial_observation"]
        self.assertEqual(martial["status"], "observed")
        self.assertIs(martial["native_legal"], False)
        self.assertEqual(martial["target_lifestyle_progress"]
                         ["xp_total_raw"], 700000)
        self.assertIs(martial["action_admitted"], False)

    def test_opt_in_off_never_calls_martial_reader(self) -> None:
        driver = OpeningDriver()
        driver.allow_private_lifestyle_formal_trial = False
        service = GameplayBridgeService(driver)
        observation = service._observe_opening_martial_authority_v1(
            before=driver.take_snapshot(), revision=4)
        self.assertIsNone(observation)
        self.assertEqual(driver.martial_calls, 0)

    def test_new_service_after_cold_restore_requeries_same_episode(self) -> None:
        driver = OpeningDriver()
        before = driver.take_snapshot()
        first = GameplayBridgeService(driver)
        self.assertEqual(first._observe_opening_martial_authority_v1(
            before=before, revision=4)["status"], "observed")
        restored = GameplayBridgeService(driver)
        self.assertEqual(restored._observe_opening_martial_authority_v1(
            before=before, revision=4)["status"], "observed")
        self.assertEqual(driver.martial_calls, 2)

    def test_changed_opening_frame_reports_red_without_action(self) -> None:
        driver = OpeningDriver()
        original = driver.query_player_lifestyle_martial_authority_private_v1

        def move_frame(*, expected_revision: int) -> dict[str, object]:
            result = original(expected_revision=expected_revision)
            driver.state["date_raw"] += 1
            return result

        driver.query_player_lifestyle_martial_authority_private_v1 = move_frame
        service = GameplayBridgeService(driver)
        result = service._observe_opening_martial_authority_v1(
            before=driver.take_snapshot(), revision=4)
        self.assertEqual(result, {"status": "red", "issue": "opening_frame_changed"})
        report = _compact_plan({"opening_lifestyle_martial_observation": result})
        self.assertEqual(report["opening_lifestyle_martial_observation"]["issue"],
                         "opening_frame_changed")
        self.assertIs(report["opening_lifestyle_martial_observation"]
                      ["action_admitted"], False)

    def test_focusless_opening_keeps_observation_if_formal_route_missing(self) -> None:
        driver = OpeningDriver()
        driver.focus_presence = "absent"
        service = GameplayBridgeService(driver)
        result = service._plan_initial_lifestyle_focus_first_v1(
            {"snapshot_id": "native:3", "revision": 4,
             "plan": {"selected_step": "life-advance"}},
            {"query-campaign-root-context-v1"},
        )["plan"]
        self.assertIsNone(result["selected_step"])
        self.assertEqual(driver.martial_calls, 1)
        self.assertEqual(_compact_plan(result)
                         ["opening_lifestyle_martial_observation"]["status"],
                         "observed")


if __name__ == "__main__":
    unittest.main()
