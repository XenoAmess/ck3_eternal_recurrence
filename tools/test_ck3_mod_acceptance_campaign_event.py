"""Portable explicit campaign event-boundary tests against actual host methods."""
from __future__ import annotations

import asyncio
import ast
import copy
import json
import gc
import warnings
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest

from test_ck3_mod_acceptance_pause import frame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
HOST = ROOT / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"


def campaign_frame(date, *, paused=False, event=None, actor=22, revision=9):
    value = frame(paused=paused, ready=paused, revision=revision)
    value["date_raw"] = date
    value["active_event"] = event
    value["played_character"].update(character_id=actor, source="native")
    value["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] = date
    return value


class CampaignEventTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        cls.definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                           and n.name in {"_campaign_pending_running_date", "_campaign_pause_pending_ready_successor", "_campaign_pause_frame_rejection_detail", "campaign_pause_frame_binding", "require_campaign_pause_successor", "campaign_event_instance"}]
        client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PlanClient")
        cls.definitions.extend(n for n in client.body if isinstance(n, ast.AsyncFunctionDef)
                               and n.name in {"advance", "advance_event_boundary", "advance_campaign_event_boundary", "pause_campaign_after_advance", "wait_campaign_running_successor"})

    def client(self, observations, *, done=False, tick=.1, rejected_step=None, cancel=False):
        before = campaign_frame(100, paused=True, revision=4)
        class FakeIO:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=5, poll_interval=0)
                self.report = {}
                self.tools = {name: {} for name in ("ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step",
                                                     "ck3_query_current_event_window_context_v1")}
                self.episode_identity = None
                self.managed_done = threading.Event()
                if done:
                    self.managed_done.set()
                self.clock = 0.0
                self.calls = []
                self.waits = 0
                self.frames = iter([before] + observations)
                self.snapshot = before

            async def call(self, name):
                self.calls.append((name, {}))
                return {"snapshot": True, "action_steps": ["pause-map", "resume-map", "set-speed-1"],
                        "current_event_window_context_v1_query_supported": True,
                        "bridge_capabilities": ["game.command.query-current-event-window-context-v1"]}

            async def invoke(self, name, arguments, *, fresh_revision=True):
                self.calls.append((name, dict(arguments)))
                return {"step": arguments["step"], "accepted": arguments["step"] != rejected_step, "status": "submitted"}

            async def fresh(self):
                if cancel:
                    raise asyncio.CancelledError()
                self.clock += tick
                self.snapshot = copy.deepcopy(next(self.frames))
                return self.snapshot

            async def wait_snapshot(self, expected, timeout):
                self.waits += 1
                self.snapshot = copy.deepcopy(before)
                return self.snapshot

            async def set_campaign_speed_one_presubmission_once(self, starting):
                self.calls.append(("speed-preflight", {}))

        value = FakeIO()
        namespace = {"asyncio": asyncio, "json": json, "now": lambda: "SYNTHETIC_ONLY",
                     "time": SimpleNamespace(monotonic=lambda: value.clock)}
        definitions = ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[]))
        exec(compile(definitions, str(HOST), "exec"), namespace)
        for name in ("advance", "advance_event_boundary", "advance_campaign_event_boundary", "pause_campaign_after_advance", "wait_campaign_running_successor"):
            setattr(value, name, lambda *args, _name=name, **kwargs: namespace[_name](value, *args, **kwargs))
        value.binding = namespace["campaign_pause_frame_binding"]
        return value

    @staticmethod
    def step(**kwargs):
        return {"days": 1, "timeout": 5, "allow_event_boundary": True, **kwargs}

    async def test_campaign_without_episode_reaches_actual_full_paused_day(self):
        value = self.client([campaign_frame(124), campaign_frame(124, paused=True, revision=10)])
        result = await value.advance_event_boundary(self.step())
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIsNone(result["event_boundary"])
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["after"]["paused"], True)
        self.assertIs(result["actor_transition"]["predecessor_death_proved"], False)
        self.assertEqual([args["step"] for name, args in value.calls if name == "ck3_execute_step"],
                         ["pause-map", "resume-map", "pause-map"])
        self.assertIsNone(value.episode_identity)

    async def test_early_event_never_earns_day_even_if_pause_arrives_at_target(self):
        event = {"instance_id": 7}
        value = self.client([campaign_frame(112, event=event), campaign_frame(124, paused=True, event=event, revision=10)])
        result = await value.advance_event_boundary(self.step())
        self.assertEqual(result["progress_status"], "event_before_target")
        self.assertIs(result["requested_interval_complete"], False)
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertEqual(result["event_boundary"]["date_raw"], 112)
        self.assertEqual(result["selected_event_options"], 0)
        self.assertFalse(any("select" in name for name, _ in value.calls))

    async def test_event_at_target_or_during_pause_retains_actual_full_boundary(self):
        event = {"instance_id": 7}
        for observed in (campaign_frame(124, event=event), campaign_frame(124)):
            with self.subTest(event_before_pause=observed["active_event"] is not None):
                value = self.client([observed, campaign_frame(124, paused=True, event=event, revision=10)])
                result = await value.advance_event_boundary(self.step())
                self.assertIs(result["requested_interval_complete"], True)
                self.assertEqual(result["event_boundary"]["active_event"], event)
                self.assertEqual(result["after"]["active_event"], event)
                self.assertEqual(result["event_resolution"], "typed_query_required")

    async def test_actor_change_is_explicit_once_and_never_death_proof(self):
        frames = [campaign_frame(124, actor=23), campaign_frame(124, paused=True, actor=23, revision=10)]
        value = self.client(frames)
        with self.assertRaisesRegex(RuntimeError, "owner, clock or rejection"):
            await value.advance_event_boundary(self.step())
        value = self.client(frames)
        result = await value.advance_event_boundary(self.step(allow_actor_change=True))
        self.assertEqual(result["actor_transition"], {"allowed": True, "observed": True, "before": 22, "after": 23,
                                                    "predecessor_death_proved": False})
        value = self.client([campaign_frame(112, actor=23), campaign_frame(124, actor=24, revision=10)])
        with self.assertRaises(RuntimeError):
            await value.advance_event_boundary(self.step(allow_actor_change=True))
        for malformed in (1, "true", None):
            value = self.client(frames)
            with self.assertRaises(ValueError):
                await value.advance_event_boundary(self.step(allow_actor_change=malformed))
            self.assertEqual(value.calls, [])

    async def test_malformed_lost_event_owner_or_full_frame_is_rejected(self):
        event = {"instance_id": 7}
        for after_event in (None, {"instance_id": 8}, {"instance_id": True}, {"instance_id": 0}):
            value = self.client([campaign_frame(112, event=event), campaign_frame(112, paused=True, event=after_event, revision=10)])
            with self.subTest(after_event=after_event), self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())
        for field in ("generation", "owner", "ready", "date", "rejection"):
            after = campaign_frame(124, paused=True, revision=10)
            diag = after["diagnostics"]; mailbox = diag["last_heartbeat"]["main_thread_query_mailbox_v1"]
            if field == "generation": diag["hello"]["connection_generation"] = 2
            elif field == "owner": mailbox["owner_tid"] = 34
            elif field == "ready": mailbox["ready"] = False
            elif field == "date": after["date_raw"] = 123
            else: diag["rejected_state_snapshot_count"] = 1
            value = self.client([campaign_frame(124), after])
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())

    async def test_deadline_manager_cancel_and_rejected_ack_do_not_return_success(self):
        value = self.client([], tick=6)
        with self.assertRaises(TimeoutError):
            await value.advance_event_boundary(self.step())
        self.assertFalse(any(name == "ck3_execute_step" for name, _ in value.calls))
        value = self.client([], done=True)
        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter("always", RuntimeWarning)
            with self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())
            gc.collect()
        self.assertEqual(emitted, [], "The done gate must precede coroutine creation")
        self.assertEqual(value.calls, [])
        value = self.client([], cancel=True)
        with self.assertRaises(asyncio.CancelledError):
            await value.advance_event_boundary(self.step())
        for rejected in ("pause-map", "resume-map"):
            value = self.client([], rejected_step=rejected)
            with self.subTest(rejected=rejected), self.assertRaisesRegex(RuntimeError, "unadmitted"):
                await value.advance_event_boundary(self.step())

    async def test_one_life_still_requires_original_episode_and_does_not_dispatch_campaign(self):
        value = self.client([])
        value.snapshot["episode_projection"] = "one_life"
        with self.assertRaisesRegex(ValueError, "episode anchor"):
            await value.advance_event_boundary(self.step())
        self.assertEqual(value.calls, [])

    async def test_default_normal_day_and_default_event_rejection_are_preserved(self):
        value = self.client([campaign_frame(124), campaign_frame(124, paused=True, revision=10)])
        result = await value.advance({"days": 1, "timeout": 5})
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIsNone(result["event_boundary"])
        with self.assertRaises(RuntimeError):
            value.binding(campaign_frame(124, paused=True, event={"instance_id": 7}))




class FlorinCampaignEventTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        unit = ROOT / 'ck3_autonomous_player/tests/unit'
        if str(unit) not in sys.path: sys.path.insert(0, str(unit))
        tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
        client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PlanClient')
        cls.definitions = [n for n in client.body if isinstance(n, ast.AsyncFunctionDef)
            and n.name in {'advance', 'advance_event_boundary', 'advance_campaign_event_boundary'}]

    def client(self, directory, *, event=None, pending=None, starting_pending=None, boundary_date=None, drift_pending=False,
               purpose=None, pre_resume_event=False, speed_readback_event=False,
               terminal='triggered', wrong_generation=False, drop_arm=False, missing=None):
        from test_florin_timeline_control_v1 import ClockDriver, RESOURCES, STATUS
        from test_florin_event_control import frame as actual_cpp_full, FIXTURES
        from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
        has_boundary = event is not None or pending is not None
        ending_date = boundary_date if boundary_date is not None else 24012 if has_boundary else 24024
        early_boundary = has_boundary and ending_date < 24024
        class Transport(ClockDriver):
            def __init__(self):
                super().__init__(directory)
                self.command_timeout_seconds = 5
                self.snapshot.update(speed=2 if speed_readback_event else 1, active_event=None,
                    pending_character_interaction=copy.deepcopy(starting_pending), episode_projection='native_campaign')
                self.resumed = False; self.canceled = False; self.reads_after_resume = 0
                self.snapshot['diagnostics'].update(bridge_pid=42, connection_generation=3)
                self.snapshot['diagnostics']['hello'].update(pid=42, connection_generation=3)
                self.snapshot['diagnostics']['hello']['capabilities'] = [
                    'game.state.snapshot', 'game.query.current-event-options.v1', 'game.command.full-snapshot-clock-control.v1',
                    'game.command.pause-map', 'game.command.resume-map', 'game.command.set-speed-1',
                    'game.command.research-arm-tactical-daily-sentinel-v1-N',
                    'game.command.research-query-tactical-daily-sentinel-v1',
                    'game.command.research-cancel-tactical-daily-sentinel-v1-generation-N']
                producer = NativeHeadlessGameplayDriver(endpoint=SimpleNamespace(start=lambda *_: None), episode_projection='native_campaign')
                hello = copy.deepcopy(actual_cpp_full()['diagnostics']['hello'])
                hello['capabilities'] = list(self.snapshot['diagnostics']['hello']['capabilities'])
                producer.state.ingest(hello)
                producer.state.ingest(json.loads((FIXTURES / 'full1210/full-snapshot-producer-102.json').read_bytes()))
                self.actual_caps = producer.capabilities()

            def capabilities(self): return copy.deepcopy(self.actual_caps)

            def status(self):
                row = json.loads((RESOURCES / 'date-arm1210/armed-generation1.json').read_text())
                status = row['result']['tactical_daily_sentinel']; status['speed'] = 1
                if wrong_generation and not self.resumed: status['generation'] = 2
                if self.resumed:
                    ending = ending_date
                    if self.canceled: status['state'] = 'idle'
                    elif not has_boundary or terminal == 'triggered':
                        status.update(state='triggered', last_observed_date_raw=ending, trigger_date_raw=ending,
                            completed_daily_ticks=0 if early_boundary else 1, overshoot_days=0, pause_observed=True,
                            intermediate_pause_count=1 if early_boundary else 0,
                            trigger_flags=(1 << 13) if early_boundary else 1,
                            trigger_reasons=['native_pause'] if early_boundary else ['date_deadline'],
                            signed_date_delta_from_target_raw=ending-24024, pause_wrapper_called=not early_boundary)
                return status

            def wait_for_command_result(self, request_id, timeout):
                step = self.sent[-1]['step']
                if step.startswith('research-arm-'):
                    row = json.loads((RESOURCES / 'date-arm1210/armed-generation1.json').read_text())
                    row['result']['tactical_daily_sentinel']['speed'] = 1
                elif step == STATUS or step.startswith('research-cancel-'):
                    if step.startswith('research-cancel-'): self.canceled = True
                    row = {'type':'command_result','protocol_version':1,'request_id':request_id,'ok':True,
                        'result':{'step':step,'accepted':True,'status':'available','tactical_daily_sentinel':self.status()}}
                else:
                    row = json.loads((RESOURCES / 'newnative/full-clock1210/full-clock-ack-submitted01.json').read_text())
                    if step == 'resume-map': self.resumed = True
                row['request_id'] = request_id; row['result']['step'] = step
                return row

        driver = Transport()
        if missing == 'query': driver.actual_caps['bridge_capabilities'].remove('game.query.current-event-options.v1')
        elif missing == 'flag': driver.actual_caps['current_event_options_v1210_query_supported'] = False
        elif missing == 'flag_int': driver.actual_caps['current_event_options_v1210_query_supported'] = 1
        elif missing in ('pause-map', 'resume-map', 'set-speed-1'): driver.actual_caps['action_steps'].remove(missing)
        elif missing == 'cancel': driver.actual_caps['bridge_capabilities'].remove('game.command.research-cancel-tactical-daily-sentinel-v1-generation-N')
        elif missing == 'cap_pid': driver.actual_caps['diagnostics']['bridge_pid'] = 43
        elif missing == 'cap_generation': driver.actual_caps['diagnostics']['connection_generation'] = 4
        elif missing == 'sha': driver.snapshot['diagnostics']['hello']['expected_ck3_sha256'] = '0'*64
        class Client:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=5, poll_interval=0)
                self.tools = {name:{} for name in ('ck3_get_capabilities','ck3_take_snapshot','ck3_execute_step','ck3_query_current_event_window_context_v1')}
                self.report = {}; self.snapshot = driver.take_snapshot(); self.episode_identity = None
                self.managed_done = threading.Event(); self.driver = driver

            async def fresh(self):
                if not driver.resumed:
                    if speed_readback_event and any(row['step'] == 'set-speed-1' for row in driver.sent):
                        driver.snapshot.update(speed=1,active_event={'instance_id':42})
                    if pre_resume_event and any(row['step'].startswith('research-arm-') for row in driver.sent):
                        driver.snapshot['active_event'] = {'instance_id':42}
                if driver.resumed:
                    driver.reads_after_resume += 1
                    observed_pending = copy.deepcopy(pending)
                    if drift_pending and driver.reads_after_resume > 1 and observed_pending is not None:
                        observed_pending['sender_character_id'] += 1
                    driver.snapshot.update(date_raw=ending_date,
                        revision=73, native_revision=12, snapshot_id='native:12', active_event=copy.deepcopy(event),
                        pending_character_interaction=observed_pending, paused=True)
                self.snapshot = driver.take_snapshot()
                return self.snapshot

            async def call(self, name): return driver.capabilities()

            async def invoke(self, name, arguments, *, fresh_revision=True):
                step = arguments['step']
                if drop_arm and step.startswith('research-arm-'):
                    # Deliberate inert transport that reports an ARM without
                    # invoking the real primitive must NOT grant resume.
                    return {'step':step,'accepted':True,'status':'available','tactical_daily_sentinel':driver.status()}
                required = ('game.command.research-arm-tactical-daily-sentinel-v1-N' if step.startswith('research-arm-') else
                    'game.command.research-cancel-tactical-daily-sentinel-v1-generation-N' if step.startswith('research-cancel-') else None)
                return driver._execute_primitive_step(step, expected_revision=arguments.get('expected_revision'),
                    required_capability=required, internal_semantic_snapshot=True)

        value = Client()
        namespace = {'asyncio':asyncio, 'time':__import__('time'), 'Path':Path}
        if purpose is not None:
            # Real reviewed-context/prepared/frozen producer and exact Host
            # loader, with temporary authored identity only; no mocked permit.
            from test_product_acceptance_purpose import ProductPurposeTests, pin, write
            import argparse
            import importlib.util
            fixture = ProductPurposeTests()
            fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            product, case = purpose
            fixture.contract.update(product=product,case_id=case)
            fixture.prepared.update(product=product,case=case)
            fixture.frozen.update(mod_key=product,cell=case)
            fixture.context.update(product=product,case=case)
            fixture.refresh_contract()
            write(fixture.frozen_path,fixture.frozen)
            fixture.context['frozen_argv'] = pin(fixture.frozen_path)
            fixture.refresh_context()
            fixture.produce()
            spec = importlib.util.spec_from_file_location('actual_inbox_policy_host',HOST)
            if spec is None or spec.loader is None: raise ValueError('Actual Host loader unavailable')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            namespace['load_product_acceptance_clock_v1'] = module.load_product_acceptance_clock_v1
            value.args = module.parser().parse_args(fixture.frozen['argv'][5:])
            value.args.command_timeout = 5
            value.args.poll_interval = 0
        else:
            # This real loader returns None from the actual unbound args path.
            loader_tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
            loader = next(n for n in loader_tree.body if isinstance(n,ast.FunctionDef)
                          and n.name == 'load_product_acceptance_clock_v1')
            exec(compile(ast.fix_missing_locations(ast.Module(body=[loader],type_ignores=[])),str(HOST),'exec'),
                 {'argparse':__import__('argparse'),'ProductAcceptanceClockV1':object,'Path':Path},namespace)
        exec(compile(ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[])), str(HOST), 'exec'), namespace)
        for name in ('advance','advance_event_boundary','advance_campaign_event_boundary'):
            setattr(value, name, lambda *args,_name=name,**kwargs: namespace[_name](value,*args,**kwargs))
        return value

    @staticmethod
    def step(): return {'days':1,'timeout':5,'allow_event_boundary':True}

    async def test_actual_sdk_arm_status_permit_resume_and_completed_day_are_used(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp))
            result = await value.advance_event_boundary(self.step())
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(steps, ['research-arm-tactical-daily-sentinel-v1-24000-to-24024-speed-1-mode-terminal-a-0',
                'research-query-tactical-daily-sentinel-v1','resume-map','research-query-tactical-daily-sentinel-v1'])
            self.assertTrue(result['requested_interval_complete']); self.assertEqual(result['elapsed_hours'],24)
            self.assertEqual(result['selected_event_options'],0)
            self.assertIsNone(value.driver._florin_date_arm_ready_v1)
            self.assertFalse(result['florin_date_sentinel']['physical_save_confirmed'])

    async def test_early_actual_event_preserved_and_generation_cancel_has_independent_idle_read(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), event={'instance_id':42}, terminal='armed')
            result = await value.advance_event_boundary(self.step())
            self.assertFalse(result['requested_interval_complete']); self.assertEqual(result['elapsed_hours'],12)
            self.assertEqual(result['after']['active_event'], {'instance_id':42})
            self.assertEqual(result['event_resolution'],'typed_query_required'); self.assertEqual(result['selected_event_options'],0)
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(steps.count('resume-map'),1)
            self.assertEqual(steps[-2:], ['research-cancel-tactical-daily-sentinel-v1-generation-1','research-query-tactical-daily-sentinel-v1'])
            self.assertEqual(result['florin_date_sentinel']['stop']['state'],'idle')

    async def test_early_native_pause_terminal_is_not_canceled_or_credited_as_a_day(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), event={'instance_id':42})
            result = await value.advance_event_boundary(self.step())
            self.assertFalse(result['requested_interval_complete']); self.assertEqual(result['elapsed_hours'],12)
            self.assertIsNone(result['florin_date_sentinel']['cancel'])
            self.assertFalse(any(row['step'].startswith('research-cancel-') for row in value.driver.sent))

    async def test_missing_actual_capabilities_or_exact_source_refuses_before_any_clock_send(self):
        import tempfile
        for missing in ('query','flag','flag_int','pause-map','resume-map','set-speed-1','cancel','sha','cap_pid','cap_generation'):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp:
                value = self.client(Path(temp), missing=missing)
                with self.assertRaises(ValueError): await value.advance_event_boundary(self.step())
                self.assertEqual(value.driver.sent,[])

    async def test_forged_host_arm_ack_does_not_create_actual_sdk_resume_permission(self):
        import tempfile
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), drop_arm=True)
            with self.assertRaisesRegex(BridgeUnavailableError, 'qualified bounded Date ARM'):
                await value.advance_event_boundary(self.step())
            self.assertEqual(value.driver.sent,[])

    async def test_generation_drift_rejects_before_resume_and_preserves_original_arm(self):
        import tempfile
        from xar_autoplayer.bridge.driver import BridgeUnavailableError
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), wrong_generation=True)
            with self.assertRaisesRegex(BridgeUnavailableError, 'independent Date status differs'):
                await value.advance_event_boundary(self.step())
            self.assertEqual([row['step'] for row in value.driver.sent],
                ['research-arm-tactical-daily-sentinel-v1-24000-to-24024-speed-1-mode-terminal-a-0','research-query-tactical-daily-sentinel-v1'])


    @staticmethod
    def pending():
        return {'instance_id':33554448, 'sender_character_id':34232,
                'auto_accept_notification':False, 'source':'native'}

    async def test_pending_at_target_returns_actual_boundary_after_real_sdk_terminal_without_replay(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), pending=self.pending(), boundary_date=24024)
            result = await value.advance_event_boundary(self.step())
            self.assertTrue(result['requested_interval_complete'])
            self.assertEqual(result['elapsed_hours'],24)
            self.assertEqual(result['event_boundary']['pending_character_interaction'],self.pending())
            self.assertEqual(result['after']['pending_character_interaction'],self.pending())
            self.assertIsNone(result['after']['active_event'])
            self.assertEqual(result['selected_event_options'],0)
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(sum(step.startswith('research-arm-') for step in steps),1)
            self.assertEqual(steps.count('resume-map'),1)
            self.assertEqual(steps[-1],'research-query-tactical-daily-sentinel-v1')
            self.assertFalse(any('select-event' in step or 'reply' in step for step in steps))
            self.assertEqual(result['florin_date_sentinel']['stop']['trigger_reasons'],['date_deadline'])

    async def test_early_pending_cancels_same_generation_and_never_claims_one_day(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), pending=self.pending(), terminal='armed')
            result = await value.advance_event_boundary(self.step())
            self.assertFalse(result['requested_interval_complete'])
            self.assertEqual(result['elapsed_hours'],12)
            self.assertEqual(result['after']['pending_character_interaction'],self.pending())
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(steps.count('resume-map'),1)
            self.assertEqual(steps[-2:],['research-cancel-tactical-daily-sentinel-v1-generation-1',
                                       'research-query-tactical-daily-sentinel-v1'])
            self.assertEqual(result['florin_date_sentinel']['stop']['state'],'idle')

    async def test_early_pending_native_pause_terminal_is_preserved_without_cancel_or_day_credit(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), pending=self.pending())
            result = await value.advance_event_boundary(self.step())
            self.assertFalse(result['requested_interval_complete'])
            self.assertEqual(result['elapsed_hours'],12)
            self.assertIsNone(result['florin_date_sentinel']['cancel'])
            self.assertFalse(any(row['step'].startswith('research-cancel-') for row in value.driver.sent))

    async def test_pending_sender_drift_at_independent_terminal_read_refuses_without_replay(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp), pending=self.pending(), boundary_date=24024, drift_pending=True)
            with self.assertRaisesRegex(RuntimeError,'notification boundary changed'):
                await value.advance_event_boundary(self.step())
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(steps.count('resume-map'),1)
            self.assertEqual(sum(step.startswith('research-arm-') for step in steps),1)

    async def test_pending_exact_typed_identity_refuses_bool_source_and_wrong_fields(self):
        import tempfile
        for changed in ({'instance_id':True},{'sender_character_id':True},
                        {'auto_accept_notification':1},{'source':'copied'}):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temp:
                pending = {**self.pending(),**changed}
                value = self.client(Path(temp),pending=pending,boundary_date=24024)
                with self.assertRaises(ValueError):
                    await value.advance_event_boundary(self.step())
                self.assertEqual([row['step'] for row in value.driver.sent].count('resume-map'),1)

    async def test_default_florin_day_still_refuses_pending_without_optin_or_reply(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value = self.client(Path(temp),pending=self.pending(),boundary_date=24024)
            with self.assertRaisesRegex(RuntimeError,'pending interaction interrupted'):
                await value.advance({'days':1,'timeout':5})
            steps = [row['step'] for row in value.driver.sent]
            self.assertEqual(steps.count('resume-map'),1)
            self.assertFalse(any('select-event' in step or 'reply' in step for step in steps))



    @staticmethod
    def inbox_step(**kwargs):
        return {'days':1,'timeout':5,'allow_event_boundary':True,
                'pending_interaction_policy':'observe_unanswered_inbox',**kwargs}

    async def test_reviewed_market_cases_can_observe_existing_unanswered_inbox_and_real_completed_day(self):
        import tempfile
        for case in ('market-evolution','delisting-gui'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                pending=self.pending()
                value=self.client(Path(temp),starting_pending=pending,pending=pending,boundary_date=24024,
                                  purpose=('financial-markets',case))
                result=await value.advance_event_boundary(self.inbox_step())
                self.assertTrue(result['requested_interval_complete'])
                self.assertEqual(result['elapsed_hours'],24)
                self.assertIsNone(result['event_boundary'])
                evidence=result['pending_interaction_observation']
                self.assertEqual(evidence['before'],pending);self.assertEqual(evidence['after'],pending)
                self.assertEqual(evidence['changes'],[]);self.assertFalse(evidence['resolved'])
                self.assertFalse(evidence['reply_attempted']);self.assertEqual(evidence['modal_status'],'not_observed')
                steps=[row['step'] for row in value.driver.sent]
                self.assertEqual(steps.count('resume-map'),1)
                self.assertEqual(sum(step.startswith('research-arm-') for step in steps),1)
                self.assertFalse(any('reply' in step or 'select-event' in step for step in steps))

    async def test_observed_inbox_appearance_disappearance_and_sender_change_are_not_resolution(self):
        import tempfile
        pending=self.pending(); changed={**pending,'sender_character_id':34233}
        for before,after,kind in ((None,pending,'appeared'),(pending,None,'disappeared'),(pending,changed,'changed')):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                value=self.client(Path(temp),starting_pending=before,pending=after,boundary_date=24024,
                                  purpose=('financial-markets','market-evolution'))
                result=await value.advance_event_boundary(self.inbox_step())
                evidence=result['pending_interaction_observation']
                self.assertEqual(evidence['before'],before);self.assertEqual(evidence['after'],after)
                self.assertEqual([row['change'] for row in evidence['changes']],[kind])
                self.assertFalse(evidence['resolved']);self.assertTrue(result['requested_interval_complete'])

    async def test_inbox_policy_needs_exact_literal_optin_and_real_reviewed_case(self):
        import tempfile
        trials=[(True,True,None),('unknown',True,None),('observe_unanswered_inbox',False,None),
                ('observe_unanswered_inbox',True,None),('observe_unanswered_inbox',True,('other','market-evolution')),
                ('observe_unanswered_inbox',True,('financial-markets','other'))]
        for policy,event_mode,purpose in trials:
            with self.subTest(policy=policy,event_mode=event_mode,purpose=purpose), tempfile.TemporaryDirectory() as temp:
                value=self.client(Path(temp),purpose=purpose)
                with self.assertRaises(ValueError):
                    await value.advance({'days':1,'timeout':5,'allow_event_boundary':event_mode,'pending_interaction_policy':policy})
                self.assertEqual(value.driver.sent,[])

    async def test_default_policy_still_rejects_starting_inbox_before_any_clock_control(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value=self.client(Path(temp),starting_pending=self.pending())
            with self.assertRaises(ValueError): await value.advance_event_boundary(self.step())
            self.assertEqual(value.driver.sent,[])

    async def test_actual_event_with_observed_inbox_still_returns_the_original_early_event_boundary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value=self.client(Path(temp),starting_pending=self.pending(),pending=self.pending(),event={'instance_id':42},
                              purpose=('financial-markets','market-evolution'))
            result=await value.advance_event_boundary(self.inbox_step())
            self.assertFalse(result['requested_interval_complete']);self.assertEqual(result['elapsed_hours'],12)
            self.assertEqual(result['event_boundary']['active_event'],{'instance_id':42})
            self.assertFalse(result['pending_interaction_observation']['resolved'])
            self.assertEqual([row['step'] for row in value.driver.sent].count('resume-map'),1)

    async def test_event_appearing_in_speed_readback_or_after_arm_never_gets_a_resume(self):
        import tempfile
        for stage in ('speed','armed'):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temp:
                value=self.client(Path(temp),starting_pending=self.pending(),pending=self.pending(),
                    speed_readback_event=stage=='speed',pre_resume_event=stage=='armed',
                    purpose=('financial-markets','market-evolution'))
                with self.assertRaisesRegex(ValueError,'before the sole resume'):
                    await value.advance_event_boundary(self.inbox_step())
                steps=[row['step'] for row in value.driver.sent]
                self.assertNotIn('resume-map',steps)
                self.assertEqual(sum(step.startswith('research-arm-') for step in steps),1 if stage=='armed' else 0)

    async def test_observed_inbox_preserves_signed_native_identity_bits_and_rejects_bad_sentinels(self):
        import tempfile
        for identifier,sender in ((0,0),(-(2**31),-(2**31))):
            with self.subTest(identifier=identifier,sender=sender), tempfile.TemporaryDirectory() as temp:
                pending={**self.pending(),'instance_id':identifier,'sender_character_id':sender}
                value=self.client(Path(temp),starting_pending=pending,pending=pending,boundary_date=24024,
                                  purpose=('financial-markets','market-evolution'))
                result=await value.advance_event_boundary(self.inbox_step())
                self.assertEqual(result['pending_interaction_observation']['after'],pending)
        for fields in ({'instance_id':-1},{'instance_id':True},{'instance_id':2**31},
                       {'sender_character_id':-1},{'sender_character_id':True},{'sender_character_id':2**31},
                       {'auto_accept_notification':1},{'source':'copied'}):
            with self.subTest(fields=fields), tempfile.TemporaryDirectory() as temp:
                value=self.client(Path(temp),starting_pending={**self.pending(),**fields},
                                  purpose=('financial-markets','market-evolution'))
                with self.assertRaises(ValueError): await value.advance_event_boundary(self.inbox_step())
                self.assertEqual(value.driver.sent,[])



    async def test_observed_inbox_that_cannot_advance_still_exhausts_original_deadline_without_replay(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value=self.client(Path(temp),starting_pending=self.pending(),pending=self.pending(),boundary_date=24012,
                              purpose=('financial-markets','market-evolution'))
            with self.assertRaises(TimeoutError):
                await value.advance_event_boundary(self.inbox_step(timeout=0.5))
            steps=[row['step'] for row in value.driver.sent]
            self.assertEqual(steps.count('resume-map'),1)
            self.assertEqual(sum(step.startswith('research-arm-') for step in steps),1)
            self.assertFalse(any('reply' in step or 'select-event' in step for step in steps))



    async def test_public_saved_cli_real_purpose_and_clock_preserve_original_args(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value=self.client(Path(temp),starting_pending=self.pending(),pending=self.pending(),boundary_date=24024,
                              purpose=('financial-markets','market-evolution'))
            self.assertIsInstance(value.args.saved_campaign_save,Path)
            self.assertIs(value.args.saved_campaign_server,False)
            saved=value.args.saved_campaign_save
            result=await value.advance_event_boundary(self.inbox_step())
            self.assertTrue(result['requested_interval_complete'])
            self.assertEqual(result['elapsed_hours'],24)
            self.assertEqual(value.args.saved_campaign_save,saved)
            self.assertIs(value.args.saved_campaign_server,False)
            self.assertIsNone(value.args.frontend_fixture_start_policy)
            self.assertEqual([row['step'] for row in value.driver.sent].count('resume-map'),1)

    async def test_public_cli_without_any_existing_campaign_mode_refuses_before_native_clock(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            value=self.client(Path(temp),purpose=('financial-markets','market-evolution'))
            self.assertIs(value.args.saved_campaign_server,False)
            value.args.saved_campaign_save=None
            with self.assertRaisesRegex(ValueError,'existing campaign startup mode'):
                await value.advance_event_boundary(self.inbox_step())
            self.assertEqual(value.driver.sent,[])

    async def test_public_saved_cli_wrong_allocated_identity_and_unparsed_source_still_refuse(self):
        import tempfile
        for field,changed in (('bridge_pipe','wrong-pipe'),('agent_source_root',ROOT/'not-the-source'),
                              ('saved_campaign_save',True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                value=self.client(Path(temp),purpose=('financial-markets','market-evolution'))
                self.assertIs(value.args.saved_campaign_server,False)
                setattr(value.args,field,changed)
                with self.assertRaises(ValueError):
                    await value.advance_event_boundary(self.inbox_step())
                self.assertIs(value.args.saved_campaign_server,False)
                self.assertEqual(value.driver.sent,[])


if __name__ == "__main__":
    unittest.main()
