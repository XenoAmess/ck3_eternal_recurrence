"""No-launch native feast guest candidate read contract."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_guest_candidate_private_transport import (
    SCHEMA, STEP, query_activity_feast_guest_candidate_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {"snapshot_id": "native:3", "revision": 5,
            "native_revision": 3, "date_raw": 53219928,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def payload(status: str = "observed") -> dict[str, object]:
    found = status == "observed"
    complete = found or status == "no_qualified_candidate"
    return {
        "schema": SCHEMA, "snapshot_revision": 3,
        "date_raw": 53219928, "actor_character_id": 29829,
        "activity_key": "activity_feast", "planning_stage": 5,
        "status": status,
        "normal_refresh_sequence": 7 if complete else None,
        "source_fingerprint": "0x0123456789abcdef" if complete else None,
        "native_filtered_pre_invitation": True if found else False if complete else None,
        "candidate": {
            "character_id": 32716, "planner_join_raw": 75000,
            "travel_days": 3, "arrival_raw": 53219976,
            "planned_start_raw": 53220000,
        } if found else None,
        "read_only": True, "raw_pointer_fields_persisted": False,
    }


class Driver:
    allow_private_activity_feast_guest_candidate_query = True

    def __init__(self, native: dict[str, object]) -> None:
        self.native = native
        self.sent: list[dict[str, object]] = []
        self.after = snapshot()
        self.ok = True
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        status = self.native["status"]
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": self.ok,
            "error": "native_guest_frame_changed" if not self.ok else None,
            "result": {
                "step": STEP, "accepted": True,
                "status": "available" if status in {
                    "observed", "no_qualified_candidate"} else "unavailable",
                "private_build": True, "read_only": True,
                "advertised": False,
                "activity_feast_guest_candidate": self.native,
                "backend_id": "native-headless",
            } if self.ok else None,
        }


class GuestCandidateReadTest(unittest.TestCase):
    def test_candidate_is_only_pre_invitation_and_bound_to_paused_frame(self) -> None:
        driver = Driver(payload())
        result = query_activity_feast_guest_candidate_private_v1(
            driver, expected_revision=5)
        self.assertEqual(driver.sent[0], {
            "type": "execute_step", "protocol_version": 1,
            "request_id": driver.sent[0]["request_id"],
            "step": STEP, "expected_revision": 3,
            "expected_date_raw": 53219928,
            "expected_actor_character_id": 29829,
            "expected_planning_stage": 5,
            "expected_activity_key": "activity_feast",
        })
        self.assertEqual(result["candidate"]["character_id"], 32716)
        self.assertIs(result["native_filtered_pre_invitation"], True)
        self.assertNotIn("final_invite_legal", result)
        self.assertNotIn("start_ready", result)
        driver.native["candidate"]["character_id"] = 1
        self.assertEqual(result["candidate"]["character_id"], 32716)

    def test_complete_empty_is_distinct_from_typed_unavailable(self) -> None:
        empty = query_activity_feast_guest_candidate_private_v1(
            Driver(payload("no_qualified_candidate")), expected_revision=5)
        self.assertEqual(empty["status"], "no_qualified_candidate")
        self.assertIs(empty["native_filtered_pre_invitation"], False)
        self.assertIsNone(empty["candidate"])
        unavailable = query_activity_feast_guest_candidate_private_v1(
            Driver(payload("candidate_source_unavailable")), expected_revision=5)
        self.assertEqual(unavailable["status"], "candidate_source_unavailable")
        self.assertIsNone(unavailable["native_filtered_pre_invitation"])
        self.assertIsNone(unavailable["normal_refresh_sequence"])

    def test_unknown_or_malformed_status_is_red_not_empty(self) -> None:
        with self.assertRaisesRegex(BridgeUnavailableError, "status unknown"):
            query_activity_feast_guest_candidate_private_v1(
                Driver(payload("unknown")), expected_revision=5)
        bad = payload("no_qualified_candidate")
        bad["candidate"] = payload()["candidate"]
        with self.assertRaisesRegex(BridgeUnavailableError, "empty result malformed"):
            query_activity_feast_guest_candidate_private_v1(
                Driver(bad), expected_revision=5)
        bad = payload("arrival_unavailable")
        bad["native_filtered_pre_invitation"] = False
        with self.assertRaisesRegex(BridgeUnavailableError, "unavailable result malformed"):
            query_activity_feast_guest_candidate_private_v1(
                Driver(bad), expected_revision=5)

    def test_default_off_native_red_and_changed_frame(self) -> None:
        driver = Driver(payload())
        driver.allow_private_activity_feast_guest_candidate_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_guest_candidate_private_v1(
                driver, expected_revision=5)
        self.assertEqual(driver.sent, [])
        driver = Driver(payload())
        driver.ok = False
        with self.assertRaisesRegex(BridgeUnavailableError, "frame_changed"):
            query_activity_feast_guest_candidate_private_v1(
                driver, expected_revision=5)
        driver = Driver(payload())
        driver.after["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed paused frame"):
            query_activity_feast_guest_candidate_private_v1(
                driver, expected_revision=5)


if __name__ == "__main__":
    unittest.main()
