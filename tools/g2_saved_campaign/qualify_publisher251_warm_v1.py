"""Qualify finite future C5 SEM/CAP through actual startup and ordinary call flow."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType,SimpleNamespace
from prepare_c3_life_opening_classifier_v1 import pinned,load_functions
from owner_response_json_once_v1 import prepare_success_response_row_v1
from publisher251_warm_queue_v1 import make_publisher251_warm_queue_v1,warm_inputs,project_warm_state


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,required=True);parser.add_argument('--post-close',type=Path,required=True)
    parser.add_argument('--source-proof',type=Path,required=True);parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args();root=args.runtime_root.resolve(strict=True);sources=[]
    def readsource(path,sha=None,limit=1024**2):
        raw,pin=pinned(path,expected=sha,limit=limit);sources.append(pin);return raw,pin
    leaf,leafpin=readsource(Path(__file__).with_name('publisher251_warm_queue_v1.py'))
    startup,startpin=readsource(Path(__file__).with_name('startup_readiness_v1.py'),'c9b1bfa0efd002d2fd9f05298ba1d2ba218fa5dded335b30de18ced7d5f7b2c3')
    closed,closepin=readsource(args.post_close,'fd2a83b0fffbdf8c98551306a91463a9ab76ea08db202448f89cb87c94a4a4f7')
    proof,proofpin=readsource(args.source_proof,'dfe9834d06efecba05681f18746108b8de8891c535db2702a3f7c7736774de33')
    admission={'schema':'xar.publisher251-sameGame-C5/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'post_close':closepin,'source_proof':proofpin}
    state,gov,close=warm_inputs(admission)
    queue,qp=readsource(root/'root_p37c5_sdk_queue.py','0752acc6993c1fd92df133c8a4078fc5722a99bc5160ade0395e07c3443bff95')
    freeze,fp=readsource(root/'ROOT-FINAL-SDK-FREEZE-P37C4.json',limit=2*1024**2);sys.path.insert(0,json.loads(freeze)['source_root'])
    launch=json.loads((root/'ROOT-ACTUAL-GAME-LAUNCH-C4.json').read_bytes())
    semraw,sempin=readsource(root/'p37-responses/0198-1-result.json','900303320147c02c96f257de6caf75ae6f400523e5010b48b459babaa063a16f')
    capraw,cappin=readsource(root/'p37-responses/0199-1-result.json','a0e4603f08ceb65d4fcbf03da71f0429f91e2777d63d0a2fae001b876fe27cc1')
    # Explicit future software payload, based on actual198 fields and observed250
    # identity/date/Native lower bound; not a claimed252 response.
    sem=copy.deepcopy(json.loads(semraw));sem['request']={'sequence':252,'tool':'ck3_take_semantic_snapshot_private_v1','arguments':{}}
    body=sem['result']['structured_content'];body.update(snapshot_id='native:60',native_revision=60,revision=2,date_raw=53146896)
    body['diagnostics']['connection_generation']=body['diagnostics']['hello']['connection_generation']=2
    cap=copy.deepcopy(json.loads(capraw));cap['request']={'sequence':253,'tool':'ck3_get_capabilities','arguments':{}}
    cap['result']['structured_content']['native_session_control']['driver_state_restore_kind']='same_pid_hot'
    classifier,cp=readsource(root/'root_p37c4_result_classifier.py','d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    scope={'Path':Path,'copy':copy,'json':json,'ast':ast,'hashlib':hashlib};load_functions(classifier,scope,str(root/'root_p37c4_result_classifier.py'))
    args.output_root.mkdir(parents=True,exist_ok=False);fixture=args.output_root/'fixture';fixture.mkdir()
    (args.output_root/'root_p37c5_warm_resume.py').write_bytes(leaf)
    classifierpin=args.output_root/'FIXTURE-classifier-pin.json';classifierpin.write_text(json.dumps({'source':cp['path'],'sha256':cp['sha256']}),encoding='utf-8')
    admission['classifier_pin']={'path':str(classifierpin),'bytes':classifierpin.stat().st_size,'sha256':hashlib.sha256(classifierpin.read_bytes()).hexdigest()}
    qroot=fixture/'queue';outbox=fixture/'outbox';inbox=fixture/'inbox'
    for path in (qroot,outbox,inbox):path.mkdir()
    events=[];calls=[];observed=[]
    def atomic(path,value,**kw):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and not kw.get('replace'):raise FileExistsError(path)
        path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        events.append({'event':'persist','file':path.name})
    def read(path,*a):return json.loads(Path(path).read_bytes())
    qt=ast.parse(queue);selected=[]
    for name in ('decoded','frame','consume_sequence','persist_loop_state','generated','full_loop'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    actual_call=copy.deepcopy(next(n for n in ast.walk(qt) if isinstance(n,ast.AsyncFunctionDef) and n.name=='call'))
    class CurrentRelay(ast.NodeTransformer):
        def visit_ImportFrom(self,node):
            if node.module=='root_p37c4_overlay_relay':node.module='root_p37c5_overlay_relay'
            return node
    selected.append(CurrentRelay().visit(actual_call))
    env={'N':fixture,'Q':qroot,'OUTBOX':outbox,'INBOX':inbox,'Path':Path,'copy':copy,'json':json,'time':time,
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','CAPABILITIES':'ck3_get_capabilities','METRICS':'root_current_runtime_metrics',
        'AUTO':'ck3_auto_turn','SAVE':'ck3_save_checkpoint','INITIAL_CAMERA':'root_initialize_campaign_camera_v1',
        'REPLY_RESERVE':512*1024**2+65536,'FRONTEND':('a','b','c'),'now':lambda:datetime.now(timezone.utc),
        'read':read,'atomic':atomic,'atomic_payload_v1':lambda path,raw,**kw:atomic(path,json.loads(raw),**kw),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,'preserve_first_exception':lambda *a,**kw:None,
        'display_projection':lambda row,body:{'request':row['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}},
        'pending_request_paths':lambda *a,**kw:[],'load_cold_result_classifier':lambda:scope['classify_auto_result_credit_v1']}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c5_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        call=env['call'];consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state']
        generated=env['generated'];full_loop=env['full_loop']
        def guard(self,**kw):pass
        def call_budget(self,*a):return 1
        def check_before(self,*a):pass
        def check_after(self,*a):raise AssertionError('Warm startup must not delegate to legacy cold/NewGame guards')
    old_ready=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name.startswith('P37') and n.name.endswith('oldReadyQueue')))
    old_ready.body=[n for n in old_ready.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='call']
    old_ready.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old_ready],type_ignores=[])),str(root/'root_p37c5_sdk_queue.py'),'exec'),env)
    Warm=make_publisher251_warm_queue_v1(env[old_ready.name],env,admission_path=Path('SOFTWARE-NO-ACTUAL-PREFLIGHT'))
    q=Warm.__new__(Warm);q.__dict__.update(launch=launch,next_sequence=252,initial_frame=None,initial_save=None,
        initial_camera=None,semantic=None,zero_day_preparation=False,checkpoint_bootstrap_verified=False,cold_readiness_verified=False,
        expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],
        _publisher251_warm={'phase':'semantic','admission':admission,'state':state,'gov':gov,'close':close},
        halted=None,current_attempt=None,held_control=None,loop_count=0)
    score=ModuleType('root_score_month_samples_c4')
    def observe(rootdir,snapshot,game,path):
        row=read(path)
        if path.name!='READINESS-0252-000001-result.json' or (outbox/'0252-1-result.json').exists() or q.next_sequence!=252:
            raise AssertionError('Readiness source/check_after/consume order changed')
        if row['request']!=sem['request'] or env['decoded'](row)!=body:raise AssertionError('Observer source row mismatch')
        observed.append({'source':str(path),'next_sequence':q.next_sequence,'canonical252_exists':False})
    score.observe_semantic=observe
    relay=ModuleType('root_p37c5_overlay_relay')
    def publish(path,compact):
        if not Path(path).exists() or q.next_sequence!=read(path)['request']['sequence']+1:raise AssertionError('C5 relay before canonical publication')
        events.append({'event':'explicit_C5_relay','file':Path(path).name})
    relay.relay_compact=publish;relay.error_projection=lambda row:row
    oldrelay=ModuleType('root_p37_overlay_relay');oldrelay.relay_compact=lambda *a:(_ for _ in ()).throw(AssertionError('Old provider invoked'))
    mods={'root_score_month_samples_c4':score,'root_p37c5_overlay_relay':relay,'root_p37_overlay_relay':oldrelay}
    prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            row=[sem,cap][len(calls)]
            if tool!=row['request']['tool'] or arguments!={}:raise AssertionError('Unexpected fake tool call')
            calls.append(tool);return SimpleNamespace(model_dump=lambda **kw:copy.deepcopy(row['result']))
    try:
        session=Session()
        for row in (sem,cap):asyncio.run(q.call(session,row['request'],inbox/f"{row['request']['sequence']:04d}-1-result.json"))
        opening=env['frame'](body,semantic=True,expected_lifecycle=q.expected_lifecycle_binding)
        expected=project_warm_state(state,opening,outbox/'0252-1-result.json',proofpin)
        if q.next_sequence!=254 or q.full_loop_state!=expected or q.halted is not None:raise AssertionError('Warm boundary differs')
        if (q.full_loop_state['counts']!=state['counts'] or q.initial_save!=state['actual_saved_checkpoint']
            or q.full_loop_state['checkpoint_dirty_since_save'] is not True):raise AssertionError('History/lastSaved/dirty changed')
        if Warm.full_loop is not Base.full_loop or Warm.generated is not Base.generated:raise AssertionError('Ordinary algorithm replaced')
        negatives=[]
        for name in ('wrong_actor','wrong_Game','date_drift','Native_regressed','cold_CAP'):
            instance=Warm.__new__(Warm);instance.__dict__.update(copy.deepcopy(q.__dict__))
            instance.next_sequence=252;instance._publisher251_warm['phase']='semantic'
            bad=copy.deepcopy(body);badcap=copy.deepcopy(cap['result']['structured_content'])
            if name=='wrong_actor':bad['played_character']['character_id']+=1
            elif name=='wrong_Game':bad['diagnostics']['hello']['pid']+=1
            elif name=='date_drift':bad['date_raw']+=24
            elif name=='Native_regressed':bad['native_revision']=59;bad['snapshot_id']='native:59'
            else:
                instance._publisher251_warm['phase']='capabilities';badcap['native_session_control']['driver_state_restore_kind']='cold_checkpoint'
            actualrow=copy.deepcopy(sem);actualrow['result']['structured_content']=bad
            instance.current_attempt={'request':sem['request'],'row':actualrow,'response':str(qroot/'READINESS-0252-000001-result.json')}
            try:instance.check_after(env['CAPABILITIES'] if name=='cold_CAP' else env['SEMANTIC'],{},badcap if name=='cold_CAP' else bad)
            except ValueError:negatives.append(name)
            else:raise AssertionError('Wrong warm binding accepted: '+name)
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.publisher251-warm-call-order-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,
        'future_SEM252_CAP253_are_explicit_software_fixtures':True,'actual_readiness_check_after_consume_publish_and_ordinary_CAP_flow':True,
        'source_pointer252_offset':0,'observed':observed,'events':events,'negative_cases_rejected':negatives,
        'old_C4_exit1_App0_normalfalse_preserved':True,'same_Game_153556_no_cold_SAVE_load':True,
        'counts98_T0_lastSaved61_dirtytrue_preserved':True,'pending99_cleared_only_after_fresh_SEM_CAP':True,
        'query_or_AUTO99_completion_credit':0,'actual_Game_Native_MCP_calls':0,'runtime_files_mutated':0,
        'actual_C5_preflight_or_warm_pass_claimed':False,'leaf':leafpin}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','leaf':leafpin,'qualification':str(args.output_root/'QUALIFICATION.json')}))


if __name__=='__main__':main()
