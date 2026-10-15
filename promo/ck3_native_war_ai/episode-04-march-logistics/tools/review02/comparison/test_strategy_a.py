"""Synthetic offline A decision/state checks; never evidence of gameplay."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import r10_compare as c
from test_r10_compare import Fixture
import strategy_a as a


class StrategyATests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name); self.e = c.Evidence(self.temp.name)
        self.arm = self.f.results['arms'][0]
        for ep in (self.f.plan['baseline'], self.arm['cold_start']):
            ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(controllable=True))
        self.f.plan['strategies']['A']['route_preview'] = self.preview(self.f.plan['baseline'])
        self.fresh = self.preview(self.arm['cold_start'])

    def preview(self, ep):
        s = c.body(self.e.json(ep['snapshot'])); p = s['player_armies'][0]
        return self.f.put('synthetic-preview', {
            'step': f'preview-move-army-{p["army_id"]}-to-30', 'accepted': True, 'status': 'available',
            **{'queried_'+k: s[k] for k in ('snapshot_id', 'revision', 'native_revision', 'episode_run_id')},
            'queried_connection_generation': s['diagnostics']['connection_generation'],
            'route_preview': {'status': 'available', 'army_id': p['army_id'],
                              'origin_province_id': p['current_province_id'], 'target_province_id': 30,
                              'route_province_ids': [30], 'previewed_date_raw': s['date_raw']}})

    def admit(self):
        return a.admit(self.f.plan, self.arm['runtime'], self.arm['loaded_save_sha256'],
                       self.arm['cold_start'], self.fresh, self.e)

    def moving(self):
        state = self.admit(); after = deepcopy(self.arm['cold_start'])
        def edit(x):
            s = x['body']; s.update(snapshot_id='A:post-move', revision=11, native_revision=10)
            s['player_armies'][0].update(army_state='moving', route_province_ids=[30],
                                       route_read_status='complete_nonempty', move_target_province_id=30)
        after['snapshot'] = self.f.edit(after['snapshot'], edit)
        after['army_result'] = self.f.edit(after['army_result'], lambda x: x.update(
            queried_snapshot_id='A:post-move', queried_revision=11, queried_native_revision=10))
        return a.observe_move(state, after, self.e)

    def update(self, state, index):
        return a.update(state, self.arm['days'][index], self.arm['observations'][index], self.e)

    def test_independent_A_unknown_B_C_fees_do_not_block_action(self):
        self.f.plan['strategies']['B'] = None; self.f.plan['strategies']['C'] = None
        self.f.plan['prerequisites'] = {'maintenance_settlement': None}; self.f.plan['compare_fees'] = True
        s = self.admit()
        self.assertEqual(s['proposed_call'], {'tool': 'ck3_move_army', 'arguments': {
            'army_id': 1, 'target_province_id': 30, 'expected_revision': 10}})
        self.assertFalse(s['live_execution_performed']); self.assertFalse(s['research_card_closed'])

    def test_UNBOUND_template_is_rejected(self):
        p = c.parse(Path(__file__).with_name('PLAN.template.UNBOUND.json').read_bytes())
        with self.assertRaisesRegex(ValueError, 'UNBOUND'):
            a.admit(p, self.arm['runtime'], None, self.arm['cold_start'], self.fresh, self.e)

    def test_stale_preview_frame_episode_generation_and_target_rejected(self):
        original = self.fresh
        for key, value in [('queried_native_revision', 123), ('queried_episode_run_id', 'old'),
                           ('queried_connection_generation', 9)]:
            with self.subTest(key=key):
                self.fresh = self.f.edit(original, lambda x: x.update({key: value}))
                with self.assertRaisesRegex(ValueError, 'preview.*differs'): self.admit()
        self.fresh = self.f.edit(original, lambda x: x['route_preview'].update(target_province_id=999))
        with self.assertRaisesRegex(ValueError, 'target/date'): self.admit()

    def test_checkpoint_and_runtime_source_binding_required(self):
        self.arm['loaded_save_sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'checkpoint'): self.admit()
        self.arm['loaded_save_sha256'] = 'c'*64; self.arm['runtime']['source_head'] = 'f'*40
        with self.assertRaisesRegex(ValueError, 'source/DLL'): self.admit()

    def test_explicit_full_scope_and_complete_DATA_required(self):
        ep = self.arm['cold_start']; original = ep['army_result']
        ep['army_result'] = self.f.edit(original, lambda x: x.pop('army_strengths_query_scope'))
        with self.assertRaisesRegex(ValueError, 'explicit complete'): self.admit()
        ep['army_result'] = self.f.edit(original, lambda x: x['army_strengths'][0].update(regiment_replenishment_records_v1=[]))
        with self.assertRaisesRegex(ValueError, 'DATA'): self.admit()

    def test_all_T0_regiments_are_original_cohort(self):
        self.f.plan['original_regiment_ids'] = [1]
        with self.assertRaisesRegex(ValueError, 'entire T0 Army'): self.admit()

    def test_ArRg_ID_is_not_mistaken_for_signed_public_CUnit(self):
        full_id = 2**31+7
        self.f.plan['original_regiment_ids'] = [full_id, 2]
        def replace(x):
            row = x['army_strengths'][0]
            row['regiment_strengths'][0]['army_regiment_id'] = full_id
            row['regiment_replenishment_records_v1'][0]['army_regiment_id'] = full_id
        for ep in (self.f.plan['baseline'], self.arm['cold_start']):
            ep['army_result'] = self.f.edit(ep['army_result'], replace)
        self.assertEqual(self.admit()['actual']['cohort_current'], 100)

    def test_ACK_is_not_move_postcondition(self):
        with self.assertRaisesRegex(ValueError, 'ACK'):
            self.update(self.admit(), 0)

    def test_independent_post_state_and_actual_first_day_bracket(self):
        s = self.moving(); self.assertIsNone(s['proposed_call'])
        s = self.update(s, 0); self.assertIsNone(a.report(s)['disposition'])
        s = self.update(s, 1); r = a.report(s)
        self.assertEqual(r['arrival_interval_days'], [1, 2])
        self.assertEqual(r['arrival_actual']['date_raw'], 1048)
        self.assertEqual([x['day'] for x in r['report_date_endpoints']], [1])
        self.assertIsNone(r['joint_common_date_rows']); self.assertIsNone(r['D90_endpoint'])
        self.assertIsNone(r['actual_fees']); self.assertIsNone(r['winner'])

    def test_route_target_mismatch_is_not_actual_Move(self):
        s = self.admit()
        with self.assertRaisesRegex(ValueError, 'independent Move'):
            a.observe_move(s, self.arm['cold_start'], self.e)

    def test_clock_overshoot_and_reset_rejected_without_mutating_state(self):
        s = self.moving(); day = deepcopy(self.arm['days'][0])
        day['clock_source'] = self.f.edit(day['clock_source'], lambda x: x['clock'].update(overshoot_days=1))
        with self.assertRaisesRegex(ValueError, 'overshoot'):
            a.update(s, day, self.arm['observations'][0], self.e)
        self.assertEqual(len(s['days']), 0)
        with self.assertRaisesRegex(ValueError, 'days missing'):
            self.update(s, 1)

    def test_army_scope_change_cannot_be_hidden_as_loss(self):
        s = self.moving(); ep = deepcopy(self.arm['observations'][0]); ep['strategy_army_ids'] = [1, 2]
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            a.update(s, self.arm['days'][0], ep, self.e)

    def test_unknown_original_regiment_is_never_zero(self):
        s = self.moving(); ep = self.arm['observations'][0]
        def edit(x):
            row = x['army_strengths'][0]
            row['regiment_strengths'] = row['regiment_strengths'][1:]
            row['regiment_replenishment_records_v1'] = row['regiment_replenishment_records_v1'][1:]
            row.update(regiment_count=1, current_soldiers=50, maximum_soldiers=50)
        ep['army_result'] = self.f.edit(ep['army_result'], edit)
        with self.assertRaisesRegex(ValueError, 'original cohort missing'):
            self.update(s, 0)

    def test_early_stop_is_not_D90_censor(self):
        s = self.moving(); ep = self.arm['observations'][0]
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(
            army_state='regular', route_province_ids=[], route_read_status='complete_empty', move_target_province_id=None))
        self.arm['days'][0]['paused_snapshot'] = ep['snapshot']
        r = a.report(self.update(s, 0))
        self.assertIsNone(r['disposition']); self.assertEqual(r['action_status'], 'needs_current_state_decision')
        self.assertIsNone(r['arrival_actual'])

    def test_arrival_is_not_allowed_to_silently_continue(self):
        s = self.update(self.update(self.moving(), 0), 1)
        day = deepcopy(self.arm['days'][1]); day['day'] = 3
        ep = deepcopy(self.arm['observations'][1]); ep['day'] = 3
        with self.assertRaisesRegex(ValueError, 'unregistered post-arrival'):
            a.update(s, day, ep, self.e)

    def test_duplicate_route_label_is_rejected(self):
        ep = self.arm['cold_start']
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(
            route_read_status='complete_nonempty'))
        with self.assertRaisesRegex(ValueError, 'contradicts'): self.admit()

    def test_new_record_is_kept_separate_from_original_cohort(self):
        s = self.update(self.moving(), 0); ep = self.arm['observations'][1]
        def add(x):
            row = x['army_strengths'][0]
            row['regiment_strengths'].append({'army_regiment_id': 3, 'current_soldiers': 1,
                                              'maximum_soldiers': 1, 'scale': 1})
            row['regiment_replenishment_records_v1'].append({
                'army_regiment_id': 3, 'status': 'available', 'native_data_record_count': 1,
                'records': [{'record_index': 0, 'persistent_regiment_id': 103, 'chunk_index': 0,
                             'current_soldiers': 1, 'maximum_soldiers': 1}]})
            row.update(regiment_count=3, current_soldiers=101, maximum_soldiers=101)
        ep['army_result'] = self.f.edit(ep['army_result'], add)
        r = a.report(self.update(s, 1))
        self.assertEqual(r['arrival_actual']['cohort_current'], 100)
        self.assertEqual(r['arrival_actual']['all_strategy_current'], 101)

    def test_only_actual_90_verified_days_grant_budget_censor(self):
        s = self.moving()
        for n in range(1, 91):
            ep = self.f.ep('A', n)
            ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(
                current_province_id=11, army_state='moving', route_province_ids=[30],
                route_read_status='complete_nonempty', move_target_province_id=30))
            clock = {'state': 'triggered', 'generation': n, 'starting_date_raw': 1000+(n-1)*24,
                     'target_date_raw': 1000+n*24, 'last_observed_date_raw': 1000+n*24,
                     'trigger_date_raw': 1000+n*24, 'speed': 5, 'mode': 'terminal_or_sentinel',
                     'army_count': 0, 'combat_count': 0, 'completed_daily_ticks': 1,
                     'intermediate_pause_count': 0, 'overshoot_days': 0,
                     'signed_date_delta_from_target_raw': 0, 'abnormal': False,
                     'pause_observed': True, 'pause_wrapper_called': True, 'trigger_reasons': ['date_deadline']}
            row = {'day': n, 'clock_source': self.f.put('synthetic-day-clock', {'clock': clock}),
                   'paused_snapshot': ep['snapshot'], 'strategy_army_ids': [1]}
            s = a.update(s, row, ep, self.e)
            if n == 89: self.assertIsNone(a.report(s)['disposition'])
        r = a.report(s)
        self.assertEqual(r['disposition'], 'budget-censored')
        self.assertEqual(r['absolute_deadline_raw'], 3160)
        self.assertIsNone(r['arrival_actual']); self.assertIsNone(r['arrival_interval_days'])

    def test_postarrival_observation_does_not_replace_arrival_metrics(self):
        self.f.plan['follow_after_arrival_to_day90'] = True
        self.f.plan['post_arrival_policy'] = 'SYNTHETIC stay at frozen goal; no resubmission.'
        s = self.update(self.update(self.moving(), 0), 1)
        ep = self.f.ep('A', 3)
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(current_province_id=30))
        day = deepcopy(self.arm['days'][1]); day['day'] = 3; day['paused_snapshot'] = ep['snapshot']
        day['clock_source'] = self.f.edit(day['clock_source'], lambda x: x['clock'].update(
            generation=3, starting_date_raw=1048, target_date_raw=1072,
            last_observed_date_raw=1072, trigger_date_raw=1072))
        r = a.report(a.update(s, day, ep, self.e))
        self.assertEqual(r['arrival_actual']['day'], 2)
        self.assertEqual(r['current_actual']['day'], 3)
        self.assertEqual(r['arrival_interval_days'], [1, 2]); self.assertIsNone(r['D90_endpoint'])


if __name__ == '__main__':
    unittest.main()
