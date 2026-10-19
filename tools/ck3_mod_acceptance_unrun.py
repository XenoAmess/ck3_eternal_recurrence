"""Close an actual idle, allocated-only public run without host/OS exit credit.

The CLI writes bounded metadata only. Public allocate remains the only allocator.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os
from ck3_mod_acceptance import check_pin, pin, read_json

SCHEMA = 'ck3-mod-acceptance-allocated-unrun-closure-v1'
def need(value, message):
    if not value: raise ValueError(message)
def _read(path):
    path=Path(path);need(path.stat().st_size<=1024*1024,'Small original metadata required')
    return read_json(path)
def _exact(bundle, key, path):
    ref=bundle[key];need(Path(ref['path']).resolve()==Path(path).resolve(),'Unrun original path differs: '+key)
    check_pin(Path(path),ref);return _read(path)

def _allocator_argv(bundle, machine, keeper_stamps):
    """Read one original wait receipt, or the pinned original Popen triplet.

    The triplet has no shell field; only its actual Popen wait is credited.
    Neither receipt form establishes a host or CK3 exit.
    """
    keys=('allocator_intent','allocator_process','allocator_exit')
    combined='allocator_result' in bundle
    need((combined and not any(k in bundle for k in keys))
         or (not combined and all(k in bundle for k in keys)),
         'One complete original allocator evidence form required')
    def original(key):
        ref=bundle[key];check_pin(Path(ref['path']),ref);return _read(ref['path'])
    if combined:
        command=original('allocator_result')
        need(command.get('machine_id')==machine and command.get('exit_code')==0
             and command.get('shell') is False and bool(command.get('finished_at_utc')),
             'Actual original allocator wait0 differs')
        argv=command.get('argv',[])
    else:
        intent,process,exit_row=(original(k) for k in keys)
        pid=process.get('pid');created=process.get('create_time')
        need(all(row.get('machine_id')==machine for row in (intent,process,exit_row))
             and intent.get('stage')=='allocate' and type(pid) is int and pid>0
             and exit_row.get('pid')==pid and exit_row.get('actual_original_popen_wait') is True
             and type(exit_row.get('returncode')) is int and exit_row['returncode']==0
             and intent.get('argv')==process.get('argv'),
             'Actual original allocator intent/process/wait0 differs')
        need(type(created) in (int,float),'Original allocator process creation time missing')
        started=datetime.fromtimestamp(created,timezone.utc)
        intended=datetime.fromisoformat(intent['at_utc']);finished=datetime.fromisoformat(exit_row['completed_at_utc'])
        need(intended.tzinfo is not None and finished.tzinfo is not None
             and intended<=started<=keeper_stamps[0]<=keeper_stamps[-1]<=finished,
             'Original allocator intent/process/wait time differs')
        argv=process.get('argv',[])
    need(isinstance(argv,list) and all(isinstance(x,str) for x in argv),'Original allocator argv missing')
    index=next((i for i,x in enumerate(argv) if Path(x).name=='ck3_mod_acceptance.py'),-1)
    # The public CLI's mode is positional: it accepts both mode-first and
    # global-options-first invocations. Preserve the actual argv unchanged.
    need(index>=0 and argv.count('allocate')==1 and
         (argv[index+1:index+2]==['allocate'] or argv[-1:] == ['allocate']),
         'Actual original allocator command differs')
    return argv

def _release_stages(keeper,cas,done,cas_source,done_source,release,task):
    from ck3_mod_acceptance_allocate import closed_lease
    for value in (cas,done):
        need(value['event']['task_id']==task and value['event']['resources']==[],
             'Wrong allocated-unrun CAS task/resources')
    separate=(cas['event']['kind']=='status' and done['event']['kind']=='completed'
              and cas['event']['sequence']<done['event']['sequence'])
    # A direct CAS completion is one original event. The two proof files must
    # preserve the same canonical bytes/offset/task, rather than mix releases.
    direct=(cas['event']['kind']==done['event']['kind']=='completed'
            and cas['event']['sequence']==done['event']['sequence']
            and cas['event']==done['event'] and cas['task']==done['task']
            and cas_source.get('schema')=='xar-screen-release-canonical-reconstruction-v1'
            and cas_source==done_source)
    need((separate or direct) and keeper['last_sequence']<cas['event']['sequence']
         and done['task']['last_sequence']==done['event']['sequence'] and done['task']['state']=='done'
         and release==done and closed_lease(keeper,done,task),
         'Actual allocated-unrun CAS then admin DONE differs')
    return 'direct-completed' if direct else 'status-then-completed'

def _journal_events(raw,start,release_sequence,done_sequence):
    requested={release_sequence,done_sequence};lines={};offset=start
    for line in raw.splitlines(keepends=True):
        row=json.loads(line)
        if row.get('sequence') in requested:
            need(row['sequence'] not in lines,'Duplicate original CAS/DONE sequence in bounded journal tail')
            lines[row['sequence']]=(offset,line,row)
        offset+=len(line)
    need(len(lines)==len(requested),'Exact original CAS/DONE events absent from bounded journal tail')
    return lines

def validate_allocated_unrun(previous, freeze, close_path, keeper_root, release, bus_packet):
    from ck3_mod_acceptance_allocate import read_failed_runtime_release, runtime_process_inventory
    import ck3_live_run_id as ids
    previous,keeper_root=Path(previous).resolve(),Path(keeper_root).resolve()
    bundle=_read(close_path);machine=ids.current_machine_id();run=freeze['run_id'];task=freeze['screen_task']
    need(bundle.get('schema')==SCHEMA and bundle.get('run_id')==run and bundle.get('machine_id')==machine
         ==freeze.get('identity_allocation',{}).get('machine_id'),'Unrun full run/machine identity differs')
    need(all(bundle.get(k) is False for k in ('host_started','native_session_started','game_started',
         'normal_close_qualified','original_host_exit0','business_pass')),'Allocated-only closure cannot grant game/host credit')
    ready=_exact(bundle,'ready',previous/'ready-context.json')
    _exact(bundle,'frozen',previous/'frozen-argv.json')
    context=_exact(bundle,'allocated_context',previous/'allocated-context.json')
    need(ready['run_id']==context['run_id']==run and Path(ready['run_dir']).resolve()==previous
         and Path(ready['keeper_root']).resolve()==keeper_root and ready['frozen_argv']==bundle['frozen']
         and ready['prepared_case']==context['prepared_case'],'Original allocated-only READY differs')
    check_pin(Path(ready['prepared_case']['path']),ready['prepared_case'])
    keeper=_exact(bundle,'keeper',keeper_root/'report.json')
    parent=_exact(bundle,'keeper_parent_exit',previous/'keeper-actual-parent-exit.json')
    need(keeper.get('task_id')==task and keeper.get('thread_exited') is True and keeper.get('failure') is None
         and keeper.get('entry_error') is None and keeper.get('game_actions') is False
         and parent.get('run_id')==run and parent.get('keeper_actual_exit_code')==0
         and parent.get('keeper_report')==keeper,'Original idle keeper STOP/wait0 unavailable')
    idle=_exact(bundle,'idle_timeout',previous/'allocation-unused-idle-timeout.json')
    stop=bundle['keeper_STOP'];need(Path(stop['path']).resolve()==keeper_root/'STOP','Original STOP crossed keeper')
    check_pin(keeper_root/'STOP',stop)
    need((keeper_root/'STOP').read_text(encoding='utf-8')=='Unused allocation idle deadline; no game/native/normal credit.\n'
         and idle.get('reason')=='NEVER_LAUNCHED_ALLOCATION_IDLE_TIMEOUT' and idle.get('idle_seconds')==600
         and all(idle.get(k) is False for k in ('game_started','native_session_started','normal_close_qualified','business_pass')),
         'Original unused idle STOP differs')
    keeper_ready=_exact(bundle,'keeper_ready',keeper_root/'ready.json')
    stamps=[datetime.fromisoformat(v) for v in (keeper_ready['at_utc'],idle['utc'],keeper['at_utc'])]
    need(all(x.tzinfo is not None for x in stamps) and (stamps[1]-stamps[0]).total_seconds()>=600
         and stamps[2]>=stamps[1],'Original ten-minute unused interval unproven')
    argv=_allocator_argv(bundle,machine,stamps)
    def argument(name):
        need(argv.count(name)==1 and argv.index(name)+1<len(argv),'Original allocator argument missing: '+name)
        return argv[argv.index(name)+1]
    need(Path(argument('--prepared-case')).resolve()==Path(ready['prepared_case']['path']).resolve()
         and Path(argument('--keeper-output')).resolve()==keeper_root,'Actual original allocator wait0 differs')
    stdout=bundle['allocator_stdout'];check_pin(Path(stdout['path']),stdout)
    allocated,end=json.JSONDecoder().raw_decode(Path(stdout['path']).read_text(encoding='utf-8-sig').lstrip())
    need(allocated.get('status')=='ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN' and allocated.get('task')==task
         and Path(allocated['live']).resolve()==previous and Path(allocated['keeper_root']).resolve()==keeper_root,
         'Actual original allocator READY output differs')
    state=Path(freeze['state_dir']).resolve()
    absent={name:not (previous/name).exists() for name in ('launch-intent.json','launch.json','host-started.json',
        'host-supervisor.json','host-supervisor-started.json','supervisor.json','host-original-process-exit.json',
        'native-report.json','native-report.session.log','case-output')}
    absent['state/control']=not (state/'control').exists()
    absent['state/native-session']=not (state/'native-session').exists()
    absent['controls-empty']=(previous/'controls').is_dir() and not any((previous/'controls').iterdir())
    for name in ('save games','logs','run'):
        path=state/'profile'/name;absent['profile/'+name]=not path.exists() or not any(path.iterdir())
    need(all(absent.values()),'Allocated-unrun predecessor has actual host/native/control/Save evidence')
    identity=freeze['identity_allocation'];root=ids.default_state_root().resolve()
    need(Path(identity['state_root']).resolve()==root,'Actual machine counter namespace differs')
    products=Path(argument('--products')).resolve();product_key=argument('--product')
    need(str(products) in freeze['files'],'Original allocated product registry pin missing')
    check_pin(products,freeze['files'][str(products)])
    product=_read(products)['products'][product_key];external_mod=product.get('external_mod',False)
    need(type(external_mod) is bool and product_key==ready['product']
         and (product.get('runtime_mod_key') or product_key)==freeze['mod_key'],
         'Original allocated product namespace differs')
    counter=root/machine/freeze['mod_key']/'counter.json';row=_exact(bundle,'counter',counter)
    need(row.get('machine_id')==machine and row.get('mod_key')==freeze['mod_key']
         and ids.format_run_id(machine,freeze['mod_key'],row['last_sequence'],external_mod=external_mod)==run,
         'Allocated-unrun run is not the latest actual machine/product counter')
    cas=read_failed_runtime_release(Path(bundle['CAS_release']['path']))
    done=read_failed_runtime_release(Path(bundle['admin_done']['path']))
    for key in ('CAS_release','admin_done'):
        check_pin(Path(bundle[key]['path']),bundle[key])
    _release_stages(keeper,cas,done,_read(bundle['CAS_release']['path']),
        _read(bundle['admin_done']['path']),release,task)
    current=[x for x in bus_packet.get('tasks',[]) if x.get('task_id')==task]
    # The canonical list command adds only age_seconds/stale to raw task files.
    # Keep every original field exact, and reject undeclared or invalid extras.
    original=done['task'];snapshot=current[0] if len(current)==1 else {}
    need(len(current)==1 and set(snapshot)==set(original)|{'age_seconds','stale'}
         and {key:snapshot[key] for key in original}==original
         and type(snapshot['age_seconds']) is int and snapshot['age_seconds']>=0
         and snapshot['stale'] is False,'Current allocated-unrun task readback differs')
    import psutil
    inventory=runtime_process_inventory(psutil,os.getpid())
    need(not inventory['blockers'],'Allocated-unrun predecessor process still running: '+repr(inventory['blockers']))
    return {'mode':'previous-shared-allocated-unrun-idle','actual_process_inventory':inventory,
        'failure_cleanup':{'close':pin(close_path),'original_evidence':{k:v for k,v in bundle.items() if k!='counter' and isinstance(v,dict) and 'sha256' in v},
            'absent_launch_native_control_Save':absent,'original_keeper_wait_proven':True,'original_keeper_exit_code':0,
            'host_started':False,'native_session_started':False,'original_host_exit_code':None,
            'original_ck3_exit_code':None,'typed_normal_exit_proven':False,'business_pass':False}}

def _write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return pin(path)
def build_bundle(args):
    import ck3_live_run_id as ids
    from ck3_mod_acceptance_allocate import read_failed_runtime_release, current_screen_absent
    allocator={key:getattr(args,key,None) for key in ('allocator_result','allocator_intent','allocator_process','allocator_exit')}
    need((allocator['allocator_result'] is not None and all(allocator[k] is None for k in allocator if k!='allocator_result'))
         or (allocator['allocator_result'] is None and all(allocator[k] is not None for k in allocator if k!='allocator_result')),
         'Provide --allocator-result or all three --allocator-intent/--allocator-process/--allocator-exit originals')
    live=args.previous_live.resolve();keeper=args.keeper_root.resolve();freeze=_read(live/'frozen-argv.json')
    machine=ids.current_machine_id();taskpath=args.task_bus_root/'tasks'/(freeze['screen_task']+'.json');task=_read(taskpath)
    journal=args.task_bus_root/'events.jsonl';size=journal.stat().st_size;start=max(0,size-65536)
    with journal.open('rb') as f:f.seek(start);raw=f.read(65536)
    if start:
        first=raw.index(b'\n')+1;start+=first;raw=raw[first:]
    lines=_journal_events(raw,start,args.release_sequence,args.done_sequence)
    output=args.output.resolve();need(not output.exists(),'New C metadata output required');output.mkdir(parents=True)
    proofs={}
    for label,sequence in (('CAS_release',args.release_sequence),('admin_done',args.done_sequence)):
        offset,line,event=lines[sequence]
        proofs[label]=_write(output/(label+'.canonical.json'),{'schema':'xar-screen-release-canonical-reconstruction-v1',
            'machine_id':machine,'source_event_stream':str(journal.resolve()),'source_event_byte_offset':offset,
            'source_event_bytes':len(line),'source_event_raw_utf8':line.decode(),'source_event_raw_sha256':hashlib.sha256(line).hexdigest(),
            'event':event,'actual_task_pin':pin(taskpath),'task':task,'release_confirmed_by_canonical_readback':True,'original_stdout_captured':False})
    row={'schema':SCHEMA,'machine_id':machine,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'run_id':freeze['run_id'],
         **{k:False for k in ('host_started','native_session_started','game_started','normal_close_qualified','original_host_exit0','business_pass')},**proofs}
    paths={'ready':live/'ready-context.json','frozen':live/'frozen-argv.json','allocated_context':live/'allocated-context.json',
        'keeper':keeper/'report.json','keeper_parent_exit':live/'keeper-actual-parent-exit.json','keeper_STOP':keeper/'STOP',
        'keeper_ready':keeper/'ready.json','idle_timeout':live/'allocation-unused-idle-timeout.json',
        **{k:v for k,v in allocator.items() if v is not None},'allocator_stdout':args.allocator_stdout,
        'counter':ids.default_state_root()/machine/freeze['mod_key']/'counter.json'}
    row.update({k:pin(v) for k,v in paths.items()});bundle=_write(output/'ALLOCATED-UNRUN.actual.json',row)
    release=read_failed_runtime_release(Path(proofs['admin_done']['path']))
    bus=args.task_bus_root/'bin/codex_task_bus.py'
    packet=current_screen_absent(Path(freeze['lease_anchor']),args.task_bus_root,
        freeze['files'][str(bus.resolve())]['sha256'],None)
    verdict=validate_allocated_unrun(live,freeze,Path(bundle['path']),keeper,release,packet)
    return {'bundle':bundle,'previous_release':proofs['admin_done'],'validation':verdict,'SDK_or_launch':False}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--previous-live',type=Path,required=True)
    p.add_argument('--keeper-root',type=Path,required=True)
    allocator=p.add_mutually_exclusive_group(required=True)
    allocator.add_argument('--allocator-result',type=Path)
    allocator.add_argument('--allocator-intent',type=Path)
    p.add_argument('--allocator-process',type=Path);p.add_argument('--allocator-exit',type=Path)
    p.add_argument('--allocator-stdout',type=Path,required=True);p.add_argument('--task-bus-root',type=Path,required=True)
    p.add_argument('--release-sequence',type=int,required=True);p.add_argument('--done-sequence',type=int,required=True)
    p.add_argument('--output',type=Path,required=True)
    print(json.dumps(build_bundle(p.parse_args()),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
