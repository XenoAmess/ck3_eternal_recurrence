"""One compound consumer of the seven sealed complete native knowledge wires.

The actual collector/mailbox/serializer produces synthetic-memory command_result
files. Only nonce correlation changes in replay; business bodies stay unchanged.
This source seals expectations before FIRST and makes no live-game claim.
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

from mcp.server.mcpserver.exceptions import ToolError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_religion_tenets_private_transport import STEP
from xar_autoplayer.bridge.player_tenet_knowledge_catalogue_12003 import SCHEMA, SIBLING_KEY
from xar_autoplayer.bridge.target_rite_tenet_comparison_12003 import SIBLING_KEY as COMPARISON_KEY
from xar_autoplayer.bridge.version_identity import CK3_12002, CK3_12003


TOOL = "ck3_query_player_religion_tenets_v1"
ACTOR_ID = 0x03000004
DATE_RAW = 53175816
NATIVE_REVISION = 701
TARGET_RITE_ID = 0x85000003
A, B, C = "tenet_0", "tenet_1", "tenet_2"
_OLD_KEYS = {
    "schema", "game_version", "executable_sha256", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "faith_id", "current_rite", "faith_main_rite", "personal_tenets_complete",
    "personal_tenets", "effective_tenet_states", "status_values",
}
_CATALOGUE_KEYS = {
    "schema", "game_version", "executable_sha256", "scope", "available",
    "unavailable_reason", "capture_epoch", "date_raw", "played_character_id",
    "has_character_extension", "extra_collection_source", "extra_collection_complete",
    "extra_tenet_keys", "loaded_registry_complete", "loaded_definition_count",
    "native_has_prophet", "knowledge_inputs_complete", "knowledge_formula", "rows",
}
_CASES = (
    "no-draft-extra-input.json",
    "no-draft-prophet-input.json",
    "native-default-empty.json",
    "native-order-and-duplicates.json",
    "observed-empty-registry.json",
    "missing-prophet-definition.json",
    "old-unrequested-result.json",
)
_SUCCESS = {
    "no-draft-extra-input.json": (True, [B], False, (A, B, C), (False, True, False)),
    "no-draft-prophet-input.json": (True, [], True, (A, B), (False, False)),
    "native-default-empty.json": (False, [], False, (A, B), (False, False)),
    "native-order-and-duplicates.json": (True, [B, B], False, (B, A, B), (True, False, True)),
    "observed-empty-registry.json": (True, [], False, (), ()),
}


def _load_wire(name: str) -> dict[str, object]:
    directory = os.environ.get("XAR_PLAYER_TENET_KNOWLEDGE_NATIVE_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root must supply XAR_PLAYER_TENET_KNOWLEDGE_NATIVE_WIRE_DIR")
    return json.loads((Path(directory) / name).read_text(encoding="utf-8"))


class KnowledgeCatalogueWireDriver:
    """Bind the actual production method to the protocol cache and G2 route."""

    allow_private_player_religion_tenets_query = True
    command_timeout_seconds = 1.0
    query_player_religion_tenets_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_tenets_private_v1
    )

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline:player-tenet-knowledge-native-wire")
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


class PlayerTenetKnowledgeCatalogue12003Compound(unittest.IsolatedAsyncioTestCase):
    async def test_actual_seven_full_wires_through_registered_production_chain(self) -> None:
        packets = {name: _load_wire(name) for name in _CASES}
        outputs: dict[str, dict[str, object]] = {}
        for filename in _CASES:
            with self.subTest(wire=filename):
                packet = packets[filename]
                native = packet["result"]["player_religion_tenets"]
                driver = KnowledgeCatalogueWireDriver(packet)
                arguments: dict[str, object] = {"expected_revision": driver.snapshot["revision"]}
                if filename != "old-unrequested-result.json":
                    arguments["include_knowledge_catalogue"] = True
                if filename == "native-order-and-duplicates.json":
                    arguments.update(target_rite_id=TARGET_RITE_ID, tenet_key=B)
                called = await create_server(driver).call_tool(TOOL, arguments)
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertIsInstance(actual, dict)
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(set(native) - {SIBLING_KEY, COMPARISON_KEY}, _OLD_KEYS)
                self.assertIs(actual["available"], True)
                self.assertEqual(actual["date_raw"], DATE_RAW)
                self.assertEqual(actual["played_character_id"], ACTOR_ID)
                self.assertEqual(actual["snapshot_revision"], NATIVE_REVISION)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                self.assertEqual(request["expected_snapshot_revision"], NATIVE_REVISION)
                self.assertNotIn("character_id", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                if filename == "old-unrequested-result.json":
                    self.assertNotIn("include_knowledge_catalogue", request)
                    self.assertNotIn(SIBLING_KEY, native)
                    self.assertNotIn(SIBLING_KEY, actual)
                else:
                    self.assertIs(request["include_knowledge_catalogue"], True)
                    catalogue = actual[SIBLING_KEY]
                    self.assertEqual(set(catalogue), _CATALOGUE_KEYS)
                    self.assertEqual(catalogue["schema"], SCHEMA)
                    self.assertEqual(catalogue["scope"], "actual_played_character_extra_c8_and_prophet_inputs")
                    self.assertEqual(catalogue["knowledge_formula"], "extra_c8_membership_or_prophet_perk")
                    self.assertEqual(catalogue["game_version"], CK3_12003.game_version)
                    self.assertEqual(catalogue["executable_sha256"], CK3_12003.executable_sha256)
                    self.assertEqual(catalogue["played_character_id"], ACTOR_ID)
                    self.assertEqual(catalogue["date_raw"], DATE_RAW)
                    self.assertGreater(catalogue["capture_epoch"], 0)
                    self.assertEqual(catalogue["capture_epoch"], actual["capture_epoch"])
                if filename == "native-order-and-duplicates.json":
                    self.assertEqual(request["target_rite_id"], TARGET_RITE_ID)
                    self.assertEqual(request["tenet_key"], B)
                else:
                    self.assertNotIn("target_rite_id", request)
                    self.assertNotIn("tenet_key", request)
                    self.assertNotIn(COMPARISON_KEY, actual)
                outputs[filename] = actual

        for filename, (has_extension, extra_keys, prophet, registry_keys, members) in _SUCCESS.items():
            with self.subTest(observation=filename):
                catalogue = outputs[filename][SIBLING_KEY]
                self.assertIs(catalogue["available"], True)
                self.assertIsNone(catalogue["unavailable_reason"])
                self.assertIs(catalogue["has_character_extension"], has_extension)
                self.assertEqual(catalogue["extra_collection_source"],
                                 "character_extension_c8" if has_extension else "native_default_collection")
                self.assertEqual(catalogue["extra_tenet_keys"], extra_keys)
                self.assertIs(catalogue["native_has_prophet"], prophet)
                for flag in ("extra_collection_complete", "loaded_registry_complete", "knowledge_inputs_complete"):
                    self.assertIs(catalogue[flag], True)
                self.assertEqual(catalogue["loaded_definition_count"], len(registry_keys))
                self.assertEqual([row["tenet_key"] for row in catalogue["rows"]], list(registry_keys))
                self.assertEqual([row["source_index"] for row in catalogue["rows"]], list(range(len(registry_keys))))
                for row, expected_member in zip(catalogue["rows"], members):
                    self.assertEqual(set(row), {"source_index", "tenet_key", "native_extra_knowledge", "knowledge"})
                    self.assertIs(row["native_extra_knowledge"], expected_member)
                    self.assertIs(row["knowledge"], expected_member or prophet)

        extra_root = outputs["no-draft-extra-input.json"]
        self.assertIn(C, [row["key"] for row in extra_root["personal_tenets"]])
        self.assertIn({"key": A, "current_rite_status": 0}, extra_root["effective_tenet_states"])
        self.assertEqual(extra_root[SIBLING_KEY]["extra_tenet_keys"], [B])
        # C's personal provenance does not put it in the C8 knowledge collection.
        self.assertIs(extra_root[SIBLING_KEY]["rows"][2]["knowledge"], False)

        duplicate_root = outputs["native-order-and-duplicates.json"]
        comparison = duplicate_root[COMPARISON_KEY]
        self.assertIs(comparison["available"], True)
        self.assertIs(comparison["named_comparison_ready"], True)
        self.assertEqual(comparison["requested_target_rite_id"], TARGET_RITE_ID)
        self.assertEqual(comparison["tenet_key"], B)
        self.assertEqual(comparison["capture_epoch"], duplicate_root["capture_epoch"])
        self.assertIs(comparison["same_rite"], False)
        self.assertIs(comparison["same_faith"], True)
        for scope, status, keys in (
            (comparison["actor_rite"], 1, ["tenet_4", "tenet_4"]),
            (comparison["target_rite"], 3, [C, C]),
        ):
            self.assertEqual(scope["named_tenet_status"], status)
            self.assertIs(scope["named_tenet_core_member"], False)
            self.assertIs(scope["named_tenet_faith_main_core_member"], False)
            self.assertEqual(scope["core_tenet_keys"], keys)
            self.assertEqual(scope["faith_main_core_tenet_keys"], ["tenet_3"])
        self.assertEqual(duplicate_root["current_rite"]["rite_id"], 0)
        self.assertEqual(comparison["target_rite"]["rite_id"], TARGET_RITE_ID)

        failure_root = outputs["missing-prophet-definition.json"]
        failure = failure_root[SIBLING_KEY]
        self.assertIs(failure_root["available"], True)
        self.assertIs(failure["available"], False)
        self.assertEqual(failure["unavailable_reason"], "prophet_definition_unavailable")
        for flag in ("extra_collection_complete", "loaded_registry_complete", "knowledge_inputs_complete"):
            self.assertIs(failure[flag], False)
        for field in ("has_character_extension", "extra_collection_source", "extra_tenet_keys",
                      "loaded_definition_count", "native_has_prophet", "rows"):
            self.assertIsNone(failure[field])
        self.assertEqual(failure_root["current_rite"]["core_tenets"], [
            {"key": "tenet_4", "current_rite_status": 4},
            {"key": "tenet_4", "current_rite_status": 4},
        ])

        old_packet = packets["old-unrequested-result.json"]
        # Explicit false also keeps the same complete old wire and request fields.
        false_driver = KnowledgeCatalogueWireDriver(old_packet)
        called = await create_server(false_driver).call_tool(TOOL, {
            "expected_revision": false_driver.snapshot["revision"],
            "include_knowledge_catalogue": False,
        })
        self.assertFalse(called.is_error)
        self.assertNotIn(SIBLING_KEY, called.structured_content)
        self.assertNotIn("include_knowledge_catalogue", false_driver.sent[0])
        self.assertEqual({key: called.structured_content[key] for key in _OLD_KEYS},
                         old_packet["result"]["player_religion_tenets"])

        # This preserves a legacy driver's original method signature in MCP.
        class LegacySignatureDriver:
            allow_private_player_religion_tenets_query = True

            def __init__(self) -> None:
                self.revisions: list[int] = []

            def query_player_religion_tenets_private_v1(self, *, expected_revision: int) -> dict[str, object]:
                self.revisions.append(expected_revision)
                return {"old_route": True}

        legacy_driver = LegacySignatureDriver()
        legacy_server = create_server(legacy_driver)
        for arguments in ({"expected_revision": 702},
                          {"expected_revision": 702, "include_knowledge_catalogue": False}):
            called = await legacy_server.call_tool(TOOL, arguments)
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content, {"old_route": True})
        self.assertEqual(legacy_driver.revisions, [702, 702])

        # Request validation covers real entry points without changing any wire.
        for invalid in (None, 0, 1, "true", "false", [], {}):
            with self.subTest(non_bool=invalid):
                driver = KnowledgeCatalogueWireDriver(old_packet)
                with self.assertRaises(BridgeUnavailableError):
                    driver.query_player_religion_tenets_private_v1(
                        expected_revision=driver.snapshot["revision"],
                        include_knowledge_catalogue=invalid,
                    )
                self.assertEqual(driver.sent, [])
                self.assertEqual(driver.ingested_types, [])
                with self.assertRaises(ToolError):
                    await create_server(driver).call_tool(TOOL, {
                        "expected_revision": driver.snapshot["revision"],
                        "include_knowledge_catalogue": invalid,
                    })
                self.assertEqual(driver.sent, [])

        other_build_driver = KnowledgeCatalogueWireDriver(old_packet)
        hello = other_build_driver.snapshot["diagnostics"]["hello"]
        hello["expected_ck3_version"] = CK3_12002.game_version
        hello["expected_ck3_sha256"] = CK3_12002.executable_sha256
        with self.assertRaises(BridgeUnavailableError):
            other_build_driver.query_player_religion_tenets_private_v1(
                expected_revision=other_build_driver.snapshot["revision"],
                include_knowledge_catalogue=True,
            )
        self.assertEqual(other_build_driver.sent, [])
        self.assertEqual(other_build_driver.ingested_types, [])

        for incomplete_pair in ({"target_rite_id": TARGET_RITE_ID}, {"tenet_key": B}):
            driver = KnowledgeCatalogueWireDriver(old_packet)
            with self.assertRaises(BridgeUnavailableError):
                driver.query_player_religion_tenets_private_v1(
                    expected_revision=driver.snapshot["revision"],
                    include_knowledge_catalogue=True, **incomplete_pair,
                )
            self.assertEqual(driver.sent, [])
            self.assertEqual(driver.ingested_types, [])


if __name__ == "__main__":
    unittest.main()
