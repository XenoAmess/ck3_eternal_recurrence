"""Modern preserved failure originals reach the existing full failed-live reducer."""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from typing import Iterator
from contextlib import contextmanager

import ck3_mod_acceptance_allocate as subject
from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue, file_pin, json_object, object_field
from ck3_mod_acceptance import pin
import test_ck3_mod_acceptance_failed_resource_closure as existing_serial


class ModernSerialFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        owner = existing_serial.SerialOriginalWaitClosureTests('runTest')
        owner.setUp(); self.addCleanup(owner.doCleanups)
        self.owner = owner
        f = owner.fixture
        self.execution = f.root/'modern-execution'; self.execution.mkdir()
        self.outer = f.root/'modern-outer'; self.outer.mkdir()
        self.refs = {key:file_pin(value) for key,value in f.refs.items()}
        machine = f.machine
        self.commit = 'a'*40
        runtime = self.write(f.root/'modern-runtime-manifest.json', {'source_commit':self.commit})
        freeze = json_object(f.freeze); freeze['runtime_manifest'] = json_object(runtime)
        f.freeze = dict(freeze)
        self.refs['frozen_argv'] = self.write(f.run_dir/'frozen-argv.json', freeze)
        ready = json_object(json.loads(Path(self.refs['ready_context']['path']).read_bytes()))
        ready['frozen_argv'] = json_object(self.refs['frozen_argv'])
        self.refs['ready_context'] = self.write(Path(self.refs['ready_context']['path']), ready)
        prepared = json_object(json.loads(Path(self.refs['prepared_case']['path']).read_bytes()))
        prepared['runtime_manifest'] = json_object(runtime)
        self.refs['prepared_case'] = self.write(Path(self.refs['prepared_case']['path']), prepared)
        ready['prepared_case'] = json_object(self.refs['prepared_case'])
        self.refs['ready_context'] = self.write(Path(self.refs['ready_context']['path']), ready)
        source = f.root/'modern-source.py'; source.write_text('import subprocess\np=subprocess.Popen([])\np.wait()\n',encoding='utf8')
        argv: list[JsonValue] = ['python','-B','-X','utf8',str(source),'--source-commit',self.commit]
        self.root_wait = self.outer/'ROOT-SERIAL.original-wait.json'
        self.write(self.outer/'ROOT-SERIAL.started.json', {'machine_id':machine,'pid':91000,'argv':argv,
            'started_at_utc':self.stamp(-1),'original_wait_pending':True})
        self.write(self.root_wait, {'machine_id':machine,'pid':91000,'argv':argv,'actual_original_popen_wait':True,
            'original_wait_returncode':2,'finished_at_utc':self.stamp(70)})
        self.write(self.outer/'ROOT-NATIVE-IDENTITY.json', {'machine_id':machine,'pid':91000,
            'process_creation_filetime_100ns':self.birth(-1),'observed_at_utc':self.stamp(-.5),
            'source':'GetProcessTimes original Popen retained handle'})
        (self.outer/'ROOT-SERIAL.stdout.log').write_bytes(b'Authored actual terminal records\n')
        (self.outer/'ROOT-SERIAL.stderr.log').write_bytes(b'')
        handles: list[JsonValue] = []
        for index,label in enumerate(subject.MODERN_SERIAL_FAILURE_LABELS):
            mode = 'run' if label=='PUBLIC-RUN' else 'allocate'
            original = owner.originals[mode+'_intent']
            start_second = 10+index if index<6 else 63+index
            end_second = 60 if label=='PUBLIC-RUN' else (68.5 if label=='SCREEN-RELEASE' else start_second+.5)
            if label=='SCREEN-RELEASE': start_second=68
            if label=='SCREEN-LIST': start_second=66
            pid = 92000+index
            code = 2 if label in ('PUBLIC-RUN','PUBLIC-VERIFY') else 0
            child_argv: JsonValue = original['argv'] if label in ('PUBLIC-RUN','ALLOCATE') else ['python','authored-control',label]
            if label=='SCREEN-RELEASE': child_argv=['python','task-bus','release-screen-cas','--task',freeze['screen_task']]
            intent: JsonObject = {'machine_id':machine,'observed_at_utc':self.stamp(start_second+.000001),
                'started_at_utc':self.stamp(start_second),'argv':child_argv,'source_commit':self.commit}
            began: JsonObject = {'machine_id':machine,'observed_at_utc':self.stamp(start_second+.000003),
                'started_at_utc':self.stamp(start_second+.000002),'pid':pid,
                'process_creation_filetime_100ns':self.birth(start_second),
                'process_create_time_seconds':self.seconds(start_second),'original_wait_pending':True}
            ended: JsonObject = {'machine_id':machine,'observed_at_utc':self.stamp(end_second+.000001),
                'finished_at_utc':self.stamp(end_second),'pid':pid,'process_creation_filetime_100ns':self.birth(start_second),
                'original_wait_returncode':code,'elapsed_seconds':float(end_second-start_second)}
            for role,suffix,row in (('intent','.intent.actual.json',intent),('started','.started.actual.json',began),('wait','.original-wait.actual.json',ended)):
                ref=self.write(self.execution/(label+suffix),row)
                if label in ('PUBLIC-RUN','ALLOCATE'): self.refs[mode+'_'+role]=ref
            for role in ('stdout','stderr'):
                path=self.execution/(label+'.'+role+'.log')
                if label=='SCREEN-RELEASE' and role=='stdout':
                    path.write_bytes(Path(self.refs['release']['path']).read_bytes()); self.refs['release']=file_pin(pin(path))
                elif label in ('PUBLIC-RUN','ALLOCATE'):
                    path.write_bytes(Path(self.refs[mode+'_'+role]['path']).read_bytes())
                else: path.write_bytes(b'')
                if label in ('PUBLIC-RUN','ALLOCATE'): self.refs[mode+'_'+role]=file_pin(pin(path))
            handles.append({'label':label,'pid':pid,'birth_filetime':self.birth(start_second),
                'actual_original_popen_wait':True,'returncode':code,'stdout_closed':True,'stderr_closed':True})
        display: JsonObject = {'width':1024,'height':768,'frequency':60,'bits':32}
        self.write(self.execution/'DISPLAY-MODE.actual.json', {'machine_id':machine,'observed_at_utc':self.stamp(5),'before':display,'actual':[2560,1440]})
        self.write(self.execution/'DISPLAY-RESTORED.actual.json', {'machine_id':machine,'observed_at_utc':self.stamp(67),'before':display,'actual':[1024,768]})
        life: JsonObject = {'kind':'preserved_failure', **{name:json_object(json.loads(Path(self.refs[key]['path']).read_bytes()))
            for name,key in (('normal','normal_close'),('retained','retained_exit'),('host','host_exit'))}}
        self.terminal: JsonObject = {'machine_id':machine,'observed_at_utc':self.stamp(69),'run_id':f.run_dir.name,
            'public_returncode':2,'verify_returncode':2,'allocator_returncode':0,'screen_release':json_object(self.refs['release']),
            'normal_close_qualified':False,'business_pass':False,'failure_preserved':True,
            'actual_lifecycle_kind':'preserved_failure','actual_host_returncode':1,'lifecycle_facts':life,'original_handles':handles}
        self.terminal_path=self.execution/'ALL-ORIGINAL-TERMINALS.actual.json'
        self.publish()

    @staticmethod
    def stamp(second: float) -> str:
        return (datetime(2026,10,24,10,tzinfo=timezone.utc)+timedelta(seconds=second)).isoformat()

    @classmethod
    def seconds(cls, second: float) -> str:
        return str(Decimal(str(datetime.fromisoformat(cls.stamp(second)).timestamp())))

    @classmethod
    def birth(cls, second: float) -> str:
        return str(int(Decimal(cls.seconds(second))*10000000)+116444736000000000)

    @staticmethod
    def write(path: Path, value: JsonObject) -> FilePin:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value),encoding='utf8')
        return file_pin(pin(path))

    def publish(self) -> None:
        terminal=self.write(self.terminal_path,self.terminal)
        self.refs.update(subject.modern_serial_failure_original_pins(terminal,self.root_wait))
        self.owner.fixture.refs=dict(self.refs)
        self.owner.fixture.release_path=Path(self.refs['release']['path'])
        self.owner.publish()

    def check(self) -> JsonObject:
        return self.owner.check()

    def test_complete_modern_producer_and_full_reducer_preserve_failed_credit(self) -> None:
        proof=object_field(self.check(),'failure_cleanup')
        self.assertEqual(proof['original_host_exit_code'],1)
        self.assertEqual(proof['original_ck3_exit_code'],0)
        self.assertIs(proof['actual_retained_os0'],True)
        for key in ('normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass'):
            self.assertIs(proof[key],False)
        self.assertEqual(self.terminal,json.loads(Path(self.refs['root_serial_terminal']['path']).read_bytes()))

    def test_missing_original_handle_pin_and_crossed_lifecycle_rejected(self) -> None:
        for key in ('serial_SCREEN-RELEASE_wait','display_restored','root_serial_identity','serial_COLD-GUARD-1_stderr'):
            refs=dict(self.refs);del refs[key]
            with self.subTest(missing=key),self.assertRaisesRegex(ValueError,'Complete modern'):
                subject.preserved_serial_failure_bundle(self.owner.fixture.machine,self.owner.fixture.run_dir.name,self.owner.fixture.keeper,refs)
        original=copy.deepcopy(self.terminal)
        life=object_field(self.terminal,'lifecycle_facts');life['host']={};self.terminal['lifecycle_facts']=life
        with self.assertRaisesRegex(ValueError,'failed lifecycle'):self.publish()
        self.terminal=original

    def test_changed_wait_birth_code_release_display_and_false_credit_rejected(self) -> None:
        for key,bad in (('verify_returncode',0),('actual_host_returncode',True),('business_pass',True),('failure_preserved',False)):
            original=copy.deepcopy(self.terminal);self.terminal[key]=bad
            with self.subTest(field=key),self.assertRaises(ValueError):self.publish()
            self.terminal=original
        changes: tuple[tuple[str,str,JsonValue], ...] = (('serial_COLD-GUARD-0_wait','original_wait_returncode',False),
                ('root_serial_wait','original_wait_returncode',0),('display_restored','actual',[2560,1440]),
                ('serial_SCREEN-RELEASE_started','process_creation_filetime_100ns',134373000000000001))
        for key,field,bad_value in changes:
            path=Path(self.refs[key]['path']);raw=path.read_bytes();row=json_object(json.loads(raw));row[field]=bad_value
            self.write(path,row)
            with self.subTest(original=key),self.assertRaises(ValueError):self.publish()
            path.write_bytes(raw)
        self.publish()

    def test_modern_originals_revalidated_inside_existing_writer_lock(self) -> None:
        import test_preserved_failure_native_os0 as existing
        from types import SimpleNamespace
        @contextmanager
        def boundaries() -> Iterator[None]:
            with self.owner.boundaries(): yield
        bridge=SimpleNamespace(setUp=lambda:None,doCleanups=lambda:None,fixture=self.owner.fixture,
            check=self.check,boundaries=boundaries)
        writer=existing.FailedLiveWriterLockTests('runTest');self.addCleanup(writer.doCleanups)
        with patch.object(existing,'CaseClientFailureClosureTests',return_value=bridge):writer.setUp()
        record=writer.claim()
        self.assertIs(object_field(object_field(json_object(json.loads((record/'intent.json').read_bytes())),'closure'),'failure_cleanup')['business_pass'],False)

    def test_new_modern_display_pin_drift_inside_writer_lock_refuses(self) -> None:
        import test_preserved_failure_native_os0 as existing
        from types import SimpleNamespace
        bridge=SimpleNamespace(setUp=lambda:None,doCleanups=lambda:None,fixture=self.owner.fixture,
            check=self.check,boundaries=self.owner.boundaries)
        writer=existing.FailedLiveWriterLockTests('runTest');self.addCleanup(writer.doCleanups)
        with patch.object(existing,'CaseClientFailureClosureTests',return_value=bridge):writer.setUp()
        def drift() -> None:
            path=Path(self.refs['display_restored']['path']);path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError):writer.claim(mutation=drift)

    def test_entire_modified_production_ast_is_strict(self) -> None:
        from mypy import api
        names={'PreservedSerialFailureBundle','preserved_serial_failure_bundle','serial_original_evidence_pins',
            '_serial_failure_original','modern_serial_failure_original_pins','validate_modern_serial_failure_evidence',
            '_validate_serial_process_originals','validate_serial_original_public_wait','_late_integer'}
        tree=ast.parse(Path(subject.__file__).read_text(encoding='utf8'))
        nodes=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
        self.assertEqual({node.name for node in nodes},names)
        constants=[node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in
            {'MODERN_SERIAL_FAILURE_TERMINAL_FIELDS','MODERN_SERIAL_FAILURE_LABELS','PRESERVED_TYPED_OBSERVER_SOURCE_KEYS'} for t in node.targets)]
        prelude='''from __future__ import annotations
from typing import Literal, TypedDict
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import json, math, re
from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, file_pin, text_field, strings_field, object_field
from ck3_mod_acceptance import pin, check_pin
'''
        source=prelude+ast.unparse(ast.fix_missing_locations(ast.Module(body=[*constants,*nodes],type_ignores=[])))
        stdout,stderr,code=api.run(['--strict','--strict-equality','--follow-imports=silent','--no-incremental','--cache-dir','nul','-c',source])
        self.assertEqual(code,0,stdout+stderr)


if __name__=='__main__':unittest.main()
