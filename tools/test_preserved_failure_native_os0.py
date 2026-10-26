"""R0001 actual source shapes -> existing failed-live resource consumer.

Relocated files and absent processes are authored regression inputs. The source
excerpt preserves the full originals' pins separately and grants no live PASS.
"""
from __future__ import annotations

import copy
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
from ck3_mod_acceptance_background_types import JsonObject, JsonValue, file_pin, json_object, text_field, strings_field
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

    def check(self) -> JsonObject:
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
            return f.check()

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


class ProcessAbsent(Exception):
    pass


if __name__ == '__main__':
    unittest.main()
