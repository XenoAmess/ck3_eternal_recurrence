"""Actual AUTO247 diagnostic + portable same-incident refinement tests."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from tools.g2_saved_campaign import runtime_repair_status_v4 as status


class ReasonTests(unittest.TestCase):
    def setUp(self):
        self.row = json.loads((Path(__file__).with_name('fixtures') / 'campaign_root_paused_boundary_actual247.json').read_bytes())['row']

    def test_actual247_known_cause_is_short_chinese(self):
        reason, evidence = status.diagnostic_reason(self.row)
        self.assertEqual(reason, '暂停读取边界未就绪，自动推进暂停')
        self.assertEqual(evidence['native_error'], 'paused application-main boundary is not ready')
        self.assertEqual(evidence['native_step'], 'query-campaign-root-context-v1')

    def test_unknown_native_error_preserves_raw_text(self):
        row = deepcopy(self.row)
        rejection = row['result']['structured_content']['diagnostics']['native_command_rejection']
        rejection['native_error'] = 'unrecognized backend failure'
        reason, evidence = status.diagnostic_reason(row)
        self.assertIn('unrecognized backend failure', reason)
        self.assertEqual(evidence['mapping'], 'unknown_native_error_preserved')
        row['result']['is_error'] = False
        self.assertIsNone(status.diagnostic_reason(row))

    def test_same_incident_and_credit_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            publisher = status.ReasonPublisher.__new__(status.ReasonPublisher)
            publisher.session, publisher.store, publisher.outbox = root, root / 'status', root / 'p35-responses'
            publisher.current, publisher.binding = publisher.store / 'CURRENT.json', {'game_pid': 263980}
            auto = publisher.outbox / '0247-1-result.json'
            status.core.atomic(auto, self.row)
            halt = root / 'p35-queue/ROOT-REQUEST-HALTED-0210.json'
            status.core.atomic(halt, {'original_response': str(auto)})
            state = {'schema': status.core.SCHEMA, 'binding': publisher.binding,
                'incident_id': 'same-original-incident', 'phase': 'repairing',
                'pause_reason': 'generic SDK error', 'halt_receipt': status.core.pin(halt),
                'original_request': self.row['request'], 'business_credit': 0,
                'preserved_completed_cycles': 12454}
            status.core.atomic(publisher.current, state)
            publisher.state = lambda: status.core.read(publisher.current)
            def emit(updated):
                status.core.atomic(publisher.current, updated, replace=True)
                return {'source': 'fake display file boundary'}
            publisher.emit = emit
            result = publisher.refine_current()
            after = publisher.state()
            self.assertEqual(after['incident_id'], state['incident_id'])
            self.assertEqual(after['phase'], state['phase'])
            self.assertEqual(after['preserved_completed_cycles'], 12454)
            self.assertEqual(after['business_credit'], 0)
            self.assertFalse(result['new_incident_created'])
            self.assertTrue(Path(after['reason_refinement']['path']).is_file())
            again = publisher.refine_current()
            self.assertEqual(again['status'], 'SAME_INCIDENT_REASON_ALREADY_REFINED')

    def test_record_waiting_alone_has_no_native_rejection(self):
        self.assertIsNone(status.diagnostic_reason({'status': 'waiting_segment'}))


if __name__ == '__main__':
    unittest.main()
