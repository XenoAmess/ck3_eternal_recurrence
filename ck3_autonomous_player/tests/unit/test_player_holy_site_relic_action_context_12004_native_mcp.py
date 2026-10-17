"""New compiled action-context packets through actual Driver/Service/MCP.

Positive DTOs are exclusively C++ reader/serializer outputs. Endpoint I/O,
hello and frame snapshots are synthetic. Common hooks are SHA-bound source
increments applied before bridge __init__, never monkeypatched service calls.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get("XAR_RELIC_ACTION_CONTEXT_BASE_SOURCE_ROOT", str(REPO)))
overlay_path = REPO / "ck3_autonomous_player/native_bridge/research/relic_action_context_source_overlay.py"
spec = importlib.util.spec_from_file_location("relic_action_context_source_overlay", overlay_path)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
if REPO.resolve() == BASE.resolve():
    sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
    HOOKS = None
else:
    HOOKS = overlay.install(BASE, REPO)


def source_for(relative):
    if HOOKS is None:
        path = BASE / relative
        return path, path.read_text(encoding="utf-8-sig"), None
    return overlay.candidate_source(BASE, HOOKS, relative)


from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_player_holy_site_relic_action_context_v1"
STEP = "query-player-holy-site-relic-action-context-v1"
PERMISSION = "allow_private_player_holy_site_relic_action_context_query"
RESULT_KEY = "player_holy_site_relic_action_context"
FIXTURES = os.environ.get("XAR_RELIC_ACTION_CONTEXT_NATIVE_FIXTURES")
REQUIRED_FIXTURES = frozenset(json.loads(os.environ.get("XAR_RELIC_ACTION_CONTEXT_REQUIRED_FIXTURES", "[]")))


class Endpoint:
    pipe_name = r"\\.\pipe\relic-action-context-compiled-source-fixture-only"

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
            assert request["step"] == STEP
            self.publish(self.packet)

    def transport_error(self):
        return None

    def close(self):
        pass


def fixture_packets():
    rows = []
    if FIXTURES:
        for path in sorted(Path(FIXTURES).glob("*.json")):
            raw = path.read_bytes()
            packet = json.loads(raw.decode("utf-8-sig"))
            if (isinstance(packet, dict) and packet.get("type") == "command_result"
                    and isinstance(packet.get("result"), dict) and packet["result"].get("step") == STEP):
                rows.append((path, raw, packet))
    return rows


class PublicOptinTests(unittest.TestCase):
    def test_standalone_cli_shared_case_and_service_are_independent_default_off(self):
        flag = "--private-player-holy-site-relic-action-context-query"
        self.assertFalse(parser().parse_args([]).private_player_holy_site_relic_action_context_query)
        args = parser().parse_args([flag])
        self.assertTrue(args.private_player_holy_site_relic_action_context_query)
        self.assertFalse(args.private_player_holy_site_relic_permissions_query)
        self.assertFalse(args.private_player_holy_site_relic_context_query)
        self.assertFalse(args.private_player_holy_site_query)
        self.assertTrue(callable(GameplayBridgeService.query_player_holy_site_relic_action_context_v1))
        host_path, host_source, _ = source_for("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
        tree = ast.parse(host_source)
        parser_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parser")
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute) and target.attr == PERMISSION for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        namespace = dict(argparse=argparse, Path=Path, __file__=str(host_path), sys=sys, os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser_function], type_ignores=[])), str(host_path), "exec"), namespace)
        for tools in ((), (TOOL,)):
            args = namespace["parser"]().parse_args([item for tool in tools for item in ("--case-read-only-mcp-tool", tool)])
            driver = SimpleNamespace(case_declared_read_only_mcp_tools=frozenset(args.case_read_only_mcp_tool))
            exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])), str(host_path), "exec"), {"driver": driver})
            self.assertEqual(getattr(driver, PERMISSION), bool(tools))
            self.assertFalse(getattr(driver, "allow_private_player_holy_site_relic_permissions_query", False))
        acceptance_path, acceptance_source, _ = source_for("tools/ck3_mod_acceptance.py")
        acceptance = ast.parse(acceptance_source, str(acceptance_path))
        allowed = next(node for node in acceptance.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_READ_ONLY_MCP_TOOLS" for target in node.targets))
        self.assertIn(TOOL, ast.literal_eval(allowed.value.args[0]))
        _, mcp_source, _ = source_for("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py")
        tool_body = next(node for node in ast.walk(ast.parse(mcp_source))
                         if isinstance(node, ast.FunctionDef) and node.name == TOOL)
        result = next(node.value for node in tool_body.body if isinstance(node, ast.Return))
        self.assertEqual((result.func.value.id, result.func.attr), ("service", "query_player_holy_site_relic_action_context_v1"))


@unittest.skipUnless(FIXTURES, "requires new compiled action-context reader/serializer command_result packets")
class RelicActionContextNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, packet, *, enabled=True, frame_packet=None):
        self.assertEqual(Path(inspect.getfile(NativeHeadlessGameplayDriver)).resolve(),
                         (BASE / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").resolve())
        self.assertTrue(callable(NativeHeadlessGameplayDriver.query_player_holy_site_relic_action_context_private_v1))
        source_frame = frame_packet or packet
        native = source_frame["result"][RESULT_KEY]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        setattr(driver, PERMISSION, enabled)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command." + STEP]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:relic-action-context-fixture", "revision": source_frame["result"]["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": native["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": native["played_character_id"], "alive": True}}})
        return driver, endpoint

    async def call_native(self, session, driver, request_source):
        native = request_source["result"][RESULT_KEY]
        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                     "holy_site_id": native["requested_holy_site_id"], "artifact_id": native["requested_artifact_id"]}
        self.assertTrue(request_source["request_id"].startswith("g2-read-"))
        request_uuid = SimpleNamespace(hex=request_source["request_id"][len("g2-read-"):])
        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=request_uuid):
            reply = await session.call_tool(TOOL, arguments)
        return arguments, reply

    async def test_new_compiled_packets_cross_actual_driver_service_and_mcp_client_session(self):
        from mcp import Client, ClientSession
        packets = fixture_packets()
        self.assertTrue(REQUIRED_FIXTURES, "freeze this domain's new producer packet names before qualification")
        self.assertEqual(REQUIRED_FIXTURES, {path.name for path, _, _ in packets})
        for path, raw, packet in packets:
            with self.subTest(fixture=path.name):
                original = deepcopy(packet)
                native = packet["result"][RESULT_KEY]
                driver, endpoint = self.setup_driver(packet)
                try:
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session, ClientSession)
                        tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
                        tool = tools[TOOL]
                        self.assertTrue(tool.annotations.read_only_hint)
                        self.assertFalse(tool.annotations.destructive_hint)
                        self.assertFalse(tool.annotations.idempotent_hint)
                        self.assertFalse(tool.annotations.open_world_hint)
                        self.assertEqual(set(tool.input_schema["properties"]), {"expected_revision", "holy_site_id", "artifact_id"})
                        self.assertEqual(set(tool.input_schema["required"]), {"expected_revision", "holy_site_id", "artifact_id"})
                        self.assertNotIn("ck3_query_player_holy_site_relic_permissions_v1", tools)
                        arguments, reply = await self.call_native(client.session, driver, packet)
                    self.actual_mcp_results.append({"fixture": path.name, "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                        "native_packet": original, "arguments": arguments, "requests": endpoint.requests,
                        "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    for key, expected in native.items():
                        self.assertEqual(actual[key], expected, key)
                    self.assertFalse(actual["action_ready"])
                    self.assertFalse(actual["loaded_source_pins_verified"])
                    self.assertIn(actual["evaluation_context"]["getter_backend"], {"owned_fixture_injected_getter", "unavailable"})
                    self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                    self.assertNotEqual(actual["capture_epoch"], actual["queried_native_revision"])
                    self.assertNotEqual(arguments["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(len(endpoint.requests), 1)
                    request = endpoint.requests[0]
                    for key in ("holy_site_id", "artifact_id"):
                        self.assertEqual(request[key], native["requested_" + key])
                    self.assertEqual(request["expected_snapshot_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(request["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(packet, original)
                    if path.name in {"faith-drift.json", "ownership-drift.json"}:
                        self.assertFalse(native["available"])
                        self.assertFalse(native["preview_identity_available"])
                        self.assertIsNone(native["preview_identity_sha256"])
                finally:
                    driver.close()

    async def test_optin_off_and_required_strict_full_ids_reject_before_native_io(self):
        from mcp import Client, ClientSession
        packet = fixture_packets()[0][2]
        driver, endpoint = self.setup_driver(packet, enabled=False)
        try:
            async with Client(create_server(driver)) as client:
                self.assertIsInstance(client.session, ClientSession)
                self.assertNotIn(TOOL, {item.name for item in (await client.session.list_tools()).tools})
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()
        driver, endpoint = self.setup_driver(packet)
        try:
            async with Client(create_server(driver)) as client:
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                source = packet["result"][RESULT_KEY]
                valid = {"expected_revision": revision, "holy_site_id": source["requested_holy_site_id"],
                         "artifact_id": source["requested_artifact_id"]}
                arguments = [{k: v for k, v in valid.items() if k != field} for field in valid]
                arguments.extend(({**valid, "enshrine": True}, {**valid, "expected_revision": revision + 1},
                                  {**valid, "expected_revision": True}))
                for field in ("holy_site_id", "artifact_id"):
                    for bad in (None, True, "1", -1, 0xFFFFFFFF, 2**32, 1.25):
                        arguments.append({**valid, field: bad})
                for args in arguments:
                    reply = await client.session.call_tool(TOOL, args)
                    self.assertTrue(reply.is_error, args)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_explicit_mutations_keep_original_request_and_frame_and_fail_closed(self):
        from mcp import Client
        source_path, source_raw, source = next((path, raw, packet) for path, raw, packet in fixture_packets()
            if packet["result"][RESULT_KEY]["preview_identity_available"])
        mutations = {
            "foreign-build": lambda p: p["result"].update(game_version="1.20.1.1"),
            "different-requested-site": lambda p: p["result"][RESULT_KEY].update(
                requested_holy_site_id=p["result"][RESULT_KEY]["requested_holy_site_id"] ^ 1),
            "different-requested-artifact": lambda p: p["result"][RESULT_KEY].update(
                requested_artifact_id=p["result"][RESULT_KEY]["requested_artifact_id"] ^ 1),
            "different-player": lambda p: p["result"][RESULT_KEY].update(
                played_character_id=p["result"][RESULT_KEY]["played_character_id"] ^ 1),
            "different-date": lambda p: p["result"][RESULT_KEY].update(date_raw=p["result"][RESULT_KEY]["date_raw"] + 1),
            "missing-nested-permissions": lambda p: p["result"][RESULT_KEY].pop("permissions"),
            "window-selection-written": lambda p: p["result"][RESULT_KEY]["evaluation_context"].update(window_selection_written=True),
            "invented-action-readiness": lambda p: p["result"][RESULT_KEY].update(action_ready=True),
            "wrong-preview-canonical-hash": lambda p: p["result"][RESULT_KEY].update(preview_identity_sha256="0" * 64),
            "text-changed-without-new-preview-hash": lambda p: p["result"][RESULT_KEY]["selected_action_effect_description"].update(text="explicit test mutation"),
            "effective-slot-permission-invented": lambda p: p["result"][RESULT_KEY]["destination"].update(effective_slot_script_permission_independently_observed=True),
            "faith-changed-without-new-preview-hash": lambda p: p["result"][RESULT_KEY]["permissions"].update(
                player_faith_id=p["result"][RESULT_KEY]["permissions"]["player_faith_id"] ^ 1),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                altered = deepcopy(source)
                mutate(altered)
                driver, endpoint = self.setup_driver(altered, frame_packet=source)
                try:
                    async with Client(create_server(driver)) as client:
                        arguments, reply = await self.call_native(client.session, driver, source)
                    self.assertTrue(reply.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.actual_mcp_results.append({"negative_case": name, "explicit_mutation_of_compiled_packet": True,
                        "source_compiled_packet": source_path.name,
                        "source_compiled_packet_sha256": hashlib.sha256(source_raw).hexdigest(),
                        "altered_packet": altered, "native_failure_observed": False,
                        "request_and_frame_source": "original_compiled_packet",
                        "arguments": arguments, "response": reply.model_dump(mode="json")})
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()
