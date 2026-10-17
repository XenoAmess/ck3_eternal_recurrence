"""Offline status/rendering/recovery tests; no Game/OBS/Desktop operations."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import importlib.util
from pathlib import Path
import unittest

from tools.g2_saved_campaign import runtime_repair_status as repair

R = Path(__file__).resolve().parent
from tools.g2_saved_campaign import live_decision_overlay as overlay


class RepairStatusTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.state = {'schema': repair.SCHEMA, 'incident_id': 'synthetic-test',
            'binding': {'session': str(R), 'game_pid': 263980, 'game_creation_filetime': 134366781612159835,
                        'sdk_prefix': 'p35'},
            'phase': 'repair_applied_waiting_for_progress', 'pause_reason': '静止军队停表结果校验误拒',
            'repair_message': '已修复静止军队结果校验',
            'repair_applied_at_utc': self.now.isoformat(),
            'observed_frame': {'date_raw': 53483064, 'actor_character_id': 39979,
                               'episode_run_id': 'native-39979-5ee2d59fcb51'},
            'last_decision': {'summary': 'life-advance-one-day'}, 'expires_at_utc': None}
        self.semantic = {'ended_at_utc': (self.now + timedelta(seconds=1)).isoformat(),
            'request': {'tool': repair.SEMANTIC_TOOL}, 'result': {'is_error': False,
            'structured_content': {'date_raw': 53483088, 'paused': True, 'map_ready': True,
                'played_character': {'character_id': 39979, 'alive': True},
                'episode_run_id': 'native-39979-5ee2d59fcb51', 'diagnostics': {'bridge_pid': 263980}}}}
        self.batch = {'ended_at_utc': (self.now + timedelta(seconds=2)).isoformat(),
            'request': {'command': 'full_loop', 'arguments': {'max_turns': 1}},
            'result': {'is_error': False, 'structured_content': {
                'status': 'bounded_loop_finished', 'actual_turns': 1,
                'actual_end_date_raw': 53483088, 'cumulative_cycles': 12455}}}

    def test_actual_current_overlay_repairs_without_fake_mcp(self):
        row = repair.status_relay(self.state, self.now)
        envelope, body = overlay.decode(row)
        self.assertEqual(envelope, {})
        self.assertEqual(body, {})
        self.assertIn('正在修复中', row['client_error'])
        self.assertIn('最近决策', row['client_error'])
        self.assertEqual(row['request']['tool'], repair.TOOL)
        self.assertFalse(row['root_runtime_repair_status']['Game_action_submitted'])

    def test_actual_current_overlay_resolved_metadata(self):
        self.state['phase'] = 'resolved'
        row = repair.status_relay(self.state, self.now)
        _, body = overlay.decode(row)
        self.assertEqual(overlay.action_name(body['step']), '修复状态')
        self.assertEqual(overlay.outcome_text(body), '已恢复推进')
        self.assertIn('已修复静止军队结果校验', overlay.war_reason(body['plan']))
        self.assertIn('最近决策', overlay.war_reason(body['plan']))
        self.assertFalse(body['business_action'])
        self.assertEqual(body['new_business_credit'], 0)

    def test_real_progress_positive(self):
        proof = repair.recovery_proof(self.state, self.semantic, self.batch)
        self.assertEqual(proof['actual_end_date_raw'], 53483088)
        self.assertEqual(proof['new_Game_calls_by_status_sidecar'], 0)

    def test_patch_ack_and_same_day_cannot_resolve(self):
        state = deepcopy(self.state)
        state['phase'] = 'repairing'
        self.assertIsNone(repair.recovery_proof(state, self.semantic, self.batch))
        batch = deepcopy(self.batch)
        batch['result']['structured_content']['actual_end_date_raw'] = 53483064
        self.assertIsNone(repair.recovery_proof(self.state, self.semantic, batch))

    def test_failure_wrong_pid_actor_episode_and_stale_sem_rejected(self):
        for field, value in [('pid', 1), ('actor', 1), ('episode', 'other'), ('stale', None), ('error', None)]:
            sem, batch = deepcopy(self.semantic), deepcopy(self.batch)
            body = sem['result']['structured_content']
            if field == 'pid': body['diagnostics']['bridge_pid'] = value
            elif field == 'actor': body['played_character']['character_id'] = value
            elif field == 'episode': body['episode_run_id'] = value
            elif field == 'stale': sem['ended_at_utc'] = (self.now - timedelta(seconds=1)).isoformat()
            else: batch['result']['is_error'] = True
            with self.subTest(field=field):
                self.assertIsNone(repair.recovery_proof(self.state, sem, batch))


if __name__ == '__main__':
    unittest.main()
