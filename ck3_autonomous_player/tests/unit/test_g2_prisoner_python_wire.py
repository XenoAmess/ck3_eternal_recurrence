"""Actual production collection wire, distinct from native quote/live evidence."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
FIXTURES = ROOT / "native_bridge/research/fixtures"

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_prisoner_collection_private_transport import STEP
from xar_autoplayer.bridge.version_identity import CK3_12002


def wire(name):
    return json.loads((FIXTURES / f"ck3_12002_prisoner_{name}.json").read_text(encoding="utf-8"))


class PrisonerNativeWireDriver:
    command_timeout_seconds = 1.0
    allow_private_prisoner_collection_query = True
    query_player_prisoner_collection_private_v1 = NativeHeadlessGameplayDriver.query_player_prisoner_collection_private_v1

    def __init__(self, value):
        self.value = value
        self.endpoint = self.state = self
        self.requests = []
        self.snapshot = {
            "paused": True, "map_ready": True, "revision": 12,
            "native_revision": 11, "snapshot_id": "native:11", "date_raw": 14,
            "played_character": {"character_id": 16777218, "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256}},
        }

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        request = self.requests[-1]
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": request["step"], "accepted": True,
                           "status": self.value["status"], "query_sequence": 4,
                           "observation_revision": 13, "snapshot_revision": 11,
                           "player_prisoner_collection": deepcopy(self.value),
                           "private_build": True, "read_only": True,
                           "advertised": False, "backend_id": "native-headless"}}


class PrisonerPythonWireTests(unittest.TestCase):
    def test_bytes_and_quote_evidence_scope_are_frozen(self):
        manifest = json.loads((FIXTURES / "ck3_12002_prisoner_python_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["local_ck3_operations"], [])
        self.assertIn("synthetic shared quote DTO", manifest["quote_scope"])
        for row in manifest["fixtures"]:
            self.assertEqual(hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest(), row["sha256"])

    def test_actual_two_rows_and_lineage_fields_round_trip(self):
        value = wire("two-prisoners")
        driver = PrisonerNativeWireDriver(value)
        result = driver.query_player_prisoner_collection_private_v1(expected_revision=12)
        self.assertEqual(result["player_prisoner_collection"], value)
        self.assertEqual(value["total_count"], 2)
        self.assertEqual(result["exact_ck3_build"], CK3_12002.game_version)
        self.assertEqual(result["exe_sha256"], CK3_12002.executable_sha256)
        self.assertEqual([request["step"] for request in driver.requests], [STEP])

    def test_actual_empty_and_unavailable_are_distinct(self):
        for name in ("empty", "old-executable-unavailable"):
            value = wire(name)
            driver = PrisonerNativeWireDriver(value)
            result = driver.query_player_prisoner_collection_private_v1(expected_revision=12)
            self.assertEqual(result["player_prisoner_collection"], value)
            self.assertEqual(result["status"], value["status"])


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class PrisonerMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_sdk_returns_real_nonempty_collection_as_readonly(self):
        from mcp import Client

        driver = PrisonerNativeWireDriver(wire("two-prisoners"))
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            name = "ck3_query_player_prisoner_collection_private_v1"
            self.assertTrue(tools[name].annotations.read_only_hint)
            called = await client.call_tool(name, {"expected_revision": 12})
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content["player_prisoner_collection"]["total_count"], 2)
            self.assertEqual(called.structured_content["player_prisoner_collection"], driver.value)
            self.assertEqual(len(driver.requests), 1)


if __name__ == "__main__":
    unittest.main()
