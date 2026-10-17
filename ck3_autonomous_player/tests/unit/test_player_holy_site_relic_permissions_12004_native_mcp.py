"""Only newly compiled native permissions packets provide positive DTO inputs.

Endpoint hello/state/I/O is synthetic. Driver, Service, FastMCP and ClientSession
execute actual source with the exact SHA-bound incremental candidate hooks.
The common modules are patched in memory before base bridge initialization;
neither the main tree nor another agent's source/build is changed or copied.
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
BASE = Path(os.environ.get("XAR_RELIC_PERMISSIONS_BASE_SOURCE_ROOT", str(REPO)))
overlay_path = REPO / "ck3_autonomous_player/native_bridge/research/relic_permissions_source_overlay.py"
spec = importlib.util.spec_from_file_location("relic_permissions_source_overlay", overlay_path)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
if REPO.resolve() == BASE.resolve():
    # Once merged, load the ordinary repository modules without an old overlay.
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

TOOL = "ck3_query_player_holy_site_relic_permissions_v1"
STEP = "query-player-holy-site-relic-permissions-v1"
PERMISSION = "allow_private_player_holy_site_relic_permissions_query"
RESULT_KEY = "player_holy_site_relic_permissions"
FIXTURES = os.environ.get("XAR_RELIC_PERMISSIONS_NATIVE_FIXTURES")
REQUIRED_FIXTURES = frozenset(json.loads(os.environ.get("XAR_RELIC_PERMISSIONS_REQUIRED_FIXTURES", "[]")))


class Endpoint:
    pipe_name = r"\\.\pipe\relic-permissions-compiled-source-fixture-only"

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
    def test_standalone_cli_shared_case_and_service_hooks_are_independent_default_off(self):
        flag = "--private-player-holy-site-relic-permissions-query"
        self.assertFalse(parser().parse_args([]).private_player_holy_site_relic_permissions_query)
        args = parser().parse_args([flag])
        self.assertTrue(args.private_player_holy_site_relic_permissions_query)
        self.assertFalse(args.private_player_holy_site_relic_context_query)
        self.assertFalse(args.private_player_holy_site_query)
        self.assertFalse(args.private_holy_site_adoption_detail_query)
        self.assertTrue(callable(GameplayBridgeService.query_player_holy_site_relic_permissions_v1))
        host_path, host_source, _ = source_for(
            "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
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
            self.assertFalse(getattr(driver, "allow_private_player_holy_site_relic_context_query", False))
        acceptance_path, acceptance_source, _ = source_for("tools/ck3_mod_acceptance.py")
        acceptance = ast.parse(acceptance_source, str(acceptance_path))
        allowed = next(node for node in acceptance.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_READ_ONLY_MCP_TOOLS" for target in node.targets))
        self.assertIn(TOOL, ast.literal_eval(allowed.value.args[0]))
        _, mcp_source, _ = source_for("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py")
        tool_body = next(node for node in ast.walk(ast.parse(mcp_source))
                         if isinstance(node, ast.FunctionDef) and node.name == TOOL)
        result = next(node.value for node in tool_body.body if isinstance(node, ast.Return))
        self.assertEqual((result.func.value.id, result.func.attr), ("service", "query_player_holy_site_relic_permissions_v1"))


@unittest.skipUnless(FIXTURES, "requires newly compiled permissions reader/serializer command_result packets")
class RelicPermissionsNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, packet, *, enabled=True):
        self.assertEqual(Path(inspect.getfile(NativeHeadlessGameplayDriver)).resolve(),
                         (BASE / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").resolve())
        self.assertTrue(callable(NativeHeadlessGameplayDriver.query_player_holy_site_relic_permissions_private_v1))
        native = packet["result"][RESULT_KEY]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        setattr(driver, PERMISSION, enabled)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command." + STEP]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:relic-permissions-fixture", "revision": packet["result"]["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": native["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": native["played_character_id"], "alive": True}}})
        return driver, endpoint

    async def call_native(self, session, driver, packet):
        native = packet["result"][RESULT_KEY]
        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                     "holy_site_id": native["requested_holy_site_id"]}
        if native["requested_artifact_id"] is not None:
            arguments["artifact_id"] = native["requested_artifact_id"]
        self.assertTrue(packet["request_id"].startswith("g2-read-"))
        request_uuid = SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])
        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=request_uuid):
            reply = await session.call_tool(TOOL, arguments)
        return arguments, reply

    async def test_new_compiled_packets_cross_real_driver_service_and_mcp_client_session(self):
        from mcp import Client, ClientSession
        packets = fixture_packets()
        self.assertTrue(REQUIRED_FIXTURES, "freeze the producer's required new fixture names before qualification")
        self.assertEqual(REQUIRED_FIXTURES, {path.name for path, _, _ in packets},
                         "requires exactly the frozen new permissions packet set")
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
                        self.assertEqual(set(tool.input_schema["required"]), {"expected_revision", "holy_site_id"})
                        self.assertNotIn("ck3_query_player_holy_site_relic_context_v1", tools)
                        self.assertNotIn("ck3_query_player_holy_site_v1", tools)
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
                    self.assertIn(actual["evaluation_context"]["getter_backend"],
                                  {"owned_fixture_injected_getter", "unavailable"})
                    self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                    self.assertNotEqual(actual["capture_epoch"], actual["queried_native_revision"])
                    self.assertNotEqual(arguments["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(len(endpoint.requests), 1)
                    request = endpoint.requests[0]
                    self.assertEqual(request["holy_site_id"], native["requested_holy_site_id"])
                    self.assertEqual(request.get("artifact_id"), native["requested_artifact_id"])
                    self.assertEqual(request["expected_snapshot_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(request["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(packet, original)
                    if path.name == "selected-different.json":
                        self.assertNotEqual(native["requested_artifact_id"], native["current_buttons"]["selected_artifact_id"])
                        self.assertIs(native["current_buttons"]["context_matches_requested_artifact"], False)
                    elif path.name == "nonowned-permission.json":
                        self.assertIs(native["artifact_permissions"]["player_inventory_contains_reference"], False)
                        self.assertIs(native["artifact_permissions"]["can_enshrine"]["value"], True)
                        self.assertIs(native["action_ready"], False)
                    elif path.name in {"window-unavailable.json", "foreign-slot.json"}:
                        self.assertFalse(native["window_context"]["available"])
                        self.assertTrue(native["current_candidates"]["available"])
                        self.assertFalse(native["artifact_permissions"]["available"])
                    elif path.name == "stale-artifact.json":
                        self.assertFalse(native["artifact_permissions"]["object_resolved"])
                        self.assertIsNone(native["artifact_permissions"]["can_enshrine"]["value"])
                    elif path.name == "stale-site-generation.json":
                        self.assertFalse(native["available"])
                        self.assertIsNone(native["holy_site_id"])
                    elif path.name == "predicate-unavailable.json":
                        self.assertFalse(native["current_candidates"]["available"])
                        self.assertIsNone(native["current_candidates"]["artifact_ids"])
                        self.assertIsInstance(native["current_candidates"]["evaluations"], list)
                    elif path.name == "no-artifact-request.json":
                        self.assertIsNone(native["requested_artifact_id"])
                        self.assertEqual(native["artifact_permissions"]["unavailable_reason"], "artifact_id_not_requested")
                        self.assertIsNone(native["current_buttons"]["context_matches_requested_artifact"])
                    elif path.name == "empty-player-inventory.json":
                        self.assertTrue(native["player_inventory"]["available"])
                        self.assertEqual(native["player_inventory"]["artifact_ids"], [])
                        self.assertEqual(native["current_candidates"]["artifact_ids"], [])
                        self.assertEqual(native["current_candidates"]["evaluations"], [])
                    elif path.name == "cache-unavailable.json":
                        self.assertTrue(native["window_context"]["available"])
                        self.assertFalse(native["window_context"]["cached_candidates"]["available"])
                        self.assertTrue(native["artifact_permissions"]["available"])
                    elif path.name == "automatic-slot.json":
                        self.assertTrue(native["window_context"]["available"])
                        self.assertEqual(native["window_context"]["slot_mode"], "native_automatic")
                        self.assertIsNone(native["window_context"]["selected_slot_index"])
                        self.assertIsNone(native["window_context"]["selected_slot_artifact_id"])
                finally:
                    driver.close()

    async def test_optin_off_and_strict_input_reject_before_native_io(self):
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
                site = packet["result"][RESULT_KEY]["requested_holy_site_id"]
                arguments = [{"expected_revision": revision},
                             {"expected_revision": revision, "holy_site_id": site, "enshrine": True},
                             {"expected_revision": revision + 1, "holy_site_id": site},
                             {"expected_revision": True, "holy_site_id": site}]
                for field in ("holy_site_id", "artifact_id"):
                    for bad in (True, "1", -1, 0xFFFFFFFF, 2**32, 1.25):
                        arguments.append({"expected_revision": revision, "holy_site_id": site, field: bad})
                for args in arguments:
                    reply = await client.session.call_tool(TOOL, args)
                    self.assertTrue(reply.is_error, args)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_explicit_mutations_of_compiled_packets_fail_closed_over_real_mcp(self):
        from mcp import Client
        source_path, source_raw, packet = next((path, raw, packet) for path, raw, packet in fixture_packets()
            if packet["result"][RESULT_KEY]["available"]
            and packet["result"][RESULT_KEY]["window_context"]["available"]
            and packet["result"][RESULT_KEY]["artifact_permissions"]["available"])

        def unknown_permission(p):
            p["result"][RESULT_KEY]["artifact_permissions"]["can_remove"].update(
                available=False, value=False, unavailable_reason="explicit_test_mutation_unknown")

        def invented_candidate_list(p):
            current = p["result"][RESULT_KEY]["current_candidates"]
            current.update(available=False, artifact_ids=[], unavailable_reason="explicit_test_mutation_partial")

        mutations = {
            "foreign-build": lambda p: p["result"].update(game_version="1.20.1.1"),
            "different-site": lambda p: p["result"][RESULT_KEY].update(
                holy_site_id=p["result"][RESULT_KEY]["requested_holy_site_id"] ^ 1),
            "wrong-artifact-identity": lambda p: p["result"][RESULT_KEY]["artifact_permissions"].update(
                artifact_id=p["result"][RESULT_KEY]["requested_artifact_id"] ^ 1),
            "missing-nullable-field": lambda p: p["result"][RESULT_KEY].pop("beneficiaries"),
            "window-selection-written": lambda p: p["result"][RESULT_KEY]["evaluation_context"].update(window_selection_written=True),
            "window-candidate-cache-written": lambda p: p["result"][RESULT_KEY]["evaluation_context"].update(window_candidate_cache_written=True),
            "unverified-source-bound-getter": lambda p: p["result"][RESULT_KEY]["evaluation_context"].update(getter_backend="source_bound_native_getter"),
            "unknown-permission-promoted-to-false": unknown_permission,
            "partial-candidates-promoted-to-empty": invented_candidate_list,
            "invented-action-readiness": lambda p: p["result"][RESULT_KEY].update(action_ready=True),
            "invented-beneficiaries": lambda p: p["result"][RESULT_KEY].update(beneficiaries=[]),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                altered = deepcopy(packet)
                mutate(altered)
                driver, endpoint = self.setup_driver(altered)
                try:
                    async with Client(create_server(driver)) as client:
                        arguments, reply = await self.call_native(client.session, driver, altered)
                    self.assertTrue(reply.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.actual_mcp_results.append({"negative_case": name,
                        "explicit_mutation_of_compiled_packet": True,
                        "source_compiled_packet": source_path.name,
                        "source_compiled_packet_sha256": hashlib.sha256(source_raw).hexdigest(),
                        "altered_packet": altered, "native_failure_observed": False,
                        "arguments": arguments, "response": reply.model_dump(mode="json")})
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()
