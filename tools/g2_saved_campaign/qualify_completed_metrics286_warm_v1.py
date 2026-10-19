"""Offline actual-C6 startup/call/full_loop composition for completed MET286."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType,SimpleNamespace
from prepare_c3_life_opening_classifier_v1 import pinned,load_functions
from owner_response_json_once_v1 import prepare_success_response_row_v1
from completed_metrics286_warm_resume_v1 import make_completed_met286_queue_v1,validate_inputs,SCHEMA,MACHINE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--packet-root',type=Path,required=True)
    parser.add_argument('--source-proof',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args();root=args.runtime_root.resolve(strict=True);pack=args.packet_root.resolve(strict=True);sources=[]
    def source(path,sha=None,limit=1024**2):
        raw,pin=pinned(path,expected=sha,limit=limit);sources.append(pin);return raw,pin
    def ref(path):return source(path)[1]
    leaf,leafpin=source(Path(__file__).with_name('completed_metrics286_warm_resume_v1.py'))
    source(Path(__file__).with_name('startup_readiness_v1.py'),'c9b1bfa0efd002d2fd9f05298ba1d2ba218fa5dded335b30de18ced7d5f7b2c3')
    queue,queuepin=source(root/'root_p37c6_sdk_queue.py','600703088920399e0d8c354ec283d84144c660cb9f761900df603e2077a2e63f')
    freeze=json.loads((root/'ROOT-FINAL-SDK-FREEZE-P37C6.json').read_bytes());sys.path.insert(0,freeze['source_root'])
    sys.path.append(str(root))
    from root_p37_checkpoint_cadence import checkpoint_after_settled_cycle,checkpoint_context_from_auto
    from pending_request_paths import pending_request_paths
    args.output_root.mkdir(parents=True,exist_ok=False);fixture=args.output_root/'fixture';fixture.mkdir()
    admission={'schema':SCHEMA,'machine_id':MACHINE,
        'failure_packet':ref(pack/'c5-full258-MET286-failure69/FROZEN.json'),
        'publication_failure':ref(args.source_proof),
        'original_AUTO':ref(root/'p37-responses/0285-1-result.json'),
        'original_MET':ref(root/'p37-responses/0286-1-result.json'),
        'old_closed':ref(root/'ROOT-P37C5-OWNER-CLOSED.json'),
        'old_pair':ref(root/'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C5.json'),
        'post_close':ref(pack/'c6-same-game-warm70/POST-C5-CLOSE.json')}
    # This is a labeled software ACK fixture, never written to runtime or claimed
    # as an actual C6 publication. Actual admission still requires the live ACK.
    projection=ref(root/'responses/p37-responses-0286-1-result.json')
    ackpath=fixture/'SOFTWARE-ONLY-ACK.json'
    ackpath.write_text(json.dumps({'schema':'xar.ck3.decision-text-published/v1','status':'TEXT_PUBLISHED',
        'machine_id':MACHINE,'OBS_draw_ack':False,'business_submission_or_outcome_inferred':False,
        'source_observation':projection,'publisher_started':{'software_fixture_only':True}}),encoding='utf-8')
    admission['completed_MET_publication_ACK']=ref(ackpath)
    state,gov,metrics,ack=validate_inputs(admission)
    semraw,sempin=source(root/'p37-responses/0252-1-result.json')
    capraw,cappin=source(root/'p37-responses/0253-1-result.json')
    sem=copy.deepcopy(json.loads(semraw));sem['request']={'sequence':287,'tool':'ck3_take_semantic_snapshot_private_v1','arguments':{}}
    body=sem['result']['structured_content'];body.update(snapshot_id='native:69',native_revision=69,revision=2,date_raw=53146968)
    body['diagnostics']['connection_generation']=body['diagnostics']['hello']['connection_generation']=3
    cap=copy.deepcopy(json.loads(capraw));cap['request']={'sequence':288,'tool':'ck3_get_capabilities','arguments':{}}
    classifier,cp=source(root/'root_p37c4_result_classifier.py','d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    scope={'Path':Path,'copy':copy,'json':json,'ast':ast,'hashlib':hashlib};load_functions(classifier,scope,str(root/'root_p37c4_result_classifier.py'))
    classifierpath=fixture/'classifier-pin.json';classifierpath.write_text(json.dumps({'source':cp['path'],'sha256':cp['sha256']}),encoding='utf-8')
    admission['classifier_pin']=ref(classifierpath)
    qroot=fixture/'queue';outbox=fixture/'outbox';inbox=fixture/'inbox'
    for path in (qroot,outbox,inbox,fixture/'campaign-score/months'):path.mkdir(parents=True)
    (fixture/'campaign-score/months/month-000.json').write_bytes(b'{}')
    events=[];calls=[];observed=[];guards=[]
    def atomic(path,value,**kw):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and not kw.get('replace'):raise FileExistsError(path)
        path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        events.append({'event':'persist','file':path.name})
    def read(path,*a):return json.loads(Path(path).read_bytes())
    qt=ast.parse(queue);selected=[]
    for name in ('decoded','frame','consume_sequence','persist_loop_state','generated','full_loop','call'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    cold=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='FreshQueue')
    postcheck=copy.deepcopy(next(n for n in cold.body if isinstance(n,ast.FunctionDef) and n.name=='check_after'))
    postcheck.name='original_met_postcheck';selected.append(postcheck)
    clean=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue')
    selected.append(next(n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name=='require_camera_pixel_admission'))
    env={'N':fixture,'Q':qroot,'OUTBOX':outbox,'INBOX':inbox,'Path':Path,'copy':copy,'json':json,'time':time,
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','CAPABILITIES':'ck3_get_capabilities','METRICS':'root_current_runtime_metrics',
        'AUTO':'ck3_auto_turn','SAVE':'ck3_save_checkpoint','INITIAL_CAMERA':'root_initialize_campaign_camera_v1',
        'REPLY_RESERVE':512*1024**2+65536,'FRONTEND':('a','b','c'),'now':lambda:datetime.now(timezone.utc),
        'read':read,'atomic':atomic,'atomic_payload_v1':lambda path,raw,**kw:atomic(path,json.loads(raw),**kw),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,'preserve_first_exception':lambda *a,**kw:None,
        'display_projection':lambda row,body:{'request':row['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}},
        'pending_request_paths':pending_request_paths,'load_cold_result_classifier':lambda:scope['classify_auto_result_credit_v1'],
        'checkpoint_after_settled_cycle':checkpoint_after_settled_cycle,'checkpoint_context_from_auto':checkpoint_context_from_auto,
        'pending_marker_from_credit':lambda *a,**kw:None}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c6_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        call=env['call'];consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state']
        generated=env['generated'];full_loop=env['full_loop'];require_camera_pixel_admission=env['require_camera_pixel_admission']
        check_after=env['original_met_postcheck']
        def guard(self,**kw):guards.append(kw)
        def call_budget(self,*a):return 1
        def check_before(self,*a):pass
    old_ready=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name.startswith('P37') and n.name.endswith('oldReadyQueue')))
    old_ready.body=[n for n in old_ready.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='call']
    old_ready.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old_ready],type_ignores=[])),str(root/'root_p37c6_sdk_queue.py'),'exec'),env)
    Warm=make_completed_met286_queue_v1(env[old_ready.name],env,admission_path=Path('SOFTWARE-NO-ACTUAL-PREFLIGHT'))
    q=Warm.__new__(Warm);q.__dict__.update(launch=read(root/'ROOT-ACTUAL-GAME-LAUNCH-C4.json'),next_sequence=287,
        initial_frame=None,initial_save=None,initial_camera=None,semantic=None,zero_day_preparation=False,
        checkpoint_bootstrap_verified=False,cold_readiness_verified=False,
        expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],
        _completed_met286={'phase':'semantic','admission':admission,'state':copy.deepcopy(state),'gov':copy.deepcopy(gov),'body':metrics,'ack':ack},
        halted=None,current_attempt=None,held_control=None,loop_count=0,job={'session_id':'SOFTWARE-FIXTURE-SESSION'})
    atomic(fixture/'ROOT-ACTUAL-DRIVER-MODE-P37C6.json',{'episode_projection':'one_life','before_submit_observation':True})
    score=ModuleType('root_score_month_samples_c4');score.END_RAW=53407128;score.anchor_path=None
    def observe(rootdir,snapshot,game,path):
        row=read(path)
        if path.name!='READINESS-0287-000001-result.json' or (outbox/'0287-1-result.json').exists() or q.next_sequence!=287:
            raise AssertionError('Actual startup source/check_after/consume order changed')
        if row['request']!=sem['request'] or env['decoded'](row)!=body:raise AssertionError('Observer source row mismatch')
        observed.append({'source':str(path),'next_sequence':q.next_sequence,'canonical287_exists':False})
    score.observe_semantic=observe;score.persist=lambda *a,**kw:None
    relay=ModuleType('root_p37c6_overlay_relay')
    def publish(path,compact):
        if not Path(path).exists() or q.next_sequence!=read(path)['request']['sequence']+1:raise AssertionError('Relay precedes canonical publication/consume')
        events.append({'event':'explicit_C6_relay','file':Path(path).name})
    relay.relay_compact=publish;relay.error_projection=lambda row:row
    legacy=ModuleType('root_p37_overlay_relay');legacy.relay_compact=lambda *a:(_ for _ in ()).throw(AssertionError('Old provider invoked'))
    mods={m.__name__:m for m in (score,relay,legacy)};prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    class NextAutoReached(BaseException):pass
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            if len(calls)>=2:
                calls.append({'tool':tool,'sequence':q.current_attempt,'next_sequence':q.next_sequence})
                if tool!=env['AUTO']:raise AssertionError('Old MET was replayed')
                raise NextAutoReached()
            row=(sem,cap)[len(calls)]
            if tool!=row['request']['tool'] or arguments!={}:raise AssertionError('Unexpected software RPC')
            calls.append({'tool':tool,'sequence':row['request']['sequence']})
            return SimpleNamespace(model_dump=lambda **kw:copy.deepcopy(row['result']))
    negatives=[]
    try:
        session=Session()
        for row in (sem,cap):asyncio.run(q.call(session,row['request'],inbox/f"{row['request']['sequence']:04d}-1-result.json"))
        if q.next_sequence!=289 or q.full_loop_state!=state or q.halted is not None:raise AssertionError('Original pending112 was changed by bootstrap')
        if q.initial_frame!=env['frame'](body,semantic=True,expected_lifecycle=q.expected_lifecycle_binding):raise AssertionError('App opening is not fresh SEM287')
        if Warm.full_loop is not Base.full_loop:raise AssertionError('Settlement algorithm replaced')
        atomic(fixture/'ROOT-CAMPAIGN-MAP-ADMITTED-C6.json',{'status':'GREEN','reviewer':'/root','game_pid':q.launch['pid'],
            'game_creation_filetime':q.launch['creation_filetime'],'Game_map_visible':True,'decision_text_visible':True,
            'recording_session_id':q.job['session_id'],'actual_initial_frame':q.initial_frame})
        for name in ('wrong_actor','wrong_Game','date_drift','Native_regressed','cold_CAP'):
            instance=Warm.__new__(Warm);instance.__dict__.update(copy.deepcopy(q.__dict__))
            instance.next_sequence=287;instance._completed_met286['phase']='semantic'
            bad=copy.deepcopy(body);badcap=copy.deepcopy(cap['result']['structured_content'])
            if name=='wrong_actor':bad['played_character']['character_id']+=1
            elif name=='wrong_Game':bad['diagnostics']['hello']['pid']+=1
            elif name=='date_drift':bad['date_raw']+=24
            elif name=='Native_regressed':bad['native_revision']=67;bad['snapshot_id']='native:67'
            else:instance._completed_met286['phase']='capabilities';badcap['native_session_control']['driver_state_restore_kind']='cold_checkpoint'
            row=copy.deepcopy(sem);row['result']['structured_content']=bad
            instance.current_attempt={'request':sem['request'],'row':row,'response':str(qroot/'READINESS-0287-000001-result.json')}
            try:instance.check_after(env['CAPABILITIES'] if name=='cold_CAP' else env['SEMANTIC'],{},badcap if name=='cold_CAP' else bad)
            except ValueError:negatives.append(name)
            else:raise AssertionError('Invalid fresh binding accepted: '+name)
        try:asyncio.run(q.generated(session,env['AUTO']))
        except ValueError:negatives.append('AUTO_before_original_MET286_rejected')
        else:raise AssertionError('Pending112 bypassed original MET')
        first=asyncio.run(q.full_loop(session,{'sequence':289,'command':'full_loop','arguments':{'max_turns':1}},inbox/'0289-1-result.json'))
        settled=copy.deepcopy(q.full_loop_state)
        if len(calls)!=2 or first['cumulative_cycles']!=112 or first['actual_turns']!=1 or q.next_sequence!=290:
            raise AssertionError('Original full_loop did not settle112 with zero RPC/sequence replay')
        event=read(qroot/'CUMULATIVE-TURN-000112.json')
        rebound=read(qroot/'ROOT-MET286-SETTLED-AND-WARM-REBOUND.json')
        if (settled['pending_cycle'] is not None or event['after_metrics_response']!=admission['original_MET']['path']
                or event['after']['revision']!=9 or settled['before']!=q.initial_frame
                or settled['before_metrics_response']!=str(outbox/'0287-1-result.json')
                or rebound['settled_metrics_frame']!=event['after']
                or rebound['new_ordinary_credit_from_rebind']!=0):
            raise AssertionError('Original286 settlement or subsequent actual-opening source rebind changed')
        for key,value in state['counts'].items():
            if settled['counts'][key]!=value+(1 if key=='primitive_accepted_turns' else 0):raise AssertionError('Unrelated credit changed: '+key)
        if settled['start_date_raw']!=state['start_date_raw'] or settled['actual_saved_checkpoint']!=state['actual_saved_checkpoint'] or settled['checkpoint_dirty_since_save'] is not True:
            raise AssertionError('T0/lastSaved61/dirty changed')
        if (qroot/'CUMULATIVE-TURN-000112.json').is_file() is not True:raise AssertionError('Original settlement marker missing')
        try:asyncio.run(q.full_loop(session,{'sequence':290,'command':'full_loop','arguments':{'max_turns':1}},inbox/'0290-1-result.json'))
        except NextAutoReached:pass
        else:raise AssertionError('Original generated next AUTO did not run')
        if len(calls)!=3 or calls[-1]['tool']!=env['AUTO'] or not (inbox/'0291-1-result.json').is_file():raise AssertionError('Next new AUTO sequence differs')
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.completed-MET286-C6-software-composition/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'leaf':leafpin,
        'future_SEM287_CAP288_and_ACK_are_explicit_software_fixtures':True,
        'actual_readiness_check_after_consume_canonical_publish_explicit_relay_CAP_flow':True,'observed':observed,
        'exact_C6_original_full_loop_generated_call_AST_used':True,'original_Clean_map_gate_and_MET_postcheck_executed':True,
        'old_MET286_replayed_RPC_count':0,'full289_settled_cycle':first['cumulative_cycles'],'first_counts':settled['counts'],
        'original_MET_path_and_public_revision9_preserved':True,'next_new_AUTO_sequence':291,
        'settled112_then_current_source_rebound_to_fresh_SEM287_public2':True,
        'negative_cases_rejected':negatives,'software_calls':calls,'events':events,
        'actual_Game_Native_MCP_calls':0,'runtime_files_mutated':0,'actual_C6_preflight_or_warm_claimed':False,
        'limits':['Constructor process/recording guards require actual runtime preflight.',
            'Physical C6 SEM/CAP and publisher ACK remain owner-produced live evidence.']}
    (args.output_root/'QUALIFICATION.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','leaf':leafpin,'qualification':str(args.output_root/'QUALIFICATION.json')}))


if __name__=='__main__':main()
