"""One compound consumes five actual .3 doctrine-knowledge command-result wires.

Expectations are sealed with the native producer before FIRST. Its five new
cases use synthetic memory through the actual collector/mailbox/serializer and
build renderer. Only request nonce correlation changes during replay.
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

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeProtocolState
from xar_autoplayer.bridge.player_religion_doctrine_knowledge_private_transport import STEP
from xar_autoplayer.bridge.version_identity import CK3_12003


TOOL = "ck3_query_player_religion_doctrine_knowledge_v1"
ACTOR_ID = 0x03000004
RITE_ID = 0x82000002
DATE_RAW = 53175816
NATIVE_REVISION = 701
LEARNED_SCHEMA = "ck3_12003_played_doctrine_knowledge_v1"
LOOKUP_SCHEMA = "ck3_12003_played_doctrine_knowledge_lookup_v1"
_COMMON_KEYS = {
    "schema", "game_version", "executable_sha256", "available", "unavailable_reason",
    "capture_epoch", "date_raw", "played_character_id",
}
_LEARNED_KEYS = _COMMON_KEYS | {"rite_id", "knowledge_source", "learned_rows"}
_LOOKUP_KEYS = _COMMON_KEYS | {
    "requested_doctrine_key", "definition_found", "definition", "native_knows_doctrine",
}
_CASES = (
    ("learned-e0-order-duplicates.json", "learned_rows", None),
    ("learned-rite-default-empty.json", "learned_rows", None),
    ("lookup-known-true.json", "by_key", "doctrine_a"),
    ("lookup-known-false.json", "by_key", "doctrine_c"),
    ("lookup-definition-not-found.json", "by_key", "doctrine_absent"),
)


def _load_wire(name: str) -> dict[str, object]:
    directory = os.environ.get("XAR_DOCTRINE_KNOWLEDGE_SCHEMA_12003_NATIVE_WIRE_DIR")
    if not directory:
        raise RuntimeError("Root must supply XAR_DOCTRINE_KNOWLEDGE_SCHEMA_12003_NATIVE_WIRE_DIR")
    return json.loads((Path(directory) / name).read_text(encoding="utf-8"))


class DoctrineKnowledgeWireDriver:
    """Use the real Driver method, protocol cache and private G2 transport."""

    allow_private_player_religion_doctrine_knowledge_query = True
    command_timeout_seconds = 1.0
    query_player_religion_doctrine_knowledge_private_v1 = (
        NativeHeadlessGameplayDriver.query_player_religion_doctrine_knowledge_private_v1
    )

    def __init__(self, packet: dict[str, object]) -> None:
        self.packet = deepcopy(packet)
        self.state = NativeProtocolState("offline:doctrine-knowledge-schema-12003-native-wire")
        result = packet["result"]
        native = result["player_religion_doctrine_knowledge"]
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


class DoctrineKnowledgeSchema12003Compound(unittest.IsolatedAsyncioTestCase):
    async def test_five_actual_whole_wires_through_registered_production_chain(self) -> None:
        outputs: dict[str, dict[str, object]] = {}
        for filename, mode, key in _CASES:
            with self.subTest(wire=filename):
                packet = _load_wire(filename)
                native = packet["result"]["player_religion_doctrine_knowledge"]
                driver = DoctrineKnowledgeWireDriver(packet)
                arguments: dict[str, object] = {"expected_revision": driver.snapshot["revision"]}
                if key is not None:
                    arguments["doctrine_key"] = key
                called = await create_server(driver).call_tool(TOOL, arguments)
                self.assertFalse(called.is_error)
                actual = called.structured_content
                self.assertIsInstance(actual, dict)
                # This includes the actual build-rendered schema; no native
                # business field is constructed or changed for consumption.
                self.assertEqual({field: actual[field] for field in native}, native)
                self.assertEqual(set(native), _LEARNED_KEYS if mode == "learned_rows" else _LOOKUP_KEYS)
                self.assertEqual(actual["schema"], LEARNED_SCHEMA if mode == "learned_rows" else LOOKUP_SCHEMA)
                self.assertEqual(actual["game_version"], CK3_12003.game_version)
                self.assertEqual(actual["executable_sha256"], CK3_12003.executable_sha256)
                self.assertEqual(actual["exe_sha256"], CK3_12003.executable_sha256)
                self.assertIs(actual["available"], True)
                self.assertIsNone(actual["unavailable_reason"])
                self.assertEqual(actual["played_character_id"], ACTOR_ID)
                self.assertEqual(actual["date_raw"], DATE_RAW)
                self.assertEqual(actual["query_date_raw"], DATE_RAW)
                self.assertEqual(actual["snapshot_revision"], NATIVE_REVISION)
                self.assertGreater(actual["capture_epoch"], 0)
                self.assertNotEqual(actual["capture_epoch"], NATIVE_REVISION)
                self.assertEqual(actual["query_mode"], mode)
                self.assertEqual(packet["result"]["query_mode"], mode)
                self.assertEqual(actual["status"], "observed")
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], NATIVE_REVISION)
                self.assertEqual(request["expected_snapshot_revision"], NATIVE_REVISION)
                self.assertNotIn("character_id", request)
                if key is None:
                    self.assertNotIn("doctrine_key", request)
                else:
                    self.assertEqual(request["doctrine_key"], key)
                    self.assertEqual(actual["requested_doctrine_key"], key)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0.0))
                outputs[filename] = actual

        learned = outputs["learned-e0-order-duplicates.json"]
        self.assertEqual(learned["rite_id"], RITE_ID)
        self.assertEqual(learned["knowledge_source"], "character_extension")
        self.assertEqual(learned["learned_rows"], [
            {"doctrine_key": "doctrine_b", "group_key": "group_a",
             "source": "character_extension", "native_knows_doctrine": True},
            {"doctrine_key": "doctrine_a", "group_key": "group_a",
             "source": "character_extension", "native_knows_doctrine": True},
            {"doctrine_key": "doctrine_b", "group_key": "group_a",
             "source": "character_extension", "native_knows_doctrine": True},
        ])

        fallback = outputs["learned-rite-default-empty.json"]
        self.assertEqual(fallback["rite_id"], RITE_ID)
        self.assertEqual(fallback["knowledge_source"], "rite_default")
        self.assertEqual(fallback["learned_rows"], [])
        # The actual actor Rite is empty although the synthetic main Rite has C.
        # The native reader does not substitute that main-Rite collection.
        self.assertIs(fallback["available"], True)

        for filename, key, group, known in (
            ("lookup-known-true.json", "doctrine_a", "group_a", True),
            ("lookup-known-false.json", "doctrine_c", "group_b", False),
        ):
            with self.subTest(lookup=filename):
                lookup = outputs[filename]
                self.assertIs(lookup["definition_found"], True)
                self.assertEqual(lookup["definition"], {
                    "doctrine_key": key, "group_key": group, "source": "definition_registry",
                })
                self.assertIs(lookup["native_knows_doctrine"], known)

        absent = outputs["lookup-definition-not-found.json"]
        self.assertEqual(absent["requested_doctrine_key"], "doctrine_absent")
        self.assertIs(absent["available"], True)
        self.assertIs(absent["definition_found"], False)
        self.assertIsNone(absent["definition"])
        self.assertIsNone(absent["native_knows_doctrine"])
        self.assertIsNone(absent["unavailable_reason"])


if __name__ == "__main__":
    unittest.main()
