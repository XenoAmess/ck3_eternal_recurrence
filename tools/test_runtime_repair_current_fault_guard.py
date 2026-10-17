from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.g2_saved_campaign import runtime_repair_current_fault_guard as m

FIXTURE = Path(__file__).with_name('fixtures') / 'repair_false_stops_actual1875.json'


def actual():
    return json.loads(FIXTURE.read_bytes())['body']


class CurrentFaultQualification(unittest.TestCase):
    def test_original_historical_full_does_not_stop_current_following_control(self):
        halt = actual()['original_halt']
        self.assertFalse(m.current_queue_stop(halt, {'pending_cycle': {'auto_sequence': 2362}},
            {'status': 'following_actual_control', 'control_sequence': 2327}, 1836))

    def test_current_matching_pending_halt_qualifies(self):
        halt = actual()['original_halt']
        number = halt['original_request']['sequence']
        self.assertTrue(m.current_queue_stop(halt, {'pending_cycle': {'auto_sequence': number}}, {}, 1836))
        self.assertFalse(m.current_queue_stop(halt, {'pending_cycle': {'auto_sequence': number}}, {}, 1836,
                                             terminal=True))
        self.assertFalse(m.current_queue_stop(halt, {'pending_cycle': {'auto_sequence': number}}, {}, 1836,
                                             recovered=True))

    def test_no_pending_summary_error_requires_current_exact_stopped_full(self):
        halt = actual()['original_halt']
        feeder = {'status': 'halted_review_required', 'control_sequence': 1836}
        self.assertTrue(m.current_queue_stop(halt, {}, feeder, 1836))
        self.assertFalse(m.current_queue_stop(halt, {}, feeder, 1820))
        self.assertFalse(m.current_queue_stop(halt, {}, {'status': 'following_actual_control',
                                                        'control_sequence': 1836}, 1836))

    def prepare_host(self, root):
        value = actual()
        for name in ('p36-queue', 'p36-responses', 'status', 'responses'):
            (root / name).mkdir()
        queue, outbox, store = root / 'p36-queue', root / 'p36-responses', root / 'status'
        def put(path, row): path.write_text(json.dumps(row), encoding='utf-8')
        original = json.loads(FIXTURE.with_name('repair_readonly_actual1875_1911.json').read_bytes())['original']
        original_path = outbox / '1875-1-result.json'
        put(original_path, original)
        halt = value['original_halt']
        halt['original_response'] = str(original_path)
        halt_path = queue / 'ROOT-REQUEST-HALTED-1836.json'
        put(halt_path, halt)
        for key in ('queue_reopened', 'prior_resolved'):
            value[key]['binding']['session'] = str(root)
            value[key]['halt_receipt'] = m.core.pin(halt_path)
        put(store / 'actual-RESOLVED-SETTLED-PAIR.json', value['prior_resolved'])
        audit = value['old_recovery_audit']
        audit['original_response'] = str(original_path)
        put(queue / 'READONLY-PRECONDITION-RECOVERY-1876.json', audit)
        put(outbox / '1876-1-result.json', value['old_recovery'])
        loop = {'pending_cycle': {'auto_sequence': 2362}}
        feeder = {'status': 'following_actual_control', 'control_sequence': 2327}
        loop_path, feeder_path = root / 'loop.json', root / 'feeder.json'
        put(loop_path, loop)
        put(feeder_path, feeder)
        publisher = m.CurrentFaultPublisher.__new__(m.CurrentFaultPublisher)
        publisher.session, publisher.queue, publisher.outbox, publisher.store = root, queue, outbox, store
        publisher.prefix, publisher.binding = 'p36', value['queue_reopened']['binding']
        publisher.current = store / 'CURRENT.json'
        state = value['queue_reopened']
        put(publisher.current, state)
        publisher.state = lambda: state
        publisher.small_inputs = lambda: (loop, feeder, loop_path, feeder_path)
        return publisher, halt_path, state

    def test_terminal_cache_reloads_exact_fault_and_retains_sdk_namespace(self):
        with tempfile.TemporaryDirectory() as folder:
            publisher, halt_path, _ = self.prepare_host(Path(folder))
            identity, halt = publisher.identity_for_halt(halt_path)
            self.assertIn(m.fingerprint(identity), publisher.terminal_faults())
            other = {**identity, 'sdk_prefix': 'different-generation'}
            self.assertNotEqual(m.fingerprint(identity), m.fingerprint(other))
            publisher.store = Path(folder) / 'not-a-directory'
            self.assertIn(m.fingerprint(identity), publisher.terminal_faults())
            publisher.qualification = lambda *args: (False, {})
            publisher.state = lambda: self.fail('Historical opener entered')
            self.assertIsNone(publisher._open_exact(halt_path, halt['original_request'], 'old', 'old'))

    def test_withdrawal_preserves_false_state_and_grants_no_recovery_or_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            publisher, halt_path, state = self.prepare_host(root)
            original = publisher.current.read_bytes()
            publisher.latest_decision = lambda: ({'source': {'path': 'synthetic-display-source', 'sha256': '0'*64}},
                {'tool': 'ck3_auto_turn', 'result': {'structured_content': {
                    'status': 'planned', 'selected_step': 'life-advance', 'plan': {'phase': 'ordinary'}}}})
            result = publisher.retract_stale_queue_incident()
            self.assertFalse(result['recovery_claimed'])
            self.assertFalse(result['EDL_wait_interval_allowed'])
            self.assertTrue(state['withdrawal_is_not_recovery'])
            self.assertNotIn('recovery_proof', state)
            self.assertEqual(next(publisher.store.glob('*CURRENT-BEFORE.json')).read_bytes(), original)
            audit = json.loads(next(publisher.store.glob('*WITHDRAWN.json')).read_bytes())
            self.assertEqual(audit['new_business_credit'], 0)
            self.assertTrue(audit['normal_gameplay_must_not_be_compressed'])
            self.assertEqual(len(list((root / 'responses').glob('*WITHDRAWN.json'))), 1)


class RecordingEvidence(unittest.TestCase):
    def test_capture_health_needs_current_pending_or_operator_stopped_feeder(self):
        halt = actual()['original_halt']
        health, feeder = {'status': 'blocked'}, {'status': 'following_actual_control'}
        self.assertIsNone(m.record.current_recording_pause(health, feeder, None, {}, halt))
        pending = {'pending_cycle': {'auto_sequence': halt['original_request']['sequence']}}
        self.assertTrue(m.record.current_recording_pause(health, feeder, None, pending, halt)[
            'current_matching_unrecovered_pending_halt'])
        self.assertIsNone(m.record.current_recording_pause(health, feeder, None, pending, halt, True))
        stop = {'reason': 'automatic_recording_recovery'}
        self.assertIsNone(m.record.current_recording_pause(health, feeder, stop, {}, halt, True))
        self.assertTrue(m.record.current_recording_pause(health, {'status': 'operator_stopped'}, stop, {}, halt,
            True)['current_operator_stopped_with_recording_stop_marker'])

    def test_unchanged_health_does_not_hide_late_feeder_stop_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            queue, health_root = root / 'p36-queue', root / 'automatic-recording-recovery-p36'
            queue.mkdir(); health_root.mkdir()
            def put(path, row): path.write_text(json.dumps(row), encoding='utf-8')
            put(health_root / 'STATUS.json', {'status': 'waiting_frame'})
            put(queue / 'ROOT-CUMULATIVE-LOOP-STATE.json', {'pending_cycle': None})
            feeder = root / 'ROOT-CONTINUOUS-FEEDER-STATUS-P36.json'
            put(feeder, {'status': 'following_actual_control'})
            publisher = m.record.RecordingGuardPublisher.__new__(m.record.RecordingGuardPublisher)
            publisher.session, publisher.queue, publisher.prefix = root, queue, 'p36'
            publisher.state = lambda: {'phase': 'expired'}
            opened = []
            publisher.open_source_incident = lambda *args: opened.append(args)
            publisher.observe_recording_pause()
            self.assertEqual(opened, [])
            put(feeder, {'status': 'operator_stopped'})
            put(root / 'ROOT-CONTINUOUS-FEEDER-STOP-P36', {'reason': 'automatic_recording_recovery'})
            publisher.observe_recording_pause()
            self.assertEqual(len(opened), 1)


if __name__ == '__main__':
    unittest.main()
