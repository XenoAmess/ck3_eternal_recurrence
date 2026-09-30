"""No-launch contract for one requested filtered feast guest."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_guest_target_private_transport import (
    SCHEMA, STEP, query_activity_feast_guest_target_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {"snapshot_id": "native:3", "revision": 5,
            "native_revision": 3, "date_raw": 53219928,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def payload(*, status: str = "observed", join: int = 300000,
            arrival: int = 53220000, start: int = 53220100) -> dict[str, object]:
    complete = status in {"observed", "target_not_filtered"}
    member = status == "observed"
    return {
        "schema": SCHEMA, "snapshot_revision": 3,
        "date_raw": 53219928, "actor_character_id": 29829,
        "activity_key": "activity_feast", "planning_stage": 5,
        "status": "observed" if complete else "unavailable",
        "target_status": status, "target_character_id": 43699,
        "selected_status": "observed", "start_gate_status": "observed",
        "normal_refresh_sequence": 7 if complete else None,
        "source_fingerprint": "0x0123456789abcdef" if complete else None,
        "active_rule_count": 3 if complete else None,
        "filtered_group_count": 3 if complete else None,
        "selected_row_count": 0 if complete else None,
        "native_filtered_member": member if complete else None,
        "selected_member": False if complete else None,
        "planner_join_raw": join if member else None,
        "travel_days": 3 if member else None,
        "arrival_raw": arrival if member else None,
        "planned_start_raw": start if member else None,
        "positive_join": join > 0 if member else None,
        "timely_arrival": arrival <= start if member else None,
        "final_can_start": False if complete else None,
        "authored_rule_membership": None,
        "native_guest_route_qualified": False,
        "read_only": True, "advertised": False,
    }


class Driver:
    allow_private_activity_feast_guest_target_query = True

    def __init__(self, native: dict[str, object]) -> None:
        self.native = native
        self.sent: list[dict[str, object]] = []
        self.after = snapshot()
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": STEP, "accepted": True,
                           "status": "available" if self.native["status"] == "observed"
                           else "unavailable", "private_build": True,
                           "read_only": True, "advertised": False,
                           "activity_feast_guest_target": self.native,
                           "backend_id": "native-headless"}}


class TargetReadTest(unittest.TestCase):
    def test_requested_full_id_and_negative_join_stay_observed(self) -> None:
        driver = Driver(payload(join=-1))
        result = query_activity_feast_guest_target_private_v1(
            driver, expected_revision=5, target_character_id=43699)
        self.assertEqual(driver.sent[0]["target_character_id"], 43699)
        self.assertEqual(result["planner_join_raw"], -1)
        self.assertIs(result["positive_join"], False)
        self.assertIs(result["final_can_start"], False)
        self.assertIs(result["native_guest_route_qualified"], False)

    def test_late_and_absent_are_not_unavailable(self) -> None:
        late = query_activity_feast_guest_target_private_v1(
            Driver(payload(arrival=53220200)), expected_revision=5,
            target_character_id=43699)
        self.assertIs(late["timely_arrival"], False)
        absent = query_activity_feast_guest_target_private_v1(
            Driver(payload(status="target_not_filtered")), expected_revision=5,
            target_character_id=43699)
        self.assertEqual(absent["status"], "observed")
        self.assertIs(absent["native_filtered_member"], False)
        self.assertIsNone(absent["planner_join_raw"])

    def test_unavailable_and_bad_full_id_stay_red(self) -> None:
        unavailable = query_activity_feast_guest_target_private_v1(
            Driver(payload(status="native_evaluation_failed")),
            expected_revision=5, target_character_id=43699)
        self.assertEqual(unavailable["status"], "unavailable")
        selected_failed = payload()
        selected_failed["status"] = "unavailable"
        selected_failed["selected_status"] = "guest_source_unavailable"
        for key in (
            "normal_refresh_sequence", "source_fingerprint", "active_rule_count",
            "filtered_group_count", "selected_row_count", "native_filtered_member",
            "selected_member", "planner_join_raw", "travel_days", "arrival_raw",
            "planned_start_raw", "positive_join", "timely_arrival", "final_can_start",
        ):
            selected_failed[key] = None
        independent_red = query_activity_feast_guest_target_private_v1(
            Driver(selected_failed), expected_revision=5, target_character_id=43699)
        self.assertEqual(independent_red["target_status"], "observed")
        self.assertEqual(independent_red["selected_status"], "guest_source_unavailable")
        self.assertEqual(independent_red["status"], "unavailable")
        bad = payload()
        bad["target_character_id"] = 38293
        with self.assertRaises(BridgeUnavailableError):
            query_activity_feast_guest_target_private_v1(
                Driver(bad), expected_revision=5, target_character_id=43699)
        with self.assertRaises(ValueError):
            query_activity_feast_guest_target_private_v1(
                Driver(payload()), expected_revision=5,
                target_character_id=0x10000AAB3)

    def test_default_off_and_frame_change(self) -> None:
        driver = Driver(payload())
        driver.allow_private_activity_feast_guest_target_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_guest_target_private_v1(
                driver, expected_revision=5, target_character_id=43699)
        self.assertEqual(driver.sent, [])
        driver = Driver(payload())
        driver.after["date_raw"] += 1
        with self.assertRaises(BridgeUnavailableError):
            query_activity_feast_guest_target_private_v1(
                driver, expected_revision=5, target_character_id=43699)


if __name__ == "__main__":
    unittest.main()
