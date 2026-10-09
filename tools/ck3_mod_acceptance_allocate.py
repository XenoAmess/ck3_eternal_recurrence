"""One shared allocation followed immediately by the existing screen keeper."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,os,platform,re,subprocess,sys,time
from pathlib import Path
from ck3_mod_acceptance import Selection,path_at,check_pin,pin,read_json
from ck3_mod_acceptance_prepare import write_json

def require(value,message):
    if not value:raise ValueError(message)

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

def previous_session_closure(previous,freeze,report):
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
        'report':pin(previous/'native-report.json'),'host_started':pin(started_path),'host_exit':pin(exit_path),
        'safe_launch_error':session['error'],'control_files_absent':absent,
        'control_observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'original_cleanup_ok':False,'original_ck3_exit_code':None,'original_job_active_processes_final':None,
        'typed_normal_exit_proven':False,'business_pass':False}}

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

def allocate_and_keep(selection,args):
    require(selection.prepared_path and not selection.context,'One prepared unused case and no allocated context required')
    bootstrap_path=getattr(args,'first_machine_bootstrap',None)
    for name in ('attempt','keeper_output','previous_release'):
        require(getattr(args,name,None),'Allocation missing --'+name.replace('_','-'))
    if bootstrap_path:
        require(not getattr(args,'previous_live',None) and not getattr(args,'previous_keeper',None),
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
        report=read_json(previous/'native-report.json');prior_keeper=read_json(args.previous_keeper/'report.json')
        release=read_actual_release(args.previous_release)
        session_closure=previous_session_closure(previous,freeze,report)
        require(closed_lease(prior_keeper,release,freeze['screen_task']),'Previous screen keeper/release is not closed')
        require_latest_screen_release(release,args.latest_screen_release)
        closure={**session_closure,'run_id':freeze['run_id'],
                 'previous_live':str(previous),'previous_keeper':str(args.previous_keeper.resolve()),
                 'release':pin(args.previous_release),'machine':binding}
    import psutil
    inventory=runtime_process_inventory(psutil,os.getpid())
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
    if not declared:
        policy=read_json(selection.case_path(selection.case['startup']['fixture_start_policy'])) if selection.case['startup']['mode']=='fixture' else None
        declared={relative:{'sha256':sha} for relative,sha in policy['profile_input_sha256'].items()} if policy else None
    observed={p.relative_to(profile).as_posix():pin(p) for p in sorted(profile.rglob('*')) if p.is_file()}
    if declared:
        require(set(observed)==set(declared) and all(observed[k]['sha256']==declared[k]['sha256'] for k in declared),
                'Cold profile changed after preparation')
    files={Path(row['path']).resolve():row for row in preflight['checked_inputs']}
    files.update({p:pin(p) for p in (selection.runtime_path,selection.products_path,selection.prepared_path,
        path_at(selection.runtime['reviewed_launcher']['path'],base),path_at(selection.runtime['control_queue']['path'],base),
        bus,keeper,Path(__file__),root/'tools/ck3_live_run_id.py',lease_repo/'tools/codex_task_bus.py',
        lease_repo/'promo/ck3_native_war_ai/integration/screen_bus_lease.py')})
    if selection.adapter_path:
        files.update({p:pin(p) for p in sorted(selection.adapter_path.parent.glob('*')) if p.is_file()})
        files.update({p:pin(p) for p in (Path(__file__).with_name('ck3_mod_acceptance.py'),
            Path(__file__).with_name('ck3_mod_acceptance_client.py'),Path(__file__).with_name('ck3_mod_acceptance_prepare.py'))})
    files.update({Path(row['path']):row for row in observed.values()})
    if bootstrap_path:
        for row in [closure['bootstrap'],closure['archive_index'],*closure['original_evidence'].values()]:
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
    keeper_argv=[str(selection.locations['python']),'-B','-X','utf8',str(keeper),'--repo',str(lease_repo),
        '--root',str(args.keeper_output.resolve()),'--task',task,'--sequence',str(sequence)]
    stdout=(live/'keeper-stdout.log').open('xb');stderr=(live/'keeper-stderr.log').open('xb')
    child=subprocess.Popen(keeper_argv,cwd=root,stdout=stdout,stderr=stderr)
    write_json(live/'keeper-process.json',{'pid':child.pid,'create_time':psutil.Process(child.pid).create_time(),'argv':keeper_argv})
    while not (args.keeper_output/'ready.json').exists():
        require(child.poll() is None,'Original keeper failed before READY; preserve actual stderr')
        require(time.monotonic()-started<30,'Original keeper did not become READY within existing bound')
        time.sleep(.02)
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
    code=child.wait();stdout.close();stderr.close()
    closed={'keeper_actual_exit_code':code,'keeper_report':read_json(args.keeper_output/'report.json'),
            'run_id':identity.run_id,'business_pass':False}
    write_json(live/'keeper-actual-parent-exit.json',closed)
    return {**allocated,**closed}
