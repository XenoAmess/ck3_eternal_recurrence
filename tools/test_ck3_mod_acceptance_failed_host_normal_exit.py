"""Real queue CLI -> host hold/invoke -> MCP -> existing exit driver, no CK3.

All native endpoints, process API responses and completion DTOs are synthetic.
No process is launched except the actual queue producer's Python CLI.
"""
from __future__ import annotations

import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("XAR_FAILED_EXIT_TEST_SOURCE_ROOT", str(REPO)))
sys.path[:0] = [str(REPO / "tools"), str(REPO / "ck3_autonomous_player/src"),
               str(REPO / "ck3_autonomous_player/tests/unit")]
from mcp import Client
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.normal_exit_host_terminal_v1 import require_failed_host_normal_exit_plan_v1
from test_normal_exit_integrated_v1 import FakeExitDriver, driver_module
import test_ck3_mod_acceptance_failure_shutdown as cleanup_fixture

HOST = SOURCE / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
PRODUCER = SOURCE / "tools/ck3_mod_acceptance_queue_control.py"


def actual_host_class():
    tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
    names = {"lookup", "resolve", "serialized", "tool_envelope", "tool_payload", "load_plan",
             "campaign_speed_presubmission_receipt", "finished_native_process_exit_zero_proof",
             "finished_native_exit_zero_proof", "finished_native_failure_shutdown_proof"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    nodes += [node for node in tree.body if isinstance(node, ast.ClassDef)
              and node.name == "CampaignSpeedPreSubmissionRevisionError"]
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PlanClient")
    methods = [node for node in original.body if isinstance(node, ast.AsyncFunctionDef)
               and node.name in {"call", "fresh", "invoke", "execute", "hold"}]
    if len(nodes) != len(names) + 1 or len(methods) != 5:
        raise AssertionError("Actual production host dependency closure changed")
    selected = ast.ClassDef(name="ActualHost", bases=[], keywords=[], body=methods, decorator_list=[])
    namespace = {"datetime": datetime, "timezone": timezone, "copy": copy, "json": json,
                 "Path": Path, "re": re, "time": __import__("time"), "asyncio": asyncio,
                 "now": lambda: datetime.now(timezone.utc).isoformat()}
    unit = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                           *nodes, selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(unit), str(HOST), "exec"), namespace)
    return namespace["ActualHost"]


class Journal:
    def __init__(self):
        self.rows = []

    def write(self, direction, value):
        self.rows.append((direction, copy.deepcopy(value)))


class FailedHostNormalExitTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="SYNTHETIC_FAILED_EXIT_NO_CK3_")
        self.addCleanup(temporary.cleanup)
        self.live = Path(temporary.name)
        self.controls = self.live / "controls"
        self.controls.mkdir()
        self.report = {"phase": "hold", "finished_at": None, "status": "RED",
                       "error": "SYNTHETIC Actual independent progress scope absent",
                       "steps": [{"id": "original-business-failure", "ok": False,
                                  "error": "preserved original error", "finished_at": "synthetic"}]}
        self.original = copy.deepcopy(self.report)
        self.report_path = self.live / "native-report.json"
        self.frozen = self.live / "frozen-argv.json"
        self.frozen.write_text(json.dumps({"argv": ["SYNTHETIC_NO_HOST_PROCESS",
            "--control-plan-dir", str(self.controls)]}), encoding="utf-8")
        self.client = None

    def publish(self, step, *, name=None, accepted=True):
        self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
        before = self.report_path.read_bytes()
        frozen = self.frozen.read_bytes()
        plan = self.live / "reviewed-plan.json"
        raw = json.dumps({"steps": [step]}, indent=2).encode()
        plan.write_bytes(raw)
        name = name or step["id"] + ".json"
        result = subprocess.run([sys.executable, "-B", "-O", "-X", "utf8", str(PRODUCER),
            "--live", str(self.live), "--plan", str(plan), "--name", name], capture_output=True)
        if self.client is None:
            self.assertEqual(self.report_path.read_bytes(), before)
        self.assertEqual(self.frozen.read_bytes(), frozen)
        if accepted:
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
            self.assertEqual((self.controls / name).read_bytes(), raw)
            receipt = json.loads(result.stdout)
            self.assertEqual(receipt["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertIs(receipt["business_pass"], False)
            self.assertIs(receipt["normal_close_qualified"], False)
            self.assertEqual(receipt["host_error_preserved"], self.original["error"])
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.controls / name).exists())
        return result

    async def wait_row(self, identity):
        for _ in range(300):
            matches = [row for row in self.report["steps"] if row["id"] == identity and row.get("finished_at")]
            if matches:
                return matches[-1]
            await asyncio.sleep(0.01)
        self.fail("Actual host did not consume the once-published control")

    def tool_step(self, identity, tool, args=None, *, fresh=True):
        return {"id": identity, "tool": tool, "args": args or {}, "fresh_revision": fresh}

    async def chain(self, *, unknown):
        driver = FakeExitDriver(self.live / "driver")
        driver.path.mkdir()
        service = GameplayBridgeService(driver)
        done = threading.Event()
        with patch.object(driver_module, "verify_source_inventory_v1",
                          return_value={"source_inventory_sha256": "b" * 64}):
            async with Client(create_server(driver, service_override=service)) as public:
                client = actual_host_class()()
                self.client = client
                client.session = public
                client.args = SimpleNamespace(command_timeout=0.2, frontend_mod_load_observation=False,
                                              control_plan_dir=self.controls)
                client.report, client.results, client.snapshot = self.report, {}, {}
                client.tools = {tool.name: {"inputSchema": tool.input_schema}
                                for tool in (await public.list_tools()).tools}
                client.episode_identity = None
                client.managed_done = done
                client.calls = Journal()
                client.write = lambda: self.report_path.write_text(json.dumps(self.report), encoding="utf-8")
                client.consumed_control_plans = set()
                client.control_plan_execution_depth = 0
                holder = asyncio.create_task(client.hold(60))
                try:
                    # Reproduce the actual rejected R0001 shape, including fresh_revision=true.
                    query = self.tool_step("failure-exit-query-001", "ck3_query_normal_exit_context_v1")
                    await asyncio.to_thread(self.publish, query)
                    self.assertTrue((await self.wait_row(query["id"]))["ok"])
                    await asyncio.to_thread(self.publish, query, name="same-id-different-name.json", accepted=False)
                    prepare = self.tool_step("prepare-once", "ck3_request_normal_exit_v1",
                        {"action": "prepare_confirmation", "expected_revision": "72",
                         "expected_exit_context_signature": "c" * 64}, fresh=False)
                    await asyncio.to_thread(self.publish, prepare)
                    self.assertTrue((await self.wait_row(prepare["id"]))["ok"])
                    query = self.tool_step("fresh-modal-query", "ck3_query_normal_exit_context_v1")
                    await asyncio.to_thread(self.publish, query)
                    self.assertTrue((await self.wait_row(query["id"]))["ok"])
                    driver.fail_after_confirm = unknown
                    driver.remain_pending = True
                    confirm = self.tool_step("confirm-original-process", "ck3_request_normal_exit_v1",
                        {"action": "confirm_desktop", "expected_revision": "72",
                         "expected_exit_context_signature": "c" * 64}, fresh=False)
                    await asyncio.to_thread(self.publish, confirm)
                    confirmation = await self.wait_row(confirm["id"])
                    self.assertTrue(confirmation["ok"])
                    self.assertNotIn("after_snapshot", confirmation)
                    self.assertIs(confirmation["result"]["retry_authorized"], False)
                    self.assertIs(confirmation["result"]["process_exit_observed"], False)
                    if unknown:
                        self.assertIsNone(confirmation["result"]["native_observation"])
                        self.assertIs(confirmation["result"]["typed_normal_exit_observed"], False)
                    observer = driver._normal_exit_owned_observer_v1
                    self.assertIsNotNone(observer)
                    opens = sum(row[0] == "open" for row in driver.api.calls)
                    sent = len(driver.sent)
                    replay = self.tool_step("different-id-cannot-replay", "ck3_request_normal_exit_v1",
                        {"action": "confirm_desktop", "expected_revision": "73",
                         "expected_exit_context_signature": "d" * 64}, fresh=False)
                    await asyncio.to_thread(self.publish, replay)
                    refused = await self.wait_row(replay["id"])
                    self.assertFalse(refused["ok"])
                    self.assertEqual(len(driver.sent), sent)
                    self.assertIs(driver._normal_exit_owned_observer_v1, observer)
                    observe = self.tool_step("observe-pending-original", "ck3_observe_normal_exit_v1")
                    await asyncio.to_thread(self.publish, observe)
                    pending = await self.wait_row(observe["id"])
                    self.assertTrue(pending["ok"])
                    self.assertNotIn("after_snapshot", pending)
                    self.assertIs(pending["result"]["process_exit_observed"], False)
                    driver.api.wait_result, driver.api.code = 0, 0
                    observe = self.tool_step("observe-completed-original", "ck3_observe_normal_exit_v1")
                    await asyncio.to_thread(self.publish, observe)
                    completed = await self.wait_row(observe["id"])
                    self.assertTrue(completed["ok"])
                    self.assertIs(completed["result"]["process_exit_observed"], True)
                    self.assertIs(completed["result"]["typed_normal_exit_observed"], not unknown)
                    self.assertEqual(sum(row[0] == "open" for row in driver.api.calls), opens)
                    self.assertEqual(len(driver.sent), sent)
                    self.assertIs(service.driver, driver)
                    self.assertIs(client.session, public)
                    # The original managed supervisor supplies cleanup, never the exit ACK.
                    cleanup = cleanup_fixture.FailureShutdownTests().report()
                    cleanup["session"]["report"]["pid"] = 43
                    cleanup["session"]["report"]["shutdown"]["ck3_pid"] = 43
                    self.report.update({key: cleanup[key] for key in
                        ("fixture_only", "pipe", "managed_session_done", "managed_session_thread_finished", "session")})
                    done.set()
                    finish = {"id": "finish-failure-after-real-predicate", "kind": "finish_hold",
                              "failure_shutdown": True, "expect": {"hold_finished": True,
                              "failure_preserved": True, "business_pass": False, "normal_close_qualified": False}}
                    await asyncio.to_thread(self.publish, finish)
                    self.assertTrue((await self.wait_row(finish["id"]))["ok"])
                    await holder
                    self.assertEqual(self.report["error"], self.original["error"])
                    self.assertEqual(self.report["status"], "RED")
                    self.assertEqual(self.report["steps"][0], self.original["steps"][0])
                    self.assertEqual([row["action"] for row in driver.sent],
                                     ["query_context", "prepare_confirmation", "query_context", "confirm_desktop"])
                finally:
                    self.report["hold_finished_by_control_plan"] = True
                    await holder

    def test_real_producer_to_original_service_and_pending_process_observer(self):
        asyncio.run(self.chain(unknown=False))

    def test_unknown_exit_is_not_replayed_under_new_id_revision_or_signature(self):
        asyncio.run(self.chain(unknown=True))

    def test_closed_intent_validation_rejects_unrelated_or_wrong_contract_before_queue(self):
        good = self.tool_step("valid", "ck3_query_normal_exit_context_v1")
        require_failed_host_normal_exit_plan_v1([good])
        for change in ({"tool": "ck3_execute_step"}, {"kind": "raw_step"}, {"continue_on_error": True},
                       {"fresh_revision": 1}, {"arguments": {}}, {"args": {"expected_revision": 72}},
                       {"args": {"expected_revision": True}}, {"args": {"expected_revision": "072"}},
                       {"args": {"expected_revision": None}}, {"args": {"pid": 43}},
                       {"fresh_revision": False}, {"args": {"expected_revision": str(2**64)}}):
            with self.subTest(change=change):
                bad = {**good, **change, "id": "invalid-" + str(len(list(self.controls.iterdir())))}
                self.publish(bad, accepted=False)
        for value in (None, {}, [], [good, good]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_failed_host_normal_exit_plan_v1(value)
        for action in ("prepare_confirmation", "continue_preparation", "disable_exit_autosave", "confirm_desktop"):
            require_failed_host_normal_exit_plan_v1([self.tool_step("fixed-" + action,
                "ck3_request_normal_exit_v1", {"action": action, "expected_revision": str(2**53 + 1),
                "expected_exit_context_signature": "a" * 64}, fresh=False)])

    def test_consumer_independently_rejects_bypassed_business_plan_before_call(self):
        client = actual_host_class()()
        client.report, client.results, client.snapshot = self.report, {}, {}
        client.args = SimpleNamespace(frontend_mod_load_observation=False)
        client.episode_identity = None
        client.write = lambda: None
        async def forbidden(*args, **kwargs):
            raise AssertionError("Failed-host business intent reached its transport")
        client.invoke = forbidden
        with self.assertRaisesRegex(ValueError, "existing typed normal-exit"):
            asyncio.run(client.execute([self.tool_step("bypassed", "ck3_execute_step")]))
        self.assertFalse(self.report["steps"][-1]["ok"])
        self.assertEqual(self.report["error"], self.original["error"])
        with self.assertRaisesRegex(ValueError, "already consumed"):
            asyncio.run(client.execute([self.tool_step("bypassed", "ck3_query_normal_exit_context_v1")]))

    def test_actual_modified_host_admission_scope_is_strict(self):
        from mypy import api
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PlanClient")
        method = next(node for node in original.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "execute")
        loop = next(node for node in method.body if isinstance(node, ast.For))
        duplicate = [node for node in loop.body if isinstance(node, ast.If) and
                     "failed host lifecycle step ID already consumed" in ast.unparse(node)]
        guarded = [node for node in ast.walk(method) if isinstance(node, ast.If) and
                   any(isinstance(child, ast.ImportFrom) and
                       any(alias.name == "require_failed_host_normal_exit_plan_v1" for alias in child.names)
                       for child in node.body)]
        self.assertEqual(len(duplicate), 1)
        self.assertEqual(len(guarded), 1)
        # Check the exact new statements against real typed SDK dependencies.
        # Unchanged historical execute branches stay outside this scoped check.
        unit = ast.parse('''from typing import Protocol, TypedDict
class Report(TypedDict):
    error: object
    steps: list[dict[str, object]]
class Host(Protocol):
    report: Report
def checked(self: Host, steps: list[dict[str, object]], row: dict[str, object],
            kind: object, failure_shutdown: bool) -> None:
    pass
''')
        unit.body[-1].body = [*copy.deepcopy(duplicate), *copy.deepcopy(guarded)]
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC_EXIT_SCOPE_") as temporary:
            path = Path(temporary) / "actual_host_exit_admission_scope.py"
            path.write_text(ast.unparse(ast.fix_missing_locations(unit)), encoding="utf-8")
            stdout, stderr, code = api.run(["--strict", "--follow-imports=silent", "--no-incremental",
                "--cache-dir", str(Path(temporary) / "mypy-cache"), str(path)])
        self.assertEqual(code, 0, stdout + stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
