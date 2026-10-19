"""Replay closed198/199 through real readiness/check_after/consume/publish order."""
from __future__ import annotations
import argparse
import ast
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from types import ModuleType, SimpleNamespace

from prepare_c3_life_opening_classifier_v1 import load_functions, pinned
from saved61_cold_queue_v1 import make_saved61_cold_queue_v1
from owner_response_json_once_v1 import prepare_success_response_row_v1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--seed',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args();root=args.runtime_root.resolve(strict=True)
    sources=[]
    def source(path,sha=None,limit=1024**2):
        raw,pin=pinned(path,expected=sha,limit=limit);sources.append(pin);return raw
    leaf=source(Path(__file__).with_name('saved61_cold_queue_v1.py'))
    startup=source(Path(__file__).with_name('startup_readiness_v1.py'),'c9b1bfa0efd002d2fd9f05298ba1d2ba218fa5dded335b30de18ced7d5f7b2c3')
    queue=source(root/'root_p37c4_sdk_queue.py','9832cbdaeeb1a0add22a97d039aa83eb677853f731abebbd15a61e804f6f3b0f')
    oldleaf=source(root/'root_p37c4_cold_resume.py','82d40a057f5091094728c0ca1a77cdb990c8b649b6c2ce2199f8dde53d2b44d9')
    seed=json.loads(source(args.seed,'13ace44626932920b7558ac7c74e5f648e697d291aa1d84a6671d166be4efdbc'))
    sem=json.loads(source(root/'p37-responses/0198-1-result.json','900303320147c02c96f257de6caf75ae6f400523e5010b48b459babaa063a16f'))
    cap=json.loads(source(root/'p37-responses/0199-1-result.json','a0e4603f08ceb65d4fcbf03da71f0429f91e2777d63d0a2fae001b876fe27cc1'))
    launch=json.loads(source(root/'ROOT-ACTUAL-GAME-LAUNCH-C4.json'))
    actualmap=json.loads(source(root/'ROOT-CAMPAIGN-MAP-ADMITTED-C4.json'))
    frozen=json.loads(source(root/'ROOT-FINAL-SDK-FREEZE-P37C4.json',limit=2*1024**2));sys.path.insert(0,frozen['source_root'])
    cpraw=source(root/'ROOT-P37C4-CLASSIFIER-PIN.json');cppin=sources[-1]
    classifier=source(root/'root_p37c4_result_classifier.py','d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    class_scope={'Path':Path,'copy':copy,'hashlib':hashlib,'ast':ast,'json':json}
    load_functions(classifier,class_scope,str(root/'root_p37c4_result_classifier.py'))
    # Preflight, bind_opening and the CAP postcheck have no business-guard change.
    oldtree,newtree=ast.parse(oldleaf),ast.parse(leaf)
    for name in ('saved_inputs','bind_opening','project_opening','preflight','check_before'):
        before=next(n for n in ast.walk(oldtree) if isinstance(n,ast.FunctionDef) and n.name==name)
        after=next(n for n in ast.walk(newtree) if isinstance(n,ast.FunctionDef) and n.name==name)
        if ast.dump(before)!=ast.dump(after):raise AssertionError('Unchanged guard AST differs: '+name)
    oldafter=next(n for n in ast.walk(oldtree) if isinstance(n,ast.FunctionDef) and n.name=='check_after')
    newafter=next(n for n in ast.walk(newtree) if isinstance(n,ast.FunctionDef) and n.name=='check_after')
    if ast.dump(oldafter.body[2])!=ast.dump(newafter.body[2]):raise AssertionError('CAP guard changed')
    args.output_root.mkdir(parents=True,exist_ok=False)
    fixture=args.output_root/'fixture';fixture.mkdir()
    outbox=fixture/'outbox';outbox.mkdir();qroot=fixture/'queue';qroot.mkdir();inbox=fixture/'inbox';inbox.mkdir()
    events=[];observer=[];mock_calls=[]
    def atomic(path,value,**kw):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and not kw.get('replace'):raise FileExistsError(str(path))
        raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()
        if len(raw)>kw.get('limit',1024**2):raise ValueError('fixture bound')
        path.write_bytes(raw);events.append({'event':'persist','file':path.name})
    def read(path,*a):
        if Path(path).name=='ROOT-CAMPAIGN-MAP-ADMITTED-C4.json':return copy.deepcopy(actualmap)
        return json.loads(Path(path).read_bytes())
    qt=ast.parse(queue);selected=[]
    for name in ('decoded','frame','consume_sequence','persist_loop_state','generated','full_loop'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    clean=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue')
    selected.append(next(n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name=='require_camera_pixel_admission'))
    ordinary_call=next(n for n in ast.walk(qt) if isinstance(n,ast.AsyncFunctionDef) and n.name=='call')
    env={'N':fixture,'Q':qroot,'INBOX':inbox,'OUTBOX':outbox,'Path':Path,'copy':copy,'json':json,'time':time,
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','CAPABILITIES':'ck3_get_capabilities',
        'METRICS':'root_current_runtime_metrics','AUTO':'ck3_auto_turn','SAVE':'ck3_save_checkpoint',
        'INITIAL_CAMERA':'root_initialize_campaign_camera_v1','FRONTEND':('a','b','c'),
        'REPLY_RESERVE':512*1024**2+65536,'now':lambda:datetime.now(timezone.utc),'read':read,'atomic':atomic,
        'atomic_payload_v1':lambda path,raw,**kw:atomic(path,json.loads(raw),**kw),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,
        'preserve_first_exception':lambda *a,**kw:None,'pending_request_paths':lambda *a,**kw:[],
        'display_projection':lambda row,body:{'request':row['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}},
        'load_cold_result_classifier':lambda:class_scope['classify_auto_result_credit_v1']}
    exec(compile(ast.Module(body=selected+[ordinary_call],type_ignores=[]),str(root/'root_p37c4_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        call=env['call'];consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state']
        generated=env['generated'];full_loop=env['full_loop'];require_camera_pixel_admission=env['require_camera_pixel_admission']
        def guard(self,**kw):pass
        def call_budget(self,*a):return 1
        def check_before(self,*a):pass
        def check_after(self,*a):raise AssertionError('Cold phases must use the reviewed cold postcheck')
    # Keep the actual inherited readiness selector in the ordinary MRO. The new
    # first-cold override supplies an explicit relay to the same production flow.
    original_ready=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='P37C4oldReadyQueue'))
    original_ready.body=[n for n in original_ready.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='call']
    original_ready.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[original_ready],type_ignores=[])),str(root/'root_p37c4_sdk_queue.py'),'exec'),env)
    Cold=make_saved61_cold_queue_v1(env['P37C4oldReadyQueue'],env,admission_path=Path('NO-PREFLIGHT-RUN-IN-SOFTWARE-FIXTURE'))
    q=Cold.__new__(Cold);q.__dict__.update(launch=launch,next_sequence=198,initial_frame=None,initial_save=None,
        initial_camera=None,semantic=None,zero_day_preparation=False,checkpoint_bootstrap_verified=False,cold_readiness_verified=False,
        expected_lifecycle_binding=seed['actual_saved_checkpoint']['succession_lifecycle'],
        _saved61_cold={'phase':'semantic','seed':copy.deepcopy(seed),'checkpoint':copy.deepcopy(seed['actual_saved_checkpoint']),
            'governance':{'state':{'council_pending':None,'construction_actions':{},'crown_pending':None},'pending_focus':None},
            'admission':{'classifier_pin':cppin}},job={'session_id':actualmap['recording_session_id']},
        halted=None,current_attempt=None,held_control=None,loop_count=0)
    score=ModuleType('root_score_month_samples_c4')
    def observe(rootdir,body,game,path):
        row=read(path)
        if path.name!='READINESS-0198-000001-result.json' or (outbox/'0198-1-result.json').exists():
            raise AssertionError('Observer must use the real readiness attempt before outer publication')
        if row['request']!=sem['request'] or env['decoded'](row)!=sem['result']['structured_content'] or q.next_sequence!=198:
            raise AssertionError('Observer tool/frame/sequence source mismatch')
        observer.append({'path':str(path),'row_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'canonical198_exists':False,'next_sequence':q.next_sequence});events.append({'event':'observe','file':path.name})
    score.observe_semantic=observe
    relay=ModuleType('root_p37c4_overlay_relay')
    def publish(path,compact):
        if not Path(path).exists() or q.next_sequence!=read(path)['request']['sequence']+1:
            raise AssertionError('Relay must follow consume and actual canonical publication')
        events.append({'event':'current_C4_relay','file':Path(path).name})
    relay.relay_compact=publish;relay.error_projection=lambda row:row
    oldrelay=ModuleType('root_p37_overlay_relay')
    oldrelay.relay_compact=lambda *a:(_ for _ in ()).throw(AssertionError('Old implicit provider used'))
    modules={'root_score_month_samples_c4':score,'root_p37c4_overlay_relay':relay,'root_p37_overlay_relay':oldrelay}
    prior={name:sys.modules.get(name) for name in modules};sys.modules.update(modules)
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            expected=[sem,cap][len(mock_calls)]
            if tool!=expected['request']['tool'] or arguments!={}:raise AssertionError('Unexpected tool fixture call')
            mock_calls.append(tool);return SimpleNamespace(model_dump=lambda **kw:copy.deepcopy(expected['result']))
    try:
        session=Session()
        for row in (sem,cap):
            request=copy.deepcopy(row['request']);path=inbox/f"{request['sequence']:04d}-1-result.json"
            awaitable=q.call(session,request,path)
            body,response=asyncio.run(awaitable)
            if response!=outbox/path.name or env['decoded'](read(response))!=body:raise AssertionError('Canonical response/body differs')
        correct=str(outbox/'0198-1-result.json');opening=env['frame'](sem['result']['structured_content'],semantic=True,expected_lifecycle=q.expected_lifecycle_binding)
        if q.next_sequence!=200 or q.full_loop_state!=__import__('saved61_cold_queue_v1').project_opening(seed,opening,correct):
            raise AssertionError('Exact198 source or74 historical state changed')
        bound=read(qroot/'ROOT-SAVED61-COLD-BOUND.json')
        if bound['semantic_response']!=correct or q.cold_semantic_response_path!=correct or q._saved61_cold['semantic_response']!=correct:
            raise AssertionError('Any cold source pointer has an offset')
        if q.full_loop_state['counts']!=seed['counts'] or q.full_loop_state['start_date_raw']!=53144328:
            raise AssertionError('Historical score/day counters changed')
        if Cold.full_loop is not Base.full_loop or Cold.generated is not Base.generated:raise AssertionError('Ordinary loop replaced')
        q.require_camera_pixel_admission()
        # Same actual actors/map/goal guards reject source mutations before observe.
        negatives=[]
        original=copy.deepcopy(sem['result']['structured_content'])
        for name in ('wrong_actor','wrong_Game','wrong_goal','unknown_result'):
            bad=copy.deepcopy(original);row=copy.deepcopy(sem)
            if name=='wrong_actor':bad['played_character']['character_id']+=1
            elif name=='wrong_Game':bad['diagnostics']['hello']['pid']+=1
            elif name=='wrong_goal':bad['campaign_goal']={}
            else:row['client_error']='unknown'
            row['result']['structured_content']=bad
            instance=Cold.__new__(Cold);instance.__dict__.update(copy.deepcopy(q.__dict__))
            instance.next_sequence=198;instance._saved61_cold['phase']='semantic'
            instance.current_attempt={'request':sem['request'],'row':row,'response':str(qroot/'READINESS-0198-000001-result.json')}
            try:instance.check_after(env['SEMANTIC'],{},bad)
            except ValueError:negatives.append(name)
            else:raise AssertionError('Cold business guard accepted '+name)
    finally:
        for name,value in prior.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value
    result={'schema':'xar.saved61-real-call-order-software/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,
        'actual_closed198_199_payloads_used':True,'actual_readiness_check_after_consume_publish_order':True,
        'actual_C4_ordinary_CAP_call_used':True,'source_pointer_sequence':198,'source_pointer_offset':0,
        'observer':observer,'events':events,'historical_cycles74_counts_T0_preserved':True,
        'preflight_bind_goal_and_CAP_guard_AST_unchanged':True,'original_generated_full_loop_inherited':True,
        'actual_current_C4_map_contract_used':True,'negative_cases_rejected':negatives,
        'mock_closed_payload_calls':mock_calls,'actual_Game_Native_MCP_calls':0,'runtime_files_mutated':0,
        'actual_preflight_recording_or_new_cold_pass_claimed':False}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','leaf_sha256':hashlib.sha256(leaf).hexdigest(),'qualification':str(args.output_root/'QUALIFICATION.json')}))


if __name__=='__main__':main()
