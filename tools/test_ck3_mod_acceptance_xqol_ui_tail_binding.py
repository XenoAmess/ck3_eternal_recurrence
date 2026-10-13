"""Focused fixed current38 -> QA27-08 -> R33 scoped-evidence binding checks.

No game, builder, public prepare, profile or old native-report is used.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from test_ck3_mod_acceptance_xqol_minimal_scope import restore_minimal_ui_adapter, restore_minimal_ui_contract

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'tools/ck3_mod_acceptance_cases/xqol_ui_tail_adapter.py'
CONTRACT = ROOT / 'tools/ck3_mod_acceptance_cases/xqol_ui_tail.json'
GENERATED = 'common/character_interactions/xqol_generated_release_interactions.txt'
DISPATCH = 'common/scripted_effects/xqol_conversion_effects.txt'
CURRENT_GENERATED = {'bytes': 14995, 'sha256': '75c6132ee9c30dab40e912f294ab2d1953bd2d3f1cc07c6afc2834c3cc1a12eb'}
LEGACY_GENERATED = {'bytes': 14943, 'sha256': '9992b5c91f2f482eb2165d33c9066978c2ca3757a281f8d0f4e99096a168bb73'}
CURRENT_DISPATCH = {'bytes': 8127, 'sha256': '608c7e6811b7444274947c82ba63439cabd4887e61bcb978bf196d738fe72d5f'}
R33_PINS = {
    GENERATED: {'bytes': 14134, 'sha256': '456dbf029c115393dd04b83707802f029799ec5021a66b76959d8e3460573f0a'},
    DISPATCH: {'bytes': 7458, 'sha256': '0a4f93d7019afe94cfff76f7f6129023dc08b07c96dcf61ea170a5e5c40ec7db'},
}
ACTOR_BLOCK = (b'\t\tscope:actor = {\n\t\t\ttrigger_if = {\n'
               b'\t\t\t\tlimit = { is_ai = yes }\n'
               b'\t\t\t\tis_adult = yes\n\t\t\t}\n\t\t}\n')
PRIOR_ACTOR_BLOCK = (b'\t\ttrigger_if = {\n\t\t\tlimit = { is_ai = yes }\n'
                     b'\t\t\tis_adult = yes\n\t\t}\n')


def content_pin(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def file_pin(path):
    path = Path(path).resolve()
    return {'path': str(path), **content_pin(path.read_bytes())}


def binding_function():
    # Only these two pure definitions execute; no adapter imports/entrypoint run.
    source = ast.parse(ADAPTER.read_bytes().decode('utf-8-sig'))
    selected = [node for node in source.body
                if isinstance(node, ast.FunctionDef)
                and node.name in ('require', 'prior_formal_binding')]
    namespace = {'Path': Path, 'hashlib': hashlib, 'pin': file_pin}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(ADAPTER), 'exec'), namespace)
    return namespace['prior_formal_binding']


class FixedUiTailBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = staticmethod(binding_function())
        cls.generated = (ROOT / 'mod_xenoamess_quality_of_life' / GENERATED).read_bytes()
        cls.dispatch = (ROOT / 'mod_xenoamess_quality_of_life' / DISPATCH).read_bytes()

    def inputs(self, directory, generated):
        product = Path(directory)
        for relative, raw in ((GENERATED, generated), (DISPATCH, self.dispatch)):
            path = product / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        # The unchanged 25 rows are deliberately inert synthetic rows, not
        # an acceptance claim about a real staging. Actual two files are read.
        expected = {f'unchanged-{index:02}.txt': {'bytes': index, 'sha256': f'{index:064x}'}
                    for index in range(25)}
        expected.update({GENERATED: content_pin(generated), DISPATCH: content_pin(self.dispatch)})
        source = copy.deepcopy(expected)
        source.update(copy.deepcopy(R33_PINS))
        receipt = {
            'formal_product_files': copy.deepcopy(source),
            'source_prepared': {'sha256': '28e7bfca6b7165a749a4311c7182387d9a368ad8b1067175dcb9d600f6b1dfd5'},
            'source_run_id': '4-8e1c2f1861--xenoamess-quality-of-life--R0033',
        }
        context = {'case_inputs': {
            'product_dir': str(product),
            'formal_product_files': expected,
            'prior_core_evidence': {'sha256': '3be254579a2a5004b6dbb15c48e5ec619f784503f2b75fe854e936bd0547dbe1'},
        }}
        return context, receipt, source

    def test_exact_52_byte_projection_and_legacy_branch_both_restore_full_r33(self):
        self.assertEqual(content_pin(self.generated), CURRENT_GENERATED)
        self.assertEqual(content_pin(self.dispatch), CURRENT_DISPATCH)
        self.assertEqual(self.generated.count(ACTOR_BLOCK), 2)
        legacy = self.generated.replace(ACTOR_BLOCK, PRIOR_ACTOR_BLOCK)
        self.assertEqual(len(self.generated) - len(legacy), 52)
        self.assertEqual(content_pin(legacy), LEGACY_GENERATED)
        for raw in (self.generated, legacy):
            with self.subTest(generated_pin=content_pin(raw)), tempfile.TemporaryDirectory() as directory:
                context, receipt, source = self.inputs(directory, raw)
                result = self.binding(context, receipt, source)
                self.assertEqual(result['mode'], 'r33_scoped_conversion_stock_pending_only')
                self.assertEqual(result['restored_source_pins'], R33_PINS)
                self.assertEqual({key: {field: row[field] for field in ('bytes', 'sha256')}
                                  for key, row in result['current_pins'].items()},
                                 {GENERATED: content_pin(raw), DISPATCH: CURRENT_DISPATCH})
                self.assertEqual(result['unchanged_formal_files'], 25)
                self.assertEqual(result['reused_scope'], 'defense23/reverse/final6 only')
                self.assertIs(result['conversion_reply_credit'], False)

    def test_reject_unknown_declarations_actual_bytes_and_wrong_r33_provenance(self):
        for issue in ('extra_formal_change', 'unknown_generated_pin', 'actual_generated_mutation',
                      'actual_dispatch_mutation', 'prior_receipt', 'prior_prepared', 'prior_run'):
            with self.subTest(issue=issue), tempfile.TemporaryDirectory() as directory:
                context, receipt, source = self.inputs(directory, self.generated)
                expected = context['case_inputs']['formal_product_files']
                if issue == 'extra_formal_change':
                    expected['unchanged-00.txt']['sha256'] = 'f' * 64
                elif issue == 'unknown_generated_pin':
                    expected[GENERATED]['sha256'] = 'f' * 64
                elif issue == 'actual_generated_mutation':
                    (Path(directory) / GENERATED).write_bytes(self.generated + b'# unexpected\n')
                elif issue == 'actual_dispatch_mutation':
                    (Path(directory) / DISPATCH).write_bytes(self.dispatch + b'# unexpected\n')
                elif issue == 'prior_receipt':
                    context['case_inputs']['prior_core_evidence']['sha256'] = 'f' * 64
                elif issue == 'prior_prepared':
                    receipt['source_prepared']['sha256'] = 'f' * 64
                elif issue == 'prior_run':
                    receipt['source_run_id'] = 'unreviewed-other-run'
                with self.assertRaises(ValueError):
                    self.binding(context, receipt, source)

    def test_every_other_adapter_definition_and_original_ui_contract_remain_exact(self):
        registry = json.loads((ROOT / 'tools/ck3_mod_acceptance_products.json').read_bytes())
        for product, case, filename in (
                ('xqol', 'ui_tail', 'xqol_ui_tail.json'),
                ('reclaim-motherland', 'core', 'rmtm_keypaths.json'),
                ('reclaim-motherland', 'threshold_ui', 'rmtm_threshold_ui.json')):
            with self.subTest(product=product, case=case):
                current = json.loads((CONTRACT.parent / filename).read_bytes())
                registered = next(item for item in registry['products'][product]['cases']
                                  if item['id'] == case)
                self.assertEqual(current['original_budgets'], registered['budgets'])
        tree = ast.parse(restore_minimal_ui_adapter(ADAPTER.read_bytes()).decode('utf-8-sig'))
        tree.body = [node for node in tree.body if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     or node.name != 'prior_formal_binding']
        digest = hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()
        self.assertEqual(digest, '8bbcc52ca4cd3b9205206cd0a365cc5f7a8e614731d6c688e4939f9779b6dcf4')
        restored_contract=(json.dumps(restore_minimal_ui_contract(json.loads(CONTRACT.read_bytes())),ensure_ascii=False,indent=2)+'\n').encode()
        self.assertEqual(content_pin(restored_contract),
                         {'bytes': 1647, 'sha256': 'd0010b9380ba2d79ffeb002f7585c38de12dff31d9d3e65f89e008a74be2e26e'})
        contract = json.loads(CONTRACT.read_bytes())
        self.assertEqual(contract['readonly_step_count'], 9)
        self.assertEqual(contract['focused_slider_order'], ['slider-anchor','save-100','restore-anchor','map-clean'])
        self.assertIs(contract['guards_independent_supplement_required'], True)
        self.assertIs(contract['normal_close_required'], True)
        self.assertIs(contract['business_pass'], False)
        self.assertIs(contract['product_release_pass'], False)


if __name__ == '__main__':
    unittest.main()
