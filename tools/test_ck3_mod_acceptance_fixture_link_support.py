"""Exercise real public native qualification over owned files, never run EXEs."""
from pathlib import Path
import importlib.util
import os
import subprocess
import unittest
from unittest.mock import patch

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


class ConfiguredPhysicalLinkConsumer(unittest.TestCase):
    """The real public qualifier consumes v2; the finite original-build proof is isolated."""
    setUp = baseline.QualifiedNativeConsumer.setUp
    tearDown = baseline.QualifiedNativeConsumer.tearDown
    put = baseline.QualifiedNativeConsumer.put
    flush = baseline.QualifiedNativeConsumer.flush
    consume = baseline.QualifiedNativeConsumer.consume
    save_support = FixtureLinkSupportConsumer.save_support

    def support(self) -> None:
        FixtureLinkSupportConsumer.support(self)
        self.configured = self.obj
        self.borrowed = self.base / 'retained original build/actual production.obj'
        self.borrowed.parent.mkdir()
        self.obj.rename(self.borrowed)
        source = builder.pin(self.snapshot_root / 'src/dll.cpp')
        row = {'configured_object': str(self.configured), 'object': builder.pin(self.borrowed),
               'production_target': 'xar_ck3_bridge', 'native_relative': 'src/dll.cpp', 'source': source,
               'configured_compile_command_index': 0}
        self.proof = builder.native_successor.FixtureObjectProof([dict(row)],
            self.put('original-plan', {'finite': 'plan'}), self.put('original-incremental', {'finite': 'result'}),
            self.put('original-commands', {'finite': 'commands'}), self.put('original-dependencies', {'finite': 'dependencies'}))
        self.rsp = self.base / 'actual fixture link.rsp'
        self.link_words = [str(self.borrowed), '/OUT:' + str(self.exe)]
        self.link_execution = {**self.execution, 'source_commit': self.commit,
            'argv': [str(self.base / 'link.exe'), '@' + str(self.rsp)], 'cwd': str(self.build), 'response_files': []}
        self.link_support.update(schema='ck3-fixture-production-object-link-support-v2',
            fixtures={'finite_fixture': [builder.pin(self.borrowed)]}, objects=[row],
            producer_config=self.put('original-config', {'source_commit': self.commit, 'machine_id': baseline.MACHINE}),
            production_plan=self.proof.production_plan,
            incremental_production_result=self.proof.incremental_production_result,
            baseline_compile_commands=self.proof.baseline_compile_commands,
            original_dependencies=self.proof.original_dependencies)
        self.save_link()
        self.boundary = patch.object(builder.native_successor, 'verified_fixture_object_bindings',
                                     side_effect=self.original_proof)
        self.boundary.start()
        self.addCleanup(self.boundary.stop)

    def original_proof(self, config: object, outputs: list[str], *, noncompiled_replay: object = None) -> object:
        # This authored physical-object fixture has no reviewed source binding.
        # Actual replay validation is exercised by the shared producer/binding tests.
        if noncompiled_replay is not None:
            raise ValueError('Authored physical-object fixture requires noncompiled_replay=None')
        self.assertEqual(config, {'source_commit': self.commit, 'machine_id': baseline.MACHINE})
        self.assertEqual(outputs, [str(self.configured)])
        return self.proof

    def save_link(self) -> None:
        self.rsp.write_text(subprocess.list2cmdline(self.link_words), encoding='utf-8')
        self.link_execution['response_files'] = [builder.pin(self.rsp)]
        self.link_support['actual_links'] = {'finite_fixture': self.put('actual-link', self.link_execution)}
        self.save_support()

    def test_real_qualifier_accepts_borrowed_physical_object_without_faking_configured_file(self) -> None:
        self.support()
        self.assertFalse(self.configured.exists())
        self.assertEqual(self.consume()['fixture_link_support'], self.qualification['fixture_link_support'])
        self.assertFalse(self.configured.exists())

    def test_boolean_and_float_compile_indices_are_rejected(self) -> None:
        self.support()
        for bad in (False, 0.0, None, '0', -1, 999):
            with self.subTest(value=bad):
                self.link_support['objects'][0]['configured_compile_command_index'] = bad
                self.save_support()
                with self.assertRaises(ValueError):
                    self.consume()

    def test_missing_unknown_or_extra_object_fields_are_rejected(self) -> None:
        self.support()
        row = dict(self.link_support['objects'][0])
        for changed in ({key: value for key, value in row.items() if key != 'configured_object'},
                        {**row, 'actual_compile_command': {}}, {**row, 'configured_object': None}):
            self.link_support['objects'] = [changed]
            self.save_support()
            with self.assertRaises(ValueError):
                self.consume()

    def test_omitted_duplicate_and_unlinked_configured_objects_are_rejected(self) -> None:
        self.support()
        row = dict(self.link_support['objects'][0])
        for changed in ([], [row, row], [{**row, 'configured_object': str(self.base / 'foreign.obj')}]):
            self.link_support['objects'] = changed
            self.save_support()
            with self.assertRaisesRegex(ValueError, 'omitted, duplicate or unlinked'):
                self.consume()

    def test_exact_current_command_index_and_source_are_required(self) -> None:
        self.support()
        self.link_support['objects'][0]['source'] = builder.pin(self.snapshot_root / 'src/protocol.cpp')
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'source pin differs'):
            self.consume()

    def test_physical_substitution_cannot_bypass_original_build_proof(self) -> None:
        self.support()
        other = self.base / 'plausible.obj'
        other.write_bytes(self.borrowed.read_bytes())
        self.link_support['objects'][0]['object'] = builder.pin(other)
        self.link_support['fixtures']['finite_fixture'] = [builder.pin(other)]
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'verified original production bindings'):
            self.consume()

    def test_changed_physical_bytes_are_rejected(self) -> None:
        self.support()
        self.borrowed.write_bytes(b'changed physical bytes')
        with self.assertRaisesRegex(ValueError, 'changed'):
            self.consume()

    def test_each_original_provenance_pin_is_required_exact(self) -> None:
        self.support()
        for field in ('production_plan', 'incremental_production_result', 'baseline_compile_commands', 'original_dependencies'):
            original = self.link_support[field]
            self.link_support[field] = self.qualification['profile']
            self.save_support()
            with self.assertRaisesRegex(ValueError, 'production provenance differs'):
                self.consume()
            self.link_support[field] = original

    def test_link_rsp_cannot_omit_duplicate_or_substitute_physical_objects(self) -> None:
        self.support()
        for words in ([str(self.configured), '/OUT:' + str(self.exe)],
                      ['/OUT:' + str(self.exe)],
                      [str(self.borrowed), str(self.borrowed), '/OUT:' + str(self.exe)],
                      [str(self.borrowed), str(self.base / 'extra.obj'), '/OUT:' + str(self.exe)]):
            self.link_words = words
            self.save_link()
            with self.assertRaisesRegex(ValueError, 'RSP object map'):
                self.consume()

    def test_link_out_must_equal_actual_file_api_fixture_executable(self) -> None:
        self.support()
        self.link_words[-1] = '/OUT:' + str(self.base / 'other.exe')
        self.save_link()
        with self.assertRaisesRegex(ValueError, 'configured EXE differs'):
            self.consume()

    def test_unknown_failed_boolean_and_wrong_machine_link_results_are_rejected(self) -> None:
        self.support()
        original = dict(self.link_execution)
        for changes in ({'original_wait_returncode': None}, {'original_wait_returncode': 1},
                        {'original_wait_returncode': False}, {'machine_id': 'other'},
                        {'source_commit': '0' * 40}, {'stopped_reason': 'timeout'}):
            self.link_execution = {**original, **changes}
            self.save_link()
            with self.assertRaisesRegex(ValueError, 'fixture link Popen.wait zero'):
                self.consume()

    def test_link_response_reference_and_working_directory_are_exact(self) -> None:
        self.support()
        for changes in ({'argv': [str(self.base / 'link.exe'), '@wrong.rsp']},
                        {'cwd': str(self.base)}, {'argv': ['relative-link.exe', '@' + str(self.rsp)]}):
            original = dict(self.link_execution)
            self.link_execution.update(changes)
            self.save_link()
            with self.assertRaisesRegex(ValueError, 'exact linker response file'):
                self.consume()
            self.link_execution = original

    def test_raw_target_sets_and_actual_file_api_pin_are_exact(self) -> None:
        self.support()
        self.link_support['actual_links']['extra'] = self.link_support['actual_links']['finite_fixture']
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'target set differs'):
            self.consume()
        self.link_support['actual_links'].pop('extra')
        self.link_support['fixture_file_api']['finite_fixture'] = self.qualification['profile']
        self.save_support()
        with self.assertRaisesRegex(ValueError, 'link File API pin differs'):
            self.consume()


if __name__ == '__main__':
    unittest.main()
