"""First-machine admission regressions with synthetic evidence and no bus/game."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_live_run_id as ids
import ck3_mod_acceptance_allocate as allocation
from ck3_mod_acceptance_keeper import write_new


class FirstMachineBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.machine='synthetic-machine-12345'
        self.binding={'machine_id':self.machine,'state_root':str(self.root/'id-state'),
            'admission_root':str(self.root/'id-state'/self.machine/'.shared-runtime-admissions-v1')}
        self.selection=SimpleNamespace(runtime_path=self.root/'runtime.local.json',manifest_path=self.root/'manifest.json',
            locations={'repo_root':self.root},prepared_path=self.root/'prepared.json')
        self.put(self.selection.runtime_path,{'schema':'synthetic-config'})
        self.put(self.selection.manifest_path,{'schema':'synthetic-manifest'})
        self.put(self.selection.prepared_path,{'schema':'synthetic-prepared'})

    def put(self,path,value):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);write_new(path,value);return allocation.pin(path)

    def fixture(self):
        refs={};legacy=self.root/'legacy';pid=2468;task='synthetic-old-screen'
        identity={'schema':'xar.ck3-live-run-identity.v1','machine_id':self.machine,'run_id':self.machine+'--vanilla--R0001',
            'execution_id':'synthetic-execution','allocated_at_utc':'2026-10-09T10:00:00+00:00'}
        refs['identity']=self.put(legacy/'identity.json',identity)
        namespace=self.root/'id-state'/self.machine/'vanilla';namespace.mkdir(parents=True)
        (namespace/'allocations.jsonl').write_text(json.dumps(identity)+'\n',encoding='utf-8')
        refs['profile']=self.put(legacy/'profile.json',{'schema_version':1,'historical':True})
        creation=134360257538492014
        launch={'run_id':identity['run_id'],'execution_id':identity['execution_id'],'game_started':True,'pid':pid,
            'task':task,'process_create_time':creation/10000000-11644473600}
        refs['launch']=self.put(legacy/'launch.json',launch)
        native={key:True for key in ('exact_build_verified','owner_verified','process_identity_verified',
            'source_abi_pins_verified','stock_files_verified','loaded_source_binding_verified')}
        native.update(game_pid=pid,process_creation_filetime_100ns=creation)
        result={'schema':'ck3-normal-exit-process-observation-result-v1','typed_normal_exit_observed':True,
            'process_exit_observed':True,'exit_code':0,'autosave_verified':False,
            'process_creation_filetime_100ns':creation,
            'process_preconfirm_pin':{'pid':pid,'creation_filetime_100ns':creation,'retained_handle_token':'a'*32},
            'native_observation':native,'process_observation':{'pid':pid,'creation_filetime_100ns':creation,
                'retained_handle_token':'a'*32,'process_identity_verified':True,'process_exit_observed':True,
                'wait_state':'signaled','wait_result':0,'errors':[],'exit_code':0}}
        refs['typed_normal_exit']=self.put(legacy/'sdk.json',{'structuredContent':{
            'schema':'ck3.native-profile-receipt.v1','profile_sha256':refs['profile']['sha256'],
            'status':'process_exit_observed_zero','result':result}})
        refs['original_handle_exit']=self.put(legacy/'original-handle.json',{'pid':pid,'returncode':0})
        refs['keeper_final']=self.put(legacy/'keeper.json',{'task_id':task,'last_sequence':10,'thread_exited':True,
            'failure':None,'entry_error':None})
        refs['client_final']=self.put(legacy/'client.json',{'status':'CLOSED','terminal_exit_requested':True})
        closeout={'schema':'codex.task_bus.v1','task_id':task,'last_sequence':12,'state':'done','resources':[],
            'updated_at_utc':'2026-10-09T11:00:00+00:00'}
        refs['closeout_task']=self.put(legacy/'closeout.json',closeout)
        archive=self.put(self.root/'tracked/INDEX.json',{'evidence_entries':[{'source':row} for row in refs.values()]})
        bundle={'schema':'ck3-mod-acceptance-first-machine-bootstrap-v1','machine':self.binding,
            'runtime_config':allocation.pin(self.selection.runtime_path),'runtime_manifest':allocation.pin(self.selection.manifest_path),
            'repo_root':str(self.root),'legacy_archive_index':archive,'legacy_profile_mcp_closure':refs}
        path=self.root/'bootstrap.json';self.put(path,bundle);bundle['_bundle_path']=str(path)
        events=[{'schema':'codex.task_bus.v1','task_id':task,'sequence':10,'resources':['ck3-screen:acquired'],'state':'running'},
                {'schema':'codex.task_bus.v1','task_id':task,'sequence':11,'resources':[],'state':'done'}]
        return bundle,events,{'tasks':[closeout]},Path(refs['closeout_task']['path'])

    def validate(self,bundle,events,packet,release):
        with patch.object(allocation.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
            return allocation.validate_legacy_bootstrap(bundle,self.selection,self.binding,events,packet,release)

    def test_original_legacy_zero_closure_admits_no_shared_qualification_or_autosave_claim(self):
        values=self.fixture();result=self.validate(*values)
        self.assertEqual(result['mode'],'first-machine-legacy-profile-mcp-closure')
        self.assertIs(result['legacy_shared_runtime_qualified'],False)
        self.assertIs(result['legacy_autosave_verified'],False)
        self.assertIs(result['legacy_typed_normal0'],True)
        self.assertIs(result['legacy_original_parent_handle0'],True)

    def test_cross_machine_and_changed_runtime_config_rejected(self):
        bundle,events,packet,release=self.fixture()
        changed=copy.deepcopy(bundle);changed['machine']['machine_id']='another-machine'
        with self.assertRaisesRegex(ValueError,'actual OS'):self.validate(changed,events,packet,release)
        changed=copy.deepcopy(bundle);changed['runtime_config']['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'one selected'):self.validate(changed,events,packet,release)

    def test_process_gone_or_parent_zero_alone_cannot_replace_typed_normal_exit(self):
        bundle,events,packet,release=self.fixture()
        for key in ('typed_normal_exit','original_handle_exit'):
            changed=copy.deepcopy(bundle);source=Path(changed['legacy_profile_mcp_closure'][key]['path'])
            value=json.loads(source.read_text(encoding='utf-8'))
            if key=='typed_normal_exit':value['structuredContent']['result']['typed_normal_exit_observed']=False
            else:value['returncode']=1
            replacement=self.root/(key+'-invalid.json');row=self.put(replacement,value)
            changed['legacy_profile_mcp_closure'][key]=row
            # Even a newly archived counterfactual must fail the semantic gate.
            archive=json.loads(Path(bundle['legacy_archive_index']['path']).read_text(encoding='utf-8'))
            archive['evidence_entries'].append({'source':row})
            alternate=self.root/(key+'-index.json');changed['legacy_archive_index']=self.put(alternate,archive)
            with self.assertRaisesRegex(ValueError,'typed normal0'):self.validate(changed,events,packet,release)

    def test_unreleased_fresh_bus_or_missing_durable_release_rejected(self):
        bundle,events,packet,release=self.fixture()
        changed=copy.deepcopy(packet);changed['tasks'][0]['resources']=['ck3-screen:acquired']
        with self.assertRaisesRegex(ValueError,'independent bus'):self.validate(bundle,events,changed,release)
        with self.assertRaisesRegex(ValueError,'durable bus'):self.validate(bundle,events[:1],packet,release)

    def test_later_local_id_blocks_first_machine_bootstrap_even_with_empty_artifacts(self):
        bundle,events,packet,release=self.fixture()
        path=self.root/'id-state'/self.machine/'vanilla/allocations.jsonl'
        with path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps({'schema':'xar.ck3-live-run-identity.v1','machine_id':self.machine,
                'run_id':'later-red','allocated_at_utc':'2026-10-09T12:00:00+00:00'})+'\n')
        with self.assertRaisesRegex(ValueError,'later local live identity'):self.validate(bundle,events,packet,release)

    def test_global_bootstrap_intent_survives_failure_and_new_runtime_directory(self):
        args=SimpleNamespace(previous_live=None)
        closure={'mode':'first-machine-legacy-profile-mcp-closure'}
        first=allocation.claim_machine_admission(self.binding,self.selection,args,closure)
        self.assertTrue((first/'intent.json').is_file())
        self.selection.runtime_path=Path(self.root/'another-empty-root/runtime.json')
        self.put(self.selection.runtime_path,{'new':'directory'})
        with self.assertRaisesRegex(ValueError,'already consumed'):
            allocation.claim_machine_admission(self.binding,self.selection,args,closure)
        with self.assertRaises(FileNotFoundError):
            allocation.claim_machine_admission(self.binding,self.selection,SimpleNamespace(previous_live=self.root/'old'),
                                               {'mode':'previous-shared-managed-session'})

    def test_routine_allocation_cannot_select_old_closed_run_before_latest_red(self):
        record=allocation.claim_machine_admission(self.binding,self.selection,SimpleNamespace(previous_live=None),
                                                  {'mode':'first-machine-legacy-profile-mcp-closure'})
        self.put(record/'allocation.json',{'run_id':'latest-red','live':str(self.root/'latest-red')})
        with self.assertRaisesRegex(ValueError,'latest machine allocation'):
            allocation.claim_machine_admission(self.binding,self.selection,SimpleNamespace(previous_live=self.root/'older-green'),
                                               {'mode':'previous-shared-managed-session'})

    def test_machine_and_state_overrides_cannot_start_another_first_epoch(self):
        for key in (ids.MACHINE_ENV,ids.STATE_ROOT_ENV):
            with patch.dict(os.environ,{key:'synthetic-override'}):
                with self.assertRaisesRegex(ValueError,'environment overrides'):
                    allocation.actual_machine_binding(ids)

    def test_bus_history_retains_shared_registration_despite_later_summary_change(self):
        bus=self.root/'bus';bus.mkdir()
        rows=[{'schema':'codex.task_bus.v1','sequence':1,'kind':'registered',
               'summary':'vanilla case shared runtime acceptance'},
              {'schema':'codex.task_bus.v1','sequence':2,'kind':'completed','summary':'historical RED'}]
        (bus/'events.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n',encoding='utf-8')
        events,shared=allocation.shared_bus_history(bus)
        self.assertEqual(len(events),2);self.assertEqual(len(shared),1)

    def test_python_controller_inventory_checks_actual_run_argument_and_new_keeper(self):
        class Process:
            def __init__(self,pid,name,argv):self.pid=pid;self.info={'pid':pid,'name':name};self.argv=argv
            def cmdline(self):return self.argv
        fake=SimpleNamespace(process_iter=lambda _:iter([
            Process(10,'python.exe',['python','-B','tools/ck3_mod_acceptance.py','run','--runtime','config']),
            Process(11,'python.exe',['python','tools/ck3_mod_acceptance_keeper.py']),
            Process(12,'python.exe',['python','ordinary-build.py']),Process(13,'ck3.exe',[])]),
            NoSuchProcess=type('NoSuchProcess',(Exception,),{}),AccessDenied=type('AccessDenied',(Exception,),{}))
        result=allocation.runtime_process_inventory(fake,999)
        self.assertEqual({row['pid'] for row in result['blockers']},{10,11,13})
        self.assertIs(result['process_absence_is_normal_exit_proof'],False)


if __name__=='__main__':unittest.main()
