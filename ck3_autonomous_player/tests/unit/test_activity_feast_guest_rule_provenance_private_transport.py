"""No-launch contract for a passive ordinary feast rule membership read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.activity_feast_guest_rule_provenance_private_transport import (
    SCHEMA, STEP, query_activity_feast_guest_rule_provenance_private_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError, UnsupportedStepError


def snapshot() -> dict[str, object]:
    return {"snapshot_id": "native:3", "revision": 5,
            "native_revision": 3, "date_raw": 10000,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 31000, "alive": True}}


def payload(*, member: bool = True, status: str = "observed") -> dict[str, object]:
    ids = [32000, 33000] if member else [33000]
    observed = status == "observed"
    return {
        "schema": SCHEMA, "snapshot_revision": 3,
        "date_raw": 10000, "actor_character_id": 31000,
        "activity_key": "activity_feast", "planning_stage": 5,
        "authored_rule_key": "activity_invite_rule_vassals",
        "rule_status": "observed_active", "status": status,
        "candidate_character_id": 32000,
        "rule_active": True,
        "native_key_hash": 12345 if observed else None,
        "normal_refresh_sequence": 12 if observed else None,
        "raw_rule_character_count": 3 if observed else None,
        "filtered_rule_character_count": len(ids) if observed else None,
        "candidate_membership": member if observed else None,
        "filtered_rule_character_ids": ids if observed else None,
    }


class Driver:
    allow_private_activity_feast_guest_rule_provenance_query = True

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
                "activity_feast_guest_rule_provenance": self.native,
                "backend_id": "native-headless",
            },
        }


class GuestRuleProvenanceReadTest(unittest.TestCase):
    def test_positive_and_negative_membership_are_observed_without_action(self) -> None:
        for member in (True, False):
            with self.subTest(member=member):
                driver = Driver(payload(member=member))
                result = query_activity_feast_guest_rule_provenance_private_v1(
                    driver, expected_revision=5,
                    authored_rule_key="activity_invite_rule_vassals",
                    candidate_character_id=32000)
                self.assertIs(result["candidate_membership"], member)
                self.assertEqual(driver.sent[0]["candidate_character_id"], 32000)
                self.assertEqual(driver.sent[0]["authored_rule_key"],
                                 "activity_invite_rule_vassals")
                self.assertNotIn("policy_approved", driver.sent[0])

    def test_unavailable_or_inconsistent_member_stays_unusable(self) -> None:
        unavailable = query_activity_feast_guest_rule_provenance_private_v1(
            Driver(payload(status="no_normal_refresh")), expected_revision=5,
            authored_rule_key="activity_invite_rule_vassals",
            candidate_character_id=32000)
        self.assertIsNone(unavailable["candidate_membership"])
        bad = payload(member=False)
        bad["candidate_membership"] = True
        with self.assertRaisesRegex(BridgeUnavailableError, "observed data malformed"):
            query_activity_feast_guest_rule_provenance_private_v1(
                Driver(bad), expected_revision=5,
                authored_rule_key="activity_invite_rule_vassals",
                candidate_character_id=32000)

    def test_disabled_and_changed_frame_reject(self) -> None:
        driver = Driver(payload())
        driver.allow_private_activity_feast_guest_rule_provenance_query = False
        with self.assertRaises(UnsupportedStepError):
            query_activity_feast_guest_rule_provenance_private_v1(
                driver, expected_revision=5,
                authored_rule_key="activity_invite_rule_vassals",
                candidate_character_id=32000)
        self.assertEqual(driver.sent, [])
        driver = Driver(payload())
        driver.after["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "crossed paused frame"):
            query_activity_feast_guest_rule_provenance_private_v1(
                driver, expected_revision=5,
                authored_rule_key="activity_invite_rule_vassals",
                candidate_character_id=32000)


if __name__ == "__main__":
    unittest.main()
