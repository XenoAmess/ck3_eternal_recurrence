"""Portable CLI-boundary regression tests; never import a live runner.

Only main/CLI AST is executed with mock providers. --source-root allows an
external candidate checkout; normal CI reads this repository by relative path.
"""
from pathlib import Path
import argparse
import ast
import builtins
import contextlib
import copy
from functools import lru_cache
import io
import json
from types import SimpleNamespace
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {
    'tools/run_acceptance.py': None,
    'tools/run_vivhite_acceptance.py': None,
    'tools/run_remove_mandala_acceptance.py': 'preflight_only',
    'tools/run_xenoamess_quality_of_life_acceptance.py': 'namespace',
    'tools/run_xqol_defense_acceptance.py': 'namespace',
    'tools/run_reclaim_the_motherland_acceptance.py': 'namespace',
    'tools/run_tributary_expansion_directives_acceptance.py': 'namespace',
    'tools/run_celestial_commerce_corruption_acceptance.py': 'namespace',
    'tools/run_auto_upgrade_buildings_acceptance.py': 'preflight_only',
    'tools/run_ox_here_acceptance.py': 'preflight_only',
    'tools/run_zhongguo_acceptance.py': 'preflight_only',
    'mod_superman_qiang/tools/run_acceptance.py': 'superman',
    'tools/run_terminal_acceptance.py': None,
    'tools/run_balance_matrix.py': None,
}


class Tripwire:
    def __init__(self, effects, name):
        self.effects, self.name = effects, name

    def __getattr__(self, name):
        self.effects.append(self.name + '.' + name)
        raise AssertionError('Forbidden provider touched: ' + self.name + '.' + name)

    def __call__(self, *args, **kwargs):
        self.effects.append(self.name)
        raise AssertionError('Forbidden provider called: ' + self.name)


class MockParser:
    def __init__(self, namespace):
        self.namespace = namespace

    def add_argument(self, *args, **kwargs):
        return None

    def add_mutually_exclusive_group(self, *args, **kwargs):
        return self

    def parse_args(self, *args, **kwargs):
        return self.namespace

    def error(self, message):
        raise AssertionError(message)

    def exit(self, code, message):
        raise AssertionError((code, message))


class MockPath:
    def __init__(self, calls, label='mock'):
        self.calls, self.label = calls, label

    @property
    def parent(self):
        return self

    def expanduser(self):
        return self

    def resolve(self):
        return self

    def exists(self):
        return False

    def mkdir(self, *args, **kwargs):
        # Reclaim's original preflight creates its external artifact directory.
        self.calls.append(('original-directory-provider', self.label))


@lru_cache(maxsize=None)
def source_tree(relative_path):
    return ast.parse((SOURCE_ROOT / relative_path).read_text(encoding='utf-8-sig'))


def mock_globals(node, effects, namespace):
    denied = lambda *a, **k: Tripwire(effects, 'builtin-IO')()
    safe = dict(vars(builtins))
    safe.update(open=denied, __import__=denied, eval=denied, exec=denied)
    result = {
        n.id: Tripwire(effects, n.id) for n in ast.walk(node)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in safe
    }
    result.update(
        __builtins__=safe, sys=SimpleNamespace(stderr=io.StringIO()), json=json,
        argparse=SimpleNamespace(ArgumentParser=lambda *a, **k: MockParser(namespace)),
    )
    if isinstance(node, ast.FunctionDef):
        for default in (*node.args.defaults, *[d for d in node.args.kw_defaults if d]):
            for n in ast.walk(default):
                if isinstance(n, ast.Name):
                    result[n.id] = 300.0
    return result


def main_function(relative_path, globals_):
    main = copy.deepcopy(next(n for n in source_tree(relative_path).body
                              if isinstance(n, ast.FunctionDef) and n.name == 'main'))
    # Type annotations aren't execution providers or part of the tested body.
    main.returns = None
    for node in ast.walk(main):
        if isinstance(node, ast.arg):
            node.annotation = None
        if isinstance(node, ast.AnnAssign):
            node.annotation = ast.Name(id='object', ctx=ast.Load())
    module = ast.fix_missing_locations(ast.Module(body=[main], type_ignores=[]))
    exec(compile(module, '<legacy-main-mocked>', 'exec'), globals_)
    return globals_['main']


def invoke(relative_path, main, preflight=False):
    kind = ENTRIES[relative_path]
    if kind == 'namespace':
        return main(SimpleNamespace(preflight=preflight, source='mock-source',
                                   artifacts_dir='mock-artifacts', keep_userdir=True,
                                   bridge_dll=None, bridge_injector=None, bridge_pipe=None))
    if kind == 'preflight_only':
        return main(preflight_only=preflight)
    if relative_path.endswith('run_terminal_acceptance.py'):
        return main('observer')
    if relative_path.endswith('run_balance_matrix.py'):
        return main(['balanced'])
    return main()


def add_original_providers(globals_, calls, relative_path):
    config = object()
    globals_['resolve_native_bridge_config'] = lambda *a: (
        calls.append(('original-config-provider', a)) or config)
    globals_['preflight'] = lambda *a, **k: (
        calls.append(('original-preflight-provider', len(a))) or {})
    globals_['Path'] = lambda value: MockPath(calls, str(value))
    globals_['RUNS_ROOT'] = MockPath(calls, 'original-RUNS_ROOT')
    globals_['SOURCE'] = MockPath(calls, 'original-SOURCE')
    globals_['_validate_phase2_frontend_first_options'] = lambda *a, **k: (
        calls.append(('original-options-provider',)))
    if relative_path.endswith('run_xqol_defense_acceptance.py'):
        globals_['DEFENSE_MARKERS'] = ('ORIGINAL-LITERAL',)
        globals_['run_defense_scenario'] = object()
        globals_['base'] = SimpleNamespace(main=lambda args: (
            calls.append(('original-base-preflight-provider', args.preflight)) or 41))
    if relative_path.endswith(('run_tributary_expansion_directives_acceptance.py',
                               'run_celestial_commerce_corruption_acceptance.py')):
        globals_['DEFAULT_SOURCE'] = MockPath(calls, 'original-source')
        globals_['configure_harness'] = lambda source: (
            calls.append(('original-configure-harness-provider',)))
        globals_['configure_reusable'] = lambda source: (
            calls.append(('original-configure-reusable-provider',)))
        globals_['harness'] = SimpleNamespace(main=lambda **kwargs: (
            calls.append(('original-harness-provider', kwargs['preflight_only'])) or 41))


class LegacyLiveEntryTests(unittest.TestCase):
    def context(self, relative_path, namespace=None):
        node = next(n for n in source_tree(relative_path).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'main')
        effects = []
        namespace = namespace or SimpleNamespace(live=True, prepare=False, mcp_server=False)
        globals_ = mock_globals(node, effects, namespace)
        return effects, globals_

    def check_live(self, relative_path):
        effects, globals_ = self.context(relative_path)
        with contextlib.redirect_stdout(io.StringIO()):
            result = invoke(relative_path, main_function(relative_path, globals_))
        self.assertEqual(result, 2)
        self.assertEqual(effects, [], 'Live entry touched an original provider')
        text = globals_['sys'].stderr.getvalue()
        self.assertIn('tools/ck3_mod_acceptance.py', text)
        self.assertIn('plan / prepare / allocate / preflight / run / verify', text)

    def check_preflight(self, relative_path):
        effects, globals_ = self.context(relative_path)
        calls = []
        add_original_providers(globals_, calls, relative_path)
        with contextlib.redirect_stdout(io.StringIO()):
            result = invoke(relative_path, main_function(relative_path, globals_), True)
        delegated = relative_path.endswith(('run_xqol_defense_acceptance.py',
                                            'run_tributary_expansion_directives_acceptance.py',
                                            'run_celestial_commerce_corruption_acceptance.py'))
        self.assertEqual(result, 41 if delegated else 0)
        self.assertEqual(effects, [])
        self.assertTrue(any('preflight-provider' in call[0] or
                            'harness-provider' in call[0] for call in calls))
        self.assertEqual(globals_['sys'].stderr.getvalue(), '')

    def check_original_cli_preflight(self, relative_path):
        cli = copy.deepcopy(next(n for n in source_tree(relative_path).body
                                 if isinstance(n, ast.If) and '__name__' in ast.unparse(n.test)))
        effects, calls = [], []
        globals_ = mock_globals(cli, effects, SimpleNamespace(preflight=True))
        globals_.update(__name__='__main__', BALANCE_FIXTURES={}, SCENARIOS={})
        globals_['preflight'] = lambda: calls.append(('original-cli-preflight-provider',))
        def exit_zero(code):
            raise SystemExit(code)
        globals_['sys'].exit = exit_zero
        module = ast.fix_missing_locations(ast.Module(body=[cli], type_ignores=[]))
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
            exec(compile(module, '<legacy-cli-mocked>', 'exec'), globals_)
        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(effects, [])
        self.assertEqual(calls, [('original-cli-preflight-provider',)])

    def check_superman_preserved(self, mode):
        relative_path = 'mod_superman_qiang/tools/run_acceptance.py'
        namespace = SimpleNamespace(live=False, prepare=mode == 'prepare',
                                    mcp_server=mode == 'mcp_server', run_dir='mock-run')
        effects, globals_ = self.context(relative_path, namespace)
        calls = []
        globals_['prepare'] = lambda args: (
            calls.append(('original-prepare-provider',)) or {'ok': True})
        globals_['mcp_server'] = lambda run: (
            calls.append(('original-mcp-server-provider', run)) or 41)
        with contextlib.redirect_stdout(io.StringIO()):
            result = invoke(relative_path, main_function(relative_path, globals_))
        self.assertEqual(result, 0 if mode == 'prepare' else 41)
        self.assertEqual(effects, [])
        self.assertEqual(len(calls), 1)


def parameterized(check, argument):
    def test(self):
        check(self, argument)
    return test


for relative_path, kind in ENTRIES.items():
    name = relative_path.removesuffix('.py').replace('/', '_')
    setattr(LegacyLiveEntryTests, 'test_live_' + name,
            parameterized(LegacyLiveEntryTests.check_live, relative_path))
    if kind in ('namespace', 'preflight_only'):
        setattr(LegacyLiveEntryTests, 'test_preflight_' + name,
                parameterized(LegacyLiveEntryTests.check_preflight, relative_path))
    elif relative_path in ('tools/run_acceptance.py', 'tools/run_vivhite_acceptance.py'):
        setattr(LegacyLiveEntryTests, 'test_cli_preflight_' + name,
                parameterized(LegacyLiveEntryTests.check_original_cli_preflight, relative_path))
for mode in ('prepare', 'mcp_server'):
    setattr(LegacyLiveEntryTests, 'test_superman_' + mode,
            parameterized(LegacyLiveEntryTests.check_superman_preserved, mode))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-root', type=Path)
    args, remaining = parser.parse_known_args()
    if args.source_root:
        SOURCE_ROOT = args.source_root.resolve()
    unittest.main(argv=['test_legacy_live_acceptance_entry_guard.py', *remaining])
