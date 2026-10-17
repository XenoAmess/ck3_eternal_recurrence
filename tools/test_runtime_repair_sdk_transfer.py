from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from tools.g2_saved_campaign import runtime_repair_sdk_transfer as m
from tools.g2_saved_campaign import runtime_repair_status_v5 as v5
P = Path(__file__).parent
class TransferTests(unittest.TestCase):

    def setUp(self):
        self.data = json.loads((P / 'fixtures/repair_sdk_transfer_actual19_20.json').read_bytes())

    def transfer(self):
        return m.qualify_transfer(*(self.data[k] for k in ('state', 'active', 'old_pair', 'old_exit', 'new_pair', 'published', 'semantic', 'caps', 'freeze')))

    def proof(self, state):
        return m.transferred_progress_proof(state, *(self.data[k] for k in ('turn', 'auto', 'metrics', 'loop', 'new_pair', 'published', 'observed')))

    def test_original349_preserved_and_new_sequence2_is_not_recovery(self):
        state = self.transfer()
        self.assertEqual(state['incident_id'], self.data['state']['incident_id'])
        self.assertEqual(state['binding']['sdk_prefix'], 'p35')
        self.assertEqual(state['source_binding']['sdk_prefix'], 'p35')
        self.assertEqual(state['active_binding']['sdk_prefix'], 'p36')
        self.assertEqual(state['original_request']['sequence'], 349)
        self.assertEqual(state['repair_applied_sequence'], 2)
        self.assertEqual(state['phase'], 'repair_applied_waiting_for_progress')
        self.assertEqual(state['opened_at_utc'], self.data['state']['opened_at_utc'])
        self.assertNotIn('recovery_proof', state)

    def test_actual19_20_settled_progress_works_despite_sequence_reset(self):
        proof = self.proof(self.transfer())
        self.assertIsNotNone(proof)
        self.assertEqual(proof['auto_sequence'], 19)
        self.assertEqual(proof['actual_date_delta_raw'], 24)
        self.assertEqual(proof['actual_progress_ended_at_utc'], self.data['auto']['ended_at_utc'])

    def test_same_day_readonly_is_not_recovery(self):
        state = self.transfer()
        self.data['turn']['date_delta_raw'] = 0
        self.assertIsNone(self.proof(state))

    def test_wrong_game_exit_or_bootstrap_rejected(self):
        for key in ('game_pid', 'game_creation_filetime'):
            with self.subTest(key=key):
                data = deepcopy(self.data)
                self.data['active'][key] += 1
                with self.assertRaises(ValueError):
                    self.transfer()
                self.data = data
        self.data['old_exit']['processes'][0]['exit_code'] = 1
        with self.assertRaises(ValueError):
            self.transfer()
        self.data['old_exit']['processes'][0]['exit_code'] = 0
        self.data['caps']['result']['structured_content']['native_session_control']['driver_state_restore_kind'] = 'cold_checkpoint'
        with self.assertRaises(ValueError):
            self.transfer()

    def test_wrong_active_pair_or_connection_never_resolves(self):
        state = self.transfer()
        state['active_connection_generation'] += 1
        self.assertIsNone(self.proof(state))
        state = self.transfer()
        state['active_sdk_pair'][0]['creation_filetime'] += 1
        self.assertIsNone(self.proof(state))

class FirstRecoveryHint(unittest.TestCase):

    def test_late_current_count12944_still_resolves_original12603_19_20(self):
        data = json.loads((P / 'fixtures/repair_sdk_transfer_actual19_20.json').read_bytes())
        state = m.qualify_transfer(*(data[k] for k in ('state', 'active', 'old_pair', 'old_exit', 'new_pair', 'published', 'semantic', 'caps', 'freeze')))
        state['first_recovery_turn_hint'] = {'global_turn': 12603, 'classification': 'lookup_hint_only_not_recovery_proof'}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            queue, outbox, store = (root / n for n in ('p36-queue', 'p36-responses', 'status'))
            for path in (queue, outbox, store):
                path.mkdir()

            def put(path, value):
                path.write_text(json.dumps(value), encoding='utf-8')
            turn = deepcopy(data['turn'])
            auto_path, met_path = (outbox / '0019-1-result.json', outbox / '0020-1-result.json')
            turn.update(auto_response=str(auto_path), after_metrics_response=str(met_path))
            put(queue / 'CUMULATIVE-TURN-012603.json', turn)
            put(auto_path, data['auto'])
            put(met_path, data['metrics'])
            put(queue / 'ROOT-CUMULATIVE-LOOP-STATE.json', {**data['loop'], 'completed_cycles': 12944})
            put(root / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P36.json', data['new_pair'])
            put(root / 'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P36.json', data['published'])

            class Handle:

                def __init__(self, row):
                    self.row = row

                def identity(self, role):
                    return {**self.row, 'role': role}

                def observe(self):
                    return {'kernel_exit_observed': False}
            publisher = m.TransferPublisher.__new__(m.TransferPublisher)
            publisher.session, publisher.queue, publisher.outbox, publisher.store = (root, queue, outbox, store)
            publisher.prefix = 'p36'
            publisher._sdk_handles = [(r['role'], Handle(r)) for r in data['new_pair']['processes']]
            publisher.observe_sdk_pair = lambda: None
            emitted = []
            publisher.emit = lambda s: emitted.append(deepcopy(s))
            self.assertTrue(publisher.resolve_if_proved(state))
            proof = emitted[0]['recovery_proof']
            self.assertEqual(proof['global_turn'], 12603)
            self.assertEqual(proof['auto_sequence'], 19)
            self.assertEqual(proof['actual_progress_ended_at_utc'], data['auto']['ended_at_utc'])
            self.assertEqual(proof['cumulative_cycles'], 12944)
            self.assertEqual(emitted[0]['original_request']['sequence'], 349)

class ImportIsolation(unittest.TestCase):
    def test_import_does_not_replace_v5_proof(self):
        self.assertIs(v5.settled_progress_proof, m._base_progress)
        self.assertIsNot(v5.settled_progress_proof, m.transferred_progress_proof)

if __name__ == '__main__':
    unittest.main()
