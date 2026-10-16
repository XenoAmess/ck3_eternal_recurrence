"""Portable synthetic C operation regressions; no CK3, SDK or desktop access."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace, ModuleType
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
GUARD=HERE.parent/'runtime_binding.py'

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

candidate=module(HERE/'operation_root_relay.py','portable_C_operation_subject')

def pinned(path):
    raw=Path(path).read_bytes()
    return {'path':str(Path(path).resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

class Fixture:
    def __init__(self,root):
        self.root=root;self.repo=root/'repo';self.repo.mkdir()
        self.scene=root/'new-scene';self.scene.mkdir()
        self.now=datetime(2031,1,1,12,tzinfo=timezone.utc)
        self.machine='SYNTHETIC-portable-machine';self.source='a'*40
        self.run_id=self.machine+'--vanilla--R0007'
        self.run=self.scene/self.run_id
        (self.run/'requests').mkdir(parents=True);(self.run/'responses').mkdir()
        verify=self.repo/candidate.VERIFY_REL;verify.parent.mkdir(parents=True)
        verify.write_text('SYNTHETIC = True\n')
        self.life={'lifecycle':'ordinary_campaign_succession','xar_enabled':'xar_off'}
        self.context={'machine_id':self.machine,'source_head':self.source,'identity':{
            'machine_id':self.machine,'sequence':7,'run_id':self.run_id,'mod_key':'vanilla'}}
        self.proof={'machine_id':self.machine,'source_head':self.source,'run_id':self.run_id,
            'pid':901,'process_creation_filetime_100ns':134000000000000123,'connection_generation':1,
            'actual_runtime_character_full_id':42,'episode_run_id':'synthetic-new-cold-42',
            'stable_character_intent':{'historical_id':1128,
                'bookmark_character_name_key':'bookmark_rags_to_riches_duke_robert'}}
        self.runtime={'source_head':self.source,'native_dll_sha256':'d'*64,
            'started_at_utc':(self.now-timedelta(minutes=2)).isoformat()}
        self.plan={'status':'frozen','frozen_at_utc':(self.now-timedelta(minutes=4)).isoformat(),
            'build':{'source_head':self.source,'native_dll_sha256':'d'*64},'t0_raw':123456,
            'normal_save':{'kind':'normal-native-checkpoint','sha256':'b'*64,'bytes':1234},
            'strategies':{'C':{'mode':'whole-via'}}}
        self.prepared={'prepared_at':(self.now-timedelta(minutes=3)).isoformat(),
            'machine_id':self.machine,'assets_root':str(self.scene),'succession_lifecycle':self.life,
            'checkpoint':{'source':{'save':{'sha256':'b'*64,'bytes':1234},'date_raw':123456,
                'actor_id':42,'source_lifecycle':self.life}}}
        state=self.scene/'state-a02'
        (state/'native-session/army-query-history-results').mkdir(parents=True)
        self.prepared['state_dir']=str(state)
        self.capacity={'admitted':True,'machine_id':self.machine,'source_head':self.source,'run_id':self.run_id,
            'scene_root':str(self.scene),'policy_version':'1.0.0','source_binding':{'new_clean_integrated_source_head':self.source},
            'root_atomic_adoption_required':False,'root_adopted_at_utc':(self.now-timedelta(minutes=1)).isoformat(),
            'quota_review_at_utc':(self.now+timedelta(minutes=30)).isoformat(),
            'component_ceiling_bytes':{'driver':128*1024*1024},'new_scene_aggregate_bytes':256*1024*1024}
        self.context['capacity_admission']=str(self.scene/'capacity.json')
        self.document={'schema':'xar.e04.live-operation-binding.v1','operation_id':'SYNTHETIC-C-7',
            'machine_id':self.machine,'run_id':self.run_id,'run_sequence':7,'source_head':self.source,
            'scene_root':str(self.scene),'created_at_utc':self.now.isoformat(),
            'deadline_utc':self.capacity['quota_review_at_utc'],'normal_save_sha256':'b'*64,
            'runtime':{'pid':901,'process_create_time_100ns':134000000000000123,
                'generation':1,'actor':42,'episode':'synthetic-new-cold-42'},
            'max_runtime_total_bytes':64*1024*1024,'guard_sha256':pinned(GUARD)['sha256']}
        self.args=SimpleNamespace(repo=self.repo,context=self.scene/'context.json',
            runtime_proof=self.scene/'proof.json',plan=self.scene/'plan.json',prepared=self.scene/'prepared.json',
            runtime_guard=GUARD,runtime_guard_sha256=pinned(GUARD)['sha256'],live_binding=self.scene/'operation.json',
            runtime=self.runtime,source_head=self.source,run_id=self.run_id,run_sequence=7,
            loaded_save_sha256='b'*64,max_runtime_total_bytes=64*1024*1024,
            deadline_utc=self.capacity['quota_review_at_utc'],army_id=0,card='C',case_id='SYNTHETIC-C',
            attempt='stage-a01',stage='admit',request_helper=self.scene/'helper.py')
        self.args.request_helper.write_text('# synthetic; never imported\n')
        self.transport=SimpleNamespace(RUN=self.run,ASSETS=self.scene,CONTEXT=self.context)
        self.calls=[]
        def request(identifier,tool,arguments,timeout):
            self.calls.append((identifier,tool,arguments))
            req={'request_id':identifier,'tool':tool,'arguments':arguments}
            row={'machine_id':self.machine,'request':req,'is_error':False,'body':{'accepted':True}}
            (self.run/'requests'/(identifier+'.json')).write_text(json.dumps(req))
            (self.run/'responses'/(identifier+'.json')).write_text(json.dumps(row))
            return row
        self.transport.request=request
        self.flush()

    def put(self,path,value):
        path.write_text(json.dumps(value),encoding='utf-8');return pinned(path)

    def flush(self):
        self.put(self.scene/'capacity.json',self.capacity)
        self.document['capacity_admission']=pinned(self.scene/'capacity.json')
        for key,value in [('context',self.context),('runtime_proof',self.proof),('plan',self.plan),('prepared',self.prepared)]:
            ref=self.put(getattr(self.args,key),value);setattr(self.args,key+'_sha256',ref['sha256'])
        self.args.live_binding_sha256=self.put(self.args.live_binding,self.document)['sha256']
        self.args.request_helper_sha256=pinned(self.args.request_helper)['sha256']

    def construct(self,*,process_value=134000000000000123):
        with patch.object(candidate.subprocess,'run',return_value=SimpleNamespace(stdout=self.source+'\n')):
            return candidate.Live(self.args,transport=self.transport,process_probe=lambda pid:process_value,
                machine_probe=lambda repo:self.machine,clock=lambda:self.now)


class ConstructorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='SYNTHETIC-C-operation-')
        self.addCleanup(self.temp.cleanup);self.f=Fixture(Path(self.temp.name))

    def test_normal_constructor_accepts_explicit_new_machine_and_low_allocated_sequence(self):
        io=self.f.construct()
        self.assertEqual(io.machine,'SYNTHETIC-portable-machine')
        self.assertEqual(io.binding['army_id'],0)
        self.assertEqual(io.binding['process_create_time_100ns'],134000000000000123)
        self.assertFalse(io.meta['fresh_C_arm_qualified']);self.assertFalse(io.meta['R10_completed'])
        self.assertFalse(self.f.calls)

    def test_old_continuation_or_unfrozen_plan_refused_before_transport(self):
        self.f.runtime['started_at_utc']=self.f.plan['frozen_at_utc']
        with self.assertRaisesRegex(RuntimeError,'continuation'):
            self.f.construct()
        self.assertFalse(self.f.calls)
        self.assertFalse((self.f.scene/'strategy-c-phased-a03').exists())
        self.f.runtime['started_at_utc']=(self.f.now-timedelta(minutes=2)).isoformat()
        self.f.plan['status']='draft';self.f.flush()
        with self.assertRaisesRegex(RuntimeError,'formal frozen'):
            self.f.construct()

    def test_prepared_save_sha_date_actor_bytes_and_lifecycle_are_independent(self):
        original=deepcopy(self.f.prepared)
        changes=[lambda p:p['checkpoint']['source']['save'].update(sha256='c'*64),
            lambda p:p['checkpoint']['source']['save'].update(bytes=1235),
            lambda p:p['checkpoint']['source'].update(date_raw=123480),
            lambda p:p['checkpoint']['source'].update(actor_id=43),
            lambda p:p['checkpoint']['source'].update(source_lifecycle={'lifecycle':'fixture'}),
            lambda p:p.update(succession_lifecycle={'lifecycle':'ordinary_campaign_succession','xar_enabled':'xar_on'})]
        for index,change in enumerate(changes):
            self.f.prepared=deepcopy(original);change(self.f.prepared);self.f.flush()
            with self.subTest(index=index),self.assertRaises(RuntimeError):self.f.construct()
        self.assertFalse(self.f.calls)

    def test_wrong_machine_run_source_DLL_and_process_lifetime_refused(self):
        original=deepcopy(self.f.proof)
        for key,value in [('machine_id','foreign'),('run_id','old-run'),('source_head','f'*40),('pid',902),
                          ('process_creation_filetime_100ns',134000000000000124),('connection_generation',2),
                          ('actual_runtime_character_full_id',43),('episode_run_id','old-episode')]:
            self.f.proof=deepcopy(original);self.f.proof[key]=value;self.f.flush()
            with self.subTest(key=key),self.assertRaises((ValueError,RuntimeError)):self.f.construct()
        self.f.proof=original;self.f.runtime['native_dll_sha256']='e'*64;self.f.flush()
        with self.assertRaisesRegex(RuntimeError,'DLL'):
            self.f.construct()
        self.assertFalse(self.f.calls)

    def test_actual_PID_creation_probe_is_not_replaced_by_matching_metadata(self):
        with self.assertRaisesRegex(RuntimeError,'PID/create-time'):
            self.f.construct(process_value=134000000000000124)
        self.assertFalse(self.f.calls)

    def test_expired_candidate_or_wrong_scene_capacity_refused(self):
        self.f.now+=timedelta(minutes=30)
        with self.assertRaisesRegex(ValueError,'expired'):
            self.f.construct()
        self.f.now-=timedelta(minutes=30)
        self.f.capacity['root_atomic_adoption_required']=True;self.f.flush()
        with self.assertRaisesRegex(ValueError,'Root-adopted'):
            self.f.construct()
        self.f.capacity['root_atomic_adoption_required']=False
        self.f.capacity['scene_root']=str(self.f.scene/'old');self.f.flush()
        with self.assertRaisesRegex(ValueError,'another scene'):
            self.f.construct()

    def test_unknown_submission_once_claim_is_not_replayed_on_new_attempt(self):
        io=self.f.construct();calls=[]
        def timeout(identifier,tool,arguments,timeout):
            calls.append(identifier)
            (self.f.run/'requests'/(identifier+'.json')).write_text(json.dumps({'request_id':identifier}))
            raise TimeoutError('SYNTHETIC original result unknown')
        self.f.transport.request=timeout
        with self.assertRaises(TimeoutError):io.action('initial-move','ck3_move_army',{}, {})
        self.assertTrue((io.case/'initial-move.once.claim.json').exists())
        self.f.args.attempt='stage-a02'
        second=self.f.construct()
        with self.assertRaises(FileExistsError):second.action('initial-move','ck3_move_army',{}, {})
        self.assertEqual(len(calls),1)

    def test_guard_revalidates_capacity_hash_and_deadline_before_every_request(self):
        io=self.f.construct()
        self.f.capacity['admitted']=False;self.f.put(self.f.scene/'capacity.json',self.f.capacity)
        with self.assertRaisesRegex(ValueError,'SHA'):
            io.request('fresh','ck3_take_snapshot',{})
        self.assertFalse(self.f.calls)
        self.f.put(self.f.scene/'capacity.json',{**self.f.capacity,'admitted':True})
        self.f.now+=timedelta(minutes=30)
        with self.assertRaisesRegex(ValueError,'expired'):
            io.request('fresh','ck3_take_snapshot',{})
        self.assertFalse(self.f.calls)

    def test_case_cannot_adopt_history_or_replace_its_operation(self):
        case=self.f.scene/'strategy-c-phased-a03'/self.f.args.case_id
        case.mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError,'historical'):
            self.f.construct()
        case.rmdir();self.f.construct()
        self.f.document['operation_id']='SYNTHETIC-replaced';self.f.args.attempt='stage-a02';self.f.flush()
        with self.assertRaisesRegex(RuntimeError,'C case operation'):
            self.f.construct()

    def test_response_machine_identity_and_complete_sidecar_budget_are_enforced(self):
        io=self.f.construct()
        def foreign(identifier,tool,arguments,timeout):
            req={'request_id':identifier};row={'machine_id':'foreign','is_error':False,'request':req}
            (self.f.run/'requests'/(identifier+'.json')).write_text(json.dumps(req))
            (self.f.run/'responses'/(identifier+'.json')).write_text(json.dumps(row));return row
        self.f.transport.request=foreign
        with self.assertRaisesRegex(RuntimeError,'response error/machine'):
            io.request('foreign','ck3_take_snapshot',{})
        # Meter refusal is exercised with small declared limit; no large file.
        io.runtime_total_budget_bytes=1
        with self.assertRaisesRegex(RuntimeError,'cannot reserve'):
            io.request('bounded','ck3_query_army_strengths',{})


    def test_actual_state_a02_driver_reference_and_sidecar_are_used(self):
        io=self.f.construct()
        self.assertEqual(io.state_dir,Path(self.f.prepared['state_dir']).resolve())
        self.assertEqual(io.native_session,self.f.scene/'state-a02/native-session')
        before=io.used_bytes()
        stale=self.f.scene/'state-a01/native-session'
        stale.mkdir(parents=True)
        (stale/'old.json').write_text('old state is not active')
        self.assertEqual(io.used_bytes(),before)
        raw=io.native_session/'army-query-history-results/current.json'
        query={'army_strengths_profile':'ordinary_core_v1','query_sequence':1,
            'army_strengths_query_scope':{'army_ids':[0]},
            'army_strengths':[{'army_id':0,'native_carmy_id':77}]}
        ref=self.f.put(raw,query)
        self.assertEqual(io.used_bytes(),before+ref['bytes'])
        snapshot={'snapshot_id':'synthetic-a02-F','revision':10,'native_revision':9,'date_raw':123456,
            'paused':True,'map_ready':True,'episode_run_id':'synthetic-new-cold-42',
            'played_character':{'character_id':42,'alive':True},
            'diagnostics':{'bridge_pid':901,'connection_generation':1}}
        def request(identifier,tool,arguments,timeout):
            req={'request_id':identifier,'tool':tool,'arguments':arguments}
            row={'machine_id':self.f.machine,'is_error':False,'request':req,
                'body':snapshot if tool=='ck3_take_snapshot' else {}}
            if tool=='ck3_query_army_strengths':
                row['army_history_evidence']={'machine_id':self.f.machine,'request_id':identifier,
                    'query_sequence':1,'raw_result_reference':{**ref,
                        'kind':'complete-driver-army-query-result-json-v1','wire_bytes_preserved':False}}
            (self.f.run/'requests'/(identifier+'.json')).write_text(json.dumps(req))
            (self.f.run/'responses'/(identifier+'.json')).write_text(json.dumps(row))
            return row
        self.f.transport.request=request
        io.v=SimpleNamespace(frame=lambda s,q,b:{'snapshot':s,'strength':q,'native_carmy_id':b['native_carmy_id']})
        observed,refs=io.frame('exact-state-a02')
        self.assertEqual(refs['strength']['path'],str(raw.resolve()))
        self.assertEqual(observed['native_carmy_id'],77)

    def test_whole_run_mcp_root_payload_blocks_next_request_at_budget(self):
        io=self.f.construct();before=io.used_bytes()
        payload=b'SYNTHETIC-duplicate-MCP-ledger\n'*256
        (self.f.run/'mcp-calls.jsonl').write_bytes(payload)
        self.assertEqual(io.used_bytes(),before+len(payload))
        reserve=candidate.MAX_RESPONSE+65536
        io.runtime_total_budget_bytes=before+reserve+len(payload)-1
        with self.assertRaisesRegex(RuntimeError,'cannot reserve'):
            io.request('bounded-after-mcp','ck3_take_snapshot',{})
        self.assertFalse(self.f.calls)
        self.assertFalse(list((self.f.run/'requests').iterdir()))

    def test_prepared_state_outside_admitted_scene_is_refused(self):
        self.f.prepared['state_dir']=str(self.f.root/'another-task-state')
        self.f.flush()
        with self.assertRaisesRegex(RuntimeError,'state/native-session escapes'):
            self.f.construct()
        self.assertFalse(self.f.calls)


class ProviderTests(unittest.TestCase):
    def test_real_provider_normally_constructs_relay_with_exact_bindings(self):
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC-C-provider-') as directory:
            f=Fixture(Path(directory));g=module(GUARD,'synthetic_provider_shared_guard')
            guard=g.OperationGuard(f.args.live_binding,f.args.live_binding_sha256,
                context=f.context,runtime=g.proof_runtime(f.proof),scene_root=f.scene,
                source_head=f.source,machine_id=f.machine,run_id=f.run_id,
                max_runtime_total_bytes=f.args.max_runtime_total_bytes,deadline_utc=f.args.deadline_utc,
                normal_save_sha256=f.args.loaded_save_sha256,clock=lambda:f.now)
            entry=module(HERE/'phased_relay.py','portable_C_phase_subject')
            synthetic=f.scene/'synthetic_reader.py';synthetic.write_text('SYNTHETIC = True\n')
            bundle={'machine_id':f.machine,'source_head':f.source,'deadline_utc':f.args.deadline_utc,
                'repo':str(f.repo),'runtime_request_budget_bytes':f.args.max_runtime_total_bytes,
                'army_id':0,'case_id':f.args.case_id,'evidence_roots':[str(f.scene)],'runtime':f.runtime,
                'current_loaded_features':{'SYNTHETIC_ONLY':True},
                'context':pinned(f.args.context),'runtime_proof':pinned(f.args.runtime_proof),
                'plan':pinned(f.args.plan),'prepared':pinned(f.args.prepared),
                'request_helper':pinned(f.args.request_helper),'capacity':pinned(f.scene/'capacity.json'),
                'live_binding':pinned(f.args.live_binding),'modules':{
                    'root_relay':pinned(HERE/'operation_root_relay.py'),
                    'dcda_coherent_reader':pinned(synthetic),'next_adapter':pinned(synthetic)}}
            constructions=[]
            def normal_constructor(args):
                constructions.append(args)
                return candidate.Live(args,transport=f.transport,
                    process_probe=lambda pid:134000000000000123,machine_probe=lambda repo:f.machine,
                    clock=lambda:f.now)
            facade=SimpleNamespace(OPERATION_BINDING_API=candidate.OPERATION_BINDING_API,Live=normal_constructor)
            delta=SimpleNamespace(Live=SimpleNamespace(strength_at=lambda *a:None,coherent_stop_core=lambda *a:None))
            def reviewed_import(path,name):
                return facade if Path(path)==HERE/'operation_root_relay.py' else delta
            top=ModuleType('xar_autoplayer');top.__path__=[]
            bridge=ModuleType('xar_autoplayer.bridge');bridge.__path__=[]
            fake_native=ModuleType('xar_autoplayer.bridge.native_driver')
            bridge.native_driver=fake_native
            with (patch.object(entry,'operation_guard',return_value=(g,guard)),
                  patch.object(entry,'module',side_effect=reviewed_import),
                  patch.object(candidate.subprocess,'run',return_value=SimpleNamespace(stdout=f.source+'\n')),
                  patch.dict(sys.modules,{'xar_autoplayer':top,'xar_autoplayer.bridge':bridge,
                                          'xar_autoplayer.bridge.native_driver':fake_native})):
                io,native=entry.provider(bundle,SimpleNamespace(attempt='stage-a01',stage='admit'))
            self.assertEqual(len(constructions),1)
            self.assertEqual(constructions[0].loaded_save_sha256,'b'*64)
            self.assertEqual(constructions[0].runtime_guard_sha256,pinned(GUARD)['sha256'])
            self.assertEqual(io.live_operation_guard.pin,pinned(f.args.live_binding))
            self.assertIs(native,fake_native);self.assertFalse(f.calls)
            self.assertEqual(io.meta['C_module_pins'],bundle['modules'])


if __name__=='__main__':unittest.main(verbosity=2)
