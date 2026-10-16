"""New offline binding cases only; every fixture is explicitly synthetic."""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--scratch-root', type=Path)
fixture_args, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]]+remaining
spec = importlib.util.spec_from_file_location('_C_explicit_binding_candidate',
    Path(__file__).with_name('phased_relay.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
NEW = 'c4992c304d196135d9590799d69ffb3c9f5510e6'


class BindingCases(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='C-explicit-bindings-', dir=fixture_args.scratch_root)
        self.directory = Path(self.temporary.name).resolve()
        if fixture_args.scratch_root is not None:
            self.assertTrue(self.directory.is_relative_to(fixture_args.scratch_root.resolve()))
        self.addCleanup(self.temporary.cleanup)
        module = self.directory/'synthetic_module.py'
        module.write_text('SYNTHETIC = True\n', encoding='utf-8')
        self.b = {
            'source_head': NEW, 'machine_id': 'SYNTHETIC-machine', 'deadline_utc': c.DEADLINE,
            'repo': str(self.directory), 'runtime_request_budget_bytes': 17*1024*1024,
            'army_id': 7, 'case_id': 'SYNTHETIC-C', 'evidence_roots': [str(self.directory)],
            'runtime': {'source_head': NEW, 'native_dll_sha256': 'a'*64,
                        'started_at_utc': '2026-10-15T21:00:00+00:00'},
            'modules': {key:c.pin(module) for key in ('root_relay','dcda_coherent_reader','next_adapter')},
            'request_helper': c.pin(module), 'current_loaded_features': {'SYNTHETIC': True}}
        self.put('context', {'synthetic': True, 'machine_id': 'SYNTHETIC-machine',
            'source_head': NEW, 'identity': {'machine_id': 'SYNTHETIC-machine', 'mod_key': 'vanilla',
                'sequence': 278, 'run_id': 'SYNTHETIC-machine--vanilla--R0278'}})
        self.put('runtime_proof', {'synthetic': True, 'machine_id': 'SYNTHETIC-machine',
            'source_head': NEW, 'run_id': 'SYNTHETIC-machine--vanilla--R0278', 'pid': 1,
            'process_creation_filetime_100ns': 2, 'connection_generation': 3,
            'actual_runtime_character_full_id': 4, 'episode_run_id': 'SYNTHETIC-episode',
            'stable_character_intent': {'historical_id': 1128,
                'bookmark_character_name_key': 'bookmark_rags_to_riches_duke_robert'}})
        self.put('plan', {'synthetic': True, 'build': {'source_head': NEW,
            'native_dll_sha256': 'a'*64}})
        self.put('capacity', {'synthetic': True, 'machine_id': 'SYNTHETIC-machine',
            'admitted': True, 'quota_review_at_utc': c.DEADLINE})
        self.put('prepared', {'synthetic': True})
    def put(self, key, value):
        path = self.directory/(key+'.json')
        path.write_text(json.dumps(value), encoding='utf-8')
        self.b[key] = c.pin(path)
    def modify(self, key, change):
        value = c.load(self.b[key]['path'])
        change(value)
        self.put(key, value)
    def test_explicit_c499_pins_prepare_and_forward_real_sequence(self):
        result = c.prepare(self.b)
        self.assertEqual(result['status'], 'SOURCE-COMPOSITION-PREPARED')
        self.assertEqual(result['source_head'], NEW)
        self.assertEqual(result['run_sequence'], 278)
        self.assertFalse(result['live_qualification_granted'])
        self.assertFalse(result['provider_imported'])
        args = c.provider_arguments(self.b, argparse.Namespace(attempt='SYNTHETIC-1', stage='admit'),
                                    c.runtime_binding(self.b))
        self.assertEqual((args.source_head,args.run_sequence,args.run_id),
            (NEW,278,'SYNTHETIC-machine--vanilla--R0278'))
        self.assertEqual(args.runtime_proof_sha256, self.b['runtime_proof']['sha256'])
    def test_missing_explicit_source_runtime_identity_or_module_pin_refuses(self):
        missing = deepcopy(self.b)
        missing.pop('source_head')
        self.assertEqual(c.prepare(missing)['status'], 'NEEDS_ROOT_BINDINGS')
        missing = deepcopy(self.b)
        missing['runtime'].pop('source_head')
        with self.assertRaisesRegex(ValueError, 'source differs'):
            c.prepare(missing)
        missing = deepcopy(self.b)
        missing['modules'].pop('next_adapter')
        with self.assertRaisesRegex(ValueError, 'module pins are incomplete'):
            c.prepare(missing)
        self.modify('runtime_proof', lambda p:p.pop('episode_run_id'))
        with self.assertRaisesRegex(ValueError, 'episode missing'):
            c.prepare(self.b)
    def test_context_proof_and_plan_source_are_independent_guards(self):
        for key in ('context','runtime_proof','plan'):
            before = deepcopy(self.b[key])
            raw = Path(before['path']).read_bytes()
            def change(value):
                (value['build'] if key == 'plan' else value)['source_head'] = c.SOURCE
            self.modify(key, change)
            with self.subTest(witness=key), self.assertRaisesRegex(ValueError, 'source differs'):
                c.prepare(self.b)
            Path(before['path']).write_bytes(raw)
            self.b[key] = before
    def test_sequence_run_id_and_runtime_intent_must_match(self):
        self.modify('context', lambda value:value['identity'].update(sequence=279))
        with self.assertRaisesRegex(ValueError, 'sequence differs'):
            c.prepare(self.b)
        self.modify('context', lambda value:value['identity'].update(sequence=278))
        self.modify('runtime_proof', lambda value:value.update(run_id='SYNTHETIC-machine--vanilla--R0279'))
        with self.assertRaisesRegex(ValueError, 'sequence differs'):
            c.prepare(self.b)
        self.modify('runtime_proof', lambda value:value.update(run_id='SYNTHETIC-machine--vanilla--R0278'))
        self.b['runtime']['run_sequence'] = 279
        with self.assertRaisesRegex(ValueError, 'runtime run_sequence differs'):
            c.prepare(self.b)
    def test_exact_module_pin_is_not_bypassed_by_valid_new_source(self):
        Path(self.b['modules']['next_adapter']['path']).write_text('SYNTHETIC = False\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'bytes/SHA changed'):
            c.prepare(self.b)
    def test_historical_dcda_remains_historical_and_cannot_claim_new_runtime(self):
        self.b['source_head'] = c.SOURCE
        with self.assertRaisesRegex(ValueError, 'source differs'):
            c.prepare(self.b)
        self.b['runtime']['source_head'] = c.SOURCE
        for key in ('context','runtime_proof','plan'):
            def change(value):
                (value['build'] if key == 'plan' else value)['source_head'] = c.SOURCE
            self.modify(key, change)
        result = c.prepare(self.b)
        self.assertEqual(result['source_head'], c.SOURCE)
        self.assertFalse(result['live_qualification_granted'])


if __name__ == '__main__':
    unittest.main()
