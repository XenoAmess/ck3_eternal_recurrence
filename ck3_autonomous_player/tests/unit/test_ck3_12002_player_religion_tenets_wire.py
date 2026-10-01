"""Actual Tenet mailbox packets through the production protocol state cache."""

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
from xar_autoplayer.bridge.player_religion_tenets_private_transport import (
    STEP, normalize_player_religion_tenets_v1,
    query_player_religion_tenets_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT.parent / "research/religion_doctrine12002_tenet_rows_mailbox_wire_fixtures.json"
FIXTURE_SHA256 = "489a430bbd919f059219792d7374d642df4f9087a44171f9391762fdf669ee1d"
CASES = ("current-main-personal", "known-empty-personal", "personal-without-rite", "tenet-state-unavailable")


def load_fixture(name: str) -> dict[str, object]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"][name]["command_result"]


class TenetMailboxPacketDriver:
    """Correlate request_id and ingest the unchanged actual full native packet."""

    allow_private_player_religion_tenets_query = True
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline-tenet-mailbox-fixture")
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
            "played_character": {"character_id": result["player_religion_tenets"]["played_character_id"],
                                 "alive": True},
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


class PlayerReligionTenets12002WireTest(unittest.TestCase):
    def test_actual_dto_preserves_native_sources_zero_null_empty_and_failure(self) -> None:
        self.assertEqual(hashlib.sha256(FIXTURES.read_bytes()).hexdigest(), FIXTURE_SHA256)
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_tenets"]
                driver = TenetMailboxPacketDriver(packet)
                outputs[case] = normalize_player_religion_tenets_v1(native, snapshot=driver.snapshot)
                self.assertEqual(outputs[case], native)
        current = outputs["current-main-personal"]
        self.assertEqual(current["current_rite"]["rite_id"], 0)
        self.assertGreater(current["faith_id"], 0x7FFFFFFF)
        self.assertNotEqual(current["current_rite"]["rite_id"], current["faith_main_rite"]["rite_id"])
        self.assertEqual(current["current_rite"]["core_tenets"], [{"key": "tenet_4", "current_rite_status": 4}])
        self.assertEqual(current["faith_main_rite"]["core_tenets"], [{"key": "tenet_3", "current_rite_status": 3}])
        self.assertEqual(current["personal_tenets"][0], {"key": "tenet_0", "current_rite_status": 0})
        self.assertEqual({row["current_rite_status"] for row in current["effective_tenet_states"]}, set(range(5)))
        empty = outputs["known-empty-personal"]
        self.assertTrue(empty["available"])
        self.assertTrue(empty["personal_tenets_complete"])
        self.assertEqual(empty["personal_tenets"], [])
        absent = outputs["personal-without-rite"]
        self.assertIsNone(absent["current_rite"])
        self.assertIsNone(absent["faith_main_rite"])
        self.assertEqual([row["key"] for row in absent["personal_tenets"]], ["tenet_0", "tenet_4"])
        self.assertTrue(all(row["current_rite_status"] is None for row in absent["personal_tenets"]))
        failed = outputs["tenet-state-unavailable"]
        self.assertFalse(failed["available"])
        self.assertFalse(failed["personal_tenets_complete"])
        self.assertEqual(failed["unavailable_reason"], "tenet_state_unavailable")
        self.assertEqual((failed["date_raw"], failed["played_character_id"]),
                         (current["date_raw"], current["played_character_id"]))

    def test_actual_full_packets_pass_ingest_wait_and_readonly_query(self) -> None:
        for case in CASES:
            with self.subTest(case=case):
                packet = load_fixture(case)
                native = packet["result"]["player_religion_tenets"]
                driver = TenetMailboxPacketDriver(packet)
                actual = query_player_religion_tenets_private_v1(driver, expected_revision=driver.snapshot["revision"])
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
                self.assertNotIn("character_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))

    def test_disabled_query_sends_nothing(self) -> None:
        driver = TenetMailboxPacketDriver(load_fixture("current-main-personal"))
        driver.allow_private_player_religion_tenets_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_tenets_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
