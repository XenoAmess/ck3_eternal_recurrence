"""Compiled command_result packets through real Driver -> Service -> MCP ClientSession.

XAR_HOLY_SITE_RELIC_NATIVE_FIXTURES is the C++ fixture output directory. This
test never constructs a positive relic DTO. Only endpoint hello/snapshot/I/O
are synthetic. XAR_HOLY_SITE_RELIC_BASE_SOURCE_ROOT can supply unmodified
dependencies while this candidate remains an external partial source overlay.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib
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
BASE = Path(os.environ.get("XAR_HOLY_SITE_RELIC_BASE_SOURCE_ROOT", str(REPO)))
sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
import xar_autoplayer
xar_autoplayer.__path__.insert(0, str(REPO / "ck3_autonomous_player/src/xar_autoplayer"))
if REPO.resolve() != BASE.resolve():
    # The base bridge __init__ imports NativeDriver immediately. Merely adding
    # an overlay path after importing that package leaves the old class cached.
    # Execute the real package initializer with both paths already established.
    # A fresh interpreter is required; never evict modules behind existing objects.
    if any(name == "xar_autoplayer.bridge" or name.startswith("xar_autoplayer.bridge.")
           for name in sys.modules):
        raise RuntimeError("external relic source overlay requires a fresh interpreter")
    bridge_base = BASE / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    bridge_stage = REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge"
    bridge_spec = importlib.util.spec_from_file_location(
        "xar_autoplayer.bridge", bridge_base / "__init__.py",
        submodule_search_locations=[str(bridge_stage), str(bridge_base)])
    bridge_package = importlib.util.module_from_spec(bridge_spec)
    sys.modules[bridge_spec.name] = bridge_package
    xar_autoplayer.bridge = bridge_package
    bridge_spec.loader.exec_module(bridge_package)
else:
    import xar_autoplayer.bridge

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_player_holy_site_relic_context_v1"
STEP = "query-player-holy-site-relic-context-v1"
PERMISSION = "allow_private_player_holy_site_relic_context_query"
RESULT_KEY = "player_holy_site_relic_context"
FIXTURES = os.environ.get("XAR_HOLY_SITE_RELIC_NATIVE_FIXTURES")
EXPECTED_NATIVE_FIXTURES = {
    "normal.json", "cache-disagreement.json", "stale-generation.json",
    "holder-faith-unavailable.json", "getters-unavailable.json", "empty-inventory.json",
    "bad-unused-reference.json", "duplicate-slots.json", "cache-unavailable.json",
}


class Endpoint:
    pipe_name = r"\\.\pipe\holy-site-relic-compiled-source-fixture-only"

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
    if not FIXTURES:
        return []
    rows = []
    for path in sorted(Path(FIXTURES).glob("*.json")):
        raw = path.read_bytes()
        packet = json.loads(raw.decode("utf-8-sig"))
        if (isinstance(packet, dict) and packet.get("type") == "command_result"
                and isinstance(packet.get("result"), dict) and packet["result"].get("step") == STEP):
            rows.append((path, raw, packet))
    return rows


class PublicOptinTests(unittest.TestCase):
    def test_standalone_cli_and_shared_case_optin_are_independent_default_off(self):
        flag = "--private-player-holy-site-relic-context-query"
        self.assertFalse(parser().parse_args([]).private_player_holy_site_relic_context_query)
        selected = parser().parse_args([flag])
        self.assertTrue(selected.private_player_holy_site_relic_context_query)
        self.assertFalse(selected.private_player_holy_site_query)
        self.assertFalse(selected.private_holy_site_adoption_detail_query)
        host = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
        tree = ast.parse(host.read_text(encoding="utf-8-sig"))
        parser_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parser")
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute) and target.attr == PERMISSION for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        namespace = dict(argparse=argparse, Path=Path, __file__=str(host), sys=sys, os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser_function], type_ignores=[])), str(host), "exec"), namespace)
        for tools in ((), (TOOL,)):
            args = namespace["parser"]().parse_args([item for tool in tools for item in ("--case-read-only-mcp-tool", tool)])
            driver = SimpleNamespace(case_declared_read_only_mcp_tools=frozenset(args.case_read_only_mcp_tool))
            exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])), str(host), "exec"), {"driver": driver})
            self.assertEqual(getattr(driver, PERMISSION), bool(tools))
            self.assertFalse(getattr(driver, "allow_private_player_holy_site_query", False))
        acceptance = ast.parse((REPO / "tools/ck3_mod_acceptance.py").read_text(encoding="utf-8-sig"))
        allowed = next(node for node in acceptance.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "CASE_READ_ONLY_MCP_TOOLS" for target in node.targets))
        self.assertIn(TOOL, ast.literal_eval(allowed.value.args[0]))
        mcp_source = REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py"
        mcp_tree = ast.parse(mcp_source.read_text(encoding="utf-8-sig"))
        tool_body = next(node for node in ast.walk(mcp_tree) if isinstance(node, ast.FunctionDef) and node.name == TOOL)
        return_call = next(node.value for node in tool_body.body if isinstance(node, ast.Return))
        self.assertIsInstance(return_call, ast.Call)
        self.assertEqual(return_call.func.value.id, "service")
        self.assertEqual(return_call.func.attr, "query_player_holy_site_relic_context_v1")
        self.assertTrue(callable(GameplayBridgeService.query_player_holy_site_relic_context_v1))


@unittest.skipUnless(FIXTURES, "requires newly compiled native relic command_result packets")
class RelicNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, packet, *, enabled=True):
        self.assertEqual(Path(inspect.getfile(NativeHeadlessGameplayDriver)).resolve(),
                         (REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").resolve())
        self.assertTrue(callable(getattr(NativeHeadlessGameplayDriver,
                                        "query_player_holy_site_relic_context_private_v1", None)))
        native = packet["result"][RESULT_KEY]
        endpoint = Endpoint(packet)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        setattr(driver, PERMISSION, enabled)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command." + STEP]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:relic-fixture", "revision": packet["result"]["snapshot_revision"], "state": {
                "phase": "map_hud", "date": "synthetic-frame-only", "date_raw": native["date_raw"],
                "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                "played_character": {"character_id": native["played_character_id"], "alive": True}}})
        return driver, endpoint

    def uuid_for(self, packet):
        self.assertTrue(packet["request_id"].startswith("g2-read-"))
        return SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])

    async def call_native(self, session, driver, packet):
        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"],
                     "holy_site_id": packet["result"][RESULT_KEY]["requested_holy_site_id"]}
        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=self.uuid_for(packet)):
            reply = await session.call_tool(TOOL, arguments)
        return arguments, reply

    async def test_compiled_packets_cross_real_driver_service_and_mcp_client_session(self):
        from mcp import Client, ClientSession
        packets = fixture_packets()
        self.assertTrue(EXPECTED_NATIVE_FIXTURES <= {path.name for path, _, _ in packets},
                        "requires all nine compiled production-reader/serializer variants")
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
                        self.assertFalse(tool.annotations.idempotent_hint)
                        self.assertEqual(set(tool.input_schema["properties"]), {"expected_revision", "holy_site_id"})
                        self.assertEqual(set(tool.input_schema["required"]), {"expected_revision", "holy_site_id"})
                        self.assertNotIn("ck3_query_player_holy_site_v1", tools)
                        arguments, reply = await self.call_native(client.session, driver, packet)
                    self.actual_mcp_results.append({"fixture": path.name, "fixture_sha256": hashlib.sha256(raw).hexdigest(),
                        "native_packet": original, "arguments": arguments, "request": endpoint.requests,
                        "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    self.assertEqual(actual["available"], native["available"])
                    self.assertEqual(actual["unavailable_reason"], native["unavailable_reason"])
                    for key in ("cached_world_state", "county_context", "inventory", "current_relic_evaluation",
                                "associated_faith_ids", "evaluation_context"):
                        self.assertEqual(actual[key], native[key])
                    self.assertFalse(actual["beneficiaries_observed"])
                    self.assertIsNone(actual["beneficiaries"])
                    self.assertFalse(actual["can_enshrine_observed"])
                    self.assertIsNone(actual["can_enshrine"])
                    self.assertIn(actual["evaluation_context"]["getter_backend"],
                                  {"owned_fixture_injected_getter", "unavailable"})
                    self.assertFalse(actual["evaluation_context"]["script_rng_effects_verified"])
                    self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                    self.assertNotEqual(actual["capture_epoch"], actual["queried_native_revision"])
                    self.assertNotEqual(arguments["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(len(endpoint.requests), 1)
                    self.assertEqual(endpoint.requests[0]["holy_site_id"], native["requested_holy_site_id"])
                    self.assertEqual(endpoint.requests[0]["expected_snapshot_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(endpoint.requests[0]["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(packet, original)
                finally:
                    driver.close()

    async def test_optin_off_hides_tool_and_strict_input_rejects_before_native_io(self):
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
                for args in ({"expected_revision": revision}, {"expected_revision": revision, "holy_site_id": True},
                             {"expected_revision": revision, "holy_site_id": str(site)},
                             {"expected_revision": revision, "holy_site_id": 0xFFFFFFFF},
                             {"expected_revision": revision, "holy_site_id": site, "enshrine": True},
                             {"expected_revision": revision + 1, "holy_site_id": site}):
                    reply = await client.session.call_tool(TOOL, args)
                    self.assertTrue(reply.is_error)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_explicitly_corrupted_native_packets_fail_closed_over_real_mcp(self):
        from mcp import Client
        source_path, source_raw, packet = next(
            (path, raw, packet) for path, raw, packet in fixture_packets()
            if packet["result"][RESULT_KEY]["available"])
        mutations = {
            "foreign-build": lambda p: p["result"].update(game_version="1.20.1.1"),
            "different-site": lambda p: p["result"][RESULT_KEY].update(
                holy_site_id=p["result"][RESULT_KEY]["requested_holy_site_id"] ^ 1),
            "world-cache-write": lambda p: p["result"][RESULT_KEY]["evaluation_context"].update(world_cache_written=True),
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
