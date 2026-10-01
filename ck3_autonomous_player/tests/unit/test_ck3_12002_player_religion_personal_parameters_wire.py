"""Actual personal-parameter mailbox packets through production protocol cache."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_personal_parameters_private_transport import (
    STEP, normalize_player_religion_personal_parameters_v1,
    query_player_religion_personal_parameters_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT.parent / "research/religion_doctrine12002_personal_parameters_mailbox_wire_fixtures.json"
FIXTURE_SHA256 = "67127a018d06c6e76ff606ea77094b4e6e2ed6f22315cc217f213fa87257ed0a"
CASES = (
    "personal-true-and-known-missing.json", "extension-absent.json", "empty-owned-tenets.json",
    "database-unavailable.json", "state-changed.json",
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"][name]["command_result"]


class PersonalParametersMailboxPacketDriver:
    """Only correlate request_id; production ingest/wait owns full result frames."""

    allow_private_player_religion_personal_parameters_query = True
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-personal-parameters-mailbox-fixture")
        result = packet["result"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1, "capabilities": [],
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        })
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {
                "character_id": result["player_religion_personal_parameters"]["played_character_id"],
                "alive": True,
            },
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": self.state.diagnostics()["hello"]},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_frame_types: list[str] = []
        self.endpoint = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.ingested_frame_types.append(self.state.ingest(packet))


class PlayerReligionPersonalParameters12002WireTest(unittest.TestCase):
    def test_actual_dto_preserves_complete_false_legal_absence_and_native_failure(self) -> None:
        self.assertEqual(hashlib.sha256(FIXTURES.read_bytes()).hexdigest(), FIXTURE_SHA256)
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_personal_parameters"]
                driver = PersonalParametersMailboxPacketDriver(packet)
                outputs[case] = normalize_player_religion_personal_parameters_v1(native, snapshot=driver.snapshot)
                self.assertEqual(outputs[case], native)
        current = outputs[CASES[0]]
        observed = {row["key"]: row["value"] for row in current["parameters"]}
        self.assertIs(observed["meditation_mechanics_active"], False)
        self.assertIs(observed["tenet_ritual_hospitality_free_guest_recruitment"], True)
        self.assertIs(observed["tenet_adaptive_study_rite_bonus"], True)
        self.assertIs(observed["tenet_adoptionism_adoption_personal_active"], False)
        self.assertTrue(current["supported_keys_complete"])
        self.assertNotIn("unsupported-key", observed)
        absent, empty = outputs[CASES[1]], outputs[CASES[2]]
        self.assertFalse(absent["has_character_extension"])
        self.assertTrue(empty["has_character_extension"])
        for result in (absent, empty):
            self.assertTrue(result["available"])
            self.assertTrue(result["personal_parameters_complete"])
            self.assertEqual(result["personal_tenet_keys"], [])
            self.assertEqual({row["key"] for row in result["parameters"]}, set(observed))
            self.assertTrue(all(row["value"] is False for row in result["parameters"]))
        for case, reason in zip(CASES[3:], ("parameter_registry_unavailable", "state_changed")):
            failed = outputs[case]
            self.assertFalse(failed["available"])
            self.assertFalse(failed["supported_keys_complete"])
            self.assertFalse(failed["personal_parameters_complete"])
            self.assertEqual(failed["parameters"], [])
            self.assertEqual(failed["unavailable_reason"], reason)
            self.assertEqual((failed["capture_epoch"], failed["date_raw"], failed["played_character_id"]),
                             (current["capture_epoch"], current["date_raw"], current["played_character_id"]))

    def test_actual_full_packets_pass_ingest_wait_and_readonly_query(self) -> None:
        for case in CASES:
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_personal_parameters"]
                driver = PersonalParametersMailboxPacketDriver(packet)
                actual = query_player_religion_personal_parameters_private_v1(
                    driver, expected_revision=driver.snapshot["revision"],
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(driver.ingested_frame_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], actual["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], actual["snapshot_revision"])
                self.assertEqual(set(request), {"type", "protocol_version", "request_id", "step",
                                               "expected_revision", "expected_snapshot_revision"})
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))

    def test_disabled_query_sends_nothing(self) -> None:
        driver = PersonalParametersMailboxPacketDriver(load_fixture(CASES[0]))
        driver.allow_private_player_religion_personal_parameters_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_personal_parameters_private_v1(
                driver, expected_revision=driver.snapshot["revision"],
            )
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
