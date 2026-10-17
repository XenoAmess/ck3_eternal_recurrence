"""Only new Create-once guards and new production Create serializer packets."""
import argparse
import ast
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

STAGE = Path(__file__).resolve().parents[3]
BASE = Path(os.environ.get("XAR_CREATE_ONCE_BASE", str(STAGE))).resolve()
if STAGE == BASE:
    sys.path.insert(0, str(BASE / "ck3_autonomous_player/src"))
    HOOKS = None
else:
    spec = importlib.util.spec_from_file_location("create_once_source_overlay",
        STAGE / "ck3_autonomous_player/native_bridge/research/create_once_source_overlay.py")
    overlay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(overlay)
    HOOKS = overlay.install(BASE, STAGE)

from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.mcp_server import create_server, parser
from xar_autoplayer.bridge.holy_site_creation_create_once_private_transport import create_holy_site_once_private_v1
from xar_autoplayer.bridge.player_holy_site_creation_context_private_transport import normalize_player_holy_site_creation_context_v1
from xar_autoplayer.bridge.version_identity import CK3_12004
from mcp import Client, ClientSession

TOOL = "ck3_create_holy_site_once_v1"
FLAG = "--private-player-holy-site-creation-create-once"
PERMISSION = "allow_private_player_holy_site_creation_create_once"
UI_PERMISSION = "allow_private_player_holy_site_creation_ui"
FIXTURES = os.environ.get("XAR_CREATE_ONCE_PACKETS")
STATE = Path(os.environ["XAR_CREATE_ONCE_STATE"]) if "XAR_CREATE_ONCE_STATE" in os.environ else None


def source_for(relative):
    if HOOKS is None:
        return (BASE / relative).read_text(encoding="utf-8-sig")
    return overlay.candidate_source(BASE, HOOKS, relative)[1]


class Endpoint:
    pipe_name = r"\\.\pipe\create-once-new-production-packets-only"

    def __init__(self, packet=None, drop=False):
        self.packet, self.requests, self.drop = packet, [], drop

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request["type"] == "execute_step":
            self.requests.append(deepcopy(request))
            if self.packet is None:
                raise AssertionError("guard sent an unauthorized native action")
            if request["request_id"] != self.packet["request_id"]:
                raise AssertionError("request ID differs from actual production serializer packet")
            if not self.drop:
                self.publish(self.packet)

    def close(self):
        pass

    def transport_error(self):
        return None


counter = 0


def setup(packet=None, *, ui=True, create=True, state_dir=True, drop=False):
    global counter
    counter += 1
    native = packet["result"] if packet else {"native_revision": 37, "date_raw": 51394920, "played_character_id": 15893}
    if "player_holy_site_creation_context" in native:
        native = {**native["player_holy_site_creation_context"], "native_revision": native["snapshot_revision"]}
    folder = STATE / ("case-%03d" % counter)
    folder.mkdir(parents=True, exist_ok=False)
    endpoint = Endpoint(packet, drop)
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        state_dir=folder if state_dir else None, command_timeout_seconds=0.2)
    setattr(driver, UI_PERMISSION, ui)
    setattr(driver, PERMISSION, create)
    endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
        "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
        "expected_ck3_sha256": CK3_12004.executable_sha256,
        "capabilities": ["game.state.snapshot", "game.command.navigate-ingame-ui-v1",
            "game.command.query-player-holy-site-creation-context-v1"]})
    endpoint.publish({"type": "state_snapshot", "protocol_version": 1, "snapshot_id": "native:create-once-new-fixture",
        "revision": native["native_revision"], "state": {"phase": "map_hud", "date": "synthetic-frame-only",
            "date_raw": native["date_raw"], "speed": 1, "paused": True, "map_ready": True, "history": [],
            "active_event": None, "pending_character_interaction": None, "player_armies": [], "active_wars": [],
            "played_character": {"character_id": native["played_character_id"], "alive": True}}})
    return driver, endpoint, folder


def revision(driver):
    return driver.take_snapshot_without_native_command_history()["revision"]


def claim_files(folder):
    return list((folder / "native-session/holy-site-creation-create-once-intents").glob("*.pending.json"))


@unittest.skipUnless(STATE, "requires an explicitly owned Create qualification state directory")
class CreationCreateOnceGuardsTests(unittest.IsolatedAsyncioTestCase):
    guard_results = []

    async def test_both_permissions_are_exact_true_and_independent(self):
        for ui, create in ((False, False), (False, True), (True, False), (True, True), (1, True), (True, 1)):
            driver, endpoint, folder = setup(ui=ui, create=create)
            try:
                async with Client(create_server(driver)) as client:
                    self.assertIsInstance(client.session, ClientSession)
                    tools = {tool.name: tool for tool in (await client.session.list_tools()).tools}
                    enabled = ui is True and create is True
                    self.assertEqual(TOOL in tools, enabled)
                    if enabled:
                        self.assertFalse(tools[TOOL].annotations.read_only_hint)
                        self.assertTrue(tools[TOOL].annotations.destructive_hint)
                        self.assertFalse(tools[TOOL].annotations.idempotent_hint)
                    else:
                        with self.assertRaises(Exception):
                            create_holy_site_once_private_v1(driver, expected_revision=revision(driver),
                                expected_preview_identity_sha256="a" * 64)
                self.assertEqual(endpoint.requests, [])
                self.assertFalse(claim_files(folder))
                self.guard_results.append({"guard": "independent exact permissions", "ui": ui,
                    "create": create, "tool_registered": enabled, "native_sends": 0})
            finally:
                driver.close()

    async def test_strict_preview_revision_and_extra_fields_reject_before_native_io(self):
        driver, endpoint, folder = setup()
        try:
            async with Client(create_server(driver)) as client:
                good = {"expected_preview_identity_sha256": "a" * 64, "expected_revision": revision(driver)}
                bad = [{**good, "expected_preview_identity_sha256": value} for value in (
                    None, True, 1, "", "a" * 63, "a" * 65, "A" * 64, "g" * 64)]
                bad += [{**good, "expected_revision": value} for value in (True, 0, "2")]
                bad += [{**good, name: 1} for name in ("actor_id", "faith_id", "callback", "rva", "create", "selected")]
                for args in bad:
                    reply = await client.session.call_tool(TOOL, args)
                    self.assertTrue(reply.is_error)
                self.guard_results.append({"guard": "strict schema and extras", "rejections": len(bad), "native_sends": 0})
            with self.assertRaises(Exception):
                create_holy_site_once_private_v1(driver, expected_revision=revision(driver) + 1,
                    expected_preview_identity_sha256="a" * 64)
            self.assertEqual(endpoint.requests, [])
            self.assertFalse(claim_files(folder))
        finally:
            driver.close()
        driver, endpoint, folder = setup(state_dir=False)
        try:
            with self.assertRaises(Exception):
                create_holy_site_once_private_v1(driver, expected_revision=revision(driver),
                    expected_preview_identity_sha256="a" * 64)
            self.assertEqual(endpoint.requests, [])
        finally:
            driver.close()

    async def test_only_new_cli_host_case_flag_and_forwarding(self):
        self.assertFalse(parser().parse_args([]).private_player_holy_site_creation_create_once)
        parsed = parser().parse_args([FLAG])
        self.assertTrue(parsed.private_player_holy_site_creation_create_once)
        self.assertFalse(parsed.private_player_holy_site_creation_ui)
        host = ast.parse(source_for("ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"))
        fn = next(n for n in host.body if isinstance(n, ast.FunctionDef) and n.name == "parser")
        env = {"argparse": argparse, "Path": Path, "__file__": str(BASE / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"), "sys": sys, "os": os}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), "new-host-parser", "exec"), env)
        self.assertFalse(env["parser"]().parse_args([]).private_player_holy_site_creation_create_once)
        forward = next(n for n in ast.walk(host) if isinstance(n, ast.If)
            and "private_player_holy_site_creation_create_once" in ast.unparse(n.test)
            and any(isinstance(x, ast.Name) and x.id == "child_args" for x in ast.walk(n)))
        for enabled in (False, True):
            ns = {"args": SimpleNamespace(private_player_holy_site_creation_create_once=enabled), "child_args": []}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[forward], type_ignores=[])), "new-host-forward", "exec"), ns)
            self.assertEqual(ns["child_args"], [FLAG] if enabled else [])
        case = ast.parse(source_for("tools/ck3_mod_acceptance.py"))
        init = next(n for n in ast.walk(case) if isinstance(n, ast.FunctionDef) and n.name == "__init__"
            and any(isinstance(x, ast.Attribute) and x.attr == "opt_in_holy_site_creation_create_once" for x in ast.walk(n)))
        offset = next(i for i, n in enumerate(init.body) if isinstance(n, ast.Assign)
            and any(isinstance(x, ast.Attribute) and x.attr == "opt_in_holy_site_creation_create_once" for x in n.targets))
        statements = init.body[offset:offset + 3]
        for value, ui, required, accepted in ((False, False, [], True), (True, False, [TOOL], False),
                (1, True, [TOOL], False), (True, True, [], False), (True, True, [TOOL], True)):
            obj = SimpleNamespace(case={"opt_in_holy_site_creation_create_once": value, "required_mcp_tools": required},
                opt_in_holy_site_creation_ui=ui)
            code = compile(ast.fix_missing_locations(ast.Module(body=statements, type_ignores=[])), "new-case-guard", "exec")
            if accepted:
                exec(code, {"self": obj})
            else:
                with self.assertRaises(ValueError):
                    exec(code, {"self": obj})
        self.guard_results.append({"guard": "new flag default/forward and Case exact opt-in", "passed": True})

    async def test_legacy_preview_key_is_unknown_without_raw_mutation(self):
        path = Path(os.environ["XAR_CREATE_ONCE_LEGACY_CONTEXT_PACKET"])
        packet = json.loads(path.read_bytes())
        value = packet["result"]["holy_site_creation_ui"]["context"]
        original = deepcopy(value)
        driver, endpoint, folder = setup(packet)
        try:
            before = driver.take_snapshot_without_native_command_history()
            normalized = normalize_player_holy_site_creation_context_v1(value, snapshot=before)
            self.assertIsNone(normalized["preview_identity_sha256"])
            self.assertEqual(value, original)
            with self.assertRaises(ValueError):
                create_holy_site_once_private_v1(driver, expected_revision=revision(driver),
                    expected_preview_identity_sha256=normalized["preview_identity_sha256"])
            self.assertEqual(endpoint.requests, [])
            self.guard_results.append({"guard": "single legacy DTO compatibility", "preview": None,
                "native_sends": 0, "original_packet_unchanged": True})
        finally:
            driver.close()


@unittest.skipUnless(FIXTURES, "new production Create serializer packets required")
class CreationCreateOnceNativeTests(unittest.IsolatedAsyncioTestCase):
    actual_results = []

    async def test_new_production_packets_and_once_replay_guard_through_real_mcp(self):
        required = set(json.loads(os.environ["XAR_CREATE_ONCE_PACKET_NAMES"]))
        paths = [Path(FIXTURES) / name for name in sorted(required)]
        self.assertTrue(paths)
        for path in paths:
            packet = json.loads(path.read_bytes())
            if "player_holy_site_creation_context" in packet.get("result", {}):
                driver, endpoint, folder = setup(packet)
                driver.allow_private_player_holy_site_creation_context_query = True
                core = packet["result"]["player_holy_site_creation_context"]
                args = {"expected_revision": revision(driver)}
                stub = SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])
                try:
                    async with Client(create_server(driver)) as client:
                        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4", return_value=stub):
                            reply = await client.session.call_tool("ck3_query_player_holy_site_creation_context_v1", args)
                    self.actual_results.append({"packet": str(path), "new_preview_query_only": True,
                        "wire_requests": endpoint.requests, "reply": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    for key, value in core.items():
                        self.assertEqual(reply.structured_content[key], value, key)
                    self.assertRegex(reply.structured_content["preview_identity_sha256"], "^[0-9a-f]{64}$")
                    self.assertFalse(reply.structured_content["action_ready"])
                    self.assertFalse(reply.structured_content["create_invoked"])
                    self.assertEqual(len(endpoint.requests), 1)
                finally:
                    driver.close()
                continue
            if packet.get("result", {}).get("holy_site_creation_ui", {}).get("operation") != "create_holy_site_once":
                continue
            original = deepcopy(packet)
            driver, endpoint, folder = setup(packet)
            ui = packet["result"]["holy_site_creation_ui"]
            args = {"expected_preview_identity_sha256": ui["expected_preview_identity_sha256"],
                "expected_revision": revision(driver)}
            self.assertTrue(packet["request_id"].startswith("creation-create-"))
            stub = SimpleNamespace(hex=packet["request_id"][len("creation-create-"):])
            try:
                async with Client(create_server(driver)) as client:
                    with patch("xar_autoplayer.bridge.holy_site_creation_create_once_private_transport.uuid.uuid4", return_value=stub):
                        reply = await client.session.call_tool(TOOL, args)
                    self.actual_results.append({"packet": str(path), "arguments": args,
                        "wire_requests": deepcopy(endpoint.requests), "reply": reply.model_dump(mode="json")})
                    self.assertFalse(reply.is_error, str(reply))
                    actual = reply.structured_content
                    for key, value in packet["result"].items():
                        self.assertEqual(actual[key], value, key)
                    self.assertFalse(actual["business_outcome_observed"])
                    self.assertFalse(actual["action_ready"])
                    self.assertFalse(actual["automatic_retry"])
                    self.assertEqual(len(endpoint.requests), 1)
                    self.assertEqual(endpoint.requests[0]["subject_id"], 0)
                    self.assertEqual(endpoint.requests[0]["expected_preview_identity_sha256"], args["expected_preview_identity_sha256"])
                    attempted = packet["result"]["native_dispatch_attempted"]
                    self.assertEqual(bool(claim_files(folder)), attempted)
                    if attempted:
                        again = {**args, "expected_revision": revision(driver)}
                        duplicate = await client.session.call_tool(TOOL, again)
                        self.assertTrue(duplicate.is_error)
                        self.assertEqual(len(endpoint.requests), 1)
                        self.actual_results[-1]["identical_intent_retry_rejected_without_send"] = True
                self.assertEqual(packet, original)
            finally:
                driver.close()

    async def test_create_unknown_transport_and_false_world_success_keep_claim(self):
        packets = [json.loads((Path(FIXTURES) / name).read_bytes())
            for name in json.loads(os.environ["XAR_CREATE_ONCE_PACKET_NAMES"])]
        packet = next(p for p in packets if p.get("result", {}).get("native_dispatch_attempted") is True)
        for label in ("transport-timeout", "false-world-success"):
            altered = deepcopy(packet)
            if label == "false-world-success":
                altered["result"]["holy_site_creation_ui"]["business_outcome_observed"] = True
            driver, endpoint, folder = setup(altered, drop=label == "transport-timeout")
            args = {"expected_preview_identity_sha256": altered["result"]["holy_site_creation_ui"]["expected_preview_identity_sha256"],
                "expected_revision": revision(driver)}
            stub = SimpleNamespace(hex=altered["request_id"][len("creation-create-"):])
            try:
                async with Client(create_server(driver)) as client:
                    with patch("xar_autoplayer.bridge.holy_site_creation_create_once_private_transport.uuid.uuid4", return_value=stub):
                        reply = await client.session.call_tool(TOOL, args)
                    self.assertTrue(reply.is_error)
                    self.assertTrue(claim_files(folder))
                    args["expected_revision"] = revision(driver)
                    retry = await client.session.call_tool(TOOL, args)
                    self.assertTrue(retry.is_error)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.actual_results.append({"negative_case": label, "explicit_packet_mutation": label == "false-world-success",
                        "native_sends": 1, "pending_claim_retained": True, "retry_rejected_without_send": True,
                        "reply": reply.model_dump(mode="json")})
            finally:
                driver.close()
