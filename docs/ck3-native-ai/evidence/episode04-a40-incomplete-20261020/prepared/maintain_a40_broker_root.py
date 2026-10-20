"""Fixed two-leaf a40 broker enrollment. Review by default; never accepts a root."""
from pathlib import Path
from contextlib import ExitStack
import argparse,datetime as dt,hashlib,json,os,sys,uuid,traceback
ROOT=Path('C:/Program Files/XAR CK3 Project EXE Broker')
HERE=Path('C:/ck3-e04-resume-20261020-a01/next-r06-a01/native-plan')
BUILD=HERE.parent/'native-build-a40-a01'
MID='desktop-3fevhd2-1c74096080';OWNER='S-1-5-21-4063940640-1897558599-686929869-1001'
RECEIPT=BUILD/'BROKER-EXACT-ROOT-MAINTENANCE.actual-a01.json'
OLD={'policy.json':(1088,'a7ce254d966b8303e1eba186c9fcad47d3265f2d51dac52e88c53446271e0243'),'installation-manifest.json':(1120,'2b24624cdc747b3c6fe82a58e28341102bd3bc979e066211e0cc93759912a673')}
NEW={'policy.json':('BROKER-POLICY-EXACT-A40-ROOT.candidate-a01.json',1157,'9b8d2f551b4b2c305d551522008cd19d2e3aa0fdc932d425bcacdba96b4da1d1'),'installation-manifest.json':('BROKER-INSTALLATION-MANIFEST-EXACT-A40-ROOT.candidate-a01.json',1119,'80670b731a5e173301117546de4ffbf4b770e681cb264fbed596ecf611d5e6a6')}
SEAL=(95324,'130d18a9d9bf8e4c9fc0038971f3214a3120616cc0843642825d56c6bd7ef0e2')
PRIMITIVES={'protected_runtime.py':(1813,'885d7ff841f23fe0052afe413ede380f9810bcb5f8db7cd188da326b2dfbbace'),'native_safety.py':(35834,'873ec34e49d2549493ffddeb934d4d7d12e7a97de76fecc43c5135c0ee5118e2'),'windows_adapter.py':(22706,'88eb97048190b3a0caf89941a77701dfd9c5434f0c5d32e1deda00056bcd9f82'),'installer_core.py':(12874,'090063ebf11e0e704a8c4fcb41034de5bd0e7c49a4c4253b053ff3a5ca15f493')}
def digest(b):return hashlib.sha256(b).hexdigest()
def checked(raw,pin):
 if (len(raw),digest(raw))!=tuple(pin):raise ValueError('exact admitted bytes differ')
 return raw
def pin(path):
 raw=Path(path).read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':digest(raw)}
def raw(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--expected-helper-sha256',required=True);a.add_argument('--apply',action='store_true');args=a.parse_args()
 if Path(__file__).resolve()!=HERE/'maintain_a40_broker_root.py':raise ValueError('fixed reviewed entry only')
 if digest(Path(__file__).read_bytes())!=args.expected_helper_sha256:raise ValueError('entry pin differs')
 if sys.flags.isolated!=1 or sys.flags.no_site!=1:raise ValueError('protected Python -I -S -B required')
 if Path(sys.executable).resolve()!=ROOT/'runtime/python.exe':raise ValueError('fixed protected Python only')
 for n,p in PRIMITIVES.items():checked((ROOT/n).read_bytes(),p)
 sys.path.insert(0,str(ROOT))
 from protected_runtime import activate_sealed_paths
 activate_sealed_paths(ROOT)
 from native_safety import NativeSafety
 from windows_adapter import WindowsInstallerAdapter,verify_outer_parents
 from installer_core import task_spec,strict_json
 from worker_core import parse_policy
 safety=NativeSafety(OWNER,str(ROOT/'private-frozen'),str(ROOT/'receipts'));adapter=WindowsInstallerAdapter(safety)
 facts={'schema':'xar.e04.a40-exact-broker-root-maintenance.v1','machine_id':MID,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'REVIEW_ONLY_NOT_INSTALLED','source_entry':pin(__file__),'source_candidates':{},'token_identity':adapter.token_identity(),'only_allowed_new_build_root':str(BUILD),'replaced_leaves':[],'settings_calls':0,'task_run_calls':0,'task_registration_calls':0}
 if args.apply and facts['token_identity']!={'sid':OWNER,'admin':True}:
  facts['status']='ADMIN_REQUIRED_NO_INSTALLED_WRITE';print(json.dumps(facts));return 3
 def idle():
  t=adapter._scheduler().GetFolder(task_spec(OWNER)['folder']).GetTask(task_spec(OWNER)['name'])
  if t.GetInstances(0).Count!=0:raise ValueError('fixed broker task must be idle')
 def read(path,size):
  with safety.lock_file(str(path)) as lease:return lease.read_bytes(max(size,1))
 def replace(name,before,data,tag):
  import win32file
  path=ROOT/name
  with safety.lock_dir(str(ROOT)):
   adapter._verify_acl(str(path),OWNER)
   checked(read(path,len(before)),(len(before),digest(before)))
   temp=str(path)+'.a40-'+tag+'.tmp'
   adapter._create_file_secure(temp,data,OWNER)
   checked(read(temp,len(data)),(len(data),digest(data)))
   idle();win32file.MoveFileEx(temp,str(path),1|8)
   proof=adapter._verify_acl(str(path),OWNER)
   checked(read(path,len(data)),(len(data),digest(data)))
   return proof
 with ExitStack() as hold:
  # Hold reviewed user inputs, candidates and all unchanged installed code.
  for path in [Path(__file__),*[HERE/x[0] for x in NEW.values()]]:
   lease=hold.enter_context(safety.lock_file(str(path),owner_sid=OWNER));content=lease.read_bytes(20000)
   if path.name=='maintain_a40_broker_root.py':
    if digest(content)!=args.expected_helper_sha256:raise ValueError('held entry differs')
   else:
    row=next(x for x in NEW.values() if x[0]==path.name);checked(content,row[1:]);facts['source_candidates'][path.name]=pin(path)
  verify_outer_parents(safety);hold.enter_context(safety.lock_dir(str(ROOT)))
  old={n:checked(read(ROOT/n,p[0]),p) for n,p in OLD.items()}
  new={n:checked((HERE/p[0]).read_bytes(),p[1:]) for n,p in NEW.items()}
  seal_raw=checked(read(ROOT/'runtime-seal.json',SEAL[0]),SEAL);seal=strict_json(seal_raw)
  policy=parse_policy(new['policy.json']);prior=strict_json(old['policy.json'])
  wanted=dict(prior);wanted['allowed_build_roots']=[*prior['allowed_build_roots'],str(BUILD)]
  if policy!=wanted:raise ValueError('policy delta is not the single exact a40 root')
  before_manifest=strict_json(old['installation-manifest.json']);after_manifest=strict_json(new['installation-manifest.json'])
  wanted_manifest=dict(before_manifest);wanted_manifest['policy']={'path':'policy.json','size':len(new['policy.json']),'sha256':digest(new['policy.json'])}
  if after_manifest!=wanted_manifest:raise ValueError('task/seal/manifest identity changed')
  facts['outer_and_source_scope_verified']=True;facts['before_acl']={n:adapter._verify_acl(str(ROOT/n),OWNER) for n in OLD}
  facts['task_before']=adapter.verify_task(task_spec(OWNER));idle()
  rows=seal['files'];facts['unchanged_sealed_file_count']=len(rows)
  for row in rows:
   if row['path'] in OLD:raise ValueError('mutable configuration unexpectedly in immutable runtime seal')
   path=ROOT/row['path'];safety.verify_protected_path(str(path))
   lease=hold.enter_context(safety.lock_file(str(path)));checked(lease.read_bytes(max(row['size'],1)),(row['size'],row['sha256']))
  lease=hold.enter_context(safety.lock_file(str(ROOT/'runtime-seal.json')));checked(lease.read_bytes(SEAL[0]),SEAL)
  facts['runtime_seal_before']=pin(ROOT/'runtime-seal.json')
  if not args.apply:print(json.dumps(facts));return 0
  if dt.datetime.now(dt.timezone.utc)>=dt.datetime.fromisoformat('2026-10-20T08:00:00+00:00'):raise ValueError('capacity hard deadline reached')
  if RECEIPT.exists():raise FileExistsError('preserve previous actual receipt')
  tag=uuid.uuid4().hex;archive=ROOT/'private-frozen'/('a40-exact-root-'+tag)
  facts['archive_path']=str(archive);facts['status']='APPLYING_TWO_REVIEWED_CONFIG_LEAVES'
  with safety.lock_dir(str(ROOT/'private-frozen')):adapter._create_directory_secure(str(archive),OWNER,'private')
  for n,b in old.items():
   dest=archive/(n+'.before');adapter._create_file_secure(str(dest),b,OWNER,'private');checked(read(dest,len(b)),(len(b),digest(b)))
  adapter._create_file_secure(str(archive/'metadata.json'),raw(facts),OWNER,'private')
  try:
   for n in OLD:
    facts.setdefault('replacement_acl',{})[n]=replace(n,old[n],new[n],tag);facts['replaced_leaves'].append(n)
   facts['task_after']=adapter.verify_task(task_spec(OWNER));idle()
   if facts['task_before']!=facts['task_after']:raise ValueError('fixed task definition or ACL changed')
   for row in rows:
    checked(read(ROOT/row['path'],row['size']),(row['size'],row['sha256']))
   checked(read(ROOT/'runtime-seal.json',SEAL[0]),SEAL)
   facts['after_files']={n:pin(ROOT/n) for n in OLD};facts['after_acl']={n:adapter._verify_acl(str(ROOT/n),OWNER) for n in OLD}
   if any(facts['before_acl'][n]['actual']['security']!=facts['after_acl'][n]['actual']['security'] for n in OLD):raise ValueError('config owner/DACL changed')
   facts.update(status='EXACT_A40_BUILD_ROOT_INSTALLED_AND_READ_BACK',runtime_code_task_seal_external_source_roots_unchanged=True,actual_defender_SYSTEM_registration_still_pending=True)
  except BaseException as error:
   facts.update(status='MAINTENANCE_FAILED_OR_PARTIAL',error=repr(error),traceback=traceback.format_exc(),rollback=[])
   for n in reversed(facts['replaced_leaves']):
    try:replace(n,new[n],old[n],tag+'rollback');facts['rollback'].append(n)
    except BaseException as rollback:facts.setdefault('rollback_errors',[]).append(repr(rollback))
  facts['finished_at_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
  adapter.write_new_external_receipt(str(RECEIPT),raw(facts))
  print(json.dumps({'status':facts['status'],'receipt':pin(RECEIPT)}))
  return 0 if facts['status']=='EXACT_A40_BUILD_ROOT_INSTALLED_AND_READ_BACK' else 1
if __name__=='__main__':raise SystemExit(main())
