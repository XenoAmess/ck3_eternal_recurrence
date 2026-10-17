"""New production UI serializer packets cross actual Driver/Service/MCP.

Result inputs are explicitly synthetic native DTO fixtures. The test boundary
replaces only endpoint hello/state/I/O; no engine selection is claimed.
"""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

STAGE = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get("XAR_CREATION_UI_BASE_SOURCE_ROOT", str(STAGE))).resolve()
QUERY = Path(os.environ.get("XAR_CREATION_UI_QUERY_STAGE", str(STAGE))).resolve()
spec = importlib.util.spec_from_file_location("creation_ui_source_overlay",
    STAGE / "ck3_autonomous_player/native_bridge/research/creation_ui_source_overlay.py")
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)
if BASE == STAGE.resolve():
    sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
    HOOKS = None
else:
    HOOKS = overlay.install(BASE, STAGE, QUERY)

from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.version_identity import CK3_12004

PERMISSION = "allow_private_player_holy_site_creation_ui"
TOOLS = {
    "query": "ck3_query_ingame_ui_window_v1",
    "open_holy_site_creation": "ck3_open_holy_site_creation_window_v1",
    "select_holy_site_creation_type": "ck3_select_holy_site_creation_type_v1",
    "select_holy_site_creation_barony": "ck3_select_holy_site_creation_barony_v1",
    "set_holy_site_creation_artifact_selection": "ck3_set_holy_site_creation_artifact_selection_v1",
}
FIXTURES = os.environ.get("XAR_CREATION_UI_NATIVE_FIXTURES")
REQUIRED = frozenset(json.loads(os.environ.get("XAR_CREATION_UI_REQUIRED_FIXTURES", "[]")))


def source_for(relative):
    if HOOKS is None:
        path = BASE / relative
        return path, path.read_text(encoding="utf-8-sig"), None
    return overlay.candidate_source(BASE, QUERY, HOOKS, relative)


def packets():
    result = []
    if FIXTURES:
        for path in sorted(Path(FIXTURES).glob("*.json")):
            raw = path.read_bytes()
            packet = json.loads(raw.decode("utf-8-sig"))
            if (isinstance(packet, dict) and packet.get("type") == "command_result"
                    and isinstance(packet.get("result"), dict)
                    and packet["result"].get("window_kind") == "holy_site_creation"):
                result.append((path, raw, packet))
    return result


class Endpoint:
    pipe_name = r"\\.\pipe\new-creation-ui-production-serializer-fixtures-only"

    def __init__(self, packet):
        self.packet, self.requests, self.on_frame = packet, [], None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, value):
        self.on_frame(deepcopy(value))

    def send(self, request):
        if request["type"] == "execute_step":
            self.requests.append(deepcopy(request))
            if request["request_id"] != self.packet["request_id"]:
                raise RuntimeError("UI production request ID differs from the actual serializer packet")
            self.publish(self.packet)

    def close(self):
        pass

    def transport_error(self):
        return None


class CreationUiOptinTests(unittest.TestCase):
    def test_standalone_and_managed_ui_optins_are_independent_default_off(self):
        flag = "--private-player-holy-site-creation-ui"
        self.assertFalse(parser().parse_args([]).private_player_holy_site_creation_ui)
        args = parser().parse_args([flag])
        self.assertTrue(args.private_player_holy_site_creation_ui)
        self.assertFalse(args.private_player_holy_site_creation_context_query)
        path, source, _ = source_for("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py")
        tree = ast.parse(source)
        parser_fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "parser")
        namespace = dict(argparse=argparse, Path=Path, __file__=str(path), sys=sys, os=os)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[parser_fn], type_ignores=[])), str(path), "exec"), namespace)
        assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Attribute) and target.attr == PERMISSION for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        for argv, expected in (([], False), ([flag], True)):
            args = namespace["parser"]().parse_args(argv)
            driver = SimpleNamespace()
            exec(compile(ast.fix_missing_locations(ast.Module(body=assignments, type_ignores=[])), str(path), "exec"),
                 {"driver": driver, "args": args})
            self.assertIs(getattr(driver, PERMISSION), expected)
        forward = next(node for node in ast.walk(tree) if isinstance(node, ast.If)
            and "private_player_holy_site_creation_ui" in ast.unparse(node.test)
            and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                    and isinstance(child.func.value, ast.Name) and child.func.value.id == "child_args"
                    and child.func.attr == "append" for child in ast.walk(node)))
        for enabled in (False, True):
            env = {"args": SimpleNamespace(private_player_holy_site_creation_ui=enabled), "child_args": []}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[forward], type_ignores=[])), str(path), "exec"), env)
            self.assertEqual(env["child_args"], [flag] if enabled else [])
        mcp_path, mcp_source, _ = source_for("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py")
        mcp_tree = ast.parse(mcp_source)
        mode = next(node for node in ast.walk(mcp_tree) if isinstance(node, ast.If)
            and any(isinstance(child, ast.Attribute) and child.attr == "private_player_holy_site_creation_ui"
                    for child in ast.walk(node.test)))
        for backend, transport, accepted in (("native-headless", "stdio", True),
                                               ("desktop", "stdio", False),
                                               ("native-headless", "sse", False)):
            env = {"args": SimpleNamespace(private_player_holy_site_creation_ui=True,
                                           driver=backend, transport=transport)}
            code = compile(ast.fix_missing_locations(ast.Module(body=[mode], type_ignores=[])), str(mcp_path), "exec")
            if accepted:
                exec(code, env)
            else:
                with self.assertRaises(ValueError):
                    exec(code, env)
        for operation, tool in TOOLS.items():
            if operation == "query":
                continue
            node = next(n for n in ast.walk(mcp_tree)
                        if isinstance(n, ast.FunctionDef) and n.name == tool)
            forwarded = next(n.value for n in node.body if isinstance(n, ast.Return))
            self.assertEqual(forwarded.func.value.id, "service")
            self.assertNotIn("create", forwarded.func.attr.replace("creation", ""))


@unittest.skipUnless(FIXTURES, "requires newly compiled production UI serializer packets")
class CreationUiNativeMcpTests(unittest.IsolatedAsyncioTestCase):
    actual_mcp_results = []
    state_counter = 0

    def setup_driver(self, packet, *, enabled=True):
        raw = packet["result"]
        endpoint = Endpoint(packet)
        type(self).state_counter += 1
        state_dir = Path(os.environ["XAR_CREATION_UI_STATE_ROOT"]) / f"case-{type(self).state_counter:03d}"
        state_dir.mkdir(parents=True, exist_ok=False)
        driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
            state_dir=state_dir, command_timeout_seconds=1.0)
        setattr(driver, PERMISSION, enabled)
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
            "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256,
            "capabilities": ["game.state.snapshot", "game.command.navigate-ingame-ui-v1",
                             "game.command.query-ingame-ui-window-v1"]})
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": "native:new-creation-ui-serializer-fixture", "revision": raw["native_revision"],
            "state": {"phase": "map_hud", "date": "synthetic-only", "date_raw": raw["date_raw"],
                      "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                      "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                      "played_character": {"character_id": raw["played_character_id"], "alive": True}}})
        return driver, endpoint

    def arguments(self, driver, packet):
        raw = packet["result"]["holy_site_creation_ui"]
        operation = raw["operation"]
        args = {"expected_revision": driver.take_snapshot_without_native_command_history()["revision"]}
        if operation == "query":
            args["window_kind"] = "holy_site_creation"
        elif operation == "select_holy_site_creation_type":
            args["type_key"] = raw["type_key"]
        elif operation == "select_holy_site_creation_barony":
            args["barony_title_id"] = raw["requested_object_id"]
        elif operation == "set_holy_site_creation_artifact_selection":
            args.update(artifact_id=raw["requested_object_id"], selected=raw["selected"])
        return TOOLS[operation], args

    async def invoke(self, session, driver, packet, *, arguments=None):
        tool, args = self.arguments(driver, packet)
        if arguments is not None:
            args = arguments
        request_id = packet["request_id"]
        prefix, sequence, fragment = request_id.split("-", 2)
        self.assertEqual((prefix, sequence, len(fragment)), ("step", "2", 12))
        self.assertTrue(all(c in "0123456789abcdef" for c in fragment))
        with patch("xar_autoplayer.bridge.native_driver.uuid.uuid4", return_value=SimpleNamespace(hex=fragment + "0" * 20)):
            reply = await session.call_tool(tool, args)
        return tool, args, reply

    async def test_new_original_serializer_packets_cross_real_driver_service_sdk_without_raw_rewrite(self):
        from mcp import Client, ClientSession
        rows = packets()
        self.assertTrue(REQUIRED)
        self.assertEqual(REQUIRED, {path.name for path, _, _ in rows})
        for path, original_bytes, packet in rows:
            with self.subTest(fixture=path.name):
                original = deepcopy(packet)
                driver, endpoint = self.setup_driver(packet)
                try:
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session, ClientSession)
                        tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
                        for operation, tool in TOOLS.items():
                            self.assertIn(tool, tools)
                            if operation != "query":
                                self.assertFalse(tools[tool].annotations.read_only_hint)
                                self.assertFalse(tools[tool].annotations.destructive_hint)
                                self.assertFalse(tools[tool].annotations.idempotent_hint)
                        self.assertNotIn("ck3_query_player_holy_site_creation_context_v1", tools)
                        tool, args, reply = await self.invoke(client.session, driver, packet)
                    self.actual_mcp_results.append({"fixture": path.name,
                        "fixture_sha256": hashlib.sha256(original_bytes).hexdigest(),
                        "native_packet_unchanged": original, "tool": tool, "arguments": args,
                        "requests": endpoint.requests, "response": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    for key, value in packet["result"].items():
                        self.assertEqual(actual[key], value, key)
                    self.assertEqual(args["expected_revision"], 2)
                    self.assertEqual(actual["queried_native_revision"], 37)
                    self.assertNotEqual(args["expected_revision"], actual["queried_native_revision"])
                    self.assertEqual(len(endpoint.requests), 1)
                    req = endpoint.requests[0]
                    ui = packet["result"]["holy_site_creation_ui"]
                    self.assertEqual(req["expected_revision"], 37)
                    self.assertEqual(req["window_kind"], "holy_site_creation")
                    self.assertEqual(req["subject_id"], ui["requested_object_id"])
                    self.assertEqual(req["step"], "query-ingame-ui-window-v1" if ui["operation"] == "query" else "navigate-ingame-ui-v1")
                    self.assertEqual(req.get("operation"), None if ui["operation"] == "query" else ui["operation"])
                    self.assertEqual(req.get("type_key"), ui["type_key"])
                    self.assertEqual(req.get("selected"), ui["selected"])
                    self.assertIs(actual["holy_site_creation_ui"]["create_dispatched"], False)
                    self.assertEqual(packet, original)
                    if actual["status"] == "verification_pending":
                        self.assertIs(actual["available"], False)
                        self.assertIs(actual["verification_pending"], True)
                        self.assertIs(actual["holy_site_creation_ui"]["selection_verified"], False)
                finally:
                    driver.close()

    async def test_disabled_ui_and_strict_inputs_reject_before_wire(self):
        from mcp import Client
        packet = next(p for _, _, p in packets()
                      if p["result"]["holy_site_creation_ui"]["operation"] == "select_holy_site_creation_type")
        driver, endpoint = self.setup_driver(packet, enabled=False)
        try:
            async with Client(create_server(driver)) as client:
                tool_names = {tool.name for tool in (await client.session.list_tools()).tools}
                self.assertFalse(set(TOOLS.values()) - {TOOLS["query"]} & tool_names)
                reply = await client.session.call_tool(TOOLS["query"],
                    {"window_kind": "holy_site_creation", "expected_revision": 2})
                self.assertTrue(reply.is_error)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()
        driver, endpoint = self.setup_driver(packet)
        try:
            async with Client(create_server(driver)) as client:
                bad = [(TOOLS["select_holy_site_creation_type"], {"expected_revision": 2, "type_key": value})
                       for value in (True, "", "x" * 161, "测" * 60, "x\0y")]
                for value in (True, -1, 0xFFFFFFFF, 2**32, "1"):
                    bad.append((TOOLS["select_holy_site_creation_barony"], {"expected_revision": 2, "barony_title_id": value}))
                for value in (1, "false", None):
                    bad.append((TOOLS["set_holy_site_creation_artifact_selection"],
                        {"expected_revision": 2, "artifact_id": 0xF0000009, "selected": value}))
                for extra in ("create", "actor_id", "faith_id", "rva", "callback", "coordinates"):
                    bad.append((TOOLS["open_holy_site_creation"], {"expected_revision": 2, extra: True}))
                for revision in (True, -1, "2", 37):
                    bad.append((TOOLS["open_holy_site_creation"], {"expected_revision": revision}))
                for tool, arguments in bad:
                    reply = await client.session.call_tool(tool, arguments)
                    self.assertTrue(reply.is_error, (tool, arguments))
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_explicit_new_serializer_packet_mutations_reject_over_real_mcp(self):
        from mcp import Client
        path, raw, packet = next(row for row in packets()
            if row[2]["result"]["holy_site_creation_ui"]["operation"] == "select_holy_site_creation_type"
            and row[2]["result"]["available"])
        def ui(p):
            return p["result"]["holy_site_creation_ui"]
        cases = {
            "create-dispatched": lambda p: ui(p).update(create_dispatched=True),
            "missing-selector-field": lambda p: ui(p).pop("selected"),
            "false-selected-state": lambda p: ui(p)["context"].update(selected_type_key="different"),
            "wrong-epoch": lambda p: ui(p)["context"].update(capture_epoch=p["result"]["pump_epoch"] + 1),
            "no-postcondition": lambda p: ui(p).update(postcondition_observed=False),
            "null-context-with-success": lambda p: ui(p).update(context=None),
            "wrong-window": lambda p: p["result"].update(window_name="faith_window"),
            "invalid-current-faith": lambda p: p["result"].update(current_subject_id=0xFFFFFFFF),
            "unknown-ack-as-success": lambda p: p["result"].update(status="ui_selection_verified", verification_pending=True),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                altered = deepcopy(packet)
                mutate(altered)
                driver, endpoint = self.setup_driver(altered)
                try:
                    async with Client(create_server(driver)) as client:
                        tool, args, reply = await self.invoke(client.session, driver, altered)
                    self.assertTrue(reply.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.actual_mcp_results.append({"negative_case": name,
                        "explicit_mutation_of_new_serializer_packet": True, "native_failure_observed": False,
                        "source_packet": path.name, "source_packet_sha256": hashlib.sha256(raw).hexdigest(),
                        "altered_packet": altered, "tool": tool, "arguments": args,
                        "requests": endpoint.requests, "response": reply.model_dump(mode="json")})
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()
