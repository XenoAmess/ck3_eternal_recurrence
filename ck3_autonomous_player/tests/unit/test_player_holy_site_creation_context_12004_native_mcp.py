"""New compiled C++ packets cross production Driver, Service and real MCP SDK.

Only endpoint I/O, hello and state_snapshot are synthetic. Positive creation
DTOs come solely from the newly compiled reader/serializer fixture packets.
Explicit packet mutations below test rejection, never new live observations.
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

STAGE = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get("XAR_CREATION_CONTEXT_BASE_SOURCE_ROOT", str(STAGE))).resolve()
overlay_path = STAGE / "ck3_autonomous_player/native_bridge/research/creation_context_source_overlay.py"
spec = importlib.util.spec_from_file_location("creation_context_source_overlay", overlay_path)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
if BASE == STAGE.resolve():
    # After integration, ordinary discovery imports the production repository
    # directly; an old candidate manifest must not patch the integrated source.
    sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
    HOOKS = None
else:
    HOOKS = overlay.install(BASE, STAGE)

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.version_identity import CK3_12004

TOOL = "ck3_query_player_holy_site_creation_context_v1"
STEP = "query-player-holy-site-creation-context-v1"
PERMISSION = "allow_private_player_holy_site_creation_context_query"
RESULT_KEY = "player_holy_site_creation_context"
FIXTURES = os.environ.get("XAR_CREATION_CONTEXT_NATIVE_FIXTURES")
REQUIRED = frozenset(json.loads(os.environ.get("XAR_CREATION_CONTEXT_REQUIRED_FIXTURES", "[]")))
HIGH_ACTOR_PACKET = os.environ.get("XAR_CREATION_CONTEXT_HIGH_ACTOR_PACKET")
HIGH_ACTOR_SHA256 = os.environ.get("XAR_CREATION_CONTEXT_HIGH_ACTOR_SHA256")


def source_for(relative):
    if HOOKS is None:
        path = BASE / relative
        return path, path.read_text(encoding="utf-8-sig"), None
    return overlay.candidate_source(BASE, HOOKS, relative)


def fixture_packets():
    rows = []
    if FIXTURES:
        for path in sorted(Path(FIXTURES).glob("*.json")):
            raw = path.read_bytes()
            packet = json.loads(raw.decode("utf-8-sig"))
            if (isinstance(packet, dict) and packet.get("type") == "command_result"
                    and isinstance(packet.get("result"), dict)
                    and packet["result"].get("step") == STEP):
                rows.append((path, raw, packet))
    return rows


class Endpoint:
    pipe_name = r"\\.\pipe\creation-context-new-compiled-source-fixture-only"

    def __init__(self, packet, *, change_after=None):
        self.packet, self.requests, self.on_frame = packet, [], None
        self.change_after = change_after

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request["type"] == "execute_step":
            self.requests.append(deepcopy(request))
            if request["request_id"] != self.packet["request_id"] or request["step"] != STEP:
                raise RuntimeError("creation fixture lost its actual outgoing request identity")
            self.publish(self.packet)
            if self.change_after is not None:
                self.publish(self.change_after)

    def transport_error(self):
        return None

    def close(self):
        pass


class PublicOptinTests(unittest.TestCase):
    def test_independent_default_off_cli_case_host_and_service_hooks(self):
        flag = "--private-player-holy-site-creation-context-query"
        self.assertFalse(parser().parse_args([]).private_player_holy_site_creation_context_query)
        args = parser().parse_args([flag])
        self.assertTrue(args.private_player_holy_site_creation_context_query)
        for sibling in ("private_player_holy_site_relic_permissions_query",
                        "private_player_holy_site_relic_context_query", "private_player_holy_site_query"):
            self.assertFalse(getattr(args, sibling))
        self.assertTrue(callable(GameplayBridgeService.query_player_holy_site_creation_context_v1))
        self.assertTrue(callable(NativeHeadlessGameplayDriver.query_player_holy_site_creation_context_private_v1))
        host_path, host_source, _ = source_for(
            "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
        tree = ast.parse(host_source)
        parser_function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parser")
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Attribute) and target.attr == PERMISSION
                               for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        namespace = dict(argparse=argparse, Path=Path, __file__=str(host_path), sys=sys, os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser_function], type_ignores=[])),
                     str(host_path), "exec"), namespace)
        for tools in ((), (TOOL,)):
            args = namespace["parser"]().parse_args(
                [item for tool in tools for item in ("--case-read-only-mcp-tool", tool)])
            driver = SimpleNamespace(case_declared_read_only_mcp_tools=frozenset(args.case_read_only_mcp_tool))
            exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])),
                         str(host_path), "exec"), {"driver": driver})
            self.assertIs(getattr(driver, PERMISSION), bool(tools))
            self.assertFalse(getattr(driver, "allow_private_player_holy_site_relic_permissions_query", False))
        acceptance_path, acceptance_source, _ = source_for("tools/ck3_mod_acceptance.py")
        allowed = next(node for node in ast.parse(acceptance_source, str(acceptance_path)).body
                       if isinstance(node, ast.Assign) and any(
                           isinstance(target, ast.Name) and target.id == "CASE_READ_ONLY_MCP_TOOLS"
                           for target in node.targets))
        self.assertIn(TOOL, ast.literal_eval(allowed.value.args[0]))
        mcp_path, mcp_source, _ = source_for("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py")
        mcp_tree = ast.parse(mcp_source)
        tool = next(node for node in ast.walk(mcp_tree)
                    if isinstance(node, ast.FunctionDef) and node.name == TOOL)
        forwarded = next(node.value for node in tool.body if isinstance(node, ast.Return))
        self.assertEqual((forwarded.func.value.id, forwarded.func.attr),
                         ("service", "query_player_holy_site_creation_context_v1"))
        guard = next(node for node in ast.walk(mcp_tree) if isinstance(node, ast.If)
                     and isinstance(node.test, ast.BoolOp) and any(
                         isinstance(child, ast.Attribute)
                         and child.attr == "private_player_holy_site_creation_context_query"
                         for child in ast.walk(node.test)))
        for driver, transport, accepted in (("native-headless", "stdio", True),
                                             ("desktop", "stdio", False),
                                             ("native-headless", "sse", False)):
            namespace = {"args": SimpleNamespace(private_player_holy_site_creation_context_query=True,
                                                 driver=driver, transport=transport)}
            code = compile(ast.fix_missing_locations(ast.Module(body=[guard], type_ignores=[])),
                           str(mcp_path), "exec")
            if accepted:
                exec(code, namespace)
            else:
                with self.assertRaises(ValueError):
                    exec(code, namespace)


@unittest.skipUnless(FIXTURES, "requires the new compiled creation reader/serializer packet set")
class CreationContextNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []

    def setup_driver(self, packet, *, enabled=True, change_after=None, frame_packet=None):
        self.assertEqual(Path(inspect.getfile(NativeHeadlessGameplayDriver)).resolve(),
                         (BASE / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py").resolve())
        if HOOKS is not None:
            self.assertIsNotNone(getattr(sys.modules[NativeHeadlessGameplayDriver.__module__],
                                         "__candidate_hook_sha256__", None))
        frame_packet = packet if frame_packet is None else frame_packet
        native = frame_packet["result"][RESULT_KEY]
        endpoint = Endpoint(packet, change_after=change_after)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
        setattr(driver, PERMISSION, enabled)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
                          "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
                          "expected_ck3_sha256": CK3_12004.executable_sha256,
                          "capabilities": ["game.state.snapshot", "game.command." + STEP]})
        self.state_frame = {"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:creation-context-fixture", "revision": frame_packet["result"]["snapshot_revision"],
            "state": {"phase": "map_hud", "date": "synthetic-frame-only", "date_raw": native["date_raw"],
                      "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                      "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                      "played_character": {"character_id": native["played_character_id"], "alive": True}}}
        endpoint.publish(self.state_frame)
        return driver, endpoint

    async def call_native(self, session, driver, packet):
        arguments = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"]}
        self.assertTrue(packet["request_id"].startswith("g2-read-"))
        request_hex = packet["request_id"][len("g2-read-"):]
        self.assertEqual(len(request_hex), 32)
        self.assertTrue(all(c in "0123456789abcdef" for c in request_hex))
        request_uuid = SimpleNamespace(hex=request_hex)
        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=request_uuid):
            reply = await session.call_tool(TOOL, arguments)
        return arguments, reply

    async def test_new_compiled_packets_cross_actual_driver_service_mcp_and_preserve_raw_values(self):
        from mcp import Client, ClientSession
        packets = fixture_packets()
        self.assertTrue(REQUIRED, "freeze new producer filenames before qualification")
        self.assertEqual(REQUIRED, {path.name for path, _, _ in packets})
        split_revision_samples = 0
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
                        self.assertEqual(set(tool.input_schema["properties"]), {"expected_revision"})
                        self.assertEqual(set(tool.input_schema["required"]), {"expected_revision"})
                        for sibling in ("ck3_query_player_holy_site_relic_permissions_v1",
                                        "ck3_query_player_holy_site_v1"):
                            self.assertNotIn(sibling, tools)
                        arguments, reply = await self.call_native(client.session, driver, packet)
                    self.actual_mcp_results.append({"fixture": path.name,
                        "fixture_sha256": hashlib.sha256(raw).hexdigest(), "native_packet": original,
                        "arguments": arguments, "requests": endpoint.requests,
                        "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    for key, expected in native.items():
                        self.assertEqual(actual[key], expected, key)
                    self.assertIs(actual["read_only"], True)
                    self.assertIs(actual["action_ready"], False)
                    self.assertIs(actual["create_invoked"], False)
                    self.assertIs(actual["native_affordability_observed"], False)
                    self.assertIsNone(actual["native_affordable"])
                    self.assertEqual(actual["queried_revision"], arguments["expected_revision"])
                    self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                    split_revision_samples += arguments["expected_revision"] != actual["queried_native_revision"]
                    self.assertEqual(len(endpoint.requests), 1)
                    request = endpoint.requests[0]
                    self.assertEqual(set(request), {"type", "protocol_version", "request_id", "step",
                                                   "expected_revision", "expected_snapshot_revision"})
                    self.assertEqual(request["expected_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(request["expected_snapshot_revision"], packet["result"]["snapshot_revision"])
                    self.assertEqual(packet, original)
                finally:
                    driver.close()
        self.assertGreater(split_revision_samples, 0, "public != native revision is mandatory")

    async def test_optin_and_strict_public_input_reject_before_native_io(self):
        from mcp import Client
        packet = fixture_packets()[0][2]
        driver, endpoint = self.setup_driver(packet, enabled=False)
        try:
            async with Client(create_server(driver)) as client:
                self.assertNotIn(TOOL, {tool.name for tool in (await client.session.list_tools()).tools})
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()
        driver, endpoint = self.setup_driver(packet)
        try:
            async with Client(create_server(driver)) as client:
                revision = driver.take_snapshot_without_native_command_history()["revision"]
                bad_inputs = [{}, {"expected_revision": revision + 1}]
                for bad in (True, "1", 0, -1, 1.25):
                    bad_inputs.append({"expected_revision": bad})
                for forbidden in ("actor_id", "character_id", "create", "type_key", "barony_title_id",
                                  "artifact_ids", "bypass_requirements"):
                    bad_inputs.append({"expected_revision": revision, forbidden: True})
                for arguments in bad_inputs:
                    reply = await client.session.call_tool(TOOL, arguments)
                    self.assertTrue(reply.is_error, arguments)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_explicit_compiled_packet_mutations_fail_closed_over_real_mcp(self):
        from mcp import Client
        path, raw, packet = next(row for row in fixture_packets()
                                if row[2]["result"][RESULT_KEY]["available"])
        def native(p):
            return p["result"][RESULT_KEY]
        mutations = {
            "foreign-build": lambda p: p["result"].update(game_version="1.20.1.1"),
            "native-revision-mismatch": lambda p: p["result"].update(snapshot_revision=p["result"]["snapshot_revision"] + 1),
            "foreign-player": lambda p: native(p).update(played_character_id=native(p)["played_character_id"] ^ 1),
            "missing-nullable-field": lambda p: native(p).pop("native_affordable"),
            "unknown-enabled-as-false": lambda p: native(p).update(native_enabled_observed=False, native_create_button_enabled=False),
            "bypass-presented-as-normal": lambda p: native(p).update(bypass_requirements_observed=True, bypass_requirements_raw=1,
                native_enabled_observed=True, native_create_button_enabled=True,
                normal_requirements_legality_observed=True, normal_requirements_can_create=True),
            "invented-affordability": lambda p: native(p).update(native_affordability_observed=True, native_affordable=True),
            "invented-fresh-quote": lambda p: native(p).update(cached_quote_freshness_observed=True),
            "invented-rendered-visibility": lambda p: native(p).update(rendered_visibility_observed=True),
            "invented-action-readiness": lambda p: native(p).update(action_ready=True),
            "create-invoked": lambda p: native(p).update(create_invoked=True),
            "partial-model-promoted-to-empty": lambda p: native(p).update(available=False,
                unavailable_reason="explicit_test_partial", models_available=False, models_complete=False,
                available_holy_site_types=[], potential_barony_title_ids=[], enshrinable_artifact_ids=[]),
            "sentinel-reference-in-model": lambda p: native(p).update(potential_barony_title_ids=[0xFFFFFFFF]),
            "bool-as-raw-resource": lambda p: native(p).update(cached_resource_quote_available=True, cached_resource_vector_raw=[True] + [0] * 9),
            "oversize-raw-resource": lambda p: native(p).update(cached_resource_quote_available=True, cached_resource_vector_raw=[2**63] + [0] * 9),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                altered = deepcopy(packet)
                mutate(altered)
                driver, endpoint = self.setup_driver(altered, frame_packet=packet)
                try:
                    # The public/native pre-frame remains the original fixture;
                    # the explicitly mutated payload cannot redefine its binding.
                    async with Client(create_server(driver)) as client:
                        arguments, reply = await self.call_native(client.session, driver, altered)
                    self.assertTrue(reply.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.actual_mcp_results.append({"negative_case": name,
                        "explicit_mutation_of_compiled_packet": True,
                        "source_compiled_packet": path.name,
                        "source_compiled_packet_sha256": hashlib.sha256(raw).hexdigest(),
                        "altered_packet": altered, "native_failure_observed": False,
                        "arguments": arguments, "requests": endpoint.requests,
                        "response": reply.model_dump(mode="json")})
                finally:
                    driver.close()

    async def test_independent_after_snapshot_binding_rejects_changed_frame(self):
        from mcp import Client
        path, raw, packet = fixture_packets()[0]
        driver, endpoint = self.setup_driver(packet)
        changed = deepcopy(self.state_frame)
        changed["revision"] += 1
        changed["state"]["date_raw"] += 1
        endpoint.change_after = changed
        try:
            before = driver.take_snapshot_without_native_command_history()
            async with Client(create_server(driver)) as client:
                arguments, reply = await self.call_native(client.session, driver, packet)
            after = driver.take_snapshot_without_native_command_history()
            self.assertTrue(reply.is_error)
            self.assertNotEqual(before["native_revision"], after["native_revision"])
            self.assertNotEqual(before["revision"], after["revision"])
            self.assertEqual(endpoint.requests[0]["expected_revision"], before["native_revision"])
            self.actual_mcp_results.append({"negative_case": "independent_after_frame_changed",
                "source_compiled_packet": path.name, "source_compiled_packet_sha256": hashlib.sha256(raw).hexdigest(),
                "native_packet_unchanged": packet, "snapshot_before": before, "snapshot_after": after,
                "synthetic_state_io_change": changed, "arguments": arguments, "requests": endpoint.requests,
                "response": reply.model_dump(mode="json")})
        finally:
            driver.close()

    async def test_original_signed_actor_public_boundary_remains_explicitly_unclosed(self):
        from mcp import Client
        self.assertTrue(HIGH_ACTOR_PACKET, "bind the original high-actor C++ packet separately")
        path = Path(HIGH_ACTOR_PACKET)
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), HIGH_ACTOR_SHA256)
        packet = json.loads(raw.decode("utf-8-sig"))
        original = deepcopy(packet)
        native = packet["result"][RESULT_KEY]
        self.assertLess(native["played_character_id"], -1)
        driver, endpoint = self.setup_driver(packet)
        try:
            diagnostic = driver.state.raw_transport_snapshot()
            self.assertIs(diagnostic["semantic_packet_accepted"], False)
            self.assertEqual(diagnostic["native_packet"]["state"]["played_character"]["character_id"],
                             native["played_character_id"])
            async with Client(create_server(driver)) as client:
                # No accepted public semantic snapshot exists; this call only
                # verifies that the production boundary refuses to send.
                arguments = {"expected_revision": max(1, diagnostic["public_revision"])}
                reply = await client.session.call_tool(TOOL, arguments)
            self.assertTrue(reply.is_error)
            self.assertEqual(endpoint.requests, [])
            self.assertEqual(packet, original)
            self.actual_mcp_results.append({"boundary_case": "original_signed_actor_public_state_rejected",
                "status": "UNRESOLVED_PUBLIC_ACTOR_BOUNDARY", "high_signed_actor_supported": False,
                "native_getter_failure_observed": False, "native_command_sent": False,
                "source_compiled_packet": str(path), "source_compiled_packet_sha256": HIGH_ACTOR_SHA256,
                "native_packet_unchanged": original, "raw_transport_diagnostic": diagnostic,
                "arguments": arguments, "requests": endpoint.requests,
                "response": reply.model_dump(mode="json")})
        finally:
            driver.close()


if __name__ == "__main__":
    unittest.main()
