import copy
import importlib.util
import json
from pathlib import Path
import unittest

P = Path(__file__).parent
from tools.g2_saved_campaign import runtime_repair_status_v5 as module


class SettledPairTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((P / 'fixtures/repair_status_settled_actual252_253.json').read_bytes())

    def proof(self):
        return module.settled_progress_proof(*(self.data[key] for key in
            ('state', 'turn', 'auto', 'metrics', 'loop', 'pair', 'published', 'observed_pair')))

    def test_actual_first_progress_without_full_or_extra_sem(self):
        proof = self.proof()
        self.assertIsNotNone(proof)
        self.assertEqual(proof['actual_date_delta_raw'], 24)
        self.assertEqual(proof['auto_sequence'], 252)
        self.assertEqual(proof['actual_progress_ended_at_utc'], '2026-10-17T03:56:03.699725+00:00')
        self.assertFalse(proof['extra_SEM_or_completed_FULL_required'])

    def test_unsettled_or_unpaired_does_not_resolve(self):
        for field, value in [('stage', 'auto_submitted'), ('date_delta_raw', 0), ('global_turn', 12552)]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.data)
                self.data['turn'][field] = value
                self.assertIsNone(self.proof())
                self.data = original
        self.data['metrics']['request']['sequence'] += 2
        self.assertIsNone(self.proof())

    def test_reconsume_or_wrong_game_not_progress(self):
        self.data['state']['repair_applied_sequence'] = 252
        self.assertIsNone(self.proof())
        self.data['state']['repair_applied_sequence'] = 249
        self.data['state']['binding']['game_pid'] += 1
        self.assertIsNone(self.proof())

    def test_exact_birth_and_kernel_exit(self):
        self.data['observed_pair'][0]['creation_filetime'] += 1
        self.assertIsNone(self.proof())
        self.data['observed_pair'][0]['creation_filetime'] -= 1
        self.data['observed_pair'][0]['kernel_exit_observed'] = True
        self.assertIsNone(self.proof())

    def test_ack_query_and_connection_mismatch_rejected(self):
        self.data['auto']['request']['tool'] = 'root_current_runtime_metrics'
        self.assertIsNone(self.proof())
        self.data['auto']['request']['tool'] = 'ck3_auto_turn'
        body = module.core.decode(self.data['metrics'])
        body['connection_generation'] += 1
        self.data['metrics']['result'] = {'structured_content': body}
        self.assertIsNone(self.proof())

    def test_actual_blocked_reason_is_not_native_error(self):
        brief, evidence = module.diagnostic_reason(self.data['blocked'])
        self.assertEqual(brief, '\u6218\u540e\u4fdd\u62a4\u7b56\u7565\u6ca1\u6709\u9009\u51fa\u540e\u7eed\u884c\u52a8')
        self.assertFalse(evidence['Native_error_inferred'])
        self.assertFalse(evidence['business_action_inferred'])
        wrong = copy.deepcopy(self.data['blocked'])
        body = module.core.decode(wrong)
        body['plan']['phase'] = 'other_phase'
        wrong['result'] = {'structured_content': body}
        self.assertIsNone(module.diagnostic_reason(wrong))

    def test_public_reason_override_preserves_the_v4_module_function(self):
        self.assertIsNone(module.v4.diagnostic_reason(self.data['blocked']))
        publisher = module.SettledPairPublisher.__new__(module.SettledPairPublisher)
        self.assertEqual(publisher.diagnose(self.data['blocked']),
                         module.diagnostic_reason(self.data['blocked']))

if __name__ == '__main__':
    unittest.main()
