"""Portable, desktop-free checks for the explicit normal Quit reviewer binding."""
from pathlib import Path
import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
ACTUAL_REVIEWER = '/root/qol_original_cells_runner'

def require(value, message):
    if not value:
        raise RuntimeError(message)

class NormalQuitReviewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = REPO/'tools/ck3_mod_acceptance_normal_quit.py'
        spec = importlib.util.spec_from_file_location('normal_quit_reviewer_under_test', path)
        cls.helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.helper)

    def request(self, root, reviewer):
        live, keeper = root/'run-R42', root/'keeper'
        return live, keeper, {'run_id':live.name, 'reviewer':reviewer, 'pid':4242,
            'create_time':12345.25, 'original_hold_deadline':12945.25,
            'live':str(live), 'keeper_root':str(keeper), 'screen_task':'actual-screen-task'}

    def test_actual_runner_is_forwarded_and_accepted(self):
        # Execute the actual client method with process/desktop boundaries replaced
        # by inert doubles, then feed that independent argv identity to the helper.
        tree = ast.parse((REPO/'tools/ck3_mod_acceptance_client.py').read_text(encoding='utf-8-sig'))
        client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'CaseClient')
        method = next(node for node in client.body if isinstance(node, ast.FunctionDef)
                      and node.name == 'start_normal_quit_automation')
        namespace = {'Path':Path, 'require':require, 'os':os, 'subprocess':subprocess}
        exec(compile(ast.Module(body=[method], type_ignores=[]), '<actual-client-method>', 'exec'), namespace)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            live, keeper, request = self.request(root, ACTUAL_REVIEWER)
            output = root/'case-output'
            output.mkdir()
            request_path = output/'normal-quit-awaiting.json'
            reviewer = mock.Mock(return_value=ACTUAL_REVIEWER)
            fake = types.SimpleNamespace(remaining=lambda:60, output=output, live=live, keeper=keeper,
                _process={'pid':4242,'create_time':12345.25}, _hold=12945.25,
                focus_retained_process_for_quit=lambda:None, normal_quit_reviewer=reviewer,
                checkpoint=lambda *args:None, selection=types.SimpleNamespace(
                    locations={'python':Path(sys.executable), 'repo_root':REPO}, runtime_environment={}))
            config = {name:{'path':str(root/name),'bytes':1,'sha256':'a'*64}
                      for name in ('helper','matcher','templates')}
            check_module = types.ModuleType('ck3_mod_acceptance')
            check_module.check_pin = lambda *args:None
            with mock.patch.dict(sys.modules, {'ck3_mod_acceptance':check_module}), mock.patch.object(subprocess,'Popen') as popen:
                namespace['start_normal_quit_automation'](fake, request_path, config)
            reviewer.assert_called_once_with()
            argv = popen.call_args.args[0]
            expected = argv[argv.index('--expected-reviewer')+1]
            self.assertEqual(expected, ACTUAL_REVIEWER)
            self.assertEqual(self.helper.validate_request(request,live=live,keeper_root=keeper,pid=4242,
                create_time=12345.25,deadline=12945.25,expected_reviewer=expected), 'actual-screen-task')

    def test_forged_root_and_missing_independent_reviewer_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            live, keeper, request = self.request(Path(temporary), '/root')
            with self.assertRaisesRegex(RuntimeError, 'identity/deadline differs'):
                self.helper.validate_request(request,live=live,keeper_root=keeper,pid=4242,
                    create_time=12345.25,deadline=12945.25,expected_reviewer=ACTUAL_REVIEWER)
            for expected in ('', ' ', ACTUAL_REVIEWER+' ', None):
                with self.subTest(expected=expected), self.assertRaisesRegex(RuntimeError, 'Explicit actual expected reviewer'):
                    self.helper.validate_request(request,live=live,keeper_root=keeper,pid=4242,
                        create_time=12345.25,deadline=12945.25,expected_reviewer=expected)

if __name__ == '__main__':
    unittest.main()
