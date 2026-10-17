import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

P = Path(__file__).resolve().parent
from tools.g2_saved_campaign import runtime_repair_readonly_progress as mod
FIXTURES = P/'fixtures/clean_repair_status'


def read(name):
    return json.loads((FIXTURES/name).read_bytes())


class ReadonlyStatus(unittest.TestCase):
    def test_actual_diagnostics_and_newer_frame_do_not_infer_business_or_recovery(self):
        expected = [('actual-auto185.json', '\u5efa\u8bbe\u67e5\u8be2\u7684\u6682\u505c\u5e27\u6682\u4e0d\u53ef\u7528'),
            ('actual-auto196.json', '\u7ee7\u627f\u4eba\u5173\u7cfb\u67e5\u8be2\u7684\u53ea\u8bfb\u5feb\u7167\u5df2\u53d8\u5316'),
            ('actual-auto517.json', '\u6d3e\u7cfb\u884c\u52a8\u6b63\u5728\u7b49\u5f85\u65b0\u5feb\u7167'),
            ('actual-auto21-newer.json', '\u6d3e\u7cfb\u884c\u52a8\u7684\u540c\u65e5\u6682\u505c\u5feb\u7167\u5df2\u66f4\u65b0')]
        for name, reason in expected:
            row = read(name)
            with self.subTest(name=name):
                self.assertEqual(mod.diagnostic_reason(row)[0], reason)
                row['result']['is_error'] = False
                self.assertIsNone(mod.diagnostic_reason(row))

    def test_exact22_applies_original21_only_and_preserves_pending_gift(self):
        state, audit = read('actual-opened21-newer.json'), read('actual-recovery22-newer.json')
        # The full actual halted request is contained in the audit; minimal
        # companion halt fields are sufficient for this pure qualification.
        halt = {'original_request': audit['original_request'], 'replay_allowed': False, 'next_sequence': 22}
        proof = mod.qualify_readonly_recovery(state, halt, read('actual-auto21-newer.json'),
            read('actual-control22-newer.json'), audit, read('actual-sem23-newer.json'))
        self.assertEqual(proof['progress_search_start_turn'], 373)
        self.assertFalse(proof['recovery_claimed'])
        self.assertEqual(proof['business_credit'], 0)
        self.assertTrue(audit['qualification']['faction_pending_ledger_must_be_preserved'])
        state['original_request']['sequence'] = 788
        with self.assertRaises(ValueError):
            mod.qualify_readonly_recovery(state, halt, read('actual-auto21-newer.json'),
                read('actual-control22-newer.json'), audit, read('actual-sem23-newer.json'))

    def test_automatic_applied_uses_actual187_contract_and_real_temp_file_pins(self):
        original, audit, control, semantic = [read(name) for name in ('actual-auto185.json',
            'actual-recovery187.json', 'actual-control187.json', 'actual-sem188.json')]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);queue = root/'p37-queue';outbox = root/'p37-responses';store = root/'status'
            for p in (queue, outbox, store): p.mkdir()
            handler = root/'readonly-handler.py';handler.write_text('# synthetic handler bytes; never executed\n', encoding='utf-8')
            op, sp, cp = outbox/'0185-1-result.json', outbox/'0188-1-result.json', outbox/'0187-1-result.json'
            ap = queue/'READONLY-PRECONDITION-RECOVERY-0187.json'
            mod.core.atomic(op, original);mod.core.atomic(sp, semantic)
            audit.update(original_response=str(op), original_response_sha256=mod.core.pin(op)['sha256'],
                fresh_semantic_response=str(sp), fresh_semantic_sha256=mod.core.pin(sp)['sha256'])
            audit['qualification'].update(handler_source=str(handler), handler_sha256=mod.core.pin(handler)['sha256'])
            control['result']['structured_content'].update(audit=str(ap), fresh_semantic_response=str(sp))
            mod.core.atomic(ap, audit);mod.core.atomic(cp, control)
            hp = queue/'HALT.json';halt = read('actual-halt142.json');halt['original_response'] = str(op)
            mod.core.atomic(hp, halt)
            state = {'incident_id': 'actual185-contract-temp-paths', 'phase': 'repairing',
                'original_request': original['request'], 'halt_receipt': mod.core.pin(hp),
                'binding': {'sdk_prefix': 'p37', 'game_pid': 230672, 'game_creation_filetime': 134366924532682885},
                'observed_frame': audit['failed_pending_cycle']['before']}
            pub = object.__new__(mod.ReadonlyProgressPublisher)
            pub.session,pub.queue,pub.outbox,pub.store,pub.prefix = root,queue,outbox,store,'p37'
            pub.state = lambda: copy.deepcopy(state)
            captured = []
            pub.emit = lambda value: captured.append(value) or {'metadata_only_test': True}
            self.assertTrue(pub.observe_known_readonly_applied())
            self.assertEqual(captured[0]['phase'], 'repair_applied_waiting_for_progress')
            self.assertEqual(captured[0]['progress_search_start_turn'], 83)
            self.assertFalse(captured[0]['readonly_applied_proof']['recovery_claimed'])
            self.assertEqual(captured[0]['readonly_applied_proof']['business_credit'], 0)
            handler.write_text('# altered handler\n', encoding='utf-8')
            with self.assertRaises(ValueError): pub.apply_readonly(cp, state['incident_id'], 185, 'known repair')

    def test_terminal_dedup_points_to_old_resolution_not_new_CURRENT(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);halt=root/'HALT.json';halt.write_text('{}', encoding='utf-8')
            archive=root/'old-RESOLVED.json';archive.write_text('{"incident_id":"old"}', encoding='utf-8')
            current=root/'CURRENT.json';current.write_text('{"incident_id":"new"}', encoding='utf-8')
            pub=object.__new__(mod.ReadonlyProgressPublisher)
            pub.store,pub.current=root,current
            pub.identity_for_halt=lambda path,binding: ({'exact-test-identity':'old'}, {})
            cache={};pub.terminal_faults=lambda:cache
            state={'halt_receipt':mod.core.pin(halt),'binding':{},'incident_id':'old','phase':'resolved'}
            pub.remember_resolved_archive(state,archive)
            proof=mod.core.read(next(root.glob('*-CLOSED-FAULT.json')))
            self.assertEqual(proof['terminal_state'],mod.core.pin(archive))
            self.assertNotEqual(proof['terminal_state'],mod.core.pin(current))


if __name__=='__main__':unittest.main()
