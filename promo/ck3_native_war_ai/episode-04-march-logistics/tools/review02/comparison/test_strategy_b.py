"""Synthetic supplied-evidence tests only; no SDK/game/live qualification."""
from copy import deepcopy
import tempfile
import unittest

import r10_compare as c
import strategy_b as b
from test_r10_compare import Fixture


class BFixture:
    def __init__(self, root):
        self.f = Fixture(root)
        self.plan = self.f.plan
        self.arm = deepcopy(self.f.results['arms'][1])
        self.rt = self.arm['runtime']
        cold = self.ep(0, 10, [(1, [1, 2], 10, None)])
        self.arm['cold_start'] = cold
        self.plan['baseline'] = deepcopy(cold)
        self.trace = {'schema': 'xar.e04.r10.strategy-b-events.v1',
                      'plan_sha256': 'd' * 64, 'events': []}
        split = self.ep(0, 11, [(1, [1], 10, None), (2, [2], 10, None)])
        self.action('split', cold, split, 'split-army-half-1')
        m1 = self.ep(0, 12, [(1, [1], 10, 20), (2, [2], 10, None)])
        self.action('move', split, m1, 'move-army-1-to-20', unit_id=1, target_province_id=20)
        m2 = self.ep(0, 13, [(1, [1], 10, 20), (2, [2], 10, 21)])
        self.action('move', m1, m2, 'move-army-2-to-21', unit_id=2, target_province_id=21)
        landed = self.ep(1, 14, [(1, [1], 20, None), (2, [2], 21, None)])
        rested = self.ep(2, 15, [(1, [1], 20, None), (2, [2], 21, None)])
        for aid, site in ((1, 20), (2, 21)):
            self.trace['events'].append({'kind': 'rest-enter', 'endpoint': landed,
                                         'unit_id': aid, 'province_id': site})
        for aid, site in ((1, 20), (2, 21)):
            self.trace['events'].append({'kind': 'rest-exit', 'endpoint': rested,
                                         'unit_id': aid, 'province_id': site, 'reason': 'threshold'})
        meet1 = self.ep(2, 16, [(1, [1], 20, 30), (2, [2], 21, None)])
        self.action('move', rested, meet1, 'move-army-1-to-30', unit_id=1, target_province_id=30)
        meet2 = self.ep(2, 17, [(1, [1], 20, 30), (2, [2], 21, 30)])
        self.action('move', meet1, meet2, 'move-army-2-to-30', unit_id=2, target_province_id=30)
        pre = self.ep(3, 18, [(1, [1], 30, None), (2, [2], 30, None)])
        post = self.ep(3, 19, [(1, [1, 2, 3], 30, None)], commander=11)
        self.action('merge', pre, post, 'merge-armies-1-with-2', destination_army_id=1,
                    source_army_id=2, merge_destination_policy='destination-main',
                    commander_policy='preserve-defined-result')

    def ep(self, day, rev, units, commander=10):
        rs, positions = [], []
        for aid, ids, province, target in units:
            regiments = [{'army_regiment_id': rid, 'current_soldiers': 1 if rid == 3 else 50,
                          'maximum_soldiers': 1 if rid == 3 else 50, 'scale': 1} for rid in ids]
            groups = [{'army_regiment_id': r['army_regiment_id'], 'status': 'available',
                       'ready': True, 'source': 'native_all_data_records', 'native_data_record_count': 1,
                       'records': [{'record_index': 0, 'persistent_regiment_id': r['army_regiment_id'] + 100,
                                    'chunk_index': 0, 'status': 'available',
                                    'current_soldiers': r['current_soldiers'],
                                    'maximum_soldiers': r['maximum_soldiers']}]} for r in regiments]
            native = aid * 100 + 1
            rs.append({'army_id': aid, 'status': 'available', 'native_carmy_id': native,
                       'native_army_resolution_v1': {'status': 'available', 'ready': True,
                                                     'entry_full_id': native},
                       'regiment_count': len(regiments),
                       'current_soldiers': sum(r['current_soldiers'] for r in regiments),
                       'maximum_soldiers': sum(r['maximum_soldiers'] for r in regiments),
                       'regiment_strengths': regiments, 'regiment_replenishment_records_v1': groups,
                       'current_supply_raw': 1000000, 'current_supply_scale': 100000,
                       'current_supply_capacity_raw': 30000000, 'current_supply_capacity_scale': 100000})
            positions.append({'army_id': aid, 'owner_character_id': 7, 'controllable': True,
                              'in_combat': False, 'retreating': False, 'current_province_id': province,
                              'army_state': 'moving' if target is not None else 'regular',
                              'route_province_ids': [target] if target is not None else [],
                              'route_read_status': 'complete_nonempty' if target is not None else 'complete_empty',
                              'move_target_province_id': target})
        snap = {'date_raw': 1000 + day * 24, 'revision': rev, 'native_revision': rev - 1,
                'snapshot_id': 'B:' + str(rev), 'paused': True, 'map_ready': True,
                'played_character': {'character_id': 7, 'alive': True},
                'played_character_gold': {'raw': 25000000, 'scale': 100000},
                'active_wars': [{'war_id': 1, 'player_side': 'attacker'}], 'player_armies': positions,
                'episode_run_id': self.rt['episode'], 'diagnostics': {'bridge_pid': self.rt['pid'],
                'connection_generation': 1, 'hello': {'expected_ck3_version': '1.20.0.4',
                                                     'expected_ck3_sha256': c.EXE}}}
        query = {'accepted': True, 'status': 'available', 'army_strengths': rs,
                 'army_strengths_query_scope': {'army_ids': [p['army_id'] for p in positions],
                                                'published_scope_status': 'available'},
                 'queried_connection_generation': 1}
        for k in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id'):
            query['queried_' + k] = snap[k]
        return {'day': day, 'snapshot': self.f.put('B-snapshot', {'body': snap,
                'machine_id': self.rt['machine_id'], 'is_error': False}),
                'army_result': self.f.put('B-query', query),
                'strategy_army_ids': [p['army_id'] for p in positions],
                'commander': {'source': self.f.put('B-commander', {'id': commander}), 'pointer': '/id'},
                'loaded_features': {'source': self.f.features, 'pointer': '/loaded'}}

    def action(self, kind, before, after, step, **extra):
        f = c.frame(self.f_read(before['snapshot']))
        t = c.frame(self.f_read(after['snapshot']))
        request = {'request_id': 'B-' + str(len(self.trace['events'])), 'tool': 'ck3_execute_step',
                   'arguments': {'step': step, 'expected_revision': f['revision']}}
        body = {'step': step, 'accepted': True, 'status': kind + '_submitted'}
        if kind == 'merge':
            body['war_action'] = {'status': 'merge_applied', 'postcondition_verified': True,
                                 'source_army_id_absent': True, 'destination_army_id': 1,
                                 'source_army_id': 2, 'submitted_public_revision': f['revision'],
                                 'observed_native_revision': t['native_revision']}
            for k in ('date_raw', 'snapshot_id', 'native_revision', 'episode_run_id'):
                body['war_action']['submitted_' + k] = f[k]
            for k in ('date_raw', 'episode_run_id'):
                body['war_action']['observed_' + k] = t[k]
        self.trace['events'].append({'kind': kind, 'before': before, 'after': after,
            'request': self.f.put('B-request', request), 'response': self.f.put('B-response',
            {'request': request, 'body': body, 'is_error': False}), 'outcome': 'applied', **extra})

    def f_read(self, pin):
        return c.parse((self.f.root / pin['path']).read_bytes())

    def check(self):
        return b.audit(self.plan, self.arm, self.trace, c.Evidence(self.f.root), plan_sha256='d' * 64)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.f = BFixture(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_retains_new_one_and_changed_commander_without_live_credit(self):
        out = self.f.check()
        self.assertTrue(out['strategy_b_split_rest_merge_verified'])
        end = out['final_observation']
        self.assertEqual((end['original_cohort_current'], end['all_strategy_current']), (100, 101))
        self.assertEqual(end['commander_id'], 11)
        self.assertEqual(end['extra_regiment_rows'][0]['army_regiment_id'], 3)
        self.assertEqual(len(end['extra_regiment_DATA']), 1)
        self.assertFalse(out['live_execution_performed'])
        self.assertFalse(out['R10_comparison_qualified'])

    def test_recipe_has_absolute_deadline_and_actual_exit_rule(self):
        out = b.recipe(self.f.plan, c.Evidence(self.f.f.root))
        self.assertEqual(out['absolute_deadline_raw'], 3160)
        self.assertEqual(out['role_assignment'], {'main': 20, 'child': 21})
        self.assertFalse(out['site_stock_growth_semantically_qualified'])
        self.assertFalse(out['live_execution_performed'])

    def test_unknown_timeout_preserved_without_retry(self):
        self.f.trace['events'] = self.f.trace['events'][:1]
        event = self.f.trace['events'][0]
        event.update(outcome='unknown', after=None,
                     response=self.f.f.put('timeout', {'is_error': True, 'error': 'timeout'}))
        out = self.f.check()
        self.assertEqual(out['stop']['outcome'], 'unknown')
        self.assertFalse(out['stop']['retry_allowed'])
        self.assertEqual(out['next_operation'], 'diagnose-without-resubmitting')

    def test_failed_action_cannot_be_followed_by_new_request(self):
        self.f.trace['events'][0]['outcome'] = 'rejected'
        with self.assertRaisesRegex(ValueError, 'after failed or unknown'):
            self.f.check()

    def test_ack_without_independent_poststate_rejected(self):
        self.f.trace['events'][0]['after'] = None
        with self.assertRaisesRegex(ValueError, 'ACK without independent'):
            self.f.check()

    def test_public_child_without_actual_resolution_rejected(self):
        ep = self.f.trace['events'][0]['after']
        ep['army_result'] = self.f.f.edit(ep['army_result'], lambda q:
            q['army_strengths'][1]['native_army_resolution_v1'].update(ready=False))
        with self.assertRaisesRegex(ValueError, 'actual CArmy resolution'):
            self.f.check()

    def test_child_cannot_alias_main_actual_army(self):
        ep = self.f.trace['events'][0]['after']
        def change(q):
            q['army_strengths'][1]['native_carmy_id'] = 101
            q['army_strengths'][1]['native_army_resolution_v1']['entry_full_id'] = 101
        ep['army_result'] = self.f.f.edit(ep['army_result'], change)
        with self.assertRaisesRegex(ValueError, 'alias one actual'):
            self.f.check()

    def test_split_cannot_create_extra_one_before_merge(self):
        self.f.trace['events'][0]['after'] = self.f.ep(0, 11, [(1, [1], 10, None), (2, [2, 3], 10, None)])
        with self.assertRaisesRegex(ValueError, 'split changed original'):
            self.f.check()

    def test_cold_save_sha_mismatch_rejected(self):
        self.f.arm['loaded_save_sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'normal save SHA'):
            self.f.check()

    def test_cold_baseline_wallet_drift_rejected(self):
        ep = self.f.arm['cold_start']
        ep['snapshot'] = self.f.f.edit(ep['snapshot'], lambda s:
            s['body']['played_character_gold'].update(raw=9))
        with self.assertRaisesRegex(ValueError, 'cold T0'):
            self.f.check()

    def test_no_unrecorded_movement_to_rest(self):
        del self.f.trace['events'][1:3]
        with self.assertRaisesRegex(ValueError, 'without a previously observed movement'):
            self.f.check()

    def test_threshold_must_be_actual_and_not_getter_prediction(self):
        self.f.plan['strategies']['B']['minimum_stock_raw'] = 2000000
        with self.assertRaisesRegex(ValueError, 'threshold/max-stay'):
            self.f.check()

    def test_maximum_stay_must_reach_frozen_cap(self):
        self.f.trace['events'][5]['reason'] = 'maximum_rest_days'
        with self.assertRaisesRegex(ValueError, 'threshold/max-stay'):
            self.f.check()

    def test_reverse_merge_cannot_echo_policy_to_pass(self):
        self.f.trace['events'][-1].update(destination_army_id=2, source_army_id=1)
        with self.assertRaisesRegex(ValueError, 'direction violates'):
            self.f.check()

    def test_merge_receipt_alone_does_not_prove_source_gone(self):
        event = self.f.trace['events'][-1]
        event['after'] = self.f.ep(3, 19, [(1, [1], 30, None), (2, [2], 30, None)])
        with self.assertRaisesRegex(ValueError, 'merge incomplete'):
            self.f.check()

    def test_merge_may_not_drop_original_regiment(self):
        event = self.f.trace['events'][-1]
        event['after'] = self.f.ep(3, 19, [(1, [1, 3], 30, None)])
        with self.assertRaisesRegex(ValueError, 'original cohort missing'):
            self.f.check()

    def test_stale_expected_revision_rejected(self):
        event = self.f.trace['events'][0]
        event['request'] = self.f.f.edit(event['request'], lambda q:
            q['arguments'].update(expected_revision=1))
        with self.assertRaisesRegex(ValueError, 'fresh public revision'):
            self.f.check()

    def test_scope_is_bounded_to_pinned_plan_bytes(self):
        self.f.trace['plan_sha256'] = 'e' * 64
        with self.assertRaisesRegex(ValueError, 'frozen plan bytes'):
            self.f.check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
