"""Actual clergy full envelopes consumed by the production native protocol cache."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_clergy_appointment_private_transport import (
    query_player_clergy_appointment_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_clergy_appointment"
CASES = ("vacant-valid", "incumbent-reassign-denied", "candidate-native-denied",
         "foreign-context", "position-absent", "candidate-unavailable", "context-unavailable")


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class ProtocolPacketDriver:
    """Feed actual full packets to real ingest/wait; no pipe or stub wait."""

    allow_private_player_clergy_appointment_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_clergy_appointment"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["owner_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:clergy-appointment")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerClergyAppointment12002WireTests(unittest.TestCase):
    def test_seven_actual_provider_packets_preserve_predicates_absence_and_unavailability(self) -> None:
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                result = packet["result"]
                native = result["player_clergy_appointment"]
                driver = ProtocolPacketDriver(packet)
                actual = query_player_clergy_appointment_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                    candidate_character_id=native["candidate_character_id"], timeout_seconds=1,
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["query_status"], result["status"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["snapshot_revision"], 701)
                self.assertEqual(actual["capture_epoch"], 3)
                self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
                self.assertEqual(actual["queried_native_revision"], 701)
                self.assertIs(actual["action_eligibility_complete"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-player-clergy-appointment-v1")
                self.assertEqual(request["candidate_character_id"], 100663301)
                self.assertEqual(request["expected_revision"], 701)
                self.assertEqual(request["expected_snapshot_revision"], 701)
                self.assertNotIn("owner_character_id", request)
                self.assertEqual(packet["request_id"], 'clergy"worker-fixture')
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                outputs[case] = actual
        vacant = outputs["vacant-valid"]
        self.assertEqual(vacant["status"], "available")
        self.assertEqual(vacant["owner_rite_id"], 0)
        self.assertEqual(vacant["candidate_rite_id"], 0)
        self.assertIsNone(vacant["incumbent_character_id"])
        incumbent = outputs["incumbent-reassign-denied"]
        self.assertIs(incumbent["candidate_is_incumbent"], True)
        self.assertIs(incumbent["native_valid_character"], True)
        self.assertIs(incumbent["native_can_reassign"], False)
        denied = outputs["candidate-native-denied"]
        self.assertEqual(denied["query_status"], "observed")
        self.assertIs(denied["native_valid_character"], False)
        self.assertIs(denied["native_can_reassign"], True)
        self.assertGreater(denied["candidate_rite_id"], 0x7FFFFFFF)
        foreign = outputs["foreign-context"]
        self.assertIs(foreign["candidate_matches_owner_context"], False)
        self.assertIs(foreign["native_valid_character"], True)
        self.assertNotEqual(foreign["candidate_court_owner_id"], foreign["owner_character_id"])
        absent = outputs["position-absent"]
        self.assertEqual(absent["status"], "available")
        self.assertIs(absent["position_present"], False)
        self.assertIsNone(absent["active_task_id"])
        for key in ("native_valid_position", "native_valid_character", "native_can_reassign"):
            self.assertIsNone(absent[key])
        for case, failure in (("candidate-unavailable", "candidate_unavailable"),
                              ("context-unavailable", "candidate_context_unavailable")):
            self.assertEqual(outputs[case]["status"], "unavailable")
            self.assertEqual(outputs[case]["query_status"], "unavailable")
            self.assertEqual(outputs[case]["failure"], failure)
            self.assertIsNone(outputs[case]["native_valid_character"])

    def test_zero_candidate_is_rejected_without_defaulting_to_player(self) -> None:
        driver = ProtocolPacketDriver(actual_packet("vacant-valid"))
        with self.assertRaises(ValueError):
            query_player_clergy_appointment_private_v1(
                driver, expected_revision=driver.snapshot["revision"], candidate_character_id=0,
            )
        self.assertEqual(driver.sent, [])

    def test_disabled_private_permission_sends_no_query(self) -> None:
        driver = ProtocolPacketDriver(actual_packet("vacant-valid"))
        driver.allow_private_player_clergy_appointment_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_clergy_appointment_private_v1(
                driver, expected_revision=driver.snapshot["revision"], candidate_character_id=100663301,
            )
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
