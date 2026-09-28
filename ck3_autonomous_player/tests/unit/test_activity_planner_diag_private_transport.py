"""No-launch contract for the default-off paused activity planner diagnostic."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_planner_diag_private_transport import (
    SCHEMA, STEP, query_activity_planner_diag_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "native:4", "revision": 5, "native_revision": 4,
        "date_raw": 53219928, "paused": True, "map_ready": True,
        "played_character": {"character_id": 29829, "alive": True},
    }


def value() -> dict[str, object]:
    return {
        "schema": SCHEMA, "snapshot_revision": 4,
        "date_raw": 53219928, "actor_character_id": 29829,
        "planner_status": "observed", "planner_present": True,
        "widget_attached": False, "widget_visible": False,
        "planning_stage": 2,
        "host_view_activity_key_source": "host_view_current_type",
        "host_view_activity_key": "activity_feast",
        "configured_cost_state": "unknown",
        "final_can_start_state": "unknown",
        "raw_pointer_fields_persisted": False,
    }


class Driver:
    allow_private_activity_planner_diag_query = True

    def __init__(self) -> None:
        self.sent: list[dict[str, object]] = []
        self.reply = value()
        self.after = snapshot()
        self.endpoint = self
        self.state = self

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": STEP, "accepted": True, "status": "available",
                "private_build": True, "read_only": True,
                "advertised": False, "backend_id": "native-headless",
                "activity_planner_diag": self.reply,
            },
        }

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)


class ActivityPlannerDiagPrivateTransportTest(unittest.TestCase):
    def test_closed_window_stays_unknown_cost_and_final_legality(self) -> None:
        driver = Driver()
        result = query_activity_planner_diag_private_v1(driver, expected_revision=5)
        self.assertEqual(result["host_view_activity_key"], "activity_feast")
        self.assertEqual(result["configured_cost_state"], "unknown")
        self.assertEqual(result["final_can_start_state"], "unknown")
        self.assertEqual(len(driver.sent), 1)
        self.assertEqual(driver.sent[0]["step"], STEP)
        self.assertEqual(driver.sent[0]["expected_revision"], 4)

    def test_planner_absent_is_valid_observation(self) -> None:
        driver = Driver()
        driver.reply.update({"planner_status": "planner_absent",
                             "planner_present": False,
                             "planning_stage": None,
                             "host_view_activity_key": None})
        result = query_activity_planner_diag_private_v1(driver, expected_revision=5)
        self.assertEqual(result["planner_status"], "planner_absent")

    def test_rejects_invented_cost_and_crossed_frame(self) -> None:
        driver = Driver()
        driver.reply["configured_cost_state"] = "known"
        with self.assertRaises(BridgeUnavailableError):
            query_activity_planner_diag_private_v1(driver, expected_revision=5)
        driver = Driver()
        driver.after["date_raw"] += 1
        with self.assertRaises(BridgeUnavailableError):
            query_activity_planner_diag_private_v1(driver, expected_revision=5)

    def test_default_off_rejects_before_wire(self) -> None:
        driver = Driver()
        driver.allow_private_activity_planner_diag_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_planner_diag_private_v1(driver, expected_revision=5)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
