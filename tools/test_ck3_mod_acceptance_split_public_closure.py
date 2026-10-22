"""R11's actual split-command producer fields reach the shared failed-live consumer.

The source leaves retain their original pins. Relocated files and process absence
below are authored test inputs, never another observation of the game or AI.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance import pin


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError('Object required')
    return {key: item for key, item in value.items() if isinstance(key, str)}


def string(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError('Text required')
    return value


def integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError('Exact integer required')
    return value


def source_fixture() -> dict[str, object]:
    path = Path(__file__).parent / 'fixtures/ck3_r11_failed_resource_closure.json'
    value = obj(json.loads(path.read_text(encoding='utf-8')))
    if value.get('schema') != 'ck3-r11-failed-resource-closure-source-excerpt-v1':
        raise ValueError('Source excerpt schema drifted')
    return value


class SplitPublicClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = source_fixture()
        self.machine = string(self.source['machine_id'])
        self.original_leaves = obj(self.source['leaves'])
        self.leaves = obj(self.relocate(self.original_leaves))
        self.freeze = obj(self.leaves['frozen_argv'])
        self.run_dir = self.root / 'external/live' / string(self.source['run_id'])
        self.keeper = Path(string(obj(self.leaves['ready_context'])['keeper_root']))
        self.state = Path(string(self.freeze['state_dir']))
        self.close = self.root / 'closure.json'
        self.refs: dict[str, object] = {}
        original_pins = obj(self.source['source_pins'])
        for key, raw_pin in original_pins.items():
            path = Path(string(self.relocate(obj(raw_pin)['path'])))
            if key in self.leaves:
                self.refs[key] = self.write(path, self.leaves[key])
            elif key == 'native_report':
                self.refs[key] = self.write(path, self.leaves['native_report_projection'])
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'Authored STOP\n' if key == 'keeper_stop' else b'')
                self.refs[key] = pin(path)
        # The authored files have their own pins; the actual source pins stay in
        # source_fixture and are never presented as hashes of these new files.
        ready = obj(self.leaves['ready_context'])
        ready['prepared_case'] = self.refs['prepared_case']
        ready['frozen_argv'] = self.refs['frozen_argv']
        self.refs['ready_context'] = self.write(self.run_dir / 'ready-context.json', ready)
        self.write(self.run_dir / 'run-context-r11-a01.json', ready)
        self.normal = obj(self.leaves['normal_close'])
        self.native_report = obj(self.leaves['native_report_projection'])
        self.native = obj(obj(self.native_report['session'])['report'])
        self.release = obj(self.leaves['release'])
        self.release_path = Path(string(obj(self.refs['release'])['path']))
        self.bus: dict[str, object] = {'tasks': [self.release['task']]}
        self.bundle: dict[str, object] = {
            'schema': 'ck3-mod-acceptance-failed-live-resource-closure-v1',
            'machine_id': self.machine, 'run_id': self.run_dir.name, 'keeper_root': str(self.keeper),
            'closure_kind': 'retained-wait-expired-then-native-cleanup',
            'public_wait_format': 'command-intent-process-exit-completion',
            'normal_close_qualified': False, 'typed_normal_exit_proven': False,
            'business_pass': False, 'release_pass': False,
            'failed_query': {'step_id': 'xalw-core-0004', 'tool': 'ck3_open_player_inventory_window_v1'},
            'original_evidence': self.refs,
        }
        self.write(self.close, self.bundle)
        self.live: set[int] = set()
        self.blockers: list[dict[str, object]] = []
        self.created: dict[int, float] = {}
        for key in ('host_started', 'keeper_process', 'retained_identity'):
            identity = obj(self.leaves[key])
            pid, created = identity['pid'], identity['create_time']
            if type(pid) is not int or not isinstance(created, (int, float)):
                raise ValueError('Exact fixture identity required')
            self.created[pid] = float(created)
        class MissingProcess(Exception):
            pass
        def process(pid: int) -> SimpleNamespace:
            if pid not in self.live:
                raise MissingProcess()
            return SimpleNamespace(create_time=lambda: self.created[pid])
        self.psutil = SimpleNamespace(Process=process, NoSuchProcess=MissingProcess,
            pid_exists=lambda pid: pid in self.live, process_iter=lambda fields: [])

    def relocate(self, value: object) -> object:
        if isinstance(value, str):
            prefix = 'D:/workspace/ck3-living-artifacts-20261022'
            normalized = value.replace('\\', '/')
            if normalized.startswith(prefix):
                return str(self.root / 'external' / normalized[len(prefix):].lstrip('/'))
            return value
        if isinstance(value, list):
            return [self.relocate(item) for item in value]
        if isinstance(value, dict):
            return {key: self.relocate(item) for key, item in value.items()}
        return value

    def write(self, path: Path, value: object) -> dict[str, object]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + '\n', encoding='utf-8')
        return obj(pin(path))

    def reseal(self, key: str, value: object) -> None:
        path = Path(string(obj(self.refs[key])['path']))
        self.refs[key] = self.write(path, value)
        self.write(self.close, self.bundle)

    def check(self) -> dict[str, object]:
        # Retain the original source's ordering rather than the temporary copy's
        # new mtime. This is an authored filesystem observation, not an OS claim.
        normal_ns = int(string(self.source['normal_close_mtime_ns_decimal']))
        actual_stat = Path.stat
        normal_path = self.run_dir / 'case-output/normal-close-result.json'
        def stat(path: Path, *, follow_symlinks: bool = True) -> object:
            original = actual_stat(path, follow_symlinks=follow_symlinks)
            if path == normal_path:
                return SimpleNamespace(st_size=original.st_size, st_mtime_ns=normal_ns,
                                       st_mode=original.st_mode)
            return original
        with patch.dict(sys.modules, {'psutil': self.psutil}), \
                patch.object(allocation, 'runtime_process_inventory',
                             return_value={'blockers': self.blockers}), \
                patch.object(Path, 'stat', stat):
            return obj(allocation.previous_failed_live_resource_closure(self.run_dir, self.freeze, self.close,
                self.keeper, self.release_path, self.bus))

    def test_actual_r11_fields_roundtrip_through_whole_consumer(self) -> None:
        self.assertEqual(json.loads(json.dumps(self.source)), self.source)
        proof = obj(self.check()['failure_cleanup'])
        self.assertEqual(proof['original_host_exit_code'], 1)
        self.assertEqual(proof['native_reported_ck3_exit_code'], 1)
        self.assertIsNone(proof['original_ck3_exit_code'])
        self.assertIsNone(proof['original_host_error'])
        self.assertIsNone(proof['native_cleanup_qualified'])
        self.assertTrue(proof['original_host_wait_proven'])
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass',
                    'release_pass', 'actual_retained_os0', 'failure_lifecycle_completed'):
            self.assertIs(proof[key], False)

    def test_split_wait_fields_types_and_sources_are_strict(self) -> None:
        original = copy.deepcopy(obj(self.leaves['run_wait']))
        for change in ({'pid': True}, {'pid': 2844.0}, {'returncode': 0},
                       {'actual_original_popen_wait': False}, {'extra': None}):
            with self.subTest(change=change):
                self.reseal('run_wait', {**original, **change})
                with self.assertRaises(ValueError):
                    self.check()
        missing = dict(original)
        missing.pop('pid')
        self.reseal('run_wait', missing)
        with self.assertRaises(ValueError):
            self.check()

    def test_split_command_completion_and_argv_cannot_drift(self) -> None:
        for key, change in (
            ('run_completion', {'exit_code': True}),
            ('run_completion', {'command': str(self.root / 'other-command.json')}),
            ('run_process', {'argv': ['other.exe']}),
            ('run_intent', {'stage': 'allocate'}),
            ('run_command', {'machine_id': 'other-machine'}),
        ):
            with self.subTest(key=key, change=change):
                original = copy.deepcopy(self.leaves[key])
                self.reseal(key, {**obj(original), **change})
                with self.assertRaises(ValueError):
                    self.check()
                self.reseal(key, original)

    def test_null_error_requires_exact_failed_step_and_diagnostic(self) -> None:
        report = copy.deepcopy(self.native_report)
        for steps in ([], [{'id': 'xalw-core-0004', 'ok': True}],
                      [{'id': 'xalw-core-0004', 'ok': False, 'error': '',
                        'finished_at': '2026-10-22T15:13:55+00:00', 'plan': {}}]):
            with self.subTest(steps=steps):
                self.reseal('native_report', {**report, 'steps': steps})
                with self.assertRaises(ValueError):
                    self.check()
        self.reseal('native_report', report)
        self.bundle['failed_query'] = {'step_id': 'xalw-core-0004', 'tool': 'wrong'}
        self.write(self.close, self.bundle)
        with self.assertRaises(ValueError):
            self.check()

    def test_normal_os_and_cleanup_credit_cannot_be_upgraded(self) -> None:
        original = copy.deepcopy(self.normal)
        for key in ('normal_close_qualified', 'business_pass', 'failure_lifecycle_completed'):
            with self.subTest(key=key):
                self.reseal('normal_close', {**original, key: True})
                with self.assertRaises(ValueError):
                    self.check()
        self.reseal('normal_close', original)
        native = obj(obj(self.native_report['session'])['report'])
        shutdown = obj(native['shutdown'])
        shutdown['job_active_processes_final'] = 1
        native['shutdown'] = shutdown
        self.native_report['session'] = {'error': None, 'report': native}
        self.reseal('native_report', self.native_report)
        with self.assertRaises(ValueError):
            self.check()

    def test_original_processes_screen_and_controls_must_be_absent(self) -> None:
        pids = list(self.created)
        pids += [integer(obj(self.leaves['host_supervisor'])['pid']),
                 integer(obj(self.leaves['run_process'])['pid']),
                 integer(obj(self.leaves['allocate_process'])['pid'])]
        for pid in pids:
            with self.subTest(pid=pid):
                self.live = {pid}
                with self.assertRaisesRegex(ValueError, 'still present'):
                    self.check()
        self.live = set()
        self.blockers = [{'pid': 999, 'name': 'ck3.exe'}]
        with self.assertRaisesRegex(ValueError, 'still running'):
            self.check()
        self.blockers = []
        self.bus = {'tasks': [{'resources': ['ck3-screen:acquired']}]}
        with self.assertRaisesRegex(ValueError, 'screen owner'):
            self.check()
        self.bus = {'tasks': []}
        self.write(self.state / 'control/unsafe-cleanup.json', {})
        with self.assertRaisesRegex(ValueError, 'controls remain'):
            self.check()

    def test_keeper_wait_and_cas_must_remain_original_and_complete(self) -> None:
        original = obj(self.leaves['keeper_exit'])
        self.reseal('keeper_exit', {**original, 'keeper_actual_exit_code': 1})
        with self.assertRaisesRegex(ValueError, 'keeper wait/thread'):
            self.check()
        self.reseal('keeper_exit', original)
        release = copy.deepcopy(self.release)
        task = obj(release['task'])
        task['resources'] = ['ck3-screen:acquired']
        release['task'] = task
        self.reseal('release', release)
        with self.assertRaises(ValueError):
            self.check()

    def test_actual_named_pipe_argv_does_not_mask_a_live_frozen_host(self) -> None:
        argv = self.freeze['argv']
        if not isinstance(argv, list):
            raise ValueError('Frozen argv list required')
        host = Path(string(argv[4]))
        arguments = ['python.exe', 'unrelated-provider.py', '--pipe',
                     '\\\\.\\pipe\\xar_ck3_bridge_mcp_administrator']
        process = SimpleNamespace(info={'name': 'python.exe'}, cmdline=lambda: arguments)
        self.psutil.process_iter = lambda fields: [process]
        self.check()
        arguments.append(str(host))
        with self.assertRaisesRegex(ValueError, 'frozen host interpreter'):
            self.check()


if __name__ == '__main__':
    unittest.main(verbosity=2)
