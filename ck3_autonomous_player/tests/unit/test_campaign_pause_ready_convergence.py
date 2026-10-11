"""Pure host seams: pause convergence and failed-plan retention within original deadlines."""
import ast
import asyncio
import copy
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

PACKAGE = Path(__file__).resolve().parents[2]
HOST = Path(os.environ.get('XAR_PAUSE_TEST_HOST', str(PACKAGE / 'native_bridge/research/run_ck3_12002_mcp_live.py')))


def load_host(path):
    tree = ast.parse(path.read_bytes())
    names = {'_campaign_pause_frame_rejection_detail', 'campaign_pause_frame_binding',
             'require_campaign_pause_successor', 'campaign_event_instance', '_campaign_pause_pending_ready_successor'}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PlanClient')
    methods = [n for n in client.body if isinstance(n, ast.AsyncFunctionDef)
               and n.name in {'pause_campaign_after_advance', 'hold'}]
    nodes.append(ast.ClassDef(name='PlanClient', bases=[], keywords=[], body=methods, decorator_list=[]))
    space = {'now': lambda: 'synthetic-test-time'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'), space)
    return space


def frame(revision=10, *, paused=False, ready=False, consecutive=0):
    return {'episode_projection': 'native_campaign', 'backend_id': 'native-headless',
            'source': 'injected-dll-named-pipe', 'map_ready': True, 'format_version': 1,
            'complete_snapshot': True, 'paused': paused, 'played_character': {'character_id': 31254, 'alive': True},
            'active_event': None, 'one_life_terminal_reason': None, 'snapshot_id': f'native:{revision}',
            'native_revision': revision, 'revision': revision + 1, 'date_raw': 53145408, 'local_player_id': 0, 'speed': 1,
            'diagnostics': {'connected': True, 'semantic_state_available': True, 'last_error': None,
            'transport_fatal_error': None, 'bridge_pid': 16408, 'connection_generation': 1,
            'rejected_state_snapshot_count': 0, 'pipe_name': 'synthetic-same-owner-only',
            'hello': {'expected_ck3_version': '1.20.0.4',
                'expected_ck3_sha256': '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518',
                'game_adapter_id': 'ck3-1.20.0.4-msvc-x64', 'ck3_build_match': True, 'connection_generation': 1, 'pid': 16408},
            'last_heartbeat': {'pid': 16408, 'main_thread_query_mailbox_v1': {
                'owner_tid': 1964, 'current_tid': 1964, 'owner_verified_pump_epochs': revision,
                'installed': True, 'ready': ready, 'stop': False, 'failure': 0, 'stamp_read_success': True,
                'date_raw': 53145408, 'application_main_observed': True, 'paused': paused,
                'paused_main_thread_observed': ready, 'consecutive_verified': consecutive}}}}


class Harness:
    def __init__(self, frames, *, timeout=2.0, fresh_cost=0.05):
        self.space = load_host(HOST)
        self.clock = 100.0
        self.fresh_cost = fresh_cost
        self.frames = list(frames)
        self.fresh_count = 0
        self.mutations = []
        self.sleep_values = []
        self.space['time'] = SimpleNamespace(monotonic=lambda: self.clock)
        async def sleep(seconds):
            if seconds < 0:
                raise RuntimeError('negative sleep')
            self.sleep_values.append(seconds)
            self.clock += seconds
        self.space['asyncio'] = SimpleNamespace(wait_for=asyncio.wait_for, sleep=sleep)
        self.client = self.space['PlanClient']()
        self.client.args = SimpleNamespace(command_timeout=timeout, poll_interval=0.1)
        self.client.report = {}
        self.client.managed_done = asyncio.Event()
        async def invoke(name, arguments, *, fresh_revision=True):
            self.mutations.append((name, copy.deepcopy(arguments)))
            return {'step': 'pause-map', 'accepted': True, 'status': 'submitted'}
        async def fresh():
            self.fresh_count += 1
            self.clock += self.fresh_cost
            if len(self.frames) > 1:
                return copy.deepcopy(self.frames.pop(0))
            return copy.deepcopy(self.frames[0])
        self.client.invoke, self.client.fresh = invoke, fresh

    async def run(self, **kwargs):
        return await self.client.pause_campaign_after_advance(frame(), **kwargs)


class PauseReadyConvergenceTests(unittest.IsolatedAsyncioTestCase):
    def assert_one_pause(self, h):
        self.assertEqual(h.mutations, [('ck3_execute_step', {'step': 'pause-map'})])

    async def test_hold_retains_diagnosed_failed_plan_only_until_original_deadline(self):
        space = load_host(HOST)
        rejected = frame(11, paused=True)
        with self.assertRaises(RuntimeError) as actual_rejection:
            space['campaign_pause_frame_binding'](rejected)
        matching = actual_rejection.exception
        wrong_text = RuntimeError('unrelated command failure')
        wrong_text.ck3_campaign_pause_frame_diagnostic = copy.deepcopy(matching.ck3_campaign_pause_frame_diagnostic)
        wrong_schema = RuntimeError(str(matching))
        wrong_schema.ck3_campaign_pause_frame_diagnostic = {'schema': 'unrelated-diagnostic'}
        missing_diagnostic = RuntimeError(str(matching))
        wrong_type = ValueError(str(matching))
        wrong_type.ck3_campaign_pause_frame_diagnostic = copy.deepcopy(matching.ck3_campaign_pause_frame_diagnostic)

        class PlanPath:
            def __str__(self):
                return 'inert-control-plan.json'

            def stat(self):
                return SimpleNamespace(st_mtime_ns=1)

        for error in (matching, wrong_text, wrong_schema, missing_diagnostic, wrong_type):
            with self.subTest(error_type=type(error).__name__, error=str(error),
                              diagnostic=getattr(error, 'ck3_campaign_pause_frame_diagnostic', None)):
                clock = [100.0]
                path = PlanPath()
                loads, mutations, sleeps = [], [], []
                client = space['PlanClient']()
                client.report = {'error': None, 'steps': []}
                client.managed_done = asyncio.Event()
                client.control_plan_execution_depth = 0
                client.consumed_control_plans = set()
                client.args = SimpleNamespace(control_plan_dir=SimpleNamespace(glob=lambda pattern: [path]))
                client.write = lambda: None

                def load_plan(actual):
                    self.assertIs(actual, path)
                    loads.append(actual)
                    return [{'id': 'one-advance-then-pause'}]

                async def execute(plan):
                    mutations.extend(['advance', 'pause'])
                    clock[0] += 0.125
                    client.report['steps'].append({'id': plan[0]['id'], 'ok': False, 'error': str(error)})
                    raise error

                async def sleep(seconds):
                    # Reaching the existing hold loop proves the exception did
                    # not escape to the host's stop/managed-session cleanup.
                    self.assertFalse(client.managed_done.is_set())
                    self.assertEqual(client.control_plan_execution_depth, 0)
                    self.assertEqual(mutations, ['advance', 'pause'])
                    self.assertFalse(client.report['steps'][0]['ok'])
                    sleeps.append(seconds)
                    clock[0] += seconds

                client.execute = execute
                space.update(time=SimpleNamespace(monotonic=lambda: clock[0], time=lambda: 2000.0),
                             asyncio=SimpleNamespace(sleep=sleep), copy=copy, load_plan=load_plan)
                if error is matching:
                    await client.hold(1.0)
                    self.assertEqual(clock[0], 101.0)
                    self.assertAlmostEqual(sum(sleeps), 0.875)
                    self.assertEqual(client.report['hold_until_utc_estimated'], 2001.0)
                    self.assertEqual(client.report['error'], f'RuntimeError: {matching}')
                    retained = client.report['control_plan_pause_readback_failures']
                    self.assertEqual(len(retained), 1)
                    self.assertEqual(retained[0]['diagnostic'], matching.ck3_campaign_pause_frame_diagnostic)
                    self.assertFalse(retained[0]['business_pass'])
                    self.assertFalse(retained[0]['normal_close_qualified'])
                else:
                    with self.assertRaises(type(error)) as caught:
                        await client.hold(1.0)
                    self.assertIs(caught.exception, error)
                    self.assertEqual(clock[0], 100.125)
                    self.assertEqual(sleeps, [])
                    self.assertNotIn('control_plan_pause_readback_failures', client.report)
                self.assertEqual(len(loads), 1)
                self.assertEqual(mutations, ['advance', 'pause'])
                self.assertEqual(client.consumed_control_plans, {(str(path), 1)})
                self.assertEqual(client.control_plan_execution_depth, 0)
                self.assertFalse(client.managed_done.is_set())

    async def test_pending_paused_frame_requires_later_original_ready_guard(self):
        pending = frame(11, paused=True, consecutive=1)
        h = Harness([pending, frame(12, paused=True, ready=True, consecutive=2)])
        with self.assertRaises(RuntimeError):
            h.space['campaign_pause_frame_binding'](pending)
        actual = await h.run()
        self.assertTrue(actual['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['ready'])
        self.assertEqual(h.fresh_count, 2)
        self.assert_one_pause(h)
        evidence = h.client.report['campaign_pause_readbacks'][0]
        self.assertEqual(evidence['status'], 'FULL_PAUSED_FRAME_OBSERVED')
        self.assertFalse(evidence['pending_owner_stamp_readbacks'][0]['business_credit'])

    async def test_zero_then_one_pump_remain_unqualified_until_ready(self):
        h = Harness([frame(11, paused=True), frame(12, paused=True, consecutive=1),
                     frame(13, paused=True, ready=True, consecutive=2)])
        actual = await h.run()
        self.assertEqual(actual['native_revision'], 13)
        self.assertEqual(len(h.client.report['campaign_pause_readbacks'][0]['pending_owner_stamp_readbacks']), 2)
        self.assert_one_pause(h)

    async def test_never_ready_exhausts_original_deadline_without_mutation_retry(self):
        h = Harness([frame(11, paused=True, consecutive=1)], timeout=0.3)
        with self.assertRaisesRegex(TimeoutError, 'original command deadline'):
            await h.run()
        self.assert_one_pause(h)
        self.assertEqual(h.client.report['campaign_pause_readbacks'][0]['status'], 'FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED')
        self.assertLessEqual(h.clock, 100.35)

    async def test_other_guard_failure_immediately_preserves_original_error(self):
        pending = frame(11, paused=True, consecutive=1)
        pending['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['current_tid'] = 1965
        h = Harness([pending, frame(12, paused=True, ready=True, consecutive=2)])
        with self.assertRaisesRegex(RuntimeError, 'complete same-owner frame') as caught:
            await h.run()
        self.assertIsInstance(caught.exception.ck3_campaign_pause_frame_diagnostic, dict)
        self.assertEqual(h.fresh_count, 1)
        self.assert_one_pause(h)

    async def test_owner_identity_and_clock_changes_are_not_waitable(self):
        paths = [('diagnostics', 'bridge_pid'), ('diagnostics', 'connection_generation'),
                 ('diagnostics', 'pipe_name'), ('played_character', 'character_id'),
                 ('diagnostics', 'rejected_state_snapshot_count'), ('date_raw',), ('revision',),
                 ('native_revision',), ('diagnostics', 'last_heartbeat', 'main_thread_query_mailbox_v1', 'owner_verified_pump_epochs')]
        for path in paths:
            with self.subTest(path=path):
                pending = frame(11, paused=True, consecutive=1)
                node = pending
                for key in path[:-1]: node = node[key]
                value = node[path[-1]]
                node[path[-1]] = 'foreign-pipe' if isinstance(value, str) else (1 if path[-1] in {'revision', 'native_revision', 'owner_verified_pump_epochs'} else value + 1)
                if path[-1] == 'date_raw':
                    node[path[-1]] = 53145384
                    pending['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['date_raw'] = 53145384
                h = Harness([pending, frame(12, paused=True, ready=True, consecutive=2)])
                with self.assertRaises(RuntimeError): await h.run()
                self.assertEqual(h.fresh_count, 1)
                self.assert_one_pause(h)

    async def test_pending_sequence_cannot_regress_after_first_read(self):
        a, b = frame(12, paused=True, consecutive=1), frame(11, paused=True, consecutive=1)
        h = Harness([a, b, frame(13, paused=True, ready=True, consecutive=2)])
        with self.assertRaises(RuntimeError): await h.run()
        self.assertEqual(h.fresh_count, 2)
        self.assert_one_pause(h)

    async def test_ready_false_with_two_pumps_or_bad_stamp_is_not_transition(self):
        for change in ('two-pumps', 'stamp-paused', 'application-main', 'generation'):
            with self.subTest(change=change):
                pending = frame(11, paused=True, consecutive=1)
                m = pending['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']
                if change == 'two-pumps': m['consecutive_verified'] = 2
                if change == 'stamp-paused': m['paused'] = False
                if change == 'application-main': m['application_main_observed'] = False
                if change == 'generation': pending['diagnostics']['hello']['connection_generation'] = 2
                h = Harness([pending, frame(12, paused=True, ready=True, consecutive=2)])
                with self.assertRaises(RuntimeError): await h.run()
                self.assertEqual(h.fresh_count, 1)
                self.assert_one_pause(h)

    async def test_active_event_is_not_silently_admitted(self):
        pending = frame(11, paused=True, consecutive=1)
        pending['active_event'] = {'instance_id': 7}
        h = Harness([pending])
        with self.assertRaises(RuntimeError): await h.run()
        self.assert_one_pause(h)

    async def test_existing_running_to_paused_transition_still_succeeds(self):
        transition = frame(11)
        transition['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['paused'] = True
        h = Harness([transition, frame(12, paused=True, ready=True, consecutive=2)])
        actual = await h.run()
        self.assertTrue(actual['paused'])
        self.assert_one_pause(h)

    async def test_explicit_original_command_deadline_is_not_reset(self):
        h = Harness([frame(11, paused=True, consecutive=1)], timeout=2)
        with self.assertRaisesRegex(TimeoutError, 'original command deadline'):
            await h.run(command_deadline=100.2)
        self.assertLessEqual(h.clock, 100.25)
        self.assert_one_pause(h)

    async def test_managed_session_end_is_not_waited_through(self):
        h = Harness([frame(11, paused=True, consecutive=1)])
        original_fresh = h.client.fresh
        async def ended():
            value = await original_fresh()
            h.client.managed_done.set()
            return value
        h.client.fresh = ended
        with self.assertRaisesRegex(RuntimeError, 'managed session finished'):
            await h.run()
        self.assert_one_pause(h)


if __name__ == '__main__':
    unittest.main()
