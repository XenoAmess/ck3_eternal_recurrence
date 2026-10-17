"""New compiled decision-detail packets through Driver -> Service -> real MCP.

Set XAR_HOLY_SITE_DECISION_FIXTURES to the freshly compiled native output.
Only transport hello/snapshot scaffolding is synthetic. Positive result DTOs
are never constructed here. Missing new packets remain native-pending.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import get_args
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.holy_site_decision_action_v1 import (
    HOLY_SITE_DECISION_KEYS_V1, HolySiteDecisionActionV1,
    holy_site_decision_key_v1, normalize_holy_site_decision_action_v1,
)
from xar_autoplayer.bridge.holy_site_adoption_detail_private_transport import (
    query_holy_site_decision_detail_private_v1,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_player_holy_site_decision_detail_v1"
STEP = "query-player-holy-site-decision-detail-v1"
PERMISSION = "allow_private_holy_site_adoption_detail_query"
BODY = "player_holy_site_decision_detail"
FIXTURES = os.environ.get("XAR_HOLY_SITE_DECISION_FIXTURES")
FIXTURE_ACTIONS = {
    "promote-native-false.json": "promote",
    "promote-native-true.json": "promote",
    "demote-native-false.json": "demote",
    "demote-native-true.json": "demote",
    "abandon-native-false.json": "abandon",
    "abandon-native-true.json": "abandon",
    "cross-action-rejected.json": "promote",
    "invalid-action-rejected.json": "promote",
}


class Endpoint:
    pipe_name = r"\\.\pipe\holy-site-decision-compiled-source-fixture-only"

    def __init__(self, packet=None):
        self.packet, self.requests, self.on_frame = packet, [], None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request["type"] == "execute_step":
            self.requests.append(deepcopy(request))
            if self.packet is None:
                raise AssertionError("parameter rejection must happen before native I/O")
            assert request["request_id"] == self.packet["request_id"]
            assert request["step"] == STEP
            self.publish(self.packet)

    def transport_error(self):
        return None

    def close(self):
        pass


def driver_for(packet=None, *, enabled=True):
    """Frame scaffolding only; result business fields always come from C++."""
    endpoint = Endpoint(packet)
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                         command_timeout_seconds=1.0)
    setattr(driver, PERMISSION, enabled)
    result = packet["result"] if packet else None
    primary = result[BODY] if result else None
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
        "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
        "capabilities": ["game.state.snapshot", "game.command." + STEP]})
    endpoint.publish({"type": "state_snapshot", "protocol_version": 1, "snapshot_id": "native:701",
        "revision": result["snapshot_revision"] if result else 701, "state": {
            "phase": "map_hud", "date": "synthetic-frame-scaffolding-only",
            "date_raw": result["date_raw"] if result else 123456,
            "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
            "pending_character_interaction": None, "player_armies": [], "active_wars": [],
            "played_character": {"character_id": primary["played_character_id"] if primary else 29829,
                                 "alive": True}}})
    return driver, endpoint


class ActionIdentityTests(unittest.TestCase):
    def test_only_four_fixed_actions_and_original_decision_keys(self):
        expected = {"adopt": "adopt_holy_site_decision", "promote": "elevate_holy_site_decision",
                    "demote": "demote_holy_site_decision", "abandon": "abandon_holy_site_decision"}
        self.assertEqual(set(get_args(HolySiteDecisionActionV1)), set(expected))
        self.assertEqual(dict(HOLY_SITE_DECISION_KEYS_V1), expected)
        for action, key in expected.items():
            self.assertEqual(holy_site_decision_key_v1(action), key)
        with self.assertRaises(TypeError):
            HOLY_SITE_DECISION_KEYS_V1["promote"] = "arbitrary_decision"

    def test_invalid_enum_and_raw_decision_key_fail_before_transport(self):
        for action in (None, True, 1, {}, [], "", "Promote", "elevate", "promote ",
                       "elevate_holy_site_decision", "arbitrary_decision"):
            with self.subTest(action=action):
                with self.assertRaises(ValueError):
                    normalize_holy_site_decision_action_v1(action)
                # An object without endpoint/state proves admission precedes I/O.
                with self.assertRaises(ValueError):
                    query_holy_site_decision_detail_private_v1(
                        object(), expected_revision=1, action=action, holy_site_id=0x81000002)


class ReadOnlyWiringAstTests(unittest.TestCase):
    def test_generic_tool_routes_through_service_without_arbitrary_decision_key(self):
        path = REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        tool = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == TOOL)
        self.assertEqual([a.arg for a in tool.args.args], ["action", "holy_site_id", "expected_revision"])
        self.assertEqual(ast.unparse(tool.args.args[0].annotation), "HolySiteDecisionActionV1")
        returned = next(n.value for n in tool.body if isinstance(n, ast.Return))
        self.assertEqual(ast.unparse(returned.func), "service.query_player_holy_site_decision_detail_v1")
        annotations = next(k.value for k in tool.decorator_list[0].keywords if k.arg == "annotations")
        self.assertIs(next(k.value.value for k in annotations.keywords if k.arg == "readOnlyHint"), True)
        self.assertIs(next(k.value.value for k in annotations.keywords if k.arg == "destructiveHint"), False)
        self.assertTrue(callable(GameplayBridgeService.query_player_holy_site_decision_detail_v1))
        self.assertTrue(callable(NativeHeadlessGameplayDriver.query_holy_site_decision_detail_private_v1))


class ActionParameterMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_management_and_independent_cooldown_tools_have_only_fixed_inputs(self):
        from mcp import Client, ClientSession
        driver, endpoint = driver_for()
        surfaces = {
            TOOL: (True, False, {"action", "holy_site_id", "expected_revision"}),
            "ck3_query_player_holy_site_decision_cooldown_v1": (True, False, {"action", "expected_revision"}),
            "ck3_open_holy_site_decision_v1": (False, False, {"action", "holy_site_id", "expected_revision"}),
            "ck3_confirm_holy_site_decision_v1": (False, True, {"action", "holy_site_id", "expected_revision"}),
        }
        try:
            async with Client(create_server(driver)) as client:
                self.assertIsInstance(client.session, ClientSession)
                tools = {item.name: item for item in (await client.session.list_tools()).tools}
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                for name, (readonly, destructive, properties) in surfaces.items():
                    tool = tools[name]
                    self.assertEqual(set(tool.input_schema["properties"]), properties)
                    self.assertEqual(set(tool.input_schema["required"]), properties)
                    self.assertIs(tool.input_schema["additionalProperties"], False)
                    self.assertEqual(set(tool.input_schema["properties"]["action"]["enum"]),
                                     {"adopt", "promote", "demote", "abandon"})
                    self.assertIs(tool.annotations.read_only_hint, readonly)
                    self.assertIs(tool.annotations.destructive_hint, destructive)
                    arguments = {"action": "promote", "expected_revision": revision}
                    if "holy_site_id" in properties:
                        arguments["holy_site_id"] = 0x81000002
                    for invalid in ({"action": "arbitrary_decision"}, {"decision_key": "elevate_holy_site_decision"},
                                    {"native_pointer": 0x140000000}, {"bypass_requirements": True}):
                        reply = await client.session.call_tool(name, {**arguments, **invalid})
                        self.assertTrue(reply.is_error)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_literal_and_extra_argument_rejections_over_real_mcp_before_native_io(self):
        from mcp import Client, ClientSession
        driver, endpoint = driver_for()
        try:
            async with Client(create_server(driver)) as client:
                self.assertIsInstance(client.session, ClientSession)
                tools = {item.name: item for item in (await client.session.list_tools()).tools}
                self.assertEqual(set(tools[TOOL].input_schema["properties"]["action"]["enum"]),
                                 {"adopt", "promote", "demote", "abandon"})
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                for invalid in ({"action": "elevate"}, {"action": "elevate_holy_site_decision"},
                                {"action": ""}, {"action": None}, {"action": True}, {"action": 1},
                                {"decision_key": "elevate_holy_site_decision"}, {"confirm": True}):
                    reply = await client.session.call_tool(TOOL,
                        {"action": "promote", "holy_site_id": 0x81000002,
                         "expected_revision": revision, **invalid})
                    self.assertTrue(reply.is_error)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()


@unittest.skipUnless(FIXTURES, "native_pending: requires newly compiled four-action decision-detail packets")
class HolySiteDecisionDetailNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def load_packet(self, filename):
        path = Path(FIXTURES) / filename
        raw = path.read_bytes()
        packet = json.loads(raw.decode("utf-8-sig"))
        self.assertEqual(packet["type"], "command_result")
        self.assertEqual(packet["result"]["step"], STEP)
        return path, raw, packet

    async def call_packet(self, driver, packet, action):
        from mcp import Client, ClientSession
        self.assertTrue(packet["request_id"].startswith("g2-read-"))
        native = packet["result"][BODY]
        arguments = {"action": action, "holy_site_id": native["requested_holy_site_id"],
                     "expected_revision": driver.take_snapshot_without_native_command_history()["revision"]}
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session, ClientSession)
            tools = {item.name: item for item in (await client.session.list_tools()).tools}
            self.assertTrue(tools[TOOL].annotations.read_only_hint)
            self.assertEqual(set(tools[TOOL].input_schema["properties"]),
                             {"action", "holy_site_id", "expected_revision"})
            with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                       return_value=SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])):
                reply = await client.session.call_tool(TOOL, arguments)
        return arguments, reply

    async def test_new_compiled_true_false_and_cross_action_native_rejection_packets(self):
        for filename, action in FIXTURE_ACTIONS.items():
            if filename == "invalid-action-rejected.json":
                continue
            with self.subTest(fixture=filename):
                path, raw, packet = self.load_packet(filename)
                original = deepcopy(packet)
                native = packet["result"][BODY]
                driver, endpoint = driver_for(packet)
                self.assertEqual(Path(inspect.getfile(type(driver))).resolve(),
                    (REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").resolve())
                try:
                    arguments, reply = await self.call_packet(driver, packet, action)
                    self.actual_mcp_results.append({"fixture": path.name,
                        "fixture_sha256": hashlib.sha256(raw).hexdigest(), "native_packet": original,
                        "arguments": arguments, "requests": endpoint.requests,
                        "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    self.assertEqual(actual["action"], action)
                    self.assertEqual(actual["requested_decision_key"], holy_site_decision_key_v1(action))
                    self.assertEqual(actual["schema"], "ck3_12004_holy_site_decision_detail_v1")
                    for key in ("available", "unavailable_reason", "decision_key", "native_can_confirm",
                                "normal_requirements_legality_observed", "normal_requirements_can_confirm",
                                "native_resource_quote_available", "native_resource_quote",
                                "native_detail_context_verified", "native_requirements_description_available",
                                "native_requirements_description", "native_cost_description_available",
                                "native_cost_description", "native_decision_cooldown_observed",
                                "native_decision_cooldown"):
                        self.assertEqual(actual[key], native[key])
                    self.assertTrue(actual["read_only"])
                    for key in ("action_ready", "decision_confirm_invoked", "adoption_completed_observed"):
                        self.assertIs(actual[key], False)
                    if filename == "cross-action-rejected.json":
                        self.assertIs(actual["available"], False)
                        self.assertIsNone(actual["decision_key"])
                        self.assertIsNone(actual["native_can_confirm"])
                        self.assertTrue(actual["unavailable_reason"])
                    else:
                        self.assertIs(actual["available"], True)
                        self.assertEqual(actual["decision_key"], holy_site_decision_key_v1(action))
                        self.assertIs(actual["normal_requirements_can_confirm"], "-true" in filename)
                    if actual["native_decision_cooldown_observed"]:
                        self.assertEqual(actual["native_decision_cooldown"]["decision_key"],
                                         holy_site_decision_key_v1(action))
                    self.assertEqual(len(endpoint.requests), 1)
                    request = endpoint.requests[0]
                    self.assertEqual(request["action"], action)
                    self.assertEqual(request["holy_site_id"], native["requested_holy_site_id"])
                    self.assertNotIn("decision_key", request)
                    self.assertEqual(request["expected_snapshot_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(packet, original)
                finally:
                    driver.close()

    async def test_invalid_cpp_enum_packet_is_rejected_without_claiming_public_reachability(self):
        path, raw, packet = self.load_packet("invalid-action-rejected.json")
        native = packet["result"][BODY]
        self.assertEqual(native["action"], "")
        self.assertEqual(native["requested_decision_key"], "")
        self.assertIs(native["available"], False)
        driver, endpoint = driver_for(packet)
        try:
            arguments, reply = await self.call_packet(driver, packet, "promote")
            self.assertTrue(reply.is_error)
            self.assertEqual(len(endpoint.requests), 1)
            self.actual_mcp_results.append({"fixture": path.name,
                "fixture_sha256": hashlib.sha256(raw).hexdigest(), "native_packet": packet,
                "input_origin": "compiled fixture passed invalid C++ enum directly; unreachable through public Literal",
                "arguments": arguments, "requests": endpoint.requests,
                "response": reply.model_dump(mode="json")})
        finally:
            driver.close()

    async def test_explicit_cross_action_packet_corruption_is_not_native_evidence(self):
        path, raw, packet = self.load_packet("promote-native-false.json")
        for name in ("self-consistent-foreign-action", "foreign-requested-key", "foreign-actual-key"):
            changed = deepcopy(packet)
            native = changed["result"][BODY]
            if name == "self-consistent-foreign-action":
                native["action"] = "demote"
                native["requested_decision_key"] = holy_site_decision_key_v1("demote")
                native["decision_key"] = holy_site_decision_key_v1("demote")
                if native["native_decision_cooldown_observed"]:
                    native["native_decision_cooldown"]["decision_key"] = holy_site_decision_key_v1("demote")
            elif name == "foreign-requested-key":
                native["requested_decision_key"] = holy_site_decision_key_v1("demote")
            else:
                native["decision_key"] = holy_site_decision_key_v1("demote")
            driver, endpoint = driver_for(changed)
            try:
                arguments, reply = await self.call_packet(driver, changed, "promote")
                self.assertTrue(reply.is_error)
                self.assertEqual(len(endpoint.requests), 1)
                self.actual_mcp_results.append({"negative_case": name,
                    "explicit_manual_mutation": True, "native_failure_observed": False,
                    "source_compiled_packet": path.name, "source_sha256": hashlib.sha256(raw).hexdigest(),
                    "mutated_packet": changed, "arguments": arguments,
                    "response": reply.model_dump(mode="json")})
            finally:
                driver.close()


if __name__ == "__main__":
    unittest.main()
