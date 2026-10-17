"""Public renderer consumes status metadata; no live overlay or desktop calls."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from tools.g2_saved_campaign.runtime_repair_overlay_view import repair_banner


class RepairBannerTests(unittest.TestCase):
    def test_repairing_and_verified_resumed_banner_expire(self):
        now = datetime.now(timezone.utc)
        session = Path(__file__).parent
        state = {'schema': 'xar.runtime-repair-status/v1', 'phase': 'repairing',
                 'binding': {'session': str(session), 'game_pid': 101, 'game_creation_filetime': 202},
                 'pause_reason': '结果校验失败', 'repair_message': '校验已修复'}
        kwargs = dict(session=session, game_pid=101, game_creation_filetime=202, now=now)
        self.assertIn('正在修复中', repair_banner(state, **kwargs))
        state.update(phase='resolved', expires_at_utc=(now + timedelta(seconds=30)).isoformat())
        self.assertEqual(repair_banner(state, **kwargs), '')
        state['recovery_proof'] = {'actual_new_progress': True}
        self.assertIn('已恢复推进', repair_banner(state, **kwargs))
        self.assertEqual(repair_banner(state, **{**kwargs, 'now': now + timedelta(seconds=31)}), '')
        self.assertEqual(repair_banner(state, **{**kwargs, 'game_creation_filetime': 303}), '')


if __name__ == '__main__':
    unittest.main()
