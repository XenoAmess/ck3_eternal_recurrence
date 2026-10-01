"""Consume actual full native hostility packets through the production cache."""

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
from xar_autoplayer.bridge.player_religion_hostility_private_transport import (
    STEP, normalize_player_religion_hostility_v1,
    query_player_religion_hostility_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURE = ROOT.parent / "research/religion_doctrine12002_hostility_mailbox_wire_fixtures.json"
CASES = ("asymmetric", "same-faith", "zero-target-id", "target-unavailable", "native-sentinel")


def actual_packet(case: str) -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8-sig"))["cases"][case + ".json"]


class MailboxPacketDriver:
    """Use real ingest/wait; request correlation is the sole changed wire field."""

    allow_private_player_religion_hostility_query = True

    def __init__(self, frame: dict[str, object]) -> None:
        self.frame = deepcopy(frame)
        result = frame["result"]
        native = result["player_religion_hostility"]
        revision = result["snapshot_revision"]
        self.snapshot = {
            "snapshot_id": f"native:{revision}", "revision": revision + 1,
            "native_revision": revision, "date_raw": result["date_raw"],
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
        self.state = NativeProtocolState("offline-fixture:religion-hostility")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionHostility12002WireTests(unittest.TestCase):
    def test_actual_directional_dtos_keep_full_ids_zero_and_null(self) -> None:
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                native = packet["result"]["player_religion_hostility"]
                self.assertEqual(normalize_player_religion_hostility_v1(
                    native, snapshot=MailboxPacketDriver(packet).snapshot,
                ), native)
        asymmetric = actual_packet("asymmetric")["result"]["player_religion_hostility"]
        self.assertGreater(asymmetric["target_rite_id"], 0x7FFFFFFF)
        self.assertGreater(asymmetric["actor_faith_id"], 0x7FFFFFFF)
        self.assertGreater(asymmetric["actor_religion_id"], 0x7FFFFFFF)
        self.assertNotEqual(asymmetric["actor_rite_id"], asymmetric["actor_main_rite_id"])
        self.assertEqual([asymmetric[key] for key in (
            "actor_rite_towards_target", "target_rite_towards_actor",
            "actor_faith_towards_target", "target_faith_towards_actor",
        )], [2, 0, 3, 1])
        same = actual_packet("same-faith")["result"]["player_religion_hostility"]
        self.assertTrue(same["same_faith"])
        self.assertTrue(same["same_religion"])
        self.assertEqual(actual_packet("zero-target-id")["result"]["player_religion_hostility"]["target_rite_id"], 0)

    def test_five_actual_packets_reach_production_protocol_ingest_and_wait(self) -> None:
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                native = packet["result"]["player_religion_hostility"]
                driver = MailboxPacketDriver(packet)
                target = 0 if case == "zero-target-id" else 2197815298
                actual = query_player_religion_hostility_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], target_rite_id=target,
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["snapshot_revision"], packet["result"]["snapshot_revision"])
                self.assertEqual(actual["queried_native_revision"], actual["snapshot_revision"])
                self.assertNotEqual(actual["capture_epoch"], actual["snapshot_revision"])
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["target_rite_id"], target)
                self.assertEqual(request["expected_revision"], 701)
                self.assertEqual(request["expected_snapshot_revision"], 701)
                self.assertNotIn("character_id", request)
                self.assertNotIn("actor_rite_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                outputs[case] = actual
        self.assertEqual(outputs["asymmetric"]["target_rite_towards_actor"], 0)
        for case, reason in (("target-unavailable", "target_rite_unavailable"),
                             ("native-sentinel", "native_level_unavailable")):
            self.assertFalse(outputs[case]["available"])
            self.assertEqual(outputs[case]["unavailable_reason"], reason)
            self.assertIsNone(outputs[case]["target_rite_id"])
            self.assertIsNone(outputs[case]["target_rite_towards_actor"])
            self.assertIsNone(outputs[case]["same_faith"])

    def test_required_uint32_target_and_disabled_query_send_nothing(self) -> None:
        driver = MailboxPacketDriver(actual_packet("asymmetric"))
        for invalid in (-1, 0x100000000, True, None):
            with self.subTest(target=invalid), self.assertRaises(ValueError):
                query_player_religion_hostility_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], target_rite_id=invalid,
                )
        with self.assertRaises(TypeError):
            query_player_religion_hostility_private_v1(driver, expected_revision=driver.snapshot["revision"])
        driver.allow_private_player_religion_hostility_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_hostility_private_v1(
                driver, expected_revision=driver.snapshot["revision"], target_rite_id=2197815298,
            )
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()
