"""Exercise real public native qualification over owned files, never run EXEs."""
from pathlib import Path
import importlib.util
import os
import unittest

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('CK3_LINK_SUPPORT_TEST_ROOT', str(HERE.parent)))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load('link_support_candidate', HERE / 'ck3_mod_acceptance_build_runtime.py')
baseline = load('link_support_owned_baseline', ROOT / 'tools/test_ck3_mod_acceptance_build_runtime.py')
baseline.builder = builder


class FixtureLinkSupportConsumer(unittest.TestCase):
    setUp = baseline.QualifiedNativeConsumer.setUp
    tearDown = baseline.QualifiedNativeConsumer.tearDown
    put = baseline.QualifiedNativeConsumer.put
    flush = baseline.QualifiedNativeConsumer.flush
    consume = baseline.QualifiedNativeConsumer.consume

    def support(self):
        self.obj = self.build / 'CMakeFiles/xar_ck3_bridge.dir/src/dll.cpp.obj'
        self.obj.parent.mkdir(parents=True, exist_ok=True)
        self.obj.write_bytes(b'owned production object identity; never linked or loaded')
        self.targets[2]['link'] = {'commandFragments': [
            {'role': 'libraries', 'fragment': '"' + str(self.obj) + '"'}]}
        self.flush()
        command = {'directory': str(self.build), 'file': str(self.snapshot_root / 'src/dll.cpp'),
                   'output': str(self.obj), 'command': 'owned compiler -c src/dll.cpp -o ' + str(self.obj)}
        commands = self.build / 'compile_commands.json'
        commands.write_bytes(builder.encoded([command]))
        self.scope['compile_commands'] = builder.pin(commands)
        scope = self.put('scope', self.scope)
        self.qualification['configured_scope'] = scope
        freeze = builder.read(self.qualification['production_freeze']['path'])
        freeze['scope'] = scope
        self.qualification['production_freeze'] = self.put('freeze', freeze)
        delivery = builder.read(self.qualification['delivery']['path'])
        delivery.update(scope=scope, production_freeze=self.qualification['production_freeze'])
        self.qualification['delivery'] = self.put('delivery', delivery)
        self.link_support = {'schema': 'ck3-fixture-production-object-link-support-v1',
            'machine_id': baseline.MACHINE, 'source_commit': self.commit, 'actual_live_business_qualified': False,
            'configured_scope': scope, 'production_freeze': self.qualification['production_freeze'],
            'fixture_results': self.qualification['fixture_results'],
            'fixture_file_api': {'finite_fixture': builder.pin(self.reply / 'finite.json')},
            'fixtures': {'finite_fixture': [builder.pin(self.obj)]},
            'objects': [{'object': builder.pin(self.obj), 'production_target': 'xar_ck3_bridge',
                'native_relative': 'src/dll.cpp', 'source': builder.pin(self.snapshot_root / 'src/dll.cpp'),
                'actual_compile_command': command}]}
        if hasattr(self, 'expansion'):
            self.expansion.update({name: self.qualification[name] for name in
                ('profile', 'snapshot', 'configured_scope', 'production_freeze', 'fixture_results')})
            self.qualification['profile_expansion'] = self.put('profile-expansion', self.expansion)
        self.save_support()

    def save_support(self):
        self.qualification['fixture_link_support'] = self.put('fixture-link-support', self.link_support)
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])

    def test_old_fixture_without_external_objects_preserves_existing_route(self):
        self.assertIsNone(self.consume()['fixture_link_support'])

    def test_real_consumer_accepts_exact_actual_production_object_support(self):
        self.support()
        self.assertEqual(self.consume()['fixture_link_support'], self.qualification['fixture_link_support'])

    def test_raw_object_without_source_bound_receipt_is_rejected(self):
        self.support()
        self.qualification.pop('fixture_link_support')
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])
        with self.assertRaisesRegex(ValueError, 'exact source-bound link-support receipt'):
            self.consume()

    def test_omitted_actual_link_input_is_rejected(self):
        self.support()
        self.link_support['fixtures']['finite_fixture'] = []
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'raw-object links differ'):
            self.consume()

    def test_duplicate_or_unlinked_object_is_rejected(self):
        self.support()
        self.link_support['objects'].append(dict(self.link_support['objects'][0]))
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'omitted, duplicate or unlinked'):
            self.consume()

    def test_changed_actual_object_bytes_are_rejected(self):
        self.support()
        self.obj.write_bytes(b'changed owned object')
        with self.assertRaisesRegex(ValueError, 'Exact input changed'):
            self.consume()

    def test_fixture_object_cannot_impersonate_production_output(self):
        self.support()
        self.link_support['objects'][0]['production_target'] = 'finite_fixture'
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'selected production target output'):
            self.consume()

    def test_altered_compile_command_is_rejected(self):
        self.support()
        self.link_support['objects'][0]['actual_compile_command'] = {
            **self.link_support['objects'][0]['actual_compile_command'], 'command': 'other command'}
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'compile command differs'):
            self.consume()

    def test_wrong_production_source_pin_is_rejected(self):
        self.support()
        self.link_support['objects'][0]['source'] = builder.pin(self.snapshot_root / 'src/protocol.cpp')
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'source pin differs'):
            self.consume()

    def test_actual_link_file_api_pin_is_required(self):
        self.support()
        self.link_support['fixture_file_api']['finite_fixture'] = self.qualification['profile']
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'link File API pin differs'):
            self.consume()

    def test_unknown_execution_or_scope_cannot_substitute_actual_receipts(self):
        self.support()
        self.link_support['fixture_results'] = []
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'scope/freeze/finite execution pins differ'):
            self.consume()

    def test_quoted_paths_and_external_source_objects_are_detected(self):
        obj = self.build / 'path with spaces/support.obj'
        target = {'sources': [{'path': str(obj), 'isGenerated': True}],
                  'link': {'commandFragments': [{'fragment': '"' + str(obj) + '" user32.lib'}]}}
        self.assertEqual(builder.fixture_object_inputs(target, self.snapshot_root, self.build), {obj.resolve()})


class ProfileLinkOwnerConsumer(unittest.TestCase):
    """CMake's implicit production owner dependency follows only validated objects."""
    put = baseline.QualifiedNativeConsumer.put
    flush = baseline.QualifiedNativeConsumer.flush
    consume = baseline.QualifiedNativeConsumer.consume
    tearDown = baseline.QualifiedNativeConsumer.tearDown
    git = baseline.ProfileExpansionConsumer.git
    expand_flush = baseline.ProfileExpansionConsumer.expand_flush
    save_expansion = baseline.ProfileExpansionConsumer.save_expansion
    support = FixtureLinkSupportConsumer.support
    save_support = FixtureLinkSupportConsumer.save_support

    def setUp(self):
        baseline.ProfileExpansionConsumer.setUp(self)
        self.targets[2]['dependencies'] = [{'id': 'dll'}]
        self.support()

    def test_actual_production_owner_is_the_only_added_fixture_dependency(self):
        self.assertEqual(self.consume()['fixture_link_support'], self.qualification['fixture_link_support'])

    def test_implicit_owner_without_validated_object_support_is_rejected(self):
        self.qualification.pop('fixture_link_support')
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])
        with self.assertRaisesRegex(ValueError, 'exact source-bound link-support receipt'):
            self.consume()

    def test_unrelated_extra_dependency_still_fails_reviewed_closure(self):
        self.targets.append({'id': 'foreign', 'name': 'unreviewed_extra_target', 'type': 'STATIC_LIBRARY',
                             'sources': [], 'compileGroups': [], 'artifacts': []})
        self.model['configurations'][0]['targets'].append(
            {'id': 'foreign', 'name': 'unreviewed_extra_target', 'jsonFile': 'foreign.json'})
        self.targets[2]['dependencies'].append({'id': 'foreign'})
        self.support()
        with self.assertRaisesRegex(ValueError, 'fixture dependency closure differs'):
            self.consume()


if __name__ == '__main__':
    unittest.main()
