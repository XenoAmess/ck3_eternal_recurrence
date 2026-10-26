"""R0001 actual source shapes -> existing failed-live resource consumer.

Relocated files and absent processes are authored regression inputs. The source
excerpt preserves the full originals' pins separately and grants no live PASS.
"""
from __future__ import annotations

import copy
import argparse
import contextlib
from collections.abc import Callable, Iterator
import ast
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_allocate as allocation
import ck3_mod_acceptance as entry
import ck3_live_run_id as ids
from ck3_mod_acceptance_fresh_machine_bootstrap import MachineBinding
from ck3_mod_acceptance_background_types import JsonObject, JsonValue, file_pin, json_object, object_field, text_field, strings_field
from test_product_acceptance_purpose import pin


class PreservedNativeOS0Tests(unittest.TestCase):
    fixture_name = 'ck3_R0001_preserved_failure_native_os0.json'

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = json_object(json.loads((Path(__file__).parent / 'fixtures' / self.fixture_name).read_bytes()))
        self.original_root = text_field(source, 'original_root').replace('\\', '/')
        self.machine = text_field(source, 'machine_id')
        self.source = source
        self.leaves = json_object(self.relocate(source['leaves']))
        self.refs: JsonObject = {}
        original_pins = json_object(source['source_pins'])
        for key, raw in original_pins.items():
            original = file_pin(raw)
            path = Path(str(self.relocate(original['path'])))
            path.parent.mkdir(parents=True, exist_ok=True)
            if key in self.leaves:
                self.refs[key] = self.write(path, self.leaves[key])
            else:
                if not path.exists():
                    path.write_bytes(b'Authored non-game output\n')
                self.refs[key] = json_object(pin(path))
        self.freeze = json_object(self.leaves['frozen_argv'])
        self.ready = json_object(self.leaves['ready_context'])
        self.run_dir = Path(text_field(self.ready, 'run_dir'))
        self.keeper = Path(text_field(self.ready, 'keeper_root'))
        self.ready['prepared_case'], self.ready['frozen_argv'] = self.refs['prepared_case'], self.refs['frozen_argv']
        self.reseal('ready_context', self.ready)
        argv = strings_field(json_object(self.leaves['run_wait']), 'argv')
        self.write(Path(argv[argv.index('--run-context') + 1]), self.ready)
        self.report = json_object(self.leaves['native_report'])
        self.release_path = Path(text_field(json_object(self.refs['release']), 'path'))
        self.close = self.root / 'resource-close.json'
        self.bundle: JsonObject = {'schema': 'ck3-mod-acceptance-failed-live-resource-closure-v1',
            'machine_id': self.machine, 'run_id': self.run_dir.name, 'keeper_root': str(self.keeper),
            'closure_kind': 'preserved-failure-native-process-exit-zero',
            'public_wait_format': 'root-observed-command-exit-v1',
            'normal_close_qualified': False, 'typed_normal_exit_proven': False,
            'business_pass': False, 'release_pass': False, 'original_evidence': self.refs}
        self.write(self.close, self.bundle)
        # These processes are authored absent fixtures. The actual R0001 test
        # execution is a separate read-only call against the retained originals.
        self.psutil = SimpleNamespace(pid_exists=lambda pid: False, process_iter=lambda fields: [],
            Process=self.missing_process, NoSuchProcess=ProcessAbsent)

    @staticmethod
    def missing_process(pid: int) -> object:
        raise ProcessAbsent()

    def relocate(self, value: JsonValue) -> JsonValue:
        if isinstance(value, str):
            normalized = value.replace('\\', '/')
            if normalized.startswith(self.original_root):
                return str(self.root / 'external' / normalized[len(self.original_root):].lstrip('/'))
            return normalized
        if isinstance(value, list):
            return [self.relocate(item) for item in value]
        if isinstance(value, dict):
            return {key: self.relocate(item) for key, item in value.items()}
        return value

    def write(self, path: Path, value: object) -> JsonObject:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return json_object(pin(path))

    def reseal(self, key: str, value: JsonValue) -> None:
        self.leaves[key] = value
        self.refs[key] = self.write(Path(text_field(json_object(self.refs[key]), 'path')), value)
        if hasattr(self, 'bundle'):
            self.write(self.close, self.bundle)

    def check(self) -> JsonObject:
        release = json_object(self.leaves['release'])
        with patch.dict(sys.modules, {'psutil': self.psutil}), patch.object(allocation,
                'runtime_process_inventory', return_value={'blockers': []}):
            return json_object(allocation.previous_failed_live_resource_closure(self.run_dir,
                {key: value for key, value in self.freeze.items()}, self.close,
                self.keeper, self.release_path, {'tasks': [release['task']]}))

    def test_actual_shapes_roundtrip_original_false_close_and_host_one_are_preserved(self) -> None:
        self.assertEqual(self.source, json.loads(json.dumps(self.source)))
        proof = self.check()
        facts = json_object(proof['failure_cleanup'])
        self.assertEqual(facts['original_host_exit_code'], 1)
        self.assertEqual(facts['original_ck3_exit_code'], 0)
        self.assertEqual(facts['win32_birth_filetime'], '134373083942703873')
        self.assertIs(facts['original_normal_close_lifecycle_completed'], False)
        self.assertIs(facts['failure_lifecycle_completed'], True)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(facts[key], False)
        self.assertIs(json_object(self.leaves['normal_close'])['failure_lifecycle_completed'], False)

    def test_uncompleted_wrong_or_duplicate_finish_and_job_termination_refuse(self) -> None:
        baseline = copy.deepcopy(self.report)
        steps = baseline['steps']
        if not isinstance(steps, list):
            raise ValueError('Actual finish steps required')
        for kind in ('not_ok', 'duplicate', 'missing', 'job_termination'):
            report = copy.deepcopy(baseline)
            row = json_object(copy.deepcopy(steps[0]))
            if kind == 'not_ok':
                row['ok'] = False
                report['steps'] = [row]
            elif kind == 'duplicate':
                report['steps'] = [row, row]
            elif kind == 'missing':
                report['steps'] = []
            else:
                session = json_object(report['session'])
                native = json_object(session['report'])
                shutdown = json_object(native['shutdown'])
                shutdown['job_active_processes_before_termination'] = 1
                native['shutdown'], session['report'], report['session'] = shutdown, native, session
            self.reseal('native_report', report)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.check()

    def test_root_exit_wrong_machine_bool_float_and_filetime_number_refuse(self) -> None:
        baseline = copy.deepcopy(json_object(self.leaves['run_wait']))
        for value in (True, 2.0, 0):
            changed = copy.deepcopy(baseline)
            changed['exit_code'] = value
            self.reseal('run_wait', changed)
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check()
        self.reseal('run_wait', baseline)
        window = json_object(self.leaves['root_window_start'])
        window['birth_filetime'] = 134373083942703873
        self.reseal('root_window_start', window)
        with self.assertRaises(ValueError):
            self.check()


class CaseClientFailureClosureTests(unittest.TestCase):
    """Actual failed public-case leaves -> shared producer -> full resource consumer."""

    def setUp(self) -> None:
        self.fixture = PreservedNativeOS0Tests()
        self.fixture.fixture_name = 'ck3_R0020_case_client_failure_native_cleanup.json'
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        f = self.fixture
        f.bundle = json_object(allocation.case_client_cleanup_bundle(f.machine, f.run_dir.name, f.keeper, f.refs))
        f.bundle['original_evidence'] = f.refs
        f.write(f.close, f.bundle)
        self.alive: set[int] = set()

    @contextlib.contextmanager
    def boundaries(self) -> Iterator[None]:
        f = self.fixture
        original_stat = Path.stat
        normal_path = f.run_dir / 'case-output/normal-close-result.json'
        normal_ns = int(text_field(f.source, 'normal_close_mtime_ns_decimal'))

        def stat(path: Path, *, follow_symlinks: bool = True) -> object:
            actual = original_stat(path, follow_symlinks=follow_symlinks)
            if path == normal_path:
                return SimpleNamespace(st_size=actual.st_size, st_mtime_ns=normal_ns, st_mode=actual.st_mode)
            return actual

        def process(pid: int) -> object:
            if pid not in self.alive:
                raise ProcessAbsent()
            host = json_object(f.leaves['host_started'])
            return SimpleNamespace(create_time=lambda: host['create_time'])

        f.psutil.Process = process
        with patch.object(Path, 'stat', stat):
            yield

    def check(self) -> JsonObject:
        with self.boundaries():
            return self.fixture.check()

    def test_actual_shapes_producer_serialization_full_consumer_preserves_failure(self) -> None:
        f = self.fixture
        original = {key: Path(text_field(json_object(ref), 'path')).read_bytes() for key, ref in f.refs.items()}
        self.assertEqual(f.bundle, json.loads(json.dumps(f.bundle)))
        facts = json_object(self.check()['failure_cleanup'])
        self.assertEqual(facts['closure_kind'], allocation.CASE_CLIENT_CLEANUP_KIND)
        self.assertEqual(facts['original_host_exit_code'], 0)
        self.assertEqual(facts['original_report_status'], 'GREEN')
        self.assertIsNone(facts['original_host_error'])
        self.assertIsNone(facts['original_ck3_exit_code'])
        self.assertEqual(facts['native_reported_ck3_exit_code'], 1)
        self.assertEqual(facts['win32_birth_filetime'], '134374506697010812')
        for key in ('original_retained_wait_signaled', 'failure_lifecycle_completed', 'actual_retained_os0',
                    'normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(facts[key], False)
        self.assertIsNone(facts['native_cleanup_qualified'])
        self.assertEqual(original, {key: Path(text_field(json_object(ref), 'path')).read_bytes()
                                    for key, ref in f.refs.items()})

    def test_wrong_public_type_and_missing_original_wait_rejected(self) -> None:
        f = self.fixture
        baseline = copy.deepcopy(json_object(f.leaves['run_wait']))
        for field, value in (('exit_code', True), ('exit_code', 2.0),
                             ('actual_original_popen_wait', False), ('machine_id', 'other-machine')):
            changed = copy.deepcopy(baseline)
            changed[field] = value
            f.reseal('run_wait', changed)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.check()

    def test_wrong_pin_or_crossed_case_error_rejected(self) -> None:
        f = self.fixture
        ref = json_object(f.refs['case_error'])
        ref['sha256'] = '0' * 64
        f.refs['case_error'] = ref
        f.write(f.close, f.bundle)
        with self.assertRaises(ValueError):
            self.check()
        failure = json_object(f.leaves['case_error'])
        failure['run_id'] = 'other-run'
        f.reseal('case_error', failure)
        with self.assertRaises(ValueError):
            self.check()

    def test_unknown_or_incomplete_native_cleanup_rejected(self) -> None:
        f = self.fixture
        baseline = copy.deepcopy(json_object(f.leaves['native_report']))
        for field, value in (('ck3_exit_code', None), ('ck3_exit_code', True), ('ck3_exit_code', 1.0),
                             ('ck3_exit_code', 0), ('ck3_exit_code', -1), ('ck3_exit_code', 1 << 32),
                             ('cleanup_proven', False), ('tree_gone', False),
                             ('job_active_processes_final', False), ('job_active_processes_final', 1)):
            report = copy.deepcopy(baseline)
            session = json_object(report['session'])
            native = json_object(session['report'])
            shutdown = json_object(native['shutdown'])
            shutdown[field] = value
            native['shutdown'], session['report'] = shutdown, native
            report['session'] = session
            f.reseal('native_report', report)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.check()

    def test_win32_exit_upper_boundary_and_integer_nanosecond_chronology(self) -> None:
        from datetime import datetime, timezone
        f = self.fixture
        report = json_object(f.leaves['native_report'])
        native = json_object(json_object(report['session'])['report'])
        shutdown = json_object(native['shutdown'])
        shutdown['ck3_exit_code'] = (1 << 32) - 1
        native['shutdown'] = shutdown
        stamp = datetime.fromisoformat(text_field(native, 'finished_at'))
        delta = stamp - datetime(1970, 1, 1, tzinfo=timezone.utc)
        actual_ns = (delta.days * 86400 + delta.seconds) * 1000000000 + delta.microseconds * 1000
        inputs = (f.leaves['normal_close'], f.leaves['retained_exit'], f.leaves['retained_identity'],
                  native, report, f.leaves['case_error'], f.run_dir.name)
        accepted = allocation.validate_case_client_native_cleanup(*inputs, actual_ns - 1)
        self.assertEqual(accepted['native_reported_ck3_exit_code'], (1 << 32) - 1)
        for normal_ns in (actual_ns, actual_ns + 1, True, 1.0):
            with self.subTest(normal_ns=normal_ns), self.assertRaises(ValueError):
                allocation.validate_case_client_native_cleanup(*inputs, normal_ns)

    def test_original_unknown_wait_cannot_be_upgraded(self) -> None:
        f = self.fixture
        retained = json_object(f.leaves['retained_exit'])
        retained['exit_code'] = 1
        normal = json_object(f.leaves['normal_close'])
        normal['retained_handle'] = retained
        f.reseal('retained_exit', retained)
        f.reseal('normal_close', normal)
        with self.assertRaises(ValueError):
            self.check()

    def test_still_alive_or_screen_owned_rejected(self) -> None:
        host = json_object(self.fixture.leaves['host_started'])
        pid = host['pid']
        if type(pid) is not int or not isinstance(pid, int):
            raise ValueError('Exact authored host PID required')
        self.alive.add(pid)
        with self.assertRaises(ValueError):
            self.check()
        self.alive.clear()
        release = json_object(self.fixture.leaves['release'])
        task = json_object(release['task'])
        task['resources'] = ['ck3-screen:acquired']
        release['task'] = task
        self.fixture.reseal('release', release)
        with self.assertRaises(ValueError):
            self.check()

    def test_filetime_numeric_and_wrong_host_branch_rejected(self) -> None:
        f = self.fixture
        retained = json_object(f.leaves['retained_exit'])
        retained['creation_filetime_100ns'] = 134374506697010812
        normal = json_object(f.leaves['normal_close'])
        normal['retained_handle'] = retained
        f.reseal('retained_exit', retained)
        f.reseal('normal_close', normal)
        with self.assertRaises(ValueError):
            self.check()
        retained['creation_filetime_100ns'] = '134374506697010812'
        normal['retained_handle'] = retained
        f.reseal('retained_exit', retained)
        f.reseal('normal_close', normal)
        host = json_object(f.leaves['host_exit'])
        host['returncode'] = 1
        f.reseal('host_exit', host)
        with self.assertRaises(ValueError):
            self.check()

    def test_actual_new_producer_validator_and_dispatch_scope_is_strict(self) -> None:
        from mypy import api
        tools = Path(__file__).parent
        tree = ast.parse((tools/'ck3_mod_acceptance_allocate.py').read_text(encoding='utf-8-sig'))
        names = {'CaseClientCleanupBundle', 'CaseClientNativeCleanupFacts', 'case_client_cleanup_bundle',
                 'validate_case_client_native_cleanup', '_late_integer'}
        nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
                 and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        constants = [node for node in tree.body if isinstance(node, ast.AnnAssign)
                     and isinstance(node.target, ast.Name) and node.target.id == 'CASE_CLIENT_CLEANUP_KIND']
        self.assertEqual(len(constants), 1)
        consumer = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == 'previous_failed_live_resource_closure')
        branches = [node for node in ast.walk(consumer) if isinstance(node, ast.If)
                    and isinstance(node.test, ast.Name) and node.test.id == 'client_failure'
                    and any(isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                            and child.func.id == 'validate_case_client_native_cleanup' for child in ast.walk(node))]
        self.assertEqual(len(branches), 1)
        prelude = '''from __future__ import annotations
from typing import Literal, TypedDict
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import math, re
from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, file_pin, object_field, text_field
'''
        dispatch = ast.parse('''def checked_dispatch(previous: Path, freeze: JsonObject,
        normal: object, retained: object, game: object, native: object, report: object,
        original: Callable[[str, Path], object]) -> CaseClientNativeCleanupFacts:
    pass
''').body[0]
        if not isinstance(dispatch, ast.FunctionDef):
            self.fail('Expected actual extracted dispatcher function')
        dispatch.body = copy.deepcopy(branches[0].body)+[ast.Return(value=ast.Name(id='client_facts', ctx=ast.Load()))]
        source = prelude+ast.unparse(ast.fix_missing_locations(ast.Module(body=[*constants, *nodes, dispatch], type_ignores=[])))
        with patch.dict(os.environ, {'MYPYPATH': os.pathsep.join((str(tools), str(tools.parent/'ck3_autonomous_player/src')))}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', 'nul', '-c', source])
        self.assertEqual(code, 0, stdout+stderr)


class FailedLiveWriterLockTests(unittest.TestCase):
    """Real Selection and OS writer lock -> full R0020 resource reducer."""

    def setUp(self) -> None:
        self.case = CaseClientFailureClosureTests('runTest')
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        f = self.case.fixture
        self.closed = self.case.check()
        self.closed.update(release=f.refs['release'], run_id=f.run_dir.name,
                           previous_live=str(f.run_dir), previous_keeper=str(f.keeper))
        self.root = f.root / 'next-selection'
        self.root.mkdir()
        source = self.root / 'source'
        (source / 'tools').mkdir(parents=True)
        self.consumer = source / 'tools/ck3_mod_acceptance_allocate.py'
        self.consumer.write_bytes(Path(allocation.__file__).read_bytes())
        self.source_leaf = source / 'fixture-source.txt'
        self.source_leaf.write_bytes(b'Actual immutable authored source input\n')
        paths: dict[str, Path] = {'source_root': source}
        for name in ('source_index', 'native_source_index', 'dll', 'injector', 'save', 'inventory', 'initial'):
            path = self.root / (name + '.json')
            path.write_bytes(b'{}')
            paths[name] = path
        self.source_index = paths['source_index']
        f.write(self.source_index, {'schema': 'ck3-common-source-index-v1', 'machine_id': f.machine,
            'files': {str(p.relative_to(source)).replace('\\', '/'):
                {key: value for key, value in pin(p).items() if key != 'path'}
                for p in (self.consumer, self.source_leaf)}})
        flags = ['--agent-source-root', '--game-dir', '--bridge-dll', '--bridge-injector',
                 '--bridge-pipe', '--output', '--state-dir', '--plan', '--control-plan-dir',
                 '--fixture-profile', *entry.BUDGET_FLAGS.values(), *entry.SAVED_FLAGS.values()]
        host = self.root / 'host.py'
        host.write_text('import argparse\np=argparse.ArgumentParser()\n' +
                        ''.join('p.add_argument(' + repr(flag) + ')\n' for flag in flags),
                        encoding='utf-8')
        paths['host'] = host
        for name in ('game/binaries', 'userdir', 'artifacts', 'lease', 'bus/bin'):
            (self.root / name).mkdir(parents=True)
        engine = self.root / 'game/binaries/ck3.exe'
        engine.write_bytes(b'Authored non-executable game input')
        bus = self.root / 'bus/bin/codex_task_bus.py'
        bus.write_bytes(b'# Authored bus boundary; never launched\n')

        def row(key: str) -> JsonObject:
            ref = pin(paths[key])
            return {'path_key': key, 'bytes': ref['bytes'], 'sha256': ref['sha256']}

        manifest: JsonObject = {'schema': entry.MANIFEST_SCHEMA, 'machine_id': f.machine,
            'source_root': {'path_key': 'source_root'}, 'host': row('host'),
            'source_index': row('source_index'), 'native_source_index': row('native_source_index'),
            'native': {'dll': row('dll'), 'injector': row('injector')},
            'game': {'version': 'authored-not-live', 'exe_sha256': pin(engine)['sha256']},
            'capabilities': {}}
        manifest_path = self.root / 'manifest.json'
        f.write(manifest_path, manifest)
        runtime_path = self.root / 'runtime.json'
        f.write(runtime_path, {'schema': entry.RUNTIME_SCHEMA, 'machine_id': f.machine,
            'manifest': pin(manifest_path), 'python': sys.executable, 'repo_root': str(source),
            'game_dir': str(self.root / 'game'), 'userdir_root': str(self.root / 'userdir'),
            'artifacts_root': str(self.root / 'artifacts'),
            'paths': {key: str(value) for key, value in paths.items()},
            'allocation': {'lease_repo': str(self.root / 'lease'), 'task_bus': pin(bus)}})
        products_path = self.root / 'products.json'
        saved = pin(paths['save'])
        startup: JsonObject = {'mode': 'saved_campaign', 'state_dir': str(self.root / 'state'),
            'saved_campaign': {'save': saved['path'], 'bytes': saved['bytes'], 'sha256': saved['sha256'],
                              'player_id': 1, 'date_raw': 1, 'product_inventory': str(paths['inventory'])}}
        f.write(products_path, {'schema': entry.PRODUCTS_SCHEMA, 'products': {'closure-fixture': {
            'cases': [{'id': 'core', 'status': 'ready', 'startup': startup,
                       'initial_plan': pin(paths['initial']),
                       'budgets': {'command_timeout': 120, 'readiness_timeout': 1800, 'timeout': 10800,
                                   'hold_seconds': 9000, 'poll_interval': 0.25},
                       'required_mcp_tools': []}]}}})
        prepared_path = self.root / 'prepared.json'
        f.write(prepared_path, {'schema': 'ck3-mod-acceptance-prepared-case-v1',
            'product': 'closure-fixture', 'case': 'core', 'runtime_manifest': pin(manifest_path),
            'startup': startup, 'case_inputs': {}})
        self.selection = entry.Selection(runtime_path, products_path, 'closure-fixture',
                                         'core', prepared_path=prepared_path)
        self.assertEqual(self.selection.preflight()['blockers'], [])
        self.args = argparse.Namespace(previous_live=f.run_dir, previous_keeper=f.keeper,
            previous_failure_close=f.close, previous_release=f.release_path)
        self.admission = self.root / 'admissions'
        f.write(self.admission / '000001/allocation.json', {'live': str(f.run_dir), 'run_id': f.run_dir.name})
        self.binding: MachineBinding = {'machine_id': f.machine, 'state_root': str(self.root / 'ID-state'),
                                       'admission_root': str(self.admission)}
        self.packet: JsonObject = {'tasks': [json_object(f.leaves['release'])['task']]}
        self.active = False
        self.calls: list[str] = []

    def claim(self, mutation: Callable[[], None] | None = None,
              after_reducer: Callable[[], None] | None = None) -> Path:
        f = self.case.fixture
        original_lock = ids._exclusive_file_lock
        original_reducer = allocation.previous_failed_live_resource_closure

        @contextlib.contextmanager
        def locked(path: Path) -> Iterator[None]:
            with original_lock(path):
                self.active = True
                try:
                    if mutation is not None:
                        mutation()
                    yield
                finally:
                    self.active = False

        def bus(lease_repo: Path, bus_dir: Path, bus_sha: str, audit_dir: Path) -> object:
            self.assertTrue(self.active)
            self.calls.append('fresh_bus')
            return self.packet

        def reducer(previous: Path, freeze: dict[str, object], close: Path, keeper: Path,
                    release: Path, packet: dict[str, object]) -> dict[str, object]:
            self.assertTrue(self.active)
            self.calls.append('real_reducer')
            result = original_reducer(previous, freeze, close, keeper, release, packet)
            if after_reducer is not None:
                after_reducer()
            return result

        with self.case.boundaries(), patch.dict(sys.modules, {'psutil': f.psutil}), \
                patch.object(ids, '_exclusive_file_lock', locked), \
                patch.object(allocation, 'current_screen_absent', side_effect=bus), \
                patch.object(allocation, 'previous_failed_live_resource_closure', side_effect=reducer):
            return allocation.claim_machine_admission(self.binding, self.selection, self.args,
                                                      copy.deepcopy(self.closed))

    def assert_no_new_intent(self) -> None:
        self.assertFalse((self.admission / 'machine.json').exists())
        self.assertFalse((self.admission / '000002').exists())

    def test_real_selection_writer_lock_full_reducer_and_serialized_unknowns(self) -> None:
        originals = {key: Path(text_field(json_object(ref), 'path')).read_bytes()
                     for key, ref in self.case.fixture.refs.items()}
        record = self.claim()
        self.assertEqual(self.calls, ['fresh_bus', 'real_reducer'])
        self.assertEqual(record.name, '000002')
        intent = json_object(json.loads((record / 'intent.json').read_bytes()))
        facts = object_field(object_field(intent, 'closure'), 'failure_cleanup')
        self.assertEqual(facts['original_host_exit_code'], 0)
        self.assertEqual(facts['native_reported_ck3_exit_code'], 1)
        self.assertIsNone(facts['original_ck3_exit_code'])
        self.assertIsNone(facts['native_cleanup_qualified'])
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass',
                    'original_retained_wait_signaled'):
            self.assertIs(facts[key], False)
        self.assertEqual(intent, json.loads(json.dumps(intent)))
        self.assertEqual(originals, {key: Path(text_field(json_object(ref), 'path')).read_bytes()
                                    for key, ref in self.case.fixture.refs.items()})

    def test_locked_original_source_and_bundle_drift_reject_without_intent(self) -> None:
        f = self.case.fixture
        for label, path in [('bundle', f.close), ('release', f.release_path),
                            ('original_native_report', Path(text_field(json_object(f.refs['native_report']), 'path'))),
                            ('selected_source', self.source_leaf), ('actual_consumer', self.consumer),
                            ('selected_index', self.source_index)]:
            with self.subTest(drift=label):
                original = path.read_bytes()
                self.calls.clear()
                try:
                    with self.assertRaises(ValueError):
                        def change() -> None:
                            path.write_bytes(original + b' ')
                        self.claim(change)
                finally:
                    path.write_bytes(original)
                self.assert_no_new_intent()

    def test_evidence_and_source_drift_after_real_reducer_reject_without_intent(self) -> None:
        f = self.case.fixture
        native = Path(text_field(json_object(f.refs['native_report']), 'path'))
        for label, path in [('original_native_report', native), ('selected_source', self.source_leaf)]:
            with self.subTest(after_reducer_drift=label):
                original = path.read_bytes()
                def change() -> None:
                    path.write_bytes(original + b' ')
                try:
                    with self.assertRaises(ValueError):
                        self.claim(after_reducer=change)
                finally:
                    path.write_bytes(original)
                self.assert_no_new_intent()

    def test_fresh_bus_or_os_generation_reject_without_intent(self) -> None:
        f = self.case.fixture
        baseline = copy.deepcopy(self.packet)
        for changed in ('screen', 'process'):
            with self.subTest(changed=changed):
                if changed == 'screen':
                    self.packet = {'tasks': [{'resources': ['ck3-screen:acquired']}]}
                else:
                    host_pid = json_object(f.leaves['host_started']).get('pid')
                    if type(host_pid) is not int:
                        raise ValueError('Authored host PID must remain an exact integer')
                    self.case.alive.add(host_pid)
                try:
                    with self.assertRaises(ValueError):
                        self.claim()
                finally:
                    self.packet = copy.deepcopy(baseline)
                    self.case.alive.clear()
                self.assertEqual(self.calls[-2:], ['fresh_bus', 'real_reducer'])
                self.assert_no_new_intent()

    def test_exact_new_locked_helper_scope_is_strict(self) -> None:
        from mypy import api
        tools = Path(__file__).parent
        source = ast.parse((tools / 'ck3_mod_acceptance_allocate.py').read_text(encoding='utf-8-sig'))
        names = {'_FailedLiveBusQuery', 'revalidate_failed_live_resource_admission'}
        nodes = [copy.deepcopy(node) for node in source.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        prelude = '''from __future__ import annotations
import argparse
from pathlib import Path
from typing import Protocol, runtime_checkable
from ck3_mod_acceptance import Selection, path_at, pin, read_json, check_pin
from ck3_mod_acceptance_background_types import JsonObject, json_object, file_pin, object_field, text_field
from ck3_mod_acceptance_allocate import current_screen_absent, previous_failed_live_resource_closure, _canonical_source_index_files
'''
        program = prelude + ast.unparse(ast.fix_missing_locations(ast.Module(body=list(nodes), type_ignores=[])))
        source_roots = (str(tools), str(Path(allocation.__file__).parents[1] / 'ck3_autonomous_player/src'),
                        str(Path(entry.__file__).parent), str(Path(entry.__file__).parents[1] / 'ck3_autonomous_player/src'))
        with patch.dict(os.environ, {'MYPYPATH': os.pathsep.join(source_roots)}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', os.devnull, '-c', program])
        self.assertEqual(code, 0, stdout + stderr)


class ProcessAbsent(Exception):
    pass


if __name__ == '__main__':
    unittest.main()
