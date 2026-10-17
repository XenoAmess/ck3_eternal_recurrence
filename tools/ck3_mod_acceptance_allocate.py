"""One shared allocation followed immediately by the existing screen keeper."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,os,platform,re,subprocess,sys,time
from pathlib import Path
from ck3_mod_acceptance import Selection,path_at,check_pin,pin,read_json
from ck3_mod_acceptance_prepare import write_json

def require(value,message):
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
    original('allocated_context_pin',previous/'allocated-context.json')
    require(ready.get('run_id')==freeze['run_id'] and
            Path(ready['run_dir']).resolve()==previous.resolve() and
            Path(ready['keeper_root']).resolve()==keeper_root.resolve() and
            ready['frozen_argv']==bundle['frozen_argv_pin'], 'Unconsumed READY identity differs')
    keeper=original('keeper_report_pin',keeper_root/'report.json')
    parent=original('keeper_actual_parent_exit_pin',previous/'keeper-actual-parent-exit.json')
    require(parent.get('run_id')==freeze['run_id'] and parent.get('keeper_actual_exit_code')==0 and
            parent.get('keeper_report')==keeper and keeper.get('thread_exited') is True and
            keeper.get('failure') is None,'Actual cooperative keeper wait0 required')
    scene=keeper_root.parent
    refs=bundle['original_process_exit_pins']
    never_attempted=bundle.get('unused_reason')=='coordinator_interrupted_before_first_launch'
    release_stem='screen-release-01'
    if never_attempted:
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
    if not never_attempted:
        trigger=original('observer_trigger_pin',scene/'allocation-pressure-trigger-01.json')
        require(trigger.get('actual_run_id')==freeze['run_id'] and trigger.get('reason')==
                'FINITE_OBSERVER_WINDOW_EXPIRED_NOT_BUSINESS_TIMEOUT', 'Original observer expiry missing')
    require(Path(bundle['release_result_pin']['path']).resolve()==
            Path(refs[release_stem]['path']).with_name(release_stem+'.stdout.log').resolve(),
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

def previous_prelaunch_host_failure_closure(previous,freeze,close_path,keeper_root,release,bus_packet):
    """Release a host that exited before game launch; grant no native or normal-exit credit."""
    bundle=read_json(close_path)
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
    require(host.get('run_id')==freeze['run_id'] and host.get('argv')==freeze['argv'] and
            host.get('actual_popen_retained') is True and
            supervisor.get('pid')==host.get('supervisor_pid') and
            exited.get('run_id')==freeze['run_id'] and exited.get('pid')==host.get('pid') and
            exited.get('actual_original_popen_wait') is True and
            type(exited.get('returncode')) is int and exited['returncode']!=0 and
            exited.get('normal_ck3_exit_inferred') is False and
            (not cache_identity_rejected or exited['returncode']==1) and
            (cache_identity_rejected or any(cause in stderr for cause in (
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
        else:
            require(value.get('schema')=='ck3-recorded-actual-command-v1' and
                    value.get('exit_code')==code and value.get('finished_at_utc'),
                    'Prelaunch original public '+mode+' completion differs')
        require(isinstance(argv,list) and argv.count('--runtime')==1 and
                argv[argv.index('--runtime')-1]==mode and argv.count('--prepared-case')==1 and
                Path(argv[argv.index('--prepared-case')+1]).resolve()==
                    (Path(freeze['state_dir']).parent/'prepared/prepared-case.json').resolve(),
                'Prelaunch original public '+mode+' completion differs')
        if mode=='run':
            require(argv.count('--run-context')==1 and
                    Path(argv[argv.index('--run-context')+1]).is_file(),
                    'Prelaunch reviewed run context missing')
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
            'business_pass':False,'release_pass':False,'absent_game_controls':absent}}

def previous_pre_ready_closure(previous,freeze,close_path,keeper_root,release,bus_packet):
    """Keep historical unknown waits; retain the observed argparse original wait2."""
    bundle=read_json(close_path)
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

def actual_machine_binding(ids):
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

def claim_machine_admission(binding,selection,args,closure):
    """One machine-wide chain; new artifact/runtime directories cannot reset it."""
    import ck3_live_run_id as ids
    from ck3_mod_acceptance_keeper import write_new
    root=Path(binding['admission_root']);root.mkdir(parents=True,exist_ok=True)
    with ids._exclusive_file_lock(root/'chain.lock'):
        identity=root/'machine.json'
        if identity.exists():require(read_json(identity)==binding,'Existing machine admission identity changed')
        else:write_new(identity,binding)
        records=sorted(path for path in root.glob('[0-9]*') if path.is_dir())
        bootstrap=closure['mode']=='first-machine-legacy-profile-mcp-closure'
        if bootstrap:
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
    while not (keeper_root/'ready.json').exists():
        polled=child.poll()
        if polled is not None:
            waited=child.wait();stdout.close();stderr.close()
            write_json(live/'keeper-pre-ready-parent-exit.json',{
                'schema':'ck3-keeper-pre-ready-original-parent-exit-v1','run_id':live.name,
                'pid':child.pid,'actual_original_popen_wait':True,
                'actual_poll_exit_code':polled,'keeper_actual_exit_code':waited,
                'ready_absent':not (keeper_root/'ready.json').exists(),
                'at_utc':datetime.now(timezone.utc).isoformat(),'game_started':False,'business_pass':False})
            raise ValueError('Original keeper failed before READY; preserve actual stderr')
        require(time.monotonic()-started<30,'Original keeper did not become READY within existing bound')
        time.sleep(.02)

def allocate_and_keep(selection,args):
    require(selection.prepared_path and not selection.context,'One prepared unused case and no allocated context required')
    bootstrap_path=getattr(args,'first_machine_bootstrap',None)
    failure_path=getattr(args,'previous_failure_close',None)
    for name in ('attempt','keeper_output','previous_release'):
        require(getattr(args,name,None),'Allocation missing --'+name.replace('_','-'))
    if bootstrap_path:
        require(not failure_path and not getattr(args,'previous_live',None) and not getattr(args,'previous_keeper',None),
                'First-machine legacy bootstrap and previous shared live/keeper are mutually exclusive')
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
    check_pin(path_at(selection.runtime['reviewed_launcher']['path'],base),selection.runtime['reviewed_launcher'])
    task=configured['task_prefix']+args.attempt
    require(not (bus.parents[1]/'tasks'/(task+'.json')).exists(),'Choose a globally unused screen task')
    require(not args.keeper_output.exists(),'Keeper output already consumed')
    ledger=selection.state_dir.parent/'single-use-ledger'
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
        bundle=read_json(bootstrap_path);bundle['_bundle_path']=str(bootstrap_path.resolve())
        closure=validate_legacy_bootstrap(bundle,selection,binding,events,bus_packet,args.previous_release)
    else:
        previous=args.previous_live.resolve();freeze=read_json(previous/'frozen-argv.json')
        require(freeze.get('identity_allocation',{}).get('machine_id')==machine and
                Path(freeze.get('identity_allocation',{}).get('state_root','')).resolve()==state_root,
                'Previous shared scene belongs to another actual machine/ID state')
        report_reference=None;report_projection=None
        failure_schema=read_json(failure_path).get('schema') if failure_path else None
        allocated_unused=failure_schema=='ck3-public-cell-pre-consumption-close-v1'
        never_launched=failure_schema=='ck3-mod-acceptance-never-launched-closure-v1'
        prelaunch_host=failure_schema=='ck3-mod-acceptance-prelaunch-host-failure-closure-v1'
        pre_ready=failure_schema=='ck3-mod-acceptance-pre-ready-closure-v1'
        failed_resource=failure_schema=='lyd.actual-failed-resource-closure.v1'
        if allocated_unused or never_launched or prelaunch_host or pre_ready or failed_resource:
            report=None
        elif failure_path:
            report=read_json(previous/'native-report.json')
        else:
            report,report_reference,report_projection=previous_native_cleanup(previous,freeze)
        prior_keeper=read_json(args.previous_keeper/'report.json') if not pre_ready else None
        # The canonical bus event/task reconstruction is valid for a successful
        # predecessor too; its bytes are verified by read_failed_runtime_release.
        release=read_failed_runtime_release(args.previous_release)
        if allocated_unused:
            session_closure=previous_allocated_unused_closure(previous,freeze,failure_path,
                            args.previous_keeper,release,bus_packet)
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
        if not pre_ready:
            require(closed_lease(prior_keeper,release,freeze['screen_task']),'Previous screen keeper/release is not closed')
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
    for row in selection.runtime.get('allocator_overlay',{}).values():
        if isinstance(row,dict) and {'path','bytes','sha256'}<=row.keys():
            check_pin(Path(row['path']),row);files[Path(row['path']).resolve()]=row
    if selection.adapter_path:
        files.update({p:pin(p) for p in sorted(selection.adapter_path.parent.glob('*')) if p.is_file()})
        shared_tools=Path(sys.modules['ck3_mod_acceptance'].__file__).parent
        files.update({p:pin(p) for p in (shared_tools/'ck3_mod_acceptance.py',
            shared_tools/'ck3_mod_acceptance_client.py',shared_tools/'ck3_mod_acceptance_prepare.py')})
    files.update({Path(row['path']):row for row in observed.values()})
    if bootstrap_path:
        for row in [closure['bootstrap'],closure['archive_index'],*closure['original_evidence'].values()]:
            files[Path(row['path']).resolve()]=row
    if failure_path:
        proof=closure['failure_cleanup']
        for row in [proof['close'],*proof['original_evidence'].values()]:
            files[Path(row['path']).resolve()]=row
    machine_admission=claim_machine_admission(binding,selection,args,closure)
    ledger.mkdir()
    write_json(ledger/'allocation-intent.json',{'status':'CONSUMED_ALLOCATION_INTENT_NOT_RUN','attempt':args.attempt,
        'product':selection.product_key,'case':selection.case['id'],'prepared_case':pin(selection.prepared_path),
        'at_utc':datetime.now(timezone.utc).isoformat(),'machine_admission':str(machine_admission),
        'predecessor_admission':closure,'actual_process_inventory':inventory})
    external_mod=selection.product.get('external_mod',False)
    require(type(external_mod) is bool,'Product external_mod must be a literal boolean')
    mod_key=selection.product.get('runtime_mod_key') or selection.product_key
    identity=ids.allocate_live_run_id(mod_key,state_root=state_root,machine_id=machine,external_mod=external_mod)
    live=selection.locations['artifacts_root']/identity.run_id;live.mkdir(parents=True,exist_ok=False);(live/'controls').mkdir()
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
    context_path=live/'allocated-context.json';write_json(context_path,context)
    actual=Selection(selection.runtime_path,selection.products_path,selection.product_key,selection.case['id'],context_path,selection.prepared_path)
    frozen={'run_id':identity.run_id,'mod_key':identity.mod_key,'execution_id':identity.execution_id,
        'screen_task':task,'cell':selection.case['id'],'argv':actual.argv,'state_dir':str(actual.state_dir),
        'source_root':str(actual.manifest_path_key(actual.manifest['source_root'])),
        'runtime_manifest':pin(actual.manifest_path),'runtime_environment':actual.runtime_environment,
        'identity_allocation':{'machine_id':machine,'state_root':str(state_root)},
        'lease_anchor':str(lease_repo),'previous_session_closed':True,'previous_screen_released':True,
        'predecessor_admission':pin(live/'predecessor-admission.json'),
        'files':{str(path):{k:row[k] for k in ('bytes','sha256')} for path,row in files.items()},
        'launch_requires_fresh_owned_cas_and_offline_direct_review':True,'business_pass':False}
    write_json(live/'frozen-argv.json',frozen)
    # All slow pin/profile work precedes register. No tool boundary occurs
    # between the actual allocated JSON and the original keeper subprocess.
    result=subprocess.run([str(selection.locations['python']),'-B','-X','utf8',str(bus),
        '--expected-cli-sha256',bus_ref['sha256'].upper(),'register','--task',task,
        '--summary',selection.product_key+' '+selection.case['id']+' shared runtime acceptance',
        '--next-step','Fresh offline/nonce review then one shared host launch',
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
    wait_for_keeper_ready(child,args.keeper_output,live,started,stdout,stderr)
    ready=read_json(args.keeper_output/'ready.json')
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
