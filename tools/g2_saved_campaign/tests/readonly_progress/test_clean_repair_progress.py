import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent
sys.path[:0]=[str(P),'Z:/ck3_mod_rewrite/tools']
from tools.g2_saved_campaign import runtime_repair_readonly_progress as mod
PACK=P/'fixtures/clean_repair_status'
def read(name): return json.loads((PACK/name).read_bytes())

class Tests(unittest.TestCase):
    def setUp(self):
        self.state, self.turn = read('actual-applied196-v2.json'), read('actual-turn86.json')
        self.auto, self.met, self.before_met = [read(x) for x in
            ('actual-auto204.json', 'actual-met205.json', 'actual-met201.json')]
        self.loop, self.pair, self.published = [read(x) for x in
            ('actual-loop-after86.json', 'actual-pinned37.json', 'actual-generations37.json')]
        # Native process I/O is the sole fake boundary in this pure proof.
        # Published actual PID/FT/executable values remain unchanged.
        self.observed = [{**row, 'kernel_exit_observed': False} for row in self.pair['processes']]

    def proof(self):
        return mod.progress_proof(self.state, self.turn, self.auto, self.met, self.before_met,
                                  self.loop, self.pair, self.published, self.observed)

    def test_actual_first_progress_and_late_notice_are_distinct(self):
        before = copy.deepcopy(self.turn)
        proof = self.proof()
        self.assertIsNotNone(proof)
        self.assertEqual(proof['global_turn'], 86)
        self.assertEqual(proof['auto_sequence'], 204)
        self.assertEqual(proof['actual_progress_ended_at_utc'], '2026-10-17T07:25:19.295257+00:00')
        self.assertEqual(proof['actual_date_delta_raw'], 192)
        self.assertEqual(proof['planning_frame_qualification']['actual_planning_source_frame']['native_revision'], 63)
        self.assertEqual(proof['planning_frame_qualification']['immutable_queue_before']['native_revision'], 62)
        self.assertEqual(self.turn, before)

    def test_identity_regression_future_frame_and_connection_rejected(self):
        for key, value in [('bridge_pid', 999), ('date_raw', 53145144), ('actor_character_id', 9),
                           ('episode_run_id', 'wrong'), ('native_revision', 61),
                           ('native_revision', 74), ('revision', 75), ('connection_generation', 2)]:
            with self.subTest(key=key, value=value):
                original = self.auto
                self.auto = copy.deepcopy(original)
                self.auto['result']['structured_content']['planning_source_frame'][key] = value
                self.assertIsNone(self.proof())
                self.auto = original

    def test_exact_paired_metrics_and_actual_pair_required(self):
        self.observed[0]['creation_filetime'] += 1
        self.assertIsNone(self.proof())
        self.observed[0]['creation_filetime'] -= 1
        self.met['result']['structured_content']['revision'] += 1
        self.assertIsNone(self.proof())

    def test_readonly_or_wrong_clock_result_cannot_resolve(self):
        self.turn['date_delta_raw'] = 0
        self.assertIsNone(self.proof())
        self.turn = read('actual-turn86.json')
        self.auto['result']['structured_content']['result']['ending_date_raw'] += 24
        self.assertIsNone(self.proof())

    def test_real_resolver_skips_zero_day_before_reading_auto_and_uses_first86(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queue, outbox, store = root / 'p37-queue', root / 'p37-responses', root / 'status'
            queue.mkdir(); outbox.mkdir(); store.mkdir()
            for name, row in [('0204-1-result.json', self.auto), ('0205-1-result.json', self.met),
                              ('0201-1-result.json', self.before_met)]:
                (outbox / name).write_text(json.dumps(row), encoding='utf-8')
            for number in (85, 86):
                turn = read('actual-turn%d.json' % number)
                for key in ('auto_response', 'before_metrics_response', 'after_metrics_response'):
                    turn[key] = str(outbox / Path(str(turn[key]).replace(chr(92), '/')).name)
                mod.core.atomic(queue / ('CUMULATIVE-TURN-%06d.json' % number), turn)
            # Current count can be far beyond the first recovery; no last64 shortcut.
            self.loop['completed_cycles'] = 12944
            mod.core.atomic(queue / 'ROOT-CUMULATIVE-LOOP-STATE.json', self.loop)
            mod.core.atomic(root / 'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37.json', self.pair)
            mod.core.atomic(root / 'ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37.json', self.published)
            current = store / 'CURRENT.json'
            mod.core.atomic(current, self.state)
            publisher = object.__new__(mod.ReadonlyProgressPublisher)
            publisher.session, publisher.queue, publisher.outbox = root, queue, outbox
            publisher.store, publisher.current, publisher.prefix = store, current, 'p37'
            publisher.binding = self.state['binding']
            class Handle:
                def __init__(self, row): self.row = row
                def identity(self, role): return dict(self.row)
                def observe(self): return {'kernel_exit_observed': False}
            publisher._sdk_handles = [(row['role'], Handle(row)) for row in self.pair['processes']]
            publisher.observe_sdk_pair = lambda: None
            publisher.state = lambda: mod.core.read(publisher.current)
            publisher.emit = lambda state: mod.core.atomic(current, state, replace=True)
            publisher.remember_resolved_archive = lambda state, archive: None
            with patch.object(mod.auto, 'clock_receipt', wraps=mod.auto.clock_receipt) as clock:
                self.assertTrue(publisher.resolve_if_proved(publisher.state()))
            self.assertEqual([Path(call.args[0]).name for call in clock.call_args_list], ['0204-1-result.json'])
            result = publisher.state()
            self.assertEqual(result['recovery_proof']['global_turn'], 86)
            self.assertEqual(result['actual_wait_ended_at_utc'], '2026-10-17T07:25:19.295257+00:00')
            self.assertGreater(mod.core.stamp(result['resolved_at_utc']), mod.core.stamp(result['actual_wait_ended_at_utc']))
            # A later genuine fault must keep its visible CURRENT unchanged.
            superseded_store = root / 'superseded-status'
            superseded_store.mkdir()
            publisher.store = superseded_store
            publisher.current = superseded_store / 'CURRENT.json'
            newer = {'incident_id': 'later-real-fault', 'phase': 'repairing'}
            mod.core.atomic(publisher.current, newer)
            publisher.emit = lambda state: self.fail('An older resolved incident must not overwrite a newer CURRENT')
            prior = read('actual-applied196-v2.json')
            self.assertTrue(publisher.resolve_if_proved(prior))
            self.assertEqual(publisher.state(), newer)
            self.assertTrue(prior['superseded_incident_archive_only'])

if __name__ == '__main__':
    unittest.main()
