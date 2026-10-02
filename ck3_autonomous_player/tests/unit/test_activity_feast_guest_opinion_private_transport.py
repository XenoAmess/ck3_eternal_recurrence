"""No-launch contract for the arbitrary feast guest opinion read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest
import json
import os

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_guest_opinion_private_transport import (
    SCHEMA, STEP, query_activity_feast_guest_opinion_private_v1,
    parse_activity_feast_guest_opinion_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {"snapshot_id": "native:3", "revision": 5,
            "native_revision": 3, "date_raw": 10000,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 31000, "alive": True}}


def payload(status: str = "observed") -> dict[str, object]:
    return {
        "schema": SCHEMA, "snapshot_revision": 3,
        "date_raw": 10000, "actor_character_id": 31000,
        "guest_character_id": 32000, "status": status,
        "guest_opinion_of_actor": -25 if status == "observed" else None,
        "read_only": True, "raw_pointer_fields_persisted": False,
    }


class Driver:
    allow_private_activity_feast_guest_opinion_query = True

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
        return {
            "type": "command_result", "protocol_version": 1,
            "request_id": request_id, "ok": True,
            "result": {
                "step": STEP, "accepted": True,
                "status": "available" if self.native["status"] == "observed"
                          else "unavailable",
                "private_build": True, "read_only": True,
                "advertised": False,
                "activity_feast_guest_opinion": self.native,
                "backend_id": "native-headless",
            },
        }


class GuestOpinionReadTest(unittest.TestCase):
    def test_actual_production_named_reader_and_serializer_wire(self) -> None:
        wire_path = os.environ.get("XAR_FEAST_REWARD_FIXTURE_WIRE")
        if wire_path is None:
            self.skipTest("production native named-reader wire fixture is not configured")
        wire = json.loads(Path(wire_path).read_text(encoding="utf-8"))
        for name, native in wire.items():
            with self.subTest(case=name):
                parsed = parse_activity_feast_guest_opinion_private_v1(
                    native, native_revision=4, date_raw=10000,
                    actor_id=31000, guest_id=32000, envelope_status="available")
                self.assertEqual(parsed["guest_opinion_of_actor"], -25)
                self.assertNotIn("attendance_verified", parsed)
                self.assertNotIn("benefit_verified", parsed)
        modifiers = wire["absent_and_zero"]["reward_opinion_modifiers"]
        self.assertEqual(modifiers["hosted_feast_opinion"],
                         {"status": "observed", "present": False, "value": None})
        self.assertEqual(modifiers["impressed_opinion"],
                         {"status": "observed", "present": True, "value": 0})
        failed = wire["missing_definition"]["reward_opinion_modifiers"]
        self.assertEqual(failed["hosted_mediocre_feast_opinion"],
                         {"status": "read_failed", "present": None, "value": None})
        self.assertEqual(failed["impressed_opinion"]["status"], "observed")
        invalid = deepcopy(wire["missing_definition"])
        invalid["reward_opinion_modifiers"]["hosted_mediocre_feast_opinion"]["present"] = False
        with self.assertRaisesRegex(BridgeUnavailableError, "failure malformed"):
            parse_activity_feast_guest_opinion_private_v1(
                invalid, native_revision=4, date_raw=10000,
                actor_id=31000, guest_id=32000, envelope_status="available")

    def test_negative_opinion_is_observed_for_arbitrary_pair(self) -> None:
        driver = Driver(payload())
        result = query_activity_feast_guest_opinion_private_v1(
            driver, expected_revision=5, guest_character_id=32000)
        self.assertEqual(result["guest_opinion_of_actor"], -25)
        self.assertEqual(driver.sent[0]["guest_character_id"], 32000)
        self.assertEqual(driver.sent[0]["expected_actor_character_id"], 31000)
        self.assertNotIn("rule_key", result)
        self.assertNotIn("invitation_accepted", result)

    def test_unknown_opinion_cannot_become_zero(self) -> None:
        unavailable = query_activity_feast_guest_opinion_private_v1(
            Driver(payload("opinion_unavailable")), expected_revision=5,
            guest_character_id=32000)
        self.assertEqual(unavailable["status"], "opinion_unavailable")
        self.assertIsNone(unavailable["guest_opinion_of_actor"])
        bad = payload("opinion_unavailable")
        bad["guest_opinion_of_actor"] = 0
        with self.assertRaisesRegex(BridgeUnavailableError, "unavailable malformed"):
            query_activity_feast_guest_opinion_private_v1(
                Driver(bad), expected_revision=5, guest_character_id=32000)

    def test_disabled_or_crossed_frame_fails_before_value_use(self) -> None:
        driver = Driver(payload())
        driver.allow_private_activity_feast_guest_opinion_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_guest_opinion_private_v1(
                driver, expected_revision=5, guest_character_id=32000)
        self.assertEqual(driver.sent, [])
        driver = Driver(payload())
        driver.after["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed paused frame"):
            query_activity_feast_guest_opinion_private_v1(
                driver, expected_revision=5, guest_character_id=32000)


if __name__ == "__main__":
    unittest.main()
