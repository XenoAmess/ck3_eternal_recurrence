"""Future readiness floor with real public selection; no CK3 or desktop calls."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import test_ck3_mod_acceptance as fixtures


class ReadinessPolicyTests(unittest.TestCase):
    setUp = fixtures.SharedEntryTests.setUp
    write = fixtures.SharedEntryTests.write
    select = fixtures.SharedEntryTests.select

    def requested(self, seconds):
        self.products['products']['xqol']['cases'][0]['budgets']['readiness_timeout'] = seconds
        self.write(self.products_path, self.products)
        return self.select()

    def test_external_catalog_cannot_request_shorter_future_startup(self):
        for requested, effective in ((400, 1800), (900, 1800), (1500, 1800),
                                     (1800, 1800), (2400, 2400)):
            with self.subTest(requested=requested):
                selected = self.requested(requested)
                original = copy.deepcopy(selected.case['budgets'])
                described = selected.describe()
                self.assertEqual(selected.argv[selected.argv.index('--readiness-timeout') + 1], str(effective))
                self.assertEqual(described['budgets'], original)
                self.assertEqual(described['effective_budgets'], {**original, 'readiness_timeout': effective})
                policy = described['readiness_policy']
                self.assertEqual((policy['requested_seconds'], policy['effective_seconds'], policy['minimum_seconds']),
                                 (requested, effective, 1800))
                self.assertEqual(policy['floor_applied'], requested < 1800)
                self.assertFalse(policy['historical_receipts_reclassified'])
                for key, flag in fixtures.entry.BUDGET_FLAGS.items():
                    if key != 'readiness_timeout':
                        self.assertEqual(selected.argv[selected.argv.index(flag) + 1], str(original[key]))

    def test_null_original_budget_stays_unbound_until_explicit_input(self):
        selected = self.requested(None)
        self.assertNotIn('--readiness-timeout', selected.argv)
        self.assertIn('Original case budget unbound: readiness_timeout', selected.blockers)
        prepared = {'schema': 'ck3-mod-acceptance-prepared-case-v1', 'product': 'xqol', 'case': 'core',
                    'runtime_manifest': fixtures.entry.pin(self.manifest_path), 'startup': {},
                    'case_inputs': {'budgets': {'readiness_timeout': 400}}}
        path = self.root / 'explicit-prepared.json'
        self.write(path, prepared)
        selected = fixtures.entry.Selection(self.runtime_path, self.products_path, 'xqol', 'core', prepared_path=path)
        self.assertEqual(selected.case['budgets']['readiness_timeout'], 400)
        self.assertEqual(selected.effective_budgets['readiness_timeout'], 1800)

    def test_prepare_records_effective_policy_without_rewriting_product_contract(self):
        selected = self.requested(400)
        self.products['product_inventory'] = str(self.files['inventory'])
        selected.products = self.products
        selected.adapter_path = self.files['initial']
        selected.adapter_config = self.files['initial']
        selected.load_adapter = lambda: SimpleNamespace(prepare_case=lambda context: {
            'startup': {'state_dir': context['state_dir']}, 'no_game_started': True})
        inputs = self.root / 'inputs.json'
        self.write(inputs, {'state_dir': str(self.root / 'unused-state'), 'case_inputs': {}})
        result = selected.prepare(inputs, self.root / 'prepare')
        prepared = json.loads(Path(result['prepared_case']['path']).read_bytes())
        self.assertEqual(prepared['readiness_policy'], selected.readiness_policy)
        self.assertEqual(result['readiness_policy'], selected.readiness_policy)
        self.assertEqual(prepared['effective_budgets']['readiness_timeout'], 1800)
        self.assertEqual(selected.case['budgets']['readiness_timeout'], 400)
        self.assertEqual(prepared['runtime_status'], 'NOT_RUN')
        self.assertEqual(prepared['business_acceptance'], 'NOT_ASSESSED')

    def test_changed_prepared_policy_is_rejected(self):
        selected = self.requested(400)
        prepared = {'schema': 'ck3-mod-acceptance-prepared-case-v1', 'product': 'xqol', 'case': 'core',
                    'runtime_manifest': fixtures.entry.pin(self.manifest_path), 'startup': {}, 'case_inputs': {},
                    'readiness_policy': {**selected.readiness_policy, 'effective_seconds': 400}}
        path = self.root / 'wrong-policy.json'
        self.write(path, prepared)
        with self.assertRaisesRegex(ValueError, 'Prepared readiness policy differs'):
            fixtures.entry.Selection(self.runtime_path, self.products_path, 'xqol', 'core', prepared_path=path)

    def test_invalid_readiness_is_not_converted_into_a_valid_budget(self):
        for value in (True, 0, -1, float('nan'), float('inf'), '400'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'readiness_timeout'):
                self.requested(value)

class ReadinessCliDefaults(unittest.TestCase):
    def test_current_and_legacy_runnable_cli_defaults_are_at_least_1800(self):
        root = Path(__file__).resolve().parent.parent
        paths = [root / 'ck3_autonomous_player/src/xar_autoplayer/cli.py',
                 root / 'tools/run_one_generation_canary.py',
                 *sorted((root / 'ck3_autonomous_player/native_bridge/research').glob('run_*.py'))]
        found = 0
        for path in paths:
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and
                        node.func.attr == 'add_argument' and any(isinstance(a, ast.Constant) and
                        a.value in ('--readiness-timeout', '--readiness-timeout-seconds') for a in node.args)):
                    continue
                for keyword in node.keywords:
                    if keyword.arg == 'default' and isinstance(keyword.value, ast.Constant):
                        value = keyword.value.value
                        if type(value) in (int, float):
                            found += 1
                            self.assertGreaterEqual(value, 1800, str(path.relative_to(root)))
        self.assertEqual(found, 33)

    def test_private_observer_function_defaults_use_the_same_floor(self):
        root = Path(__file__).resolve().parent.parent / 'ck3_autonomous_player/src/xar_autoplayer'
        for name in ('h3937_combined_paused_war_scope_run.py', 'h3937_paused_war_scope_run.py'):
            defaults = [value.value for node in ast.walk(ast.parse((root / name).read_text(encoding='utf-8-sig')))
                        if isinstance(node, ast.FunctionDef)
                        for argument, value in zip(node.args.kwonlyargs, node.args.kw_defaults)
                        if argument.arg == 'readiness_timeout_seconds' and isinstance(value, ast.Constant)]
            self.assertEqual(defaults, [1800], name)


if __name__ == '__main__':
    unittest.main()
