"""One compound production consumer of Root's complete native Tenet wires.

The source expectations are sealed before the first run. The files are actual
native serializer/mailbox output from synthetic memory, not live game evidence.
This consumer never reconstructs or changes a business packet body.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_religion_tenets_private_transport import STEP
from xar_autoplayer.bridge.target_rite_tenet_comparison_12003 import SIBLING_KEY
from xar_autoplayer.bridge.version_identity import CK3_12003


TOOL = "ck3_query_player_religion_tenets_v1"
ACTOR_ID = 0x03000004
DATE_RAW = 53175816
ACTOR_RITE_ID = 0
MAIN_RITE_ID = 0x82000002
FAITH_ID = 0x83000003
TARGET_RITE_ID = 0x85000003
HIGH_TARGET_RITE_ID = 0xA5000003
WRONG_TARGET_RITE_ID = 0xA6000003
_OLD_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "faith_id", "current_rite", "faith_main_rite", "personal_tenets_complete",
    "personal_tenets", "effective_tenet_states", "status_values",
}
_CASES = (
    ("distinct-same-faith.json", TARGET_RITE_ID, "tenet_1"),
    ("valid-zero-prohibited.json", TARGET_RITE_ID, "tenet_0"),
    ("same-rite-core.json", ACTOR_RITE_ID, "tenet_4"),
    ("missing-definition.json", TARGET_RITE_ID, "tenet_absent"),
    ("high-generation-target.json", HIGH_TARGET_RITE_ID, "tenet_1"),
    ("wrong-generation-target.json", WRONG_TARGET_RITE_ID, "tenet_1"),
    ("old-no-comparison.json", None, None),
)


def _load_wire(name: str) -> dict[str, object]:
    directory = os.environ.get("XAR_TARGET_RITE_TENET_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root must supply XAR_TARGET_RITE_TENET_WIRE_DIR")
    # The whole command_result is consumed unchanged, except request correlation.
    return json.loads((Path(directory) / name).read_text(encoding="utf-8"))


class TargetComparisonWireDriver:
    """Use the production Driver method, protocol cache and G2 transport."""

    allow_private_player_religion_tenets_query = True
    command_timeout_seconds = 1.0
    query_player_religion_tenets_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_tenets_private_v1
    )

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline:target-rite-tenet-native-wire")
        result = packet["result"]
        native = result["player_religion_tenets"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1, "capabilities": [],
            "expected_ck3_version": result["game_version"],
            "expected_ck3_sha256": result["executable_sha256"],
        })
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": self.state.diagnostics()["hello"]},
        }
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class TargetRiteTenetComparison12003Compound(unittest.IsolatedAsyncioTestCase):
    async def test_actual_full_wires_through_registered_mcp_driver_and_transport(self) -> None:
        outputs: dict[str, dict[str, object]] = {}
        for filename, target_id, key in _CASES:
            with self.subTest(wire=filename):
                packet = _load_wire(filename)
                native = packet["result"]["player_religion_tenets"]
                driver = TargetComparisonWireDriver(packet)
                arguments = {"expected_revision": driver.snapshot["revision"]}
                if target_id is not None:
                    arguments.update(target_rite_id=target_id, tenet_key=key)
                called = await create_server(driver).call_tool(TOOL, arguments)
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertIsInstance(actual, dict)
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(set(native) - {SIBLING_KEY}, _OLD_KEYS)
                self.assertEqual(actual["date_raw"], DATE_RAW)
                self.assertEqual(actual["played_character_id"], ACTOR_ID)
                self.assertEqual(actual["snapshot_revision"], 701)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], 701)
                self.assertEqual(request["expected_snapshot_revision"], 701)
                self.assertNotIn("character_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                if target_id is None:
                    self.assertNotIn(SIBLING_KEY, native)
                    self.assertNotIn(SIBLING_KEY, actual)
                    self.assertNotIn("target_rite_id", request)
                    self.assertNotIn("tenet_key", request)
                else:
                    comparison = actual[SIBLING_KEY]
                    self.assertEqual(request["target_rite_id"], target_id)
                    self.assertEqual(request["tenet_key"], key)
                    self.assertEqual(comparison["requested_target_rite_id"], target_id)
                    self.assertEqual(comparison["tenet_key"], key)
                    self.assertEqual(comparison["capture_epoch"], actual["capture_epoch"])
                    self.assertEqual(comparison["date_raw"], DATE_RAW)
                    self.assertEqual(comparison["played_character_id"], ACTOR_ID)
                    self.assertIs(comparison["read_only"], True)
                    self.assertEqual(comparison["status_values"], {
                        "unknown": 0, "known": 1, "prohibited": 2, "permitted": 3, "core": 4,
                    })
                outputs[filename] = actual

        for filename, target_id, expected_statuses in (
            ("distinct-same-faith.json", TARGET_RITE_ID, (1, 3)),
            ("valid-zero-prohibited.json", TARGET_RITE_ID, (0, 2)),
            ("high-generation-target.json", HIGH_TARGET_RITE_ID, (1, 3)),
        ):
            with self.subTest(observation=filename):
                comparison = outputs[filename][SIBLING_KEY]
                self.assertIs(comparison["available"], True)
                self.assertIs(comparison["named_comparison_ready"], True)
                self.assertIsNone(comparison["unavailable_reason"])
                self.assertIs(comparison["same_rite"], False)
                self.assertIs(comparison["same_faith"], True)
                actor = comparison["actor_rite"]
                target = comparison["target_rite"]
                self.assertEqual((actor["rite_id"], target["rite_id"]), (ACTOR_RITE_ID, target_id))
                self.assertEqual((actor["faith_id"], target["faith_id"]), (FAITH_ID, FAITH_ID))
                self.assertEqual((actor["faith_main_rite_id"], target["faith_main_rite_id"]),
                                 (MAIN_RITE_ID, MAIN_RITE_ID))
                self.assertEqual(actor["core_tenet_keys"], ["tenet_4", "tenet_4"])
                self.assertEqual(actor["faith_main_core_tenet_keys"], ["tenet_3"])
                self.assertEqual(target["core_tenet_keys"], ["tenet_2", "tenet_2"])
                self.assertEqual(target["faith_main_core_tenet_keys"], ["tenet_3"])
                for scope in (actor, target):
                    self.assertIs(scope["current_is_main"], False)
                    self.assertIs(scope["core_tenets_complete"], True)
                    self.assertIs(scope["faith_main_core_tenets_complete"], True)
                    self.assertIs(scope["named_tenet_core_member"], False)
                    self.assertIs(scope["named_tenet_faith_main_core_member"], False)
                self.assertEqual((actor["named_tenet_status"], target["named_tenet_status"]),
                                 expected_statuses)

        same = outputs["same-rite-core.json"][SIBLING_KEY]
        self.assertIs(same["available"], True)
        self.assertIs(same["named_comparison_ready"], True)
        self.assertIs(same["same_rite"], True)
        self.assertIs(same["same_faith"], True)
        for scope in (same["actor_rite"], same["target_rite"]):
            self.assertEqual(scope["rite_id"], ACTOR_RITE_ID)
            self.assertEqual(scope["core_tenet_keys"], ["tenet_4", "tenet_4"])
            self.assertEqual(scope["faith_main_core_tenet_keys"], ["tenet_3"])
            self.assertIs(scope["named_tenet_core_member"], True)
            self.assertIs(scope["named_tenet_faith_main_core_member"], False)
            self.assertEqual(scope["named_tenet_status"], 4)

        for filename, reason in (
            ("missing-definition.json", "tenet_definition_unavailable"),
            ("wrong-generation-target.json", "target_rite_unavailable"),
        ):
            with self.subTest(unavailable=filename):
                root = outputs[filename]
                comparison = root[SIBLING_KEY]
                self.assertIs(root["available"], True)
                self.assertIs(comparison["available"], False)
                self.assertIs(comparison["named_comparison_ready"], False)
                self.assertEqual(comparison["unavailable_reason"], reason)
                for field in ("actor_rite", "target_rite", "same_rite", "same_faith"):
                    self.assertIsNone(comparison[field])
                self.assertEqual(root["current_rite"]["core_tenets"], [
                    {"key": "tenet_4", "current_rite_status": 4},
                    {"key": "tenet_4", "current_rite_status": 4},
                ])

        old = outputs["old-no-comparison.json"]
        self.assertEqual(old["current_rite"]["core_tenets"], [
            {"key": "tenet_4", "current_rite_status": 4},
            {"key": "tenet_4", "current_rite_status": 4},
        ])

        # The two incomplete request pairs and malformed new scalar arguments
        # go through the actual production method, before any packet dispatch.
        for invalid in (
            {"target_rite_id": TARGET_RITE_ID},
            {"tenet_key": "tenet_1"},
            {"target_rite_id": TARGET_RITE_ID, "tenet_key": ""},
            {"target_rite_id": -1, "tenet_key": "tenet_1"},
            {"target_rite_id": 0x100000000, "tenet_key": "tenet_1"},
            {"target_rite_id": TARGET_RITE_ID, "tenet_key": "x" * 129},
        ):
            with self.subTest(request=invalid):
                driver = TargetComparisonWireDriver(_load_wire("old-no-comparison.json"))
                with self.assertRaises(BridgeUnavailableError):
                    driver.query_player_religion_tenets_private_v1(
                        expected_revision=driver.snapshot["revision"], **invalid,
                    )
                self.assertEqual(driver.sent, [])
                self.assertEqual(driver.ingested_types, [])


if __name__ == "__main__":
    unittest.main()
