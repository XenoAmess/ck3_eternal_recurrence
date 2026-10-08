"""Bounded own-laws tests without importing the production bridge module graph.

The new contract leaf is loaded directly. New service/native method bodies and
MCP registration are compiled from their actual source AST, with caller-owned
snapshot/primitive doubles. No driver, endpoint, SDK, game or pipe is constructed.
"""
from __future__ import annotations

import ast
import asyncio
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated
import unittest

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field


BRIDGE = Path(__file__).resolve().parents[1] / "src/xar_autoplayer/bridge"
_SPEC = importlib.util.spec_from_file_location("isolated_title_own_laws_contract", BRIDGE / "title_own_laws_contract.py")
CONTRACT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CONTRACT)
_TREES: dict[str, ast.Module] = {}
MCP_CELLS: list[dict[str, object]] = []


class BridgeUnavailableError(RuntimeError):
    pass


class UnsupportedStepError(RuntimeError):
    pass


class PreSubmissionRevisionMismatchError(RuntimeError):
    pass


def _tree(filename: str) -> ast.Module:
    if filename not in _TREES:
        _TREES[filename] = ast.parse((BRIDGE / filename).read_text("utf-8-sig"))
    return _TREES[filename]


def _node(filename: str, name: str, *, class_name: str | None = None) -> ast.FunctionDef:
    root = _tree(filename)
    if class_name is not None:
        root = next(item for item in root.body if isinstance(item, ast.ClassDef) and item.name == class_name)
        matches = [item for item in root.body if isinstance(item, ast.FunctionDef) and item.name == name]
    else:
        matches = [item for item in ast.walk(root) if isinstance(item, ast.FunctionDef) and item.name == name]
    if len(matches) != 1:
        raise AssertionError((filename, name, len(matches)))
    return copy.deepcopy(matches[0])


def _namespace() -> dict[str, object]:
    return {
        **vars(CONTRACT), "BridgeUnavailableError": BridgeUnavailableError,
        "UnsupportedStepError": UnsupportedStepError,
        "PreSubmissionRevisionMismatchError": PreSubmissionRevisionMismatchError,
    }


def _compile(node: ast.FunctionDef, filename: str, namespace: dict[str, object] | None = None):
    namespace = _namespace() if namespace is None else namespace
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(BRIDGE / filename), "exec"), namespace)
    return namespace[node.name]


def _snapshot() -> dict[str, object]:
    return {
        "revision": 17, "native_revision": 71, "date_raw": 100660915,
        "paused": True, "map_ready": True, "snapshot_id": "native-frame-71",
        "played_character": {"character_id": 12345, "alive": True},
        "diagnostics": {"connection_generation": 3}, "episode_run_id": "episode-a",
    }


def _dto(title_id: int = 0x80000000, laws: list[dict[str, object]] | None = None) -> dict[str, object]:
    laws = [] if laws is None else copy.deepcopy(laws)
    snapshot = _snapshot()
    return {
        "schema": CONTRACT.TITLE_OWN_LAWS_V1_SCHEMA, "schema_version": 1,
        "game_version": CONTRACT.TITLE_OWN_LAWS_V1_GAME_VERSION,
        "executable_sha256": CONTRACT.TITLE_OWN_LAWS_V1_EXE_SHA256,
        "status": "available", "available": True, "unavailable_reason": None,
        "snapshot_revision": snapshot["native_revision"], "date_raw": snapshot["date_raw"],
        "actor_character_id": snapshot["played_character"]["character_id"],
        "title_id": title_id, "native_law_count": len(laws), "laws": laws,
        "single_heir_member": any(row["key"] == "single_heir_succession_law" for row in laws),
    }


def _unavailable(title_id: int = 0x80000000) -> dict[str, object]:
    value = _dto(title_id)
    value.update(status="unavailable", available=False, unavailable_reason="title_identity_not_resolved",
                 native_law_count=None, laws=None, single_heir_member=None)
    return value


def _normalize(value: object, title_id: int = 0x80000000) -> dict[str, object]:
    snapshot = _snapshot()
    return CONTRACT.normalize_title_own_laws_v1(
        value, expected_title_id=title_id, expected_actor_character_id=12345,
        expected_snapshot_revision=snapshot["native_revision"], expected_date_raw=snapshot["date_raw"],
    )


def _envelope(title_id: int = 0x80000000, *, unavailable: bool = False) -> dict[str, object]:
    value = _unavailable(title_id) if unavailable else _dto(title_id)
    return {
        "step": CONTRACT.query_title_own_laws_v1_step(title_id), "accepted": True,
        "read_only": True, "backend_id": "native-headless", "status": value["status"],
        "query_sequence": 1, "snapshot_revision": 71, "date_raw": 100660915,
        "title_own_laws": value,
    }


class ServiceDouble:
    query_title_own_laws_v1 = _compile(_node("service.py", "query_title_own_laws_v1"), "service.py")

    def __init__(self, title_id: int = 0x80000000):
        self.frame = _snapshot()
        self.result = _envelope(title_id)
        self.bridge_capabilities = [CONTRACT.QUERY_TITLE_OWN_LAWS_V1_CAPABILITY]
        self.calls: list[dict[str, object]] = []
        self.snapshot_calls = 0

    def snapshot(self):
        self.snapshot_calls += 1
        return copy.deepcopy(self.frame)

    def capabilities(self):
        return {"bridge_capabilities": self.bridge_capabilities}

    def execute_step(self, step, *, expected_revision):
        self.calls.append({"step": step, "expected_revision": expected_revision})
        return copy.deepcopy(self.result)


_NATIVE_NAMESPACE = _namespace()
_NATIVE_NAMESPACE["_same_paused_native_frame"] = _compile(_node("native_driver.py", "_same_paused_native_frame"), "native_driver.py")


class NativeDouble:
    query_title_own_laws_v1 = _compile(_node("native_driver.py", "query_title_own_laws_v1"), "native_driver.py")
    _execute_title_own_laws_v1_query = _compile(_node("native_driver.py", "_execute_title_own_laws_v1_query"), "native_driver.py", _NATIVE_NAMESPACE)

    def __init__(self, title_id: int = 0x80000000):
        self.frames = [_snapshot(), _snapshot()]
        self.result = _envelope(title_id)
        self.calls: list[dict[str, object]] = []
        self.snapshot_calls = 0

    def take_snapshot(self):
        value = copy.deepcopy(self.frames[self.snapshot_calls])
        self.snapshot_calls += 1
        return value

    def _execute_primitive_step(self, step, *, expected_revision, required_capability):
        self.calls.append({"step": step, "expected_revision": expected_revision, "required_capability": required_capability})
        if expected_revision != self.frames[0]["revision"]:
            raise PreSubmissionRevisionMismatchError("caller-owned primitive stale-revision guard")
        return copy.deepcopy(self.result)


class TitleOwnLawsContractTests(unittest.TestCase):
    def test_full_uint32_title_ids_and_strict_input(self):
        for value in (0, 0x80000000, 0xFFFFFFFE):
            with self.subTest(valid=value):
                step = CONTRACT.query_title_own_laws_v1_step(value)
                self.assertEqual(step, "query-title-own-laws-v1-" + str(value))
                self.assertEqual(CONTRACT.parse_query_title_own_laws_v1_step(step), value)
        for value in ("0", 0.0, True, False, -1, 0xFFFFFFFF, 0x100000000):
            with self.subTest(invalid=value), self.assertRaises(ValueError):
                CONTRACT.query_title_own_laws_v1_step(value)

    def test_only_canonical_unsigned_decimal_steps(self):
        for token in ("", "ID", "-1", "+1", " 1", "1 ", "01", "0.0", "１", "4294967295", "10000000000"):
            with self.subTest(token=token):
                self.assertIsNone(CONTRACT.parse_query_title_own_laws_v1_step(CONTRACT.QUERY_TITLE_OWN_LAWS_V1_STEP_PREFIX + token))
        self.assertIsNone(CONTRACT.parse_query_title_own_laws_v1_step(None))

    def test_paused_current_actor_required_without_holder_or_faith(self):
        self.assertEqual(CONTRACT.title_own_laws_query_actor(_snapshot()), 12345)
        for key, replacement in (("paused", False), ("map_ready", False), ("played_character", None),
                                 ("played_character", {"alive": False, "character_id": 12345}),
                                 ("played_character", {"alive": True, "character_id": True})):
            value = _snapshot()
            value[key] = replacement
            with self.subTest(key=key, value=replacement), self.assertRaises(ValueError):
                CONTRACT.title_own_laws_query_actor(value)

    def test_ordered_rows_deepcopy_printable_ascii_and_definition_uint32_max(self):
        rows = [{"native_definition_id": 0xFFFFFFFF, "key": "Upper-Case.!~"},
                {"native_definition_id": 0, "key": "single_heir_succession_law"}]
        value = _dto(laws=rows)
        result = _normalize(value)
        self.assertEqual(result["laws"], rows)
        self.assertTrue(result["single_heir_member"])
        result["laws"][0]["key"] = "changed"
        self.assertEqual(value["laws"], rows)

    def test_empty_available_is_distinct_from_unavailable(self):
        empty, missing = _normalize(_dto()), _normalize(_unavailable())
        self.assertEqual((empty["available"], empty["native_law_count"], empty["laws"], empty["single_heir_member"]), (True, 0, [], False))
        self.assertEqual((missing["available"], missing["native_law_count"], missing["laws"], missing["single_heir_member"]), (False, None, None, None))
        for field, replacement in (("unavailable_reason", ""), ("native_law_count", 0), ("laws", []), ("single_heir_member", False)):
            value = _unavailable()
            value[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                _normalize(value)

    def test_complete_dto_fields_and_exact_provenance(self):
        value = _unavailable()
        del value["laws"]
        with self.assertRaises(ValueError):
            _normalize(value)
        for field, replacement in (("schema", "other"), ("schema_version", True), ("game_version", "1.20.0.3"),
                                   ("executable_sha256", "0" * 64), ("unavailable_reason", "not-null")):
            value = _dto()
            value[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                _normalize(value)

    def test_title_actor_revision_and_date_are_independent_bindings(self):
        for field, replacement in (("title_id", 0), ("actor_character_id", 9), ("snapshot_revision", 72),
                                   ("date_raw", 100660916), ("snapshot_revision", True), ("title_id", True)):
            value = _dto()
            value[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                _normalize(value)

    def test_count_bounds_complete_rows_and_keys(self):
        valid_rows = [{"native_definition_id": i, "key": "a"} for i in range(256)]
        self.assertEqual(len(_normalize(_dto(laws=valid_rows))["laws"]), 256)
        malformed = []
        value = _dto(laws=[{"native_definition_id": 1, "key": "a"}])
        value["native_law_count"] = 2
        malformed.append(value)
        malformed.append(_dto(laws=valid_rows + [{"native_definition_id": 256, "key": "a"}]))
        value = _dto()
        value["native_law_count"] = False
        malformed.append(value)
        for definition in (True, -1, 2**32):
            malformed.append(_dto(laws=[{"native_definition_id": definition, "key": "a"}]))
        for key in ("", "a b", "\x20", "\x7f", "é", "a" * 256):
            malformed.append(_dto(laws=[{"native_definition_id": 1, "key": key}]))
        value = _dto(laws=[{"native_definition_id": 1, "key": "a", "inferred_holder": 7}])
        malformed.append(value)
        for index, value in enumerate(malformed):
            with self.subTest(index=index), self.assertRaises(ValueError):
                _normalize(value)

    def test_single_heir_uses_exact_complete_key_membership(self):
        value = _dto(laws=[{"native_definition_id": 5, "key": "single_heir_succession_law_extra"}])
        self.assertFalse(_normalize(value)["single_heir_member"])
        for available, member, status in ((True, True, "available"), (True, False, "unavailable"), (1, False, "available")):
            value = _dto()
            value.update(available=available, single_heir_member=member, status=status)
            with self.subTest(value=value), self.assertRaises(ValueError):
                _normalize(value)


class TitleOwnLawsRouteTests(unittest.TestCase):
    def test_service_rejects_bad_scalar_inputs_before_snapshot_or_execute(self):
        for title_id, revision in (("0", 17), (0.0, 17), (True, 17), (0xFFFFFFFF, 17),
                                   (0, "17"), (0, 17.0), (0, True), (0, -1)):
            service = ServiceDouble()
            with self.subTest(title_id=title_id, revision=revision), self.assertRaises(ValueError):
                service.query_title_own_laws_v1(title_id, expected_revision=revision)
            self.assertEqual(service.calls, [])
            self.assertEqual(service.snapshot_calls, 0)

    def test_service_routes_unsigned_id_with_public_and_native_revision(self):
        for title_id in (0, 0x80000000, 0xFFFFFFFE):
            service = ServiceDouble(title_id)
            result = service.query_title_own_laws_v1(title_id, expected_revision=17)
            self.assertEqual(service.calls, [{"step": CONTRACT.query_title_own_laws_v1_step(title_id), "expected_revision": 17}])
            self.assertEqual(result["title_id"], title_id)
            self.assertEqual(result["queried_native_revision"], 71)
            self.assertEqual(result["queried_revision"], 17)
            self.assertEqual(result["title_own_laws"]["actor_character_id"], 12345)

    def test_service_refuses_stale_revision_unready_actor_and_missing_capability(self):
        service = ServiceDouble()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            service.query_title_own_laws_v1(0x80000000, expected_revision=16)
        self.assertEqual(service.calls, [])
        service = ServiceDouble()
        service.bridge_capabilities = []
        with self.assertRaises(UnsupportedStepError):
            service.query_title_own_laws_v1(0x80000000, expected_revision=17)
        self.assertEqual(service.calls, [])
        service = ServiceDouble()
        service.frame["paused"] = False
        with self.assertRaises(BridgeUnavailableError):
            service.query_title_own_laws_v1(0x80000000, expected_revision=17)
        self.assertEqual(service.calls, [])

    def test_service_rejects_malformed_outer_and_mixed_inner_bindings(self):
        for field, replacement in (("accepted", False), ("read_only", False), ("backend_id", "hybrid"),
                                   ("step", "query-title-own-laws-v1-0"), ("snapshot_revision", 17),
                                   ("date_raw", 0), ("query_sequence", 0), ("query_sequence", True),
                                   ("query_sequence", 2**64), ("status", "unavailable")):
            service = ServiceDouble()
            service.result[field] = replacement
            with self.subTest(field=field), self.assertRaises(BridgeUnavailableError):
                service.query_title_own_laws_v1(0x80000000, expected_revision=17)
        service = ServiceDouble()
        service.result["title_own_laws"]["actor_character_id"] = 99
        with self.assertRaises(BridgeUnavailableError):
            service.query_title_own_laws_v1(0x80000000, expected_revision=17)

    def test_service_preserves_reason_and_nulls_for_unavailable_read(self):
        service = ServiceDouble()
        service.result = _envelope(unavailable=True)
        result = service.query_title_own_laws_v1(0x80000000, expected_revision=17)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["title_own_laws"]["laws"])
        self.assertEqual(result["title_own_laws"]["unavailable_reason"], "title_identity_not_resolved")

    def test_native_query_uses_required_capability_and_checks_two_paused_frames(self):
        for title_id in (0, 0x80000000, 0xFFFFFFFE):
            driver = NativeDouble(title_id)
            result = driver._execute_title_own_laws_v1_query(CONTRACT.query_title_own_laws_v1_step(title_id), expected_revision=17)
            self.assertEqual(driver.calls, [{"step": CONTRACT.query_title_own_laws_v1_step(title_id), "expected_revision": 17,
                                            "required_capability": CONTRACT.QUERY_TITLE_OWN_LAWS_V1_CAPABILITY}])
            self.assertEqual(driver.snapshot_calls, 2)
            self.assertEqual(result["title_own_laws"]["title_id"], title_id)

    def test_native_query_rejects_frame_owner_and_date_changes(self):
        for field, replacement in (("native_revision", 72), ("snapshot_id", "other"), ("paused", False),
                                   ("date_raw", 100660916), ("episode_run_id", "other"),
                                   ("diagnostics", {"connection_generation": 4}),
                                   ("played_character", {"character_id": 99, "alive": True})):
            driver = NativeDouble()
            driver.frames[1][field] = replacement
            with self.subTest(field=field), self.assertRaises(BridgeUnavailableError):
                driver._execute_title_own_laws_v1_query(CONTRACT.query_title_own_laws_v1_step(0x80000000), expected_revision=17)
            self.assertEqual(len(driver.calls), 1)

    def test_native_refuses_malformed_step_revision_envelope_and_stale_primitive(self):
        driver = NativeDouble()
        with self.assertRaises(UnsupportedStepError):
            driver._execute_title_own_laws_v1_query("query-title-own-laws-v1-4294967295", expected_revision=17)
        self.assertEqual((driver.snapshot_calls, len(driver.calls)), (0, 0))
        driver = NativeDouble()
        with self.assertRaises(ValueError):
            driver._execute_title_own_laws_v1_query("query-title-own-laws-v1-0", expected_revision=True)
        self.assertEqual((driver.snapshot_calls, len(driver.calls)), (0, 0))
        driver = NativeDouble()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            driver._execute_title_own_laws_v1_query("query-title-own-laws-v1-2147483648", expected_revision=16)
        self.assertEqual(driver.calls[0]["expected_revision"], 16)
        for field, replacement in (("backend_id", "hybrid"), ("read_only", False), ("query_sequence", 0)):
            driver = NativeDouble()
            driver.result[field] = replacement
            with self.subTest(field=field), self.assertRaises(BridgeUnavailableError):
                driver._execute_title_own_laws_v1_query("query-title-own-laws-v1-2147483648", expected_revision=17)
            self.assertEqual(driver.snapshot_calls, 1)

    def test_native_public_method_keeps_unsigned_payload_and_strict_inputs(self):
        calls = []
        driver = SimpleNamespace(execute_step=lambda step, **kwargs: calls.append((step, kwargs)) or {"sentinel": True})
        method = NativeDouble.query_title_own_laws_v1
        self.assertEqual(method(driver, 0xFFFFFFFE, expected_revision=0), {"sentinel": True})
        self.assertEqual(calls, [("query-title-own-laws-v1-4294967294", {"expected_revision": 0})])
        for title_id, revision in ((True, 0), (0, True)):
            with self.assertRaises(ValueError):
                method(driver, title_id, expected_revision=revision)
        self.assertEqual(len(calls), 1)

    def test_exact_new_native_execute_step_router_statements(self):
        node = _node("native_driver.py", "_execute_step_unrecorded", class_name="NativeHeadlessGameplayDriver")
        selected = []
        for statement in node.body:
            names = {item.id for item in ast.walk(statement) if isinstance(item, ast.Name)}
            if "title_own_laws_title_id" in names:
                selected.append(copy.deepcopy(statement))
        self.assertEqual(len(selected), 3)
        node.name = "isolated_exact_new_router"
        node.body = selected
        router = _compile(node, "native_driver.py")
        calls = []
        driver = SimpleNamespace(_execute_title_own_laws_v1_query=lambda step, **kwargs: calls.append((step, kwargs)) or {"routed": True})
        for title_id in (0, 0x80000000, 0xFFFFFFFE):
            self.assertEqual(router(driver, CONTRACT.query_title_own_laws_v1_step(title_id), expected_revision=17), {"routed": True})
        with self.assertRaises(UnsupportedStepError):
            router(driver, "query-title-own-laws-v1-ID", expected_revision=17)
        self.assertEqual(len(calls), 3)

    def test_hybrid_fails_closed_before_any_backend_access(self):
        hybrid = _compile(_node("native_driver.py", "execute_step", class_name="ConfiguredHybridFallbackDriver"), "native_driver.py")
        for step in ("query-title-own-laws-v1-0", "query-title-own-laws-v1-2147483648", "query-title-own-laws-v1-ID"):
            with self.subTest(step=step), self.assertRaises(UnsupportedStepError):
                hybrid(object(), step, expected_revision=17)

    def test_exact_action_steps_excludes_template_and_dynamic_prefix(self):
        node = _node("native_driver.py", "_action_steps")
        namespace = _namespace()
        # Other capability constants are distinct sentinels; this qualifies the
        # new exclusion only, without importing or requalifying old capabilities.
        for item in ast.walk(node):
            if isinstance(item, ast.Name) and item.id.isupper() and item.id not in namespace:
                namespace[item.id] = False if item.id.endswith("PRODUCTION_ENABLED") else "unused:" + item.id
        namespace["_ACTION_CAPABILITY_PREFIX"] = "game.command."
        namespace["controllable_armies"] = lambda armies: []
        action_steps = _compile(node, "native_driver.py", namespace)
        capabilities = [CONTRACT.QUERY_TITLE_OWN_LAWS_V1_CAPABILITY,
                        "game.command.query-title-own-laws-v1-2147483648",
                        "game.command.query-title-own-laws-v1-4294967294", "game.command.pause"]
        self.assertEqual(action_steps(capabilities), ["pause"])


class TitleOwnLawsMCPTests(unittest.TestCase):
    def test_real_call_tool_strict_inputs_and_unsigned_boundaries(self):
        class ForwardingService:
            def __init__(self):
                self.calls = []

            def query_title_own_laws_v1(self, title_id, *, expected_revision):
                self.calls.append({"title_id": title_id, "expected_revision": expected_revision,
                                   "title_type": type(title_id).__name__, "revision_type": type(expected_revision).__name__})
                return {"title_id": title_id, "expected_revision": expected_revision}

        service = ForwardingService()
        server = MCPServer(name="Isolated title own-laws source validation")
        namespace = {"server": server, "service": service, "Annotated": Annotated, "Field": Field,
                     "read_only_tool": ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)}
        _compile(_node("mcp_server.py", "ck3_query_title_own_laws_v1"), "mcp_server.py", namespace)

        async def check():
            tools = await server.list_tools()
            tool = next(item for item in tools if item.name == "ck3_query_title_own_laws_v1")
            annotations = tool.annotations.model_dump(by_alias=True)
            schema = tool.model_dump(by_alias=True)["inputSchema"]
            self.assertTrue(annotations["readOnlyHint"])
            self.assertFalse(annotations["destructiveHint"])
            self.assertEqual(schema["properties"]["title_id"]["minimum"], 0)
            self.assertEqual(schema["properties"]["title_id"]["exclusiveMaximum"], 4294967295)
            self.assertEqual(schema["properties"]["expected_revision"]["minimum"], 0)
            inputs = [({"title_id": value, "expected_revision": 0}, False) for value in ("0", 0.0, True, -1, 0xFFFFFFFF)]
            inputs += [({"title_id": 0, "expected_revision": value}, False) for value in ("0", 0.0, True, -1)]
            inputs += [({"title_id": 0}, False), ({"expected_revision": 0}, False)]
            inputs += [({"title_id": value, "expected_revision": 0}, True) for value in (0, 0x80000000, 0xFFFFFFFE)]
            for args, valid in inputs:
                count = len(service.calls)
                error = None
                try:
                    await server.call_tool("ck3_query_title_own_laws_v1", args)
                    returned = True
                except Exception as exception:
                    returned = False
                    error = type(exception).__name__ + ": " + str(exception)[:220]
                called = len(service.calls) != count
                MCP_CELLS.append({"input": args, "returned": returned, "service_called": called, "error": error,
                                  "observed_service_call": service.calls[-1] if called else None})
                self.assertEqual((returned, called), (valid, valid), args)
            self.assertEqual(len(service.calls), 3)
            self.assertEqual([row["title_id"] for row in service.calls], [0, 0x80000000, 0xFFFFFFFE])

        asyncio.run(check())


if __name__ == "__main__":
    unittest.main(verbosity=2)
