"""ROOT-only, one reviewed <=1000-file R54 cache batch; no recursion or automatic replay."""
import argparse
from contextlib import ExitStack
import ctypes
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import msvcrt
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
TARGET = Path('C:/workspace/ck3-common-runtime/cases/lyd-i4-natural-expiry-20261011-005/state/profile/shadercache')
MANIFEST = Path('C:/workspace/ck3-common-runtime/graphics-seeds/lyd-r54-20261011-001/manifest.json')
MANIFEST_SHA = 'a1fab6e0e92e4a8ea394d6e85e365f5c6be619e87d4f2c16b7ed9d2623cebe06'
ROOT = 'lyd-transaction-control-scaffold-l0-20261009-root'
COORD = 'lyd-volume-c-admission-20261010-root'
LOCK = Path('C:/workspace/.codex-task-bus/lyd-volume-c.admission.lock')
CLI = Path('C:/workspace/.codex-task-bus/bin/codex_task_bus.py')
CLI_SHA = 'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
EXPIRY = '2026-10-17T13:06:29.278808+00:00'
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
INDEXED = {'path':str(BASE/'source06-source07-cleanup-candidate-20261010-001/cleanup_indexed_exports.py'),
 'bytes':24564,'sha256':'41028f3518a65590c018a1b8167b6305a25c16eabf44400bac6e2b1a1d44060c'}
NATIVE = {'path':str(BASE/'storage-cleanup-20261010-001/cleanup_two_derived_texts.py'),
 'bytes':16241,'sha256':'09ac7024f5abb2cfee8e7112fd337d46adb59a814672ac0e3c4208e3cd97424f'}
BACKEND = {'path':'C:/workspace/ck3_eternal_recurrence/tools/project_exe_broker/native_safety.py',
 'bytes':35834,'sha256':'873ec34e49d2549493ffddeb934d4d7d12e7a97de76fecc43c5135c0ee5118e2'}

FACTS = {'path': 'C:\\workspace\\ck3_lyd_runtime_20261004\\r54-mutable-cache-retirement-review-20261011-001\\FACTS.source-only.json', 'bytes': 7021, 'sha256': '70b1bb961eebbac64f9fe5979549ec740ad6867a7238c14042f34b3b143fdfcf'}
R54_CLOSED = {'path': 'C:\\workspace\\ck3_lyd_runtime_20261004\\i4-root-storage-admission-20261011-008\\CLOSED-RESERVATION.actual.json', 'bytes': 6414, 'sha256': '87f9756d18edd0d0b48f007be7799090b11ab3d4d573f7979e832936a23a5876'}
R55_CLOSED = {'path': 'C:\\workspace\\ck3_lyd_runtime_20261004\\i4-root-storage-admission-20261011-011\\CLOSED-RESERVATION.actual.json', 'bytes': 7496, 'sha256': '698328e9cef1661e3f26fe4f2bf6540adb6907e54a8d445af3a198d991cc7ae3'}


def require(value, message):
 if not value: raise RuntimeError(message)


def now():
 return datetime.now(timezone.utc).isoformat()


def pin(path, limit=8*1048576):
 path=Path(path).resolve()
 require(path.stat().st_size<=limit,'Bounded source/metadata file only')
 raw=path.read_bytes()
 return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def equal_pin(a,b):
 return Path(a['path']).resolve()==Path(b['path']).resolve() and all(a[k]==b[k] for k in ('bytes','sha256'))


def checked(ref):
 require(equal_pin(pin(ref['path']),ref),'Pinned metadata/source changed: '+ref['path'])
 return json.loads(Path(ref['path']).read_text(encoding='utf-8-sig'))


def write_new(path,value):
 raw=(json.dumps(value,indent=2)+'\n').encode('utf-8')
 require(len(raw)<=1048576,'Compact receipt exceeded1MiB')
 with Path(path).open('xb') as f:
  f.write(raw);f.flush();os.fsync(f.fileno())


def imported(name,ref):
 require(equal_pin(pin(ref['path']),ref),'Reviewed mature helper changed')
 spec=importlib.util.spec_from_file_location(name,ref['path'])
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module


def load():
 require(socket.gethostname()=='BF-202609141645','Wrong machine')
 policy_path=Path('C:/workspace/ck3_eternal_recurrence/docs/storage-retention-policy.json')
 require(pin(policy_path)['sha256']=='ca60e36bef8e59ffafa939689a6ba4106420f20b7c2db19a1199d6408b3131e5',
  'Reviewed retention policy changed')
 policy=json.loads(policy_path.read_text(encoding='utf-8-sig'))
 require(policy['policy_version']=='1.0.0' and policy['lifecycle']['superseded_or_rebuildable_may_expire_early'],
  'Conditional early duplicate retirement not supported by actual policy')
 require(equal_pin(pin(BACKEND['path']),BACKEND),'Reviewed native backend changed')
 old=imported('r54_reviewed_indexed_helpers',INDEXED)
 core=imported('r54_reviewed_native_helpers',NATIVE)
 native=core.Win32Backend();native._api()
 manifest_pin=pin(MANIFEST)
 require(manifest_pin['bytes']==687704 and manifest_pin['sha256']==MANIFEST_SHA,'Retained seed manifest changed')
 seed=checked(manifest_pin)
 require(seed['schema']=='ck3-mod-acceptance-shader-cache-seed-v2'
  and Path(seed['snapshot_root']).resolve()==MANIFEST.parent
  and seed['startup_qualified'] is False and seed['business_pass'] is False,'Wrong immutable derivative seed')
 source_root=MANIFEST.parent/'shadercache'
 require(not source_root.resolve().is_relative_to(TARGET.resolve())
  and not TARGET.resolve().is_relative_to(source_root.resolve()),'Recovery/deletion roots overlap')
 rows=seed['files'];seen=set()
 for row in rows:
  relative=old.safe_relative(row['relative_path'])
  require(set(row)=={'relative_path','bytes','sha256'} and relative.casefold() not in seen
   and type(row['bytes']) is int and row['bytes']>=0 and len(row['sha256'])==64
   and all(c in '0123456789abcdef' for c in row['sha256']),'Invalid/duplicate manifest row')
  seen.add(relative.casefold())
  require((TARGET/relative).absolute().is_relative_to(TARGET)
   and (source_root/relative).absolute().is_relative_to(source_root),'Manifest path escaped exact roots')
 require(len(rows)==3740 and sum(row['bytes'] for row in rows)==146942067,'Selected exact cache inventory differs')
 return old,core,native,manifest_pin,source_root,rows


def closed_context(manifest_pin):
 facts=checked(FACTS)
 require(Path(facts['target_root']).resolve()==TARGET and equal_pin(facts['retained_seed_manifest'],manifest_pin)
  and facts['candidate_files']==3740 and facts['candidate_logical_bytes']==146942067,
  'Original narrow candidate target/seed/inventory changed')
 for ref in (R54_CLOSED,R55_CLOSED):
  value=checked(ref)
  require(value['schema']=='lyd-manual-coordinated-storage-reservation-closure-v1'
   and value['status']=='CLOSED_NO_FURTHER_WRITES_RESERVED' and value['owner_task']==ROOT
   and value['coordinator_task']==COORD and value['machine_id']=='BF-202609141645'
   and value['remaining_reserved_peak_bytes']==0 and value['runtime_or_business_qualification'] is False
   and value['retention']['original_cold_cache_review_unchanged_at_utc']==EXPIRY
   and value['retention']['automatic_TTL_renewal'] is False,
   'Pinned actual administrative closure/protection differs')
 latest=checked(R55_CLOSED)
 require(equal_pin(latest['actual_new_immutable_seed'],manifest_pin),
  'R55 actual closure does not bind retained R54 immutable seed')
 return {'candidate':FACTS,'R54_closed':R54_CLOSED,'R55_closed':R55_CLOSED}


def fresh(receipt,manifest_pin):
 require(receipt is not None,'Fresh actual ROOT consumer proof required; no deletion without it')
 ref=pin(receipt);value=checked(ref)
 moment=datetime.fromisoformat(value['at_utc'].replace('Z','+00:00'))
 require(moment.tzinfo is not None and 0<=(datetime.now(timezone.utc)-moment).total_seconds()<=300,
  'ROOT consumer proof older5min')
 keys={'schema','at_utc','reviewer','exact_target_root','current_seed_manifest','R54_closed','R55_closed',
  'direct_related_processes','relevant_process_access_unknown','current_ROOT_plan_original_root_dependencies',
  'old_target_cache_not_in_current_runtime_inputs','retained_seed_and_origin_evidence_kept',
  'Source14_CASE6_R55_profiles_kept','actual_process_probe_method','only_redundant_payload_protection_released',
  'original_review_at_utc_unchanged'}
 require(set(value)==keys and value['schema']=='ck3-r54-cache-root-consumer-proof-v1'
  and value['reviewer']=='/root' and Path(value['exact_target_root']).resolve()==TARGET
  and equal_pin(value['current_seed_manifest'],manifest_pin)
  and equal_pin(value['R54_closed'],R54_CLOSED) and equal_pin(value['R55_closed'],R55_CLOSED)
  and value['direct_related_processes']==[] and value['relevant_process_access_unknown']==[]
  and value['current_ROOT_plan_original_root_dependencies']==[]
  and value['old_target_cache_not_in_current_runtime_inputs'] is True
  and value['retained_seed_and_origin_evidence_kept'] is True and value['Source14_CASE6_R55_profiles_kept'] is True
  and value['only_redundant_payload_protection_released'] is True
  and value['original_review_at_utc_unchanged']==EXPIRY
  and isinstance(value['actual_process_probe_method'],str) and value['actual_process_probe_method'].strip(),
  'Actual ROOT current consumers/process access/limited protection release proof incomplete')
 closed_context(manifest_pin)
 require(pin(CLI)['sha256'].upper()==CLI_SHA,'Exact task-bus CLI changed')
 cmd=[sys.executable,'-B','-X','utf8',str(CLI),'--expected-cli-sha256',CLI_SHA,'list','--stale-after','600']
 result=subprocess.run(cmd,capture_output=True,check=True,timeout=30)
 require(len(result.stdout)<=1048576,'Fresh bus response exceeds bound')
 packet=json.loads(result.stdout);require(packet.get('ok') is True,'Fresh bus list failed')
 registered=[r for r in packet['tasks'] if r.get('state') in ('running','waiting')]
 active={r['task_id']:r for r in registered if not r.get('stale')}
 require(set(active)=={ROOT,COORD} and active[ROOT]['resources']==[]
  and active[COORD]['resources']==['storage-volume-c:coordinator']
  and not any('ck3-screen:acquired' in r.get('resources',[]) for r in registered),
  'Fresh actual ROOT/coordinator/no-screen ownership differs')
 return {'ROOT_consumer_proof':ref,'bus_command':cmd,'bus_stdout_bytes':len(result.stdout),
  'bus_stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'at_utc':now()}


def guard_leaf(stack,old,core,native,path,expected,access,share):
 core.parents(stack,native,path)
 handle=core.opened(stack,native,path,access,share)
 info=old.ordinary_file(core,native,handle,path,expected['bytes'])
 return handle,info


def plan(values,args):
 old,core,native,manifest_pin,source_root,rows=values
 for name in ('ROOT-PROTECTION-NARROWING.actual.json','IDENTITIES.plan.jsonl','PLAN.actual.json'):
  require(not (HERE/name).exists(),'Create-only plan already attempted; preserve partial')
 require(args.reviewer=='/root' and not args.release_original_protection and args.consumer_receipt is None,
  'Read-only metadata plan neither releases protection nor consumes an apply review')
 context=closed_context(manifest_pin);started=time.monotonic();metadata_objects=0
 with ExitStack() as roots,(HERE/'IDENTITIES.plan.jsonl').open('xb') as audit:
  ti=old.root_guard(roots,core,native,TARGET)
  si=old.root_guard(roots,core,native,source_root)
  metadata_objects+=len(TARGET.parents)+len(source_root.parents)+2
  require(old.root_identity(ti)!=old.root_identity(si),'Source and target native root identities alias')
  for i,row in enumerate(rows):
   require(time.monotonic()-started<=120,'Read-only metadata plan exceeded120s; preserve partial, do not apply')
   relative=row['relative_path'];sp=source_root/relative;tp=TARGET/relative
   metadata_objects+=len(sp.parents)+len(tp.parents)+2
   require(metadata_objects<=100000,'Read-only metadata plan exceeded100000 objects')
   with ExitStack() as held:
    _,sinfo=guard_leaf(held,old,core,native,sp,row,0x80,3)
    _,tinfo=guard_leaf(held,old,core,native,tp,row,0x80,3)
    require(old.root_identity(sinfo)!=old.root_identity(tinfo),'Source/target native FILEID aliases')
    audit.write((json.dumps({'i':i,'s':old.compact(sinfo),'t':old.compact(tinfo)},separators=(',',':'))+'\n').encode('utf-8'))
  audit.flush();os.fsync(audit.fileno())
 require(time.monotonic()-started<=120,'Read-only metadata plan exceeded120s')
 require((HERE/'IDENTITIES.plan.jsonl').stat().st_size<=4*1048576,'Identity audit exceeds4MiB')
 write_new(HERE/'PLAN.actual.json',{'schema':'ck3-r54-cache-exact-native-plan-v1','at_utc':now(),
  'executor':pin(__file__),'manifest':manifest_pin,'closed_context':context,
  'target_root':str(TARGET),'source_root':str(source_root),'target_root_identity':old.root_identity(ti),
  'source_root_identity':old.root_identity(si),'identities':pin(HERE/'IDENTITIES.plan.jsonl'),
  'count':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'max_batch':1000,'batches':4,
  'metadata_objects_including_parent_guards':metadata_objects,'elapsed_seconds':time.monotonic()-started,
  'body_reads_or_deletion':False,'metadata_birth_mtime_preserved':True,'original_review_unchanged':EXPIRY,
  'protection_release':'PROPOSED_ONLY_ROOT_FRESH_APPLY_REVIEW_REQUIRED','byte_equality':'UNKNOWN_NOT_HASHED',
  'actual_reclaimed_bytes':0,'prior_five_SAVE_or_R52_credit_repeated':False})
 print(json.dumps({'plan':pin(HERE/'PLAN.actual.json'),'actual_deletions':0}))


def apply(values,args):
 old,core,native,manifest_pin,source_root,rows=values
 require(type(args.batch) is int and 0<=args.batch<4,'Explicit single batch0..3 only')
 n=args.batch;stem='BATCH-'+str(n).zfill(3)
 paths={k:HERE/(stem+suffix) for k,suffix in [('claim','.claim.json'),('ledger','.detail.jsonl'),
  ('result','.actual.json'),('cursor','.cursor.json')]}
 require(all(not p.exists() for p in paths.values()),'Batch already claimed/partially attempted; NEVER REPLAY')
 planned=checked(pin(HERE/'PLAN.actual.json'))
 require(planned['schema']=='ck3-r54-cache-exact-native-plan-v1' and equal_pin(planned['executor'],pin(__file__))
  and equal_pin(planned['manifest'],manifest_pin),'Reviewed plan/executor/seed differs')
 require(args.reviewer=='/root' and args.release_original_protection,
  'ROOT explicit conditional duplicate protection release required')
 require(planned['closed_context']==closed_context(manifest_pin)
  and planned['count']==3740 and planned['logical_bytes']==146942067 and planned['max_batch']==1000
  and planned['batches']==4 and planned['original_review_unchanged']==EXPIRY,
  'Reviewed narrow plan/closures/count/expiry changed')
 require(equal_pin(pin(planned['identities']['path']),planned['identities']),'Identity plan changed')
 predecessor=None
 if n:
  predecessor=pin(HERE/('BATCH-'+str(n-1).zfill(3)+'.cursor.json'))
  previous=checked(predecessor)
  require(previous['ok'] is True and previous['next_batch']==n
   and equal_pin(previous['plan'],pin(HERE/'PLAN.actual.json')),'Previous batch not fully closed; no automatic retry')
 begin,end=n*1000,min((n+1)*1000,len(rows))
 checks=fresh(args.consumer_receipt,manifest_pin)
 decision_path=HERE/'ROOT-PROTECTION-NARROWING.actual.json'
 if n==0:
  require(not decision_path.exists(),'Original protection decision already attempted; preserve it')
  write_new(decision_path,{'schema':'ck3-r54-cache-conditional-protection-narrowing-v1','at_utc':now(),
   'reviewer':args.reviewer,'target_root':str(TARGET),'replacement_manifest':manifest_pin,
   'original_review_at_utc_unchanged':EXPIRY,'plan':pin(HERE/'PLAN.actual.json'),
   'reason':'Only byte-identical redundant R54 mutable shadercache payload loses its rebuildable-copy owner use. Retained immutable R54 seed, actual origin metadata/business snapshots, Source14, CASE6 and R55 inputs remain protected. Held source/target SHA equality required for each exact file.',
   'only_byte_identical_redundant_payload_release':True,'changed_unique_busy_unlisted_files_retained':True,
   'ROOT_consumer_proof':checks,'runtime_or_business_credit':False,'automatic_TTL_renewal':False})
 decision=checked(pin(decision_path))
 require(decision['reviewer']=='/root' and decision['only_byte_identical_redundant_payload_release'] is True
  and equal_pin(decision['plan'],pin(HERE/'PLAN.actual.json'))
  and equal_pin(decision['replacement_manifest'],manifest_pin)
  and Path(decision['target_root']).resolve()==TARGET and decision['original_review_at_utc_unchanged']==EXPIRY,
  'Original payload protection was not explicitly narrowly released for this exact plan')
 write_new(paths['claim'],{'at_utc':now(),'batch':n,'begin':begin,'end':end,'plan':pin(HERE/'PLAN.actual.json'),
  'checks':checks,'predecessor_cursor':predecessor,'never_replay':True})
 before=shutil.disk_usage('C:/').free;started=now();deleted=logical=allocated=0;failure=None
 with paths['ledger'].open('xb') as ledger:
  def event(value):
   raw=(json.dumps({'at_utc':now(),**value},separators=(',',':'))+'\n').encode('utf-8')
   require(ledger.tell()+len(raw)<=2*1048576,'Single batch audit exceeds2MiB')
   ledger.write(raw);ledger.flush();os.fsync(ledger.fileno())
  try:
   with ExitStack() as roots,Path(planned['identities']['path']).open('r',encoding='utf-8') as identities:
    ti=old.root_guard(roots,core,native,TARGET);si=old.root_guard(roots,core,native,source_root)
    require(old.root_identity(ti)==planned['target_root_identity'] and old.root_identity(si)==planned['source_root_identity'],
     'Native root identity changed')
    for i in range(begin):
     record=json.loads(identities.readline());require(record['i']==i,'Identity plan reordered')
    for i in range(begin,end):
     row=rows[i];record=json.loads(identities.readline());require(record['i']==i,'Identity plan reordered')
     relative=row['relative_path'];target_path=TARGET/relative;source_path=source_root/relative
     disposition=closed=absent=False
     try:
      with ExitStack() as held:
       sh,sinfo=guard_leaf(held,old,core,native,source_path,row,0x80000000|0x80,1)
       th,tinfo=guard_leaf(held,old,core,native,target_path,row,0x10000|0x80000000|0x80,1)
       require(old.compact(sinfo)==record['s'] and old.compact(tinfo)==record['t'],
        'Planned source/target FILEID/mtime/size/attributes changed')
       require(old.root_identity(sinfo)!=old.root_identity(tinfo),'Source and target FILEID aliases')
       source_SHA=old.hash_handle(native,sh,row);target_SHA=old.hash_handle(native,th,row)
       require(source_SHA==target_SHA==row['sha256'],'Original held source and target must both equal manifest SHA')
       require(old.compact(core.meta(native,sh,source_path))==record['s']
        and old.compact(core.meta(native,th,target_path))==record['t'],'Held source/target metadata changed while hashing')
       allocation=old.allocated_size(native,th,row['bytes'])
       event({'event':'intent','i':i,'source_SHA':source_SHA,'target_SHA':target_SHA,
        's':record['s'],'t':record['t'],'logical_bytes':row['bytes'],'allocation_size_api_bytes':allocation,
        'source_READ_handle_held':True,'target_DELETE_READ_handle_held':True,'share_mode':1})
       class DISPOSITION(ctypes.Structure):
        _fields_=[('DeleteFile',ctypes.c_ubyte)]
       flag=DISPOSITION(1)
       native._ok(native.SetFileInfo(th,4,ctypes.byref(flag),ctypes.sizeof(flag)));disposition=True
       core.HANDLE_CLOSERS[th]();closed=True
       try: target_path.lstat()
       except FileNotFoundError: absent=True
       require(absent,'Disposition/close acknowledged but target path still exists')
       event({'event':'actual','i':i,'disposition_ack':True,'close_ack':True,'absent':True,
        'source_handle_held_through_absence_readback':True})
       deleted+=1;logical+=row['bytes'];allocated+=allocation
     except Exception as error:
      failure={'i':i,'error':str(error),'disposition_ack':disposition,'close_ack':closed,'absence_observed':absent}
      event({'event':'failure_stop','failure':failure});break
  except Exception as error:
   failure={'error':str(error)};event({'event':'fatal_stop','failure':failure})
 finished=datetime.now(timezone.utc);after=shutil.disk_usage('C:/').free
 ok=failure is None and deleted==end-begin
 result={'schema':'ck3-r54-cache-exact-batch-result-v1','started_at_utc':started,'finished_at_utc':finished.isoformat(),
  'batch':n,'begin':begin,'end':end,'claim':pin(paths['claim']),'plan':pin(HERE/'PLAN.actual.json'),
  'deleted_files':deleted,'logical_deleted_bytes':logical,'allocation_size_api_deleted_sum':allocated,
  'free_before':before,'free_after':after,'global_free_delta_not_exclusive_cleanup_credit':after-before,
  'ok':ok,'failure_or_null':failure,'detail':pin(paths['ledger']),'original_review_unchanged':EXPIRY,
  'identity_and_detail_retention_expires_at_utc':(finished+timedelta(days=30)).isoformat(),
  'compact_summary_review_at_utc':(finished+timedelta(days=180)).isoformat(),
  'old_R54_cache_metadata_historical_not_current_availability':True,'seed_and_original_failure_evidence_retained':True,
  'recursive_directory_deletion':False,'automatic_retry':False,'business_credit':False}
 write_new(paths['result'],result)
 write_new(paths['cursor'],{'at_utc':now(),'ok':ok,'batch':n,'next_batch':n+1 if ok else None,
  'plan':pin(HERE/'PLAN.actual.json'),'actual_result':pin(paths['result']),
  'availability':'EXACT_ORDINAL_BATCH_PAYLOAD_DELETED' if ok else 'PARTIAL_OR_NOT_DELETED_DO_NOT_REPLAY',
  'manifest_ordinals':[begin,end],'retained_reconstruction_manifest':manifest_pin,'retained_source_root':str(source_root),
  'original_review_unchanged':EXPIRY,'TTL_auto_renewal':False})
 print(json.dumps({'result':pin(paths['result']),'cursor':pin(paths['cursor']),'ok':ok,'deleted_files':deleted}))
 require(ok,'Batch incomplete; preserve original failure/partial, never automatically retry')


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 modes=parser.add_mutually_exclusive_group(required=True)
 modes.add_argument('--plan',action='store_true');modes.add_argument('--apply',action='store_true')
 parser.add_argument('--batch',type=int);parser.add_argument('--consumer-receipt',type=Path)
 parser.add_argument('--reviewer',choices=['/root'],required=True)
 parser.add_argument('--release-original-protection',action='store_true')
 args=parser.parse_args()
 require(LOCK.is_file(),'Existing ROOT volume coordinator lock required')
 with LOCK.open('r+b') as lock:
  lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
  try:
   values=load()
   if args.plan: plan(values,args)
   else: apply(values,args)
  finally:
   lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)


if __name__=='__main__': main()
