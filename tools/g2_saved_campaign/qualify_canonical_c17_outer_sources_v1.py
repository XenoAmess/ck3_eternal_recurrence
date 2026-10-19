"""Detached qualifications for the actual future outer creator hunks. No Game/Task."""
import argparse
import ast
import asyncio
import copy
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import types
import sys

import canonical_c17_outer_binding_v1 as binding
import c17_normal_checkpoint_inputs_v1 as normal
import prepare_canonical_c17_outer_sources_v1 as producer


def require(ok, why):
    if not ok:raise ValueError(why)


def function(source, name):
    return next(n for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)


def bootstrap_case(sources):
    node=function(sources['root_checkpoint_bootstrap_c17.py'],'launch_prepared')
    calls=[]
    runtime=types.SimpleNamespace(NativeBridgeLaunchConfig=lambda *args:'bridge',
        launch=lambda *args,**kwargs:calls.append((args,kwargs)))
    native=types.SimpleNamespace(validate_cold_start_checkpoint_for_pipe=lambda *args:'validated')
    ns={'api':lambda:(None,native,runtime),'verify_cold_profile':lambda spec:None,
        'read':lambda path:{'pipe_name':'original-pipe'},'N':Path('Z:/detached'),
        'PRELAUNCH':'original-prelaunch','Path':Path}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-bootstrap','exec'),ns)
    spec=object();ns['launch_prepared'](spec,'dll','injector')
    require('pre_native_resume' not in calls[-1][1],'default path unexpectedly added a hook')
    same_hook=object();ns['launch_prepared'](spec,'dll','injector',pre_native_resume=same_hook)
    require(calls[-1][1]['pre_native_resume'] is same_hook
        and calls[-1][1]['before_process_create'] is None,'original same hook was not passed before runtime resume')
    return 'actual bootstrap: absent hook preserves original kwargs; enabled same callback identity'


async def stdio_cases():
    events=[];streams=object();generation=object();edge=object()
    @asynccontextmanager
    async def captured(stock,**kwargs):
        events.append('capture_enter')
        try:yield types.SimpleNamespace(require_generation=lambda:generation)
        finally:events.append('capture_exit')
    @asynccontextmanager
    async def stdio(params,**kwargs):
        events.append('stock_enter')
        try:yield streams
        finally:events.append('stock_exit')
    params=types.SimpleNamespace(command='direct-python',args=['-B','-S','entry'],cwd='cwd',env={'original':'1'})
    stock=types.SimpleNamespace(stdio_client=stdio)
    error=RuntimeError('original business exception identity')
    try:
        async with binding.owned_stdio(None,stock,params,errlog='err',capture_factory=captured) as value:
            require(value==(streams,generation),'default stdio streams changed')
            raise error
    except RuntimeError as actual:
        require(actual is error,'default stdio replaced the original exception')
    require(events==['capture_enter','stock_enter','stock_exit','capture_exit'],'original MCP/Job context cleanup order changed')
    events.clear()
    @asynccontextmanager
    async def spawn(plan,**kwargs):
        events.append('actual_mcp_creator')
        try:yield edge,streams,generation
        finally:events.append('original_mcp_cleanup')
    chain=types.SimpleNamespace(prepare_child_v1=lambda *args,**kwargs:events.append(('prepare',kwargs)) or object(),
        spawn_owned_mcp_v1=spawn,
        export_actual_child_chain_v1=lambda *args:events.append('export_actual_App_before_pair_wait'))
    b=types.SimpleNamespace(chain=chain,result=types.SimpleNamespace(holder=object()),
        child_env=lambda env:dict(env),root=Path('Z:/detached'),io=object(),control=object())
    async with binding.owned_stdio(b,stock,params,errlog='err',capture_factory=captured) as value:
        require(value==(streams,generation),'enabled original MCP streams changed')
        events.append('original_Queue_pair_publication_and_wait')
    require(events[0][0]=='prepare' and events[0][1]['role']=='MCPApp'
        and events[1:]==['actual_mcp_creator','export_actual_App_before_pair_wait',
            'original_Queue_pair_publication_and_wait','original_mcp_cleanup'], 'actual App upward chain handshake reordered')
    return 'original stock contexts/exception identity preserved; App chain exported before original pair wait'


def owner_case():
    b=binding.OuterBindingV1.__new__(binding.OuterBindingV1)
    b.result=types.SimpleNamespace(holder=types.SimpleNamespace(_creation_role_v1='owner'))
    b.io=object();b.control=object()
    b.direct_python=Path('C:/qualified/base/python.exe');b.root=Path('Z:/detached');b.dependency_root=Path('Z:/qualified/deps')
    events=[];child=object();edge=object();plan=types.SimpleNamespace(child=child)
    def prepare(holder,**kwargs):
        events.append(('prepare',kwargs));return plan
    b.chain=types.SimpleNamespace(prepare_child_v1=prepare,
        spawn_owned_popen_v1=lambda p,**kwargs:events.append('actual_Popen_return') or edge,
        export_actual_child_chain_v1=lambda *args:events.append('export_original_Queue_App_handles'))
    original=['old-venv-redirector','-B','-X','utf8','Z:/detached/root_p37c17_sdk_queue.py','--continuous']
    require(b.spawn_queue(original,stdout='stdout',stderr='stderr') is child,'owner did not retain original Popen')
    args=events[0][1]
    require(args['command']==[str(b.direct_python),'-B','-S','-X','utf8',*original[4:]]
        and args['entry_source']==original[4] and args['role']=='Queue'
        and args['env']['XAR_FRESH_SDK_DEPENDENCY_ROOT']==str(b.dependency_root)
        and events[1:]==['actual_Popen_return','export_original_Queue_App_handles'],
        'direct Queue command/dependency environment/export source differs')
    return 'actual outer method uses true direct base Queue command, original args and dependency root'


def static_callers(sources):
    sup=ast.parse(sources['root_native30_supervisor_c17.py'])
    main=next(n for n in sup.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    calls=[n for n in ast.walk(main) if isinstance(n,ast.Call)]
    launch=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='launch_prepared')
    hook=next(k.value for k in launch.keywords if k.arg=='pre_native_resume')
    require(isinstance(hook,ast.IfExp) and ast.unparse(hook.orelse)=='canonical.factory.pre_native_resume',
        'supervisor does not pass its same retained factory hook')
    text=ast.get_source_segment(sources['root_native30_supervisor_c17.py'].decode(),main)
    require(text.index('canonical.revoke()')<text.index('signal_sdk_exit(reason)')
        and text.index('canonical.close()')>text.index('runtime.stop_tracked(handle'), 'root revoke or original cleanup order changed')
    app=sources['root_p37c17_mcp_entry.py'].decode()
    require(app.index('server=original_create(')<app.index('_canonical.install_service(service)')
        and "if not sys.flags.no_site:" in app,'actual retained Service/no-site guard was bypassed')
    queue=sources['root_p37c17_sdk_queue.py'].decode()
    require('"--driver", "native-headless"' in queue and '"-B", "-S", "-X", "utf8"' in queue,
        'existing App driver/private flags/no-site command changed')
    return 'actual supervisor hook/creator, post-original Service install and revoke-before-stop source seams'


def normal_input_case(sources):
    pair=[{'role':role,'pid':pid,'creation_filetime':birth,'exit_code':0,
        'kernel_exit_observed':True,'observation_error':None} for role,pid,birth in normal.OLD_PAIR]
    publisher={'pid':123,'creation_filetime':456}
    rows={'sdk':{'machine_id':binding.MACHINE,'normal':True,'launcher_exit_code':0,'processes':pair},
        'pair':{'processes':pair},
        'game':{'machine_id':binding.MACHINE,**normal.OLD_GAME,'kernel_signaled':True,'exit_code':0,'forced_owned_job_cleanup':False},
        'capture':{'game_pid':normal.OLD_GAME['pid'],'game_creation_filetime':normal.OLD_GAME['creation_filetime'],
            'inputs_unbound':True,'engine_close':{'actual_exit_code':0,'normal_exit_proven':True,'forced_process_calls':0}},
        'started':{'game':normal.OLD_GAME,'publisher':publisher},
        'pubchild':{'machine_id':binding.MACHINE,'publisher':publisher,'normal_STOP_observed':True,'first_error':None},
        'pubowner':{'machine_id':binding.MACHINE,'publisher':publisher,'status':'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO',
            'kernel_exit_observed':True,'exit_code':0,'forced_process_calls':0,
            'Popen_original_kernel_handle_retained':True,'child_closed':'pubchild'},
        'record':{'status':'CLEANUP_OBSERVED','capture_closed_verified':True,'inputs_unbound':True,
            'engine_exit_code':0,'normal_engine_exit_proven':True,'stop_rpc_calls':0,'capture_closed':'capture',
            'decision_text_publisher':{'status':'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO','machine_id':binding.MACHINE,
                'normal_exit_claimed':True,'exit_proof_consumed_from_original_owner':True,
                'forced_process_calls':0,'owner_closed':'pubowner','publisher_started':'started'}}}
    close={'machine_id':binding.MACHINE,'old_sdk_closure_kind':normal.KIND,'old_Game':normal.OLD_GAME,
        'sdk_closed':'sdk','old_sdk_pair':'pair','Game_exit':'game','recording_shutdown':'record'}
    normal.validate_normal_closure(close,rows.__getitem__)
    for slot,key,value in [('game','creation_filetime',1),('pubowner','exit_code',1),('sdk','normal',False)]:
        old=rows[slot][key];rows[slot][key]=value
        try:normal.validate_normal_closure(close,rows.__getitem__)
        except ValueError:pass
        else:raise ValueError('foreign/abnormal normal-closure fixture was accepted')
        finally:rows[slot][key]=old
    # Execute the actual existing cold factory SAVE projector, including its
    # original source-bound checkpoint_saved callback; never touch a Driver/SAVE.
    import importlib.util
    cadence_name='root_p37_checkpoint_cadence'
    prior=sys.modules.get(cadence_name)
    spec=importlib.util.spec_from_file_location(cadence_name,producer.prior.T/(cadence_name+'.py'))
    cadence=importlib.util.module_from_spec(spec);spec.loader.exec_module(cadence)
    sys.modules[cadence_name]=cadence
    try:
        factory=sources['root_p37c17_cold_resume.py']
        nodes=[function(factory,'clean'),function(factory,'project_checkpoint_seed')]
        ns={'copy':copy,'hashlib':hashlib,'Path':Path,'require':require}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-maintenance-projector','exec'),ns)
        original=json.loads((producer.prior.T.parent.parent/'p51-fresh1066-v20261019-prepare01/c16-war-results8495-failure91/state.json').read_bytes())
        original['pending_cycle']=None
        before=original['before'];cp=copy.deepcopy(original['actual_saved_checkpoint'])
        cp['date_raw']=before['date_raw']
        body={'paused':True,'map_ready':True,'one_life_terminal':False,'revision':before['revision'],
            'played_character':{'alive':True,'character_id':before['actor_character_id']},
            'date_raw':before['date_raw'],'episode_run_id':before['episode_run_id'],
            'diagnostics':{'bridge_pid':normal.OLD_GAME['pid'],'hello':{'pid':normal.OLD_GAME['pid']}},
            'campaign_goal':original['campaign_goal_anchor']}
        save={'request':{'tool':'ck3_save_checkpoint','arguments':{'expected_revision':body['revision']}},
            'result':{'is_error':False,'result_type':'complete','structured_content':{'checkpoint':cp}}}
        semantic={'result':{'is_error':False,'structured_content':body}}
        admission={'old_sdk_closure_kind':normal.KIND,'old_Game':normal.OLD_GAME,
            'save_response':{'path':'synthetic-SAVE-response'},'saved_semantic_response':{'path':'synthetic-SEM-response'},
            'cold_prelaunch':'prelaunch'}
        rows['prelaunch']={'final_driver_close':'close'};rows['close']={**close,'checkpoint':cp}
        projector=ns['project_checkpoint_seed']
        seed=projector(original,save,save_response=admission['save_response']['path'],
            semantic_response=admission['saved_semantic_response']['path'])
        normal.validate_saved_seed(admission,seed,original,save,semantic,
            {'completed_cycles':original['completed_cycles'],'pending_cycle':None},projector=projector,checked=rows.__getitem__)
        require(seed['completed_cycles']==original['completed_cycles']
            and seed['counts']['checkpoint_saved']==original['counts']['checkpoint_saved']+1,
            'actual direct-SAVE projector changed ordinary credit or lost new maintenance SAVE')
    finally:
        if prior is None:sys.modules.pop(cadence_name,None)
        else:sys.modules[cadence_name]=prior
    return 'normal closure positive/foreign Game/failed publisher/non-normal SDK rejects; actual original SAVE projector increments only SAVE count'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    disabled,off_records=producer.build_sources()
    # This is a synthetic source label solely to exercise generated syntax. It
    # is never written into a Native pin, freeze, config or runtime admission.
    enabled,records=producer.build_sources(enabled=True,native_build_label='Native30 SYNTHETIC_SOFTWARE_LABEL_NOT_ADMITTED')
    require(binding.prepare_supervisor(object(),enabled=False) is None
        and binding.receive_entry(object(),'owner',[],enabled=False) is None,'default OFF performed policy/resource work')
    checks=[bootstrap_case(enabled),asyncio.run(stdio_cases()),owner_case(),static_callers(enabled),normal_input_case(enabled)]
    for name in ('canonical_c17_outer_binding_v1.py','c17_normal_checkpoint_inputs_v1.py','prepare_canonical_c17_outer_sources_v1.py',Path(__file__).name):
        compile((producer.OWN/name).read_bytes(),name,'exec')
    files={name:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in enabled.items()}
    own={name:{'bytes':(producer.OWN/name).stat().st_size,
        'sha256':hashlib.sha256((producer.OWN/name).read_bytes()).hexdigest()} for name in
        ('canonical_c17_outer_binding_v1.py','c17_normal_checkpoint_inputs_v1.py','prepare_canonical_c17_outer_sources_v1.py',Path(__file__).name)}
    report={'schema':'xar.c17.canonical-outer-source-qualification/v1','machine_id':binding.MACHINE,
        'utc':datetime.now(timezone.utc).isoformat(),'status':'OUTER_SOURCE_SEAMS_QUALIFIED_NOT_DEPLOYED',
        'D_writes':0,'Task_registrations':0,'Game_RPC':0,'Driver_SAVE_body_reads':0,
        'source_inputs':producer.PINS,'new_repo_sources':own,'changed_repo_bytes':sum(v['bytes'] for v in own.values()),
        'outputs_in_memory_only':files,'output_logical_bytes':sum(len(raw) for raw in enabled.values()),
        'exact_inverse_hunks':{name:len(hunks) for name,hunks in records.items()},'checks':checks,
        'topology':['durable Task: canonical supervisor -> actual SDKowner -> Queue -> stock MCP App',
            'durable Task: original decision display/OBS owner','durable Task: original feeder'],
        'remaining_before_any_freeze_or_adoption':[
            'Root complete new canonical SDK closure: phase M7 eleven files alone are insufficient',
            'Native30 actual qualification/DLL identity, current normal SAVE/clean closure and metadata budget',
            'Supply actual future normal maintenance SAVE/current clean state and exact normal C16 closure receipts; the finite F90 path remains isolated',
            'Freeze creator three tools and all entry sources/policy/direct base Python/dependency file pins',
            'Actual harmless complete source-enabled creator chain / Native30 optional component not exercised by these detached tests',
            'Only sole runtime may create the three durable Tasks, new Game and actual cold SEM/CAP/pixel admission'],
        'H_state':'unknown; no actual provider adoption or qualification RPC is claimed'}
    with args.output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps({'output':str(args.output),'bytes':args.output.stat().st_size,
        'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'changed_repo_bytes':report['changed_repo_bytes'],
        'logical_outputs_not_written':report['output_logical_bytes'],'checks':len(checks)}))


if __name__=='__main__':main()
