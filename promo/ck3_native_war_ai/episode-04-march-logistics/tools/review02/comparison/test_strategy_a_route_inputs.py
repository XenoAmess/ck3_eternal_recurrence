"""Minimal synthetic counterexamples for the existing-state policy adapter."""
from copy import deepcopy
import tempfile
import unittest

import r10_compare as c
import strategy_a as a
from strategy_a_route_inputs import next_decision
from test_r10_compare import Fixture


class InputsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name); self.e = c.Evidence(self.temp.name)
        self.arm = self.f.results['arms'][0]
        for ep in (self.f.plan['baseline'], self.arm['cold_start'], *self.arm['observations']):
            ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(controllable=True))
        self.f.plan['strategies']['A']['route_preview'] = self.preview(self.f.plan['baseline'])
        self.fresh = self.preview(self.arm['cold_start'])
        self.state = a.admit(self.f.plan, self.arm['runtime'], 'c'*64, self.arm['cold_start'], self.fresh, self.e)

    def preview(self, ep, supply=True):
        s = c.body(self.e.json(ep['snapshot'])); p = s['player_armies'][0]
        route = {'status': 'available', 'army_id': 1, 'origin_province_id': p['current_province_id'],
                 'target_province_id': 30, 'route_province_ids': [20, 30], 'previewed_date_raw': s['date_raw']}
        if supply:
            def row(role, pid, limit, usage):
                return {'status': 'available', 'unavailable_reason': None, 'role': role, 'province_id': pid,
                        'native_supply_limit_soldiers': limit, 'native_supply_usage_soldiers': usage, 'scale': 1}
            route['province_supply'] = {'status': 'available', 'unavailable_reason': None, 'army_id': 1,
                'native_carmy_id': 77, 'owner_character_id': 7, 'commander_character_id': None,
                'current': row('current', p['current_province_id'], 4000, 6000),
                'target': row('target', 30, 3000, 0)}
        return self.f.put('synthetic-preview', {'accepted': True, 'status': 'available',
            'step': 'preview-move-army-1-to-30', 'route_preview': route,
            **{'queried_'+k: s[k] for k in ('snapshot_id', 'revision', 'native_revision', 'episode_run_id')},
            'queried_connection_generation': s['diagnostics']['connection_generation']})

    def moving(self):
        post = deepcopy(self.state['cold_start'])
        def edit(x):
            s = x['body']; s.update(snapshot_id='A:post', revision=11, native_revision=10)
            s['player_armies'][0].update(army_state='moving', route_province_ids=[20, 30],
                                       route_read_status='complete_nonempty', move_target_province_id=30)
        post['snapshot'] = self.f.edit(post['snapshot'], edit)
        post['army_result'] = self.f.edit(post['army_result'], lambda x: x.update(
            queried_snapshot_id='A:post', queried_revision=11, queried_native_revision=10))
        return a.observe_move(self.state, post, self.e)

    def advance(self, state, index, province=None):
        ep = deepcopy(self.arm['observations'][index]); day = deepcopy(self.arm['days'][index])
        if province is not None:
            ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(current_province_id=province))
        day['paused_snapshot'] = ep['snapshot']
        return a.update(state, day, ep, self.e)

    def test_target_usage_zero_is_not_future_headroom(self):
        result = next_decision(self.state, self.e, self.fresh)
        target = result['native_province_supply']['target']
        self.assertEqual(target['native_supply_usage_soldiers'], 0)
        self.assertFalse(target['signed_usage_exceeds_limit'])
        self.assertIsNone(result['unknown']['future_target_usage_soldiers'])
        self.assertIsNone(result['unknown']['future_losses_soldiers'])
        self.assertEqual(result['proposed_call'], self.state['proposed_call'])

    def test_individual_Army_below_limit_does_not_erase_aggregate_pressure(self):
        result = next_decision(self.state, self.e, self.fresh)
        self.assertEqual(result['observed_current']['all_strategy_current'], 100)
        self.assertEqual(result['native_province_supply']['current']['usage_minus_limit_soldiers'], 2000)
        self.assertTrue(result['current_aggregate_pressure_suggests_review'])
        self.assertIsNone(result['unknown']['split_size_to_avoid_loss'])
        self.assertIsNone(result['unknown']['split_loss_saving_soldiers'])
        self.assertEqual(result['policy'], 'preserve_frozen_whole_direct')
        self.assertEqual(result['proposed_call']['tool'], 'ck3_move_army')

    def test_missing_sibling_never_blocks_legal_Move_or_means_zero(self):
        pin = self.preview(self.state['cold_start'], supply=False)
        r = next_decision(self.state, self.e, pin)
        self.assertEqual(r['proposed_call'], self.state['proposed_call'])
        self.assertIsNone(r['native_province_supply']['current'])
        self.assertIsNone(r['current_aggregate_pressure_suggests_review'])

    def test_unavailable_context_keeps_legal_Move(self):
        def edit(x):
            s = x['route_preview']['province_supply']
            s.update(status='unavailable', unavailable_reason='owner_unresolved', owner_character_id=None, native_carmy_id=None)
            for role in ('current', 'target'):
                s[role].update(status='unavailable', unavailable_reason='owner_unresolved',
                               native_supply_limit_soldiers=None, native_supply_usage_soldiers=None)
        r = next_decision(self.state, self.e, self.f.edit(self.fresh, edit))
        self.assertIsNone(r['native_province_supply']['current'])
        self.assertEqual(r['proposed_call']['tool'], 'ck3_move_army')

    def test_partial_target_does_not_erase_current_pressure(self):
        def edit(x):
            s = x['route_preview']['province_supply']; s.update(status='partial', unavailable_reason='target_not_read')
            s['target'].update(status='unavailable', unavailable_reason='target_not_read',
                               native_supply_limit_soldiers=None, native_supply_usage_soldiers=None)
        r = next_decision(self.state, self.e, self.f.edit(self.fresh, edit))
        self.assertTrue(r['current_aggregate_pressure_suggests_review'])
        self.assertIsNone(r['native_province_supply']['target'])

    def test_stale_preview_and_wrong_supply_context_rejected(self):
        pin = self.f.edit(self.fresh, lambda x: x.update(queried_connection_generation=9))
        with self.assertRaisesRegex(ValueError, 'generation differs'):
            next_decision(self.state, self.e, pin)
        pin = self.f.edit(self.fresh, lambda x: x['route_preview']['province_supply'].update(owner_character_id=999))
        with self.assertRaisesRegex(ValueError, 'owner differs'):
            next_decision(self.state, self.e, pin)

    def test_queued_intermediate_is_not_actual_pass_through(self):
        s = self.moving(); r = next_decision(s, self.e)
        self.assertEqual(r['queued_route'], [20, 30])
        self.assertEqual(r['actual_observed_on_initial_route'], [])
        self.assertEqual(r['not_independently_observed_province_ids'], [20, 30])
        self.assertEqual(r['proposed_call']['arguments'], {'step': 'preview-move-army-1-to-30', 'expected_revision': 11})

    def test_arrival_does_not_backfill_unsampled_intermediate(self):
        s = self.advance(self.advance(self.moving(), 0), 1)
        r = next_decision(s, self.e)
        self.assertEqual({x['province_id'] for x in r['actual_observed_on_initial_route']}, {30})
        self.assertEqual(r['not_independently_observed_province_ids'], [20])
        self.assertEqual(r['policy'], 'terminal'); self.assertIsNone(r['proposed_call'])

    def test_actual_pass_through_requires_original_snapshot_current(self):
        s = self.advance(self.moving(), 0, province=20)
        r = next_decision(s, self.e)
        self.assertEqual([(x['province_id'], x['day']) for x in r['actual_observed_on_initial_route']], [(20, 1)])
        self.assertEqual(r['not_independently_observed_province_ids'], [30])

    def test_world_contact_yields_to_ordinary_policy_without_new_Move(self):
        ep = self.arm['observations'][0]
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(
            army_state='in_combat', controllable=False, route_province_ids=[],
            route_read_status='complete_empty', move_target_province_id=None))
        r = next_decision(self.advance(self.moving(), 0), self.e)
        self.assertEqual(r['ordinary_policy_action_status'], 'needs_current_state_decision')
        self.assertIsNone(r['proposed_call'])

    def test_current_zero_attrition_and_negative_rate_are_not_future_prediction(self):
        ep = self.state['cold_start']
        def edit(x):
            x['army_strengths'][0].update(current_supply_change_monthly_raw=-500000,
                current_supply_change_monthly_scale=100000,
                current_attrition_fraction_raw=0, current_attrition_fraction_scale=100000)
        ep['army_result'] = self.f.edit(ep['army_result'], edit)
        r = next_decision(self.state, self.e, self.fresh)
        self.assertEqual(r['observed_current']['current_attrition_fraction']['raw'], 0)
        self.assertEqual(r['observed_current']['current_supply_change_monthly']['raw'], -500000)
        self.assertIsNone(r['unknown']['future_losses_soldiers'])
        self.assertIsNone(r['unknown']['military_maintenance_paid_raw'])
        self.assertIsNone(r['unknown']['future_refills_soldiers'])

    def test_null_getter_with_scale_remains_unknown(self):
        ep = self.state['cold_start']
        ep['army_result'] = self.f.edit(ep['army_result'], lambda x: x['army_strengths'][0].update(
            current_attrition_fraction_raw=None, current_attrition_fraction_scale=100000))
        self.assertIsNone(next_decision(self.state, self.e)['observed_current']['current_attrition_fraction'])

    def test_native_zero_and_INTMAX_are_valid_but_bool_is_not_integer(self):
        pin = self.f.edit(self.fresh, lambda x: x['route_preview']['province_supply']['current'].update(
            native_supply_limit_soldiers=2**31-1, native_supply_usage_soldiers=0))
        r = next_decision(self.state, self.e, pin)
        self.assertFalse(r['current_aggregate_pressure_suggests_review'])
        bad = self.f.edit(pin, lambda x: x['route_preview']['province_supply']['current'].update(native_supply_usage_soldiers=False))
        with self.assertRaisesRegex(ValueError, 'native usage'):
            next_decision(self.state, self.e, bad)


if __name__ == '__main__':
    unittest.main()
