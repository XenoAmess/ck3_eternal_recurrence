from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import runtime_repair_auto_applied as m

FIXTURE = Path(__file__).with_name('fixtures') / 'repair_readonly_actual1875_1911.json'


def data():
    return json.loads(FIXTURE.read_bytes())


def applied(value):
    return m.applied_proof(*(value[k] for k in
        ('state', 'halt', 'original', 'response', 'audit', 'semantic')))


class AutomaticApplied(unittest.TestCase):
    def test_actual_readonly_control_marks_applied_and_requires_new_progress(self):
        proof = applied(data())
        self.assertEqual(proof['repair_sequence'], 1876)
        self.assertEqual(proof['first_candidate_settled_turn'], 13510)
        self.assertFalse(proof['recovery_claimed'])
        self.assertFalse(proof['original_AUTO_replayed'])

    def test_replay_credit_wrong_game_request_and_counts_reject(self):
        mutations = (
            lambda v: v['audit'].update(original_auto_replayed=True),
            lambda v: v['audit'].update(gameplay_actions_submitted=1),
            lambda v: v['audit']['same_game'].update(pid=1),
            lambda v: v['audit']['original_request'].update(sequence=1),
            lambda v: v['audit'].update(completed_cycles_before_after=1),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = data()
                mutate(value)
                self.assertIsNone(applied(value))

    def test_dedicated_large_envelope_preserves_ordinary_metadata_bound(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'clock.json'
            value = data()['auto']
            # Actual clock fields; only the large repeated transport volume is
            # synthetic padding. This is not the original 2.78 MB AUTO packet.
            value['synthetic_transport_padding'] = 'x' * (2781241 - len(json.dumps(value)))
            path.write_text(json.dumps(value), encoding='utf-8')
            with self.assertRaises(ValueError):
                m.core.read(path)
            body = m.core.decode(m.clock_receipt(path))
            self.assertEqual(body['result']['ending_date_raw'] - body['result']['starting_date_raw'], 216)
            value['synthetic_transport_padding'] = 'x' * (4 * 1024**2)
            path.write_text(json.dumps(value), encoding='utf-8')
            with self.assertRaises(ValueError):
                m.clock_receipt(path)
            value.pop('synthetic_transport_padding')
            value['result']['structured_content']['synthetic_body_padding'] = 'x' * (2 * 1024**2)
            path.write_text(json.dumps(value), encoding='utf-8')
            with self.assertRaises(ValueError):
                m.clock_receipt(path)

    def test_real_publisher_reads_only_first_positive_clock_after_zero_turns(self):
        value = data()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            queue, outbox, store = (root / n for n in ('p36-queue', 'p36-responses', 'status'))
            for path in (queue, outbox, store):
                path.mkdir()

            def put(path, content):
                path.write_text(json.dumps(content), encoding='utf-8')

            state = value['state']
            paths = {name: outbox / f'{sequence:04d}-1-result.json' for name, sequence in
                     (('original', 1875), ('response', 1876), ('semantic', 1877),
                      ('auto', 1911), ('metrics', 1912))}
            for name in ('original', 'semantic', 'auto', 'metrics'):
                put(paths[name], value[name])
            halt_path = queue / 'HALT.json'
            value['halt']['original_response'] = str(paths['original'])
            put(halt_path, value['halt'])
            state['halt_receipt'] = m.core.pin(halt_path)
            audit_path = queue / 'READONLY-PRECONDITION-RECOVERY-1876.json'
            handler = root / 'reviewed_handler.py'
            handler.write_text('# synthetic source bytes for path and hash binding\n')
            audit = value['audit']
            audit.update(original_response=str(paths['original']),
                original_response_sha256=m.core.pin(paths['original'])['sha256'],
                fresh_semantic_response=str(paths['semantic']),
                fresh_semantic_sha256=m.core.pin(paths['semantic'])['sha256'])
            audit['qualification'].update(handler_source=str(handler),
                handler_sha256=m.core.pin(handler)['sha256'])
            put(audit_path, audit)
            value['response']['result']['structured_content'].update(audit=str(audit_path),
                fresh_semantic_response=str(paths['semantic']))
            put(paths['response'], value['response'])
            for turn in value['earlier_zero_date_turns']:
                put(queue / f'CUMULATIVE-TURN-{turn["global_turn"]:06d}.json', turn)
            turn = value['turn']
            turn.update(auto_response=str(paths['auto']), after_metrics_response=str(paths['metrics']))
            put(queue / 'CUMULATIVE-TURN-013526.json', turn)
            put(queue / 'ROOT-CUMULATIVE-LOOP-STATE.json', value['loop'])
            put(root / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P36.json', value['pair'])
            put(root / 'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P36.json', value['published'])

            class Handle:
                def __init__(self, row): self.row = row
                def identity(self, role): return {**self.row, 'role': role}
                def observe(self): return {'kernel_exit_observed': False}

            publisher = m.AutoAppliedPublisher.__new__(m.AutoAppliedPublisher)
            publisher.session, publisher.queue, publisher.outbox, publisher.store = root, queue, outbox, store
            publisher.prefix = 'p36'
            publisher.state = lambda: state
            publisher._sdk_handles = [(r['role'], Handle(r)) for r in value['pair']['processes']]
            publisher.observe_sdk_pair = lambda: None
            emitted = []
            publisher.emit = lambda result: emitted.append(deepcopy(result))
            self.assertTrue(publisher.observe_known_readonly_applied())
            self.assertEqual(state['phase'], 'repair_applied_waiting_for_progress')
            with patch.object(m, 'clock_receipt', wraps=m.clock_receipt) as clock:
                self.assertTrue(publisher.resolve_if_proved(state))
            self.assertEqual([c.args[0] for c in clock.call_args_list], [paths['auto']])
            proof = emitted[-1]['recovery_proof']
            self.assertEqual(proof['global_turn'], 13526)
            self.assertEqual(proof['actual_date_delta_raw'], 216)
            self.assertEqual(proof['actual_progress_ended_at_utc'], '2026-10-17T04:47:06.511988+00:00')
            self.assertTrue(proof['first_progress_search_complete'])
            self.assertEqual(state['original_request']['sequence'], 1875)


if __name__ == '__main__':
    unittest.main()
