"""External-capacity timeout originals reach the shared reducer and writer lock.

All process/task observations are authored fixtures. The retained recorder text
is parsed, never imported or executed; its machine-specific constants are unused.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Callable
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_unrun as subject
from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue, file_pin, json_object, object_field
import test_ck3_mod_acceptance_unrun_stages as fixtures


class CapacityWaitUnrunTests(unittest.TestCase):
    def setUp(self) -> None:
        owner=fixtures.SerialKnownWaitPrelaunchTests('runTest');owner.setUp();self.addCleanup(owner.doCleanups)
        self.owner=owner;f=owner.fixture;self.f=f;self.serial=0
        self.execution=owner.execution
        for path in self.execution.glob('COLD-GUARD-*'):
            path.unlink()
        for name in ('CAPACITY-START.actual.json','CAPACITY.stdout.log'):
            (self.execution/name).unlink()
        owner.source.write_bytes((Path(__file__).parent/'testdata/allocated_unrun_capacity_wait/serial-source.py.txt').read_bytes())
        self.root_wait=owner.root_execution/'ROOT-SERIAL.original-wait.actual.json'
        self.root_start=owner.root_execution/'ROOT-SERIAL.started.actual.json'
        pre=f.write('preallocate.json',{'fixture':'actual preallocation input'})
        self.requested=f.root/'no-postallocate-capacity.json'
        old=json_object(json.loads((owner.root_execution/'ROOT-SERIAL.started.json').read_bytes()))
        argv=old['argv']
        if not isinstance(argv,list):raise AssertionError('Authored argv required')
        argv.extend(['--preallocate-capacity',pre['path'],'--preallocate-capacity-sha256',pre['sha256'],
            '--prelaunch-capacity',str(self.requested)])
        root_birth='1792713600.0000001'
        f.write_path(self.root_start,{'machine_id':f.machine,'pid':90003,'argv':argv,
            'process_create_time_seconds':root_birth,'started_at_utc':self.stamp(0),'original_wait_pending':True})
        f.write_path(self.root_wait,{'machine_id':f.machine,'pid':90003,'argv':argv,
            'process_create_time_seconds':root_birth,'started_at_utc':self.stamp(0),
            'actual_original_popen_wait':True,'original_wait_returncode':1,'finished_at_utc':self.stamp(189)})
        keeper=json_object(json.loads((f.keeper/'report.json').read_bytes()));keeper['at_utc']=self.stamp(187)
        f.write_path(f.keeper/'report.json',keeper)
        parent=json_object(json.loads((f.live/'keeper-actual-parent-exit.json').read_bytes()));parent['keeper_report']=keeper
        f.write_live('keeper-actual-parent-exit.json',parent)
        allocation=json_object(json.loads(owner.stdout.read_text(encoding='utf8').splitlines()[0]))
        # The actual public allocator flushes READY before its keeper wait, then
        # appends the terminal record. The original early pin remains a prefix.
        ready_raw=(json.dumps(allocation)+'\n').encode('utf8')
        owner.stdout.write_bytes(ready_raw)
        early_stdout=subject._ttl_pin(owner.stdout)
        with owner.stdout.open('ab') as stream:
            stream.write((json.dumps({**allocation,**parent})+'\n').encode('utf8'))
        waited=json_object(json.loads((self.execution/'ALLOCATE.original-wait.actual.json').read_bytes()))
        waited.update(observed_at_utc=self.stamp(188),finished_at_utc=self.stamp(188),elapsed_seconds=187.0)
        f.write_path(self.execution/'ALLOCATE.original-wait.actual.json',waited)
        failure=json_object(json.loads((self.execution/'ROOT-SERIAL-FAILURE.actual.json').read_bytes()))
        handles=failure['original_handles']
        if not isinstance(handles,list):raise AssertionError('Authored handles required')
        failure.update(observed_at_utc=self.stamp(186),error=repr(TimeoutError(
            'Root postallocate capacity not delivered within180s; no public run')),original_handles=handles[:1])
        f.write_path(self.execution/'ROOT-SERIAL-FAILURE.actual.json',failure)
        static=json_object(json.loads((self.execution/'STATIC-INPUTS-PRECOMPILED.actual.json').read_bytes()))
        for key in ('guard_original','guard_interpreter','capacity_original','guard_code_sha256','capacity_source_sha256'):
            static.pop(key)
        static.update(new_capacity_scanner_created=False,cold_guard_used=False,
            preallocate_capacity=json_object(pre),postallocate_capacity_path=str(self.requested))
        f.write_path(self.execution/'STATIC-INPUTS-PRECOMPILED.actual.json',static)
        f.write_path(self.execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json',{
            'machine_id':f.machine,'observed_at_utc':self.stamp(6),'run_id':f.run_id,
            'ready_context':json_object(owner.ready),'allocation_stdout':json_object(early_stdout),
            'grant':json_object(owner.grant),'expected_output':str(self.requested),'maximum_wait_seconds':180,
            'Game_not_started':True,'capacity_collector_owner':'/root'})
        terminal={'label':'ALLOCATE','pid':90000,'process_creation_filetime_100ns':handles[0]['birth_filetime'],
            'receipt_written':True,'returncode':0} if isinstance(handles[0],dict) else {}
        (owner.root_execution/'ROOT-SERIAL.stdout.log').write_text('ACTUAL_READY_ROOT_CAPACITY_REQUIRED '+f.run_id+
            '\nORIGINAL_WAIT_ACTUAL '+json.dumps(terminal)+'\n',encoding='utf8')
        (owner.root_execution/'ROOT-SERIAL.stderr.log').write_text('Authored original traceback\nTimeoutError: '
            'Root postallocate capacity not delivered within180s; no public run\n',encoding='utf8')
        self.release: JsonObject={'schema':'codex.task_bus.v1','ok':True,
            'task':{'task_id':'fixture-task','state':'waiting','resources':[],'last_sequence':12,'repo':'fixture-repo','git':{}},
            'event':{'task_id':'fixture-task','state':'waiting','resources':[],'sequence':12,'kind':'status',
                'timestamp_utc':self.stamp(200),'retirement':{'kind':'expired-own-claim-released',
                    'business_status':'unresolved_red','prior_sequence':10}}}
        self.publish_release()

    @staticmethod
    def stamp(second: int) -> str:
        return (datetime(2026,10,23,tzinfo=timezone.utc)+timedelta(seconds=second)).isoformat()

    def publish_release(self) -> None:
        f=self.f;f.done=self.release
        f.done_pin=f.write('expired-release.json',self.release)
        task=object_field(self.release,'task')
        f.write_path(f.bus/'tasks/fixture-task.json',task)
        (f.bus/'events.jsonl').write_text(json.dumps(self.release['event'])+'\n',encoding='utf8')
        f.packet={'tasks':[{**task,'age_seconds':1200,'stale':True}]}

    def args(self) -> argparse.Namespace:
        self.serial+=1;f=self.f;o=self.owner
        return argparse.Namespace(previous_live=f.live,keeper_root=f.keeper,output=f.root/('capacity-result-'+str(self.serial)),
            task_bus_root=f.bus,capacity_wait_root_wait=self.root_wait,
            prelaunch_orchestrator_source=o.source,root_screen_release=Path(f.done_pin['path']),
            next_state=f.root/'new-state',allocator_intent=self.execution/'ALLOCATE.intent.actual.json',
            allocator_process=self.execution/'ALLOCATE.started.actual.json',allocator_exit=self.execution/'ALLOCATE.original-wait.actual.json',
            allocator_stdout=o.stdout,release_sequence=12)

    def produce(self) -> subject.UnrunBundleReport:
        return subject.build_bundle(self.args())

    def claim(self, mutation: Callable[[],None] | None = None) -> tuple[Path,list[bool]]:
        with patch.object(self.owner,'produce',side_effect=self.produce):
            return self.owner.claim(mutation)

    def test_shared_producer_full_reducer_roundtrip_preserves_actual_waits_and_no_game(self) -> None:
        result=self.produce();row=json_object(json.loads(Path(result['bundle']['path']).read_bytes()))
        self.assertEqual(row['closure_kind'],subject.CAPACITY_WAIT_KIND)
        self.assertEqual(row['receipt_format'],subject.CAPACITY_WAIT_FORMAT)
        for absent in ('serial_guards','admin_done','idle_timeout','prelaunch_guard_state'):
            self.assertNotIn(absent,row)
        cleanup=object_field(result['validation'],'failure_cleanup')
        self.assertEqual(cleanup['original_root_exit_code'],1)
        self.assertEqual(cleanup['original_allocator_exit_code'],0)
        self.assertEqual(cleanup['original_keeper_exit_code'],0)
        self.assertEqual(cleanup['guard_original_wait_codes'],[])
        self.assertTrue(cleanup['closed_task_stale'])
        for key in ('normal_close_qualified','typed_normal_exit_proven','business_pass','release_pass'):
            self.assertIs(cleanup[key],False)
        self.assertEqual(json.loads(json.dumps(row)),row)

    def test_actual_allocator_rechecks_complete_chain_under_original_writer_lock(self) -> None:
        record,observed=self.claim();self.assertEqual(observed,[True])
        row=json_object(json.loads((record/'intent.json').read_bytes()))
        self.assertEqual(object_field(row,'closure')['mode'],'previous-shared-allocated-unrun-prelaunch-orchestrator-failed')
        self.assertIs(row['business_pass'],False)

    def test_rich_root_and_native_allocator_reject_wrong_missing_bool_float_and_pid(self) -> None:
        cases: tuple[tuple[Path,str,JsonValue], ...]=(
            (self.root_start,'pid',True),(self.root_start,'pid',90003.0),
            (self.root_wait,'pid',90004),(self.root_wait,'original_wait_returncode',True),
            (self.root_wait,'original_wait_returncode',1.0),(self.root_wait,'process_create_time_seconds',1792713600.0),
            (self.root_wait,'started_at_utc',self.stamp(1)),
            (self.execution/'ALLOCATE.started.actual.json','pid',False),
            (self.execution/'ALLOCATE.started.actual.json','process_creation_filetime_100ns',134373000000000001),
            (self.execution/'ALLOCATE.original-wait.actual.json','pid',90001),
            (self.execution/'ALLOCATE.original-wait.actual.json','original_wait_returncode',False),
            (self.execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json','maximum_wait_seconds',180.0),
            (self.execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json','Game_not_started',1),
        )
        for path,key,value in cases:
            original=path.read_bytes();row=json_object(json.loads(original));row[key]=value
            self.f.write_path(path,row)
            with self.subTest(path=path.name,key=key,value=value),self.assertRaises(ValueError):self.produce()
            path.write_bytes(original)
        for path,key in ((self.root_wait,'process_create_time_seconds'),(self.root_wait,'started_at_utc'),
                (self.execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json','grant')):
            original=path.read_bytes();row=json_object(json.loads(original));del row[key];self.f.write_path(path,row)
            with self.subTest(missing=key),self.assertRaises(ValueError):self.produce()
            path.write_bytes(original)

    def test_source_ast_short_wait_fake_guard_or_actual_postallocate_receipt_rejected(self) -> None:
        source=self.owner.source;original=source.read_bytes()
        source.write_bytes(original.replace(b'gate_deadline = time.monotonic()+180',b'gate_deadline = time.monotonic()+181'))
        with self.assertRaisesRegex(ValueError,'source AST'):self.produce()
        source.write_bytes(original)
        for path in (self.execution/'COLD-GUARD-0.intent.actual.json',self.requested):
            path.write_text('{}',encoding='utf8')
            with self.subTest(path=path.name),self.assertRaises(ValueError):self.produce()
            path.unlink()

    def test_current_counter_and_original_keeper_exit_types_remain_exact(self) -> None:
        counter=self.f.ids/self.f.machine/'living-artifacts/counter.json'
        parent=self.f.live/'keeper-actual-parent-exit.json'
        for path,key,bad in ((counter,'last_sequence',True),(counter,'last_sequence',1.0),
                (counter,'last_sequence',2),(parent,'keeper_actual_exit_code',False),
                (parent,'keeper_actual_exit_code',0.0)):
            original=path.read_bytes();row=json_object(json.loads(original));row[key]=bad
            self.f.write_path(path,row)
            with self.subTest(path=path.name,key=key,bad=bad),self.assertRaises(ValueError):self.produce()
            path.write_bytes(original)

    def test_original_ready_prefix_cannot_be_replaced_by_final_stdout_or_wrong_hash(self) -> None:
        path=self.execution/'AWAITING-ROOT-PRELAUNCH-CAPACITY.actual.json'
        original=path.read_bytes();row=json_object(json.loads(original))
        prefix=file_pin(row['allocation_stdout'])
        self.assertLess(prefix['bytes'],self.owner.stdout.stat().st_size)
        for bad in ({**prefix,'sha256':'0'*64},{**prefix,'bytes':True},
                {**prefix,'bytes':float(prefix['bytes'])},subject._ttl_pin(self.owner.stdout)):
            row['allocation_stdout']=json_object(bad);self.f.write_path(path,row)
            with self.subTest(prefix=bad),self.assertRaises(ValueError):self.produce()
        path.write_bytes(original)

    def test_expired_release_exact_kind_prior_sequence_task_and_stale_types(self) -> None:
        original=copy.deepcopy(self.release)
        value: JsonValue
        for key,value in (('kind','completed'),('sequence',True),('sequence',12.0)):
            event=object_field(self.release,'event');event[key]=value;self.release['event']=event;self.publish_release()
            with self.subTest(event=key),self.assertRaises(ValueError):self.produce()
            self.release=copy.deepcopy(original)
        for key,value in (('prior_sequence',True),('prior_sequence',10.0),('prior_sequence',9),('kind','other')):
            event=object_field(self.release,'event');retirement=object_field(event,'retirement');retirement[key]=value
            event['retirement']=retirement;self.release['event']=event;self.publish_release()
            with self.subTest(retirement=key),self.assertRaises(ValueError):self.produce()
            self.release=copy.deepcopy(original)
        self.publish_release()
        for key,value in (('stale',1),('stale',None),('age_seconds',True),('age_seconds',1200.0)):
            tasks=self.f.packet['tasks']
            if not isinstance(tasks,list):raise AssertionError('Authored packet')
            task=json_object(tasks[0]);task[key]=value;self.f.packet={'tasks':[task]}
            with self.subTest(snapshot=key),self.assertRaises(ValueError):self.produce()
            self.publish_release()

    def test_source_pin_or_owner_or_sequence_or_process_change_inside_writer_lock_rejected(self) -> None:
        mutations: list[Callable[[],None]]=[]
        def drift() -> None:
            path=self.execution/'ALLOCATE.original-wait.actual.json';path.write_bytes(path.read_bytes()+b' ')
        def owner() -> None:
            self.f.packet={'tasks':[{'task_id':'revived-owner','resources':['ck3-screen:acquired']}]}
        def sequence() -> None:
            task={**object_field(self.release,'task'),'last_sequence':13,'age_seconds':1200,'stale':True}
            self.f.packet={'tasks':[task]}
        def process() -> None:
            self.f.runtime={'blockers':[{'pid':123,'name':'ck3.exe'}]}
        mutations.extend((drift,owner,sequence,process))
        for mutate in mutations:
            original=(self.execution/'ALLOCATE.original-wait.actual.json').read_bytes()
            with self.subTest(mutation=mutate.__name__),self.assertRaises(ValueError):self.claim(mutate)
            self.assertFalse((self.f.root/'admission/machine.json').exists())
            (self.execution/'ALLOCATE.original-wait.actual.json').write_bytes(original)
            self.f.runtime={'blockers':[]};self.publish_release()

    def test_cross_format_and_changed_bundle_sha_rejected_by_real_consumer(self) -> None:
        report=self.produce();path=Path(report['bundle']['path']);row=json_object(json.loads(path.read_bytes()))
        row['receipt_format']=subject.SERIAL_PRELAUNCH_FORMAT
        self.f.write_path(path,row)
        release=subject._serial_resources().read_failed_runtime_release(Path(report['previous_release']['path']))
        with self.assertRaisesRegex(ValueError,'kind/format'):
            subject.validate_allocated_unrun(self.f.live,self.f.freeze,path,self.f.keeper,release,self.f.packet,
                next_state=self.f.root/'new-state')
        row['receipt_format']=subject.CAPACITY_WAIT_FORMAT
        ref=object_field(row,'capacity_wait_awaiting');ref['sha256']='0'*64;row['capacity_wait_awaiting']=ref
        self.f.write_path(path,row)
        with self.assertRaisesRegex(ValueError,'bytes changed'):
            subject.validate_allocated_unrun(self.f.live,self.f.freeze,path,self.f.keeper,release,self.f.packet,
                next_state=self.f.root/'new-state')

    def test_complete_modified_production_scope_strict(self) -> None:
        from mypy import api
        names={'_capacity_wait_source','_capacity_wait_root_paths','_capacity_wait_ready_prefix',
            'validate_capacity_wait','_capacity_wait_release',
            '_exact','build_serial_prelaunch_bundle','validate_allocated_unrun','build_bundle','main'}
        tree=ast.parse(Path(subject.__file__).read_text(encoding='utf8'))
        nodes: list[ast.stmt]=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
        self.assertEqual({n.name for n in nodes if isinstance(n,(ast.ClassDef,ast.FunctionDef))},names)
        prelude='''from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from collections.abc import Mapping
from typing import Literal
import argparse, ast, hashlib, json, re, os
from ck3_mod_acceptance import check_pin, pin, same_directory_control_peer
from ck3_mod_acceptance_launcher_pin_refusal import validate_launcher_pin_refusal
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field, strings_field
from ck3_mod_acceptance_unrun import (SCHEMA, PRELAUNCH_KIND, SERIAL_PRELAUNCH_FORMAT, CAPACITY_WAIT_KIND,
    CAPACITY_WAIT_FORMAT, PrelaunchGuardState, SerialPrelaunchGuardEvidence, SerialUnarmedGuardEvidence,
    UnrunBundleReport, _serial_raw, _serial_original, _serial_argument, _serial_allocator,
    _ttl_allocator_stdout, _serial_resources, _sequence, _timestamp, _integer, _read, need,
    _serial_required_path, _serial_root_paths, _journal_events, _captured_release, _write,
    _ttl_pin, _serial_prepared_phases, _ttl_recovery_sources, _SerialUnrunReducer, _UnrunProcessInventory,
    OFFLINE_TTL_KIND, ABORTED_KIND, CLOSED_KEEPER_ABORTED_KIND, validate_pre_intent_offline_ttl_refusal,
    validate_aborted_allocation_v1, validate_prelaunch_orchestrator,
    _allocator_argv, _release_stages, _recovery_input_validation, _serial_cleanup_waits,
    build_aborted_bundle_v1, build_pre_intent_offline_ttl_bundle, _phase_guard_evidence,
    _prelaunch_guard_state, PRELAUNCH_KIND)
'''
        scoped=prelude+ast.unparse(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])))
        root=Path(__file__).resolve().parent.parent
        with patch.dict(os.environ,{'MYPYPATH':os.pathsep.join((str(root/'tools'),str(root/'ck3_autonomous_player/src')))}):
            stdout,stderr,code=api.run(['--strict','--strict-equality','--follow-imports=silent','--no-incremental',
                '--cache-dir','nul','-c',scoped])
        self.assertEqual(code,0,stdout+stderr)


if __name__=='__main__':
    unittest.main()
