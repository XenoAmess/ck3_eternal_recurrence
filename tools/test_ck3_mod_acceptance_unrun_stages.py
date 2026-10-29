"""Persistent regression for the actual default CAS completion path."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import ast
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import argparse
import importlib
import psutil
from contextlib import AbstractContextManager, ExitStack, contextmanager
from collections.abc import Callable, Iterator, Mapping
from typing import Protocol, runtime_checkable
from types import SimpleNamespace
from unittest.mock import patch
from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue, json_object, strings_field, text_field
from ck3_mod_acceptance_unrun import _release_stages
import ck3_mod_acceptance_unrun as subject

def member(row: JsonObject, key: str) -> JsonObject:
    value=row.get(key)
    if not isinstance(value,dict):raise AssertionError('Fixture object required')
    return value

class ReleaseStagesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.keeper: JsonObject={'task_id':'idle','thread_exited':True,'last_sequence':10}
        self.cas: JsonObject={'ok':True,'event':{'task_id':'idle','resources':[],
            'sequence':11,'kind':'completed'},'task':{'task_id':'idle','state':'done',
            'resources':[],'last_sequence':11}}
        self.done=deepcopy(self.cas)
        member(self.done,'event')['sequence']=12
        member(self.done,'task')['last_sequence']=12

    def test_idle_actual_completed_then_administrative_completion(self) -> None:
        self.assertEqual(_release_stages(self.keeper,self.cas,self.done,{}, {},self.done,'idle'),
            'completed-then-admin-completed')

    def test_json_round_trip_preserves_release_contract(self) -> None:
        import json
        from ck3_mod_acceptance_background_types import json_object
        cas=json_object(json.loads(json.dumps(self.cas)))
        done=json_object(json.loads(json.dumps(self.done)))
        self.assertEqual(_release_stages(self.keeper,cas,done,{}, {},done,'idle'),
            'completed-then-admin-completed')

    def test_captured_original_release_keeps_earlier_task_and_exact_journal_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'release.json'
            cas = {**self.cas, 'schema': 'codex.task_bus.v1'}
            member(cas, 'event')['state'] = 'done'
            path.write_text(json.dumps(cas), encoding='utf-8')
            reference = subject._captured_release(path, member(cas, 'event'), 'idle', 11)
            self.assertEqual(Path(reference['path']).read_bytes(), path.read_bytes())
            self.assertEqual(_release_stages(self.keeper, cas, self.done, {}, {}, self.done, 'idle'),
                'completed-then-admin-completed')
            cases: tuple[tuple[str, str, JsonValue], ...] = (
                ('task', 'last_sequence', 12), ('task', 'last_sequence', True),
                ('event', 'sequence', 11.0), ('task', 'resources', ['ck3-screen:acquired']),
                ('event', 'summary', 'different event'))
            for section, field, bad in cases:
                changed = deepcopy(cas); member(changed, section)[field] = bad
                path.write_text(json.dumps(changed), encoding='utf-8')
                with self.subTest(section=section, field=field), self.assertRaises(ValueError):
                    subject._captured_release(path, member(cas, 'event'), 'idle', 11)

    def test_crossed_original_task_and_resources_are_rejected(self) -> None:
        cases: list[tuple[str,JsonValue]]=[('task_id','other'),('state','waiting'),
            ('resources',['ck3-screen:acquired']),('last_sequence',12)]
        for key,bad in cases:
            cas=deepcopy(self.cas);member(cas,'task')[key]=bad
            with self.assertRaises(ValueError):
                _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')

    def test_sequence_types_missing_fields_and_order_are_rejected(self) -> None:
        bad_values: list[JsonValue]=[True,11.0,None,[],{},10,13]
        for bad in bad_values:
            cas=deepcopy(self.cas);member(cas,'event')['sequence']=bad
            with self.assertRaises(ValueError):
                _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')
        cas=deepcopy(self.cas);del member(cas,'event')['sequence']
        with self.assertRaises(ValueError):
            _release_stages(self.keeper,cas,self.done,{}, {},self.done,'idle')

class ExternalExecCompletionTests(unittest.TestCase):
    """Portable synthetic contracts; never fabricate a historical wait receipt."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='unrun-external-exec-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.serial = 0
        self.machine = 'synthetic-test-machine'
        self.stamps = [datetime(2026, 10, 23, 15, 49, tzinfo=timezone.utc),
                       datetime(2026, 10, 23, 15, 59, tzinfo=timezone.utc)]
        self.command = ('D:/Python/python.exe -B D:/repo/tools/ck3_mod_acceptance.py allocate '
                        '--prepared-case D:/case/prepared-case.json --keeper-output D:/keeper '
                        '--products D:/repo/tools/products.json --product test-product')
        self.output = '{\r\n  "status": "ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN"\r\n}\r\n'
        self.stdout = self.write_raw('final-output.json', self.output.encode('utf-8'))
        self.receipt: dict[str, object] = {
            'schema': 'external-exec-completion-v1', 'machine_id': self.machine,
            'original_request': self.write_json('request.json', {'cmd': self.command,
                'shell': 'cmd.exe', 'workdir': 'D:/repo', 'max_output_tokens': 5000, 'yield_time_ms': 10000}),
            # Earlier tool output is permitted and explicitly not claimed to be
            # part of the exact final output block pinned by allocator_stdout.
            'initial_response': self.write_json('initial.json', {'chunk_id': 'initial-fixture',
                'wall_time_seconds': 10.0, 'session_id': 97171, 'original_token_count': 1, 'output': 'earlier READY\n'}),
            'completion_request': {'session_id': 97171, 'chars': '', 'max_output_tokens': 6000, 'yield_time_ms': 1000},
            'completion_response': self.write_json('final.json', {'chunk_id': 'final-fixture',
                'wall_time_seconds': 0.000024, 'exit_code': 0, 'original_token_count': 598, 'output': self.output}),
            'completion_observed_at_utc': '2026-10-23T16:00:20Z', 'exit_code': 0,
            'allocator_stdout': self.stdout,
        }

    def write_raw(self, name: str, raw: bytes) -> FilePin:
        path = self.root / name
        path.write_bytes(raw)
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def write_json(self, name: str, raw: object) -> FilePin:
        return self.write_raw(name, json.dumps(raw, ensure_ascii=False, indent=2).encode('utf-8'))

    def parse(self, raw: object | None = None, stdout: object | None = None) -> subject.ExternalAllocatorCompletion:
        return subject.parse_external_exec_completion(self.receipt if raw is None else raw, self.machine,
            self.stamps, self.stdout if stdout is None else stdout)

    def changed_original(self, key: str, field: str, value: object, *, remove: bool = False) -> dict[str, object]:
        changed = deepcopy(self.receipt)
        original = subject._pinned_object(changed[key], 'synthetic original')
        if remove:
            del original[field]
        else:
            original[field] = value
        self.serial += 1
        changed[key] = self.write_json(f'changed-{self.serial}.json', original)
        return changed

    def test_final_tool_output_and_cmd_fact_survive_json_round_trip(self) -> None:
        raw: object = json.loads(json.dumps(self.receipt))
        completion = self.parse(raw)
        self.assertEqual(completion.command_text, self.command)
        self.assertEqual(completion.shell, 'cmd.exe')
        self.assertEqual(completion.workdir, 'D:/repo')
        self.assertEqual(completion.session_id, 97171)
        self.assertIs(type(completion.exit_code), int)
        self.assertEqual(completion.exit_code, 0)
        self.assertEqual(completion.argv[2:4], ('D:/repo/tools/ck3_mod_acceptance.py', 'allocate'))
        self.assertEqual(Path(self.stdout['path']).read_bytes(), self.output.encode('utf-8'))
        self.assertNotIn('earlier READY', self.output)

    def test_session_exit_and_count_fields_reject_bool_and_equal_floats(self) -> None:
        for invalid in (False, 0.0):
            with self.subTest(exit_code=invalid), self.assertRaises(ValueError):
                self.parse({**self.receipt, 'exit_code': invalid})
            for field in ('exit_code', 'original_token_count'):
                with self.subTest(final_field=field, value=invalid), self.assertRaises(ValueError):
                    self.parse(self.changed_original('completion_response', field, invalid))
        for invalid in (True, 97171.0, 9007199254740992):
            with self.subTest(initial_session=invalid), self.assertRaises(ValueError):
                self.parse(self.changed_original('initial_response', 'session_id', invalid))
            request = subject._object(self.receipt['completion_request'], 'request')
            request['session_id'] = invalid
            with self.subTest(completion_session=invalid), self.assertRaises(ValueError):
                self.parse({**self.receipt, 'completion_request': request})
        for invalid in (True, float(self.stdout['bytes'])):
            wrong = {**self.stdout, 'bytes': invalid}
            with self.subTest(pin_bytes=invalid), self.assertRaises(ValueError):
                self.parse({**self.receipt, 'allocator_stdout': wrong}, wrong)

    def test_original_request_and_completion_association_are_exact(self) -> None:
        cases: tuple[tuple[str, str, object], ...] = (
            ('original_request', 'shell', False), ('original_request', 'shell', 'other-shell'),
            ('original_request', 'workdir', 'relative/repo'), ('initial_response', 'session_id', 97172),
            ('completion_response', 'exit_code', 1), ('completion_response', 'session_id', 97171),
            ('completion_response', 'wall_time_seconds', True), ('completion_response', 'wall_time_seconds', float('inf')),
        )
        for key, field, value in cases:
            with self.subTest(key=key, field=field, value=value), self.assertRaises(ValueError):
                self.parse(self.changed_original(key, field, value))
        request = subject._object(self.receipt['completion_request'], 'request')
        request['chars'] = 'q'
        with self.assertRaises(ValueError):
            self.parse({**self.receipt, 'completion_request': request})
        for field in ('schema', 'original_request', 'completion_response', 'completion_observed_at_utc'):
            changed = deepcopy(self.receipt)
            del changed[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.parse(changed)
        with self.assertRaises(ValueError):
            self.parse({**self.receipt, 'original_host_exit0': True})

    def test_raw_final_output_cannot_be_replaced_by_lf_or_truncated_prefix(self) -> None:
        projection = self.write_raw('lf-display.json', self.output.replace('\r\n', '\n').encode('utf-8'))
        with self.assertRaisesRegex(ValueError, 'final tool output bytes differ'):
            self.parse({**self.receipt, 'allocator_stdout': projection}, projection)
        with self.assertRaisesRegex(ValueError, 'stdout pin differs'):
            self.parse({**self.receipt, 'allocator_stdout': projection})
        truncated = self.output[:-3]
        raw = self.write_raw('truncated.json', truncated.encode('utf-8'))
        changed = self.changed_original('completion_response', 'output', truncated)
        changed['allocator_stdout'] = raw
        with self.assertRaises(ValueError):
            self.parse(changed, raw)
        with self.assertRaises(ValueError):
            self.parse(self.changed_original('completion_response', 'exit_code', None, remove=True))

    def test_pins_and_completion_observation_remain_bound_to_originals(self) -> None:
        for invalid in ('2026-10-23T15:58:00Z', '2026-10-23T16:00:20', None):
            with self.subTest(observed_at=invalid), self.assertRaises(ValueError):
                self.parse({**self.receipt, 'completion_observed_at_utc': invalid})
        with self.assertRaises(ValueError):
            self.parse({**self.receipt, 'machine_id': 'different-machine'})
        final = subject._evidence_pin(self.receipt['completion_response'], 'final')
        Path(final['path']).write_bytes(b'changed original')
        with self.assertRaises(ValueError):
            self.parse()

    def test_shell_operators_expansion_and_nonliteral_quoting_are_rejected(self) -> None:
        for suffix in (' & echo other', ' | other', ' > output', ' %EXPAND%', ' !EXPAND!', ' ^x', '\nother', '"concat"'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.parse(self.changed_original('original_request', 'cmd', self.command + suffix))
        self.assertEqual(subject._cmd_allocator_argv('"D:/Program Files/Python/python.exe" D:/repo/tools/ck3_mod_acceptance.py allocate')[0],
                         'D:/Program Files/Python/python.exe')

    def test_public_allocator_consumer_accepts_external_form_and_rejects_mixed_forms(self) -> None:
        reference = self.write_json('external-completion.json', self.receipt)
        bundle = {'allocator_external_exec': reference, 'allocator_stdout': self.stdout}
        self.assertEqual(subject._allocator_argv(bundle, self.machine, self.stamps), self.command.split())
        for key in ('allocator_result', 'allocator_intent', 'allocator_process', 'allocator_exit'):
            with self.subTest(mixed=key), self.assertRaisesRegex(ValueError, 'One complete original'):
                subject._allocator_argv({**bundle, key: reference}, self.machine, self.stamps)
        changed = self.changed_original('original_request', 'cmd', self.command.replace(' allocate ', ' run '))
        changed_reference = self.write_json('wrong-operation.json', changed)
        with self.assertRaisesRegex(ValueError, 'allocator command differs'):
            subject._allocator_argv({'allocator_external_exec': changed_reference, 'allocator_stdout': self.stdout}, self.machine, self.stamps)


class RootAllocatorTripletTests(unittest.TestCase):
    """Execute the Root recorder shape against an owned, no-Game CLI stub.

    Each positive triplet comes from a real child PID/birth and original wait.
    Negative fixtures mutate only these temporary originals, never scene files.
    """

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='unrun-root-recorder-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'repo'
        (self.repo / 'tools').mkdir(parents=True)
        self.output = self.root / 'work-package/root-execution-test'
        self.output.mkdir(parents=True)
        self.machine = 'owned-no-game-fixture'
        stub = self.repo / 'tools/ck3_mod_acceptance.py'
        stub.write_text("from pathlib import Path\nfrom datetime import datetime,timezone\nimport json,time\n"
            "assert __import__('sys').argv[1]=='allocate'\n"
            "ready=datetime.now(timezone.utc).isoformat()\ntime.sleep(.02)\n"
            "Path('../work-package/keeper-stamps.json').write_text(json.dumps([ready,datetime.now(timezone.utc).isoformat()]),encoding='utf-8')\n",
            encoding='utf-8')
        self.producer = self.root / 'root-public.once.py'
        source = ("from pathlib import Path\nfrom datetime import datetime,timezone\n"
            "import json,subprocess,sys,time,psutil\nREPO=Path(" + repr(str(self.repo)) + ")\n"
            "C=REPO.parent/'work-package'\nOUT=C/'root-execution-test'\nPYTHON=" + repr(sys.executable) + "\n"
            "MACHINE=" + repr(self.machine) + "\n") + r'''
def stamp():
    return datetime.now(timezone.utc).isoformat()
def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
mode = sys.argv[1]
argv = [PYTHON, '-B', '-X', 'utf8', 'tools/ck3_mod_acceptance.py', mode]
prefix = {'run': 'PUBLIC-RUN', 'allocate': 'ALLOCATE', 'preflight': 'PREFLIGHT'}[mode]
write_new(OUT / (prefix + '.intent.actual.json'), {'machine_id': MACHINE, 'argv': argv, 'started_at_utc': stamp()})
started = time.monotonic()
with (OUT / (prefix + '.stdout.log')).open('xb') as out, (OUT / (prefix + '.stderr.log')).open('xb') as err:
    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)
    write_new(OUT / (prefix + '.started.actual.json'), {'machine_id': MACHINE,
        'pid': child.pid, 'process_create_time_seconds': str(psutil.Process(child.pid).create_time()),
        'started_at_utc': stamp(), 'original_wait_pending': True})
    code = child.wait()
write_new(OUT / (prefix + '.original-wait.actual.json'), {'machine_id': MACHINE,
    'original_wait_returncode': code, 'elapsed_seconds': time.monotonic() - started, 'finished_at_utc': stamp()})
raise SystemExit(code)
'''
        self.source_raw = source.encode('utf-8')
        self.producer.write_bytes(self.source_raw)
        subprocess.run([sys.executable, '-B', '-X', 'utf8', str(self.producer), 'allocate'],
            cwd=self.repo, capture_output=True, check=True)
        self.paths = {'allocator_intent': self.output / 'ALLOCATE.intent.actual.json',
            'allocator_process': self.output / 'ALLOCATE.started.actual.json',
            'allocator_exit': self.output / 'ALLOCATE.original-wait.actual.json'}
        self.raw = {key: path.read_bytes() for key, path in self.paths.items()}
        self.originals = {key: json_object(json.loads(raw)) for key, raw in self.raw.items()}
        self.stamps = [datetime.fromisoformat(value) for value in
            json.loads((self.root / 'work-package/keeper-stamps.json').read_bytes())]
        self.bundle: dict[str, object] = {key: self.reference(path) for key, path in self.paths.items()}
        self.bundle['allocator_command'] = self.reference(self.producer)

    @staticmethod
    def reference(path: Path) -> FilePin:
        raw = path.read_bytes()
        return FilePin(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def restore(self) -> None:
        for key, path in self.paths.items():
            path.write_bytes(self.raw[key])
        self.producer.write_bytes(self.source_raw)

    def changed(self, key: str, field: str, value: JsonValue, *, remove: bool = False) -> dict[str, object]:
        self.restore()
        row = deepcopy(self.originals[key])
        if remove:
            del row[field]
        else:
            row[field] = value
        path = self.paths[key]
        path.write_text(json.dumps(row, allow_nan=True), encoding='utf-8')
        return {**self.bundle, key: self.reference(path)}

    def parse(self, bundle: Mapping[str, object] | None = None,
            stamps: list[datetime] | None = None) -> list[str]:
        return subject._allocator_argv(self.bundle if bundle is None else bundle,
            self.machine, self.stamps if stamps is None else stamps)

    def test_actual_child_original_wait_and_json_round_trip(self) -> None:
        value = json_object(json.loads(json.dumps(self.bundle)))
        self.assertEqual(self.parse(value), self.originals['allocator_intent']['argv'])
        process = self.originals['allocator_process']
        parsed = subject._root_allocator_triplet(self.originals['allocator_intent'], process,
            self.originals['allocator_exit'], command=self.bundle['allocator_command'],
            paths=(self.paths['allocator_intent'], self.paths['allocator_process'], self.paths['allocator_exit']),
            machine=self.machine, keeper_stamps=self.stamps)
        self.assertGreater(parsed.pid, 0)
        self.assertEqual(parsed.process_create_time_seconds, Decimal(str(process['process_create_time_seconds'])))
        self.assertNotIn('pid', self.originals['allocator_exit'])
        self.assertNotIn('argv', process)

    def test_exact_twelve_fields_and_missing_command_are_required(self) -> None:
        for key, row in self.originals.items():
            for field in row:
                with self.subTest(key=key, missing=field), self.assertRaises(ValueError):
                    self.parse(self.changed(key, field, None, remove=True))
            with self.subTest(key=key, extra=True), self.assertRaises(ValueError):
                self.parse(self.changed(key, 'projection_alias', True))
        self.restore()
        missing = dict(self.bundle)
        del missing['allocator_command']
        with self.assertRaises(ValueError):
            self.parse(missing)

    def test_exact_pid_wait_pending_birth_and_finite_elapsed_types(self) -> None:
        cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('allocator_process', 'pid', True), ('allocator_process', 'pid', 1.0),
            ('allocator_process', 'pid', 0), ('allocator_process', 'pid', 9007199254740992),
            ('allocator_process', 'original_wait_pending', 1),
            ('allocator_process', 'original_wait_pending', False),
            ('allocator_exit', 'original_wait_returncode', False),
            ('allocator_exit', 'original_wait_returncode', 0.0),
            ('allocator_exit', 'original_wait_returncode', 2),
            ('allocator_exit', 'elapsed_seconds', True), ('allocator_exit', 'elapsed_seconds', -1),
            ('allocator_exit', 'elapsed_seconds', float('nan')), ('allocator_exit', 'elapsed_seconds', float('inf')),
            ('allocator_process', 'process_create_time_seconds', 1.0),
            ('allocator_process', 'process_create_time_seconds', '01792982215.0'),
            ('allocator_process', 'process_create_time_seconds', 'NaN'),
        )
        for key, field, bad in cases:
            with self.subTest(key=key, field=field, value=bad), self.assertRaises(ValueError):
                self.parse(self.changed(key, field, bad))

    def test_machine_timezone_and_intent_birth_keeper_wait_order(self) -> None:
        for key in self.paths:
            with self.subTest(machine=key), self.assertRaises(ValueError):
                self.parse(self.changed(key, 'machine_id', 'different-machine'))
        cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('allocator_intent', 'started_at_utc', self.stamps[-1].isoformat()),
            ('allocator_process', 'started_at_utc', '2000-01-01T00:00:00+00:00'),
            ('allocator_exit', 'finished_at_utc', self.stamps[0].isoformat()),
            ('allocator_intent', 'started_at_utc', '2026-01-01T00:00:00'),
            ('allocator_process', 'started_at_utc', '2026-01-01T00:00:00+01:00'),
            ('allocator_process', 'process_create_time_seconds', '1.0'),
        )
        for key, field, bad in cases:
            with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                self.parse(self.changed(key, field, bad))
        self.restore()
        with self.assertRaises(ValueError):
            self.parse(stamps=list(reversed(self.stamps)))
        with self.assertRaises(ValueError):
            self.parse(stamps=[])

    def test_different_producer_child_writer_argv_and_wait_cannot_grant_identity(self) -> None:
        source = self.source_raw.decode('utf-8')
        replacements = (
            ('code = child.wait()', 'code = 0'),
            ('subprocess.Popen(argv,', 'subprocess.Popen(other_argv,'),
            ("'pid': child.pid", "'pid': 123"),
            ('psutil.Process(child.pid)', 'psutil.Process(123)'),
            ("'original_wait_returncode': code", "'original_wait_returncode': 0"),
            ("path.open('x'", "path.open('w'"),
            ("OUT=C/'root-execution-test'", "OUT=C/'other-output'"),
            ('import json,subprocess,sys,time,psutil', 'import json,subprocess,sys,time,psutil\nsubprocess=object()'),
            ('import json,subprocess,sys,time,psutil', 'import json,subprocess,sys,time,psutil\nsubprocess.Popen=object()'),
            ('import json,subprocess,sys,time,psutil', 'import json,subprocess,sys,time,psutil\nalias=subprocess'),
            ('import json,subprocess,sys,time,psutil', 'import json,sys,time,psutil\nimport pathlib as subprocess'),
            ('import json,subprocess,sys,time,psutil', "import json,subprocess,sys,time,psutil\nglobals()['subprocess']=object()"),
        )
        for old, new in replacements:
            self.restore()
            self.assertIn(old, source)
            self.producer.write_text(source.replace(old, new), encoding='utf-8')
            bundle = {**self.bundle, 'allocator_command': self.reference(self.producer)}
            with self.subTest(producer_change=old), self.assertRaises(ValueError):
                self.parse(bundle)
        self.restore()
        self.producer.write_bytes(self.source_raw + b'\n# changed after original pin\n')
        with self.assertRaises(ValueError):
            self.parse()

    def test_old_triplet_remains_distinct_and_root_files_cannot_be_crossed(self) -> None:
        intent, process, waited = (self.originals[key] for key in
            ('allocator_intent', 'allocator_process', 'allocator_exit'))
        argv = intent['argv']
        old: dict[str, JsonObject] = {
            'allocator_intent': {'machine_id': self.machine, 'stage': 'allocate', 'argv': argv,
                'at_utc': intent['started_at_utc']},
            'allocator_process': {'machine_id': self.machine, 'pid': process['pid'], 'argv': argv,
                'create_time': float(str(process['process_create_time_seconds']))},
            'allocator_exit': {'machine_id': self.machine, 'pid': process['pid'],
                'actual_original_popen_wait': True, 'returncode': 0, 'completed_at_utc': waited['finished_at_utc']}}
        legacy: dict[str, object] = {}
        for key, row in old.items():
            path = self.root / (key + '.json')
            path.write_text(json.dumps(row), encoding='utf-8')
            legacy[key] = self.reference(path)
        self.assertEqual(self.parse(legacy), argv)
        other = self.output / 'OTHER.original-wait.actual.json'
        other.write_bytes(self.raw['allocator_exit'])
        with self.assertRaises(ValueError):
            self.parse({**self.bundle, 'allocator_exit': self.reference(other)})

    def prelaunch_fixture(self, *, observed_root: bool = False, phase_guards: bool = False,
            intent_root: bool = False, phase_count: int = 3,
            before_armed: bool = False) -> tuple[dict[str, object], Path, Path, list[datetime]]:
        """Run a real recorder, threaded Popen waits and mechanical STOP branch."""
        if before_armed and not (observed_root and phase_guards and intent_root):
            raise ValueError('Before-ARMED fixture requires the actual intent-bound phase contract')
        output=self.root/'work-package/root-prelaunch-test';output.mkdir()
        keeper=self.root/'work-package/keeper';keeper.mkdir()
        live=self.root/(self.machine+'--living-artifacts--R0001');live.mkdir();(live/'controls').mkdir()
        prepared=self.root/'prelaunch-prepared.json';prepared.write_text('{}',encoding='utf8')
        if phase_guards:
            contract=self.root/'prelaunch-contract.json'
            contract.write_text(json.dumps({'gui_phases':[{'id':phase} for phase in
                ('fixture-phase', *(f'fixture-phase-{index}' for index in range(1, phase_count)))]}),encoding='utf8')
            prepared.write_text(json.dumps({'contract':self.reference(contract)}),encoding='utf8')
        products=self.root/'prelaunch-products.json';products.write_text(json.dumps({'products':{'living-artifacts':{'external_mod':False}}}),encoding='utf8')
        state=self.root/'prelaunch-state';ids=self.root/'prelaunch-ids'
        counter=ids/self.machine/'living-artifacts/counter.json';counter.parent.mkdir(parents=True)
        counter.write_text(json.dumps({'machine_id':self.machine,'mod_key':'living-artifacts','last_sequence':1}),encoding='utf8')
        freeze: JsonObject={'run_id':live.name,'screen_task':'fixture-prelaunch-task','state_dir':str(state),'mod_key':'living-artifacts',
            'source_root':str(self.repo),'lease_anchor':str(self.root),'identity_allocation':{'machine_id':self.machine,'state_root':str(ids)},
            'files':{str(products.resolve()):json_object(self.reference(products))}}
        if observed_root:
            manifest=self.root/'original-runtime-manifest.json'
            manifest.write_text(json.dumps({'machine_id':self.machine,'source_commit':'a'*40}),encoding='utf8')
            freeze['runtime_manifest']=json_object(self.reference(manifest))
        frozen=live/'frozen-argv.json';frozen.write_text(json.dumps(freeze),encoding='utf8')
        ready=live/'ready-context.json';ready_value={'run_id':live.name,'run_dir':str(live),'keeper_root':str(keeper),
            'frozen_argv':self.reference(frozen),'prepared_case':self.reference(prepared),'product':'living-artifacts'}
        ready.write_text(json.dumps(ready_value),encoding='utf8');(live/'allocated-context.json').write_text(json.dumps(ready_value),encoding='utf8')
        guard=self.root/'fixture-guard.py'
        guard.write_text(r'''
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,sys,time
if os.name != 'nt':signal.signal(signal.SIGTERM,lambda *_:sys.exit(1))
output,live=Path(sys.argv[-1]).parent,Path(sys.argv[sys.argv.index('--live')+1])
def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
row=dict(schema='root-external-deadline-guard-armed-v1',machine_id='owned-no-game-fixture',run_id=live.name,
    live=str(live),ready_context=pin(live/'ready-context.json'),pid=os.getpid(),process_creation_filetime_100ns='1',
    birth_source='GetProcessTimes(GetCurrentProcess)',guard=pin(Path(__file__)),armed_at_utc=datetime.now(timezone.utc).isoformat(),
    phase='fixture-phase',state='WAITING_FOR_ACTUAL_FROZEN_AND_PHASE',wait_awaiting_seconds=5400,reserve_seconds=1200,
    game_or_queue_action_sent=False,deadline_bound=False)
with (output/'DEADLINE-GUARD.ARMED.actual.json').open('x',encoding='utf8') as f:json.dump(row,f)
while True:time.sleep(.01)
''',encoding='utf8')
        (self.repo/'tools/ck3_mod_acceptance.py').write_text(
            "from pathlib import Path\nfrom datetime import datetime,timezone\nimport json,time\n"
            f"keeper=Path({str(keeper)!r})\n"
            f"live=Path({str(live)!r})\n"
            "keeper.joinpath('ready.json').write_text(json.dumps({'at_utc':datetime.now(timezone.utc).isoformat(),'lease':{'task_id':'fixture-prelaunch-task','sequence':10}}),encoding='utf8')\n"
            "while not keeper.joinpath('STOP').exists():time.sleep(.01)\n"
            "report={'at_utc':datetime.now(timezone.utc).isoformat(),'task_id':'fixture-prelaunch-task','last_sequence':10,'thread_exited':True,'failure':None,'entry_error':None,'game_actions':False}\n"
            "keeper.joinpath('report.json').write_text(json.dumps(report),encoding='utf8')\n"
            "live.joinpath('keeper-actual-parent-exit.json').write_text(json.dumps({'run_id':live.name,'keeper_actual_exit_code':0,'keeper_report':report}),encoding='utf8')\n",encoding='utf8')
        recorder=self.root/'prelaunch-public.py'
        recorder_source=self.source_raw.decode('utf8').replace("OUT=C/'root-execution-test'","OUT=C/'root-prelaunch-test'")
        recorder_source=recorder_source.replace("mode]\n", "mode]\nargv += "+repr(['--prepared-case',str(prepared),'--keeper-output',str(keeper),'--products',str(products),'--product','living-artifacts'])+"\n",1)
        recorder.write_text(recorder_source,encoding='utf8')
        source=self.root/'orchestrate.py'
        source.write_text(
            "from pathlib import Path\nfrom datetime import datetime, timezone\nimport json,subprocess,sys,threading,time\n"
            f"REPO=Path({str(self.repo)!r})\nOUT=Path({str(output)!r})\nPUBLIC=Path({str(recorder)!r})\n"
            f"MACHINE={self.machine!r}\nkeeper=Path({str(keeper)!r})\nlive=Path({str(live)!r})\nGUARD=Path({str(guard)!r})\n"
            f"GUARD_PYTHON={str(Path(sys.base_prefix)/('python.exe' if sys.platform=='win32' else 'bin/python3'))!r}\n"+r'''
def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump({'machine_id': MACHINE, 'at': datetime.now(timezone.utc).isoformat(), **value}, stream, indent=2)
        stream.write('\n')
def start(label, argv):
    out = (OUT / (label + '.stdout.log')).open('xb')
    err = (OUT / (label + '.stderr.log')).open('xb')
    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)
    put(OUT / (label + '.started.actual.json'), {'argv': argv, 'pid': child.pid, 'original_wait_pending': True})
    def wait():
        code = child.wait()
        out.close()
        err.close()
        put(OUT / (label + '.original-wait.actual.json'), {'original_wait_returncode': code})
    thread = threading.Thread(target=wait, daemon=False)
    thread.start()
    return child, thread
allocate, allocate_thread=start('ORCHESTRATOR.ALLOCATE',[sys.executable,'-B','-X','utf8',str(PUBLIC),'allocate'])
guard = guard_thread = None
public_started = False
try:
    while not (keeper/'ready.json').exists():time.sleep(.01)
    guard,guard_thread=start('DEADLINE-GUARD',[GUARD_PYTHON,'-B','-X','utf8',str(GUARD),'--live',str(live),
        '--ready-context',str(live/'ready-context.json'),'--run-id',live.name,'--phase','fixture-phase','--reserve-seconds','1200',
        '--wait-awaiting-seconds','5400','--armed',str(OUT/'DEADLINE-GUARD.ARMED.actual.json'),'--output',str(OUT/'DEADLINE-GUARD.actual.json')])
    while not (OUT/'DEADLINE-GUARD.ARMED.actual.json').exists():time.sleep(.01)
    raise KeyError('revision')
    public_started = True
except BaseException as error:
    put(OUT / 'ORCHESTRATOR.failure.actual.json', {'error': repr(error),
        'public_started': public_started, 'business_pass': False})
    print('ORCHESTRATOR_FAILURE_PRESERVED', repr(error), flush=True)
    if not public_started:
        if keeper.is_dir() and not (keeper / 'STOP').exists():
            (keeper / 'STOP').write_text('Root mechanical prelaunch refused before public run\n', encoding='utf-8')
        if guard is not None and guard.poll() is None:
            put(OUT / 'DEADLINE-GUARD.CANCEL.actual.json', {'pid': guard.pid,
                'reason': 'Mechanical prelaunch refused before public run; cancel retained Root helper'})
            guard.terminate()
finally:
    print('PUBLIC_STAGE_ENDED_KEEPER_REQUIRES_ROOT_CLOSURE', flush=True)
    if guard_thread is not None:
        guard_thread.join()
    allocate_thread.join()
    print('ALL_ORIGINAL_OPERATOR_CHILD_WAITS_CONSUMED', flush=True)
''',encoding='utf8')
        root_refs: dict[str, FilePin] = {}
        if observed_root:
            # A real intermediate process makes wrapper != armed deterministic.
            # Native birth1 is explicitly fixture data, not a live OS claim.
            raw = guard.read_text(encoding='utf8')
            raw = raw.replace("output,live=", "import subprocess\nif '--fixture-worker' not in sys.argv:\n    child=subprocess.Popen([sys.executable,*sys.argv,'--fixture-worker'])\n    sys.exit(child.wait())\nsys.argv.remove('--fixture-worker')\noutput,live=")
            raw = raw.replace('while True:time.sleep(.01)',
                f"while not Path({str(keeper/'STOP')!r}).exists():time.sleep(.01)\nsys.exit(1)")
            if phase_guards:
                raw = raw.replace("phase='fixture-phase'", "phase=sys.argv[sys.argv.index('--phase')+1]")
                raw = raw.replace("(output/'DEADLINE-GUARD.ARMED.actual.json')", "Path(sys.argv[sys.argv.index('--armed')+1])")
            if before_armed:
                raw = "import time\ntime.sleep(.1)\nraise ValueError('Fixture refused before ARMED publication')\n"
            guard.write_text(raw, encoding='utf8')
            raw = source.read_text(encoding='utf8')
            raw = raw.replace("'at': datetime.now", "'observed_at_utc': datetime.now")
            raw = raw.replace("'original_wait_pending': True}",
                "'process_creation_filetime_100ns':'1','initial_exit_code':259,'original_wait_pending': True}")
            raw = raw.replace("{'original_wait_returncode': code}",
                "{'original_wait_returncode': code,'argv':argv,'pid':child.pid}")
            raw = raw.replace("'public_started': public_started, 'business_pass': False}",
                "'public_started': public_started,'normal_closed':False,'business_pass':False,'no_automatic_replay':True,'no_manual_case_client_created':True}")
            raw = raw.replace('Root mechanical prelaunch refused before public run\\n',
                'Root mechanical prelaunch refused before public run.\\n')
            raw = raw.replace('Mechanical prelaunch refused before public run; cancel retained Root helper',
                'Actual mechanical prelaunch failure; no Game action')
            raw = raw.replace('            guard.terminate()\nfinally:', '            guard.terminate()\n    raise\nfinally:')
            if before_armed:
                raw = raw.replace('    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)',
                    "    if label == 'DEADLINE-GUARD':\n        put(OUT/(label+'.intent.actual.json'),{'argv':argv,'source_commit':'a'*40})\n"
                    '    child = subprocess.Popen(argv, cwd=REPO, stdout=out, stderr=err)')
                raw = raw.replace("    while not (OUT/'DEADLINE-GUARD.ARMED.actual.json').exists():time.sleep(.01)",
                    "    while not (OUT/'DEADLINE-GUARD.ARMED.actual.json').exists():\n"
                    "        if guard.poll() is not None:\n            guard_thread.join()\n"
                    "            raise ValueError('Original producer exited before publication')\n        time.sleep(.01)")
            if phase_guards and not before_armed:
                raw = raw.replace('public_started = False', 'extra_guards = []\npublic_started = False')
                raw = raw.replace("    raise KeyError('revision')", r'''
    for index in (1,2):
        label='DEADLINE-GUARD-'+str(index)
        argv=[GUARD_PYTHON,'-B','-X','utf8',str(GUARD),'--live',str(live),
            '--ready-context',str(live/'ready-context.json'),'--run-id',live.name,'--phase','fixture-phase-'+str(index),
            '--reserve-seconds','1200','--wait-awaiting-seconds','5400',
            '--armed',str(OUT/(label+'.ARMED.actual.json')),'--output',str(OUT/(label+'.actual.json'))]
        put(OUT/(label+'.intent.actual.json'),{'argv':argv,'source_commit':'a'*40})
        pair=start(label,argv);extra_guards.append((label,pair))
        while not (OUT/(label+'.ARMED.actual.json')).exists():time.sleep(.01)
    raise KeyError('revision')''')
                raw = raw.replace('    raise\nfinally:', r'''
        for label,pair in extra_guards:
            if pair[0].poll() is None:
                put(OUT/(label+'.CANCEL.actual.json'),{'pid':pair[0].pid,
                    'reason':'Actual mechanical prelaunch failure; no Game action'})
                pair[0].terminate()
    raise
finally:''')
                raw = raw.replace('    allocate_thread.join()',
                    '    for label,pair in extra_guards:pair[1].join()\n    allocate_thread.join()')
            raw = raw.replace('for index in (1,2):', f'for index in range(1,{phase_count}):')
            if intent_root:
                raw = raw.replace("str(PUBLIC),'allocate'])", "str(PUBLIC),'allocate','--binding-sha256',sys.argv[sys.argv.index('--input-binding-sha256')+1]])")
            source.write_text(raw, encoding='utf8')
            argv = [sys.executable,'-B','-X','utf8',str(source),'--mode','launch','--execute-root-reviewed-launch',
                '--repo-root',str(self.repo),
                '--out',str(output),'--keeper-output',str(keeper),'--public-recorder',str(recorder),
                '--scene-root',str(self.root/'work-package'),'--deadline-guard',str(guard)]
            started = json_object({'machine_id':self.machine,'source_commit':'a'*40,'argv':argv,
                'started_at_utc':datetime.now(timezone.utc).isoformat()})
            if intent_root:
                binding_path=self.root/'root-launch-binding.json'
                guard_interpreter = Path(sys.base_prefix)/('python.exe' if sys.platform == 'win32' else 'bin/python3')
                interpreter_pin = self.reference(guard_interpreter)
                binding_path.write_text(json.dumps({'machine_id':self.machine,'source_commit':'a'*40,
                    'orchestrator':self.reference(source),'public_recorder':self.reference(recorder),
                    **({'deadline_guard':self.reference(guard), 'guard_interpreter':interpreter_pin} if before_armed else {})}),encoding='utf8')
                argv += ['--input-binding',str(binding_path),'--input-binding-sha256',self.reference(binding_path)['sha256']]
                if before_armed:
                    argv += ['--guard-interpreter',str(guard_interpreter),
                        '--guard-interpreter-sha256',interpreter_pin['sha256']]
                intent_path=self.root/'ROOT.intent.actual.json'
                intent_path.write_text(json.dumps({'machine_id':self.machine,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                    'argv':argv,'binding':self.reference(binding_path),'ambient_pythonpath_removed':True,'no_manual_sdk_import_path':True}),encoding='utf8')
            child_process = subprocess.Popen(argv,cwd=self.repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            started.update(pid=child_process.pid,process_birth_seconds=str(psutil.Process(child_process.pid).create_time()))
            if phase_guards:
                started = json_object({'machine_id':self.machine,'source_commit':'a'*40,'argv':argv,
                    'pid':child_process.pid,'process_create_time_seconds':str(psutil.Process(child_process.pid).create_time()),
                    'observed_at_utc':datetime.now(timezone.utc).isoformat(),
                    'ambient_pythonpath_removed':True,'original_wait_pending':True})
            if intent_root:
                del started['source_commit'];del started['ambient_pythonpath_removed']
            start_path=self.root/'root-started.json';start_path.write_text(json.dumps(started),encoding='utf8')
            captured_out,captured_err=child_process.communicate(timeout=20)
            self.assertEqual(child_process.returncode,1,(captured_out,captured_err))
            waited={**started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'original_wait_returncode':child_process.returncode}
            if phase_guards:
                finished=datetime.now(timezone.utc)
                waited={'machine_id':self.machine,'observed_at_utc':finished.isoformat(),
                    'original_wait_returncode':child_process.returncode,
                    'elapsed_seconds':finished.timestamp()-float(str(started['process_create_time_seconds']))}
            if intent_root:
                waited.update(argv=argv,pid=child_process.pid)
                start_path.unlink();start_path=self.root/'ROOT.started.actual.json'
                start_path.write_text(json.dumps(started),encoding='utf8')
            wait_path=self.root/'root-wait.json';wait_path.write_text(json.dumps(waited),encoding='utf8')
            if intent_root:
                wait_path.rename(self.root/'ROOT.original-wait.actual.json');wait_path=self.root/'ROOT.original-wait.actual.json'
            root_refs={'prelaunch_orchestrator_started':self.reference(start_path),'prelaunch_orchestrator_wait':self.reference(wait_path)}
            if intent_root:
                root_refs['prelaunch_orchestrator_intent']=self.reference(intent_path)
            if not before_armed:
                armed=json.loads((output/'DEADLINE-GUARD.ARMED.actual.json').read_bytes())
                try:psutil.Process(armed['pid']).wait(timeout=5)
                except psutil.NoSuchProcess:pass
        else:
            child=subprocess.run([sys.executable,'-B','-X','utf8',str(source)],cwd=self.repo,capture_output=True,timeout=20)
            self.assertEqual(child.returncode,0,child.stderr)
        bundle: dict[str, object]={'allocator_intent':self.reference(output/'ALLOCATE.intent.actual.json'),
            'allocator_process':self.reference(output/'ALLOCATE.started.actual.json'),
            'allocator_exit':self.reference(output/'ALLOCATE.original-wait.actual.json'),
            'allocator_command':self.reference(recorder),'prelaunch_orchestrator_source':self.reference(source),
            'ready':self.reference(ready),'keeper_STOP':self.reference(keeper/'STOP'),**root_refs}
        guard_paths = {'prelaunch_failure':'ORCHESTRATOR.failure.actual.json',
            'prelaunch_guard_started':'DEADLINE-GUARD.started.actual.json','prelaunch_guard_wait':'DEADLINE-GUARD.original-wait.actual.json',
            'prelaunch_allocator_wait':'ORCHESTRATOR.ALLOCATE.original-wait.actual.json'}
        guard_paths.update({'prelaunch_guard_intent':'DEADLINE-GUARD.intent.actual.json',
            'prelaunch_guard_stdout':'DEADLINE-GUARD.stdout.log','prelaunch_guard_stderr':'DEADLINE-GUARD.stderr.log'} if before_armed else
            {'prelaunch_guard_armed':'DEADLINE-GUARD.ARMED.actual.json','prelaunch_guard_cancel':'DEADLINE-GUARD.CANCEL.actual.json'})
        for key,name in guard_paths.items():bundle[key]=self.reference(output/name)
        if before_armed:
            bundle['prelaunch_guard_state']='failed-before-armed'
        if phase_guards and not before_armed:
            bundle['prelaunch_phase_guards']=subject._phase_guard_evidence(output)
        cas={'schema':'codex.task_bus.v1','ok':True,'task':{'task_id':'fixture-prelaunch-task','state':'waiting','resources':[],'last_sequence':11},
            'event':{'task_id':'fixture-prelaunch-task','kind':'status','resources':[],'sequence':11}}
        done={'schema':'codex.task_bus.v1','ok':True,'task':{'task_id':'fixture-prelaunch-task','state':'done','resources':[],'last_sequence':12},
            'event':{'task_id':'fixture-prelaunch-task','kind':'completed','resources':[],'sequence':12}}
        for key,value in (('CAS_release',cas),('admin_done',done)):
            path=self.root/(key+'.json');path.write_text(json.dumps(value),encoding='utf8');bundle[key]=self.reference(path)
        for key,path in {'frozen':frozen,'allocated_context':live/'allocated-context.json','keeper':keeper/'report.json',
                'keeper_parent_exit':live/'keeper-actual-parent-exit.json','keeper_ready':keeper/'ready.json','counter':counter}.items():bundle[key]=self.reference(path)
        allocated={'status':'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN','task':'fixture-prelaunch-task','live':str(live),'keeper_root':str(keeper)}
        stdout=self.root/'fixture-allocator-ready.json';stdout.write_text(json.dumps(allocated),encoding='utf8');bundle['allocator_stdout']=self.reference(stdout)
        bundle.update(schema=subject.SCHEMA,closure_kind=subject.PRELAUNCH_KIND,machine_id=self.machine,run_id=live.name,
            **{key:False for key in ('host_started','native_session_started','game_started','normal_close_qualified','original_host_exit0','business_pass')})
        stamps=[datetime.fromisoformat(str(subject._read(keeper/name)['at_utc'])) for name in ('ready.json','report.json')]
        return bundle,live,keeper,stamps

    def test_real_prelaunch_producer_observed_waits_and_json_round_trip(self) -> None:
        bundle,live,keeper,stamps=self.prelaunch_fixture()
        value=json_object(json.loads(json.dumps(bundle)))
        evidence=subject.validate_prelaunch_orchestrator(value,previous=live,keeper=keeper,machine=self.machine,
            ready_at=stamps[0],keeper_closed_at=stamps[1])
        self.assertIn('prelaunch_guard_wait',evidence)
        self.assertEqual(subject._allocator_argv(value,self.machine,stamps)[5],'allocate')
        self.assertLess((stamps[1]-stamps[0]).total_seconds(),600)

    def test_real_first_guard_exits_before_armed_without_fabricated_later_guards(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2, before_armed=True)
        value = json_object(json.loads(json.dumps(bundle)))
        evidence = subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
            machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        self.assertEqual(subject._pinned_object(evidence['prelaunch_guard_wait'], 'wait')['original_wait_returncode'], 1)
        self.assertGreater(evidence['prelaunch_guard_stderr']['bytes'], 0)
        self.assertEqual(evidence['prelaunch_guard_stdout']['bytes'], 0)
        self.assertIn('prelaunch_guard_source', evidence)
        self.assertIn('prelaunch_guard_interpreter', evidence)
        self.assertIn('prelaunch_prepared_contract', evidence)
        output = Path(evidence['prelaunch_guard_wait']['path']).parent
        self.assertFalse((output/'DEADLINE-GUARD.ARMED.actual.json').exists())
        self.assertFalse((output/'DEADLINE-GUARD.CANCEL.actual.json').exists())
        self.assertEqual(list(output.glob('DEADLINE-GUARD-*')), [])

    def test_before_armed_rejects_wrong_discriminator_missing_wait_types_and_crossed_originals(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2, before_armed=True)
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        for state in (None, True, 1, 'unknown', 'armed-cancelled'):
            with self.subTest(state=state), self.assertRaises(ValueError):
                invoke({**bundle, 'prelaunch_guard_state': state})
        for key in ('prelaunch_guard_state', 'prelaunch_guard_wait', 'prelaunch_guard_intent',
                'prelaunch_guard_stderr', 'prelaunch_orchestrator_intent'):
            changed = dict(bundle);del changed[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):invoke(changed)
        cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('prelaunch_guard_wait', 'original_wait_returncode', 0),
            ('prelaunch_guard_wait', 'original_wait_returncode', True),
            ('prelaunch_guard_wait', 'original_wait_returncode', 1.0),
            ('prelaunch_guard_wait', 'pid', True), ('prelaunch_guard_wait', 'pid', 1),
            ('prelaunch_guard_started', 'process_creation_filetime_100ns', 1),
            ('prelaunch_guard_started', 'process_creation_filetime_100ns', '01'),
            ('prelaunch_guard_started', 'initial_exit_code', 259.0),
            ('prelaunch_guard_started', 'original_wait_pending', 1),
            ('prelaunch_guard_intent', 'source_commit', 'b'*40),
            ('prelaunch_guard_wait', 'observed_at_utc', stamps[1].isoformat()),
            ('prelaunch_failure', 'public_started', True),
            ('prelaunch_failure', 'error', "KeyError('revision')"))
        for key, field, bad in cases:
            original = subject._evidence_pin(bundle[key], key);path = Path(original['path']);raw = path.read_bytes()
            changed = json.loads(raw);changed[field] = bad;path.write_text(json.dumps(changed), encoding='utf8')
            try:
                with self.subTest(key=key, field=field), self.assertRaises(ValueError):
                    invoke({**bundle, key: self.reference(path)})
            finally:path.write_bytes(raw)
        original = subject._evidence_pin(bundle['prelaunch_guard_stderr'], 'stderr')
        path = Path(original['path']);raw = path.read_bytes();path.write_bytes(b'')
        try:
            with self.assertRaises(ValueError):invoke({**bundle, 'prelaunch_guard_stderr':self.reference(path)})
        finally:path.write_bytes(raw)
        root_intent = Path(subject._evidence_pin(bundle['prelaunch_orchestrator_intent'], 'intent')['path'])
        binding = Path(subject._evidence_pin(subject._read(root_intent)['binding'], 'binding')['path'])
        raw = binding.read_bytes();changed = json.loads(raw);changed['deadline_guard'] = bundle['allocator_command']
        binding.write_text(json.dumps(changed), encoding='utf8')
        try:
            with self.assertRaises(ValueError):invoke(bundle)
        finally:binding.write_bytes(raw)

    def test_before_armed_rejects_any_armed_cancel_extra_phase_or_later_public_artifact(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2, before_armed=True)
        output = Path(subject._evidence_pin(bundle['prelaunch_guard_wait'], 'wait')['path']).parent
        for name in ('DEADLINE-GUARD.ARMED.actual.json', 'DEADLINE-GUARD.CANCEL.actual.json',
                'DEADLINE-GUARD.actual.json', 'DEADLINE-GUARD-1.intent.actual.json',
                'ORCHESTRATOR.PUBLIC-RUN.started.actual.json', 'PUBLIC-RUN.intent.actual.json',
                'LAUNCH-GATES-CONSUMED.actual.json'):
            path = output/name;path.write_text('{}', encoding='utf8')
            try:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    subject.validate_prelaunch_orchestrator(bundle, previous=live, keeper=keeper,
                        machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
            finally:path.unlink()

    def test_before_armed_native_generation_distinguishes_reused_live_and_unknown_pid(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2, before_armed=True)
        started = subject._pinned_object(bundle['prelaunch_guard_started'], 'started')
        pid = subject._integer(started['pid'], 'fixture original pid', 1)
        birth = subject._text(started['process_creation_filetime_100ns'], 'fixture birth')
        def invoke() -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(bundle, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        with patch('psutil.pid_exists', side_effect=lambda observed: observed == pid):
            with patch('ck3_mod_acceptance_launcher.process_identity',
                    return_value={'pid':pid, 'birth_filetime':str(int(birth)+1)}) as observe:
                self.assertIn('prelaunch_guard_wait', invoke())
                observe.assert_called_once_with(pid)
            with patch('ck3_mod_acceptance_launcher.process_identity',
                    return_value={'pid':pid, 'birth_filetime':birth}), self.assertRaisesRegex(ValueError, 'still present'):
                invoke()
            with patch('ck3_mod_acceptance_launcher.process_identity', side_effect=ValueError('Native read unavailable')), \
                    self.assertRaisesRegex(ValueError, 'generation unavailable'):
                invoke()
            with patch('ck3_mod_acceptance_launcher.process_identity', return_value=None), \
                    self.assertRaisesRegex(ValueError, 'generation unavailable'):
                invoke()
            with patch('ck3_mod_acceptance_launcher.process_identity',
                    return_value={'pid':pid, 'birth_filetime':str(int(birth)+1)}):
                missing = dict(bundle);del missing['prelaunch_guard_wait']
                with self.assertRaises(ValueError):
                    subject.validate_prelaunch_orchestrator(missing, previous=live, keeper=keeper,
                        machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])

    def test_before_armed_binds_interpreter_pin_and_original_root_interpreter_arguments(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2, before_armed=True)
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        keys = ('prelaunch_guard_intent', 'prelaunch_guard_started', 'prelaunch_guard_wait')
        originals = {key: Path(subject._evidence_pin(bundle[key], key)['path']).read_bytes() for key in keys}
        changed = dict(bundle)
        for key in keys:
            path = Path(subject._evidence_pin(bundle[key], key)['path'])
            row = json.loads(originals[key]);row['argv'][0] = str(self.producer)
            path.write_text(json.dumps(row), encoding='utf8');changed[key] = self.reference(path)
        try:
            with self.assertRaisesRegex(ValueError, 'argv/first phase/source'):invoke(changed)
        finally:
            for key in keys:Path(subject._evidence_pin(bundle[key], key)['path']).write_bytes(originals[key])
        keys = ('prelaunch_orchestrator_intent', 'prelaunch_orchestrator_started', 'prelaunch_orchestrator_wait')
        originals = {key: Path(subject._evidence_pin(bundle[key], key)['path']).read_bytes() for key in keys}
        for flag, wrong in (('--guard-interpreter', str(self.producer)), ('--guard-interpreter-sha256', '0'*64)):
            changed = dict(bundle)
            for key in keys:
                path = Path(subject._evidence_pin(bundle[key], key)['path'])
                row = json.loads(originals[key]);argv = row['argv'];argv[argv.index(flag)+1] = wrong
                path.write_text(json.dumps(row), encoding='utf8');changed[key] = self.reference(path)
            try:
                with self.subTest(flag=flag), self.assertRaisesRegex(ValueError, 'interpreter crossed launch binding'):
                    invoke(changed)
            finally:
                for key in keys:Path(subject._evidence_pin(bundle[key], key)['path']).write_bytes(originals[key])

    def test_prelaunch_wrong_fields_types_source_pid_chronology_and_action_reject(self) -> None:
        bundle,live,keeper,stamps=self.prelaunch_fixture()
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value,previous=live,keeper=keeper,machine=self.machine,
                ready_at=stamps[0],keeper_closed_at=stamps[1])
        cases: tuple[tuple[str,str,JsonValue],...]=(
            ('prelaunch_failure','public_started',True),('prelaunch_failure','public_started',0),
            ('prelaunch_failure','business_pass',True),('prelaunch_failure','alias',False),
            ('prelaunch_guard_cancel','pid',True),('prelaunch_guard_cancel','pid',1),
            ('prelaunch_guard_wait','original_wait_returncode',False),('prelaunch_guard_wait','original_wait_returncode',0),
            ('prelaunch_guard_armed','reserve_seconds',1200.0),('prelaunch_guard_armed','game_or_queue_action_sent',True),
            ('prelaunch_guard_armed','run_id','different-run'),('prelaunch_guard_wait','at',stamps[0].isoformat()))
        for key,field,bad in cases:
            original=subject._evidence_pin(bundle[key],key);path=Path(original['path']);raw=path.read_bytes()
            changed=json.loads(raw);changed[field]=bad;path.write_text(json.dumps(changed),encoding='utf8')
            with self.subTest(key=key,field=field),self.assertRaises(ValueError):invoke({**bundle,key:self.reference(path)})
            path.write_bytes(raw)
        missing=dict(bundle);del missing['prelaunch_guard_wait']
        with self.assertRaises(ValueError):invoke(missing)
        source=Path(subject._evidence_pin(bundle['prelaunch_orchestrator_source'],'source')['path'])
        raw=source.read_bytes();source.write_text(raw.decode().replace('code = child.wait()','code = 0'),encoding='utf8')
        with self.assertRaises(ValueError):invoke({**bundle,'prelaunch_orchestrator_source':self.reference(source)})
        source.write_bytes(raw)
        action=Path(subject._evidence_pin(bundle['prelaunch_guard_wait'],'wait')['path']).parent/'PUBLIC-RUN.intent.actual.json'
        action.write_text('{}',encoding='utf8')
        with self.assertRaises(ValueError):invoke(bundle)

    def test_observed_root_real_producer_wrapper_identity_and_round_trip(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True)
        value = json_object(json.loads(json.dumps(bundle)))
        evidence = subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
            machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        started = subject._pinned_object(value['prelaunch_guard_started'], 'started')
        armed = subject._pinned_object(value['prelaunch_guard_armed'], 'armed')
        self.assertNotEqual(started['pid'], armed['pid'])
        self.assertIn('prelaunch_orchestrator_wait', evidence)
        self.assertEqual(subject._allocator_argv(value, self.machine, stamps)[5], 'allocate')

    def test_split_root_three_real_guards_original_waits_and_round_trip(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True)
        value = json_object(json.loads(json.dumps(bundle)))
        evidence = subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
            machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        guards = {key: value for key, value in evidence.items() if key.startswith('DEADLINE-GUARD-')}
        self.assertEqual(set(guards), {label+'.'+key for label in ('DEADLINE-GUARD-1','DEADLINE-GUARD-2')
            for key in ('intent','started','armed','cancel','original_wait')})
        for reference in guards.values():
            self.assertEqual(set(reference), {'path','bytes','sha256'})
            self.assertEqual(self.reference(Path(reference['path'])), reference)
        self.assertEqual(subject._allocator_argv(value, self.machine, stamps)[5], 'allocate')

    def test_intent_bound_root_two_real_guards_original_waits_and_round_trip(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2)
        value = json_object(json.loads(json.dumps(bundle)))
        evidence = subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
            machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        self.assertIn('prelaunch_orchestrator_intent', evidence)
        self.assertEqual({key for key in evidence if key.startswith('DEADLINE-GUARD-')},
            {'DEADLINE-GUARD-1.' + key for key in ('intent','started','armed','cancel','original_wait')})
        self.assertEqual(subject._allocator_argv(value, self.machine, stamps)[5], 'allocate')

    def test_intent_bound_root_rejects_changed_shape_types_binding_and_incomplete_phases(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True,
            intent_root=True, phase_count=2)
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('prelaunch_orchestrator_intent','ambient_pythonpath_removed',1),
            ('prelaunch_orchestrator_intent','no_manual_sdk_import_path',False),
            ('prelaunch_orchestrator_intent','machine_id','different-machine'),
            ('prelaunch_orchestrator_intent','observed_at_utc',stamps[1].isoformat()),
            ('prelaunch_orchestrator_started','pid',True),
            ('prelaunch_orchestrator_started','original_wait_pending',1),
            ('prelaunch_orchestrator_wait','pid',1),
            ('prelaunch_orchestrator_wait','elapsed_seconds',True),
            ('prelaunch_orchestrator_wait','original_wait_returncode',False))
        for key, field, bad in cases:
            path=Path(subject._evidence_pin(bundle[key],key)['path']);raw=path.read_bytes()
            changed=json.loads(raw);changed[field]=bad;path.write_text(json.dumps(changed),encoding='utf8')
            with self.subTest(key=key,field=field),self.assertRaises(ValueError):
                invoke({**bundle,key:self.reference(path)})
            path.write_bytes(raw)
        missing=dict(bundle);del missing['prelaunch_orchestrator_intent']
        with self.assertRaises(ValueError):invoke(missing)
        allocation_wait=Path(subject._evidence_pin(bundle['prelaunch_allocator_wait'],'allocator wait')['path'])
        allocation_raw=allocation_wait.read_bytes();wrong_allocation=json.loads(allocation_raw)
        wrong_allocation['argv'][-1]='b'*64;allocation_wait.write_text(json.dumps(wrong_allocation),encoding='utf8')
        with self.assertRaisesRegex(ValueError,'public recorder invocation differs'):
            invoke({**bundle,'prelaunch_allocator_wait':self.reference(allocation_wait)})
        allocation_wait.write_bytes(allocation_raw)
        changed_refs: dict[str, object] = {}
        originals: dict[Path, bytes] = {}
        for key in ('prelaunch_orchestrator_intent','prelaunch_orchestrator_started','prelaunch_orchestrator_wait'):
            path=Path(subject._evidence_pin(bundle[key],key)['path']);originals[path]=path.read_bytes()
            value=json.loads(originals[path]);value['argv'][-1]='b'*64
            path.write_text(json.dumps(value),encoding='utf8');changed_refs[key]=self.reference(path)
        with self.assertRaisesRegex(ValueError,'arguments crossed launch binding'):
            invoke({**bundle,**changed_refs})
        for path, raw in originals.items():path.write_bytes(raw)
        intent_path=Path(subject._evidence_pin(bundle['prelaunch_orchestrator_intent'],'intent')['path'])
        intent=json.loads(intent_path.read_bytes());binding=Path(intent['binding']['path']);binding_raw=binding.read_bytes()
        changed_binding=json.loads(binding_raw);changed_binding['source_commit']='b'*40
        binding.write_text(json.dumps(changed_binding),encoding='utf8')
        intent['binding']=self.reference(binding);intent_raw=intent_path.read_bytes()
        intent_path.write_text(json.dumps(intent),encoding='utf8')
        with self.assertRaises(ValueError):invoke({**bundle,'prelaunch_orchestrator_intent':self.reference(intent_path)})
        binding.write_bytes(binding_raw);intent_path.write_bytes(intent_raw)
        output=Path(subject._evidence_pin(bundle['allocator_intent'],'intent')['path']).parent
        missing_guard=output/'DEADLINE-GUARD-1.CANCEL.actual.json';guard_raw=missing_guard.read_bytes();missing_guard.unlink()
        with self.assertRaisesRegex(ValueError,'Exact consecutive complete'):invoke(bundle)
        missing_guard.write_bytes(guard_raw)
        extra=output/'DEADLINE-GUARD-2.started.actual.json';extra.write_text('{}',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'Exact consecutive complete'):invoke(bundle)
        extra.unlink()
        for path in output.glob('DEADLINE-GUARD-1.*'):path.unlink()
        without_group=dict(bundle);del without_group['prelaunch_phase_guards']
        with self.assertRaisesRegex(ValueError,'prepared contract and phase guard count differ'):
            invoke(without_group)

    def test_split_root_and_additional_guard_wrong_contracts_are_rejected(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True, phase_guards=True)
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        root_cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('prelaunch_orchestrator_started','ambient_pythonpath_removed',1),
            ('prelaunch_orchestrator_started','original_wait_pending',0),
            ('prelaunch_orchestrator_started','process_create_time_seconds',1),
            ('prelaunch_orchestrator_wait','elapsed_seconds',True),
            ('prelaunch_orchestrator_wait','original_wait_returncode',False),
            ('prelaunch_orchestrator_wait','pid',1))
        for key, field, bad in root_cases:
            path=Path(subject._evidence_pin(bundle[key],key)['path']);raw=path.read_bytes()
            changed=json.loads(raw);changed[field]=bad;path.write_text(json.dumps(changed),encoding='utf8')
            with self.subTest(key=key,field=field),self.assertRaises(ValueError):
                invoke({**bundle,key:self.reference(path)})
            path.write_bytes(raw)
        output=Path(subject._evidence_pin(bundle['allocator_intent'],'intent')['path']).parent
        guard_cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('intent','source_commit','b'*40),('started','pid',True),
            ('started','process_creation_filetime_100ns',1),('ARMED','phase','wrong-phase'),
            ('ARMED','game_or_queue_action_sent',True),('CANCEL','pid',True),
            ('original-wait','original_wait_returncode',0),('original-wait','pid',False),
            ('original-wait','observed_at_utc',stamps[0].isoformat()))
        for suffix, field, bad in guard_cases:
            path=output/('DEADLINE-GUARD-1.'+suffix+'.actual.json');raw=path.read_bytes()
            changed=json.loads(raw);changed[field]=bad;path.write_text(json.dumps(changed),encoding='utf8')
            changed_bundle={**bundle,'prelaunch_phase_guards':subject._phase_guard_evidence(output)}
            with self.subTest(suffix=suffix,field=field),self.assertRaises(ValueError):invoke(changed_bundle)
            path.write_bytes(raw)
        missing=dict(bundle);del missing['prelaunch_phase_guards']
        with self.assertRaises(ValueError):invoke(missing)
        unknown=output/'DEADLINE-GUARD-3.started.actual.json';unknown.write_text('{}',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'Exact consecutive complete additional'):invoke(bundle)
        unknown.unlink()
        with patch.object(psutil,'pid_exists',return_value=True),self.assertRaisesRegex(ValueError,'still present'):
            invoke(bundle)

    def test_observed_root_rejects_wrong_fields_types_binding_wait_and_later_actions(self) -> None:
        bundle, live, keeper, stamps = self.prelaunch_fixture(observed_root=True)
        def invoke(value: Mapping[str, object]) -> dict[str, FilePin]:
            return subject.validate_prelaunch_orchestrator(value, previous=live, keeper=keeper,
                machine=self.machine, ready_at=stamps[0], keeper_closed_at=stamps[1])
        cases: tuple[tuple[str, str, JsonValue], ...] = (
            ('prelaunch_orchestrator_wait','original_wait_returncode',False),
            ('prelaunch_orchestrator_wait','original_wait_returncode',0),
            ('prelaunch_orchestrator_started','pid',True),
            ('prelaunch_failure','public_started',0),
            ('prelaunch_failure','normal_closed',True),
            ('prelaunch_guard_wait','original_wait_returncode',0),
            ('prelaunch_guard_wait','pid',True),
            ('prelaunch_guard_started','process_creation_filetime_100ns',1),
            ('prelaunch_guard_armed','reserve_seconds',1200.0),
            ('prelaunch_guard_armed','game_or_queue_action_sent',True),
            ('prelaunch_guard_cancel','alias',False))
        for key, field, bad in cases:
            path=Path(subject._evidence_pin(bundle[key],key)['path']);raw=path.read_bytes()
            changed=json.loads(raw);changed[field]=bad;path.write_text(json.dumps(changed),encoding='utf8')
            with self.subTest(key=key,field=field),self.assertRaises(ValueError):invoke({**bundle,key:self.reference(path)})
            path.write_bytes(raw)
        missing=dict(bundle);del missing['prelaunch_orchestrator_wait']
        with self.assertRaises(ValueError):invoke(missing)
        path=Path(subject._evidence_pin(bundle['prelaunch_orchestrator_started'],'start')['path'])
        raw=path.read_bytes();changed=json.loads(raw);changed['argv'][changed['argv'].index('--out')+1]=str(self.root/'other')
        path.write_text(json.dumps(changed),encoding='utf8')
        with self.assertRaises(ValueError):invoke({**bundle,'prelaunch_orchestrator_started':self.reference(path)})
        path.write_bytes(raw)
        source=Path(subject._evidence_pin(bundle['prelaunch_orchestrator_source'],'source')['path'])
        raw=source.read_bytes();source.write_bytes(raw+b'\n')
        with self.assertRaises(ValueError):invoke(bundle)
        source.write_bytes(raw)
        with patch.object(psutil,'pid_exists',return_value=True),self.assertRaisesRegex(ValueError,'still present'):
            invoke(bundle)
        action=Path(subject._evidence_pin(bundle['prelaunch_guard_wait'],'wait')['path']).parent/'ORCHESTRATOR.PUBLIC-RUN.intent.actual.json'
        action.write_text('{}',encoding='utf8')
        with self.assertRaises(ValueError):invoke(bundle)


class AbortedAllocationTests(unittest.TestCase):
    """Run the real bundle producer and consumer; only OS observers are fixtures."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='unrun-aborted-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.machine = 'fixture-machine'
        self.run_id = self.machine+'--living-artifacts--R0001'
        self.live = self.root/self.run_id
        self.keeper = self.root/'keeper'
        self.state = self.root/'old-state'
        self.source = self.root/'source'
        self.ids = self.root/'ids'
        self.live.mkdir();self.keeper.mkdir();(self.live/'controls').mkdir()
        self.serial = 0
        self.prepared = self.write('prepared.json',{'fixture':'prepared'})
        self.products = self.write('products.json',{'products':{'living-artifacts':{'external_mod':False}}})
        self.bus = self.root/'bus'
        (self.bus/'bin').mkdir(parents=True)
        cli = self.bus/'bin/codex_task_bus.py';cli.write_bytes(b'fixture cli')
        cli_pin: JsonObject={'path':str(cli.resolve()),'bytes':11,'sha256':hashlib.sha256(cli.read_bytes()).hexdigest()}
        self.freeze: JsonObject={'run_id':self.run_id,'screen_task':'fixture-task','state_dir':str(self.state),
            'source_root':str(self.source),'mod_key':'living-artifacts','lease_anchor':str(self.root),
            'identity_allocation':{'machine_id':self.machine,'state_root':str(self.ids)},
            'files':{str(Path(self.products['path']).resolve()):json_object(self.products),str(cli.resolve()):cli_pin}}
        frozen = self.write_live('frozen-argv.json',self.freeze)
        ready: JsonObject={'run_id':self.run_id,'run_dir':str(self.live),'keeper_root':str(self.keeper),
            'frozen_argv':json_object(frozen),'prepared_case':json_object(self.prepared),'product':'living-artifacts'}
        self.write_live('ready-context.json',ready);self.write_live('allocated-context.json',ready)
        self.write_path(self.keeper/'inputs.json',{'task_id':'fixture-task'})
        self.write_path(self.keeper/'ready.json',{'at_utc':'2026-10-23T00:01:00Z',
            'lease':{'task_id':'fixture-task','sequence':10}})
        self.write_live('keeper-process.json',{'pid':2147483001})
        argv=['python','tools/ck3_mod_acceptance.py','allocate','--prepared-case',self.prepared['path'],
              '--keeper-output',str(self.keeper),'--products',self.products['path'],'--product','living-artifacts']
        self.intent=self.write('intent.json',{'machine_id':self.machine,'at_utc':'2026-10-23T00:00:00Z',
            'stage':'allocate','argv':argv})
        self.process=self.write('process.json',{'machine_id':self.machine,'pid':2147483000,'argv':argv})
        self.wrapper=self.write('wrapper.json',{'schema':'operational-wrapper-external-exec-failure-v1',
            'machine_id':self.machine,'observed_at_utc':'2026-10-23T00:02:00Z',
            'allocator_started_pid':2147483000,'keeper_started_pid':2147483001,
            'allocator_original_popen_wait_observed':False,'allocator_exit_code':None,
            'run_invoked':False,'game_started':False,'tool_result':{'chunk_id':'fixture','exit_code':1,'session_id':None}})
        self.stdout=self.write('allocator.stdout.json',{'status':'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN',
            'task':'fixture-task','keeper_pid':2147483001,'live':str(self.live),
            'context':str(self.live/'ready-context.json')})
        self.write_path(self.ids/self.machine/'living-artifacts/counter.json',{'machine_id':self.machine,'mod_key':'living-artifacts','last_sequence':1})
        task: JsonObject={'task_id':'fixture-task','state':'waiting','resources':[],'last_sequence':11,'repo':'fixture-repo','git':{}}
        self.cas=self.write('cas.json',{'schema':'codex.task_bus.v1','ok':True,'task':task,
            'event':{'task_id':'fixture-task','state':'waiting','resources':[],'sequence':11,
                'retirement':{'kind':'expired-own-claim-released','business_status':'unresolved_red','prior_sequence':10}}})
        done_task={**task,'state':'done','last_sequence':12}
        self.done: JsonObject={'schema':'codex.task_bus.v1','ok':True,'task':done_task,
            'event':{'task_id':'fixture-task','state':'done','resources':[],'sequence':12,'kind':'completed'}}
        self.done_pin=self.write('done.json',self.done)
        self.packet: JsonObject={'tasks':[{**done_task,'age_seconds':0,'stale':False}]}
        self.game: JsonObject={'tasklist_returncode':0,'tasklist_pids':[],'wmi_pids':[],'processes':[]}
        self.runtime: JsonObject={'blockers':[]}
        import ck3_mod_acceptance_allocate as allocator
        import ck3_live_run_id as ids
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(ids,'current_machine_id',return_value=self.machine))
        stack.enter_context(patch.object(ids,'default_state_root',return_value=self.ids))
        stack.enter_context(patch.object(allocator,'runtime_process_inventory',side_effect=lambda *_:self.runtime))
        stack.enter_context(patch.object(allocator,'current_screen_absent',side_effect=lambda *_:self.packet))
        provider=SimpleNamespace(__file__=str(self.source/'ck3_autonomous_player/src/xar_autoplayer/environment.py'),
            ck3_process_inventory=lambda:self.game)
        original_import=importlib.import_module
        stack.enter_context(patch.object(importlib,'import_module',side_effect=lambda name, package=None:
            provider if name=='xar_autoplayer.environment' else original_import(name,package)))

    def write_path(self, path: Path, value: object) -> FilePin:
        path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(value).encode('utf-8');path.write_bytes(raw)
        return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

    def write(self, name: str, value: object) -> FilePin:
        return self.write_path(self.root/name,value)

    def write_live(self, name: str, value: object) -> FilePin:
        return self.write_path(self.live/name,value)

    def produce(self) -> subject.UnrunBundleReport:
        self.serial+=1
        return subject.build_aborted_bundle_v1(argparse.Namespace(previous_live=self.live,keeper_root=self.keeper,
            allocator_intent=Path(self.intent['path']),allocator_process=Path(self.process['path']),
            allocator_exit=None,allocator_result=None,allocator_external_exec=None,
            aborted_wrapper=Path(self.wrapper['path']),aborted_release=Path(self.cas['path']),
            admin_release=Path(self.done_pin['path']),allocator_stdout=Path(self.stdout['path']),
            next_state=self.root/'new-state',output=self.root/f'output-{self.serial}',task_bus_root=self.bus))

    def test_actual_producer_dispatch_consumer_and_json_round_trip_keep_waits_unknown(self) -> None:
        report=self.produce();verdict=report['validation'];cleanup=member(verdict,'failure_cleanup')
        from ck3_mod_acceptance_allocate import (predecessor_keeper_report_v1,
                                                require_predecessor_keeper_release_v1)
        self.assertFalse((self.keeper/'report.json').exists())
        self.assertIsNone(predecessor_keeper_report_v1(self.keeper,aborted_wrapper=True,
            pre_ready=False,expired_keeper=False,interrupted_owner=False))
        with self.assertRaises(FileNotFoundError):
            predecessor_keeper_report_v1(self.keeper,aborted_wrapper=False,
                pre_ready=False,expired_keeper=False,interrupted_owner=False)
        self.assertFalse(cleanup['original_allocator_wait_proven']);self.assertIsNone(cleanup['original_allocator_exit_code'])
        self.assertFalse(cleanup['original_keeper_wait_proven']);self.assertIsNone(cleanup['original_keeper_exit_code'])
        self.assertFalse(cleanup['business_pass']);self.assertFalse(cleanup['normal_close_qualified'])
        actual=subject.validate_aborted_allocation_v1(self.live,json.loads(json.dumps(self.freeze)),
            Path(report['bundle']['path']),self.keeper,self.done,json.loads(json.dumps(self.packet)),next_state=self.root/'new-state')
        self.assertEqual(actual['mode'],'previous-shared-allocated-aborted-wrapper-resource-only')
        require_predecessor_keeper_release_v1(None,self.done,str(self.freeze['screen_task']),
            exceptional_terminal_validated=actual['mode']=='previous-shared-allocated-aborted-wrapper-resource-only')
        with self.assertRaisesRegex(ValueError,'keeper/release'):
            require_predecessor_keeper_release_v1(None,self.done,str(self.freeze['screen_task']),
                exceptional_terminal_validated=False)

    def test_any_actual_launch_or_terminal_evidence_refuses_missing_wait_branch(self) -> None:
        for name in ('launch-intent.json','host-started.json','native-report.json','keeper-actual-parent-exit.json'):
            path=self.live/name;path.write_text('{}',encoding='utf-8')
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'launch/native/control'):self.produce()
            path.unlink()

    def test_crossed_wait_claim_bool_pid_active_tree_and_dual_provider_reject(self) -> None:
        for key,value in (('allocator_original_popen_wait_observed',True),('allocator_exit_code',0),
                          ('allocator_started_pid',True),('run_invoked',True)):
            raw=json.loads(Path(self.wrapper['path']).read_text(encoding='utf-8'));raw[key]=value
            original=self.wrapper;self.wrapper=self.write(f'changed-{key}.json',raw)
            with self.subTest(key=key),self.assertRaises(ValueError):self.produce()
            self.wrapper=original
        self.game['wmi_pids']=[3]
        with self.assertRaisesRegex(ValueError,'dual-provider'):self.produce()
        self.game['wmi_pids']=[];self.runtime['blockers']=[{'pid':3}]
        with self.assertRaisesRegex(ValueError,'dual-provider'):self.produce()

    def test_pin_drift_crossed_resource_sequence_and_reused_state_are_rejected(self) -> None:
        report=self.produce();path=Path(report['bundle']['path']);bundle=json.loads(path.read_text(encoding='utf-8'))
        bundle['allocator_exit_code']=0;self.write_path(path,bundle)
        with self.assertRaises(ValueError):subject.validate_aborted_allocation_v1(self.live,self.freeze,path,self.keeper,self.done,self.packet,next_state=self.root/'new-state')
        report=self.produce();path=Path(report['bundle']['path'])
        with self.assertRaisesRegex(ValueError,'quarantined'):subject.validate_aborted_allocation_v1(self.live,self.freeze,path,self.keeper,self.done,self.packet,next_state=self.state)
        Path(self.stdout['path']).write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):subject.validate_aborted_allocation_v1(self.live,self.freeze,path,self.keeper,self.done,self.packet,next_state=self.root/'new-state')


@runtime_checkable
class AbortedAdmissionLock(Protocol):
    def __call__(self, path: Path) -> AbstractContextManager[object]: ...


class ClosedKeeperAbortedAllocationTests(unittest.TestCase):
    """R35: serial guard assertion, lost outer wait, real idle keeper wait0."""

    def setUp(self) -> None:
        fixture = AbortedAllocationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.serial = 0
        intent = json_object(json.loads(Path(fixture.intent['path']).read_text(encoding='utf8')))
        self.argv = intent['argv']
        fixture.intent = fixture.write('serial-intent.json', {'machine_id':fixture.machine,
            'observed_at_utc':'2026-10-23T00:00:00.000001Z', 'argv':self.argv,
            'started_at_utc':'2026-10-23T00:00:00Z'})
        fixture.process = fixture.write('serial-started.json', {'machine_id':fixture.machine,
            'observed_at_utc':'2026-10-23T00:00:00.002Z', 'pid':2147483000,
            'process_create_time_seconds':'1792713600.000001',
            'started_at_utc':'2026-10-23T00:00:00.001Z', 'original_wait_pending':True})
        source = fixture.root/'original-serial.py'
        source.write_text('raise AssertionError("original guard redirector differs")\n', encoding='utf8')
        self.source = source
        original_failure = fixture.write('serial-failure.json', {'machine_id':fixture.machine,
            'observed_at_utc':'2026-10-23T00:02:00Z', 'error':'AssertionError()',
            'public_started':False, 'display_before':None, 'no_automatic_replay':True})
        tool: JsonObject = {'chunk_id':'original-wrapper-failed', 'exit_code':1, 'output':'AssertionError'}
        tool_pin = fixture.write('original-tool-terminal.json', tool)
        wrapper = json_object(json.loads(Path(fixture.wrapper['path']).read_text(encoding='utf8')))
        source_raw = source.read_bytes()
        source_ref: FilePin = {'path':str(source.resolve()), 'bytes':len(source_raw),
            'sha256':hashlib.sha256(source_raw).hexdigest()}
        wrapper.update({'tool_result':tool, 'original_source':json_object(source_ref),
            'original_failure':json_object(original_failure), 'original_tool_result':json_object(tool_pin)})
        fixture.wrapper = fixture.write('serial-wrapper-readback.json', wrapper)
        cas = json_object(json.loads(Path(fixture.cas['path']).read_text(encoding='utf8')))
        member(cas, 'task')['state'] = 'done'
        member(cas, 'event').update({'state':'done', 'kind':'completed'})
        member(cas, 'event').pop('retirement')
        fixture.cas = fixture.write('closed-keeper-release.json', cas)
        self.keeper_report: JsonObject = {'task_id':'fixture-task', 'thread_exited':True,
            'failure':None, 'entry_error':None, 'game_actions':False, 'last_sequence':10,
            'at_utc':'2026-10-23T00:11:00.000001Z'}
        fixture.write_path(fixture.keeper/'report.json', self.keeper_report)
        self.parent: JsonObject = {'keeper_actual_exit_code':0, 'keeper_report':self.keeper_report,
            'run_id':fixture.run_id, 'business_pass':False}
        fixture.write_live('keeper-actual-parent-exit.json', self.parent)
        fixture.write_live('allocation-unused-idle-timeout.json', {'reason':'NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT',
            'idle_seconds':600, 'utc':'2026-10-23T00:11:00Z', 'game_started':False,
            'native_session_started':False, 'normal_close_qualified':False, 'business_pass':False})
        (fixture.keeper/'STOP').write_text('Unused allocation idle deadline; no game/native/normal credit.\n', encoding='utf8')
        allocated = json_object(json.loads(Path(fixture.stdout['path']).read_text(encoding='utf8')))
        allocated.update({'game_started':False, 'business_pass':False})
        self.allocated = allocated
        self.stdout_path = fixture.root/'serial-allocator.stdout.log'
        self.stdout_path.write_text(json.dumps(allocated)+'\n'+json.dumps({**allocated, **self.parent})+'\n', encoding='utf8')

    def args(self) -> argparse.Namespace:
        self.serial += 1
        fixture = self.fixture
        return argparse.Namespace(previous_live=fixture.live, keeper_root=fixture.keeper,
            allocator_intent=Path(fixture.intent['path']), allocator_process=Path(fixture.process['path']),
            allocator_exit=None, allocator_result=None, allocator_external_exec=None,
            aborted_wrapper=Path(fixture.wrapper['path']), aborted_keeper_closed=True,
            aborted_release=Path(fixture.cas['path']), admin_release=Path(fixture.done_pin['path']),
            allocator_stdout=self.stdout_path, next_state=fixture.root/'new-state',
            output=fixture.root/f'closed-keeper-output-{self.serial}', task_bus_root=fixture.bus)

    def produce(self) -> subject.UnrunBundleReport:
        return subject.build_bundle(self.args())

    def test_real_producer_dispatch_and_round_trip_preserve_each_original_wait(self) -> None:
        report = self.produce()
        bundle = json_object(json.loads(Path(report['bundle']['path']).read_text(encoding='utf8')))
        self.assertEqual(bundle['closure_kind'], subject.CLOSED_KEEPER_ABORTED_KIND)
        self.assertFalse(bundle['allocator_original_wait_observed'])
        self.assertIsNone(bundle['allocator_exit_code'])
        self.assertTrue(bundle['keeper_original_wait_observed'])
        self.assertEqual(bundle['keeper_exit_code'], 0)
        fixture = self.fixture
        original_release = json_object(json.loads(Path(fixture.cas['path']).read_text(encoding='utf8')))
        self.assertNotIn('retirement', member(original_release, 'event'))
        import ck3_mod_acceptance_allocate as allocator
        reducer: object = subject.validate_allocated_unrun
        if not isinstance(reducer, allocator._PrelaunchUnrunAdmissionReducer):
            raise AssertionError('Actual shared reducer unavailable')
        verdict = json_object(reducer(fixture.live, fixture.freeze,
            Path(report['bundle']['path']), fixture.keeper, fixture.done, fixture.packet,
            next_state=fixture.root/'new-state'))
        self.assertEqual(verdict['mode'], 'previous-shared-allocated-unrun-prelaunch-orchestrator-failed')
        cleanup = member(verdict, 'failure_cleanup')
        self.assertFalse(cleanup['original_allocator_wait_proven'])
        self.assertIsNone(cleanup['original_allocator_exit_code'])
        self.assertTrue(cleanup['original_keeper_wait_proven'])
        self.assertEqual(cleanup['original_keeper_exit_code'], 0)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertFalse(cleanup[key])
        self.assertEqual(self.argv, json.loads(Path(fixture.intent['path']).read_text())['argv'])

    def test_known_keeper_wait_cannot_be_hidden_or_replaced_with_bool(self) -> None:
        fixture = self.fixture
        parent_path = fixture.live/'keeper-actual-parent-exit.json'
        raw = parent_path.read_bytes()
        for value in (True, 1, None):
            fixture.write_path(parent_path, {**self.parent, 'keeper_actual_exit_code':value})
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'internal Popen wait0'):
                self.produce()
        parent_path.write_bytes(raw)
        missing = fixture.keeper/'report.json'
        keeper_raw = missing.read_bytes();missing.unlink()
        with self.assertRaises(FileNotFoundError):self.produce()
        missing.write_bytes(keeper_raw)
        args = self.args();args.aborted_keeper_closed = False
        with self.assertRaises(ValueError):subject.build_bundle(args)

    def test_original_source_tool_stdout_and_allocator_wait_claim_are_verified(self) -> None:
        fixture = self.fixture
        wrapper = json_object(json.loads(Path(fixture.wrapper['path']).read_text(encoding='utf8')))
        original = fixture.wrapper
        fixture.wrapper = fixture.write('false-allocator-wait.json', {**wrapper, 'allocator_exit_code':0})
        with self.assertRaisesRegex(ValueError, 'unknown wait'):self.produce()
        fixture.wrapper = original
        source_raw = self.source.read_bytes();self.source.write_bytes(source_raw+b'\n')
        with self.assertRaises(ValueError):self.produce()
        self.source.write_bytes(source_raw)
        raw = self.stdout_path.read_bytes()
        self.stdout_path.write_text(json.dumps(self.allocated)+'\n'+json.dumps({**self.allocated,
            **self.parent, 'keeper_actual_exit_code':1}), encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'final stdout'):self.produce()
        self.stdout_path.write_bytes(raw)

    def claim(self, mutation: Callable[[], None] | None = None) -> tuple[Path, list[bool]]:
        import ck3_live_run_id as ids
        import ck3_mod_acceptance_allocate as allocator
        from ck3_mod_acceptance import Selection
        from ck3_mod_acceptance_fresh_machine_bootstrap import MachineBinding
        fixture = self.fixture
        report = self.produce()
        close = Path(report['bundle']['path'])
        selection = object.__new__(Selection)
        selection.state_dir = fixture.root/'new-state'
        selection.runtime_path = fixture.root/'runtime.json'
        selection.manifest_path = fixture.root/'manifest.json'
        selection.prepared_path = Path(fixture.prepared['path'])
        cli = fixture.bus/'bin/codex_task_bus.py'
        selection.runtime = {'allocation':{'lease_repo':str(fixture.root),
            'task_bus':{'path':str(cli), 'sha256':hashlib.sha256(cli.read_bytes()).hexdigest()}}}
        for path in (selection.runtime_path, selection.manifest_path):path.write_text('{}', encoding='utf8')
        args = argparse.Namespace(previous_live=fixture.live, previous_keeper=fixture.keeper,
            previous_failure_close=close, previous_release=Path(fixture.done_pin['path']))
        binding: MachineBinding = {'machine_id':fixture.machine, 'state_root':str(fixture.ids),
            'admission_root':str(fixture.root/'admission')}
        original_lock: object = ids._exclusive_file_lock
        if not isinstance(original_lock, AbortedAdmissionLock):raise AssertionError('Actual machine lock unavailable')
        reducer: object = subject.validate_allocated_unrun
        if not isinstance(reducer, allocator._PrelaunchUnrunAdmissionReducer):raise AssertionError('Actual reducer unavailable')
        held = False
        observations: list[bool] = []
        @contextmanager
        def locked(path: Path) -> Iterator[None]:
            nonlocal held
            with original_lock(path):
                held = True
                try:
                    if mutation is not None:mutation()
                    yield
                finally:held = False
        def reduce(previous: Path, freeze: object, path: Path, keeper: Path,
                release: object, bus: object, *, next_state: Path) -> JsonObject:
            observations.append(held)
            return reducer(previous, freeze, path, keeper, release, bus, next_state=next_state)
        with patch.object(ids, '_exclusive_file_lock', side_effect=locked), \
                patch.object(subject, 'validate_allocated_unrun', side_effect=reduce):
            record = allocator.claim_machine_admission(binding, selection, args, report['validation'])
        return record, observations

    def test_actual_allocator_revalidates_real_producer_under_original_writer_lock(self) -> None:
        record, observations = self.claim()
        self.assertEqual(observations, [True])
        intent = json_object(json.loads((record/'intent.json').read_text(encoding='utf8')))
        cleanup = member(member(intent, 'closure'), 'failure_cleanup')
        self.assertTrue(cleanup['original_keeper_wait_proven'])
        self.assertIsNone(cleanup['original_allocator_exit_code'])
        self.assertFalse(intent['business_pass'])

    def test_launch_inside_lock_rejects_before_any_intent(self) -> None:
        def mutate() -> None:
            (self.fixture.live/'host-started.json').write_text('{}', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'launch/native/control'):
            self.claim(mutate)
        admission = self.fixture.root/'admission'
        self.assertFalse((admission/'machine.json').exists())
        self.assertEqual(list(admission.glob('[0-9]*')), [])

    def test_known_keeper_pin_change_inside_lock_rejects_before_any_intent(self) -> None:
        def mutate() -> None:
            path = self.fixture.live/'keeper-actual-parent-exit.json'
            path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaises(ValueError):self.claim(mutate)
        admission = self.fixture.root/'admission'
        self.assertFalse((admission/'machine.json').exists())
        self.assertEqual(list(admission.glob('[0-9]*')), [])


class SerialKnownWaitPrelaunchTests(unittest.TestCase):
    """Authored process observations enter the real producer/reducer/OS lock.

    These temporary files model the actual R37 receipt shapes. No process birth,
    Game activity or historical original is claimed from the authored fixtures.
    """

    def setUp(self) -> None:
        f = AbortedAllocationTests('runTest')
        f.setUp(); self.addCleanup(f.doCleanups)
        self.fixture = f
        self.serial = 0
        self.commit = 'a'*40
        self.execution = f.root/'execution'
        self.execution.mkdir()
        self.root_execution = f.root/'root-execution'
        self.root_execution.mkdir()
        self.source = f.root/'serial-source.py'
        self.source.write_text('import subprocess\np=subprocess.Popen([])\np.wait()\n', encoding='utf8')
        manifest = f.write('predecessor-runtime-manifest.json', {'source_commit':self.commit})
        f.freeze['runtime_manifest'] = json_object(manifest)
        files = member(f.freeze, 'files')
        files[str(Path(manifest['path']))] = json_object(manifest)
        f.freeze['files'] = {name:{key:value for key,value in member(files,name).items() if key!='path'} for name in files}
        frozen = f.write_live('frozen-argv.json', f.freeze)
        ready = json_object(json.loads((f.live/'ready-context.json').read_bytes()))
        contract = f.write('serial-contract.json', {'gui_phases':[{'id':'phase-1'}, {'id':'phase-2'}]})
        f.prepared = f.write('prepared.json', {'contract':json_object(contract)})
        ready['prepared_case'] = json_object(f.prepared)
        ready['frozen_argv'] = json_object(frozen)
        self.ready = f.write_live('ready-context.json',ready)
        f.write_live('allocated-context.json',ready)
        self.keeper_report: JsonObject = {'task_id':'fixture-task','thread_exited':True,'failure':None,
            'entry_error':None,'game_actions':False,'last_sequence':10,'at_utc':self.stamp(15)}
        f.write_path(f.keeper/'report.json',self.keeper_report)
        f.write_path(f.keeper/'ready.json',{'at_utc':self.stamp(5),'lease':{'task_id':'fixture-task','sequence':10}})
        self.parent: JsonObject = {'run_id':f.run_id,'keeper_actual_exit_code':0,
            'keeper_report':self.keeper_report,'business_pass':False}
        f.write_live('keeper-actual-parent-exit.json',self.parent)
        (f.keeper/'STOP').write_text('Root pre-public failure; original allocation proves own never-Game keeper; no continuation qualification.\n',encoding='utf8')
        self.grant = f.write('grant.json', {'fixture':'bounded grant input'})
        self.launch_ready = f.write('launch-ready.json', {'fixture':'source-bound prepared input'})
        root_argv = [sys.executable,'-B','-X','utf8',str(self.source),'--source-commit',self.commit,
            '--grant',self.grant['path'],'--grant-sha256',self.grant['sha256'],
            '--ready',self.launch_ready['path'],'--ready-sha256',self.launch_ready['sha256']]
        f.write_path(self.root_execution/'ROOT-SERIAL.started.json',{'machine_id':f.machine,'pid':90003,
            'argv':root_argv,'started_at_utc':self.stamp(0),'original_wait_pending':True})
        f.write_path(self.root_execution/'ROOT-SERIAL.original-wait.json',{'machine_id':f.machine,'pid':90003,
            'argv':root_argv,'actual_original_popen_wait':True,'original_wait_returncode':1,'finished_at_utc':self.stamp(17)})
        (self.root_execution/'ROOT-SERIAL.stderr.log').write_bytes(b'Authored original root failure\n')
        guard = f.root/'guard.py';guard.write_text('pass\n',encoding='utf8')
        guard_invocation = 'exec(compile('+repr('pass\n')+','+repr(str(guard))+',"exec"))'
        interpreter = f.root/'guard-python.exe';interpreter.write_bytes(b'Authored interpreter identity, never executable')
        binder = f.root/'capacity.py';binder.write_text('pass\n',encoding='utf8')
        static: JsonObject = {'machine_id':f.machine,'source_commit':self.commit,'original_Popen_registry_retained':True,
            'grant':json_object(self.grant),'ready':json_object(self.launch_ready),
            'guard_original':json_object(subject._ttl_pin(guard)),'guard_interpreter':json_object(subject._ttl_pin(interpreter)),
            'capacity_original':json_object(subject._ttl_pin(binder)),'guard_code_sha256':hashlib.sha256(guard_invocation.encode()).hexdigest(),
            'capacity_source_sha256':'b'*64}
        f.write_path(self.execution/'STATIC-INPUTS-PRECOMPILED.actual.json',static)
        allocated: JsonObject = {'status':'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN','task':'fixture-task',
            'keeper_pid':2147483001,'live':str(f.live),'keeper_root':str(f.keeper),
            'context':str(f.live/'ready-context.json'),'game_started':False,'business_pass':False}
        self.stdout = self.execution/'ALLOCATE.stdout.log'
        self.stdout.write_text(json.dumps(allocated)+'\n'+json.dumps({**allocated,**self.parent})+'\n',encoding='utf8')
        (self.execution/'ALLOCATE.stderr.log').write_bytes(b'')
        argv = ['python','tools/ck3_mod_acceptance.py','allocate','--prepared-case',f.prepared['path'],
            '--keeper-output',str(f.keeper),'--products',f.products['path'],'--product','living-artifacts']
        processes: list[JsonObject] = []
        terminal: list[JsonObject] = []
        for index,label in enumerate(('ALLOCATE','COLD-GUARD-0','COLD-GUARD-1')):
            second = 1 if index==0 else 5+index
            pid = 90000+index
            born = int(datetime.fromisoformat(self.stamp(second)).timestamp())
            birth = str(116444736000000000+born*10000000+1)
            actual_argv = argv if index==0 else [str(interpreter),'-B','-X','utf8','-c',
                guard_invocation,
                '--live',str(f.live),'--ready-context',str(f.live/'ready-context.json'),'--run-id',f.run_id,
                '--phase','phase-'+str(index),'--reserve-seconds','1200','--wait-awaiting-seconds','5400',
                '--armed',str(self.execution/(label+'.ARMED.actual.json')),'--output',str(self.execution/(label+'.actual.json'))]
            f.write_path(self.execution/(label+'.intent.actual.json'),{'machine_id':f.machine,
                'observed_at_utc':self.stamp(second),'argv':actual_argv,'source_commit':self.commit,'started_at_utc':self.stamp(second)})
            f.write_path(self.execution/(label+'.started.actual.json'),{'machine_id':f.machine,
                'observed_at_utc':self.stamp(second), 'pid':pid,
                'process_creation_filetime_100ns':birth,'process_create_time_seconds':str(born)+'.0000001',
                'started_at_utc':self.stamp(second),'original_wait_pending':True})
            code = 0 if index==0 else 1
            f.write_path(self.execution/(label+'.original-wait.actual.json'),{'machine_id':f.machine,
                'observed_at_utc':self.stamp(16 if index==0 else 11+index),'pid':pid,
                'process_creation_filetime_100ns':birth,'original_wait_returncode':code,'elapsed_seconds':10.0,
                'finished_at_utc':self.stamp(16 if index==0 else 11+index)})
            processes.append({'label':label,'pid':pid,'birth_filetime':birth,'original_wait_consumed':False,'actual_returncode':None})
            terminal.append({'label':label,'pid':pid,'process_creation_filetime_100ns':birth,'receipt_written':True,'returncode':code})
            if index:
                armed = f.write_path(self.execution/(label+'.ARMED.actual.json'),{'schema':'root-external-deadline-guard-armed-v1',
                    'machine_id':f.machine,'run_id':f.run_id,'live':str(f.live),'ready_context':self.ready,
                    'pid':pid,'process_creation_filetime_100ns':birth,'birth_source':'GetProcessTimes(GetCurrentProcess)',
                    'state':'WAITING_FOR_ACTUAL_FROZEN_AND_PHASE','game_or_queue_action_sent':False,'deadline_bound':False,
                    'reserve_seconds':1200,'wait_awaiting_seconds':5400,'guard':subject._ttl_pin(guard),
                    'phase':'phase-'+str(index),'armed_at_utc':self.stamp(second)})
                (self.execution/(label+'.stdout.log')).write_text('ROOT_DEADLINE_GUARD_ARMED '+json.dumps(armed)+'\n',encoding='utf8')
                (self.execution/(label+'.stderr.log')).write_bytes(b'')
        self.error = "ValueError('Actual build/validation writers must be closed before prelaunch')"
        f.write_path(self.execution/'ROOT-SERIAL-FAILURE.actual.json',{'machine_id':f.machine,'observed_at_utc':self.stamp(10),
            'error':self.error,'public_started':False,'display_before':None,'no_automatic_replay':True,
            'screen_CAS_attempted':False,'original_handles':processes})
        (self.root_execution/'ROOT-SERIAL.stdout.log').write_text('ACTUAL_READY '+f.run_id+'\n'+
            ''.join('ORIGINAL_WAIT_ACTUAL '+json.dumps(row)+'\n' for row in terminal),encoding='utf8')
        requested = f.root/'not-written.json'
        cap = f.write_path(requested.with_name(requested.name+'.REFUSAL.json'),{'schema':'rrf-parameterized-prelaunch-refusal-v1',
            'machine_id':f.machine,'error':self.error,'receipt_exists':False,'no_automatic_retry':True,'requested_receipt':str(requested)})
        f.write_path(self.execution/'CAPACITY.stdout.log',{'refusal':cap})
        f.write_path(self.execution/'CAPACITY-START.actual.json',{'machine_id':f.machine,
            'derived_source_sha256':'b'*64,'argv':[str(binder),'--output',str(requested)]})
        f.write_path(f.bus/'tasks/fixture-task.json',f.done['task'])
        (f.bus/'events.jsonl').write_text(json.dumps(f.done['event'])+'\n',encoding='utf8')

    @staticmethod
    def stamp(second: int) -> str:
        return '2026-10-23T00:00:'+str(second).zfill(2)+'+00:00'

    def produce(self) -> subject.UnrunBundleReport:
        self.serial += 1
        f = self.fixture
        return subject.build_bundle(argparse.Namespace(previous_live=f.live,keeper_root=f.keeper,
            output=f.root/('serial-result-'+str(self.serial)), task_bus_root=f.bus,
            serial_prelaunch_root_wait=self.root_execution/'ROOT-SERIAL.original-wait.json',
            prelaunch_orchestrator_source=self.source,root_screen_release=Path(f.done_pin['path']),
            next_state=f.root/'new-state',allocator_intent=self.execution/'ALLOCATE.intent.actual.json',
            allocator_process=self.execution/'ALLOCATE.started.actual.json',allocator_exit=self.execution/'ALLOCATE.original-wait.actual.json',
            allocator_stdout=self.stdout,release_sequence=12,done_sequence=12))

    def claim(self, mutation: Callable[[], None] | None = None) -> tuple[Path,list[bool]]:
        bridge = ClosedKeeperAbortedAllocationTests('runTest')
        bridge.fixture = self.fixture
        original = self.fixture.done_pin
        def produce() -> subject.UnrunBundleReport:
            report = self.produce()
            self.fixture.done_pin = report['previous_release']
            return report
        try:
            with patch.object(bridge,'produce',side_effect=produce):
                return bridge.claim(mutation)
        finally:
            self.fixture.done_pin = original

    def test_real_producer_full_reducer_roundtrip_known_waits_and_no_idle(self) -> None:
        report = self.produce()
        cleanup = member(report['validation'],'failure_cleanup')
        self.assertEqual(report['validation']['mode'],'previous-shared-allocated-unrun-prelaunch-orchestrator-failed')
        self.assertEqual(cleanup['original_root_exit_code'],1)
        self.assertEqual(cleanup['original_allocator_exit_code'],0)
        self.assertEqual(cleanup['guard_original_wait_codes'],[1,1])
        self.assertEqual(cleanup['original_keeper_exit_code'],0)
        for key in ('normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass'):
            self.assertIs(cleanup[key],False)
        row = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.assertNotIn('idle_timeout',row)
        self.assertNotIn('allocator_exit_code',row)
        self.assertFalse((self.fixture.live/'allocation-unused-idle-timeout.json').exists())
        self.assertEqual(row,json.loads(json.dumps(row)))

    def test_known_waits_reach_original_writer_lock_and_late_launch_refuses(self) -> None:
        record, observations = self.claim()
        self.assertEqual(observations,[True])
        intent = json_object(json.loads((record/'intent.json').read_bytes()))
        self.assertEqual(member(member(intent,'closure'),'failure_cleanup')['original_allocator_exit_code'],0)

    def test_native_or_public_start_inside_writer_lock_refuses_before_new_intent(self) -> None:
        def launch() -> None:
            (self.fixture.live/'launch-intent.json').write_text('{}',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'host/native/control'):
            self.claim(launch)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())

    def test_wrong_type_birth_returncode_and_original_pin_are_rejected(self) -> None:
        for name,field,bad in (('ALLOCATE.started.actual.json','pid',True),
                ('ALLOCATE.started.actual.json','process_creation_filetime_100ns',134373000000000001),
                ('ALLOCATE.original-wait.actual.json','original_wait_returncode',False),
                ('COLD-GUARD-0.original-wait.actual.json','original_wait_returncode',0),
                ('ROOT-SERIAL-FAILURE.actual.json','public_started',True)):
            path = self.execution/name; raw = path.read_bytes(); row=json_object(json.loads(raw));row[field]=bad
            path.write_text(json.dumps(row),encoding='utf8')
            with self.subTest(name=name,field=field),self.assertRaises(ValueError):self.produce()
            path.write_bytes(raw)
        path=self.root_execution/'ROOT-SERIAL.original-wait.json';raw=path.read_bytes()
        row=json_object(json.loads(raw));row['original_wait_returncode']=True
        path.write_text(json.dumps(row),encoding='utf8')
        with self.assertRaises(ValueError):self.produce()
        path.write_bytes(raw)

    def test_original_guard_source_wait_and_known_pin_drift_inside_lock_refuse(self) -> None:
        def drift() -> None:
            path=self.execution/'ALLOCATE.original-wait.actual.json';path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError):self.claim(drift)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())

    def test_complete_new_serial_producer_parser_and_role_scope_is_strict(self) -> None:
        from mypy import api
        path = Path(subject.__file__)
        tree = ast.parse(path.read_text(encoding='utf8'))
        names = {'SerialObservedProcess','SerialPrelaunchGuardEvidence','SerialUnarmedGuardEvidence','_SerialUnrunResources',
            '_SerialUnrunReducer','_serial_resources','_serial_original','_serial_raw','_serial_child',
            '_serial_argument','_serial_allocator','validate_serial_prelaunch','_serial_required_path',
            'build_serial_prelaunch_bundle','_serial_unarmed_guard','_serial_cleanup_waits',
            '_serial_root_paths','_serial_prepared_phases'}
        nodes: list[ast.stmt] = [node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        self.assertEqual({node.name for node in nodes if isinstance(node,(ast.ClassDef,ast.FunctionDef))},names)
        prelude = '''from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Literal, TypedDict, Protocol, runtime_checkable
import argparse, ast, hashlib, json, math, re
from ck3_mod_acceptance import same_directory_control_peer
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field, strings_field
from ck3_mod_acceptance_unrun import (SCHEMA, PRELAUNCH_KIND, SERIAL_PRELAUNCH_FORMAT, UnrunBundleReport,
    PrelaunchGuardState, _prelaunch_guard_state,
    _timestamp, _integer, _ttl_pin, _ttl_allocator_stdout, _captured_release, _sequence,
    _journal_events, _ttl_recovery_sources, _write, validate_allocated_unrun)
'''
        source = prelude+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))
        repo = path.resolve().parent.parent
        source_path = os.pathsep.join((str(repo/'tools'), str(repo/'ck3_autonomous_player/src')))
        with patch.dict(os.environ, {'MYPYPATH':source_path}):
            stdout,stderr,code = api.run(['--strict','--strict-equality','--follow-imports=silent',
                '--no-incremental','--cache-dir','nul','-c',source])
        self.assertEqual(code,0,stdout+stderr)


class SerialNativeBirthSinglePhasePrelaunchTests(unittest.TestCase):
    """Authored INNER observations exercise the actual single-phase producer chain."""

    def setUp(self) -> None:
        owner = SerialKnownWaitPrelaunchTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fixture = f = owner.fixture
        self.serial = 0
        self.set_phases(('phase-1',))
        for path in owner.execution.glob('COLD-GUARD-1.*'):
            path.unlink()
        failure_path = owner.execution/'ROOT-SERIAL-FAILURE.actual.json'
        failure = json_object(json.loads(failure_path.read_bytes()))
        handles = failure['original_handles']
        if not isinstance(handles, list):
            raise AssertionError('Authored original handles required')
        failure['original_handles'] = handles[:2]
        f.write_path(failure_path, failure)
        start = json_object(json.loads((owner.root_execution/'ROOT-SERIAL.started.json').read_bytes()))
        wait = json_object(json.loads((owner.root_execution/'ROOT-SERIAL.original-wait.json').read_bytes()))
        born = int(datetime.fromisoformat(owner.stamp(0)).timestamp())
        birth = str(116444736000000000 + born*10000000 + 10)
        start['process_creation_filetime_100ns'] = birth
        wait.update({'process_creation_filetime_100ns':birth, 'started_at_utc':owner.stamp(0), 'elapsed_seconds':17.0})
        f.write_path(owner.root_execution/'INNER-STARTED.actual.json', start)
        f.write_path(owner.root_execution/'INNER-ORIGINAL-WAIT.actual.json', wait)
        lines = (owner.root_execution/'ROOT-SERIAL.stdout.log').read_text(encoding='utf8').splitlines()
        (owner.root_execution/'SERIAL.stdout.log').write_text('\n'.join(lines[:3])+'\n', encoding='utf8')
        (owner.root_execution/'SERIAL.stderr.log').write_bytes(b'Authored native-birth root failure\n')

    def set_phases(self, phases: tuple[str, ...]) -> None:
        f, owner = self.fixture, self.owner
        contract = f.write('serial-contract.json', {'gui_phases':[{'id':phase} for phase in phases]})
        f.prepared = f.write('prepared.json', {'contract':json_object(contract)})
        ready = json_object(json.loads((f.live/'ready-context.json').read_bytes()))
        ready['prepared_case'] = json_object(f.prepared)
        owner.ready = f.write_live('ready-context.json', ready)
        f.write_live('allocated-context.json', ready)
        armed_path = owner.execution/'COLD-GUARD-0.ARMED.actual.json'
        armed = json_object(json.loads(armed_path.read_bytes()))
        armed['ready_context'] = json_object(owner.ready)
        ref = f.write_path(armed_path, armed)
        (owner.execution/'COLD-GUARD-0.stdout.log').write_text('ROOT_DEADLINE_GUARD_ARMED '+json.dumps(ref)+'\n', encoding='utf8')

    def produce(self) -> subject.UnrunBundleReport:
        self.serial += 1
        f, owner = self.fixture, self.owner
        return subject.build_bundle(argparse.Namespace(previous_live=f.live, keeper_root=f.keeper,
            output=f.root/('native-single-result-'+str(self.serial)), task_bus_root=f.bus,
            serial_prelaunch_root_wait=owner.root_execution/'INNER-ORIGINAL-WAIT.actual.json',
            prelaunch_orchestrator_source=owner.source, root_screen_release=Path(f.done_pin['path']),
            next_state=f.root/'new-state', allocator_intent=owner.execution/'ALLOCATE.intent.actual.json',
            allocator_process=owner.execution/'ALLOCATE.started.actual.json',
            allocator_exit=owner.execution/'ALLOCATE.original-wait.actual.json',
            allocator_stdout=owner.stdout, release_sequence=12, done_sequence=12))

    def test_actual_producer_reducer_roundtrip_native_root_and_single_guard(self) -> None:
        report = self.produce()
        cleanup = member(report['validation'], 'failure_cleanup')
        self.assertEqual(cleanup['guard_original_wait_codes'], [1])
        self.assertEqual(cleanup['original_root_exit_code'], 1)
        self.assertEqual(cleanup['original_allocator_exit_code'], 0)
        self.assertEqual(cleanup['original_keeper_exit_code'], 0)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(cleanup[key], False)
        row = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.assertEqual(row, json.loads(json.dumps(row)))
        self.assertEqual(Path(text_field(member(row, 'prelaunch_orchestrator_started'), 'path')).name, 'INNER-STARTED.actual.json')
        self.assertEqual(Path(text_field(member(row, 'serial_root_stdout'), 'path')).name, 'SERIAL.stdout.log')
        with patch.object(self.owner, 'produce', side_effect=self.produce):
            record, observations = self.owner.claim()
        self.assertEqual(observations, [True])
        self.assertTrue((record/'intent.json').exists())

    def test_native_birth_wait_fields_types_source_and_pin_drift_reject(self) -> None:
        for name, field, bad in (
                ('INNER-STARTED.actual.json', 'process_creation_filetime_100ns', 134377193820537706),
                ('INNER-STARTED.actual.json', 'process_creation_filetime_100ns', '0134377193820537706'),
                ('INNER-STARTED.actual.json', 'process_creation_filetime_100ns', '18446744073709551616'),
                ('INNER-STARTED.actual.json', 'pid', True),
                ('INNER-ORIGINAL-WAIT.actual.json', 'process_creation_filetime_100ns', '1'),
                ('INNER-ORIGINAL-WAIT.actual.json', 'actual_original_popen_wait', 1),
                ('INNER-ORIGINAL-WAIT.actual.json', 'original_wait_returncode', True),
                ('INNER-ORIGINAL-WAIT.actual.json', 'elapsed_seconds', True),
                ('INNER-ORIGINAL-WAIT.actual.json', 'elapsed_seconds', 1000),
                ('INNER-ORIGINAL-WAIT.actual.json', 'started_at_utc', self.owner.stamp(1))):
            path = self.owner.root_execution/name; raw = path.read_bytes()
            row = json_object(json.loads(raw)); row[field] = bad
            self.fixture.write_path(path, row)
            with self.subTest(name=name, field=field, bad=bad), self.assertRaises(ValueError):
                self.produce()
            path.write_bytes(raw)
        report = self.produce()
        bundle = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.owner.source.write_bytes(self.owner.source.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            subject.validate_serial_prelaunch(bundle, previous=self.fixture.live, keeper=self.fixture.keeper,
                machine=self.fixture.machine, ready_at=datetime.fromisoformat(self.owner.stamp(5)),
                keeper_closed_at=datetime.fromisoformat(self.owner.stamp(15)))

    def test_missing_extra_reordered_or_duplicate_prepared_guard_is_not_tolerated(self) -> None:
        for phases in (('phase-1', 'phase-2'), ('phase-2',), ('phase-1', 'phase-1')):
            self.set_phases(phases)
            with self.subTest(phases=phases), self.assertRaises(ValueError):
                self.produce()
        self.set_phases(('phase-1',))
        extra = self.owner.execution/'COLD-GUARD-1.intent.actual.json'
        extra.write_text('{}', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'Prepared phases'):
            self.produce()


class RegistrySupportRecoveryTests(unittest.TestCase):
    """Actual producer/reducer/lock with authored, unselected registry inputs."""

    def setUp(self) -> None:
        owner = SerialNativeBirthSinglePhasePrelaunchTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fixture = f = owner.fixture
        self.base = owner.owner
        self.repo = f.source.resolve(); self.repo.mkdir(parents=True)
        self.blobs: dict[str, bytes] = {}
        self.current_registry: dict[str, bytes] = {}
        prepare = self.repo/'tools/ck3_mod_acceptance_prepare.py'
        self.prepare = f.write_path(prepare, {'authored':'same frozen prepare'})
        files = member(f.freeze, 'files')
        manifest = f.write('predecessor-runtime-manifest.json',
            {'source_commit':self.base.commit, 'machine_id':f.machine})
        f.freeze['runtime_manifest'] = json_object(manifest)
        files[manifest['path']] = {'bytes':manifest['bytes'], 'sha256':manifest['sha256']}
        files[str(prepare)] = {'bytes':self.prepare['bytes'], 'sha256':self.prepare['sha256']}
        for relative in ('tools/ck3_mod_acceptance_unrun.py', 'tools/ck3_mod_acceptance_allocate.py'):
            path = self.repo/relative
            old = b'authored original recovery reader\n'
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(old)
            ref = subject._ttl_pin(path)
            files[str(path)] = {'bytes':ref['bytes'], 'sha256':ref['sha256']}
            self.blobs[relative] = old
            path.write_bytes(b'authored current recovery reader\n')
        for relative in subject._registry_support_paths():
            before: JsonObject = {'schema':'ck3-xqol-original-followup-case-v1',
                'case':Path(relative).stem.removeprefix('xqol_'), 'original_budgets':{'timeout':300},
                'fixture_files':['unchanged.fixture'], 'full_product_pass_from_cell':False,
                'support_files':{'../ck3_mod_acceptance_prepare.py':{'bytes':1,'sha256':'a'*64},
                    'unchanged.py':{'bytes':2,'sha256':'b'*64}}}
            path = self.repo/relative; path.parent.mkdir(parents=True, exist_ok=True)
            old = json.dumps(before).encode()
            path.write_bytes(old); ref = subject._ttl_pin(path)
            files[str(path)] = {'bytes':ref['bytes'], 'sha256':ref['sha256']}
            self.blobs[relative] = old
            member(before, 'support_files')['../ck3_mod_acceptance_prepare.py'] = {
                'bytes':self.prepare['bytes'], 'sha256':self.prepare['sha256']}
            raw = json.dumps(before).encode(); path.write_bytes(raw)
            self.current_registry[relative] = raw
        unknown = self.repo/'tools/ck3_mod_acceptance_cases/xqol_unknown.json'
        unknown.write_bytes(b'{"fixture":"unknown is never waived"}')
        unknown_ref = subject._ttl_pin(unknown)
        files[str(unknown)] = {'bytes':unknown_ref['bytes'], 'sha256':unknown_ref['sha256']}
        adapter = f.write_path(self.repo/'tools/ck3_mod_acceptance_cases/generic_product_adapter.py',
            {'fixture':'selected generic adapter, never executed'})
        contract = f.write('serial-contract.json', {'schema':'ck3-mod-acceptance-product-case-v1',
            'product':'living-artifacts', 'case_id':'cold_reload', 'gui_phases':[{'id':'phase-1'}]})
        f.prepared = f.write('prepared.json', {'schema':'ck3-mod-acceptance-prepared-case-v1',
            'product':'living-artifacts', 'case':'cold_reload', 'contract':json_object(contract),
            'runtime_manifest':f.freeze['runtime_manifest'], 'adapter':json_object(adapter)})
        for ref in (adapter, contract, f.prepared):
            files[ref['path']] = {'bytes':ref['bytes'], 'sha256':ref['sha256']}
        f.freeze['cell'] = 'cold_reload'
        self.refresh_context()

        def git(command: list[str], *, capture_output: bool, check: bool) -> subprocess.CompletedProcess[bytes]:
            if (len(command) != 6 or command[:4] != ['git','-C',str(self.repo),'cat-file']
                    or command[4] not in ('-s','blob') or not capture_output or not check):
                raise AssertionError('Only authored exact immutable Git blob observations allowed')
            commit, relative = command[5].split(':', 1)
            if commit != self.base.commit:
                raise AssertionError('Original fixture commit differs')
            raw = self.blobs[relative]
            return subprocess.CompletedProcess(command, 0,
                stdout=str(len(raw)).encode() if command[4] == '-s' else raw)
        self.git_patch = patch.object(subprocess, 'run', side_effect=git)
        self.git_patch.start(); self.addCleanup(self.git_patch.stop)

    def refresh_context(self) -> None:
        f, base = self.fixture, self.base
        frozen = f.write_live('frozen-argv.json', f.freeze)
        ready = json_object(json.loads((f.live/'ready-context.json').read_bytes()))
        ready.update({'schema':'ck3-mod-acceptance-run-context-v1',
            'prepared_case':json_object(f.prepared), 'case':'cold_reload', 'frozen_argv':json_object(frozen)})
        base.ready = f.write_live('ready-context.json', ready)
        f.write_live('allocated-context.json', ready)
        armed_path = base.execution/'COLD-GUARD-0.ARMED.actual.json'
        armed = json_object(json.loads(armed_path.read_bytes())); armed['ready_context'] = json_object(base.ready)
        ref = f.write_path(armed_path, armed)
        (base.execution/'COLD-GUARD-0.stdout.log').write_text('ROOT_DEADLINE_GUARD_ARMED '+json.dumps(ref)+'\n', encoding='utf8')

    def test_v2_real_producer_full_reducer_roundtrip_and_original_writer_lock(self) -> None:
        report = self.owner.produce()
        bundle = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        evolution = member(bundle, 'recovery_reader_evolution')
        self.assertEqual(evolution['schema'], 'ck3-prelaunch-recovery-reader-evolution-v2')
        changes = evolution['registry_support_changes']
        if not isinstance(changes, list): raise AssertionError('Typed changes required')
        self.assertEqual(len(changes), 7)
        self.assertEqual(bundle, json.loads(json.dumps(bundle)))
        for raw in changes:
            row = json_object(raw)
            self.assertNotEqual(member(row, 'original_snapshot')['sha256'], member(row, 'current_source')['sha256'])
        self.assertFalse(member(report['validation'], 'failure_cleanup')['business_pass'])
        with patch.object(self.base, 'produce', side_effect=self.owner.produce):
            record, observations = self.base.claim()
        self.assertEqual(observations, [True]); self.assertTrue((record/'intent.json').exists())

    def test_old_v1_two_reader_branch_and_registry_only_v2_remain_explicit(self) -> None:
        for relative, raw in self.current_registry.items():
            (self.repo/relative).write_bytes(self.blobs[relative])
        first = self.owner.produce()
        old = member(json_object(json.loads(Path(first['bundle']['path']).read_bytes())), 'recovery_reader_evolution')
        self.assertEqual(old['schema'], 'ck3-prelaunch-recovery-reader-evolution-v1')
        self.assertNotIn('registry_support_changes', old)
        for relative, raw in self.current_registry.items(): (self.repo/relative).write_bytes(raw)
        for relative in ('tools/ck3_mod_acceptance_unrun.py', 'tools/ck3_mod_acceptance_allocate.py'):
            (self.repo/relative).write_bytes(self.blobs[relative])
        second = self.owner.produce()
        new = member(json_object(json.loads(Path(second['bundle']['path']).read_bytes())), 'recovery_reader_evolution')
        self.assertEqual(new['changed_recovery_sources'], [])
        self.assertEqual(new['schema'], 'ck3-prelaunch-recovery-reader-evolution-v2')

    def test_other_fields_types_unknown_registry_and_unfrozen_prepare_are_rejected(self) -> None:
        relative = subject._registry_support_paths()[0]; path = self.repo/relative
        raw = path.read_bytes()
        mutations: list[tuple[str, JsonValue]] = [('schema','wrong'),('extra',False),('full_product_pass_from_cell',0),
            ('original_budgets',{'timeout':300.0}),('fixture_files',['changed.fixture']),
            ('support_files',{'../ck3_mod_acceptance_prepare.py':{'bytes':True,'sha256':self.prepare['sha256']}})]
        for field, bad in mutations:
            row = json_object(json.loads(raw)); row[field] = bad; self.fixture.write_path(path, row)
            with self.subTest(field=field), self.assertRaises(ValueError): self.owner.produce()
            path.write_bytes(raw)
        path.write_bytes(raw[:-1]+b',"schema":"ck3-xqol-original-followup-case-v1"}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.owner.produce()
        path.write_bytes(raw)
        unknown = self.repo/'tools/ck3_mod_acceptance_cases/xqol_unknown.json'
        original_unknown = unknown.read_bytes(); unknown.write_bytes(b'changed unknown registry')
        with self.assertRaisesRegex(ValueError, 'Immutable original input changed'): self.owner.produce()
        unknown.write_bytes(original_unknown)
        prepare = Path(self.prepare['path']); prepare.write_bytes(prepare.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'frozen prepare'): self.owner.produce()

    def test_active_xqol_actual_launch_and_false_original_git_blob_reject(self) -> None:
        ready_path = self.fixture.live/'ready-context.json'; original = ready_path.read_bytes()
        ready = json_object(json.loads(original)); ready['product'] = 'xqol'; self.fixture.write_path(ready_path, ready)
        with self.assertRaisesRegex(ValueError, 'selected case'): self.owner.produce()
        ready_path.write_bytes(original)
        launch = self.fixture.live/'launch-intent.json'; launch.write_text('{}', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'launch/native/control/Save'): self.owner.produce()
        launch.unlink()
        relative = subject._registry_support_paths()[0]
        self.blobs[relative] = self.blobs[relative]+b' '
        with self.assertRaisesRegex(ValueError, 'Git blob size'): self.owner.produce()

    def test_registry_pin_drift_and_unknown_evolution_reject_inside_original_lock(self) -> None:
        def mutate() -> None:
            path = self.repo/subject._registry_support_paths()[0]
            row = json_object(json.loads(path.read_bytes())); row['fixture_files'] = ['late mutation']
            self.fixture.write_path(path, row)
        with patch.object(self.base, 'produce', side_effect=self.owner.produce):
            with self.assertRaises(ValueError): self.base.claim(mutate)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())

    def test_original_resource_waits_precede_registry_exception_and_unknown_schema_refuses(self) -> None:
        path = self.base.execution/'COLD-GUARD-0.original-wait.actual.json'
        original = path.read_bytes(); row = json_object(json.loads(original)); row['original_wait_returncode'] = 0
        self.fixture.write_path(path, row)
        with patch.object(subject, '_recovery_input_validation', wraps=subject._recovery_input_validation) as observe:
            with self.assertRaises(ValueError): self.owner.produce()
            observe.assert_not_called()
        path.write_bytes(original)
        report = self.owner.produce()
        bundle = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        member(bundle, 'recovery_reader_evolution')['schema'] = 'unknown-version'
        with self.assertRaisesRegex(ValueError, 'evolution differs'):
            subject._recovery_input_validation(self.fixture.live, self.fixture.freeze,
                Path(report['bundle']['path']), bundle, registry_support=True)

    def test_complete_typed_registry_evolution_scope_is_strict(self) -> None:
        from mypy import api
        path = Path(subject.__file__); tree = ast.parse(path.read_text(encoding='utf8'))
        names = {'TTLRecoverySource','TTLRecoveryEvolutionFields','TTLReaderEvolution','RecoveryContentPin',
            'RegistrySupportChange','RegistrySelectedCase','TTLRegistrySupportEvolution',
            '_registry_support_paths','_registry_json_pairs','_registry_json','_registry_content_pin',
            '_recovery_git_snapshot','_registry_selected_case','_registry_support_change',
            '_ttl_recovery_sources','_recovery_input_validation'}
        nodes: list[ast.stmt] = [node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names
            or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TTLRecoveryEvolution' for t in node.targets)]
        self.assertEqual({n.name for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef))}, names)
        prelude = '''from __future__ import annotations
from pathlib import Path
from collections.abc import Mapping
from typing import Literal, TypedDict
import hashlib, json, re, subprocess
from ck3_mod_acceptance import same_directory_control_peer
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field
from ck3_mod_acceptance_unrun import _integer, _ttl_pin, _pinned_object
'''
        source = prelude+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))
        repo = path.resolve().parent.parent
        with patch.dict(os.environ, {'MYPYPATH':os.pathsep.join((str(repo/'tools'), str(repo/'ck3_autonomous_player/src')))}):
            stdout, stderr, code = api.run(['--strict','--strict-equality','--follow-imports=silent',
                '--no-incremental','--cache-dir','nul','-c',source])
        self.assertEqual(code, 0, stdout+stderr)


class SerialCapturedKnownWaitPrelaunchTests(unittest.TestCase):
    """Armed guards retain the earlier CAS task and later administrative DONE."""

    def setUp(self) -> None:
        owner = SerialKnownWaitPrelaunchTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fixture = f = owner.fixture
        self.serial = 0
        cas = deepcopy(f.done)
        member(cas, 'event')['sequence'] = 11
        member(cas, 'task')['last_sequence'] = 11
        self.cas = f.write('original-screen-release.json', cas)
        (f.bus/'events.jsonl').write_text(json.dumps(cas['event'])+'\n'+json.dumps(f.done['event'])+'\n', encoding='utf8')

    def args(self) -> argparse.Namespace:
        self.serial += 1
        f, owner = self.fixture, self.owner
        return argparse.Namespace(previous_live=f.live, keeper_root=f.keeper,
            output=f.root/('captured-result-'+str(self.serial)), task_bus_root=f.bus,
            serial_prelaunch_root_wait=owner.root_execution/'ROOT-SERIAL.original-wait.json',
            prelaunch_orchestrator_source=owner.source, root_screen_release=Path(self.cas['path']),
            admin_release=Path(f.done_pin['path']), next_state=f.root/'new-state',
            allocator_intent=owner.execution/'ALLOCATE.intent.actual.json',
            allocator_process=owner.execution/'ALLOCATE.started.actual.json',
            allocator_exit=owner.execution/'ALLOCATE.original-wait.actual.json',
            allocator_stdout=owner.stdout, release_sequence=11, done_sequence=12)

    def produce(self) -> subject.UnrunBundleReport:
        return subject.build_bundle(self.args())

    def test_armed_roundtrip_keeps_original_release_task_and_admin_done(self) -> None:
        report = self.produce()
        cleanup = member(report['validation'], 'failure_cleanup')
        self.assertEqual(cleanup['guard_original_wait_codes'], [1, 1])
        self.assertIs(cleanup['business_pass'], False)
        row = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.assertEqual(row['prelaunch_guard_state'], 'armed-cancelled')
        self.assertEqual(row['CAS_release'], self.cas)
        self.assertEqual(row['serial_release_original'], self.cas)
        self.assertEqual(row['admin_done'], self.fixture.done_pin)
        self.assertEqual(row['serial_admin_original'], self.fixture.done_pin)
        self.assertEqual(row, json.loads(json.dumps(row)))
        self.assertFalse(list(Path(report['bundle']['path']).parent.glob('*.canonical.json')))

    def test_original_admin_reaches_original_writer_lock(self) -> None:
        with patch.object(self.owner, 'produce', side_effect=self.produce):
            record, observations = self.owner.claim()
        self.assertEqual(observations, [True])
        intent = json_object(json.loads((record/'intent.json').read_bytes()))
        self.assertEqual(member(member(intent, 'closure'), 'failure_cleanup')['guard_original_wait_codes'], [1, 1])

    def test_armed_original_task_types_event_and_resources_stay_journal_bound(self) -> None:
        changes: tuple[tuple[str, str, JsonValue], ...] = (
            ('task', 'last_sequence', 12), ('task', 'last_sequence', True),
            ('task', 'resources', ['ck3-screen:acquired']), ('task', 'task_id', 'different-task'),
            ('event', 'sequence', 11.0), ('event', 'summary', 'different journal event'))
        path = Path(self.cas['path']); raw = path.read_bytes()
        for section, key, bad in changes:
            row = json_object(json.loads(raw)); member(row, section)[key] = bad
            path.write_text(json.dumps(row), encoding='utf8')
            with self.subTest(section=section, key=key), self.assertRaises(ValueError): self.produce()
            path.write_bytes(raw)
        args = self.args(); args.admin_release = Path(self.cas['path'])
        with self.assertRaisesRegex(ValueError, 'captured release differs'): subject.build_bundle(args)
        args = self.args(); args.admin_release = str(self.fixture.done_pin['path'])
        with self.assertRaisesRegex(ValueError, 'path argument required: admin_release'): subject.build_bundle(args)

    def test_original_admin_drift_inside_writer_lock_refuses(self) -> None:
        def drift() -> None:
            path = Path(self.fixture.done_pin['path']); path.write_bytes(path.read_bytes()+b' ')
        with patch.object(self.owner, 'produce', side_effect=self.produce):
            with self.assertRaises(ValueError): self.owner.claim(drift)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())

    def test_missing_admin_does_not_reconstruct_an_earlier_task_from_later_done(self) -> None:
        args = self.args(); del args.admin_release
        with self.assertRaisesRegex(ValueError, 'screen release differs'): subject.build_bundle(args)


class SerialUnarmedKnownWaitPrelaunchTests(unittest.TestCase):
    """Authored R39-shaped originals enter the shared producer and real lock."""

    def setUp(self) -> None:
        owner = SerialKnownWaitPrelaunchTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fixture = f = owner.fixture
        self.serial = 0
        self.execution = e = owner.execution
        contract = f.write('first-phase-contract.json', {'gui_phases':[{'id':'phase-1'}]})
        prepared = json_object(json.loads(Path(f.prepared['path']).read_bytes()))
        prepared['contract'] = json_object(contract)
        f.prepared = f.write_path(Path(f.prepared['path']), prepared)
        ready = json_object(json.loads((f.live/'ready-context.json').read_bytes()))
        ready['prepared_case'] = json_object(f.prepared)
        owner.ready = f.write_live('ready-context.json', ready)
        f.write_live('allocated-context.json', ready)
        label = 'CORE-GUARD-0'
        for suffix in ('.intent.actual.json', '.started.actual.json', '.original-wait.actual.json'):
            row = json_object(json.loads((e/('COLD-GUARD-0'+suffix)).read_bytes()))
            if suffix == '.intent.actual.json':
                argv = strings_field(row, 'argv')
                argv[argv.index('--wait-awaiting-seconds')+1] = '7200'
                argv[argv.index('--armed')+1] = str(e/(label+'.ARMED.actual.json'))
                argv[argv.index('--output')+1] = str(e/(label+'.actual.json'))
                row['argv'] = [value for value in argv]
            f.write_path(e/(label+suffix), row)
        static = json_object(json.loads((e/'STATIC-INPUTS-PRECOMPILED.actual.json').read_bytes()))
        guard = member(static, 'guard_original')['path']
        (e/(label+'.stdout.log')).write_bytes(b'')
        (e/(label+'.stderr.log')).write_text('File "'+str(guard)+'", line 1, in main\n'
            'ValueError: Reviewed exact run/phase and the fixed1200-second reserve required\n', encoding='utf8')
        failure = json_object(json.loads((e/'ROOT-SERIAL-FAILURE.actual.json').read_bytes()))
        failure['error'] = repr(RuntimeError('Original child ended before '+str(e/(label+'.ARMED.actual.json'))))
        handles = failure['original_handles']
        if not isinstance(handles, list):
            raise AssertionError('Authored original handle list required')
        failure['original_handles'] = [json_object(handles[0]), {**json_object(handles[1]), 'label':label}]
        f.write_path(e/'ROOT-SERIAL-FAILURE.actual.json', failure)
        lines = (owner.root_execution/'ROOT-SERIAL.stdout.log').read_text(encoding='utf8').splitlines()
        (owner.root_execution/'ROOT-SERIAL.stdout.log').write_text('\n'.join(
            line.replace('COLD-GUARD-0', label) for line in lines if 'COLD-GUARD-1' not in line)+'\n', encoding='utf8')
        for path in (*e.glob('COLD-GUARD-*'), *e.glob('CAPACITY*')):
            path.unlink()
        cas = deepcopy(f.done)
        member(cas, 'event')['sequence'] = 11
        member(cas, 'task')['last_sequence'] = 11
        self.cas = f.write('original-screen-release.json', cas)
        (f.bus/'events.jsonl').write_text(json.dumps(cas['event'])+'\n'+json.dumps(f.done['event'])+'\n', encoding='utf8')

    def args(self) -> argparse.Namespace:
        self.serial += 1
        f, owner = self.fixture, self.owner
        return argparse.Namespace(previous_live=f.live, keeper_root=f.keeper,
            output=f.root/('unarmed-result-'+str(self.serial)), task_bus_root=f.bus,
            serial_prelaunch_root_wait=owner.root_execution/'ROOT-SERIAL.original-wait.json',
            prelaunch_orchestrator_source=owner.source, root_screen_release=Path(self.cas['path']),
            admin_release=Path(f.done_pin['path']), next_state=f.root/'new-state',
            allocator_intent=self.execution/'ALLOCATE.intent.actual.json',
            allocator_process=self.execution/'ALLOCATE.started.actual.json',
            allocator_exit=self.execution/'ALLOCATE.original-wait.actual.json',
            allocator_stdout=owner.stdout, release_sequence=11, done_sequence=12)

    def produce(self) -> subject.UnrunBundleReport:
        return subject.build_bundle(self.args())

    def claim(self, mutation: Callable[[], None] | None = None) -> tuple[Path, list[bool]]:
        with patch.object(self.owner, 'produce', side_effect=self.produce):
            return self.owner.claim(mutation)

    def test_real_producer_roundtrip_retains_one_known_guard_wait_and_original_releases(self) -> None:
        report = self.produce()
        cleanup = member(report['validation'], 'failure_cleanup')
        self.assertEqual(cleanup['guard_original_wait_codes'], [1])
        self.assertEqual(cleanup['original_root_exit_code'], 1)
        self.assertEqual(cleanup['original_allocator_exit_code'], 0)
        self.assertEqual(cleanup['original_keeper_exit_code'], 0)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(cleanup[key], False)
        row = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.assertEqual(row, json.loads(json.dumps(row)))
        self.assertEqual(row['prelaunch_guard_state'], 'failed-before-armed')
        self.assertEqual(row['CAS_release'], self.cas)
        self.assertEqual(row['admin_done'], self.fixture.done_pin)
        self.assertNotIn('idle_timeout', row)
        self.assertNotIn('serial_capacity_start', row)
        self.assertFalse((self.fixture.live/'allocation-unused-idle-timeout.json').exists())

    def test_actual_allocator_revalidates_producer_under_original_writer_lock(self) -> None:
        record, observations = self.claim()
        self.assertEqual(observations, [True])
        intent = json_object(json.loads((record/'intent.json').read_bytes()))
        self.assertEqual(member(member(intent, 'closure'), 'failure_cleanup')['guard_original_wait_codes'], [1])
        self.assertIs(intent['business_pass'], False)

    def test_late_native_launch_and_original_wait_drift_inside_lock_refuse(self) -> None:
        def drift() -> None:
            path = self.execution/'CORE-GUARD-0.original-wait.actual.json'
            path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError): self.claim(drift)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())
        def launch() -> None:
            (self.fixture.live/'launch-intent.json').write_text('{}', encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'host/native/control'): self.claim(launch)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())

    def test_wrong_native_identity_types_waits_missing_fields_and_argv_refuse(self) -> None:
        changes: tuple[tuple[str, str, JsonValue], ...] = (
            ('CORE-GUARD-0.started.actual.json', 'pid', True),
            ('CORE-GUARD-0.started.actual.json', 'process_creation_filetime_100ns', 134373000000000001),
            ('CORE-GUARD-0.original-wait.actual.json', 'original_wait_returncode', False),
            ('CORE-GUARD-0.original-wait.actual.json', 'original_wait_returncode', 0),
            ('CORE-GUARD-0.original-wait.actual.json', 'pid', 90007),
            ('ROOT-SERIAL-FAILURE.actual.json', 'public_started', True))
        for name, key, bad in changes:
            path = self.execution/name; raw = path.read_bytes()
            row = json_object(json.loads(raw)); row[key] = bad
            path.write_text(json.dumps(row), encoding='utf8')
            with self.subTest(name=name, key=key), self.assertRaises(ValueError): self.produce()
            path.write_bytes(raw)
        path = self.execution/'CORE-GUARD-0.intent.actual.json'; raw = path.read_bytes()
        row = json_object(json.loads(raw)); row.pop('source_commit')
        path.write_text(json.dumps(row), encoding='utf8')
        with self.assertRaises(ValueError): self.produce()
        path.write_bytes(raw)
        row = json_object(json.loads(raw)); argv = strings_field(row, 'argv')
        argv[argv.index('--wait-awaiting-seconds')+1] = '5400'; row['argv'] = [value for value in argv]
        path.write_text(json.dumps(row), encoding='utf8')
        with self.assertRaises(ValueError): self.produce()
        path.write_bytes(raw)

    def test_later_guard_capacity_public_and_armed_claims_refuse(self) -> None:
        names = ('CORE-GUARD-0.ARMED.actual.json', 'CORE-GUARD-0.CANCEL.actual.json',
            'CORE-GUARD-0.actual.json', 'CORE-GUARD-1.intent.actual.json',
            'COLD-GUARD-0.intent.actual.json', 'CAPACITY-START.actual.json',
            'PUBLIC-RUN.intent.actual.json', 'DISPLAY-MODE.actual.json', 'STEAM-OFFLINE.prelaunch.actual.json')
        for name in names:
            path = self.execution/name; path.write_text('{}', encoding='utf8')
            with self.subTest(name=name), self.assertRaises(ValueError): self.produce()
            path.unlink()

    def test_source_diagnostic_and_crossed_original_release_refuse(self) -> None:
        static = json_object(json.loads((self.execution/'STATIC-INPUTS-PRECOMPILED.actual.json').read_bytes()))
        guard = Path(text_field(member(static, 'guard_original'), 'path'))
        original = guard.read_bytes(); guard.write_bytes(original+b'\n')
        with self.assertRaises(ValueError): self.produce()
        guard.write_bytes(original)
        path = self.execution/'CORE-GUARD-0.stderr.log'; raw = path.read_bytes()
        path.write_bytes(b'unrelated startup error\n')
        with self.assertRaises(ValueError): self.produce()
        path.write_bytes(raw)
        args = self.args(); args.root_screen_release = Path(self.fixture.done_pin['path'])
        with self.assertRaises(ValueError): subject.build_bundle(args)
        report = self.produce(); close = Path(report['bundle']['path'])
        row = json_object(json.loads(close.read_bytes())); row['prelaunch_guard_state'] = 'armed-cancelled'
        self.fixture.write_path(close, row)
        from ck3_mod_acceptance_allocate import _PrelaunchUnrunAdmissionReducer
        reducer: object = subject.validate_allocated_unrun
        if not isinstance(reducer, _PrelaunchUnrunAdmissionReducer):
            raise AssertionError('Actual shared prelaunch reducer unavailable')
        with self.assertRaises(ValueError):
            reducer(self.fixture.live, self.fixture.freeze, close,
                self.fixture.keeper, self.fixture.done, self.fixture.packet, next_state=self.fixture.root/'new-state')

    def test_original_keeper_known_wait_rejects_bool_float_null_and_failure(self) -> None:
        path = self.fixture.live/'keeper-actual-parent-exit.json'; raw = path.read_bytes()
        for value in (False, 0.0, None, 1):
            row = json_object(json.loads(raw)); row['keeper_actual_exit_code'] = value
            self.fixture.write_path(path, row)
            with self.subTest(value=value), self.assertRaises(ValueError): self.produce()
        path.write_bytes(raw)


class SerialColdUnarmedKnownWaitPrelaunchTests(unittest.TestCase):
    """R43-shaped authored observations use the real producer/reducer and lock."""

    def setUp(self) -> None:
        owner = SerialUnarmedKnownWaitPrelaunchTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fixture = f = owner.fixture
        self.execution = e = owner.execution
        self.guard_source = '''def main() -> int:
    if (live.name != args.run_id or not args.phase.replace('-', '').isalnum() or args.reserve_seconds != 1200
            or not 0 < args.wait_awaiting_seconds <= 5400):
        raise ValueError('Reviewed exact run/phase and the fixed1200-second reserve required')
    if (not isinstance(ready, dict) or ready.get('schema') != 'ck3-mod-acceptance-run-context-v1' or ready.get('run_id') != args.run_id
            or Path(str(ready.get('run_dir', ''))).resolve() != live
            or ready.get('product') != 'living-artifacts' or ready.get('case') != 'core'):
        raise ValueError('Actual allocated ready-context crossed exact live/run/product/case')
    return 0
'''
        contract = f.write('first-phase-contract.json', {'schema':'ck3-mod-acceptance-product-case-v1',
            'product':'living-artifacts', 'case_id':'cold_reload', 'gui_phases':[{'id':'phase-1'}]})
        prepared = json_object(json.loads(Path(f.prepared['path']).read_bytes()))
        prepared.update({'schema':'ck3-mod-acceptance-prepared-case-v1', 'product':'living-artifacts',
            'case':'cold_reload', 'contract':json_object(contract)})
        f.prepared = f.write_path(Path(f.prepared['path']), prepared)
        ready = json_object(json.loads((f.live/'ready-context.json').read_bytes()))
        ready.update({'schema':'ck3-mod-acceptance-run-context-v1', 'case':'cold_reload',
            'prepared_case':json_object(f.prepared)})
        f.write_live('ready-context.json', ready); f.write_live('allocated-context.json', ready)
        for suffix in ('.intent.actual.json', '.started.actual.json', '.original-wait.actual.json'):
            original = e/('CORE-GUARD-0'+suffix)
            row = json_object(json.loads(original.read_bytes()))
            if suffix == '.intent.actual.json':
                argv = strings_field(row, 'argv')
                argv[argv.index('--wait-awaiting-seconds')+1] = '5400'
                argv[argv.index('--armed')+1] = str(e/'COLD-GUARD-0.ARMED.actual.json')
                argv[argv.index('--output')+1] = str(e/'COLD-GUARD-0.actual.json')
                row['argv'] = [value for value in argv]
            f.write_path(e/('COLD-GUARD-0'+suffix), row); original.unlink()
        for path in e.glob('CORE-GUARD-0.*'):
            path.unlink()
        self.set_guard(self.guard_source)
        (e/'COLD-GUARD-0.stdout.log').write_bytes(b'')
        static = json_object(json.loads((e/'STATIC-INPUTS-PRECOMPILED.actual.json').read_bytes()))
        guard = text_field(member(static, 'guard_original'), 'path')
        parsed = ast.parse(self.guard_source)
        raises = [node for node in ast.walk(parsed) if isinstance(node, ast.Raise)]
        (e/'COLD-GUARD-0.stderr.log').write_text('File "'+guard+'", line '+str(raises[-1].lineno)+', in main\n'
            "    raise ValueError('Actual allocated ready-context crossed exact live/run/product/case')\n"
            'ValueError: Actual allocated ready-context crossed exact live/run/product/case\n', encoding='utf8')
        failure = json_object(json.loads((e/'ROOT-SERIAL-FAILURE.actual.json').read_bytes()))
        failure['error'] = repr(RuntimeError('Original child ended before '+str(e/'COLD-GUARD-0.ARMED.actual.json')))
        handles = failure['original_handles']
        if not isinstance(handles, list):
            raise AssertionError('Authored original handle list required')
        failure['original_handles'] = [json_object(handles[0]), {**json_object(handles[1]), 'label':'COLD-GUARD-0'}]
        f.write_path(e/'ROOT-SERIAL-FAILURE.actual.json', failure)
        stdout = owner.owner.root_execution/'ROOT-SERIAL.stdout.log'
        stdout.write_text(stdout.read_text(encoding='utf8').replace('CORE-GUARD-0', 'COLD-GUARD-0'), encoding='utf8')

    def set_guard(self, raw: str) -> None:
        f, e = self.fixture, self.execution
        static = json_object(json.loads((e/'STATIC-INPUTS-PRECOMPILED.actual.json').read_bytes()))
        guard = Path(text_field(member(static, 'guard_original'), 'path'))
        guard.write_text(raw, encoding='utf8')
        invocation = 'exec(compile('+repr(raw)+','+repr(str(guard))+',"exec"))'
        static['guard_original'] = json_object(subject._ttl_pin(guard))
        static['guard_code_sha256'] = hashlib.sha256(invocation.encode()).hexdigest()
        f.write_path(e/'STATIC-INPUTS-PRECOMPILED.actual.json', static)
        path = e/'COLD-GUARD-0.intent.actual.json'
        row = json_object(json.loads(path.read_bytes())); argv = strings_field(row, 'argv')
        argv[5] = invocation; row['argv'] = [value for value in argv]
        f.write_path(path, row)

    def test_cold_producer_consumer_serialization_and_real_writer_lock_preserve_failure(self) -> None:
        report = self.owner.produce()
        row = json_object(json.loads(Path(report['bundle']['path']).read_bytes()))
        self.assertEqual(row, json.loads(json.dumps(row)))
        self.assertEqual(row['prelaunch_guard_state'], 'failed-before-armed')
        guards = row['serial_guards']
        self.assertIsInstance(guards, list)
        if not isinstance(guards, list):
            raise AssertionError('Actual typed guard rows required')
        self.assertEqual(json_object(guards[0])['label'], 'COLD-GUARD-0')
        cleanup = member(report['validation'], 'failure_cleanup')
        self.assertEqual(cleanup['guard_original_wait_codes'], [1])
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'):
            self.assertIs(cleanup[key], False)
        record, observations = self.owner.claim()
        self.assertTrue((record/'intent.json').is_file())
        self.assertEqual(observations, [True])

    def test_cold_rejects_wrong_supported_wait_first_phase_diagnostic_frame_and_typed_wait(self) -> None:
        path = self.execution/'COLD-GUARD-0.intent.actual.json'; raw = path.read_bytes()
        for option, bad in (('--wait-awaiting-seconds', '7020'), ('--wait-awaiting-seconds', '0'), ('--phase', 'phase-2')):
            row = json_object(json.loads(raw)); argv = strings_field(row, 'argv')
            argv[argv.index(option)+1] = bad; row['argv'] = [value for value in argv]
            self.fixture.write_path(path, row)
            with self.subTest(option=option, bad=bad), self.assertRaises(ValueError): self.owner.produce()
        path.write_bytes(raw)
        path = self.execution/'COLD-GUARD-0.stderr.log'; raw = path.read_bytes()
        for bad_stderr in (b'ValueError: unrelated failure\n', raw.replace(b', in main', b', in unrelated')):
            path.write_bytes(bad_stderr)
            with self.subTest(stderr=bad_stderr), self.assertRaises(ValueError): self.owner.produce()
        path.write_bytes(raw)
        path = self.execution/'COLD-GUARD-0.original-wait.actual.json'; raw = path.read_bytes()
        for bad_code in (False, 1.0, 0):
            row = json_object(json.loads(raw)); row['original_wait_returncode'] = bad_code
            self.fixture.write_path(path, row)
            with self.subTest(code=bad_code), self.assertRaises(ValueError): self.owner.produce()
        path.write_bytes(raw)

    def test_cold_rejects_rebound_source_semantics_and_non_cold_prepared_contract(self) -> None:
        for raw in (self.guard_source.replace("ready.get('case') != 'core'", "ready.get('case') != 'cold_reload'"),
                self.guard_source.replace('<= 5400', '<= 7200')):
            self.set_guard(raw)
            with self.subTest(source=raw), self.assertRaisesRegex(ValueError, 'refusal AST'): self.owner.produce()
        self.set_guard(self.guard_source)
        path = Path(self.fixture.prepared['path']); original = path.read_bytes()
        prepared = json_object(json.loads(original)); prepared['case'] = 'core'
        ref = self.fixture.write_path(path, prepared)
        for name in ('ready-context.json', 'allocated-context.json'):
            row = json_object(json.loads((self.fixture.live/name).read_bytes()))
            row['prepared_case'] = json_object(ref); self.fixture.write_live(name, row)
        with self.assertRaisesRegex(ValueError, 'prepared cold_reload'): self.owner.produce()

    def test_cold_rejects_later_guard_capacity_or_original_wait_drift_in_writer_lock(self) -> None:
        for name in ('CORE-GUARD-0.intent.actual.json', 'COLD-GUARD-1.intent.actual.json', 'CAPACITY-START.actual.json'):
            path = self.execution/name; path.write_text('{}', encoding='utf8')
            with self.subTest(name=name), self.assertRaises(ValueError): self.owner.produce()
            path.unlink()
        def drift() -> None:
            path = self.execution/'COLD-GUARD-0.original-wait.actual.json'
            path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError): self.owner.claim(drift)
        self.assertFalse((self.fixture.root/'admission/machine.json').exists())


if __name__=='__main__':unittest.main()
