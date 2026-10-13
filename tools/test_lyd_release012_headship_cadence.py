"""Portable synthetic cadence test; no game, SDK, queue or live qualification."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ck3_mod_acceptance_cases import lyd_release012_headship_adapter as case
from ck3_mod_acceptance_cases import lyd_release012_keypaths_adapter as keypaths


class CadenceTest(unittest.TestCase):
    def test_fresh_before_complete_cached_pages_and_independent_final_read(self):
        original_globals = (keypaths.CASE, keypaths.RESULT, keypaths.native_head_bundle)
        base = case.load_base()
        self.assertEqual(original_globals,
                         (keypaths.CASE, keypaths.RESULT, keypaths.native_head_bundle))
        self.assertIs(base.review_cell.__globals__['native_head_bundle'], base.native_head_bundle)
        self.assertEqual(base.prepare_case.__globals__['CASE'], case.CASE)
        self.assertEqual(base.verify_case.__globals__['RESULT'], case.RESULT)
        frame = {'revision': 8, 'native_revision': 7, 'date_raw': 53144712,
                 'played_character': {'character_id': 31254, 'alive': True},
                 'paused': True, 'diagnostics': {'bridge_pid': 4321,
                                                'connection_generation': 1}}
        religion = {'faith_key': 'confucian_faith', 'faith_id': 31, 'faith_main_rite_id': 33}
        member = {'character_id': 31254, 'rite_id': 33, 'faith_id': 31,
                  'effective_learning': 5, 'complete': True, 'alive': True,
                  'adult': True, 'imprisoned': False, 'incapable': False, 'is_ai': False}
        dto = {'available': True, 'predicates_complete': True, 'played_character_id': 31254,
               'faith_id': 31, 'played_rite_id': 33, 'members': [member],
               'rites': [{'rite_id': 33, 'complete': True, 'county_title_ids': [],
                          'native_county_count': 0}],
               'complete_native_faith_member_ids': [31254],
               'complete_native_faith_rite_ids': [33]}
        reads, religion_reads, requests = [], [], []

        class Client:
            operator_reviewer = '/synthetic-root'

            def remaining(self):
                return 10000.0

            def snapshot(self, **kwargs):
                return copy.deepcopy(frame)

            def validate_frame(self, value, **kwargs):
                return value

            def root_checkpoint(self, name, payload, reserve):
                requests.append((name, copy.deepcopy(payload)))
                response = {'status': 'observe', 'run_id': 'synthetic-run',
                            'reviewer': self.operator_reviewer}
                if name == 'preparation-request-current':
                    response['request_full_readiness'] = True
                return response

        def assembly(client, initial, name, tool):
            self.assertEqual(tool, case.ASSEMBLY)
            reads.append(name)
            return frame, {'result': copy.deepcopy(dto)}

        def review(context, client, initial, phase, consumed):
            request = {'phase': phase['id'], 'actual_typed_event': {'synthetic_page': True}}
            client.root_checkpoint(phase['id'] + '-first', request)
            client.root_checkpoint(phase['id'] + '-page', request)
            if phase['id'] == 'preparation':
                member['effective_learning'] = 16
                no_event = {**request, 'actual_typed_event': None}
                for name in ('paid-event-ended', 'after-navigation', 'ordinary-observe',
                             'preparation-request-current', 'requested-readiness',
                             'after-explicit-refresh'):
                    client.root_checkpoint(name, no_event)
                # The explicit read saw16, but the independent final read must
                # reject14 rather than trust ROOT's earlier completion.
                member['effective_learning'] = 14
            return {'phase': phase['id'], 'status': 'complete', 'qualified': True}

        def read_religion(client, initial, name):
            religion_reads.append(name)
            return copy.deepcopy(religion)

        base.religion = read_religion
        base.call = assembly
        base.formal = SimpleNamespace(observe_query=lambda frame, result, name: result)
        base.review_cell = review
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admission = root / 'ADMISSION.actual.json'
            expiry = datetime.fromtimestamp(time.time() + 10000, timezone.utc)
            raw = json.dumps({'reservation_expires_at_utc': expiry.isoformat()}).encode('utf-8')
            admission.write_bytes(raw)
            ref = {'path': str(admission), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
            config = {'case_id': case.CASE, 'storage_admission': ref, 'phases': [
                {'id': 'baseline', 'required': True, 'maximum_review_seconds': 900},
                {'id': 'preparation', 'required': True, 'maximum_review_seconds': 3600},
                {'id': 'institution', 'required': True, 'maximum_review_seconds': 1800}]}
            context = {'run_id': 'synthetic-run', 'output': str(root)}
            with patch.object(case, 'load_base', return_value=base), \
                 patch.object(base.generic, 'compiled_contract', return_value=({'config': config}, ref)):
                result = case.run_case(context, Client())
            self.assertEqual([name for name, _ in requests], [
                'baseline-first', 'baseline-page', 'preparation-first',
                'preparation-page', 'paid-event-ended', 'after-navigation',
                'ordinary-observe', 'preparation-request-current', 'requested-readiness',
                'after-explicit-refresh'])
            self.assertEqual([p['actual_readiness_fresh_for_this_checkpoint'] for _, p in requests],
                             [True, False, True, False, False, False, False, False, True, False])
            for index in (1, 3, 4, 5, 6, 7, 9):
                with self.subTest(retained_checkpoint=requests[index][0]):
                    self.assertEqual(requests[index][1]['actual_readiness_scope'],
                                     'retained_full_observation_not_current_frame')
            for index in (3, 4, 5, 6, 7):
                self.assertEqual(requests[index][1]['actual_readiness']['roster']['actual_actor']['effective_learning'], 5)
            paid = requests[8][1]['actual_readiness']
            self.assertEqual(requests[8][1]['actual_readiness_scope'],
                             'fresh_full_readiness_before_ROOT_response')
            self.assertEqual(paid['roster']['actual_actor']['effective_learning'], 16)
            self.assertTrue(case.prepared_ready(religion, paid['religion'], paid['roster']))
            self.assertEqual(requests[9][1]['actual_readiness'], paid)
            self.assertEqual(reads, [
                'baseline-first-readiness-assembly', 'headship-baseline-final-assembly',
                'preparation-first-readiness-assembly', 'requested-readiness-readiness-assembly',
                'headship-preparation-final-assembly'])
            self.assertEqual(religion_reads, ['headship-original-religion'] + [
                name.removesuffix('-assembly') + '-religion' for name in reads])
            self.assertEqual([c['phase'] for c in result['cells']], ['baseline', 'preparation'])
            self.assertEqual(result['cells'][1]['actual_readiness']['roster']['actual_actor']['effective_learning'], 14)
            self.assertFalse(result['cells'][1]['qualified'])
            self.assertFalse(result['case_contract_qualified'])
            self.assertFalse(result['business_pass'])
            self.assertFalse(result['formal_B4_B5_C3_credit'])

    def test_explicit_read_does_not_extend_phase_storage_or_quit_reserve(self):
        clock = SimpleNamespace(now=1000.0)
        deadline = clock.now + 7200
        requests = []

        class Client:
            def remaining(self):
                return deadline - clock.now

            def root_checkpoint(self, name, payload, reserve):
                requests.append((name, copy.deepcopy(payload), reserve))
                return {'status': 'observe', 'request_full_readiness': name == 'request-current'}

        bounded = case.BoundedClient(Client(), deadline, None, None, None)
        bounded.last_readiness = {'synthetic_observation': True}
        request = {'phase': 'preparation', 'actual_typed_event': None}
        with patch.object(case.time, 'time', side_effect=lambda: clock.now), \
             patch.object(bounded, 'read_readiness', return_value=bounded.last_readiness) as reads:
            bounded.begin_phase({'maximum_review_seconds': 3600})
            phase_deadline = bounded.phase_deadline
            self.assertEqual(phase_deadline, 4600.0)
            bounded.root_checkpoint('first', request)
            clock.now = 1100.0
            bounded.root_checkpoint('request-current', request)
            clock.now = 1200.0
            bounded.root_checkpoint('fresh-requested', request)
            clock.now = 1300.0
            bounded.root_checkpoint('ordinary-observe', request)
            self.assertEqual(reads.call_count, 2)
            self.assertFalse(bounded.requested_readiness_phases)
            self.assertEqual(bounded.phase_deadline, phase_deadline)
            self.assertEqual(bounded.deadline, deadline)
            for _, payload, reserve in requests:
                self.assertEqual(payload['fixed_phase_deadline_epoch'], phase_deadline)
                self.assertEqual(payload['effective_storage_deadline_epoch'], deadline)
                self.assertGreaterEqual(reserve, case.QUIT_RESERVE)
            clock.now = phase_deadline
            with self.assertRaisesRegex(ValueError, 'Fixed phase review deadline reached'):
                bounded.root_checkpoint('phase-expired', request)
            clock.now = deadline - case.QUIT_RESERVE
            with self.assertRaisesRegex(ValueError, 'Original normal Quit reserve reached'):
                bounded.root_checkpoint('quit-reserved', request)
            self.assertEqual(reads.call_count, 2)
            self.assertEqual(len(requests), 4)


if __name__ == '__main__':
    unittest.main()
