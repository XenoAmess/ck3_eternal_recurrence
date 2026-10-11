"""Inert-clock tests of the actual host advance entry; no native or process calls."""
import ast
import asyncio
import copy
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

PACKAGE = Path(os.environ.get('XAR_PAUSE_TEST_PACKAGE', str(Path(__file__).resolve().parents[2])))
HOST = Path(os.environ.get('XAR_PAUSE_TEST_HOST', str(PACKAGE / 'native_bridge/research/run_ck3_12002_mcp_live.py')))
spec = importlib.util.spec_from_file_location('pause_base', PACKAGE / 'tests/unit/test_campaign_pause_ready_convergence.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
START = 53144904


def actual_frame(revision, *, date=START, paused=False, mailbox_date=None):
    value = base.frame(revision, paused=paused, ready=paused, consecutive=2 if paused else 0)
    value['played_character']['source'] = 'native'
    value['date_raw'] = date
    value['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['date_raw'] = date if mailbox_date is None else mailbox_date
    return value


def load_host():
    tree = ast.parse(HOST.read_bytes())
    names = {'_campaign_pause_frame_rejection_detail', 'campaign_pause_frame_binding',
             'require_campaign_pause_successor', 'campaign_event_instance',
             '_campaign_pause_pending_ready_successor', '_campaign_pending_running_date'}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'PlanClient')
    methods = [node for node in client.body if isinstance(node, ast.AsyncFunctionDef)
               and node.name in {'pause_campaign_after_advance', 'wait_campaign_running_successor', 'advance_campaign_event_boundary'}]
    if {node.name for node in nodes} != names or len(methods) != 3:
        raise ValueError('Candidate host seams missing')
    nodes.append(ast.ClassDef(name='PlanClient', bases=[], keywords=[], body=methods, decorator_list=[]))
    space = {'copy': copy, 'now': lambda: 'synthetic-time'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(HOST), 'exec'), space)
    return space


class Harness:
    def __init__(self, observations, *, timeout=2.0):
        self.space, self.clock = load_host(), 100.0
        self.observations, self.reads, self.actions = list(observations), 0, []
        self.client = self.space['PlanClient']()
        self.client.args = SimpleNamespace(command_timeout=timeout, poll_interval=0.1)
        self.client.report = {}
        self.client.managed_done = asyncio.Event()
        self.client.tools = {name: {} for name in ('ck3_get_capabilities', 'ck3_take_snapshot',
            'ck3_execute_step', 'ck3_query_current_event_window_context_v1')}
        self.space['time'] = SimpleNamespace(monotonic=lambda: self.clock)
        async def sleep(seconds):
            if seconds < 0:
                raise ValueError('negative wait')
            self.clock += seconds
        self.space['asyncio'] = SimpleNamespace(wait_for=asyncio.wait_for, sleep=sleep)
        async def fresh():
            self.reads += 1
            self.clock += 0.05
            if self.reads == 1:
                return actual_frame(10, paused=True)
            value = self.observations.pop(0) if len(self.observations) > 1 else self.observations[0]
            return copy.deepcopy(value)
        async def invoke(name, arguments, **kwargs):
            self.actions.append(arguments['step'])
            return {'step': arguments['step'], 'accepted': True,
                    'status': 'already_paused' if len(self.actions) == 1 else 'submitted'}
        async def call(name):
            if name != 'ck3_get_capabilities':
                raise ValueError('unexpected tool')
            return {'snapshot': True, 'action_steps': ['pause-map', 'resume-map', 'set-speed-1'],
                    'current_event_window_context_v1_query_supported': True,
                    'bridge_capabilities': ['game.command.query-current-event-window-context-v1']}
        async def wait_snapshot(expected, timeout):
            return actual_frame(10, paused=True)
        async def set_speed(before):
            self.actions.append('set-speed-1')
        self.client.fresh, self.client.invoke, self.client.call = fresh, invoke, call
        self.client.wait_snapshot, self.client.set_campaign_speed_one_presubmission_once = wait_snapshot, set_speed

    async def run(self):
        return await self.client.advance_campaign_event_boundary({'allow_event_boundary': True, 'days': 1})


class RunningDateConvergenceTests(unittest.IsolatedAsyncioTestCase):
    def gap(self, revision=46):
        return actual_frame(revision, mailbox_date=START + 24)

    def success_tail(self):
        return [actual_frame(47, date=START + 24), actual_frame(48, date=START + 24, paused=True)]

    async def test_actual_advance_waits_for_complete_match_without_replaying_actions(self):
        gap = self.gap()
        space = load_host()
        with self.assertRaisesRegex(RuntimeError, 'complete same-owner frame'):
            space['campaign_pause_frame_binding'](gap, allow_running=True)
        original = copy.deepcopy(gap)
        h = Harness([gap, *self.success_tail()])
        result = await h.run()
        self.assertEqual(gap, original)
        self.assertEqual(result['elapsed_hours'], 24)
        self.assertTrue(result['requested_interval_complete'])
        self.assertTrue(result['after']['paused'])
        self.assertEqual(result['running_successor']['native_revision'], 47)
        self.assertEqual(h.actions, ['pause-map', 'set-speed-1', 'resume-map', 'pause-map'])
        evidence = h.client.report['campaign_running_date_readbacks'][0]
        self.assertFalse(evidence['business_credit'])
        self.assertEqual(evidence['original_rejection']['first_failed_condition'], 31)
        self.assertEqual(evidence['status'], 'COMPLETE_ORIGINAL_GUARDS_OBSERVED')

    async def test_no_gap_uses_original_single_running_observation(self):
        h = Harness(self.success_tail())
        result = await h.run()
        self.assertEqual(h.reads, 3)
        self.assertEqual(result['elapsed_hours'], 24)
        self.assertNotIn('campaign_running_date_readbacks', h.client.report)

    async def test_never_converges_within_original_deadline_no_final_pause_or_replay(self):
        h = Harness([self.gap()], timeout=0.3)
        with self.assertRaisesRegex(TimeoutError, 'original command deadline'):
            await h.run()
        self.assertEqual(h.actions, ['pause-map', 'set-speed-1', 'resume-map'])
        self.assertLessEqual(h.clock, 100.35)
        self.assertEqual(h.client.report['campaign_running_date_readbacks'][0]['status'],
                         'FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED')

    async def test_other_predicates_or_nonpositive24_gap_are_not_waitable(self):
        for kind in ('owner', 'stamp', 'event', 'paused', 'backward', 'ahead48', 'incomplete'):
            with self.subTest(kind=kind):
                gap = self.gap()
                mailbox = gap['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']
                if kind == 'owner': mailbox['current_tid'] += 1
                if kind == 'stamp': mailbox['stamp_read_success'] = False
                if kind == 'event': gap['active_event'] = {'instance_id': 101}
                if kind == 'paused': gap['paused'] = True
                if kind == 'backward': mailbox['date_raw'] = START - 24
                if kind == 'ahead48': mailbox['date_raw'] = START + 48
                if kind == 'incomplete': gap['complete_snapshot'] = False
                h = Harness([gap, *self.success_tail()])
                with self.assertRaises(RuntimeError): await h.run()
                self.assertEqual(h.reads, 2)
                self.assertEqual(h.actions, ['pause-map', 'set-speed-1', 'resume-map'])

    async def test_pending_identity_rejections_and_clock_changes_fail_closed(self):
        for key in ('pid', 'generation', 'actor', 'pipe', 'rejections', 'revision', 'native_revision', 'pump', 'date'):
            with self.subTest(key=key):
                gap = self.gap()
                diagnostics = gap['diagnostics']
                mailbox = diagnostics['last_heartbeat']['main_thread_query_mailbox_v1']
                if key == 'pid':
                    diagnostics['bridge_pid'] += 1
                    diagnostics['hello']['pid'] += 1
                    diagnostics['last_heartbeat']['pid'] += 1
                if key == 'generation':
                    diagnostics['connection_generation'] += 1
                    diagnostics['hello']['connection_generation'] += 1
                if key == 'actor': gap['played_character']['character_id'] += 1
                if key == 'pipe': diagnostics['pipe_name'] = 'foreign-connection'
                if key == 'rejections': diagnostics['rejected_state_snapshot_count'] += 1
                if key == 'revision': gap['revision'] = 1
                if key == 'native_revision':
                    gap['native_revision'], gap['snapshot_id'] = 1, 'native:1'
                if key == 'pump': mailbox['owner_verified_pump_epochs'] = 1
                if key == 'date':
                    gap['date_raw'], mailbox['date_raw'] = START - 24, START
                h = Harness([gap, *self.success_tail()])
                with self.assertRaises(RuntimeError): await h.run()
                self.assertEqual(h.reads, 2)

    async def test_later_coherent_pair_cannot_erase_pending_owner_date(self):
        h = Harness([self.gap(), actual_frame(47), *self.success_tail()])
        with self.assertRaisesRegex(RuntimeError, 'complete same-owner frame'):
            await h.run()
        self.assertEqual(h.reads, 3)
        self.assertEqual(h.actions, ['pause-map', 'set-speed-1', 'resume-map'])

    async def test_pending_sequence_nonregression_and_final_rejection_guard_preserved(self):
        for kind in ('pending-revision', 'final-rejections'):
            with self.subTest(kind=kind):
                later = self.gap(45) if kind == 'pending-revision' else actual_frame(47, date=START + 24)
                if kind == 'final-rejections': later['diagnostics']['rejected_state_snapshot_count'] = 1
                h = Harness([self.gap(), later, *self.success_tail()])
                with self.assertRaises(RuntimeError): await h.run()
                self.assertEqual(h.reads, 3)
                self.assertEqual(h.actions, ['pause-map', 'set-speed-1', 'resume-map'])


if __name__ == '__main__':
    unittest.main()
