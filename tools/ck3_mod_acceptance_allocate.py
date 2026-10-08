"""One shared allocation followed immediately by the existing screen keeper."""
from __future__ import annotations
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys,time
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

def allocate_and_keep(selection,args):
    require(selection.prepared_path and not selection.context,'One prepared unused case and no allocated context required')
    for name in ('attempt','keeper_output','previous_live','previous_keeper','previous_release'):
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
    previous=args.previous_live.resolve();freeze=read_json(previous/'frozen-argv.json')
    report=read_json(previous/'native-report.json');prior_keeper=read_json(args.previous_keeper/'report.json')
    release=read_actual_release(args.previous_release)
    require(closed_session(report),'Previous live session has not proved complete cleanup')
    require(native_cleanup_closed(report),'Previous native job/tree/inventory/control closure unproven; no OS0 inference')
    require(closed_lease(prior_keeper,release,freeze['screen_task']),'Previous screen keeper/release is not closed')
    require_latest_screen_release(release,args.latest_screen_release)
    import psutil
    blockers=[]
    tokens=('screen_keeper.py','runtime_harness_','run_ck3_12002_mcp_live.py','run_defense_days_',
        'start_reviewed_fixture.py','start_personally_reviewed_fixture_','run_defense_machine_auto_',
        'run_defense_after_d1_','run_raw_observer_01.py','observe_cold','ck3_mod_acceptance.py run')
    for process in psutil.process_iter(['pid','name']):
        name=(process.info.get('name') or '').lower()
        if name=='ck3.exe':blockers.append({'pid':process.pid,'name':name})
        elif name.startswith(('python','pypy')) and process.pid!=os.getpid():
            try:command=' '.join(process.cmdline()).lower()
            except psutil.NoSuchProcess:continue
            except psutil.AccessDenied as error:raise RuntimeError('Cannot prove old runtime process closed: '+str(process.pid)) from error
            if any(token in command for token in tokens):blockers.append({'pid':process.pid,'name':name,'command':command})
    require(not blockers,'Previous CK3/keeper/controller still running: '+repr(blockers))
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
    ledger.mkdir()
    write_json(ledger/'allocation-intent.json',{'status':'CONSUMED_ALLOCATION_INTENT_NOT_RUN','attempt':args.attempt,
        'product':selection.product_key,'case':selection.case['id'],'prepared_case':pin(selection.prepared_path),
        'at_utc':datetime.now(timezone.utc).isoformat()})
    sys.path.insert(0,str(root/'tools'));import ck3_live_run_id as ids
    machine=ids.current_machine_id();state_root=ids.default_state_root().resolve()
    external_mod=selection.product.get('external_mod',False)
    require(type(external_mod) is bool,'Product external_mod must be a literal boolean')
    mod_key=selection.product.get('runtime_mod_key') or selection.product_key
    identity=ids.allocate_live_run_id(mod_key,state_root=state_root,machine_id=machine,external_mod=external_mod)
    live=selection.locations['artifacts_root']/identity.run_id;live.mkdir(parents=True,exist_ok=False);(live/'controls').mkdir()
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
