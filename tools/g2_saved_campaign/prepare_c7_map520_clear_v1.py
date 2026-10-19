"""Actual outer FULL520 preflight reproduction and exact521 local recovery."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace,ModuleType
from prepare_c3_life_opening_classifier_v1 import pinned
from c7_map520_preflight_clear_v1 import KIND


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-root',type=Path,required=True)
    p.add_argument('--packet',type=Path,required=True);p.add_argument('--root-review',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True);args=p.parse_args();root=args.runtime_root.resolve(strict=True);sources=[]
    def source(path,sha=None):
        raw,pin=pinned(path,expected=sha,limit=1024**2);sources.append(pin);return raw,pin
    packet,pp=source(args.packet,'ba5c98d373ef20dc14358ebcebe895f142ca28b3ad31c3a17febd5d2a739c3b6')
    review,rp=source(args.root_review,'17e3cb081b1065102127513c3a650464d66227b7e64cfa537642f956d2f185b6')
    corrected,mp=source(root/'ROOT-CAMPAIGN-MAP-ADMITTED-C7.json','7c00ba6454f7997a564bd1b2d0ba6e45a2e7a4eda1ed51994f17b16367f10678')
    values={Path(ref['original_source']).name:json.loads(Path(ref['path']).read_bytes()) for ref in json.loads(packet)['sources']}
    old,op=source(root/'root_saved_campaign_preflight.py','24a2dd46a69a206cccca9dab5a63a1bb2f1fe4f9693778a0e954e49165639500')
    leaf,lp=source(Path(__file__).with_name('c7_map520_preflight_clear_v1.py'));digest=lp['sha256']
    args.output_root.mkdir(parents=True,exist_ok=False)
    tree=ast.parse(old);last=[n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1]
    lines=old.decode().splitlines(keepends=True);lines[last.lineno-1]=lines[last.lineno-1].replace('async def recover_zero_rpc_preflight(','async def recover_before_map520(',1)
    changed=''.join(lines)+f'''

async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={{"repair_kind":{KIND!r}}}:
        source=Path(__file__).with_name("root_c7_map520_preflight_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!={digest!r}:
            raise ValueError("reviewed map520 local preflight leaf differs")
        scope={{}}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,packet_ref={pp!r},corrected_map_ref={mp!r},
            root_review_ref={rp!r},birth_reader=process_birth_filetime)
    return await recover_before_map520(queue,session,request,path,env)
'''
    expected=copy.deepcopy(tree);[n for n in expected.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1].name='recover_before_map520'
    assert [ast.dump(n) for n in expected.body]==[ast.dump(n) for n in ast.parse(changed).body[:-1]]
    control=args.output_root/'root_saved_campaign_preflight.py';control.write_text(changed,encoding='utf-8')
    (args.output_root/'root_c7_map520_preflight_clear.py').write_bytes(leaf)
    raw,qp=source(root/'root_p37c7_sdk_queue.py','fd579859a384ba94a059a38701719918ef763a15d7df21f86c5b347dc6ff0a30');qt=ast.parse(raw)
    selected=[]
    for name in ('frame','decoded','consume_sequence','persist_loop_state','halt_request','run_request_loop','full_loop','generated'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    clean=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue')
    selected.append(next(n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name=='require_camera_pixel_admission'))
    writes=[];active={};guards=[];calls=[]
    class Stop(BaseException):pass
    class NewAutoReached(BaseException):pass
    class AdmissionEnded(RuntimeError):pass
    class RecordingPaused(RuntimeError):pass
    async def sleep(_):raise Stop()
    def atomic(path,value,**kw):writes.append((str(path),copy.deepcopy(value)))
    def read(path,*a):
        if Path(path)==active.get('path'):return copy.deepcopy(active['request'])
        if Path(path)==root/'ROOT-CAMPAIGN-MAP-ADMITTED-C7.json' and active.get('wrong_map'):return values['ROOT-CAMPAIGN-MAP-ADMITTED-C7.json']
        return json.loads(Path(path).read_bytes())
    env={'N':root,'Q':root/'p37-queue','OUTBOX':root/'p37-responses','INBOX':root/'p37-requests',
        'Path':Path,'copy':copy,'hashlib':hashlib,'json':json,'read':read,'atomic':atomic,'now':lambda:datetime.now(timezone.utc),
        'asyncio':SimpleNamespace(sleep=sleep),'AdmissionEnded':AdmissionEnded,'RecordingPaused':RecordingPaused,
        'pending_request_paths':lambda *a,**kw:[] if active.get('new_full') else [active['path']],
        'preserve_first_exception':lambda *a,**kw:str(root/'ROOT-FIRST-QUEUE-EXCEPTION-P37C7.json'),
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','METRICS':'root_current_runtime_metrics','AUTO':'ck3_auto_turn','SAVE':'ck3_save_checkpoint'}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c7_sdk_queue.py'),'exec'),env)
    class Queue(SimpleNamespace):
        consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state'];halt_request=env['halt_request']
        full_loop=env['full_loop'];generated=env['generated'];require_camera_pixel_admission=env['require_camera_pixel_admission']
        def guard(self,**kw):guards.append(kw)
        async def call(self,session,request,path):calls.append(request);raise NewAutoReached()
    state=values['ROOT-CUMULATIVE-LOOP-STATE.json'];opening=values['ROOT-C7-SOURCE-ONLY-WARM-BOUND.json']['fresh_opening']
    def make(*,already_halted=True):
        q=Queue(next_sequence=521 if already_halted else 520,held_control=None,current_attempt=None,
            halted={'request':{'sequence':520,'command':'full_loop','arguments':{'max_turns':30}},'row':None,'response':None} if already_halted else None,
            halt_cause={'error_type':'ValueError','message':'Root must review the new actual map and overlay before initial SAVE'} if already_halted else None,
            full_loop_state=copy.deepcopy(state),initial_frame=copy.deepcopy(opening),initial_save=state['actual_saved_checkpoint'],
            launch={'pid':153556,'creation_filetime':134368602545256920},job={'session_id':json.loads(corrected)['recording_session_id']},
            _source_only381={'phase':'ready'},zero_day_preparation=False,checkpoint_bootstrap_verified=True,loop_count=0,
            governance_result_state=None,lifestyle_pending_focus=None,result_classifier_pin=None)
        return q
    module=ModuleType('root_saved_campaign_preflight');module.__file__=str(control);exec(compile(changed,str(control),'exec'),module.__dict__)
    kernel=ModuleType('root_p37_known_pause_recovery_control');kernel.process_birth_filetime=lambda pid:134368602545256920
    score=ModuleType('root_score_month_samples_c4');score.END_RAW=53407128;score.anchor_path=None
    mods={m.__name__:m for m in (module,kernel,score)};prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    request={'sequence':521,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}}
    try:
        q=make(already_halted=False);active.update(request={'sequence':520,'command':'full_loop','arguments':{'max_turns':30}},path=env['INBOX']/'0520-1-result.json',wrong_map=True)
        try:asyncio.run(env['run_request_loop'](q,None))
        except Stop:pass
        assert q.next_sequence==521 and q.halted==make().halted and q.halt_cause==make().halt_cause and q.full_loop_state==state and not calls
        assert not any(Path(path).name=='INFLIGHT-0520.json' for path,value in writes)
        writes.clear();active.update(request=request,path=env['INBOX']/'0521-1-result.json',wrong_map=False)
        try:asyncio.run(env['run_request_loop'](q,None))
        except Stop:pass
        assert q.next_sequence==522 and q.halted is None and q.full_loop_state==state and not calls and len(writes)==4
        negatives=[]
        for name in ('unknown_original_response','pending_work','uncorrected_map'):
            bad=make()
            if name=='unknown_original_response':bad.halted['row']={'unknown':True}
            elif name=='pending_work':bad.full_loop_state['pending_cycle']={'stage':'auto_unsettled'}
            else:active['wrong_map']=True
            count=len(writes)
            try:asyncio.run(module.recover_zero_rpc_preflight(bad,None,request,active['path'],env))
            except ValueError:
                assert len(writes)==count and bad.next_sequence==521;negatives.append(name)
            else:raise AssertionError('Invalid local preflight admitted: '+name)
            active['wrong_map']=False
        active.update(new_full=True)
        try:asyncio.run(q.full_loop(None,{'sequence':522,'command':'full_loop','arguments':{'max_turns':1}},env['INBOX']/'0522-1-result.json'))
        except NewAutoReached:pass
        else:raise AssertionError('Original next FULL did not reach a fresh AUTO')
        assert len(calls)==1 and calls[0]['sequence']==523 and calls[0]['tool']==env['AUTO']
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.C7-map520-exact521-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'control':source(control)[1],
        'leaf':source(args.output_root/'root_c7_map520_preflight_clear.py')[1],
        'actual_original_FULL520_gate_and_halt_order_reproduced':True,'original_Root_camera_guard_revalidated':True,
        'actual_outer521_calls':0,'219_day381_state_unchanged_by_clear':True,'first_fresh_AUTO_after_next_FULL':523,
        'previous_recovery_ASTs_preserved':True,'negative_cases_rejected':negatives,'runtime_files_mutated':0,
        'actual_Game_Native_MCP_calls':0,'actual521_success_claimed':False}
    path=args.output_root/'QUALIFICATION.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','control':result['control'],'leaf':result['leaf']}))


if __name__=='__main__':main()
