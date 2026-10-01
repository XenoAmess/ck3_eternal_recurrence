"""Actual native member lists through real protocol ingest/wait and query leaf."""

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
from xar_autoplayer.bridge.player_rite_members_private_transport import query_player_rite_members_private_v1
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_rite_members"


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class ProtocolPacketDriver:
    """Only the request nonce changes before the real production cache ingests wire."""

    allow_private_player_rite_members_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_rite_members"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:rite-members")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerRiteMembers12002WireTests(unittest.TestCase):
    def test_four_actual_packets_keep_faith_rite_county_scope_and_empty_reason(self) -> None:
        outputs = {}
        for case in ("current-members", "known-empty", "legal-no-rite", "title-unavailable"):
            with self.subTest(case=case):
                packet = actual_packet(case)
                native = packet["result"]["player_rite_members"]
                driver = ProtocolPacketDriver(packet)
                actual = query_player_rite_members_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["capture_epoch"], 3)
                self.assertEqual(actual["snapshot_revision"], 701)
                self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-player-rite-members-v1")
                self.assertEqual(request["expected_revision"], 701)
                self.assertEqual(request["expected_snapshot_revision"], 701)
                self.assertNotIn("character_id", request)
                self.assertNotIn("candidate_character_id", request)
                self.assertEqual(packet["request_id"], 'members"worker-fixture')
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                outputs[case] = actual
        current = outputs["current-members"]
        self.assertEqual(current["faith_character_ids"], [50331652, 2264924165, 2281701382])
        self.assertEqual(current["rite_character_ids"], [50331652, 2281701382])
        self.assertEqual(current["county_title_ids"], [2298478594])
        self.assertGreater(current["rite_id"], 0x7FFFFFFF)
        self.assertGreater(current["faith_id"], 0x7FFFFFFF)
        self.assertGreater(current["religion_id"], 0x7FFFFFFF)
        for case in ("known-empty", "legal-no-rite", "title-unavailable"):
            for key in ("faith_character_ids", "rite_character_ids", "county_title_ids"):
                self.assertEqual(outputs[case][key], [])
        empty = outputs["known-empty"]
        self.assertIs(empty["available"], True)
        self.assertIsNotNone(empty["rite_id"])
        no_rite = outputs["legal-no-rite"]
        self.assertIs(no_rite["available"], True)
        for key in ("rite_id", "faith_id", "religion_id"):
            self.assertIsNone(no_rite[key])
        unavailable = outputs["title-unavailable"]
        self.assertIs(unavailable["available"], False)
        self.assertEqual(unavailable["unavailable_reason"], "county_title_unavailable")
        self.assertEqual(unavailable["status"], "unavailable")

    def test_disabled_private_permission_sends_no_query(self) -> None:
        driver = ProtocolPacketDriver(actual_packet("current-members"))
        driver.allow_private_player_rite_members_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_rite_members_private_v1(driver, expected_revision=driver.snapshot["revision"])
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
