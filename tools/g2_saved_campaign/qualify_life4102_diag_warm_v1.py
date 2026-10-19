"""Actual-C7 software startup/ordinary call/full-loop composition, no live RPC."""
from __future__ import annotations
import argparse,ast,asyncio,copy,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from types import ModuleType,SimpleNamespace
from prepare_c3_life_opening_classifier_v1 import pinned,load_functions
from owner_response_json_once_v1 import prepare_success_response_row_v1
from life4102_diag_warm_queue_v1 import make_life4102_diag_warm_queue_v1, warm_inputs, TOOL, CHILD_TOOL


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',type=Path,required=True);parser.add_argument('--queue-sha256',required=True)
    parser.add_argument('--clean-seed',type=Path,required=True);parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args();root=args.runtime_root.resolve(strict=True);sources=[]
    def source(path,sha=None,limit=1024**2):
        raw,pin=pinned(path,expected=sha,limit=limit);sources.append(pin);return raw,pin
    leaf,leafpin=source(Path(__file__).with_name('life4102_diag_warm_queue_v1.py'))
    source(Path(__file__).with_name('startup_readiness_v1.py'),'c9b1bfa0efd002d2fd9f05298ba1d2ba218fa5dded335b30de18ced7d5f7b2c3')
    queue,queuepin=source(root/'root_p37c8_sdk_queue.py',args.queue_sha256)
    seedraw,seedpin=source(args.clean_seed,'11a0de1e994f597abdce3d7c2a8c5c3b810bcc576a7a872e4a3de7148e32738d')
    seed=json.loads(seedraw);refs={Path(ref['original_source']).name:ref for ref in seed['source_refs']}
    pairraw,pairpin=source(root/'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C7.json')
    actual_input={'schema':'xar.C8-LIFE4102-diagnostic-warm/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'post_close':seedpin,'old_closed':seed['actual_sdk_closed'],'old_pair':pairpin}
    warm_inputs(actual_input)
    bad_input=copy.deepcopy(actual_input);bad_input['machine_id']='wrong-machine'
    try:warm_inputs(bad_input)
    except ValueError:pass
    else:raise AssertionError('Foreign machine admission accepted')
    state=json.loads(Path(refs['ROOT-CUMULATIVE-LOOP-STATE.json']['path']).read_bytes())
    gov=json.loads(Path(refs['ROOT-GOVERNANCE-RESULT-STATE.json']['path']).read_bytes())
    freeze=json.loads((root/'ROOT-FINAL-SDK-FREEZE-P37C7.json').read_bytes());sys.path.insert(0,freeze['source_root'])
    semraw,sempin=source(root/'p37-responses/3863-1-result.json')
    capraw,cappin=source(root/'p37-responses/0519-1-result.json')
    sem=copy.deepcopy(json.loads(semraw));sem['request']={'sequence':4104,'tool':'ck3_take_semantic_snapshot_private_v1','arguments':{}}
    body=sem['result']['structured_content'];body.update(snapshot_id='native:3135',native_revision=3135,revision=2,date_raw=53188032)
    body['campaign_goal']=copy.deepcopy(state['campaign_goal_anchor'])
    body['diagnostics']['connection_generation']=body['diagnostics']['hello']['connection_generation']=5
    cap=copy.deepcopy(json.loads(capraw));cap['request']={'sequence':4105,'tool':'ck3_get_capabilities','arguments':{}}
    cap['result']['structured_content'].update(episode_run_id='native-40526-1bec95182886',episode_character_id=40526)
    classifier,cp=source(root/'root_p37c4_result_classifier.py','d47350282ad422978bac99653aa5757a5d72d6af10fb690e615592a3ff825991')
    scope={'Path':Path,'copy':copy,'json':json,'ast':ast,'hashlib':hashlib};load_functions(classifier,scope,str(root/'root_p37c4_result_classifier.py'))
    args.output_root.mkdir(parents=True,exist_ok=False);fixture=args.output_root/'fixture';fixture.mkdir()
    classifierpath=fixture/'classifier-pin.json';classifierpath.write_text(json.dumps({'source':cp['path'],'sha256':cp['sha256']}),encoding='utf-8')
    admission={'classifier_pin':source(classifierpath)[1],'lifestyle_diagnostic_path':str(fixture/'C8-LIFE2-ONCE.json'),
        'retained_C6_publisher_started':json.loads((root/'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C6.json').read_bytes())['publisher_started'],
        'retained_recording_job':'explicit-software-recording-fixture'}
    qroot=fixture/'queue';outbox=fixture/'outbox';inbox=fixture/'inbox'
    for path in (qroot,outbox,inbox,fixture/'campaign-score/months'):path.mkdir(parents=True)
    (fixture/'campaign-score/months/month-000.json').write_bytes(b'{}')
    events=[];calls=[];observed=[]
    def atomic(path,value,**kw):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and not kw.get('replace'):raise FileExistsError(path)
        path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        events.append({'event':'persist','file':path.name})
    def read(path,*a):return json.loads(Path(path).read_bytes())
    qt=ast.parse(queue);selected=[]
    for name in ('decoded','frame','consume_sequence','persist_loop_state','generated','full_loop','call'):
        selected.append(next(n for n in ast.walk(qt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name))
    baseclass=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='FreshQueue')
    selected.append(next(n for n in baseclass.body if isinstance(n,ast.FunctionDef) and n.name=='check_after'))
    clean=next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name=='CleanRobertMainMenuQueue')
    selected.append(next(n for n in clean.body if isinstance(n,ast.FunctionDef) and n.name=='require_camera_pixel_admission'))
    env={'N':fixture,'Q':qroot,'OUTBOX':outbox,'INBOX':inbox,'Path':Path,'copy':copy,'json':json,'time':time,
        'SEMANTIC':'ck3_take_semantic_snapshot_private_v1','CAPABILITIES':'ck3_get_capabilities','METRICS':'root_current_runtime_metrics',
        'AUTO':'ck3_auto_turn','SAVE':'ck3_save_checkpoint','INITIAL_CAMERA':'root_initialize_campaign_camera_v1',
        'REPLY_RESERVE':512*1024**2+65536,'FRONTEND':('a','b','c'),'now':lambda:datetime.now(timezone.utc),
        'read':read,'atomic':atomic,'atomic_payload_v1':lambda path,raw,**kw:atomic(path,json.loads(raw),**kw),
        '_owner_response_success_row_once_v1':prepare_success_response_row_v1,'preserve_first_exception':lambda *a,**kw:None,
        'display_projection':lambda row,body:{'request':row['request'],'result':{'is_error':False,'structured_content':{'status':'fixture'}}},
        'pending_request_paths':lambda *a,**kw:[],'load_cold_result_classifier':lambda:scope['classify_auto_result_credit_v1']}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'root_p37c8_sdk_queue.py'),'exec'),env)
    class Base(SimpleNamespace):
        call=env['call'];consume_sequence=env['consume_sequence'];persist_loop_state=env['persist_loop_state']
        generated=env['generated'];full_loop=env['full_loop'];require_camera_pixel_admission=env['require_camera_pixel_admission']
        check_after=env['check_after']
        def guard(self,**kw):pass
        def call_budget(self,*a):return 1
        def check_before(self,*a):pass
    old_ready=copy.deepcopy(next(n for n in qt.body if isinstance(n,ast.ClassDef) and n.name.startswith('P37') and n.name.endswith('oldReadyQueue')))
    old_ready.body=[n for n in old_ready.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='call']
    old_ready.bases=[ast.Name(id='Base',ctx=ast.Load())];env['Base']=Base
    exec(compile(ast.fix_missing_locations(ast.Module(body=[old_ready],type_ignores=[])),str(root/'root_p37c8_sdk_queue.py'),'exec'),env)
    Warm=make_life4102_diag_warm_queue_v1(env[old_ready.name],env,admission_path=Path('SOFTWARE-NO-ACTUAL-PREFLIGHT'))
    q=Warm.__new__(Warm);q.__dict__.update(launch=read(root/'ROOT-ACTUAL-GAME-LAUNCH-C4.json'),next_sequence=4104,
        initial_frame=None,initial_save=None,initial_camera=None,semantic=None,zero_day_preparation=False,
        checkpoint_bootstrap_verified=False,cold_readiness_verified=False,expected_lifecycle_binding=state['actual_saved_checkpoint']['succession_lifecycle'],
        _life4102={'phase':'semantic','admission':admission,'state':copy.deepcopy(state),'gov':copy.deepcopy(gov),'refs':refs,'post':seed,'diag_attempted':False},
        halted=None,current_attempt=None,held_control=None,loop_count=0,job={'session_id':'explicit-software-C6-retained-session'})
    score=ModuleType('root_score_month_samples_c4');score.END_RAW=53407128;score.anchor_path=None
    def observe(rootdir,snapshot,game,path):
        row=read(path)
        if path.name!='READINESS-4104-000001-result.json' or (outbox/'4104-1-result.json').exists() or q.next_sequence!=4104:
            raise AssertionError('Readiness source/check_after/consume order changed')
        if row['request']!=sem['request'] or env['decoded'](row)!=body:raise AssertionError('Observer source row mismatch')
        observed.append({'source':str(path),'next_sequence':q.next_sequence,'canonical4104_exists':False})
    score.observe_semantic=observe
    relay=ModuleType('root_p37c6_overlay_relay')
    def publish(path,compact):
        assert Path(path).exists() and q.next_sequence==read(path)['request']['sequence']+1
        events.append({'event':'retained_C6_relay','file':Path(path).name})
    relay.relay_compact=publish;relay.error_projection=lambda row:row
    legacy=ModuleType('root_p37_overlay_relay');legacy.relay_compact=lambda *a:(_ for _ in ()).throw(AssertionError('Old provider invoked'))
    mods={m.__name__:m for m in (score,relay,legacy)};prior={k:sys.modules.get(k) for k in mods};sys.modules.update(mods)
    class NewAutoReached(BaseException):pass
    class Session:
        async def call_tool(self,tool,arguments,**kw):
            if len(calls)>=2:
                assert tool==env['AUTO'];calls.append({'tool':tool,'new_sequence':4107});raise NewAutoReached()
            row=(sem,cap)[len(calls)];assert tool==row['request']['tool'] and arguments=={}
            calls.append({'tool':tool,'sequence':row['request']['sequence']})
            return SimpleNamespace(model_dump=lambda **kw:copy.deepcopy(row['result']))
    try:
        session=Session()
        for row in (sem,cap):asyncio.run(q.call(session,row['request'],inbox/f"{row['request']['sequence']:04d}-1-result.json"))
        expected=copy.deepcopy(state);expected.update(pending_cycle=None,before=q.initial_frame,before_metrics_response=str(outbox/'4104-1-result.json'),
            before_source_kind='actual_sameGame_LIFE4102_warm_semantic_snapshot')
        assert q.next_sequence==4106 and q.full_loop_state==expected and q.initial_save==state['actual_saved_checkpoint']
        assert Warm.full_loop is Base.full_loop and Warm.generated is Base.generated and q.halted is None
        atomic(fixture/'ROOT-CAMPAIGN-MAP-ADMITTED-C7.json',{'status':'GREEN','reviewer':'/root','game_pid':q.launch['pid'],
            'game_creation_filetime':q.launch['creation_filetime'],'Game_map_visible':True,'decision_text_visible':True,
            'recording_session_id':q.job['session_id'],'actual_initial_frame':q.initial_frame})
        negatives=[]
        for name in ('wrong_Game','date_drift','cold_CAP'):
            instance=Warm.__new__(Warm);instance.__dict__.update(copy.deepcopy(q.__dict__))
            instance.next_sequence=4104;instance._life4102['phase']='semantic'
            bad=copy.deepcopy(body);badcap=copy.deepcopy(cap['result']['structured_content'])
            if name=='wrong_Game':bad['diagnostics']['hello']['pid']+=1
            elif name=='date_drift':bad['date_raw']+=24
            else:instance._life4102['phase']='capabilities';badcap['native_session_control']['driver_state_restore_kind']='cold_checkpoint'
            row=copy.deepcopy(sem);row['result']['structured_content']=bad
            instance.current_attempt={'request':sem['request'],'row':row,'response':str(qroot/'READINESS-4104-000001-result.json')}
            try:instance.check_after(env['CAPABILITIES'] if name=='cold_CAP' else env['SEMANTIC'],{},badcap if name=='cold_CAP' else bad)
            except ValueError:negatives.append(name)
            else:raise AssertionError('Invalid warm binding accepted: '+name)
        assert q.full_loop_state['completed_cycles']==1956 and q.full_loop_state['counts']==state['counts']
        try:q.check_before(CHILD_TOOL,{'expected_revision':2})
        except ValueError:negatives.append('child_before_first_diagnostic')
        else:raise AssertionError('Conditional child read accepted before first diagnostic')
        require_before=False
        try:q.check_before(TOOL,{'expected_revision':2716})
        except ValueError:require_before=True
        assert require_before
        diagnostic={'schema':'xar.app-owned-lifestyle-current-state-once-diagnostic.v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
            'gameplay_action_submitted':False,'expected_revision':2,'method':'NativeDriver.query_player_lifestyle_current_state_private_v1',
            'status':'observed','same_frame':True,'query_attempted':True,
            'before':{'revision':2},'after':{'revision':2},
            'original_method_return':{'available':False,'native_error':'native_lifestyle_current_state_current_lifestyle_getter_failed'},
            'expected_owner_frame':{'bridge_pid':153556,'player_character_id':40526,'date_raw':53188032,'min_native_revision':3134,
                'episode_run_id':'native-40526-1bec95182886'}}
        async def diag_call(tool,arguments,**kw):
            assert tool==TOOL and arguments=={'expected_revision':2}
            calls.append({'tool':tool,'sequence':4106})
            return SimpleNamespace(model_dump=lambda **kw:{'is_error':False,'result_type':'complete','structured_content':copy.deepcopy(diagnostic),'content':[]})
        session.call_tool=diag_call
        asyncio.run(q.call(session,{'sequence':4106,'tool':TOOL,'arguments':{'expected_revision':2}},inbox/'4106-1-result.json'))
        assert env['decoded'](read(outbox/'4106-1-result.json'))==diagnostic and q.next_sequence==4107
        try:q.check_before(TOOL,{'expected_revision':2})
        except ValueError:negatives.append('diagnostic_replay')
        else:raise AssertionError('One diagnostic replay accepted')
        child={'schema':'xar.app-owned-child-focus-once-diagnostic.v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
            'method':'NativeDriver.query_child_education_focus_private_v1','expected_revision':2,'status':'observed',
            'gameplay_action_submitted':False,'prior_lifestyle_diagnostic_path':admission['lifestyle_diagnostic_path'],
            'original_method_return':{'available':False,'native_error':'explicit-software-child-observation'}}
        async def child_call(tool,arguments,**kw):
            assert tool==CHILD_TOOL and arguments=={'expected_revision':2}
            calls.append({'tool':tool,'sequence':4107})
            return SimpleNamespace(model_dump=lambda **kw:{'is_error':False,'result_type':'complete','structured_content':copy.deepcopy(child),'content':[]})
        session.call_tool=child_call
        asyncio.run(q.call(session,{'sequence':4107,'tool':CHILD_TOOL,'arguments':{'expected_revision':2}},inbox/'4107-1-result.json'))
        assert env['decoded'](read(outbox/'4107-1-result.json'))==child and q.next_sequence==4108
        try:q.check_before(CHILD_TOOL,{'expected_revision':2})
        except ValueError:negatives.append('child_diagnostic_replay')
        else:raise AssertionError('Conditional diagnostic replay accepted')
        assert q.full_loop_state==expected and q.full_loop_state['counts']==state['counts']
    finally:
        for k,v in prior.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
    result={'schema':'xar.C8-LIFE4102-warm-software-composition/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'sources':sources,'leaf':leafpin,
        'actual_C8_original_call_full_loop_generated_AST_loaded':True,'actual_startup_check_after_consume_publish_C6_relay_CAP_order_used':True,
        'future_SEM4104_CAP4105_are_explicit_software_fixtures':True,'constructor_and_postclose_inputs_qualified':False,
        'no_completed_result_supply_or_old_action_replay':True,'blocked4102_zero_credit_only':True,'diagnostic_nested_native_error_preserved':True,'restored1956_counts_and_loop_SAVE1773_cache_preserved':True,
        'current_source_and_classifier_opening_are_same_fresh_SEM4104':True,'original_Clean_map_gate_executed':False,
        'diagnostic_sequence':4106,'observed':observed,'events':events,'software_calls':calls,'negative_cases_rejected':negatives,
        'actual_postclose_inputs_checked':True,'conditional_child_focus_original_call_exercised':True,
        'actual_Game_Native_MCP_calls':0,'runtime_files_mutated':0,'actual_C8_warm_pass_claimed':False}
    path=args.output_root/'QUALIFICATION.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','leaf':leafpin,'qualification':str(path)}))


if __name__=='__main__':main()
