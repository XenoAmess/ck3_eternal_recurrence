"""Finite offline positive/negative tests of this exact reviewer correction."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import json
import sys
import unittest
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_client as client
spec = importlib.util.spec_from_file_location('candidate_business', HERE / 'ck3_mod_acceptance_cases/_business.py')
business = importlib.util.module_from_spec(spec)
spec.loader.exec_module(business)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream)

class ReviewerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='ck3-business-reviewer-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.live = self.root / 'ACTUAL_RUN_01'
        self.live.mkdir(parents=True, exist_ok=False)
        self.output = self.live / 'case-output'
        self.output.mkdir()
        self.frozen = {'run_id': self.live.name, 'argv': ['same-case-argv'],
                       'runtime_environment': {}, 'screen_task': 'same-original-screen',
                       'reviewer': '/test/operator-a'}
        self.frozen_path = self.live / 'frozen-argv.json'
        save(self.frozen_path, self.frozen)
        self.context = {'run_id': self.live.name, 'reviewer': '/test/operator-a',
                        'frozen_argv': entry.pin(self.frozen_path)}
        self.context_path = self.live / 'actual-context.json'
        save(self.context_path, self.context)
        self.selection = SimpleNamespace(context=self.context, context_path=self.context_path,
                                         run_dir=self.live, argv=self.frozen['argv'], runtime_environment={})
        self.evidence = self.output / 'actual-original-evidence.raw'
        with self.evidence.open('xb') as stream:
            stream.write(b'finite offline evidence; no game action or live credit\n')

    def persist(self):
        self.context_path.write_text(json.dumps(self.context), encoding='utf-8')

    def refreeze(self):
        self.frozen_path.write_text(json.dumps(self.frozen), encoding='utf-8')
        self.context['frozen_argv'] = entry.pin(self.frozen_path)
        self.persist()

    def response(self, reviewer='/test/operator-a', run_id=None, status='complete'):
        save(self.output / 'same-checkpoint-accepted.json',
             {'run_id': run_id or self.live.name, 'reviewer': reviewer, 'status': status,
              'facts': {'unchanged_original_business_fact': True}, 'evidence': [entry.pin(self.evidence)]})

    def check(self, expected='/test/operator-a'):
        return business.final_root_evidence({'output': str(self.output), 'run_id': self.live.name,
                                             'operator_reviewer': expected}, ['same-checkpoint'])

    def delegated(self, **updates):
        self.context['reviewer'] = '/root'
        self.frozen['reviewer'] = '/root'
        self.refreeze()
        self.delegation = {'schema': 'ck3-mod-acceptance-operator-delegation-v1',
                           'run_id': self.live.name, 'screen_task': self.frozen['screen_task'],
                           'frozen_argv': self.context['frozen_argv'], 'delegated_by': '/root',
                           'delegate_reviewer': '/test/delegate-b', 'scopes': ['ui', 'checkpoint']}
        self.delegation.update(updates)
        path = self.live / 'original-seven-field-delegation.json'
        save(path, self.delegation)
        self.context['operator_delegation'] = entry.pin(path)
        self.persist()

    def test_actual_nonroot_positive(self):
        expected = client.resolve_operator_reviewer(self.selection)
        self.response()
        self.assertEqual(len(self.check(expected)), 1)

    def test_actual_root_positive(self):
        self.context['reviewer'] = self.frozen['reviewer'] = '/root'
        self.refreeze()
        self.response('/root')
        self.assertEqual(len(self.check(client.resolve_operator_reviewer(self.selection))), 1)

    def test_original_valid_delegation_positive(self):
        self.delegated()
        expected = client.resolve_operator_reviewer(self.selection)
        self.assertEqual(expected, '/test/delegate-b')
        self.response(expected)
        self.assertEqual(len(self.check(expected)), 1)

    def test_claimed_root_negative(self):
        self.response('/root')
        with self.assertRaises(ValueError):
            self.check(client.resolve_operator_reviewer(self.selection))

    def test_other_run_negative(self):
        self.response(run_id='OTHER_RUN')
        with self.assertRaises(ValueError): self.check()

    def test_pending_status_negative(self):
        self.response(status='pending')
        with self.assertRaises(ValueError): self.check()

    def test_changed_evidence_sha_negative(self):
        self.response()
        self.evidence.write_bytes(b'changed bytes')
        with self.assertRaises(ValueError): self.check()

    def test_no_validated_expected_reviewer_negative(self):
        self.response()
        with self.assertRaises(ValueError):
            business.final_root_evidence({'output': str(self.output), 'run_id': self.live.name}, ['same-checkpoint'])

    def test_persisted_context_reviewer_drift_negative(self):
        changed = {**self.context, 'reviewer': '/test/impostor'}
        self.context_path.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_changed_frozen_sha_negative(self):
        self.frozen_path.write_bytes(b'{}')
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_frozen_run_crossing_negative(self):
        self.frozen['run_id'] = 'OTHER_RUN'
        self.refreeze()
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_frozen_case_argv_crossing_negative(self):
        self.frozen['argv'] = ['other-case-argv']
        self.refreeze()
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_delegation_run_crossing_negative(self):
        self.delegated(run_id='OTHER_RUN')
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_delegation_extra_scope_negative(self):
        self.delegated(scopes=['ui', 'checkpoint', 'publish'])
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_delegation_frozen_sha_negative(self):
        bad = {**self.context['frozen_argv'], 'sha256': '0' * 64}
        self.delegated(frozen_argv=bad)
        with self.assertRaises(ValueError): client.resolve_operator_reviewer(self.selection)

    def test_live_client_method_uses_same_resolver(self):
        held = client.CaseClient.__new__(client.CaseClient)
        held.selection = self.selection
        self.assertEqual(held.resolve_operator_reviewer(), client.resolve_operator_reviewer(self.selection))

    def test_public_verify_injects_validated_reviewer(self):
        self.response()
        save(self.output / 'normal-close-result.json', {'normal_close_qualified': True})
        selected = entry.Selection.__new__(entry.Selection)
        selected.__dict__.update(self.selection.__dict__)
        observed = {}
        selected.adapter_context = lambda: {'output': str(self.output), 'run_id': self.live.name,
                                            'operator_reviewer': '/test/forged-context-value'}
        def verify_case(context):
            observed.update(context)
            business.final_root_evidence(context, ['same-checkpoint'])
            return {'case_contract_qualified': True, 'gui_contract_qualified': True, 'business_pass': False}
        selected.load_adapter = lambda: SimpleNamespace(verify_case=verify_case)
        result = selected.verify()
        self.assertEqual(observed['operator_reviewer'], '/test/operator-a')
        self.assertTrue(result['case_acceptance_pass'])
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['product_release_pass'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
