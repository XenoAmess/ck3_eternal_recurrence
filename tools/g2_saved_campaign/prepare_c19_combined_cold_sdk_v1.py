"""Source-only C19 M7 + finite event knowledge + bounded WAL composition.

The actual family-fixed C18/source15 is the sole complete baseline.  Old
frozen candidates provide named hunks/leaves, never replacement SDK trees.
No output SDK, full Driver copy, Git object, Task or Game is created here.
"""
from __future__ import annotations
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

import prepare_c16_perf_warm_sdk_v1 as exact
import prepare_c18_m7_cold_sdk_v1 as m7
import bounded_multiday_wal_source_v1 as bounded

REPO=Path(__file__).resolve().parents[2]
MACHINE='xenoamess-full-tower-eb9d2c1186'
N=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
BASE_ROOT=N/'sdk-v20261019-candidate/src15'
BASE_FREEZE=N/'robert30-v20261019-campaign01/runtime/ROOT-FINAL-SDK-FREEZE-P37C18.json'
FREEZE_PIN=(375083,'624c0a229abea3241474e31958bfe4b4102e970f7032f3fc9821273a15ee1d5b')
BASE='0e8a190bf3e5ec187e7bc30d76310585922a0b50'
FAMILY='xar_autoplayer/family_marriage_formal_consumer.py'
FAMILY_PIN=(61273,'d8bbaa3c469f10f974b43335f8505913ae292c4f9b487dddf3e8da1a3c93deaf')
DRIVER=m7.DRIVER
M2='xar_autoplayer/vanilla_events/event_offline_analysis.py'
M2_NEW='xar_autoplayer/vanilla_events/c19_finite_source_rebind_v1.py'
WAL_NEW='xar_autoplayer/bridge/bounded_multiday_wal_v1.py'
M2_BASE=(28093,'f76ee3f2bb7fb3951da5a4e75533c72fb48a3eff01f860cd31a9518c5766c52f')
M2_AFTER=(28542,'2d4a046d969ab3d0d076e460936e8cf4cf605e1f90cbe34f9bb963e0e6240d1e')
NEW_PINS={M2_NEW:(10456,'153cec501dfbfa6e24d754204f68dd5e5aec4ebe95b6379c3615ff22474a3837'),
          WAL_NEW:(8955,'d23eb5a4110663911f5b291e5044de1b8db29d56016806873d4e6f4ff3fd0c3e')}
INPUT_PINS={
 'tools/g2_saved_campaign/prepare_c16_perf_warm_sdk_v1.py':(25869,'ed79fdb82f422c4cd17dc9fc1c00a133603dbea2ca4374b980172c1eb33a916b'),
 'tools/g2_saved_campaign/prepare_c18_m7_cold_sdk_v1.py':(13208,'657050c6368e3f704452d0781adcc1515dec16c981f7af37d51917c024a3eaf6'),
 'tools/g2_saved_campaign/bounded_multiday_wal_source_v1.py':(3527,'a3717e6a64c0f53f1841f329c39c00f8853aeef083b5c1b0066a661fb0a2a3a4'),
 'docs/ck3-native-ai/evidence/g2-m2-c19-finite-source-rebind-hunks-2026-10-20.json':(1660,'95bddc5a7be1d9464ba569c4ca9de87473e59564a014f578f0e0cad8ddf5c17b'),
}


def read_manifest():
    for name,pin in INPUT_PINS.items():exact.check_bytes((REPO/name).read_bytes(),pin,'frozen input '+name)
    raw=exact.check_bytes(BASE_FREEZE.read_bytes(),FREEZE_PIN,'actual C18 fullfreeze')
    doc=json.loads(raw)
    exact.require(doc['machine_id']==MACHINE and doc['status']=='FINAL_SOURCE_FROZEN'
        and doc['business_source_commit']==BASE and Path(doc['source_root']).resolve()==BASE_ROOT.resolve()
        and doc['source_file_count']==1445 and doc['source_bytes']==59052571,'family-fixed actual C18 binding differs')
    rows={}
    for row in doc['files']:
        name=exact.safe_relative(row['relative'])
        exact.require(name not in rows and row['git_mode'] in ('100644','100755')
            and type(row['bytes']) is int and 0<=row['bytes']<=8*1024**2,'invalid base row')
        rows[name]=dict(row)
    exact.require(len(rows)==1445 and sum(r['bytes'] for r in rows.values())==59052571,'actual full source set differs')
    return doc,rows


def read_base(name,indexed):
    row=indexed[name]
    with (BASE_ROOT/name).open('rb') as stream:raw=stream.read(8*1024**2+1)
    exact.check_bytes(raw,(row['bytes'],row['sha256']),'actual source15 '+name)
    exact.require(exact.blob_sha(raw)==row['git_blob_sha1'],'actual Gitblob differs: '+name)
    return raw


def apply_m7_driver(data):
    result=data
    for commit,name in m7.CHANGES:
        if name==DRIVER:result,_=exact.transfer_committed(result,commit+'^',commit,name)
    return result


def m2_hunks():
    name='docs/ck3-native-ai/evidence/g2-m2-c19-finite-source-rebind-hunks-2026-10-20.json'
    return [(row['before'].encode(),row['after'].encode()) for row in json.loads((REPO/name).read_bytes())['edits']]


def compose(*,verify_all_base=True):
    base,indexed=read_manifest();originals={}
    def old(name):
        if name not in originals:originals[name]=read_base(name,indexed)
        return originals[name]
    exact.check_bytes(old(FAMILY),FAMILY_PIN,'mandatory retained family fix')
    exact.check_bytes(old(DRIVER),(1637048,'cc60c9af670c37ef2085f66d07db17a2bd309660fcb60c05a5340df7720874ab'),
                      'actual inherited WAL/speed Driver')
    changed={};operations=[]
    for name,pin in m7.NEW.items():
        exact.require(name not in indexed,'new M7 leaf already present')
        changed[name]=exact.check_bytes(exact.git_source(m7.DONOR,name),pin,'pinned M7 '+name)
        operations.append({'kind':'new_pinned_M7_leaf','relative':name,'donor':m7.DONOR,'after':exact.pin(changed[name])})
    for commit,name in m7.CHANGES:
        before=changed[name] if name in changed else old(name)
        changed[name],operation=exact.transfer_committed(before,commit+'^',commit,name)
        operations.append(operation)
    m7_driver=changed[DRIVER]
    exact.check_bytes(m7_driver,(1638658,'330caa34eba442c0764c628499e979600bda2d58ea51b365cb4e4829b3db13ed'),
                      'M7-only intermediate preserves actual WAL/speed')
    changed[DRIVER]=bounded.transform_driver_bytes_v1(m7_driver)
    exact.require(bounded.reverse_driver_bytes_v1(changed[DRIVER])==m7_driver,'multiday inverse lost M7 bytes')
    # Independent source spans must commute; this proves that neither layer
    # silently replaces the other layer's full Driver with its historic base.
    alternate=apply_m7_driver(bounded.transform_driver_bytes_v1(old(DRIVER)))
    exact.require(alternate==changed[DRIVER],'M7 and bounded WAL compositions do not commute')
    operations.append({'kind':'guarded_bounded_multiday_two_hunks','relative':DRIVER,
        'producer':INPUT_PINS['tools/g2_saved_campaign/bounded_multiday_wal_source_v1.py'],
        'before':exact.pin(m7_driver),'after':exact.pin(changed[DRIVER]),
        'required_two_method_AST':bounded.METHODS,'inverse_restores_M7_bytes':True,
        'M7_then_WAL_equals_WAL_then_M7':True})
    exact.check_bytes(old(M2),M2_BASE,'retained finite-letter source loader')
    changed[M2]=exact.transfer_exact_hunks(old(M2),m2_hunks())
    exact.check_bytes(changed[M2],M2_AFTER,'finite two-key loader candidate')
    operations.append({'kind':'exact_M2_finite_three_hunks','relative':M2,'before':exact.pin(old(M2)),
        'after':exact.pin(changed[M2]),'inverse_restores_actual_bytes':True})
    for name,pin in NEW_PINS.items():
        exact.require(name not in indexed,'new independent helper already present')
        changed[name]=exact.check_bytes((REPO/exact.PREFIX/name).read_bytes(),pin,'new helper '+name)
        operations.append({'kind':'new_pinned_independent_helper','relative':name,'after':exact.pin(changed[name])})
    exact.require(len(changed)==15 and len(set(changed)-set(indexed))==9,'expected nine new plus six existing deltas')
    # All M7 endpoints remain the independently reviewed donor implementations;
    # only the two separate WAL method ASTs intentionally differ in Driver.
    before_asts=exact.function_asts(old(DRIVER));final_asts=exact.function_asts(changed[DRIVER])
    m7_asts=exact.function_asts(m7_driver);donor_asts=exact.function_asts(exact.git_source(m7.DONOR,DRIVER))
    m7_names={name for name in set(before_asts)|set(m7_asts) if before_asts.get(name)!=m7_asts.get(name)}
    for name in m7_names:
        exact.require(final_asts[name]==m7_asts[name]==donor_asts[name],'M7 endpoint altered by another package: '+name)
    wal_names={'NativeHeadlessGameplayDriver.'+name for name in bounded.METHODS}
    for name in set(before_asts)|set(final_asts):
        if name not in m7_names|wal_names:
            exact.require(before_asts.get(name)==final_asts.get(name),'unrelated Driver method changed: '+name)
    for name in (m7.RUNTIME,m7.ROOT,m7.OWNER,m7.EPOCH):
        exact.require(changed[name]==exact.git_source(m7.DONOR,name),'M7 independent seam differs: '+name)
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
    exact.require(rows[FAMILY]==indexed[FAMILY] and FAMILY not in changed,'family fix was overwritten')
    closure=m7.direct_internal_dependencies(changed,rows)
    epoch_names=[]
    for node in ast.walk(ast.parse(changed[m7.EPOCH])):
        if isinstance(node,ast.Assign) and any(isinstance(n,ast.Name) and n.id=='names' for n in node.targets):
            epoch_names=list(ast.literal_eval(node.value))
    exact.require(epoch_names and all('xar_autoplayer/'+name in rows for name in epoch_names),'epoch source dependency missing')
    epoch_inputs={name:rows['xar_autoplayer/'+name]['sha256'] for name in epoch_names}
    epoch=hashlib.sha256(json.dumps(epoch_inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    stable=[rows[name] for name in sorted(rows)]
    row_bytes=json.dumps(stable,sort_keys=True,separators=(',',':')).encode()
    exact.require(len(stable)==1454 and sum(r['bytes'] for r in stable)==59176029,'combined full manifest arithmetic differs')
    plan={'schema':'xar.c19.combined-cold-sdk-source-composition/v1','machine_id':MACHINE,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_ONLY_DEFAULT_OFF_NOT_ADOPTED',
        'base_freeze':{'path':str(BASE_FREEZE),'bytes':FREEZE_PIN[0],'sha256':FREEZE_PIN[1]},
        'base_source_root':str(BASE_ROOT),'base_business_commit':BASE,'base1445_leaves_verified':verify_all_base,
        'complete_manifest':{'file_count':len(stable),'source_bytes':sum(r['bytes'] for r in stable),
            'canonical_rows_JSON':exact.pin(row_bytes),'access':'compose() returns full exact1454 rows in memory'},
        'delta':delta,'operations':operations,'new_leaves':9,'changed_existing_leaves':6,'unchanged_base_leaves':1439,
        'internal_static_dependency_closure':closure,'family_fix_preserved':rows[FAMILY],
        'epoch_inputs':epoch_inputs,'epoch_source_model':epoch,
        'Driver_M7_method_names':sorted(m7_names),'Driver_WAL_only_method_names':sorted(wal_names),
        'all_other_Driver_method_ASTs_unchanged':True,
        'changed_source_logical_bytes_each':sum(map(len,changed.values())),
        'prospective_dual_changed4096cluster_allocation_upper_bytes':sum(2*((len(raw)+4095)//4096)*4096 for raw in changed.values()),
        'Native_binary_or_loaded_qualification':0,'actual_H':'unknown','actual_perf_seconds_saved':None,
        'D_SDK_Git_Task_Game_RPC_writes':0,'Driver_SAVE_ledger_body_reads':0,
        'FULL_timing_in_business_tree':False,
        'future_controls_timing':'Build the genuinely enabled then-C19 canonical custody graph first; use only transform_queue/transform_handoff/transform_feeder from the frozen timing producer. Its fixed build_sources calls outer.build_sources(enabled=False) and must not replace the live custody graph.',
        'Native_transition_remaining':'Source baseline metadata is Native29. Original exporter requires matching base/native pin; Native30 needs a separately reviewed explicit transition contract with real qualified new DLL evidence, not mutation of the old624c freeze.',
        'future_cold_boundary':'Same original campaign/SAVE/goal and wall anchor, new actual Game birth; take then actor/episode/date/recording and normal closure. Never reuse F90 or a hardcoded current actor.',
        'default_boundaries':['M7 cold callback/received adapters remain defaultOFF','WAL writer uses existing explicit env/default; helper changes storage eligibility only','M2 new knowledge scope is two exact source/GUI/type shapes; execution/material contracts remainFalse']}
    return changed,stable,plan


if __name__=='__main__':
    _,_,report=compose()
    if len(sys.argv)==2:
        path=Path(sys.argv[1]).resolve();exact.require(path.is_relative_to(REPO.resolve()),'small source report outside workspace')
        raw=(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
        exact.require(len(raw)<=64*1024,'small source report cap')
        with path.open('xb') as stream:stream.write(raw)
        print(json.dumps({'report':{'path':str(path),**exact.pin(raw)}}))
    else:
        print(json.dumps({k:v for k,v in report.items() if k not in ('delta','operations','internal_static_dependency_closure','epoch_inputs')},indent=2))
