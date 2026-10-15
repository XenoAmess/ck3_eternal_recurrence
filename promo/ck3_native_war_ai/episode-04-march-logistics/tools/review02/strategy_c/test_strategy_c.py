"""Synthetic policy counterexamples, plus one small actual historical receipt.

No test launches CK3 or creates live acceptance credit.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import strategy_c as c


def plan():
    return {'t0_raw': 24000, 'max_natural_days': 90, 'raw_per_day': 24,
            'goal_province_id': 30, 'arrival_states': ['stationary', 'sieging'],
            'original_regiment_ids': [101, 102], 'strategies': {'C': {
                'mode': 'whole-via', 'waypoint_province_ids': [20],
                'route_preview': {'path': 'SYNTHETIC-preview.json', 'bytes': 1, 'sha256': '0' * 64}}}}


def obs(day=0, revision=1, position=10, route=None, target=None, stock=3,
        current=(8, 9), state='stationary'):
    route = [] if route is None else route
    total = sum(current)
    return {'endpoint': {'day': day, 'date_raw': 24000 + day * 24,
        'units': [{'army_id': 7, 'current_province_id': position,
                   'state': state, 'route': route, 'target': target,
                   'stock_raw': stock, 'capacity_raw': 30000000, 'scale': 100000,
                   'current_soldiers': total, 'maximum_soldiers': 20}],
        'commander_id': 11, 'cohort_regiments': [
            {'army_regiment_id': rid, 'current_soldiers': cur, 'maximum_soldiers': 10}
            for rid, cur in zip((101, 102), current)],
        'cohort_current': total, 'cohort_maximum': 20,
        'all_strategy_current': total, 'all_strategy_maximum': 20, 'treasury_raw': 9000000},
        'binding': {'machine_id': 'SYNTHETIC-machine', 'pid': 123,
                    'process_create_time_100ns': 456, 'connection_generation': 1,
                    'episode': 'SYNTHETIC-episode', 'snapshot_id': f'SYNTHETIC-{revision}',
                    'revision': revision, 'native_revision': revision, 'native_carmy_id': 9,
                    'paused': True, 'controllable': True, 'in_combat': False,
                    'retreating': False, 'move_target_observable': bool(route)}}


def clock(observation, generation):
    raw = observation['endpoint']['date_raw']
    observation['clock'] = {'state': 'triggered', 'starting_date_raw': raw - 24,
        'target_date_raw': raw, 'last_observed_date_raw': raw, 'trigger_date_raw': raw,
        'speed': 5, 'completed_daily_ticks': 1, 'overshoot_days': 0,
        'signed_date_delta_from_target_raw': 0, 'abnormal': False, 'pause_observed': True,
        'mode': 'terminal_or_sentinel', 'army_count': 0, 'combat_count': 0,
        'trigger_reasons': ['date_deadline'], 'pause_wrapper_called': True,
        'intermediate_pause_count': 0, 'generation': generation}
    return observation


def preview(observation, target=20, route=None):
    b = observation['binding']
    u = observation['endpoint']['units'][0]
    return {'accepted': True,
        **{k: b[v] for k, v in [('queried_snapshot_id', 'snapshot_id'),
             ('queried_revision', 'revision'), ('queried_native_revision', 'native_revision'),
             ('queried_connection_generation', 'connection_generation'),
             ('queried_episode_run_id', 'episode')]},
        'route_preview': {'status': 'available', 'army_id': 7,
             'origin_province_id': u['current_province_id'], 'target_province_id': target,
             'route_province_ids': [target] if route is None else route,
             'previewed_date_raw': observation['endpoint']['date_raw']}}


def launched():
    p, initial = plan(), obs()
    state = c.start(p, initial)
    pending, action = c.propose_move(p, state, initial, preview(initial))
    applied = obs(revision=2, route=[20], target=20, state='moving')
    return p, c.observe(p, pending, applied), action


class StrategyCCounterexamples(unittest.TestCase):
    def test_pending_state_survives_JSON_persistence_before_one_submit(self):
        p, initial = plan(), obs()
        state = json.loads(json.dumps(c.start(p, initial)))
        state, _ = c.propose_move(p, state, initial, preview(initial))
        state = json.loads(json.dumps(state))
        applied = obs(revision=2, route=[20], target=20, state='moving')
        self.assertEqual(c.observe(p, state, applied)['phase'], 'marching')

    def test_whole_via_two_leg_flow_and_no_supply_or_refill_wait(self):
        p, state, action = launched()
        self.assertFalse(action['dispatch_performed'])
        self.assertEqual(state['phase'], 'marching')  # stock3, original17/20 is enough to execute frozen C
        at_way = clock(obs(1, 3, 20, stock=1), 10)
        state = c.observe(p, state, at_way)
        state, _ = c.propose_move(p, state, at_way, preview(at_way, 30, [25, 30]))
        applied = obs(1, 4, 20, [25, 30], 30, stock=1, state='moving')
        state = c.observe(p, state, applied)
        middle = clock(obs(2, 5, 25, [30], 30, stock=0, state='moving'), 11)
        state = c.observe(p, state, middle)
        arrived = clock(obs(3, 6, 30, stock=0, current=(9, 9), state='sieging'), 12)
        state = c.observe(p, state, arrived)
        self.assertEqual(state['phase'], 'arrived')
        self.assertEqual(state['arrivals'][-1]['observed_interval_days'], [2, 3])
        out = c.outcome(state, arrived)
        self.assertIsNone(out['physical_ADD_or_debit_cause'])
        self.assertIsNone(out['actual_military_fees'])
        self.assertFalse(out['research_card_closed'])

    def test_ack_unknown_remains_pending_and_cannot_resubmit(self):
        p, initial = plan(), obs()
        pending, _ = c.propose_move(p, c.start(p, initial), initial, preview(initial))
        unchanged = c.observe(p, pending, initial)
        self.assertEqual(unchanged['phase'], 'pending_move')
        with self.assertRaisesRegex(ValueError, 'must not be resubmitted'):
            c.propose_move(p, unchanged, initial, preview(initial))
        with self.assertRaisesRegex(ValueError, 'before advancing'):
            c.observe(p, unchanged, clock(obs(1, 2, 20), 1))

    def test_london_camera_and_moving_through_goal_do_not_prove_arrival(self):
        p, state, _ = launched()
        wrong = clock(obs(1, 3, 10, [20], 20, state='moving'), 1)
        wrong['camera_center_province'] = 20
        self.assertEqual(c.observe(p, state, wrong)['phase'], 'marching')
        crossing = clock(obs(1, 3, 20, [20], 20, state='moving'), 1)
        self.assertEqual(c.observe(p, state, crossing)['phase'], 'marching')

    def test_stale_preview_and_inconsistent_target_observability_fail(self):
        p, initial = plan(), obs()
        state = c.start(p, initial)
        stale = preview(initial)
        stale['queried_revision'] = 0
        with self.assertRaisesRegex(ValueError, 'stale/foreign'):
            c.propose_move(p, state, initial, stale)
        # Native Route returns complete_empty with observable=false/id-null;
        # this is a normal endpoint, not a missing target-clear getter.
        self.assertFalse(initial['binding']['move_target_observable'])
        c.start(p, initial)
        initial['binding']['move_target_observable'] = True
        with self.assertRaisesRegex(ValueError, 'native complete-route'):
            c.start(p, initial)

    def test_wrong_target_and_unregistered_waiting_policy_fail(self):
        p, initial = plan(), obs()
        state = c.start(p, initial)
        with self.assertRaisesRegex(ValueError, 'frozen next target'):
            c.propose_move(p, state, initial, preview(initial, 30))
        p['strategies']['C']['minimum_stock_raw'] = 100
        with self.assertRaisesRegex(ValueError, 'unregistered'):
            c.start(p, initial)

    def test_two_day_sampling_cannot_be_exact_even_with_valid_final_position(self):
        p, state, _ = launched()
        with self.assertRaisesRegex(ValueError, 'missing daily observation'):
            c.observe(p, state, clock(obs(2, 3, 20), 1))
        one = clock(obs(1, 3, 20), 1)
        one['clock']['completed_daily_ticks'] = 2
        with self.assertRaisesRegex(ValueError, 'one actual day'):
            c.observe(p, state, one)
        one['clock']['completed_daily_ticks'] = True
        with self.assertRaisesRegex(ValueError, 'actual integers'):
            c.observe(p, state, one)

    def test_no_clock_reset_or_reused_generation(self):
        p, state, _ = launched()
        day1 = clock(obs(1, 3, 10, [20], 20, state='moving'), 7)
        state = c.observe(p, state, day1)
        with self.assertRaisesRegex(ValueError, 'generation must increase'):
            c.observe(p, state, clock(obs(2, 4, 10, [20], 20, state='moving'), 7))
        with self.assertRaisesRegex(ValueError, 'common T0'):
            c.start(p, day1)

    def test_original_deficit_not_hidden_by_new_regiment_or_effective_strength(self):
        p, initial = plan(), obs()
        initial['endpoint']['all_strategy_current'] += 1
        with self.assertRaisesRegex(ValueError, 'cannot substitute'):
            c.start(p, initial)
        # A genuinely observed additional 1/1 is retained separately, never
        # subtracted from the frozen cohort's physical deficit or discarded.
        initial['endpoint']['units'][0]['current_soldiers'] += 1
        initial['endpoint']['all_strategy_maximum'] += 1
        initial['endpoint']['units'][0]['maximum_soldiers'] += 1
        state = c.start(p, initial)
        result = c.outcome(state, initial)
        self.assertEqual(result['original_cohort_physical_current'], 17)
        self.assertEqual(result['all_strategy_current'], 18)
        bad = obs(current=(10, 9))
        bad['endpoint']['cohort_regiments'][0]['current_soldiers'] = None
        bad['endpoint']['cohort_regiments'][0]['effective_current'] = 10
        with self.assertRaisesRegex(ValueError, 'physical scale1'):
            c.start(p, bad)

    def test_new_runtime_or_commander_does_not_reuse_C_state(self):
        p, state, _ = launched()
        for field, value in [('native_carmy_id', 10), ('connection_generation', 2),
                             ('machine_id', 'SYNTHETIC-other-machine')]:
            changed = clock(obs(1, 3, 20), 1)
            changed['binding'][field] = value
            with self.assertRaisesRegex(ValueError, 'runtime/subject changed'):
                c.observe(p, state, changed)
        changed = clock(obs(1, 3, 20), 1)
        changed['endpoint']['commander_id'] = 12
        with self.assertRaisesRegex(ValueError, 'commander changed'):
            c.observe(p, state, changed)

    def test_changed_applied_route_and_unlogged_reroute_fail(self):
        p, initial = plan(), obs()
        pending, _ = c.propose_move(p, c.start(p, initial), initial, preview(initial))
        with self.assertRaisesRegex(ValueError, 'applied route differs'):
            c.observe(p, pending, obs(revision=2, route=[15, 20], target=20, state='moving'))
        p, state, _ = launched()
        with self.assertRaisesRegex(ValueError, 'unlogged reroute'):
            c.observe(p, state, clock(obs(1, 3, 10, [16, 20], 20, state='moving'), 1))

    def test_only_real_day90_nonarrival_is_budget_censor(self):
        p, state, _ = launched()
        stopped = c.stop(state, 'world-event: war ended at day0')
        self.assertEqual(stopped['phase'], 'stopped')
        for day in range(1, 91):
            state = c.observe(p, state, clock(obs(day, day + 2, 10, [20], 20, state='moving'), day))
        self.assertEqual(state['phase'], 'budget-censored')
        self.assertEqual(state['last_day'], 90)

    def test_historical_C_receipt_has_15_two_day_deviations_not_15_day_sampling(self):
        episode = Path(__file__).resolve().parents[3]
        value = json.loads((episode / 'evidence/r0176-c-descriptive-march/normalized_C_result.json').read_bytes())
        self.assertEqual(len(value['sampling_deviations']), 15)
        self.assertTrue(all(x['planned_max_days'] == 1 and x['actual_days'] == 2
                            and x['one_day_eligible'] is False for x in value['sampling_deviations']))
        self.assertEqual(value['observed_arrival_interval_days'], [75, 77])
        self.assertEqual(value['sampling_deviations'][-1]['observed_days'], [75, 77])
        self.assertEqual(value['controlled_comparison_eligibility'], 'NOT_GRANTED')
        self.assertIsNone(value['London_endpoint_metrics']['exact_arrival_tick'])
        self.assertIsNone(value['applied_refill_payment_ledger'])


if __name__ == '__main__':
    unittest.main()
