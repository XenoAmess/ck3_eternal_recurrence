"""One shared allocation followed immediately by the existing screen keeper."""
from __future__ import annotations
import ast
from ck3_mod_acceptance_launcher_protocol_v1 import BACKGROUND_CLOSURE_SCHEMAS_V1
from ck3_mod_acceptance_background_types import FilePin, JsonObject, ProcessGeneration, json_object, file_pin, keyed_file_pin, object_field, text_field, strings_field, CONTROL_QUEUE_MODULE_ORDER_V1
from ck3_mod_acceptance_fresh_machine_bootstrap import (
    FRESH_ADMISSION_MODE, FRESH_BOOTSTRAP_SCHEMA, MachineBinding,
    require_empty_machine_history, validate_fresh_bootstrap, create_current_process_observation,
    fresh_ledger_path, retire_pre_identity_request, parse_bootstrap, validate_frozen_fresh_admission,
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import argparse
    from ck3_mod_acceptance import Selection
    from xar_autoplayer.saved_campaign_profile_inventory_v2 import Inventory
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,platform,re,subprocess,sys,time
import math
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Literal, Protocol, TypedDict, runtime_checkable
from ck3_mod_acceptance import (Selection,path_at,check_pin,pin,read_json,same_directory_control_peer,
    NormalExitAllocatedContextV1, NormalExitAllocationBindingV1,
    normal_exit_tools_opted_in_v1, normal_exit_static_binding_v1,
    _verification_actual_pin_v1)
from ck3_mod_acceptance_prepare import write_json
from ck3_mod_acceptance_runtime_inputs import validate_allocated_running_inputs

def recording_input_files(selection: Selection) -> dict[Path, FilePin]:
    sources = selection.recording_runtime_input_sources()
    if sources is None:
        raise ValueError('Actual recording running-input source closure required')
    return {Path(row['path']).resolve(): row for row in (sources['helper'], sources['contract'])}


@runtime_checkable
class _NormalExitProfileProducerV1(Protocol):
    def load_builder(self, path: Path) -> object: ...
    def create_profile(self, args: object, runtime: object, manifest: object,
                       runtime_manifest: object, destination: Path, builder: object) -> object: ...


def allocate_normal_exit_profile_v1(selection: Selection, live: Path) -> NormalExitAllocationBindingV1 | None:
    """Invoke the existing create-only producer once, after the actual run ID."""
    case = json_object(selection.case)
    if not normal_exit_tools_opted_in_v1(case.get('required_mcp_tools', [])):
        return None
    manifest = json_object(selection.manifest)
    runtime = json_object(selection.runtime)
    paths = object_field(runtime, 'paths')
    source = Path(text_field(paths, text_field(object_field(manifest, 'source_root'), 'path_key'))).resolve()
    producer_path = source / 'tools/ck3_mod_acceptance_normal_exit_profile.py'
    builder_path = source / 'tools/build_normal_exit_source_inventory_v1.py'
    spec = importlib.util.spec_from_file_location('_allocated_existing_normal_exit_profile', producer_path)
    if spec is None or spec.loader is None:
        raise ValueError('Existing managed normal-exit profile producer is unavailable')
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    if not isinstance(producer, _NormalExitProfileProducerV1):
        raise ValueError('Existing managed normal-exit producer interface differs')
    native = object_field(manifest, 'native')
    state = selection.state_dir.resolve()
    args = SimpleNamespace(state_dir=state, game_dir=Path(text_field(runtime, 'game_dir')).resolve(),
        bridge_dll=Path(text_field(paths, text_field(object_field(native, 'dll'), 'path_key'))).resolve(),
        bridge_injector=Path(text_field(paths, text_field(object_field(native, 'injector'), 'path_key'))).resolve(),
        output=live.resolve() / 'native-report.json',
        frontend_mod_load_observation=text_field(object_field(case, 'startup'), 'mode') == 'workshop_cache',
        saved_campaign_save=None)
    manifest_ref = _verification_actual_pin_v1(selection.manifest_path)
    profile = producer.create_profile(args, runtime, manifest, manifest_ref,
        live.resolve() / 'normal-exit-binding', producer.load_builder(builder_path))
    binding = normal_exit_static_binding_v1(profile, state_dir=state,
        run_dir=live, runtime_manifest=manifest_ref)
    binding['files'].extend([_verification_actual_pin_v1(producer_path), _verification_actual_pin_v1(builder_path)])
    return binding


def require(value: object, message: str) -> None:
    if not value:raise ValueError(message)

LEGACY_KEEPER_SHA='2afdf264b509a045c878fd1ee94426cf418cd747a5773ded43a83001a3813def'
LEGACY_KEEPER_BUS=Path('C:/workspace/.codex-task-bus')
LEGACY_KEEPER_BUS_SHA='B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'

def verify_profile_inventory(declared,observed):
    require(set(observed)==set(declared) and all(observed[k]['sha256']==declared[k]['sha256'] and
            ('bytes' not in declared[k] or observed[k]['bytes']==declared[k]['bytes']) for k in declared),
            'Cold profile changed after preparation')

def closed_session(report):
    return (bool(report.get('finished_at')) and report.get('managed_session_thread_finished') is True
            and report.get('cleanup_ok') is True)

def native_cleanup_closed(report):
    native=report.get('session',{}).get('report',{});shutdown=native.get('shutdown',{})
    inventory=shutdown.get('final_ck3_inventory',{});absent=shutdown.get('control_files_absent')
    return (bool(native.get('finished_at')) and shutdown.get('ok') is True and
        shutdown.get('cleanup_proven') is True and shutdown.get('tree_gone') is True and
        shutdown.get('job_active_processes_final')==0 and shutdown.get('contract_errors')==[] and
        inventory.get('tasklist_returncode')==0 and all(inventory.get(k)==[] for k in
            ('tasklist_pids','wmi_pids','native_pids','processes')) and isinstance(absent,dict) and
        bool(absent) and all(v is True for v in absent.values()))

def previous_native_cleanup(previous,freeze):
    """Reuse the original terminal parse; the native body is only statted here."""
    native_path=previous/'native-report.json'
    projection_path=previous/'native-cleanup-projection.actual.json'
    if not projection_path.exists():
        return read_json(native_path),None,None
    require(projection_path.stat().st_size<=1048576,'Previous native cleanup projection exceeds small receipt limit')
    raw=projection_path.read_bytes()
    require(len(raw)<=1048576,'Previous native cleanup projection exceeds small receipt limit')
    value=json.loads(raw.decode('utf-8-sig'))
    require(isinstance(value,dict) and value.get('schema')=='lyd.native-cleanup-field-projection.v1' and
            value.get('run_id')==freeze['run_id'],'Previous native cleanup projection crossed run/schema')
    original=value.get('original_native_report',{})
    require(isinstance(original,dict) and Path(original.get('path','')).resolve()==native_path.resolve() and
            type(original.get('bytes')) is int and original['bytes']>0 and native_path.is_file() and
            native_path.stat().st_size==original['bytes'] and
            re.fullmatch(r'[0-9a-fA-F]{64}',str(original.get('sha256',''))) is not None,
            'Previous native cleanup projection original path/size/pin differs')
    host_path=previous/'host-original-process-exit.json';host=value.get('original_host_exit',{})
    require(isinstance(host,dict) and Path(host.get('path','')).resolve()==host_path.resolve(),
            'Previous native cleanup projection host exit path differs')
    check_pin(host_path,host)
    exited=read_json(host_path)
    require(exited.get('run_id')==freeze['run_id'] and exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int,'Previous native cleanup projection original host wait differs')
    report=value.get('projection')
    require(isinstance(report,dict),'Previous native cleanup projection fields missing')
    projection_pin={'path':str(projection_path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    return report,original,projection_pin

def previous_session_closure(previous,freeze,report,report_reference=None):
    """Keep failed launch cleanup separate from a returned native shutdown."""
    if closed_session(report):
        require(native_cleanup_closed(report),'Previous native job/tree/inventory/control closure unproven; no OS0 inference')
        return {'mode':'previous-shared-managed-session'}
    session=report.get('session')
    require(bool(report.get('finished_at')) and report.get('managed_session_thread_finished') is True and
        report.get('status')=='RED' and report.get('cleanup_ok') is False and report.get('steps')==[] and
        report.get('readiness') is None and isinstance(session,dict) and session.get('report') is None and
        isinstance(session.get('error'),str) and re.fullmatch(
            r'AgentError: native-session failed after [0-9]+(?:\.[0-9]+)?s \(launch_error\): '
            r'CK3 launch contract failed safely: .+',session['error']),
        'Previous live session has not proved complete cleanup or an exact safe failed launch')
    state=Path(freeze['state_dir']).resolve()
    require(Path(report.get('state_dir','')).resolve()==state,'Previous failed-launch state differs from frozen argv')
    control=state/'control'
    require(control.is_dir(),'Previous failed-launch control directory missing')
    absent={name:not (control/name).exists() for name in ('unsafe-cleanup.json','ck3.json')}
    absent['watchdog-*.ready.json']=not list(control.glob('watchdog-*.ready.json'))
    require(all(absent.values()),'Previous failed-launch unsafe/PID/watchdog-ready controls remain')
    started_path=previous/'host-started.json';exit_path=previous/'host-original-process-exit.json'
    started=read_json(started_path);exited=read_json(exit_path)
    require(started.get('run_id')==freeze['run_id'] and exited.get('run_id')==freeze['run_id'] and
        started.get('actual_popen_retained') is True and exited.get('actual_original_popen_wait') is True and
        type(started.get('pid')) is int and started['pid']>0 and type(exited.get('pid')) is int and
        exited['pid']==started['pid'] and
        type(exited.get('returncode')) is int and exited['returncode']==1 and
        exited.get('normal_ck3_exit_inferred') is False,
        'Previous failed-launch original host Popen failure is missing or crossed run/PID')
    return {'mode':'previous-shared-failed-launch','failure_cleanup':{
        'report':report_reference if report_reference is not None else pin(previous/'native-report.json'),
        'host_started':pin(started_path),'host_exit':pin(exit_path),
        'safe_launch_error':session['error'],'control_files_absent':absent,
        'control_observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'original_cleanup_ok':False,'original_ck3_exit_code':None,'original_job_active_processes_final':None,
        'typed_normal_exit_proven':False,'business_pass':False}}

def previous_allocated_unused_closure(previous,freeze,close_path,keeper_root,release,bus_packet):
    """Reuse a READY allocation refused before launch, without native/OS0 credit."""
    bundle=read_json(close_path);evidence={}
    require(bundle.get('schema')=='ck3-public-cell-pre-consumption-close-v1' and
            bundle.get('status')=='CLOSED_RESOURCE_ONLY' and bundle.get('run_id')==freeze['run_id'] and
            all(bundle.get(k) is False for k in ('allocation_consumed','native_session_started',
                'host_started','game_started','normal_close_qualified','business_pass')) and
            bundle.get('retained_actual_OS0') is None,'Actual unconsumed READY closure required')
    def original(key,path):
        ref=bundle[key]
        require(Path(ref['path']).resolve()==path.resolve(),'Unconsumed original path differs: '+key)
        check_pin(path,ref);evidence[key]=ref
        return read_json(path)
    original('frozen_argv_pin',previous/'frozen-argv.json')
    ready=original('ready_context_pin',previous/'ready-context.json')
    allocated_context=original('allocated_context_pin',previous/'allocated-context.json')
    require(ready.get('run_id')==freeze['run_id'] and
            Path(ready['run_dir']).resolve()==previous.resolve() and
            Path(ready['keeper_root']).resolve()==keeper_root.resolve() and
            ready['frozen_argv']==bundle['frozen_argv_pin'], 'Unconsumed READY identity differs')
    keeper=original('keeper_report_pin',keeper_root/'report.json')
    parent=original('keeper_actual_parent_exit_pin',previous/'keeper-actual-parent-exit.json')
    require(parent.get('run_id')==freeze['run_id'] and parent.get('keeper_actual_exit_code')==0 and
            parent.get('keeper_report')==keeper and keeper.get('thread_exited') is True and
            keeper.get('failure') is None,'Actual cooperative keeper wait0 required')
    modern_idle=bundle.get('unused_reason')=='NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT'
    if modern_idle:
        machine=freeze.get('identity_allocation',{}).get('machine_id')
        prepared_path=Path(ready.get('prepared_case',{}).get('path','')).resolve()
        original('prepared_case_pin',prepared_path)
        ledger=Path(freeze['state_dir']).resolve().parent/'single-use-ledger'
        if 'single_use_ledger' in freeze:
            nested=Path(freeze['single_use_ledger']).resolve()
            require(nested==ledger/'pre-identity-epoch-000002',
                    'Recovered first allocation ledger must remain in the original profile ledger namespace')
            validate_frozen_fresh_admission(json_object(freeze),previous)
            ledger=nested
        allocation_intent=original('single_use_intent_pin',ledger/'allocation-intent.json')
        allocated=original('single_use_allocated_pin',ledger/'allocated.json')
        keeper_ready=original('keeper_ready_pin',keeper_root/'ready.json')
        idle=original('idle_timeout_pin',previous/'allocation-unused-idle-timeout.json')
        stop_path=keeper_root/'STOP';stop_ref=bundle['keeper_stop_pin']
        require(Path(stop_ref['path']).resolve()==stop_path.resolve(),'Idle STOP original path differs')
        check_pin(stop_path,stop_ref);evidence['keeper_stop_pin']=stop_ref
        require(bool(machine) and bundle.get('machine_id')==machine and
                ready.get('prepared_case')==bundle['prepared_case_pin'] and
                allocated_context.get('run_id')==freeze['run_id'] and
                allocated_context.get('prepared_case')==ready['prepared_case'] and
                allocation_intent.get('status')=='CONSUMED_ALLOCATION_INTENT_NOT_RUN' and
                allocation_intent.get('prepared_case')==ready['prepared_case'] and
                allocated.get('status')=='ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN' and
                Path(allocated.get('live','')).resolve()==previous.resolve() and
                allocated.get('task')==freeze['screen_task'] and
                Path(allocated.get('keeper_root','')).resolve()==keeper_root.resolve() and
                Path(allocated.get('prepared_case','')).resolve()==prepared_path and
                Path(allocated.get('actual_host_argv','')).resolve()==(previous/'frozen-argv.json').resolve() and
                allocated.get('keeper_ready')==keeper_ready and
                keeper_ready.get('lease',{}).get('task_id')==freeze['screen_task'] and
                keeper.get('game_actions') is False and
                idle.get('reason')=='NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT' and
                type(idle.get('idle_seconds')) is int and idle['idle_seconds']==600 and
                all(idle.get(k) is False for k in ('game_started','native_session_started','normal_close_qualified','business_pass')) and
                stop_path.read_text(encoding='utf-8')=='Unused allocation idle deadline; no game/native/normal credit.\n',
                'Actual modern unused allocation/idle STOP identity differs')
        times=[datetime.fromisoformat(value) for value in
               (keeper_ready['at_utc'],idle['utc'],keeper['at_utc'])]
        require(all(t.tzinfo is not None and t.utcoffset() is not None for t in times) and
                (times[1]-times[0]).total_seconds()>=600 and times[2]>=times[1],
                'Actual original ten-minute idle window did not expire')
        operation_dirs=[]
        for mode,code in (('run',2),('allocate',0)):
            key='public_'+mode
            intent_path=Path(bundle[key+'_intent_pin']['path']).resolve()
            require(intent_path.name=='intent.json','Modern original public intent path differs')
            command=original(key+'_intent_pin',intent_path)
            process=original(key+'_process_pin',intent_path.parent/'original-process.json')
            ended=original(key+'_exit_pin',intent_path.parent/'original-exit.json')
            argv=command.get('argv',[])
            def argument(name):
                require(isinstance(argv,list) and argv.count(name)==1 and argv.index(name)+1<len(argv),
                        'Modern original public argument missing: '+name)
                return argv[argv.index(name)+1]
            require(all(row.get('machine_id')==machine for row in (command,process,ended)) and
                    command.get('stage')==mode and bool(command.get('at_utc')) and
                    process.get('argv')==argv and type(process.get('pid')) is int and process['pid']>0 and
                    type(process.get('create_time')) in (int,float) and process['create_time']>0 and
                    ended.get('pid')==process['pid'] and ended.get('actual_original_popen_wait') is True and
                    type(ended.get('returncode')) is int and ended['returncode']==code and
                    bool(ended.get('completed_at_utc')) and argv[-1:]==[mode] and argv.count(mode)==1 and
                    Path(argument('--prepared-case')).resolve()==prepared_path,
                    'Modern original public '+mode+' retained wait differs')
            operation_dirs.append(intent_path.parent.parent)
            if mode=='run':
                context_path=Path(argument('--run-context')).resolve();context=read_json(context_path)
                result=original('public_run_stdout_pin',intent_path.parent/'stdout.log')
                refusal=original('public_run_stderr_pin',intent_path.parent/'stderr.log')
                require(context.get('run_id')==freeze['run_id'] and
                        Path(context.get('run_dir','')).resolve()==previous.resolve() and
                        Path(context.get('keeper_root','')).resolve()==keeper_root.resolve() and
                        context.get('frozen_argv')==ready['frozen_argv'] and
                        context.get('prepared_case')==ready['prepared_case'] and
                        result.get('run_id')==freeze['run_id'] and result.get('host_argv')==freeze['argv'] and
                        result.get('runtime_status')=='LAUNCH_FAILED' and
                        result.get('business_acceptance')=='NOT_ASSESSED' and result.get('launcher_exit_code')==2 and
                        refusal.get('status')=='BLOCKED' and refusal.get('business_pass') is False and
                        refusal.get('error')=="ValueError('Original keeper has stopped or requested STOP')",
                        'Modern unused run is not the original keeper-STOP prelaunch refusal')
                run_intent=intent_path;run_runtime=Path(argument('--runtime')).resolve()
                evidence['public_run_context_pin']=pin(context_path)
            else:
                require(Path(argument('--keeper-output')).resolve()==keeper_root.resolve() and
                        Path(argument('--runtime')).resolve()==run_runtime,
                        'Modern original allocation crossed keeper/runtime')
        require(operation_dirs[0]==operation_dirs[1] and
                [path.resolve() for path in operation_dirs[0].glob('*/intent.json')
                 if read_json(path).get('stage')=='run']==[run_intent] and
                not (previous/'host-supervisor-started.json').exists(),
                'Modern idle closure requires its unique public run and no actual supervisor')
    scene=keeper_root.parent
    refs=bundle['original_process_exit_pins']
    never_attempted=bundle.get('unused_reason')=='coordinator_interrupted_before_first_launch'
    release_stem='screen-release-01'
    if modern_idle:
        terminals=()
    elif never_attempted:
        require(bundle.get('observer_status')=='NEVER_STARTED' and bundle.get('observer_exit_code') is None
                and bundle.get('original_windows_expired') is True
                and not any(scene.glob('public-run-*-operation.json'))
                and not any(scene.glob('allocation-observer-*-operation.json')),
                'Never-attempted allocation has run/observer activity')
        old_budget=bundle['original_control_window_pin']
        check_pin(Path(old_budget['path']),old_budget);evidence['original_control_window_pin']=old_budget
        budget=read_json(Path(old_budget['path']))
        require(datetime.fromisoformat(bundle['utc'])>datetime.fromisoformat(budget['valid_until_utc']),
                'Actual interrupted close must follow the expired original window')
        release_stem=bundle.get('screen_release_stem')
        require(release_stem in ('screen-release-01','screen-release-02'),'Exact original release stem required')
        terminals=(('public-allocate-01',0),('stop-keeper-01',0),(release_stem,0))
    else:
        terminals=(('public-run-01',2),('public-run-02',2),('allocation-observer-01',2),
                   ('public-allocate-01',0),('screen-release-01',0))
    for name,code in terminals:
        path=scene/(name+'-process-exit.json');ref=refs[name]
        require(Path(ref['path']).resolve()==path.resolve(),'Unconsumed terminal crossed scene')
        check_pin(path,ref);wait=read_json(path);operation=wait['operation']
        check_pin(Path(operation['path']),operation);op=read_json(Path(operation['path']))
        require(wait.get('schema')=='xar-root-exact-public-command-exit-v1' and
                wait.get('returncode')==code and bool(wait.get('finished_utc')) and
                op.get('schema')=='xar-root-exact-public-command-v1',
                'Unconsumed original terminal differs')
        for key in ('stdout','stderr'):check_pin(Path(wait[key]['path']),wait[key])
        argv=op['argv']
        if name.startswith('public-'):
            mode='allocate' if name=='public-allocate-01' else 'run'
            index=next((i for i,arg in enumerate(argv) if Path(arg).name=='ck3_mod_acceptance.py'),-1)
            require(index>=0 and argv[index+1]==mode and
                    Path(argv[argv.index('--prepared-case')+1]).resolve()==
                    Path(bundle['prepared_case_pin']['path']).resolve(),
                    'Unconsumed public terminal crossed case/mode')
            if mode=='run':
                context=read_json(Path(argv[argv.index('--run-context')+1]))
                result=read_json(Path(wait['stdout']['path']))
                require(context.get('run_id')==freeze['run_id'] and
                        Path(context['run_dir']).resolve()==previous.resolve() and
                        result.get('runtime_status')=='LAUNCH_FAILED' and
                        result.get('business_acceptance')=='NOT_ASSESSED',
                        'Unconsumed run must be an actual prelaunch refusal')
        evidence[name]=ref
    if not never_attempted and not modern_idle:
        trigger=original('observer_trigger_pin',scene/'allocation-pressure-trigger-01.json')
        require(trigger.get('actual_run_id')==freeze['run_id'] and trigger.get('reason')==
                'FINITE_OBSERVER_WINDOW_EXPIRED_NOT_BUSINESS_TIMEOUT', 'Original observer expiry missing')
    require(Path(bundle['release_result_pin']['path']).resolve()==
            ((previous/'root-screen-release-a01.json').resolve() if modern_idle else
             Path(refs[release_stem]['path']).with_name(release_stem+'.stdout.log').resolve()),
            'Unconsumed original release path differs')
    check_pin(Path(bundle['release_result_pin']['path']),bundle['release_result_pin'])
    require(read_actual_release(Path(bundle['release_result_pin']['path']))==release and
            closed_lease(keeper,release,freeze['screen_task']), 'Actual unconsumed lease release required')
    matching=[t for t in bus_packet.get('tasks',[]) if t.get('task_id')==freeze['screen_task']]
    require(len(matching)==1 and matching[0].get('state') in ('done','waiting') and
            matching[0].get('resources')==[] and matching[0].get('last_sequence',-1)>=
            release['task']['last_sequence'], 'Unconsumed predecessor lease still occupied')
    names=('launch-intent.json','launch.json','host-started.json','host-supervisor.json',
           'host-original-process-exit.json','native-report.json','case-output')
    absent={name:not (previous/name).exists() for name in names}
    absent['state/control']=not (Path(freeze['state_dir'])/'control').exists()
    absent['run/controls/*']=not (previous/'controls').exists() or not any((previous/'controls').iterdir())
    require(all(absent.values()),'Unconsumed predecessor has actual launch/native/control evidence')
    import psutil
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Unconsumed CK3/keeper/controller still present')
    return {'mode':'previous-shared-allocated-unused','actual_process_inventory':inventory,
            'failure_cleanup':{'close':pin(close_path),'original_evidence':evidence,
                'absent_launch_native_and_control_evidence':absent,'native_session_started':False,
                'host_started':False,'original_ck3_exit_code':None,'typed_normal_exit_proven':False,
                'business_pass':False}}


def predecessor_keeper_report_v1(keeper_root: Path, *, aborted_wrapper: bool,
        pre_ready: bool, expired_keeper: bool, interrupted_owner: bool) -> JsonObject | None:
    """Let each exceptional reducer validate its own original terminal evidence."""
    if aborted_wrapper or pre_ready or expired_keeper or interrupted_owner:
        return None
    return json_object(read_json(keeper_root/'report.json'))


def require_predecessor_keeper_release_v1(keeper: JsonObject | None, release: JsonObject,
        task: str, *, exceptional_terminal_validated: bool) -> None:
    """An exceptional reducer owns terminal evidence; ordinary closure needs the report."""
    if exceptional_terminal_validated:
        return
    if keeper is None or not closed_lease(keeper,release,task):
        raise ValueError('Previous screen keeper/release is not closed')


def wait_for_allocated_keeper(child,live,keeper_root,*,idle_seconds=600):
    """Stop only an allocation that never started launching within ten minutes.

    An admitted host keeps its existing lifecycle and budgets. The actual Popen
    wait remains the exit evidence; no CK3/native/normal exit is inferred here.
    """
    deadline=time.monotonic()+idle_seconds
    launch_names=('launch-intent.json','launch.json','host-started.json','host-supervisor.json','native-report.json')
    while child.poll() is None:
        if any((live/name).exists() for name in launch_names):
            return child.wait()
        if time.monotonic()>=deadline:
            import psutil
            if any((p.info.get('name') or '').lower()=='ck3.exe' for p in psutil.process_iter(['name'])):
                return child.wait()
            write_json(live/'allocation-unused-idle-timeout.json',{
                'utc':datetime.now(timezone.utc).isoformat(),'reason':'NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT',
                'idle_seconds':idle_seconds,'game_started':False,'native_session_started':False,
                'normal_close_qualified':False,'business_pass':False})
            stop=keeper_root/('STOP' if (keeper_root/'inputs.json').exists() else 'stop.request')
            if not stop.exists():
                with stop.open('x',encoding='utf-8') as stream:
                    stream.write('Unused allocation idle deadline; no game/native/normal credit.\n')
                    stream.flush();os.fsync(stream.fileno())
            return child.wait()
        time.sleep(.5)
    return child.wait()

def previous_never_launched_closure(previous,freeze,close_path,keeper_root,release,bus_packet):
    """Close an allocated checkout failure without inventing a native/OS exit."""
    bundle=read_json(close_path)
    require(bundle.get('schema')=='ck3-mod-acceptance-never-launched-closure-v1' and
            bundle.get('run_id')==freeze['run_id'],'Exact never-launched predecessor bundle required')
    ready_path=previous/'ready-context.json';ready=read_json(ready_path)
    require(ready.get('run_id')==freeze['run_id'] and
            Path(ready.get('run_dir','')).resolve()==previous.resolve() and
            Path(ready.get('keeper_root','')).resolve()==keeper_root.resolve(),
            'Never-launched READY crossed run/keeper')
    check_pin(previous/'frozen-argv.json',ready['frozen_argv'])
    keeper_path=keeper_root/'report.json';keeper=read_json(keeper_path)
    require(keeper.get('task_id')==freeze['screen_task'] and keeper.get('thread_exited') is True and
            keeper.get('failure') is None and keeper.get('game_actions') is False and
            keeper.get('entry_error')=="RuntimeError('screen task checkout has current tracked or untracked changes')",
            'Exact terminated prelaunch checkout keeper failure required')
    parent_path=previous/'keeper-actual-parent-exit.json';parent=read_json(parent_path)
    require(parent.get('run_id')==freeze['run_id'] and parent.get('keeper_report')==keeper and
            type(parent.get('keeper_actual_exit_code')) is int and parent['keeper_actual_exit_code']==1,
            'Original failed keeper parent wait required')
    row=bundle.get('allocator_result',{});command_path=Path(row.get('path',''))
    check_pin(command_path,row);command=read_json(command_path);argv=command.get('argv',[])
    def argument(name):
        require(isinstance(argv,list) and argv.count(name)==1 and argv.index(name)+1<len(argv),
                'Never-launched original allocator argument missing: '+name)
        return argv[argv.index(name)+1]
    require(command.get('schema')=='ck3-recorded-actual-command-v1' and
            type(command.get('exit_code')) is int and command['exit_code']==0 and
            bool(command.get('finished_at_utc')) and 'allocate' in argv and
            Path(argument('--keeper-output')).resolve()==keeper_root.resolve() and
            Path(argument('--prepared-case')).resolve()==Path(ready['prepared_case']['path']).resolve(),
            'Original allocator terminal0 crossed prepared case/keeper')
    names=('launch-intent.json','launch.json','host-started.json','host-supervisor.json','supervisor.json',
           'host-original-process-exit.json','native-report.json','native-cleanup-projection.actual.json')
    absent={name:not (previous/name).exists() for name in names}
    state=Path(freeze['state_dir']).resolve()
    absent['state/control']=not (state/'control').exists()
    controls=previous/'controls'
    absent['run/controls/*']=controls.is_dir() and not any(controls.iterdir())
    require(all(absent.values()),'Never-launched predecessor has launch/native/PID/control evidence')
    tasks=bus_packet.get('tasks',[])
    matching=[task for task in tasks if task.get('task_id')==freeze['screen_task']]
    require(closed_lease(keeper,release,freeze['screen_task']) and len(matching)==1 and
            matching[0].get('state') in ('done','waiting') and matching[0].get('resources')==[] and
            matching[0].get('last_sequence')>=release['task']['last_sequence'],
            'Never-launched predecessor actual CAS release/current no-owner unproven')
    import psutil
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Never-launched CK3/keeper/controller still present')
    return {'mode':'previous-shared-never-launched-checkout-failure',
            'actual_process_inventory':inventory,'failure_cleanup':{
                'close':pin(close_path),'original_evidence':{'ready':pin(ready_path),
                  'frozen':pin(previous/'frozen-argv.json'),'keeper':pin(keeper_path),
                  'keeper_parent_wait':pin(parent_path),'allocator':pin(command_path)},
                'absent_launch_native_and_control_evidence':absent,
                'native_session_started':False,'host_started':False,'typed_normal_exit_proven':False,
                'original_ck3_exit_code':None,'business_pass':False}}

def _prelaunch_fields(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError('Prelaunch evidence must be an object')
    fields: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('Prelaunch evidence key must be a string')
        fields[key] = item
    return fields


def _saved_readonly_tail_prelaunch(stderr: object, bundle: object) -> bool:
    terminal = ('saved campaign initial tail plan permits read-only observations only; '
                'normal GUI Save/Load/quit has separate same-live evidence')
    if not isinstance(stderr, str) or stderr.splitlines() != [terminal]:
        return False
    fields = _prelaunch_fields(bundle)
    if (fields.get('closure_kind') != 'saved-campaign-readonly-tail-prelaunch'
            or fields.get('native_session_started') is not False
            or fields.get('normal_close_qualified') is not False
            or fields.get('business_pass') is not False):
        raise ValueError('Readonly-tail closure must explicitly preserve no-native/no-business state')
    return True


def _prelaunch_public_completion(value: object, mode: Literal['run', 'allocate'],
                                 machine: object) -> list[str]:
    fields = _prelaunch_fields(value)
    if not isinstance(machine, str) or not machine or fields.get('machine_id') != machine:
        raise ValueError('Readonly-tail public command machine differs')
    code = 2 if mode == 'run' else 0
    wait_key = 'original_popen_wait_result' if mode == 'run' else 'original_Popen_wait_returncode'
    pid_key = 'pid' if mode == 'run' else 'original_pid'
    pid = fields.get(pid_key)
    if (type(fields.get('exit_code')) is not int or fields['exit_code'] != code
            or type(fields.get(wait_key)) is not int or fields[wait_key] != code
            or type(pid) is not int or pid <= 0
            or (mode == 'allocate' and fields.get('status') != 'ORIGINAL_POPEN_COMPLETED')):
        raise ValueError('Readonly-tail original public command retained wait differs')
    stamps: list[datetime] = []
    for key in ('started_at_utc', 'finished_at_utc'):
        raw = fields.get(key)
        if not isinstance(raw, str):
            raise ValueError('Readonly-tail public command timestamp missing')
        stamp = datetime.fromisoformat(raw)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError('Readonly-tail public command timestamp lacks timezone')
        stamps.append(stamp)
    if stamps[1] < stamps[0]:
        raise ValueError('Readonly-tail public command completion precedes start')
    raw_argv = fields.get('argv')
    if not isinstance(raw_argv, list):
        raise ValueError('Readonly-tail public command argv missing')
    argv: list[str] = []
    for argument in raw_argv:
        if not isinstance(argument, str):
            raise ValueError('Readonly-tail public command argv must contain strings')
        argv.append(argument)
    return argv


def _allocated_profile_prelaunch(stderr: object, frozen: object) -> bool:
    terminal = 'This selected projection derives the actual profile once; supplied replacement is forbidden'
    if not isinstance(stderr, str) or stderr.splitlines()[-1:] != ['ValueError: ' + terminal]:
        return False
    fields = json_object(frozen)
    argv = strings_field(fields, 'argv')
    selected = [Path(item).resolve() for item in argv if item.endswith('shared-host.py')]
    if len(selected) != 1:
        raise ValueError('Allocated profile rejection requires its selected frozen host')
    host = selected[0]
    reference = object_field(object_field(fields, 'files'), str(host))
    check_pin(host, reference)
    frames = re.findall(r'  File "([^"]+)", line [0-9]+, in ([^\r\n]+)', stderr)
    if (len(frames) != 2 or [frame[1] for frame in frames] != ['<module>', 'main']
            or any(Path(frame[0]).resolve() != host for frame in frames)
            or f"raise ValueError('{terminal}')" not in stderr):
        raise ValueError('Allocated profile rejection requires the original pre-game main stack')
    return True


@runtime_checkable
class _SavedInventoryVerifierV2(Protocol):
    def parse_inventory(self, value: object) -> Inventory: ...
    def verify_inventory(self, inventory: Inventory, *, profile: Path,
                         actual_enabled_mods: object) -> Inventory: ...


class FrozenV2RegistrarRejection(TypedDict):
    host: FilePin
    source_index: FilePin
    verifier: FilePin
    inventory: FilePin
    prepared_case: FilePin
    registrar: FilePin
    inventory_binding: Literal['reproduced_from_frozen_prepared_file_closure']
    original_rejection_reproduced: Literal[True]


def _saved_inventory_registrar_prelaunch(stderr: object, frozen: object) -> FrozenV2RegistrarRejection | None:
    """Reproduce the exact frozen V2 rejection, before any managed game session."""
    terminal = 'ValueError: Saved campaign fixture/overlay contains a cold-start registrar: '
    if not isinstance(stderr, str) or not stderr.splitlines():
        return None
    last = stderr.splitlines()[-1]
    if not last.startswith(terminal):
        return None
    fields = json_object(frozen)
    argv: list[str] = strings_field(fields, 'argv')
    files = object_field(fields, 'files')
    hosts = [Path(arg).resolve() for arg in argv if Path(arg).name == 'shared-host.py']
    indices = [Path(path).resolve() for path in files if Path(path).name == 'source-index.json']
    if len(hosts) != 1 or len(indices) != 1:
        raise ValueError('V2 registrar requires exact frozen host/source index')
    host, index = hosts[0], indices[0]
    check_pin(host, object_field(files, str(host)))
    check_pin(index, object_field(files, str(index)))
    root = Path(text_field(fields, 'source_root')).resolve()
    machine = text_field(object_field(fields, 'identity_allocation'), 'machine_id')
    sources = _canonical_source_index_files(read_json(index), root, machine)
    verifier = root / 'ck3_autonomous_player/src/xar_autoplayer/saved_campaign_profile_inventory_v2.py'
    if verifier not in sources:
        raise ValueError('V2 registrar verifier is absent from frozen source index')
    check_pin(verifier, dict(sources[verifier]))
    frames = re.findall(r'  File "([^"]+)", line ([0-9]+), in ([^\r\n]+)\r?\n    ([^\r\n]+)', stderr)
    expected = ((host, 'run', 'saved_campaign = prepare_saved_campaign(args, spec)'),
                (host, 'prepare_saved_campaign', 'inventory = verify_inventory(parse_inventory(inventory_value), profile=profile, actual_enabled_mods=dlc["enabled_mods"])'),
                (verifier, 'verify_inventory', 'raise ValueError("Saved campaign fixture/overlay contains a cold-start registrar: " + str(path))'))
    if len(frames) < 3:
        raise ValueError('V2 registrar frozen pre-game call chain missing')
    for (path, line, function, statement), (source, name, code) in zip(frames[-3:], expected):
        lines = source.read_text(encoding='utf-8-sig').splitlines()
        if (Path(path).resolve() != source or function != name or statement.strip() != code
                or not 0 < int(line) <= len(lines) or lines[int(line)-1].strip() != code):
            raise ValueError('V2 registrar traceback differs from frozen source call chain')
    def argument(flag: str) -> str:
        if argv.count(flag) != 1 or argv.index(flag)+1 >= len(argv):
            raise ValueError('V2 registrar frozen argument missing: ' + flag)
        return argv[argv.index(flag)+1]
    profile = Path(text_field(fields, 'state_dir')).resolve() / 'profile'
    offending = Path(last[len(terminal):]).resolve()
    if (not offending.is_relative_to(profile) or offending.suffix.casefold() != '.txt'
            or not offending.is_file() or offending.is_symlink()):
        raise ValueError('V2 registrar must identify its original prepared fixture file')
    inventory = Path(argument('--saved-campaign-product-inventory')).resolve()
    preparations = [Path(path).resolve() for path in files if Path(path).name=='prepared-case.json']
    if len(preparations)!=1:
        raise ValueError('V2 registrar original frozen preparation missing')
    prepared_path = preparations[0]
    check_pin(prepared_path, object_field(files, str(prepared_path)))
    prepared = read_json(prepared_path)
    startup = object_field(prepared, 'startup')
    if (startup.get('mode')!='saved_campaign' or startup.get('state_dir')!=str(profile.parent)
            or object_field(startup, 'saved_campaign').get('product_inventory')!=str(inventory)):
        raise ValueError('V2 registrar inventory crossed frozen prepared startup')
    profile_files = object_field(object_field(object_field(prepared, 'preparation'), 'profile_preparation'), 'files')
    expected_products = [file_pin(value) for relative,value in profile_files.items()
                         if relative.startswith(('mod/', 'mod-content/'))]
    inventory_value = read_json(inventory)
    product_values = inventory_value.get('product_files')
    if (not isinstance(product_values, list) or not expected_products
            or sorted((file_pin(value) for value in product_values), key=lambda row:row['path'])
                != sorted(expected_products, key=lambda row:row['path'])):
        raise ValueError('V2 registrar inventory differs from frozen prepared file closure')
    spec = importlib.util.spec_from_file_location('_prelaunch_saved_inventory_v2', verifier)
    if spec is None or spec.loader is None:
        raise ValueError('Frozen V2 inventory verifier cannot be loaded')
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        if not isinstance(module, _SavedInventoryVerifierV2):
            raise ValueError('Frozen V2 inventory verifier interface missing')
        try:
            module.verify_inventory(module.parse_inventory(inventory_value), profile=profile,
                                    actual_enabled_mods=read_json(profile/'dlc_load.json')['enabled_mods'])
        except ValueError as error:
            if str(error) != last[len('ValueError: '):]:
                raise ValueError('Frozen V2 verifier did not reproduce the original registrar rejection') from error
        else:
            raise ValueError('Frozen V2 verifier no longer rejects the original registrar')
    finally:
        if previous is None:sys.modules.pop(spec.name, None)
        else:sys.modules[spec.name] = previous
    return FrozenV2RegistrarRejection(host=file_pin(pin(host)), source_index=file_pin(pin(index)),
        verifier=sources[verifier], inventory=file_pin(pin(inventory)),
        prepared_case=file_pin(pin(prepared_path)), registrar=file_pin(pin(offending)),
        inventory_binding='reproduced_from_frozen_prepared_file_closure', original_rejection_reproduced=True)


def _prelaunch_root_public_wait(wait_value: object, intent_value: object, producer: str, wait_path: Path,
        machine: str, mode: Literal['run', 'allocate'], run_id: str) -> list[str]:
    """Read the actual Root intent/wait pair without inventing Popen metadata."""
    waited, intent = json_object(wait_value), json_object(intent_value)
    code = 2 if mode == 'run' else 0
    wait_fields = {'machine_id', 'original_wait_returncode', 'elapsed_seconds'}
    intent_fields = {'machine_id', 'argv'}
    if mode == 'run':
        wait_fields |= {'run_id', 'finished_at_utc'}
        intent_fields |= {'run_id', 'started_at_utc'}
    else:
        wait_fields.add('observed_at_utc')
    if set(waited) != wait_fields or set(intent) != intent_fields:
        raise ValueError('V2 registrar original Root intent/wait fields differ')
    elapsed = waited.get('elapsed_seconds')
    if (waited.get('machine_id') != machine or intent.get('machine_id') != machine
            or type(waited.get('original_wait_returncode')) is not int
            or waited['original_wait_returncode'] != code or type(elapsed) not in (int, float)
            or not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed <= 0):
        raise ValueError('V2 registrar actual Root public wait differs')
    stamp = datetime.fromisoformat(text_field(waited, 'finished_at_utc' if mode == 'run' else 'observed_at_utc'))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('V2 registrar actual Root public wait timestamp lacks timezone')
    if mode == 'run':
        start = datetime.fromisoformat(text_field(intent, 'started_at_utc'))
        if (start.tzinfo is None or start > stamp or waited.get('run_id') != run_id
                or intent.get('run_id') != run_id):
            raise ValueError('V2 registrar actual Root run identity/chronology differs')
    tree = ast.parse(producer)
    popens = [node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
        and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id=='p'
        and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name) and node.value.func.value.id=='subprocess'
        and node.value.func.attr=='Popen']
    waits = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
        and len(node.targets)==1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id=='code'
        and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name) and node.value.func.value.id=='p'
        and node.value.func.attr=='wait' and not node.value.args and not node.value.keywords]
    targets = [node for node in ast.walk(tree) if isinstance(node, ast.With) and any(
        isinstance(item.context_expr, ast.Call) and isinstance(item.context_expr.func, ast.Attribute)
        and item.context_expr.func.attr=='open' and item.context_expr.args
        and isinstance(item.context_expr.args[0], ast.Constant) and item.context_expr.args[0].value=='x'
        and isinstance(item.context_expr.func.value, ast.BinOp)
        and isinstance(item.context_expr.func.value.op, ast.Div)
        and isinstance(item.context_expr.func.value.right, ast.Constant)
        and item.context_expr.func.value.right.value==wait_path.name for item in node.items)]
    dumps = [node for target in targets for node in ast.walk(target) if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
        and node.func.value.id=='json' and node.func.attr=='dump' and node.args
        and isinstance(node.args[0], ast.Dict) and any(isinstance(key, ast.Constant)
            and key.value=='original_wait_returncode' and isinstance(value, ast.Name) and value.id=='code'
            for key,value in zip(node.args[0].keys,node.args[0].values))]
    if (len(popens)!=1 or len(waits)!=1 or len(dumps)!=1
            or not (popens[0].lineno, popens[0].col_offset) < (waits[0].lineno, waits[0].col_offset) < (dumps[0].lineno, dumps[0].col_offset)
            or any(keyword.arg=='shell' and not (isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False) for keyword in popens[0].keywords)):
        raise ValueError('V2 registrar Root producer must record the original Popen.wait result')
    argv: list[str] = strings_field(intent, 'argv')
    indices = [index for index,arg in enumerate(argv) if Path(arg).name=='ck3_mod_acceptance.py']
    if len(indices)!=1 or indices[0]+1>=len(argv) or argv[indices[0]+1]!=mode:
        raise ValueError('V2 registrar actual Root command mode differs')
    return argv


def _prelaunch_background_admission(value: object, machine: object) -> None:
    """Read historical launch provenance only; this grants no current offline admission."""
    from steam_offline_state_contract import parse_result
    admission = json_object(value)
    reference = object_field(admission, 'receipt')
    path = Path(text_field(reference, 'path')).resolve()
    size = reference.get('bytes')
    if type(size) is not int or not 0 < size <= 65536:
        raise ValueError('Prelaunch background receipt size differs')
    check_pin(path, reference)
    result = parse_result(read_json(path))
    steam = result.steam
    if (admission.get('schema') != 'ck3-mod-acceptance-background-offline-admission-v1'
            or admission.get('machine_id') != machine or result.machine_id != machine
            or result.status != 'offline' or result.observation_method != 'native_current_user_byte'
            or admission.get('background_only') is not True or steam is None
            or type(admission.get('steam_pid')) is not int or admission['steam_pid'] != steam.pid
            or admission.get('steam_birth_filetime') != steam.birth_filetime
            or admission.get('observed_at_utc') != result.observed_at_utc
            or admission.get('observation_method') != result.observation_method):
        raise ValueError('Prelaunch background admission provenance differs')


def _profile_replacement_public_completion(value: object, mode: Literal['run', 'allocate'],
                                           machine: object) -> list[str]:
    fields = json_object(value)
    expected = 2 if mode == 'run' else 0
    elapsed = fields.get('elapsed_seconds')
    if (not isinstance(machine, str) or not machine or fields.get('machine_id') != machine
            or type(fields.get('original_wait_returncode')) is not int
            or fields['original_wait_returncode'] != expected
            or type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed <= 0):
        raise ValueError('Allocated profile original public command retained wait differs')
    started = datetime.fromisoformat(text_field(fields, 'started_at_utc'))
    if started.tzinfo is None or started.utcoffset() is None:
        raise ValueError('Allocated profile public command timestamp lacks timezone')
    if mode == 'run':
        finished = datetime.fromisoformat(text_field(fields, 'finished_at_utc'))
        if finished.tzinfo is None or finished.utcoffset() is None or finished < started:
            raise ValueError('Allocated profile public command completion precedes start')
    return strings_field(fields, 'argv')


def previous_menu_initialization_failure(previous: Path, freeze: dict[str, object], bundle: object,
        close_path: Path, keeper_root: Path, release: dict[str, object], bus_packet: dict[str, object]) -> dict[str, object]:
    """Admit only the observed pre-game campaign-factory failure, never native cleanup."""
    import psutil
    value = json_object(bundle)
    frozen = json_object(freeze)
    evidence = object_field(value, 'original_evidence')
    required = {'frozen_argv', 'ready_context', 'prepared_case', 'host_started', 'host_exit', 'host_supervisor',
                'native_report', 'server_stderr', 'readiness_result', 'entry_result',
                'keeper_report', 'keeper_parent_exit', 'keeper_process'}
    if (set(value) != {'schema', 'closure_kind', 'machine_id', 'observed_at_utc', 'run_id', 'keeper_root',
                       'normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass',
                       'native_cleanup_qualified', 'original_evidence'} or set(evidence) != required):
        raise ValueError('Exact menu initialization closure fields required')
    machine = text_field(object_field(frozen, 'identity_allocation'), 'machine_id')
    run_id = text_field(frozen, 'run_id')
    if (value.get('schema') != 'ck3-mod-acceptance-prelaunch-host-failure-closure-v1'
            or value.get('closure_kind') != 'menu-mcp-initialization-before-native-session'
            or value.get('machine_id') != machine or value.get('run_id') != run_id
            or Path(text_field(value, 'keeper_root')).resolve() != keeper_root.resolve()
            or any(value.get(key) is not False for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass'))
            or 'native_cleanup_qualified' not in value or value['native_cleanup_qualified'] is not None):
        raise ValueError('Menu initialization failure identity/negative qualification differs')
    stamp = datetime.fromisoformat(text_field(value, 'observed_at_utc'))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError('Menu failure observation requires an actual timezone')

    def original(key: str, expected: Path, *, decode: bool = True) -> JsonObject:
        ref = file_pin(evidence.get(key))
        if Path(ref['path']).resolve() != expected.resolve() or ref['bytes'] > 1048576:
            raise ValueError('Menu failure original path/bound differs: ' + key)
        check_pin(expected, dict(ref))
        return json_object(json.loads(expected.read_bytes())) if decode else {}

    original('frozen_argv', previous / 'frozen-argv.json')
    ready = original('ready_context', previous / 'ready-context.json')
    if (ready.get('run_id') != run_id or ready.get('frozen_argv') != evidence['frozen_argv']
            or Path(text_field(ready, 'run_dir')).resolve() != previous.resolve()
            or Path(text_field(ready, 'keeper_root')).resolve() != keeper_root.resolve()):
        raise ValueError('Menu failure READY/frozen binding differs')
    prepared = original('prepared_case', Path(text_field(object_field(ready, 'prepared_case'), 'path')))
    if (object_field(prepared, 'startup').get('mode') != 'workshop_cache'
            or prepared.get('runtime_manifest') != frozen.get('runtime_manifest')
            or ready.get('prepared_case') != evidence['prepared_case']):
        raise ValueError('Menu failure is not the actual prepared cache boundary')
    host = original('host_started', previous / 'host-started.json')
    exited = original('host_exit', previous / 'host-original-process-exit.json')
    supervisor = original('host_supervisor', previous / 'host-supervisor-started.json')
    if (host.get('run_id') != run_id or exited.get('run_id') != run_id
            or host.get('argv') != frozen.get('argv') or host.get('actual_popen_retained') is not True
            or exited.get('actual_original_popen_wait') is not True or type(exited.get('returncode')) is not int
            or exited['returncode'] != 1 or exited.get('pid') != host.get('pid')
            or exited.get('normal_ck3_exit_inferred') is not False):
        raise ValueError('Menu failure lacks its original host Popen wait1')
    report = original('native_report', previous / 'native-report.json')
    original('server_stderr', previous / 'native-report.server-stderr.log', decode=False)
    stderr = (previous / 'native-report.server-stderr.log').read_text(encoding='utf-8-sig')
    if (stderr.splitlines()[-1:] != ['ValueError: One original ordinary service/driver']
            or not all(fragment in stderr for fragment in ('registration_mcp.py', 'controls = Controls(service, driver)',
                'driver.episode_projection == "native_campaign"', 'in native_server'))):
        raise ValueError('Menu failure is not the exact observed campaign factory rejection')
    if (report.get('status') != 'RED' or report.get('phase') != 'initializing-mcp' or not report.get('error')
            or not report.get('finished_at') or report.get('steps') != []
            or report.get('session') != {'report': None, 'error': None}
            or any(report.get(key) is not False for key in ('managed_session_done', 'managed_session_thread_finished', 'cleanup_ok'))
            or report.get('frontend_mod_load_launch') != {'status': 'WAITING_FOR_ACTUAL_SINGLE_MENU_LAUNCH'}
            or 'readiness' in report or Path(text_field(report, 'state_dir')).resolve() != Path(text_field(frozen, 'state_dir')).resolve()
            or Path(text_field(report, 'agent_source_root')).resolve() != Path(text_field(frozen, 'source_root')).resolve()):
        raise ValueError('Menu failure report does not prove the native session was never started')
    native_wire = Path(text_field(report, 'native_wire'))
    if native_wire.resolve() != (previous / 'native-report.native-wire.jsonl').resolve() or (native_wire.exists() and native_wire.stat().st_size):
        raise ValueError('Menu failure has native communication evidence')
    argv = strings_field(frozen, 'argv')
    if argv.count('--frontend-mod-load-observation') != 1 or '--frontend-fixture-start-policy' in argv or '--saved-campaign-server' in argv:
        raise ValueError('Menu failure crossed a campaign startup')
    files = object_field(frozen, 'files')
    selected_host = Path(argv[4]).resolve()
    check_pin(selected_host, object_field(files, str(selected_host)))
    identity = object_field(report, 'identity')
    for path_key, sha_key in (('game_executable', 'game_sha256'), ('dll', 'dll_sha256'), ('injector', 'injector_sha256')):
        path = Path(text_field(identity, path_key)).resolve()
        ref = object_field(files, str(path))
        if ref.get('sha256') != identity.get(sha_key):
            raise ValueError('Menu failure frozen native/game identity differs')
        check_pin(path, ref)
    readiness = original('readiness_result', previous / 'case-output/readiness-window-result.json')
    entry = original('entry_result', previous / 'case-output/entry-run-result.json')
    if (readiness.get('status') != 'READINESS_ERROR' or object_field(readiness, 'binding').get('run_id') != run_id
            or readiness.get('error') != 'ValueError: Actual shared host failed; preserve error and do not replay'
            or entry.get('run_id') != run_id or entry.get('case_error') != readiness['error']
            or entry.get('business_acceptance') != 'RED_OR_INCOMPLETE'):
        raise ValueError('Menu failure original public readiness error differs')
    keeper = original('keeper_report', keeper_root / 'report.json')
    waited = original('keeper_parent_exit', previous / 'keeper-actual-parent-exit.json')
    keeper_process = original('keeper_process', previous / 'keeper-process.json')
    if (waited.get('run_id') != run_id or type(waited.get('keeper_actual_exit_code')) is not int
            or waited['keeper_actual_exit_code'] != 0 or waited.get('keeper_report') != keeper
            or keeper.get('task_id') != frozen.get('screen_task') or keeper.get('thread_exited') is not True
            or keeper.get('failure') is not None or keeper.get('entry_error') is not None
            or not closed_lease(keeper, release, frozen['screen_task'])):
        raise ValueError('Menu failure actual keeper wait/release differs')
    tasks = bus_packet.get('tasks')
    task = object_field(json_object(release), 'task')
    if not isinstance(tasks, list) or any(not isinstance(row, dict) or 'ck3-screen:acquired' in row.get('resources', []) for row in tasks) or task.get('state') != 'done' or task.get('resources') != []:
        raise ValueError('Menu failure actual screen remains owned')
    for process in (host, supervisor, keeper_process):
        pid = process.get('pid')
        if type(pid) is not int or not isinstance(pid, int) or pid <= 0 or psutil.pid_exists(pid):
            raise ValueError('Menu failure original host/supervisor/keeper process remains')
    state = Path(text_field(frozen, 'state_dir'))
    absent = {name: not (state / 'control' / name).exists() for name in ('ck3.json', 'unsafe-cleanup.json')}
    absent['watchdog-*.ready.json'] = not list((state / 'control').glob('watchdog-*.ready.json'))
    inventory = runtime_process_inventory(psutil, os.getpid())
    if not all(absent.values()) or inventory['blockers']:
        raise ValueError('Menu failure Game/runtime/control absence not proven')
    return {'mode': 'previous-shared-menu-initialization-failure', 'actual_process_inventory': inventory,
        'failure_cleanup': {'close': pin(close_path), 'original_evidence': evidence, 'original_host_exit_code': 1,
            'original_host_wait_proven': True, 'original_ck3_exit_code': None, 'native_cleanup_qualified': None,
            'normal_close_qualified': False, 'typed_normal_exit_proven': False, 'business_pass': False,
            'release_pass': False, 'original_cleanup_ok': False, 'administrative_resource_admission_only': True}}


def previous_prelaunch_host_failure_closure(previous: Path, freeze: dict[str, object], close_path: Path,
                                            keeper_root: Path, release: dict[str, object],
                                            bus_packet: dict[str, object]) -> dict[str, object]:
    """Release a host that exited before game launch; grant no native or normal-exit credit."""
    bundle=read_json(close_path)
    if bundle.get('closure_kind') == 'menu-mcp-initialization-before-native-session':
        return previous_menu_initialization_failure(previous, freeze, bundle, close_path, keeper_root, release, bus_packet)
    require(bundle.get('schema')=='ck3-mod-acceptance-prelaunch-host-failure-closure-v1' and
            bundle.get('run_id')==freeze['run_id'] and
            Path(bundle.get('keeper_root','')).resolve()==keeper_root.resolve() and
            bundle.get('business_pass') is False and bundle.get('normal_close_qualified') is False,
            'Prelaunch host closure crossed run/keeper or claims business credit')
    evidence={}
    def original(key,path):
        ref=bundle[key]
        require(Path(ref['path']).resolve()==path.resolve() and
                type(ref.get('bytes')) is int and 0<ref['bytes']<=1048576,
                'Prelaunch original path/size differs: '+key)
        check_pin(path,ref);evidence[key]=ref
        return read_json(path) if path.suffix=='.json' else path.read_text(errors='replace')
    ready=original('ready_context',previous/'ready-context.json')
    require(ready.get('run_id')==freeze['run_id'] and
            Path(ready.get('run_dir','')).resolve()==previous.resolve() and
            Path(ready.get('keeper_root','')).resolve()==keeper_root.resolve() and
            ready.get('frozen_argv')==pin(previous/'frozen-argv.json'),
            'Prelaunch READY/frozen identity differs')
    host=original('host_started',previous/'host-started.json')
    supervisor=original('host_supervisor',previous/'host-supervisor-started.json')
    exited=original('host_exit',previous/'host-original-process-exit.json')
    stderr=original('host_stderr',previous/'host-stderr.log')
    cache_identity_rejected=(stderr.splitlines()[-1:] == [
        'ValueError: public preparation and selected runtime identities differ'] and
        'ck3_mod_acceptance_normal_exit_profile.py' in stderr and
        'in project_profile' in stderr and 'in create_profile' in stderr and
        'host_entry.py' in stderr and 'profile = helper.create_profile(' in stderr)
    registrar_prefix='ValueError: saved campaign product-only profile contains a cold-start registrar: '
    terminal=stderr.splitlines()[-1:]
    saved_registrar_rejected=(len(terminal)==1 and terminal[0].startswith(registrar_prefix) and
        len(terminal[0])>len(registrar_prefix) and 'in prepare_saved_campaign' in stderr and
        'saved_campaign = prepare_saved_campaign(args, spec)' in stderr and
        'raise ValueError("saved campaign product-only profile contains a cold-start registrar: " + str(path))' in stderr)
    readonly_tail_rejected=_saved_readonly_tail_prelaunch(stderr,bundle)
    allocated_profile_rejected=_allocated_profile_prelaunch(stderr,freeze)
    inventory_registrar=_saved_inventory_registrar_prelaunch(stderr,freeze)
    if inventory_registrar is not None:
        require(bundle.get('closure_kind')=='saved-campaign-v2-inventory-registrar-prelaunch' and
                bundle.get('machine_id')==freeze.get('identity_allocation',{}).get('machine_id') and
                all(bundle.get(key) is False for key in ('native_session_started','normal_close_qualified',
                    'typed_normal_exit_proven','business_pass','release_pass')) and
                'native_cleanup_qualified' in bundle and bundle['native_cleanup_qualified'] is None,
                'V2 registrar closure must preserve exact no-native/no-business facts')
    saved_profile_rejected=saved_registrar_rejected or readonly_tail_rejected or inventory_registrar is not None
    background_rejected=allocated_profile_rejected or inventory_registrar is not None
    supervisor_bound=supervisor.get('pid')==host.get('supervisor_pid')
    supervisor_binding=None
    if saved_profile_rejected or allocated_profile_rejected:
        intent=original('launch_intent',previous/'launch-intent.json')
        sargv=supervisor.get('argv',[])
        def supervisor_argument(name):
            require(isinstance(sargv,list) and sargv.count(name)==1 and sargv.index(name)+1<len(sargv),
                    'Saved registrar original supervisor argument missing: '+name)
            return sargv[sargv.index(name)+1]
        require(type(supervisor.get('pid')) is int and supervisor['pid']>0 and
                type(host.get('supervisor_pid')) is int and host['supervisor_pid']>0 and
                intent.get('run_id')==freeze['run_id'] and intent.get('frozen_argv')==ready['frozen_argv'] and
                isinstance(intent.get('ticket'),str) and re.fullmatch(r'[0-9a-f]{64}',intent['ticket']) is not None and
                supervisor_argument('--launch-ticket')==intent['ticket'] and sargv.count('--supervise')==1 and
                Path(supervisor_argument('--run-root')).resolve()==previous.resolve() and
                Path(supervisor_argument('--keeper-root')).resolve()==keeper_root.resolve() and
                bool(intent.get('admitted_lease')) and host.get('admitted_lease')==intent['admitted_lease'] and
                intent['admitted_lease'].get('task_id')==freeze['screen_task'],
                'Saved registrar original supervisor launch ticket/lease chain differs')
        if background_rejected:
            machine=freeze.get('identity_allocation',{}).get('machine_id')
            identity=supervisor.get('original_popen_identity',{})
            admission=object_field(json_object(intent),'background_admission')
            require(intent.get('schema')=='ck3-mod-acceptance-background-launch-intent-v1' and
                    supervisor.get('machine_id')==machine and type(host.get('pid')) is int and host['pid']>0 and
                    type(exited.get('pid')) is int and type(identity.get('pid')) is int and
                    identity['pid']==supervisor['pid'] and
                    isinstance(identity.get('birth_filetime'),str) and
                    re.fullmatch(r'[1-9][0-9]*',identity['birth_filetime']) is not None and
                    host.get('background_offline_admission')==admission and
                    intent.get('steam_offline_receipt')==admission.get('receipt') and
                    Path(supervisor_argument('--steam-offline-receipt')).resolve()==Path(admission['receipt']['path']).resolve() and
                    intent['admitted_lease'].get('schema')=='xar.promo.screen-lease-cas/v1' and
                    intent['admitted_lease'].get('screen_resource')=='ck3-screen:acquired' and
                    type(intent['admitted_lease'].get('sequence')) is int,
                    'Allocated profile original background ticket/lease chain differs')
            _prelaunch_background_admission(admission,machine)
            evidence['steam_offline_receipt']=admission['receipt']
        else:
            require(all(host.get('direct_review',{}).get(key)==intent.get(key) for key in ('proof','challenge')),
                    'Saved registrar original supervisor review chain differs')
            for key in ('proof','challenge'):
                ref=intent[key];path=Path(supervisor_argument('--'+key)).resolve()
                require(path==Path(ref['path']).resolve(),'Saved registrar original supervisor review path differs')
                check_pin(path,ref)
        stamps=[datetime.fromisoformat(row['at_utc']) for row in (intent,supervisor,host,exited)]
        require(all(stamp.tzinfo is not None and stamp.utcoffset() is not None for stamp in stamps) and
                all(a<=b for a,b in zip(stamps,stamps[1:])),
                'Saved registrar original launcher/host timestamps differ')
        supervisor_bound=True
        supervisor_binding={'mode':('original_background_launch_ticket_lease_chain' if background_rejected else
                                    'original_launch_ticket_lease_proof_chain'),
            'launcher_popen_pid':supervisor['pid'],'actual_supervise_pid':host['supervisor_pid'],
            'parent_child_relationship_observed':False,'original_at_utc':[row['at_utc'] for row in (intent,supervisor,host,exited)]}
    require(host.get('run_id')==freeze['run_id'] and host.get('argv')==freeze['argv'] and
            host.get('actual_popen_retained') is True and
            supervisor_bound and
            exited.get('run_id')==freeze['run_id'] and exited.get('pid')==host.get('pid') and
            exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int and exited['returncode']!=0 and
            exited.get('normal_ck3_exit_inferred') is False and
            (not (cache_identity_rejected or saved_profile_rejected or allocated_profile_rejected) or exited['returncode']==1) and
            (cache_identity_rejected or saved_profile_rejected or allocated_profile_rejected or any(cause in stderr for cause in (
                'ValueError: normal exit requires the actual public prepared profile',
                'ValueError: effective host differs from reviewed projection',
                'ValueError: normal-exit private V1 does not support enabled mod GUI files'))),
            'Prelaunch original host exit/cause differs')
    readiness=original('readiness_result',previous/'case-output/readiness-window-result.json')
    entry=original('entry_run_result',previous/'case-output/entry-run-result.json')
    early=readiness.get('host_exit_before_report',{})
    timeout=(readiness.get('status')=='READINESS_TIMEOUT' and
             entry.get('case_error')=='TimeoutError: Original case readiness budget elapsed')
    failed_before_report=(readiness.get('status')=='READINESS_HOST_EXIT_BEFORE_REPORT' and
        early.get('host_started')==evidence['host_started'] and
        early.get('host_exit')==evidence['host_exit'] and
        early.get('host_stderr')==evidence['host_stderr'] and
        early.get('host_returncode')==exited['returncode'] and
        all(early.get(key) is False for key in ('native_report_observed',
            'normal_close_qualified','native_exit_zero_proven','business_pass')) and
        str(entry.get('case_error','')).startswith('ValueError: Original shared host exited before report'))
    require((timeout or failed_before_report) and
            readiness.get('binding',{}).get('run_id')==freeze['run_id'] and
            entry.get('run_id')==freeze['run_id'] and
            entry.get('launcher_exit_code')==0 and
            entry.get('business_acceptance')=='RED_OR_INCOMPLETE',
            'Original public RED/readiness result differs')
    if cache_identity_rejected:
        prepared=original('prepared_case',Path(freeze['state_dir']).parent/'prepared/prepared-case.json')
        require(ready.get('prepared_case')==evidence['prepared_case'] and
                prepared.get('case')=='workshop_cache' and
                prepared.get('startup',{}).get('mode')=='workshop_cache',
                'Cache identity rejection requires its original prepared cache case')
        profile=original('profile_preparation',Path(freeze['state_dir']).parent/'prepared/profile-preparation.json')
        require(prepared.get('preparation',{}).get('profile_preparation')==evidence['profile_preparation'] and
                profile.get('schema')=='ck3-mod-acceptance-prepared-workshop-cache-v1' and
                'game_version' not in profile and 'exe_sha256' not in profile and
                Path(profile.get('state_dir','')).resolve()==Path(freeze['state_dir']).resolve() and
                profile.get('fixture_mounted') is False and profile.get('campaign_started') is False and
                profile.get('cache_content_copied') is False,
                'Cache identity rejection requires its exact pre-identity menu preparation')
    if allocated_profile_rejected:
        prepared_path=Path(ready.get('prepared_case',{}).get('path','')).resolve()
        prepared=original('prepared_case',prepared_path)
        profile_path=previous/'normal-exit-binding/normal-exit-managed-profile.json'
        profile=original('normal_exit_managed_profile',profile_path)
        hargv=host['argv']
        require(ready.get('prepared_case')==evidence['prepared_case'] and
                prepared.get('startup',{}).get('mode')=='fixture' and
                Path(prepared.get('startup',{}).get('state_dir','')).resolve()==Path(freeze['state_dir']).resolve() and
                ready.get('normal_exit_managed_profile')==evidence['normal_exit_managed_profile'] and
                hargv.count('--normal-exit-managed-profile')==1 and
                Path(hargv[hargv.index('--normal-exit-managed-profile')+1]).resolve()==profile_path.resolve() and
                hargv.count('--normal-exit-managed-profile-sha256')==1 and
                hargv[hargv.index('--normal-exit-managed-profile-sha256')+1]==evidence['normal_exit_managed_profile']['sha256'] and
                Path(profile.get('state_directory','')).resolve()==Path(freeze['state_dir']).resolve() and
                Path(profile.get('evidence_directory','')).resolve()==previous.resolve(),
                'Allocated profile rejection crossed original prepared fixture/profile')
    if saved_profile_rejected:
        prepared_path=Path(ready.get('prepared_case',{}).get('path','')).resolve()
        prepared=original('prepared_case',prepared_path)
        require(ready.get('prepared_case')==evidence['prepared_case'] and
                prepared.get('startup',{}).get('mode')=='saved_campaign' and
                Path(prepared.get('startup',{}).get('state_dir','')).resolve()==Path(freeze['state_dir']).resolve(),
                'Saved rejection crossed original prepared saved campaign/profile')
        if saved_registrar_rejected:
            registrar=Path(terminal[0][len(registrar_prefix):]).resolve()
            require(registrar.is_relative_to(Path(freeze['state_dir']).resolve()/'profile') and
                    registrar.suffix.casefold()=='.txt',
                    'Saved registrar rejection crossed original prepared saved campaign/profile')
        if inventory_registrar is not None:
            require(prepared.get('runtime_manifest')==freeze.get('runtime_manifest') and
                    prepared['startup']['saved_campaign']['product_inventory']==inventory_registrar['inventory']['path'],
                    'V2 registrar rejected inventory crossed original prepared/runtime binding')
            evidence.update({'frozen_V2_'+key:ref for key,ref in {
                'host':inventory_registrar['host'], 'source_index':inventory_registrar['source_index'],
                'verifier':inventory_registrar['verifier'], 'inventory':inventory_registrar['inventory'],
                'prepared_case':inventory_registrar['prepared_case'], 'registrar':inventory_registrar['registrar']}.items()})
    def command(key,mode,code):
        row=bundle[key];path=Path(row['path']).resolve()
        check_pin(path,row);evidence[key]=row;value=read_json(path);argv=value.get('argv',[])
        if cache_identity_rejected:
            if mode=='run':
                require(path==(previous/'public-run-original-command.json').resolve(),
                        'Cache original public run command path differs')
                ended=original('public_run_exit',previous/'public-run-original-exit.json')
                machine=freeze.get('identity_allocation',{}).get('machine_id')
                require(bool(machine) and value.get('machine_id')==machine and ended.get('machine_id')==machine and
                        ended.get('run_id')==freeze['run_id'] and ended.get('actual_original_popen_wait') is True and
                        ended.get('returncode')==code and ended.get('business_pass_inferred') is False and
                        type(ended.get('pid')) is int and ended.get('at_utc') and value.get('at_utc'),
                        'Cache original public run retained wait differs')
            else:
                require(path==(previous/'root-allocation-completion.json').resolve(),
                        'Cache original allocation completion path differs')
                started=original('public_allocate_start',previous/'root-allocation-original-command.json')
                require(started.get('argv')==argv and started.get('pid')==value.get('pid') and
                        type(value.get('pid')) is int and value.get('returncode')==code and
                        started.get('at_utc')==value.get('at_utc') and value.get('completed_at_utc'),
                        'Cache original allocation parent completion differs')
        elif inventory_registrar is not None:
            intent_path=Path(bundle[key+'_intent']['path']).resolve()
            producer_path=Path(bundle[key+'_producer']['path']).resolve()
            require(intent_path.parent==path.parent and producer_path.parent==path.parent,
                    'V2 registrar original Root intent/producer crossed execution directory')
            argv=_prelaunch_root_public_wait(value,original(key+'_intent',intent_path),
                original(key+'_producer',producer_path),path,freeze['identity_allocation']['machine_id'],
                mode,freeze['run_id'])
        elif allocated_profile_rejected:
            argv=_profile_replacement_public_completion(value,mode,freeze.get('identity_allocation',{}).get('machine_id'))
        elif readonly_tail_rejected:
            argv=_prelaunch_public_completion(value,mode,freeze.get('identity_allocation',{}).get('machine_id'))
        elif saved_registrar_rejected:
            require(path.name=='intent.json', 'Saved registrar original public intent path differs')
            started=original(key+'_process',path.parent/'original-process.json')
            ended=original(key+'_exit',path.parent/'original-exit.json')
            machine=freeze.get('identity_allocation',{}).get('machine_id')
            require(bool(machine) and all(row.get('machine_id')==machine for row in (value,started,ended)) and
                    value.get('stage')==mode and bool(value.get('at_utc')) and
                    started.get('argv')==argv and type(started.get('pid')) is int and started['pid']>0 and
                    type(started.get('create_time')) in (int,float) and started['create_time']>0 and
                    ended.get('pid')==started['pid'] and ended.get('actual_original_popen_wait') is True and
                    type(ended.get('returncode')) is int and ended['returncode']==code and
                    bool(ended.get('completed_at_utc')),
                    'Saved registrar original public '+mode+' retained wait differs')
        else:
            require(value.get('schema')=='ck3-recorded-actual-command-v1' and
                    value.get('exit_code')==code and value.get('finished_at_utc'),
                    'Prelaunch original public '+mode+' completion differs')
        require(isinstance(argv,list) and argv.count('--runtime')==1 and
                ((argv[-1:]==[mode] and argv.count(mode)==1) if saved_registrar_rejected else
                    argv[argv.index('--runtime')-1]==mode) and argv.count('--prepared-case')==1 and
                Path(argv[argv.index('--prepared-case')+1]).resolve()==
                    (prepared_path if saved_profile_rejected or allocated_profile_rejected else
                     (Path(freeze['state_dir']).parent/'prepared/prepared-case.json').resolve()),
                'Prelaunch original public '+mode+' completion differs')
        if mode=='run':
            require(argv.count('--run-context')==1 and
                    Path(argv[argv.index('--run-context')+1]).is_file(),
                    'Prelaunch reviewed run context missing')
            if saved_profile_rejected or allocated_profile_rejected:
                context_path=Path(argv[argv.index('--run-context')+1]).resolve()
                context=read_json(context_path)
                require(context.get('run_id')==freeze['run_id'] and
                        Path(context.get('run_dir','')).resolve()==previous.resolve() and
                        Path(context.get('keeper_root','')).resolve()==keeper_root.resolve() and
                        context.get('frozen_argv')==ready['frozen_argv'] and
                        context.get('prepared_case')==ready['prepared_case'],
                        'Saved registrar original public run context differs')
                evidence['public_run_context']=pin(context_path)
        else:
            require(argv.count('--keeper-output')==1 and
                    Path(argv[argv.index('--keeper-output')+1]).resolve()==keeper_root.resolve(),
                    'Prelaunch allocator keeper differs')
        return Path(argv[argv.index('--runtime')+1]).resolve()
    require(command('public_run','run',2)==command('public_allocate','allocate',0),
            'Prelaunch public run/allocate runtime differs')
    if cache_identity_rejected:
        observed=original('pre_game_red',previous/'root-pre-game-red.json')
        require(observed.get('run_id')==freeze['run_id'] and
                observed.get('machine_id')==freeze['identity_allocation']['machine_id'] and
                observed.get('host_actual_wait')==exited and
                observed.get('public_actual_wait')==read_json(Path(evidence['public_run_exit']['path'])) and
                observed.get('native_report_exists') is False and observed.get('actual_ck3_inventory')==[] and
                observed.get('game_launch_not_observed') is True and
                observed.get('normal_exit_pass') is False and observed.get('cache_load_pass') is False,
                'Cache original pre-game RED observation differs')
    keeper=original('keeper_report',keeper_root/'report.json')
    parent=original('keeper_parent_exit',previous/'keeper-actual-parent-exit.json')
    require(keeper.get('task_id')==freeze['screen_task'] and
            keeper.get('thread_exited') is True and keeper.get('failure') is None and
            keeper.get('game_actions') is False and
            parent.get('run_id')==freeze['run_id'] and
            parent.get('keeper_actual_exit_code')==0 and parent.get('keeper_report')==keeper and
            (inventory_registrar is None or type(parent.get('keeper_actual_exit_code')) is int) and
            closed_lease(keeper,release,freeze['screen_task']),
            'Prelaunch keeper/original screen release differs')
    tasks=[row for row in bus_packet.get('tasks',[]) if row.get('task_id')==freeze['screen_task']]
    require(len(tasks)==1 and tasks[0].get('state') in ('done','waiting') and
            tasks[0].get('resources')==[] and
            tasks[0].get('last_sequence',-1)>=release['task']['last_sequence'],
            'Prelaunch current screen owner not released')
    state=Path(freeze['state_dir']).resolve()
    absent={'native-report.json':not (previous/'native-report.json').exists(),
            'launch.json':not (previous/'launch.json').exists(),
            'state/control':not (state/'control').exists(),
            'run/controls/*':not any((previous/'controls').iterdir())}
    require(all(absent.values()),'Prelaunch native/game/control evidence unexpectedly exists')
    import psutil
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Prelaunch CK3/keeper/controller still running')
    return {'mode':'previous-shared-prelaunch-host-failure',
        'actual_process_inventory':inventory,
        'failure_cleanup':{'close':pin(close_path),'original_evidence':evidence,
            'original_host_exit_code':exited['returncode'],'original_host_wait_proven':True,
            'native_session_started':False,'original_ck3_exit_code':None,
            'normal_close_qualified':False,'typed_normal_exit_proven':False,
            'business_pass':False,'release_pass':False,'absent_game_controls':absent,
            **({'supervisor_binding':supervisor_binding} if saved_profile_rejected or allocated_profile_rejected else {}),
            **({'frozen_V2_registrar_rejection':inventory_registrar} if inventory_registrar is not None else {}),
            **({'native_cleanup_qualified':None,'administrative_resource_admission_only':True}
               if background_rejected else {})}}


class RecorderPreReadyClosure(TypedDict):
    schema: Literal['ck3-mod-acceptance-pre-ready-closure-v1']
    failure_kind: Literal['recorder-service-initialization-rejected']
    machine_id: str
    run_id: str
    allocated_context: FilePin
    frozen_argv: FilePin
    keeper_process: FilePin
    keeper_stderr: FilePin
    keeper_stdout: FilePin
    keeper_report: FilePin
    keeper_inputs: FilePin
    keeper_parent_wait: FilePin
    allocator_started: FilePin
    allocator_result: FilePin
    allocator_producer: FilePin
    allocator_stdout: FilePin
    allocator_stderr: FilePin


class RecorderPreReadyFacts(TypedDict):
    close: FilePin
    original_evidence: dict[str, FilePin]
    absent_launch_native_and_control_evidence: dict[str, bool]
    original_allocator_exit_code: Literal[2]
    original_keeper_exit_code: Literal[1]
    original_keeper_wait_proven: Literal[True]
    original_keeper_thread_exited: Literal[False]
    original_keeper_error_kind: Literal['recorder-service-initialization-rejected']
    source_commit: str
    native_session_started: Literal[False]
    host_started: Literal[False]
    typed_normal_exit_proven: Literal[False]
    original_ck3_exit_code: None
    business_pass: Literal[False]


class RecorderPreReadyResult(TypedDict):
    mode: Literal['previous-shared-recorder-pre-ready-failure']
    actual_process_inventory: JsonObject
    failure_cleanup: RecorderPreReadyFacts


def _pre_ready_pin(value: object) -> FilePin:
    row = file_pin(value)
    path = Path(row['path'])
    if not path.is_absolute() or row['bytes'] > 1048576 or path.stat().st_size != row['bytes']:
        raise ValueError('Bounded exact pre-READY original required')
    if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
        raise ValueError('Pre-READY original content changed')
    return row


def _pre_ready_read(value: FilePin) -> dict[str, object]:
    return _late_object(json.loads(Path(_pre_ready_pin(value)['path']).read_bytes()), 'Pre-READY original')


def create_recorder_pre_ready_closure(previous: Path, keeper_root: Path, *,
        allocator_started: FilePin, allocator_result: FilePin, allocator_producer: FilePin,
        allocator_stdout: FilePin, allocator_stderr: FilePin) -> RecorderPreReadyClosure:
    """Pin actual failure inputs; acceptance remains the live shared reducer's job."""
    def original(path: Path) -> FilePin:
        return _pre_ready_pin(pin(path))
    freeze = _pre_ready_read(original(previous/'frozen-argv.json'))
    identity = _late_object(freeze.get('identity_allocation'), 'Pre-READY machine identity')
    machine, run = identity.get('machine_id'), freeze.get('run_id')
    if not isinstance(machine, str) or not machine or not isinstance(run, str) or not run:
        raise ValueError('Original pre-READY machine/run required')
    return {
        'schema':'ck3-mod-acceptance-pre-ready-closure-v1',
        'failure_kind':'recorder-service-initialization-rejected', 'machine_id':machine, 'run_id':run,
        'allocated_context':original(previous/'allocated-context.json'),
        'frozen_argv':original(previous/'frozen-argv.json'),
        'keeper_process':original(previous/'keeper-process.json'),
        'keeper_stderr':original(previous/'keeper-stderr.log'),
        'keeper_stdout':original(previous/'keeper-stdout.log'),
        'keeper_report':original(keeper_root/'report.json'),
        'keeper_inputs':original(keeper_root/'inputs.json'),
        'keeper_parent_wait':original(previous/'keeper-pre-ready-parent-exit.json'),
        'allocator_started':_pre_ready_pin(allocator_started),
        'allocator_result':_pre_ready_pin(allocator_result),
        'allocator_producer':_pre_ready_pin(allocator_producer),
        'allocator_stdout':_pre_ready_pin(allocator_stdout),
        'allocator_stderr':_pre_ready_pin(allocator_stderr)}


def _pre_ready_git_source(repo: Path, commit: str, path: Path, frozen_pin: object) -> None:
    declared = _late_object(frozen_pin, 'Pre-READY frozen source pin')
    if set(declared) != {'bytes', 'sha256'}:
        raise ValueError('Exact frozen pre-READY source fields required')
    row = file_pin({'path':str(path.resolve()), **declared})
    relative = path.resolve().relative_to(repo.resolve()).as_posix()
    result = subprocess.run(['git', '-C', str(repo), 'cat-file', 'blob', commit+':'+relative],
                            capture_output=True, check=True)
    if len(result.stdout) != row['bytes'] or hashlib.sha256(result.stdout).hexdigest() != row['sha256']:
        raise ValueError('Pre-READY original Git blob differs from frozen source')


def validate_recorder_pre_ready_closure(previous: Path, freeze_raw: object, close_path: Path,
        keeper_root: Path, release_raw: object, bus_raw: object) -> RecorderPreReadyResult:
    """The original failed keeper stays failed; only absent resources may continue."""
    previous, keeper_root = previous.resolve(), keeper_root.resolve()
    bundle = _pre_ready_read(_pre_ready_pin(pin(close_path)))
    reference_names = ('allocated_context','frozen_argv','keeper_process','keeper_stderr',
        'keeper_stdout','keeper_report','keeper_inputs','keeper_parent_wait','allocator_started',
        'allocator_result','allocator_producer','allocator_stdout','allocator_stderr')
    if set(bundle) != {'schema','failure_kind','machine_id','run_id',*reference_names} or \
            bundle.get('schema') != 'ck3-mod-acceptance-pre-ready-closure-v1' or \
            bundle.get('failure_kind') != 'recorder-service-initialization-rejected':
        raise ValueError('Exact recorder pre-READY closure fields required')
    refs = {name:_pre_ready_pin(bundle[name]) for name in reference_names}
    fixed = {'allocated_context':previous/'allocated-context.json', 'frozen_argv':previous/'frozen-argv.json',
        'keeper_process':previous/'keeper-process.json', 'keeper_stderr':previous/'keeper-stderr.log',
        'keeper_stdout':previous/'keeper-stdout.log', 'keeper_report':keeper_root/'report.json',
        'keeper_inputs':keeper_root/'inputs.json', 'keeper_parent_wait':previous/'keeper-pre-ready-parent-exit.json'}
    for name, path in fixed.items():
        if Path(refs[name]['path']).resolve() != path.resolve():
            raise ValueError('Recorder pre-READY reference crossed path: '+name)
    freeze = _late_object(freeze_raw, 'Pre-READY frozen input')
    if freeze != _pre_ready_read(refs['frozen_argv']):
        raise ValueError('Original frozen pre-READY input differs')
    identity = _late_object(freeze.get('identity_allocation'), 'Pre-READY original machine')
    machine, run, task = identity.get('machine_id'), freeze.get('run_id'), freeze.get('screen_task')
    state_text = freeze.get('state_dir')
    if not isinstance(state_text,str) or not Path(state_text).is_absolute():
        raise ValueError('Original pre-READY state path required')
    if (not isinstance(machine,str) or not machine or not isinstance(run,str) or not run or
            not isinstance(task,str) or not task or bundle['machine_id'] != machine or bundle['run_id'] != run):
        raise ValueError('Recorder pre-READY original machine/run/task differs')
    context = _pre_ready_read(refs['allocated_context'])
    if (context.get('run_id') != run or Path(str(context.get('run_dir',''))).resolve() != previous.resolve() or
            Path(str(context.get('keeper_root',''))).resolve() != keeper_root.resolve()):
        raise ValueError('Recorder pre-READY allocated context crossed run/keeper')
    producer = validate_recorded_public_producer(Path(refs['allocator_producer']['path']).read_bytes(),machine)
    operation = validate_recorded_public_wait(_pre_ready_read(refs['allocator_result']),
        _pre_ready_read(refs['allocator_started']),producer,machine,'allocate',2)
    def argument(argv: list[str], name: str) -> str:
        if argv.count(name) != 1 or argv.index(name)+1 >= len(argv):
            raise ValueError('Recorder pre-READY argument missing: '+name)
        return argv[argv.index(name)+1]
    argv = operation['argv']
    prepared = file_pin(context.get('prepared_case'))
    _pre_ready_pin(prepared)
    if (Path(argument(argv,'--keeper-output')).resolve() != keeper_root.resolve() or
            Path(argument(argv,'--prepared-case')).resolve() != Path(prepared['path']).resolve()):
        raise ValueError('Recorder pre-READY original allocation crossed prepared/keeper')
    blocked = _pre_ready_read(refs['allocator_stdout'])
    if (blocked.get('status') != 'BLOCKED' or
            blocked.get('error') != 'Original keeper failed before READY; preserve actual stderr'):
        raise ValueError('Exact original pre-READY allocator stdout required')
    process = _pre_ready_read(refs['keeper_process'])
    if set(process) != {'pid','create_time','argv'}:
        raise ValueError('Exact original keeper process fields required')
    pid = _late_integer(process.get('pid'),'Original pre-READY keeper PID')
    created = process.get('create_time')
    if (pid <= 0 or type(created) not in (int,float) or
            not isinstance(created,(int,float)) or isinstance(created,bool) or not math.isfinite(created) or created <= 0):
        raise ValueError('Original pre-READY keeper generation required')
    keeper_argv_raw = process.get('argv')
    if not isinstance(keeper_argv_raw,list) or any(not isinstance(v,str) or not v for v in keeper_argv_raw):
        raise ValueError('Original pre-READY keeper argv required')
    keeper_argv = [v for v in keeper_argv_raw if isinstance(v,str)]
    parent = _pre_ready_read(refs['keeper_parent_wait'])
    if set(parent) != {'schema','run_id','pid','actual_original_popen_wait','actual_poll_exit_code',
            'keeper_actual_exit_code','ready_absent','at_utc','game_started','business_pass'}:
        raise ValueError('Exact original keeper wait fields required')
    if (parent.get('schema') != 'ck3-keeper-pre-ready-original-parent-exit-v1' or
            parent.get('run_id') != run or _late_integer(parent.get('pid'),'Pre-READY wait PID') != pid or
            parent.get('actual_original_popen_wait') is not True or
            _late_integer(parent.get('actual_poll_exit_code'),'Pre-READY keeper poll') != 1 or
            _late_integer(parent.get('keeper_actual_exit_code'),'Pre-READY keeper wait') != 1 or
            parent.get('ready_absent') is not True or parent.get('game_started') is not False or
            parent.get('business_pass') is not False):
        raise ValueError('Actual recorder pre-READY original wait1 required')
    report = _pre_ready_read(refs['keeper_report'])
    inputs = _pre_ready_read(refs['keeper_inputs'])
    if (set(report) != {'schema','task_id','last_sequence','failure','thread_exited','journal','at_utc',
            'entry_error','checkout_head','screen_released','game_actions'} or
            report.get('schema') != 'xar.promo.screen-lease-keeper/v1' or
            inputs.get('schema') != 'ck3-mod-acceptance-keeper-inputs-v1'):
        raise ValueError('Exact original keeper initialization report required')
    error = "ValueError('Segmented recorder requires the existing scene and raw ceilings')"
    sequence = _late_integer(inputs.get('initial_sequence'),'Pre-READY original sequence')
    if (sequence <= 0 or report.get('task_id') != task or
            _late_integer(report.get('last_sequence'),'Pre-READY report sequence') != sequence or
            report.get('failure') is not None or report.get('thread_exited') is not False or
            report.get('entry_error') != error or report.get('screen_released') is not False or
            report.get('game_actions') is not False or 'recording' in report or
            report.get('journal') != str(keeper_root/'journal.jsonl') or
            inputs.get('task_id') != task or inputs.get('screen_acquired_by_this_tool') is not False or
            Path(argument(keeper_argv,'--root')).resolve() != keeper_root.resolve() or
            argument(keeper_argv,'--task') != task or argument(keeper_argv,'--sequence') != str(sequence)):
        raise ValueError('Exact original recorder initialization rejection/report required')
    if _pre_ready_read(refs['keeper_stdout']) != report or Path(refs['keeper_stderr']['path']).read_bytes() != b'':
        raise ValueError('Original recorder keeper stdout/report/stderr differs')
    repo_text = freeze.get('source_root')
    if not isinstance(repo_text,str) or not Path(repo_text).is_absolute():
        raise ValueError('Original pre-READY source root required')
    repo = Path(repo_text)
    manifest_ref = _pre_ready_pin(freeze.get('runtime_manifest'))
    manifest = _pre_ready_read(manifest_ref)
    commit = manifest.get('source_commit')
    if (not isinstance(commit,str) or re.fullmatch('[0-9a-f]{40}',commit) is None or
            manifest.get('machine_id') != machine or inputs.get('checkout_head') != commit or
            report.get('checkout_head') != commit or Path(str(inputs.get('repo',''))).resolve() != repo.resolve()):
        raise ValueError('Original pre-READY canonical source commit differs')
    frozen_files = _late_object(freeze.get('files'),'Pre-READY frozen files')
    keeper_path = repo/'tools/ck3_mod_acceptance_keeper.py'
    service_path = repo/'tools/ck3_mod_acceptance_recorder.py'
    if keeper_argv.count(str(keeper_path)) != 1 or Path(argument(keeper_argv,'--repo')).resolve() != repo.resolve():
        raise ValueError('Original canonical keeper path differs')
    _pre_ready_git_source(repo,commit,keeper_path,frozen_files.get(str(keeper_path.resolve())))
    service_frozen = frozen_files.get(str(service_path.resolve()))
    _pre_ready_git_source(repo,commit,service_path,service_frozen)
    service_row = _late_object(service_frozen,'Original recorder source')
    if argument(keeper_argv,'--recorder-service-sha256') != service_row['sha256']:
        raise ValueError('Original recorder service argv/frozen pin differs')
    config_path = Path(argument(keeper_argv,'--recorder-config')).resolve()
    config_frozen = _late_object(frozen_files.get(str(config_path)),'Original recorder configuration')
    config_ref = _pre_ready_pin({'path':str(config_path), **config_frozen})
    if argument(keeper_argv,'--recorder-config-sha256') != config_ref['sha256']:
        raise ValueError('Original recorder configuration argv/frozen pin differs')
    config = _pre_ready_read(config_ref)
    if config.get('schema') != 'ck3-mod-acceptance-recording-config-v2' or config.get('machine_id') != machine:
        raise ValueError('Original segmented recorder machine/schema differs')
    reservation_ref = _pre_ready_pin(config.get('storage_reservation'))
    reservation = _pre_ready_read(reservation_ref)
    scene = reservation.get('this_write_peak_bytes')
    if (type(scene) is not int or not isinstance(scene,int) or scene <= 2147483648 or
            reservation.get('machine_id') != machine):
        raise ValueError('Original recorder parent ceiling rejection is unproven')
    raw_peak, total_raw = reservation.get('raw_subcap_bytes'), config.get('total_raw_bytes')
    approved = reservation.get('approved_root')
    capture_value = config.get('capture_root')
    if (type(raw_peak) is not int or not isinstance(raw_peak,int) or not 0 < raw_peak <= 536870912 or
            type(total_raw) is not int or not isinstance(total_raw,int) or not 0 < total_raw <= raw_peak or
            not isinstance(approved,str) or not Path(approved).is_absolute() or
            not isinstance(capture_value,str) or not Path(capture_value).is_absolute() or
            not Path(capture_value).resolve().is_relative_to(Path(approved).resolve()) or
            Path(capture_value).resolve() == Path(approved).resolve()):
        raise ValueError('Original recorder raw ceiling/capture scope differs')
    registration_path = previous/'screen-registration.json'
    registration_ref = _pre_ready_pin(pin(registration_path))
    registration = _pre_ready_read(registration_ref)
    registered = _late_object(registration.get('task'),'Original registration task')
    if (registration.get('ok') is not True or registered.get('task_id') != task or
            _late_integer(registered.get('last_sequence'),'Registration sequence') != sequence):
        raise ValueError('Original pre-READY screen registration differs')
    absent = {name:not (previous/name).exists() for name in ('ready-context.json','launch-intent.json',
        'launch.json','host-started.json','host-supervisor.json','supervisor.json','host-original-process-exit.json',
        'native-report.json','native-cleanup-projection.actual.json','keeper-actual-parent-exit.json')}
    absent.update(keeper_ready=not (keeper_root/'ready.json').exists(),
        keeper_journal=not (keeper_root/'journal.jsonl').exists(),
        keeper_renewals=not (keeper_root/'renewal-audit').exists(),
        state_control=not (Path(state_text)/'control').exists(),
        empty_controls=(previous/'controls').is_dir() and not any((previous/'controls').iterdir()))
    capture = config.get('capture_root')
    if not isinstance(capture,str) or not Path(capture).is_absolute():
        raise ValueError('Original capture root required')
    absent['raw_capture_files'] = not Path(capture).exists() or not any(Path(capture).iterdir())
    absent['native_wire_evidence'] = not any(previous.glob('native-report.*'))
    if not all(absent.values()):
        raise ValueError('Recorder pre-READY has READY/lease-thread/host/game/control/recording evidence')
    release = _late_object(release_raw,'Actual pre-READY resource release')
    released = _late_object(release.get('task'),'Released pre-READY task')
    bus = _late_object(bus_raw,'Current pre-READY bus')
    tasks_raw = bus.get('tasks')
    if not isinstance(tasks_raw,list):
        raise ValueError('Fresh pre-READY bus task list required')
    tasks = [_late_object(v,'Fresh pre-READY task') for v in tasks_raw]
    matching = [v for v in tasks if v.get('task_id') == task]
    if (release.get('ok') is not True or released.get('task_id') != task or
            released.get('state') not in ('done','waiting') or released.get('resources') != [] or
            _late_integer(released.get('last_sequence'),'Released pre-READY sequence') <= sequence or
            len(matching) != 1 or matching[0].get('state') not in ('done','waiting') or
            matching[0].get('resources') != [] or
            _late_integer(matching[0].get('last_sequence'),'Fresh pre-READY release sequence') <
            _late_integer(released['last_sequence'],'Original release sequence')):
        raise ValueError('Actual pre-READY CAS release/current no-owner unproven')
    import psutil
    try:
        current = psutil.Process(pid)
        if current.create_time() == created:
            raise ValueError('Original pre-READY keeper generation still present')
    except psutil.NoSuchProcess:
        pass
    inventory = json_object(runtime_process_inventory(psutil,os.getpid()))
    if inventory.get('blockers') != []:
        raise ValueError('Pre-READY CK3/keeper/controller still present')
    refs.update(runtime_manifest=manifest_ref, recorder_config=config_ref, recording_admission=reservation_ref,
                registration=registration_ref)
    return {'mode':'previous-shared-recorder-pre-ready-failure','actual_process_inventory':inventory,
        'failure_cleanup':{'close':_pre_ready_pin(pin(close_path)),'original_evidence':refs,
            'absent_launch_native_and_control_evidence':absent,'original_allocator_exit_code':2,
            'original_keeper_exit_code':1,'original_keeper_wait_proven':True,'original_keeper_thread_exited':False,
            'original_keeper_error_kind':'recorder-service-initialization-rejected','source_commit':commit,
            'native_session_started':False,'host_started':False,'typed_normal_exit_proven':False,
            'original_ck3_exit_code':None,'business_pass':False}}

def revalidate_recorder_pre_ready_admission(selection: Selection, args: argparse.Namespace,
        closure: JsonObject) -> JsonObject:
    """Refresh process and bus observations inside the original machine writer lock."""
    runtime = _late_object(selection.runtime,'Selected runtime')
    configured = _late_object(runtime.get('allocation'),'Selected allocation')
    base = selection.runtime_path.parent
    bus_ref = _late_object(configured.get('task_bus'),'Selected task bus')
    lease_value, bus_value = configured.get('lease_repo'), bus_ref.get('path')
    digest = bus_ref.get('sha256')
    if not isinstance(lease_value,str) or not isinstance(bus_value,str) or not isinstance(digest,str):
        raise ValueError('Original admission task-bus binding required')
    lease_repo, bus = path_at(lease_value,base), path_at(bus_value,base)
    previous, keeper, close, release_path = (getattr(args,name,None) for name in
        ('previous_live','previous_keeper','previous_failure_close','previous_release'))
    if not all(isinstance(v,Path) for v in (previous,keeper,close,release_path)):
        raise ValueError('Actual pre-READY predecessor paths required')
    if not isinstance(previous,Path) or not isinstance(keeper,Path) or not isinstance(close,Path) or not isinstance(release_path,Path):
        raise ValueError('Actual pre-READY predecessor paths required')
    packet = current_screen_absent(lease_repo,bus.parents[1],digest,
        selection.state_dir.parent/'allocation-bus-writer-revalidation')
    renewed = validate_recorder_pre_ready_closure(previous,read_json(previous/'frozen-argv.json'),
        close,keeper,read_failed_runtime_release(release_path),packet)
    if renewed['mode'] != closure.get('mode'):
        raise ValueError('Recorder pre-READY closure changed under original writer lock')
    result = dict(closure)
    result.update(json_object(renewed))
    return result


@runtime_checkable
class _TTLAdmissionEvidence(Protocol):
    def current_screen_absent(self, lease_repo: Path, bus_dir: Path, bus_sha: str, audit_dir: Path) -> object: ...
    def read_failed_runtime_release(self, path: Path) -> object: ...


@runtime_checkable
class _TTLAdmissionReducer(Protocol):
    def __call__(self, previous: Path, freeze_value: object, close_path: Path,
            keeper_root: Path, release_value: object, bus_value: object, next_state: Path) -> JsonObject: ...


def revalidate_pre_intent_offline_ttl_admission(selection: Selection, args: argparse.Namespace,
        closure: JsonObject) -> JsonObject:
    """Run the TTL recovery reducer again under the original machine writer lock."""
    runtime = json_object(selection.runtime)
    configured = object_field(runtime, 'allocation')
    bus_ref = object_field(configured, 'task_bus')
    base = selection.runtime_path.parent
    lease_repo = path_at(text_field(configured, 'lease_repo'), base)
    bus = path_at(text_field(bus_ref, 'path'), base)
    digest = text_field(bus_ref, 'sha256')
    previous, keeper, close, release_path = (getattr(args, name, None) for name in
        ('previous_live', 'previous_keeper', 'previous_failure_close', 'previous_release'))
    if not isinstance(previous, Path) or not isinstance(keeper, Path) or not isinstance(close, Path) or not isinstance(release_path, Path):
        raise ValueError('Actual TTL-refusal predecessor paths required')
    original_close = object_field(closure, 'failure_cleanup').get('close')
    if json_object(pin(close)) != original_close:
        raise ValueError('TTL recovery closure changed before original writer lock')
    provider: object = same_directory_control_peer('ck3_mod_acceptance_allocate')
    if not isinstance(provider, _TTLAdmissionEvidence):
        raise ValueError('Existing TTL recovery evidence provider unavailable')
    packet = json_object(provider.current_screen_absent(lease_repo, bus.parents[1], digest,
        selection.state_dir.parent / 'allocation-bus-writer-revalidation'))
    unrun = same_directory_control_peer('ck3_mod_acceptance_unrun')
    reducer: object = unrun.validate_pre_intent_offline_ttl_refusal
    if not isinstance(reducer, _TTLAdmissionReducer):
        raise ValueError('Existing TTL recovery reducer unavailable')
    renewed = reducer(previous,
        read_json(previous / 'frozen-argv.json'), close, keeper,
        provider.read_failed_runtime_release(release_path), packet, selection.state_dir)
    if (renewed.get('mode') != closure.get('mode')
            or object_field(renewed, 'failure_cleanup').get('close') != original_close):
        raise ValueError('TTL recovery closure changed under original writer lock')
    return {**closure, **renewed}


def previous_pre_ready_closure(previous,freeze,close_path,keeper_root,release,bus_packet):
    """Keep historical unknown waits; retain the observed argparse original wait2."""
    bundle=read_json(close_path)
    if 'failure_kind' in bundle:
        return validate_recorder_pre_ready_closure(previous,freeze,close_path,keeper_root,release,bus_packet)
    require(bundle.get('schema')=='ck3-mod-acceptance-pre-ready-closure-v1' and
            bundle.get('run_id')==freeze['run_id'],'Exact pre-READY predecessor bundle required')
    evidence={}
    for key,path in {'allocated_context':previous/'allocated-context.json',
        'frozen_argv':previous/'frozen-argv.json','keeper_process':previous/'keeper-process.json',
        'keeper_stderr':previous/'keeper-stderr.log'}.items():
        row=bundle[key]
        require(Path(row['path']).resolve()==path.resolve(),'Pre-READY evidence crossed path: '+key)
        check_pin(path,row);evidence[key]=pin(path)
    context=read_json(previous/'allocated-context.json')
    require(context.get('run_id')==freeze['run_id'] and
            Path(context.get('run_dir','')).resolve()==previous.resolve() and
            Path(context.get('keeper_root','')).resolve()==keeper_root.resolve(),
            'Pre-READY allocated context crossed run/keeper')
    row=bundle['allocator_result'];command_path=Path(row['path']);check_pin(command_path,row)
    command=read_json(command_path);recorded_command=command
    retained_allocator=command.get('schema')=='xar-root-exact-public-command-exit-v1'
    if retained_allocator:
        operation=command.get('operation',{});operation_path=Path(operation.get('path',''))
        check_pin(operation_path,operation);recorded_command=read_json(operation_path)
        require(command.get('actor')=='/root' and recorded_command.get('actor')=='/root' and
                recorded_command.get('schema')=='xar-root-exact-public-command-v1',
                'Pre-READY actual allocator wait/operation differs')
        evidence['allocator_operation']=pin(operation_path)
    argv=recorded_command.get('argv',[])
    def argument(values,name):
        require(isinstance(values,list) and values.count(name)==1 and values.index(name)+1<len(values),
                'Pre-READY original argument missing: '+name)
        return values[values.index(name)+1]
    code=command.get('returncode') if retained_allocator else command.get('exit_code')
    finished=command.get('finished_utc') if retained_allocator else command.get('finished_at_utc')
    require((retained_allocator or command.get('schema')=='ck3-recorded-actual-command-v1') and
            type(code) is int and code==2 and finished and 'allocate' in argv and
            Path(argument(argv,'--keeper-output')).resolve()==keeper_root.resolve() and
            Path(argument(argv,'--prepared-case')).resolve()==Path(context['prepared_case']['path']).resolve(),
            'Original pre-READY allocator terminal2 crossed keeper/case')
    stdout=bundle['allocator_stdout']
    require(Path(stdout['path']).resolve()==Path(command['stdout']['path']).resolve() and
            stdout['bytes']==command['stdout']['bytes'] and stdout['sha256']==command['stdout']['sha256'],
            'Pre-READY original allocator stdout differs')
    check_pin(Path(stdout['path']),stdout);blocked=read_json(Path(stdout['path']))
    require(blocked.get('status')=='BLOCKED' and
            blocked.get('error')=='Original keeper failed before READY; preserve actual stderr',
            'Exact pre-READY allocator failure required')
    process=read_json(previous/'keeper-process.json');keeper_argv=process.get('argv',[])
    require(type(process.get('pid')) is int and process['pid']>0 and
            type(process.get('create_time')) in (int,float) and
            Path(argument(keeper_argv,'--root')).resolve()==keeper_root.resolve() and
            argument(keeper_argv,'--task')==freeze['screen_task'],
            'Pre-READY original keeper process identity crossed task/root')
    stderr=(previous/'keeper-stderr.log').read_text(encoding='utf-8')
    missing_bus='RuntimeError: bus source or installed CLI is missing' in stderr
    parent_path=previous/'keeper-pre-ready-parent-exit.json'
    parent=None
    if not missing_bus:
        # Only the actual pinned four-argument legacy keeper's rejected bus tail.
        keeper_paths=[Path(value).resolve() for value in keeper_argv
                      if Path(value).name=='screen_keeper.py']
        require(len(keeper_paths)==1,'Exact pre-READY legacy keeper source required')
        keeper_path=keeper_paths[0];keeper_ref=freeze.get('files',{}).get(str(keeper_path),{})
        require(keeper_ref.get('bytes')==1600 and keeper_ref.get('sha256')==LEGACY_KEEPER_SHA,
                'Pre-READY legacy keeper frozen source differs')
        check_pin(keeper_path,keeper_ref)
        extras=['--bus-dir',argument(keeper_argv,'--bus-dir'),
                '--bus-cli',argument(keeper_argv,'--bus-cli'),
                '--bus-cli-sha256',argument(keeper_argv,'--bus-cli-sha256')]
        require(keeper_argv[keeper_argv.index('--sequence')+2:]==extras and stderr.splitlines() and
                stderr.splitlines()[-1]=='screen_keeper.py: error: unrecognized arguments: '+' '.join(extras),
                'Exact pre-READY unsupported legacy bus arguments required')
        parent_ref=bundle.get('keeper_parent_wait',{})
        require(Path(parent_ref.get('path','')).resolve()==parent_path.resolve(),
                'Pre-READY original keeper wait path differs')
        check_pin(parent_path,parent_ref);parent=read_json(parent_path)
        require(parent.get('schema')=='ck3-keeper-pre-ready-original-parent-exit-v1' and
                parent.get('run_id')==freeze['run_id'] and parent.get('pid')==process['pid'] and
                parent.get('actual_original_popen_wait') is True and
                type(parent.get('actual_poll_exit_code')) is int and parent['actual_poll_exit_code']==2 and
                type(parent.get('keeper_actual_exit_code')) is int and parent['keeper_actual_exit_code']==2 and
                parent.get('ready_absent') is True and parent.get('game_started') is False and
                parent.get('business_pass') is False,
                'Pre-READY exact original keeper argparse wait2 required')
        evidence['keeper_parent_wait']=pin(parent_path)
    require(not retained_allocator or parent is not None,
            'Actual allocator wait variant requires the observed legacy argparse wait2')
    registered=read_json(previous/'screen-registration.json')
    sequence=registered.get('task',{}).get('last_sequence')
    require(registered.get('ok') is True and registered.get('task',{}).get('task_id')==freeze['screen_task'] and
            type(sequence) is int and int(argument(keeper_argv,'--sequence'))==sequence,
            'Pre-READY original registration/keeper sequence differs')
    names=('ready-context.json','launch-intent.json','launch.json','host-started.json','host-supervisor.json',
           'supervisor.json','host-original-process-exit.json','native-report.json',
            'native-cleanup-projection.actual.json','keeper-actual-parent-exit.json')
    absent={name:not (previous/name).exists() for name in names}
    if parent is None:absent['keeper-pre-ready-parent-exit.json']=not parent_path.exists()
    absent['keeper_root']=not keeper_root.exists()
    absent['state/control']=not (Path(freeze['state_dir'])/'control').exists()
    absent['run/controls/*']=(previous/'controls').is_dir() and not any((previous/'controls').iterdir())
    require(all(absent.values()),'Pre-READY predecessor has READY/launch/native/control/keeper evidence')
    snapshot=release.get('task',{});tasks=bus_packet.get('tasks',[])
    matching=[task for task in tasks if task.get('task_id')==freeze['screen_task']]
    require(release.get('ok') is True and snapshot.get('task_id')==freeze['screen_task'] and
            snapshot.get('state') in ('done','waiting') and snapshot.get('resources')==[] and
            type(snapshot.get('last_sequence')) is int and snapshot['last_sequence']>sequence and
            len(matching)==1 and matching[0].get('state') in ('done','waiting') and
            matching[0].get('resources')==[] and matching[0].get('last_sequence')>=snapshot['last_sequence'],
            'Pre-READY actual CAS release/current no-owner unproven')
    import psutil
    require(not psutil.pid_exists(process['pid']),'Pre-READY original keeper PID still present')
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Pre-READY CK3/keeper/controller still present')
    evidence.update(allocator=pin(command_path),allocator_stdout=pin(Path(stdout['path'])),
                    registration=pin(previous/'screen-registration.json'))
    return {'mode':'previous-shared-pre-ready-keeper-failure','actual_process_inventory':inventory,
        'failure_cleanup':{'close':pin(close_path),'original_evidence':evidence,
            'absent_launch_native_and_control_evidence':absent,'original_keeper_exit_code':2 if parent else None,
            'original_keeper_wait_proven':parent is not None,
            'original_keeper_error_kind':'legacy-keeper-unsupported-bus-arguments' if parent else 'installed-bus-missing',
            'native_session_started':False,'host_started':False,
            'typed_normal_exit_proven':False,'original_ck3_exit_code':None,'business_pass':False}}

def closed_lease(keeper,release,task):
    snapshot=release.get('task',{})
    return (keeper.get('task_id')==task and keeper.get('thread_exited') is True and
        release.get('ok') is True and snapshot.get('task_id')==task and
        snapshot.get('state') in ('done','waiting') and snapshot.get('resources')==[] and
        type(snapshot.get('last_sequence')) is int and type(keeper.get('last_sequence')) is int and
        snapshot['last_sequence']>keeper['last_sequence'])

def read_actual_release(path):
    value=read_json(path)
    if 'stdout' in value:
        require(value.get('exit_code',value.get('returncode'))==0 and isinstance(value['stdout'],str),
                'Actual tool-wrapper release did not succeed')
        value=json.loads(value['stdout'])
    require(value.get('ok') is True and value.get('schema')=='codex.task_bus.v1','Actual bus release is missing')
    return value

def read_failed_runtime_release(path):
    """Read an original release, or its exact canonical event/task reconstruction."""
    value=read_json(path)
    if value.get('schema')!='xar-screen-release-canonical-reconstruction-v1':
        return read_actual_release(path)
    raw=value.get('source_event_raw_utf8','').encode('utf-8')
    offset=value.get('source_event_byte_offset');size=value.get('source_event_bytes')
    require(type(offset) is int and offset>=0 and type(size) is int and size==len(raw) and
            hashlib.sha256(raw).hexdigest()==value.get('source_event_raw_sha256'),
            'Failed-runtime release canonical event identity differs')
    with Path(value['source_event_stream']).open('rb') as stream:
        stream.seek(offset);actual=stream.read(size)
    require(actual==raw and json.loads(raw)==value.get('event'),
            'Failed-runtime release is absent from the actual canonical event stream')
    task_pin=value['actual_task_pin'];check_pin(Path(task_pin['path']),task_pin)
    require(read_json(Path(task_pin['path']))==value.get('task') and
            value.get('release_confirmed_by_canonical_readback') is True,
            'Failed-runtime release current task readback differs')
    return {'schema':'codex.task_bus.v1','ok':True,'task':value['task'],'event':value['event'],
            'canonical_reconstruction':pin(path),'original_stdout_captured':False}

def previous_runtime_failure_closure(previous,freeze,report,close_path,keeper_root,release_path,bus_packet):
    """Administrative recovery for the observed report-writer crash, not OS0/PASS."""
    bundle=read_json(close_path);evidence={};correction=None
    if bundle.get('schema')=='xar-failed-report-writer-retained-exit-correction-v1':
        correction=bundle;row=correction['original_resource_close_pin']
        check_pin(Path(row['path']),row);evidence['original_resource_close']=pin(Path(row['path']))
        bundle=read_json(Path(row['path']))
        require(correction.get('run_id')==freeze['run_id'] and correction.get('host_exit_code') is None and
                correction.get('host_wait_proven') is False and correction.get('normal_close_qualified') is False and
                correction.get('business_pass') is False and correction.get('release_pass') is False,
                'Failed-runtime correction crossed identity or claims unavailable exit/PASS credit')
    require(bundle.get('schema')=='xar-failed-report-writer-attempt-resource-closed-v1' and
            bundle.get('status')=='FAILED_ATTEMPT_RESOURCE_CLOSED' and
            bundle.get('run_id')==freeze['run_id'] and bundle.get('case')==freeze['cell'] and
            Path(bundle.get('next_previous_live','')).resolve()==previous.resolve(),
            'Explicit failed-runtime closure crossed run/case/live')
    require(bundle.get('normal_close_qualified') is False and bundle.get('business_pass') is False and
            bundle.get('release_pass') is False and bundle.get('original_evidence_not_rewritten') is True and
            bundle.get('native_report_unfinished') is True and not report.get('finished_at'),
            'Failed-runtime closure must preserve unfinished failure without normal/PASS credit')
    state=Path(freeze['state_dir']).resolve()
    require(Path(report.get('state_dir','')).resolve()==state and
            Path(report.get('agent_source_root','')).resolve()==Path(freeze['source_root']).resolve(),
            'Failed-runtime report state/source differs from frozen argv')

    def original(key,expected=None):
        row=bundle[key];path=Path(row['path']).resolve()
        require(expected is None or path==Path(expected).resolve(),'Failed-runtime original path differs: '+key)
        check_pin(path,row);evidence[key]=pin(path)
        return path

    original('native_report',previous/'native-report.json')
    stderr=original('harness_stderr',previous/'harness-stderr.log').read_text(encoding='utf-8-sig')
    require('PermissionError: [WinError 5]' in stderr and 'replace-report-from-partial' in stderr,
            'Failed-runtime original report-writer error is missing')
    launch=read_json(original('original_launch_pin',previous/'launch.json'))
    require(launch.get('argv')==freeze['argv'] and type(launch.get('harness_pid')) is int and
            launch['harness_pid']>0 and type(launch.get('create_time')) in (int,float),
            'Failed-runtime original host PID/time/argv binding differs')
    prepared=read_json(original('prepared_case'));runtime=read_json(original('runtime'))
    require(prepared.get('runtime_manifest')==freeze['runtime_manifest'] and
            Path(prepared['startup']['state_dir']).resolve()==state and
            Path(runtime['manifest']['path']).resolve()==Path(freeze['runtime_manifest']['path']).resolve() and
            all(runtime['manifest'].get(key)==freeze['runtime_manifest'].get(key) for key in ('bytes','sha256')),
            'Failed-runtime prepared/runtime inputs crossed frozen scene')

    def waited(key,mode,code):
        value=read_json(original(key))
        require(value.get('schema')=='xar-root-exact-public-command-exit-v1' and
                type(value.get('returncode')) is int and value['returncode']==code and
                value.get('business_or_release_pass_claimed') is False,
                'Failed-runtime actual public '+mode+' wait receipt differs')
        for name in ('operation','stdout','stderr'):
            row=value[name];check_pin(Path(row['path']),row)
        operation=read_json(Path(value['operation']['path']));argv=operation['argv']
        index=next((i for i,arg in enumerate(argv) if Path(arg).name=='ck3_mod_acceptance.py'),-1)
        require(index>=0 and argv[index+1]==mode,'Failed-runtime wait belongs to another public command')
        def argument(flag):return argv[argv.index(flag)+1]
        require(Path(argument('--runtime')).resolve()==Path(bundle['runtime']['path']).resolve() and
                Path(argument('--prepared-case')).resolve()==Path(bundle['prepared_case']['path']).resolve(),
                'Failed-runtime actual public wait crossed runtime/preparation')
        if mode=='run':
            context=read_json(Path(argument('--run-context')))
            require(context.get('run_id')==freeze['run_id'] and
                    Path(context.get('run_dir','')).resolve()==previous.resolve(),
                    'Failed-runtime actual run wait crossed live identity')
        else:
            require(argument('--attempt')==bundle['attempt'] and
                    Path(argument('--keeper-output')).resolve()==keeper_root.resolve(),
                    'Failed-runtime allocator wait crossed keeper/attempt')
        return value

    waited('run_process_exit','run',2);waited('allocator_actual_exit','allocate',0)
    keeper=read_json(keeper_root/'report.json')
    keeper_exit=read_json(original('keeper_actual_exit',previous/'keeper-actual-parent-exit.json'))
    require(keeper_exit.get('run_id')==freeze['run_id'] and
            type(keeper_exit.get('keeper_actual_exit_code')) is int and keeper_exit['keeper_actual_exit_code']==0 and
            keeper_exit.get('keeper_report')==keeper,
            'Failed-runtime actual keeper parent wait differs')
    original('canonical_screen_release_pin',release_path)
    release=read_failed_runtime_release(release_path);task=release['task'];event=release.get('event',{})
    require(closed_lease(keeper,release,freeze['screen_task']) and task.get('state')=='done' and
            event.get('task_id')==freeze['screen_task'] and event.get('sequence')==task['last_sequence'] and
            event.get('state')=='done' and event.get('resources')==[],
            'Failed-runtime exact completed screen release differs')
    require(isinstance(bus_packet.get('tasks'),list) and
            not any('ck3-screen:acquired' in row.get('resources',[]) for row in bus_packet['tasks']),
            'Failed-runtime administrative admission still has a screen owner')
    identity_path=previous/'case-output/retained-current-process-identity.json'
    exit_path=previous/'case-output/actual-retained-handle-os-exit.json'
    identity=read_json(identity_path);game_exit=read_json(exit_path)
    evidence['ck3_identity']=pin(identity_path);evidence['ck3_retained_exit']=pin(exit_path)
    require(identity.get('retained_synchronize_query_handle_acquired') is True and
            game_exit.get('retained_synchronize_query_handle_acquired') is True and
            game_exit.get('pid')==identity.get('pid') and game_exit.get('create_time')==identity.get('create_time') and
            game_exit.get('signaled') is True and type(game_exit.get('exit_code')) is int and
            game_exit['exit_code']!=0 and game_exit.get('actual_retained_os0') is False,
            'Failed-runtime original retained CK3 nonzero exit proof differs')
    if correction is not None:
        for key,path in (('actual_retained_exit_pin',exit_path),('retained_identity_pin',identity_path),
                         ('frozen_argv_pin',previous/'frozen-argv.json'),('original_launch_pin',previous/'launch.json')):
            row=correction[key]
            require(Path(row['path']).resolve()==path.resolve(),'Failed-runtime correction original path differs')
            check_pin(path,row)
        require(correction.get('retained_process')==game_exit and correction.get('original_ck3_exit_code')==game_exit['exit_code'] and
                correction.get('retained_actual_OS0') is False and correction.get('host_pid')==launch['harness_pid'] and
                correction.get('host_create_time')==launch['create_time'], 'Failed-runtime corrected retained identity differs')
    import psutil
    host_identity={'pid':launch['harness_pid'],'create_time':launch['create_time']}
    keeper_identity=read_json(previous/'keeper-process.json')
    for label,identity_row in (('host',host_identity),('CK3',identity),('keeper',keeper_identity)):
        require(type(identity_row.get('pid')) is int and identity_row['pid']>0 and
                type(identity_row.get('create_time')) in (int,float), 'Failed-runtime '+label+' identity missing')
        try:present=psutil.Process(identity_row['pid']).create_time()==identity_row['create_time']
        except psutil.NoSuchProcess:present=False
        require(not present,'Failed-runtime original '+label+' identity still present')
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Failed-runtime CK3/keeper/controller still running')
    control=state/'control'
    absent={name:not (control/name).exists() for name in ('unsafe-cleanup.json','ck3.json')}
    absent['watchdog-*.ready.json']=not list(control.glob('watchdog-*.ready.json'))
    require(all(absent.values()),'Failed-runtime unsafe/PID/watchdog-ready controls remain')
    evidence['frozen_argv']=pin(previous/'frozen-argv.json')
    evidence['keeper_report']=pin(keeper_root/'report.json')
    return {'mode':'previous-shared-failed-report-writer-runtime','failure_cleanup':{
        'close':pin(close_path),'original_evidence':evidence,'host_identity':host_identity,
        'original_host_exit_code':None,'original_host_wait_proven':False,
        'original_ck3_exit_code':game_exit['exit_code'],'actual_retained_os0':False,
        'original_report_status':report.get('status'),'original_report_finished_at':report.get('finished_at'),
        'normal_close_qualified':False,'typed_normal_exit_proven':False,'business_pass':False,
        'release_pass':False,'control_files_absent':absent,'administrative_resource_admission_only':True},
        'actual_process_inventory':inventory}

def previous_expired_keeper_resource_closure(previous, freeze, bundle, close_path, keeper_root,
                                             release_path, bus_packet):
    """Retire absent failed-live resources without inventing a missing keeper exit."""
    import psutil
    machine = freeze.get('identity_allocation', {}).get('machine_id')
    require(bundle.get('machine_id') == machine and bundle.get('observed_at_utc') and
            bundle.get('closure_kind') == 'expired-keeper-missing-final-report' and
            bundle.get('keeper_final_report_missing') is True,
            'Expired-keeper closure machine/kind/observation differs')
    refs, evidence = bundle.get('original_evidence'), {}
    require(isinstance(refs, dict), 'Expired-keeper original evidence pins required')
    def original(key, expected=None):
        row = refs[key]; path = Path(row['path']).resolve()
        require((expected is None or path == Path(expected).resolve()) and
                type(row.get('bytes')) is int and 0 <= row['bytes'] <= 1048576,
                'Expired-keeper original path/bound differs: ' + key)
        check_pin(path, row); evidence[key] = row
        return read_json(path)
    original('frozen_argv', previous/'frozen-argv.json')
    ready = original('ready_context', previous/'ready-context.json')
    require(ready.get('run_id') == freeze['run_id'] and
            Path(ready.get('run_dir', '')).resolve() == previous and
            Path(ready.get('keeper_root', '')).resolve() == keeper_root and
            ready.get('frozen_argv') == refs['frozen_argv'],
            'Expired-keeper READY crossed frozen run/keeper')
    prepared = original('prepared_case', ready['prepared_case']['path'])
    require(refs['prepared_case'] == ready['prepared_case'] and
            Path(prepared['startup']['state_dir']).resolve() == Path(freeze['state_dir']).resolve() and
            prepared['runtime_manifest'] == freeze['runtime_manifest'],
            'Expired-keeper preparation crossed runtime/state')
    host = original('host_started', previous/'host-started.json')
    exited = original('host_exit', previous/'host-original-process-exit.json')
    supervisor = original('host_supervisor', previous/'host-supervisor-started.json')
    require(host.get('run_id') == exited.get('run_id') == freeze['run_id'] and
            host.get('actual_popen_retained') is True and host.get('argv') == freeze['argv'] and
            exited.get('pid') == host.get('pid') and exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int and exited.get('normal_ck3_exit_inferred') is False,
            'Expired-keeper original host wait/run differs; host code is not CK3 exit proof')
    def argument(argv, flag):
        require(isinstance(argv, list) and argv.count(flag) == 1 and argv.index(flag) + 1 < len(argv),
                'Expired-keeper original argument missing: ' + flag)
        return argv[argv.index(flag) + 1]
    require('--supervise' in supervisor.get('argv', []) and
            Path(argument(supervisor['argv'], '--run-root')).resolve() == previous and
            Path(argument(supervisor['argv'], '--keeper-root')).resolve() == keeper_root,
            'Expired-keeper original supervisor crossed run/keeper')
    keeper = original('keeper_process', previous/'keeper-process.json')
    require(Path(argument(keeper.get('argv'), '--root')).resolve() == keeper_root and
            argument(keeper['argv'], '--task') == freeze['screen_task'],
            'Expired-keeper original process crossed task/root')
    game = original('retained_identity', previous/'case-output/retained-current-process-identity.json')
    normal = original('normal_close', previous/'case-output/normal-close-result.json')
    retained = normal.get('retained_handle', {})
    require(normal.get('normal_close_qualified') is False and normal.get('business_pass') is False and
            retained.get('actual_retained_os0') is False and
            retained.get('pid') == game.get('pid') and retained.get('create_time') == game.get('create_time'),
            'Expired-keeper original close claims normal/business credit or crossed CK3 identity')
    handover = original('handover_snapshot')
    require(handover.get('machine_id') == machine and handover.get('observed_at_utc') and
            handover.get('keeper_final_report_exists') is False and
            handover.get('normal_close_qualified') is False,
            'Expired-keeper historical missing report/negative qualification is unbound')
    for key in ('host_exit', 'normal_close'):
        matches = [row for row in handover.get('leaves', [])
                   if Path(row.get('path', '')).resolve() == Path(refs[key]['path']).resolve()]
        require(len(matches) == 1 and matches[0].get('source_machine_id') == machine and
                matches[0].get('source_sha256') == refs[key]['sha256'] and
                matches[0].get('bytes') == refs[key]['bytes'],
                'Expired-keeper handover source pin differs: ' + key)
    require(not (keeper_root/'report.json').exists() and
            not (previous/'keeper-actual-parent-exit.json').exists(),
            'Expired-keeper missing-report recovery cannot replace existing keeper evidence')
    original('release', release_path)
    canonical = read_json(release_path)
    bus_dir = Path(argument(keeper['argv'], '--bus-dir')).resolve()
    require(canonical.get('schema') == 'xar-screen-release-canonical-reconstruction-v1' and
            Path(canonical.get('source_event_stream', '')).resolve() == bus_dir/'events.jsonl' and
            Path(canonical['actual_task_pin']['path']).resolve() == bus_dir/'tasks'/(freeze['screen_task']+'.json'),
            'Expired-keeper retirement must bind the original keeper canonical bus')
    release = read_failed_runtime_release(release_path)
    task, event = release['task'], release.get('event', {})
    retirement = event.get('retirement', {})
    require(task.get('task_id') == event.get('task_id') == freeze['screen_task'] and
            task.get('state') == event.get('state') == 'waiting' and
            task.get('resources') == event.get('resources') == [] and event.get('kind') == 'status' and
            type(event.get('sequence')) is int and event['sequence'] == task.get('last_sequence') and
            retirement.get('kind') == 'expired-own-claim-released' and
            retirement.get('business_status') == 'unresolved_red' and
            type(retirement.get('prior_sequence')) is int and retirement['prior_sequence'] < event['sequence'],
            'Expired-keeper exact abnormal CAS retirement differs')
    prior = bundle.get('retired_prior_event', {})
    require(type(prior.get('byte_offset')) is int and prior['byte_offset'] >= 0 and
            type(prior.get('bytes')) is int and 0 < prior['bytes'] <= 1048576,
            'Expired-keeper retired prior event offset/bound missing')
    with (bus_dir/'events.jsonl').open('rb') as stream:
        stream.seek(prior['byte_offset']); raw = stream.read(prior['bytes'])
    require(hashlib.sha256(raw).hexdigest() == prior.get('sha256'),
            'Expired-keeper retired prior canonical event bytes differ')
    old = json.loads(raw)
    require(old.get('task_id') == freeze['screen_task'] and old.get('sequence') == retirement['prior_sequence'] and
            old.get('state') == 'running' and old.get('resources') == ['ck3-screen:acquired'] and
            (datetime.fromisoformat(event['timestamp_utc']) -
             datetime.fromisoformat(old['timestamp_utc'])).total_seconds() > 600,
            'Expired-keeper retirement did not close the exact expired claim')
    tasks = bus_packet.get('tasks')
    require(isinstance(tasks, list) and not any('ck3-screen:acquired' in row.get('resources', []) for row in tasks),
            'Expired-keeper still has an actual screen owner')
    matching = [row for row in tasks if row.get('task_id') == freeze['screen_task']]
    require(len(matching) == 1 and matching[0].get('last_sequence') == event['sequence'] and
            matching[0].get('state') == 'waiting' and matching[0].get('resources') == [],
            'Expired-keeper current bus task differs from exact retired claim')
    identities = {}
    for label, identity in (('host', host), ('CK3', game), ('keeper', keeper)):
        require(type(identity.get('pid')) is int and identity['pid'] > 0 and
                type(identity.get('create_time')) in (int, float), 'Expired-keeper original identity absent: ' + label)
        try: present = psutil.Process(identity['pid']).create_time() == identity['create_time']
        except psutil.NoSuchProcess: present = False
        require(not present, 'Expired-keeper original process still present: ' + label)
        identities[label] = {'pid':identity['pid'], 'create_time':identity['create_time'], 'present':False}
    require(all(type(pid) is int and pid > 0 and not psutil.pid_exists(pid)
                for pid in (supervisor.get('pid'), host.get('supervisor_pid'))),
            'Expired-keeper original supervisor still present or identity missing')
    inventory = runtime_process_inventory(psutil, os.getpid())
    require(not inventory['blockers'], 'Expired-keeper runtime/CK3/controller still running')
    selected_host = Path(freeze['argv'][4]).resolve()
    for process in psutil.process_iter(['pid', 'name']):
        if (process.info.get('name') or '').lower().startswith(('python', 'pypy')):
            try: argv = process.cmdline()
            except psutil.NoSuchProcess: continue
            require(not any(Path(arg).resolve() == selected_host for arg in argv
                            if arg and Path(arg).name.lower() == selected_host.name.lower()),
                    'Expired-keeper frozen host interpreter or redirector still present')
    state = Path(freeze['state_dir']).resolve()
    absent = {name:not (state/'control'/name).exists() for name in ('ck3.json', 'unsafe-cleanup.json')}
    absent['watchdog-*.ready.json'] = not list((state/'control').glob('watchdog-*.ready.json'))
    require(all(absent.values()), 'Expired-keeper PID/unsafe/watchdog controls remain')
    inventory.update(machine_id=machine, original_identities=identities, source=pin(Path(__file__)))
    return {'mode':'previous-shared-failed-live-expired-keeper-resource-closed',
            'actual_process_inventory':inventory, 'failure_cleanup':{
                'close':pin(close_path), 'original_evidence':evidence, 'abnormal_resource_closure':True,
                'retired_prior_sequence':old['sequence'], 'retirement_sequence':event['sequence'],
                'original_host_exit_code':exited['returncode'], 'original_host_wait_proven':True,
                'original_keeper_wait_proven':False, 'keeper_thread_exit_proven':False,
                'keeper_final_report_missing':True, 'original_ck3_exit_code':None, 'actual_retained_os0':False,
                'native_cleanup_qualified':None, 'normal_close_qualified':False, 'typed_normal_exit_proven':False,
                'business_pass':False, 'release_pass':False, 'control_files_absent':absent,
                'administrative_resource_admission_only':True}}


def previous_missing_normal_resource_closure(previous, freeze, bundle, close_path, keeper_root,
                                             release_path, bus_packet):
    """Close a proved failed host's resources while retaining missing exit receipts."""
    import psutil
    machine = freeze.get('identity_allocation', {}).get('machine_id')
    require(bundle.get('machine_id') == machine and bundle.get('observed_at_utc') and
            bundle.get('closure_kind') == 'failed-host-without-normal-close-result',
            'Missing-normal failure closure machine/kind/time differs')
    refs, evidence = bundle.get('original_evidence'), {}
    require(isinstance(refs, dict), 'Missing-normal failure evidence pins required')
    def original(key, expected=None):
        row = refs[key]; path = Path(row['path']).resolve()
        require((expected is None or path == Path(expected).resolve()) and
                type(row.get('bytes')) is int and 0 <= row['bytes'] <= 1048576,
                'Missing-normal original path/bound differs: ' + key)
        check_pin(path, row); evidence[key] = row
        return read_json(path)
    original('frozen_argv', previous/'frozen-argv.json')
    ready = original('ready_context', previous/'ready-context.json')
    require(ready.get('run_id') == freeze['run_id'] and Path(ready.get('run_dir', '')).resolve() == previous and
            Path(ready.get('keeper_root', '')).resolve() == keeper_root and ready.get('frozen_argv') == refs['frozen_argv'],
            'Missing-normal READY crossed frozen run/keeper')
    prepared = original('prepared_case', ready['prepared_case']['path'])
    require(ready['prepared_case'] == refs['prepared_case'] and
            Path(prepared['startup']['state_dir']).resolve() == Path(freeze['state_dir']).resolve() and
            prepared['runtime_manifest'] == freeze['runtime_manifest'], 'Missing-normal preparation crossed runtime/state')
    host = original('host_started', previous/'host-started.json')
    exited = original('host_exit', previous/'host-original-process-exit.json')
    supervisor = original('host_supervisor', previous/'host-supervisor-started.json')
    require(host.get('run_id') == exited.get('run_id') == freeze['run_id'] and
            host.get('actual_popen_retained') is True and host.get('argv') == freeze['argv'] and
            exited.get('pid') == host.get('pid') and exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int and exited['returncode'] != 0 and
            exited.get('normal_ck3_exit_inferred') is False, 'Missing-normal original failed host wait differs')
    def argument(argv, flag):
        require(isinstance(argv, list) and argv.count(flag) == 1 and argv.index(flag) + 1 < len(argv),
                'Missing-normal original argument missing: ' + flag)
        return argv[argv.index(flag) + 1]
    require('--supervise' in supervisor.get('argv', []) and
            Path(argument(supervisor['argv'], '--run-root')).resolve() == previous and
            Path(argument(supervisor['argv'], '--keeper-root')).resolve() == keeper_root,
            'Missing-normal original supervisor crossed run/keeper')
    projection = original('native_cleanup_projection', previous/'native-cleanup-projection.actual.json')
    require(projection.get('machine_id') == machine and projection.get('observed_at_utc'),
            'Missing-normal native projection machine/time missing')
    report, native_ref, projection_ref = previous_native_cleanup(previous, freeze)
    require(native_ref is not None and report.get('status') == 'RED' and report.get('error') and
            report.get('managed_session_done') is True and closed_session(report) and native_cleanup_closed(report) and
            Path(report.get('state_dir', '')).resolve() == Path(freeze['state_dir']).resolve() and
            Path(report.get('agent_source_root', '')).resolve() == Path(freeze['source_root']).resolve() and
            report.get('pipe') == argument(freeze['argv'], '--bridge-pipe'),
            'Missing-normal original native failure/Job cleanup is incomplete')
    native = report['session']['report']; shutdown = native['shutdown']
    require(report['session'].get('error') is None and native.get('pid') == shutdown.get('ck3_pid') and
            type(shutdown.get('ck3_exit_code')) is int and shutdown['ck3_exit_code'] != 0,
            'Missing-normal native failed-process identity/exit differs')
    entry = original('entry_result', previous/'case-output/entry-run-result.json')
    close_error = original('normal_close_error', previous/'case-output/normal-close-error-preserved.json')
    require(entry.get('run_id') == freeze['run_id'] and entry.get('host_argv') == freeze['argv'] and
            entry.get('case_error') and entry.get('normal_close_error') == close_error.get('error') and
            isinstance(close_error.get('error'), str) and bool(close_error['error']) and
            close_error.get('business_pass') is False,
            'Missing-normal original case/close error is absent or crossed run')
    missing = {name:not (previous/'case-output'/name).exists()
               for name in ('normal-close-result.json', 'actual-retained-handle-os-exit.json')}
    require(all(missing.values()), 'Missing-normal branch cannot replace existing close/retained-exit evidence')
    game = original('retained_identity', previous/'case-output/retained-current-process-identity.json')
    require(game.get('retained_synchronize_query_handle_acquired') is True and game.get('pid') == native['pid'],
            'Missing-normal retained original CK3 identity differs')
    public = original('public_wait')
    allocator = original('allocator_wait')
    for mode, value, code in (('run', public, 2), ('allocate', allocator, 0)):
        argv = value.get('argv', [])
        command = next((i for i, arg in enumerate(argv) if Path(arg).name == 'ck3_mod_acceptance.py'), -1)
        require(value.get('machine_id') == machine and value.get('observed_at_utc') and
                value.get('actual_original_popen_wait') is True and value.get('returncode') == code and
                command >= 0 and argv[command+1] == mode and argument(argv, '--case') == freeze['cell'] and
                Path(argument(argv, '--prepared-case')).resolve() == Path(refs['prepared_case']['path']).resolve(),
                'Missing-normal actual public completion differs: ' + mode)
        if mode == 'run':
            context = original('public_run_context', argument(argv, '--run-context'))
            require(context.get('run_id') == freeze['run_id'] and Path(context.get('run_dir', '')).resolve() == previous,
                    'Missing-normal public run context differs')
        else:
            require(Path(argument(argv, '--keeper-output')).resolve() == keeper_root,
                    'Missing-normal allocator keeper differs')
    require(Path(argument(public['argv'], '--runtime')).resolve() == Path(argument(allocator['argv'], '--runtime')).resolve(),
            'Missing-normal original public runtimes differ')
    keeper = original('keeper_report', keeper_root/'report.json')
    parent = original('keeper_exit', previous/'keeper-actual-parent-exit.json')
    require(parent.get('run_id') == freeze['run_id'] and parent.get('keeper_actual_exit_code') == 0 and
            parent.get('keeper_report') == keeper and keeper.get('failure') is None and keeper.get('entry_error') is None,
            'Missing-normal original keeper wait/thread differs')
    original('release', release_path); release = read_failed_runtime_release(release_path)
    task, event = release['task'], release.get('event', {})
    require(closed_lease(keeper, release, freeze['screen_task']) and task.get('state') == 'done' and
            event.get('task_id') == freeze['screen_task'] and event.get('sequence') == task['last_sequence'] and
            event.get('state') == 'done' and event.get('resources') == [], 'Missing-normal actual CAS release differs')
    tasks = bus_packet.get('tasks'); matching = [row for row in tasks or [] if row.get('task_id') == freeze['screen_task']]
    require(isinstance(tasks, list) and not any('ck3-screen:acquired' in row.get('resources', []) for row in tasks) and
            len(matching) == 1 and matching[0].get('state') == 'done' and matching[0].get('resources') == [] and
            matching[0].get('last_sequence') == task['last_sequence'], 'Missing-normal current screen task is not closed')
    keeper_process = original('keeper_process', previous/'keeper-process.json')
    require(Path(argument(keeper_process.get('argv'), '--root')).resolve() == keeper_root and
            argument(keeper_process['argv'], '--task') == freeze['screen_task'], 'Missing-normal keeper identity crossed task/root')
    for label, identity in (('host', host), ('CK3', game), ('keeper', keeper_process)):
        require(type(identity.get('pid')) is int and identity['pid'] > 0 and
                type(identity.get('create_time')) in (int, float), 'Missing-normal original identity absent: ' + label)
        try: present = psutil.Process(identity['pid']).create_time() == identity['create_time']
        except psutil.NoSuchProcess: present = False
        require(not present, 'Missing-normal original process still present: ' + label)
    require(all(type(pid) is int and pid > 0 and not psutil.pid_exists(pid)
                for pid in (supervisor.get('pid'), host.get('supervisor_pid'), public.get('pid'), allocator.get('pid'))),
            'Missing-normal original public/supervisor process still present or identity missing')
    inventory = runtime_process_inventory(psutil, os.getpid())
    require(not inventory['blockers'], 'Missing-normal CK3/runtime/controller still running')
    owned_recorders = []
    scene_token = str(keeper_root.parent).replace('/', '\\').casefold()
    for process in psutil.process_iter(['pid', 'name']):
        name = (process.info.get('name') or '').lower()
        if name == 'ffmpeg.exe' or name.startswith(('python', 'pypy')):
            try: argv = process.cmdline()
            except psutil.NoSuchProcess: continue
            if scene_token in ' '.join(argv).replace('/', '\\').casefold() and (
                    name == 'ffmpeg.exe' or any(Path(arg).name in
                    ('window_take_actor.py', 'ck3_mod_acceptance_recorder.py') for arg in argv)):
                owned_recorders.append({'pid':process.pid, 'name':name})
    require(not owned_recorders, 'Missing-normal owned recorder still running')
    state = Path(freeze['state_dir']).resolve()
    absent = {name:not (state/'control'/name).exists() for name in ('ck3.json', 'unsafe-cleanup.json')}
    absent['watchdog-*.ready.json'] = not list((state/'control').glob('watchdog-*.ready.json'))
    require(all(absent.values()), 'Missing-normal PID/unsafe/watchdog controls remain')
    inventory.update(machine_id=machine, source=pin(Path(__file__)), owned_recorders=owned_recorders)
    return {'mode':'previous-shared-failed-host-missing-normal-resource-closed', 'actual_process_inventory':inventory,
            'failure_cleanup':{'close':pin(close_path), 'original_evidence':evidence, 'native_report':native_ref,
                'native_cleanup_projection':projection_ref, 'original_host_exit_code':exited['returncode'],
                'original_host_wait_proven':True, 'original_keeper_wait_proven':True,
                'original_ck3_exit_code':None, 'native_reported_ck3_exit_code':shutdown['ck3_exit_code'],
                'retained_os_exit_receipt':None, 'normal_close_result':None, 'missing_original_receipts':missing,
                'native_job_cleanup_observed':True, 'native_cleanup_qualified':None,
                'normal_close_qualified':False, 'typed_normal_exit_proven':False,
                'actual_retained_os0':False, 'business_pass':False, 'release_pass':False,
                'control_files_absent':absent, 'administrative_resource_admission_only':True}}


class LateNativeCleanupFacts(TypedDict):
    closure_kind: Literal['retained-wait-expired-then-native-cleanup']
    original_ck3_exit_code: None
    original_retained_wait_signaled: Literal[False]
    actual_retained_os0: Literal[False]
    native_reported_ck3_exit_code: int
    native_process_exit_code: None
    failure_lifecycle_completed: Literal[False]
    native_cleanup_qualified: None


class FailedGuiOS0CleanupFacts(TypedDict):
    closure_kind: Literal['failed-host-gui-os0-cleanup-complete']
    original_ck3_exit_code: Literal[0]
    original_retained_wait_signaled: Literal[True]
    actual_retained_os0: Literal[True]
    native_reported_ck3_exit_code: Literal[0]
    native_process_exit_code: Literal[0]
    failure_lifecycle_completed: Literal[True]
    native_cleanup_qualified: Literal[True]


class PreservedFailureOS0Facts(TypedDict):
    closure_kind: Literal['preserved-failure-native-process-exit-zero']
    original_ck3_exit_code: Literal[0]
    actual_retained_os0: Literal[True]
    native_cleanup_qualified: Literal[True]
    failure_lifecycle_completed: Literal[True]
    original_normal_close_lifecycle_completed: bool
    win32_birth_filetime: str


class PreservedTypedObserverSources(TypedDict):
    receipt_pin: FilePin
    receipt: JsonObject
    close_pin: FilePin
    close: JsonObject
    claim_pin: FilePin
    claim: JsonObject
    inventory_pin: FilePin


PRESERVED_TYPED_OBSERVER_SOURCE_KEYS = (
    'typed_exit_observer_receipt', 'typed_exit_observer_close', 'typed_exit_confirm_claim',
    'normal_exit_profile', 'normal_exit_source_inventory', 'normal_exit_wire_source',
    'normal_exit_observer_source', 'normal_exit_process_source', 'normal_exit_frozen_source_index')


def preserved_failure_typed_format(bundle_value: object) -> bool:
    """Select one explicit original evidence format, rejecting mixed bundles."""
    bundle = json_object(bundle_value)
    refs = object_field(bundle, 'original_evidence')
    typed = bundle.get('process_exit_evidence_format') == 'typed-native-observer-v2'
    if 'process_exit_evidence_format' in bundle and (
            not typed or bundle.get('closure_kind') != 'preserved-failure-native-process-exit-zero'):
        raise ValueError('Preserved failure process evidence format is unknown or crossed closure kinds')
    if typed and any(key in refs for key in ('root_window_start', 'root_window_exit')):
        raise ValueError('Typed observer must not mix GUI window originals')
    if not typed and any(key in refs for key in PRESERVED_TYPED_OBSERVER_SOURCE_KEYS):
        raise ValueError('Typed observer originals require their explicit evidence format')
    return typed


def _canonical_source_index_files(index_value: object, source_root: Path,
        machine_id: str) -> dict[Path, FilePin]:
    """Read canonical relative signatures without accepting historical list aliases."""
    index = json_object(index_value)
    if (index.get('schema') != 'ck3-common-source-index-v1'
            or index.get('machine_id') != machine_id):
        raise ValueError('Original canonical source index schema/machine required')
    entries = object_field(index, 'files')
    root = source_root.resolve()
    result: dict[Path, FilePin] = {}
    for relative, value in entries.items():
        parts = relative.split('/')
        if ('\\' in relative or ':' in relative or chr(0) in relative
                or any(part in ('', '.', '..') for part in parts)):
            raise ValueError('Canonical source path cannot escape or alias its frozen root')
        path = root.joinpath(*parts)
        actual = path.resolve()
        if (not actual.is_relative_to(root) or actual != path
                or path.is_symlink() or path.is_junction()):
            raise ValueError('Canonical source path crosses its frozen root')
        metadata = json_object(value)
        if set(metadata) != {'bytes', 'sha256'}:
            raise ValueError('Exact canonical source signature fields required')
        ref = keyed_file_pin(str(actual), metadata)
        if actual in result:
            raise ValueError('Canonical source index repeats a file identity')
        result[actual] = ref
    return result


def _typed_frozen_source_index_files(index_value: object, source_root: Path,
        machine_id: str) -> dict[Path, FilePin]:
    """Import a sealed historical predecessor or the single current wire format."""
    index = json_object(index_value)
    if index.get('schema') == 'ck3-common-source-index-v1':
        return _canonical_source_index_files(index, source_root, machine_id)
    rows = index.get('files')
    if (index.get('schema') != 'ck3-shared-source-frozen-successor-v1'
            or index.get('machine_id') != machine_id or not isinstance(rows, list)):
        raise ValueError('Original frozen source index schema/machine/files required')
    result: dict[Path, FilePin] = {}
    for value in rows:
        metadata = json_object(value)
        if set(metadata) != {'path', 'bytes', 'sha256'}:
            raise ValueError('Exact historical source file pin fields required')
        ref = file_pin(metadata)
        path = Path(ref['path'])
        if not path.is_absolute() or path.resolve() in result:
            raise ValueError('Historical source index repeats or aliases a file identity')
        result[path.resolve()] = ref
    return result


def preserved_typed_observer_sources(freeze_value: object, ready_value: object,
        refs_value: object) -> PreservedTypedObserverSources:
    """Read the same original SDK receipt/profile/sources, never a GUI projection."""
    freeze, ready, refs = (json_object(value) for value in (freeze_value, ready_value, refs_value))
    if any(key in refs for key in ('root_window_start', 'root_window_exit')):
        raise ValueError('Typed observer must not mix GUI window originals')
    pins: dict[str, FilePin] = {}
    for key in PRESERVED_TYPED_OBSERVER_SOURCE_KEYS:
        ref = file_pin(refs.get(key))
        bound = 16777216 if key == 'normal_exit_frozen_source_index' else 1048576
        if set(object_field(refs, key)) != {'path', 'bytes', 'sha256'} or ref['bytes'] > bound:
            raise ValueError('Bounded exact typed observer original pin required: ' + key)
        path = Path(ref['path'])
        if (not path.is_absolute() or path.is_symlink() or not path.is_file()
                or path.stat().st_size != ref['bytes'] or _verification_actual_pin_v1(path) != ref):
            raise ValueError('Typed observer original bytes changed: ' + key)
        pins[key] = ref
    files = object_field(freeze, 'files')
    # The public wire was indexed by the original frozen source graph, rather
    # than repeated in frozen-argv.files. Consume that original graph as well.
    for key in ('normal_exit_profile', 'normal_exit_source_inventory', 'normal_exit_frozen_source_index'):
        ref = pins[key]
        if files.get(ref['path']) != {'bytes': ref['bytes'], 'sha256': ref['sha256']}:
            raise ValueError('Typed observer source/profile is not an original frozen input: ' + key)
    index = json_object(json.loads(Path(pins['normal_exit_frozen_source_index']['path']).read_bytes()))
    root = Path(text_field(freeze, 'source_root')).resolve()
    indexed = _typed_frozen_source_index_files(index, root,
        text_field(object_field(freeze, 'identity_allocation'), 'machine_id'))
    for key, name in (('normal_exit_wire_source', 'normal_exit_public_wire_v2.py'),
                      ('normal_exit_observer_source', 'normal_exit_pending_observer_v1.py'),
                      ('normal_exit_process_source', 'normal_exit_process_observer_v1.py')):
        ref = pins[key]
        path = Path(ref['path']).resolve()
        if (path != root/'ck3_autonomous_player/src/xar_autoplayer/bridge'/name
                or indexed.get(path) != ref):
            raise ValueError('Typed observer SDK source belongs to a different frozen source')
    profile_ref = pins['normal_exit_profile']
    profile = json_object(json.loads(Path(profile_ref['path']).read_bytes()))
    inventory = object_field(profile, 'normal_exit_source_inventory')
    if (type(profile.get('schema_version')) is not int or profile.get('schema_version') != 1
            or ready.get('normal_exit_managed_profile') != profile_ref
            or inventory != {'path': pins['normal_exit_source_inventory']['path'],
                             'sha256': pins['normal_exit_source_inventory']['sha256']}
            or Path(text_field(profile, 'state_directory')).resolve() != Path(text_field(freeze, 'state_dir')).resolve()
            or Path(text_field(profile, 'evidence_directory')).resolve() != Path(profile_ref['path']).resolve().parent.parent
            or Path(profile_ref['path']).resolve().parent.name != 'normal-exit-binding'
            or Path(profile_ref['path']).resolve().parent.parent.name != freeze.get('run_id')):
        raise ValueError('Typed observer original profile/inventory crossed the allocated run')
    requests = Path(text_field(freeze, 'state_dir')).resolve()/'native-session/normal-exit-map-requests'
    if any(Path(pins[key]['path']).resolve().parent != requests for key in
           ('typed_exit_observer_receipt', 'typed_exit_observer_close', 'typed_exit_confirm_claim')):
        raise ValueError('Typed observer original receipts crossed the allocated state directory')
    return PreservedTypedObserverSources(
        receipt_pin=pins['typed_exit_observer_receipt'],
        receipt=json_object(json.loads(Path(pins['typed_exit_observer_receipt']['path']).read_bytes())),
        close_pin=pins['typed_exit_observer_close'],
        close=json_object(json.loads(Path(pins['typed_exit_observer_close']['path']).read_bytes())),
        claim_pin=pins['typed_exit_confirm_claim'],
        claim=json_object(json.loads(Path(pins['typed_exit_confirm_claim']['path']).read_bytes())),
        inventory_pin=pins['normal_exit_source_inventory'])


def validate_preserved_typed_observer(report_value: object, sources: PreservedTypedObserverSources,
        pid: int) -> str:
    from xar_autoplayer.bridge.normal_exit_public_wire_v2 import (
        normal_exit_public_result_v2, parse_normal_exit_public_result_v2)
    report = json_object(report_value)
    steps = report.get('steps')
    if not isinstance(steps, list):
        raise ValueError('Original typed observer steps required')
    rows = [json_object(row) for row in steps]
    observed = [row for row in rows if object_field(row, 'plan').get('tool') == 'ck3_observe_normal_exit_v1'
                and row.get('ok') is True and object_field(row, 'result').get('process_exit_observed') is True]
    if len(observed) != 1:
        raise ValueError('Exactly one successful original terminal observer is required')
    public = object_field(observed[0], 'result')
    parsed = parse_normal_exit_public_result_v2(public)
    projected = json_object(normal_exit_public_result_v2(sources['receipt']))
    expected: JsonObject = {**projected, 'observer_retained': False,
        'observer_close_receipt_path': sources['close_pin']['path']}
    if public != expected:
        raise ValueError('Public typed observer differs from its original receipt and explicit handle close')
    confirms = [row for row in rows if object_field(row, 'plan').get('tool') == 'ck3_request_normal_exit_v1'
                and object_field(object_field(row, 'plan'), 'args').get('action') == 'confirm_desktop'
                and row.get('ok') is True]
    if len(confirms) != 1:
        raise ValueError('Exactly one original desktop confirmation is required')
    confirmed = object_field(confirms[0], 'result')
    confirmed_model = parse_normal_exit_public_result_v2(confirmed,
        expected_process_creation_filetime_100ns=parsed.process_creation_filetime_100ns)
    for key in ('request_id', 'claim_path', 'source_inventory_sha256', 'process_creation_filetime_100ns', 'process_preconfirm_pin'):
        if public.get(key) != confirmed.get(key):
            raise ValueError('Terminal observer crossed the original once-only desktop confirmation')
    process, preconfirm = object_field(public, 'process_observation'), object_field(public, 'process_preconfirm_pin')
    birth = text_field(public, 'process_creation_filetime_100ns')
    if (public.get('schema') != 'ck3-normal-exit-process-observation-result-v2'
            or public.get('action') != 'confirm_desktop' or public.get('status') != 'process_exit_observed_zero'
            or public.get('process_exit_observed') is not True or public.get('typed_normal_exit_observed') is not True
            or public.get('retry_authorized') is not False or public.get('autosave_verified') is not False
            or type(public.get('exit_code')) is not int or public.get('exit_code') != 0
            or type(public.get('native_submission_count')) is not int or public.get('native_submission_count') != 0
            or type(confirmed.get('native_submission_count')) is not int or confirmed.get('native_submission_count') != 1
            or process.get('pid') != pid or type(process.get('pid')) is not int
            or process.get('wait_state') != 'signaled' or type(process.get('wait_result')) is not int or process.get('wait_result') != 0
            or process.get('process_identity_verified') is not True or process.get('process_exit_observed') is not True
            or process.get('creation_filetime_100ns') != birth or preconfirm.get('creation_filetime_100ns') != birth
            or process.get('retained_handle_token') != preconfirm.get('retained_handle_token')
            or public.get('receipt_path') != sources['receipt_pin']['path']
            or public.get('claim_path') != sources['claim_pin']['path']
            or public.get('source_inventory_sha256') != sources['inventory_pin']['sha256']):
        raise ValueError('Original typed native observer does not establish the same retained OS0 process')
    close, claim = sources['close'], sources['claim']
    identity = object_field(claim, 'identity')
    confirmed_memory = json_object(confirmed_model.to_memory())
    native_confirmation = object_field(confirmed_memory, 'native_observation')
    if (set(close) != {'schema', 'reason', 'fact_receipt_path', 'pid', 'creation_filetime_100ns',
                       'retained_handle_token', 'close_error', 'retry_authorized'}
            or set(claim) != {'schema', 'identity', 'request_id', 'status', 'exit_context_signature',
                              'source_inventory_sha256', 'process_preconfirm_pin'}
            or set(identity) != {'game_pid', 'creation_filetime_100ns', 'action'}
            or close.get('schema') != 'ck3-normal-exit-observer-close-v1'
            or close.get('reason') != 'independent_exit_fact_preserved' or close.get('close_error') is not None
            or close.get('retry_authorized') is not False or close.get('fact_receipt_path') != sources['receipt_pin']['path']
            or type(close.get('pid')) is not int or close.get('pid') != pid
            or str(_late_integer(close.get('creation_filetime_100ns'), 'Observer close birth')) != birth
            or close.get('retained_handle_token') != preconfirm.get('retained_handle_token')
            or claim.get('schema') != 'ck3-normal-exit-once-claim-v1' or claim.get('request_id') != public.get('request_id')
            or claim.get('status') != 'claimed_result_unknown_no_retry'
            or claim.get('source_inventory_sha256') != public.get('source_inventory_sha256')
            or claim.get('process_preconfirm_pin') != confirmed_memory.get('process_preconfirm_pin')
            or claim.get('exit_context_signature') != native_confirmation.get('exit_context_signature')
            or type(identity.get('game_pid')) is not int or identity.get('game_pid') != pid
            or str(_late_integer(identity.get('creation_filetime_100ns'), 'Original claim birth')) != birth
            or identity.get('action') != 'confirm_desktop'):
        raise ValueError('Original observer close/once claim belongs to another process or source')
    return birth


def _late_object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError(label + ' must be an object')
    return {k: v for k, v in value.items() if isinstance(k, str)}


def _late_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(label + ' must be an integer, not bool')
    return value


def _late_check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_preserved_failure_native_os0(normal_value: object, retained_value: object,
        game_value: object, native_value: object, report_value: object,
        window_start_value: object, window_exit_value: object, machine_id: str, *,
        typed_observer_sources: PreservedTypedObserverSources | None = None) -> PreservedFailureOS0Facts:
    """Read the completed failure lifecycle without rewriting the original close."""
    normal, retained, game, native, report = (
        json_object(value) for value in (normal_value, retained_value, game_value, native_value,
                                        report_value))
    shutdown = object_field(native, 'shutdown')
    pid = _late_integer(game.get('pid'), 'Original retained CK3 PID')
    native_pid = _late_integer(native.get('pid'), 'Original native CK3 PID')
    shutdown_pid = _late_integer(shutdown.get('ck3_pid'), 'Original shutdown CK3 PID')
    birth = game.get('create_time')
    if (type(birth) not in (int, float) or not isinstance(birth, (int, float))
            or not math.isfinite(birth) or pid <= 0):
        raise ValueError('Original retained CK3 process identity absent')
    error = text_field(report, 'error')
    original_lifecycle = normal.get('failure_lifecycle_completed')
    if type(original_lifecycle) is not bool or not isinstance(original_lifecycle, bool):
        raise ValueError('Original close lifecycle boolean must remain explicit')
    if (retained.get('pid') != pid or type(retained.get('pid')) is not int
            or retained.get('create_time') != birth or type(retained.get('create_time')) not in (int, float)
            or retained.get('signaled') is not True or retained.get('actual_retained_os0') is not True
            or type(retained.get('exit_code')) is not int or retained.get('exit_code') != 0
            or retained.get('retained_synchronize_query_handle_acquired') is not True
            or game.get('retained_synchronize_query_handle_acquired') is not True
            or normal.get('retained_handle') != retained or normal.get('host_error') != error
            or normal.get('normal_close_qualified') is not False or normal.get('business_pass') is not False
            or normal.get('failure_preserved') is not True
            or normal.get('managed_thread_finished') is not True or normal.get('cleanup_ok') is not True
            or normal.get('host_finished_at') != report.get('finished_at')
            or native.get('exit_reason') != 'process_exit' or native_pid != pid
            or type(native.get('process_exit_code')) is not int or native.get('process_exit_code') != 0
            or shutdown_pid != pid or type(shutdown.get('ck3_exit_code')) is not int
            or shutdown.get('ck3_exit_code') != 0
            or type(shutdown.get('job_active_processes_before_termination')) is not int
            or shutdown.get('job_active_processes_before_termination') != 0
            or type(shutdown.get('job_active_processes_final')) is not int
            or shutdown.get('job_active_processes_final') != 0
            or shutdown.get('ok') is not True or shutdown.get('cleanup_proven') is not True):
        raise ValueError('Preserved failure must retain actual OS0, native process exit and zero pre-cleanup Job count')
    steps = report.get('steps')
    if not isinstance(steps, list):
        raise ValueError('Original failure lifecycle steps absent')
    finishes = [json_object(item) for item in steps
                if object_field(json_object(item), 'plan').get('kind') == 'finish_hold']
    if len(finishes) != 1:
        raise ValueError('Exactly one original failure finish_hold is required')
    row = finishes[0]
    plan, result, after = object_field(row, 'plan'), object_field(row, 'result'), object_field(row, 'after_snapshot')
    proof = object_field(after, 'process_exit_zero_proof')
    if (plan.get('failure_shutdown') is not True or row.get('ok') is not True
            or result.get('hold_finished') is not True or result.get('failure_preserved') is not True
            or result.get('host_error') != error or result.get('business_pass') is not False
            or result.get('normal_close_qualified') is not False
            or after != normal.get('failure_shutdown_proof')
            or after.get('status') != 'failure_shutdown_lifecycle_only'
            or after.get('business_pass') is not False or after.get('normal_close_qualified') is not False
            or proof.get('managed_session_done') is not True or _late_integer(proof.get('pid'), 'Failure proof CK3 PID') != pid
            or proof.get('exit_reason') != 'process_exit' or type(proof.get('process_exit_code')) is not int
            or proof.get('process_exit_code') != 0 or proof.get('shutdown') != shutdown):
        raise ValueError('Original finish_hold did not consume this preserved failure native exit proof')
    native_end, finish_end, host_end = (datetime.fromisoformat(text_field(value, key)) for value, key in
        ((native, 'finished_at'), (row, 'finished_at'), (report, 'finished_at')))
    if any(stamp.tzinfo is None for stamp in (native_end, finish_end, host_end)) or not native_end <= finish_end <= host_end:
        raise ValueError('Native exit, failure finish_hold and host completion chronology differs')
    if typed_observer_sources is not None:
        if window_start_value is not None or window_exit_value is not None:
            raise ValueError('Typed native observer evidence cannot be mixed with GUI window receipts')
        filetime = validate_preserved_typed_observer(report, typed_observer_sources, pid)
    else:
        window_start, window_exit = json_object(window_start_value), json_object(window_exit_value)
        filetime = text_field(window_start, 'birth_filetime')
        if (window_start.get('machine_id') != machine_id or window_exit.get('machine_id') != machine_id
                or type(window_start.get('pid')) is not int or window_start.get('pid') != pid
                or type(window_exit.get('pid')) is not int or window_exit.get('pid') != pid
                or window_exit.get('opened') is not True or window_exit.get('exit_code_read') is not True
                or type(window_exit.get('wait_result')) is not int or window_exit.get('wait_result') != 0
                or type(window_exit.get('actual_exit_code')) is not int or window_exit.get('actual_exit_code') != 0):
            raise ValueError('Original Root window observation does not prove the same PID signaled OS0')
    if re.fullmatch('[1-9][0-9]{0,19}', filetime) is None or int(filetime) >= 1 << 64:
        raise ValueError('Original Win32 birth FILETIME requires a canonical uint64 decimal string')
    # FILETIME is preserved at native precision. The existing Popen numeric
    # create_time and WMI microsecond string remain independent original facts.
    return PreservedFailureOS0Facts(closure_kind='preserved-failure-native-process-exit-zero',
        original_ck3_exit_code=0, actual_retained_os0=True, native_cleanup_qualified=True,
        failure_lifecycle_completed=True, original_normal_close_lifecycle_completed=original_lifecycle,
        win32_birth_filetime=filetime)


def validate_root_observed_public_exit(value: object, machine: str,
        mode: Literal['run', 'allocate'], code: int) -> list[str]:
    """Consume the Root's actual original command receipt, without invented Popen fields."""
    row = json_object(value)
    if (row.get('machine_id') != machine or type(row.get('exit_code')) is not int
            or row.get('exit_code') != code):
        raise ValueError('Root-observed original public command exit differs')
    argv = strings_field(row, 'argv')
    indices = [i for i, item in enumerate(argv) if Path(item).name == 'ck3_mod_acceptance.py']
    if len(indices) != 1 or indices[0] + 1 >= len(argv) or argv[indices[0] + 1] != mode:
        raise ValueError('Root-observed original public command mode differs')
    # Historical Root allocator observations carry observed_at_utc. The later
    # original command producer carries a started/finished pair instead. These
    # are distinct original receipt shapes, never synthesized timestamp aliases.
    if mode == 'allocate' and 'finished_at_utc' in row:
        if 'observed_at_utc' in row:
            raise ValueError('Root-observed allocator terminal timestamp formats cannot be mixed')
        started = datetime.fromisoformat(text_field(row, 'started_at_utc'))
        finished = datetime.fromisoformat(text_field(row, 'finished_at_utc'))
        if started.tzinfo is None or finished.tzinfo is None or started > finished:
            raise ValueError('Root-observed allocator command completion chronology differs')
        stamp = row['finished_at_utc']
    else:
        stamp = row.get('finished_at_utc') if mode == 'run' else row.get('observed_at_utc')
    if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
        raise ValueError('Root-observed original public terminal timestamp absent')
    return argv


def validate_late_native_cleanup(normal_value: object, retained_value: object,
        game_value: object, native_value: object, report_value: object,
        normal_written_ns: int, failed_query_value: object = None) -> LateNativeCleanupFacts:
    """Keep an unsignaled original wait distinct from later native Job cleanup."""
    normal = _late_object(normal_value, 'Original normal-close result')
    retained = _late_object(retained_value, 'Original retained wait')
    game = _late_object(game_value, 'Original retained identity')
    native = _late_object(native_value, 'Later native report')
    report = _late_object(report_value, 'Original host report')
    shutdown = _late_object(native.get('shutdown'), 'Later native shutdown')
    pid = _late_integer(game.get('pid'), 'Original CK3 PID')
    created = game.get('create_time')
    _late_check(pid > 0 and type(created) in (int, float) and
        game.get('retained_synchronize_query_handle_acquired') is True and
        retained.get('retained_synchronize_query_handle_acquired') is True and
        _late_integer(retained.get('pid'), 'Retained wait PID') == pid ==
        _late_integer(native.get('pid'), 'Native CK3 PID') ==
        _late_integer(shutdown.get('ck3_pid'), 'Shutdown CK3 PID') and
        type(retained.get('create_time')) in (int, float) and retained.get('create_time') == created,
        'Late cleanup crossed the actual retained CK3 identity')
    _late_check(retained.get('signaled') is False and 'exit_code' in retained and
        retained['exit_code'] is None and retained.get('actual_retained_os0') is False and
        retained == normal.get('retained_handle'),
        'Late cleanup requires the original unsignaled/null retained wait')
    error = report.get('error')
    failure_known = isinstance(error, str) and bool(error)
    if 'error' in report and error is None and failed_query_value is not None:
        validate_failed_live_diagnostic(report, failed_query_value)
        failure_known = True
    _late_check(normal.get('normal_close_qualified') is False and normal.get('business_pass') is False and
        normal.get('failure_lifecycle_completed') is False and normal.get('managed_thread_finished') is False and
        normal.get('host_finished_at') is None and normal.get('cleanup_ok') is None and
        'host_error' in normal and normal['host_error'] == error and failure_known,
        'Late cleanup must preserve the failed original close')
    code = _late_integer(shutdown.get('ck3_exit_code'), 'Native-reported cleanup exit')
    _late_check(code != 0 and native.get('process_exit_code') is None and
        native.get('exit_reason') == 'stop' and shutdown.get('ok') is True and
        shutdown.get('tree_gone') is True and shutdown.get('cleanup_proven') is True and
        _late_integer(shutdown.get('job_active_processes_final'), 'Final native Job count') == 0,
        'Late cleanup is native Job cleanup, not retained OS0 or normal exit')
    finished = native.get('finished_at')
    _late_check(isinstance(finished, str), 'Later native finish time is missing')
    if not isinstance(finished, str):
        raise ValueError('Later native finish time is missing')
    stamp = datetime.fromisoformat(finished)
    _late_check(stamp.tzinfo is not None and
        _late_integer(normal_written_ns, 'Original normal-close write time') > 0 and
        stamp.timestamp() * 1_000_000_000 > normal_written_ns,
        'Native cleanup did not finish after the original retained wait expired')
    return {'closure_kind': 'retained-wait-expired-then-native-cleanup',
        'original_ck3_exit_code': None, 'original_retained_wait_signaled': False,
        'actual_retained_os0': False, 'native_reported_ck3_exit_code': code,
        'native_process_exit_code': None, 'failure_lifecycle_completed': False,
        'native_cleanup_qualified': None}


def validate_failed_gui_os0_cleanup(normal_value: object, retained_value: object,
        game_value: object, native_value: object, report_value: object,
        review_value: object, run_id: str) -> FailedGuiOS0CleanupFacts:
    """Preserve a failed host while admitting its reviewed GUI OS0 resource cleanup."""
    import math
    normal = _late_object(normal_value, 'Failed GUI close')
    retained = _late_object(retained_value, 'Original GUI retained wait')
    game = _late_object(game_value, 'Original GUI CK3 identity')
    native = _late_object(native_value, 'Original GUI native report')
    report = _late_object(report_value, 'Original failed GUI host report')
    review = _late_object(review_value, 'Original manual GUI review')
    shutdown = _late_object(native.get('shutdown'), 'Original GUI shutdown')
    pid = _late_integer(game.get('pid'), 'Original GUI CK3 PID')
    created = game.get('create_time')
    if not isinstance(created, (int, float)) or isinstance(created, bool) or not math.isfinite(created):
        raise ValueError('Original GUI CK3 birth must be finite numeric identity')
    _late_check(pid > 0 and game.get('retained_synchronize_query_handle_acquired') is True and
        retained.get('retained_synchronize_query_handle_acquired') is True and
        _late_integer(retained.get('pid'), 'GUI retained PID') == pid ==
        _late_integer(native.get('pid'), 'GUI native PID') ==
        _late_integer(shutdown.get('ck3_pid'), 'GUI shutdown PID') and
        type(retained.get('create_time')) in (int, float) and retained.get('create_time') == created and
        retained.get('signaled') is True and retained.get('actual_retained_os0') is True and
        _late_integer(retained.get('exit_code'), 'GUI retained exit') == 0 and
        retained == normal.get('retained_handle'), 'Failed GUI retained OS0 identity differs')
    error = report.get('error')
    _late_check(isinstance(error, str) and bool(error) and normal.get('host_error') == error and
        normal.get('normal_close_qualified') is False and normal.get('business_pass') is False and
        normal.get('failure_preserved') is True and normal.get('failure_lifecycle_completed') is True and
        normal.get('managed_thread_finished') is True and normal.get('cleanup_ok') is True and
        normal.get('host_finished_at') == report.get('finished_at'),
        'Failed GUI close must preserve its original host failure and completed cleanup')
    _late_check(review.get('schema') == 'ck3-mod-acceptance-manual-normal-quit-review-v1' and
        review.get('run_id') == run_id and isinstance(review.get('reviewer'), str) and bool(review['reviewer']) and
        _late_integer(review.get('pid'), 'Manual GUI PID') == pid and
        type(review.get('create_time')) in (int, float) and review.get('create_time') == created and
        review.get('normal_gui_quit') is True and review.get('direct_reviewed') is True and
        review.get('autosave_unchecked_observed') is True and
        all(review.get(key) is False for key in
            ('actual_os0_proven', 'actual_native0_proven', 'process_exit_claimed', 'business_pass')) and
        review == normal.get('root_normal_gui_review') == normal.get('operator_normal_gui_review'),
        'Failed GUI original direct review differs or claims unobserved exit credit')
    _late_check(native.get('exit_reason') == 'process_exit' and
        _late_integer(native.get('process_exit_code'), 'Native GUI process exit') == 0 and
        _late_integer(shutdown.get('ck3_exit_code'), 'Native GUI shutdown exit') == 0 and
        _late_integer(shutdown.get('job_active_processes_before_termination'), 'GUI pre-cleanup Job count') == 0 and
        shutdown.get('ok') is True and shutdown.get('tree_gone') is True and
        shutdown.get('cleanup_proven') is True and
        _late_integer(shutdown.get('job_active_processes_final'), 'GUI final Job count') == 0,
        'Failed GUI exit must be original process OS0 with no Job termination')
    finished, host_finished = native.get('finished_at'), report.get('finished_at')
    if not isinstance(finished, str) or not isinstance(host_finished, str):
        raise ValueError('Failed GUI native and host finish times are required')
    first, last = datetime.fromisoformat(finished), datetime.fromisoformat(host_finished)
    _late_check(first.tzinfo is not None and last.tzinfo is not None and first <= last,
        'Failed GUI cleanup chronology differs')
    return {'closure_kind': 'failed-host-gui-os0-cleanup-complete',
        'original_ck3_exit_code': 0, 'original_retained_wait_signaled': True,
        'actual_retained_os0': True, 'native_reported_ck3_exit_code': 0,
        'native_process_exit_code': 0, 'failure_lifecycle_completed': True,
        'native_cleanup_qualified': True}


def _failed_gui_source(refs_value: object, key: str, expected: Path) -> dict[str, object]:
    """Read the two new bounded GUI leaves without an untyped legacy I/O boundary."""
    refs = _late_object(refs_value, 'Failed GUI evidence references')
    ref = _late_object(refs.get(key), 'Failed GUI source pin')
    path, digest = ref.get('path'), ref.get('sha256')
    size = _late_integer(ref.get('bytes'), 'Failed GUI source bytes')
    if (set(ref) != {'path', 'bytes', 'sha256'} or not isinstance(path, str) or
            Path(path).resolve() != expected.resolve() or not 0 < size <= 1048576 or
            not isinstance(digest, str) or re.fullmatch('[0-9a-f]{64}', digest) is None):
        raise ValueError('Failed GUI original source pin differs: ' + key)
    with expected.open('rb') as stream:
        raw = stream.read(size + 1)
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Failed GUI original source bytes differ: ' + key)
    return _late_object(json.loads(raw), 'Failed GUI original source object')


def validate_late_public_wait(value_raw: object, started_raw: object, process_raw: object,
        argv_raw: object, machine: str, mode: Literal['run', 'allocate'], code: int) -> list[str]:
    """Consume the actual recorded-Popen format without fabricating legacy fields."""
    value = _late_object(value_raw, 'Original public wait')
    started = _late_object(started_raw, 'Original public STARTED')
    process = _late_object(process_raw, 'Original public retained Popen')
    _late_check(isinstance(argv_raw, list) and all(isinstance(arg, str) for arg in argv_raw),
        'Original public argv must be a string list')
    if not isinstance(argv_raw, list):
        raise ValueError('Original public argv is missing')
    argv = [arg for arg in argv_raw if isinstance(arg, str)]
    _late_check(all(row.get('machine_id') == machine and row.get('argv') == argv
        for row in (value, started, process)) and
        _late_integer(value.get('original_popen_wait_result'), 'Original Popen wait') == code and
        _late_integer(value.get('exit_code'), 'Original public exit') == code and
        started.get('original_popen_wait_result') is None and
        process.get('original_popen_wait_result') is None and
        _late_integer(value.get('pid'), 'Original public PID') ==
        _late_integer(process.get('pid'), 'Retained public PID') > 0,
        'Late cleanup public original Popen identity/wait differs: ' + mode)
    start, end = value.get('started_at_utc'), value.get('finished_at_utc')
    digest = value.get('argv_sha256')
    _late_check(isinstance(digest, str) and len(digest) == 64 and
        all(ch in '0123456789abcdef' for ch in digest), 'Original public argv SHA is missing')
    _late_check(isinstance(start, str) and isinstance(end, str) and
        all(row.get('started_at_utc') == start and row.get('argv_sha256') == value.get('argv_sha256')
            for row in (started, process)), 'Original public start/argv binding differs')
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError('Original public wait times missing')
    first, last = datetime.fromisoformat(start), datetime.fromisoformat(end)
    _late_check(first.tzinfo is not None and last.tzinfo is not None and last >= first,
        'Original public Popen completion precedes its start')
    return argv


def validate_late_failed_day(diagnostic_raw: object, row_raw: object) -> None:
    """The original unknown request is a host advance_day, not a missing MCP tool."""
    diagnostic = _late_object(diagnostic_raw, 'Original failed-day selection')
    row = _late_object(row_raw, 'Original failed day')
    plan = _late_object(row.get('plan'), 'Original failed day plan')
    _late_check(diagnostic.get('kind') == 'advance_day' and 'tool' not in diagnostic and
        row.get('id') == diagnostic.get('step_id') and isinstance(row.get('id'), str) and
        plan.get('kind') == 'advance_day' and 'tool' not in plan and
        _late_integer(plan.get('days'), 'Original failed requested days') == 1 and
        row.get('ok') is False and isinstance(row.get('error'), str) and bool(row['error']) and
        isinstance(row.get('finished_at'), str) and bool(row['finished_at']),
        'Late-cleanup source-bound failed natural day differs')


def validate_failed_live_diagnostic(report_raw: object, diagnostic_raw: object) -> None:
    """Bind a failed step even when a continue-on-error host has null top-level error."""
    report = _late_object(report_raw, 'Original failed host report')
    diagnostic = _late_object(diagnostic_raw, 'Original failed-step selection')
    steps = report.get('steps')
    _late_check(isinstance(steps, list), 'Original failed steps must be a list')
    if not isinstance(steps, list):
        raise ValueError('Original failed steps missing')
    rows = [_late_object(item, 'Original host step') for item in steps]
    selected = [row for row in rows if row.get('id') == diagnostic.get('step_id')]
    _late_check(isinstance(diagnostic.get('step_id'), str) and bool(diagnostic['step_id']) and
        len(selected) == 1, 'Failed-live source-bound failed query is missing')
    row = selected[0]
    plan = _late_object(row.get('plan'), 'Original failed step plan')
    _late_check(row.get('ok') is False and isinstance(row.get('error'), str) and bool(row['error']) and
        isinstance(row.get('finished_at'), str) and bool(row['finished_at']),
        'Failed-live source-bound failed query is missing')
    if diagnostic.get('kind') == 'advance_day':
        _late_check(set(diagnostic) == {'step_id', 'kind'}, 'Failed-day selection fields differ')
        validate_late_failed_day(diagnostic, row)
    else:
        _late_check(set(diagnostic) == {'step_id', 'tool'} and
            isinstance(diagnostic.get('tool'), str) and bool(diagnostic['tool']) and
            plan.get('tool') == diagnostic['tool'], 'Failed-live selected failed tool differs')


class SplitPublicWaitFacts(TypedDict):
    argv: list[str]
    pid: int


def _recorded_decimal(value: object, label: str) -> int:
    if not isinstance(value, str) or re.fullmatch(r'(0|[1-9][0-9]*)', value) is None:
        raise ValueError(label + ' must be canonical decimal text')
    number = int(value)
    _late_check(0 < number <= 18446744073709551615, label + ' is outside uint64')
    return number


class RecordedPublicProducerFacts(TypedDict):
    custody_duration_ns: int
    root_quit_duration_ns: int


class FailedSupervisorAbsenceFacts(TypedDict):
    original_supervisor_generation: ProcessGeneration
    current_supervisor_generation: ProcessGeneration | None
    original_supervisor_generation_absent: Literal[True]


def validate_failed_supervisor_generation(original_value: object,
        current_value: object) -> FailedSupervisorAbsenceFacts:
    """A reused PID cannot resurrect the recorded supervisor's exact FILETIME birth."""
    supervisor = _late_object(original_value, 'Original failed supervisor')
    original = _late_object(supervisor.get('original_popen_identity'), 'Original supervisor generation')
    pid = _late_integer(supervisor.get('pid'), 'Original supervisor PID')
    birth = original.get('birth_filetime')
    _late_check(set(original) == {'pid', 'birth_filetime'} and pid > 0 and
        _late_integer(original.get('pid'), 'Original supervisor generation PID') == pid,
        'Original supervisor generation PID differs')
    original_birth = _recorded_decimal(birth, 'Original supervisor FILETIME')
    if not isinstance(birth, str):
        raise ValueError('Original supervisor FILETIME must be decimal text')
    original_typed: ProcessGeneration = {'pid': pid, 'birth_filetime': birth}
    current_typed: ProcessGeneration | None = None
    if current_value is not None:
        current = _late_object(current_value, 'Current supervisor PID generation')
        current_birth = current.get('birth_filetime')
        _late_check(set(current) == {'pid', 'birth_filetime'} and
            _late_integer(current.get('pid'), 'Current supervisor generation PID') == pid,
            'Current supervisor generation PID differs')
        observed_birth = _recorded_decimal(current_birth, 'Current supervisor FILETIME')
        if not isinstance(current_birth, str):
            raise ValueError('Current supervisor FILETIME must be decimal text')
        _late_check(observed_birth > original_birth, 'Failed-live original supervisor still present or birth chronology differs')
        current_typed = {'pid': pid, 'birth_filetime': current_birth}
    return {'original_supervisor_generation': original_typed,
        'current_supervisor_generation': current_typed, 'original_supervisor_generation_absent': True}


def _recorded_duration(expression: ast.expr, label: str) -> int:
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name) or \
            expression.func.id != 'str' or len(expression.args) != 1 or expression.keywords:
        raise ValueError(label + ' must encode a decimal deadline')
    added = expression.args[0]
    if not isinstance(added, ast.BinOp) or not isinstance(added.op, ast.Add) or \
            not isinstance(added.left, ast.Name) or added.left.id != 't':
        raise ValueError(label + ' must add a duration to the original monotonic start')
    multiplied = added.right
    if not isinstance(multiplied, ast.BinOp) or not isinstance(multiplied.op, ast.Mult) or \
            not isinstance(multiplied.left, ast.Constant) or \
            not isinstance(multiplied.right, ast.Constant):
        raise ValueError(label + ' must multiply positive integer seconds by 1000000000')
    seconds = _late_integer(multiplied.left.value, label + ' seconds')
    scale = _late_integer(multiplied.right.value, label + ' scale')
    _late_check(0 < seconds <= 18446744073709551615 // 1000000000 and scale == 1000000000,
        label + ' seconds/scale differ')
    return seconds * scale


def validate_recorded_public_producer(source_raw: object, machine: str) -> RecordedPublicProducerFacts:
    """Bind the pinned wrapper's direct Popen/wait publication, without executing it."""
    if not isinstance(source_raw, bytes) or not source_raw or len(source_raw) > 1048576:
        raise ValueError('Recorded public producer source bytes required')
    tree = ast.parse(source_raw.decode('utf-8'))
    # The source is an original evidence input, not a reconstructed intent. Verify
    # its direct wait-to-EXIT tail; no source hash or historical PID is hardcoded.
    expected = ast.parse("""
child=subprocess.Popen(argv,env=env,cwd=REPO,stdout=out,stderr=err)
v={'schema':'ck3-recorded-actual-command-v1','machine_id':MACHINE,'argv':argv,'shell':False,'pid':child.pid,'started_at_utc':datetime.now(timezone.utc).isoformat(),'started_monotonic_ns':str(t),'original_wait_pending':True}
if mode=='allocate':v.update(custody_deadline_monotonic_ns=str(t+11400*1000000000),root_quit_deadline_monotonic_ns=str(t+10800*1000000000))
with start.open('x',encoding='utf-8') as h:json.dump(v,h)
print(json.dumps(v),flush=True)
code=child.wait()
v.update(original_wait_pending=False,actual_original_popen_wait=True,exit_code=code,finished_at_utc=datetime.now(timezone.utc).isoformat(),finished_monotonic_ns=str(time.monotonic_ns()))
with exitp.open('x',encoding='utf-8') as h:json.dump(v,h)
print(json.dumps({'operation':mode,'original_wait':code,'receipt':str(exitp)}),flush=True)
""").body
    value = expected[1]
    if not isinstance(value, ast.Assign) or not isinstance(value.value, ast.Dict):
        raise ValueError('Recorded producer schema template differs')
    value.value.values[1] = ast.Constant(value=machine)
    signature = [ast.dump(node, include_attributes=False) for node in expected]
    durations: dict[str, int] = {}
    candidates: list[list[ast.stmt]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            for index, statement in enumerate(node.body):
                if ast.dump(statement, include_attributes=False) == signature[0]:
                    candidates.append(node.body[index:])
    if len(candidates) == 1 and len(candidates[0]) == len(expected):
        deadline = candidates[0][2]
        if isinstance(deadline, ast.If) and not deadline.orelse and len(deadline.body) == 1:
            statement = deadline.body[0]
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
                call = statement.value
                _late_check(ast.dump(deadline.test) == ast.dump(expected[2].test)
                    if isinstance(expected[2], ast.If) else False,
                    'Recorded public producer allocation branch differs')
                _late_check(isinstance(call.func, ast.Attribute) and
                    isinstance(call.func.value, ast.Name) and call.func.value.id == 'v' and
                    call.func.attr == 'update' and not call.args and
                    {item.arg for item in call.keywords} == {
                        'custody_deadline_monotonic_ns', 'root_quit_deadline_monotonic_ns'} and
                    len(call.keywords) == 2,
                    'Recorded public producer allocation deadlines differ')
                for item in call.keywords:
                    if item.arg is None:
                        raise ValueError('Recorded producer deadline keyword missing')
                    durations[item.arg] = _recorded_duration(item.value, item.arg)
                # Durations are parameters of the actual wrapper, not this field
                # contract. Their receipt values still receive uint64/order checks.
                signature[2] = ast.dump(deadline, include_attributes=False)
    _late_check(len(candidates) == 1 and
        [ast.dump(node, include_attributes=False) for node in candidates[0]] == signature,
        'Recorded public producer direct original Popen/wait publication differs')
    _late_check(0 < durations['root_quit_deadline_monotonic_ns'] <
        durations['custody_deadline_monotonic_ns'], 'Recorded producer custody durations differ')
    return {'custody_duration_ns': durations['custody_deadline_monotonic_ns'],
            'root_quit_duration_ns': durations['root_quit_deadline_monotonic_ns']}


def validate_recorded_public_wait(wait_raw: object, started_raw: object,
        producer: RecordedPublicProducerFacts, machine: str,
        mode: Literal['run', 'allocate'], code: int) -> SplitPublicWaitFacts:
    """Consume genuine STARTED/EXIT receipts; retain the other public formats."""
    waited = _late_object(wait_raw, 'Recorded public EXIT')
    started = _late_object(started_raw, 'Recorded public STARTED')
    common = {'schema', 'machine_id', 'argv', 'shell', 'pid', 'started_at_utc',
              'started_monotonic_ns', 'original_wait_pending'}
    if mode == 'allocate':
        common |= {'custody_deadline_monotonic_ns', 'root_quit_deadline_monotonic_ns'}
    _late_check(set(started) == common and set(waited) == common | {
        'actual_original_popen_wait', 'exit_code', 'finished_at_utc', 'finished_monotonic_ns'},
        'Recorded public STARTED/EXIT fields differ')
    _late_check(all(row['schema'] == 'ck3-recorded-actual-command-v1' and
        row['machine_id'] == machine and row['shell'] is False for row in (started, waited)) and
        started['original_wait_pending'] is True and waited['original_wait_pending'] is False and
        waited['actual_original_popen_wait'] is True,
        'Recorded public schema/machine/original wait differs')
    _late_check(all(started[key] == waited[key] and type(started[key]) is type(waited[key])
        for key in common - {'original_wait_pending'}), 'Recorded public STARTED/EXIT identity differs')
    argv_raw = started['argv']
    if not isinstance(argv_raw, list) or not argv_raw or any(
            not isinstance(arg, str) or not arg or '\x00' in arg for arg in argv_raw):
        raise ValueError('Recorded public argv must be nonempty strings')
    argv = [arg for arg in argv_raw if isinstance(arg, str)]
    indexes = [index for index, arg in enumerate(argv) if Path(arg).name == 'ck3_mod_acceptance.py']
    _late_check(len(indexes) == 1 and indexes[0] + 1 < len(argv) and argv[indexes[0] + 1] == mode,
        'Recorded public command mode differs')
    pid = _late_integer(started['pid'], 'Recorded public PID')
    _late_check(0 < pid <= 4294967295 and
        _late_integer(waited['pid'], 'Recorded public EXIT PID') == pid and
        _late_integer(waited['exit_code'], 'Recorded public original exit') == code,
        'Recorded public PID/original exit differs')
    first = _recorded_decimal(started['started_monotonic_ns'], 'Recorded start monotonic')
    last = _recorded_decimal(waited['finished_monotonic_ns'], 'Recorded finish monotonic')
    _late_check(last >= first, 'Recorded public monotonic completion precedes start')
    stamps: list[datetime] = []
    for raw in (started['started_at_utc'], waited['finished_at_utc']):
        if not isinstance(raw, str):
            raise ValueError('Recorded public UTC timestamps must be text')
        stamp = datetime.fromisoformat(raw)
        offset = stamp.utcoffset()
        _late_check(stamp.tzinfo is not None and offset is not None and
            offset.total_seconds() == 0, 'Recorded public timestamp must be UTC')
        stamps.append(stamp)
    _late_check(stamps[1] >= stamps[0], 'Recorded public UTC completion precedes start')
    if mode == 'allocate':
        custody = _recorded_decimal(started['custody_deadline_monotonic_ns'], 'Recorded custody deadline')
        root_quit = _recorded_decimal(started['root_quit_deadline_monotonic_ns'], 'Recorded Root quit deadline')
        _late_check(first < root_quit < custody and
            custody == first + _late_integer(producer['custody_duration_ns'], 'Producer custody duration') and
            root_quit == first + _late_integer(producer['root_quit_duration_ns'], 'Producer Root quit duration'),
            'Recorded public custody ordering/producer duration differs')
    return {'argv': argv, 'pid': pid}


def validate_split_public_wait(wait_raw: object, command_raw: object, intent_raw: object,
        process_raw: object, completion_raw: object, command_path: Path, machine: str,
        mode: Literal['run', 'allocate'], code: int) -> SplitPublicWaitFacts:
    """Consume the actual command/intent/process/exit/completion producer without aliases."""
    waited = _late_object(wait_raw, 'Original split public exit')
    command = _late_object(command_raw, 'Original split public command')
    intent = _late_object(intent_raw, 'Original split public intent')
    process = _late_object(process_raw, 'Original split public process')
    completion = _late_object(completion_raw, 'Original split public completion')
    required = (
        (waited, {'machine_id', 'pid', 'returncode', 'actual_original_popen_wait', 'completed_at_utc'}),
        (command, {'machine_id', 'observed_at_utc', 'argv'}),
        (intent, {'machine_id', 'at_utc', 'stage', 'argv'}),
        (process, {'machine_id', 'pid', 'create_time', 'argv'}),
        (completion, {'machine_id', 'observed_at_utc', 'exit_code', 'command',
                      'original_subprocess_wait_observed'}),
    )
    _late_check(all(set(row) == fields and row.get('machine_id') == machine for row, fields in required),
        'Split public fields/machine differ')
    raw_argv = command['argv']
    _late_check(isinstance(raw_argv, list) and bool(raw_argv) and
        all(isinstance(arg, str) and bool(arg) for arg in raw_argv), 'Split public argv must be strings')
    if not isinstance(raw_argv, list):
        raise ValueError('Split public argv missing')
    argv = [arg for arg in raw_argv if isinstance(arg, str)]
    pid = _late_integer(waited['pid'], 'Original split public PID')
    _late_check(pid > 0 and _late_integer(process['pid'], 'Original split process PID') == pid and
        command['argv'] == intent['argv'] == process['argv'] and intent['stage'] == mode and
        waited['actual_original_popen_wait'] is True and
        completion['original_subprocess_wait_observed'] is True and
        _late_integer(waited['returncode'], 'Original split public wait') == code and
        _late_integer(completion['exit_code'], 'Original split completion exit') == code,
        'Split public original Popen identity/argv/wait differs: ' + mode)
    completion_command = completion['command']
    _late_check(isinstance(completion_command, str) and bool(completion_command),
        'Split public completion command path missing')
    if not isinstance(completion_command, str):
        raise ValueError('Split public completion command path missing')
    _late_check(Path(completion_command).resolve() == command_path.resolve(),
        'Split public completion crossed command')
    stamps: list[datetime] = []
    for raw in (command['observed_at_utc'], intent['at_utc'], waited['completed_at_utc'],
                completion['observed_at_utc']):
        _late_check(isinstance(raw, str), 'Split public timestamp must be text')
        if not isinstance(raw, str):
            raise ValueError('Split public timestamp missing')
        stamp = datetime.fromisoformat(raw)
        _late_check(stamp.tzinfo is not None, 'Split public timestamp lacks timezone')
        stamps.append(stamp)
    created = process['create_time']
    _late_check(type(created) in (int, float), 'Split public process birth must be numeric')
    if not isinstance(created, (int, float)) or isinstance(created, bool):
        raise ValueError('Split public process birth must be numeric')
    _late_check(math.isfinite(created) and stamps == sorted(stamps) and
        stamps[0].timestamp() <= created <= stamps[2].timestamp(),
        'Split public process/time ordering differs')
    return {'argv': argv, 'pid': pid}


def is_frozen_host_argument(argument: str, selected_host: Path) -> bool:
    """Windows named pipes are IPC arguments, never the selected disk script."""
    if argument.startswith(('\\\\.\\pipe\\', '\\\\?\\pipe\\')):
        return False
    return Path(argument).resolve() == selected_host


def previous_interrupted_owner_closure(previous: Path, freeze: dict[str, object], close_path: Path,
        keeper_root: Path, release_path: Path, next_state: Path, current_source_root: Path) -> JsonObject:
    """Reobserve both providers and the canonical bus; old controls stay quarantined."""
    import importlib
    import psutil
    import ck3_live_run_id as ids
    from ck3_mod_acceptance_interrupted import validate_interrupted_owner
    from ck3_mod_acceptance_background_types import text_field
    from ck3_mod_acceptance_fresh_machine_bootstrap import machine_binding
    frozen=json_object(freeze)
    source=current_source_root/'ck3_autonomous_player/src'
    sys.path.insert(0,str(source))
    try:
        provider=importlib.import_module('xar_autoplayer.environment')
        location=getattr(provider,'__file__',None)
        if not isinstance(location,str) or not Path(location).resolve().is_relative_to(source.resolve()):
            raise ValueError('Interrupted process provider differs from selected shared source: '+str(location))
        game=provider.ck3_process_inventory()
    finally:
        sys.path.remove(str(source))
    binding=machine_binding(actual_machine_binding(ids))
    current=create_current_process_observation(binding=binding,
        runtime_inventory=runtime_process_inventory(psutil,os.getpid()),ck3_inventory=game)
    keeper=json_object(read_json(previous/'keeper-process.json'))
    from ck3_mod_acceptance_interrupted import argument
    cli=Path(argument(keeper.get('argv'),'--bus-cli'))
    bus_dir=Path(argument(keeper.get('argv'),'--bus-dir'))
    cli_sha=argument(keeper.get('argv'),'--bus-cli-sha256')
    packet=subprocess.run([sys.executable,str(cli),'--bus-dir',str(bus_dir),
        '--expected-cli-sha256',cli_sha,'list'],capture_output=True,check=True,timeout=20)
    return validate_interrupted_owner(previous=previous,frozen=frozen,close_path=close_path,
        keeper_root=keeper_root,release=read_failed_runtime_release(release_path),
        bus_packet=json.loads(packet.stdout),binding=binding,current_processes=current,
        present_pids=set(psutil.pids()),next_state=next_state)


def previous_failed_live_resource_closure(previous: Path, freeze: dict[str, object], close_path: Path,
        keeper_root: Path, release_path: Path, bus_packet: dict[str, object]) -> dict[str, object]:
    """Admit an ended failed live attempt's resources; never grant normal-exit credit."""
    import psutil
    previous, keeper_root = previous.resolve(), keeper_root.resolve()
    require(close_path.stat().st_size <= 1048576, 'Failed-live closure exceeds small bound')
    bundle = read_json(close_path)
    require(bundle.get('schema') == 'ck3-mod-acceptance-failed-live-resource-closure-v1' and
            bundle.get('run_id') == freeze['run_id'] == previous.name and
            isinstance(bundle.get('machine_id'), str) and
            freeze['run_id'].startswith(bundle['machine_id'] + '--') and
            Path(bundle.get('keeper_root', '')).resolve() == keeper_root and
            all(bundle.get(key) is False for key in ('normal_close_qualified', 'typed_normal_exit_proven',
                                                    'business_pass', 'release_pass')),
            'Failed-live closure identity or negative qualification differs')
    if bundle.get('closure_kind') == 'failed-host-without-normal-close-result':
        return previous_missing_normal_resource_closure(previous, freeze, bundle, close_path,
                                                       keeper_root, release_path, bus_packet)
    if bundle.get('closure_kind') == 'expired-keeper-missing-final-report':
        return previous_expired_keeper_resource_closure(previous, freeze, bundle, close_path,
                                                       keeper_root, release_path, bus_packet)
    late_cleanup = bundle.get('closure_kind') == 'retained-wait-expired-then-native-cleanup'
    gui_os0 = bundle.get('closure_kind') == 'failed-host-gui-os0-cleanup-complete'
    preserved_os0 = bundle.get('closure_kind') == 'preserved-failure-native-process-exit-zero'
    typed_observer = preserved_failure_typed_format(bundle)
    split_public = bundle.get('public_wait_format') == 'command-intent-process-exit-completion'
    recorded_public = bundle.get('public_wait_format') == 'recorded-actual-command-started-exit-v1'
    root_observed_public = bundle.get('public_wait_format') == 'root-observed-command-exit-v1'
    require(not root_observed_public or preserved_os0, 'Root-observed public format requires preserved native process OS0')
    require(not preserved_os0 or root_observed_public, 'Preserved native process OS0 requires its actual Root public receipts')
    require('public_wait_format' not in bundle or split_public or recorded_public or root_observed_public,
            'Failed-live public wait format is unknown')
    require(not (split_public or recorded_public) or late_cleanup or gui_os0,
            'Recorded public wait requires original expired retained wait')
    require(not gui_os0 or recorded_public, 'Failed GUI OS0 requires recorded original STARTED/EXIT')
    public_pids = []
    recorded_attempts: list[str] = []
    refs, evidence = bundle.get('original_evidence'), {}
    require(isinstance(refs, dict), 'Original failed-live evidence pins required')
    def original(key, expected=None, *, decode=True, max_bytes=1048576):
        row = refs[key]; path = Path(row['path']).resolve()
        require(expected is None or path == Path(expected).resolve(), 'Failed-live original path differs: ' + key)
        require(type(row.get('bytes')) is int and 0 <= row['bytes'] <= max_bytes,
                'Failed-live evidence bound differs: ' + key)
        check_pin(path, row); evidence[key] = row
        return read_json(path) if decode else path.read_bytes()
    original('frozen_argv', previous/'frozen-argv.json')
    ready = original('ready_context', previous/'ready-context.json')
    require(ready.get('run_id') == freeze['run_id'] and
            Path(ready.get('run_dir', '')).resolve() == previous and
            Path(ready.get('keeper_root', '')).resolve() == keeper_root,
            'Failed-live ready context crossed allocation')
    prepared = original('prepared_case', ready['prepared_case']['path'])
    require(refs['prepared_case'] == ready['prepared_case'] and
            Path(prepared['startup']['state_dir']).resolve() == Path(freeze['state_dir']).resolve() and
            prepared['runtime_manifest'] == freeze['runtime_manifest'],
            'Failed-live preparation crossed frozen runtime/state')
    state = Path(freeze['state_dir']).resolve()
    host = original('host_started', previous/'host-started.json')
    host_exit = original('host_exit', previous/'host-original-process-exit.json')
    supervisor = original('host_supervisor', previous/'host-supervisor-started.json')
    require(host.get('run_id') == host_exit.get('run_id') == freeze['run_id'] and
            host.get('actual_popen_retained') is True and host.get('argv') == freeze['argv'] and
            host_exit.get('pid') == host.get('pid') and host_exit.get('actual_original_popen_wait') is True and
            type(host_exit.get('returncode')) is int and host_exit['returncode'] != 0 and
            host_exit.get('normal_ck3_exit_inferred') is False and
            type(supervisor.get('pid')) is int and type(host.get('supervisor_pid')) is int,
            'Failed-live original host/supervisor nonzero wait differs')
    supervisor_argv = supervisor.get('argv', [])
    require(isinstance(supervisor_argv, list) and '--supervise' in supervisor_argv and
            supervisor_argv.count('--run-root') == 1 and
            Path(supervisor_argv[supervisor_argv.index('--run-root') + 1]).resolve() == previous and
            supervisor_argv.count('--keeper-root') == 1 and
            Path(supervisor_argv[supervisor_argv.index('--keeper-root') + 1]).resolve() == keeper_root,
            'Failed-live supervisor argv belongs to another run/keeper')
    def public_wait(mode, code):
        value = original(mode + '_wait')
        parent = Path(refs[mode + '_wait']['path']).resolve().parent
        if root_observed_public:
            argv = validate_root_observed_public_exit(value, bundle['machine_id'], mode, code)
        elif recorded_public:
            exit_path = Path(refs[mode + '_wait']['path']).resolve()
            require(exit_path.name.startswith(mode + '-') and exit_path.name.endswith('.EXIT.actual.json'),
                    'Recorded public original EXIT path differs')
            stem = exit_path.name[:-len('.EXIT.actual.json')]
            recorded_attempts.append(stem[len(mode) + 1:])
            producer_facts = validate_recorded_public_producer(
                original('public_command_producer', decode=False), bundle['machine_id'])
            facts = validate_recorded_public_wait(value,
                original(mode + '_started', parent/(stem + '.STARTED.actual.json')),
                producer_facts, bundle['machine_id'], mode, code)
            argv = facts['argv']; public_pids.append(facts['pid'])
        elif split_public:
            facts = validate_split_public_wait(value,
                original(mode + '_command', parent/'command.json'),
                original(mode + '_intent', parent/'intent.json'),
                original(mode + '_process', parent/'process.json'),
                original(mode + '_completion', parent/'completion.json'), parent/'command.json',
                bundle['machine_id'], mode, code)
            require(Path(refs[mode + '_wait']['path']).resolve() == parent/'exit.json',
                    'Split public original exit path differs')
            argv = facts['argv']; public_pids.append(facts['pid'])
        elif late_cleanup:
            argv = validate_late_public_wait(value,
                original(mode + '_started', parent/'STARTED.actual.json'),
                original(mode + '_process', parent/'ORIGINAL-PROCESS.actual.json'),
                json.loads(original(mode + '_argv', parent/'argv.json', decode=False)), bundle['machine_id'], mode, code)
            public_pids.append(value['pid'])
        else:
            require(value.get('machine_id') == bundle['machine_id'] and value.get('phase') == mode and
                    value.get('actual_original_popen_wait') is True and value.get('completed_at_utc') and
                    type(value.get('returncode')) is int and value['returncode'] == code,
                    'Failed-live actual public wait differs: ' + mode)
            argv = value.get('argv'); require(isinstance(argv, list), 'Actual public argv missing')
        index = next((i for i, arg in enumerate(argv) if Path(arg).name == 'ck3_mod_acceptance.py'), -1)
        require(index >= 0 and argv[index + 1] == mode, 'Failed-live public command mode differs')
        def argument(flag):
            require(argv.count(flag) == 1 and argv.index(flag) + 1 < len(argv), 'Failed-live public flag missing: ' + flag)
            return argv[argv.index(flag) + 1]
        require(argument('--case') == freeze['cell'] and
                Path(argument('--prepared-case')).resolve() == Path(refs['prepared_case']['path']).resolve(),
                'Failed-live public command crossed case/preparation')
        if mode == 'run':
            context = read_json(Path(argument('--run-context')))
            require(context.get('run_id') == freeze['run_id'] and
                    Path(context.get('run_dir', '')).resolve() == previous,
                    'Failed-live public run context differs')
        else:
            require(Path(argument('--keeper-output')).resolve() == keeper_root,
                    'Failed-live allocator keeper differs')
            if recorded_public:
                require(stem == mode + '-' + argument('--attempt'),
                        'Recorded public receipt crossed allocator attempt')
        if not (late_cleanup or gui_os0 or preserved_os0):
            intent = original(mode + '_intent', parent/'intent.json')
            require(intent.get('argv') == argv and intent.get('phase') == mode,
                    'Failed-live original command intent differs')
        stdout_name = (stem + '.stdout.json') if recorded_public else (
            'stdout.json' if split_public else ('stdout.txt' if late_cleanup else 'stdout.log'))
        original(mode + '_stdout', None if root_observed_public else parent/stdout_name, decode=False, max_bytes=16777216)
        stderr_name = (stem + '.stderr.txt') if recorded_public else (
            'stderr.txt' if late_cleanup and not split_public else 'stderr.log')
        original(mode + '_stderr', None if root_observed_public else parent/stderr_name, decode=False, max_bytes=16777216)
        return Path(argument('--runtime')).resolve()
    require(public_wait('run', 2) == public_wait('allocate', 0), 'Failed-live public runtime differs')
    require(not recorded_public or len(recorded_attempts) == 2 and
            bool(recorded_attempts[0]) and recorded_attempts[0] == recorded_attempts[1],
            'Recorded public STARTED/EXIT pair crossed attempts')
    report = original('native_report', previous/'native-report.json', max_bytes=67108864)
    diagnostic = bundle.get('failed_query')
    if gui_os0 or preserved_os0:
        require('failed_query' not in bundle and isinstance(report.get('error'), str) and bool(report['error']),
                'Failed GUI OS0 requires its original top-level host error, not a fabricated failed query')
    else:
        validate_failed_live_diagnostic(report, diagnostic)
    original_error = report.get('error')
    require(report.get('status') == 'RED' and
            ((isinstance(original_error, str) and bool(original_error)) or
             (late_cleanup and 'error' in report and original_error is None)) and report.get('finished_at') and
            report.get('managed_session_done') is True and report.get('managed_session_thread_finished') is True and
            report.get('cleanup_ok') is True and Path(report['state_dir']).resolve() == state and
            Path(report['agent_source_root']).resolve() == Path(freeze['source_root']).resolve() and
            report.get('pipe') == freeze['argv'][freeze['argv'].index('--bridge-pipe') + 1],
            'Failed-live original finished report/cleanup differs')
    session = report.get('session', {}); native = session.get('report', {}); shutdown = native.get('shutdown', {})
    require(session.get('error') is None and native.get('pid') == shutdown.get('ck3_pid') and
            native.get('finished_at') and shutdown.get('ok') is True and
            shutdown.get('cleanup_proven') is True and shutdown.get('tree_gone') is True and
            shutdown.get('job_active_processes_final') == 0 and shutdown.get('contract_errors') == [] and
            all(value is True for value in shutdown.get('control_files_absent', {}).values()) and
            bool(shutdown.get('control_files_absent')) and
            all(shutdown.get('final_ck3_inventory', {}).get(key) == [] for key in ('tasklist_pids', 'wmi_pids', 'native_pids')),
            'Failed-live original native Job/process/control cleanup is incomplete')
    normal = original('normal_close', previous/'case-output/normal-close-result.json')
    require(normal.get('normal_close_qualified') is False and normal.get('business_pass') is False and
            normal.get('host_error') == report['error'], 'Failed-live original close claims normal/business credit')
    game = original('retained_identity', previous/'case-output/retained-current-process-identity.json')
    retained = original('retained_exit', previous/'case-output/actual-retained-handle-os-exit.json')
    late_facts = None
    gui_facts = None
    preserved_facts = None
    if late_cleanup:
        late_facts = validate_late_native_cleanup(normal, retained, game, native, report,
            (previous/'case-output/normal-close-result.json').stat().st_mtime_ns, diagnostic)
    elif preserved_os0:
        machine = text_field(json_object(bundle), 'machine_id')
        if typed_observer:
            typed_sources = preserved_typed_observer_sources(freeze, ready, refs)
            evidence.update({key: refs[key] for key in PRESERVED_TYPED_OBSERVER_SOURCE_KEYS})
            preserved_facts = validate_preserved_failure_native_os0(normal, retained, game, native, report,
                None, None, machine, typed_observer_sources=typed_sources)
        else:
            preserved_facts = validate_preserved_failure_native_os0(normal, retained, game, native, report,
                original('root_window_start'), original('root_window_exit'), machine)
    elif gui_os0:
        gui_refs = _late_object(refs, 'Failed GUI original references')
        review = _failed_gui_source(gui_refs, 'manual_gui_review', previous/'case-output/normal-quit-root-result.json')
        _failed_gui_source(gui_refs, 'normal_quit_awaiting', previous/'case-output/normal-quit-awaiting.json')
        evidence.update({key: gui_refs[key] for key in ('manual_gui_review', 'normal_quit_awaiting')})
        require(review.get('quit_request') == gui_refs['normal_quit_awaiting'],
                'Failed GUI review crossed the original quit request')
        visual = review.get('evidence')
        if not isinstance(visual, list) or not 0 < len(visual) <= 16:
            raise ValueError('Failed GUI original visual evidence is missing or unbounded')
        for item in visual:
            ref = _late_object(item, 'Failed GUI original visual evidence pin')
            path = ref.get('path')
            size = _late_integer(ref.get('bytes'), 'Failed GUI original visual bytes')
            if not isinstance(path, str) or not 0 < size <= 16777216:
                raise ValueError('Failed GUI original visual evidence pin is invalid')
            check_pin(Path(path), ref)
        original_run_id = freeze['run_id']
        if not isinstance(original_run_id, str):
            raise ValueError('Failed GUI original run ID must be text')
        gui_facts = validate_failed_gui_os0_cleanup(normal, retained, game, native, report,
                                                   review, original_run_id)
    else:
        require(game.get('retained_synchronize_query_handle_acquired') is True and
            retained.get('retained_synchronize_query_handle_acquired') is True and
            retained.get('pid') == game.get('pid') == native.get('pid') and
            retained.get('create_time') == game.get('create_time') and retained.get('signaled') is True and
            type(retained.get('exit_code')) is int and retained['exit_code'] != 0 and
            retained.get('actual_retained_os0') is False and retained == normal.get('retained_handle') and
            shutdown.get('ck3_exit_code') == retained['exit_code'],
                'Failed-live original retained nonzero CK3 exit differs')
    original('server_stderr', report['server_stderr'], decode=False, max_bytes=16777216)
    keeper = original('keeper_report', keeper_root/'report.json')
    if split_public or recorded_public or root_observed_public:
        require(bool(original('keeper_stop', keeper_root/'STOP', decode=False)),
                'Failed-live original cooperative keeper STOP is missing')
    waited = original('keeper_exit', previous/'keeper-actual-parent-exit.json')
    require(waited.get('run_id') == freeze['run_id'] and waited.get('keeper_actual_exit_code') == 0 and
            waited.get('keeper_report') == keeper and keeper.get('task_id') == freeze['screen_task'] and
            keeper.get('thread_exited') is True and keeper.get('failure') is None and keeper.get('entry_error') is None,
            'Failed-live actual keeper wait/thread differs')
    original('release', release_path)
    release = read_failed_runtime_release(release_path); task, event = release['task'], release.get('event', {})
    require(closed_lease(keeper, release, freeze['screen_task']) and
            task.get('state') in (('done', 'waiting') if gui_os0 else ('done',)) and
            event.get('task_id') == freeze['screen_task'] and event.get('sequence') == task['last_sequence'] and
            event.get('state') == task.get('state') and event.get('resources') == [],
            'Failed-live actual CAS release differs')
    if gui_os0 and task.get('state') == 'waiting':
        retirement = event.get('retirement', {})
        require(isinstance(retirement, dict) and retirement.get('kind') == 'expired-own-claim-released' and
                retirement.get('business_status') == 'unresolved_red' and
                type(retirement.get('prior_sequence')) is int and
                0 < retirement['prior_sequence'] < task['last_sequence'],
                'Failed GUI waiting release must preserve unresolved business failure')
    require(isinstance(bus_packet.get('tasks'), list) and
            not any('ck3-screen:acquired' in row.get('resources', []) for row in bus_packet['tasks']),
            'Failed-live still has an actual screen owner')
    keeper_process = original('keeper_process', previous/'keeper-process.json')
    for label, identity in (('host', host), ('CK3', game), ('keeper', keeper_process)):
        require(type(identity.get('pid')) is int and identity['pid'] > 0 and
                type(identity.get('create_time')) in (int, float), 'Failed-live identity absent: ' + label)
        try: present = psutil.Process(identity['pid']).create_time() == identity['create_time']
        except psutil.NoSuchProcess: present = False
        require(not present, 'Failed-live original process still present: ' + label)
    supervisor_facts = None
    if gui_os0:
        from ck3_mod_acceptance_launcher import process_identity
        supervisor_pid = _late_integer(supervisor.get('pid'), 'Original supervisor PID')
        current_supervisor = process_identity(supervisor_pid) if psutil.pid_exists(supervisor_pid) else None
        supervisor_facts = validate_failed_supervisor_generation(supervisor, current_supervisor)
        require(host['supervisor_pid'] == supervisor_pid or not psutil.pid_exists(host['supervisor_pid']),
                'Failed-live original supervisor still present without a recorded generation')
    else:
        require(not psutil.pid_exists(supervisor['pid']) and not psutil.pid_exists(host['supervisor_pid']),
                'Failed-live original supervisor still present')
    require(all(type(pid) is int and pid > 0 and not psutil.pid_exists(pid) for pid in public_pids),
            'Late-cleanup original run/allocator process still present')
    inventory = runtime_process_inventory(psutil, os.getpid())
    require(not inventory['blockers'], 'Failed-live runtime/CK3/controller still running')
    selected_host = Path(freeze['argv'][4]).resolve()
    for process in psutil.process_iter(['pid', 'name']):
        if (process.info.get('name') or '').lower().startswith(('python', 'pypy')):
            try: arguments = process.cmdline()
            except psutil.NoSuchProcess: continue
            require(not any(is_frozen_host_argument(arg, selected_host) for arg in arguments if arg),
                    'Failed-live frozen host interpreter or redirector still present')
    absent = {name:not (state/'control'/name).exists() for name in ('ck3.json', 'unsafe-cleanup.json')}
    absent['watchdog-*.ready.json'] = not list((state/'control').glob('watchdog-*.ready.json'))
    require(all(absent.values()), 'Failed-live PID/unsafe/watchdog controls remain')
    result = {'mode':'previous-shared-failed-live-resource-closed', 'failure_cleanup':{
        'close':pin(close_path), 'original_evidence':evidence,
        'original_host_exit_code':host_exit['returncode'], 'original_host_wait_proven':True,
        'original_ck3_exit_code':retained['exit_code'], 'actual_retained_os0':False,
        'original_report_status':report['status'], 'original_host_error':report['error'],
        'native_job_cleanup_observed':True, 'normal_close_qualified':False, 'typed_normal_exit_proven':False,
        'business_pass':False, 'release_pass':False, 'control_files_absent':absent,
        'administrative_resource_admission_only':True}, 'actual_process_inventory':inventory}
    if late_facts is not None:
        result['failure_cleanup'].update(late_facts)
    if gui_facts is not None:
        result['failure_cleanup'].update(gui_facts)
    if preserved_facts is not None:
        result['failure_cleanup'].update(preserved_facts)
    if supervisor_facts is not None:
        result['failure_cleanup'].update(supervisor_facts)
    return result


def previous_failed_resource_closure(previous,freeze,close_path,keeper_root,release_path,bus_packet):
    """Admit failed-case resource closure, never native/OS0/normal/PASS credit."""
    evidence={}
    def original(row,expected=None):
        path=Path(row['path']).resolve()
        require(expected is None or path==Path(expected).resolve(),'Failed-resource original path differs')
        require(type(row.get('bytes')) is int and 0<row['bytes']<=1048576 and
                path.stat().st_size==row['bytes'],'Failed-resource receipt exceeds small bound')
        check_pin(path,row);evidence[str(path)]=row
        return read_json(path)
    require(close_path.stat().st_size<=1048576,'Failed-resource closure exceeds small bound')
    bundle=read_json(close_path)
    require(bundle.get('schema')=='lyd.actual-failed-resource-closure.v1' and
            bundle.get('run_id')==freeze['run_id'] and
            Path(bundle.get('keeper_root','')).resolve()==keeper_root.resolve(),
            'Failed-resource closure crossed run/keeper')
    stop=original(bundle['original_stop_proof'],previous/'keeper-stop-proof-001.json')
    late={'original_stop_proof','allocator_original_wait','actual_CAS_release','keeper_actual_exit'}
    require({k:v for k,v in bundle.items() if k not in late}==
            {k:v for k,v in stop.items() if k not in late},'Failed-resource original STOP facts changed')
    require(stop.get('schema')==bundle['schema'] and stop.get('run_id')==freeze['run_id'] and
            stop.get('resource_close_only_not_native_or_normal_acceptance') is True and
            stop.get('original_failure_preserved') is True and stop.get('business_pass') is False and
            stop.get('game_os_exit_zero_qualified') is False and stop.get('normal_gui_quit_qualified') is False and
            stop.get('native_cleanup_qualified') is None and stop.get('native_report_read') is False,
            'Failed-resource closure must preserve unknown native/OS exit and failed business')
    normal=original(bundle['original_normal_close_result'],previous/'case-output/normal-close-result.json')
    require(normal==stop.get('normal_close_result_original') and normal.get('normal_close_qualified') is False and
            normal.get('business_pass') is False,'Failed-resource normal close differs or claims PASS')
    host=original(bundle['original_host_started'],previous/'host-started.json')
    exited=original(bundle['original_host_exit'],previous/'host-original-process-exit.json')
    supervisor=original(bundle['original_host_supervisor'],previous/'host-supervisor-started.json')
    require(host.get('run_id')==freeze['run_id'] and host.get('actual_popen_retained') is True and
            host.get('argv')==freeze['argv'] and exited.get('run_id')==freeze['run_id'] and
            exited.get('pid')==host.get('pid') and exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int and exited['returncode']==0 and
            exited.get('normal_ck3_exit_inferred') is False and exited.get('business_pass') is False and
            bundle.get('original_host_actual_wait_returncode')==0 and
            supervisor.get('pid')==host.get('supervisor_pid'),'Failed-resource original host/supervisor wait differs')
    def waited(row,mode,code):
        value=original(row);argv=value.get('argv',[])
        require(value.get('schema')=='ck3-recorded-actual-command-v1' and
                type(value.get('exit_code')) is int and value['exit_code']==code and
                bool(value.get('finished_at_utc')) and isinstance(argv,list) and
                argv.count('--runtime')==1 and argv.index('--runtime')>0 and
                argv[argv.index('--runtime')-1]==mode,'Failed-resource original public '+mode+' completion differs')
        def argument(flag):
            require(argv.count(flag)==1 and argv.index(flag)+1<len(argv),'Missing public '+flag)
            return argv[argv.index(flag)+1]
        require(argument('--case')==freeze['cell'] and Path(argument('--prepared-case')).resolve()==
                (Path(freeze['state_dir']).parent/'prepared/prepared-case.json').resolve(),
                'Failed-resource public command crossed case/preparation')
        if mode=='run':
            context=read_json(Path(argument('--run-context')))
            require(context.get('schema')=='ck3-mod-acceptance-run-context-v1' and
                    context.get('run_id')==freeze['run_id'] and
                    Path(context.get('run_dir','')).resolve()==previous.resolve(),
                    'Failed-resource public run crossed live context')
        else:
            require(Path(argument('--keeper-output')).resolve()==keeper_root.resolve(),
                    'Failed-resource allocator crossed keeper')
        return argument('--runtime')
    require(bundle.get('original_public_exit_code')==2 and Path(waited(bundle['public_run'],'run',2)).resolve()==
            Path(waited(bundle['allocator_original_wait'],'allocate',0)).resolve(),
            'Failed-resource original public runtime differs')
    keeper=read_json(keeper_root/'report.json')
    keeper_exit=original(bundle['keeper_actual_exit'],previous/'keeper-actual-parent-exit.json')
    require(keeper_exit.get('run_id')==freeze['run_id'] and type(keeper_exit.get('keeper_actual_exit_code')) is int and
            keeper_exit['keeper_actual_exit_code']==0 and keeper_exit.get('keeper_report')==keeper and
            keeper.get('thread_exited') is True and keeper.get('failure') is None and keeper.get('entry_error') is None,
            'Failed-resource keeper original wait/thread differs')
    original(bundle['actual_CAS_release'],release_path)
    release=read_actual_release(release_path);task=release['task'];event=release.get('event',{})
    require(closed_lease(keeper,release,freeze['screen_task']) and task.get('state')=='done' and
            event.get('task_id')==freeze['screen_task'] and event.get('sequence')==task['last_sequence'] and
            event.get('state')=='done' and event.get('resources')==[],'Failed-resource exact CAS completion differs')
    require(isinstance(bus_packet.get('tasks'),list) and
            not any('ck3-screen:acquired' in row.get('resources',[]) for row in bus_packet['tasks']),
            'Failed-resource still has a screen owner')
    import psutil
    keeper_identity=original(bundle['keeper_process'],previous/'keeper-process.json')
    game_path=previous/'case-output/retained-current-process-identity.json'
    game=original(pin(game_path),game_path)
    for label,identity in (('host',host),('keeper',keeper_identity),('CK3',game)):
        require(type(identity.get('pid')) is int and identity['pid']>0 and
                type(identity.get('create_time')) in (int,float),'Failed-resource '+label+' identity missing')
        try:present=psutil.Process(identity['pid']).create_time()==identity['create_time']
        except psutil.NoSuchProcess:present=False
        require(not present,'Failed-resource original '+label+' still present')
    require(type(supervisor.get('pid')) is int and supervisor['pid']>0 and not psutil.pid_exists(supervisor['pid']),
            'Failed-resource original supervisor still present')
    inventory=runtime_process_inventory(psutil,os.getpid())
    require(not inventory['blockers'],'Failed-resource CK3/keeper/controller still running')
    for path in (previous/'frozen-argv.json',keeper_root/'report.json'):
        evidence[str(path.resolve())]=pin(path)
    return {'mode':'previous-shared-failed-attempt-resource-closed','failure_cleanup':{
        'close':pin(close_path),'original_evidence':evidence,'original_host_exit_code':exited['returncode'],
        'original_host_wait_proven':True,'original_ck3_exit_code':None,'actual_retained_os0':False,
        'native_cleanup_qualified':None,'normal_close_qualified':False,'typed_normal_exit_proven':False,
        'business_pass':False,'release_pass':False,'administrative_resource_admission_only':True},
        'actual_process_inventory':inventory}

def require_latest_screen_release(previous,latest_path):
    if latest_path is None:return
    latest=read_actual_release(latest_path);task=latest.get('task',{});old=previous['task']
    require(task.get('state') in ('done','waiting') and task.get('resources')==[] and
        type(task.get('last_sequence')) is int and task['last_sequence']>old['last_sequence'] and
        latest.get('event',{}).get('task_id')==task.get('task_id') and
        latest.get('event',{}).get('sequence')==task['last_sequence'],
        'Intervening latest screen epoch is not actually closed')

def actual_machine_binding(ids: ModuleType) -> MachineBinding:
    """The bootstrap uses the OS machine identity and canonical local ID store.

    An environment-selected machine/ID namespace must never manufacture a
    second first-machine epoch. The opaque OS identifier itself is not saved.
    """
    require(not os.environ.get(ids.MACHINE_ENV) and not os.environ.get(ids.STATE_ROOT_ENV),
            'Shared machine admission refuses machine or ID-state environment overrides')
    token=ids._automatic_machine_token()
    require(token.startswith(('windows-machine-guid:','machine-id:')),
            'Stable OS machine identity is unavailable; hostname alone cannot admit bootstrap')
    machine=ids.derive_machine_id(platform.node(),token)
    require(ids.current_machine_id()==machine,'Actual machine identity differs from canonical allocator')
    state_root=ids.default_state_root().resolve()
    return {'machine_id':machine,'state_root':str(state_root),
            'admission_root':str(state_root/machine/'.shared-runtime-admissions-v1')}

def machine_id_history(binding):
    namespace=Path(binding['state_root'])/binding['machine_id'];rows=[];files=[]
    require(namespace.is_dir(),'Existing canonical machine ID history is required for bootstrap')
    for path in sorted(namespace.glob('*/allocations.jsonl')):
        files.append(pin(path))
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            row=json.loads(line)
            require(row.get('schema')=='xar.ck3-live-run-identity.v1' and
                    row.get('machine_id')==binding['machine_id'],'Canonical ID history crossed machine/schema')
            rows.append(row)
    require(rows,'Canonical machine ID history is empty')
    return rows,files

def shared_bus_history(bus_dir):
    """Read the existing local bus journal, never a new artifacts directory."""
    path=bus_dir/'events.jsonl';events=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        row=json.loads(line)
        require(row.get('schema')=='codex.task_bus.v1' and type(row.get('sequence')) is int,
                'Actual local bus event history is invalid')
        events.append(row)
    shared=[row for row in events if row.get('kind')=='registered' and
            'shared runtime acceptance' in row.get('summary','')]
    return events,shared

def current_screen_absent(lease_repo,bus_dir,bus_sha,audit_dir):
    from ck3_mod_acceptance_keeper import load_lease_module
    module=load_lease_module(lease_repo)
    packet=module.call_bus(lease_repo/'tools/codex_task_bus.py',bus_dir,bus_sha.upper(),
                           'list','--stale-after','600',audit_dir=audit_dir)
    tasks=packet.get('tasks')
    require(isinstance(tasks,list) and all(isinstance(row,dict) for row in tasks),'Actual task list missing')
    require(not any('ck3-screen:acquired' in row.get('resources',[]) for row in tasks),
            'Screen resource is still claimed, including stale/unsafe claims')
    return packet

def validate_legacy_bootstrap(bundle,selection,binding,bus_events,bus_packet,previous_release):
    """Admit a closed legacy profile-MCP scene without calling it a shared run."""
    if bundle.get('schema')=='ck3-mod-acceptance-first-managed-bootstrap-v2':
        from ck3_mod_acceptance_legacy_managed_bootstrap import validate_bootstrap
        return validate_bootstrap(bundle,selection,binding,bus_events,bus_packet,previous_release)
    require(bundle.get('schema')=='ck3-mod-acceptance-first-machine-bootstrap-v1',
            'Explicit first-machine bootstrap bundle schema required')
    require(bundle.get('machine')==binding,'Bootstrap machine/canonical ID state differs from actual OS configuration')
    require(bundle.get('runtime_config')==pin(selection.runtime_path) and
            bundle.get('runtime_manifest')==pin(selection.manifest_path) and
            Path(bundle.get('repo_root','')).resolve()==selection.locations['repo_root'].resolve(),
            'Bootstrap differs from the one selected local common runtime/config/checkout')
    archive=path_at(bundle['legacy_archive_index']['path'],selection.runtime_path.parent)
    check_pin(archive,bundle['legacy_archive_index'])
    require(archive.is_relative_to(selection.locations['repo_root'].resolve()),'Legacy archive index must be tracked in this checkout')
    subprocess.run(['git','ls-files','--error-unmatch','--',str(archive)],cwd=selection.locations['repo_root'],
                   capture_output=True,check=True)
    original=read_json(archive)
    archived={row['source']['path'].replace('\\','/').lower():row['source']
              for row in original.get('evidence_entries',[]) if isinstance(row,dict) and 'source' in row}
    required=('identity','launch','profile','typed_normal_exit','original_handle_exit','keeper_final','client_final','closeout_task')
    refs=bundle.get('legacy_profile_mcp_closure',{})
    require(set(refs)==set(required),'Complete original profile-MCP closure references required')
    values={}
    for key in required:
        row=refs[key];path=Path(row['path']).resolve();check_pin(path,row)
        found=archived.get(str(path).replace('\\','/').lower())
        require(found is not None and found['bytes']==row['bytes'] and found['sha256']==row['sha256'],
                'Legacy closure is not the archived original bytes: '+key)
        values[key]=read_json(path)
    identity,launch=values['identity'],values['launch']
    require(identity.get('machine_id')==binding['machine_id'] and launch.get('run_id')==identity.get('run_id') and
            launch.get('execution_id')==identity.get('execution_id') and launch.get('game_started') is True,
            'Legacy scene is not an actual allocated launch on this machine')
    history,history_files=machine_id_history(binding)
    require(any(row==identity for row in history),'Legacy identity is absent from actual canonical machine history')
    sdk=values['typed_normal_exit'];typed=sdk.get('structuredContent',sdk)
    result=typed.get('result',{});observation=result.get('process_observation',{});native=result.get('native_observation',{})
    handle=values['original_handle_exit'];pid=launch.get('pid')
    require(typed.get('schema')=='ck3.native-profile-receipt.v1' and
        typed.get('profile_sha256')==refs['profile']['sha256'] and typed.get('status')=='process_exit_observed_zero' and
        result.get('schema')=='ck3-normal-exit-process-observation-result-v1' and
        result.get('typed_normal_exit_observed') is True and result.get('process_exit_observed') is True and
        type(result.get('exit_code')) is int and result['exit_code']==0 and
        observation.get('process_identity_verified') is True and observation.get('process_exit_observed') is True and
        observation.get('wait_state')=='signaled' and observation.get('wait_result')==0 and observation.get('errors')==[] and
        type(observation.get('exit_code')) is int and observation['exit_code']==0 and
        type(handle.get('returncode')) is int and handle['returncode']==0 and
        type(pid) is int and pid>0 and pid==handle.get('pid')==observation.get('pid')==native.get('game_pid'),
        'Original typed normal0 and independent retained-parent-handle0 are both required')
    creation=result.get('process_creation_filetime_100ns');pre=result.get('process_preconfirm_pin',{})
    require(type(creation) is int and creation>0 and creation==observation.get('creation_filetime_100ns')==
            native.get('process_creation_filetime_100ns')==pre.get('creation_filetime_100ns') and
            pre.get('pid')==pid and isinstance(pre.get('retained_handle_token'),str) and
            pre['retained_handle_token']==observation.get('retained_handle_token') and
            type(launch.get('process_create_time')) in (int,float) and
            abs(int((launch['process_create_time']+11644473600)*10000000)-creation)<=32,
            'Original normal-exit observation crossed retained process identity/creation')
    require(all(native.get(key) is True for key in ('exact_build_verified','owner_verified','process_identity_verified',
        'source_abi_pins_verified','stock_files_verified','loaded_source_binding_verified')),
        'Original typed exit lacks its own native identity/source guards')
    client=values['client_final'];prior_keeper=values['keeper_final'];closeout=values['closeout_task']
    require(client.get('status')=='CLOSED' and client.get('terminal_exit_requested') is True,
            'Original profile-MCP client has no terminal close receipt')
    require(prior_keeper.get('thread_exited') is True and prior_keeper.get('failure') is None and
            prior_keeper.get('entry_error') is None and prior_keeper.get('task_id')==launch.get('task'),
            'Original legacy keeper closure failed or crossed scene')
    require(Path(previous_release).resolve()==Path(refs['closeout_task']['path']).resolve(),
            '--previous-release must name this archived actual legacy closeout task')
    require(closeout.get('schema')=='codex.task_bus.v1' and closeout.get('task_id')==launch.get('task') and
            closeout.get('state') in ('done','waiting') and closeout.get('resources')==[] and
            type(closeout.get('last_sequence')) is int and closeout['last_sequence']>prior_keeper['last_sequence'],
            'Legacy screen has no actual released closeout snapshot')
    task=closeout['task_id'];matched=[row for row in bus_packet['tasks'] if row.get('task_id')==task]
    require(len(matched)==1 and matched[0].get('resources')==[] and matched[0].get('state') in ('done','waiting') and
            matched[0].get('last_sequence')==closeout['last_sequence'],
            'Fresh independent bus list does not confirm the archived legacy screen release')
    events=[row for row in bus_events if row.get('task_id')==task]
    before=[row for row in events if row['sequence']==prior_keeper['last_sequence']]
    released=[row for row in events if prior_keeper['last_sequence']<row['sequence']<=closeout['last_sequence'] and
              row.get('state') in ('done','waiting') and row.get('resources')==[]]
    require(len(before)==1 and before[0].get('resources')==['ck3-screen:acquired'] and released,
            'Actual durable bus history does not prove the keeper-owned screen was released')
    closed_at=datetime.fromisoformat(closeout['updated_at_utc']);require(closed_at.tzinfo is not None,'Legacy closeout time invalid')
    require(all(datetime.fromisoformat(row['allocated_at_utc'])<=closed_at for row in history),
            'A later local live identity already exists; bootstrap cannot bypass its closure')
    return {'mode':'first-machine-legacy-profile-mcp-closure','legacy_run_id':identity['run_id'],
        'legacy_task':task,'legacy_typed_normal0':True,'legacy_original_parent_handle0':True,
        'legacy_shared_runtime_qualified':False,'legacy_autosave_verified':result.get('autosave_verified'),
        'machine':binding,'archive_index':bundle['legacy_archive_index'],'original_evidence':refs,
        'canonical_id_history':history_files,'release_event':released[0],
        'fresh_release_task':matched[0],'bootstrap':pin(Path(bundle['_bundle_path']))}

def claim_machine_admission(binding: MachineBinding, selection: Selection,
                            args: argparse.Namespace, closure: JsonObject) -> Path:
    """One machine-wide chain; new artifact/runtime directories cannot reset it."""
    import ck3_live_run_id as ids
    from ck3_mod_acceptance_keeper import write_new
    root=Path(binding['admission_root']);root.mkdir(parents=True,exist_ok=True)
    with ids._exclusive_file_lock(root/'chain.lock'):
        if closure['mode']=='previous-shared-allocated-pre-intent-offline-ttl-refused':
            closure.update(revalidate_pre_intent_offline_ttl_admission(selection,args,closure))
        if closure['mode']=='previous-shared-recorder-pre-ready-failure':
            closure.update(revalidate_recorder_pre_ready_admission(selection,args,closure))
        if closure['mode']=='previous-shared-interrupted-owner-quarantined':
            renewed=previous_interrupted_owner_closure(args.previous_live,
                read_json(args.previous_live/'frozen-argv.json'),args.previous_failure_close,
                args.previous_keeper,args.previous_release,selection.state_dir,
                selection.manifest_path_key(selection.manifest['source_root']))
            require(renewed['mode']==closure['mode'],'Interrupted admission changed under original writer lock')
            closure.update(renewed)
        identity=root/'machine.json'
        if identity.exists():require(read_json(identity)==binding,'Existing machine admission identity changed')
        else:write_new(identity,binding)
        records=sorted(path for path in root.glob('[0-9]*') if path.is_dir())
        bootstrap=closure['mode'] in ('first-machine-legacy-profile-mcp-closure','first-machine-legacy-managed-session-closure',FRESH_ADMISSION_MODE)
        if bootstrap:
            if closure['mode']==FRESH_ADMISSION_MODE:
                require_empty_machine_history(binding)
            else:
                require(not records,'First-machine bootstrap is already consumed, including failed/RED attempts')
        elif records:
            previous=read_json(records[-1]/'allocation.json')
            require(Path(previous['live']).resolve()==args.previous_live.resolve() and
                    previous['run_id']==read_json(args.previous_live/'frozen-argv.json')['run_id'],
                    'Previous shared scene is not the latest machine allocation; preserve later RED/unfinished run')
        record=root/(str(len(records)+1).zfill(6));record.mkdir(exist_ok=False)
        write_new(record/'intent.json',{'schema':'ck3-mod-acceptance-machine-admission-intent-v1',
            'at_utc':datetime.now(timezone.utc).isoformat(),'machine':binding,'runtime_config':pin(selection.runtime_path),
            'runtime_manifest':pin(selection.manifest_path),'prepared_case':pin(selection.prepared_path),
            'closure':closure,'status':'CONSUMED_ADMISSION_INTENT_NOT_RUN','business_pass':False})
    return record

def runtime_process_inventory(psutil,caller_pid):
    blockers=[];inspected=[];count=0
    tokens=('screen_keeper.py','screen_lease_entry_','ck3_mod_acceptance_keeper.py','ck3_mod_acceptance_launcher.py',
        'ck3_native_profile_mcp.py','persistent_native_mcp_queue','diagnostic-mcp-client','runtime_harness_','run_ck3_12002_mcp_live.py',
        'run_defense_days_','start_reviewed_fixture.py','start_personally_reviewed_fixture_',
        'run_defense_machine_auto_','run_defense_after_d1_','run_raw_observer_01.py','observe_cold')
    for process in psutil.process_iter(['pid','name']):
        count+=1;name=(process.info.get('name') or '').lower()
        if name=='ck3.exe' or name in ('xar_ck3_bridge_injector.exe','xar_ck3_native_session_watchdog.exe'):
            blockers.append({'pid':process.pid,'name':name})
        elif name.startswith(('python','pypy')) and process.pid!=caller_pid:
            try:argv=process.cmdline();command=' '.join(argv).lower()
            except psutil.NoSuchProcess:continue
            except psutil.AccessDenied as error:raise RuntimeError('Cannot prove old runtime process closed: '+str(process.pid)) from error
            matched=any(token in command for token in tokens) or 'xar_autoplayer.process_watchdog' in argv or (
                any(Path(arg).name.lower()=='ck3_mod_acceptance.py' for arg in argv) and 'run' in argv)
            inspected.append({'pid':process.pid,'name':name,'runtime_controller_match':matched})
            if matched:blockers.append({'pid':process.pid,'name':name,'command':command})
    return {'at_utc':datetime.now(timezone.utc).isoformat(),'scanned_process_count':count,
            'python_controllers_inspected':inspected,'blockers':blockers,
            'process_absence_is_normal_exit_proof':False}

def keeper_command(python,keeper,lease_repo,keeper_root,task,sequence,bus_dir,bus_sha,recording=None):
    argv=[str(python),'-B','-X','utf8',str(keeper),'--repo',str(lease_repo),
        '--root',str(keeper_root.resolve()),'--task',task,'--sequence',str(sequence)]
    if hashlib.sha256(Path(keeper).read_bytes()).hexdigest()==LEGACY_KEEPER_SHA:
        require(Path(bus_dir).resolve()==LEGACY_KEEPER_BUS.resolve() and
                bus_sha.upper()==LEGACY_KEEPER_BUS_SHA,
                'Pinned legacy keeper requires its original installed bus and SHA')
        return argv
    argv += [
        '--bus-dir',str(bus_dir),'--bus-cli',str(lease_repo/'tools/codex_task_bus.py'),
        '--bus-cli-sha256',bus_sha.upper()]
    if recording:
        argv += ['--recorder-config', recording['config']['path'],
                 '--recorder-config-sha256', recording['config']['sha256'],
                 '--recorder-service-sha256', recording['service']['sha256']]
    return argv

def wait_for_keeper_ready(child,keeper_root,live,started,stdout,stderr):
    # write_new creates READY before dump/flush/fsync has finished. Existence
    # alone is not a published JSON object; keep the original process/deadline.
    ready_path=keeper_root/'ready.json'
    last_parse_error=None
    while True:
        polled=child.poll()
        if polled is not None:
            waited=child.wait();stdout.close();stderr.close()
            write_json(live/'keeper-pre-ready-parent-exit.json',{
                'schema':'ck3-keeper-pre-ready-original-parent-exit-v1','run_id':live.name,
                'pid':child.pid,'actual_original_popen_wait':True,
                'actual_poll_exit_code':polled,'keeper_actual_exit_code':waited,
                'ready_absent':not ready_path.exists(),
                'at_utc':datetime.now(timezone.utc).isoformat(),'game_started':False,'business_pass':False})
            raise ValueError('Original keeper failed before READY; preserve actual stderr') from last_parse_error
        if time.monotonic()-started>=30:
            # A persistent malformed file is still an error, never READY. Keep
            # its actual decoder failure rather than hiding it as a timeout.
            raise ValueError('Original keeper did not become READY within existing bound') from last_parse_error
        try:
            return read_json(ready_path)
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError,UnicodeDecodeError) as error:
            last_parse_error=error
        time.sleep(.02)


def _allocate_and_keep_impl(selection,args):
    require(selection.prepared_path and not selection.context,'One prepared unused case and no allocated context required')
    # Validate identity configuration before either machine/profile intent is consumed.
    import ck3_live_run_id as ids
    external_mod=selection.product.get('external_mod',False)
    require(type(external_mod) is bool,'Product external_mod must be a literal boolean')
    mod_key=selection.product.get('runtime_mod_key') or selection.product_key
    ids.validate_mod_key(mod_key,external_mod=external_mod)
    bootstrap_path=getattr(args,'first_machine_bootstrap',None)
    retirement_path=getattr(args,'retire_pre_identity',None)
    failure_path=getattr(args,'previous_failure_close',None)
    fresh_bundle=read_json(bootstrap_path) if bootstrap_path else None
    fresh_machine=bool(fresh_bundle and fresh_bundle.get('schema')==FRESH_BOOTSTRAP_SCHEMA)
    require(not retirement_path or fresh_machine,'Pre-identity retirement requires the explicit first-machine bootstrap')
    for name in (('attempt','keeper_output') if fresh_machine else ('attempt','keeper_output','previous_release')):
        require(getattr(args,name,None),'Allocation missing --'+name.replace('_','-'))
    if bootstrap_path:
        require(not failure_path and not getattr(args,'previous_live',None) and not getattr(args,'previous_keeper',None),
                'First-machine legacy bootstrap and previous shared live/keeper are mutually exclusive')
        if fresh_machine:
            require(not getattr(args,'previous_release',None) and not getattr(args,'latest_screen_release',None),
                    'Fresh-machine bootstrap forbids a fictional predecessor/release')
    else:
        for name in ('previous_live','previous_keeper'):
            require(getattr(args,name,None),'Allocation missing --'+name.replace('_','-'))
    require(re.fullmatch(r'a[0-9]+',args.attempt),'New aNN screen epoch required')
    configured=selection.runtime['allocation']
    root=selection.locations['repo_root'];base=selection.runtime_path.parent
    lease_repo=path_at(configured['lease_repo'],base)
    keeper_ref=configured['screen_keeper'];bus_ref=configured['task_bus']
    keeper=path_at(keeper_ref['path'],base);bus=path_at(bus_ref['path'],base)
    check_pin(keeper,keeper_ref);check_pin(bus,bus_ref)
    recording=configured.get('recording')
    if recording is not None:
        require(set(recording)=={'config','service'},'Shared recording requires exactly config/service pins')
        for recording_ref in recording.values():
            recording_path=path_at(recording_ref['path'],base)
            check_pin(recording_path,recording_ref)
            recording_ref['path']=str(recording_path.resolve())
        require(Path(recording['service']['path'])==keeper.with_name('ck3_mod_acceptance_recorder.py'),
                'Recorder service must be the pinned shared keeper sibling')
        require(hashlib.sha256(keeper.read_bytes()).hexdigest()!=LEGACY_KEEPER_SHA,
                'Legacy keeper does not support explicit recording')
    from ck3_mod_acceptance_recorder import validate_runtime_recording
    validate_runtime_recording(selection.runtime,base,root)
    check_pin(path_at(selection.runtime['reviewed_launcher']['path'],base),selection.runtime['reviewed_launcher'])
    task=configured['task_prefix']+args.attempt
    require(not (bus.parents[1]/'tasks'/(task+'.json')).exists(),'Choose a globally unused screen task')
    require(not args.keeper_output.exists(),'Keeper output already consumed')
    ledger_root=selection.state_dir.parent/'single-use-ledger'
    ledger=ledger_root
    if not fresh_machine:
        require(not ledger.exists(),'Prepared cold input already consumed; preserve ledger')
    preflight=selection.preflight();require(not preflight['blockers'],'Preflight blocked: '+str(preflight['blockers']))
    sys.path.insert(0,str(root/'tools'));import ck3_live_run_id as ids
    binding=actual_machine_binding(ids);machine=binding['machine_id'];state_root=Path(binding['state_root'])
    bus_dir=bus.parents[1]
    events,shared_history=shared_bus_history(bus_dir)
    bus_packet=current_screen_absent(lease_repo,bus_dir,bus_ref['sha256'],
                                    selection.state_dir.parent/'allocation-bus-preflight-audit')
    if bootstrap_path:
        require(not shared_history,'This machine bus already contains a shared allocation; use normal predecessor closure')
        if fresh_machine:
            import psutil
            # The existing environment provider independently compares tasklist with
            # native Toolhelp. Import only the selected immutable common source.
            source=selection.manifest_path_key(selection.manifest['source_root'])
            import_root=source/'ck3_autonomous_player/src'
            if not import_root.is_dir():
                import_root=source/'src'
            sys.path.insert(0,str(import_root))
            try:
                import importlib
                provider=importlib.import_module('xar_autoplayer.environment')
                provider_source=getattr(provider,'__file__',None)
                if not isinstance(provider_source,str) or not Path(provider_source).resolve().is_relative_to(import_root.resolve()):
                    raise ValueError('Fresh dual process provider differs from selected shared source')
                game_inventory=provider.ck3_process_inventory()
            finally:
                sys.path.remove(str(import_root))
            fresh_inventory=create_current_process_observation(
                runtime_inventory=runtime_process_inventory(psutil,os.getpid()),
                ck3_inventory=game_inventory,binding=binding)
            if retirement_path:
                retire_pre_identity_request(retirement_path,binding=binding,product=selection.product_key,
                    case=selection.case['id'],ledger_root=ledger_root,process_inventory=fresh_inventory,
                    bus_events=events,bus_packet=bus_packet,
                    maintenance_closures=parse_bootstrap(fresh_bundle)['maintenance_closures'])
            ledger=fresh_ledger_path(binding,ledger_root)
            require(not ledger.exists(),'Prepared cold input already consumed; preserve ledger')
            closure=json_object(validate_fresh_bootstrap(fresh_bundle,bootstrap_path=bootstrap_path,
                binding=binding,runtime_path=selection.runtime_path,manifest_path=selection.manifest_path,
                repo_root=root,bus_dir=bus_dir,bus_events=events,bus_packet=bus_packet,
                process_inventory=fresh_inventory,previous_live=getattr(args,'previous_live',None),
                previous_keeper=getattr(args,'previous_keeper',None),previous_release=getattr(args,'previous_release',None),
                previous_failure_close=failure_path,latest_screen_release=getattr(args,'latest_screen_release',None)))
        else:
            bundle=read_json(bootstrap_path);bundle['_bundle_path']=str(bootstrap_path.resolve())
            closure=validate_legacy_bootstrap(bundle,selection,binding,events,bus_packet,args.previous_release)
    else:
        previous=args.previous_live.resolve();freeze=read_json(previous/'frozen-argv.json')
        require(freeze.get('identity_allocation',{}).get('machine_id')==machine and
                Path(freeze.get('identity_allocation',{}).get('state_root','')).resolve()==state_root,
                'Previous shared scene belongs to another actual machine/ID state')
        report_reference=None;report_projection=None
        failure_bundle=read_json(failure_path) if failure_path else {}
        failure_schema=failure_bundle.get('schema')
        allocated_unused=failure_schema=='ck3-public-cell-pre-consumption-close-v1'
        allocated_unrun=failure_schema=='ck3-mod-acceptance-allocated-unrun-closure-v1'
        never_launched=failure_schema=='ck3-mod-acceptance-never-launched-closure-v1'
        prelaunch_host=failure_schema=='ck3-mod-acceptance-prelaunch-host-failure-closure-v1'
        supervisor_refused=(failure_schema=='ck3-mod-acceptance-supervisor-admission-refused-closure-v1'
                            or failure_schema in BACKGROUND_CLOSURE_SCHEMAS_V1)
        pre_ready=failure_schema=='ck3-mod-acceptance-pre-ready-closure-v1'
        failed_resource=failure_schema=='lyd.actual-failed-resource-closure.v1'
        failed_live=failure_schema=='ck3-mod-acceptance-failed-live-resource-closure-v1'
        expired_keeper=(failed_live and failure_bundle.get('closure_kind')=='expired-keeper-missing-final-report')
        interrupted_owner=(failed_live and failure_bundle.get('closure_kind')=='interrupted-owner-without-terminal-receipts')
        if allocated_unused or allocated_unrun or never_launched or prelaunch_host or supervisor_refused or pre_ready or failed_resource or failed_live:
            report=None
        elif failure_path:
            report=read_json(previous/'native-report.json')
        else:
            report,report_reference,report_projection=previous_native_cleanup(previous,freeze)
        aborted_wrapper=(allocated_unrun and failure_bundle.get('closure_kind')==
                         'wrapper-aborted-before-launch-without-terminal-waits')
        prior_keeper=predecessor_keeper_report_v1(args.previous_keeper,aborted_wrapper=aborted_wrapper,
            pre_ready=pre_ready,expired_keeper=expired_keeper,interrupted_owner=interrupted_owner)
        # The canonical bus event/task reconstruction is valid for a successful
        # predecessor too; its bytes are verified by read_failed_runtime_release.
        release=read_failed_runtime_release(args.previous_release)
        if supervisor_refused:
            if failure_schema in BACKGROUND_CLOSURE_SCHEMAS_V1:
                from ck3_mod_acceptance_background_refusal import validate_supervisor_refusal
            else:
                from ck3_mod_acceptance_supervisor_refusal import validate_supervisor_refusal
            session_closure=validate_supervisor_refusal(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
        elif allocated_unrun:
            from ck3_mod_acceptance_unrun import validate_allocated_unrun
            session_closure=validate_allocated_unrun(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet,next_state=selection.state_dir)
        elif allocated_unused:
            session_closure=previous_allocated_unused_closure(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
        elif interrupted_owner:
            if not isinstance(failure_path,Path):
                raise ValueError('Actual interrupted closure path required')
            session_closure=previous_interrupted_owner_closure(previous,freeze,failure_path,
                args.previous_keeper,args.previous_release,selection.state_dir,
                selection.manifest_path_key(selection.manifest['source_root']))
        elif failed_live:
            session_closure=previous_failed_live_resource_closure(previous,freeze,failure_path,
                            args.previous_keeper,args.previous_release,bus_packet)
        elif failed_resource:
            session_closure=previous_failed_resource_closure(previous,freeze,failure_path,
                            args.previous_keeper,args.previous_release,bus_packet)
        elif prelaunch_host:
            session_closure=previous_prelaunch_host_failure_closure(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
        elif pre_ready:
            session_closure=previous_pre_ready_closure(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
        elif never_launched:
            session_closure=previous_never_launched_closure(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
        else:
            session_closure=(previous_runtime_failure_closure(previous,freeze,report,failure_path,
                                args.previous_keeper,args.previous_release,bus_packet) if failure_path else
                             previous_session_closure(previous,freeze,report,report_reference))
        if report_projection is not None:
            session_closure['native_cleanup_projection']=report_projection
        require_predecessor_keeper_release_v1(prior_keeper,json_object(release),freeze['screen_task'],
            exceptional_terminal_validated=(pre_ready or expired_keeper or interrupted_owner or
                (aborted_wrapper and session_closure.get('mode')==
                 'previous-shared-allocated-aborted-wrapper-resource-only')))
        require_latest_screen_release(release,args.latest_screen_release)
        closure={**session_closure,'run_id':freeze['run_id'],
                 'previous_live':str(previous),'previous_keeper':str(args.previous_keeper.resolve()),
                 'release':pin(args.previous_release),'machine':binding}
    import psutil
    inventory=(closure.get('actual_process_inventory') if failure_path else
               runtime_process_inventory(psutil,os.getpid()))
    require(not inventory['blockers'],'Previous CK3/keeper/controller still running: '+repr(inventory['blockers']))
    require(subprocess.run(['git','status','--porcelain'],cwd=lease_repo,capture_output=True,check=True).stdout==b'',
            'Original lease anchor must be clean')
    state=selection.state_dir;profile=state/'profile'
    prepared=selection.prepared['preparation']
    require(not (state/'control').exists(),'Played controls already exist')
    require(all(not list((profile/name).rglob('*')) for name in ('logs','save games','run')),'Played logs/saves/run found')
    # Hash the declared prepared profile once; runtime source qualification uses
    # the exact shared manifest/index pins, without another whole-source sweep.
    declared=prepared.get('profile',{}).get('files') or prepared.get('fixtures',{}).get('profile',{}).get('files') or prepared.get('files')
    if 'graphics_cache' in selection.prepared:
        from ck3_mod_acceptance_graphics_cache import profile_enabled,graphics_union
        require(profile_enabled(selection.manifest),'Graphics cache requires shared manifest opt-in')
        declared=graphics_union(declared,selection.prepared['graphics_cache'],profile)
    if not declared:
        policy=read_json(selection.case_path(selection.case['startup']['fixture_start_policy'])) if selection.case['startup']['mode']=='fixture' else None
        declared={relative:{'sha256':sha} for relative,sha in policy['profile_input_sha256'].items()} if policy else None
    observed={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    if declared:
        verify_profile_inventory(declared,observed)
    files={Path(row['path']).resolve():row for row in preflight['checked_inputs']}
    files.update({p:pin(p) for p in (selection.runtime_path,selection.products_path,selection.prepared_path,
        path_at(selection.runtime['reviewed_launcher']['path'],base),path_at(selection.runtime['control_queue']['path'],base),
        bus,keeper,Path(__file__),root/'tools/ck3_live_run_id.py',lease_repo/'tools/codex_task_bus.py',
        lease_repo/'promo/ck3_native_war_ai/integration/screen_bus_lease.py')})
    if recording:
        for row in recording.values():
            files[Path(row['path']).resolve()]=row
        files.update(recording_input_files(selection))
    for row in selection.runtime.get('allocator_overlay',{}).values():
        if isinstance(row,dict) and {'path','bytes','sha256'}<=row.keys():
            check_pin(Path(row['path']),row);files[Path(row['path']).resolve()]=row
    if selection.adapter_path:
        files.update({p:pin(p) for p in sorted(selection.adapter_path.parent.glob('*')) if p.is_file()})
        shared_tools=Path(sys.modules['ck3_mod_acceptance'].__file__).parent
        files.update({p:pin(p) for p in (shared_tools/'ck3_mod_acceptance.py',
            shared_tools/'ck3_mod_acceptance_client.py',shared_tools/'ck3_mod_acceptance_native_day.py',shared_tools/'ck3_mod_acceptance_prepare.py')})
    # Explicit external product peers are exact frozen source inputs, never host/native overrides.
    parent_inputs=selection.prepared.get('case_inputs',{}).get('r08_parent_entry_one_day') if selection.prepared else None
    if parent_inputs is not None:
        index_ref=parent_inputs['bundle_index_pin']; index_path=Path(index_ref['path']).resolve()
        require(0<index_path.stat().st_size==index_ref['bytes']<=65536,'Bounded external parent source index')
        check_pin(index_path,index_ref); index=read_json(index_path)
        require(index.get('schema')=='xar.e04.parent.public-source-bundle.v1','Parent bundle schema')
        files[index_path]=pin(index_path)
        for row in index['files']:
            peer=Path(row['path']).resolve();check_pin(peer,row);files[peer]=pin(peer)
    shared_tools=Path(sys.modules['ck3_mod_acceptance'].__file__).parent
    for name in ('ck3_mod_acceptance_steam_gate.py','steam_offline_state_contract.py','steam_offline_state_probe.py','steam_offline_native_provider_v1.py','steam_offline_native_profiles.py','ck3_mod_acceptance_background_types.py','ck3_mod_acceptance_launcher_protocol_v1.py','ck3_live_run_id.py','ck3_mod_acceptance_graphics_cache.py','ck3_mod_acceptance_fresh_machine_bootstrap.py'):
        peer=shared_tools/name;files[peer]=pin(peer)
    # The CLI checkout and reviewed launcher's immutable source can be distinct.
    # Pin the actual consumer siblings as well as the public CLI import closure.
    actual_launcher=path_at(selection.runtime['reviewed_launcher']['path'],base)
    for name in CONTROL_QUEUE_MODULE_ORDER_V1:
        peer=actual_launcher.with_name(name+'.py').resolve();files[peer]=pin(peer)
    files.update({Path(row['path']):row for row in observed.values()})
    if bootstrap_path:
        rows=([closure['bootstrap'],*closure['maintenance_evidence'],*closure['pre_identity_retirement_evidence']] if fresh_machine else
              [closure['bootstrap'],closure['archive_index'],*closure['original_evidence'].values()])
        for row in rows:
            files[Path(row['path']).resolve()]=row
    if failure_path:
        proof=closure['failure_cleanup']
        for row in [proof['close'],*proof['original_evidence'].values()]:
            files[Path(row['path']).resolve()]=row
        if closure['mode']=='previous-shared-interrupted-owner-quarantined':
            for row in proof['quarantined_controls'].values():
                files[Path(row['path']).resolve()]=row
            helper=Path(__file__).with_name('ck3_mod_acceptance_interrupted.py')
            files[helper]=pin(helper)
    machine_admission=claim_machine_admission(binding,selection,args,closure)
    ledger.mkdir()
    write_json(ledger/'allocation-intent.json',{'status':'CONSUMED_ALLOCATION_INTENT_NOT_RUN','attempt':args.attempt,
        'product':selection.product_key,'case':selection.case['id'],'prepared_case':pin(selection.prepared_path),
        'at_utc':datetime.now(timezone.utc).isoformat(),'machine_admission':str(machine_admission),
        'predecessor_admission':closure,'actual_process_inventory':inventory})
    identity=ids.allocate_live_run_id(mod_key,state_root=state_root,machine_id=machine,external_mod=external_mod)
    live=selection.locations['artifacts_root']/identity.run_id;live.mkdir(parents=True,exist_ok=False);(live/'controls').mkdir()
    normal_exit_binding = allocate_normal_exit_profile_v1(selection, live)
    if normal_exit_binding is not None:
        files.update({Path(row['path']).resolve(): row for row in normal_exit_binding['files']})
    write_json(machine_admission/'allocation.json',{'schema':'ck3-mod-acceptance-machine-allocation-v1',
        'run_id':identity.run_id,'execution_id':identity.execution_id,'live':str(live.resolve()),
        'machine':binding,'runtime_manifest':pin(selection.manifest_path),'keeper_root':str(args.keeper_output.resolve())})
    write_json(live/'predecessor-admission.json',{'closure':closure,'actual_process_inventory':inventory,
        'fresh_bus_no_screen_owner':bus_packet,'machine_admission':str(machine_admission),'business_pass':False})
    files[(live/'predecessor-admission.json').resolve()]=pin(live/'predecessor-admission.json')
    for relative,row in observed.items():
        snapshot=live/'input-snapshots/profile'/relative;snapshot.parent.mkdir(parents=True,exist_ok=True)
        snapshot.write_bytes(Path(row['path']).read_bytes());files[snapshot.resolve()]=pin(snapshot)
    context={'schema':'ck3-mod-acceptance-run-context-v1','run_id':identity.run_id,'run_dir':str(live),
        'keeper_root':str(args.keeper_output.resolve()),'prepared_case':pin(selection.prepared_path),
        'case_inputs':selection.prepared['case_inputs'],'product':selection.product_key,'case':selection.case['id']}
    if normal_exit_binding is not None:
        normal_exit_context: NormalExitAllocatedContextV1 = {'normal_exit_managed_profile': normal_exit_binding['profile']}
        context.update(normal_exit_context)
    context_path=live/'allocated-context.json';write_json(context_path,context)
    actual=Selection(selection.runtime_path,selection.products_path,selection.product_key,selection.case['id'],context_path,selection.prepared_path)
    frozen={'run_id':identity.run_id,'mod_key':identity.mod_key,'execution_id':identity.execution_id,
        'screen_task':task,'cell':selection.case['id'],'argv':actual.argv,'state_dir':str(actual.state_dir),
        'source_root':str(actual.manifest_path_key(actual.manifest['source_root'])),
        'runtime_manifest':pin(actual.manifest_path),'runtime_environment':actual.runtime_environment,
        'identity_allocation':{'machine_id':machine,'state_root':str(state_root)},
        'lease_anchor':str(lease_repo),'previous_session_closed':not fresh_machine,'previous_screen_released':not fresh_machine,
        'predecessor_admission':pin(live/'predecessor-admission.json'),
        'files':{str(path):{k:row[k] for k in ('bytes','sha256')} for path,row in files.items()},
        'launch_requires_fresh_owned_cas_and_background_offline':True,'business_pass':False}
    if fresh_machine:
        frozen['initial_machine_no_predecessor']=True
        if ledger!=ledger_root:
            frozen['single_use_ledger']=str(ledger.resolve())
    if recording:
        running_helper=path_at(selection.runtime['reviewed_launcher']['path'],base).with_name('ck3_mod_acceptance_runtime_inputs.py')
        running_preview=validate_allocated_running_inputs(running_helper,live,json_object(frozen))
        with (live/'running-inputs-prelaunch.json').open('x',encoding='utf-8',newline='\n') as preview_stream:
            json.dump(running_preview,preview_stream,ensure_ascii=False,indent=2,allow_nan=False)
            preview_stream.write('\n')
    write_json(live/'frozen-argv.json',frozen)
    # All slow pin/profile work precedes register. No tool boundary occurs
    # between the actual allocated JSON and the original keeper subprocess.
    result=subprocess.run([str(selection.locations['python']),'-B','-X','utf8',str(bus),
        '--expected-cli-sha256',bus_ref['sha256'].upper(),'register','--task',task,
        '--summary',selection.product_key+' '+selection.case['id']+' shared runtime acceptance',
        '--next-step','Fresh background offline receipt then one shared host launch',
        '--repo',str(lease_repo),'--resource','ck3-screen:acquired'],capture_output=True)
    (live/'screen-registration.json').write_bytes(result.stdout);(live/'screen-registration-stderr.log').write_bytes(result.stderr)
    require(result.returncode==0,'Actual register failed; preserve consumed input and do not replay')
    registration=json.loads(result.stdout);sequence=registration['task']['last_sequence']
    started=time.monotonic()
    keeper_argv=keeper_command(selection.locations['python'],keeper,lease_repo,args.keeper_output,
                               task,sequence,bus_dir,bus_ref['sha256'],recording=recording)
    stdout=(live/'keeper-stdout.log').open('xb');stderr=(live/'keeper-stderr.log').open('xb')
    child=subprocess.Popen(keeper_argv,cwd=root,stdout=stdout,stderr=stderr)
    write_json(live/'keeper-process.json',{'pid':child.pid,'create_time':psutil.Process(child.pid).create_time(),'argv':keeper_argv})
    ready=wait_for_keeper_ready(child,args.keeper_output,live,started,stdout,stderr)
    context['frozen_argv']=pin(live/'frozen-argv.json')
    write_json(live/'ready-context.json',context)
    allocated={'status':'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN','live':str(live),'task':task,'sequence':sequence,
        'keeper_ready':ready,'keeper_pid':child.pid,'keeper_root':str(args.keeper_output.resolve()),
        'register_to_keeper_ready_seconds':time.monotonic()-started,'context':str(live/'ready-context.json'),
        'prepared_case':str(selection.prepared_path),'actual_host_argv':str(live/'frozen-argv.json'),
        'game_started':False,'business_pass':False}
    write_json(ledger/'allocated.json',allocated)
    print(json.dumps(allocated,ensure_ascii=False,indent=2),flush=True)
    # Retain the actual Popen and exit code; process-gone is not OS-exit evidence.
    code=wait_for_allocated_keeper(child,live,args.keeper_output);stdout.close();stderr.close()
    closed={'keeper_actual_exit_code':code,'keeper_report':read_json(args.keeper_output/'report.json'),
            'run_id':identity.run_id,'business_pass':False}
    write_json(live/'keeper-actual-parent-exit.json',closed)
    return {**allocated,**closed}


def allocate_and_keep(selection: Selection, args: argparse.Namespace) -> JsonObject:
    """Typed finite-JSON boundary around the inherited allocation/CAS flow."""
    return json_object(_allocate_and_keep_impl(selection,args))
