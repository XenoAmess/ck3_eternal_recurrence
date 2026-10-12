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
        reads, requests = [], []

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
                return {'status': 'complete', 'run_id': 'synthetic-run',
                        'reviewer': self.operator_reviewer}

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
                client.root_checkpoint('paid-event-ended', {**request, 'actual_typed_event': None})
                # ROOT saw fresh qualification before completing. A changed final
                # observation must still reject that earlier completion.
                member['effective_learning'] = 14
            return {'phase': phase['id'], 'status': 'complete', 'qualified': True}

        base.religion = lambda *args: copy.deepcopy(religion)
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
                {'id': 'preparation', 'required': True, 'maximum_review_seconds': 1800},
                {'id': 'institution', 'required': True, 'maximum_review_seconds': 1800}]}
            context = {'run_id': 'synthetic-run', 'output': str(root)}
            with patch.object(case, 'load_base', return_value=base), \
                 patch.object(base.generic, 'compiled_contract', return_value=({'config': config}, ref)):
                result = case.run_case(context, Client())
            self.assertEqual([name for name, _ in requests], [
                'baseline-first', 'baseline-page', 'preparation-first',
                'preparation-page', 'paid-event-ended'])
            self.assertEqual([p['actual_readiness_fresh_for_this_checkpoint'] for _, p in requests],
                             [True, False, True, False, True])
            self.assertEqual(requests[3][1]['actual_readiness_scope'],
                             'retained_full_observation_not_current_frame')
            self.assertEqual(requests[3][1]['actual_readiness']['roster']['actual_actor']['effective_learning'], 5)
            paid = requests[4][1]['actual_readiness']
            self.assertEqual(paid['roster']['actual_actor']['effective_learning'], 16)
            self.assertTrue(case.prepared_ready(religion, paid['religion'], paid['roster']))
            self.assertEqual(reads, [
                'baseline-first-readiness-assembly', 'headship-baseline-final-assembly',
                'preparation-first-readiness-assembly', 'paid-event-ended-readiness-assembly',
                'headship-preparation-final-assembly'])
            self.assertEqual([c['phase'] for c in result['cells']], ['baseline', 'preparation'])
            self.assertEqual(result['cells'][1]['actual_readiness']['roster']['actual_actor']['effective_learning'], 14)
            self.assertFalse(result['cells'][1]['qualified'])
            self.assertFalse(result['case_contract_qualified'])
            self.assertFalse(result['business_pass'])


if __name__ == '__main__':
    unittest.main()
