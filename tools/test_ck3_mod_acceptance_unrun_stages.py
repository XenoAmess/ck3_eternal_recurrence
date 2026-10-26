"""Persistent regression for the actual default CAS completion path."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
import argparse
import importlib
from contextlib import ExitStack
from collections.abc import Mapping
from types import SimpleNamespace
from unittest.mock import patch
from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue, json_object
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


if __name__=='__main__':unittest.main()
