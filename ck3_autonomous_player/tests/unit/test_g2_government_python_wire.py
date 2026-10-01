"""Actual native GOV producer JSON through the query driver and MCP SDK."""

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

from xar_autoplayer.bridge.government_runtime_adapter_private_transport import (
    STEP, normalize_government_runtime_adapter_v1,
    query_government_runtime_adapter_private_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12002


def wire(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"ck3_12002_government_adapter_{name}.json").read_text(encoding="utf-8"))


class NativeWireDriver:
    command_timeout_seconds = 1.0
    allow_private_government_runtime_adapter_query = True
    query_government_runtime_adapter_private_v1 = NativeHeadlessGameplayDriver.query_government_runtime_adapter_private_v1

    def __init__(self, value: dict[str, object]):
        self.value = value
        self.endpoint = self.state = self
        self.requests: list[dict[str, object]] = []
        self.snapshot = {
            "paused": True, "map_ready": True, "revision": 702,
            "native_revision": 701, "snapshot_id": "native:701",
            "date_raw": 1220410,
            "played_character": {"character_id": 29829, "alive": True},
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }

    def take_snapshot(self):
        return deepcopy(self.snapshot)

    def send(self, request):
        self.requests.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        assert request_id == self.requests[-1]["request_id"]
        return {"type": "command_result", "protocol_version": 1,
                "request_id": request_id, "ok": True,
                "result": {"step": STEP, "accepted": True,
                           "status": self.value["status"], "private_build": True,
                           "read_only": True, "advertised": False,
                           "government_runtime_adapter": deepcopy(self.value),
                           "backend_id": "native-headless"}}


class GovernmentPythonWireTests(unittest.TestCase):
    def test_bytes_are_actual_cpp_serializer_outputs(self):
        provenance = json.loads((FIXTURES / "ck3_12002_government_adapter_python_provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["local_ck3_operations"], [])
        for row in provenance["fixtures"]:
            self.assertEqual(hashlib.sha256((FIXTURES / row["file"]).read_bytes()).hexdigest(), row["sha256"])

    def test_real_feudal_features_round_trip_with_current_profile(self):
        value = wire("available")
        driver = NativeWireDriver(value)
        result = query_government_runtime_adapter_private_v1(driver, expected_revision=702)
        self.assertEqual(result["government"], value["government"])
        self.assertEqual(result["effective_feature_flags"], value["effective_feature_flags"])
        self.assertTrue(result["readiness"]["core_adapter_ready"])
        keys = {row["key"] for row in result["effective_feature_flags"]["items"]}
        self.assertIn("by_god_alone", keys)
        self.assertNotIn("barter_troops", keys)
        self.assertEqual([request["step"] for request in driver.requests], [STEP])

    def test_actual_native_unavailable_stays_unavailable(self):
        value = wire("unavailable")
        driver = NativeWireDriver(value)
        result = driver.query_government_runtime_adapter_private_v1(expected_revision=702)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["unavailable_reason"], value["unavailable_reason"])
        self.assertFalse(result["readiness"]["core_adapter_ready"])

    def test_private_cli_is_off_by_default(self):
        self.assertFalse(parser().parse_args([]).private_government_runtime_adapter_query)


@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class GovernmentMcpWireTests(unittest.IsolatedAsyncioTestCase):
    async def test_actual_complete_native_caller_packet_reaches_sdk(self):
        from mcp import Client

        packet = json.loads((FIXTURES / "ck3_12002_government_adapter_actual_caller_unavailable.json").read_text(encoding="utf-8"))

        class ActualCallerDriver(NativeWireDriver):
            def wait_for_command_result(self, request_id, timeout):
                result = deepcopy(packet)
                result["request_id"] = request_id
                return result

        driver = ActualCallerDriver(packet["result"]["government_runtime_adapter"])
        async with Client(create_server(driver)) as client:
            called = await client.call_tool("ck3_query_government_runtime_adapter_private_v1", {"expected_revision": 702})
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content["status"], "unavailable")
            self.assertEqual(called.structured_content["unavailable_reason"], "campaign_collector_unavailable")
            self.assertFalse(called.structured_content["readiness"]["core_adapter_ready"])
            self.assertEqual(len(driver.requests), 1)

    async def test_actual_native_json_is_returned_by_readonly_sdk_tool(self):
        from mcp import Client

        driver = NativeWireDriver(wire("available"))
        server = create_server(driver)
        async with Client(server) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools["ck3_query_government_runtime_adapter_private_v1"].annotations.read_only_hint)
            called = await client.call_tool("ck3_query_government_runtime_adapter_private_v1", {"expected_revision": 702})
            self.assertFalse(called.is_error)
            self.assertEqual(called.structured_content["government"], wire("available")["government"])
            self.assertTrue(called.structured_content["readiness"]["core_adapter_ready"])
            self.assertEqual(len(driver.requests), 1)

    async def test_private_read_is_not_registered_without_explicit_flag(self):
        from mcp import Client

        driver = NativeWireDriver(wire("available"))
        driver.allow_private_government_runtime_adapter_query = False
        async with Client(create_server(driver)) as client:
            tools = {tool.name for tool in (await client.list_tools()).tools}
            self.assertNotIn("ck3_query_government_runtime_adapter_private_v1", tools)


if __name__ == "__main__":
    unittest.main()
