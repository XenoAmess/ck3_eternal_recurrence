"""Compiled production reader/serializer packets through NativeDriver and MCP.

Set XAR_HOLY_SITE_NATIVE_FIXTURES to the CMake fixture output directory. Only
the transport hello/snapshot are synthetic Python inputs; no DTO is prebuilt.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_player_holy_site_v1"
FIXTURES = os.environ.get("XAR_HOLY_SITE_NATIVE_FIXTURES")


class Endpoint:
    pipe_name = r"\\.\pipe\holy-site-source-fixture-only"

    def __init__(self, packet):
        self.packet, self.requests, self.on_frame = packet, [], None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request["type"] == "execute_step":
            self.requests.append(deepcopy(request))
            assert request["request_id"] == self.packet["request_id"]
            self.publish(self.packet)

    def transport_error(self):
        return None

    def close(self):
        pass


@unittest.skipUnless(FIXTURES, "requires newly compiled native HolySite fixture packets")
class HolySiteNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, filename):
        packet = json.loads((Path(FIXTURES) / filename).read_text(encoding="utf-8"))
        result, primary = packet["result"], packet["result"]["player_holy_site"]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        driver.allow_private_player_holy_site_query = True
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command.query-player-holy-site-v1"]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:701", "revision": result["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": result["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": primary["played_character_id"], "alive": True}}})
        return driver, endpoint, packet

    async def test_compiled_native_packets_are_discovered_and_consumed_over_real_mcp(self):
        from mcp import Client
        for filename in ("window-selected.json", "explicit-selected.json", "stale-generation.json", "faith-unavailable.json"):
            with self.subTest(filename=filename):
                driver, endpoint, packet = self.setup_driver(filename)
                original = deepcopy(packet)
                try:
                    async with Client(create_server(driver)) as client:
                        tools = {t.name: t for t in (await client.list_tools()).tools}
                        self.assertTrue(tools[TOOL].annotations.read_only_hint)
                        self.assertEqual(set(tools[TOOL].input_schema["properties"]), {"expected_revision", "holy_site_id"})
                        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"]}
                        native = packet["result"]["player_holy_site"]
                        if native["requested_holy_site_id"] is not None:
                            arguments["holy_site_id"] = native["requested_holy_site_id"]
                        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                                   return_value=SimpleNamespace(hex="holy-site-fixture")):
                            reply = await client.call_tool(TOOL, arguments)
                        self.actual_mcp_results.append({"fixture": filename, "native_packet": original,
                            "arguments": arguments, "request": endpoint.requests, "response": reply.model_dump(mode="json")})
                        self.assertFalse(reply.is_error, str(reply))
                        actual = reply.structured_content
                        self.assertEqual(actual["available"], native["available"])
                        self.assertEqual(actual["unavailable_reason"], native["unavailable_reason"])
                        self.assertFalse(actual["adoption_legality_observed"])
                        self.assertEqual(actual["queried_native_revision"], 701)
                        self.assertNotEqual(actual["capture_epoch"], 701)
                        self.assertEqual(len(endpoint.requests), 1)
                        if actual["available"]:
                            self.assertEqual(actual["selected_holy_site"], native["selected_holy_site"])
                            self.assertEqual(actual["current_faith_holy_site_ids"], [0x81000002, 0x81000002])
                        else:
                            self.assertIsNone(actual["current_faith_sites"])
                        self.assertEqual(packet, original)
                finally:
                    driver.close()

    async def test_mcp_rejects_coerced_or_unknown_inputs_before_native_io(self):
        from mcp import Client
        driver, endpoint, _ = self.setup_driver("window-selected.json")
        try:
            async with Client(create_server(driver)) as client:
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                for arguments in ({"expected_revision": revision, "holy_site_id": True},
                                  {"expected_revision": revision, "holy_site_id": 0xFFFFFFFF},
                                  {"expected_revision": revision, "adopt": True}):
                    reply = await client.call_tool(TOOL, arguments)
                    self.assertTrue(reply.is_error)
                self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_foreign_build_packet_fails_closed_through_real_mcp(self):
        from mcp import Client
        driver, endpoint, _ = self.setup_driver("window-selected.json")
        # The alteration is an explicit negative transport case. The original
        # compiled fixture file remains unchanged and is never retagged.
        endpoint.packet = deepcopy(endpoint.packet)
        endpoint.packet["result"]["game_version"] = "1.20.1.1"
        try:
            async with Client(create_server(driver)) as client:
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                           return_value=SimpleNamespace(hex="holy-site-fixture")):
                    reply = await client.call_tool(TOOL, {"expected_revision": revision})
                self.actual_mcp_results.append({"negative_case": "foreign-build-packet", "response": reply.model_dump(mode="json")})
                self.assertTrue(reply.is_error)
                self.assertEqual(len(endpoint.requests), 1)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
