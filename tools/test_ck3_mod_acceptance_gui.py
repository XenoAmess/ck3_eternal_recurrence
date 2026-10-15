"""Offline checks only: no CK3, native injection, desktop, Steam or task bus."""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_gui as gui
import ck3_mod_acceptance as entry


class GuiAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.staging = self.root / 'staging'
        self.staging.mkdir()
        (self.staging / 'descriptor.mod').write_text('name="Sample"\n', encoding='utf-8')
        (self.staging / 'sample.txt').write_text('sample=yes\n', encoding='utf-8')
        self.formal = self.root / 'formal.json'
        self.write(self.formal, {'files': [{'path': name, 'size': row['bytes'], 'sha256': row['sha256']}
                                         for name, row in gui.inventory(self.staging).items()]})
        self.settings = self.root / 'pdx_settings.txt'
        self.settings.write_text('"System"={\n"language"={version=0 value="l_english"}\n}\n', encoding='utf-8')
        self.fallback = self.root / 'native-gap.json'
        self.write(self.fallback, {'status': 'ACTUAL_HASH_MISMATCH_SYNTHETIC_FIXTURE'})
        self.game = self.root / 'game'
        (self.game / 'binaries').mkdir(parents=True)
        (self.game / 'binaries/ck3.exe').write_bytes(b'fake-exe-not-executable')
        self.manifest = self.root / 'manifest.json'
        self.write(self.manifest, {'schema': 'ck3-mod-acceptance-shared-runtime-v1',
            'execution_mode': 'gui_only', 'game': {'version': 'fixture',
                'exe_sha256': gui.pin(self.game / 'binaries/ck3.exe')['sha256']}})
        self.runtime = self.root / 'runtime.json'
        self.write(self.runtime, {'schema': 'ck3-mod-acceptance-runtime-v1', 'manifest': gui.pin(self.manifest),
            'python': sys.executable, 'repo_root': str(self.root), 'game_dir': str(self.game),
            'userdir_root': str(self.root / 'userdirs'), 'artifacts_root': str(self.root / 'runs')})
        self.products = self.root / 'products.json'
        self.write(self.products, {'schema': 'ck3-mod-acceptance-products-v1', 'products': {
            'sample': {'external_mod': True, 'cases': [{'id': 'core', 'budgets': {
                'timeout': 10, 'quit_timeout': 1, 'poll_interval': .1, 'max_prepare_bytes': 8192},
                'required_business_evidence': ['doctrine_choice']}]}}})
        self.inputs = self.root / 'inputs.json'
        self.write(self.inputs, {'staging': str(self.staging), 'formal_manifest': gui.pin(self.formal),
            'settings': gui.pin(self.settings), 'mcp_fallback_evidence': [gui.pin(self.fallback)]})
        self.args = argparse.Namespace(mode='plan', runtime=self.runtime, products=self.products,
            product='sample', case='core', case_inputs=self.inputs, prepare_output=self.root / 'prepared',
            prepared_case=None, run_context=None, gui_review=None)
        self.lease_module = types.SimpleNamespace(checkout_head=lambda repo: 'a' * 40)

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def prepare(self):
        self.args.mode = 'prepare'
        with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
            return gui.dispatch(self.args)

    def test_plan_does_not_select_native_or_claim_business(self):
        result = gui.dispatch(self.args)
        self.assertEqual(result['execution_mode'], 'gui_only')
        self.assertFalse(result['business_pass'])
        self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def test_prepare_exact_isolated_chinese_profile_and_warm_cache(self):
        cache = self.root / 'warm'
        cache.mkdir()
        (cache / 'test.shader').write_bytes(b'warm-input')
        value = gui.read_json(self.inputs)
        value['warm_cache'] = str(cache)
        saved = self.root / 'old-version.ck3'
        saved.write_bytes(b'explicit-old-save-fixture')
        value['save'] = gui.pin(saved)
        value['debug_mode'] = True
        self.write(self.inputs, value)
        result = self.prepare()
        profile = Path(result['profile'])
        self.assertTrue(profile.is_relative_to(self.root / 'userdirs'))
        self.assertIn('value="l_simp_chinese"', (profile / 'pdx_settings.txt').read_text(encoding='utf-8'))
        self.assertIn('l_english', self.settings.read_text(encoding='utf-8'))
        self.assertEqual((profile / 'shadercache/test.shader').read_bytes(), b'warm-input')
        self.assertEqual((profile / 'save games/old-version.ck3').read_bytes(), saved.read_bytes())
        self.assertEqual(gui.read_json(profile / 'dlc_load.json')['enabled_mods'], ['mod/product.mod'])
        self.assertFalse(result['business_pass'])

    def test_formal_mismatch_blocks_before_profile_creation(self):
        (self.staging / 'sample.txt').write_text('changed=yes', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Formal staging bytes differ'):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())

    def test_actual_game_mismatch_is_still_rejected(self):
        (self.game / 'binaries/ck3.exe').write_bytes(b'new-game')
        self.args.mode = 'preflight'
        with self.assertRaisesRegex(ValueError, 'Installed game differs'):
            gui.dispatch(self.args)

    def test_native_binary_in_gui_manifest_is_rejected(self):
        value = gui.read_json(self.manifest)
        value['native'] = {'dll': 'must-not-load'}
        self.write(self.manifest, value)
        value = gui.read_json(self.runtime)
        value['manifest'] = gui.pin(self.manifest)
        self.write(self.runtime, value)
        with self.assertRaisesRegex(ValueError, 'must not select a native'):
            gui.dispatch(self.args)

    def test_original_harmless_process_wait_and_stop_are_distinct(self):
        keeper = types.SimpleNamespace(require_live=lambda: None)
        budgets = {'timeout': 10, 'quit_timeout': 1, 'poll_interval': .1}
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(.15)'])
        normal = gui.wait_original(child, self.root, budgets, keeper, lambda: None)
        self.assertTrue(normal['actual_original_popen_wait'])
        self.assertEqual(normal['pid'], child.pid)
        self.assertTrue(normal['process_pass'])
        (self.root / 'STOP').touch()
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(.15)'])
        with patch.object(gui, 'request_window_close', return_value=[]) as close:
            stopped = gui.wait_original(child, self.root, budgets, keeper, lambda: None)
        close.assert_called_once_with(child.pid)
        self.assertFalse(stopped['process_pass'])
        self.assertTrue(stopped['window_close_requested'])
        self.assertFalse(stopped['business_pass'])

    def test_exit_zero_without_business_review_is_incomplete(self):
        context = {'product': 'sample', 'case': 'core', 'runtime_manifest': gui.pin(self.manifest),
                   'run_dir': str(self.root), 'run_id': 'synthetic-test'}
        context_path = self.root / 'context.json'
        self.write(context_path, context)
        self.write(self.root / 'game-started.json', {'pid': 123, 'run_id': 'synthetic-test'})
        self.write(self.root / 'game-exit.json', {'pid': 123, 'process_pass': True,
                                                'actual_original_popen_wait': True})
        self.args.mode = 'verify'
        self.args.run_context = context_path
        result = gui.dispatch(self.args)
        self.assertTrue(result['process_pass'])
        self.assertFalse(result['case_acceptance_pass'])
        self.assertFalse(result['gui_business_pass'])
        review = {'run_id': 'synthetic-test', 'case': 'core', 'reviewer': 'offline-test',
                  'direct_image_review': True, 'passed': True, 'normal_gui_quit': True, 'facts': {
                      'doctrine_choice': {'passed': True, 'evidence': [gui.pin(self.fallback)]}}}
        self.write(self.root / 'business-review.json', review)
        with self.assertRaisesRegex(ValueError, 'normal in-game Quit evidence'):
            gui.dispatch(self.args)
        review['normal_quit_evidence'] = [gui.pin(self.fallback)]
        self.write(self.root / 'business-review.json', review)
        self.write(self.root / 'keeper-report.json', {'thread_exited': True, 'failure': None})
        self.write(self.root / 'screen-release.json', {'ok': True})
        result = gui.dispatch(self.args)
        self.assertTrue(result['case_acceptance_pass'])
        self.assertTrue(result['gui_business_pass'])
        self.assertTrue(result['business_pass'])

    def workshop_case(self):
        item = '3798133925'
        self.cache = self.root / 'steamapps/workshop/content/1158310' / item
        shutil.copytree(self.staging, self.cache)
        manifest = gui.read_json(self.formal)
        manifest.update(format_version=1, workshop_item_id=item, git_tag='sample-v1', git_sha='a' * 40)
        self.write(self.formal, manifest)
        self.download = self.root / 'download.json'
        self.write(self.download, {'ok': True, 'status': 'complete', 'started': True,
            'app_id': 1158310, 'item_id': item,
            'callback': {'app_id': 1158310, 'item_id': item, 'result': 1},
            'install_info': {'path': str(self.cache)}, 'worker_exit_code': 0,
            'state_flags': {'installed': True, 'needs_update': False, 'downloading': False, 'download_pending': False}})
        canonical = self.root / 'canonical-products.json'
        self.write(canonical, {'schema': 'ck3.workshop-products.v1', 'consumer_app_id': '1158310',
            'forbidden_upstream_target_ids': [], 'products': [{'key': 'sample', 'directory': 'mod_sample',
                'workshop_item_id': item, 'forbidden_upstream_ids': []}]})
        products = gui.read_json(self.products)
        product = products['products']['sample']
        product.update(directory='mod_sample', workshop_item_id=item)
        product['cases'][0]['id'] = 'workshop_cache'
        del product['cases'][0]['required_business_evidence']
        products['product_inventory'] = str(canonical)
        self.write(self.products, products)
        contract = self.root / 'tools/ck3_mod_acceptance_cases/workshop_cache.json'
        contract.parent.mkdir(parents=True)
        shutil.copyfile(Path(gui.__file__).parent / 'ck3_mod_acceptance_cases/workshop_cache.json', contract)
        self.settings.write_text('"System"={"language"={version=0 value="l_simp_chinese"}}\n', encoding='utf-8')
        configs = {'pdx_settings.txt': gui.pin(self.settings)}
        for name in ('tutorial.txt', 'presets.txt', 'player/game_rules/presets.txt'):
            path = self.root / 'ordinary' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('ordinary=yes\n', encoding='utf-8')
            configs[name] = gui.pin(path)
        self.write(self.inputs, {'state_dir': str(self.root / 'userdirs/cache-state'), 'debug_mode': True,
            'case_inputs': {'cache_path': str(self.cache), 'formal_manifest': gui.pin(self.formal),
                            'native_download_receipt': gui.pin(self.download), 'plain_configuration': configs}})
        self.args.case = 'workshop_cache'

    def completed_cache(self):
        self.workshop_case()
        result = self.prepare()
        profile = Path(result['profile'])
        self.args.prepared_case = self.args.prepare_output / 'prepared-case.json'
        context = {'product': 'sample', 'case': 'workshop_cache', 'runtime_manifest': gui.pin(self.manifest),
                   'run_dir': str(self.root), 'run_id': 'synthetic-cache'}
        self.args.run_context = self.root / 'context.json'
        self.write(self.args.run_context, context)
        self.write(self.root / 'game-started.json', {'pid': 123, 'run_id': 'synthetic-cache',
            'native_injection': False, 'argv': [str(self.game / 'binaries/ck3.exe'), '-userdir=' + str(profile), '-debug_mode']})
        self.write(self.root / 'game-exit.json', {'pid': 123, 'process_pass': True,
                                                'actual_original_popen_wait': True})
        self.write(self.root / 'keeper-report.json', {'thread_exited': True, 'failure': None})
        self.write(self.root / 'screen-release.json', {'ok': True})
        (profile / 'logs').mkdir()
        (profile / 'logs/debug.log').write_text(
            '[D] Sample|mod/product.mod|Enabled\n[D] Mounted Data: ' + str(self.cache) + '\n', encoding='utf-8')
        self.write(self.root / 'cache-review.json', {'run_id': 'synthetic-cache', 'case': 'workshop_cache',
            'reviewer': 'offline-test', 'direct_image_review': True, 'passed': True, 'normal_gui_quit': True,
            'normal_quit_evidence': [gui.pin(self.fallback)]})
        self.args.mode = 'verify'
        return profile

    def test_cache_prepare_reuses_exact_download_without_copy_or_fixture(self):
        self.workshop_case()
        before = gui.inventory(self.cache)
        result = self.prepare()
        profile = Path(result['profile'])
        self.assertEqual(gui.inventory(self.cache), before)
        self.assertFalse((profile / 'mod-content').exists())
        self.assertEqual(set(result['profile_files']), {'pdx_settings.txt', 'tutorial.txt', 'presets.txt',
                         'player/game_rules/presets.txt', 'mod/product.mod', 'dlc_load.json'})
        self.assertIn('path="' + self.cache.as_posix() + '"', (profile / 'mod/product.mod').read_text(encoding='utf-8'))
        self.assertFalse(result['business_contract_applicable'])
        self.assertFalse(result['cache_content_copied'])

    def test_cache_rejects_wrong_download_and_changed_formal_bytes(self):
        self.workshop_case()
        download = gui.read_json(self.download)
        download['callback']['result'] = 2
        self.write(self.download, download)
        inputs = gui.read_json(self.inputs)
        inputs['case_inputs']['native_download_receipt'] = gui.pin(self.download)
        self.write(self.inputs, inputs)
        with self.assertRaisesRegex(ValueError, 'SDK success callback missing'):
            self.prepare()
        self.assertFalse((self.root / 'userdirs/cache-state').exists())
        self.args.prepare_output = self.root / 'prepared-two'
        download['callback']['result'] = 1
        self.write(self.download, download)
        inputs['case_inputs']['native_download_receipt'] = gui.pin(self.download)
        self.write(self.inputs, inputs)
        (self.cache / 'sample.txt').write_text('changed=yes\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'cache content mismatch'):
            self.prepare()

    def test_cache_mount_log_and_normal_exit_pass_without_business_credit(self):
        self.completed_cache()
        result = gui.dispatch(self.args)
        self.assertTrue(result['case_acceptance_pass'])
        self.assertTrue(result['cache_acceptance_pass'])
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['gui_business_pass'])
        self.assertFalse(result['native_capability_pass'])

    def test_cache_requires_actual_mount_log_and_normal_quit(self):
        profile = self.completed_cache()
        log = profile / 'logs/debug.log'
        original = log.read_text(encoding='utf-8')
        log.write_text('Sample|mod/product.mod|Enabled\nMounted Data: wrong-cache\n', encoding='utf-8')
        self.assertFalse(gui.dispatch(self.args)['cache_acceptance_pass'])
        log.write_text(original, encoding='utf-8')
        review = gui.read_json(self.root / 'cache-review.json')
        review['normal_gui_quit'] = False
        self.write(self.root / 'cache-review.json', review)
        with self.assertRaisesRegex(ValueError, 'normal in-game Quit evidence'):
            gui.dispatch(self.args)

    def test_nonfinite_or_unbounded_poll_budget_rejected(self):
        for value in [float('nan'), float('inf'), -1, 0]:
            with self.assertRaises(ValueError):
                gui.budget(value, 'timeout')


class PublicRoutingTests(unittest.TestCase):
    def route(self, manifest, result):
        argv = ['plan', '--runtime', 'runtime.json', '--products', 'products.json',
                '--product', 'sample', '--case', 'core']
        with patch.object(entry, 'read_json', side_effect=[{'manifest': {'path': 'manifest.json'}}, manifest]), \
                patch.object(entry, 'native_dispatch', return_value=result) as native, \
                patch.object(gui, 'dispatch', return_value=result) as official_gui, \
                patch('sys.stdout', new_callable=io.StringIO):
            code = entry.main(argv)
        return code, native, official_gui

    def test_existing_native_route_is_preserved(self):
        code, native, official_gui = self.route({}, {'status': 'READY'})
        self.assertEqual(code, 0)
        native.assert_called_once()
        official_gui.assert_not_called()

    def test_explicit_gui_route_propagates_failure(self):
        code, native, official_gui = self.route({'execution_mode': 'gui_only'}, {'status': 'RED'})
        self.assertEqual(code, 2)
        native.assert_not_called()
        official_gui.assert_called_once()


if __name__ == '__main__':
    unittest.main()
