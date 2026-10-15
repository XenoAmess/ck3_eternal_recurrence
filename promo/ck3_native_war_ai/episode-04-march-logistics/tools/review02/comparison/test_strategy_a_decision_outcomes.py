"""New account/arrival consumption examples; synthetic, never gameplay proof."""
from copy import deepcopy
import unittest

import r10_compare as c
import strategy_a as a
import test_strategy_a_route_inputs as setup_examples
from strategy_a_route_inputs import next_decision


class OutcomeInputs(unittest.TestCase):
    preview = setup_examples.InputsTests.preview
    moving = setup_examples.InputsTests.moving
    advance = setup_examples.InputsTests.advance
    setUp = setup_examples.InputsTests.setUp

    def wallet(self, state, raw):
        ep = deepcopy(state['observations'][-1] if state['days'] else
                      state['move_postcondition'] or state['cold_start'])
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['played_character_gold'].update(raw=raw))
        if state['days']:
            state['observations'][-1] = ep
        elif state['move_postcondition']:
            state['move_postcondition'] = ep
        else:
            state['cold_start'] = ep
        state['actual'], _ = a._whole(ep, state['plan'], self.e, state['runtime'], state['army_id'])
        return state

    def test_wallet_fall_is_observed_without_becoming_selected_army_maintenance(self):
        state = self.wallet(self.advance(self.moving(), 0), 24500000)
        r = next_decision(state, self.e)['account_observation']
        self.assertEqual((r['t0_wallet_raw'], r['current_wallet_raw'], r['unattributed_wallet_net_raw']),
                         (25000000, 24500000, -500000))
        self.assertFalse(r['wallet_net_is_selected_army_cost'])
        self.assertIsNone(r['selected_army_maintenance_paid_raw'])
        self.assertIsNone(r['selected_army_boarding_paid_raw'])

    def test_income_can_hide_payment_and_never_means_free_or_negative_fees(self):
        state = self.wallet(self.advance(self.moving(), 0), 25900000)
        r = next_decision(state, self.e)['account_observation']
        self.assertEqual(r['unattributed_wallet_net_raw'], 900000)
        self.assertIsNone(r['selected_army_boarding_paid_raw'])
        self.assertIsNone(r['other_cash_income_raw'])
        self.assertIsNone(r['other_cash_expense_raw'])

    def test_other_army_combat_is_retained_and_does_not_invent_economic_isolation(self):
        ep = self.state['cold_start']
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'].append(
            {'army_id':94, 'owner_character_id':7, 'current_province_id':99,
             'army_state':'in_combat', 'in_combat':True, 'retreating':False}))
        r = next_decision(self.state, self.e, self.fresh)
        self.assertEqual(r['proposed_call']['tool'], 'ck3_move_army')
        self.assertEqual(r['other_observed_player_armies'][0]['army_id'], 94)
        self.assertTrue(r['other_observed_player_armies'][0]['in_combat'])
        self.assertFalse(r['account_observation']['economic_isolation_from_other_armies_proved'])

    def test_registered_fee_request_stays_requested_when_cost_unknown(self):
        self.state['plan']['compare_fees'] = True
        r = next_decision(self.state, self.e, self.fresh)
        self.assertTrue(r['account_observation']['fee_comparison_requested'])
        self.assertIsNone(r['account_observation']['selected_army_maintenance_paid_raw'])
        self.assertEqual(r['proposed_call'], self.state['proposed_call'])

    def test_first_arrival_has_actual_stock_and_does_not_fill_common_or_D90(self):
        state = self.advance(self.advance(self.moving(), 0), 1)
        r = next_decision(state, self.e)['arrival_observation']
        self.assertEqual(r['first_arrival_interval_days'], [1, 2])
        self.assertEqual(r['first_arrival_actual']['units'][0]['stock_raw'], 1000000)
        self.assertTrue(r['current_meets_frozen_arrival'])
        self.assertIsNone(r['joint_common_date_rows'])
        self.assertIsNone(r['D90_endpoint'])
        self.assertFalse(r['automatic_post_arrival_advance_proposed'])

    def test_registered_later_poststate_does_not_rewrite_first_arrival_stock(self):
        self.f.plan.update(follow_after_arrival_to_day90=True, post_arrival_policy='SYNTHETIC follow existing policy')
        self.state = a.admit(self.f.plan, self.arm['runtime'], 'c'*64,
                             self.arm['cold_start'], self.fresh, self.e)
        state = self.advance(self.advance(self.moving(), 0), 1)
        ep = self.f.ep('A', 3)
        ep['snapshot'] = self.f.edit(ep['snapshot'], lambda x: x['body']['player_armies'][0].update(controllable=True))
        ep['army_result'] = self.f.edit(ep['army_result'], lambda x: x['army_strengths'][0].update(current_supply_raw=2000000))
        day = deepcopy(self.arm['days'][1]);day.update(day=3, paused_snapshot=ep['snapshot'])
        day['clock_source'] = self.f.edit(day['clock_source'], lambda x: x['clock'].update(
            generation=3, starting_date_raw=1048, target_date_raw=1072, last_observed_date_raw=1072, trigger_date_raw=1072))
        state = a.update(state, day, ep, self.e)
        r = next_decision(state, self.e)['arrival_observation']
        self.assertEqual(r['first_arrival_day'], 2)
        self.assertEqual(r['first_arrival_actual']['units'][0]['stock_raw'], 1000000)
        self.assertEqual(r['current_actual']['units'][0]['stock_raw'], 2000000)
        self.assertFalse(r['current_meets_frozen_arrival'])
        self.assertIsNone(r['D90_endpoint'])


if __name__ == '__main__':
    unittest.main()
