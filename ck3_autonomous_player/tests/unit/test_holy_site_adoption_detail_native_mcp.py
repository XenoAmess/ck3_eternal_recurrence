"""Compiled original-detail reader packets through the production Driver and MCP.

XAR_HOLY_SITE_ADOPTION_FIXTURES names the freshly compiled fixture directory.
The Python endpoint supplies transport/frame scaffolding, never a result DTO.
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

TOOL = "ck3_query_player_holy_site_adoption_detail_v1"
FIXTURES = os.environ.get("XAR_HOLY_SITE_ADOPTION_FIXTURES")


class Endpoint:
    pipe_name = r"\\.\pipe\holy-site-adoption-source-fixture-only"

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


@unittest.skipUnless(FIXTURES, "requires newly compiled native adoption-detail fixture packets")
class HolySiteAdoptionDetailNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, filename):
        packet = json.loads((Path(FIXTURES) / filename).read_text(encoding="utf-8"))
        result = packet["result"]
        primary = result["player_holy_site_adoption_detail"]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        driver.allow_private_holy_site_adoption_detail_query = True
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command.query-player-holy-site-adoption-detail-v1"]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:701", "revision": result["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": result["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": primary["played_character_id"], "alive": True}}})
        return driver, endpoint, packet

    async def test_actual_native_packets_preserve_false_true_bypass_and_unknown_over_real_mcp(self):
        from mcp import Client
        for filename in ("native-false.json", "native-true.json", "bypass-enabled.json", "bypass-unavailable.json",
                         "parameter-mismatch.json", "fallback-first-rejected.json"):
            with self.subTest(filename=filename):
                driver, endpoint, packet = self.setup_driver(filename)
                original = deepcopy(packet)
                native = packet["result"]["player_holy_site_adoption_detail"]
                try:
                    async with Client(create_server(driver)) as client:
                        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                        self.assertTrue(tools[TOOL].annotations.read_only_hint)
                        self.assertEqual(set(tools[TOOL].input_schema["properties"]), {"holy_site_id", "expected_revision"})
                        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                                     "holy_site_id": native["requested_holy_site_id"]}
                        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                                   return_value=SimpleNamespace(hex="adoption-fixture")):
                            reply = await client.call_tool(TOOL, arguments)
                        self.actual_mcp_results.append({"fixture": filename, "native_packet": original,
                            "arguments": arguments, "requests": endpoint.requests, "response": reply.model_dump(mode="json")})
                        self.assertFalse(reply.is_error, str(reply))
                        actual = reply.structured_content
                        for key in ("available", "unavailable_reason", "native_can_confirm",
                                    "normal_requirements_legality_observed", "normal_requirements_can_confirm"):
                            self.assertEqual(actual[key], native[key])
                        self.assertTrue(actual["read_only"])
                        self.assertFalse(actual["action_ready"])
                        self.assertFalse(actual["decision_confirm_invoked"])
                        self.assertFalse(actual["adoption_completed_observed"])
                        self.assertIsNone(actual["native_resource_quote"])
                        self.assertEqual(actual["queried_native_revision"], 701)
                        self.assertEqual(len(endpoint.requests), 1)
                        if filename == "native-false.json":
                            self.assertIs(actual["normal_requirements_can_confirm"], False)
                        elif filename == "native-true.json":
                            self.assertIs(actual["normal_requirements_can_confirm"], True)
                        elif filename in ("bypass-enabled.json", "bypass-unavailable.json"):
                            self.assertIs(actual["native_can_confirm"], True)
                            self.assertIsNone(actual["normal_requirements_can_confirm"])
                        else:
                            self.assertIsNone(actual["native_can_confirm"])
                        if actual["available"]:
                            self.assertEqual(actual["selected_index"], 1)
                            self.assertEqual(actual["parameter_holy_site_id"], 0x81000002)
                            self.assertEqual(actual["selected_holy_site_id"], 0x81000002)
                            self.assertEqual(actual["confirm_tooltip"], "native fixture reason")
                        self.assertEqual(packet, original)
                finally:
                    driver.close()

    async def test_strict_admission_and_foreign_build_fail_without_forging_native_packets(self):
        from mcp import Client
        driver, endpoint, _ = self.setup_driver("native-true.json")
        try:
            async with Client(create_server(driver)) as client:
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                for invalid in ({"holy_site_id": True}, {"holy_site_id": 0xFFFFFFFF}, {"confirm": True}):
                    reply = await client.call_tool(TOOL, {"expected_revision": revision, "holy_site_id": 0x81000002, **invalid})
                    self.assertTrue(reply.is_error)
                self.assertEqual(endpoint.requests, [])
                # Explicit negative transport case; the compiled file remains intact.
                endpoint.packet = deepcopy(endpoint.packet)
                endpoint.packet["result"]["game_version"] = "1.20.1.1"
                with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                           return_value=SimpleNamespace(hex="adoption-fixture")):
                    reply = await client.call_tool(TOOL, {"expected_revision": revision, "holy_site_id": 0x81000002})
                self.actual_mcp_results.append({"negative_case": "foreign-build-packet", "response": reply.model_dump(mode="json")})
                self.assertTrue(reply.is_error)
                self.assertEqual(len(endpoint.requests), 1)
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
