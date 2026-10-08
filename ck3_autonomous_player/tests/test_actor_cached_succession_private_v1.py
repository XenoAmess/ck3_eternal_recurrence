"""Pure source-focused tests; synthetic DTOs provide no live CK3 acceptance."""
from __future__ import annotations

import ast
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
BRIDGE = REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge"
PROFILE = REPO / "tools/ck3_native_profile_mcp.py"


class BridgeUnavailableError(RuntimeError):
    pass


class UnsupportedStepError(RuntimeError):
    pass


def load_pure_scope():
    """Load only four pure source modules; never execute bridge/package initializers."""
    package = types.ModuleType("xar_autoplayer")
    package.__path__ = []
    bridge = types.ModuleType("xar_autoplayer.bridge")
    bridge.__path__ = [str(BRIDGE)]
    driver = types.ModuleType("xar_autoplayer.bridge.driver")
    driver.BridgeUnavailableError = BridgeUnavailableError
    driver.UnsupportedStepError = UnsupportedStepError
    modules = {module.__name__: module for module in (package, bridge, driver)}
    with patch.dict(sys.modules, modules):
        for name in ("version_identity", "nonwar_private_build",
                     "confucian_readonly_private_v1", "actor_cached_succession_private_v1"):
            qualified = "xar_autoplayer.bridge." + name
            spec = importlib.util.spec_from_file_location(qualified, BRIDGE / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[qualified] = module
            modules[qualified] = module
            spec.loader.exec_module(module)
    return modules, modules["xar_autoplayer.bridge.actor_cached_succession_private_v1"]


MODULES, query = load_pure_scope()


def source_tree(path):
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def method_node(path, class_name, name):
    owner = next(node for node in source_tree(path).body
                 if isinstance(node, ast.ClassDef) and node.name == class_name)
    return deepcopy(next(node for node in owner.body
                         if isinstance(node, ast.FunctionDef) and node.name == name))


def extract_function(path, name, class_name=None, globals_extra=None):
    node = method_node(path, class_name, name) if class_name else deepcopy(next(
        node for node in source_tree(path).body
        if isinstance(node, ast.FunctionDef) and node.name == name))
    node.decorator_list = []
    tree = ast.Module(body=[ast.ImportFrom(module="__future__", names=[
        ast.alias(name="annotations")], level=0), node], type_ignores=[])
    ast.fix_missing_locations(tree)
    namespace = {"__package__": "xar_autoplayer.bridge",
                 "BridgeUnavailableError": BridgeUnavailableError,
                 "UnsupportedStepError": UnsupportedStepError}
    namespace.update(globals_extra or {})
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace[name]


def frame():
    return {
        "revision": 3, "native_revision": 7, "snapshot_id": "synthetic-native:7",
        "date_raw": 53144712, "paused": True, "speed": 0, "map_ready": True,
        "local_player_id": 31254, "episode_character_id": 31254,
        "episode_run_id": "synthetic-actor-cache-only",
        "played_character": {"character_id": 31254, "alive": True},
        "active_event": None, "pending_character_interaction": None,
        "one_life_terminal_reason": None,
        "diagnostics": {
            "connected": True, "connection_generation": 2,
            "hello": {
                "pid": 991, "ck3_build_match": True,
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version": "1.20.0.4",
                "expected_ck3_sha256": query.CK3_12004.executable_sha256,
            },
        },
    }


def payload(binding, identities=None):
    identities = [0xF1000002, 17, 0xF1000002] if identities is None else list(identities)
    actor = binding["played_character_id"] & 0xFFFFFFFF
    return {
        "schema": query.NATIVE_SCHEMA, "read_only": True,
        "game_version": "1.20.0.4", "executable_sha256": query.CK3_12004.executable_sha256,
        "available": True, "unavailable_reason": None, "capture_epoch": 42,
        "date_raw": binding["date_raw"],
        "played_character_id": actor if actor < 2**31 else actor - 2**32,
        "played_character_full_id": actor, "roster_complete": True,
        "native_count": len(identities), "complete_cached_successor_ids": identities,
        "native_data_pointer": 0x1000 if identities else 0, "land_state_pointer": 0x2000,
    }


def envelope(binding, value=None):
    value = payload(binding) if value is None else value
    return {
        "step": query.STEP, "accepted": True,
        "status": "observed" if value["available"] else "unavailable",
        "private_build": True, "read_only": True, "advertised": False,
        "game_version": "1.20.0.4", "executable_sha256": query.CK3_12004.executable_sha256,
        "domain_key": query.DOMAIN_KEY, "backend_id": query.BACKEND_ID,
        "snapshot_revision": binding["native_revision"], "date_raw": binding["date_raw"],
        query.NESTED_KEY: value,
    }


class MemoryDriver:
    allow_private_actor_cached_succession_queries = True

    def __init__(self, *, before=None, after=None, response=None):
        self.before = deepcopy(frame() if before is None else before)
        self.after = deepcopy(self.before if after is None else after)
        self.response = response
        self.sent = []
        self.snapshots = 0
        self.endpoint = self
        self.state = self

    def take_snapshot(self):
        self.snapshots += 1
        return deepcopy(self.before if self.snapshots == 1 else self.after)

    def send(self, request):
        self.sent.append(deepcopy(request))

    def wait_for_command_result(self, request_id, timeout):
        if self.response is not None:
            return self.response(request_id)
        binding = query.query_binding(self.before, self.before["revision"])
        return {"type": "command_result", "protocol_version": 1, "request_id": request_id,
                "ok": True, "result": envelope(binding)}

    def query_actor_cached_succession_v1(self, *, expected_revision):
        return query.query_actor_cached_succession_private_v1(
            self, expected_revision=expected_revision)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.binding = query.query_binding(frame(), 3)

    def test_order_duplicates_full_ids_and_legal_empty_are_preserved(self):
        original = payload(self.binding)
        result = query.normalize_cached_succession(original, self.binding)
        self.assertEqual(result, original)
        self.assertIsNot(result, original)
        self.assertEqual(result["complete_cached_successor_ids"], [0xF1000002, 17, 0xF1000002])
        empty = payload(self.binding, [])
        self.assertEqual(query.normalize_cached_succession(empty, self.binding)["native_count"], 0)
        empty["native_data_pointer"] = 0x1000
        query.normalize_cached_succession(empty, self.binding)
        snapshot = frame()
        snapshot["played_character"]["character_id"] = 0xF1000001
        binding = query.query_binding(snapshot, 3)
        signed = query.normalize_cached_succession(payload(binding), binding)
        self.assertEqual(signed["played_character_id"], 0xF1000001 - 2**32)
        self.assertEqual(signed["played_character_full_id"], 0xF1000001)

    def test_unavailable_is_explicit_null_and_never_empty(self):
        value = payload(self.binding)
        value.update(available=False, roster_complete=False,
                     unavailable_reason="native_cache_double_read_changed",
                     native_count=None, complete_cached_successor_ids=None,
                     native_data_pointer=None, land_state_pointer=None)
        observed = query.project_native_query(envelope(self.binding, value), self.binding)
        self.assertIsNone(observed["native_result"][query.NESTED_KEY]["complete_cached_successor_ids"])
        self.assertEqual(observed["native_result"]["status"], "unavailable")
        for mutation in ({"native_count": 0}, {"complete_cached_successor_ids": []},
                         {"native_data_pointer": 0}, {"land_state_pointer": 0},
                         {"roster_complete": True}, {"unavailable_reason": None}):
            bad = deepcopy(value)
            bad.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                query.normalize_cached_succession(bad, self.binding)

    def test_malformed_types_count_ids_and_pointers_are_refused(self):
        mutations = (
            {"native_count": True}, {"native_count": -1}, {"native_count": 2**31},
            {"native_count": 2}, {"complete_cached_successor_ids": (1, 2, 3)},
            {"complete_cached_successor_ids": [True, 17, 18]},
            {"complete_cached_successor_ids": [0xFFFFFFFF, 17, 18]},
            {"complete_cached_successor_ids": [-1, 17, 18]},
            {"native_data_pointer": 0}, {"native_data_pointer": True},
            {"native_data_pointer": 2**64}, {"land_state_pointer": 0},
            {"land_state_pointer": True}, {"land_state_pointer": 2**64},
            {"capture_epoch": 0}, {"capture_epoch": True}, {"date_raw": 53144713},
            {"played_character_id": 65866}, {"played_character_full_id": True},
            {"played_character_full_id": 65866}, {"roster_complete": False},
            {"available": 1}, {"read_only": False}, {"unavailable_reason": "unexpected"},
            {"schema": "ck3-1.20.0.3-actor-cached-succession-v1"}, {"extra": None},
        )
        for mutation in mutations:
            bad = payload(self.binding)
            bad.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                query.normalize_cached_succession(bad, self.binding)

    def test_exact4_binding_rejects_stale_revision_and_noncurrent_owners(self):
        for revision in (0, -1, True, 3.0, None, 2**64, 4):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                query.query_binding(frame(), revision)
        mutations = (
            lambda f: f["diagnostics"]["hello"].update(
                expected_ck3_version="1.20.0.3",
                expected_ck3_sha256=MODULES["xar_autoplayer.bridge.version_identity"].CK3_12003.executable_sha256,
                game_adapter_id="ck3-1.20.0.3-msvc-x64"),
            lambda f: f["diagnostics"]["hello"].update(expected_ck3_sha256="0" * 64),
            lambda f: f["diagnostics"]["hello"].update(ck3_build_match=False),
            lambda f: f["diagnostics"]["hello"].update(game_adapter_id="ck3-1.20.0.3-msvc-x64"),
            lambda f: f["diagnostics"]["hello"].update(pid=True),
            lambda f: f["diagnostics"].update(connected=False),
            lambda f: f["diagnostics"].update(connection_generation=True),
            lambda f: f.update(paused=False),
            lambda f: f.update(map_ready=False),
            lambda f: f["played_character"].update(alive=False),
            lambda f: f["played_character"].update(character_id=-1),
            lambda f: f.update(one_life_terminal_reason="dead"),
        )
        for mutation in mutations:
            bad = frame()
            mutation(bad)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                query.query_binding(bad, 3)

    def test_envelope_public_revision_and_false_credit_are_bound(self):
        public = query.project_native_query(envelope(self.binding), self.binding, query.CK3_12004)
        self.assertEqual((public["queried_revision"], public["queried_native_revision"]), (3, 7))
        self.assertFalse(public["business_postcondition_verified"])
        self.assertFalse(public["full_product_acceptance_credit"])
        self.assertEqual(query.normalize_public_query(public, self.binding), public)
        for key, value in (("snapshot_revision", 3), ("snapshot_revision", True),
                           ("date_raw", 53144712.0), ("backend_id", "native-headless"),
                           ("domain_key", "confucian_assembly_predicates_v1"),
                           ("advertised", True), ("read_only", False),
                           ("executable_sha256", "0" * 64), ("status", "unavailable"),
                           ("extra", None)):
            bad = envelope(self.binding)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                query.project_native_query(bad, self.binding)
        for key, value in (("queried_revision", 7), ("queried_native_revision", 3),
                           ("game_pid", 992), ("connection_generation", 3),
                           ("player_character_id", 65866),
                           ("business_postcondition_verified", True),
                           ("full_product_acceptance_credit", True), ("extra", None)):
            bad = deepcopy(public)
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                query.normalize_public_query(bad, self.binding)


class TransportTests(unittest.TestCase):
    def test_one_memory_send_uses_native7_and_thin_driver_method(self):
        method = extract_function(BRIDGE / "native_driver.py", "query_actor_cached_succession_v1",
                                  "NativeHeadlessGameplayDriver")
        driver = MemoryDriver()
        with patch.dict(sys.modules, MODULES):
            result = method(driver, expected_revision=3)
        self.assertEqual(result["queried_revision"], 3)
        self.assertEqual(result["queried_native_revision"], 7)
        self.assertEqual(len(driver.sent), 1)
        request = driver.sent[0]
        self.assertEqual(set(request), {
            "type", "protocol_version", "request_id", "step", "expected_snapshot_revision"})
        self.assertEqual(request["expected_snapshot_revision"], 7)
        self.assertEqual(request["step"], query.STEP)
        self.assertTrue(request["request_id"].startswith("actor-cached-succession-"))

    def test_default_off_invalid_binding_timeout_send_nothing(self):
        driver = MemoryDriver()
        driver.allow_private_actor_cached_succession_queries = False
        with self.assertRaises(UnsupportedStepError):
            driver.query_actor_cached_succession_v1(expected_revision=3)
        self.assertEqual(driver.sent, [])
        self.assertEqual(driver.snapshots, 0)
        for revision in (True, 4):
            driver = MemoryDriver()
            with self.assertRaises(BridgeUnavailableError):
                driver.query_actor_cached_succession_v1(expected_revision=revision)
            self.assertEqual(driver.sent, [])
        for timeout in (True, 0, -1, 61, float("nan"), float("inf")):
            driver = MemoryDriver()
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                query.query_actor_cached_succession_private_v1(
                    driver, expected_revision=3, timeout_seconds=timeout)
            self.assertEqual(driver.sent, [])
            self.assertEqual(driver.snapshots, 0)

    def test_unresolved_native_error_and_foreign_receipt_never_retry(self):
        responses = (
            lambda request: None,
            lambda request: {"type": "command_result", "protocol_version": 1,
                             "request_id": request, "ok": False, "error": "cache_unavailable"},
            lambda request: {"type": "command_result", "protocol_version": 1,
                             "request_id": "foreign", "ok": True},
            lambda request: {"type": "command_result", "protocol_version": True,
                             "request_id": request, "ok": True},
            lambda request: {"type": "command_result", "protocol_version": 1,
                             "request_id": request, "ok": True, "result": {}},
        )
        for response in responses:
            driver = MemoryDriver(response=response)
            with self.subTest(response=response), self.assertRaises(BridgeUnavailableError):
                driver.query_actor_cached_succession_v1(expected_revision=3)
            self.assertEqual(len(driver.sent), 1)

    def test_crossed_paused_frame_owner_and_binding_are_refused(self):
        mutations = (
            lambda f: f.update(native_revision=8),
            lambda f: f.update(revision=4),
            lambda f: f.update(date_raw=53144713),
            lambda f: f.update(snapshot_id="foreign"),
            lambda f: f.update(speed=1),
            lambda f: f.update(paused=False),
            lambda f: f.update(active_event={"instance_id": 5}),
            lambda f: f.update(pending_character_interaction={"id": 2}),
            lambda f: f.update(episode_run_id="foreign"),
            lambda f: f.update(episode_character_id=65866),
            lambda f: f["diagnostics"].update(connection_generation=3),
            lambda f: f["diagnostics"]["hello"].update(pid=992),
            lambda f: f["played_character"].update(character_id=65866),
        )
        for mutation in mutations:
            after = frame()
            mutation(after)
            driver = MemoryDriver(after=after)
            with self.subTest(mutation=mutation), self.assertRaises(BridgeUnavailableError):
                driver.query_actor_cached_succession_v1(expected_revision=3)
            self.assertEqual(len(driver.sent), 1)

    def test_actual_service_method_revalidates_public_result_and_frame(self):
        method = extract_function(BRIDGE / "service.py", "query_actor_cached_succession_v1",
                                  "GameplayBridgeService")
        driver = MemoryDriver()
        owner = types.SimpleNamespace(driver=driver)
        with patch.dict(sys.modules, MODULES):
            result = method(owner, expected_revision=3)
        self.assertEqual(result["queried_native_revision"], 7)
        self.assertEqual(len(driver.sent), 1)
        driver = MemoryDriver()
        driver.query_actor_cached_succession_v1 = lambda **kwargs: {
            **query.project_native_query(envelope(query.query_binding(frame(), 3)),
                                         query.query_binding(frame(), 3)),
            "full_product_acceptance_credit": True}
        with patch.dict(sys.modules, MODULES), self.assertRaises(BridgeUnavailableError):
            method(types.SimpleNamespace(driver=driver), expected_revision=3)
        with patch.dict(sys.modules, MODULES), self.assertRaises(UnsupportedStepError):
            method(types.SimpleNamespace(driver=types.SimpleNamespace()), expected_revision=3)

    def test_driver_constructor_permission_is_strict_default_false(self):
        constructor = method_node(BRIDGE / "native_driver.py",
                                  "NativeHeadlessGameplayDriver", "__init__")
        names = [argument.arg for argument in constructor.args.kwonlyargs]
        index = names.index(query.PERMISSION)
        self.assertIs(constructor.args.kw_defaults[index].value, False)
        guard = next(node for node in constructor.body if isinstance(node, ast.If)
                     and query.PERMISSION in ast.unparse(node.test))
        assignment = next(node for node in constructor.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Attribute) and target.attr == query.PERMISSION
                                  for target in node.targets))
        tree = ast.fix_missing_locations(ast.Module(body=[guard, assignment], type_ignores=[]))
        for value in (False, True):
            owner = types.SimpleNamespace()
            exec(compile(tree, "<permission-only>", "exec"),
                 {"self": owner, query.PERMISSION: value})
            self.assertIs(getattr(owner, query.PERMISSION), value)
        for value in (1, None, "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exec(compile(tree, "<permission-only>", "exec"),
                     {"self": types.SimpleNamespace(), query.PERMISSION: value})


class StubAnnotations:
    def __init__(self, **values):
        self.values = values


class StubServer:
    def __init__(self, name):
        self.name = name
        self.tools = {}
        self.closed_arguments = set()

    def tool(self, *, annotations):
        def register(function):
            self.tools[function.__name__] = {
                "function": function, "annotations": annotations.values,
                "annotation": function.__annotations__,
            }
            return function
        return register


def stub_registration():
    mcp = types.ModuleType("mcp")
    server_module = types.ModuleType("mcp.server")
    server_module.MCPServer = StubServer
    types_module = types.ModuleType("mcp.types")
    types_module.ToolAnnotations = StubAnnotations
    register = extract_function(PROFILE, "create_server", globals_extra={
        "_forbid_unknown_tool_arguments_v1":
            lambda server, name: server.closed_arguments.add(name),
    })
    return register, {"mcp": mcp, "mcp.server": server_module, "mcp.types": types_module}


class ProfileSourceTests(unittest.TestCase):
    def test_default21_23_24_28_inventories_unchanged_and_flag_adds_one(self):
        register, sdk_stubs = stub_registration()
        name = "ck3_query_profile_actor_cached_succession_v1"
        for arguments, count in (
                ({}, 21), ({"confucian_readonly_tools": True}, 23),
                ({"confucian_challenger_tools": True}, 24),
                ({"confucian_challenger_tools": True, "grant_title_picker_tools": True}, 28)):
            with self.subTest(arguments=arguments), patch.dict(sys.modules, sdk_stubs):
                off = register(types.SimpleNamespace(), **arguments)
                on = register(types.SimpleNamespace(), actor_cached_succession_tools=True, **arguments)
            self.assertEqual(len(off.tools), count)
            self.assertEqual(len(on.tools), count + 1)
            self.assertEqual(set(on.tools) - set(off.tools), {name})
            self.assertNotIn(name, off.tools)
            for existing in off.tools:
                self.assertEqual(off.tools[existing]["annotations"], on.tools[existing]["annotations"])
                self.assertEqual(off.tools[existing]["annotation"], on.tools[existing]["annotation"])
            self.assertIn(name, on.closed_arguments)
            annotations = on.tools[name]["annotations"]
            self.assertIs(annotations["readOnlyHint"], True)
            self.assertIs(annotations["destructiveHint"], False)
            self.assertIs(annotations["openWorldHint"], False)
            self.assertEqual(on.tools[name]["annotation"]["expected_revision"],
                             "ActorCachedSuccessionRevisionV1")
            self.assertEqual(list(on.tools[name]["function"].__code__.co_varnames), ["expected_revision"])
        for value in (1, None, "true"):
            with patch.dict(sys.modules, sdk_stubs), self.assertRaises(ValueError):
                register(types.SimpleNamespace(), actor_cached_succession_tools=value)

    def test_strict_revision_alias_and_cli_flag_are_wired_without_main_calls(self):
        tree = source_tree(PROFILE)
        alias = next(node for node in tree.body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name)
                             and target.id == "ActorCachedSuccessionRevisionV1" for target in node.targets))
        field = alias.value.slice.elts[1]
        self.assertEqual(field.func.id, "Field")
        options = {option.arg: ast.literal_eval(option.value) if not isinstance(option.value, ast.BinOp)
                   else eval(compile(ast.Expression(option.value), "<bound>", "eval"), {})
                   for option in field.keywords}
        self.assertEqual(options, {"strict": True, "gt": 0, "lt": 2**64})
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        flag_calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                      and isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
                      and node.args and isinstance(node.args[0], ast.Constant)
                      and node.args[0].value == "--actor-cached-succession-tools"]
        self.assertEqual(len(flag_calls), 1)
        self.assertEqual({keyword.arg: ast.literal_eval(keyword.value)
                          for keyword in flag_calls[0].keywords if keyword.arg == "action"},
                         {"action": "store_true"})
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "create_server"]
        self.assertEqual(len(calls), 1)
        selected = next(keyword.value for keyword in calls[0].keywords
                        if keyword.arg == "actor_cached_succession_tools")
        self.assertEqual(ast.unparse(selected), "args.actor_cached_succession_tools")
        guard = next(node for node in main.body if isinstance(node, ast.If)
                     and "args.clock_only" in ast.unparse(node.test)
                     and "args.actor_cached_succession_tools" in ast.unparse(node.test))
        self.assertTrue(guard.body)

    def test_profile_wrapper_restores_permission_and_rechecks_frame(self):
        method = extract_function(PROFILE, "query_actor_cached_succession", "NativeProfileService")
        driver = MemoryDriver()
        driver.allow_private_actor_cached_succession_queries = False
        gameplay = types.SimpleNamespace(query_actor_cached_succession_v1=
            driver.query_actor_cached_succession_v1)
        owner = types.SimpleNamespace(
            driver=driver, _lock=threading.RLock(),
            _actor_cached_succession_tools_enabled_v1=True,
            _bound_frame=lambda revision, paused=False: frame(),
            _gameplay_service=lambda: gameplay,
            _receipt=lambda operation, value: {"operation": operation, **value},
        )
        with patch.dict(sys.modules, MODULES):
            result = method(owner, 3)
        self.assertFalse(driver.allow_private_actor_cached_succession_queries)
        self.assertEqual(result["status"], "native_actor_cached_succession_observed")
        self.assertFalse(result["business_effects_verified"])
        self.assertFalse(result["full_product_acceptance_credit"])
        self.assertEqual(len(driver.sent), 1)
        def failure(**kwargs):
            raise BridgeUnavailableError("source fixture failure")
        gameplay.query_actor_cached_succession_v1 = failure
        with patch.dict(sys.modules, MODULES), self.assertRaises(BridgeUnavailableError):
            method(owner, 3)
        self.assertFalse(driver.allow_private_actor_cached_succession_queries)
        owner._actor_cached_succession_tools_enabled_v1 = False
        with patch.dict(sys.modules, MODULES), self.assertRaises(RuntimeError):
            method(owner, 3)


if __name__ == "__main__":
    unittest.main()

