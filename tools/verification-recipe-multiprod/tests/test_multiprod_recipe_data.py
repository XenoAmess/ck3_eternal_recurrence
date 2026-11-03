"""New coherent2P DATA boundaries. Native sole first executor; no real bytecode."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from fixture_support import _Fixture, _json, _pin, _read, _tokens


class _Pair(_Fixture):
    def __init__(self, root):
        super().__init__(root)
        self.prod.write_text('package data;\npublic final class Production { public static final class Signal {} }\n', encoding='utf-8')
        self.consumer = root / 'sources/data/Consumer.java'
        self.consumer.write_text('package data;\npublic final class Consumer { Production.Signal value; }\n', encoding='utf-8')
        ready = _json(root / 'pair-source-ready.json', {'synthetic_DATA_only': True, 'sources': [_pin(self.prod), _pin(self.consumer)]})
        self.request['schema'] = 'xar.verification-recipe-request/v2'
        self.request['profile'] = 'two-prod-one-test-explicit-methods'
        self.request['production_sources'] = [
            {'source': _pin(self.prod), 'class_name': 'data.Production', 'source_ready': ready},
            {'source': _pin(self.consumer), 'class_name': 'data.Consumer', 'source_ready': ready}]
        for key in ('production_source', 'production_class', 'production_ready'):
            del self.request[key]
        self.declaration['schema'] = 'xar.native-sdk-declaration/v2'
        self.declaration['sources']['production'] = [_pin(self.prod), _pin(self.consumer)]
        self.declaration['required_families'] = {
            'production': ['data.Api', 'data.Production.Signal'],
            'test': ['data.Api', 'data.Production', 'data.Consumer', 'data.Production.Signal']}
        self.save_declaration()

    def produced(self, *, missing=None, source_tus=2):
        config_path = self.output / 'production/CONFIG.json'
        config = _read(config_path)
        output = self.output / 'production/classes/data'
        output.mkdir(parents=True)
        for name in ('Production.class', 'Production$Signal.class', 'Consumer.class'):
            if name != missing:
                (output / name).write_bytes(('SYNTHETIC DATA ONLY: ' + name).encode())
        rows = [_pin(path) for path in sorted(output.glob('*.class'))]
        directory = self.root / 'actual-pair-DATA'
        actual = _json(directory / 'ACTUAL.json', {'synthetic_DATA_only': True, 'phase': 'prod', 'source_TUs': source_tus,
                       'config': _pin(config_path), 'command': config['phases']['prod']['command'], 'exit_code': 0,
                       'error': None, 'timeout': False, 'pins_unchanged': True, 'classes': rows})
        verified = _json(directory / 'VERIFIED.json', {'synthetic_DATA_only': True, 'phase': 'prod', 'actual': actual, 'classes': rows})
        return actual, verified

    def jna(self):
        root = self.root / 'existing-qualified-fixture-DATA'
        for name in ('tmp', 'jna-tmp'):
            (root / name).mkdir(parents=True, exist_ok=True)
        basis = _json(root / 'CONFIG.json', {'synthetic_DATA_only': True, 'requires_JNA': True,
                      'fixture308': {'Windows_JNA_required': True, 'task_root': root.as_posix(),
                      'effective_fixture_properties': {'java.io.tmpdir': (root / 'tmp').as_posix(), 'jna.tmpdir': (root / 'jna-tmp').as_posix()}}})
        helper = root / 'fixture308-source-DATA.py'
        helper.write_text('# Synthetic metadata pin only; never imported or executed.\n', encoding='utf-8')
        fixture = {'requires_JNA': True, 'basis': basis, 'helper': _pin(helper)}
        self.request['fixture'] = fixture
        self.declaration['fixture'] = fixture
        self.save_declaration()


class MultiProductionRecipeDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if Path(__file__).resolve().drive.upper() != 'D:':
            raise unittest.SkipTest('The qualified profile uses isolated D outputs')
        path = Path(__file__).resolve().parents[1] / 'prepare_verification_recipe.py'
        spec = importlib.util.spec_from_file_location('new_two_production_recipe', path)
        cls.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.api)

    def scratch(self):
        temp = tempfile.TemporaryDirectory(prefix='multiprod-DATA-', dir=Path(__file__).parent)
        self.addCleanup(temp.cleanup)
        return _Pair(Path(temp.name))

    def rejected(self, fixture, code, action):
        with self.assertRaises(self.api.RecipeError) as error:
            action()
        self.assertEqual(code, error.exception.code)
        self.assertFalse((fixture.output / 'tests').exists())

    def test_coherent_pair_has_one_ordered_command_and_actual_shared_prefix(self):
        f = self.scratch()
        ready = self.api.prepare_production(f.request_path)
        config = _read(f.output / 'production/CONFIG.json')
        args = _tokens(f.output / 'production/PROD.args')
        self.assertEqual(14, len(args))
        self.assertEqual([f.prod.as_posix(), f.consumer.as_posix()], args[-2:])
        self.assertEqual([_pin(f.prod), _pin(f.consumer)], config['phases']['prod']['sources'])
        self.assertEqual(2, config['productionTUs'])
        self.assertEqual(1, sum(item.startswith('@') for item in config['phases']['prod']['command']))
        self.assertNotIn('data.Production.Signal', config['qualifiedDirectAndSamePackageFamilies'])
        self.assertEqual('data/Production$Signal.class', config['coherentProductionFamilies']['data.Production.Signal'])
        self.assertFalse(list((f.output / 'production/classes').rglob('*.class')))
        actual, verified = f.produced()
        self.api.prepare_tests(ready, actual, verified)
        test = _read(f.output / 'tests/CONFIG.json')
        for name, relative in (('data.Production', 'data/Production.class'), ('data.Consumer', 'data/Consumer.class'), ('data.Production.Signal', 'data/Production$Signal.class')):
            binding = test['named_current_API_families'][name]
            self.assertEqual(0, binding['index'])
            self.assertEqual(_pin(f.output / 'production/classes' / relative), binding['pin'])
            self.assertIn(binding['pin'], _read(actual['path'])['classes'])
        tt = _tokens(f.output / 'tests/TEST.args')
        self.assertEqual([(f.output / 'production/classes').as_posix(), f.jar.as_posix(), *f.entries], tt[tt.index('-cp') + 1].split(';'))

    def test_cardinality_duplicates_and_old_sdk_selected_family_are_refused(self):
        for case in ('zero', 'one', 'three', 'duplicate', 'old-sdk'):
            with self.subTest(case=case):
                f = self.scratch()
                pair = f.request['production_sources']
                if case == 'old-sdk':
                    f.declaration['families']['data.Production.Signal'] = dict(f.family)
                    f.save_declaration()
                    code = 'SDK_QUALIFICATION'
                else:
                    f.request['production_sources'] = {'zero': [], 'one': pair[:1], 'three': pair + pair[:1], 'duplicate': [pair[0], pair[0]]}[case]
                    f.save_request()
                    code = 'REQUEST_SCHEMA' if case == 'duplicate' else 'UNSUPPORTED_PROFILE'
                self.rejected(f, code, lambda: self.api.prepare_production(f.request_path))
                self.assertFalse(f.output.exists())

    def test_partial_actual_family_or_single_tu_receipt_cannot_prepare_Test(self):
        for missing, source_tus in (('Consumer.class', 2), ('Production$Signal.class', 2), (None, 1)):
            with self.subTest(missing=missing, source_tus=source_tus):
                f = self.scratch()
                ready = self.api.prepare_production(f.request_path)
                actual, verified = f.produced(missing=missing, source_tus=source_tus)
                code = 'PRODUCTION_NOT_VERIFIED' if source_tus == 1 else 'OUTPUT_MANIFEST'
                self.rejected(f, code, lambda: self.api.prepare_tests(ready, actual, verified))

    def test_explicit_JNA_fixture_is_pinned_owned_and_keeps_Native_budget(self):
        f = self.scratch()
        f.jna()
        ready = self.api.prepare_production(f.request_path)
        actual, verified = f.produced()
        self.api.prepare_tests(ready, actual, verified)
        config = _read(f.output / 'tests/CONFIG.json')
        properties = config['fixture']['effective_fixture_properties']
        self.assertIs(True, config['fixture']['Windows_JNA_required'])
        self.assertEqual((f.output / 'tests/tmp').as_posix(), properties['java.io.tmpdir'])
        self.assertEqual((f.output / 'tests/jna-tmp').as_posix(), properties['jna.tmpdir'])
        for value in properties.values():
            self.assertTrue(Path(value).is_dir() and Path(value).is_relative_to(f.output))
        self.assertEqual(['C:/jdk-21/bin/java.exe', '-Xmx128m', '-XX:ActiveProcessorCount=1'], config['phases']['junit']['command'][:3])
        for key in ('basis', 'helper'):
            self.assertIn(f.request['fixture'][key], config['pins'])
        g = self.scratch()
        g.jna()
        # Actual basis drift after admitted Native declaration must fail before outputs.
        Path(g.request['fixture']['basis']['path']).write_bytes(b'{}\n')
        self.rejected(g, 'PIN_MISMATCH', lambda: self.api.prepare_production(g.request_path))
        self.assertFalse(g.output.exists())


if __name__ == '__main__':
    unittest.main()
