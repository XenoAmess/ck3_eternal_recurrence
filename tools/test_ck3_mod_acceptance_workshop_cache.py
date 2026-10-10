"""Portable production-seam cache tests; no SDK, game, process or desktop.

CK3_CACHE_TEST_REFERENCE_ROOT is only for an external source overlay: it supplies
unchanged canonical registry and exact-cache helpers from the reviewed tree.
Normal CI uses this checkout directly.
"""
from pathlib import Path
import copy
from datetime import datetime, timezone
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path(os.environ.get('CK3_CACHE_TEST_REFERENCE_ROOT', ROOT)).resolve()
sys.path.insert(0, str(REFERENCE / 'tools'))
sys.path.insert(0, str(ROOT / 'tools'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


entry = load('workshop_cache_shared_entry_under_test', ROOT / 'tools/ck3_mod_acceptance.py')
adapter = load('workshop_cache_adapter_under_test', ROOT / 'tools/ck3_mod_acceptance_cases/workshop_cache_adapter.py')
prepare = sys.modules['ck3_mod_acceptance_prepare']
base_tests = load('shared_entry_test_fixtures', REFERENCE / 'tools/test_ck3_mod_acceptance.py')
base_tests.entry = entry


class WorkshopCacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = adapter.read_json(REFERENCE / 'workshop/products.json')
        self.product = next(row for row in self.registry['products'] if row['key'] == 'tributary-expansion-directives')
        self.item = self.product['workshop_item_id']
        self.cache = self.root / 'steamapps/workshop/content/1158310' / self.item
        self.cache.mkdir(parents=True)
        self.canonical_descriptor = b'name="Cache fixture"\nversion="1.0.1"\nsupported_version="1.20.*"\n'
        self.files = {'descriptor.mod': self.canonical_descriptor, 'common/scripted_effects/sample.txt': b'sample = { }\n'}
        for relative, raw in self.files.items():
            target = self.cache / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        self.manifest = {'format_version': 1, 'git_tag': 'tributary-expansion-directives-v1.0.1',
            'git_sha': 'a' * 40, 'workshop_item_id': self.item,
            'files': [{'path': relative, 'size': len(raw), 'sha256': adapter.pin(self.cache / relative)['sha256']}
                      for relative, raw in sorted(self.files.items())]}
        self.manifest_path = self.root / 'manifest.json'
        self.write(self.manifest_path, self.manifest)
        self.download = {'ok': True, 'status': 'complete', 'started': True, 'error': None,
            'app_id': 1158310, 'item_id': self.item,
            'callback': {'app_id': 1158310, 'item_id': self.item, 'result': 1},
            'install_info': {'path': str(self.cache)},
            'state_flags': {'installed': True, 'needs_update': False, 'downloading': False, 'download_pending': False},
            'worker_exit_code': 0}
        self.download_path = self.root / 'native-download.json'
        self.write(self.download_path, {'ok': True, 'tool': 'workshop_native_download', 'result': self.download})
        configs = {}
        for number, name in enumerate(prepare.CONFIG_NAMES):
            source = self.root / 'frozen-config' / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(('ordinary=' + str(number)).encode())
            configs[name] = adapter.pin(source)
        self.context = {'repo_root': str(REFERENCE), 'state_dir': str(self.root / 'state'),
            'output': str(self.root / 'prepared'), 'run_id': 'synthetic-only-R0001',
            'product': self.product['key'], 'product_spec': self.product, 'case': 'workshop_cache',
            'canonical_products_path': str(REFERENCE / 'workshop/products.json'),
            'case_contract': adapter.read_json(ROOT / 'tools/ck3_mod_acceptance_cases/workshop_cache.json'),
            'shared_game': {'version': '1.20.0.4', 'exe_sha256': '9' * 64},
            'case_inputs': {'cache_path': str(self.cache), 'formal_manifest': adapter.pin(self.manifest_path),
                'native_download_receipt': adapter.pin(self.download_path), 'plain_configuration': configs}}

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def prepared(self):
        with mock.patch('subprocess.run', side_effect=AssertionError('Preparation must never launch')):
            return adapter.prepare_case(self.context)

    def report(self):
        profile = Path(self.context['state_dir']) / 'profile'
        startup_path = Path(self.context['state_dir']) / 'preparation.json'
        created = '20261008120000.123456+000'
        process = {'pid': 42, 'create_time': adapter.wmi_epoch(created),
                   'retained_synchronize_query_handle_acquired': True}
        report = {'error': None,
            'frontend_mod_load_launch': {'status': 'ACTUAL_SINGLE_MENU_LAUNCH_RECORDED', 'pid': 42,
                'ck3_creation_date': created, 'profile_dir': str(profile),
                'actual_command': ['synthetic-ck3.exe', '-userdir=' + str(profile)],
                'continue_last_save': False, 'load_save_name': None},
            'frontend_mod_load_profile': {'profile_dir': str(profile), 'preparation_path': str(startup_path),
                'preparation_sha256': adapter.pin(startup_path)['sha256'], 'preparation': adapter.read_json(startup_path)},
            'frontend_mod_load_observation': {'status': 'ACTUAL_STABLE_MAIN_MENU_OBSERVED_READ_ONLY',
                'identity': {'bridge_pid': 42, 'connection_generation': 1, 'pipe_name': 'synthetic-pipe',
                    'native_build': {'version': '1.20.0.4', 'executable_sha256': '9' * 64}},
                'proof': {'status': 'CONSISTENT_VISIBLE_FRONTEND_SCOPE', 'route': 'main_menu',
                    'scope_root_name': 'mainmenu_panel_bottom', 'consecutive_consistent_observations': 2,
                    'widgets': [{'visible': True}, {'visible': True}]},
                'route': {'raw': 'synthetic'}, 'tree': {'raw': 'synthetic'},
                'campaign_started': False, 'actions_submitted': 0,
                'actual_cache_mount_proven': False, 'product_acceptance_proven': False}}
        return report, process

    def test_external_cache_preparation_exact_and_no_copy_or_fixture(self):
        before = {name: adapter.pin(self.cache / name) for name in self.files}
        result = self.prepared()
        profile = Path(self.context['state_dir']) / 'profile'
        self.assertEqual(result['startup']['mode'], 'workshop_cache')
        self.assertEqual(set(result['files']), set(prepare.CONFIG_NAMES) | {'mod/product.mod', 'dlc_load.json'})
        self.assertFalse((profile / 'mod-content').exists())
        self.assertEqual({p.relative_to(profile).as_posix() for p in profile.rglob('*') if p.is_file()},
                         set(prepare.CONFIG_NAMES) | {'mod/product.mod', 'dlc_load.json'})
        self.assertEqual(adapter.read_json(profile / 'dlc_load.json')['enabled_mods'], ['mod/product.mod'])
        outer = (profile / 'mod/product.mod').read_text(encoding='utf-8')
        self.assertIn('path="' + self.cache.as_posix() + '"', outer)
        self.assertIn('remote_file_id="' + self.item + '"', outer)
        self.assertNotIn('remote_file_id', (self.cache / 'descriptor.mod').read_text())
        self.assertEqual(before, {name: adapter.pin(self.cache / name) for name in self.files})
        self.assertEqual(adapter.read_json(result['initial_plan']['path']), {'steps': []})
        self.assertFalse(result['business_pass'])
        self.assertFalse((Path(self.context['output']) / 'frontend-fixture-start-policy.json').exists())

    def test_existing_descriptor_injection_exception_is_exact(self):
        (self.cache / 'descriptor.mod').write_bytes(self.canonical_descriptor + ('remote_file_id="' + self.item + '"\n').encode())
        result = self.prepared()
        strict = adapter.read_json(result['exact_cache']['path'])
        self.assertEqual(strict['descriptor']['remote_file_id'], self.item)
        self.assertEqual(strict['descriptor']['policy'], 'launcher-injected')

    def test_corrupt_extra_or_wrong_injected_id_rejected_before_profile(self):
        for mode in ('corrupt', 'extra', 'wrong_item'):
            with self.subTest(mode=mode):
                if mode == 'corrupt': (self.cache / 'common/scripted_effects/sample.txt').write_bytes(b'wrong')
                if mode == 'extra': (self.cache / 'extra.txt').write_bytes(b'extra')
                if mode == 'wrong_item':
                    (self.cache / 'descriptor.mod').write_bytes(self.canonical_descriptor + b'remote_file_id="3596263413"\n')
                with self.assertRaises(ValueError): self.prepared()
                self.assertFalse(Path(self.context['state_dir']).exists())
                (self.cache / 'common/scripted_effects/sample.txt').write_bytes(self.files['common/scripted_effects/sample.txt'])
                (self.cache / 'extra.txt').unlink(missing_ok=True)
                (self.cache / 'descriptor.mod').write_bytes(self.canonical_descriptor)

    def test_sdk_incomplete_wrong_app_item_path_or_callback_rejected(self):
        mutations = [('ok', False), ('started', False), ('status', 'pending'), ('app_id', 999),
                     ('item_id', '3596263413'), ('error', 'failure')]
        for key, value in mutations:
            with self.subTest(key=key):
                bad = copy.deepcopy(self.download); bad[key] = value
                with self.assertRaises(ValueError): adapter.validate_download(bad, self.item, self.cache)
        for field in ('callback', 'install_info', 'state_flags'):
            bad = copy.deepcopy(self.download)
            if field == 'callback': bad[field]['result'] = 0
            if field == 'install_info': bad[field]['path'] = str(self.root / 'not-cache')
            if field == 'state_flags': bad[field]['needs_update'] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                adapter.validate_download(bad, self.item, self.cache)

    def test_all_fourteen_share_one_case_host_and_original_budgets(self):
        fixture = base_tests.SharedEntryTests(methodName='test_product_cannot_override_runtime')
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        registry_path = ROOT / 'tools/ck3_mod_acceptance_products.json'
        selections = [entry.Selection(fixture.runtime_path, registry_path, row['key'], 'workshop_cache')
                      for row in self.registry['products']]
        self.assertEqual(len(selections), 14)
        choices = set()
        for selected in selections:
            argv = selected.argv
            choices.add(tuple(argv[argv.index(flag) + 1] for flag in
                             ('--agent-source-root', '--bridge-dll', '--bridge-injector')) + (argv[4],))
            self.assertIn('--frontend-mod-load-observation', argv)
            self.assertNotIn('--frontend-robert-bootstrap', argv)
            self.assertNotIn('--saved-campaign-save', argv)
            self.assertNotIn('--frontend-fixture-start-policy', argv)
            self.assertEqual(selected.case['budgets'], dict(command_timeout=300, readiness_timeout=400,
                             timeout=3600, poll_interval=.5, hold_seconds=900))
        self.assertEqual(len(choices), 1)
        self.assertEqual(len({json.dumps(s.case, sort_keys=True) for s in selections}), 1)
        for row in self.registry['products']:
            context = {**self.context, 'product': row['key'], 'product_spec': row}
            if row['workshop_item_id'] is None:
                with self.assertRaisesRegex(ValueError, 'development-only'): adapter.validate_contract(context)
            else:
                adapter.validate_contract(context)

    def test_original_source_materializer_still_copies_product(self):
        context = {**self.context, 'state_dir': str(self.root / 'ordinary-state'), 'output': str(self.root / 'ordinary-prepared')}
        result = prepare.materialize_product_profile(context, self.cache, self.context['case_inputs']['plain_configuration'])
        target = Path(result['profile']) / 'mod-content/product'
        self.assertEqual((target / 'descriptor.mod').read_bytes(), self.canonical_descriptor)
        self.assertEqual(adapter.read_json(result['product_inventory']['path'])['schema'], 'ck3-saved-campaign-product-only-profile-v1')

    def test_combined_actual_menu_load_needs_same_process_not_independent_vfs(self):
        self.prepared()
        report, process = self.report()
        accepted = adapter.combined_menu_observation(self.context, report, process)
        self.assertTrue(accepted['combined_managed_cache_profile_and_actual_menu_load'])
        self.assertEqual(accepted['independent_engine_vfs_path_readback'], 'UNKNOWN')
        self.assertFalse(accepted['actual_cache_mount_proven_by_independent_vfs'])
        variants = []
        for section, key, value in [('frontend_mod_load_launch', 'pid', 99),
            ('frontend_mod_load_launch', 'ck3_creation_date', '20261008120001.123456+000'),
            ('frontend_mod_load_launch', 'continue_last_save', True),
            ('frontend_mod_load_launch', 'actual_command', ['synthetic', '-loadsave=bad', '-userdir=' + str(Path(self.context['state_dir']) / 'profile')]),
            ('frontend_mod_load_profile', 'preparation_sha256', '0' * 64),
            ('frontend_mod_load_observation', 'campaign_started', True),
            ('frontend_mod_load_observation', 'actions_submitted', 1)]:
            bad = copy.deepcopy(report); bad[section][key] = value; variants.append(bad)
        bad = copy.deepcopy(report); bad['frontend_mod_load_observation']['identity']['bridge_pid'] = 99; variants.append(bad)
        bad = copy.deepcopy(report); bad['frontend_mod_load_observation']['identity']['native_build']['executable_sha256'] = '0' * 64; variants.append(bad)
        bad = copy.deepcopy(report); bad['frontend_mod_load_observation']['proof']['consecutive_consistent_observations'] = 1; variants.append(bad)
        for number, bad in enumerate(variants):
            with self.subTest(number=number), self.assertRaises(ValueError):
                adapter.combined_menu_observation(self.context, bad, process)

    def test_original_normal_close_remains_mandatory_and_no_business_pass(self):
        self.prepared()
        report, process = self.report()
        context = {**self.context, 'output': str(self.root / 'case-output')}

        class Client:
            _process = process
            def guard(self): return report
            def read_report(self): return report
            def checkpoint(self, name, value): adapter.write_json(Path(context['output']) / (name + '.json'), value)
            def __getattr__(self, name): raise AssertionError('Cache adapter must not invoke ' + name)

        adapter.run_case(context, Client())
        selected = object.__new__(entry.Selection)
        selected.run_dir = self.root / context['run_id']
        selected.context_path = self.root / 'allocated-context.json'
        selected.argv = ['SYNTHETIC CACHE VERIFY ONLY']
        selected.runtime_environment = {}
        frozen = selected.run_dir / 'frozen-argv.json'
        self.write(frozen, {'run_id': context['run_id'], 'reviewer': '/root',
            'argv': selected.argv, 'runtime_environment': selected.runtime_environment})
        selected.context = {'run_id': context['run_id'], 'reviewer': '/root', 'frozen_argv': entry.pin(frozen)}
        self.write(selected.context_path, selected.context)
        selected.adapter_context = lambda: context
        selected.load_adapter = lambda: adapter
        self.assertFalse(selected.verify()['case_acceptance_pass'])
        closed = Path(context['output']) / 'normal-close-result.json'
        self.write(closed, {'normal_close_qualified': False})
        self.assertFalse(selected.verify()['case_acceptance_pass'])
        self.write(closed, {'normal_close_qualified': True})
        result = selected.verify()
        self.assertEqual(context['operator_reviewer'], selected.context['reviewer'])
        self.assertTrue(result['case_acceptance_pass'])
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['product_release_pass'])

    def test_wmi_timestamp_uses_original_utc_offset(self):
        expected = datetime(2026, 10, 8, 12, 0, 0, 123456, tzinfo=timezone.utc).timestamp()
        self.assertEqual(adapter.wmi_epoch('20261008120000.123456+000'), expected)
        self.assertEqual(adapter.wmi_epoch('20261008200000.123456+480'), expected)


if __name__ == '__main__': unittest.main(verbosity=2)
