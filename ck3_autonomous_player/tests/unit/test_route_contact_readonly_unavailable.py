"""Finite route-refusal replay; no process, native transport, or live state.

The packet envelope is reconstructed from a retained failure diagnostic, not
an original complete Native packet or a successful game turn. The available
case tests the existing branch with an isolated normalizer stub.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from xar_autoplayer.bridge import native_driver as native

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/route_contact_typed_unavailable_v1.json').read_text(encoding='utf-8'))
EXPECTED = FIXTURE['body']['result']
STEP = EXPECTED['step']
REQUEST = EXPECTED['readonly_unavailable_evidence']['native_request']
RESPONSE = EXPECTED['readonly_unavailable_evidence']['native_command_result']
TINY = EXPECTED['readonly_unavailable_evidence']['same_frame_readback']['starting_frame']
HOSTILES = native.parse_query_route_contact_horizon_step(STEP)[2]
STARTING = {key: copy.deepcopy(TINY[key]) for key in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id', 'paused', 'map_ready')}
STARTING.update(played_character={'alive': True, 'character_id': TINY['actor_character_id']}, diagnostics={'connection_generation': TINY['connection_generation'], 'bridge_pid': TINY['bridge_pid']}, player_armies=[{'army_id': 318767248, 'controllable': True}], offline_hostiles=HOSTILES)


def rejection(request=None, response=None):
    request = copy.deepcopy(REQUEST if request is None else request)
    response = copy.deepcopy(RESPONSE if response is None else response)
    failure = response.get('typed_query_failure_v1')
    error = response.get('error', '')
    if isinstance(failure, dict):
        error += '; typed_query_failure_v1=' + json.dumps(failure, sort_keys=True, separators=(',', ':'))
    return native._NativeCommandRejectedError(error, native_request_id=REQUEST['request_id'], native_request_frame=request, native_command_result_frame=response)


def production_route():
    source = inspect.getsource(native.NativeHeadlessGameplayDriver._execute_native_war_step)
    start = source.index('        route_contact_query = parse_query_route_contact_horizon_step(step)')
    end = source.index('        preview = parse_preview_move_army_step(step)', start)
    namespace = dict(vars(native))
    namespace['_army_by_id'] = lambda frame, army_id: next((army for army in frame['player_armies'] if army['army_id'] == army_id), None)
    namespace['_route_contact_hostile_ids'] = lambda frame: frame['offline_hostiles']
    exec('def run(self, step, starting, selected_revision):\n' + textwrap.indent(textwrap.dedent(source[start:end]), '    '), namespace)
    return namespace


class FakeDriver:
    def __init__(self, result=None, error=None, current=None):
        self.result = result
        self.error = rejection() if error is None and result is None else error
        self.current = copy.deepcopy(STARTING if current is None else current)
        self.commands = []
        self.reads = 0
        self.records = []

    def _execute_primitive_step(self, *args, **kwargs):
        self.commands.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return copy.deepcopy(self.result)

    def take_internal_semantic_snapshot(self):
        self.reads += 1
        return copy.deepcopy(self.current)

    def _record_command(self, step, **kwargs):
        self.records.append((step, copy.deepcopy(kwargs)))
        return None


class RouteContactReadonlyUnavailableTests(unittest.TestCase):
    def setUp(self):
        self.namespace = production_route()
        self.run_route = self.namespace['run']

    def test_exact_terminal_refusal_returns_unavailable_without_retry(self):
        self.assertTrue(FIXTURE['synthetic_envelope'])
        driver = FakeDriver()
        result = self.run_route(driver, STEP, copy.deepcopy(STARTING), TINY['revision'])
        self.assertEqual(result, EXPECTED)
        self.assertEqual(len(driver.commands), 1)
        self.assertEqual(driver.reads, 1)
        self.assertTrue(driver.commands[0][1]['internal_semantic_snapshot'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['business_submission'])
        self.assertIsNone(result['route_contact_horizon'])

    def test_execute_records_failed_history_but_returns_structured_result(self):
        driver = FakeDriver()
        driver._execute_step_unrecorded = lambda *args, **kwargs: copy.deepcopy(EXPECTED)
        result = native.NativeHeadlessGameplayDriver.execute_step(driver, STEP, expected_revision=TINY['revision'])
        self.assertEqual(result, EXPECTED)
        self.assertEqual(len(driver.records), 1)
        self.assertFalse(driver.records[0][1]['ok'])
        self.assertEqual(driver.records[0][1]['result'], EXPECTED)

    def test_malformed_or_unrelated_terminal_rejections_still_raise(self):
        cases = [
            ('request ID', lambda q, r: q.update(request_id='other')),
            ('business step', lambda q, r: q.update(step='declare-war')),
            ('native revision', lambda q, r: q.update(expected_revision=141)),
            ('response ID', lambda q, r: r.update(request_id='other')),
            ('other error', lambda q, r: r.update(error='state_changed')),
            ('unstable', lambda q, r: r['typed_query_failure_v1'].update(frame_stable=False)),
            ('unfinished', lambda q, r: r['typed_query_failure_v1'].update(executor_finish=False)),
            ('exception', lambda q, r: r['typed_query_failure_v1']['executor_exception'].update(code=0xc0000005)),
            ('missing field', lambda q, r: r['typed_query_failure_v1'].pop('final_equal')),
            ('boolean type', lambda q, r: r['typed_query_failure_v1'].update(typed_result=0)),
            ('wait', lambda q, r: r['typed_query_failure_v1'].update(wait_completed=False)),
        ]
        for name, change in cases:
            with self.subTest(name=name):
                request, response = copy.deepcopy(REQUEST), copy.deepcopy(RESPONSE)
                change(request, response)
                error = rejection(request, response)
                self.assertIsNone(native._route_contact_terminal_unavailable_evidence_v1(error, STEP, TINY['native_revision']))
                driver = FakeDriver(error=error)
                with self.assertRaises(native._NativeCommandRejectedError):
                    self.run_route(driver, STEP, copy.deepcopy(STARTING), TINY['revision'])
                self.assertEqual((len(driver.commands), driver.reads), (1, 0))
        self.assertIsNone(native._route_contact_terminal_unavailable_evidence_v1(RuntimeError('same text'), STEP, TINY['native_revision']))

    def test_changed_frame_or_hostile_scope_cannot_be_normalized(self):
        cases = [
            ('date', lambda v: v.update(date_raw=v['date_raw'] + 24)),
            ('public revision', lambda v: v.update(revision=v['revision'] + 1)),
            ('native revision', lambda v: v.update(native_revision=v['native_revision'] + 1)),
            ('actor', lambda v: v['played_character'].update(character_id=40527)),
            ('PID', lambda v: v['diagnostics'].update(bridge_pid=1)),
            ('generation', lambda v: v['diagnostics'].update(connection_generation=7)),
            ('episode', lambda v: v.update(episode_run_id='other')),
            ('map', lambda v: v.update(map_ready=False)),
            ('alive', lambda v: v['played_character'].update(alive=False)),
            ('hostiles', lambda v: v.update(offline_hostiles=())),
        ]
        for name, change in cases:
            with self.subTest(name=name):
                current = copy.deepcopy(STARTING)
                change(current)
                driver = FakeDriver(current=current)
                with self.assertRaises(native.BridgeUnavailableError):
                    self.run_route(driver, STEP, copy.deepcopy(STARTING), TINY['revision'])
                self.assertEqual((len(driver.commands), driver.reads), (1, 1))

    def test_available_branch_keeps_existing_control_flow(self):
        horizon = {'offline_available_fixture': True}
        self.namespace['normalize_route_contact_horizon'] = lambda value, **kwargs: copy.deepcopy(value)
        result = {'step': STEP, 'accepted': True, 'status': 'available', 'query_sequence': 1, 'snapshot_revision': TINY['native_revision'], 'route_contact_horizon': horizon, 'backend_id': 'native-headless'}
        driver = FakeDriver(result=result)
        actual = self.run_route(driver, STEP, copy.deepcopy(STARTING), TINY['revision'])
        self.assertTrue(actual['accepted'])
        self.assertEqual(actual['route_contact_horizon'], horizon)
        self.assertNotIn('readonly_unavailable_evidence', actual)
        self.assertEqual((len(driver.commands), driver.reads), (1, 1))

    def test_failed_command_is_not_reclassified_as_business_success(self):
        result = self.run_route(FakeDriver(), STEP, copy.deepcopy(STARTING), TINY['revision'])
        for key in ('accepted', 'available', 'business_submission', 'replay_allowed'):
            self.assertIs(result[key], False)
        self.assertEqual(result['status'], 'unavailable')
        self.assertEqual(result['unavailable_reason'], 'native_complete_contact_route_unavailable')
        self.assertEqual(result['readonly_unavailable_evidence']['native_request']['step'], STEP)
        self.assertIs(result['readonly_unavailable_evidence']['native_command_result']['ok'], False)

    def test_service_execute_and_auto_turn_return_observation_without_throwing(self):
        from xar_autoplayer.bridge.service import GameplayBridgeService
        run_route = self.run_route

        class FakeService:
            execute_step = GameplayBridgeService.execute_step
            _execute_planned_turn = GameplayBridgeService._execute_planned_turn
            _execute_planned_turn_without_unhandled_capture = GameplayBridgeService._execute_planned_turn_without_unhandled_capture
            auto_turn = GameplayBridgeService.auto_turn
            _observe_wartime_family_cadence_after_turn_v1 = GameplayBridgeService._observe_wartime_family_cadence_after_turn_v1

            def __init__(self):
                self.driver = FakeDriver()
                self.strategy_state_reads = 0
                self.driver._execute_step_unrecorded = lambda command, **kwargs: run_route(self.driver, command, copy.deepcopy(STARTING), kwargs['expected_revision'])
                self.driver.execute_step = lambda command, **kwargs: native.NativeHeadlessGameplayDriver.execute_step(self.driver, command, **kwargs)
                self._auto_camera_worker = SimpleNamespace(schedule=lambda intent: {'status': 'scheduled'})

            def plan_turn(self):
                return {'snapshot_id': TINY['snapshot_id'], 'revision': TINY['revision'], 'planning_source_frame': copy.deepcopy(FIXTURE['body']['planning_source_frame']), 'plan': copy.deepcopy(FIXTURE['body']['plan'])}

            def _strategy_state_dir(self):
                self.strategy_state_reads += 1
                return None

            def _consume_feast_after_turn(self, outcome): return outcome
            def _consume_sway_after_turn(self, outcome): return outcome
            def _consume_initial_lifestyle_focus_after_turn_v1(self, outcome, **kwargs): return outcome
            def _observe_declaration_cooldown_after_turn_v1(self, *args): return None
            def _observe_family_cooldown_after_turn_v1(self, *args): return None

        service = FakeService()
        result = service.auto_turn()
        self.assertEqual(result['status'], 'executed')  # Handler completed; no gameplay credit.
        self.assertEqual(result['result'], EXPECTED)
        self.assertIsNone(result['family_wartime_opportunity_cooldown_v1'])
        self.assertEqual(result['selected_step'], STEP)
        self.assertEqual(result['planning_source_frame'], FIXTURE['body']['planning_source_frame'])
        self.assertEqual((len(service.driver.commands), service.driver.reads), (1, 1))
        self.assertFalse(service.driver.records[0][1]['ok'])
        self.assertEqual(service.strategy_state_reads, 1)  # Real hook takes its stateless branch.
        self.assertIsNone(result['family_wartime_opportunity_cooldown_v1'])


if __name__ == '__main__':
    unittest.main()
