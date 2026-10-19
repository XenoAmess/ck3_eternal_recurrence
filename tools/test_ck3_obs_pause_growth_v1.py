"""Two focused RAM qualifications of the actual canonical pause-aware hunks."""
import ast
import copy
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

from ck3_obs_pause_growth_v1 import advance_growth_deadline_v1
from g2_saved_campaign import prepare_obs_pause_aware_capture_v1 as p

MACHINE = 'xenoamess-full-tower-eb9d2c1186'
CARD_SHA = 'a5c7214d00556f97d3f3ae6bfde5fc081877e1d5c4d9624bd823b9bb4e9ebfe0'


def unique(values, message):
    rows=list(values);p.require(len(rows)==1,message);return rows[0]


def node_code(node):
    return compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),
        'actual-canonical-growth-hunk','exec')


class Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output=p.compose();cls.tree=ast.parse(cls.output['canonical_capture_candidate'])

    def test_both_actual_gates_pause_resume_and_original_timeout(self):
        calls=[n for n in ast.walk(self.tree) if isinstance(n,ast.Assign)
            and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
            and n.value.func.id=='advance_growth_deadline_v1']
        self.assertEqual(len(calls),2)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module=='ck3_obs_pause_growth_v1'
            for n in ast.walk(self.tree)))
        inline=unique((n for n in self.tree.body if isinstance(n,ast.FunctionDef)
            and n.name=='advance_growth_deadline_v1'),'one inlined pure helper')
        local=unique((n for n in ast.parse(p.HELPER.read_bytes()).body if isinstance(n,ast.FunctionDef)
            and n.name=='advance_growth_deadline_v1'),'one maintenance helper')
        self.assertEqual(ast.dump(inline,include_attributes=False),ast.dump(local,include_attributes=False))
        for statement in calls:
            watch=any(isinstance(n,ast.Name) and n.id=='video' for n in ast.walk(statement))
            prior,changed,current,status=('previous','changed','video','growth_status') if watch else ('last_bytes','last_growth','current_bytes','status')
            clock=SimpleNamespace(now=0.0);clock.monotonic=lambda:clock.now
            scope={'advance_growth_deadline_v1':advance_growth_deadline_v1,'time':clock,
                prior:0,changed:0.0,'was_paused':False}
            code=node_code(statement)
            def observe(at,size,paused,active=True):
                clock.now=float(at);scope[current]=size
                item=SimpleNamespace(output_active=active)
                if paused is not None:item.output_paused=paused
                scope[status]=item;exec(code,scope)
            with self.subTest(gate='watch' if watch else 'main'):
                observe(0,100,False);observe(10,100,True);observe(100,100,True)
                observe(101,100,False)
                self.assertEqual(scope[changed],101.0)
                observe(130,100,False)
                with self.assertRaisesRegex(RuntimeError,'did not grow'):observe(132,100,False)
                # A missing/non-boolean pause, regressed bytes, or inactive OBS
                # never acquires indefinite pause privilege.
                for invalid in (None,1,'true',False):
                    scope.update({prior:100,changed:0.0,'was_paused':False})
                    with self.subTest(unverified_pause=invalid):
                        with self.assertRaisesRegex(RuntimeError,'did not grow'):observe(40,100,invalid)
                scope.update({prior:100,changed:0.0,'was_paused':True})
                with self.assertRaisesRegex(RuntimeError,'did not grow'):observe(40,99,True)
                scope.update({prior:100,changed:0.0,'was_paused':True})
                with self.assertRaisesRegex(RuntimeError,'ended before'):observe(40,100,True,False)

    def test_actual_watch_paused_STOP_and_owner_loss_preserve_single_owned_stop(self):
        clsnode=unique((n for n in self.tree.body if isinstance(n,ast.ClassDef) and n.name=='FileGrowthWatch'),'one actual watcher')
        for mode in ('STOP','owner_loss'):
            with self.subTest(mode=mode):
                observed={'iterations':0,'reads':0,'stop_attempts':0,'stop_commands':0,'disconnects':0,'generation_closed':0}
                clock=SimpleNamespace(now=0.0);clock.monotonic=lambda:clock.now
                class Event:
                    def __init__(self):self.value=False
                    def is_set(self):return self.value
                    def set(self):self.value=True
                    def wait(self,seconds):
                        observed['iterations']+=1;clock.now+=80
                        if mode=='owner_loss':generation.live=False
                class Generation:
                    live=True
                    def check(self):
                        if not self.live:raise RuntimeError('owned OBS generation ended')
                    def close(self):observed['generation_closed']+=1
                generation=Generation();main_client=object()
                class Client:
                    def get_record_status(self):
                        observed['reads']+=1
                        return SimpleNamespace(output_active=True,output_paused=True)
                    def disconnect(self):observed['disconnects']+=1
                class Peer:
                    def __init__(self,profile,job):self.profile=profile;self.job=job;self.client=None
                    def check(self):self.generation.check()
                    def connect(self):self.check();self.client=Client();return self.client
                class VirtualPath:
                    def __init__(self,name):self.name=name
                    def __truediv__(self,name):return VirtualPath(name)
                    def is_file(self):return mode=='STOP' and observed['iterations']>0
                def stop_owned(peer):
                    observed['stop_attempts']+=1
                    peer.check()
                    self.assertIsNot(peer.client,main_client)
                    observed['stop_commands']+=1
                    return 'SOURCE-FIXTURE-OWNED-OUTPUT'
                job={'continuous':True,'receipt_root':'SOURCE-FIXTURE-NOT-ACTUAL'}
                engine=SimpleNamespace(profile={},job=job,process=object(),generation=generation,client=main_client)
                scope={'OwnedEngine':Peer,'Path':VirtualPath,'time':clock,'datetime':datetime,'timezone':timezone,
                    'advance_growth_deadline_v1':advance_growth_deadline_v1,
                    '_disk_observation':lambda job:{'reserve_reached':False},
                    '_job_bytes':lambda job:(100,200),'_append_sample':lambda *args:None,
                    '_output_binding':lambda peer:peer.check(),'_stop_owned':stop_owned}
                exec(node_code(clsnode),scope)
                watch=scope['FileGrowthWatch'].__new__(scope['FileGrowthWatch'])
                watch.engine=engine;watch.seconds=None;watch.start_monotonic=0.0
                watch.requested=Event();watch.done=Event();watch.reason=watch.output=watch.error=None
                watch.stop_confirmed=False;watch.samples=[];watch.peak=0;watch.sample_summary={};watch.last_disk_observation=None
                watch.run()
                self.assertTrue(watch.done.is_set())
                self.assertIs(engine.client,main_client)
                self.assertEqual(observed['reads'],1)
                self.assertEqual(observed['stop_attempts'],1)
                self.assertEqual(observed['generation_closed'],0)
                if mode=='STOP':
                    self.assertEqual(observed['stop_commands'],1)
                    self.assertEqual(watch.reason,'owned_shutdown_requested')
                    self.assertTrue(watch.stop_confirmed);self.assertIsNone(watch.error)
                else:
                    self.assertEqual(observed['stop_commands'],0)
                    self.assertIn('generation ended',watch.error)
                    self.assertFalse(watch.stop_confirmed)


def pin(path):
    raw=path.read_bytes();return {'path':str(path.resolve()),'bytes':len(raw),'sha256':p.sha(raw)}


def qualify(proof_path,plan_path):
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Qualification))
    if not result.wasSuccessful():raise SystemExit(1)
    output=Qualification.output;candidate=output['canonical_capture_candidate']
    files=[pin(p.HELPER),pin(Path(p.__file__)),pin(Path(__file__))]
    now=datetime.now(timezone.utc)
    proof={'schema':'xar.OBS-pause-aware-two-growth-gates-source/v1','machine_id':MACHINE,
        'observed_at_utc':now.isoformat(),'status':'SOURCE_QUALIFIED_NOT_ADOPTED','tests_passed':result.testsRun,
        'files':files,'canonical_immutable_input':output['base'],
        'candidate_RAM_only':{'bytes':len(candidate),'sha256':p.sha(candidate)},
        'exact_inverse_restores_original_bytes':True,'actual_two_gate_AST_statements_tested':True,
        'actual_FileGrowthWatch_run_AST_tested':True,'test_environment':'pure RAM clock/filesystem/owned-OBS/WS doubles; zero real OBS',
        'long_pause_resume_then_real_stall':True,'unknown_pause_no_exemption':True,
        'paused_STOP_single_original_owned_stop':True,'owner_loss_not_hidden':True,
        'independent_watch_socket_main_socket_unchanged':True,'borrowed_generation_closed':False,
        'helper_inlined_no_runtime_companion_import':True,'original_stop_disk_deadline_order_retained':True,
        'canonical_or_C16_actual_worker_modified':False,'actual_C16_worker_reference':{
            'bytes':71575,'sha256':'20e40e58137ee40ee002e3e6b3cfb670addf12b62c6e2f7f666a4252601759b8'},
        'Game_OBS_SDK_Task_RPC_Git_D_operations':0,'old_test_matrices_repeated':False,
        'new_source_cap_bytes':32768,'old_canonical_reference_bytes':p.BASE_BYTES,
        'scratch_bytes':0,'actual_allocated_bytes':None,'physical_credit_bytes':0,
        'source_card_sha256':CARD_SHA,'record_review_at_utc':(now+timedelta(days=180)).isoformat(),
        'future_writes_after_freeze':0}
    proof_raw=(json.dumps(proof,indent=2)+'\n').encode()
    plan={'schema':'xar.OBS-pause-aware-canonical-source-plan/v1','machine_id':MACHINE,
        'observed_at_utc':now.isoformat(),'status':'RAM_CANDIDATE_ONLY_NO_LIVE_ADOPTION',
        'sources':files,'proof':{'path':str(proof_path.resolve()),'bytes':len(proof_raw),'sha256':p.sha(proof_raw)},
        'entry':'prepare_obs_pause_aware_capture_v1.compose() -> standalone full canonical capture bytes in RAM; never writes it',
        'base':output['base'],'candidate':proof['candidate_RAM_only'],
        'pure_helper_delivery':'exact pinned FunctionDef is embedded in capture; local math import; no companion file needed in worker copy',
        'future_canonical_adoption':'Root separately applies qualified RAM bytes to tools/ck3_obs_capture.py and freezes full source SHA',
        'future_managed_worker':'use that newly frozen standalone leaf through original capture producer/profile/sourcepin rules; do not patch or overwrite old C16 worker',
        'controlled_status_path':'OwnedEngine.check -> own profile/output binding -> own ReqClient.GetRecordStatus -> generation check; wire outputPaused maps to output_paused in obsws-python1.8.0',
        'pause_rule':'only strict owned active/paused with non-regressed bytes suspends growth deadline; real resume starts new grace; unknown keeps original timeout',
        'ownership':'watch owns its WS connection only; never shares main ReqClient or closes borrowed process generation',
        'STOP_disk_deadline':'original checks remain outside pause exemption; _stop_owned remains one original attempt',
        'runtime_permission':'none; not a clock recovery gate; Task pause/resume protocol and real OBS acceptance are separate',
        'storage':{'new_source_hard_bytes':32768,'old_reference_bytes':p.BASE_BYTES,
            'scratch_bytes':0,'old_plus_new_upper':102424,'allocated_bytes':None,'physical_credit_bytes':0,
            'source_card_sha256':CARD_SHA},'record_review_at_utc':proof['record_review_at_utc'],'future_writes_after_freeze':0}
    plan_raw=(json.dumps(plan,indent=2)+'\n').encode()
    new_gross=sum(row['bytes'] for row in files)+len(proof_raw)+len(plan_raw)
    p.require(new_gross<=32768,'new complete source cap exceeded')
    p.require(not proof_path.exists() and not plan_path.exists(),'source records are create-only')
    with proof_path.open('xb') as stream:stream.write(proof_raw)
    with plan_path.open('xb') as stream:stream.write(plan_raw)
    print(json.dumps({'new_complete_source_bytes':new_gross,'old_reference_bytes':p.BASE_BYTES,
        'complete_participating_logical_bytes':new_gross+p.BASE_BYTES,'scratch_bytes':0,
        'tests_passed':result.testsRun,'files':files,'RAM_candidate':proof['candidate_RAM_only'],
        'proof':{'bytes':len(proof_raw),'sha256':p.sha(proof_raw)},'plan':{'bytes':len(plan_raw),'sha256':p.sha(plan_raw)}}))


if __name__=='__main__':
    if len(sys.argv)!=3:raise ValueError('two new Z source record paths required')
    qualify(Path(sys.argv[1]),Path(sys.argv[2]))
