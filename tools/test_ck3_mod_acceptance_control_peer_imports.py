"""File-backed public control import regressions; no host, SDK or game calls."""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch


@runtime_checkable
class PublicEntry(Protocol):
    def native_dispatch(self, args: argparse.Namespace) -> dict[str, object]: ...
    def same_directory_control_peer(self, name: str) -> ModuleType: ...


def load_module(name: str, source: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ValueError('File-backed module unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ControlPeerImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_path = list(sys.path)
        self.names = ('ck3_mod_acceptance', 'ck3_mod_acceptance_allocate', 'ck3_mod_acceptance_unrun')
        self.prior_modules = {name: sys.modules.pop(name, None) for name in self.names}
        temporary = Path(os.environ.get('TEMP', tempfile.gettempdir()))
        temporary.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='control-import-', dir=temporary)
        self.local = Path(self.temporary.name)/'selected-C'
        self.foreign = Path(self.temporary.name)/'frozen-D'
        self.local.mkdir()
        self.foreign.mkdir()
        tools = Path(__file__).resolve().parent
        source = Path(os.environ.get('CK3_CONTROL_IMPORT_ENTRY', str(tools/'ck3_mod_acceptance.py')))
        (self.local/'ck3_mod_acceptance.py').write_bytes(source.read_bytes())
        (self.local/'ck3_mod_acceptance_unrun.py').write_bytes((tools/'ck3_mod_acceptance_unrun.py').read_bytes())
        for root in (self.local, self.foreign):
            (root/'ck3_mod_acceptance_allocate.py').write_text(
                "from pathlib import Path\ncalls = 0\n"
                "def allocate_and_keep(selection, args):\n"
                "    global calls\n    calls += 1\n"
                "    return {'allocator_file': str(Path(__file__).resolve()), 'synthetic_no_launch': True}\n"
                "def closed_lease(*args):\n    return True\n", encoding='utf-8')
        (self.foreign/'ck3_mod_acceptance_unrun.py').write_text('foreign = True\n', encoding='utf-8')
        sys.path.insert(0, str(self.foreign))
        self.entry_module = load_module('ck3_mod_acceptance', self.local/'ck3_mod_acceptance.py')

    def tearDown(self) -> None:
        sys.path[:] = self.prior_path
        for name in self.names:
            sys.modules.pop(name, None)
            previous = self.prior_modules[name]
            if previous is not None:
                sys.modules[name] = previous
        self.temporary.cleanup()

    def dispatch(self) -> dict[str, object]:
        args = argparse.Namespace(mode='allocate', runtime=None, products=None, product=None,
                                  case=None, run_context=None, prepared_case=None)
        # Selection's construction is the boundary; real native_dispatch performs
        # the imports and calls only the tiny file-backed synthetic allocator.
        with patch.object(self.entry_module, 'Selection', return_value=object()):
            dispatch = getattr(self.entry_module, 'native_dispatch')
            result: object = dispatch(args)
        if not isinstance(result, dict):
            raise ValueError('Public dispatch result differs')
        return {str(key): value for key, value in result.items()}

    def entry(self) -> PublicEntry:
        if not isinstance(self.entry_module, PublicEntry):
            raise ValueError('Public entry interface unavailable')
        return self.entry_module

    def test_allocate_uses_siblings_despite_foreign_search_path(self) -> None:
        before = list(sys.path)
        result = self.dispatch()
        self.assertEqual(Path(str(result['allocator_file'])), (self.local/'ck3_mod_acceptance_allocate.py').resolve())
        self.assertIs(result['synthetic_no_launch'], True)
        self.assertEqual(sys.path, before)
        peer = sys.modules['ck3_mod_acceptance_allocate']
        self.dispatch()
        self.assertIs(sys.modules['ck3_mod_acceptance_allocate'], peer)
        self.assertEqual(getattr(peer, 'calls'), 2)
        self.assertEqual(Path(str(sys.modules['ck3_mod_acceptance_unrun'].__file__)), self.local/'ck3_mod_acceptance_unrun.py')

    def test_cached_foreign_allocator_refuses_before_call(self) -> None:
        foreign = load_module('ck3_mod_acceptance_allocate', self.foreign/'ck3_mod_acceptance_allocate.py')
        before = list(sys.path)
        with self.assertRaisesRegex(ValueError, 'module directory differs'):
            self.dispatch()
        self.assertEqual(getattr(foreign, 'calls'), 0)
        self.assertIs(sys.modules['ck3_mod_acceptance_allocate'], foreign)
        self.assertEqual(sys.path, before)

    def test_cached_foreign_unrun_refuses_before_allocate_call(self) -> None:
        foreign = load_module('ck3_mod_acceptance_unrun', self.foreign/'ck3_mod_acceptance_unrun.py')
        with self.assertRaisesRegex(ValueError, 'module directory differs'):
            self.dispatch()
        self.assertIs(sys.modules['ck3_mod_acceptance_unrun'], foreign)
        self.assertEqual(getattr(sys.modules['ck3_mod_acceptance_allocate'], 'calls'), 0)

    def test_unrun_release_uses_same_directory_allocator(self) -> None:
        before = list(sys.path)
        module = self.entry().same_directory_control_peer('ck3_mod_acceptance_unrun')
        keeper = {'last_sequence': 1}
        cas = {'event': {'task_id': 'synthetic', 'resources': [], 'kind': 'status', 'sequence': 2}}
        done = {'event': {'task_id': 'synthetic', 'resources': [], 'kind': 'completed', 'sequence': 3},
                'task': {'last_sequence': 3, 'state': 'done'}}
        result: object = getattr(module, '_release_stages')(keeper, cas, done, {}, {}, done, 'synthetic')
        self.assertEqual(result, 'status-then-completed')
        self.assertEqual(Path(str(sys.modules['ck3_mod_acceptance_allocate'].__file__)), self.local/'ck3_mod_acceptance_allocate.py')
        self.assertEqual(sys.path, before)

    def test_import_failure_restores_path_without_allocate(self) -> None:
        (self.local/'ck3_mod_acceptance_unrun.py').write_text("raise RuntimeError('synthetic import failure')\n", encoding='utf-8')
        before = list(sys.path)
        with self.assertRaisesRegex(RuntimeError, 'synthetic import failure'):
            self.dispatch()
        self.assertEqual(sys.path, before)
        self.assertEqual(getattr(sys.modules['ck3_mod_acceptance_allocate'], 'calls'), 0)


if __name__ == '__main__':
    unittest.main()
