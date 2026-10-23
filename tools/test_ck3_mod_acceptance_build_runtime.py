from __future__ import annotations
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PROGRAM = HERE / 'ck3_mod_acceptance_build_runtime.py'
spec = importlib.util.spec_from_file_location('candidate_public_runtime_builder', PROGRAM)
if spec is None or spec.loader is None:
    raise ValueError('Actual runtime builder import route unavailable')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)
MACHINE = 'synthetic-owned-fixture-machine'


class QualifiedNativeConsumer(unittest.TestCase):
    """Synthetic owned files exercise real qualification consumer; no EXE or game runs."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ck3-runtime-consumer-')
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.native = self.root / builder.NATIVE_PREFIX
        self.native.mkdir(parents=True)
        for name, raw in [('src/dll.cpp', b'int dll_source;'), ('src/protocol.cpp', b'int protocol_source;'), ('CMakeLists.txt', b'# fixture root')]:
            path = self.native / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(raw)
        def git(*args):
            return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()
        git('init', '-q')
        git('add', '.')
        git('-c', 'user.name=finite-consumer', '-c', 'user.email=finite@example.invalid', 'commit', '-qm', 'synthetic input fixture')
        self.commit = git('rev-parse', 'HEAD')
        self.snapshot_root = self.base / 'snapshot'
        shutil.copytree(self.native, self.snapshot_root)
        self.build = self.base / 'build'
        self.build.mkdir()
        self.reply = self.build / '.cmake/api/v1/reply'
        self.reply.mkdir(parents=True)
        self.exe = self.build / 'finite_fixture.exe'
        self.exe.write_bytes(b'owned executable identity, deliberately not executed')
        self.dll = self.build / 'bridge.dll'
        self.dll.write_bytes(b'owned production DLL identity, deliberately not loaded')
        self.published = self.base / 'published.dll'
        self.published.write_bytes(self.dll.read_bytes())
        self.old_dll = self.base / 'previous.dll'
        self.old_dll.write_bytes(b'previous DLL')
        self.log = self.base / 'owned.log'
        self.log.write_bytes(b'synthetic test metadata; no child was launched\n')
        self.profile = {'machine_id': MACHINE, 'repository_default_flags_changed': False,
                        'flags': {flag: 'OFF' for flag in builder.FORBIDDEN_OLD_FLAGS}}
        self.snapshot = {'machine_id': MACHINE, 'root_commit': self.commit,
                         'Root_native_source_base': str(self.native), 'snapshot_native_base': str(self.snapshot_root),
                         'files': [{'native_relative': path.relative_to(self.snapshot_root).as_posix(),
                                    **builder.sig(path.read_bytes())} for path in sorted(self.snapshot_root.rglob('*')) if path.is_file()]}
        self.snapshot['source_count'] = len(self.snapshot['files'])
        self.targets = [
            {'id': 'dll', 'name': 'xar_ck3_bridge', 'type': 'SHARED_LIBRARY', 'dependencies': [{'id': 'protocol'}],
             'sources': [{'path': 'src/dll.cpp', 'compileGroupIndex': 0}], 'compileGroups': [],
             'artifacts': [{'path': 'bridge.dll'}]},
            {'id': 'protocol', 'name': 'xar_bridge_protocol', 'type': 'STATIC_LIBRARY',
             'sources': [{'path': 'src/protocol.cpp', 'compileGroupIndex': 0}], 'compileGroups': [], 'artifacts': []},
            {'id': 'finite', 'name': 'finite_fixture', 'type': 'EXECUTABLE',
             'sources': [], 'compileGroups': [], 'artifacts': [{'path': 'finite_fixture.exe'}]},
        ]
        self.model = {'paths': {'source': str(self.snapshot_root), 'build': str(self.build)},
                      'configurations': [{'targets': [{'id': row['id'], 'name': row['name'], 'jsonFile': row['id'] + '.json'} for row in self.targets]}]}
        self.index = {'objects': []}
        self.execution = {'machine_id': MACHINE, 'started_at_utc': '2026-10-20T00:00:00+00:00',
                          'finished_at_utc': '2026-10-20T00:00:01+00:00', 'original_wait_returncode': 0,
                          'stopped_reason': None, 'game_started_or_attached': False,
                          'actual_live_business_qualified': False, 'log': builder.pin(self.log)}
        self.fixture_execution = {**self.execution, 'argv': [str(self.exe)]}
        self.defender = {'status': 'verified', 'admin_token': True,
                         'missing_requested_paths': [], 'verified_requested_paths': [str(self.exe)]}
        self.delivery_live = False
        self.defender_hash_mode = 'semantic'
        self.flush()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, value):
        path = self.base / (name + '.json')
        path.write_bytes(builder.encoded(value))
        return builder.pin(path)

    def flush(self):
        for row in self.targets:
            (self.reply / (row['id'] + '.json')).write_bytes(builder.encoded(row))
        model_path = self.reply / 'model.json'
        model_path.write_bytes(builder.encoded(self.model))
        index_path = self.reply / 'index.json'
        index_path.write_bytes(builder.encoded(self.index))
        compile_path = self.build / 'compile_commands.json'
        compile_path.write_bytes(b'[]\n')
        profile = self.put('profile', self.profile)
        old_profile = self.put('old-profile', {**self.profile, 'flags': {flag: 'OFF' for flag in builder.FORBIDDEN_OLD_FLAGS}})
        self.old_manifest = {'capabilities': {'ck3_take_snapshot': {'actual_production_freeze': self.put('old-freeze',
            {'published_DLL': builder.pin(self.old_dll), 'profile': old_profile})}}}
        snapshot = self.put('snapshot', self.snapshot)
        source_verification = self.put('source-verification', {'machine_id': MACHINE, 'root_commit': self.commit,
            'source_manifest': snapshot, 'all_snapshot_files_exactly_verified': len(self.snapshot['files']),
            'all_original_inputs_still_exactly_verified': len(self.snapshot['files'])})
        self.scope = {'machine_id': MACHINE, 'snapshot': snapshot, 'no_fixture_in_production': True,
            'production_TUs': {'xar_ck3_bridge': 1, 'xar_bridge_protocol': 1}, 'requested_EXEs': ['finite_fixture'],
            'targets': [{k: row.get(k, []) for k in ('name', 'type', 'sources', 'compileGroups', 'artifacts')} for row in self.targets],
            'codemodel': builder.pin(model_path), 'index': builder.pin(index_path), 'compile_commands': builder.pin(compile_path)}
        scope = self.put('scope', self.scope)
        build_execution = self.put('build-execution', {**self.execution, 'argv': ['owned-fake-cmake', '--build']})
        fixture_execution = self.put('fixture-execution', self.fixture_execution)
        fixtures = [{'target': 'finite_fixture', 'executable': builder.pin(self.exe), 'execution': fixture_execution}]
        freeze = self.put('freeze', {'machine_id': MACHINE, 'root_commit': self.commit,
            'no_fixture_target_in_production_dependency_closure': True, 'repository_default_flags_changed': False,
            'game_started_or_attached': False, 'original_DLL': builder.pin(self.dll), 'published_DLL': builder.pin(self.published),
            'build_execution': build_execution, 'source_manifest': snapshot, 'source_verification': source_verification,
            'profile': profile, 'scope': scope})
        defender_manifest = self.put('defender-manifest', {'files': [{'path': str(self.exe), 'size': self.exe.stat().st_size,
            'sha256': builder.pin(self.exe)['sha256'], 'target': 'finite_fixture'}]})
        semantic = hashlib.sha256(json.dumps(builder.read(defender_manifest['path']), sort_keys=True).encode()).hexdigest()
        defender = self.put('defender', {**self.defender,
            'manifest_sha256': semantic if self.defender_hash_mode == 'semantic' else defender_manifest['sha256']})
        binding = self.put('defender-binding', {'machine_id': MACHINE, 'status': 'verified',
            'exact_executable_count': 1, 'manifest': defender_manifest, 'receipt': defender})
        delivery = self.put('delivery', {'machine_id': MACHINE, 'actual_live_business_qualified': self.delivery_live,
            'all_original_build_and_fixture_Popen_waits_recorded': True, 'snapshot': snapshot, 'profile': profile,
            'scope': scope, 'source_verification': source_verification, 'production_freeze': freeze,
            'published_dll': builder.pin(self.published), 'Defender_settings_verified': binding,
            'finite_tests': [{'name': row['target'], 'execution': row['execution'], 'exe': row['executable']} for row in fixtures]})
        self.qualification = {'schema': 'ck3-qualified-native-build-v1', 'machine_id': MACHINE,
            'source_commit': self.commit, 'actual_live_business_qualified': False, 'delivery': delivery,
            'snapshot': snapshot, 'profile': profile, 'configured_scope': scope, 'source_verification': source_verification,
            'production_freeze': freeze, 'original_dll': builder.pin(self.dll), 'published_dll': builder.pin(self.published),
            'production_build_receipt': build_execution, 'defender_binding': binding, 'fixture_results': fixtures}
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])

    def consume(self):
        return builder.qualify_native(self.qualification_path, self.root, self.commit, MACHINE,
                                     builder.pin(self.old_dll), self.old_manifest)

    def test_real_consumer_accepts_complete_exact_owned_input(self):
        result = self.consume()
        self.assertEqual(len(result['native_files']), 2)
        self.assertEqual(result['dll'], builder.pin(self.published))
        self.assertEqual(result['qualification_ref'], builder.pin(self.qualification_path))

    def test_argc2_finite_wire_emitter_allowed_and_pinned(self):
        self.fixture_execution['argv'].append(str(self.base / 'new-wire-dir'))
        self.flush()
        self.assertEqual(len(self.consume()['native_files']), 2)

    def test_wrong_machine_rejected(self):
        self.qualification['machine_id'] = 'other-machine'
        self.put('qualification', self.qualification)
        with self.assertRaisesRegex(ValueError, 'committed qualified-native-build'):
            self.consume()

    def test_wrong_commit_rejected(self):
        self.qualification['source_commit'] = '0' * 40
        self.put('qualification', self.qualification)
        with self.assertRaisesRegex(ValueError, 'production freeze'):
            self.consume()

    def test_metadata_only_descendant_preserves_actual_native_compile_commit(self):
        (self.root / 'new_public_tool.py').write_bytes(b'# independent metadata producer\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=finite-consumer', '-c', 'user.email=finite@example.invalid',
                        'commit', '-qm', 'metadata producer only'], cwd=self.root, check=True, capture_output=True)
        native_commit = self.commit
        self.commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.root, check=True,
                                     capture_output=True, text=True).stdout.strip()
        self.assertEqual(self.consume()['compile_commit'], native_commit)

    def test_semantic_defender_hash_required_instead_of_raw_json_hash(self):
        self.defender_hash_mode = 'raw'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Administrative Defender readback'):
            self.consume()

    def test_published_dll_mutation_rejected(self):
        self.published.write_bytes(b'replaced DLL')
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Published production DLL differs'):
            self.consume()

    def test_nonzero_original_wait_rejected(self):
        self.fixture_execution['original_wait_returncode'] = 1
        self.flush()
        with self.assertRaisesRegex(ValueError, 'original finite Popen.wait zero'):
            self.consume()

    def test_unknown_original_wait_rejected(self):
        self.fixture_execution['original_wait_returncode'] = None
        self.flush()
        with self.assertRaisesRegex(ValueError, 'original finite Popen.wait zero'):
            self.consume()

    def test_ack_does_not_replace_admin_readback(self):
        self.defender['admin_token'] = False
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Administrative Defender readback'):
            self.consume()

    def test_missing_exact_defender_path_rejected(self):
        self.defender['verified_requested_paths'] = []
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Administrative Defender readback'):
            self.consume()

    def test_live_credit_cannot_be_imported(self):
        self.delivery_live = True
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Original completed build'):
            self.consume()

    def test_profile_expansion_rejected(self):
        self.profile['flags'][builder.FORBIDDEN_OLD_FLAGS[0]] = 'ON'
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Old feast Start and unqualified cost helpers must stay OFF'):
            self.consume()

    def test_missing_tracked_source_rejected(self):
        self.snapshot['files'] = [row for row in self.snapshot['files'] if row['native_relative'] != 'src/protocol.cpp']
        self.snapshot['source_count'] = len(self.snapshot['files'])
        self.flush()
        with self.assertRaisesRegex(ValueError, 'omitted or added current Root tracked inputs'):
            self.consume()

    def test_dirty_actual_root_rejected(self):
        (self.native / 'src/dll.cpp').write_bytes(b'dirty source')
        with self.assertRaisesRegex(ValueError, 'Actual current Root must be clean'):
            self.consume()

    def test_new_untracked_native_input_rejected(self):
        (self.native / 'untracked.hpp').write_bytes(b'new input')
        with self.assertRaisesRegex(ValueError, 'Actual current Root must be clean'):
            self.consume()

    def test_test_target_cannot_enter_production_closure(self):
        self.targets[0]['dependencies'].append({'id': 'finite'})
        self.flush()
        with self.assertRaisesRegex(ValueError, 'Fixture dependency entered production'):
            self.consume()

    def test_production_artifact_binding_rejected(self):
        self.targets[0]['artifacts'] = [{'path': 'other.dll'}]
        self.flush()
        with self.assertRaisesRegex(ValueError, 'not the actual File API production artifact'):
            self.consume()

    def test_fixture_artifact_binding_rejected(self):
        self.targets[2]['artifacts'] = [{'path': 'another.exe'}]
        self.flush()
        with self.assertRaisesRegex(ValueError, 'not its actual configured artifact'):
            self.consume()

    def test_native_path_escape_rejected(self):
        self.snapshot['files'][0]['native_relative'] = '../escape.cpp'
        self.flush()
        with self.assertRaises(ValueError):
            self.consume()

    def test_missing_qualified_input_creates_no_runtime(self):
        absent = self.base / 'not-delivered.json'
        with self.assertRaises(FileNotFoundError):
            builder.qualify_native(absent, self.root, self.commit, MACHINE, builder.pin(self.old_dll), self.old_manifest)
        self.assertFalse((self.base / 'runtime.local.json').exists())

    def wire_fixture(self):
        folder = self.base / 'wire'
        folder.mkdir()
        names = ['read.json', 'can-select-false.json', 'quote-dynamic-index.json', 'start-pending.json',
                 'start-unknown.json', 'post-pending.json', 'post-full-generation.json', 'quote-unavailable.json',
                 'hajj-read.json', 'hajj-quote.json', 'hajj-start.json',
                 'worldly-read.json', 'worldly-quote.json', 'worldly-start.json']
        for name in names:
            (folder / name).write_bytes(b'{"owned_synthetic_packet":true}\n')
        provenance = folder / 'PROVENANCE.json'
        provenance.write_bytes(builder.encoded({'owned_result_dtos': True, 'game_queried': False, 'native_runtime_qualified': False}))
        self.fixture_execution['argv'].append(str(folder))
        self.flush()
        row = self.qualification['fixture_results'][0]
        value = {'machine_id': MACHINE, 'actual_live_business_qualified': False,
                 'source': builder.pin(self.snapshot_root / 'src/dll.cpp'), 'executable': row['executable'],
                 'execution': row['execution'], 'packets': [builder.pin(folder / name) for name in names],
                 'provenance': builder.pin(provenance)}
        ref = self.put('wire-packets', value)
        return ref, value, folder

    def test_fourteen_actual_pinned_packet_contract(self):
        ref, _value, folder = self.wire_fixture()
        result = builder.qualified_execution_packets(ref, self.qualification['fixture_results'], self.snapshot_root, MACHINE)
        self.assertEqual(result['folder'], str(folder))

    def test_unreported_extra_packet_file_rejected(self):
        ref, _value, folder = self.wire_fixture()
        (folder / 'unexpected.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'omitted or unexpected files'):
            builder.qualified_execution_packets(ref, self.qualification['fixture_results'], self.snapshot_root, MACHINE)

    def test_packet_ack_is_not_finite_fixture_execution(self):
        _ref, value, _folder = self.wire_fixture()
        value['execution'] = self.qualification['production_build_receipt']
        ref = self.put('wire-packets', value)
        with self.assertRaisesRegex(ValueError, 'actual qualified finite fixture'):
            builder.qualified_execution_packets(ref, self.qualification['fixture_results'], self.snapshot_root, MACHINE)

    def test_packet_live_provenance_rejected(self):
        _ref, value, folder = self.wire_fixture()
        path = folder / 'PROVENANCE.json'
        path.write_bytes(builder.encoded({'owned_result_dtos': True, 'game_queried': True, 'native_runtime_qualified': True}))
        value['provenance'] = builder.pin(path)
        ref = self.put('wire-packets', value)
        with self.assertRaisesRegex(ValueError, 'cannot imply live qualification'):
            builder.qualified_execution_packets(ref, self.qualification['fixture_results'], self.snapshot_root, MACHINE)

    def freezer_input(self):
        candidate = PROGRAM.parent / 'ck3_mod_acceptance_freeze_sources.py'
        spec = importlib.util.spec_from_file_location('actual_public_source_freezer', candidate)
        freezer = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'ck3_mod_acceptance_build_runtime': builder}):
            spec.loader.exec_module(freezer)
        base_commit = self.commit
        tool = self.root / 'tools/metadata_producer.py'
        tool.parent.mkdir()
        tool.write_bytes(b'# new source metadata\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True, capture_output=True)
        subprocess.run(['git', '-c', 'user.name=finite-consumer', '-c', 'user.email=finite@example.invalid',
                        'commit', '-qm', 'new committed metadata tool'], cwd=self.root, check=True, capture_output=True)
        current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=self.root, check=True,
                                       capture_output=True, text=True).stdout.strip()
        source = self.put('source-index', {'schema': 'ck3-common-source-index-v1', 'files': {}})
        native = self.put('native-index', {'schema': 'ck3-common-native-source-index-v1', 'files': {}})
        host = builder.pin(self.native / 'src/dll.cpp')
        manifest = self.put('base-manifest', {'schema': 'ck3-mod-acceptance-shared-runtime-v1', 'machine_id': MACHINE,
            'source_commit': base_commit, 'host': {'path_key': 'host', **{k: host[k] for k in ('bytes', 'sha256')}},
            'source_index': {'path_key': 'source_index', **{k: source[k] for k in ('bytes', 'sha256')}},
            'native_source_index': {'path_key': 'native_source_index', **{k: native[k] for k in ('bytes', 'sha256')}},
            'native': {name: {'path_key': name, **{k: ref[k] for k in ('bytes', 'sha256')}}
                       for name, ref in [('dll', builder.pin(self.old_dll)), ('injector', builder.pin(self.exe))]}})
        runtime = self.put('base-runtime', {'schema': 'ck3-mod-acceptance-runtime-v1', 'repo_root': str(self.root),
            'machine_id': MACHINE, 'manifest': manifest,
            'paths': {'host': host['path'], 'source_index': source['path'], 'native_source_index': native['path'],
                      'dll': str(self.old_dll), 'injector': str(self.exe)}})
        scene = self.base / 'admitted-scene'
        scene.mkdir()
        grant = self.put('grant', {'schema': 'ck3-capture-scene-admission-v1', 'machine_id': MACHINE, 'active': True, 'approved_root': str(scene),
            'observed_at_utc': '2020-01-01T00:00:00+00:00', 'expires_at_utc': '2099-01-01T00:00:00+00:00',
            'required_free_bytes': 1})
        args = types.SimpleNamespace(base_runtime=Path(runtime['path']), source_commit=current_commit,
            scene_root=scene, storage_admission=Path(grant['path']), output=scene / 'source-freeze')
        identity = types.SimpleNamespace(current_machine_id=lambda: MACHINE)
        return freezer, args, identity

    def test_public_freezer_captures_actual_complete_committed_diff(self):
        freezer, args, identity = self.freezer_input()
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            delta_ref = freezer.freeze(args)
        delta = builder.read(delta_ref['path'])
        self.assertEqual([row['path'] for row in delta['changes']], ['tools/metadata_producer.py'])
        self.assertEqual(delta['source_commit'], args.source_commit)
        self.assertEqual(delta['changes'][0]['after'], builder.sig(b'# new source metadata\n'))
        self.assertFalse((args.output / 'runtime.local.json').exists())

    def test_public_freezer_refuses_dirty_head_before_output(self):
        freezer, args, identity = self.freezer_input()
        (self.root / 'tools/metadata_producer.py').write_bytes(b'dirty')
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            with self.assertRaisesRegex(ValueError, 'Actual Root must be clean'):
                freezer.freeze(args)
        self.assertFalse(args.output.exists())

    def test_public_freezer_refuses_wrong_declared_commit(self):
        freezer, args, identity = self.freezer_input()
        args.source_commit = self.commit
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            with self.assertRaisesRegex(ValueError, 'Actual Root must be clean'):
                freezer.freeze(args)
        self.assertFalse(args.output.exists())

    def test_public_freezer_refuses_output_outside_grant(self):
        freezer, args, identity = self.freezer_input()
        args.output = self.base / 'outside-scene'
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            with self.assertRaisesRegex(ValueError, 'fresh metadata child'):
                freezer.freeze(args)
        self.assertFalse(args.output.exists())

    def test_public_freezer_rejects_output_inside_actual_root(self):
        freezer, args, identity = self.freezer_input()
        grant = builder.read(args.storage_admission)
        grant['approved_root'] = str(self.root)
        args.scene_root = self.root
        args.output = self.root / 'forbidden-source-output'
        args.storage_admission = Path(self.put('grant', grant)['path'])
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            with self.assertRaisesRegex(ValueError, 'fresh metadata child'):
                freezer.freeze(args)
        self.assertFalse(args.output.exists())
        self.assertFalse(subprocess.run(['git', 'status', '--porcelain'], cwd=self.root, check=True,
                                        capture_output=True, text=True).stdout.strip())

    def test_public_freezer_rejects_build_only_grant_before_output(self):
        freezer, args, identity = self.freezer_input()
        grant = builder.read(args.storage_admission)
        grant['schema'] = 'ck3-native-build-admission-v1'
        args.storage_admission = Path(self.put('grant', grant)['path'])
        with patch.dict(sys.modules, {'ck3_live_run_id': identity}):
            with self.assertRaisesRegex(ValueError, 'fresh next-scene storage admission'):
                freezer.freeze(args)
        self.assertFalse(args.output.exists())

    def test_independent_research_and_obs_changes_are_indexed_without_requalification(self):
        selected = self.root / 'ck3_autonomous_player/src/xar_autoplayer/example.py'
        selected.parent.mkdir(parents=True)
        selected.write_bytes(b'# research notes: tools/g2_saved_campaign/example.py\nvalue = 1\n')
        paths = ['tools/g2_saved_campaign/new_research.py', '_runtime/official-ci.json', 'tools/ck3_obs_capture.py']
        self.assertEqual(builder.check_index_only_changes(self.root, paths), paths)
        self.assertEqual(builder.classify(paths[0]), set())
        self.assertEqual(builder.classify(paths[1]), set())
        self.assertEqual(builder.classify(paths[2]), set())

    def test_research_implementation_cannot_be_silently_index_only_after_selected_import(self):
        selected = self.root / 'ck3_autonomous_player/src/xar_autoplayer/example.py'
        selected.parent.mkdir(parents=True)
        selected.write_bytes(b'from tools.g2_saved_campaign import actual_dependency\n')
        with self.assertRaisesRegex(ValueError, 'selected runtime import'):
            builder.check_index_only_changes(self.root, ['tools/g2_saved_campaign/actual_dependency.py'])


class ProfileExpansionConsumer(unittest.TestCase):
    """Owned files test profile expansion through the real public consumer."""
    put = QualifiedNativeConsumer.put
    flush = QualifiedNativeConsumer.flush
    consume = QualifiedNativeConsumer.consume
    tearDown = QualifiedNativeConsumer.tearDown

    def setUp(self):
        QualifiedNativeConsumer.setUp(self)
        reviewed = builder.read(HERE / 'ck3_mod_acceptance_native_profile_expansions.json')
        self.new_flags = list(reviewed['flag_changes'])
        self.profile['flags'].update({name: 'ON' for name in self.new_flags})
        self.targets[0]['compileGroups'] = [{'defines': [{'define': name + '=1'} for name in self.new_flags]}]
        self.targets[1]['compileGroups'] = [{'defines': []}]
        self.targets[2].update({'sources': [{'path': 'src/dll.cpp', 'compileGroupIndex': 0}],
                                'compileGroups': [{'defines': [{'define': 'XAR_B11_PROFILE_MASK=0'}]}],
                                'dependencies': [{'id': 'protocol'}]})
        self.contract = {'schema': 'ck3-native-profile-expansion-contract-v1', 'contract_id': 'owned-five-gate-test',
            'before_flags': {flag: 'OFF' for flag in builder.FORBIDDEN_OLD_FLAGS},
            'flag_changes': {name: {'before': None, 'after': 'ON'} for name in self.new_flags},
            'production_TUs': {'xar_ck3_bridge': 1, 'xar_bridge_protocol': 1},
            'production_source_lists': {'xar_ck3_bridge': ['src/dll.cpp'], 'xar_bridge_protocol': ['src/protocol.cpp']},
            'production_macro_contracts': [{'target': 'xar_ck3_bridge', 'native_relative': 'src/dll.cpp',
                'present': [name + '=1' for name in self.new_flags], 'absent': ['XAR_OWNED_UNDEFINED']}],
            'fixture_contracts': [{'target': 'finite_fixture', 'translation_units': 1,
                'dependency_targets': ['finite_fixture', 'xar_bridge_protocol'],
                'required_defines': ['XAR_B11_PROFILE_MASK=0']}],
            'fixture_sources': {'finite_fixture': ['src/dll.cpp']},
            'fixture_included_bodies': {'finite_fixture': ['src/protocol.cpp']}}
        contract_path = self.root / builder.PROFILE_EXPANSION_RELATIVE
        contract_path.parent.mkdir(parents=True)
        contract_path.write_bytes(builder.encoded(self.contract))
        self.git('add', '.')
        self.git('-c', 'user.name=finite-consumer', '-c', 'user.email=finite@example.invalid',
                 'commit', '-qm', 'reviewed owned profile expansion')
        self.commit = self.git('rev-parse', 'HEAD')
        self.snapshot['root_commit'] = self.commit
        self.expand_flush()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=True).stdout.strip()

    def expand_flush(self):
        self.flush()
        self.expansion = {'schema': 'ck3-native-profile-expansion-v1', 'machine_id': MACHINE,
            'source_commit': self.commit, 'actual_live_business_qualified': False,
            'contract_id': self.contract['contract_id'], 'contract': builder.pin(self.root / builder.PROFILE_EXPANSION_RELATIVE),
            'previous_profile': builder.pin(self.base / 'old-profile.json'),
            **{name: self.qualification[name] for name in ('profile', 'snapshot', 'configured_scope', 'production_freeze')},
            'fixture_results': self.qualification['fixture_results'],
            'fixture_source_bindings': {name: builder.pin(self.snapshot_root / name)
                                        for name in ('src/dll.cpp', 'src/protocol.cpp')}}
        self.save_expansion()

    def save_expansion(self):
        self.qualification['profile_expansion'] = self.put('profile-expansion', self.expansion)
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])

    def test_reviewed_expansion_real_consumer_accepts(self):
        result = self.consume()
        self.assertEqual(result['profile_expansion'], self.qualification['profile_expansion'])
        self.assertEqual(len(result['native_files']), 2)

    def test_long_workspace_reads_exact_old_contract_and_rejects_changed_blob(self) -> None:
        # Git for Windows stats the revision:path token relative to cwd before
        # reading the object; use an actual long root on every CI TEMP layout.
        prefix = 'long-profile-'
        padding = max(0, 195 - len(tempfile.gettempdir()) - 43 - len(prefix))
        with tempfile.TemporaryDirectory(prefix=prefix + 'x' * padding) as long_parent:
            with patch.object(tempfile, 'tempdir', long_parent):
                owned = ProfileExpansionConsumer()
                try:
                    owned.setUp()
                    object_spec = owned.commit + ':' + builder.PROFILE_EXPANSION_RELATIVE
                    self.assertGreater(len(str(owned.root)) + 1 + len(object_spec), 260)
                    result = owned.consume()
                    self.assertEqual(result['profile_expansion'], owned.qualification['profile_expansion'])
                    contract = owned.root / builder.PROFILE_EXPANSION_RELATIVE
                    contract.write_bytes(contract.read_bytes() + b'\n')
                    owned.expansion['contract'] = builder.pin(contract)
                    owned.save_expansion()
                    with self.assertRaisesRegex(ValueError, 'differs from the actual native compile commit'):
                        owned.consume()
                finally:
                    if hasattr(owned, 'temp'):
                        owned.tearDown()

    def test_missing_actual_expansion_is_rejected(self):
        self.qualification.pop('profile_expansion')
        self.qualification_path = Path(self.put('qualification', self.qualification)['path'])
        with self.assertRaisesRegex(ValueError, 'preserves the prior reviewed'):
            self.consume()

    def test_sixth_unreviewed_flag_is_rejected(self):
        self.profile['flags']['XAR_OWNED_EXTRA'] = 'ON'
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'outside the reviewed exact delta'):
            self.consume()

    def test_wrong_machine_or_compile_identity_is_rejected(self):
        self.expansion['source_commit'] = '0' * 40
        self.save_expansion()
        with self.assertRaisesRegex(ValueError, 'native compile commit and machine'):
            self.consume()

    def test_contract_must_be_in_actual_compile_commit(self):
        path = self.root / builder.PROFILE_EXPANSION_RELATIVE
        path.write_bytes(path.read_bytes() + b'\n')
        self.expansion['contract'] = builder.pin(path)
        self.save_expansion()
        with self.assertRaisesRegex(ValueError, 'differs from the actual native compile commit'):
            self.consume()

    def test_actual_scope_pin_cannot_be_substituted(self):
        self.expansion['configured_scope'] = self.expansion['profile']
        self.save_expansion()
        with self.assertRaisesRegex(ValueError, 'actual pin differs: configured_scope'):
            self.consume()

    def test_production_source_change_with_same_count_is_rejected(self):
        self.targets[0]['sources'][0]['path'] = 'src/protocol.cpp'
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'production source bodies differ'):
            self.consume()

    def test_missing_new_production_macro_is_rejected(self):
        self.targets[0]['compileGroups'][0]['defines'].pop()
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'per-TU present/absent macros differ'):
            self.consume()

    def test_zero_valued_macro_is_still_defined(self):
        self.targets[0]['compileGroups'][0]['defines'].append({'define': 'XAR_OWNED_UNDEFINED=0'})
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'per-TU present/absent macros differ'):
            self.consume()

    def test_fixture_body_change_with_same_count_is_rejected(self):
        self.targets[2]['sources'][0]['path'] = 'src/protocol.cpp'
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'fixture source bodies differ'):
            self.consume()

    def test_fixture_mask_must_be_actual_compile_definition(self):
        self.targets[2]['compileGroups'][0]['defines'] = [{'define': 'XAR_B11_PROFILE_MASK=1'}]
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'fixture compile definitions differ'):
            self.consume()

    def test_fixture_actual_dependency_closure_is_required(self):
        self.targets[2]['dependencies'] = []
        self.expand_flush()
        with self.assertRaisesRegex(ValueError, 'fixture dependency closure differs'):
            self.consume()

    def test_included_body_pin_cannot_be_omitted(self):
        self.expansion['fixture_source_bindings'].pop('src/protocol.cpp')
        self.save_expansion()
        with self.assertRaisesRegex(ValueError, 'direct/included body pins differ'):
            self.consume()

    def test_later_metadata_commit_keeps_actual_native_commit(self):
        native_commit = self.commit
        (self.root / 'metadata.txt').write_text('owned metadata only', encoding='utf-8')
        self.git('add', '.')
        self.git('-c', 'user.name=finite-consumer', '-c', 'user.email=finite@example.invalid',
                 'commit', '-qm', 'owned descendant metadata')
        self.commit = self.git('rev-parse', 'HEAD')
        result = self.consume()
        self.assertEqual(result['compile_commit'], native_commit)
        self.assertNotEqual(result['compile_commit'], self.commit)


class CapabilityRegistrationConsumer(unittest.TestCase):
    """List the actual common MCP factory; invoke no game or business method."""
    FIRST_FOUR = {
        'required_mcp_tools': [
            'ck3_enshrine_holy_site_relic_v1', 'ck3_get_capabilities', 'ck3_observe_normal_exit_v1',
            'ck3_open_holy_site_creation_window_v1', 'ck3_open_holy_site_window_v1', 'ck3_open_player_inventory_window_v1',
            'ck3_query_campaign_root_context_v1', 'ck3_query_character_skill_effects_v1',
            'ck3_query_current_event_window_context_v1', 'ck3_query_ingame_ui_window_v1', 'ck3_query_normal_exit_context_v1',
            'ck3_query_pending_character_interaction_context_v1', 'ck3_query_player_artifact_personal_use_action_post_v1',
            'ck3_query_player_artifact_personal_use_v1', 'ck3_query_player_holy_site_creation_context_v1',
            'ck3_query_player_holy_site_relic_action_context_v1', 'ck3_query_player_holy_site_relic_context_v1',
            'ck3_query_player_holy_site_relic_permissions_v1', 'ck3_query_player_holy_site_v1',
            'ck3_query_player_inventory_window_open_post_v1', 'ck3_query_player_religion_context_v1',
            'ck3_remove_holy_site_relic_v1', 'ck3_reply_pending_character_interaction', 'ck3_request_normal_exit_v1',
            'ck3_select_event_option', 'ck3_select_holy_site_creation_barony_v1', 'ck3_select_holy_site_creation_type_v1',
            'ck3_select_holy_site_relic_artifact_v1', 'ck3_set_holy_site_creation_artifact_selection_v1',
            'ck3_set_holy_site_relic_slot_selection_v1', 'ck3_submit_player_artifact_personal_use_v1', 'ck3_take_snapshot'],
        'opt_in_read_only_mcp_tools': [
            'ck3_query_character_skill_effects_v1', 'ck3_query_player_artifact_personal_use_v1',
            'ck3_query_player_holy_site_creation_context_v1', 'ck3_query_player_holy_site_relic_action_context_v1',
            'ck3_query_player_holy_site_relic_context_v1', 'ck3_query_player_holy_site_relic_permissions_v1',
            'ck3_query_player_holy_site_v1', 'ck3_query_player_religion_context_v1'],
        'opt_in_holy_site_creation_ui': True, 'opt_in_holy_site_relic_actions': True,
        'opt_in_player_artifact_personal_use_actions': True, 'opt_in_player_inventory_window_open': True,
    }
    GHW = {
        'required_mcp_tools': [
            'ck3_get_capabilities', 'ck3_inspect_gui_window_tree_v1', 'ck3_observe_normal_exit_v1',
            'ck3_open_ingame_decisions_v1', 'ck3_query_current_event_window_context_v1',
            'ck3_query_ingame_decision_item_v1', 'ck3_query_normal_exit_context_v1',
            'ck3_query_player_ghw_permissions_v1', 'ck3_query_player_holy_site_v1',
            'ck3_query_player_pilgrimage_activities_v1', 'ck3_query_player_religion_context_v1',
            'ck3_query_player_rite_governance_v1', 'ck3_request_normal_exit_v1', 'ck3_select_event_option',
            'ck3_select_ingame_decision_item_v1', 'ck3_take_snapshot'],
        'opt_in_read_only_mcp_tools': ['ck3_query_player_ghw_permissions_v1', 'ck3_query_player_holy_site_v1',
            'ck3_query_player_pilgrimage_activities_v1', 'ck3_query_player_religion_context_v1',
            'ck3_query_player_rite_governance_v1'],
    }

    @staticmethod
    def registered(case):
        import asyncio
        sys.path.insert(0, str(HERE.parent / 'ck3_autonomous_player/src'))
        from xar_autoplayer.bridge.mcp_server import create_server

        async def names():
            return {row.name for row in await create_server(builder.registration_driver(case)).list_tools()}
        return asyncio.run(names())

    def test_actual_factory_lists_all_first_four_32_tools(self):
        self.assertEqual(len(self.FIRST_FOUR['required_mcp_tools']), 32)
        self.assertLessEqual(set(self.FIRST_FOUR['required_mcp_tools']), self.registered(self.FIRST_FOUR))

    def test_actual_factory_lists_ghw_16_and_optional_hof_confirm(self):
        self.assertLessEqual(set(self.GHW['required_mcp_tools']), self.registered(self.GHW))
        self.assertIn('ck3_confirm_ingame_decision_outcome_v1', self.registered(self.GHW))
        self.assertFalse(builder.registration_driver(self.GHW).allow_private_player_artifact_personal_use_actions)

    def test_undeclared_new_features_remain_unregistered(self):
        names = self.registered({})
        for tool in ('ck3_submit_player_artifact_personal_use_v1', 'ck3_query_player_artifact_personal_use_action_post_v1',
                     'ck3_query_player_artifact_personal_use_v1', 'ck3_query_player_ghw_permissions_v1',
                     'ck3_query_character_skill_effects_v1', 'ck3_open_player_inventory_window_v1',
                     'ck3_query_player_inventory_window_open_post_v1'):
            self.assertNotIn(tool, names)

    def test_read_only_declaration_does_not_enable_artifact_action(self):
        case = {'opt_in_read_only_mcp_tools': ['ck3_query_player_artifact_personal_use_v1']}
        names = self.registered(case)
        self.assertIn('ck3_query_player_artifact_personal_use_v1', names)
        self.assertNotIn('ck3_submit_player_artifact_personal_use_v1', names)
        self.assertNotIn('ck3_query_player_artifact_personal_use_action_post_v1', names)

    def test_selected_new_capability_rules_cover_exact_five_flags(self):
        reviewed = builder.read(HERE / 'ck3_mod_acceptance_native_profile_expansions.json')
        new_tools = ['ck3_submit_player_artifact_personal_use_v1', 'ck3_query_player_artifact_personal_use_action_post_v1',
                     'ck3_query_player_artifact_personal_use_v1', 'ck3_query_player_ghw_permissions_v1',
                     'ck3_query_character_skill_effects_v1', 'ck3_open_player_inventory_window_v1',
                     'ck3_query_player_inventory_window_open_post_v1']
        self.assertEqual({flag for tool in new_tools for flag in builder.EXTRA_CAPABILITIES[tool]},
                         set(reviewed['flag_changes']))


class CompleteMetadataBudget(unittest.TestCase):
    def test_serialized_package_at_exact_limit_round_trips_all_bytes(self) -> None:
        output = {
            'source-index.json': builder.encoded({'files': {str(i): {'bytes': i} for i in range(2552)}}),
            'shared-host.py': b'# retained complete host\n' * 20000,
        }
        limit = sum(map(len, output.values())) + 32768
        with tempfile.TemporaryDirectory(prefix='ck3-metadata-bound-') as temp:
            destination = Path(temp) / 'new-runtime'
            builder.write_bounded_metadata(destination, output, limit_bytes=limit,
                                           reserve_bytes=32768)
            self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, output)

    def test_one_byte_over_limit_creates_no_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix='ck3-metadata-bound-') as temp:
            destination = Path(temp) / 'rejected'
            with self.assertRaisesRegex(ValueError, 'Complete serialized metadata'):
                builder.write_bounded_metadata(destination, {'complete.bin': b'x' * 101},
                                               limit_bytes=100, reserve_bytes=0)
            self.assertFalse(destination.exists())

    def test_boolean_budget_is_not_an_integer_byte_count(self) -> None:
        with self.assertRaisesRegex(ValueError, 'exact integer'):
            builder.validate_metadata_bound({'one': b'x'}, limit_bytes=True, reserve_bytes=0)

    def test_large_complete_delta_reaches_actual_freeze_writer(self) -> None:
        """Reproduce the real 2552-path failure through freeze(), not a mock writer."""
        freeze_spec = importlib.util.spec_from_file_location(
            'complete_metadata_actual_freeze', HERE / 'ck3_mod_acceptance_freeze_sources.py')
        self.assertIsNotNone(freeze_spec)
        if freeze_spec is None or freeze_spec.loader is None:
            raise AssertionError('Actual source-freeze producer unavailable')
        freeze = importlib.util.module_from_spec(freeze_spec)
        freeze_spec.loader.exec_module(freeze)
        with tempfile.TemporaryDirectory(prefix='ck3-complete-delta-') as temp:
            base = Path(temp)
            root, scene = base / 'repo', base / 'scene'
            root.mkdir()
            scene.mkdir()
            (root / 'docs').mkdir()
            names = [f'docs/metadata-source-{i:04d}.md' for i in range(2552)]
            for name in names:
                (root / name).write_bytes(b'actual source bytes\n')
            native_index = base / 'native-index.json'
            native_index.write_bytes(builder.encoded({'files': {}}))
            observed = datetime.now(timezone.utc)
            admission = base / 'admission.json'
            admission.write_bytes(builder.encoded({'schema': 'owned-next-scene-admission-v1',
                'machine_id': MACHINE, 'active': True, 'approved_root': str(scene),
                'observed_at_utc': observed.isoformat(),
                'expires_at_utc': (observed + timedelta(minutes=5)).isoformat(),
                'required_free_bytes': 0}))
            commit = 'a' * 40
            runtime = {'repo_root': str(root), 'machine_id': MACHINE}
            manifest = {'machine_id': MACHINE, 'source_commit': 'b' * 40}
            refs = {'native_source_index': {'path': str(native_index)}}
            (base / 'base.json').write_bytes(builder.encoded(runtime))
            args = Namespace(base_runtime=base / 'base.json', scene_root=scene,
                             storage_admission=admission, output=scene / 'frozen', source_commit=commit)

            def actual_diff(_root: Path, arguments: list[str], *, binary: bool = False) -> tuple[object, list[str]]:
                if arguments[0] == 'rev-parse':
                    return commit, ['git', *arguments]
                if arguments[0] == 'status':
                    return '', ['git', *arguments]
                self.assertTrue(binary)
                return ('\0'.join(names) + '\0').encode(), ['git', *arguments]

            with patch.object(freeze.builder, 'load_base', return_value=(runtime, manifest, refs, {'files': {}})), \
                 patch.object(freeze, 'git', side_effect=actual_diff), \
                 patch.dict(sys.modules, {'ck3_live_run_id': types.SimpleNamespace(current_machine_id=lambda: MACHINE)}):
                result = freeze.freeze(args)
            delta = json.loads(Path(result['path']).read_bytes())
            self.assertEqual([row['path'] for row in delta['changes']], names)
            self.assertEqual(len(delta['changes']), 2552)
            self.assertGreater(sum(p.stat().st_size for p in args.output.iterdir()), 256 * 1024)
            self.assertLessEqual(sum(p.stat().st_size for p in args.output.iterdir()) + 16384,
                                 1024 * 1024)


class WireEvidenceRuntimeProducer(unittest.TestCase):
    """Actual metadata writer/Selection/adapter/factory; upstream Native qualification is owned fixture data."""

    def test_feature_json_round_trip_preserves_boolean_features_and_one_codec(self) -> None:
        original = {'saved_campaign_debug_mode': True, 'wire_evidence_codec': 'plain'}
        result = builder.wire_evidence_runtime_features(json.loads(json.dumps(original)), 'gzip-members')
        self.assertEqual(json.loads(json.dumps(result)),
                         {'saved_campaign_debug_mode': True, 'wire_evidence_codec': 'gzip-members'})
        self.assertEqual(original['wire_evidence_codec'], 'plain')
        self.assertEqual(builder.wire_evidence_runtime_features({}, 'plain'), {'wire_evidence_codec': 'plain'})

    def test_explicit_invalid_base_and_requested_codecs_are_never_defaulted(self) -> None:
        for invalid in (None, False, True, 0, 1, 1.0, '', 'gzip', [], {}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    builder.wire_evidence_runtime_features({'wire_evidence_codec': invalid}, 'plain')
                with self.assertRaises(ValueError):
                    builder.wire_evidence_runtime_features({}, invalid)
        for invalid_features in (None, [], 'plain', {1: True}):
            with self.subTest(features=invalid_features), self.assertRaises(ValueError):
                builder.wire_evidence_runtime_features(invalid_features, 'plain')

    def test_formal_cli_rejects_unknown_codec_before_reading_or_writing(self) -> None:
        argv = [part for name in ('base-runtime', 'source-delta', 'scene-root', 'storage-admission',
                                  'products', 'case-inputs', 'output', 'qualified-native')
                for part in ('--' + name, 'not-read')]
        argv += ['--source-commit', 'a' * 40, '--product', 'faith-engine', '--case', 'not-selected',
                 '--wire-evidence-codec', 'gzip']
        with patch.object(builder, 'load_base') as load, self.assertRaises(SystemExit) as result:
            builder.main(argv)
        self.assertEqual(result.exception.code, 2)
        load.assert_not_called()

    def test_formal_runtime_producer_reaches_actual_consumers_for_legacy_and_gzip(self) -> None:
        for codec in (None, 'gzip-members'):
            with self.subTest(codec=codec):
                self.assert_formal_runtime_producer(codec)

    def test_faith_ui_capabilities_reach_actual_runtime_cli_and_sdk_consumers(self) -> None:
        faith_tools = (
            'ck3_open_faith_window_v1', 'ck3_present_faith_power_ui_v1',
            'ck3_query_faith_power_ui_v1', 'ck3_query_faith_power_tooltip_v1',
        )
        for codec in (None, 'gzip-members'):
            with self.subTest(codec=codec, flags='ON'):
                self.assert_formal_runtime_producer(codec, extra_tools=faith_tools)
        for tool in faith_tools:
            for flag in ('OFF', None):
                with self.subTest(tool=tool, flag=flag):
                    self.assert_formal_runtime_producer(
                        None, extra_tools=(tool,), presentation_flag=flag,
                        expected_error='Qualified profile lacks required flag')
        with self.subTest(tool='unknown'):
            self.assert_formal_runtime_producer(
                None, extra_tools=('ck3_unreviewed_faith_tool_v1',),
                expected_error='Unreviewed global capability rule')

    def assert_formal_runtime_producer(
        self, codec: str | None, *, extra_tools: tuple[str, ...] = (),
        presentation_flag: str | None = 'ON', expected_error: str | None = None,
    ) -> None:
        # Real metadata writer and complete downstream consumers; upstream Native input is owned fixture data.
        from test_ck3_mod_acceptance import SharedEntryTests, entry
        owned = SharedEntryTests()
        owned.setUp()
        try:
            root = HERE.parent
            scene = owned.root / 'next-scene'
            scene.mkdir()
            (scene / 'managed-states').mkdir()
            destination = scene / 'generated-runtime'
            native_dir = owned.root / 'old-native/build'
            native_dir.mkdir(parents=True)
            dll = native_dir / 'bridge.dll'
            dll.write_bytes(b'owned DLL identity; never loaded')
            owned.paths.update(source_root=root, dll=dll)
            owned.runtime.update(repo_root=str(root), machine_id=MACHINE,
                                 paths={key: str(value) for key, value in owned.paths.items()}, allocation={})
            owned.manifest.update(machine_id=MACHINE, entry_environment={'PYTHONPATH_parts': [
                {'path_key': 'source_root'}, {'root_key': 'source_root', 'relative_path': 'ck3_autonomous_player/src'},
                {'root_key': 'source_root', 'relative_path': 'tools'}]})
            owned.host.write_text('# Explicit static normal-exit binding projection; ordinary shared host remains above.\n'
                                  'from pathlib import Path\n_runtime_path = Path(' + repr(str(owned.runtime_path)) + ')\n'
                                  'if __name__ == "__main__":\n    raise SystemExit(main())\n', encoding='utf-8')
            owned.manifest['host'].update(builder.sig(owned.host.read_bytes()))
            owned.manifest['native']['dll'].update(builder.sig(dll.read_bytes()))
            case_id = 'faith-engine-e02-pilgrimage-mechanism-v2'
            tools = ['ck3_take_snapshot', 'ck3_query_player_pilgrimage_planner_v1',
                     'ck3_submit_player_pilgrimage_planner_v1', 'ck3_query_player_pilgrimage_activities_v1',
                     'ck3_query_player_religion_context_v1', *extra_tools]
            owned.manifest['capabilities'] = {tool: {'source_build_ready': True, 'actual_live_qualified': False}
                                               for tool in tools if tool not in extra_tools}
            contract_path = owned.root / 'case-contract.json'
            saved = owned.case['startup']['saved_campaign']
            contract = {'schema': 'faith-engine-e02-pilgrimage-mechanism-case-v2', 'product': 'faith-engine',
                        'case': case_id, 'machine_id': MACHINE,
                        'saved_input': {key: saved[key] for key in ('save', 'bytes', 'sha256', 'player_id', 'date_raw')},
                        'profile': {'enabled_mods': [], 'product_files': []}, 'expected_actor_character_id': 1,
                        'prior_scene_date_raw': 10, 'expected_faith_id': 50, 'expected_rite_id': 13,
                        'option_key': 'pilgrimage_type_hajj', 'scope': {'new_save_allowed': False},
                        'policy': {'reserve_gold_raw': 0, 'max_journey_days': 30, 'max_day_requests': 60,
                                   'max_public_requests': 500, 'max_events': 16, 'one_day_timeout': 60,
                                   'quit_reserve_seconds': 120}}
            owned.write(contract_path, contract)
            owned.case.update(id=case_id, required_mcp_tools=tools, opt_in_player_pilgrimage_execution=True,
                              opt_in_read_only_mcp_tools=['ck3_query_player_pilgrimage_activities_v1',
                                                          'ck3_query_player_religion_context_v1'], adapter={
                                  'module': 'tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_adapter',
                                  'config': str(contract_path)})
            products = {'schema': entry.PRODUCTS_SCHEMA, 'product_inventory': str(owned.files['inventory']),
                        'products': {'faith-engine': {'cases': [owned.case]}}}
            owned.write(owned.products_path, products)
            owned.write(owned.manifest_path, owned.manifest)
            owned.runtime['manifest'] = entry.pin(owned.manifest_path)
            owned.write(owned.runtime_path, owned.runtime)
            observed = datetime.now(timezone.utc)
            grant, diff, delta, inputs = [owned.root / name for name in ('grant.json', 'diff.json', 'delta.json', 'inputs.json')]
            owned.write(grant, {'schema': 'owned-next-scene-admission-v1', 'machine_id': MACHINE, 'active': True,
                                'approved_root': str(scene), 'observed_at_utc': observed.isoformat(),
                                'expires_at_utc': (observed + timedelta(minutes=5)).isoformat(), 'required_free_bytes': 0})
            owned.write(diff, {'observed_at_utc': observed.isoformat()})
            owned.write(delta, {'Root_diff_receipt': builder.pin(diff), 'new_scene_admission': builder.pin(grant)})
            owned.write(inputs, {'case_inputs': {}})
            files = {path.relative_to(root).as_posix(): builder.sig(path.read_bytes())
                     for path in (root / 'tools').glob('ck3_mod_acceptance*.py')}
            for relative in [builder.HOST_RELATIVE, 'promo/ck3_native_war_ai/integration/recorder_job.py',
                             *(builder.SDK_PREFIX + 'xar_autoplayer/bridge/' + name for name in builder.CRITICAL_TRANSPORTS)]:
                files[relative] = builder.sig((root / relative).read_bytes())
            refs = {name: builder.pin(owned.paths[name]) for name in ('host', 'dll', 'source_index', 'native_source_index')}
            identity = builder.pin(owned.files['inventory'])
            flags = {} if presentation_flag is None else {'XAR_ENABLE_RELIGION_UI12004_PRESENTATION': presentation_flag}
            bundle = {'old_profile': {'flags': {}}, 'profile': {'flags': flags}, 'profile_ref': identity,
                      'freeze_ref': identity, 'qualification_ref': identity, 'dll': builder.pin(dll),
                      'native_files': {}, 'snapshot_root': str(native_dir), 'compile_commit': 'a' * 40,
                      'source_checkout_binding': None, 'shared_python_host_delta': None, 'execution_wire': None}
            argv = [part for name, path in (('base-runtime', owned.runtime_path), ('source-delta', delta),
                    ('scene-root', scene), ('storage-admission', grant), ('products', owned.products_path),
                    ('case-inputs', inputs), ('output', destination), ('qualified-native', owned.files['inventory']))
                    for part in ('--' + name, str(path))]
            argv += ['--source-commit', 'a' * 40, '--product', 'faith-engine', '--case', case_id]
            if codec is not None:
                argv += ['--wire-evidence-codec', codec]
            with patch.object(builder, 'load_base', return_value=(owned.runtime, owned.manifest, refs, {'files': files})), \
                 patch.object(builder, 'apply_delta', return_value=(files, set(), [])), \
                 patch.object(builder, 'qualify_native', return_value=bundle), \
                 patch.dict(sys.modules, {'ck3_live_run_id': types.SimpleNamespace(current_machine_id=lambda: MACHINE)}), \
                 redirect_stdout(io.StringIO()) as stdout:
                if expected_error is not None:
                    with self.assertRaisesRegex(ValueError, expected_error):
                        builder.main(argv)
                    self.assertFalse(destination.exists())
                    return
                self.assertEqual(builder.main(argv), 0)
            selected_codec = 'plain' if codec is None else codec
            manifest = builder.read(destination / 'manifest.json')
            self.assertEqual(manifest['host_features']['wire_evidence_codec'], selected_codec)
            for tool in extra_tools:
                self.assertIs(manifest['capabilities'][tool]['actual_live_qualified'], False)
                self.assertIs(manifest['capabilities'][tool]['source_build_ready'], True)
            for name in ('ENTRY-COMMANDS.json', 'SOURCE-BINDINGS.actual.json', 'STATIC-VALIDATION.actual.json'):
                self.assertEqual(builder.read(destination / name)['wire_evidence_codec'], selected_codec)
            self.assertEqual(json.loads(stdout.getvalue())['wire_evidence_codec'], selected_codec)
            selected = entry.Selection(destination / 'runtime.local.json', owned.products_path, 'faith-engine', case_id)
            self.assertEqual(selected.preflight()['blockers'], [])
            actual_source = Path(selected.argv[selected.argv.index('--agent-source-root') + 1])
            self.assertEqual(actual_source, root)
            projected_host = builder.module(destination / 'shared-host.py', 'wire_codec_actual_generated_host')
            previous_imports = list(sys.path)
            try:
                self.assertEqual(projected_host.configure_wire_evidence(Namespace(
                    agent_source_root=actual_source, wire_evidence_codec=selected_codec)), selected_codec)
            finally:
                sys.path[:] = previous_imports
            actual = builder.read(destination / 'STATIC-VALIDATION.actual.json')
            self.assertEqual(actual['public_Selection_argv'], selected.argv)
            self.assertEqual(actual['actual_registered_required_MCP_tools'], sorted(tools))
            self.assertIn('ck3_mod_acceptance_background_types.py', selected.runtime['allocator_overlay'])
            if codec is None:
                self.assertNotIn('--wire-evidence-codec', selected.argv)
            else:
                self.assertEqual(selected.argv[selected.argv.index('--wire-evidence-codec') + 1], codec)
                self.assertIn('--wire-evidence-codec', entry.host_cli_flags(destination / 'shared-host.py'))
        finally:
            owned.doCleanups()


if __name__ == '__main__':
    unittest.main(verbosity=2)
