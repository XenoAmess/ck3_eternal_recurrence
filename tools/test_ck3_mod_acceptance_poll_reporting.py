"""Portable evidence/cadence tests for actual startup reporting code only."""
from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import traceback
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock
import uuid

HOST = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"


class PollReportingTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        wanted = {"serialized", "JsonLines", "StartupPollReporting", "annotate_write_error", "write_atomic_report",
                  "wait_for_consistent_frontend", "wait_for_fixture_business_context", "fixture_qualification_counts"}
        cls.definitions = [node for node in tree.body if getattr(node, "name", None) in wanted]
        run = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "run")
        cls.actual_write = next(node for node in run.body if isinstance(node, ast.FunctionDef) and node.name == "write")

    def context(self, *, reporting=True):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "report.json"
        value = SimpleNamespace(clock=0.0, report={"phase": "SYNTHETIC_ONLY", "status": "RUNNING",
            "steps": [], "frontend_bootstrap": {"attempts": []}, "business_PASS_inferred": False},
            done=threading.Event(), writes=[], path=path)

        async def sleep(seconds):
            value.clock += seconds

        namespace = {"Path": Path, "threading": threading, "json": json, "os": os, "uuid": uuid,
                     "traceback": traceback, "time": SimpleNamespace(monotonic=lambda: value.clock),
                     "asyncio": SimpleNamespace(sleep=sleep), "PlanClient": object,
                     "now": lambda: "SYNTHETIC@" + str(value.clock)}
        module = ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[]))
        exec(compile(module, str(HOST), "exec"), namespace)
        atomic = namespace["write_atomic_report"]

        def counted(path, report):
            value.writes.append({"at": value.clock, "kind": getattr(value, "kind", "critical"),
                                 "managed_done": report["managed_session_done"],
                                 "status": report["status"],
                                 "business_status": report.get("frontend_fixture_business_context", {}).get("status"),
                                 "admission": "first_whole_root_query_admission" in report.get("frontend_fixture_business_context", {})})
            atomic(path, report)

        namespace.update(write_atomic_report=counted, report=value.report, done=value.done, args=SimpleNamespace(output=path))
        write_module = ast.fix_missing_locations(ast.Module(body=[self.actual_write], type_ignores=[]))
        exec(compile(write_module, str(HOST), "exec"), namespace)
        value.write = namespace["write"]
        value.reporting = None
        if reporting:
            def ordinary():
                value.kind = "ordinary"
                try:
                    value.write()
                finally:
                    value.kind = "critical"
            value.reporting = namespace["StartupPollReporting"](path.with_suffix(".frontend-observations.jsonl"), ordinary)
            value.report["frontend_observations_journal"] = str(value.reporting.journal.path)
        namespace["require_consistent_frontend_observation"] = lambda before, tree, after, **kwargs: {
            "route": before["route"], "scope_root_name": "SYNTHETIC", "widgets": tree["widgets"]}
        namespace["fixture_whole_root_admission_frame"] = lambda snapshot, submission, **kwargs: {
            "actor": 22, "date_raw": 100, "pump_epoch": snapshot["pump"]}
        value.namespace = namespace
        return value

    def journal_rows(self, context, collection):
        path = context.reporting.journal.path
        values = [json.loads(line)["message"] for line in path.read_text(encoding="utf-8").splitlines()]
        records = [row for row in values if row["collection"] == collection]
        self.assertEqual([row["index"] for row in records], list(range(len(records))))
        return [row["observation"] for row in records]

    def fixture_module(self):
        module = ModuleType("xar_autoplayer.bridge.frontend_fixture_start_contract")
        module.require_fixture_start_submission = lambda value: value
        module.fixture_business_context_binding = lambda snapshot, root, policy, submission: {
            "actor": 22, "date_raw": 100, "pump_epoch": snapshot["pump"]}
        return mock.patch.dict(sys.modules, {module.__name__: module})

    def business_client(self, qualified_after=55):
        class Client:
            def __init__(self):
                self.count = 0
                self.calls = []
            async def fresh(self):
                self.count += 1
                return {"snapshot_id": "s" + str(self.count), "revision": self.count, "pump": self.count,
                        "map_ready": True, "paused": True, "active_event": None}
            async def call(self, name, arguments):
                self.calls.append((name, arguments))
                if name == "ck3_query_engine_log_literals_v1":
                    return {"schema": "xar.ck3.engine-log-literals/v1", "log_name": "debug.log", "exists": True,
                            "read_only": True, "case_sensitive": True,
                            "matches": [{"literal": "READY", "line_count": int(self.count >= qualified_after)},
                                        {"literal": "FAIL", "line_count": 0}]}
                return {"queried_snapshot_id": "s" + str(self.count + 1), "queried_revision": self.count + 1}
        return Client()

    def frontend_client(self, keys, *, error_first=False, cancel=False):
        class Client:
            def __init__(self):
                self.index = 0
                self.route_calls = 0
                self.calls = []
            async def call(self, name):
                self.calls.append(name)
                if cancel:
                    import asyncio
                    raise asyncio.CancelledError()
                if error_first and self.index == 0:
                    self.index += 1
                    raise RuntimeError("SYNTHETIC frontend unavailable")
                if name == "ck3_inspect_frontend_gui_tree_v1":
                    return {"widgets": [{"id": keys[self.index], "full_payload": [1, 2, 3]}]}
                self.route_calls += 1
                result = {"route": "main_menu", "synthetic": True}
                if self.route_calls % 2 == 0:
                    self.index += 1
                return result
        return Client()

    async def test_ordinary_checkpoint_count_and_full_final_evidence_are_preserved(self):
        context = self.context()
        context.report["observations"] = []
        for index in range(200):
            context.clock = (index + 1) / 20
            row = {"index": index, "full_composed_payload": {"values": list(range(20))}}
            context.report["observations"].append(row)
            context.reporting.observe("synthetic.observations", index, row)
            context.reporting.checkpoint()
        ordinary = [row for row in context.writes if row["kind"] == "ordinary"]
        self.assertEqual([row["at"] for row in ordinary], [5.0, 10.0])
        context.done.set()
        context.report.update(status="SYNTHETIC_FINISHED", phase="final")
        context.write()
        self.assertEqual(len(context.writes), 3)
        self.assertTrue(context.writes[-1]["managed_done"])
        self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)
        self.assertEqual(self.journal_rows(context, "synthetic.observations"), context.report["observations"])

    async def test_actual_business_poll_keeps_every_row_and_forces_admission_and_ready(self):
        context = self.context()
        client = self.business_client()
        policy = {"required_log_markers": ["READY"], "forbidden_log_markers": ["FAIL"]}
        with self.fixture_module():
            result = await context.namespace["wait_for_fixture_business_context"](client, policy, {},
                report=context.report, write=context.write, timeout=20, poll_interval=.1, poll_reporting=context.reporting)
        self.assertGreater(len(result["observations"]), 55)
        self.assertEqual(result["status"], "ACTUAL_FIXTURE_QUALIFIED_BUSINESS_CONTEXT_BOUND")
        self.assertLess(len(context.writes), len(result["observations"]) / 5)
        self.assertTrue(any(row["admission"] and row["kind"] == "critical" for row in context.writes))
        self.assertEqual(context.writes[-1]["business_status"], result["status"])
        self.assertEqual(context.writes[-1]["kind"], "critical")
        self.assertEqual(self.journal_rows(context, "frontend_fixture_business_context.observations"), result["observations"])
        self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)
        self.assertFalse(context.report["business_PASS_inferred"])

    async def test_actual_frontend_poll_limits_ordinary_writes_and_forces_two_frame_ready(self):
        context = self.context()
        keys = list(range(40)) + [39]
        client = self.frontend_client(keys)
        result = await context.namespace["wait_for_consistent_frontend"](client,
            report=context.report, write=context.write, timeout=20, poll_interval=.25, poll_reporting=context.reporting)
        attempts = context.report["frontend_bootstrap"]["attempts"]
        self.assertEqual(len(attempts), len(keys))
        self.assertEqual(len(client.calls), len(keys) * 3)
        self.assertEqual(result[2]["consecutive_consistent_observations"], 2)
        ordinary = [row["at"] for row in context.writes if row["kind"] == "ordinary"]
        self.assertEqual(ordinary, [5.0, 10.0])
        self.assertEqual(context.writes[-1]["kind"], "critical")
        self.assertEqual(self.journal_rows(context, "frontend_bootstrap.attempts"), attempts)
        self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)

    async def test_frontend_errors_managed_done_and_cancellation_retain_original_row(self):
        context = self.context()
        client = self.frontend_client([0, 7, 7], error_first=True)
        await context.namespace["wait_for_consistent_frontend"](client,
            report=context.report, write=context.write, timeout=5, poll_interval=.25, poll_reporting=context.reporting)
        self.assertEqual(context.writes[0]["at"], 0)
        self.assertEqual(context.writes[0]["kind"], "critical")
        self.assertIn("error", context.report["frontend_bootstrap"]["attempts"][0])
        self.assertEqual(self.journal_rows(context, "frontend_bootstrap.attempts"), context.report["frontend_bootstrap"]["attempts"])
        context = self.context()
        context.done.set()
        client = self.frontend_client([])
        with self.assertRaises(RuntimeError):
            await context.namespace["wait_for_consistent_frontend"](client, report=context.report, write=context.write,
                timeout=5, managed_done=context.done, poll_reporting=context.reporting)
        self.assertEqual(client.calls, [])
        self.assertTrue(context.writes[-1]["managed_done"])
        self.assertEqual(self.journal_rows(context, "frontend_bootstrap.attempts"), context.report["frontend_bootstrap"]["attempts"])
        context = self.context()
        client = self.frontend_client([], cancel=True)
        import asyncio
        with self.assertRaises(asyncio.CancelledError):
            await context.namespace["wait_for_consistent_frontend"](client, report=context.report, write=context.write,
                timeout=5, poll_reporting=context.reporting)
        context.report.update(status="SYNTHETIC_CANCELLED", error="CancelledError")
        context.write()
        self.assertEqual(self.journal_rows(context, "frontend_bootstrap.attempts"), context.report["frontend_bootstrap"]["attempts"])
        self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)

    async def test_default_none_keeps_immediate_writes_and_business_timeout_is_immediate(self):
        context = self.context(reporting=False)
        client = self.frontend_client([7, 7])
        await context.namespace["wait_for_consistent_frontend"](client, report=context.report, write=context.write, timeout=5)
        self.assertEqual(len(context.writes), 4)
        self.assertFalse(context.path.with_suffix(".frontend-observations.jsonl").exists())
        for reporting in (False, True):
            context = self.context(reporting=reporting)
            client = self.business_client(qualified_after=1000)
            with self.fixture_module(), self.assertRaises(TimeoutError):
                await context.namespace["wait_for_fixture_business_context"](client,
                    {"required_log_markers": ["READY"], "forbidden_log_markers": ["FAIL"]}, {},
                    report=context.report, write=context.write, timeout=.2, poll_interval=.1, poll_reporting=context.reporting)
            state = context.report["frontend_fixture_business_context"]
            self.assertEqual(state["status"], "FAILED_AFTER_SINGLE_START_NO_RETRY")
            self.assertEqual(context.writes[-1]["kind"], "critical")
            self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)
            if not reporting:
                self.assertEqual(len(context.writes), len(state["observations"]) + 2)
            else:
                self.assertEqual(self.journal_rows(context, "frontend_fixture_business_context.observations"), state["observations"])

    async def test_sidecar_io_failure_propagates_once_and_keeps_full_error_report(self):
        context = self.context()
        client = self.business_client(qualified_after=1000)
        error = OSError("SYNTHETIC sidecar failure")
        with self.fixture_module(), mock.patch.object(context.reporting.journal, "write", side_effect=error) as sink:
            with self.assertRaises(OSError) as raised:
                await context.namespace["wait_for_fixture_business_context"](client,
                    {"required_log_markers": ["READY"], "forbidden_log_markers": ["FAIL"]}, {},
                    report=context.report, write=context.write, timeout=5, poll_reporting=context.reporting)
        self.assertIs(raised.exception, error)
        self.assertEqual(sink.call_count, 1)
        state = context.report["frontend_fixture_business_context"]
        self.assertEqual(len(state["observations"]), 1)
        self.assertEqual(state["status"], "FAILED_AFTER_SINGLE_START_NO_RETRY")
        self.assertEqual(json.loads(context.path.read_text(encoding="utf-8")), context.report)


if __name__ == "__main__":
    unittest.main()
