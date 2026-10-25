"""R11's actual split-command producer fields reach the shared failed-live consumer.

The source leaves retain their original pins. Relocated files and process absence
below are authored test inputs, never another observation of the game or AI.
"""
from __future__ import annotations

import copy
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Literal
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance import pin

PUBLIC_OPERATIONS: tuple[tuple[Literal['run', 'allocate'], int], ...] = (('run', 2), ('allocate', 0))


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


def recorded_source_fixture() -> dict[str, object]:
    path = Path(__file__).parent / 'fixtures/ck3_recorded_actual_public_wait_r0042.json'
    value = obj(json.loads(path.read_text(encoding='utf-8')))
    if value.get('schema') != 'ck3-recorded-actual-public-wait-source-excerpt-v1':
        raise ValueError('Recorded source excerpt schema drifted')
    leaves, pins = obj(value['leaves']), obj(value['source_pins'])
    for name, raw in leaves.items():
        ref = obj(pins[name])
        if name.endswith('.py'):
            data = string(raw).encode('utf-8')
            if len(data) != ref['bytes'] or hashlib.sha256(data).hexdigest() != ref['sha256']:
                raise ValueError('Actual recorded producer source pin differs')
    return value


def gui_os0_source_fixture() -> dict[str, object]:
    path = Path(__file__).parent / 'fixtures/ck3_r43_failed_gui_os0_closure.json'
    value = obj(json.loads(path.read_text(encoding='utf-8')))
    if value.get('schema') != 'ck3-failed-gui-os0-source-excerpt-v1':
        raise ValueError('GUI OS0 source excerpt schema differs')
    raw = string(obj(value['leaves'])['public_command_producer']).encode('utf-8')
    ref = obj(obj(value['source_pins'])['public_command_producer'])
    if len(raw) != ref['bytes'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
        raise ValueError('Actual R43 recorded producer source pin differs')
    return value


class SplitPublicClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
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

    def install_recorded_producer(self, fixture: dict[str, object] | None = None) -> None:
        """Run the actual wrapper's publication tail against harmless real children.

        Selection, Steam and game launch are deliberately outside this excerpt.
        The machine, paths and child results are authored; original R42 bytes and
        source SHA remain separately pinned in the immutable JSON fixture.
        """
        fixture = recorded_source_fixture() if fixture is None else fixture
        leaves = obj(fixture['leaves'])
        source_key = ('public_command_producer' if 'public_command_producer' in leaves
                      else 'root_execute_r0042.operation.py')
        tree = ast.parse(string(leaves[source_key]))
        tails: list[ast.With] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for index, statement in enumerate(node.body):
                    if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and \
                            isinstance(statement.targets[0], ast.Name) and statement.targets[0].id == 'child':
                        node.body = node.body[index:]
                        tails.append(node)
        if len(tails) != 1:
            raise ValueError('Unique actual Popen publication tail required')
        tail = tails[0]
        declaration = tail.body[1]
        if not isinstance(declaration, ast.Assign) or not isinstance(declaration.value, ast.Dict):
            raise ValueError('Actual producer receipt declaration required')
        declaration.value.values[1] = ast.Constant(value=self.machine)
        prelude = """from pathlib import Path
from datetime import datetime,timezone
import sys,subprocess,os,json,time
mode=sys.argv[1];argv=json.loads(sys.argv[2]);base=Path(sys.argv[3])
REPO=Path.cwd();env=dict(os.environ);stem=mode+'-'+sys.argv[4]
start=base/(stem+'.STARTED.actual.json');exitp=base/(stem+'.EXIT.actual.json')
t=time.monotonic_ns()
"""
        source = prelude + ast.unparse(ast.fix_missing_locations(ast.Module(body=[tail], type_ignores=[])))
        source += '\nraise SystemExit(code)\n'
        producer = self.root / 'authored-public-producer.py'
        producer.write_text(source, encoding='utf-8', newline='\n')
        self.refs['public_command_producer'] = pin(producer)
        base = self.root / 'recorded'
        base.mkdir()
        allocation_argv = obj(self.leaves['allocate_command'])['argv']
        if not isinstance(allocation_argv, list):
            raise ValueError('Allocation argv required')
        attempt = string(allocation_argv[allocation_argv.index('--attempt') + 1])
        for mode, code in PUBLIC_OPERATIONS:
            raw_argv = obj(self.leaves[mode + '_command'])['argv']
            if not isinstance(raw_argv, list) or any(not isinstance(arg, str) for arg in raw_argv):
                raise ValueError('Authored public argv required')
            argv = [string(arg) for arg in raw_argv]
            argv[0] = sys.executable
            entry = Path(argv[4])
            entry.parent.mkdir(parents=True, exist_ok=True)
            entry.write_text("import sys\nraise SystemExit(2 if sys.argv[1]=='run' else 0)\n",
                             encoding='utf-8', newline='\n')
            packet = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(producer), mode,
                json.dumps(argv), str(base), attempt], cwd=self.root, env=dict(os.environ),
                capture_output=True, check=False, timeout=20)
            self.assertEqual(packet.returncode, code, packet.stderr.decode('utf-8'))
            for key, suffix in (('started', '.STARTED.actual.json'), ('wait', '.EXIT.actual.json'),
                                ('stdout', '.stdout.json'), ('stderr', '.stderr.txt')):
                self.refs[mode + '_' + key] = pin(base / (mode + '-' + attempt + suffix))
            for key in ('command', 'intent', 'process', 'completion', 'argv'):
                self.refs.pop(mode + '_' + key, None)
        self.bundle['public_wait_format'] = 'recorded-actual-command-started-exit-v1'
        self.write(self.close, self.bundle)

    def install_gui_os0(self) -> None:
        """Relocate actual R43 shapes onto authored files and absent process identities."""
        fixture = gui_os0_source_fixture()
        self.install_recorded_producer(fixture)
        leaves = obj(fixture['leaves'])
        game = obj(copy.deepcopy(leaves['retained_identity']))
        authored_game = obj(self.leaves['retained_identity'])
        pid, created = integer(authored_game['pid']), authored_game['create_time']
        game.update(pid=pid, create_time=created)
        retained = obj(copy.deepcopy(leaves['retained_exit']))
        retained.update(pid=pid, create_time=created)
        review = obj(copy.deepcopy(leaves['manual_gui_review']))
        review.update(run_id=self.run_dir.name, pid=pid, create_time=created)
        request = obj(copy.deepcopy(leaves['normal_quit_awaiting']))
        request.update(run_id=self.run_dir.name, pid=pid, create_time=created)
        request_ref = self.write(self.run_dir / 'case-output/normal-quit-awaiting.json', request)
        self.refs['normal_quit_awaiting'] = request_ref
        review['quit_request'] = request_ref
        image = self.root / 'authored-gui-review.png'
        image.write_bytes(b'Authored visual evidence; no game observation')
        image_ref = pin(image)
        review.update(evidence=[image_ref], autosave_unchecked_screenshot=image_ref,
                      after_click_screenshot=image_ref, final_click=image_ref)
        self.refs['manual_gui_review'] = self.write(
            self.run_dir / 'case-output/normal-quit-root-result.json', review)
        normal = obj(copy.deepcopy(leaves['normal_close']))
        normal.update(retained_handle=retained, root_normal_gui_review=review,
                      operator_normal_gui_review=review)
        report = obj(copy.deepcopy(leaves['native_report_projection']))
        report.update(state_dir=str(self.state), agent_source_root=self.freeze['source_root'],
                      server_stderr=self.native_report['server_stderr'])
        argv = self.freeze['argv']
        if not isinstance(argv, list):
            raise ValueError('Actual frozen argv list required')
        report['pipe'] = argv[argv.index('--bridge-pipe') + 1]
        native = obj(obj(report['session'])['report'])
        native['pid'] = pid
        shutdown = obj(native['shutdown'])
        shutdown.update(ck3_pid=pid, control_files_absent={str(self.state / 'control/ck3.json'): True})
        native['shutdown'] = shutdown
        report['session'] = {'error': None, 'report': native}
        self.normal, self.native_report, self.native = normal, report, native
        self.bundle['closure_kind'] = 'failed-host-gui-os0-cleanup-complete'
        self.bundle.pop('failed_query')
        for key, value in (('normal_close', normal), ('native_report', report),
                           ('retained_identity', game), ('retained_exit', retained)):
            self.reseal(key, value)
        release = copy.deepcopy(self.release)
        task, event = obj(release['task']), obj(release['event'])
        task['state'] = event['state'] = 'waiting'
        event['retirement'] = {'kind': 'expired-own-claim-released',
            'business_status': 'unresolved_red', 'prior_sequence': integer(task['last_sequence']) - 1}
        release.update(task=task, event=event)
        self.release = release
        self.bus = {'tasks': [task]}
        self.reseal('release', release)

    def test_actual_r43_gui_os0_leaves_and_public_wait_roundtrip(self) -> None:
        fixture = gui_os0_source_fixture()
        self.assertEqual(json.loads(json.dumps(fixture)), fixture)
        leaves = obj(fixture['leaves'])
        report = obj(leaves['native_report_projection'])
        proof = allocation.validate_failed_gui_os0_cleanup(leaves['normal_close'],
            leaves['retained_exit'], leaves['retained_identity'], obj(report['session'])['report'],
            report, leaves['manual_gui_review'], string(fixture['run_id']))
        self.assertEqual(json.loads(json.dumps(proof)), proof)
        self.assertIs(proof['actual_retained_os0'], True)
        producer = allocation.validate_recorded_public_producer(
            string(leaves['public_command_producer']).encode('utf-8'), string(fixture['machine_id']))
        for mode, code in PUBLIC_OPERATIONS:
            allocation.validate_recorded_public_wait(leaves[mode + '_wait'], leaves[mode + '_started'],
                producer, string(fixture['machine_id']), mode, code)

    def test_real_r43_producer_reaches_gui_os0_whole_consumer(self) -> None:
        self.install_gui_os0()
        result = obj(self.check()['failure_cleanup'])
        self.assertIs(result['actual_retained_os0'], True)
        self.assertIs(result['native_cleanup_qualified'], True)
        self.assertEqual(result['original_host_exit_code'], 1)
        self.assertEqual(result['original_ck3_exit_code'], 0)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(result[key], False)

    def test_actual_new_process_pid_collision_does_not_resurrect_original_supervisor(self) -> None:
        from ck3_mod_acceptance_launcher import process_identity
        self.install_gui_os0()
        child = subprocess.Popen([sys.executable, '-B', '-c', 'import sys;sys.stdin.buffer.read(1)'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            current = process_identity(child.pid)
            supervisor = obj(copy.deepcopy(self.leaves['host_supervisor']))
            supervisor.update(pid=child.pid, original_popen_identity={
                'pid': child.pid, 'birth_filetime': str(int(current['birth_filetime']) - 1)})
            self.reseal('host_supervisor', supervisor)
            self.live = {child.pid}
            proof = obj(self.check()['failure_cleanup'])
            self.assertEqual(proof['current_supervisor_generation'], current)
            self.assertIs(proof['original_supervisor_generation_absent'], True)
            self.assertIs(proof['normal_close_qualified'], False)
            supervisor['original_popen_identity'] = current
            self.reseal('host_supervisor', supervisor)
            with self.assertRaisesRegex(ValueError, 'original supervisor still present'):
                self.check()
        finally:
            child.communicate(input=b'x', timeout=10)
            self.assertEqual(child.returncode, 0)
            self.live = set()

    def test_supervisor_generation_requires_exact_decimal_birth_and_json_roundtrip(self) -> None:
        original = {'pid': 123, 'original_popen_identity': {'pid': 123, 'birth_filetime': '134372440145484654'}}
        current = {'pid': 123, 'birth_filetime': '134372440145484655'}
        proof = allocation.validate_failed_supervisor_generation(original, current)
        self.assertEqual(json.loads(json.dumps(proof)), proof)
        for bad in (True, 134372440145484655, '0134372440145484655', '0', '18446744073709551616',
                    '134372440145484654', '134372440145484653'):
            with self.subTest(birth=bad), self.assertRaises(ValueError):
                allocation.validate_failed_supervisor_generation(original, {**current, 'birth_filetime': bad})
        for key in current:
            missing = dict(current)
            missing.pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                allocation.validate_failed_supervisor_generation(original, missing)
        with self.assertRaises(ValueError):
            allocation.validate_failed_supervisor_generation(original, {**current, 'pid': True})
        with self.assertRaises(ValueError):
            allocation.validate_failed_supervisor_generation({'pid': 123}, None)

    def test_gui_os0_whole_consumer_rejects_wrong_missing_and_wrong_typed_facts(self) -> None:
        self.install_gui_os0()
        retained = obj(copy.deepcopy(self.normal['retained_handle']))
        for key, bad in [('pid', True), ('exit_code', False), ('exit_code', 1),
                         ('signaled', 1), ('actual_retained_os0', None), ('create_time', float('nan'))]:
            with self.subTest(retained_key=key, value=bad):
                self.reseal('retained_exit', {**retained, key: bad})
                with self.assertRaises(ValueError):
                    self.check()
        for key in retained:
            missing = dict(retained)
            missing.pop(key)
            self.reseal('retained_exit', missing)
            with self.subTest(missing_retained=key), self.assertRaises(ValueError):
                self.check()
        self.reseal('retained_exit', retained)
        for key, bad in [('normal_close_qualified', True), ('business_pass', True),
                         ('failure_lifecycle_completed', False), ('cleanup_ok', 1),
                         ('host_error', None), ('managed_thread_finished', False)]:
            self.reseal('normal_close', {**self.normal, key: bad})
            with self.subTest(normal_key=key), self.assertRaises(ValueError):
                self.check()
        self.reseal('normal_close', self.normal)
        for bad in (None, True, 1):
            native = copy.deepcopy(self.native)
            native['process_exit_code'] = bad
            self.reseal('native_report', {**self.native_report, 'session': {'error': None, 'report': native}})
            with self.subTest(native_code=bad), self.assertRaises(ValueError):
                self.check()
        self.reseal('native_report', self.native_report)

    def test_gui_os0_preserves_review_failure_format_and_waiting_release_guards(self) -> None:
        self.install_gui_os0()
        review = obj(copy.deepcopy(self.normal['root_normal_gui_review']))
        self.reseal('manual_gui_review', {**review, 'run_id': 'other-run'})
        with self.assertRaises(ValueError):
            self.check()
        self.reseal('manual_gui_review', review)
        review_ref = obj(copy.deepcopy(self.refs['manual_gui_review']))
        for change in ({'bytes': True}, {'bytes': 1.0}, {'bytes': None},
                       {'sha256': None}, {'path': None}, {'extra': None}):
            self.refs['manual_gui_review'] = {**review_ref, **change}
            self.write(self.close, self.bundle)
            with self.subTest(review_pin=change), self.assertRaises(ValueError):
                self.check()
        for key in review_ref:
            missing = dict(review_ref)
            missing.pop(key)
            self.refs['manual_gui_review'] = missing
            self.write(self.close, self.bundle)
            with self.subTest(missing_review_pin=key), self.assertRaises(ValueError):
                self.check()
        self.refs['manual_gui_review'] = review_ref
        self.write(self.close, self.bundle)
        visual = review['evidence']
        if not isinstance(visual, list) or not visual:
            raise ValueError('Authored visual evidence required')
        image = Path(string(obj(visual[0])['path']))
        image.write_bytes(b'drift')
        with self.assertRaises(ValueError):
            self.check()
        image.write_bytes(b'Authored visual evidence; no game observation')
        for key, bad in [('public_wait_format', 'command-intent-process-exit-completion'),
                         ('failed_query', {'step_id': 'invented', 'tool': 'invented'})]:
            original = copy.deepcopy(self.bundle)
            self.bundle[key] = bad
            self.write(self.close, self.bundle)
            with self.subTest(bundle_key=key), self.assertRaises(ValueError):
                self.check()
            self.bundle = original
        self.write(self.close, self.bundle)
        for bad_retirement in (None, {}, {'kind': 'expired-own-claim-released',
                             'business_status': 'done', 'prior_sequence': 1}):
            release = copy.deepcopy(self.release)
            event = obj(release['event'])
            event['retirement'] = bad_retirement
            release['event'] = event
            self.reseal('release', release)
            with self.subTest(retirement=bad_retirement), self.assertRaises(ValueError):
                self.check()

    def test_actual_r42_recorded_sources_and_receipts_roundtrip(self) -> None:
        fixture = recorded_source_fixture()
        self.assertEqual(json.loads(json.dumps(fixture)), fixture)
        leaves = obj(fixture['leaves'])
        machine = string(fixture['machine_id'])
        producer = allocation.validate_recorded_public_producer(
            string(leaves['root_execute_r0042.operation.py']).encode('utf-8'), machine)
        for mode, code in PUBLIC_OPERATIONS:
            if mode not in ('run', 'allocate'):
                raise ValueError('Explicit operation required')
            result = allocation.validate_recorded_public_wait(
                leaves[mode + '-a2026102308.EXIT.actual.json'],
                leaves[mode + '-a2026102308.STARTED.actual.json'], producer, machine, mode, code)
            self.assertGreater(result['pid'], 0)

    def test_real_recorded_producer_reaches_whole_failed_live_consumer(self) -> None:
        self.install_recorded_producer()
        result = obj(self.check()['failure_cleanup'])
        self.assertIs(result['normal_close_qualified'], False)
        self.assertIs(result['business_pass'], False)
        self.assertIs(result['actual_retained_os0'], False)
        self.assertIsNone(result['original_ck3_exit_code'])
        self.assertEqual(result['original_host_exit_code'], 1)
        self.assertEqual(result['native_reported_ck3_exit_code'], 1)

    def test_recorded_receipt_fields_types_and_chronology_reject_drift(self) -> None:
        fixture = recorded_source_fixture()
        leaves = obj(fixture['leaves'])
        first = obj(leaves['run-a2026102308.STARTED.actual.json'])
        final = obj(leaves['run-a2026102308.EXIT.actual.json'])
        producer = allocation.validate_recorded_public_producer(
            string(leaves['root_execute_r0042.operation.py']).encode('utf-8'), string(fixture['machine_id']))
        changes: list[dict[str, object]] = [
            {'pid': True}, {'pid': 17480.0}, {'pid': 9007199254740992},
            {'exit_code': True}, {'exit_code': 0}, {'actual_original_popen_wait': 1},
            {'original_wait_pending': None}, {'shell': 0}, {'extra': None},
            {'started_monotonic_ns': 313325580079600}, {'started_monotonic_ns': '0313325580079600'},
            {'finished_monotonic_ns': '18446744073709551616'}, {'finished_monotonic_ns': '1'},
            {'finished_at_utc': '2026-10-23T09:00:00+00:00'},
            {'finished_at_utc': '2026-10-23T12:21:37'}, {'argv': ['different.exe']},
            {'machine_id': 'different-machine'}, {'schema': 'different-schema'},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                allocation.validate_recorded_public_wait({**final, **change}, first,
                    producer, string(fixture['machine_id']), 'run', 2)
        for key in final:
            missing = dict(final)
            missing.pop(key)
            with self.subTest(missing=key), self.assertRaises(ValueError):
                allocation.validate_recorded_public_wait(missing, first,
                    producer, string(fixture['machine_id']), 'run', 2)
        allocate = obj(leaves['allocate-a2026102308.STARTED.actual.json'])
        allocate_end = obj(leaves['allocate-a2026102308.EXIT.actual.json'])
        for bad in (None, True, '0001', '1', '18446744073709551616'):
            with self.subTest(deadline=bad), self.assertRaises(ValueError):
                allocation.validate_recorded_public_wait(
                    {**allocate_end, 'root_quit_deadline_monotonic_ns': bad},
                    {**allocate, 'root_quit_deadline_monotonic_ns': bad},
                    producer, string(fixture['machine_id']), 'allocate', 0)

    def test_recorded_producer_deadline_parameters_are_exact_and_receipt_bound(self) -> None:
        fixture = recorded_source_fixture()
        leaves = obj(fixture['leaves'])
        original = string(leaves['root_execute_r0042.operation.py'])
        machine = string(fixture['machine_id'])
        source = original.replace('11400*1000000000', '16800*1000000000').replace(
            '10800*1000000000', '16200*1000000000')
        producer = allocation.validate_recorded_public_producer(source.encode('utf-8'), machine)
        self.assertEqual(producer, {'custody_duration_ns': 16800000000000,
                                    'root_quit_duration_ns': 16200000000000})
        first = obj(leaves['allocate-a2026102308.STARTED.actual.json'])
        final = obj(leaves['allocate-a2026102308.EXIT.actual.json'])
        with self.assertRaisesRegex(ValueError, 'producer duration'):
            allocation.validate_recorded_public_wait(final, first, producer, machine, 'allocate', 0)
        for expression in ('str(t)', 'str(t+True*1000000000)', 'str(t+1.0*1000000000)',
                           'str(t-11400*1000000000)', 'str(t+0*1000000000)',
                           'str(t+11400*1000)', 'str(other+11400*1000000000)'):
            changed = original.replace('str(t+11400*1000000000)', expression)
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                allocation.validate_recorded_public_producer(changed.encode('utf-8'), machine)

    def test_recorded_producer_source_and_original_live_public_pids_are_checked(self) -> None:
        self.install_recorded_producer()
        for mode in ('run', 'allocate'):
            waited = obj(json.loads(Path(string(obj(self.refs[mode + '_wait'])['path'])).read_bytes()))
            self.live = {integer(waited['pid'])}
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, 'still present'):
                self.check()
        self.live = set()
        source = Path(string(obj(self.refs['public_command_producer'])['path']))
        source.write_bytes(source.read_bytes().replace(b'code = child.wait()', b'code = 0'))
        self.refs['public_command_producer'] = pin(source)
        self.write(self.close, self.bundle)
        with self.assertRaisesRegex(ValueError, 'original Popen/wait'):
            self.check()

    def test_recorded_whole_consumer_preserves_case_and_keeper_guards(self) -> None:
        self.install_recorded_producer()
        for mode, flag in (('run', '--case'), ('run', '--run-context'), ('allocate', '--keeper-output')):
            first_path = Path(string(obj(self.refs[mode + '_started'])['path']))
            final_path = Path(string(obj(self.refs[mode + '_wait'])['path']))
            first, final = obj(json.loads(first_path.read_bytes())), obj(json.loads(final_path.read_bytes()))
            argv = [string(arg) for arg in first['argv']] if isinstance(first['argv'], list) else []
            argv[argv.index(flag) + 1] = str(self.root / 'wrong')
            self.reseal(mode + '_started', {**first, 'argv': argv})
            self.reseal(mode + '_wait', {**final, 'argv': argv})
            with self.subTest(flag=flag), self.assertRaises((ValueError, FileNotFoundError)):
                self.check()
            self.reseal(mode + '_started', first)
            self.reseal(mode + '_wait', final)

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
