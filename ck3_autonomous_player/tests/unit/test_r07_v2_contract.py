"""New R07-v2 boundaries; existing compiled bytes, no new native experiments."""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

R = Path(os.environ.get('E04_R07_TEST_REPO_ROOT', Path(__file__).resolve().parents[3]))
C = Path(os.environ.get('E04_R07_TEST_CANDIDATE_ROOT', R))
SCRIPT = C / 'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/r07_v2_contract.py'
SPEC = importlib.util.spec_from_file_location('r07_v2_candidate', SCRIPT)
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)
NORMALIZE = V.load_normalizer(R)
DESIGN = json.loads(SCRIPT.with_name('r07_v2_design.pending.json').read_text(encoding='utf-8'))
FIXTURE = R / 'ck3_autonomous_player/tests/unit/fixtures/war_payment_compiled_12004_a06.json'
COMPILED = {row['case']: row['value'].get(V.JOURNAL, row['value'])
            for row in json.loads(FIXTURE.read_text(encoding='utf-8'))}


def inputs():
    j = copy.deepcopy(COMPILED['controlled_window_personal'])
    s = j['current_session']; date = s['native_date_raw'] & 0xffffffff
    actor = s['player_character_full_id']
    transition = next(r for r in j['records'] if r['kind'] == 0)
    binding = dict(machine_id=j['machine_id'], pid=s['pid'],
        create_filetime=s['process_create_time_100ns'], generation=s['connection_generation'],
        actor_id=actor, unit_id=transition['before']['requested_unit_id'], episode='fixture-episode',
        payment_epoch=j['sampling']['epoch'], window_id=s['controlled_window_id'],
        segment_id='fixture-arm-segment1', date_raw=date, previous_latest_sequence=0)
    snapshot = dict(paused=True, map_ready=True, revision=s['snapshot_revision'] + 1,
        native_revision=s['snapshot_revision'], date_raw=date, episode_run_id=binding['episode'],
        played_character=dict(character_id=actor, alive=True),
        diagnostics=dict(bridge_pid=s['pid'], connection_generation=s['connection_generation'],
            hello=dict(expected_ck3_version='1.20.0.4', expected_ck3_sha256=j['executable_sha256'])))
    sp = dict(machine_id=j['machine_id'], is_error=False,
              request=dict(tool='ck3_take_snapshot', arguments={}), body=snapshot)
    response = dict(machine_id=j['machine_id'], is_error=False,
        request=dict(tool='ck3_query_war_cash_current_resources_private_v1',
            arguments=dict(payment_sampling='query', expected_revision=snapshot['revision'])),
        body={V.JOURNAL:j, 'war_payment_control_v1':dict(requested='query', accepted=True, reason='enabled'),
              'date_raw':date, 'snapshot_revision':snapshot['native_revision'],
              'current_treasury':dict(raw=999999999, scale=100000)})
    return response, sp, binding


class R07V2(unittest.TestCase):
    def test_preparation_not_runtime_or_v1_qualification(self):
        out = V.validate_design(DESIGN)
        self.assertTrue(out['design_valid_for_observation_preparation'])
        self.assertFalse(out['actual_runtime_admission'])
        self.assertFalse(out['full_v2_qualified'])
        self.assertFalse(out['original_R07_v1_qualified'])

    def test_reject_impossible_old_horizon_and_continued_treatment(self):
        for mutate in (lambda d:d['timing'].update(max_natural_days_per_arm=7),
                       lambda d:d['arms'].update(treatment='continue_existing_R0175'),
                       lambda d:d.update(original_R07_v1_qualified=True),
                       lambda d:d['army_screening'].update(event_troop_strength_is_not_assumed=False)):
            bad = copy.deepcopy(DESIGN); mutate(bad)
            with self.assertRaises(ValueError): V.validate_design(bad)

    def test_actual_compiled_positive_not_net_wallet_delta(self):
        p, s, b = inputs(); out = V.consume_window(p, s, b, NORMALIZE)
        expected = p['body'][V.JOURNAL]['qualified_boarding_debits'][0]
        self.assertEqual(out['selected_army_boarding_callbacks'][0]['requested_amount_raw'],
                         expected['requested_amount_raw'])
        self.assertFalse(out['net_treasury_difference_used'])
        self.assertFalse(out['full_v2_qualified'])
        self.assertEqual(out['maintenance_attribution'], 'unclosed')

    def test_wrong_army_keeps_actual_payment_separate(self):
        p, s, b = inputs(); b['unit_id'] += 1
        out = V.consume_window(p, s, b, NORMALIZE)
        self.assertEqual(out['selected_army_boarding_callbacks'], [])
        self.assertEqual(len(out['other_army_boarding_callbacks']), 1)
        self.assertFalse(out['observed_empty_is_free_boarding'])

    def test_other_actor_source_and_window_rejected(self):
        for key in ('actor_id', 'pid', 'create_filetime', 'generation', 'window_id', 'payment_epoch'):
            p, s, b = inputs(); b[key] += 1
            with self.assertRaises(ValueError, msg=key): V.consume_window(p, s, b, NORMALIZE)
        p, s, b = inputs(); b['machine_id'] = 'other-machine'
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)
        p, s, b = inputs(); p['body'][V.JOURNAL]['executable_sha256'] = '0' * 64
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)

    def test_partial_and_sequence_rollback_not_zero(self):
        p, s, b = inputs(); j = p['body'][V.JOURNAL]
        j.update(read_complete=False, records=[], qualified_boarding_debits=[])
        j['sampling'].update(busy=True, active_captures=1)
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)
        p, s, b = inputs(); b['previous_latest_sequence'] = p['body'][V.JOURNAL]['latest_sequence'] + 1
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)
        p, s, b = inputs(); p['body'][V.JOURNAL]['latest_sequence'] = (1 << 64) - 1
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)

    def test_new_segment_does_not_reuse_previous_sequence(self):
        p, s, b = inputs(); out = V.consume_window(p, s, b, NORMALIZE)
        b['previous_latest_sequence'] = out['latest_sequence']
        out2 = V.consume_window(p, s, b, NORMALIZE)
        self.assertEqual(out2['selected_army_boarding_callbacks'], [])
        # An actual other window cannot be rebound merely by renaming a segment.
        b['segment_id'] = 'segment2'; b['window_id'] += 1
        with self.assertRaises(ValueError): V.consume_window(p, s, b, NORMALIZE)

    def test_storage_high32_preserved_not_called_date(self):
        p, s, b = inputs(); j = p['body'][V.JOURNAL]
        j['current_session']['native_date_raw'] |= 7 << 32
        out = V.consume_window(p, s, b, NORMALIZE)
        self.assertEqual(out['native_date_storage_u64_raw'], j['current_session']['native_date_raw'])
        self.assertEqual(out['native_date_i32_low32'], b['date_raw'])
        self.assertTrue(out['native_date_high32_is_not_a_date'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
