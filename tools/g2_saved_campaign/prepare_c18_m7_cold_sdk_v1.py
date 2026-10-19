"""Pure minimal M7 source composition over actual C17; no runtime activation.

Preserve the complete source14 tree, WAL and same-speed implementation.  Take
only the seven pinned independent M7 leaves and the exact historic M7 hunks in
five existing leaves.  No actual actor/date/SAVE/recording boundary is invented.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import prepare_c16_perf_warm_sdk_v1 as exact

REPO=Path(__file__).resolve().parents[2]
MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE_ROOT=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/sdk-v20261019-candidate/src14')
BASE_FREEZE=BASE_ROOT.parent.parent/'robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C17.json'
BASE_FREEZE_PIN=(375058,'abea90e330961720d50ec433de215bfe151c2d3c35688fc0ac03cbf73d5e8b86')
BASE_COMMIT='04a87c1ec6fd4a0d59e6237af3158ce797c7cbe4'
DONOR='36717710ccebefa1c893fc6f7471869e5b9a8f77'
PARSER_COMMIT='70137a36ea18d6d9f84375bfbef181927a90a5f9'
CHAIN_COMMIT='6dbcf3e957a2d59fd072aeed2a7a6ec52b312ac6'
EXACT_HELPER_PIN=(25869,'ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b')
DRIVER='xar_autoplayer/bridge/native_driver.py'
RUNTIME='xar_autoplayer/runtime.py'
ROOT='xar_autoplayer/bridge/campaign_root_context_contract.py'
OWNER='xar_autoplayer/bridge/successor_ui_app_owner_v1.py'
EPOCH='xar_autoplayer/successor_ui_pending_ledger_v1.py'
NEW={
 'xar_autoplayer/bridge/native_loaded_provider_custody_v1.py':(21503,'a935b8912fd553058b10e7307c04e9103669279d723a0caeff68ac9acd4ac563'),
 'xar_autoplayer/bridge/native_loaded_provider_windows_v1.py':(20371,'fd6f581ce13c22e18eff50729d9dc11a95e8b6b9a861fd6e33244a341911731b'),
 'xar_autoplayer/bridge/native_loaded_provider_receiver_v1.py':(9299,'10fdcb40766c913671c797e848d078dad7f4f4ffdd87cec80b9473b26fe53d7e'),
 'xar_autoplayer/bridge/native_loaded_provider_origin_v1.py':(15954,'3b8bd840df7b3d6af7326f388363729e909c88355d0649f892189d70ae390695'),
 'xar_autoplayer/bridge/native_loaded_provider_origin_io_v1.py':(6755,'9b0e5e3528f68777979afd1742cd4d525051ad0e9b16225d7175d4a29474827e'),
 'xar_autoplayer/bridge/player_heir_candidate_component_v1.py':(12841,'69977b160964c526187e3ae4612d2da670e6af5e6f76acc5fb2ccdfd4570342a'),
 'xar_autoplayer/player_heir_fixed_dynasty_projection_v1.py':(11877,'1ca02c48f94503ef05a4d3f0d2d3045d8eb83670c55fd6ac7952a321ac3f735e'),
}
CHANGES=((PARSER_COMMIT,DRIVER),(PARSER_COMMIT,ROOT),(PARSER_COMMIT,OWNER),(PARSER_COMMIT,EPOCH),
         (CHAIN_COMMIT,DRIVER),(CHAIN_COMMIT,RUNTIME),(CHAIN_COMMIT,EPOCH))
PROTECTED_DRIVER_METHODS=(
 '_persist_driver_state','_read_driver_state','_record_command',
 '_route_horizon_wal_eligible_v1','_driver_state_wal_scalar_fields_locked_v1',
 '_try_persist_driver_state_wal_append_v1','_advance_exact_day_with_sentinel',
 '_execute_campaign_advance_route_contact_horizon_v1',
)


def read_manifest():
    exact.check_bytes(Path(exact.__file__).read_bytes(),EXACT_HELPER_PIN,'frozen exact-hunk helper')
    raw=exact.check_bytes(BASE_FREEZE.read_bytes(),BASE_FREEZE_PIN,'actual C17 fullfreeze')
    doc=json.loads(raw)
    exact.require(doc['machine_id']==MACHINE and doc['status']=='FINAL_SOURCE_FROZEN'
        and doc['source_file_count']==1445 and doc['source_bytes']==59051187
        and doc['business_source_commit']==BASE_COMMIT
        and Path(doc['source_root']).resolve()==BASE_ROOT.resolve(),'actual full SDK binding differs')
    rows={}
    for row in doc['files']:
        name=exact.safe_relative(row['relative'])
        exact.require(name not in rows and row['git_mode'] in ('100644','100755')
            and type(row['bytes']) is int and 0<=row['bytes']<=8*1024**2,'invalid actual row')
        rows[name]=dict(row)
    exact.require(len(rows)==1445 and sum(r['bytes'] for r in rows.values())==doc['source_bytes'],
                  'actual full manifest set differs')
    return doc,rows


def read_base(name,indexed):
    row=indexed[name]
    path=BASE_ROOT/name
    exact.require(path.is_file() and not path.is_symlink(),'actual source leaf missing/symlink')
    with path.open('rb') as stream:raw=stream.read(8*1024**2+1)
    exact.check_bytes(raw,(row['bytes'],row['sha256']),'actual '+name)
    exact.require(exact.blob_sha(raw)==row['git_blob_sha1'],'actual Git blob differs: '+name)
    return raw


def direct_internal_dependencies(changed,all_rows):
    """Inventory every static internal import in all twelve changed modules."""
    import importlib.util
    result={}
    for name,raw in sorted(changed.items()):
        package=name[:-3].replace('/','.').rpartition('.')[0]
        deps=set()
        for node in ast.walk(ast.parse(raw)):
            if isinstance(node,ast.ImportFrom) and node.level:
                module=importlib.util.resolve_name('.'*node.level+(node.module or ''),package)
                if node.module is None:
                    candidates=[module+'.'+alias.name for alias in node.names]
                else:candidates=[module]
                for candidate in candidates:
                    source=candidate.replace('.','/')+'.py'
                    init=candidate.replace('.','/')+'/__init__.py'
                    exact.require(source in all_rows or init in all_rows,
                                  'missing internal dependency '+candidate+' imported by '+name)
                    deps.add(source if source in all_rows else init)
            elif isinstance(node,ast.Import):
                for alias in node.names:
                    if alias.name.startswith('xar_autoplayer.'):
                        source=alias.name.replace('.','/')+'.py'
                        init=alias.name.replace('.','/')+'/__init__.py'
                        exact.require(source in all_rows or init in all_rows,'missing absolute internal dependency')
                        deps.add(source if source in all_rows else init)
        result[name]=sorted(deps)
    return result


def compose(*,verify_all_base=True):
    base,indexed=read_manifest()
    originals={}
    def old(name):
        if name not in originals:originals[name]=read_base(name,indexed)
        return originals[name]
    exact.check_bytes(old(DRIVER),(1637048,'cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab'),
                      'actual WAL/speed Driver')
    changed={};operations=[]
    for name,expected in NEW.items():
        exact.require(name not in indexed,'new M7 dependency already present')
        changed[name]=exact.check_bytes(exact.git_source(DONOR,name),expected,'pinned independent M7 leaf '+name)
        operations.append({'kind':'new_pinned_independent_leaf','relative':name,'donor':DONOR,
                           'after':exact.pin(changed[name])})
    for commit,name in CHANGES:
        original=changed[name] if name in changed else old(name)
        after,operation=exact.transfer_committed(original,commit+'^',commit,name)
        changed[name]=after;operations.append(operation)
    exact.require(len(changed)==12,'seven new plus five existing source leaves required')
    driver_before=exact.function_asts(old(DRIVER));driver_after=exact.function_asts(changed[DRIVER])
    changed_driver=sorted(k for k in set(driver_before)|set(driver_after)
        if driver_before.get(k)!=driver_after.get(k))
    allowed={
      'NativeHeadlessGameplayDriver.__init__','NativeHeadlessGameplayDriver._invalidate_player_heir_provider_v1',
      'NativeHeadlessGameplayDriver._mark_bridge_disconnected_v1','NativeHeadlessGameplayDriver._ingest',
      'NativeHeadlessGameplayDriver._adopt_bridge_session','NativeHeadlessGameplayDriver._execute_campaign_root_context_v1_query',
      'NativeHeadlessGameplayDriver.close'}
    exact.require(set(changed_driver)<=allowed,'unrelated Driver AST changed: '+repr(set(changed_driver)-allowed))
    donor_driver_asts=exact.function_asts(exact.git_source(DONOR,DRIVER))
    for name in changed_driver:
        exact.require(driver_after[name]==donor_driver_asts[name],
                      'M7 Driver method differs from qualified donor: '+name)
    for name in PROTECTED_DRIVER_METHODS:
        key='NativeHeadlessGameplayDriver.'+name
        if key in driver_before:
            exact.require(driver_before[key]==driver_after[key],'protected WAL/speed/business method changed: '+name)
    runtime_before=exact.function_asts(old(RUNTIME));runtime_after=exact.function_asts(changed[RUNTIME])
    changed_runtime=sorted(k for k in set(runtime_before)|set(runtime_after)
        if runtime_before.get(k)!=runtime_after.get(k))
    exact.require(set(changed_runtime)=={'_apply_pre_native_resume_v1','launch'},'unrelated Runtime AST changed')
    # All remaining four independent leaves must equal their qualified donor
    # bytes, unlike the Driver whose current WAL/speed bytes are preserved.
    for name in (ROOT,OWNER,RUNTIME,EPOCH):
        donor=exact.git_source(DONOR,name)
        exact.require(changed[name]==donor,'unexpected unrelated donor delta: '+name)
    for name,raw in changed.items():compile(raw,name,'exec',dont_inherit=True)
    if verify_all_base:
        for name in indexed:old(name)
    rows={name:dict(row) for name,row in indexed.items()};delta=[]
    for name,raw in sorted(changed.items()):
        before=rows.get(name)
        after={'relative':name,**exact.pin(raw),'git_blob_sha1':exact.blob_sha(raw),
               'git_mode':before['git_mode'] if before else '100644'}
        rows[name]=after
        delta.append({'relative':name,'before':before,'after':after,'net_bytes':len(raw)-(before['bytes'] if before else 0)})
    dependencies=direct_internal_dependencies(changed,rows)
    stable=[rows[name] for name in sorted(rows)]
    manifest=json.dumps(stable,sort_keys=True,separators=(',',':')).encode()
    epoch_names=[]
    for node in ast.walk(ast.parse(changed[EPOCH])):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='names' for t in node.targets):
            epoch_names=list(ast.literal_eval(node.value))
    exact.require(epoch_names and all('xar_autoplayer/'+n in rows for n in epoch_names),'source epoch closure missing')
    epoch_inputs={name:rows['xar_autoplayer/'+name]['sha256'] for name in epoch_names}
    epoch_model=hashlib.sha256(json.dumps(epoch_inputs,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    plan={'schema':'xar.c18.m7-minimal-cold-sdk-composition/v1','machine_id':MACHINE,
      'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_COMPOSITION_READY_DEFAULT_OFF_NOT_ADOPTED',
      'base_freeze':{'path':str(BASE_FREEZE),'bytes':BASE_FREEZE_PIN[0],'sha256':BASE_FREEZE_PIN[1]},
      'base_source_root':str(BASE_ROOT),'base_business_commit':BASE_COMMIT,'base_files':len(indexed),
      'complete_manifest':{'file_count':len(stable),'source_bytes':sum(r['bytes'] for r in stable),
          'canonical_rows_JSON':exact.pin(manifest),'basis':'Exact full1445-row original manifest plus twelve-leaf delta; no full master overlay.'},
      'all_original_leaves_verified':verify_all_base,'delta':delta,'operations':operations,
      'Driver_AST_changed':changed_driver,'Runtime_AST_changed':changed_runtime,
      'protected_WAL_same_speed_and_business_method_AST_equal':True,
      'internal_static_dependency_closure':dependencies,'epoch_names':epoch_names,
      'candidate_epoch_inputs':epoch_inputs,'candidate_epoch_synthetic_source_model':epoch_model,
      'changed_leaf_logical_bytes_each':sum(map(len,changed.values())),
      'prospective_dual_changed_logical_bytes':2*sum(map(len,changed.values())),
      'native_bytes_added_or_qualified':0,'actual_H':'unknown','actual_player_heir_score_credit':0,
      'M7_ledger_checked_Service_strategy_public_MCP_changed':False,'M7_default_enabled':False,
      'explicit_cold_preload_callback_required':True,'fixed_original_D0':174,
      'then_bound_inputs':['actual machine/Game fullbirth/EXE','actual then actor/episode/date','normal SAVE and normal SDK/Game closure',
          'real pre-Native-resume retained DLL lease and absence/module/native peer/generation readbacks','canonical actual supervisor->owner->Queue->App creation chain',
          'actual then recording and source epoch','naturally produced optional root component'],
      'no_F90_or_historical_actor_date_recovery_exception':True,
      'D_output_writes':0,'Git_writes':0,'Task_or_Game_or_RPC_calls':0,'Driver_SAVE_body_reads':0,
      'future_materialization':'Requires new named capacity card and real cold authorization/boundary. Current C17 is independent.'}
    return changed,stable,plan


if __name__=='__main__':
    _,_,value=compose()
    if len(sys.argv)==2:
        target=Path(sys.argv[1]).resolve()
        exact.require(target.is_relative_to(REPO.resolve()),'small report must remain in workspace')
        raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
        exact.require(len(raw)<=48*1024,'small source report cap')
        with target.open('xb') as stream:stream.write(raw)
        print(json.dumps({'report':{'path':str(target),**exact.pin(raw)}}))
    else:print(json.dumps(value,ensure_ascii=False,indent=2))
