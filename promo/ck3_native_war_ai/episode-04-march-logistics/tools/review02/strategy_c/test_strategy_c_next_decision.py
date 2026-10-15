"""New adapter-only compound cases; no old Strategy C test suite is run."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'comparison'))
import r10_compare as reader
from test_r10_compare import Fixture
import strategy_c as c
import strategy_c_next_decision as d


def fresh_preview(observation, target=20, route=None):
    ep, binding = observation['endpoint'], observation['binding']
    unit = ep['units'][0]
    return {'accepted': True, 'route_preview': {'status': 'available',
        'army_id': unit['army_id'], 'origin_province_id': unit['current_province_id'],
        'target_province_id': target, 'route_province_ids': [target] if route is None else route,
        'previewed_date_raw': ep['date_raw']},
        **{k: binding[v] for k, v in [('queried_snapshot_id', 'snapshot_id'),
          ('queried_revision', 'revision'), ('queried_native_revision', 'native_revision'),
          ('queried_connection_generation', 'connection_generation'),
          ('queried_episode_run_id', 'episode')]}}


def movement(progress=60001, cutoff=50000):
    return {'source': 'native_current_route_edge', 'status': 'available',
            'normalized_edge_progress': {'raw': progress, 'scale': 100000},
            'loaded_movement_lock_cutoff': {'raw': cutoff, 'scale': 100000}}


class NextDecisionCompound(unittest.TestCase):
    def test_adapter_can_be_imported_without_cwd_or_sibling_sys_path(self):
        saved_path = sys.path[:]
        old_policy = sys.modules.pop('strategy_c', None)
        try:
            sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != HERE]
            spec = importlib.util.spec_from_file_location('SYNTHETIC_standalone_C_adapter',
                HERE / 'strategy_c_next_decision.py')
            loaded = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(loaded)
            result = loaded.next_decision(self.plan, self.state, self.observation)
            self.assertEqual(result['status'], 'needs_fresh_preview')
        finally:
            sys.path[:] = saved_path
            if old_policy is not None:
                sys.modules['strategy_c'] = old_policy

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='SYNTHETIC-C-next-')
        self.f = Fixture(self.temp.name)
        arm = self.f.results['arms'][2]
        self.record = arm['cold_start']
        self.record['snapshot'] = self.f.edit(self.record['snapshot'],
            lambda x: x['body']['player_armies'][0].update(controllable=True,
               in_combat=False, retreating=False, move_target_observable=False))
        def full_rows(value):
            row = value['army_strengths'][0]
            row['native_carmy_id'] = 99
            row['current_movement_progress'] = movement()
            for data in row['regiment_replenishment_records_v1']:
                data.update(source='native_all_data_records', ready=True, unavailable_reason=None)
                for record in data['records']:
                    record.update(status='available', unavailable_reason=None,
                                  effective_current_soldiers=record['current_soldiers'])
        self.record['army_result'] = self.f.edit(self.record['army_result'], full_rows)
        self.plan = self.f.plan
        self.observation = d.read_inputs(self.plan, arm['runtime'], self.record, reader.Evidence(self.temp.name))
        self.state = c.start(self.plan, self.observation)

    def tearDown(self):
        self.temp.cleanup()

    def moving(self, route=None):
        observed = deepcopy(self.observation)
        unit = observed['endpoint']['units'][0]
        unit.update(state='moving', route=[15, 20] if route is None else route,
                    target=20 if route is None else route[-1])
        observed['binding']['move_target_observable'] = True
        return observed

    def test_fresh_draft_candidate_choice_and_frozen_policy_boundary(self):
        draft = deepcopy(self.plan)
        draft['status'] = 'draft'
        previews = {21: {'accepted': False, 'route_preview': {'status': 'deferred'}},
                    20: fresh_preview(self.observation)}
        result = d.choose_draft_via(draft, self.observation, [21, 20], previews)
        self.assertEqual(result['selected_waypoint'], 20)
        self.assertEqual(result['candidate_diagnostics'][0]['province_id'], 21)
        self.assertFalse(result['onward_leg_qualified'])
        self.assertIsNone(result['proposed_call'])
        blocked = d.choose_draft_via(self.plan, self.observation, [20], previews)
        self.assertEqual(blocked['status'], 'hold_unknown')
        self.assertIn('frozen', blocked['reason'])

    def test_stale_first_preview_does_not_become_a_legal_via(self):
        draft = deepcopy(self.plan)
        draft['status'] = 'draft'
        stale = fresh_preview(self.observation)
        stale['queried_connection_generation'] += 1
        out = d.choose_draft_via(draft, self.observation, [20], {20: stale})
        self.assertIsNone(out['selected_waypoint'])
        self.assertIn('stale/foreign', out['candidate_diagnostics'][0]['reason'])

    def test_new_adapter_proposes_only_existing_preview_then_typed_move(self):
        missing = d.next_decision(self.plan, self.state, self.observation)
        self.assertEqual(missing['proposed_read_only_call']['tool'], 'ck3_execute_step')
        self.assertEqual(missing['proposed_read_only_call']['arguments']['step'], 'preview-move-army-1-to-20')
        decision = d.next_decision(self.plan, self.state, self.observation, fresh_preview(self.observation))
        self.assertEqual(decision['status'], 'propose_existing_move')
        self.assertEqual(decision['proposed_call']['tool'], 'ck3_move_army')
        self.assertEqual(decision['next_state']['phase'], 'pending_move')
        pending = d.next_decision(self.plan, decision['next_state'], self.observation)
        self.assertEqual(pending['status'], 'hold_unknown')
        self.assertIsNone(pending['proposed_call'])
        self.assertEqual(pending['proposed_read_only_call']['tool'], 'ck3_query_army_strengths')

    def test_record_level_holes_and_all_regiment_DATA_loss_block_the_proposal(self):
        for mutate in (
            lambda x: x['endpoint']['DATA'][0]['records'][0].update(status='unavailable', unavailable_reason='SYNTHETIC-unresolved'),
            lambda x: x['endpoint']['DATA'].pop(),
            lambda x: x['decision_inputs']['all_regiment_ids'].append(3),
            lambda x: x['endpoint']['DATA'][0]['records'][0].update(record_index=2),
            lambda x: x['endpoint']['DATA'][0]['records'][0].update(current_soldiers=None, effective_current_soldiers=50),
        ):
            changed = deepcopy(self.observation)
            mutate(changed)
            out = d.next_decision(self.plan, self.state, changed, fresh_preview(changed))
            self.assertEqual(out['status'], 'hold_unknown')
            self.assertIsNone(out['proposed_call'])
            self.assertIsNotNone(changed['endpoint']['DATA'])

    def test_stored_alias_occurrences_are_retained_without_gain_sum(self):
        observed = deepcopy(self.observation)
        row = observed['endpoint']['DATA'][0]
        alias = deepcopy(row['records'][0])
        alias['record_index'] = 1
        row['records'].append(alias)
        row['native_data_record_count'] = 2
        out = d.next_decision(self.plan, self.state, observed, fresh_preview(observed))
        self.assertEqual(out['status'], 'propose_existing_move')
        self.assertEqual(out['coverage']['stored_DATA_count'], 3)
        self.assertTrue(out['coverage']['record_aliases_not_summed'])
        self.assertNotIn('predicted_replenishment', out)

    def test_locked_front_does_not_forbid_a_native_suffix_preview(self):
        observed = self.moving()
        no_preview = d.route_change_advice(self.plan, observed, 25)
        self.assertEqual(no_preview['status'], 'hold_locked_front')
        self.assertFalse(no_preview['immediate_edge_cancellation_legal'])
        route = fresh_preview(observed, 25, [15, 25])
        allowed = d.route_change_advice(self.plan, observed, 25, route)
        self.assertEqual(allowed['status'], 'native_preview_available')
        self.assertTrue(allowed['suffix_route_change_ready'])
        self.assertIsNone(allowed['proposed_call'])
        self.assertFalse(allowed['immediate_edge_cancellation_legal'])
        shortcut = d.route_change_advice(self.plan, observed, 25, fresh_preview(observed, 25, [25]))
        self.assertEqual(shortcut['status'], 'hold_locked_front')
        self.assertIsNone(shortcut['suffix_route_change_ready'])

    def test_missing_lock_input_is_unknown_and_exact_cutoff_is_not_above(self):
        observed = self.moving()
        observed['decision_inputs']['current_movement_progress']['loaded_movement_lock_cutoff'] = None
        unknown = d.route_change_advice(self.plan, observed, 25, fresh_preview(observed, 25, [15, 25]))
        self.assertEqual(unknown['status'], 'hold_unknown')
        self.assertIsNone(unknown['edge_lock']['locked'])
        observed['decision_inputs']['current_movement_progress'] = movement(50000, 50000)
        equal = d.route_change_advice(self.plan, observed, 25, fresh_preview(observed, 25, [25]))
        self.assertEqual(equal['edge_lock']['state'], 'not_above_cutoff')
        self.assertIsNone(equal['immediate_edge_cancellation_legal'])

    def test_new_frame_must_use_existing_observe_and_old_interval_stays_interval(self):
        new = deepcopy(self.observation)
        new['binding']['snapshot_id'] = 'SYNTHETIC-new-publication'
        out = d.next_decision(self.plan, self.state, new, fresh_preview(new))
        self.assertEqual(out['status'], 'needs_existing_observe')
        terminal = deepcopy(self.state)
        terminal.update(phase='arrived', arrivals=[{'province_id': 30, 'day': 77,
            'observed_interval_days': [75, 77], 'exact_arrival_tick': None}])
        out = d.next_decision(self.plan, terminal, self.observation)
        self.assertEqual(out['actual_arrival_intervals'][0]['observed_interval_days'], [75, 77])
        self.assertIsNone(out['exact_arrival_tick'])
        self.assertFalse(out['research_card_closed'])

    def test_existing_march_proposes_only_the_existing_absolute_one_day_arm(self):
        proposal = d.next_decision(self.plan, self.state, self.observation, fresh_preview(self.observation))
        applied = self.moving([20])
        applied['binding']['native_revision'] += 1
        applied['binding']['revision'] += 1
        applied['binding']['snapshot_id'] += ':SYNTHETIC-applied'
        state = c.observe(self.plan, proposal['next_state'], applied)
        out = d.next_decision(self.plan, state, applied)
        self.assertEqual(out['status'], 'continue_exact_day')
        self.assertEqual(out['proposed_call']['arguments']['step'],
            'research-arm-tactical-daily-sentinel-v1-1000-to-1024-speed-5-mode-terminal-a-0')
        self.assertNotIn('resume', out['proposed_call']['arguments']['step'])


if __name__ == '__main__':
    unittest.main()
