"""Exercise real host failure/report paths with explicitly synthetic IO; no CK3."""
from __future__ import annotations

import argparse
import ast
import asyncio
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

REPO = Path(__file__).resolve().parents[1]
HOST = REPO / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
PATCH = None
ERROR = "campaign pause readback owner, clock or rejection state changed"


def candidate_text():
    text = HOST.read_text(encoding="utf-8-sig")
    if PATCH is None:
        return text
    # Apply only exact unified context in memory. No production file is written.
    lines, out, position = text.splitlines(), [], 0
    patch = PATCH.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(patch):
        match = re.fullmatch(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@.*", patch[index])
        if not match:
            index += 1
            continue
        start = int(match[1]) - 1
        out.extend(lines[position:start])
        position = start
        index += 1
        while index < len(patch) and not patch[index].startswith("@@ "):
            row = patch[index]
            if row[:1] in (" ", "-"):
                if lines[position] != row[1:]:
                    raise ValueError("reviewed patch preimage differs")
                position += 1
            if row[:1] in (" ", "+"):
                out.append(row[1:])
            index += 1
    out.extend(lines[position:])
    return "\n".join(out) + "\n"


class PauseSuccessorDiagnosticTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the existing synthetic frame factory; never execute its tests.
        sys.path.insert(0, str(HOST.parents[3] / "tools"))
        from test_ck3_mod_acceptance_campaign_event import campaign_frame
        cls.frame = staticmethod(campaign_frame)
        tree = ast.parse(candidate_text())
        names = {"_campaign_pause_frame_rejection_detail", "campaign_pause_frame_binding",
                 "require_campaign_pause_successor", "campaign_event_instance", "_campaign_pause_pending_ready_successor"}
        definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PlanClient")
        methods = {"execute", "advance_event_boundary", "advance_campaign_event_boundary",
                   "pause_campaign_after_advance"}
        client.body = [n for n in client.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in methods]
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                                 *definitions, client], type_ignores=[])
        namespace = {"asyncio": asyncio, "time": time, "copy": copy, "json": json,
                     "now": lambda: "SYNTHETIC_TEST_ONLY"}
        exec(compile(ast.fix_missing_locations(module), str(HOST), "exec"), namespace)
        cls.ns = namespace

    def io(self, initial, changed, sink):
        parent = self.ns["PlanClient"]
        class IO(parent):
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=2, poll_interval=0)
                self.report, self.write = {"steps": []}, self.persist
                self.results, self.episode_identity = {}, None
                self.tools = {n: {} for n in ("ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step",
                                              "ck3_query_current_event_window_context_v1")}
                self.snapshot = copy.deepcopy(initial)
                self.calls = []
                self.fresh_count = self.write_count = 0
            def persist(self):
                self.write_count += 1
                sink.write_text(json.dumps(self.report), encoding="utf-8")
            async def fresh(self):
                self.fresh_count += 1
                self.snapshot = copy.deepcopy(initial)
                return self.snapshot
            async def wait_snapshot(self, expected, timeout):
                self.snapshot = copy.deepcopy(changed)
                return self.snapshot
            async def call(self, name):
                self.calls.append(name)
                return {"snapshot": True, "action_steps": ["pause-map", "resume-map", "set-speed-1"],
                        "current_event_window_context_v1_query_supported": True,
                        "bridge_capabilities": ["game.command.query-current-event-window-context-v1"]}
            async def invoke(self, name, arguments, **kwargs):
                self.calls.append(arguments["step"])
                return {"step": "pause-map", "accepted": True, "status": "already_paused"}
        return IO()

    async def test_real_execute_preflight_failure_is_written_with_source_current_and_all_six_conditions(self):
        initial = self.frame(100, paused=True, revision=10)
        initial["diagnostics"]["rejected_state_snapshot_count"] = 1
        for rejected_index in range(6):
            with self.subTest(rejected_condition=rejected_index), tempfile.TemporaryDirectory() as directory:
                changed = copy.deepcopy(initial)
                mailbox = changed["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]
                if rejected_index == 0:
                    changed["played_character"]["character_id"] = 23
                elif rejected_index == 1:
                    changed["diagnostics"]["rejected_state_snapshot_count"] = 2
                elif rejected_index == 2:
                    changed["date_raw"] = mailbox["date_raw"] = 99
                elif rejected_index == 3:
                    changed["revision"] = 9
                elif rejected_index == 4:
                    changed["native_revision"] = 9
                    changed["snapshot_id"] = "native:9"
                else:
                    mailbox["owner_verified_pump_epochs"] = 9
                sink = Path(directory) / "native-report.json"
                client = self.io(initial, changed, sink)
                with self.assertRaisesRegex(RuntimeError, "^" + ERROR + "$"):
                    await client.execute([{"id": "synthetic-day-failure", "kind": "advance_day", "days": 1,
                                           "allow_event_boundary": True, "timeout": 2}])
                report = json.loads(sink.read_text(encoding="utf-8"))
                row = report["steps"][0]
                detail = row["campaign_pause_frame_diagnostic"]
                self.assertFalse(row["ok"])
                self.assertNotIn("result", row)
                self.assertEqual(row["error"], "RuntimeError: " + ERROR)
                self.assertEqual(detail["callsite"], "advance_campaign_event_boundary.preflight")
                self.assertEqual([c["failed"] for c in detail["conditions"]], [i == rejected_index for i in range(6)])
                self.assertEqual(detail["first_failed_condition"], rejected_index)
                self.assertEqual(detail["source_binding"]["rejections"], {"type": "int", "value": 1, "unavailable_reason": None})
                self.assertEqual(detail["current_binding"]["identity"]["actor"]["value"], 23 if rejected_index == 0 else 22)
                self.assertFalse(detail["additional_snapshot_or_RPC_or_retry"])
                self.assertFalse(detail["business_credit"])
                self.assertIsNone(detail["underlying_cause"])
                self.assertEqual(client.fresh_count, 1)
                self.assertEqual(client.calls, ["ck3_get_capabilities", "pause-map"])
                self.assertEqual(client.write_count, 2)
                self.assertIn("finished_at", row)

    async def test_real_postpause_failure_keeps_original_error_and_reaches_execute_writer(self):
        starting = self.frame(100, revision=10)
        changed = self.frame(100, paused=True, revision=11)
        changed["diagnostics"]["rejected_state_snapshot_count"] = 1
        with tempfile.TemporaryDirectory() as directory:
            sink = Path(directory) / "native-report.json"
            client = self.io(starting, changed, sink)
            async def actual_pause(step):
                return await client.pause_campaign_after_advance(starting)
            async def fresh():
                client.fresh_count += 1
                return copy.deepcopy(changed)
            client.advance_event_boundary = actual_pause
            client.fresh = fresh
            with self.assertRaisesRegex(RuntimeError, "^" + ERROR + "$"):
                await client.execute([{"kind": "advance_day", "allow_event_boundary": True}])
            saved = json.loads(sink.read_text(encoding="utf-8"))
            detail = saved["steps"][0]["campaign_pause_frame_diagnostic"]
            self.assertEqual(detail["callsite"], "pause_campaign_after_advance.readback")
            self.assertEqual(detail["first_failed_condition"], 1)
            self.assertEqual(saved["campaign_pause_readbacks"][0]["status"], "FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED")
            self.assertEqual(client.fresh_count, 1)

    def test_success_has_no_diagnostic_and_all_five_production_calls_are_labeled(self):
        frame = self.frame(100, paused=True, revision=10)
        bound = self.ns["campaign_pause_frame_binding"](frame)
        self.assertEqual(self.ns["require_campaign_pause_successor"](bound, frame), bound)
        tree = ast.parse(candidate_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "require_campaign_pause_successor"]
        labels = [next(k.value.value for k in call.keywords if k.arg == "diagnostic_callsite") for call in calls]
        self.assertEqual(set(labels), {"speed_presubmission.full_frame", "pause_campaign_after_advance.readback",
                                      "advance_campaign_event_boundary.preflight", "advance_campaign_event_boundary.readmission",
                                      "advance_campaign_event_boundary.running"})
        self.assertEqual(len(labels), 5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=Path, default=HOST)
    parser.add_argument("--candidate-patch", type=Path)
    options, unittest_args = parser.parse_known_args()
    HOST, PATCH = options.host, options.candidate_patch
    unittest.main(argv=[sys.argv[0], *unittest_args])
