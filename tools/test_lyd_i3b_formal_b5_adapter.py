"""Candidate tests only: synthetic B4 metadata/native DTOs, no CK3 or save body."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
if not (TOOLS / 'ck3_mod_acceptance_cases/lyd_i3b_formal_adapter.py').is_file():
    TOOLS = Path(os.environ.get('LYD_B5_DEPENDENCY_TOOLS', Path.cwd() / 'tools'))
sys.path.insert(0, str(TOOLS))
from ck3_mod_acceptance_cases import lyd_i3b_formal_adapter as b4
import test_lyd_i3b_formal_adapter as original

candidate = os.environ.get('LYD_B5_CANDIDATE_ROOT')
source = ((Path(candidate) / 'tools') if candidate else TOOLS) / 'ck3_mod_acceptance_cases/lyd_i3b_formal_b5_adapter.py'
spec = importlib.util.spec_from_file_location('ck3_mod_acceptance_cases.lyd_i3b_formal_b5_adapter', source)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def ref(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')
    return ref(path)


def b4_pass(data, title=90001):
    saved = lambda count: {'protection_checks': [{'name': str(i), 'matches': True} for i in range(count)],
        'protection_match': True, 'saved_business_checks': [{'name': 'actual', 'matches': True}],
        'saved_business_match': True, 'complete_cached_successor_ids': data['baseline_cached_succession']}
    return {'run_id': 'synthetic-B4', 'product': 'li-yu-dao', 'case': 'i3b-formal-b4',
        **{k: True for k in ('B4_pass', 'business_pass', 'case_contract_qualified', 'gui_contract_qualified', 'case_acceptance_pass')},
        'business_actions_submitted': 1, 'selected_option_number': 1,
        'fresh_B3': saved(87), 'B4': {**saved(88), 'new_title_id': title},
        'cache_before_ids': data['baseline_cached_succession'], 'cache_after_ids': data['baseline_cached_succession'],
        'terminal': {'event_definition_key': 'lyd.431', 'event_instance_id': 777, 'root_character_id': 31254,
            'native_option_indices': [0], 'actual_numeric_terms': {'serial': 3, 'nonce': 6}},
        'normal_close': {'normal_close_qualified': True, 'retained_handle': {'actual_retained_os0': True},
            'native_zero_proof': {'synthetic': 'native0'}, 'host_finished_at': 'synthetic-finished',
            'managed_thread_finished': True, 'cleanup_ok': True, 'host_error': None,
            'root_normal_gui_review': {'synthetic': 'review'}}}


def native_title(actual, data, title=90001):
    query = original.query(actual, {'available': True, 'date_raw': actual['date_raw'], 'graph_available': True,
        'game_version': adapter.TITLE_VERSION, 'executable_sha256': adapter.TITLE_EXE_SHA256,
        'faith_full_id': 107, 'legal_head_title_absent': False, 'head_title_full_id': title,
        'native_title_holder_full_id': 31254,
        'title_properties': {'available': True, **{key: True for key in data['title_properties']}},
        'title_laws': {'available': True, 'temporal_head_of_faith_succession_law_member': True,
            'complete_laws': [{'native_definition_id': 95, 'key': 'temporal_head_of_faith_succession_law'}]}},
        'confucian_religious_title')
    query['native_result'].update(game_version=adapter.TITLE_VERSION, executable_sha256=adapter.TITLE_EXE_SHA256)
    return query


class Upstream(unittest.TestCase):
    def setUp(self):
        self.data = b4.contract()

    def test_complete_pass_uses_dynamic_title_and_full_protections(self):
        self.assertEqual(adapter.validate_pass(b4_pass(self.data, 90002), self.data), 90002)

    def test_red_or_administrative_or_incomplete_B4_never_qualifies(self):
        changes = [lambda f: f.update(B4_pass=False), lambda f: f.update(case_acceptance_pass=False),
            lambda f: f['normal_close'].update(normal_close_qualified=False),
            lambda f: f['B4']['protection_checks'][4].update(matches=False),
            lambda f: f['B4']['protection_checks'].pop(),
            lambda f: f['fresh_B3'].update(saved_business_match=False),
            lambda f: f['cache_after_ids'].reverse()]
        for change in changes:
            facts = copy.deepcopy(b4_pass(self.data))
            change(facts)
            with self.subTest(change=change), self.assertRaises(ValueError):
                adapter.validate_pass(facts, self.data)

    def test_missing_upstream_rejects_before_profile_write(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / 'unused-state'
            context = {'product': 'li-yu-dao', 'case': 'i3b-formal-b5', 'case_contract': adapter.contract(),
                'case_inputs': {'B4_verified_origin': None}, 'saved_campaign': {}, 'state_dir': str(state)}
            with self.assertRaises(ValueError):
                adapter.prepare_case(context)
            self.assertFalse(state.exists())

    def bundle(self, root):
        data, facts = self.data, b4_pass(self.data)
        run = root / 'synthetic-B4'
        save = run / 'case-output/checkpoints/B4-factory-result.ck3'
        checkpoint = {'path': str(save), 'bytes': 123, 'sha256': 'a' * 64}
        facts['B4']['checkpoint'] = checkpoint
        manifest = {'path': 'synthetic-manifest.json', 'bytes': 10, 'sha256': 'b' * 64}
        prepared = put(root, 'prepared-case.json', {'schema': 'ck3-mod-acceptance-prepared-case-v1',
            'product': 'li-yu-dao', 'case': 'i3b-formal-b4', 'runtime_manifest': manifest,
            'contract': ref(Path(b4.__file__).with_name('lyd_i3b_formal_b4.json')),
            'case_inputs': {}, 'startup': {'saved_campaign': {}}})
        frozen = put(run, 'frozen-argv.json', {'run_id': 'synthetic-B4', 'runtime_manifest': manifest})
        context = put(run, 'reviewed-context.json', {'schema': 'ck3-mod-acceptance-run-context-v1',
            'run_id': 'synthetic-B4', 'run_dir': str(run), 'product': 'li-yu-dao', 'case': 'i3b-formal-b4',
            'prepared_case': prepared, 'frozen_argv': frozen})
        stdout = put(root, 'verify-stdout.json', facts)
        command = put(root, 'recorded-verify.json', {'exit_code': 0, 'argv': ['python',
            'tools/ck3_mod_acceptance.py', 'verify', '--product', 'li-yu-dao', '--case', 'i3b-formal-b4',
            '--prepared-case', prepared['path'], '--run-context', context['path']], 'stdout': stdout})
        return {'case_inputs': {'B4_verified_origin': {'prepared_case': prepared, 'run_context': context,
            'public_verify_command': command}}, 'runtime_manifest': manifest,
            'saved_campaign': {'save': str(save), 'bytes': 123, 'sha256': 'a' * 64,
                'player_id': 31254, 'date_raw': 53144712}}

    def test_ref_bound_verify_seed_and_shared_manifest_are_mandatory(self):
        with tempfile.TemporaryDirectory() as temp:
            context = self.bundle(Path(temp))
            # Only the previously tested historical B3 origin validator is isolated;
            # this test exercises real ref3 reads, public argv/seed/runtime/new-T guards.
            with patch.object(b4, 'validate_origin', return_value=(None, None, None)):
                actual = adapter.upstream(context)
                self.assertEqual(actual['title_id'], 90001)
                self.assertEqual(actual['expected']['event_instance_id'], 777)
                for role, key, value in [('saved_campaign', 'sha256', 'c' * 64),
                    ('saved_campaign', 'save', 'wrong-checkpoint.ck3'),
                    ('runtime_manifest', 'sha256', 'd' * 64)]:
                    bad = copy.deepcopy(context)
                    bad[role][key] = value
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        adapter.upstream(bad)


class Cold(unittest.TestCase):
    def setUp(self):
        self.data = b4.contract()
        self.origin = {'data': self.data, 'title_id': 90001,
            'expected': {**self.data['expected'], 'event_definition_key': 'lyd.431',
                'event_instance_id': 777, 'native_option_indices': [0]}, 'verification': {'synthetic': 'verify'}}

    def test_native_title_requires_exact_T_holder_four_attributes_and_law95(self):
        actual = original.frame(777)
        query = native_title(actual, self.data)
        self.assertTrue(adapter.native_title_matches(actual, query, self.origin))
        changes = [lambda p: p.update(head_title_full_id=90002), lambda p: p.update(native_title_holder_full_id=65865),
            lambda p: p['title_properties'].update(always_follows_primary_heir=False),
            lambda p: p['title_laws'].update(complete_laws=[])]
        for change in changes:
            bad = copy.deepcopy(query)
            change(bad['native_result']['confucian_religious_title'])
            self.assertFalse(adapter.native_title_matches(actual, bad, self.origin))

    def test_saved_title_qualification_unknown_fails_closed(self):
        saved = {'protection_checks': [{'matches': True} for _ in range(88)], 'protection_match': True,
            'saved_business_checks': [{'matches': True}], 'saved_business_match': True,
            'native_saved_Faith_Title_join': True, 'new_title_id': 90001,
            'complete_cached_successor_ids': self.data['baseline_cached_succession'],
            'saved_body_reads': 1, 'baseline_body_reads': 0,
            'saved_title_field_qualification': {'status': 'UNKNOWN', 'law': None,
                'properties': None, 'reason': 'native serialization not yet source-qualified'}}
        facts = {'cold_saved': saved, 'initial_native_title_match': True,
            'cache_before_ids': self.data['baseline_cached_succession'],
            'cache_after_ids': self.data['baseline_cached_succession'],
            'factory_actions': 0, 'event_selections': 0, 'natural_days': 0}
        self.assertFalse(adapter.assessment(facts, self.origin))

    def test_absent_B5_result_remains_false_without_an_upstream_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            result = adapter.verify_case({'product': 'li-yu-dao', 'case': 'i3b-formal-b5',
                'case_contract': adapter.contract(), 'output': temp})
            self.assertIs(result['B5_pass'], False)
            self.assertIs(result['business_pass'], False)

    def test_cold_complete_or_changed_cache_has_one_save_and_zero_mutations(self):
        class Client(original.FakeClient):
            def execute_plan(inner, steps, name, timeout=None):
                if steps[0]['tool'] == 'ck3_query_confucian_religious_title_v1':
                    inner.calls.append((steps[0]['tool'], copy.deepcopy(steps[0]['args'])))
                    return [{'ok': True, 'result': native_title(inner.snapshot(False), inner.data)}]
                return super().execute_plan(steps, name, timeout)
        for changed, invalid in ((False, None), (True, None), (False, 'one'),
                                 (False, 'law_none'), (False, 'extra_law')):
            with tempfile.TemporaryDirectory() as temp:
                client = Client(Path(temp), self.data, bad=changed)
                client.instance = 777
                context = {'product': 'li-yu-dao', 'case': 'i3b-formal-b5', 'run_id': 'synthetic-B5',
                    'case_contract': adapter.contract(), 'output': temp,
                    'saved_campaign': {'save': 'synthetic-B4.ck3', 'bytes': 123, 'sha256': 'a' * 64}}
                saved = {'protection_checks': [{'matches': True} for _ in range(88)], 'protection_match': True,
                    'saved_business_checks': [{'matches': True}], 'saved_business_match': True,
                    'native_saved_Faith_Title_join': True, 'new_title_id': 90001,
                    'complete_cached_successor_ids': self.data['baseline_cached_succession'],
                    'saved_body_reads': 1, 'baseline_body_reads': 0,
                    'saved_title_field_qualification': {'status': 'QUALIFIED_OBSERVATION',
                        'law_matches_factory_contract': True, 'properties_match_factory_contract': True,
                        'law': ['temporal_head_of_faith_succession_law'], 'binding': adapter.title_binding(),
                        'properties': {name: {'raw': spec['true_token'], 'value': True, 'path': spec['path']}
                            for name, spec in adapter.title_binding()['properties'].items()}}}
                qualification = saved['saved_title_field_qualification']
                if invalid == 'one':
                    qualification['properties']['definitive_form']['value'] = 1
                elif invalid == 'law_none':
                    qualification['law'] = None
                elif invalid == 'extra_law':
                    qualification['law'].append('unqualified_extra_law')
                with (patch.object(adapter, 'upstream', return_value=self.origin),
                        patch.object(adapter, 'read_cold_saved', return_value=saved)):
                    facts = adapter.run_case(context, client)
                self.assertIs(facts['B5_pass'], not changed and invalid is None)
                tools = [tool for tool, args in client.calls]
                self.assertEqual(tools.count('ck3_save_checkpoint'), 1)
                self.assertNotIn('ck3_select_event_option', tools)
                self.assertEqual(facts['factory_actions'], 0)
                self.assertIn('i3b-formal-b5-case-result', client.outputs)
                self.assertIs(facts['product_release_pass'], False)


if __name__ == '__main__':
    unittest.main()
