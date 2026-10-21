"""Portable normal-day result tests using actual host and client methods."""
from __future__ import annotations

import asyncio
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
from typing import Literal, Protocol, runtime_checkable
import unittest

from test_ck3_mod_acceptance_pause import frame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/src'))
HOST = ROOT / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"
CLIENT = ROOT / "tools/ck3_mod_acceptance_client.py"


DayCall = tuple[list[dict[str, object]], str, float | None, Literal[90]]


@runtime_checkable
class DayResultClient(Protocol):
    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> dict[str, object]: ...


class NormalDayResultTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        cls.definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                           and node.name in {"_campaign_pause_pending_ready_successor", "_campaign_pause_frame_rejection_detail", "campaign_pause_frame_binding", "require_campaign_pause_successor", "campaign_event_instance", "_campaign_pending_running_date"}]
        client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PlanClient")
        cls.definitions.extend(node for node in client.body if isinstance(node, ast.AsyncFunctionDef)
                               and node.name in {"advance", "pause_campaign_after_advance", "wait_campaign_running_successor"})
        spec = importlib.util.spec_from_file_location("day_result_actual_client", CLIENT)
        cls.client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.client_module)

    def host(self, *, campaign=True, during_event=False, after_change=None):
        before = frame(paused=True, ready=True, revision=4)
        reached = frame(revision=9)
        after = frame(paused=True, ready=True, revision=10)
        for value in (before, reached, after):
            value["played_character"]["source"] = "native"
        for value in (reached, after):
            value["date_raw"] = 124
            value["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] = 124
        if during_event:
            reached["active_event"] = {"instance_id": 7}
        if after_change:
            after_change(after)
        if not campaign:
            for value in (before, reached, after):
                value["episode_projection"] = "legacy-projection"
                value["diagnostics"]["hello"]["expected_ck3_version"] = "1.20.0.3"

        class FakeIO:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=5, poll_interval=0)
                self.report = {}
                self.managed_done = threading.Event()
                self.clock = 0.0
                self.calls = []
                self.waits = []
                self.frames = iter((reached, after))

            async def invoke(self, name, arguments, *, fresh_revision=True):
                self.calls.append((name, dict(arguments), fresh_revision))
                return {"step": arguments["step"], "accepted": True, "status": "submitted"}

            async def wait_snapshot(self, expected, timeout):
                self.waits.append((dict(expected), timeout))
                if len(self.waits) == 1:
                    return before
                if len(self.waits) == 2:
                    value = copy.deepcopy(before)
                    value["speed"] = 1
                    return value
                return after

            async def set_campaign_speed_one_presubmission_once(self, starting):
                self.calls.append(("speed-preflight", {}, True))

            async def fresh(self):
                self.clock += .1
                return next(self.frames)

        value = FakeIO()
        namespace = {"asyncio": asyncio, "json": json, "copy": copy, "now": lambda: 'synthetic-test-time',
                     "time": SimpleNamespace(monotonic=lambda: value.clock)}
        module = ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[]))
        exec(compile(module, str(HOST), "exec"), namespace)
        value.pause_campaign_after_advance = lambda starting, **kwargs: namespace["pause_campaign_after_advance"](value, starting, **kwargs)
        value.wait_campaign_running_successor = lambda source, bounded, remaining, **kwargs: namespace["wait_campaign_running_successor"](value, source, bounded, remaining, **kwargs)
        value.advance = lambda row: namespace["advance"](value, row)
        return value

    def client(self, row: dict[str, object]) -> tuple[DayResultClient, list[DayCall]]:
        value: object = self.client_module.CaseClient.__new__(self.client_module.CaseClient)
        setattr(value, "_seq", 0)
        setattr(value, "_binding", None)
        setattr(value, "manifest", {"game": {"version": "1.20.0.4",
            "exe_sha256": frame()["diagnostics"]["hello"]["expected_ck3_sha256"]}})
        calls: list[DayCall] = []

        def held_report(reserve: Literal[90] = 90) -> dict[str, object]:
            # Authored held-session seam: native exact-day is deliberately NOT
            # advertised, so this test continues to consume the old host row.
            if type(reserve) is not int or reserve != 90:
                raise AssertionError("Original guard reserve must remain90")
            return {"phase": "hold", "steps": [], "capabilities": {
                "action_steps": [], "bridge_capabilities": []}}

        def execute(steps: list[dict[str, object]], name: str, timeout: float | None = None,
                    reserve: Literal[90] = 90) -> list[dict[str, object]]:
            if type(reserve) is not int or reserve != 90:
                raise AssertionError("Original execute reserve must remain90")
            calls.append((steps, name, timeout, reserve))
            return [row]
        setattr(value, "guard", held_report)
        setattr(value, "execute_plan", execute)
        if not isinstance(value, DayResultClient):
            raise TypeError("Actual public client lacks the day-result interface")
        return value, calls

    async def test_campaign_success_declares_proven_interval_and_original_client_accepts_raw_row(self):
        host = self.host()
        result = await host.advance({"days": 1, "timeout": 5})
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIn("event_boundary", result)
        self.assertIsNone(result["event_boundary"])
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["after"]["paused"], True)
        row = {"ok": True, "finished_at": "synthetic", "result": result}
        original = copy.deepcopy(row)
        client, calls = self.client(row)
        self.assertEqual(client.advance_day(timeout=5), row)
        self.assertEqual(row, original)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][0]["kind"], "advance_day")
        self.assertNotIn("tool", calls[0][0][0])
        self.assertEqual(calls[0][3], 90)
        self.assertEqual([args["step"] for name, args, _ in host.calls if name == "ck3_execute_step"],
                         ["pause-map", "resume-map", "pause-map"])

    async def test_legacy_normal_shape_stays_unchanged(self):
        host = self.host(campaign=False)
        result = await host.advance({"days": 1, "timeout": 5})
        self.assertEqual(set(result), {"before", "running_successor", "after", "requested_days", "elapsed_hours"})
        self.assertNotIn("requested_interval_complete", result)
        self.assertNotIn("event_boundary", result)
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertNotIn("campaign_pause_readbacks", host.report)

    async def test_event_and_invalid_complete_frame_do_not_produce_success_result(self):
        host = self.host(during_event=True)
        with self.assertRaisesRegex(RuntimeError, "active event interrupted"):
            await host.advance({"days": 1, "timeout": 5})
        changes = [
            lambda after: after.update(active_event={"instance_id": 7}),
            lambda after: after["diagnostics"]["hello"].update(pid=12),
            lambda after: after["played_character"].update(character_id=23),
            lambda after: after["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"].update(ready=False),
            lambda after: after.update(date_raw=99),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                host = self.host(after_change=change)
                with self.assertRaises(RuntimeError):
                    await host.advance({"days": 1, "timeout": 5})
                self.assertEqual(host.report["campaign_pause_readbacks"][0]["status"],
                                 "FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED")


if __name__ == "__main__":
    unittest.main()
