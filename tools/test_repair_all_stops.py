"""Portable missing-pending/typed-blocked stop tests, no runtime APIs."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy
import json

from tools.g2_saved_campaign import runtime_repair_status_v2_all_stops as status


class StopCoverageTests(unittest.TestCase):
    def test_reconsumed_failed_clock_day_is_not_new_progress(self):
        fixture = json.loads((Path(__file__).with_name('fixtures') /
                              'repair_status_actual37_40.json').read_bytes())
        state = deepcopy(fixture['state'])
        state['resume_baseline_confirmed'] = False
        publisher = status.AllStopsPublisher.__new__(status.AllStopsPublisher)
        publisher.latest_semantic = lambda: (
            None, fixture['semantic'], status.core.semantic(fixture['semantic'], state['binding']))
        with patch.object(status.core, 'pin', return_value={'source': 'synthetic'}), \
                patch.object(status.core, 'atomic'):
            publisher.current = Path('unused')
            self.assertFalse(publisher.resolve_if_proved(state))
        self.assertTrue(state['resume_baseline_confirmed'])
        # Merely establishing the paused post-failure baseline cannot resolve.
        self.assertIsNone(status.core.recovery_proof(state, fixture['semantic'], fixture['batch']))

    def test_typed_blocked_full_with_real_feeder_stop(self):
        feeder = {'status': 'halted_review_required', 'control_sequence': 30}
        response = {'request': {'sequence': 30, 'command': 'full_loop'},
                    'result': {'is_error': False, 'structured_content': {'status': 'blocked'}}}
        self.assertIsNotNone(status.feeder_stopped(feeder, response))
        feeder['status'] = 'following_actual_control'
        self.assertIsNone(status.feeder_stopped(feeder, response))

    def test_summary_failure_without_pending_preserves_actual_request(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            publisher = status.AllStopsPublisher.__new__(status.AllStopsPublisher)
            publisher.session, publisher.queue, publisher.outbox = root, root / 'p35-queue', root / 'p35-responses'
            publisher.store, publisher.binding = root / 'status', {'game_pid': 263980}
            publisher.index = type('Index', (), {'full_sequences': [30]})()
            publisher.state = lambda: None
            publisher.latest_semantic = lambda: (None, None, {'date_raw': 53483088})
            emitted = []
            publisher.emit = lambda state: emitted.append(state)
            original = {'sequence': 32, 'tool': 'root_current_runtime_metrics'}
            status.core.atomic(publisher.queue / 'ROOT-REQUEST-HALTED-0030.json', {
                'original_request': original, 'message': "KeyError: 'start_date_raw'"})
            status.core.atomic(publisher.outbox / '0030-1-result.json', {
                'request': {'sequence': 30, 'command': 'full_loop'}, 'client_error': "KeyError: 'start_date_raw'"})
            with patch.object(status.v2.IncrementalPublisher, 'observe_halt', return_value=None), \
                    patch.object(Path, 'glob', side_effect=RuntimeError('directory scan forbidden')):
                publisher.observe_halt()
            self.assertEqual(len(emitted), 1)
            self.assertEqual(emitted[0]['original_request'], original)
            self.assertEqual(emitted[0]['source_kind'], 'actual_queue_exception_after_or_without_pending')
            self.assertEqual(emitted[0]['business_credit'], 0)


if __name__ == '__main__':
    unittest.main()
