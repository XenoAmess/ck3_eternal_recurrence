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
        observer = patch.object(gui, '_observe_checkout_for_materialization', side_effect=lambda repo:
            {'repo': str(Path(repo).resolve()), 'head': 'a' * 40, 'dirty': False, 'status_porcelain_v1': ''})
        observer.start()
        self.addCleanup(observer.stop)

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding='utf-8')

    def prepare(self):
        self.args.mode = 'prepare'
        with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
            if self.args.case == 'workshop_cache':
                # Fake EXE fixtures cannot supply real Windows PE/Steam build
                # metadata. Verify the shared selection passed to that producer.
                def engine(context):
                    self.assertEqual(context['shared_source_root'], str(self.root))
                    self.assertEqual(context['game_dir'], str(self.game))
                    self.assertEqual(context['shared_game'], gui.read_json(self.manifest)['game'])
                    return None, {'game_version': 'fixture', 'exe_sha256': gui.pin(self.game / 'binaries/ck3.exe')['sha256']}
                with patch('ck3_mod_acceptance_cases.workshop_cache_adapter._engine', side_effect=engine):
                    return gui.dispatch(self.args)
            return gui.dispatch(self.args)

    def test_pinned_prepare_records_unrelated_sdk_dirty_without_live_admission(self):
        dirty = {'repo': str(self.root.resolve()), 'head': 'b' * 40, 'dirty': True,
                 'status_porcelain_v1': ' M java/ck3-control/native-transport/SDK.java\n'}
        with patch.object(gui, '_observe_checkout_for_materialization', return_value=dirty), \
                patch.object(self.lease_module, 'checkout_head', side_effect=ValueError('dirty live checkout')) as strict:
            result = self.prepare()
        strict.assert_not_called()
        self.assertEqual(gui.pin(Path(result['profile']) / 'mod-content/product/sample.txt')['sha256'],
                         gui.pin(self.staging / 'sample.txt')['sha256'])
        observation = result['materialization_source_observation']
        self.assertTrue(observation['source_checkout']['dirty'])
        self.assertEqual(observation['source_checkout']['status_porcelain_v1'], dirty['status_porcelain_v1'])
        self.assertEqual(observation['source_checkout']['head'], 'b' * 40)
        self.assertEqual(observation['purpose'], 'EXACT_PINNED_MATERIALIZATION_ONLY_NOT_LIVE_ADMISSION')
        self.assertFalse(result['business_pass'])
        self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def test_pinned_prepare_actual_stage_drift_rejects_before_provenance_or_writes(self):
        (self.staging / 'sample.txt').write_text('changed=yes\n', encoding='utf-8')
        with patch.object(gui, '_observe_checkout_for_materialization') as observe:
            with self.assertRaisesRegex(ValueError, 'Formal staging bytes differ'):
                self.prepare()
        observe.assert_not_called()
        self.assertFalse(self.args.prepare_output.exists())
        self.assertFalse((self.root / 'userdirs').exists())

    def test_pinned_prepare_fixture_path_keeps_strict_dirty_rejection(self):
        self.fixture_inputs()
        with patch.object(self.lease_module, 'checkout_head', side_effect=ValueError('dirty live checkout')), \
                patch.object(gui, '_observe_checkout_for_materialization') as observe:
            with self.assertRaisesRegex(ValueError, 'dirty live checkout'):
                self.prepare()
        observe.assert_not_called()
        self.assertFalse(self.args.prepare_output.exists())

    def test_pinned_prepare_does_not_relax_preflight_allocate_or_run_dirty(self):
        result = self.prepare()
        self.args.prepared_case = self.args.prepare_output / 'prepared-case.json'
        run_context = self.root / 'run-context.json'
        self.write(run_context, {'product': 'sample', 'case': 'core',
            'runtime_manifest': result['runtime_manifest'], 'prepared_case': gui.pin(self.args.prepared_case),
            'implementation': gui.pin(Path(gui.__file__)), 'run_dir': str(self.root / 'run')})
        self.args.gui_review = self.fallback
        for mode in ('preflight', 'allocate', 'run'):
            with self.subTest(mode=mode):
                self.args.mode = mode
                self.args.run_context = run_context if mode == 'run' else None
                with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)), \
                        patch.object(self.lease_module, 'checkout_head', side_effect=ValueError('dirty live checkout')), \
                        patch.object(gui, '_observe_checkout_for_materialization') as observe:
                    with self.assertRaisesRegex(ValueError, 'dirty live checkout'):
                        gui.dispatch(self.args)
                observe.assert_not_called()

    def test_pinned_materialization_private_argument_cannot_authorize_live_mode(self):
        self.args.mode = 'run'
        with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
            with self.assertRaisesRegex(ValueError, 'exclusive to fresh product prepare'):
                gui.GuiSelection(self.args).preflight(_materialization_inputs=gui.read_json(self.inputs))

    def test_plan_does_not_select_native_or_claim_business(self):
        result = gui.dispatch(self.args)
        self.assertEqual(result['execution_mode'], 'gui_only')
        self.assertFalse(result['business_pass'])
        self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def vanilla_inputs(self):
        configuration = {'pdx_settings.txt': gui.pin(self.settings)}
        for name in gui.CONFIG_NAMES[1:]:
            path = self.root / ('plain-' + name.replace('/', '-'))
            path.write_bytes(b'original_plain_configuration=yes\n')
            configuration[name] = gui.pin(path)
        self.args.product = self.args.case = 'vanilla-diagnostic'
        self.write(self.products, {'schema': 'ck3-mod-acceptance-products-v1', 'products': {
            'vanilla-diagnostic': {'external_mod': True, 'cases': [{'id': 'vanilla-diagnostic',
                'profile_kind': 'vanilla_diagnostic', 'business_contract_applicable': False,
                'required_business_evidence': [], 'budgets': {'timeout': 10, 'quit_timeout': 1,
                'poll_interval': .1, 'max_prepare_bytes': 8192}}]}}})
        value = {'profile_kind': 'vanilla_diagnostic', 'plain_configuration': configuration,
                 'mcp_fallback_evidence': [gui.pin(self.fallback)]}
        self.write(self.inputs, value)
        return value

    def test_vanilla_public_producer_has_no_product_fixture_or_save_and_freezes_all_inputs(self):
        self.vanilla_inputs()
        result = self.prepare()
        self.assertEqual(result['profile_kind'], 'vanilla_diagnostic')
        self.assertFalse(result['business_contract_applicable'])
        profile = Path(result['profile'])
        self.assertEqual(gui.read_json(profile / 'dlc_load.json'), {'enabled_mods': [], 'disabled_dlcs': []})
        self.assertEqual(set(result['profile_files']), {*gui.CONFIG_NAMES, 'dlc_load.json'})
        self.assertFalse((profile / 'mod-content').exists())
        self.assertFalse((profile / 'mod').exists())
        self.assertFalse((profile / 'save games').exists())
        self.assertFalse((profile / 'shadercache').exists())
        self.assertEqual(gui.read_json(result['product_inventory']['path'])['product_files'], [])
        self.assertIn('l_simp_chinese', (profile / 'pdx_settings.txt').read_text(encoding='utf-8'))
        for row in result['inputs']:
            gui.check_pin(row)
        self.write(self.args.prepare_output / 'prepared-case.json', result)
        self.args.prepared_case = self.args.prepare_output / 'prepared-case.json'
        source = Path(result['case_inputs']['plain_configuration']['tutorial.txt']['path'])
        source.write_bytes(b'changed original configuration')
        with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
            with self.assertRaises(ValueError):
                gui.GuiSelection(self.args).preflight()

    def test_vanilla_rejects_product_warm_save_fixture_and_unknown_inputs_before_writing(self):
        original = self.vanilla_inputs()
        for field in ('staging', 'formal_manifest', 'fixture', 'fixture_manifest', 'save', 'warm_cache',
                      'debug_mode', 'source_repo', 'unknown'):
            with self.subTest(field=field):
                self.write(self.inputs, {**original, field: None})
                with self.assertRaisesRegex(ValueError, 'only its explicit kind'):
                    self.prepare()
                self.assertFalse(self.args.prepare_output.exists())

    def test_vanilla_rejects_missing_wrong_or_changed_configuration_and_fallback(self):
        original = self.vanilla_inputs()
        invalid = [
            {**original, 'plain_configuration': {}},
            {**original, 'mcp_fallback_evidence': []},
            {**original, 'mcp_fallback_evidence': True},
            {**original, 'mcp_fallback_evidence': [{**gui.pin(self.fallback), 'bytes': True}]},
            {**original, 'profile_kind': True},
        ]
        for value in invalid:
            self.write(self.inputs, value)
            with self.assertRaises((ValueError, TypeError)):
                self.prepare()
            self.assertFalse(self.args.prepare_output.exists())
        self.write(self.inputs, original)
        self.fallback.write_bytes(b'tampered fallback')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())

    def test_vanilla_kind_cannot_relabel_a_product_or_business_case(self):
        value = self.vanilla_inputs()
        products = gui.read_json(self.products)
        products['products']['sample'] = products['products']['vanilla-diagnostic']
        self.write(self.products, products)
        self.args.product = 'sample'
        with self.assertRaisesRegex(ValueError, 'cannot declare a product business'):
            gui.dispatch(self.args)
        self.args.product = 'vanilla-diagnostic'
        products['products']['vanilla-diagnostic']['cases'][0]['business_contract_applicable'] = True
        self.write(self.products, products)
        with self.assertRaisesRegex(ValueError, 'cannot declare a product business'):
            gui.dispatch(self.args)
        self.args.product = 'sample'
        self.args.case = 'core'
        products['products']['sample']['cases'][0]['id'] = 'core'
        self.write(self.products, products)
        with self.assertRaisesRegex(ValueError, 'dedicated case'):
            gui.dispatch(self.args)

    def test_vanilla_review_roundtrip_certifies_only_diagnostic_and_preserves_raw_error(self):
        self.vanilla_inputs()
        prepared = self.prepare()
        run = self.root / 'diagnostic-run'
        run.mkdir()
        self.args.prepared_case = self.args.prepare_output / 'prepared-case.json'
        context = {'product': self.args.product, 'case': self.args.case,
            'runtime_manifest': gui.pin(self.manifest), 'run_id': 'actual-diagnostic-run',
            'run_dir': str(run), 'identity': {'machine_id': 'fixture-machine'}}
        self.args.run_context = self.root / 'context.json'
        self.write(self.args.run_context, context)
        self.write(run / 'game-started.json', {'pid': 123, 'run_id': context['run_id']})
        self.write(run / 'game-exit.json', {'pid': 123, 'process_pass': True, 'actual_original_popen_wait': True})
        self.write(run / 'keeper-report.json', {'thread_exited': True, 'failure': None})
        self.write(run / 'screen-release.json', {'ok': True})
        raw = run / 'raw-error.log'
        raw.write_bytes(b'actual retained stock diagnostic, never filtered')
        image = run / 'actual-close.png'
        image.write_bytes(b'offline fixture, not a real screenshot')
        review = {'schema': 'ck3-mod-acceptance-vanilla-diagnostic-review-v1',
            'run_id': context['run_id'], 'case': self.args.case, 'machine_id': 'fixture-machine',
            'direct_image_review': True, 'reviewer': 'offline-fixture', 'normal_gui_quit': True,
            'normal_quit_evidence': [gui.pin(image)], 'observations': [gui.pin(raw)], 'passed': True}
        self.write(run / 'diagnostic-review.json', review)
        self.args.mode = 'verify'
        result = gui.dispatch(self.args)
        self.assertTrue(result['diagnostic_pass'])
        self.assertTrue(result['case_acceptance_pass'])
        for field in ('business_contract_applicable', 'gui_business_pass', 'business_pass',
                      'product_release_pass', 'native_capability_pass', 'baseline_error_waiver'):
            self.assertIs(result[field], False)
        self.assertEqual(raw.read_bytes(), b'actual retained stock diagnostic, never filtered')
        for field,value in (('machine_id', 'foreign'), ('run_id', 'foreign'), ('normal_gui_quit', False),
                            ('observations', [])):
            self.write(run / 'diagnostic-review.json', {**review, field: value})
            with self.assertRaises(ValueError):
                gui.dispatch(self.args)
        self.write(run / 'diagnostic-review.json', review)
        raw.write_bytes(b'tampered raw log')
        with self.assertRaises(ValueError):
            gui.dispatch(self.args)

    def test_vanilla_plan_explicitly_has_no_product_business_contract(self):
        self.vanilla_inputs()
        result = gui.dispatch(self.args)
        self.assertEqual(result['required_business_evidence'], [])
        self.assertFalse(result['business_contract_applicable'])

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

    def fixture_inputs(self):
        fixture = self.root / 'fixture'
        fixture.mkdir()
        (fixture / 'descriptor.mod').write_text('name="Acceptance fixture"\n', encoding='utf-8')
        (fixture / 'observe.txt').write_text('fixture_observer = yes\n', encoding='utf-8-sig')
        manifest = self.root / 'fixture-manifest.json'
        self.write(manifest, {'files': [{'path': name, 'bytes': row['bytes'], 'sha256': row['sha256']}
                                     for name, row in gui.inventory(fixture).items()]})
        inputs = gui.read_json(self.inputs)
        inputs.update(fixture=str(fixture), fixture_manifest=gui.pin(manifest))
        self.write(self.inputs, inputs)
        return fixture, manifest

    def compatibility_inputs(self):
        fixture, _ = self.fixture_inputs()
        provider = self.root / 'provider'
        provider.mkdir()
        (provider / 'descriptor.mod').write_text('name="Independent provider"\n', encoding='utf-8')
        source = self.root / 'provider-manifest.json'
        files = gui.inventory(provider)
        self.write(source, {'files': [{'path': name, 'bytes': row['bytes'], 'sha256': row['sha256']}
                                     for name, row in files.items()]})
        value = gui.read_json(self.inputs)
        value['compatibility_mods'] = [{'key': 'provider', 'directory': str(provider.resolve()),
            'source_manifest': gui.pin(source), 'files': files}]
        value['plain_configuration'] = {'pdx_settings.txt': gui.pin(self.settings)}
        for name in gui.CONFIG_NAMES[1:]:
            path = self.root / ('plain-' + name.replace('/', '-'))
            path.write_bytes(b'original=yes\n')
            value['plain_configuration'][name] = gui.pin(path)
        self.write(self.inputs, value)
        return value, provider, fixture

    def test_compatibility_gui_rejects_missing_public_contract_before_writing(self):
        self.compatibility_inputs()
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())

    def test_compatibility_gui_rejects_changed_provider_before_writing(self):
        _, provider, _ = self.compatibility_inputs()
        (provider / 'descriptor.mod').write_text('name="Changed provider"\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())

    def test_compatibility_gui_refuses_post_freeze_save_or_cache_and_null_list(self):
        original, _, _ = self.compatibility_inputs()
        for field in ('save', 'warm_cache'):
            self.write(self.inputs, {**original, field: 'not-a-fresh-fixture'})
            with self.assertRaisesRegex(ValueError, 'cannot append save/cache'):
                self.prepare()
            self.assertFalse(self.args.prepare_output.exists())
        self.write(self.inputs, {**original, 'compatibility_mods': None})
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())

    def test_compatibility_gui_uses_real_public_materializer_and_freezes_three_mounts(self):
        value, provider, fixture = self.compatibility_inputs()
        source = self.root / 'authored-producer-source.txt'
        source.write_text('AUTHORED SOFTWARE PRODUCER ONLY\n', encoding='utf-8')
        manifest = Path(value['fixture_manifest']['path'])
        self.write(manifest, {'schema': 'ck3-mod-acceptance-prebuilt-fixture-v1',
            'product': 'sample', 'case_id': 'public_core', 'machine_id': 'authored-machine',
            'observed_at_utc': '2026-11-20T00:00:00Z', 'fixture_root': str(fixture.resolve()),
            'producer_source_pins': [gui.pin(source)],
            'files': {name: {key: row[key] for key in ('bytes', 'sha256')}
                      for name, row in gui.inventory(fixture).items()},
            'receipt': {'required_markers': ['AUTHORED: PASS'],
                        'required_product_markers_minimum': {}, 'fixture_contains_business_effects': False}})
        contract = self.root / 'public-case.json'
        self.write(contract, {'schema': 'ck3-mod-acceptance-product-case-v1', 'product': 'sample',
            'case_id': 'public_core', 'fixture_source': {'kind': 'prebuilt_manifest'},
            'acceptance_scope': 'authored_software_gui_copy', 'post_start': {
                'government_key': 'feudal_government', 'primary_title_tier_key': 'duchy', 'independent': True},
            'required_startup': [], 'forbidden_startup': []})
        value.update(fixture_manifest=gui.pin(manifest), fixture_case_contract=gui.pin(contract))
        self.write(self.inputs, value)
        shared = gui.read_json(self.manifest)
        shared['machine_id'] = 'authored-machine'
        self.write(self.manifest, shared)
        runtime = gui.read_json(self.runtime)
        runtime['manifest'] = gui.pin(self.manifest)
        self.write(self.runtime, runtime)
        products = gui.read_json(self.products)
        products['products']['sample']['cases'][0]['budgets']['max_prepare_bytes'] = 1048576
        self.write(self.products, products)
        with patch('ck3_mod_acceptance_prepare._engine', return_value=(None, {
                'game_version': 'authored-no-game', 'exe_sha256': gui.pin(self.game / 'binaries/ck3.exe')['sha256']})):
            result = self.prepare()
        profile = Path(result['profile'])
        self.assertEqual(gui.read_json(profile / 'dlc_load.json')['enabled_mods'],
                         ['mod/compat_provider.mod', 'mod/product.mod', 'mod/fixture.mod'])
        frozen = gui.read_json(result['profile_preparation']['path'])
        self.assertEqual(frozen['schema'], 'ck3-mod-acceptance-prepared-fixture-v1')
        self.assertEqual(frozen['files'], gui.inventory(profile))
        compiled = gui.read_json(result['assertion_contract']['path'])
        self.assertEqual(compiled['emitter']['manifest'], gui.pin(manifest))
        self.assertEqual(compiled['case'], 'public_core')
        self.assertEqual(result['case'], 'core')
        self.assertIn(gui.pin(provider / 'descriptor.mod'), result['inputs'])
        self.assertFalse(result['business_pass'])
        self.args.prepared_case = self.args.prepare_output / 'prepared-case.json'
        for original_source in (manifest, source):
            before = original_source.read_bytes()
            original_source.write_bytes(before + b'\n')
            try:
                with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
                    with self.assertRaises(ValueError):
                        gui.GuiSelection(self.args).preflight()
            finally:
                original_source.write_bytes(before)
        (provider / 'descriptor.mod').write_text('name="changed original provider"\n', encoding='utf-8')
        with patch.object(gui.GuiSelection, 'lease', return_value=(self.lease_module, None, None, None, self.root)):
            with self.assertRaises(ValueError):
                gui.GuiSelection(self.args).preflight()

    def test_source_business_fixture_is_separate_from_formal_product_and_frozen(self):
        fixture, _ = self.fixture_inputs()
        before = gui.inventory(self.staging)
        result = self.prepare()
        profile = Path(result['profile'])
        self.assertEqual(gui.read_json(profile / 'dlc_load.json')['enabled_mods'],
                         ['mod/product.mod', 'mod/fixture.mod'])
        self.assertEqual((profile / 'mod-content/fixture/observe.txt').read_bytes(),
                         (fixture / 'observe.txt').read_bytes())
        self.assertEqual(before, gui.inventory(self.staging))
        self.assertIn('mod-content/fixture/observe.txt', result['profile_files'])
        self.assertFalse(result['business_pass'])
        self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def test_fixture_tamper_or_missing_manifest_rejects_before_preparation(self):
        fixture, _ = self.fixture_inputs()
        (fixture / 'observe.txt').write_text('changed', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Formal staging bytes differ'):
            self.prepare()
        self.assertFalse(self.args.prepare_output.exists())
        inputs = gui.read_json(self.inputs)
        del inputs['fixture_manifest']
        self.write(self.inputs, inputs)
        with self.assertRaisesRegex(ValueError, 'supplied together'):
            self.prepare()

    def test_fixture_bytes_are_charged_to_preparation_budget(self):
        fixture, manifest = self.fixture_inputs()
        (fixture / 'observe.txt').write_bytes(b'x' * 8192)
        self.write(manifest, {'files': [{'path': name, 'bytes': row['bytes'], 'sha256': row['sha256']}
                                     for name, row in gui.inventory(fixture).items()]})
        inputs = gui.read_json(self.inputs)
        inputs['fixture_manifest'] = gui.pin(manifest)
        self.write(self.inputs, inputs)
        with self.assertRaisesRegex(ValueError, 'Prepared input exceeds allocated byte budget'):
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


class BackgroundSteamAdmissionTests(unittest.TestCase):
    def test_gui_only_uses_current_shared_background_provider(self):
        selection = types.SimpleNamespace(context={'identity': {'machine_id': 'fixture-machine'}})
        receipt = Path('actual-background-receipt.json')
        admission = {'receipt': {'path': str(receipt)}, 'background_only': True}
        reader = object()
        with patch('ck3_live_run_id.current_machine_id', return_value='fixture-machine'), \
                patch('steam_offline_state_probe.WindowsReader', return_value=reader), \
                patch('ck3_mod_acceptance_steam_gate.validate_receipt', return_value=admission) as validate:
            self.assertIs(gui.validate_review(selection, receipt), admission)
        validate.assert_called_once_with(receipt, machine_id='fixture-machine', reader=reader)

    def test_gui_only_rejects_foreign_machine_before_provider(self):
        selection = types.SimpleNamespace(context={'identity': {'machine_id': 'other-machine'}})
        with patch('ck3_live_run_id.current_machine_id', return_value='fixture-machine'), \
                patch('steam_offline_state_probe.WindowsReader') as reader, \
                patch('ck3_mod_acceptance_steam_gate.validate_receipt') as validate:
            with self.assertRaisesRegex(ValueError, 'Frozen machine differs'):
                gui.validate_review(selection, Path('receipt.json'))
        reader.assert_not_called()
        validate.assert_not_called()

    def test_gui_only_keeps_shared_background_refusal(self):
        from ck3_mod_acceptance_steam_gate import BackgroundGateRefusal
        selection = types.SimpleNamespace(context={'identity': {'machine_id': 'fixture-machine'}})
        with patch('ck3_live_run_id.current_machine_id', return_value='fixture-machine'), \
                patch('steam_offline_state_probe.WindowsReader'), \
                patch('ck3_mod_acceptance_steam_gate.validate_receipt', side_effect=BackgroundGateRefusal('stale')):
            with self.assertRaisesRegex(BackgroundGateRefusal, 'stale'):
                gui.validate_review(selection, Path('receipt.json'))




class MaterializationCheckoutObservationTests(unittest.TestCase):
    def test_readonly_git_status_records_dirty_and_head_without_clean_assertion(self):
        root = Path(__file__).resolve().parent
        replies = [subprocess.CompletedProcess([], 0, stdout='c' * 40 + '\n', stderr=''),
                   subprocess.CompletedProcess([], 0, stdout=' M unrelated-SDK.java\n', stderr='')]
        with patch.object(gui.subprocess, 'run', side_effect=replies) as git:
            observed = gui._observe_checkout_for_materialization(root)
        self.assertEqual(observed['head'], 'c' * 40)
        self.assertTrue(observed['dirty'])
        self.assertEqual(observed['status_porcelain_v1'], ' M unrelated-SDK.java\n')
        self.assertEqual(git.call_args_list[0].args[0], ['git', '-C', str(root), 'rev-parse', 'HEAD'])
        self.assertEqual(git.call_args_list[1].args[0],
                         ['git', '-C', str(root), 'status', '--porcelain=v1', '--untracked-files=normal'])
        self.assertTrue(all(call.kwargs['env']['GIT_OPTIONAL_LOCKS'] == '0' for call in git.call_args_list))

    def test_observation_still_rejects_unavailable_head(self):
        with patch.object(gui.subprocess, 'run', return_value=
                          subprocess.CompletedProcess([], 0, stdout='invalid', stderr='')) as git:
            with self.assertRaisesRegex(ValueError, 'HEAD is unavailable'):
                gui._observe_checkout_for_materialization(Path(__file__).resolve().parent)
        self.assertEqual(git.call_count, 1)


if __name__ == '__main__':
    unittest.main()
