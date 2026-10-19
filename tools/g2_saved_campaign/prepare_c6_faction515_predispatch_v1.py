"""Qualify exact516 queue-only clear through actual C6 outer dispatch, then PLAN."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
from types import ModuleType,SimpleNamespace
from unittest import mock
from prepare_c3_life_opening_classifier_v1 import pinned
from owner_response_json_once_v1 import prepare_success_response_row_v1
from completed_metrics286_warm_resume_v1 import make_completed_met286_queue_v1
from c6_faction515_predispatch_clear_v1 import KIND


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-root',type=Path,required=True)
    p.add_argument('--failure-packet',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True)
    args=p.parse_args();root=args.runtime_root.resolve(strict=True);sources=[]
    def source(path,expected=None,limit=1024**2):
        raw,pin=pinned(path,expected=expected,limit=limit);sources.append(pin);return raw,pin
    packet,fp=source(args.failure_packet,'d69a3998558f8220d70061bd162339f0f2f8e1fe991fce86df52c73eeb76d182')
    context,cp=source(args.failure_packet.parent/'context/CONTEXT.json','f0ec60d1288d2d297e3358ed6316b5222acd96491ccc314d44461894bd6c1e6c')
    freeze,freeze_pin=source(root/'ROOT-FINAL-SDK-FREEZE-P37C6.json','680163f02a36944fc7c1c9c97f55aaa4816a184e46041889af0c475126b36d2f')
    freeze=json.loads(freeze);assert freeze['business_source_commit']=='13eb02ce80249921b1ac1313507793c382e08448'
    sdk=Path(freeze['source_root']);sys.path.insert(0,str(sdk))
    route,routepin=source(sdk/'xar_autoplayer/bridge/faction_gift_formal_route_v1.py','e929b86b3dcfc7c1b481de6fb55889118ec0b12cc111bf2872bb5fe248ebdebc')
    service,servicepin=source(sdk/'xar_autoplayer/bridge/service.py','9a22d369ffc245c7a26439a55819461a5c296a4fce015d1cf0ba85f86055e81e')
    pending,pendingpin=source(sdk/'xar_autoplayer/faction_gift_pending_v1.py','2152c3e2c7f48bad6864c06d43a6e32e731736a72e65df5b134250a156450293')
    gift,giftpin=source(args.failure_packet.parent/'faction-gift-pending-v1.json','24268466d6c3a9c521885c9dee0aeaff7e035e9ec3f6d5af0862c54a3e9768a0')
    args.output_root.mkdir(parents=True,exist_ok=False)
    contract={'schema':'xar.C6-faction515-source-contract/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'failure_packet':fp,'context':cp,'SDK_freeze':freeze_pin,
        'gift_ledger':giftpin,'immutable_sources':{'route':routepin,'Service':servicepin,'pending_ledger':pendingpin},
        'selected515_dispatch_occurred':False,'earlier_gift_pending_must_remain_untouched':True,
        'source_flow':['route104-171 bounded same-date paused frame wait ends with typed pre-submission mismatch',
            'route175-201 pending planner calls wait before receipt/send',
            'Service4771 plan_turn must return before4779 selected execution/before-submit'],
        'current_fresh_frame_not_read_from_live_Driver':True}
    contractpath=args.output_root/'SOURCE-CONTRACT.json';contractpath.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
    contractpin=source(contractpath)[1]
    old,oldpin=source(root/'root_saved_campaign_preflight.py','167f1840a25bbc62eb2fd032bb17e1e0183a6c14ad9a93745773d7d036b5909e')
    leaf,leafpin=source(Path(__file__).with_name('c6_faction515_predispatch_clear_v1.py'));digest=leafpin['sha256']
    tree=ast.parse(old);last=[n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1]
    lines=old.decode().splitlines(keepends=True);lines[last.lineno-1]=lines[last.lineno-1].replace('async def recover_zero_rpc_preflight(','async def recover_before_faction515(',1)
    changed=''.join(lines)+f'''

async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={{"repair_kind":{KIND!r}}}:
        source=Path(__file__).with_name("root_c6_faction515_predispatch_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!={digest!r}:
            raise ValueError("reviewed faction515 clear leaf differs")
        scope={{}}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,packet_ref={fp!r},context_ref={cp!r},
            source_contract={contractpin!r},birth_reader=process_birth_filetime)
    return await recover_before_faction515(queue,session,request,path,env)
'''
    expected=copy.deepcopy(tree);[n for n in expected.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1].name='recover_before_faction515'
    assert [ast.dump(n) for n in expected.body]==[ast.dump(n) for n in ast.parse(changed).body[:-1]]
    control=args.output_root/'root_saved_campaign_preflight.py';control.write_text(changed,encoding='utf-8')
    (args.output_root/'root_c6_faction515_predispatch_clear.py').write_bytes(leaf)
    raw,qp=source(root/'root_p37c6_sdk_queue.py','600703088920399e0d8c354ec283d84144c660cb9f761900df603e2077a2e63f');qt=ast.parse(raw)
    values={Path(ref['original_source']).name:json.loads(Path(ref['path']).read_bytes()) for ref in json.loads(packet)['sources']}
    state=values['ROOT-CUMULATIVE-LOOP-STATE.json'];gov=values['ROOT-GOVERNANCE-RESULT-STATE.json'];row=values['0515-1-result.json']
    # The actual old route reselects the independent receipt on a newer same-date
    # frame. This explicit fixture neither calls Native nor resolves the gift.
    import xar_autoplayer.bridge.faction_gift_formal_route_v1 as route_module
    driver=SimpleNamespace(state_dir=args.output_root/'fixture-state',_session_bridge_pid=153556)
    sidecar=driver.state_dir/'native-session/faction-gift-pending-v1.json';sidecar.parent.mkdir(parents=True);sidecar.write_bytes(gift)
    future={'snapshot_id':'native:419','revision':352,'native_revision':419,'date_raw':53153472,
        'episode_run_id':'native-31254-6271ac8cd441','paused':True,'map_ready':True,'played_character':{'character_id':31254,'alive':True}}
    with mock.patch.object(route_module,'_process_identity',return_value={'creation_date':json.loads(gift)['pending']['source_bridge_creation_date']}):
        planned=route_module.plan_faction_gift_private_v1(driver,{'plan':{'selected_step':'life-advance'}},future,[],set())
    assert planned['plan']['selected_step']=='private-query-faction-gift-receipt-v1' and sidecar.read_bytes()==gift
    selected=[]
    for name in ('frame','decoded','consume_sequence','persist_loop_state','halt_request','run_request_loop','call','check_before','check_after'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    writes=[];active={};calls=[]
    class Stop(BaseException):pass
    class AdmissionEnded(RuntimeError):pass
    class RecordingPaused(RuntimeError):pass
    async def sleep(_):raise Stop()
    def atomic(path,value,**kw):writes.append((str(path),copy.deepcopy(value)))
    def read(path,*a):return copy.deepcopy(active['request']) if Path(path)==active.get('path') else json.loads(Path(path).read_bytes())
    constants={}
    for node in qt.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:
                value=node.value
                constants[node.targets[0].id]=frozenset(ast.literal_eval(value.args[0])) if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='frozenset' else ast.literal_eval(value)
            except (ValueError,TypeError):pass
    env={**constants,'N':root,'Q':root/'p37-queue','OUTBOX':root/'p37-responses','INBOX':root/'p37-requests',
        'Path':Path,'copy':copy,'hashlib':hashlib,'json':json,'time':time,'read':read,'atomic':atomic,
        'now':lambda:datetime.now(timezone.utc),'asyncio':SimpleNamespace(sleep=sleep),'AdmissionEnded':AdmissionEnded,'RecordingPaused':RecordingPaused,
        'pending_request_paths':lambda *a,**kw:[active['path']],'preserve_first_exception':lambda *a,**kw:str(root/'ROOT-FIRST-QUEUE-EXCEPTION-P37C6.json'),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,'atomic_payload_v1':lambda p,b,**kw:atomic(p,json.loads(b),**kw),
        'display_projection':lambda r,b:{'request':r['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}}}
    env['REPLY_RESERVE']=512*1024**2+65536;env['READONLY_RESEARCH']=frozenset();env['ALLOWED']={*env['FRONTEND'],env['CAPABILITIES'],env['SEMANTIC'],env['METRICS'],env['SAVE'],env['AUTO'],env['INITIAL_CAMERA'],'ck3_plan_turn'}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c6_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state'];halt_request=env['halt_request']
        call=env['call'];check_before=env['check_before'];check_after=env['check_after']
        def guard(self,**kw):pass
        def call_budget(self,*a):return 1
    env['ColdQueue']=Base
    clean=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue'))
    clean.body=[n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name in ('check_before','check_after')]
    clean.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[clean],type_ignores=[])),str(root/'root_p37c6_sdk_queue.py'),'exec'),env)
    Warm=make_completed_met286_queue_v1(env['CleanRobertMainMenuQueue'],env,admission_path=Path('NO-PREFLIGHT'))
    original={'request':row['request'],'row':row,'response':str(root/'p37-responses/0515-1-result.json')}
    def make():
        q=Warm.__new__(Warm);q.__dict__.update(next_sequence=516,held_control=None,halted=copy.deepcopy(original),current_attempt=copy.deepcopy(original),
            halt_cause={'error_type':'RuntimeError','message':'SDK error; original result retained; no automatic retry'},launch={'pid':153556,'creation_filetime':134368602545256920},
            full_loop_state=copy.deepcopy(state),semantic=None,initial_frame=state['before'],initial_save=state['actual_saved_checkpoint'],
            expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],_completed_met286={'phase':'ready','consumed':True,'rebound':True},
            governance_result_state=gov['state'],lifestyle_pending_focus=gov['pending_focus'],result_classifier_pin=gov['classifier'],capabilities_verified=True,
            cold_readiness_verified=True,checkpoint_bootstrap_verified=True,checkpoint_mode=True,zero_day_preparation=False,frontend_done=len(env['FRONTEND']))
        return q
    module=ModuleType('root_saved_campaign_preflight');module.__file__=str(control);exec(compile(changed,str(control),'exec'),module.__dict__)
    kernel=ModuleType('root_p37_known_pause_recovery_control');kernel.process_birth_filetime=lambda pid:134368602545256920
    relay=ModuleType('root_p37c6_overlay_relay');relay.relay_compact=lambda *a:None;relay.error_projection=lambda row:row
    mods={m.__name__:m for m in (module,kernel,relay)};prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    request={'sequence':516,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':KIND}}
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            assert tool=='ck3_plan_turn' and arguments=={};calls.append(tool)
            return SimpleNamespace(model_dump=lambda **kw:{'is_error':False,'result_type':'complete','structured_content':{'snapshot_id':'native:419','revision':352,'plan':planned['plan']}})
    try:
        q=make();active.update(request=request,path=env['INBOX']/'0516-1-result.json')
        try:asyncio.run(env['run_request_loop'](q,Session()))
        except Stop:pass
        expected_state=copy.deepcopy(state);expected_state['pending_cycle']=None
        assert q.next_sequence==517 and q.halted is None and q.full_loop_state==expected_state and not calls
        assert not any('/state/' in filename.replace('\\','/') for filename,value in writes)
        asyncio.run(q.call(Session(),{'sequence':517,'tool':'ck3_plan_turn','arguments':{}},env['INBOX']/'0517-1-result.json'))
        assert calls==['ck3_plan_turn'] and q.next_sequence==518 and q.full_loop_state==expected_state and sidecar.read_bytes()==gift
        negatives=[]
        for name in ('unknown_original','pending_changed','foreign_Game'):
            q=make()
            if name=='unknown_original':q.halted['row']['client_error']='unknown'
            elif name=='pending_changed':q.full_loop_state['pending_cycle']['auto_sequence']=513
            else:q.launch['creation_filetime']+=1
            count=len(writes)
            try:asyncio.run(module.recover_zero_rpc_preflight(q,Session(),request,active['path'],env))
            except ValueError:
                assert len(writes)==count and q.next_sequence==516;negatives.append(name)
            else:raise AssertionError('Invalid boundary admitted: '+name)
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.C6-faction515-clear-PLAN-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'control':source(control)[1],
        'leaf':source(args.output_root/'root_c6_faction515_predispatch_clear.py')[1],'source_contract':contractpin,
        'actual_C6_outer_dispatch_and_Clean_before_after_used':True,'516_new_RPC_calls':0,'517_software_PLAN_calls':1,
        'old_actual_route_newer_same_date_fixture_selects_independent_receipt':True,'fixture_ledger_bytes_unchanged':True,
        'state_only_pending_cycle_changed':True,'negative_cases_rejected':negatives,'actual_Game_Native_MCP_calls':0,
        'runtime_files_mutated':0,'actual517_success_claimed':False}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','control':result['control'],'leaf':result['leaf'],'source_contract':contractpin}))


if __name__=='__main__':main()
