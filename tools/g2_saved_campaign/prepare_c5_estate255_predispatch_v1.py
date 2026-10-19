"""Qualify exact256 clear then original normal257 PLAN dispatch; no live RPC."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys,time
from pathlib import Path
from datetime import datetime,timezone
from types import ModuleType,SimpleNamespace
from prepare_c3_life_opening_classifier_v1 import pinned
from c5_estate255_predispatch_clear_v1 import PINS
from owner_response_json_once_v1 import prepare_success_response_row_v1
from publisher251_warm_queue_v1 import make_publisher251_warm_queue_v1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-root',type=Path,required=True)
    p.add_argument('--frozen66',type=Path,required=True);p.add_argument('--callback-absence',type=Path,required=True)
    p.add_argument('--output-root',type=Path,required=True);args=p.parse_args();root=args.runtime_root.resolve(strict=True)
    frozen,fp=pinned(args.frozen66,expected='2596ab289cc30be4befedb33d80ae653b406b69c10ac9d441aa96a4b498f90b8')
    absence,ap=pinned(args.callback_absence,expected='d02174b0697491ded03f7e63845e5a7ec89643f5887b30f81744134abd79e652')
    freeze,freeze_pin=pinned(root/'ROOT-FINAL-SDK-FREEZE-P37C5.json',
        expected='84fbe82908590e5b2813430f33ef4cb10cd8326bb2c98f0c3ee4aecfaf716290',limit=2*1024**2)
    freeze=json.loads(freeze)
    if (freeze['business_source_commit']!='6ebbffcdebe3e30353513e0984572ebc701daa2e'
        or Path(freeze['source_root']).resolve()!=root.parent.parent/'sdk-v20261019-candidate'/'src04'):
        raise AssertionError('Actual C5 business source changed')
    sys.path.insert(0,freeze['source_root'])
    refs={Path(x['source']).resolve():{k:x[k] for k in ('path','bytes','sha256')} for x in json.loads(frozen)['refs']}
    retained={};values={}
    for relative,digest in PINS.items():
        ref=refs[(root/relative).resolve()];raw,_=pinned(Path(ref['path']),expected=digest)
        retained[relative]=ref;values[relative]=json.loads(raw)
    absence=json.loads(absence)
    if absence['later_callback_filenames'] or any(Path(x).exists() for x in absence['exact_absent_paths']):
        raise AssertionError('Actual255 callback appeared; retain halt')
    sdk=Path(freeze['source_root']);guard,guardpin=pinned(sdk/'xar_autoplayer/bridge/succession_expectation_invalidation_v1.py',expected='33a1905f3e142e7784165dc706d2be0749e9a74d4745c9c43fe975689c1ca3da')
    args.output_root.mkdir(parents=True,exist_ok=False)
    contract={'schema':'xar.c5-exact255-predispatch-source-contract/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'business_source_commit':freeze['business_source_commit'],
        'SDK_freeze':freeze_pin,'guard':guardpin,'callback_absence':ap,'frozen66':fp,
        'source_flow':{'Service.auto_turn':'plan_turn4771 precedes execute4779 and before_submit5076',
            'Service.query_campaign_root_context':'independently validated root response8318 then invalidator8320',
            'NativeDriver.invalidater':'pure decision4840 precedes estate assignment4851 and persistence4854',
            'NativeDriver.execute_step':'successful root history recorded before response returns to Service',
            'Service.prepare':'same-frame history→_planning_root_result→strict turn_bundle→retain; unchanged validators'},
        'selected_business_dispatch_occurred':False,'readonly_root_query_did_occur':True,
        'same_frame_root_cache_reuse_is_revalidated_by_normal_PLAN':True,'live_history_read_claimed':False}
    contract_path=args.output_root/'SOURCE-CONTRACT.json';contract_path.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8')
    contractpin={'path':str(contract_path),'bytes':contract_path.stat().st_size,'sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest()}
    old,op=pinned(root/'root_saved_campaign_preflight.py',expected='8d3cfea291222537d557edbaa61cab6f41e823f74a93e5d5018807514bbe8694')
    leaf,lp=pinned(Path(__file__).with_name('c5_estate255_predispatch_clear_v1.py'));digest=hashlib.sha256(leaf).hexdigest()
    tree=ast.parse(old);last=[n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1]
    lines=old.decode().splitlines(keepends=True);lines[last.lineno-1]=lines[last.lineno-1].replace('async def recover_zero_rpc_preflight(','async def recover_before_estate255(',1)
    changed=''.join(lines)+f'''

async def recover_zero_rpc_preflight(queue,session,request,path,env):
    if request.get("arguments")=={{"repair_kind":"estate255_before_dispatch_for_readonly_PLAN"}}:
        source=Path(__file__).with_name("root_c5_estate255_predispatch_clear.py")
        payload=source.read_bytes()
        if len(payload)>32768 or hashlib.sha256(payload).hexdigest()!={digest!r}:
            raise ValueError("reviewed estate255 clear leaf differs")
        scope={{}}
        exec(compile(payload,str(source),"exec"),scope)
        from root_p37_known_pause_recovery_control import process_birth_filetime
        return await scope["recover"](queue,session,request,path,env,
            retained={retained!r},birth_reader=process_birth_filetime,source_contract={contractpin!r})
    return await recover_before_estate255(queue,session,request,path,env)
'''
    expected=copy.deepcopy(tree);[n for n in expected.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='recover_zero_rpc_preflight'][-1].name='recover_before_estate255'
    if [ast.dump(n) for n in expected.body]!=[ast.dump(n) for n in ast.parse(changed).body[:-1]]:raise AssertionError('Previous recovery AST changed')
    control=args.output_root/'root_saved_campaign_preflight.py';control.write_text(changed,encoding='utf-8')
    (args.output_root/'root_c5_estate255_predispatch_clear.py').write_bytes(leaf)
    raw,qp=pinned(root/'root_p37c5_sdk_queue.py',expected='0752acc6993c1fd92df133c8a4078fc5722a99bc5160ade0395e07c3443bff95',limit=1024**2);qt=ast.parse(raw)
    selected=[]
    for name in ('frame','decoded','consume_sequence','persist_loop_state','halt_request','run_request_loop'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    ordinary_call=next(n for n in ast.walk(qt) if isinstance(n,ast.AsyncFunctionDef) and n.name=='call')
    base_before=next(n for n in ast.walk(qt) if isinstance(n,ast.FunctionDef) and n.name=='check_before')
    base_after=next(n for n in ast.walk(qt) if isinstance(n,ast.FunctionDef) and n.name=='check_after')
    selected.extend([ordinary_call,base_before,base_after])
    writes=[];active={};responses={};calls=[]
    class Stop(BaseException):pass
    class AdmissionEnded(RuntimeError):pass
    class RecordingPaused(RuntimeError):pass
    async def sleep(_):raise Stop()
    def atomic(path,value,**kw):writes.append((str(path),copy.deepcopy(value)));responses[str(path)]=copy.deepcopy(value)
    def read(path,*a):
        if Path(path)==active.get('path'):return copy.deepcopy(active['request'])
        return json.loads(Path(path).read_bytes())
    constants={}
    for node in qt.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            try:
                value=node.value
                if isinstance(value,ast.Call) and isinstance(value.func,ast.Name) and value.func.id=='frozenset' and len(value.args)==1:
                    constants[node.targets[0].id]=frozenset(ast.literal_eval(value.args[0]))
                else:constants[node.targets[0].id]=ast.literal_eval(value)
            except (ValueError,TypeError):pass
    env={**constants,'N':root,'Q':root/'p37-queue','OUTBOX':root/'p37-responses','INBOX':root/'p37-requests',
        'Path':Path,'copy':copy,'hashlib':hashlib,'json':json,'time':time,'read':read,'atomic':atomic,
        'now':lambda:datetime.now(timezone.utc),'asyncio':SimpleNamespace(sleep=sleep),
        'AdmissionEnded':AdmissionEnded,'RecordingPaused':RecordingPaused,'pending_request_paths':lambda *a,**kw:[active['path']],
        'preserve_first_exception':lambda *a,**kw:str(root/'ROOT-FIRST-QUEUE-EXCEPTION-P37C5.json'),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,
        'atomic_payload_v1':lambda p,b,**kw:atomic(p,json.loads(b),**kw),
        'display_projection':lambda r,b:{'request':r['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}}}
    env['REPLY_RESERVE']=512*1024**2+65536;env['READONLY_RESEARCH']=frozenset();env['ALLOWED']={*env['FRONTEND'],env['CAPABILITIES'],env['SEMANTIC'],env['METRICS'],env['SAVE'],env['AUTO'],env['INITIAL_CAMERA'],'ck3_plan_turn'}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c5_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state'];halt_request=env['halt_request']
        call=env['call'];check_before=env['check_before'];check_after=env['check_after']
        def guard(self,**kw):pass
        def call_budget(self,*a):return 1
    env['ColdQueue']=Base
    clean=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue'))
    clean.body=[n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name in ('check_before','check_after')]
    clean.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[clean],type_ignores=[])),str(root/'root_p37c5_sdk_queue.py'),'exec'),env)
    Warm=make_publisher251_warm_queue_v1(env['CleanRobertMainMenuQueue'],env,admission_path=Path('NO-PREFLIGHT'))
    state=values['p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json'];gov=values['p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json'];row=values['p37-responses/0255-1-result.json'];sem=values['p37-responses/0252-1-result.json']
    original={'request':row['request'],'row':copy.deepcopy(row),'response':str(root/'p37-responses/0255-1-result.json')}
    def make():
        q=Warm.__new__(Warm);q.__dict__.update(next_sequence=256,held_control=None,halted=copy.deepcopy(original),current_attempt=copy.deepcopy(original),
            halt_cause={'error_type':'RuntimeError','message':'SDK error; original result retained; no automatic retry'},
            launch={'pid':153556,'creation_filetime':134368602545256920},full_loop_state=copy.deepcopy(state),
            semantic=copy.deepcopy(sem['result']['structured_content']),initial_frame=state['before'],initial_save=state['actual_saved_checkpoint'],
            expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],_publisher251_warm={'phase':'ready'},
            governance_result_state=gov['state'],lifestyle_pending_focus=gov['pending_focus'],result_classifier_pin=gov['classifier'],
            capabilities_verified=True,cold_readiness_verified=True,checkpoint_bootstrap_verified=True,checkpoint_mode=True,
            zero_day_preparation=False,frontend_done=len(env['FRONTEND']))
        return q
    module=ModuleType('root_saved_campaign_preflight');module.__file__=str(control);exec(compile(changed,str(control),'exec'),module.__dict__)
    kernel=ModuleType('root_p37_known_pause_recovery_control');kernel.process_birth_filetime=lambda pid:134368602545256920
    relay=ModuleType('root_p37c5_overlay_relay');relay.relay_compact=lambda *a:None;relay.error_projection=lambda row:row
    mods={'root_saved_campaign_preflight':module,'root_p37_known_pause_recovery_control':kernel,'root_p37c5_overlay_relay':relay}
    prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    request={'sequence':256,'command':'clear_zero_rpc_preflight_rejection','arguments':{'repair_kind':'estate255_before_dispatch_for_readonly_PLAN'}}
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            if tool!='ck3_plan_turn' or arguments!={}:raise AssertionError('Only new normal PLAN fixture may call')
            calls.append(tool);return SimpleNamespace(model_dump=lambda **kw:{'is_error':False,'result_type':'complete',
                'structured_content':{'snapshot_id':'native:61','revision':2,'plan':{'selected_step':'fixture-only-no-action'}}})
    try:
        q=make()
        try:q.check_before('ck3_plan_turn',{})
        except RuntimeError:pass
        else:raise AssertionError('Original halt must forbid direct PLAN256')
        active.update(request=request,path=env['INBOX']/'0256-1-result.json')
        try:asyncio.run(env['run_request_loop'](q,Session()))
        except Stop:pass
        expected_state=copy.deepcopy(state);expected_state['pending_cycle']=None
        if q.next_sequence!=257 or q.halted is not None or q.full_loop_state!=expected_state or len(writes)!=6 or calls:
            raise AssertionError('Actual256 outer clear changed more than pending99')
        asyncio.run(q.call(Session(),{'sequence':257,'tool':'ck3_plan_turn','arguments':{}},env['INBOX']/'0257-1-result.json'))
        if calls!=['ck3_plan_turn'] or q.next_sequence!=258 or q.full_loop_state!=expected_state:raise AssertionError('Normal PLAN flow differs')
        negatives=[]
        for name in ('unknown_original','pending_changed','foreign_Game'):
            q=make()
            if name=='unknown_original':q.halted['row']['client_error']='unknown'
            elif name=='pending_changed':q.full_loop_state['pending_cycle']['auto_sequence']=251
            else:q.launch['creation_filetime']+=1
            count=len(writes)
            try:asyncio.run(module.recover_zero_rpc_preflight(q,Session(),request,active['path'],env))
            except ValueError:
                if len(writes)!=count or q.next_sequence!=256:raise AssertionError('Negative mutated or consumed')
                negatives.append(name)
            else:raise AssertionError('Wrong exact failure accepted')
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.c5-estate255-clear-normalPLAN-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':[fp,ap,freeze_pin,guardpin,op,lp,qp],
        'control':{'path':str(control),'bytes':control.stat().st_size,'sha256':hashlib.sha256(control.read_bytes()).hexdigest()},
        'leaf':{'path':str(args.output_root/'root_c5_estate255_predispatch_clear.py'),'bytes':len(leaf),'sha256':digest},
        'source_contract':contractpin,'actual_original_outer_dispatch_and_Clean_before_after_call_used':True,
        '256_new_RPC_calls':0,'257_mock_normal_PLAN_calls':1,'mock_PLAN_does_not_claim_actual_estate_refresh':True,
        'state_only_pending_cycle_changed':True,'counts98_T0_day107_lastSaved61_preserved':True,
        'negative_cases_rejected':negatives,'runtime_files_mutated':0,'actual_Game_Native_MCP_calls':0}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','control':result['control'],'leaf':result['leaf'],'source_contract':contractpin}))


if __name__=='__main__':main()
