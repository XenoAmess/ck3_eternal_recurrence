"""A03 exact RAM quote and one admitted source/metadata/SPEC adoption.

No Task Scheduler operation, game launch, screen operation, Driver/SAVE body
read, storage replacement, or automatic retry exists in this entry.
"""
import argparse
import ast
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys

OWN=Path(__file__).resolve().parent
REPO=OWN.parents[1]
sys.path.insert(0,str(OWN))
import prepare_c23_a03_full_enabled_cold_controls_v1 as controls
MACHINE=controls.MACHINE
MAX=1048576
OLD_POLICY=(18570,'f57c8c82a948f1833f1992d0f1c87d22df0e22ce8ae9a2af53b64a874303d621')
OLD_FREEZE=(387272,'84d59b305496644c8592608cf29d33db20397fe76cc92d32128ad59b7299da03')
META_NAMES=('ROOT-CLEAN-SOURCE-FROZEN-C23.json','ROOT-LAUNCH-CONFIG-C23.json',
 'ROOT-NATIVE30-SDK-BINDING-C23.json','ROOT-PROMO-KEEPER-SOURCE-READY-C23.json')
META_SHAS={
 'ROOT-CLEAN-SOURCE-FROZEN-C23.json':'f8e9ab020b55dbb1031249859ee6c02b0677361b65c909908dfbb8a867614599',
 'ROOT-LAUNCH-CONFIG-C23.json':'0d3178de608fa393e414e70abed445bdf75034b70dc437ca63ead7fd6f46cda4',
 'ROOT-NATIVE30-SDK-BINDING-C23.json':'134412962929c165cc45eb9fc00cdd026f2c3e1d4c4dfe8ae0df8155dbd4e807',
 'ROOT-PROMO-KEEPER-SOURCE-READY-C23.json':'47c613e73dfb46e0828db5170e409b248713d4f672c760eccf1698c8216c5f45'}


def require(ok,why):
    if not ok:raise ValueError('A03 finite prepare denied: '+why)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def enc(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')


def raw(path,cap=MAX):
    path=Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size<=cap,'bounded regular named input required')
    with path.open('rb') as stream:data=stream.read(cap+1)
    require(len(data)<=cap,'bounded named read required');return data


def ref(path):
    path=Path(path).resolve(strict=True);data=raw(path)
    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}


def checked(item,cap=MAX):
    require(isinstance(item,dict) and set(item)=={'path','bytes','sha256'}
        and type(item['path']) is str and Path(item['path']).is_absolute()
        and type(item['bytes']) is int and 0<item['bytes']<=cap,'exact bounded reference required')
    data=raw(item['path'],cap)
    require((len(data),sha(data))==(item['bytes'],item['sha256']),'input pin differs: '+item['path'])
    value=json.loads(data);require(isinstance(value,dict),'JSON object required');return value


def load(item,name):
    path=Path(item['path']).resolve(strict=True)
    require(ref(path)==item,'exact finite producer source pin required')
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def stamp(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(dt.tzinfo is not None and dt.utcoffset().total_seconds()==0,'explicit UTC required');return dt


def target_ref(path,data):return {'path':str(path),'bytes':len(data),'sha256':sha(data)}


def ensure_contained(path,root):
    path=Path(path).resolve();root=Path(root).resolve(strict=True)
    require(path.is_relative_to(root) and path!=root,'output outside admitted root')
    return path


def _ram_spec(owner,*,root,stage,stage_raw,bootstrap,cwd,screen,clean,config,attempt,task,dependency_root):
    """Reuse the original prepare_spec algorithm; suppress only its write tail."""
    source=raw(owner.__file__).decode();tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare_spec')
    body=ast.get_source_segment(source,node)
    body=controls.swap(body.encode(),b'enable_driver_state_wal=False):',
        b'enable_driver_state_wal=False, task_nonce=None):').decode()
    body=controls.swap(body.encode(),b'nonce = uuid.uuid4().hex',b'nonce = task_nonce').decode()
    index=body.index('    root.mkdir(exist_ok=False)')
    require(body[index:].startswith('    root.mkdir(exist_ok=False)\n    path = root / "SPEC.json"'),
        'original finite SPEC write tail changed')
    body=body[:index]+'    return spec\n'
    stage_path=stage.resolve()
    def future_sha(path):
        return sha(stage_raw) if Path(path).resolve()==stage_path else owner.sha(path)
    scope={**vars(owner),'sha':future_sha}
    exec(compile(body,'A03-original-prepare-spec-RAM','exec'),scope)
    result=scope['prepare_spec'](root=root,role='supervisor',stage=stage,
        stage_sha256=sha(stage_raw),bootstrap_path=bootstrap,cwd=cwd,machine_id=MACHINE,
        stage_args=['--clean-source-freeze',str(clean),'--screen-admission',str(screen),
            '--launch-config',str(config),'--attempt','a03','--attempt-nonce',attempt,'--task-nonce',task],
        stop_path=cwd/'STOP-OWNED-GAME-C23',pythonpath=str(dependency_root),task_nonce=task)
    require(result['nonce']==task and result['task_name']=='XARG2ManagedOwner-'+task,'independent Task nonce differs')
    return result


def _actual_closure(plan):
    review=checked(plan['closed_consumers_ref'],65536)
    require(review.get('machine_id')==MACHINE and review.get('execution_owner')=='Root'
        and review.get('root_direct_execution_release') is True
        and review.get('status')=='A03_NO_LIVE_PREDECESSOR_CONSUMERS_REVIEWED'
        and review.get('no_live_owned_Game') is True and review.get('no_live_owned_SDK') is True
        and review.get('no_live_owned_supervisor') is True and review.get('predecessor_Tasks_absent') is True,
        'Root actual no-live predecessor consumer review required')
    require(-10<=(datetime.now(timezone.utc)-stamp(review['observed_at_utc'])).total_seconds()<=600,
        'fresh actual consumer closure review required')


def _full(plan):
    full=checked(plan['full_storage_ref'],65536);live=checked(plan['live_storage_ref'],65536)
    require(plan['full_storage_ref']['sha256']==plan['live_storage_ref']['sha256']
        and full==live and full.get('machine_id')==MACHINE,'one exact immutable/live canonical full required')
    require(datetime.now(timezone.utc)<stamp(full['review_at_utc']),'current full review expired')
    needed={'retained_other_reservations','disk_reserve_bytes','effective_project_quota',
        'approved_output_roots','review_at_utc'}
    require(needed<=set(full),'shared canonical full schema incomplete')
    approved=[Path(x).resolve() for x in full['approved_output_roots']]
    for key in ('runtime_root','output_root','task_root'):
        path=Path(plan[key]).resolve()
        require(any(path==root or path.is_relative_to(root) for root in approved),'output root not in canonical full')
    return full


def compose(plan_ref):
    """Return exact outputs/quote in RAM. Never grants runtime execution."""
    plan=checked(plan_ref,65536)
    require(plan.get('schema')=='xar.C23-A03-prepare-plan/v1' and plan.get('machine_id')==MACHINE
        and plan.get('execution_owner')=='Root' and plan.get('root_direct_execution_release') is True,
        'explicit Root A03 finite plan required')
    at=plan['observed_at_utc'];stamp(at)
    for key in ('attempt_nonce','task_nonce'):
        require(re.fullmatch('[0-9a-f]{32}',str(plan.get(key))) is not None,'explicit independent nonce required')
    require(plan['attempt_nonce']!=plan['task_nonce'],'attempt and Task nonce must differ')
    runtime=Path(plan['runtime_root']).resolve(strict=True)
    output=Path(plan['output_root']).resolve(strict=True)
    taskroot=ensure_contained(plan['task_root'],output)
    require(taskroot.name=='spec-supervisor-a03' and not taskroot.exists(),'new exact A03 Task root required')
    _actual_closure(plan);full=_full(plan)
    base=checked(plan['compact_base_ref'],524288)
    anchor=controls.business_binding(plan['business_anchor_ref'])
    require(base.get('machine_id')==MACHINE and base.get('source_root')
        and base.get('business_source_commit')==anchor['commit'] and 'canonical_preload_policy' not in base
        and base.get('source_file_count')==anchor['complete_file_count']
        and base.get('source_bytes')==anchor['complete_source_bytes'],'actual policy-free Source25 compact BASE required')
    graph,graph_report=controls.build_sources(native_transition_inputs=plan['native_transition_inputs'],
        business_anchor_ref=plan['business_anchor_ref'],frontier_ref=plan['frontier_ref'],full_timing=True)
    feeder=load(plan['feeder_producer_ref'],'_a03_finite_feeder')
    feeders,feeder_report=feeder.build_sources(review_deadline_utc=full['review_at_utc'],runtime_root=runtime)
    require(set(feeders)=={'root_p37c23_same_game_loop_feeder100.py','root_continuity_window_c23_100.py',
        'launch_c23_feeder100.py'},'complete finite feeder graph required')
    for name,data in feeders.items():compile(data,name,'exec')
    new_sources={**graph,**feeders}
    oldpolicy_path=runtime/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A02.json'
    oldpolicy_raw=raw(oldpolicy_path);require((len(oldpolicy_raw),sha(oldpolicy_raw))==OLD_POLICY,'actual A02 policy differs')
    oldfreeze=raw(runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json')
    require((len(oldfreeze),sha(oldfreeze))==OLD_FREEZE,'actual A02 RootFinal differs')
    policy=json.loads(oldpolicy_raw);rows=policy['entry_source_pins']
    require(len(rows)==44 and len({p for p,h in rows})==44,'exact A02 complete44 closure required')
    for path,digest in rows:require(ref(path)['sha256']==digest,'actual old closure differs')
    replaced=[]
    for path,digest in rows:
        old_path=Path(path)
        if old_path.parent==runtime and old_path.name==controls.OLD_HELPER:
            old_path=runtime/controls.HELPER;digest=sha(graph[controls.HELPER])
        elif old_path.parent==runtime and old_path.name in graph:digest=sha(graph[old_path.name])
        replaced.append([str(old_path),digest])
    require(len(replaced)==44 and len({p for p,h in replaced})==44,'complete A03 closure shape differs')
    six=[row[:] for row in replaced if Path(row[0]).parent==runtime and Path(row[0]).name in controls.SIX]
    require(len(six)==6 and all(r in replaced for r in six),'six exact closure subset required')
    policy.update(sdk_source_root=base['source_root'],entry_source_pins=replaced,canonical_entry_source_pins=six,
        enable_driver_state_wal_v1=True,actual_runtime_admitted=False,actual_loaded_provider_issued=False)
    policy_path=runtime/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A03.json';policy_raw=enc(policy)
    final_path=runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json'
    final={**base,'canonical_preload_policy':target_ref(policy_path,policy_raw)};final_raw=enc(final)
    require(len(final_raw)<=524288,'compact final freeze hard cap exceeded')
    final_ref=target_ref(final_path,final_raw)
    outputs={policy_path:policy_raw,final_path:final_raw}
    metadata={}
    for name in META_NAMES:
        old_path=runtime/name;data=raw(old_path)
        require(sha(data)==META_SHAS[name],'actual A02 metadata differs')
        value=json.loads(data)
        if name=='ROOT-CLEAN-SOURCE-FROZEN-C23.json':
            value.update(sdk_freeze=final_ref,at_utc=at,observed_at_utc=at,business_source_commit=anchor['commit'])
        elif name=='ROOT-LAUNCH-CONFIG-C23.json':
            value.update(SDK_freeze_sha256=final_ref['sha256'],storage_admission=plan['live_storage_ref']['path'],
                storage_admission_sha256=plan['live_storage_ref']['sha256'],full_storage_view=plan['full_storage_ref'],
                review_at_utc=full['review_at_utc'],observed_at_utc=at,business_source_commit=anchor['commit'],
                cold_attempt={'attempt_id':'a03','nonce':plan['attempt_nonce'],'task_nonce':plan['task_nonce'],
                    'execution_owner':'Root','root_direct_execution_release':True,
                    'prior_failure_a01':plan['prior_failure_a01'],'prior_failure_a02':plan['prior_failure_a02']})
        elif name=='ROOT-NATIVE30-SDK-BINDING-C23.json':
            value.update(source_root=base['source_root'],sdk_freeze_sha256=final_ref['sha256'],observed_at_utc=at)
        else:
            value.update(full_storage_view=plan['full_storage_ref'],source_review_at_utc=full['review_at_utc'],
                observed_at_utc=at,at=at)
        path=runtime/name.replace('-C23.','-C23-A03.');metadata[path]=enc(value)
    # Same known host checkout and Native30; source25 changes only the SDK view.
    metadata_config=json.loads(metadata[runtime/'ROOT-LAUNCH-CONFIG-C23-A03.json'])
    controls.validate_attempt(argparse.Namespace(attempt='a03',attempt_nonce=plan['attempt_nonce'],
        task_nonce=plan['task_nonce']),metadata_config,checked)
    native=load(plan['native_renderer_ref'],'_a03_native_renderer')
    native_raw,native_report=native.compose_native_session_v1(repository=REPO,
        capacity_ref=plan['full_storage_ref'],observed_at_utc=at)
    native_path=runtime/'ROOT-NATIVE30-NATIVE-PIN-C23-A03.json';metadata[native_path]=native_raw
    bind_path=runtime/'ROOT-NATIVE30-SDK-BINDING-C23-A03.json'
    binding=json.loads(metadata[bind_path]);binding['native_session_pin']=target_ref(native_path,native_raw)
    metadata[bind_path]=enc(binding)
    outputs.update(metadata)
    bootstrap=load(plan['bootstrap_ref'],'_a03_exact_frozen_bootstrap')
    require(raw(bootstrap.__file__)==raw(OWN/'interactive_task_owner_v1.py'),'independently frozen original bootstrap required')
    owner_source=load(ref(OWN/'interactive_task_owner_v1.py'),'_a03_original_owner_source')
    dependency_root=Path(policy['dependency_root']).resolve(strict=True)
    require(dependency_root.is_dir(),'actual pinned dependency directory required')
    spec=_ram_spec(owner_source,root=taskroot,stage=runtime/'root_native30_supervisor_c23.py',
        stage_raw=graph['root_native30_supervisor_c23.py'],bootstrap=Path(bootstrap.__file__),cwd=runtime,
        screen=Path(plan['screen_admission_ref']['path']),clean=runtime/'ROOT-CLEAN-SOURCE-FROZEN-C23-A03.json',
        config=runtime/'ROOT-LAUNCH-CONFIG-C23-A03.json',attempt=plan['attempt_nonce'],task=plan['task_nonce'],
        dependency_root=dependency_root)
    outputs[taskroot/'SPEC.json']=(json.dumps(spec,ensure_ascii=False,indent=2)+'\n').encode()
    changes={};source_rows=[]
    for name,data in new_sources.items():
        path=runtime/name
        if path.exists() and raw(path)==data:continue
        old=ref(path) if path.exists() else None
        archive=output/'post-close'/'a02-control-source'/name if old else None
        row={**target_ref(path,data),'old':old,'old_FileID':str(path.stat().st_ino) if old else None,
            'old_archive':str(archive) if archive else None}
        source_rows.append(row);changes[path]=data
    for path in outputs:
        if path==taskroot/'SPEC.json':continue
        require(path.parent==runtime and not path.exists(),'A03 metadata is create-only')
    for path in changes:require(path.parent==runtime,'finite source output outside runtime')
    attempts=[str(runtime/(stem+'-A03'+('.jsonl' if 'KEEPER' in stem else '.json'))) for stem in controls.ATTEMPT_NAMES]
    require(not any(Path(x).exists() for x in attempts),'A03 attempt already used')
    require(not any((runtime/name).exists() for name in controls.STOP_NAMES),'old stop/exit marker preserved; preparation blocked')
    require(not (runtime/'ROOT-ACTUAL-GAME-LAUNCH-C23.json').exists(),'actual successful Game launch already exists')
    # Every source/metadata/SPEC is quoted before any mutation; rename archives
    # add no data allocation. Allow one bounded receipt, intent, and FS metadata.
    logical=sum(map(len,changes.values()))+sum(map(len,outputs.values()))
    allocated=sum(((len(data)+4095)//4096)*4096 for data in [*changes.values(),*outputs.values()])
    require(allocated+131072<=2097152,'actual finite prepare exceeds 2MiB runtime hard bound')
    quote={'schema':'xar.C23-A03-finite-prepare-quote/v1','machine_id':MACHINE,'observed_at_utc':at,
        'status':'RAM_ONLY_NO_RUNTIME_GRANT','plan':plan_ref,'attempt_nonce':plan['attempt_nonce'],
        'task_nonce':plan['task_nonce'],'changed_sources':source_rows,
        'metadata':[target_ref(path,data) for path,data in outputs.items()],
        'canonical_entry_source_pins':six,'all_entry_rows':len(replaced),
        'new_source_logical':sum(map(len,changes.values())),'new_metadata_logical':sum(map(len,outputs.values())),
        'all_changes_logical':logical,'new_allocation_upper':allocated,
        'intent_receipt_and_FS_upper':131072,'runtime_prepare_peak_upper':allocated+131072,
        'final_equals_compact_BASE_plus_only_actual_policy_ref':True,
        'supervisor_attempt_outputs':attempts,'Task_spec':target_ref(taskroot/'SPEC.json',outputs[taskroot/'SPEC.json']),
        'Task_registered':False,'Game_created':False,'Driver_SAVE_body_read':False}
    return changes,outputs,quote


def _once(path,data):
    require(len(data)<=524288,'finite single output cap exceeded')
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    require(raw(path)==data,'create-only output readback differs')
    return ref(path)


def adopt(plan_ref,quote_ref,card_ref):
    plan=checked(plan_ref,65536);wanted=checked(quote_ref,65536);card=checked(card_ref,65536)
    require(card.get('schema')=='xar.C23-A03-runtime-prepare-admission/v1'
        and card.get('machine_id')==MACHINE and card.get('status')=='ADMITTED'
        and card.get('plan')==plan_ref and card.get('quote')==quote_ref
        and card.get('full_storage_ref')==plan['full_storage_ref'],
        'separate actual exact runtime prepare admission required')
    changes,outputs,quote=compose(plan_ref);require(quote==wanted,'complete RAM quote changed')
    require(type(card.get('hard_bytes')) is int and quote['runtime_prepare_peak_upper']<=card['hard_bytes'],
        'precise runtime peak exceeds admitted hard bytes')
    full=_full(plan);_actual_closure(plan)
    disk=shutil.disk_usage(plan['runtime_root'])
    require(disk.free>full['disk_reserve_bytes'],'actual canonical full free guard refused')
    # Project/quota/reservations must have been reviewed by the canonical
    # storage producer; do not substitute whole-volume disk.used as project use.
    require(card.get('canonical_capacity_review_passed') is True,'actual unified capacity review required')
    runtime=Path(plan['runtime_root']).resolve();output=Path(plan['output_root']).resolve()
    intent=output/'A03-PREPARE-INTENT.json';receipt=output/'A03-PREPARED.json'
    require(not intent.exists() and not receipt.exists(),'one-shot attempt already consumed')
    require(not Path(plan['task_root']).exists(),'Task root already exists; no replay')
    import win32file
    old_leases=[]
    try:
        for row in quote['changed_sources']:
            if row['old'] is None:
                require(not Path(row['path']).exists(),'new source already exists');continue
            path=Path(row['old']['path']);archive=Path(row['old_archive'])
            require(ref(path)==row['old'] and str(path.stat().st_ino)==row['old_FileID'],
                'actual old source CAS changed')
            require(not archive.exists() and archive.resolve().is_relative_to(output/'post-close')
                and path.stat().st_dev==output.stat().st_dev,'same-volume exact new archive required')
            # Reject active read leases; keep each exclusive lease until all
            # preflight completes. Recheck CAS before its exact rename.
            old_leases.append(win32file.CreateFile(str(path),0x80,0,None,3,0x80,None))
        _once(intent,enc({'machine_id':MACHINE,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
            'status':'ONE_SHOT_SOURCE_METADATA_PREPARE_INTENT','plan':plan_ref,'quote':quote_ref,'card':card_ref}))
    finally:
        for handle in old_leases:handle.Close()
    (output/'post-close'/'a02-control-source').mkdir(parents=True,exist_ok=False)
    source_refs=[]
    for row in quote['changed_sources']:
        path=Path(row['path']);data=changes[path]
        if row['old'] is not None:
            require(ref(path)==row['old'] and str(path.stat().st_ino)==row['old_FileID'],'last old source CAS changed')
            archive=Path(row['old_archive']);path.rename(archive)
            require(ref(archive)['sha256']==row['old']['sha256'] and str(archive.stat().st_ino)==row['old_FileID'],
                'same-ID original archive readback differs')
        source_refs.append(_once(path,data))
    Path(plan['task_root']).mkdir(exist_ok=False)
    metadata_refs=[_once(path,data) for path,data in outputs.items()]
    final=json.loads(outputs[runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A03.json'])
    base=checked(plan['compact_base_ref'],524288)
    policy_path=runtime/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A03.json';policy=json.loads(raw(policy_path))
    require(final=={**base,'canonical_preload_policy':ref(policy_path)},'final exceeded one actual policy ref addition')
    for path,digest in policy['entry_source_pins']:require(ref(path)['sha256']==digest,'actual complete closure changed')
    sys.path[:0]=[str(Path(final['source_root'])),str(OWN.parent)]
    from g2_saved_campaign.canonical_native_provider_chain_v1 import _verified_entry_sources
    require(len(_verified_entry_sources(policy['canonical_entry_source_pins']))==6,'original max8 actual six verifier refused')
    owner=load(plan['bootstrap_ref'],'_a03_actual_bootstrap_terminal')
    spec_path=Path(plan['task_root'])/'SPEC.json';owner.checked_spec(spec_path,ref(spec_path)['sha256'])
    require((len(raw(runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json')),
        sha(raw(runtime/'ROOT-FINAL-SDK-FREEZE-P37C23-A02.json')))==OLD_FREEZE,'old A02 freeze changed')
    require((len(raw(runtime/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A02.json')),
        sha(raw(runtime/'ROOT-C23-CANONICAL-PRELOAD-POLICY-A02.json')))==OLD_POLICY,'old A02 policy changed')
    result={'schema':'xar.C23-A03-finite-prepare-complete/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'A03_PREPARED_NOT_REGISTERED_NOT_RUN',
        'plan':plan_ref,'quote':quote_ref,'card':card_ref,'intent':ref(intent),
        'sources':source_refs,'metadata':metadata_refs,'all_closure_actual_hash_verified':True,
        'canonical6_original_max8_verifier_passed':True,'Task_SPEC_original_validator_passed':True,
        'full_storage_ref':plan['full_storage_ref'],'live_storage_ref':plan['live_storage_ref'],
        'old_A02_policy_and_freeze_preserved':True,'cross_file_atomic_claim':False,
        'Task_registered':False,'Game_created':False,'Driver_SAVE_body_read':False}
    return _once(receipt,enc(result))


def main(argv=None):
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('command',choices=('quote','adopt'))
    parser.add_argument('--plan',required=True,type=Path);parser.add_argument('--plan-sha',required=True)
    parser.add_argument('--quote',type=Path);parser.add_argument('--quote-sha')
    parser.add_argument('--card',type=Path);parser.add_argument('--card-sha');args=parser.parse_args(argv)
    def pinned(path,digest):
        item=ref(path);require(item['sha256']==digest,'CLI input exact SHA differs');return item
    plan_ref=pinned(args.plan,args.plan_sha)
    if args.command=='quote':result=compose(plan_ref)[2]
    else:
        require(all((args.quote,args.quote_sha,args.card,args.card_sha)),'adopt requires exact quote and separate card')
        result=adopt(plan_ref,pinned(args.quote,args.quote_sha),pinned(args.card,args.card_sha))
    print(json.dumps(result,ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())

