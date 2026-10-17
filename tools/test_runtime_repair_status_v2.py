"""Portable tests: only temporary files, immutable DTOs and fake clocks."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import runtime_repair_status_v2 as status


def write(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row), encoding='utf-8')


class IncrementalStatusTests(unittest.TestCase):
    def test_real_content_json_shape(self):
        row = {'result': {'is_error': False, 'content': [
            {'type': 'text', 'text': '{"selected_step":"life-advance-one-day","status":"executed"}'}]}}
        self.assertEqual(status.decode(row)['selected_step'], 'life-advance-one-day')
        row['result']['is_error'] = True
        self.assertIsNone(status.decode(row))

    def test_incremental_cursor_no_directory_glob_or_repeat_json_reads(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            write(root / 'NEXT-SEQUENCE-P35.json', {'next_sequence': 72})
            write(root / 'p35-requests/0070-1-result.json', {'sequence': 70, 'command': 'full_loop'})
            write(root / 'p35-responses/0071-1-result.json', {'request': {'sequence': 71}, 'result': {
                'is_error': False, 'content': [{'type': 'text', 'text': '{"selected_step":"life-advance-one-day"}'}]}})
            index = status.ReceiptIndex(root, 'p35', window=16)
            with patch.object(Path, 'glob', side_effect=RuntimeError('directory glob forbidden')):
                index.refresh()
                self.assertEqual(index.latest_actual[0]['summary'], 'life-advance-one-day')
                reads = index.reads
                for _ in range(10):
                    index.refresh()
                self.assertEqual(index.reads, reads)
                write(root / 'NEXT-SEQUENCE-P35.json', {'next_sequence': 73})
                write(root / 'p35-responses/0072-1-result.json', {'result': {
                    'structured_content': {'selected_step': 'query-declarable-wars'}}})
                index.refresh()
                self.assertEqual(index.latest_actual[0]['summary'], 'query-declarable-wars')

    def test_late_parent_full_is_observed_without_cursor_change(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            write(root / 'NEXT-SEQUENCE-P35.json', {'next_sequence': 72})
            write(root / 'p35-requests/0060-1-result.json', {'sequence': 60, 'command': 'full_loop'})
            index = status.ReceiptIndex(root, 'p35', window=16)
            index.refresh()
            self.assertIn(60, index.important_pending)
            path = root / 'p35-responses/0060-1-result.json'
            write(path, {'request': {'sequence': 60, 'command': 'full_loop'}, 'result': {
                'structured_content': {'status': 'bounded_loop_finished', 'actual_turns': 6}}})
            index.refresh()
            self.assertIn(path, index.response_paths())
            self.assertNotIn(60, index.important_pending)

    def test_latest_receipt_order_remains_numeric_past_four_digits(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            write(root / 'NEXT-SEQUENCE-P35.json', {'next_sequence': 10001})
            for number in (9999, 10000):
                write(root / f'p35-responses/{number:04d}-1-result.json', {
                    'result': {'structured_content': {'selected_step': f'actual-{number}'}}})
            index = status.ReceiptIndex(root, 'p35', window=3)
            self.assertEqual(index.response_paths()[0].name, '10000-1-result.json')
            self.assertEqual(index.latest_actual[0]['summary'], 'actual-10000')

    def test_actual_progress_projection_and_ack_negative(self):
        fixture = json.loads((Path(__file__).with_name('fixtures') / 'repair_status_actual37_40.json').read_bytes())
        proof = status.core.recovery_proof(fixture['state'], fixture['semantic'], fixture['batch'])
        self.assertEqual(proof['actual_end_date_raw'], 53483088)
        batch = json.loads(json.dumps(fixture['batch']))
        batch['result']['structured_content']['actual_end_date_raw'] = 53483064
        self.assertIsNone(status.core.recovery_proof(fixture['state'], fixture['semantic'], batch))
        state = json.loads(json.dumps(fixture['state']))
        state['phase'] = 'repairing'
        self.assertIsNone(status.core.recovery_proof(state, fixture['semantic'], fixture['batch']))

    def test_ttl_uses_monotonic_clock_after_first_binding(self):
        publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
        publisher._deadline_incident = publisher._deadline = None
        publisher.latest_decision = lambda: (None, None)
        publisher.store, publisher.current = Path('unused'), Path('unused/current')
        fixed = datetime(2026, 10, 17, tzinfo=timezone.utc)
        state = {'phase': 'resolved', 'incident_id': 'test',
                 'expires_at_utc': (fixed + timedelta(seconds=30)).isoformat()}
        with patch.object(status.core, 'utc', return_value=fixed), \
                patch.object(status.core, 'atomic') as atomic:
            with patch.object(status.time, 'monotonic', return_value=100):
                self.assertFalse(publisher.expire(state))
            with patch.object(status.time, 'monotonic', return_value=131):
                self.assertTrue(publisher.expire(state))
            self.assertEqual(state['phase'], 'expired')
            self.assertTrue(state['monotonic_ttl_elapsed'])
            self.assertEqual(atomic.call_count, 2)

    def test_sdk_exact_handle_exit_is_reported_without_process_scan(self):
        class FakeHandle:
            def identity(self, role):
                return {'role': role, 'pid': 17, 'creation_filetime': 123}
            def observe(self):
                return {'kernel_exit_observed': True, 'exit_code': 1}
        with tempfile.TemporaryDirectory() as root:
            publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
            publisher.session, publisher.store = Path(root), Path(root) / 'status'
            publisher.prefix, publisher.binding = 'p35', {'game_pid': 263980}
            publisher._sdk_handles = [('sdk_queue', FakeHandle())]
            publisher._sdk_capture_error, publisher._sdk_failure_reported = None, False
            write(Path(root) / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P35.json', {'actual_fixture': True})
            incidents = []
            publisher.open_source_incident = lambda *args: incidents.append(args)
            with patch.object(Path, 'glob', side_effect=RuntimeError('scan forbidden')):
                publisher.observe_sdk_pair()
                publisher.observe_sdk_pair()
            self.assertEqual(len(incidents), 1)
            proof = json.loads(incidents[0][0].read_bytes())
            self.assertTrue(proof['observed_processes'][0]['kernel_exit_observed'])
            self.assertEqual(proof['process_mutation_calls'], 0)

    def test_public_custody_import_captures_only_the_published_pair(self):
        from tools.g2_saved_campaign import sdk_process_custody
        class FakeHandle:
            def identity(self, role):
                return {'role': role}
            def observe(self):
                return {'kernel_exit_observed': False}
        with tempfile.TemporaryDirectory() as root:
            publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
            publisher.session, publisher.store = Path(root), Path(root) / 'status'
            publisher.prefix, publisher.binding = 'p35', {'game_pid': 303}
            publisher._sdk_handles = None
            publisher._sdk_capture_error, publisher._sdk_failure_reported = None, False
            write(Path(root) / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P35.json', {
                'status': 'SDK_PAIR_HANDLES_RETAINED', 'processes': [
                    {'role': role, 'pid': pid, 'creation_filetime': birth, 'executable': 'synthetic.exe'}
                    for role, pid, birth in [('sdk_queue', 101, 201), ('sdk_application', 102, 202)]]})
            with patch.object(sdk_process_custody.RetainedProcessGeneration, 'capture',
                              side_effect=[FakeHandle(), FakeHandle()]) as capture:
                publisher.observe_sdk_pair()
                publisher.observe_sdk_pair()
            self.assertEqual(capture.call_count, 2)
            self.assertEqual([call.args[0] for call in capture.call_args_list], [101, 102])
            self.assertEqual([call.kwargs['expected_creation_filetime']
                              for call in capture.call_args_list], [201, 202])

    def test_capture_only_wait_does_not_falsely_claim_gameplay_halt(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
            publisher.session, publisher.prefix = root, 'p35'
            publisher._recording_signature = None
            publisher.state = lambda: None
            incidents = []
            publisher.open_source_incident = lambda *args: incidents.append(args)
            health = root / 'automatic-recording-recovery-p35/STATUS.json'
            write(health, {'status': 'waiting_segment', 'at_utc': 'one'})
            publisher.observe_recording_pause()
            self.assertEqual(incidents, [])
            write(root / 'ROOT-CONTINUOUS-FEEDER-STOP-P35', {'reason': 'automatic_recording_recovery'})
            write(health, {'status': 'waiting_segment', 'at_utc': 'two'})
            publisher.observe_recording_pause()
            self.assertEqual(len(incidents), 1)
            self.assertEqual(incidents[0][2], 'actual_recording_recovery_and_feeder_pause')


    def test_recording_pause_refreshes_independent_retained_receipts(self):
        sources = (
            ('ROOT-CURRENT-HALT-P35.json', {'retained_fixture': True}),
            ('ROOT-CONTINUOUS-FEEDER-STOP-P35', {'reason': 'automatic_recording_recovery'}),
            ('ROOT-CONTINUOUS-FEEDER-STATUS-P35.json', {'status': 'operator_stopped'}),
        )
        for name, row in sources:
            with self.subTest(source=name), tempfile.TemporaryDirectory() as root:
                root = Path(root)
                publisher = status.IncrementalPublisher.__new__(status.IncrementalPublisher)
                publisher.session, publisher.prefix = root, 'p35'
                publisher._recording_signature = None
                publisher.state = lambda: None
                incidents = []
                publisher.open_source_incident = lambda *args: incidents.append(args)
                health = root / 'automatic-recording-recovery-p35/STATUS.json'
                write(health, {'status': 'waiting_segment'})
                health_signature = status.signature(health)
                with patch.object(status.core, 'read', wraps=status.core.read) as read:
                    publisher.observe_recording_pause()
                    self.assertEqual(incidents, [])
                    write(root / name, row)
                    self.assertEqual(status.signature(health), health_signature)
                    publisher.observe_recording_pause()
                    self.assertEqual(len(incidents), 1)
                    self.assertEqual(incidents[0][2],
                                     'actual_recording_recovery_and_feeder_pause')
                    reads = read.call_count
                    publisher.observe_recording_pause()
                    self.assertEqual(len(incidents), 1)
                    self.assertEqual(read.call_count, reads)



if __name__ == '__main__':
    unittest.main()
