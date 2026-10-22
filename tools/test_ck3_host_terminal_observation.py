"""Actual host AST -> public exit wire -> terminal consumer; no native/OS I/O."""
from __future__ import annotations

import ast
import asyncio
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from typing import Protocol, runtime_checkable
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
sys.path.insert(0, str(REPO))
from xar_autoplayer.bridge.normal_exit_contract_v1 import classify_terminal_exit_receipt
from xar_autoplayer.bridge.normal_exit_process_observer_v1 import RetainedProcessIdentity
from xar_autoplayer.bridge.normal_exit_public_wire_v2 import normal_exit_public_result_v2
from xar_autoplayer.bridge.normal_exit_host_terminal_v1 import (
    completed_process_final_observation_v1, normal_exit_revision_from_snapshot_v2,
)

HOST = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
BIRTH = 134371180626519916
REVISION = 2**53 + 1


def public_terminal_result(*, observed: bool = False, signaled: bool = True) -> dict[str, object]:
    """Use real classification and V2 encoding on an authored retained-handle DTO."""
    process: dict[str, object] = {"pid": 43, "creation_filetime_100ns": BIRTH,
        "retained_handle_token": "authored-original-handle", "wait_result": 0 if signaled else 258,
        "wait_state": "signaled" if signaled else "timeout", "exit_code": 0 if signaled else None,
        "process_identity_verified": True, "process_exit_observed": signaled,
        "observed_monotonic_ns": 2**64 - 1, "timeout_ms": 5000,
        "observation_deadline_reached": False, "observation_clock_domain": "driver_monotonic_v1", "errors": []}
    facts: object = classify_terminal_exit_receipt(None, process,
        driver_dispatch_receipt_observed_monotonic_ns=None,
        expected_process_identity=RetainedProcessIdentity(43, BIRTH, "authored-original-handle"))
    if not isinstance(facts, dict):
        raise AssertionError("Actual classifier must produce a fact object")
    result = {"schema": "ck3-normal-exit-process-observation-result-v1" if observed else "ck3-normal-exit-request-result-v1",
        "action": "confirm_desktop", **facts, "native_observation": None, "process_observation": process,
        "process_preconfirm_pin": {"pid": 43, "creation_filetime_100ns": BIRTH,
            "retained_handle_token": "authored-original-handle", "wait_result": 258,
            "verified_monotonic_ns": 2**53 + 2, "observation_clock_domain": "driver_monotonic_v1"},
        "driver_dispatch_receipt_observed_monotonic_ns": None, "receipt_clock_meaning": "authored driver receipt",
        "snapshot_after_required": False, "observer_retained": not signaled, "public_revision": REVISION,
        "request_id": "authored-once-exit", "claim_path": "authored-no-native-claim",
        "source_inventory_sha256": "b" * 64, "process_creation_filetime_100ns": BIRTH,
        "uses_desktop_input": False, "uses_ocr": False, "native_submission_count": 0 if observed else 1}
    return normal_exit_public_result_v2(result)


def object_row(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        raise AssertionError("Authored or retained fixture must be an object")
    return {key: item for key, item in value.items()}


@runtime_checkable
class HostClient(Protocol):
    report: dict[str, object]
    snapshot: dict[str, object]
    async def invoke(self, name: str, arguments: object = None, *, fresh_revision: bool = True) -> object: ...
    async def execute(self, plan: list[dict[str, object]]) -> None: ...
    async def observe_final(self) -> None: ...


def actual_client(report: dict[str, object], result: object, calls: list[tuple[str, object]],
        fresh_calls: list[str], *, snapshot_revision: object = REVISION) -> HostClient:
    """Compile the unchanged source AST methods; only transport/clock are authored."""
    tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
    names = {"lookup", "resolve", "finished_native_process_exit_zero_proof",
             "finished_native_exit_zero_proof", "finished_native_failure_shutdown_proof"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PlanClient")
    methods: list[ast.stmt] = [node for node in original.body if isinstance(node, ast.AsyncFunctionDef) and
               node.name in {"invoke", "execute", "observe_final"}]
    if len(nodes) != len(names) or len(methods) != 3:
        raise AssertionError("Actual host dependency scope incomplete")
    node = ast.ClassDef(name="ActualPlanClient", bases=[], keywords=[], body=methods, decorator_list=[])
    namespace: dict[str, object] = {"datetime": datetime, "timezone": timezone, "re": re,
        "copy": copy, "json": json, "now": lambda: "AUTHORED-NO-GAME-CLOCK"}
    module = ast.fix_missing_locations(ast.Module(body=[ast.ImportFrom(module="__future__",
        names=[ast.alias(name="annotations")], level=0), *nodes, node], type_ignores=[]))
    exec(compile(module, str(HOST), "exec"), namespace)
    factory = namespace["ActualPlanClient"]
    if not isinstance(factory, type):
        raise AssertionError("Actual AST class missing")
    candidate: object = factory()
    async def fresh() -> dict[str, object]:
        fresh_calls.append("fresh")
        return {"revision": snapshot_revision}
    async def call(name: str, arguments: object = None) -> object:
        calls.append((name, copy.deepcopy(arguments)))
        return copy.deepcopy(result)
    for key, value in {"report": report, "snapshot": {"revision": snapshot_revision}, "results": {},
        "tools": {"ck3_request_normal_exit_v1": {"inputSchema": {"properties": {"expected_revision": {"type": "string"}}}},
                  "ck3_query_normal_exit_context_v1": {"inputSchema": {"properties": {"expected_revision": {"type": "string"}}}}},
        "episode_identity": None, "args": SimpleNamespace(frontend_mod_load_observation=False),
        "managed_done": SimpleNamespace(is_set=lambda: True), "fresh": fresh, "call": call, "write": lambda: None}.items():
        setattr(candidate, key, value)
    if not isinstance(candidate, HostClient):
        raise AssertionError("Compiled actual host does not expose the required methods")
    return candidate


class HostTerminalObservationTests(unittest.TestCase):
    def test_registered_mcp_textual_json_reaches_actual_host_consumer(self) -> None:
        from mcp import Client
        from mcp.types import TextContent
        from xar_autoplayer.bridge.mcp_server import create_server
        from ck3_autonomous_player.tests.unit.test_normal_exit_public_wire_v2 import MemoryDriver

        async def exercise() -> None:
            driver = MemoryDriver()
            async with Client(create_server(driver)) as public:
                tools = {tool.name: {"inputSchema": tool.input_schema} for tool in (await public.list_tools()).tools}
                fresh: list[str] = []
                report: dict[str, object] = {"steps": []}
                client = actual_client(report, None, [], fresh)
                setattr(client, "tools", tools)

                async def actual_mcp_call(name: str, arguments: object = None) -> object:
                    reply = await public.call_tool(name, object_row(arguments))
                    self.assertFalse(reply.is_error)
                    texts = [item.text for item in reply.content if isinstance(item, TextContent)]
                    self.assertEqual(len(texts), 1)
                    # Consume the real public textual serializer, including the
                    # canonical string fields, instead of returning a mirrored DTO.
                    value: object = json.loads(texts[0])
                    return value

                setattr(client, "call", actual_mcp_call)
                await client.execute([{"id": "registered-request", "tool": "ck3_request_normal_exit_v1",
                    "args": {"action": "confirm_desktop", "expected_exit_context_signature": "c" * 64}}])
                await client.execute([{"id": "registered-observe", "tool": "ck3_observe_normal_exit_v1", "args": {}}])
                self.assertEqual(driver.calls, [("request", REVISION), ("observe", None)])
                self.assertEqual(fresh, ["fresh"])
                rows = report["steps"]
                if not isinstance(rows, list): raise AssertionError("Actual host rows missing")
                self.assertEqual(len(rows), 2)
                for value in rows:
                    row = object_row(value)
                    self.assertIs(row["ok"], True)
                    self.assertNotIn("after_snapshot", row)
                    result = object_row(row["result"])
                    self.assertEqual(result["process_creation_filetime_100ns"], str(BIRTH))

        asyncio.run(exercise())

    def test_actual_invoke_execute_encodes_revision_and_keeps_terminal_wire(self) -> None:
        for observed in (False, True):
            with self.subTest(observed=observed):
                calls: list[tuple[str, object]] = []
                fresh: list[str] = []
                wire = public_terminal_result(observed=observed)
                report: dict[str, object] = {"steps": []}
                client = actual_client(report, json.loads(json.dumps(wire)), calls, fresh)
                tool = "ck3_observe_normal_exit_v1" if observed else "ck3_request_normal_exit_v1"
                arguments: dict[str, object] = {} if observed else {"action": "confirm_desktop", "expected_exit_context_signature": "c" * 64}
                asyncio.run(client.execute([{"id": "actual-terminal", "kind": "tool", "tool": tool, "args": arguments}]))
                self.assertEqual(len(fresh), 0 if observed else 1)
                self.assertEqual(calls, [(tool, {} if observed else {**arguments, "expected_revision": str(REVISION)})])
                steps = report["steps"]
                self.assertIsInstance(steps, list)
                if not isinstance(steps, list): raise AssertionError("Actual host rows missing")
                row = object_row(steps[0])
                self.assertIs(row["ok"], True)
                self.assertEqual(row["result"], wire)
                self.assertNotIn("after_snapshot", row)
                self.assertEqual(wire["process_creation_filetime_100ns"], str(BIRTH))

    def test_pending_observer_is_not_exit_credit_and_never_calls_alive_snapshot(self) -> None:
        wire = public_terminal_result(observed=True, signaled=False)
        report: dict[str, object] = {"steps": []}
        fresh: list[str] = []
        client = actual_client(report, wire, [], fresh)
        asyncio.run(client.execute([{"id": "pending", "tool": "ck3_observe_normal_exit_v1", "args": {}}]))
        self.assertEqual(fresh, [])
        self.assertIs(wire["process_exit_observed"], False)
        self.assertIs(wire["typed_normal_exit_observed"], False)
        self.assertIs(wire["retry_authorized"], False)

    def test_actual_execute_rejects_malformed_terminal_without_dead_fallback(self) -> None:
        mutations: tuple[tuple[str, object], ...] = (("snapshot_after_required", 0), ("public_revision", REVISION),
            ("process_creation_filetime_100ns", float(BIRTH)), ("schema", "ck3-normal-exit-request-result-v1"))
        for key, value in mutations:
            with self.subTest(key=key):
                wire = public_terminal_result()
                wire[key] = value
                fresh: list[str] = []
                report: dict[str, object] = {"steps": []}
                client = actual_client(report, wire, [], fresh)
                with self.assertRaises(ValueError):
                    asyncio.run(client.execute([{"id": "malformed", "tool": "ck3_request_normal_exit_v1",
                        "args": {"action": "confirm_desktop", "expected_revision": str(REVISION)}, "fresh_revision": False}]))
                self.assertEqual(fresh, [])
                rows = report["steps"]
                if not isinstance(rows, list): raise AssertionError("Actual host rows missing")
                self.assertIs(object_row(rows[0])["ok"], False)

    def test_snapshot_and_explicit_revision_types_reject_false_equal_values(self) -> None:
        for bad in (True, False, 0, 1.0, "1", 2**64):
            with self.subTest(snapshot_revision=bad), self.assertRaises(ValueError):
                normal_exit_revision_from_snapshot_v2(bad)
        for bad in (True, 1, 1.0, "01", "0"):
            calls: list[tuple[str, object]] = []
            client = actual_client({"steps": []}, public_terminal_result(), calls, [])
            with self.subTest(explicit_revision=bad), self.assertRaises(ValueError):
                asyncio.run(client.invoke("ck3_request_normal_exit_v1", {"action": "confirm_desktop", "expected_revision": bad}, fresh_revision=False))
            self.assertEqual(calls, [])

    def test_actual_r8_failed_row_and_cleanup_skip_final_dead_read_without_rewriting_failure(self) -> None:
        original = object_row(json.loads((REPO / "tools/fixtures/ck3_host_terminal_r8.json").read_bytes()))
        report = copy.deepcopy(object_row(original["report"]))
        before = copy.deepcopy(report)
        calls: list[tuple[str, object]] = []
        fresh: list[str] = []
        client = actual_client(report, {}, calls, fresh)
        asyncio.run(client.observe_final())
        self.assertEqual(calls, [])
        self.assertEqual(fresh, [])
        self.assertEqual(report["steps"], before["steps"])
        self.assertEqual(report["status"], "RED")
        self.assertEqual(report["error"], before["error"])
        self.assertEqual(report["final_observation_error"], before["final_observation_error"])
        terminal = object_row(report["final_observation"])
        self.assertEqual(terminal["status"], "not_applicable")
        self.assertIs(terminal["failure_preserved"], True)
        self.assertIs(terminal["business_pass"], False)
        self.assertIs(terminal["normal_close_qualified"], False)
        failed_ids = terminal["failed_step_ids"]
        if not isinstance(failed_ids, list): raise AssertionError("Typed failed-step list missing")
        self.assertEqual(len(failed_ids), 1)

    def test_incomplete_cleanup_or_nonzero_exit_keeps_actual_final_reader(self) -> None:
        fixture = object_row(json.loads((REPO / "tools/fixtures/ck3_host_terminal_r8.json").read_bytes()))
        for name in ("managed_session_thread_finished", "native_exit", "cleanup"):
            report = copy.deepcopy(object_row(fixture["report"]))
            if name == "managed_session_thread_finished": report[name] = False
            else:
                native = object_row(object_row(report["session"])["report"])
                if name == "native_exit": native["process_exit_code"] = 1
                else:
                    shutdown = object_row(native["shutdown"])
                    shutdown["cleanup_proven"] = False
                    native["shutdown"] = shutdown
                report["session"] = {"error": None, "report": native}
            fresh: list[str] = []
            calls: list[tuple[str, object]] = []
            client = actual_client(report, {}, calls, fresh)
            with self.subTest(name=name):
                asyncio.run(client.observe_final())
                self.assertEqual(fresh, ["fresh"])
                self.assertEqual(calls, [("ck3_migration_pipe_diagnostics", None)])

    def test_final_metadata_rejects_false_equal_exit_pid_and_row_outcome(self) -> None:
        fixture = object_row(json.loads((REPO / "tools/fixtures/ck3_host_terminal_r8.json").read_bytes()))
        report = object_row(fixture["report"])
        marker = object_row(report["post_exit_finish_hold"])
        proof = object_row(marker["proof"])
        for key, value in (("pid", True), ("process_exit_code", False), ("process_exit_code", 0.0)):
            bad = {**proof, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                completed_process_final_observation_v1(bad, host_error=None, step_rows=[])
        with self.assertRaises(ValueError):
            completed_process_final_observation_v1(proof, host_error=None, step_rows=[{"id": "bad", "ok": 1}])


if __name__ == "__main__": unittest.main()
