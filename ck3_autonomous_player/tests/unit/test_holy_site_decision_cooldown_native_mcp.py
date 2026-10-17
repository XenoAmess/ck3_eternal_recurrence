"""New compiled wrapper/helper packets through the actual production Driver/MCP.

XAR_HOLY_SITE_DECISION_COOLDOWN_FIXTURES must identify a newly compiled output.
The endpoint provides transport scaffolding and forwards the whole native packet.
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
from xar_autoplayer.bridge.holy_site_decision_cooldown_private_transport import normalize_holy_site_decision_cooldown_v1

TOOL = "ck3_query_player_holy_site_decision_cooldown_v1"
STEP = "query-player-holy-site-decision-cooldown-v1"
FIXTURES = os.environ.get("XAR_HOLY_SITE_DECISION_COOLDOWN_FIXTURES")


class Endpoint:
    pipe_name = r"\\.\pipe\holy-site-decision-cooldown-source-fixture-only"

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


@unittest.skipUnless(FIXTURES, "requires newly compiled native four-key cooldown fixture packets")
class HolySiteDecisionCooldownNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, filename):
        packet = json.loads((Path(FIXTURES) / filename).read_text(encoding="utf-8"))
        envelope = packet["result"]
        native = envelope["player_holy_site_decision_cooldown"]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        driver.allow_private_holy_site_adoption_detail_query = True
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command." + STEP]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:701", "revision": envelope["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": envelope["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": native["played_character_id"], "alive": True}}})
        return driver, endpoint, packet

    async def call(self, driver, action):
        from mcp import Client
        async with Client(create_server(driver)) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            self.assertTrue(tools[TOOL].annotations.read_only_hint)
            self.assertEqual(set(tools[TOOL].input_schema["properties"]), {"action", "expected_revision"})
            self.assertEqual(set(tools[TOOL].input_schema["properties"]["action"]["enum"]), {"adopt", "promote", "demote", "abandon"})
            arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"], "action": action}
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=SimpleNamespace(hex="cooldown-fixture")):
                reply = await client.call_tool(TOOL, arguments)
            return arguments, reply

    async def test_full_native_packets_preserve_absent_active_expired_and_unknown_without_detail(self):
        names = [f"{action}-absent.json" for action in ("adopt", "promote", "demote", "abandon")]
        names += ["promote-active-afterdetail-none.json", "promote-expired.json", "changed-registry.json", "foreign-key.json", "foreign-build.json"]
        for filename in names:
            with self.subTest(filename=filename):
                driver, endpoint, packet = self.setup_driver(filename)
                original = deepcopy(packet)
                native = packet["result"]["player_holy_site_decision_cooldown"]
                try:
                    arguments, reply = await self.call(driver, native["action"])
                    self.actual_mcp_results.append({"fixture": filename, "native_packet": original,
                        "arguments": arguments, "requests": endpoint.requests, "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    for key in ("available", "unavailable_reason", "action", "decision_key",
                                "native_decision_cooldown_observed", "native_decision_cooldown"):
                        self.assertEqual(actual[key], native[key])
                    self.assertFalse(actual["detail_open_required"])
                    self.assertFalse(actual["action_ready"])
                    self.assertFalse(actual["decision_confirm_invoked"])
                    if not actual["available"]:
                        self.assertIsNone(actual["native_decision_cooldown"])
                    elif filename.endswith("-absent.json"):
                        self.assertFalse(actual["native_decision_cooldown"]["present"])
                        self.assertIsNone(actual["native_decision_cooldown"]["expiry_raw"])
                    else:
                        self.assertEqual(actual["native_decision_cooldown"]["active"], filename == "promote-active-afterdetail-none.json")
                        self.assertFalse(actual["native_decision_cooldown"]["calendar_conversion_observed"])
                    self.assertEqual(len(endpoint.requests), 1)
                    self.assertEqual(endpoint.requests[0]["action"], native["action"])
                    self.assertNotIn("holy_site_id", endpoint.requests[0])
                    self.assertEqual(packet, original)
                finally:
                    driver.close()

    async def test_bad_action_rejects_before_native_io(self):
        from mcp import Client
        for bad in ("elevate", "adopt_holy_site_decision", "ordinary_decision", 1, None):
            driver, endpoint, _ = self.setup_driver("adopt-absent.json")
            try:
                async with Client(create_server(driver)) as client:
                    revision = driver.take_snapshot_without_native_command_history()["revision"]
                    reply = await client.call_tool(TOOL, {"expected_revision": revision, "action": bad})
                    self.assertTrue(reply.is_error)
                    self.assertEqual(endpoint.requests, [])
            finally:
                driver.close()

    async def test_strict_native_source_identity_and_unknown_semantics(self):
        driver, _, packet = self.setup_driver("promote-active-afterdetail-none.json")
        try:
            snapshot = driver.take_snapshot_without_native_command_history()
            original = packet["result"]["player_holy_site_decision_cooldown"]
            self.assertTrue(normalize_holy_site_decision_cooldown_v1(original, snapshot=snapshot, action="promote")["available"])
            mutations = [lambda v: v.update(decision_key="adopt_holy_site_decision"),
                         lambda v: v["native_decision_cooldown"].update(active=False),
                         lambda v: v["native_decision_cooldown"].update(calendar_conversion_observed=True),
                         lambda v: v.update(executable_sha256="foreign-exe"),
                         lambda v: v.update(available=False, unavailable_reason="unknown", native_decision_cooldown_observed=False)]
            for mutate in mutations:
                value = deepcopy(original)
                mutate(value)
                with self.assertRaises(ValueError):
                    normalize_holy_site_decision_cooldown_v1(value, snapshot=snapshot, action="promote")
        finally:
            driver.close()



if __name__ == "__main__":
    unittest.main()
