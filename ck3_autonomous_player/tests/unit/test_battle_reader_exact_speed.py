"""New speed admission tests; all Native/OS boundaries are fake, no live I/O."""
from pathlib import Path
import copy
import json
import os
import threading
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.battle_reader_watch_v1 import CLOCK_CAPABILITIES
from xar_autoplayer.bridge import battle_reader_exact_clock_speed_v1 as speed
DATA = json.loads((HERE / 'fixtures/battle_reader_actual_clock_projection.json').read_text(encoding='utf-8'))


def entry(seq):
    failure = DATA['failures'][str(seq)]
    return {'command': failure['step'], 'ok': False, 'result': copy.deepcopy(failure)}


def snapshot(seq=52):
    clock = DATA['clocks'][str(seq)]
    frame = clock['planning_source_frame']
    s = {k: frame[k] for k in ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'episode_run_id')}
    s.update(paused=True, map_ready=True, speed=1, active_event=None, pending_character_interaction=None,
             one_life_terminal=False, war_objective_assault_supported=True,
             played_character={'alive': True, 'character_id': frame['actor_character_id']},
             episode_character_id=frame['actor_character_id'],
             diagnostics={'bridge_pid': frame['bridge_pid'], 'connection_generation': frame['connection_generation']},
             top_exclusive_modal_choice_hint={'status': 'absent', 'owner_verified': True})
    progress = copy.deepcopy(clock['result']['war_progress_before']['wars'])
    s['active_wars'] = progress
    s['player_armies'] = []
    for war in progress:
        war['allied_armies'] = []  # Explicit synthetic semantic reconstruction.
        war['objective_province_states'] = []
        for army in war['player_armies']:
            army.update(controllable=True, owner_character_id=frame['actor_character_id'])
            s['player_armies'].append(army)
    return s


def history(seq=52):
    rows = [entry(50)]
    if seq == 56:
        rows.append({'command': 'life-advance-one-day', 'ok': True,
                     'result': copy.deepcopy(DATA['clocks']['52']['result'])})
        rows.append(entry(54))
    return rows


CAPS = set(CLOCK_CAPABILITIES)
STEPS = {'set-speed-1', 'set-speed-5', 'life-advance-one-day', 'resume-map', 'pause-map',
         native.QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP}


def ready(s, rows, **overrides):
    args = dict(exact_one_day=True, result_step='life-advance-one-day', proof_kind=None,
                bridge_capabilities=CAPS, available_action_steps=STEPS, assault_in_progress=False)
    args.update(overrides)
    return speed.reader_watch_exact_speed_five_ready_v1(s, rows, **args)


def _baseline_life(self, **kwargs):
    # Disable only the new admission while exercising the same production clock.
    with patch.object(speed, 'reader_watch_exact_speed_five_ready_v1', return_value=False):
        return native.NativeHeadlessGameplayDriver._execute_life_advance(self, **kwargs)


class FakeDriver(native.NativeHeadlessGameplayDriver):
    """The production life/sentinel/resume/pause/wait methods run unchanged."""
    def __init__(self, seq=52, *, candidate=True, overshoot=False, modal=False):
        self.current = snapshot(seq)
        self._command_history = history(seq)
        self._history_lock = threading.RLock()
        self.command_timeout_seconds = 1
        self.life_advance_timeout_seconds = 1
        self.steps, self.bridge = set(STEPS), set(CAPS)
        self.state = self
        self.native_commands = []
        self.start_date = self.current['date_raw']
        self.target_date = self.start_date + 24
        self.requested_speed = None
        self.overshoot = overshoot
        self.modal = modal
        if not candidate:
            self._execute_life_advance = _baseline_life.__get__(self)
    def _h3937_date_hold_active(self, snapshot): return False
    def take_internal_semantic_snapshot(self): return copy.deepcopy(self.current)
    def capabilities(self):
        return {'snapshot': True, 'bridge_capabilities': list(self.bridge), 'action_steps': list(self.steps),
                'current_event_window_context_v1_query_supported': True}
    def _bump(self):
        self.current['native_revision'] += 1
        self.current['revision'] += 1
        self.current['snapshot_id'] = 'native:' + str(self.current['native_revision'])
    def wait_for_public_change(self, *args):
        if self.current['date_raw'] == self.start_date:
            self.current['date_raw'] = self.target_date + (24 if self.overshoot else 0)
        else:
            self.current['paused'] = True
        self._bump()
    def _execute_primitive_step(self, step, **kwargs):
        self.native_commands.append(step)
        result = {'step': step, 'accepted': True, 'status': 'submitted', 'backend_id': 'native-headless'}
        if step.startswith('set-speed-'):
            self.current['speed'] = int(step.rsplit('-', 1)[1]); self._bump()
        elif step.startswith(native._TACTICAL_DAILY_SENTINEL_ARM_PREFIX):
            arm = copy.deepcopy(DATA['clocks']['52']['result']['exact_day_native_clock']['armed'])
            self.requested_speed = self.current['speed']
            arm.update(starting_date_raw=self.start_date, target_date_raw=self.target_date,
                       last_observed_date_raw=self.start_date, speed=self.requested_speed)
            result.update(status='available', tactical_daily_sentinel=arm)
        elif step == 'resume-map':
            self.current['paused'] = False
            if self.modal:
                self.current['paused'] = True
                self.current['top_exclusive_modal_choice_hint'] = {
                    'status': 'present', 'owner_verified': True,
                    'source': 'application_main_pump_observed_modal_receiver',
                    'opaque_root_id': 'synthetic-native-modal-720',
                    'max_observation_age_ms': 2000,
                }
            self._bump()
        elif step == 'pause-map':
            self.current['paused'] = True; self._bump()
        elif step == native._TACTICAL_DAILY_SENTINEL_STATUS_STEP:
            stopped = copy.deepcopy(DATA['clocks']['52']['result']['exact_day_native_clock']['stopped'])
            stopped.update(starting_date_raw=self.start_date, target_date_raw=self.target_date,
                           last_observed_date_raw=self.current['date_raw'], trigger_date_raw=self.current['date_raw'],
                           speed=self.requested_speed, signed_date_delta_from_target_raw=24 if self.overshoot else 0,
                           overshoot_days=1 if self.overshoot else 0)
            result.update(status='available', tactical_daily_sentinel=stopped)
        elif step.startswith(native._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX):
            result.update(status='canceled')
        else:
            raise AssertionError('Unexpected Native action: ' + step)
        return result


class BattleSpeedTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start(); self.addCleanup(self.environment.stop)

    def test_actual_failed_read_and_continuous_watch_admit_without_mutating_inputs(self):
        for seq in (52, 56):
            with self.subTest(seq=seq):
                s, rows = snapshot(seq), history(seq); before = copy.deepcopy((s, rows))
                self.assertTrue(ready(s, rows))
                self.assertEqual((s, rows), before)

    def test_exact_original_failure_and_successor_binding_remain_required(self):
        variants = [lambda s, rows: rows[0]['result']['native_command_result'].update(ok=True),
                    lambda s, rows: rows[0]['result']['native_request'].update(expected_revision=True),
                    lambda s, rows: s['diagnostics'].update(connection_generation=2),
                    lambda s, rows: s['played_character'].update(character_id=999),
                    lambda s, rows: s.update(episode_run_id='successor'),
                    lambda s, rows: rows.append({'command': rows[0]['command'], 'ok': True, 'result': {}}),
                    lambda s, rows: rows.append({'command': 'life-advance-one-day', 'ok': False, 'result': {}})]
        for mutate in variants:
            s, rows = snapshot(), history(); mutate(s, rows)
            self.assertFalse(ready(s, rows))

    def test_clock_modal_assault_contact_and_identity_guards_reject_fast_mode(self):
        for args in [dict(exact_one_day=False), dict(result_step='life-advance'), dict(proof_kind='battle_identity_materialization'),
                     dict(assault_in_progress=True), dict(available_action_steps=STEPS - {'set-speed-5'})]:
            self.assertFalse(ready(snapshot(), history(), **args))
        for capability in CAPS:
            self.assertFalse(ready(snapshot(), history(), bridge_capabilities=CAPS - {capability}))
        variants = [lambda s: s.update(paused=False), lambda s: s.update(active_event={'instance_id': 1}),
                    lambda s: s.update(pending_character_interaction={}),
                    lambda s: s['top_exclusive_modal_choice_hint'].update(status='unknown'),
                    lambda s: s['top_exclusive_modal_choice_hint'].update(owner_verified=False),
                    lambda s: s.update(war_objective_assault_supported=False),
                    lambda s: s['player_armies'][0].update(retreating=True),
                    lambda s: s['player_armies'][0].update(route_province_ids=[5968], move_target_province_id=5968),
                    lambda s: s['player_armies'][0].update(in_combat=False),
                    lambda s: s['player_armies'].append({**s['player_armies'][0], 'army_id': 9, 'current_province_id': 5968}),
                    lambda s: s['player_armies'].append({'army_id': 9, 'army_state': 'embarked'})]
        for mutate in variants:
            s = snapshot(); mutate(s)
            self.assertFalse(ready(s, history()))

    def test_real_life_to_native_sentinel_chain_changes_only_wall_speed_and_receipt(self):
        for seq in (52, 56):
            with self.subTest(seq=seq):
                baseline, candidate = FakeDriver(seq, candidate=False), FakeDriver(seq)
                before = baseline._execute_life_advance(expected_revision=baseline.current['revision'], exact_one_day=True,
                    result_step='life-advance-one-day', starting_snapshot=baseline.current)
                after = candidate._execute_life_advance(expected_revision=candidate.current['revision'], exact_one_day=True,
                    result_step='life-advance-one-day', starting_snapshot=candidate.current)
                self.assertEqual(before['timeline_speed'], 1)
                self.assertEqual(after['timeline_speed'], 5)
                self.assertEqual(after['timeline_policy'], 'exact_one_day_reader_unavailable_native_speed_5')
                for key in ['starting_date_raw', 'ending_date_raw', 'elapsed_days', 'requested_horizon_days',
                            'war_progress_before', 'war_progress_after', 'ordinary_events', 'event_resolution', 'paused']:
                    self.assertEqual(before[key], after[key], key)
                self.assertEqual(after['elapsed_days'], 1)
                self.assertEqual(after['exact_day_native_clock']['stopped']['overshoot_days'], 0)
                self.assertEqual(after['exact_day_native_clock']['stopped']['speed'], 5)
                self.assertEqual(candidate.native_commands.count('resume-map'), 1)
                self.assertFalse(any(s.startswith(('move-', 'retreat-', 'surrender-', 'declare-')) for s in candidate.native_commands))

    def test_real_chain_keeps_speed_one_if_fresh_watch_or_fast_capability_is_missing(self):
        for modify in [lambda d: d.steps.remove('set-speed-5'), lambda d: d._command_history.clear()]:
            driver = FakeDriver(); modify(driver)
            result = driver._execute_life_advance(expected_revision=driver.current['revision'], exact_one_day=True,
                result_step='life-advance-one-day', starting_snapshot=driver.current)
            self.assertEqual(result['timeline_speed'], 1)
            self.assertEqual(result['timeline_policy'], 'exact_one_day_unavoidable_contact')
            self.assertEqual(result['elapsed_days'], 1)

    def test_real_chain_preserves_early_modal_interrupt_and_cancels_native_deadline(self):
        driver = FakeDriver(modal=True)
        result = driver._execute_life_advance(expected_revision=driver.current['revision'], exact_one_day=True,
            result_step='life-advance-one-day', starting_snapshot=driver.current)
        self.assertEqual(result['timeline_speed'], 5)
        self.assertEqual(result['elapsed_days'], 0)
        self.assertEqual(result['progress_status'], 'modal_interrupted')
        self.assertTrue(result['exact_day_native_clock']['modal_interrupted'])
        self.assertTrue(any(s.startswith(native._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX) for s in driver.native_commands))
        self.assertFalse(any(s.startswith('event-option-') for s in driver.native_commands))

    def test_real_native_postcondition_rejects_overshoot_without_replaying_resume(self):
        driver = FakeDriver(overshoot=True)
        with self.assertRaises(native.BridgeUnavailableError):
            driver._execute_life_advance(expected_revision=driver.current['revision'], exact_one_day=True,
                result_step='life-advance-one-day', starting_snapshot=driver.current)
        self.assertEqual(driver.native_commands.count('resume-map'), 1)
        self.assertTrue(any(s.startswith(native._TACTICAL_DAILY_SENTINEL_CANCEL_PREFIX) for s in driver.native_commands))


if __name__ == '__main__': unittest.main(verbosity=2)
