"""No-launch contract for the default-off feast guest-rule query/action transport."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_guest_rule_private_transport import (
    ACTIVATE_STEP, QUERY_STEP, SCHEMA,
    activate_activity_feast_guest_rule_private_v1,
    query_activity_feast_guest_rule_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {"snapshot_id": "native:3", "revision": 5, "native_revision": 3,
            "date_raw": 53219928, "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def payload(status: str = "observed_inactive", *, invoked: bool = False) -> dict[str, object]:
    observed = status in {"observed_inactive", "observed_active", "activated"}
    return {"schema": SCHEMA, "snapshot_revision": 3,
            "date_raw": 53219928, "actor_character_id": 29829,
            "activity_key": "activity_feast", "planning_stage": 5,
            "status": status, "invoked": invoked,
            "active": (status != "observed_inactive") if observed else None,
            "native_key_hash": 1234 if observed else None,
            "ordered_rule_count": 3 if observed else None,
            "active_rule_count": 2 if observed else None,
            "filtered_group_count": 2 if observed else None,
            "filtered_character_count": 8 if observed else None}


class Driver:
    allow_private_activity_feast_guest_rule_query = True
    allow_private_activity_feast_guest_rule_action = True

    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.sent: list[dict[str, object]] = []
        self.after = snapshot()
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(snapshot() if not self.sent else self.after)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(request)

    def wait_for_command_result(self, request_id: str, _: float) -> dict[str, object]:
        step = self.sent[-1]["step"]
        status = self.response["status"]
        outer = ("unavailable" if status not in {
            "observed_inactive", "observed_active", "activated"}
            else "available" if status == "observed_inactive"
            else "activated" if status == "activated" else "already_active")
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": step, "accepted": True, "status": outer,
                           "private_build": True,
                           "read_only": step == QUERY_STEP,
                           "advertised": False, "backend_id": "native-headless",
                           "activity_feast_guest_rule": self.response}}


class GuestRuleTransportTest(unittest.TestCase):
    def test_query_is_bound_and_keeps_inactive_distinct_from_unknown(self) -> None:
        driver = Driver(payload())
        result = query_activity_feast_guest_rule_private_v1(
            driver, authored_rule_key="activity_invite_rule_vassals", expected_revision=5)
        self.assertEqual(result["status"], "observed_inactive")
        self.assertIs(result["active"], False)
        self.assertEqual(driver.sent[0]["step"], QUERY_STEP)
        self.assertEqual(driver.sent[0]["expected_revision"], 3)
        self.assertEqual(driver.sent[0]["expected_date_raw"], 53219928)
        self.assertEqual(driver.sent[0]["expected_actor_character_id"], 29829)
        self.assertEqual(driver.sent[0]["authored_rule_key"], "activity_invite_rule_vassals")
        self.assertNotIn("policy_approved", driver.sent[0])
        self.assertNotIn("candidate_character_id", result)
        unavailable = query_activity_feast_guest_rule_private_v1(
            Driver(payload("rule_unavailable")),
            authored_rule_key="activity_invite_rule_vassals", expected_revision=5)
        self.assertEqual(unavailable["status"], "rule_unavailable")
        self.assertIsNone(unavailable["filtered_character_count"])

    def test_action_needs_explicit_policy_and_native_postcondition(self) -> None:
        driver = Driver(payload("activated", invoked=True))
        with self.assertRaises(ValueError):
            activate_activity_feast_guest_rule_private_v1(
                driver, authored_rule_key="activity_invite_rule_vassals",
                expected_revision=5, policy_approved=False)
        self.assertEqual(driver.sent, [])
        result = activate_activity_feast_guest_rule_private_v1(
            driver, authored_rule_key="activity_invite_rule_vassals",
            expected_revision=5, policy_approved=True)
        self.assertEqual(result["status"], "activated")
        self.assertIs(result["invoked"], True)
        self.assertIs(result["active"], True)
        self.assertEqual(driver.sent[0]["policy_approved"], True)
        already = activate_activity_feast_guest_rule_private_v1(
            Driver(payload("observed_active")),
            authored_rule_key="activity_invite_rule_vassals",
            expected_revision=5, policy_approved=True)
        self.assertEqual(already["status"], "observed_active")
        self.assertIs(already["invoked"], False)

    def test_default_off_and_frame_or_schema_failure(self) -> None:
        driver = Driver(payload())
        driver.allow_private_activity_feast_guest_rule_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_guest_rule_private_v1(
                driver, authored_rule_key="activity_invite_rule_vassals",
                expected_revision=5)
        self.assertEqual(driver.sent, [])
        driver = Driver(payload())
        driver.after["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed paused frame"):
            query_activity_feast_guest_rule_private_v1(
                driver, authored_rule_key="activity_invite_rule_vassals",
                expected_revision=5)
        bad = payload("native_action_failed", invoked=True)
        bad["filtered_group_count"] = 0
        with self.assertRaisesRegex(BridgeUnavailableError, "unavailable must remain unknown"):
            activate_activity_feast_guest_rule_private_v1(
                Driver(bad), authored_rule_key="activity_invite_rule_vassals",
                expected_revision=5, policy_approved=True)


if __name__ == "__main__":
    unittest.main()
