"""Compiled original-detail reader packets through the production Driver and MCP.

XAR_HOLY_SITE_ADOPTION_FIXTURES names the freshly compiled fixture directory.
The Python endpoint supplies transport/frame scaffolding, never a result DTO.
"""
from __future__ import annotations

from copy import deepcopy
import json
import hashlib
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
                        self.assertEqual(actual["native_resource_quote"], native["native_resource_quote"])
                        for key in ("native_detail_context_verified", "native_requirements_description_available",
                                    "native_requirements_description", "native_cost_description_available",
                                    "native_cost_description", "native_decision_cooldown_observed", "native_decision_cooldown"):
                            if key in native:
                                self.assertEqual(actual[key], native[key])
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

    async def test_compiled_planning_fields_preserve_partial_unknown_and_original_cooldown(self):
        from mcp import Client
        if not (Path(FIXTURES) / "detail-context-mismatch.json").is_file():
            self.skipTest("legacy native packets: planning extension absent")
        for filename in ("detail-context-mismatch.json", "requirements-unavailable.json", "quote-unavailable.json",
                         "detail-context-changed.json", "cooldown-active.json", "cooldown-expired.json", "cooldown-unavailable.json",
                         "cooldown-malformed-map.json", "cooldown-foreign-result.json", "cooldown-clock-changed.json", "text-context-getter-changed.json"):
            driver, endpoint, packet = self.setup_driver(filename)
            original = deepcopy(packet)
            native = packet["result"]["player_holy_site_adoption_detail"]
            try:
                async with Client(create_server(driver)) as client:
                    arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                                 "holy_site_id": native["requested_holy_site_id"]}
                    with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                               return_value=SimpleNamespace(hex="adoption-fixture")):
                        reply = await client.call_tool(TOOL, arguments)
                    self.actual_mcp_results.append({"fixture": filename, "native_packet": original,
                        "arguments": arguments, "requests": endpoint.requests, "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    self.assertFalse(actual["action_ready"])
                    self.assertFalse(actual["decision_confirm_invoked"])
                    self.assertIs(actual["native_can_confirm"], False)
                    for key in ("native_detail_context_verified", "native_requirements_description_available",
                                "native_requirements_description", "native_cost_description_available", "native_cost_description",
                                "native_resource_quote_available", "native_resource_quote", "native_decision_cooldown_observed",
                                "native_decision_cooldown"):
                        self.assertEqual(actual[key], native[key])
                    if filename in ("detail-context-mismatch.json", "detail-context-changed.json"):
                        self.assertFalse(actual["native_detail_context_verified"])
                        self.assertIsNone(actual["native_requirements_description"])
                        self.assertIsNone(actual["native_resource_quote"])
                    elif filename == "requirements-unavailable.json":
                        self.assertIsNone(actual["native_requirements_description"])
                        self.assertTrue(actual["native_resource_quote_available"])
                    elif filename == "quote-unavailable.json":
                        self.assertIn("Compatibility: false", actual["native_requirements_description"])
                        self.assertIsNone(actual["native_resource_quote"])
                    elif filename == "text-context-getter-changed.json":
                        self.assertIsNone(actual["native_requirements_description"])
                        self.assertIsNone(actual["native_cost_description"])
                        self.assertTrue(actual["native_resource_quote_available"])
                    elif filename in ("cooldown-unavailable.json", "cooldown-malformed-map.json", "cooldown-foreign-result.json", "cooldown-clock-changed.json"):
                        self.assertIsNone(actual["native_decision_cooldown"])
                        self.assertTrue(actual["native_resource_quote_available"])
                    else:
                        self.assertTrue(actual["native_decision_cooldown"]["present"])
                        self.assertEqual(actual["native_decision_cooldown"]["active"], filename == "cooldown-active.json")
                    self.assertEqual(packet, original)
            finally:
                driver.close()

    async def test_manual_negative_mutations_of_new_native_packet_are_rejected(self):
        from mcp import Client
        source_path = Path(FIXTURES) / "native-false.json"
        source_packet = json.loads(source_path.read_text(encoding="utf-8"))
        if not source_packet["result"]["player_holy_site_adoption_detail"].get("native_resource_quote_available"):
            self.skipTest("legacy packet lacks new planning fields")
        for name in ("quote-currency-mismatch", "quote-vector-truncated", "context-not-verified", "absent-cooldown-active"):
            driver, endpoint, packet = self.setup_driver("native-false.json")
            mutated = deepcopy(packet)
            value = mutated["result"]["player_holy_site_adoption_detail"]
            if name == "quote-currency-mismatch":
                value["native_resource_quote"]["costs_raw"]["piety"] += 1
            elif name == "quote-vector-truncated":
                value["native_resource_quote"]["resource_vector_raw"].pop()
            elif name == "context-not-verified":
                value["native_detail_context_verified"] = False
            else:
                value["native_decision_cooldown"]["active"] = True
            endpoint.packet = mutated
            try:
                async with Client(create_server(driver)) as client:
                    arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                                 "holy_site_id": value["requested_holy_site_id"]}
                    with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                               return_value=SimpleNamespace(hex="adoption-fixture")):
                        reply = await client.call_tool(TOOL, arguments)
                    self.actual_mcp_results.append({"negative_case": name, "input_is_manual_mutation": True,
                        "source_file": str(source_path), "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                        "mutated_packet": mutated, "response": reply.model_dump(mode="json")})
                    self.assertTrue(reply.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.assertEqual(json.loads(source_path.read_text(encoding="utf-8")), source_packet)
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
