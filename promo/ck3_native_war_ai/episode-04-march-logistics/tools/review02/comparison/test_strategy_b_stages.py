"""Only new B stage composition behavior, with fake Root transport."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import strategy_b_next as next_adapter
from strategy_b_stages import BStages


class Root:
    @staticmethod
    def pin(path):
        p = Path(path); raw = p.read_bytes()
        return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    @classmethod
    def verify_pin(cls, ref):
        if cls.pin(ref['path']) != ref:
            raise RuntimeError('changed pin')
    @staticmethod
    def load(path):
        return json.loads(Path(path).read_text(encoding='utf-8'))
    @classmethod
    def write_new(cls, path, value):
        with Path(path).open('x', encoding='utf-8') as stream:
            json.dump(value, stream)
        return cls.pin(path)
    @staticmethod
    def utc(): return '2026-10-15T18:45:00+00:00'
    @staticmethod
    def same_frame(a, b):
        if a['revision'] != b['revision']:
            raise RuntimeError('frame drift')
    @staticmethod
    def action_gate(frame, caps, step, kind, ids, actor):
        if step not in caps['action_steps']:
            raise RuntimeError('step not advertised')
        return {'advertised': True, 'native_validator_result_before_submission': None}
    @staticmethod
    def validate_frame(frame, binding):
        if frame.get('paused') is not True:
            raise RuntimeError('not paused')
    @staticmethod
    def roster(frame): return {v['army_id']: v for v in frame['player_armies']}


class Inputs:
    def __init__(self, directory):
        self.dir = Path(directory)
        self.plan = {'t0_raw': 1000, 'build': {'source_head': 'a' * 40},
            'goal_province_id': 50, 'strategies': {'B': {'rest_province_ids': [20, 21],
            'minimum_stock_raw': 2000000, 'maximum_deficit': 0, 'maximum_rest_days': 2,
            'merge_province_id': 30, 'merge_destination_policy': 'destination-main'}}}
        p = self.dir / 'plan.json'; p.write_text(json.dumps(self.plan))
        self.live = SimpleNamespace(case=self.dir, run=self.dir, serial=0,
            meta={'machine_id': 'synthetic-only', 'source_head': 'a' * 40},
            binding={'actor': 7}, a=SimpleNamespace(stage='rest', attempt='stage-one'))
        (self.dir / 'requests').mkdir(); (self.dir / 'responses').mkdir()
        self.live.snapshot = lambda name: (deepcopy(self.current['frame']), {'synthetic': True})
        self.commands = []
        def request(name, tool, arguments):
            self.commands.append((tool, arguments))
            return {'body': {'accepted': True, 'step': arguments['step']}}, {'synthetic': True}
        self.live.request = request
        adapter = SimpleNamespace(b=SimpleNamespace(recipe=lambda plan, evidence: None),
            _at=next_adapter._at, _movement_dependency=next_adapter._movement_dependency)
        self.stages = BStages(Root, self.live, adapter, self.plan, plan_pin=Root.pin(p), evidence=None)
        self.stages.state.update(phase='rest', main_id=1, child_id=2)
        self.current = self.packet(1000, [20, 21])
        self.stages.observe = lambda name: deepcopy(self.current)

    def packet(self, date_raw, sites, stock=1000000, deficit=0):
        positions = {aid: {'army_id': aid, 'current_province_id': site, 'army_state': 'regular',
            'route_read_status': 'complete_empty', 'route_province_ids': [], 'move_target_province_id': None}
            for aid, site in zip((1, 2), sites)}
        return {'frame': {'date_raw': date_raw, 'revision': 18, 'native_revision': 17,
                         'snapshot_id': 'synthetic-fresh-meeting'},
            'view': {'positions': positions}, 'rows': {aid: {'maximum_soldiers': 50,
                'current_soldiers': 50-deficit} for aid in (1, 2)},
            'supply': {aid: {'current_supply_raw': stock, 'current_supply_scale': 100000,
                'current_supply_capacity_raw': 30000000, 'current_supply_capacity_scale': 100000} for aid in (1, 2)},
            'packet': {'refs': {'snapshot': {'response': {'synthetic': True}}},
                       'capabilities': {'action_steps': ['merge-armies-1-with-2']}}}

    def result(self, stage='rest'):
        return Root.load(self.stages.run(stage)['path'])


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.i = Inputs(self.temp.name)
    def tearDown(self): self.temp.cleanup()

    def test_both_actual_entries_start_together_before_recovery_wait(self):
        out = self.i.result()
        self.assertEqual(out['status'], 'HOLD_REST_UNTIL_ACTUAL_EXIT')
        self.assertEqual({v['date_raw'] for v in out['rest_entries'].values()}, {1000})
        self.assertEqual(len(out['waiting_armies']), 2)
        self.assertEqual(out['rest_exits'], {})
        self.assertEqual(self.i.commands, [])

    def test_high_stock_does_not_waive_frozen_deficit(self):
        self.i.current = self.i.packet(1000, [20, 21], stock=3000000, deficit=1)
        out = self.i.result()
        self.assertEqual(out['rest_exits'], {})
        self.assertEqual(out['status'], 'HOLD_REST_UNTIL_ACTUAL_EXIT')

    def test_max_stay_exits_while_recovery_remains_false_and_meeting_needs_route(self):
        self.i.stages.state['rest_entries'] = {str(aid): {'province_id': site, 'date_raw': 1000}
            for aid, site in ((1, 20), (2, 21))}
        self.i.current = self.i.packet(1048, [20, 21])
        out = self.i.result()
        self.assertEqual(out['phase'], 'meeting')
        self.assertEqual({v['reason'] for v in out['rest_exits'].values()}, {'maximum_rest_days'})
        self.assertTrue(all(not v['recovery_threshold_observed'] for v in out['rest_exits'].values()))
        self.assertEqual(len(out['dependencies']), 2)
        self.assertIsNone(out['time_advance_request'])

    def test_missing_actual_stock_holds_even_if_a_getter_could_predict_positive(self):
        self.i.current['supply'][1]['current_supply_raw'] = None
        self.i.current['rows'][1]['current_supply_change_monthly_raw'] = 2000000
        out = self.i.result()
        self.assertEqual(out['dependencies'][0]['status'], 'HOLD_ACTUAL_SUPPLY_UNAVAILABLE')
        self.assertEqual(out['dependencies'][0]['required_fields'], ['current_supply_raw'])
        self.assertNotIn('1', out['rest_exits'])
        self.assertEqual(self.i.commands, [])

    def test_merge_uses_fresh_meeting_frame_and_exclusive_claim_after_rest(self):
        self.i.stages.state.update(phase='meeting', rest_exits={'1': {}, '2': {}})
        self.i.current = self.i.packet(1072, [30, 30])
        out = self.i.result('merge-once')
        self.assertEqual(self.i.commands, [('ck3_execute_step',
            {'step': 'merge-armies-1-with-2', 'expected_revision': 18})])
        self.assertEqual(out['status'], 'MERGE_SUBMITTED_AWAIT_INDEPENDENT_POST')
        self.assertFalse(Root.load(self.i.stages.dir / 'merge.once.claim.json')['legality_from_capability'])
        self.i.stages.state['phase'] = 'meeting'; self.i.live.a.attempt = 'second-attempt'
        second = self.i.result('merge-once')
        self.assertTrue(second['status'].startswith('HOLD_'))
        self.assertEqual(len(self.i.commands), 1)
        self.assertFalse(second['action_retry_allowed'])

    def test_rest_overrun_is_retained_as_hold_not_a_new_policy(self):
        self.i.stages.state['rest_entries'] = {str(aid): {'province_id': site, 'date_raw': 1000}
            for aid, site in ((1, 20), (2, 21))}
        self.i.current = self.i.packet(1072, [20, 21])
        out = self.i.result()
        self.assertIn('exceeded frozen maximum', out['reason'])
        self.assertEqual(self.i.plan['strategies']['B']['maximum_rest_days'], 2)
        self.assertEqual(out['rest_exits'], {})

    def test_absolute_horizon_is_not_reset_by_stage_restart(self):
        self.i.current = self.i.packet(1000 + 2160, [20, 21])
        out = self.i.result()
        self.assertEqual(out['status'], 'HOLD_ABSOLUTE_DAY90_USE_COMPARISON_CONSUMER')
        self.assertEqual(self.i.commands, [])

    def test_date_alone_cannot_admit_a_same_S0_baseline(self):
        self.i.stages.state['phase'] = 'uninitialized'
        out = self.i.result('baseline')
        self.assertTrue(out['status'].startswith('HOLD_'))
        self.assertIn('same-S0 admission needs existing actual R10 B arm', out['reason'])
        self.assertEqual(self.i.commands, [])

    def test_supply_hydrates_exact_raw_driver_reference_not_small_R09_projection(self):
        frame = {**self.i.current['frame'], 'paused': True, 'episode_run_id': 'synthetic-only',
            'player_armies': [{'army_id': 1}], 'diagnostics': {'connection_generation': 1}}
        self.i.live.binding['generation'] = 1
        self.i.live.observation = SimpleNamespace(compare_split_merge_cohorts=lambda a, b: {},
            read_bound_current_commander=lambda *a, **kw: 11)
        row = {'army_id': 1, 'native_carmy_id': 101, 'native_army_resolution_v1': {
            'status': 'available', 'ready': True, 'branch': 'resolved', 'entry_full_id': 101},
            'current_supply_raw': 2345678, 'current_supply_scale': 100000,
            'current_supply_capacity_raw': 30000000, 'current_supply_capacity_scale': 100000}
        query = {'accepted': True, 'status': 'available', 'army_strengths': [row],
            'army_strengths_query_scope': {'published_scope_status': 'available', 'army_ids': [1]},
            'queried_connection_generation': 1}
        for key in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id'):
            query['queried_' + key] = frame[key]
        snap = Root.write_new(self.i.dir / 'raw-snapshot.json', {'body': frame})
        raw = Root.write_new(self.i.dir / 'raw-ordinary.json', query)
        commander = Root.write_new(self.i.dir / 'raw-commander.json', {'body': {'synthetic': True}})
        packet = {'frame': frame, 'query': {'army_strengths': [{'army_id': 1}]},
            'refs': {'snapshot': {'response': snap}, 'same_frame_readback': {'response': snap},
                     'strength_raw': raw, 'commanders': {'1': {'response': commander}}}}
        result = self.i.stages.full_packet(packet)
        self.assertEqual(result['supply'][1]['current_supply_raw'], 2345678)
        self.assertEqual(result['assigned_commanders'], {1: 11})
        self.assertEqual(self.i.commands, [])


if __name__ == '__main__': unittest.main(verbosity=2)
