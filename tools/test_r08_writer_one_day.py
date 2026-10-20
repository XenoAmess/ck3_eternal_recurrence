"""Deterministic public routing and refusal tests, not native qualification."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import copy
import json
import sys
import tempfile
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parent),
               str(Path(__file__).resolve().parents[1]/'ck3_autonomous_player/src')]
from ck3_mod_acceptance_cases import r08_writer_one_day as actor
from ck3_mod_acceptance_cases import r10_prepare_adapter as r10
from ck3_mod_acceptance_cases import r08_writer_controller as controller
from ck3_mod_acceptance_cases import r08_writer_common_adapter as bridge


class Client:
    def __init__(self, root):
        self.output=Path(root); self._process={'pid':41}; self._handle=1
        self.selection=SimpleNamespace(locations={'python':sys.executable},
            state_dir=self.output/'profile',run_dir=self.output/'RUN')
        self._binding=(41,2,3); self.frozen={};self.closed=[];self.selection.prepared={}
    def normal_close(self, disposition): self.closed.append(disposition);return {'called':True}
    def guard(self): pass
    def retain_process(self): return self._process
    def remaining(self): return 5000
    def read_report(self):return {}
    def checkpoint(self, name, value):
        path=self.output/(name+'.json');bridge.write_new(path,value);return path


def inputs(root):
    return dict(scene_root=str(root),source_head='1'*40,native_build_source_head='2'*40,
        build_dir=str(Path(root)/'build'),machine_execution_gate={'path':str(Path(root)/'gate.json'),'bytes':3,'sha256':'0'*64},
        actor_id=3,expected_start_date_raw=100,expected_source_save_sha256='3'*64,
        profile_limit_bytes=1000,driver_limit_bytes=2000,
        deadline_utc=(datetime.now(timezone.utc)+timedelta(hours=2)).isoformat(),prefix='r08-test',
        payment_enable_once_authorized=False,admission_timeout_seconds=1)


class PublicHook(unittest.TestCase):
    def test_actual_r10_dispatch_uses_original_client_and_excludes_other_continuations(self):
        with tempfile.TemporaryDirectory() as root:
            c=Client(root); frame={'diagnostics':{'bridge_pid':41,'connection_generation':2},
                'played_character':{'character_id':3},'episode_run_id':None}
            context=dict(output=root,case_inputs={'r08_writer_one_day':inputs(root),
                'normal_checkpoint_receipt':{'sha256':'0'*64},'director_scope_revision':'reviewed'},
                shared_game={'version':'1.20.0.4','exe_sha256':'0'*64})
            relay=SimpleNamespace(client=SimpleNamespace(snapshot=lambda:frame))
            with patch.object(r10,'validate_contract'),patch.object(r10,'CommonRequestRelay',return_value=relay), \
                 patch.object(r10,'small_json'),patch.object(r10,'collect_ready_t0',return_value={}), \
                 patch.object(bridge,'retained_creation_filetime',return_value=99), \
                 patch('ck3_live_run_id.current_machine_id',return_value='machine-test'), \
                 patch.object(actor,'run_case',return_value={'full_R08_qualified':False}) as run:
                result=r10.run_case(context,c)
            run.assert_called_once_with(context,c)
            self.assertFalse(result['research_card_closed'])
            self.assertFalse(result['r08_writer_one_day']['full_R08_qualified'])
            context['case_contract']={'schema':'xar.e04.r10-common-preparation.v1'}
            for other in ('r04_county_entry','r06_refill_one_day'):
                context['case_inputs'][other]={}
                with self.assertRaisesRegex(ValueError,'mutually exclusive'):r10.validate_contract(context)
                del context['case_inputs'][other]

    def test_no_grant_times_out_without_observer_and_close_is_instance_local(self):
        with tempfile.TemporaryDirectory() as root:
            c=Client(root); other=Client(root); gate=actor.CloseGate(c)
            a=actor.settings(inputs(root)); ticks=iter([0,0,2])
            with self.assertRaises(TimeoutError):
                actor.wait_admission({'run_id':'RUN'},c,a,{'expected':dict(machine='machine-test',pid=41,created=99,
                    generation=2,episode=None,character_id=3,window=4,epoch=5,date=100),'receipt':{}},{},
                    clock=lambda:next(ticks),sleep=lambda _:None)
            self.assertFalse((Path(root)/'r08-writer-control').exists())
            with self.assertRaisesRegex(ValueError,'OFF-clear'):c.normal_close('pending')
            other.normal_close('other-case');self.assertEqual(other.closed,['other-case'])
            gate.off_clear=True;c.normal_close('restored');self.assertEqual(c.closed,['restored'])
            gate.restored=False
            with self.assertRaises(ValueError):c.normal_close('attached')

    def test_root_grant_rejects_foreign_identity_capacity_and_typed_null(self):
        with tempfile.TemporaryDirectory() as root:
            c=Client(root); a=actor.settings(inputs(root));x=dict(machine='machine-test')
            a.machine_execution_gate=bridge.write_new(Path(root)/'gate.json',{})
            cap=dict(machine_id='machine-test',admitted=True,budget_status='GREEN',run_id='RUN',
                source_head=a.source_head,scene_root=root,component_roots={'profile':str(c.selection.state_dir),'driver':str(c.selection.run_dir)},
                component_ceiling_bytes={'profile':1000,'driver':2000},quota_review_at_utc=a.deadline_utc,run_hard_deadline_utc=a.deadline_utc)
            capref=bridge.write_new(Path(root)/'cap.json',cap)
            identity={'path':'actual-identity','bytes':1,'sha256':'a'*64}
            binding={'pid':41,'episode_run_id':None}
            cfg=dict(scene_capacity=capref,watch={'expected':x,'watch_output_root':str(Path(root)/'watch'),
                'timeout_ms':30000,'max_slot_hits':128},root_identity=binding)
            auth=dict(schema=actor.AUTH_SCHEMA,status=actor.AUTH_STATUS,admitted=True,external_debugger_allowed=True,
                scope='independent-unfilmed-cd-writer-window',r06_probe_concurrent=False,scene_capacity=capref,
                runtime_identity=identity,machine_id='machine-test',source_head=a.source_head,runtime_source_head=a.source_head,
                native_build_source_head=a.native_build_source_head,run_id='RUN',expected_root_identity=binding,
                overrides_observer_policy_of_sha256=capref['sha256'],scene_root=root,watch_output_root=cfg['watch']['watch_output_root'],
                quota_review_at_utc=a.deadline_utc,maximum_watch_ms=30000,maximum_aggregate_slot_hits=128,
                payment_window_policy='preserve_existing_owned_window_no_enable_clear')
            cfg['observer_admission']=bridge.write_new(Path(root)/'grant-good.json',auth)
            actor.root_window_guard({'run_id':'RUN'},c,cfg,a,identity)
            for index, changed in enumerate((dict(machine_id='foreign'),dict(runtime_identity={}),
                dict(expected_root_identity={'pid':41,'episode_run_id':'RUN'}),dict(maximum_watch_ms=30001))):
                wrong={**auth,**changed};cfg['observer_admission']=bridge.write_new(Path(root)/('bad-'+str(index)+'.json'),wrong)
                with self.assertRaises(ValueError):actor.root_window_guard({'run_id':'RUN'},c,cfg,a,identity)

    def test_unknown_day_is_never_replayed_and_original_error_and_after_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            m=actor.load_controller();control=Path(root)/'control';control.mkdir();watch=control/'watch';watch.mkdir()
            expected=dict(pid=41,created=99,generation=2,window=4,epoch=5,character_id=3,date=100,episode=None,machine='machine-test')
            cashpath=Path(root)/'cash.json'
            bridge.write_new(cashpath,{'body':{'war_payment_observations_v1':{'current_session':{
                'pid':41,'process_create_time_100ns':99,'connection_generation':2,'loaded_game_epoch':8,
                'controlled_window_id':4,'same_owned_process_no_load_window':True,
                'game_state_identity_witness':7,'player_character_full_id':3}}}})
            beforepath=Path(root)/'before.json';bridge.write_new(beforepath,{})
            cfg={'request_prefix':'r08-test','control_root':str(control),'watch':{'expected':expected,'build_dir':root,
                'owner_binding_mode':actor.MODE,'watch_output_root':str(watch),'cash_response':str(cashpath),'before_response':str(beforepath)}}
            cfgpin=bridge.write_new(Path(root)/'cfg.json',cfg)
            bridge.write_new(control/'ROOT-ARGV.actual.json',{})
            admission={'prepare_only':True,'schema':'xar.maintenance.writer_pc.future-admission.v2','expected_episode':None,
                'owner_binding':{'mode':actor.MODE},'expected_root_identity':{k:expected[v] for k,v in (
                    ('pid','pid'),('process_create_time_100ns','created'),('connection_generation','generation'),
                    ('controlled_window_id','window'),('player_character_full_id','character_id'))},'expected_payment_epoch':5}
            admission['argv']=[str(Path(root)/'maintenance_writer_cold_observer.exe'),'--enable-ck3-12004-data-watch',
                '--fixture-meta',str(watch/'CURRENT-RAW-ADMISSION.meta.txt'),'--timeout-ms','30000','--raw',str(watch/'writer.raw.ndjson'),
                '--ready',str(watch/'writer.ready.json'),'--expected-hits','128','--machine-id','machine-test','--ordinary-null-owner-binding']
            admref=bridge.write_new(watch/'ADMISSION.actual.json',admission)
            bridge.write_new(control/'PREPARE-RESULT.actual.json',{'returncode':0,'observer_started':False,'config':cfgpin,'admission':admref})
            calls=[]
            def request(name,tool,args):
                calls.append((name,tool,args))
                if tool=='ck3_execute_step':raise TimeoutError('synthetic unknown original response')
                if tool=='ck3_take_snapshot':
                    frame={'map_ready':True,'paused':True,'played_character':{'alive':True,'character_id':3},
                        'episode_run_id':None,'revision':1,'diagnostics':{'bridge_pid':41,'connection_generation':2},
                        'date_raw':124 if name.endswith('independent-after') else 100}
                    return frame,{'path':'test-original-'+name}
                return {},{'path':'test-original-'+name}
            consumer=Path(root)/m.RESEARCH/'consume_writer_actual.py';consumer.parent.mkdir(parents=True)
            consumer.write_text('# synthetic unexecuted consumer pin\n',encoding='utf8')
            rt=SimpleNamespace(repo=Path(root),c={'expected_start_date_raw':100,'maximum_days':1},guard=lambda:None,request=request)
            process=SimpleNamespace(pid=42,poll=lambda:None)
            with patch.object(m,'load_config',return_value=cfg),patch.object(m,'RootRuntime',return_value=rt), \
                 patch.object(m,'load_module',return_value=SimpleNamespace(configure=lambda _:None,bind_inputs=lambda *args:None)), \
                 patch.object(m.subprocess,'Popen',return_value=process) as popen,patch.object(m,'await_ready',return_value={'ready':True}), \
                 patch.object(m,'check_cash',return_value={}),patch.object(m,'finalize',side_effect=ValueError('synthetic consumer rejected original raw')):
                session,result=m.observe_prepared(cfgpin)
                with self.assertRaisesRegex(ValueError,'Prepared new control'):m.observe_prepared(cfgpin)
            session.stdout.close();session.stderr.close()
            self.assertEqual(popen.call_count,1)
            self.assertEqual(sum(tool=='ck3_execute_step' for _,tool,_ in calls),1,result)
            self.assertFalse(result['day']['exact_day_qualified'])
            self.assertIn('never', (control/'day.once.json').read_text(encoding='utf8'))
            preserved=json.loads((control/'ROOT-WINDOW-RESULT.actual.json').read_bytes())
            self.assertIn('unknown',preserved['primary_error'])
            self.assertTrue(preserved['day']['after']['path'].endswith('independent-after'))
            self.assertFalse(preserved['safe_to_begin_normal_close'])
            self.assertIn('consumer rejected',preserved['observer']['error'])

    def test_prepare_failure_and_unknown_start_preserve_terminal_without_false_cleanup(self):
        for unknown_start in (False,True):
            with self.subTest(unknown_start=unknown_start),tempfile.TemporaryDirectory() as root:
                c=Client(root);settings=inputs(root);context=dict(repo_root=root,run_id='RUN',output=root,
                    case_inputs={'r08_writer_one_day':settings})
                frame=dict(episode_run_id=None,episode_projection='native_campaign',paused=True,map_ready=True,
                    played_character={'character_id':3},date_raw=100,revision=1)
                requests=[]
                class Packets:
                    def __init__(self,*args,**kwargs):pass
                    def request(self,name,tool,args):
                        requests.append((name,tool,args))
                        if tool=='ck3_take_snapshot':return frame,{}
                        if tool=='ck3_execute_step':return {'tactical_daily_sentinel':{}},{}
                        return {},{}
                legacy=SimpleNamespace(SELECTOR=None,expected_binding=lambda _:{},
                    prepare=lambda _:None if unknown_start else (_ for _ in ()).throw(ValueError('synthetic prepare refused')))
                def observe(_):
                    path=Path(root)/'r08-writer-control';path.mkdir()
                    bridge.write_new(path/'observer-start.once.json',{'unknown':True})
                    raise OSError('synthetic Popen unknown')
                legacy.observe_prepared=observe
                actual={'expected':dict(date=100,character_id=3,machine='machine-test'),
                    'common_retained_process':{'pid':41},'receipt':{},'before_response':{'path':'before'},'cash_response':{'path':'cash'}}
                def normalize(body,*,snapshot,payment_sampling):
                    if payment_sampling=='disable':raise ValueError('synthetic disable failed with original row retained')
                    return {'war_payment_observations_v1':{'sampling':{'capture_enabled':True}}}
                with patch.object(actor.subprocess,'check_output',return_value='1'*40), \
                     patch('ck3_live_run_id.current_machine_id',return_value='machine-test'), \
                     patch.object(actor,'load_controller',return_value=legacy),patch.object(bridge,'CommonPackets',Packets), \
                     patch.object(bridge,'collect_current_context',return_value=actual),patch.object(bridge,'bind_legacy_driver'), \
                     patch.object(actor,'wait_admission',return_value=({}, {'scene_capacity':{}})), \
                     patch.object(actor,'small_json',return_value={}),patch.object(actor,'pin',return_value={}), \
                     patch.object(actor.common,'actual_binding',return_value={}),patch.object(actor.common,'bound_saved_campaign_source',return_value={}), \
                     patch('xar_autoplayer.bridge.war_payment_observations_v1.normalize_payment_extras',side_effect=normalize), \
                     patch('xar_autoplayer.bridge.native_driver._normalize_tactical_daily_sentinel_status',return_value={'state':'idle'}):
                    result=actor.run_case(context,c)
                terminal=json.loads((Path(root)/'R08-WRITER-TERMINAL.json').read_bytes())
                self.assertFalse(terminal['full_R08_qualified']);self.assertFalse(terminal['Save']);self.assertFalse(terminal['OFFclear'])
                self.assertEqual(terminal['native_restore_verified'],not unknown_start)
                self.assertTrue(result['errors'])
                self.assertFalse(any(tool=='ck3_save_checkpoint' for _,tool,_ in requests))
                self.assertEqual(sum(args.get('payment_sampling')=='disable' for _,_,args in requests),0 if unknown_start else 1)
                with self.assertRaises(ValueError):c.normal_close('not-authorized')


if __name__=='__main__':unittest.main()
