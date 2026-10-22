"""Real reducer and writer-boundary regression; fixtures never start a process."""
from __future__ import annotations
import contextlib
from collections.abc import Iterator
import ast
import copy
from datetime import datetime,timedelta,timezone
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import re
import types
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, object_field
from ck3_mod_acceptance_fresh_machine_bootstrap import MachineBinding, create_current_process_observation
import ck3_mod_acceptance_interrupted as subject


class InterruptedTests(unittest.TestCase):
    def write(self,path:Path,value:object) -> FilePin:
        path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(value).encode('utf-8');path.write_bytes(raw)
        return FilePin(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def setUp(self) -> None:
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();self.live=self.root/'machine--living--R1'
        self.keeper=self.root/'keeper';self.state=self.root/'old-state';self.next=self.root/'new-state'
        self.bus=self.root/'bus';self.close=self.root/'close.json'
        self.binding:MachineBinding={'machine_id':'machine','state_root':str(self.root/'ids'),
                                     'admission_root':str(self.root/'ids/admissions')}
        self.manifest=self.write(self.root/'manifest.json',{})
        self.frozen:dict[str,object]={'run_id':self.live.name,'screen_task':'screen-old','state_dir':str(self.state),
            'source_root':str(self.root/'source'),'runtime_manifest':self.manifest,'argv':['python','host.py']}
        frozen_pin=self.write(self.live/'frozen-argv.json',self.frozen)
        prepared=self.write(self.root/'prepared.json',{'startup':{'state_dir':str(self.state)},'runtime_manifest':self.manifest})
        ready=self.write(self.live/'ready-context.json',{'run_id':self.live.name,'run_dir':str(self.live),
            'keeper_root':str(self.keeper),'frozen_argv':frozen_pin,'prepared_case':prepared})
        host=self.write(self.live/'host-started.json',{'run_id':self.live.name,'argv':self.frozen['argv'],
            'actual_popen_retained':True,'pid':1001,'supervisor_pid':1002})
        supervisor=self.write(self.live/'host-supervisor-started.json',{'pid':1002,
            'argv':['python','--run-root',str(self.live),'--keeper-root',str(self.keeper)]})
        keeper=self.write(self.live/'keeper-process.json',{'pid':1003,'argv':['python','--task','screen-old',
            '--root',str(self.keeper),'--bus-dir',str(self.bus)]})
        inputs=self.write(self.keeper/'inputs.json',{'task_id':'screen-old'})
        report=self.write(self.live/'native-report.json',{'status':'RUNNING','state_dir':str(self.state),
            'managed_session_thread_finished':False,'finished_at':None,
            'frontend_fixture_start_submission':{'status':'SINGLE_START_ACKNOWLEDGED_POST_STATE_PENDING',
                'acknowledged':True,'retry_allowed':False,'result':{'binding':{'bridge_pid':1004}}}})
        now=datetime.now(timezone.utc)
        self.task:JsonObject={'task_id':'screen-old','last_sequence':101,'state':'waiting','resources':[]}
        self.event:JsonObject={'task_id':'screen-old','sequence':101,'state':'waiting','resources':[],
            'timestamp_utc':now.isoformat(),'retirement':{'business_status':'unresolved_red','prior_sequence':100}}
        self.release:JsonObject={'ok':True,'schema':'codex.task_bus.v1','task':self.task,'event':self.event}
        release=self.write(self.root/'release.json',self.release)
        self.old_event:JsonObject={'task_id':'screen-old','sequence':100,'state':'running',
            'resources':['ck3-screen:acquired'],'timestamp_utc':(now-timedelta(minutes=20)).isoformat()}
        self.bus.mkdir()
        self.events=self.bus/'events.jsonl';self.events.write_text(json.dumps(self.old_event)+'\n'+json.dumps(self.event)+'\n',encoding='utf-8')
        self.packet:JsonObject={'tasks':[{**self.task,'age_seconds':0,'stale':False}]}
        self.current=create_current_process_observation(binding=self.binding,
            runtime_inventory={'blockers':[],'process_absence_is_normal_exit_proof':False},
            ck3_inventory={'tasklist_returncode':0,'inventory_backend':'tasklist+toolhelp32',
                'tasklist_pids':[],'wmi_pids':[],'native_pids':[],'processes':[]})
        nonce='a'*32
        values={'ck3.json':{'ck3_pid':1004,'parent_pid':1005,'nonce':nonce},
            'owner.json':{'pid':1005,'state_dir':str(self.state)},'unsafe-cleanup.json':{'ck3_pid':1004,'nonce':nonce},
            f'watchdog-{nonce}.ready.json':{'nonce':nonce,'parent_pid':1005,'watchdog_pid':1006},
            f'ck3.{nonce}.watchdog_start.json':{'nonce':nonce,'parent_pid':1005,'watchdog_pid':1006,'watchdog_parent_pid':1007}}
        self.controls={key:self.write(self.state/'control'/key,value) for key,value in values.items()}
        self.bundle:subject.InterruptedClosure={'schema':'ck3-mod-acceptance-failed-live-resource-closure-v1',
            'closure_kind':subject.KIND,'machine_id':'machine','run_id':self.live.name,'observed_at_utc':now.isoformat(),
            'keeper_root':str(self.keeper),'quarantined_state':str(self.state),'quarantined_controls':self.controls,
            'original_evidence':{'frozen_argv':frozen_pin,'ready_context':ready,'prepared_case':prepared,'host_started':host,
                'host_supervisor':supervisor,'keeper_process':keeper,'keeper_inputs':inputs,'native_report':report,'release':release},
            'normal_close_qualified':False,'typed_normal_exit_proven':False,'business_pass':False,'release_pass':False}
        self.write(self.close,self.bundle)

    def validate(self,*,present:set[int]|None=None,next_state:Path|None=None) -> JsonObject:
        return subject.validate_interrupted_owner(previous=self.live,frozen=self.frozen,close_path=self.close,
            keeper_root=self.keeper,release=self.release,bus_packet=self.packet,binding=self.binding,
            current_processes=self.current,present_pids=set() if present is None else present,
            next_state=self.next if next_state is None else next_state)

    def test_original_inputs_to_reducer_keep_quarantine_and_unknown_exits(self) -> None:
        result=self.validate();self.assertEqual(result['mode'],subject.MODE)
        cleanup=object_field(result,'failure_cleanup')
        self.assertIsNone(cleanup['original_host_exit_code']);self.assertFalse(cleanup['business_pass'])
        self.assertEqual(json.loads(json.dumps(result)),result)
        self.assertEqual({path.name for path in (self.state/'control').iterdir()},set(self.controls))

    def test_each_original_process_or_global_controller_blocks(self) -> None:
        for pid in range(1001,1008):
            with self.subTest(pid=pid),self.assertRaisesRegex(ValueError,'remains present'):self.validate(present={pid})
        runtime=object_field(self.current,'runtime_inventory');runtime['blockers']=[{'pid':2000}]
        self.current['runtime_inventory']=runtime
        with self.assertRaises(ValueError):self.validate()

    def test_unsafe_state_cannot_be_reused_or_nested(self) -> None:
        for path in (self.state,self.state/'child',self.state.parent):
            with self.subTest(path=path),self.assertRaisesRegex(ValueError,'cannot be reused'):self.validate(next_state=path)

    def test_missing_null_extra_and_wrong_type_fields_are_rejected(self) -> None:
        for field,value,delete in (('schema',None,False),('machine_id',True,False),('business_pass',0,False),
                                   ('closure_kind','other',False),('run_id',None,True),('extra',[],False)):
            bad=json_object(copy.deepcopy(self.bundle))
            if delete:del bad[field]
            else:bad[field]=value
            self.write(self.close,bad)
            with self.subTest(field=field),self.assertRaises(ValueError):self.validate()

    def test_available_terminal_receipt_requires_original_route(self) -> None:
        self.write(self.live/'host-original-process-exit.json',{'returncode':0})
        with self.assertRaisesRegex(ValueError,'Existing terminal'):self.validate()

    def test_real_venv_redirector_and_runtime_pids_stay_distinct(self) -> None:
        reference=self.bundle['original_evidence']['host_started']
        body=json.loads(Path(reference['path']).read_text(encoding='utf-8'))
        body['supervisor_pid']=1008
        self.bundle['original_evidence']['host_started']=self.write(Path(reference['path']),body)
        self.write(self.close,self.bundle)
        self.validate()
        for pid in (1002,1008):
            with self.assertRaisesRegex(ValueError,'remains present'):self.validate(present={pid})

    def test_changed_or_missing_control_never_gets_cleared(self) -> None:
        path=self.state/'control/unsafe-cleanup.json';original=path.read_bytes()
        path.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'bytes changed'):self.validate()
        path.write_bytes(original);path.unlink()
        with self.assertRaisesRegex(ValueError,'quarantine'):self.validate()

    def test_actual_bus_owner_or_changed_task_blocks(self) -> None:
        self.packet={'tasks':[{**self.task,'resources':['ck3-screen:acquired']}]}
        with self.assertRaisesRegex(ValueError,'screen owner'):self.validate()
        self.packet={'tasks':[{**self.task,'last_sequence':102}]}
        with self.assertRaisesRegex(ValueError,'Current task'):self.validate()

    def test_release_must_match_real_canonical_event_and_expired_claim(self) -> None:
        self.events.write_text(json.dumps(self.old_event)+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'canonical event'):self.validate()
        recent={**self.old_event,'timestamp_utc':datetime.now(timezone.utc).isoformat()}
        self.events.write_text(json.dumps(recent)+'\n'+json.dumps(self.event)+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'not expired'):self.validate()

    def test_actual_writer_lock_revalidates_real_reducer_before_intent(self) -> None:
        import ck3_live_run_id as ids
        import ck3_mod_acceptance_allocate as allocator
        admission=Path(self.binding['admission_root']);admission.mkdir(parents=True)
        self.write(admission/'000001/allocation.json',{'live':str(self.live),'run_id':self.live.name})
        active=[False];calls=[]
        original=ids._exclusive_file_lock
        @contextlib.contextmanager
        def locked(path:Path) -> Iterator[None]:
            with original(path):
                active[0]=True
                try:yield
                finally:active[0]=False
        def revalidate(*arguments:object) -> JsonObject:
            self.assertTrue(active[0]);calls.append(arguments);return self.validate()
        selection=types.SimpleNamespace(state_dir=self.next,runtime_path=Path(self.manifest['path']),
            manifest_path=Path(self.manifest['path']),prepared_path=Path(self.bundle['original_evidence']['prepared_case']['path']))
        args=types.SimpleNamespace(previous_live=self.live,previous_keeper=self.keeper,
            previous_failure_close=self.close,previous_release=Path(self.bundle['original_evidence']['release']['path']))
        closure=self.validate()
        with patch.object(ids,'_exclusive_file_lock',locked),patch.object(allocator,'previous_interrupted_owner_closure',revalidate):
            output=allocator.claim_machine_admission(self.binding,selection,args,closure)
        self.assertEqual(len(calls),1);self.assertTrue((output/'intent.json').is_file())
        def changed(*arguments:object) -> JsonObject:
            self.assertTrue(active[0]);return self.validate(present={1004})
        before=set(admission.iterdir())
        with patch.object(ids,'_exclusive_file_lock',locked),patch.object(allocator,'previous_interrupted_owner_closure',changed):
            with self.assertRaisesRegex(ValueError,'remains present'):
                allocator.claim_machine_admission(self.binding,selection,args,closure)
        self.assertEqual(set(admission.iterdir()),before)

    def test_actual_allocator_owned_functions_are_type_checked(self) -> None:
        repo=Path(__file__).resolve().parents[1]
        source=repo/'tools/ck3_mod_acceptance_allocate.py'
        wanted={'previous_interrupted_owner_closure','claim_machine_admission'}
        tree=ast.parse(source.read_text(encoding='utf-8-sig'))
        spans={node.name:(node.lineno,node.end_lineno or node.lineno) for node in tree.body
               if isinstance(node,ast.FunctionDef) and node.name in wanted}
        self.assertEqual(set(spans),wanted)
        result=subprocess.run([sys.executable,'-m','mypy','--follow-imports=skip','--check-untyped-defs',
            '--show-column-numbers','--no-incremental','--cache-dir','nul',str(source),
            str(repo/'tools/ck3_mod_acceptance_interrupted.py')],cwd=repo,capture_output=True,text=True,
            encoding='utf-8',timeout=45)
        self.assertIn(result.returncode,(0,1),result.stdout+result.stderr)
        self.assertFalse(result.stderr,result.stderr)
        owned=[];total=0
        for line in result.stdout.splitlines():
            match=re.match(r'^(.+?):([0-9]+):[0-9]+: error: (.*)$',line)
            if match is None:continue
            total+=1
            if Path(match.group(1)).resolve()!=source:continue
            number=int(match.group(2))
            if any(first<=number<=last for first,last in spans.values()):owned.append(line)
        self.assertEqual(owned,[],'\n'.join(owned))
        print(f'Actual allocator checker: owned functions=2, owned errors=0, complete diagnostics={total}, whole-module pass={result.returncode==0}')


if __name__=='__main__':unittest.main()
