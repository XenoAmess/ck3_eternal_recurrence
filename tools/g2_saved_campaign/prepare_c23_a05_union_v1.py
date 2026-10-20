"""A05 finite RAM union; Root alone may adopt the reviewed exact result.

No Task, Game, SDK, export, Git, storage mutation or large-body hash occurs here.
Unchanged small runtime sources may be linked only after exact source readback.
"""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import types

OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_adopt_c23_a03_v1 as original
import prepare_source26_startup_timeout_v1 as startup
import prepare_c23_a05_feeder_v1 as feeder
MACHINE=startup_source_machine='xenoamess-full-tower-eb9d2c1186'
PREP=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T0=PREP/'robert30-v20261019-campaign01/runtime'
T4=T0.with_name('runtime-a04');T5=T0.with_name('runtime-a05')
O=PREP/'p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100'
QUOTE4=(31830,'549440bbc4d1c5153a68dec0d6a5a75b8c7ac10ce33a8607711e60af51b07b19')
INDEX4=(5527,'c12c0c5770b937fe38fe193b703351a613db39c3439f6475bebb3866a81335bc')
UNREGISTER4=(1192,'4aab372211f2b71a67911f90aea54db19a99e5dfa3a11419fd323ae1d768b0b4')
HELPER='root_c23_a03_source_abort_checkpoint_inputs.py'
SOURCE26_PARENT='9b791aae9bb1314162aa5cab923e6cca2892e6d8'
CONTROL_SEQUENCE=10483


def require(ok,why):
    if not ok:raise ValueError('A05 finite union denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def enc(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


def raw(path,limit=1048576):
    path=Path(path);require(path.is_file() and path.stat().st_size<=limit,'bounded named input')
    data=path.read_bytes();require(len(data)<=limit,'bounded complete input');return data


def ref(path):
    path=Path(path).resolve(strict=True);data=raw(path)
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}


def checked(item,limit=1048576):
    data=raw(item['path'],limit)
    require((len(data),sha(data))==(item['bytes'],item['sha256']),'actual input pin differs: '+item['path'])
    return json.loads(data)


def swap(data,before,after,count=1):return startup.swap(data,before,after,count)


def _guard_source():
    return b'''
def _validate_a05_attempt(args,config):
    value=_validate_a04_attempt(args,config)
    reference=value['prior_failure_a04']
    require((reference.get('bytes'),reference.get('sha256'))==(5527,'c12c0c5770b937fe38fe193b703351a613db39c3439f6475bebb3866a81335bc'),'actual A04 failure index required')
    index=_a03_checked(reference)
    require(index.get('machine_id')==MACHINE and index.get('no_SEM_CAP_or_gameplay') is True
        and index.get('first_sequence_not_submitted')==10481 and index.get('Game_business_credit')==0,
        'actual A04 no-gameplay failure boundary required')
    rows={Path(row['path']).name:row for row in index['actual_facts']}
    closed=_a03_checked(rows['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A04.json'])
    game=_a03_checked(rows['ROOT-ACTUAL-GAME-EXIT-C23.json'])
    sdk=_a03_checked(rows['ROOT-P37C23-OWNER-CLOSED.json'])
    task=_a03_checked(next(row for row in index['actual_facts']
        if Path(row['path']).parent.name=='spec-supervisor-a04' and Path(row['path']).name=='CLOSED.json'))
    require(closed.get('machine_id')==game.get('machine_id')==sdk.get('machine_id')==task.get('machine_id')==MACHINE
        and (closed.get('keeper') or {}).get('thread_exited') is True
        and game.get('kernel_signaled') is True and game.get('exit_code')==1
        and (closed.get('owned_cleanup') or {}).get('job_active_processes_final')==0
        and sdk.get('normal') is False and len(sdk.get('processes',[]))==2
        and all(row.get('kernel_exit_observed') is True and row.get('exit_code')==1 for row in sdk['processes'])
        and task.get('job_active_after_stage')==0 and task.get('forced_remaining_cleanup') is False,
        'real forced Game1/SDKdual1 and Task0 A04 closure required')
    removed_ref=value['prior_failure_a04_unregistered']
    require((removed_ref.get('bytes'),removed_ref.get('sha256'))==(1192,'4aab372211f2b71a67911f90aea54db19a99e5dfa3a11419fd323ae1d768b0b4'),'actual A04 unregister pin required')
    removed=_a03_checked(removed_ref)
    if 'stdout' in removed:
        require(removed.get('returncode')==0 and len(removed['stdout'])<=16384,'A04 unregister wrapper failed')
        removed=json.loads(removed['stdout'])
    actual=removed.get('actual') or (removed.get('unregister') or {}).get('actual') or {}
    require(actual.get('absent_after') is True,'actual A04 supervisor Task absence required')
    require(args.attempt_nonce not in {closed.get('attempt_nonce'),closed.get('task_nonce')}
        and args.task_nonce not in {closed.get('attempt_nonce'),closed.get('task_nonce')},'independent A05 nonces required')
    return value

'''


def build_sources():
    """Read actual A04 complete86; return a new finite source map in RAM."""
    quote_raw=raw(O/'A04-ROOT-QUOTE02.json')
    require((len(quote_raw),sha(quote_raw))==QUOTE4,'exact actual A04 source plan')
    rows=json.loads(quote_raw)['source_rows'];require(len(rows)==86,'actual85+dynamicCLI closure')
    values={};previous={}
    for row in rows:
        path=Path(row['path']);require(path.parent==T4,'old source outside A04 root')
        data=raw(path);require((len(data),sha(data))==(row['bytes'],row['sha256']),'actual old frozen source differs')
        values[path.name]=data;previous[path.name]=ref(path)
    host=startup.compose_host(raw(OWN/'canonical_native_provider_chain_v1.py'))
    values['root_c23_canonical_outer.py']=startup.compose_outer(values['root_c23_canonical_outer.py'],host)
    for name,data in tuple(values.items()):values[name]=data.replace(b'C23-A04',b'C23-A05')
    supervisor=values['root_native30_supervisor_c23.py']
    supervisor=swap(supervisor,"args.attempt=='a04'","args.attempt=='a05'")
    supervisor=swap(supervisor,"value.get('attempt_id')=='a04'","value.get('attempt_id')=='a05'")
    supervisor=swap(supervisor,'choices=("a04",)','choices=("a05",)')
    supervisor=swap(supervisor,'"attempt_id":"a04"','"attempt_id":"a05"',2)
    supervisor=swap(supervisor,'_validate_a04_attempt(args, config)','_validate_a05_attempt(args, config)')
    marker=b'def main(args):'
    require(supervisor.count(marker)==1,'single original supervisor entry')
    values['root_native30_supervisor_c23.py']=supervisor.replace(marker,_guard_source()+marker)
    helper=values[HELPER]
    helper=swap(helper,'xar.source25.canonical-git-anchor/v1','xar.source26.canonical-git-anchor/v1')
    helper=swap(helper,'6b55531b1d3a44ee73ab13ea40132556030f682e',SOURCE26_PARENT)
    helper=helper.replace(b'Source25',b'Source26').replace(b'Source24 parent',b'Source25 parent')
    values[HELPER]=helper
    queue=values['root_p37c23_sdk_queue.py']
    values['root_p37c23_sdk_queue.py']=swap(queue,'admission_getter=lambda queue: None',
        "admission_getter=lambda queue: queue._normal_cold['admission'].get('control_timing')")
    feeds,feed_review=feeder.build_sources(source_runtime=T4)
    for name,data in feeds.items():
        require(values[name]==data,'feeder differs outside its independent exact seam')
    for name,data in values.items():compile(data,name,'exec')
    extras={'creator-tools/g2_saved_campaign/canonical_native_provider_chain_v1.py':host}
    for name in ('mcp_owned_stdio_binding_v1.py','sdk_process_custody.py'):
        extras['creator-tools/g2_saved_campaign/'+name]=raw(OWN/name)
    return {**values,**extras},{'schema':'xar.C23-A05-finite-source-map/v1','machine_id':MACHINE,
        'source_count':len(values),'private_creator_count':3,'predecessors':previous,'feeder':feed_review,
        'per_startup_wait_seconds':120,'startup_max':300,'steady_recv_seconds':10,
        'control_probe':{'control_sequence':CONTROL_SEQUENCE,'cycle_budget':30,'mismatch_skips_probe':True},
        'Source26_anchor_schema':'xar.source26.canonical-git-anchor/v1','Source26_parent':SOURCE26_PARENT}


def merge_into(destination,items,label):
    """One normalized path union. Equal overlap is recorded; conflict is fatal."""
    overlaps=[]
    for path,data in items.items():
        path=Path(path).resolve();require(type(data) is bytes,'complete byte output required')
        if path in destination:
            require(destination[path]==data,'conflicting duplicate output: '+str(path));overlaps.append(str(path))
        else:destination[path]=data
    return {'scope':label,'equal_overlap':overlaps}


def state_guard():
    """Only stat/bounded prefix and small pending metadata; never a large hash."""
    pre=checked(ref(T0/'ROOT-C23-COLD-PRELAUNCH.json'))
    expected=[(pre['driver_state']['path'],38356800,1792449305494327000,3377699730280567),
        (pre['checkpoint']['path'],116203629,1792449304215108900,281474988852756)]
    report=[]
    for path,size,mtime,inode in expected:
        p=Path(path);s=p.stat()
        require((s.st_size,s.st_mtime_ns,s.st_ino)==(size,mtime,inode),
            'protected large input stat changed; Root must review and selectively rehash')
        report.append({'path':str(p),'bytes':size,'mtime_ns':mtime,'FileID':str(inode),'volume':str(s.st_dev)})
    for item in pre['sidecars']:
        value=checked(item,32768)
        require('pending' not in value or value['pending'] is None,'unresolved saved-sidecar pending')
    with Path(pre['driver_state']['path']).open('rb') as stream:prefix=stream.read(4096)
    decoder=json.JSONDecoder();start=prefix.index(b'"last_checkpoint":')+len(b'"last_checkpoint":')
    checkpoint,_=decoder.raw_decode(prefix[start:].decode('utf-8'))
    require(checkpoint==pre['checkpoint'],'bounded real Driver last_checkpoint differs')
    require(T4.joinpath('state').resolve()==T0.joinpath('state').resolve(),'A04 state alias differs')
    return {'machine_id':MACHINE,'large_files':report,'Driver_prefix_bytes_read':4096,
        'large_input_hash_bytes_read':0,'small_pending_settled':True,'last_checkpoint_matches':True,
        'dead_process_memory_dirty_flag':'UNOBSERVABLE_NOT_CLAIMED','future_alias':str(T5/'state'),
        'exact_target':str(T0/'state')}


def _module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module);return module


def compose(plan,*,display_values,display_review):
    """Return exact unified files and quote. Inputs are actual pinned Root refs.

    display_values is the full reviewed eighteen-leaf RAM graph projected by
    the display producer, including its static provider and closure amendment.
    compact_base_ref must be the actual policy-free Source26 export, not a
    guessed commit or future digest. Source and display plans merge once.
    """
    require(plan.get('schema')=='xar.C23-A05-union-prepare-input/v1' and plan.get('machine_id')==MACHINE
        and plan.get('execution_owner')=='Root' and plan.get('root_direct_execution_release') is True,
        'explicit Root actual plan')
    at=plan['observed_at_utc'];deadline=datetime.fromisoformat('2026-10-20T06:30:00+00:00')
    require(datetime.now(timezone.utc)<deadline,'storage review deadline')
    require(not T5.exists(),'new exact A05 runtime root must be absent')
    for key in ('attempt_nonce','task_nonce'):
        require(re.fullmatch('[0-9a-f]{32}',str(plan.get(key))) is not None,'independent explicit nonce')
    require(plan['attempt_nonce']!=plan['task_nonce'],'attempt and Task nonce differ')
    source,source_review=build_sources();state=state_guard()
    full=checked(plan['full_storage_ref'],32768);live=checked(plan['live_storage_ref'],32768)
    require(full==live and full['machine_id']==MACHINE and full['status']=='ADMITTED'
        and plan['full_storage_ref']['sha256']==plan['live_storage_ref']['sha256']
        and full['review_at_utc']==deadline.isoformat(),'one actual canonical full and review')
    base=checked(plan['compact_base_ref'],524288)
    require('canonical_preload_policy' not in base and base['machine_id']==MACHINE,'actual policy-free Source26 BASE')
    anchor_ref=base['source26_canonical_anchor'];anchor=checked(anchor_ref,65536)
    require(anchor.get('schema')=='xar.source26.canonical-git-anchor/v1' and anchor.get('parent')==SOURCE26_PARENT
        and anchor.get('execution_owner')=='Root' and anchor.get('root_direct_execution_release') is True,
        'actual Root canonical Source26 anchor')
    require(base['business_source_commit']==anchor['commit'],'actual SDK/anchor commit')
    source_rows_raw=json.dumps(base['files'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    require({'bytes':len(source_rows_raw),'sha256':sha(source_rows_raw)}==anchor['complete_rows_JSON']
        and len(base['files'])==anchor['source_file_count'] and sum(r['bytes'] for r in base['files'])==anchor['source_bytes'],
        'complete canonical rows preserved')
    checked(anchor['source_plan'],131072)
    outputs={};overlaps=[]
    overlaps.append(merge_into(outputs,{T5/name:data for name,data in source.items()},'runtime-source'))
    overlaps.append(merge_into(outputs,{T5/name:data for name,data in display_values.items()},'complete-display'))
    require(len(display_values)==18 and (T5/'ROOT-DECISION-TEXT-PROVIDER-C23.json') in outputs,'complete display/static provider required')
    def put(name,value):
        data=enc(value);path=T5/name
        merge_into(outputs,{path:data},'metadata');return original.target_ref(path,data)
    oldfreeze=checked(ref(T4/'ROOT-FINAL-SDK-FREEZE-P37C23-A04.json'),524288)
    policy=checked(oldfreeze['canonical_preload_policy'],32768)
    dep=raw(policy['dependency_sources']['path']);dep_path=T5/'DEPENDENCY-SOURCES-C23-A05.json'
    merge_into(outputs,{dep_path:dep},'dependency source pins')
    policy['dependency_sources']=original.target_ref(dep_path,dep)
    policy['creator_tools_root']=str(T5/'creator-tools');policy['sdk_source_root']=base['source_root']
    replaced=[]
    for path,digest in policy['entry_source_pins']:
        p=Path(path)
        target=T5/p.name if p.parent==T4 else T5/'creator-tools/g2_saved_campaign'/p.name
        require(target in outputs,'complete44 source missing from union')
        replaced.append([str(target),sha(outputs[target])])
    require(len(replaced)==44 and len({x for x,h in replaced})==44,'complete44 closure')
    policy['entry_source_pins']=replaced
    six=[row for row in replaced if Path(row[0]).name in original.controls.SIX]
    require(len(six)==6,'canonical six exact subset');policy['canonical_entry_source_pins']=six
    for item in policy['external_import_source_pins'].values():
        name=Path(item['path']).name;target=T5/name
        require(target in outputs,'external import missing from union')
        item.update(original.target_ref(target,outputs[target]))
    policy_ref=put('ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json',policy)
    final={**base,'attempt_id':'a05','canonical_preload_policy':policy_ref}
    final_ref=put('ROOT-FINAL-SDK-FREEZE-P37C23-A05.json',final)
    native=checked(ref(T4/'ROOT-NATIVE30-NATIVE-PIN-C23-A04.json'))
    native.update(observed_at_utc=at,storage_admission=plan['full_storage_ref'])
    native_ref=put('ROOT-NATIVE30-NATIVE-PIN-C23-A05.json',native)
    for name in original.META_NAMES:
        value=checked(ref(T4/name.replace('-C23.','-C23-A04.')))
        if name=='ROOT-CLEAN-SOURCE-FROZEN-C23.json':
            value.update(sdk_freeze=final_ref,at_utc=at,observed_at_utc=at,business_source_commit=anchor['commit'])
        elif name=='ROOT-LAUNCH-CONFIG-C23.json':
            value.update(SDK_freeze_sha256=final_ref['sha256'],storage_admission=str(T5/'STORAGE-ADMISSION.json'),
                storage_admission_sha256=plan['full_storage_ref']['sha256'],full_storage_view=plan['full_storage_ref'],
                review_at_utc=full['review_at_utc'],observed_at_utc=at,business_source_commit=anchor['commit'])
            value['cold_attempt'].update(attempt_id='a05',nonce=plan['attempt_nonce'],task_nonce=plan['task_nonce'],
                prior_failure_a04=ref(O/'A04-FAILED-CLOSED-INDEX.json'),prior_failure_a04_unregistered=ref(O/'SUPERVISOR-A04-UNREGISTER.json'))
            env=value['Game_process_environment']
            env['XAR_CK3_DECLARATIONS_CANDIDATE_POLICY_FILE']=str(T5/'cb-candidate-policy.txt')
            env['XAR_CK3_DECLARATIONS_PROFILE_JSONL']=str(T5/'profile-output/declarable-query.jsonl')
        elif name=='ROOT-NATIVE30-SDK-BINDING-C23.json':
            value.update(source_root=base['source_root'],sdk_freeze_sha256=final_ref['sha256'],native_session_pin=native_ref,observed_at_utc=at)
        else:value.update(keeper_source=str(T5/'root_screen_bus_lease_c23.py'),source_cli=str(T5/'codex_task_bus_c15.py'),
            full_storage_view=plan['full_storage_ref'],source_review_at_utc=full['review_at_utc'],observed_at_utc=at,at=at)
        put(name.replace('-C23.','-C23-A05.'),value)
    classifier=checked(ref(T4/'ROOT-P37C23-CLASSIFIER-PIN.json'))
    classifier.update(source=str(T5/'root_p37c11_prisoner_epoch_classifier.py'),observed_at_utc=at)
    put('ROOT-P37C23-CLASSIFIER-PIN.json',classifier)
    for name in ('ROOT-C23-COLD-PRELAUNCH.json','NEXT-SEQUENCE-P37.json','cb-candidate-policy.txt'):
        merge_into(outputs,{T5/name:raw(T4/name)},'unchanged cold metadata')
    merge_into(outputs,{T5/'STORAGE-ADMISSION.json':raw(plan['full_storage_ref']['path'],32768)},'single canonical full')
    config_path=T5/'ROOT-LAUNCH-CONFIG-C23-A05.json'
    owner=original.load(original.ref(OWN/'interactive_task_owner_v1.py'),'_a05_original_owner_RAM')
    taskroot=O/'tasks/spec-supervisor-a05'
    require(not taskroot.exists(),'independent once-only A05 Task root')
    spec=original._ram_spec(owner,root=taskroot,stage=T5/'root_native30_supervisor_c23.py',stage_raw=source['root_native30_supervisor_c23.py'],
        bootstrap=T0/'interactive_task_owner_c17.py',cwd=T5,screen=Path(plan['screen_admission_path']),
        clean=T5/'ROOT-CLEAN-SOURCE-FROZEN-C23-A05.json',config=config_path,attempt=plan['attempt_nonce'],task=plan['task_nonce'],
        dependency_root=Path(policy['dependency_root']))
    spec['stage_args'][spec['stage_args'].index('--attempt')+1]='a05'
    merge_into(outputs,{taskroot/'SPEC.json':(json.dumps(spec,ensure_ascii=False,indent=2)+'\n').encode()},'once supervisor SPEC')
    # No namespace is installed until all paths have been unified and priced.
    rows=[];fresh_allocation=0;links=0
    for path,data in sorted(outputs.items()):
        require(not path.exists(),'create-only output already exists: '+str(path))
        previous=None
        if path.is_relative_to(T5):
            relative=path.relative_to(T5);candidate=T4/relative
            if candidate.is_file() and candidate.stat().st_size<=1048576 and raw(candidate)==data:previous=ref(candidate)
        allocation=0 if previous else ((len(data)+4095)//4096)*4096
        fresh_allocation+=allocation;links+=previous is not None
        rows.append({**original.target_ref(path,data),'mode':'hardlink' if previous else 'create-only','source':previous,
            'allocation_upper':allocation})
    future_owner=65536;probe_peak=131072;atomic=max(((len(b)+4095)//4096)*4096 for b in outputs.values());fs=131072
    quote={'schema':'xar.C23-A05-complete-union-quote/v1','machine_id':MACHINE,'observed_at_utc':at,
        'status':'RAM_ONLY_NOT_ADOPTED','producer':ref(__file__),'sources':source_review,'display':display_review,
        'actual_state_guard':state,'files':rows,'equal_duplicate_groups':overlaps,'unique_files':len(rows),
        'logical_bytes':sum(map(len,outputs.values())),'fresh_allocation_upper':fresh_allocation,'immutable_hardlinks':links,
        'max_atomic_copy':atomic,'future_owner_metadata_upper':future_owner,'control_probe_atomic_peak':probe_peak,
        'intent_receipt_and_FS_upper':fs,'prepare_peak_upper':fresh_allocation+atomic+future_owner+probe_peak+fs,
        'full_storage_ref':plan['full_storage_ref'],'review_at_utc':full['review_at_utc'],
        'canonical_entry_source_pins':six,'all_entry_rows':44,
        'prerequisite_directories':[str(T5/'recordings')],
        'state_junction':{'path':str(T5/'state'),'exact_target':str(T0/'state'),'must_verify_same_FileID':True},
        'adoption_order':'require all absent; create one root; create recordings; verify state alias; write each unique file once; readback all pins; do not Run Task',
        'static_provider_is_input_not_attempt_output':str(T5/'ROOT-DECISION-TEXT-PROVIDER-C23.json'),
        'gate':'after actual new Game/map/recording and original verify_segment; never during this preparation',
        'control_probe_sequence':CONTROL_SEQUENCE,'probe_only_after_actual_SEM_CAP':True,
        'body_reads_Driver_SAVE_hash':0,'Task_Game_RPC_calls':0}
    return outputs,quote


def cold_owner(inputs):
    """Reuse original saved-seed/current-recording validator after real A05 frames."""
    path=OWN/'prepare_c23_a03_cold_owner_metadata_v1.py'
    source=raw(path).decode('utf-8').replace('C23-A03','C23-A05').replace('source25_canonical_anchor','source26_canonical_anchor')
    source=source.replace("semantic=ref(runtime/'p37-responses/10479-1-result.json',262144)",
        "semantic=ref(DEFAULT_OLD_RUNTIME/'p37-responses/10479-1-result.json',262144)")
    source=source.replace("runtime/'ROOT-P37C20-CLASSIFIER-PIN.json'","runtime/'ROOT-P37C23-CLASSIFIER-PIN.json'")
    source=source.replace("'control_timing_not_enabled':True}",
        "'control_timing_not_enabled':False,'control_timing':{'schema':'xar.ck3.queue-control-timing-admission/v1','enabled':True,'machine_id':MACHINE,'control_sequence':10483,'cycle_budget':30}}")
    scope={'__file__':str(path),'__name__':'_a05_existing_cold_metadata_RAM'}
    exec(compile(source,'A05-finite-cold-metadata-RAM','exec'),scope)
    final=ref(T5/'ROOT-FINAL-SDK-FREEZE-P37C23-A05.json');policy=checked(final)['canonical_preload_policy']
    scope.update(DEFAULT_RUNTIME=T5,DEFAULT_OLD_RUNTIME=T0,FINAL_PIN=(final['bytes'],final['sha256']),
        POLICY_PIN=(policy['bytes'],policy['sha256']),FULL_SHA=inputs['full_storage_ref']['sha256'])
    return scope['compose'](inputs)
