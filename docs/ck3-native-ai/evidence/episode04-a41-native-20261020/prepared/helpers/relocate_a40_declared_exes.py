"""Fixed a40 EXE relocation and public CMake manifest; never compile/register/run."""
from pathlib import Path
from contextlib import ExitStack
import argparse, datetime as dt, hashlib, json, os, subprocess, sys

O=Path(__file__).parent
PLAN=O/'A41-RELOCATION-WORKER-PLAN.prepared-a01.json'
R=Path('D:/workspace/ck3_eternal_recurrence')
B=Path('C:/w/e04a41')
POLICY=Path('C:/Program Files/XAR CK3 Project EXE Broker/policy.json')
def now():return dt.datetime.now(dt.timezone.utc)
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def check(p,reference):
 actual=pin(p)
 if actual['bytes']!=reference['bytes'] or actual['sha256']!=reference['sha256']:raise RuntimeError('Exact input changed: '+str(p))
 return actual
def query(argv):return subprocess.check_output(argv,cwd=R,text=True,encoding='utf-8').strip()
def no_reparse(p):
 p=Path(p)
 for part in [p,*p.parents]:
  if part.exists() and getattr(part.lstat(),'st_file_attributes',0)&0x400:raise RuntimeError('Reparse path forbidden: '+str(part))
 if p.resolve()!=p.absolute():raise RuntimeError('Noncanonical fixed path')
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
 return pin(p)
def main():
 a=argparse.ArgumentParser();a.add_argument('--phase',choices=['relocate','manifest'],required=True)
 a.add_argument('--capacity',type=Path,required=True);a.add_argument('--capacity-sha256',required=True);args=a.parse_args()
 plan=json.loads(PLAN.read_bytes());capraw=args.capacity.read_bytes();cap=json.loads(capraw)
 if hashlib.sha256(capraw).hexdigest()!=args.capacity_sha256:raise RuntimeError('Capacity bytes changed')
 for k,v in [('machine_id',plan['machine_id']),('native_tree',plan['native_tree']),('build_execution_admitted',True),('aggregate_ceiling_bytes',805306368)]:
  if cap.get(k)!=v:raise RuntimeError('Capacity field differs: '+k)
 if cap['producer_plan']!=pin(PLAN):raise RuntimeError('Capacity does not bind this exact plan')
 if Path(cap['build_root']).resolve()!=B:raise RuntimeError('Wrong admitted root')
 if now()>=dt.datetime.fromisoformat(plan['hard_deadline_utc'].replace('Z','+00:00')):raise RuntimeError('Hard deadline reached')
 if query([sys.executable,'-B','-X','utf8',str(R/'tools/ck3_live_run_id.py'),'machine'])!=plan['machine_id']:raise RuntimeError('Machine differs')
 native=R/'ck3_autonomous_player/native_bridge'
 if query(['git','status','--porcelain','--',str(native)]):raise RuntimeError('Native source is dirty')
 if query(['git','rev-parse','HEAD:ck3_autonomous_player/native_bridge'])!=plan['native_tree']:raise RuntimeError('Native tree differs')
 for ref in plan['entry_dependencies']:check(ref['path'],ref)
 check(POLICY,plan['installed_policy'])
 no_reparse(B)
 cache={}
 for line in (B/'CMakeCache.txt').read_text(encoding='utf-8',errors='replace').splitlines():
  if '=' in line and ':' in line.split('=',1)[0]:cache[line.split(':',1)[0]]=line.split('=',1)[1]
 for k,v in {**plan['all_feature_flags'],'BUILD_TESTING':'ON','CMAKE_BUILD_TYPE':'Release'}.items():
  if cache.get(k)!=v:raise RuntimeError('Actual configured flag differs: '+k)
 if Path(cache['CMAKE_HOME_DIRECTORY']).resolve()!=native or Path(cache['CMAKE_CACHEFILE_DIR']).resolve()!=B:raise RuntimeError('Actual cache source/build identity differs')
 import win32con,win32file
 original=[];copies=[]
 with ExitStack() as stack:
  for row in plan['original_artifacts']:
   source=Path(row['actual']['path']);no_reparse(source)
   handle=win32file.CreateFile(str(source),win32con.GENERIC_READ,win32con.FILE_SHARE_READ,None,win32con.OPEN_EXISTING,win32con.FILE_FLAG_OPEN_REPARSE_POINT,None)
   stack.callback(handle.Close);before=win32file.GetFileInformationByHandle(handle)
   if before[0]&0x400:raise RuntimeError('Reparse original forbidden')
   chunks=[];h=hashlib.sha256();size=0
   while True:
    data=win32file.ReadFile(handle,1024*1024)[1]
    if not data:break
    h.update(data);size+=len(data)
    if source.suffix.lower()=='.exe':chunks.append(data)
   if size!=row['actual']['bytes'] or h.hexdigest()!=row['actual']['sha256']:raise RuntimeError('Original compiled artifact changed')
   original.append({'target':row['target'],'pin':row['actual'],'held_file_identity':{'volume_serial':before[4],'file_index':(before[8]<<32)|before[9],'creation_time':str(before[1]),'last_write_time':str(before[3]),'links':before[7]}})
   if source.suffix.lower()=='.exe':
    destination=B/source.name
    if args.phase=='relocate':
     if now()>=dt.datetime.fromisoformat(plan['hard_deadline_utc'].replace('Z','+00:00')):raise RuntimeError('Hard deadline reached')
     with destination.open('xb') as f:
      for data in chunks:f.write(data)
    fresh=check(destination,row['actual']);copies.append({'target':row['target'],'source':row['actual'],'destination':fresh})
   if win32file.GetFileInformationByHandle(handle)!=before:raise RuntimeError('Held original identity changed')
  if len(copies)!=3:raise RuntimeError('Exactly three declared EXE copies required')
  base={'machine_id':plan['machine_id'],'observed_at_utc':now().isoformat(),'original_compile_source_head':plan['original_compile_source_head'],'native_tree':plan['native_tree'],
   'observed_repository_head':query(['git','rev-parse','HEAD']),'observed_repository_status_porcelain':query(['git','status','--porcelain']),
   'producer_plan':pin(PLAN),'capacity':pin(args.capacity),'originals':original,'relocated_EXEs':copies,
   'new_compile_performed':False,'SYSTEM_registration_performed':False,'EXE_executed':False,'qualification_granted':False}
  if args.phase=='relocate':
   base.update(schema='xar.e04.a41-compiled-exe-relocation.v1',status='RELOCATED_ORIGINAL_COMPILED_BYTES_NOT_RECOMPILED')
   result=write(B/'A41-RELOCATION.actual-a01.json',base)
  else:
   relocation=B/'A41-RELOCATION.actual-a01.json';old=json.loads(relocation.read_bytes())
   if old['relocated_EXEs']!=copies or old['new_compile_performed'] is not False:raise RuntimeError('Relocation receipt differs')
   sys.path.insert(0,str(R/'tools'));from register_project_exe_exclusions import collect_manifest
   manifest=collect_manifest(R,native,B,'Release',plan['registration_targets'])
   expected={(str(Path(x['destination']['path']).resolve()),x['destination']['sha256']) for x in copies}
   if {(x['path'],x['sha256']) for x in manifest['files']}!=expected:raise RuntimeError('Actual CMake declaration does not match exact copies')
   directory=B/'relocation-registration-a01';directory.mkdir(exist_ok=False)
   frozen=write(directory/'manifest.json',manifest)
   base.update(schema='xar.e04.a41-relocation-manifest-prepared.v1',status='REAL_CMAKE_GRAPH_AND_RELOCATED_EXACT_EXE_MANIFEST_PREPARED',relocation=pin(relocation),manifest=frozen)
   result=write(B/'A41-RELOCATION-MANIFEST.actual-a01.json',base)
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
