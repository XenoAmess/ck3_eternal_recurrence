"""Portable normal-day result tests using actual host and client methods."""
from __future__ import annotations

import asyncio
import ast
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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


class FlorinHostDayTests(unittest.IsolatedAsyncioTestCase):
    """Real Host advance -> existing Driver reducer -> C++ ACK fixture contract."""
    def host(self, directory, *, speed=5, defect=None):
        sys.path.insert(0,str(ROOT/'ck3_autonomous_player/tests/unit'))
        from test_florin_timeline_control_v1 import ClockDriver
        from test_normal_exit_core1210_v1 import RESOURCES
        tree=ast.parse(HOST.read_text(encoding='utf-8-sig'))
        client=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='PlanClient')
        method=next(node for node in client.body if isinstance(node,ast.AsyncFunctionDef) and node.name=='advance')
        namespace={'asyncio':asyncio,'time':__import__('time'),'json':json,'copy':copy}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(HOST),'exec'),namespace)

        class ActualClockDriver(ClockDriver):
            def __init__(self):
                super().__init__(Path(directory))
                self.snapshot.update(speed=speed,source='injected-dll-named-pipe',backend_id='native-headless',
                    episode_projection='native_campaign',active_event=None,pending_character_interaction=None)
                self.snapshot['played_character']['source']='native'
                self.snapshot['diagnostics']['hello']['connection_generation']=8
                self.resume_requested=False;self.arm_step=None

            def send(self,request,**kwargs):
                super().send(request,**kwargs)
                step=request['step']
                if step=='set-speed-1':
                    self.snapshot.update(speed=1,revision=73,native_revision=12,snapshot_id='native:12')
                if step.startswith('research-arm-tactical-daily-sentinel-v1-'): self.arm_step=step
                if step=='resume-map': self.resume_requested=True

            def take_snapshot(self):
                if self.resume_requested and defect!='timeout':
                    self.snapshot.update(date_raw=24048 if defect=='overshoot' else 24024,
                        revision=74,native_revision=13,snapshot_id='native:13')
                    if defect=='actor': self.snapshot['played_character']['character_id']=123
                    if defect=='event': self.snapshot['active_event']={'instance_id':7}
                return super().take_snapshot()

            def wait_for_command_result(self,request_id,timeout):
                step=self.sent[-1]['step']
                if step.startswith('research-arm-tactical-daily-sentinel-v1-') or step=='research-query-tactical-daily-sentinel-v1':
                    result=json.loads((RESOURCES/'date-arm1210/armed-generation1.json').read_text())
                    result['request_id']=request_id;result['result']['step']=step
                    status=result['result']['tactical_daily_sentinel'];status['speed']=1
                    if self.resume_requested:
                        status.update(state='triggered',last_observed_date_raw=24024,trigger_date_raw=24024,
                            completed_daily_ticks=1,trigger_flags=1,trigger_reasons=['date_deadline'],
                            overshoot_days=0,pause_wrapper_called=True,pause_observed=True)
                        if defect=='generation': status['generation']=2
                    return result
                result=super().wait_for_command_result(request_id,timeout)
                if defect=='resume_unknown' and step=='resume-map':
                    result['ok']=False;result['result'].update(accepted=False,queue_status='indeterminate')
                return result

        driver=ActualClockDriver()
        class ActualHostIO:
            def __init__(self):
                self.args=SimpleNamespace(command_timeout=.08 if defect=='timeout' else 2,poll_interval=.001)
                self.snapshot=driver.take_snapshot();self.report={};self.managed_done=threading.Event();self.calls=[]
            async def fresh(self):
                self.snapshot=driver.take_snapshot();return self.snapshot
            async def invoke(self,name,arguments,*,fresh_revision=True):
                self.calls.append((name,copy.deepcopy(arguments),fresh_revision))
                step=arguments['step'];required=None
                if step.startswith('research-arm-tactical-daily-sentinel-v1-'):
                    required='game.command.research-arm-tactical-daily-sentinel-v1-N'
                elif step=='research-query-tactical-daily-sentinel-v1':
                    required='game.command.research-query-tactical-daily-sentinel-v1'
                return driver._execute_primitive_step(step,expected_revision=arguments.get('expected_revision'),required_capability=required)
        value=ActualHostIO()
        value.advance=lambda row:namespace['advance'](value,row)
        return value,driver

    async def test_real_host_arm_driver_resume_and_target_full_keep_signed_actor(self):
        for speed in (1,5):
            with self.subTest(speed=speed),tempfile.TemporaryDirectory() as directory:
                host,driver=self.host(directory,speed=speed)
                result=await host.advance({'days':1,'timeout':2})
                actions=[row['step'] for row in driver.sent]
                arm='research-arm-tactical-daily-sentinel-v1-24000-to-24024-speed-1-mode-terminal-a-0'
                self.assertEqual(actions,(['set-speed-1'] if speed!=1 else [])+
                    [arm,'research-query-tactical-daily-sentinel-v1','resume-map','research-query-tactical-daily-sentinel-v1'])
                self.assertEqual(result['before']['played_character']['character_id'],-2130706431)
                self.assertEqual(result['after']['played_character']['character_id'],-2130706431)
                self.assertEqual(result['elapsed_hours'],24)
                self.assertIs(result['requested_interval_complete'],True)
                self.assertIs(result['after']['paused'],True)
                self.assertEqual(result['florin_date_sentinel']['stop']['generation'],1)
                self.assertFalse(result['florin_date_sentinel']['physical_save_confirmed'])

    async def test_original_unknown_timeout_boundary_and_foreign_full_never_replay_or_pause(self):
        for defect in ('resume_unknown','timeout','overshoot','actor','event','generation'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as directory:
                host,driver=self.host(directory,speed=1,defect=defect)
                with self.assertRaises((RuntimeError,ValueError,TimeoutError)):
                    await host.advance({'days':1,'timeout':host.args.command_timeout})
                actions=[row['step'] for row in driver.sent]
                self.assertEqual(actions.count('resume-map'),1)
                self.assertNotIn('pause-map',actions)
                self.assertEqual(sum(step.startswith('research-arm-tactical-daily-sentinel-v1-') for step in actions),1)

    async def test_florin_unsupported_days_or_war_scope_reject_before_native_write(self):
        for field in ('days','war','army','actor_transition'):
            with self.subTest(field=field),tempfile.TemporaryDirectory() as directory:
                host,driver=self.host(directory)
                row={'days':2 if field=='days' else 1,'timeout':2}
                if field=='war': driver.snapshot['active_wars']=[{}]
                if field=='army': driver.snapshot['player_armies']=[{}]
                if field=='actor_transition': row['wait_for_played_character_change']=True
                with self.assertRaises(ValueError): await host.advance(row)
                self.assertEqual(driver.sent,[])


if __name__ == "__main__":
    unittest.main()
