"""Persistent regression for the actual default CAS completion path."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue
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


if __name__=='__main__':unittest.main()
