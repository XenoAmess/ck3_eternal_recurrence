"""Focused actual4 truce DTO, source-route and real MCP validation.

Load only the new contract leaf and exact source AST bodies. Snapshot/primitive
doubles are caller-owned; no production driver, game, SDK or pipe is constructed.
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
_SPEC = importlib.util.spec_from_file_location("isolated_player_truce_expiry_contract", BRIDGE / "player_truce_expiry_contract.py")
CONTRACT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(CONTRACT)
MCP_CELLS: list[dict[str, object]] = []
_TREES: dict[str, ast.Module] = {}


class BridgeUnavailableError(RuntimeError):
    pass


class UnsupportedStepError(RuntimeError):
    pass


class PreSubmissionRevisionMismatchError(RuntimeError):
    pass


def _node(filename, name, class_name=None):
    if filename not in _TREES:
        _TREES[filename] = ast.parse((BRIDGE / filename).read_text("utf-8-sig"))
    tree = _TREES[filename]
    if class_name:
        tree = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == class_name)
        matches = [item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name]
    else:
        matches = [item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == name]
    if len(matches) != 1:
        raise ValueError((filename, name, len(matches)))
    return copy.deepcopy(matches[0])


def _compile(node, filename, namespace=None):
    if namespace is None:
        namespace = {**vars(CONTRACT), "BridgeUnavailableError": BridgeUnavailableError,
                     "UnsupportedStepError": UnsupportedStepError,
                     "PreSubmissionRevisionMismatchError": PreSubmissionRevisionMismatchError}
    code = compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                   str(BRIDGE / filename), "exec", dont_inherit=True)
    exec(code, namespace)
    return namespace[node.name]


def _snapshot():
    return {"revision": 17, "native_revision": 71, "date_raw": 100660915,
            "paused": True, "map_ready": True, "snapshot_id": "native-frame-71",
            "played_character": {"character_id": 12345, "alive": True},
            "diagnostics": {"connection_generation": 3}, "episode_run_id": "episode-a"}


def _wire(no_truce=False, toward_id=67890):
    payload = {"schema_version": 1, "backend_id": CONTRACT.PLAYER_TRUCE_EXPIRY_V1_BACKEND_ID,
               "ck3_build": CONTRACT.PLAYER_TRUCE_EXPIRY_V1_BUILD,
               "executable_sha256": CONTRACT.PLAYER_TRUCE_EXPIRY_V1_EXECUTABLE_SHA256,
               "status": "no_truce" if no_truce else "available", "snapshot_revision": 71,
               "current_date_raw": 100660915, "owner_character_id": 12345,
               "toward_character_id": toward_id, "native_has_truce": not no_truce,
               "actual_expiry_observable": not no_truce,
               "expiry_date_raw": None if no_truce else 100661915,
               "same_frame_stable": True, "readiness": not no_truce,
               "temporal_semantics": "post_application_persisted_relation_state",
               "unavailable_reason": "native_has_truce_false" if no_truce else None}
    return {"step": CONTRACT.query_player_truce_expiry_v1_step(toward_id), "accepted": True,
            "query_sequence": 1, "snapshot_revision": 71, "raiktor_actual_truce_expiry": payload,
            "backend_id": "native-headless", "read_only": True, "date_raw": 100660915}


def _normalize(wire):
    return CONTRACT.normalize_player_truce_expiry_v1(
        wire, expected_toward_character_id=67890, expected_owner_character_id=12345,
        expected_snapshot_revision=71, expected_date_raw=100660915)


_FRAME = _compile(_node("native_driver.py", "_same_paused_native_frame"), "native_driver.py")
_NATIVE_NAMESPACE = {**vars(CONTRACT), "BridgeUnavailableError": BridgeUnavailableError,
                     "UnsupportedStepError": UnsupportedStepError,
                     "PreSubmissionRevisionMismatchError": PreSubmissionRevisionMismatchError,
                     "_same_paused_native_frame": _FRAME}


class NativeDouble:
    query_player_truce_expiry_v1 = _compile(
        _node("native_driver.py", "query_player_truce_expiry_v1", "NativeHeadlessGameplayDriver"),
        "native_driver.py", _NATIVE_NAMESPACE)

    def __init__(self, no_truce=False):
        self.before = _snapshot()
        self.after = _snapshot()
        self.result = _wire(no_truce)
        self.reads, self.calls, self.records = 0, [], []

    def take_snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.before if self.reads == 1 else self.after)

    def _execute_primitive_step(self, step, **kwargs):
        self.calls.append((step, kwargs))
        return copy.deepcopy(self.result)

    def _record_command(self, step, **kwargs):
        self.records.append((step, kwargs))


class ServiceDouble:
    query_player_truce_expiry_v1 = _compile(
        _node("service.py", "query_player_truce_expiry_v1", "GameplayBridgeService"), "service.py")

    def __init__(self, no_truce=False):
        self.frame, self.reads, self.calls = _snapshot(), 0, []
        self.result = _wire(no_truce)
        self.caps = [CONTRACT.QUERY_PLAYER_TRUCE_EXPIRY_V1_CAPABILITY]
        self.driver = SimpleNamespace(query_player_truce_expiry_v1=self._query)

    def snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.frame)

    def capabilities(self):
        return {"bridge_capabilities": self.caps}

    def _query(self, toward_character_id, **kwargs):
        self.calls.append((toward_character_id, kwargs))
        return copy.deepcopy(self.result)


class PlayerTruceExpiryTests(unittest.TestCase):
    def test_available_and_observed_absence_remain_distinct(self):
        present, absent = _normalize(_wire()), _normalize(_wire(True))
        self.assertTrue(present["readiness"])
        self.assertGreater(present["expiry_date_raw"], present["current_date_raw"])
        self.assertEqual(absent["status"], "no_truce")
        self.assertFalse(absent["readiness"])
        self.assertIsNone(absent["expiry_date_raw"])
        self.assertEqual(absent["unavailable_reason"], "native_has_truce_false")
        for field, value in (("status", "unavailable"), ("same_frame_stable", False),
                             ("owner_character_id", 12346), ("snapshot_revision", 72),
                             ("executable_sha256", "0" * 64)):
            malformed = _wire(True)
            malformed["raiktor_actual_truce_expiry"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                _normalize(malformed)
        malformed = _wire()
        malformed.pop("read_only")
        with self.assertRaises(ValueError):
            _normalize(malformed)

    def test_service_validates_before_driver_and_binds_current_frame(self):
        service = ServiceDouble(True)
        result = service.query_player_truce_expiry_v1(67890, expected_revision=17)
        self.assertEqual(result["player_truce_expiry_v1"]["status"], "no_truce")
        self.assertFalse(result["player_truce_expiry_v1"]["readiness"])
        self.assertEqual((result["queried_revision"], result["queried_native_revision"]), (17, 71))
        self.assertEqual(service.calls, [(67890, {"expected_revision": 17})])
        present = ServiceDouble().query_player_truce_expiry_v1(67890, expected_revision=17)
        self.assertTrue(present["player_truce_expiry_v1"]["readiness"])
        for args in (("67890", 17), (True, 17), (0, 17), (67890, False), (67890, -1)):
            service = ServiceDouble()
            with self.subTest(args=args), self.assertRaises(ValueError):
                service.query_player_truce_expiry_v1(args[0], expected_revision=args[1])
            self.assertEqual((service.reads, service.calls), (0, []))
        service = ServiceDouble()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            service.query_player_truce_expiry_v1(67890, expected_revision=16)
        self.assertEqual(service.calls, [])
        service = ServiceDouble()
        service.result["raiktor_actual_truce_expiry"]["owner_character_id"] = 12346
        with self.assertRaises(BridgeUnavailableError):
            service.query_player_truce_expiry_v1(67890, expected_revision=17)

    def test_native_direct_read_without_wars_and_two_frame_closure(self):
        native = NativeDouble(True)
        result = native.query_player_truce_expiry_v1(67890, expected_revision=17)
        self.assertEqual(result["raiktor_actual_truce_expiry"]["status"], "no_truce")
        self.assertEqual(native.calls, [(CONTRACT.query_player_truce_expiry_v1_step(67890),
                                       {"expected_revision": 17, "required_capability": CONTRACT.QUERY_PLAYER_TRUCE_EXPIRY_V1_CAPABILITY})])
        self.assertEqual(native.reads, 2)
        self.assertTrue(native.records[-1][1]["ok"])
        present = NativeDouble().query_player_truce_expiry_v1(67890, expected_revision=17)
        self.assertTrue(present["raiktor_actual_truce_expiry"]["readiness"])
        native = NativeDouble()
        with self.assertRaises(PreSubmissionRevisionMismatchError):
            native.query_player_truce_expiry_v1(67890, expected_revision=16)
        self.assertEqual(native.calls, [])
        for field, value in (("date_raw", 100660916), ("native_revision", 72),
                             ("played_character", {"character_id": 12346, "alive": True})):
            native = NativeDouble()
            native.after[field] = value
            with self.subTest(field=field), self.assertRaises(BridgeUnavailableError):
                native.query_player_truce_expiry_v1(67890, expected_revision=17)
            self.assertFalse(native.records[-1][1]["ok"])

    def test_hybrid_fails_closed_without_delegating(self):
        query = _compile(_node("native_driver.py", "query_player_truce_expiry_v1", "ConfiguredHybridFallbackDriver"), "native_driver.py")
        with self.assertRaises(UnsupportedStepError):
            query(object(), 67890, expected_revision=17)
        service = ServiceDouble()
        service.caps = []
        with self.assertRaises(UnsupportedStepError):
            service.query_player_truce_expiry_v1(67890, expected_revision=17)
        self.assertEqual(service.calls, [])

    def test_existing_action_filter_excludes_reused_cap_and_dynamic_step(self):
        node = _node("native_driver.py", "_action_steps")
        namespace = {name.id: "unused-" + name.id for name in ast.walk(node)
                     if isinstance(name, ast.Name) and name.id.isupper()}
        namespace.update(_ACTION_CAPABILITY_PREFIX="game.command.",
                         QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_CAPABILITY=CONTRACT.QUERY_PLAYER_TRUCE_EXPIRY_V1_CAPABILITY,
                         QUERY_RAIKTOR_ACTUAL_TRUCE_EXPIRY_V1_STEP_PREFIX=CONTRACT.QUERY_PLAYER_TRUCE_EXPIRY_V1_STEP_PREFIX,
                         controllable_armies=lambda armies: [])
        steps = _compile(node, "native_driver.py", namespace)
        self.assertEqual(steps([CONTRACT.QUERY_PLAYER_TRUCE_EXPIRY_V1_CAPABILITY,
                                "game.command." + CONTRACT.query_player_truce_expiry_v1_step(67890),
                                "game.command.pause"]), ["pause"])

    def test_real_mcp_call_tool_strict_inputs(self):
        class ForwardingService:
            def __init__(self):
                self.calls = []

            def query_player_truce_expiry_v1(self, toward_character_id, *, expected_revision):
                self.calls.append({"toward_character_id": toward_character_id, "expected_revision": expected_revision})
                return self.calls[-1]

        service = ForwardingService()
        server = MCPServer(name="Isolated player truce expiry source validation")
        namespace = {"server": server, "service": service, "Annotated": Annotated, "Field": Field,
                     "read_only_tool": ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)}
        _compile(_node("mcp_server.py", "ck3_query_player_truce_expiry_v1"), "mcp_server.py", namespace)

        async def check():
            tool = (await server.list_tools())[0]
            annotations = tool.annotations.model_dump(by_alias=True)
            self.assertTrue(annotations["readOnlyHint"])
            self.assertFalse(annotations["destructiveHint"])
            schema = tool.model_dump(by_alias=True)["inputSchema"]["properties"]
            self.assertEqual((schema["toward_character_id"]["exclusiveMinimum"], schema["toward_character_id"]["maximum"]), (0, 2**31 - 1))
            self.assertEqual(schema["expected_revision"]["minimum"], 0)
            cells = [({"toward_character_id": value, "expected_revision": 0}, False)
                     for value in ("1", 1.0, True, 0, 2**31)]
            cells += [({"toward_character_id": 1, "expected_revision": value}, False)
                      for value in ("0", 0.0, True, -1)]
            cells += [({"toward_character_id": 1}, False), ({"expected_revision": 0}, False)]
            cells += [({"toward_character_id": value, "expected_revision": 0}, True) for value in (1, 2**31 - 1)]
            for args, valid in cells:
                count, error = len(service.calls), None
                try:
                    await server.call_tool("ck3_query_player_truce_expiry_v1", args)
                    returned = True
                except Exception as failure:
                    returned, error = False, type(failure).__name__ + ": " + str(failure)[:180]
                called = len(service.calls) != count
                MCP_CELLS.append({"input": args, "returned": returned, "service_called": called, "error": error,
                                  "observed_service_call": service.calls[-1] if called else None})
                self.assertEqual((returned, called), (valid, valid), args)
            self.assertEqual(len(service.calls), 2)

        asyncio.run(check())


if __name__ == "__main__":
    unittest.main(verbosity=2)
