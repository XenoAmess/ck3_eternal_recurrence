"""F98 actual early-loop/finisher AST plus injected RAM I/O/OS/session.

No runtime write, Game/process/pipe/desktop action, or actual tool invocation.
The frozen Queue, failed responses and closure metadata are read-only inputs.
"""
import ast
import builtins
import copy
from contextlib import nullcontext
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import exact_clock10476_maintenance_v1 as o
from test_exact_clock10468_observe_reanchor_v1 import Ram, functions, encoded

RAW = o._raw


def build():
    ram=Ram()
    old=json.loads(RAW(o.F98/'state.json'))
    gov=json.loads(RAW(o.F98/'gov.json'))
    auto=json.loads(RAW(o.F98/'AUTO.json'))
    for leaf, source in (('ROOT-CUMULATIVE-LOOP-STATE.json','state.json'),('ROOT-GOVERNANCE-RESULT-STATE.json','gov.json')):
        ram.files[o.T/'p37-queue'/leaf]=RAW(o.F98/source)
    ram.files[o.T/'p37-responses/10476-1-result.json']=RAW(o.F98/'AUTO.json')
    ram.files[o.T/'NEXT-SEQUENCE-P37.json']=RAW(o.F98/'NEXT.json')
    ram.files[o.T/'STORAGE-ADMISSION.json']=encoded({'status':'ADMITTED','review_at_utc':'software-scope','disk_reserve_bytes':4096})
    ram.files[o.T/'ROOT-ACTUAL-DRIVER-MODE-P37C20.json']=encoded({'episode_projection':'one_life','before_submit_observation':True})
    ns={'__file__':str(o.T/'root_p37c20_sdk_queue.py'),'Path':Path,'json':json,'copy':copy,
        'N':o.T,'Q':o.T/'p37-queue','INBOX':o.T/'p37-requests','OUTBOX':o.T/'p37-responses',
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','SAVE':'ck3_save_checkpoint','AUTO':'ck3_auto_turn',
        'FRONTEND':('front0','front1','front2'),'CAPABILITIES':'caps','METRICS':'metrics','INITIAL_CAMERA':'camera',
        'REPLY_RESERVE':64*1024**2,'atomic':ram.atomic,'read':ram.read,
        'now':lambda:datetime.now(timezone.utc),'shutil':SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=2**40)),
        '_control_span_v1':lambda name:nullcontext()}
    raw=RAW(o.T/'root_p37c20_sdk_queue.py',1024**2)
    if hashlib.sha256(raw).hexdigest()!=o.QUEUE_SHA: raise ValueError('actual Queue differs')
    functions(raw,('decoded','frame','persist_loop_state','finish_cumulative_checkpoint','recover_partial_life_advance','check_after'),ns,last=('recover_partial_life_advance',))
    cadence=RAW(o.T/'root_p37_checkpoint_cadence.py')
    ns['STATE_KEY']='checkpoint_calendar_v1'
    functions(cadence,('_scope','checkpoint_saved'),ns)
    Queue=type('ActualEarlyQueueFixture',(),{name:ns[name] for name in ('persist_loop_state','finish_cumulative_checkpoint','recover_partial_life_advance','check_after')})
    q=Queue();q.full_loop_state=copy.deepcopy(old);q.governance_result_state=gov['state']
    q.lifestyle_pending_focus=gov['pending_focus'];q.result_classifier_pin=gov['classifier']
    q.expected_lifecycle_binding=old['actual_saved_checkpoint']['succession_lifecycle']
    q.checkpoint_lifecycle_matches=lambda value:value==q.expected_lifecycle_binding
    q.launch={'pid':o.GAME,'pipe':r'\\.\pipe\xar-g2-robert30-v20261019-campaign01'}
    q.job={'game_creation_filetime':o.BIRTH};q.record_job=o.T/'recordings/2b8912a6-757d-46a4-a8ae-b7702a730a90'
    q.halted={'request':auto['request'],'row':auto,'response':str(o.T/'p37-responses/10476-1-result.json')}
    q.current_attempt=copy.deepcopy(q.halted);q.next_sequence=10477;q.held_control=None
    q.recording_paused=True;q.semantic={'old_cache_not_current':True};q.initial_save=old['actual_saved_checkpoint']
    q.admission={'review_at_utc':'software-scope'};q.args=SimpleNamespace(artifact_cap_bytes=2**40)
    q.artifact_bytes=lambda:0;q.call_budget=lambda tool:12
    def poison(*a,**k):raise AssertionError('ordinary record guard/consume must not be bypassed or invoked')
    q.guard=q.consume_sequence=poison
    # Actual early dispatch branch, followed by the actual record-paused refusal.
    tree=ast.parse(raw)
    head=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and n.lineno==3409)
    head=copy.deepcopy(head);paused=copy.deepcopy(head.orelse[0].orelse[0]);paused.orelse=[];head.orelse=[paused]
    command=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and n.lineno==3392)
    fn=ast.AsyncFunctionDef(name='early',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=x) for x in ('queue','session','request','path')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[copy.deepcopy(command),head],decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),ns['__file__'],'exec'),ns)
    disp=ModuleType('root_saved_campaign_preflight');disp.__file__=str(o.T/'root_saved_campaign_preflight.py')
    disp.Path=Path;disp.hashlib=hashlib
    async def legacy(*a):raise AssertionError('old recovery contract must not run')
    disp.recover_zero_rpc_preflight=legacy
    transformed=o.transform_dispatcher_v1(RAW(o.T/'root_saved_campaign_preflight.py'),hashlib.sha256(RAW(Path(o.__file__))).hexdigest())
    suffix=transformed[len(RAW(o.T/'root_saved_campaign_preflight.py')):]
    builtins.exec(compile(suffix,disp.__file__,'exec'),disp.__dict__)
    def injected_exec(code,scope):
        builtins.exec(code,scope)
        scope['recover'].__kwdefaults__['birth_reader']=lambda pid:disp.births[pid]
        scope['_raw']=ram.raw;scope['_exists']=ram.exists
    disp.births=dict(o.LIVE)
    disp.__dict__['exec']=injected_exec
    ram.files[o.T/'root_c20_clock10476_maintenance.py']=RAW(Path(o.__file__))
    body={'snapshot_id':'native:4372','revision':8,'native_revision':4372,'date_raw':o.DATE,'paused':True,'map_ready':True,
          'played_character':{'alive':True,'character_id':40526},'episode_run_id':o.EPISODE,
          'one_life_terminal':False,'one_life_terminal_reason':None,'succession_lifecycle':q.expected_lifecycle_binding,
          'campaign_goal':copy.deepcopy(old['campaign_goal_anchor']),'active_event':{'new_fixture_event':True},
          'player_armies':[{'new_fixture_army':True}],'active_wars':[{'new_fixture_war':True}],
          'diagnostics':{'bridge_pid':o.GAME,'connection_generation':4,'pipe_name':q.launch['pipe'],
              'hello':{'pid':o.GAME,'connection_generation':4,'ck3_build_match':True,'game_adapter_status':'ready','game_adapter_id':'ck3-1.20.0.4-msvc-x64'}}}
    return q,ram,ns,disp,body,old,gov


class Session:
    def __init__(self,q,body,mode='ok'):
        self.q,self.body,self.mode=q,body,mode;self.calls=[]
    async def call_tool(self,tool,args,**kw):
        if self.q.halted is None:raise AssertionError('halt cleared before maintenance completed')
        self.calls.append((tool,copy.deepcopy(args)))
        if tool=='ck3_execute_step':
            if args!={'step':o.STATUS_STEP}:raise AssertionError('arbitrary primitive')
            result={'is_error':self.mode=='status_refused','result_type':'complete','structured_content':{
                'step':o.STATUS_STEP,'accepted':True,'tactical_daily_sentinel':{'generation':999,'state':'triggered'}}}
        elif tool=='ck3_take_semantic_snapshot_private_v1':
            if args:raise AssertionError('SEM args')
            result={'is_error':False,'result_type':'complete','structured_content':self.body}
        elif tool=='ck3_save_checkpoint':
            if args!={'expected_revision':self.body['revision']}:raise AssertionError('stale SAVE revision')
            if self.q.full_loop_state['pending_cycle'] is not None:raise AssertionError('failed AUTO counted or left pending before SAVE')
            if self.mode=='save_timeout':raise TimeoutError('fixture actual-result unknown; no resend')
            cp=copy.deepcopy(self.q.full_loop_state['actual_saved_checkpoint']);cp.update(date_raw=o.DATE,history_index=5257,sha256='a'*64)
            if self.mode=='bad_save':cp['episode_character_id']=1
            result={'is_error':False,'result_type':'complete','structured_content':{'step':'save-checkpoint','accepted':True,'checkpoint':cp}}
        else:raise AssertionError('non-maintenance tool')
        return SimpleNamespace(model_dump=lambda **k:copy.deepcopy(result))


class Qualification(unittest.IsolatedAsyncioTestCase):
    async def invoke(self,q,ram,ns,disp,session):
        req={'sequence':10477,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':o.KIND}}
        ram.files[o.T/'p37-requests/10477-1-result.json']=encoded(req)
        with patch.object(Path,'read_bytes',lambda p:ram.raw(p,2*1024**2)),patch.dict(sys.modules,{'root_saved_campaign_preflight':disp}):
            await ns['early'](q,session,req,o.T/'p37-requests/10477-1-result.json')
        return ram.read(o.T/'p37-responses/10477-1-result.json')['result']

    async def test_actual_early_closed_record_route_and_original_save_finisher(self):
        q,ram,ns,disp,body,old,gov=build();s=Session(q,body)
        result=await self.invoke(q,ram,ns,disp,s)
        self.assertFalse(result['is_error'],result)
        self.assertEqual([t for t,a in s.calls],['ck3_execute_step',ns['SEMANTIC'],'ck3_save_checkpoint'])
        self.assertEqual(q.next_sequence,10481);self.assertIsNone(q.halted);self.assertTrue(q.recording_paused)
        self.assertEqual(q.full_loop_state['completed_cycles'],4753)
        self.assertEqual(q.full_loop_state['counts'],{**old['counts'],'checkpoint_saved':74})
        self.assertEqual(q.full_loop_state['before']['date_raw'],o.DATE)
        self.assertEqual(q.full_loop_state['checkpoint_calendar_v1']['last_saved_date_raw'],o.DATE)
        self.assertIsNone(q.full_loop_state['pending_cycle']);self.assertFalse(q.full_loop_state['checkpoint_dirty_since_save'])
        self.assertEqual(q.semantic,body)
        self.assertEqual(ram.read(o.T/'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json'),{**gov,'pending_cycle':None})
        self.assertEqual(ram.read(o.T/'NEXT-SEQUENCE-P37.json')['next_sequence'],10481)
        self.assertEqual(result['structured_content']['failed_cycle_credit'],0)
        self.assertFalse(result['structured_content']['sentinel_stop_claimed'])
        self.assertLess(sum(len(ram.files[p]) for p in set(ram.writes)),524288)
        with self.assertRaises(ValueError):await self.invoke(q,ram,ns,disp,s)
        self.assertEqual(len(s.calls),3)

    async def test_status_refused_stays_unknown_save_timeout_never_replays(self):
        for mode in ('status_refused','save_timeout','bad_save'):
            with self.subTest(mode=mode):
                q,ram,ns,disp,body,old,gov=build();s=Session(q,body,mode);halt=q.halted
                r=await self.invoke(q,ram,ns,disp,s)
                if mode=='status_refused':self.assertFalse(r['is_error'],r)
                else:
                    self.assertTrue(r['is_error'],r);self.assertIs(q.halted,halt)
                    self.assertEqual(q.full_loop_state['counts'],old['counts'])
                    self.assertTrue(q.full_loop_state['checkpoint_dirty_since_save'])
                    self.assertEqual(q.full_loop_state['before']['date_raw'],o.DATE)
                self.assertEqual(len(s.calls),3);self.assertEqual(q.next_sequence,10481)

    async def test_fresh_identity_refusals_and_original_storage_gates(self):
        for mode in ('actor','date','goal','connection','unpaused','storage','exit','cap','kernel','NEXT_CAS'):
            with self.subTest(mode=mode):
                q,ram,ns,disp,body,old,gov=build();s=Session(q,body);halt=q.halted
                if mode=='actor':body['played_character']['character_id']=1
                if mode=='date':body['date_raw']-=24
                if mode=='goal':body['campaign_goal']={}
                if mode=='connection':body['diagnostics']['connection_generation']=5
                if mode=='unpaused':body['paused']=False
                if mode=='storage':q.admission['review_at_utc']='different'
                if mode=='exit':ram.files[o.T/'EXIT-SDK-P37C20']=b'Root stop'
                if mode=='cap':q.args.artifact_cap_bytes=1
                if mode=='kernel':disp.births[30936]+=1
                if mode=='NEXT_CAS':ram.files[o.T/'NEXT-SEQUENCE-P37.json']=encoded({'next_sequence':10478})
                if mode in ('storage','exit','cap','kernel','NEXT_CAS'):
                    with self.assertRaises(ValueError):await self.invoke(q,ram,ns,disp,s)
                    self.assertEqual(s.calls,[]);self.assertEqual(q.next_sequence,10477)
                else:
                    r=await self.invoke(q,ram,ns,disp,s);self.assertTrue(r['is_error'],r)
                    self.assertEqual(len(s.calls),2);self.assertEqual(q.next_sequence,10480)
                self.assertIs(q.halted,halt);self.assertEqual(q.full_loop_state,old)

    async def test_partial_metadata_write_is_honest_and_no_save(self):
        q,ram,ns,disp,body,old,gov=build();ram.fail_state=True;s=Session(q,body);halt=q.halted
        r=await self.invoke(q,ram,ns,disp,s)
        self.assertTrue(r['is_error']);self.assertTrue(r['structured_content']['metadata_may_be_partly_committed'])
        self.assertEqual(len(s.calls),2);self.assertIs(q.halted,halt)
        self.assertEqual(ram.read(o.T/'p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json'),old)
        self.assertIsNone(ram.read(o.T/'p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json')['pending_cycle'])

    async def test_ordinary_full_still_refused_by_actual_record_paused_branch(self):
        q,ram,ns,disp,body,old,gov=build();s=Session(q,body)
        with self.assertRaisesRegex(ValueError,'recording paused'):
            await ns['early'](q,s,{'sequence':10477,'command':'full_loop','arguments':{}},o.T/'p37-requests/10477-1-result.json')
        self.assertEqual(s.calls,[]);self.assertEqual(q.next_sequence,10477)


if __name__=='__main__':unittest.main(verbosity=2)
