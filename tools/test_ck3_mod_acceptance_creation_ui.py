"""Pure case admission/argv tests; same AST isolation as the relic opt-in tests."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).with_name('ck3_mod_acceptance.py')
TOOLS = {'ck3_open_holy_site_creation_window_v1', 'ck3_select_holy_site_creation_type_v1',
    'ck3_select_holy_site_creation_barony_v1', 'ck3_set_holy_site_creation_artifact_selection_v1'}


class CreationUiCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
        cls.constants = {n.targets[0].id: ast.literal_eval(n.value.args[0]) for n in cls.tree.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and
            n.targets[0].id in {'CASE_HOLY_SITE_CREATION_UI_MCP_TOOLS', 'CASE_READ_ONLY_MCP_TOOLS'}}
        selection = next(n for n in cls.tree.body if isinstance(n, ast.ClassDef) and n.name == 'Selection')
        init = next(n for n in selection.body if isinstance(n, ast.FunctionDef) and n.name == '__init__')
        position = next(i for i, n in enumerate(init.body) if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Attribute) and t.attr == 'opt_in_holy_site_creation_ui' for t in n.targets))
        cls.admission = compile(ast.fix_missing_locations(ast.Module(body=init.body[position:position+3], type_ignores=[])), str(SOURCE), 'exec')
        branch = next(n for n in ast.walk(selection) if isinstance(n, ast.If) and
            isinstance(n.test, ast.Attribute) and n.test.attr == 'opt_in_holy_site_creation_ui')
        cls.argv_branch = compile(ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[])), str(SOURCE), 'exec')
        describe = next(n for n in selection.body if isinstance(n, ast.FunctionDef) and n.name == 'describe')
        ns = {}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[describe], type_ignores=[])), str(SOURCE), 'exec'), ns)
        cls.describe = staticmethod(ns['describe'])
        adapter_context = next(n for n in selection.body if isinstance(n, ast.FunctionDef) and n.name == 'adapter_context')
        exec(compile(ast.fix_missing_locations(ast.Module(body=[adapter_context], type_ignores=[])), str(SOURCE), 'exec'),
            {'read_json': lambda path: {}, 'pin': lambda path: {}}, ns)
        cls.adapter_context = staticmethod(ns['adapter_context'])

    def admit(self, case):
        runner = SimpleNamespace(case=case)
        exec(self.admission, {'self': runner, **self.constants})
        return runner.opt_in_holy_site_creation_ui

    def test_exact_four_UI_tools_are_not_readonly(self):
        self.assertEqual(self.constants['CASE_HOLY_SITE_CREATION_UI_MCP_TOOLS'], TOOLS)
        self.assertFalse(TOOLS & self.constants['CASE_READ_ONLY_MCP_TOOLS'])

    def test_default_and_explicit_false_keep_UI_disabled(self):
        self.assertIs(self.admit({}), False)
        self.assertIs(self.admit({'opt_in_holy_site_creation_ui': False}), False)

    def test_true_requires_all_four_explicit_required_tools(self):
        self.assertIs(self.admit({'opt_in_holy_site_creation_ui': True, 'required_mcp_tools': sorted(TOOLS)}), True)
        for missing in TOOLS:
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                self.admit({'opt_in_holy_site_creation_ui': True, 'required_mcp_tools': sorted(TOOLS - {missing})})
        with self.assertRaises(ValueError):
            self.admit({'opt_in_holy_site_creation_ui': True})

    def test_non_boolean_optin_is_rejected(self):
        for value in (None, 0, 1, 'true', [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.admit({'opt_in_holy_site_creation_ui': value, 'required_mcp_tools': sorted(TOOLS)})

    def test_argv_only_forwards_the_existing_UI_flag_when_true(self):
        for enabled in (False, True):
            argv = ['existing']
            exec(self.argv_branch, {'self': SimpleNamespace(opt_in_holy_site_creation_ui=enabled), 'argv': argv})
            self.assertEqual(argv, ['existing', '--private-player-holy-site-creation-ui'] if enabled else ['existing'])

    def test_describe_reports_actual_creation_boolean_without_changing_relic_value(self):
        for enabled in (False, True):
            runner = SimpleNamespace(product_key='example', case={'id': 'case', 'budgets': {}},
                manifest_path=Path('manifest.json'), values={'run_id': None}, argv=[],
                opt_in_read_only_mcp_tools=[], opt_in_holy_site_relic_actions=False,
                opt_in_holy_site_creation_ui=enabled, runtime_environment={},
                effective_budgets={}, readiness_policy={}, blockers=[])
            result = self.describe(runner)
            self.assertIs(result['opt_in_holy_site_creation_ui'], enabled)
            self.assertIs(result['opt_in_holy_site_relic_actions'], False)
            self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def test_adapter_context_reports_actual_creation_boolean(self):
        for enabled in (False, True):
            runner = SimpleNamespace(locations={'repo_root': Path('repo'), 'game_dir': Path('game')},
                run_dir=Path('run'), state_dir=Path('state'), context={}, prepared=None, product_key='example',
                case={'id': 'case'}, manifest={'source_root': {}, 'game': {}}, product={},
                products={'product_inventory': 'inventory.json'}, adapter_config=Path('contract.json'),
                manifest_path=Path('manifest.json'), readiness_policy={}, opt_in_holy_site_creation_ui=enabled,
                manifest_path_key=lambda value: Path('source'), case_path=lambda value: Path(value))
            self.assertIs(self.adapter_context(runner, inputs={})['opt_in_holy_site_creation_ui'], enabled)


if __name__ == '__main__':
    unittest.main(verbosity=2)
