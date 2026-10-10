"""Synthetic leaf tests: exact derivative inputs never turn a failed launch GREEN."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocator
import ck3_mod_acceptance_graphics_cache as cache


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return cache._pin(path)


class GraphicsCacheTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[2] / 'synthetic-test-work'
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='graphics-', dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.counter = 0
        self.outer_names = ('mod/product.mod', 'mod/transaction_control.mod')
        self.run = self.root / 'source-run'
        self.old_state = self.root / 'old-state'
        (self.old_state / 'control').mkdir(parents=True)
        self.source_rows = self.business(self.old_state)
        self.runtime, self.manifest = self.runtime_fixture('source', target=False)
        self.target_runtime, self.target_manifest = self.runtime_fixture('target', target=True)
        self.source_manifest_path = self.root / 'source/manifest.json'
        self.target_manifest_path = self.root / 'target/manifest.json'
        prepared_path = self.root / 'source/prepared-case.json'
        prepared = {'runtime_manifest': self.runtime['manifest'],
                    'startup': {'state_dir': str(self.old_state)},
                    'preparation': {'profile': {'files': self.source_rows}}}
        prepared_pin = write(prepared_path, prepared)
        runtime_pin = write(self.root / 'source/runtime.local.json', self.runtime)
        frozen_files = {row['path']: cache._signature(row) for row in (prepared_pin, runtime_pin)}
        exe_pin = cache._pin(Path(self.runtime['game_dir']) / 'binaries/ck3.exe')
        frozen_files[exe_pin['path']] = cache._signature(exe_pin)
        for relative, row in self.source_rows.items():
            snapshot = self.run / 'input-snapshots/profile' / relative
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.old_state / 'profile' / relative, snapshot)
            frozen_files[str(snapshot.resolve())] = cache._signature(row)
        self.freeze = {'run_id': 'synthetic-R0044', 'screen_task': 'synthetic-closed-task',
                       'state_dir': str(self.old_state), 'source_root': self.runtime['paths']['source_root'],
                       'runtime_manifest': self.runtime['manifest'], 'files': frozen_files}
        frozen_pin = write(self.run / 'frozen-argv.json', self.freeze)
        self.original_report = {'finished_at': '2026-10-10T00:00:00Z', 'managed_session_thread_finished': True,
            'status': 'RED', 'cleanup_ok': False, 'steps': [], 'readiness': None, 'state_dir': str(self.old_state),
            'session': {'report': None, 'error': 'AgentError: native-session failed after 900.0s (launch_error): '
                'CK3 launch contract failed safely: synthetic readiness deadline'}}
        report_pin = write(self.run / 'native-report.json', self.original_report)
        started_pin = write(self.run / 'host-started.json', {'run_id': self.freeze['run_id'], 'pid': 71,
                                                           'actual_popen_retained': True})
        exited_pin = write(self.run / 'host-original-process-exit.json', {'run_id': self.freeze['run_id'], 'pid': 71,
            'actual_original_popen_wait': True, 'returncode': 1, 'normal_ck3_exit_inferred': False})
        keeper_pin = write(self.root / 'keeper/report.json', {'task_id': self.freeze['screen_task'],
                                                            'thread_exited': True, 'last_sequence': 4339})
        release_pin = write(self.root / 'release.json', {'schema': 'codex.task_bus.v1', 'ok': True,
            'task': {'task_id': self.freeze['screen_task'], 'state': 'done', 'resources': [], 'last_sequence': 4340},
            'event': {'task_id': self.freeze['screen_task'], 'sequence': 4340}})
        self.origin_pin = write(self.root / 'origin.json', {'schema': cache.ORIGIN_SCHEMA,
            'source_run_id': self.freeze['run_id'], 'evidence': {'frozen_argv': frozen_pin, 'prepared_case': prepared_pin,
                'runtime_local': runtime_pin, 'native_report': report_pin, 'host_started': started_pin,
                'host_exit': exited_pin, 'keeper_report': keeper_pin, 'release': release_pin}})
        self.source_cache = self.old_state / 'profile/shadercache'
        for relative, body in (('dx11/ps_5_0/0123456789abcdef.bin', b'synthetic-pixel-shader'),
                               ('dx11/vs_5_0/fedcba9876543210.scache', b'synthetic-vertex-cache')):
            path = self.source_cache / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)

    def business(self, state):
        profile = state / 'profile'
        bodies = {name: ('ordinary-' + name).encode() for name in cache.CONFIGS}
        bodies.update({'mod-content/product/descriptor.mod': b'name="synthetic-product"\n',
                       'mod-content/transaction_control/events/fixture.txt': b'namespace = synthetic\n',
                       'dlc_load.json': (json.dumps({'enabled_mods': list(self.outer_names), 'disabled_dlcs': []}) + '\n').encode()})
        for name in self.outer_names:
            bodies[name] = ('name="synthetic-' + Path(name).stem + '"\npath="' +
                            (profile / 'mod-content' / Path(name).stem).resolve().as_posix() + '"\n').encode()
        rows = {}
        for relative, body in bodies.items():
            path = profile / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            rows[relative] = cache._pin(path)
        return rows

    def runtime_fixture(self, name, *, target):
        root = self.root / name
        paths = {}
        for key in ('source_root',):
            path = root / key
            path.mkdir(parents=True)
            paths[key] = str(path)
        for key in ('host', 'dll', 'injector'):
            path = root / (key + '.data')
            path.write_bytes(('identical-' + key).encode())
            paths[key] = str(path)
        exe = root / 'game/binaries/ck3.exe'
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b'synthetic-identical-game-exe')
        core = {'ck3_autonomous_player/src/runtime.py': cache._signature(cache._pin(Path(paths['host'])))}
        native = {'ck3_autonomous_player/native_bridge/src/bridge.cpp': cache._signature(cache._pin(Path(paths['dll'])))}
        if target:
            core['tools/ck3_mod_acceptance_graphics_cache.py'] = cache._signature(cache._pin(cache.__file__))
            core['tools/ck3_mod_acceptance.py'] = cache._signature(cache._pin(entry.__file__))
            core['tools/ck3_mod_acceptance_allocate.py'] = cache._signature(cache._pin(allocator.__file__))
        for key, schema, rows in (('source_index', 'ck3-common-source-index-v1', core),
                                  ('native_source_index', 'ck3-common-native-source-index-v1', native)):
            path = root / (key + '.json')
            write(path, {'schema': schema, 'source_commit': name + '-test-only', 'files': rows})
            paths[key] = str(path)
        def row(key):
            return {'path_key': key, **cache._signature(cache._pin(paths[key]))}
        manifest = {'schema': entry.MANIFEST_SCHEMA, 'source_root': {'path_key': 'source_root'},
            'host': row('host'), 'source_index': row('source_index'), 'native_source_index': row('native_source_index'),
            'native': {'dll': row('dll'), 'injector': row('injector')},
            'game': {'version': 'synthetic-build', 'exe_sha256': cache._pin(exe)['sha256']},
            'host_features': {'saved_campaign_debug_mode': True}}
        if target:
            manifest['profile_features'] = {cache.FEATURE: True}
        manifest_pin = write(root / 'manifest.json', manifest)
        runtime = {'manifest': manifest_pin, 'paths': paths, 'repo_root': str(root / 'repo'),
                   'game_dir': str(root / 'game')}
        return runtime, manifest

    def seed(self):
        self.counter += 1
        with patch.object(allocator, 'runtime_process_inventory', return_value={
                'blockers': [], 'process_absence_is_normal_exit_proof': False}):
            return cache.freeze_shader_cache_seed(self.origin_pin, self.root / ('immutable-' + str(self.counter)))

    def target(self, enabled=True):
        self.counter += 1
        state = self.root / ('fresh-state-' + str(self.counter))
        rows = self.business(state)
        selection = SimpleNamespace(manifest=copy.deepcopy(self.target_manifest), runtime=copy.deepcopy(self.target_runtime),
                                    state_dir=state, prepared={'preparation': {'profile': {'files': rows}}})
        selection.manifest['profile_features'] = {cache.FEATURE: enabled}
        output = self.root / ('prepared-' + str(self.counter))
        output.mkdir()
        return selection, output

    def prepare(self, selection, output, seed_pin):
        graphics = cache.prepare_graphics_cache(selection, seed_pin, selection.prepared['preparation'], output)
        selection.prepared['graphics_cache'] = graphics
        return graphics

    def changed_seed(self, seed_pin, mutate):
        path = Path(seed_pin['path'])
        value = cache._read(path)
        mutate(value)
        return write(path, value)

    def public_selection(self, state, *, seed_pin=None, enabled=True):
        selection = entry.Selection.__new__(entry.Selection)
        selection.context = {}
        selection.case = {'id': 'synthetic', 'status': 'ready', 'budgets': {}, 'initial_plan': 'synthetic-plan.json'}
        selection.product_key = 'synthetic-product'
        selection.manifest = copy.deepcopy(self.target_manifest)
        selection.manifest['profile_features'] = {cache.FEATURE: enabled}
        selection.manifest_path = self.target_manifest_path
        selection.runtime = copy.deepcopy(self.target_runtime)
        selection.adapter_path = self.root / 'synthetic-adapter.py'
        selection.adapter_path.write_text('# Synthetic adapter input only\n')
        selection.adapter_config = self.root / 'synthetic-contract.json'
        write(selection.adapter_config, {})
        def context(output, inputs):
            return {'case_inputs': inputs}
        def prepare_case(context):
            rows = self.business(Path(context['state_dir']))
            return {'startup': {'state_dir': context['state_dir']}, 'profile': {'files': rows}}
        selection.adapter_context = context
        selection.load_adapter = lambda: SimpleNamespace(prepare_case=prepare_case)
        inputs = {'state_dir': str(state), 'case_inputs': {}}
        if seed_pin is not None:
            inputs['shader_cache_seed'] = seed_pin
        inputs_path = self.root / ('inputs-' + str(self.counter) + '.json')
        write(inputs_path, inputs)
        return selection, inputs_path

    def test_default_off_strict_boolean_and_public_opt_in(self):
        self.assertFalse(cache.profile_enabled({}))
        self.assertFalse(cache.profile_enabled({'profile_features': {cache.FEATURE: False}}))
        for value in (None, 0, 1, 'true', [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                cache.profile_enabled({'profile_features': {cache.FEATURE: value}})
        with self.assertRaises(ValueError):
            cache.profile_enabled({'profile_features': {'unknown': True}})
        selection, inputs = self.public_selection(self.root / 'off-state', seed_pin={'invalid': True}, enabled=False)
        output = self.root / 'off-output'
        with self.assertRaisesRegex(ValueError, 'default OFF'):
            selection.prepare(inputs, output)
        self.assertFalse(output.exists())
        self.assertFalse((self.root / 'off-state').exists())

    def test_public_prepare_without_seed_keeps_business_only(self):
        selection, inputs = self.public_selection(self.root / 'ordinary-state', enabled=False)
        result = selection.prepare(inputs, self.root / 'ordinary-output')
        prepared = cache._read(result['prepared_case']['path'])
        self.assertNotIn('graphics_cache', prepared)
        self.assertFalse((self.root / 'ordinary-state/profile/shadercache').exists())
        self.assertEqual(prepared['business_acceptance'], 'NOT_ASSESSED')

    def test_public_prepare_routes_opt_in_and_keeps_original_red(self):
        seed = self.seed()
        original = (self.run / 'native-report.json').read_bytes()
        selection, inputs = self.public_selection(self.root / 'public-state', seed_pin=seed)
        result = selection.prepare(inputs, self.root / 'public-output')
        prepared = cache._read(result['prepared_case']['path'])
        self.assertEqual(prepared['runtime_status'], 'NOT_RUN')
        self.assertEqual(prepared['business_acceptance'], 'NOT_ASSESSED')
        self.assertEqual(len(prepared['graphics_cache']['files']), 2)
        closure = prepared['graphics_cache']['source_closure']['failure_cleanup']
        self.assertIs(closure['original_cleanup_ok'], False)
        self.assertIsNone(closure['original_ck3_exit_code'])
        self.assertIs(closure['typed_normal_exit_proven'], False)
        self.assertIs(closure['business_pass'], False)
        self.assertEqual((self.run / 'native-report.json').read_bytes(), original)
        source = cache._read(seed['path'])
        self.assertIs(source['startup_qualified'], False)
        self.assertIs(source['business_pass'], False)
        profile = self.root / 'public-state/profile'
        for row in source['files']:
            self.assertEqual((profile / 'shadercache' / row['relative_path']).read_bytes(),
                             (self.source_cache / row['relative_path']).read_bytes())
        self.assertFalse(any(name.startswith('shadercache/') for name in prepared['preparation']['profile']['files']))

    def test_seed_and_prepared_pins_accept_only_exact_inventory(self):
        seed = self.seed()
        selection, output = self.target()
        self.prepare(selection, output, seed)
        pins = cache.validate_prepared_graphics(selection)
        self.assertIn(seed, pins)
        self.assertIn(self.origin_pin, pins)
        expected = cache.graphics_union(cache.business_files(selection.prepared['preparation']),
                                       selection.prepared['graphics_cache'], selection.state_dir / 'profile')
        observed = {path.relative_to(selection.state_dir / 'profile').as_posix(): cache._pin(path)
                    for path in (selection.state_dir / 'profile').rglob('*') if path.is_file()}
        allocator.verify_profile_inventory(expected, observed)
        extra = selection.state_dir / 'profile/shadercache/dx11/ps_5_0/1111111111111111.bin'
        extra.write_bytes(b'undeclared')
        observed[extra.relative_to(selection.state_dir / 'profile').as_posix()] = cache._pin(extra)
        with self.assertRaisesRegex(ValueError, 'Cold profile changed'):
            allocator.verify_profile_inventory(expected, observed)
        with self.assertRaisesRegex(ValueError, 'Unlisted or missing prepared'):
            cache.validate_prepared_graphics(selection)

    def test_key_rejects_canonical_configuration_game_host_and_native_changes(self):
        seed = self.seed()
        for what in ('canonical', 'configuration', 'game', 'host', 'native'):
            with self.subTest(what=what):
                selection, output = self.target()
                if what in ('canonical', 'configuration'):
                    relative = 'mod-content/product/descriptor.mod' if what == 'canonical' else cache.CONFIGS[0]
                    path = selection.state_dir / 'profile' / relative
                    path.write_bytes(b'different-declared-business-input')
                    selection.prepared['preparation']['profile']['files'][relative] = cache._pin(path)
                elif what == 'game':
                    selection.manifest['game']['exe_sha256'] = 'b' * 64
                else:
                    key = 'dll' if what == 'native' else 'host'
                    path = self.root / ('different-' + what)
                    path.write_bytes(b'different-runtime-bytes')
                    selection.runtime['paths'][key] = str(path)
                    row = {'path_key': key, **cache._signature(cache._pin(path))}
                    if what == 'native':
                        selection.manifest['native']['dll'] = row
                    else:
                        selection.manifest['host'] = row
                with self.assertRaisesRegex(ValueError, 'key mismatch|game EXE'):
                    self.prepare(selection, output, seed)
                self.assertFalse((output / 'graphics-cache-preparation.json').exists())
                self.assertFalse((selection.state_dir / 'profile/shadercache').exists())

    def test_source06_only_four_prepare_paths_may_differ(self):
        seed = self.seed()
        selection, output = self.target()
        index_path = Path(selection.runtime['paths']['source_index'])
        index = cache._read(index_path)
        index['files']['ck3_autonomous_player/src/runtime.py']['sha256'] = 'b' * 64
        row = write(index_path, index)
        selection.manifest['source_index'] = {'path_key': 'source_index', **cache._signature(row)}
        with self.assertRaisesRegex(ValueError, 'key mismatch'):
            self.prepare(selection, output, seed)

    def test_snapshot_tamper_and_public_failure_leave_no_prepared_manifest(self):
        seed = self.seed()
        manifest = cache._read(seed['path'])
        path = Path(manifest['snapshot_root']) / 'shadercache' / manifest['files'][0]['relative_path']
        original = path.read_bytes()
        path.write_bytes(b'x' * len(original))
        selection, inputs = self.public_selection(self.root / 'tampered-state', seed_pin=seed)
        output = self.root / 'tampered-output'
        with self.assertRaisesRegex(ValueError, 'bytes/SHA changed'):
            selection.prepare(inputs, output)
        self.assertFalse((output / 'prepared-case.json').exists())
        self.assertFalse((output / 'graphics-cache-preparation.json').exists())

    def test_seed_rejects_duplicate_escape_and_unlisted_file(self):
        for what in ('duplicate', 'escape', 'unlisted', 'business-path'):
            with self.subTest(what=what):
                seed = self.seed()
                if what == 'unlisted':
                    (Path(seed['path']).parent / 'unexpected.txt').write_bytes(b'extra')
                else:
                    def mutate(value):
                        if what == 'duplicate':
                            value['files'].append(copy.deepcopy(value['files'][0]))
                        else:
                            value['files'][0]['relative_path'] = '../escape.bin' if what == 'escape' else 'mod-content/product/cache.bin'
                    seed = self.changed_seed(seed, mutate)
                selection, output = self.target()
                with self.assertRaises(ValueError):
                    self.prepare(selection, output, seed)
                self.assertFalse((output / 'graphics-cache-preparation.json').exists())

    def test_link_and_nonregular_inputs_are_rejected(self):
        seed = self.seed()
        manifest = cache._read(seed['path'])
        path = Path(manifest['snapshot_root']) / 'shadercache' / manifest['files'][0]['relative_path']
        linked = self.root / 'second-hardlink.bin'
        os.link(path, linked)
        selection, output = self.target()
        with self.assertRaisesRegex(ValueError, 'unlinked file'):
            self.prepare(selection, output, seed)
        with self.assertRaisesRegex(ValueError, 'Ordinary unlinked file'):
            cache._plain_path(path.parent)

    def test_allocator_rejects_business_cache_overlap_product_path_and_byte_tamper(self):
        seed = self.seed()
        selection, output = self.target()
        graphics = self.prepare(selection, output, seed)
        business = cache.business_files(selection.prepared['preparation'])
        smuggled = dict(business)
        smuggled.update(graphics['files'])
        with self.assertRaisesRegex(ValueError, 'overlap'):
            cache.graphics_union(smuggled, graphics, selection.state_dir / 'profile')
        altered = copy.deepcopy(graphics)
        key, row = next(iter(altered['files'].items()))
        del altered['files'][key]
        altered['files']['mod-content/product/cache.bin'] = row
        receipt = {key: value for key, value in altered.items() if key != 'receipt'}
        altered['receipt'] = write(Path(graphics['receipt']['path']), receipt)
        with self.assertRaisesRegex(ValueError, 'cannot enter business/product'):
            cache.graphics_union(business, altered, selection.state_dir / 'profile')
        observed = copy.deepcopy(business)
        relative = 'mod-content/product/descriptor.mod'
        observed[relative]['sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'Cold profile changed'):
            allocator.verify_profile_inventory(business, observed)

    def test_outer_normalization_preserves_all_other_bytes_and_semantic_path(self):
        seed = self.seed()
        for body in ('name="changed"\npath="{correct}"\n',
                     'name="synthetic-product"\npath="{wrong}"\n'):
            selection, output = self.target()
            path = selection.state_dir / 'profile/mod/product.mod'
            path.write_text(body.format(correct=(selection.state_dir / 'profile/mod-content/product').as_posix(),
                                        wrong=self.old_state.as_posix()), encoding='utf-8')
            selection.prepared['preparation']['profile']['files']['mod/product.mod'] = cache._pin(path)
            with self.assertRaises(ValueError):
                self.prepare(selection, output, seed)

    def test_changed_original_pin_and_live_blocker_reject_snapshot(self):
        report_path = self.run / 'native-report.json'
        report_path.write_bytes(report_path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Pinned input changed'):
            self.seed()
        write(report_path, self.original_report)
        output = self.root / 'blocked-snapshot'
        with patch.object(allocator, 'runtime_process_inventory', return_value={'blockers': [{'pid': 71}]}):
            with self.assertRaisesRegex(ValueError, 'Active game/keeper/controller'):
                cache.freeze_shader_cache_seed(self.origin_pin, output)
        self.assertFalse(output.exists())

    def test_snapshot_rejects_source_change_after_copy_without_manifest(self):
        original_copy = cache._copy
        changed = False
        def copy_then_change(source, target, expected=None):
            nonlocal changed
            result = original_copy(source, target, expected)
            if not changed:
                path = Path(source)
                path.write_bytes(b'x' * path.stat().st_size)
                changed = True
            return result
        output = self.root / 'changed-during-snapshot'
        with patch.object(allocator, 'runtime_process_inventory', return_value={'blockers': []}), \
                patch.object(cache, '_copy', side_effect=copy_then_change):
            with self.assertRaisesRegex(ValueError, 'changed before snapshot completion'):
                cache.freeze_shader_cache_seed(self.origin_pin, output)
        self.assertFalse((output / 'manifest.json').exists())

    def test_actual_transaction_control_name_is_declared_without_product_allowlist(self):
        seed = self.seed()
        selection, output = self.target()
        graphics = self.prepare(selection, output, seed)
        self.assertEqual(len(graphics['files']), 2)
        profile_key = cache._read(seed['path'])['cache_key']['profile']
        self.assertEqual(set(profile_key['outer_descriptors']), set(self.outer_names))
        self.assertIn('mod/transaction_control.mod', profile_key['outer_descriptors'])
        self.assertIn('mod-content/transaction_control/events/fixture.txt', profile_key['canonical_mod_files'])

    def test_declared_enabled_outers_reject_unknown_duplicate_mismatch_and_escape(self):
        seed = self.seed()
        cases = {'unknown': ['mod/product.mod', 'mod/unknown.mod'],
                 'duplicate': ['mod/product.mod', 'mod/product.mod'],
                 'casefold-duplicate': ['mod/product.mod', 'mod/Product.mod'],
                 'missing': ['mod/product.mod'],
                 'escape': ['mod/product.mod', '../transaction_control.mod'],
                 'outside-mod': ['mod/product.mod', 'outside/transaction_control.mod']}
        for what, enabled in cases.items():
            with self.subTest(what=what):
                selection, output = self.target()
                path = selection.state_dir / 'profile/dlc_load.json'
                write(path, {'enabled_mods': enabled, 'disabled_dlcs': []})
                selection.prepared['preparation']['profile']['files']['dlc_load.json'] = cache._pin(path)
                with self.assertRaisesRegex(ValueError, 'outer descriptor'):
                    self.prepare(selection, output, seed)
                self.assertFalse((output / 'graphics-cache-preparation.json').exists())
        selection, output = self.target()
        path = selection.state_dir / 'profile/mod/unknown.mod'
        path.write_bytes(b'name="unknown"\npath="outside"\n')
        selection.prepared['preparation']['profile']['files']['mod/unknown.mod'] = cache._pin(path)
        with self.assertRaisesRegex(ValueError, 'business inventory'):
            self.prepare(selection, output, seed)

    def test_enabled_outer_must_own_declared_canonical_tree_and_single_path(self):
        seed = self.seed()
        for what in ('different-tree', 'two-paths', 'noncanonical-second-path'):
            with self.subTest(what=what):
                selection, output = self.target()
                rows = selection.prepared['preparation']['profile']['files']
                if what == 'different-tree':
                    relative = 'mod-content/transaction_control/events/fixture.txt'
                    del rows[relative]
                    target = selection.state_dir / 'profile/mod-content/other/events/fixture.txt'
                    target.parent.mkdir(parents=True)
                    target.write_bytes(b'namespace = synthetic\n')
                    rows[target.relative_to(selection.state_dir / 'profile').as_posix()] = cache._pin(target)
                else:
                    path = selection.state_dir / 'profile/mod/transaction_control.mod'
                    with path.open('ab') as stream:
                        stream.write(b'path="outside"\n' if what == 'two-paths' else b' path = "outside"\n')
                    rows['mod/transaction_control.mod'] = cache._pin(path)
                with self.assertRaises(ValueError):
                    self.prepare(selection, output, seed)
                self.assertFalse((output / 'graphics-cache-preparation.json').exists())


if __name__ == '__main__':
    unittest.main()
