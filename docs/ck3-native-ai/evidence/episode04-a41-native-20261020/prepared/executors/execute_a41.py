"""One bounded A41 invocation of sealed public argv; no hidden fallback/retry."""
from pathlib import Path
import argparse,ctypes,datetime as dt,hashlib,json,os,re,subprocess,sys,time
from ctypes import wintypes as w
O=Path(__file__).parent;R=Path('D:/workspace/ck3_eternal_recurrence');B=Path('C:/w/e04a41')
CAP=O.parent/'capacity/A41-C-NATIVE-SOURCE-BOUND.actual-a01.json'
CAPSHA='1f66dad3c016ab88e8bc52d3b399591041440302b27dbca7a988c27077d8cb54'
PLAN=O/'A41-RELOCATION-WORKER-PLAN.prepared-a02.json'
PLANSHA='96bc09b43fd8f6daa40853e9d0760fbc338d13034f1c3978935d5d2bda307606'
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
 return pin(p)
def query(argv):return subprocess.check_output(argv,cwd=R,text=True,encoding='utf-8').strip()
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetProcessTimes.argtypes=[w.HANDLE,*[ctypes.POINTER(w.FILETIME)]*4];k.GetProcessTimes.restype=w.BOOL
k.GetCurrentProcess.restype=w.HANDLE
def life(pid,handle):
 c,e,kt,ut=[w.FILETIME() for _ in range(4)]
 if not k.GetProcessTimes(handle,ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut)):raise ctypes.WinError(ctypes.get_last_error())
 return {'pid':pid,'creation_filetime':(c.dwHighDateTime<<32)|c.dwLowDateTime}
a=argparse.ArgumentParser();a.add_argument('--stage',choices=['main','worker'],required=True);a.add_argument('--worker-source-head');a.add_argument('--Root-worker-release-source');args=a.parse_args()
assert pin(CAP)['sha256']==CAPSHA and pin(PLAN)['sha256']==PLANSHA
cap=load(CAP);plan=load(PLAN);assert cap['producer_plan']==pin(PLAN)
fresh=cap['fresh_stage_helper'];assert pin(fresh['path'])==fresh
common_ref=next(x for x in cap['scheme_sources'] if Path(x['path']).name=='capacity_common.py');assert pin(common_ref['path'])==common_ref
sys.path.insert(0,str(Path(common_ref['path']).parent));import capacity_common as capacity
for ref in plan['entry_dependencies']:assert pin(ref['path'])==ref
if args.stage=='worker':assert args.worker_source_head and args.Root_worker_release_source
B.mkdir(exist_ok=True);phases=B/'qualification-phases';phases.mkdir(exist_ok=True)
parent=life(os.getpid(),k.GetCurrentProcess());peak=0;guard_count=0;minima={};protocol=[]
def footprint():
 for attempt in range(3):
  try:
   total=0
   for base,dirs,files in os.walk(B,followlinks=False):
    for n in dirs+files:
     p=Path(base)/n;s=p.stat(follow_symlinks=False)
     assert not getattr(s,'st_file_attributes',0)&0x400,'Reparse in owned root'
     if n in files:total+=s.st_size
   return total
  except FileNotFoundError:
   if attempt==2:raise
def guard():
 global peak,guard_count,minima
 assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(plan['hard_deadline_utc'].replace('Z','+00:00'))
 for attempt in range(3):
  try:ledger,identity,ref=capacity.snapshot();break
  except capacity.StorageConflict:
   if attempt==2:raise
 balances=capacity.balances(ledger);vol=capacity.volumes();budget=capacity.budget(vol,balances)
 for key in ['C_floor_margin_bytes','C_quota_margin_bytes','D_floor_margin_bytes']:
  minima[key]=min(minima.get(key,budget[key]),budget[key]);assert budget[key]>=0,(key,budget[key])
 claim=next(c for c in ledger['claims'] if c.get('state')=='active' and c['task_id']==capacity.T)
 assert claim['native_source_bound_capacity']==pin(CAP) and claim['native_a41_remaining_future_bytes']==805306368
 total=footprint();assert total<=cap['new_native_root_ceiling_bytes'] and total+33554432<=805306368
 peak=max(peak,total);guard_count+=1
 return {'observed_at_utc':now(),'native_root_bytes':total,'native_plus_full_protocol_charge':total+33554432,'budget':budget,'ledger':ref}
def fresh_phase(phase,directory):
 argv=[plan['python'],'-B','-X','utf8',fresh['path'],'--cap',str(CAP),'--cap-sha256',CAPSHA,'--phase',phase,'--output',str(directory/'capacity-fresh.actual.json')]
 if phase.startswith('worker_'):argv+=['--worker-source-head',args.worker_source_head]
 value=subprocess.run(argv,cwd=R,capture_output=True,text=True,encoding='utf-8')
 if value.returncode:raise RuntimeError('Fresh phase rejected: '+value.stderr+value.stdout)
 out=directory/'capacity-fresh.actual.json';v=load(out);assert v['admitted'] and v['phase_capacity_admissible'] and v['budget_status']=='GREEN'
 return pin(out)
env=os.environ.copy();temp=B/'.executor-temp';temp.mkdir(exist_ok=True)
env.update(TEMP=str(temp),TMP=str(temp),PYTHONPYCACHEPREFIX=str(B/'.executor-python-cache'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',VSLANG='1033')
def run_phase(phase):
 directory=phases/phase;directory.mkdir(exist_ok=False)
 before=guard();fresh_ref=fresh_phase(phase,directory)
 argv=[x.replace('{SOURCE_BOUND_CAPACITY_PATH}',str(CAP)).replace('{SOURCE_BOUND_CAPACITY_SHA256}',CAPSHA) for x in plan['phase_argv'][phase]]
 intent={'schema':'xar.e04.a41-phase-intent.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'phase':phase,'argv':argv,'cwd':str(R),'capacity':pin(CAP),'fresh_capacity':fresh_ref,'producer_plan':pin(PLAN),'executor':pin(__file__),'parent':parent,
  'actual_repository_head':query(['git','rev-parse','HEAD']),'actual_repository_status_porcelain':query(['git','status','--porcelain']),'native_tree':plan['native_tree'],'before_guard':before,
  'Root_worker_release':{'source':args.Root_worker_release_source,'actual_released_clean_HEAD':args.worker_source_head} if phase.startswith('worker_') else None}
 write(directory/'intent.actual.json',intent)
 stdout=directory/'stdout.txt';stderr=directory/'stderr.txt';failure=None
 with stdout.open('xb') as out,stderr.open('xb') as err:
  p=subprocess.Popen(argv,cwd=R,env=env,stdout=out,stderr=err);child=life(p.pid,int(p._handle));write(directory/'Popen.actual.json',{'machine_id':plan['machine_id'],'observed_at_utc':now(),'parent':parent,'child':child,'argv':argv})
  print(json.dumps({'phase':phase,'Popen':child}),flush=True)
  while p.poll() is None:
   try:guard()
   except Exception as e:
    failure=repr(e)
    if p.poll() is None:
     assert life(p.pid,int(p._handle))==child
     subprocess.run(['taskkill.exe','/PID',str(p.pid),'/T','/F'],capture_output=True)
    break
   time.sleep(1)
  code=p.wait()
 after=guard()
 result={'schema':'xar.e04.a41-phase-result.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'phase':phase,'Popen':child,'original_wait_return_code':code,'guard_failure':failure,'stdout':pin(stdout),'stderr':pin(stderr),'intent':pin(directory/'intent.actual.json'),'after_guard':after,'guard_observations':guard_count,'peak_root_bytes':peak,'minimum_budget_margins':minima}
 ref=write(directory/'result.actual.json',result)
 if code or failure:raise RuntimeError('Actual phase failed: '+phase+' '+str(code)+' '+str(failure))
 return ref
def verified_system(receipt_path,expected):
 receipt=load(receipt_path)
 assert receipt['status']=='verified' and receipt['admin_token'] is True and receipt['system_token_sid']=='S-1-5-18'
 assert receipt['missing_requested_paths']==[]
 actual={(str(Path(x['path']).resolve()),x['sha256']) for x in receipt['files']}
 assert actual==expected,(actual,expected)
 # Private data is not enumerated. Derive exact owned logical bytes from fixed writer + actual protected request/receipt.
 proofdirs=list(Path(receipt_path).parent.glob('broker-proof-*'));assert len(proofdirs)==1
 proofdir=proofdirs[0];req=(proofdir/'request.json').read_bytes();rv=json.loads(req);raw=(proofdir/'protected-worker-receipt.json').read_bytes();sv=json.loads(raw)
 assert sv['broker_identity']['request_id']==rv['request_id'] and sv['broker_identity']['request_sha256']==hashlib.sha256(req).hexdigest()
 marker=json.dumps({'request_id':rv['request_id'],'request_sha256':hashlib.sha256(req).hexdigest()},sort_keys=True,separators=(',',':')).encode()+b'\n'
 protocol.append({'request_id':rv['request_id'],'actual_raw_request_bytes':len(req),'actual_protected_result_bytes':len(raw),'two_private_marker_bytes':2*len(marker),'derived_fixed_protocol_growth_bytes':2*len(req)+2*len(marker)+len(raw),'formula':'inbox raw + frozen raw + 2 canonical markers + protected result; installed fixed writer contract, not a private-directory measurement','protected_result':pin(proofdir/'protected-worker-receipt.json')})
 assert sum(x['derived_fixed_protocol_growth_bytes'] for x in protocol)<=33554432
 return pin(receipt_path)
results={}
try:
 if args.stage=='main':
  for phase in list(plan['phase_argv'])[:5]:results[phase]=run_phase(phase)
  configured=load(B/'producer-configure-a01/native-msvc-result.json')
  assert configured['configured'] is True and configured['built'] is False and configured['status']=='configured'
  relocation=load(B/'A41-RELOCATION.actual-a01.json');assert relocation['new_compile_performed'] is False and len(relocation['relocated_EXEs'])==3
  expected={(str(Path(x['destination']['path']).resolve()),x['destination']['sha256']) for x in relocation['relocated_EXEs']}
  system=verified_system(B/'relocation-registration-a01/receipt.json',expected)
  ui=(phases/'main_UI_finite_cold/stdout.txt').read_text(encoding='utf-8',errors='replace')
  assert re.search(r'100% tests passed, 0 tests failed out of 1\b',ui) and re.search(r'1/1 Test\s+#\d+: xar_ck3_ingame_ui_navigation_v1_test\s+\.+\s+Passed',ui),ui
  q={'schema':'xar.e04.a41-main-relocation-qualification.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'status':'MAIN_RELOCATED_BYTES_SYSTEM3_AND_EXACT_UI1_PASS_WORKER_PENDING',
   'source_head':plan['original_compile_source_head'],'native_build_source_head':plan['original_compile_source_head'],'native_tree':plan['native_tree'],'production_bytes_qualified':True,'focused_UI_cold_qualified':True,'focused_cold_qualified':False,
   'original_compile_source_head':plan['original_compile_source_head'],'original_compile_result':plan['original_public_producer_result'],'new_main_compile_performed':False,
   'genuine_configure_result':pin(B/'producer-configure-a01/native-msvc-result.json'),'relocation':pin(B/'A41-RELOCATION.actual-a01.json'),'real_new_manifest':pin(B/'relocation-registration-a01/manifest.json'),'SYSTEM_receipt':system,
   'carrier_module':plan['carrier_DLL'],'relocated_EXEs':relocation['relocated_EXEs'],'phases':results,'protocol_growth_by_actual_request':protocol,
   'root_peak_bytes_known':peak,'fixed_protocol_charge_bytes':33554432,'minimum_budget_margins':minima,'worker_scope_actual':'NOT_EXECUTED_PENDING_ROOT_NEW_CLEAN_HEAD','game_SDK_screen_live_observer_executed':False}
  print(json.dumps({'main_qualification':write(B/'ROOT-A41-MAIN-RELOCATION-QUALIFICATION.actual-a01.json',q)}),flush=True)
 else:
  assert (B/'ROOT-A41-MAIN-RELOCATION-QUALIFICATION.actual-a01.json').is_file()
  for phase in ['worker_live_actual_configure_build','worker_V5_actual_configure_build']:
   results[phase]=run_phase(phase)
   argv=plan['phase_argv'][phase];build=Path(argv[argv.index('--build-dir')+1]);report=load(build/'native-msvc-result.json')
   assert report['built'] is True and report['status']=='built' and report['build_succeeded'] is True
   manifest=load(report['defender_exclusions']['manifest']);ref=verified_system(report['defender_exclusions']['receipt'],{(str(Path(x['path']).resolve()),x['sha256']) for x in manifest['files']})
   assert ref['sha256']==report['defender_exclusions']['receipt_sha256']
  v5=B/'refill-worker-cold-a01';br=load(v5/'native-msvc-result.json')
  binding={'schema':'xar.refill.worker_cold_build_binding.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'build_result':pin(v5/'native-msvc-result.json'),'system_receipt':pin(br['defender_exclusions']['receipt']),'source_manifest':plan['worker_source_manifest']}
  write(v5/'BUILD-BINDING.actual-a01.json',binding)
  results['worker_V5_two_owned_cases']=run_phase('worker_V5_two_owned_cases')
  write(B/'A41-WORKER-PHASES-COMPLETED.actual-a01.json',{'machine_id':plan['machine_id'],'observed_at_utc':now(),'phases':results,'actual_clean_invocation_HEAD':args.worker_source_head,'Root_release_source':args.Root_worker_release_source,'source_layers':plan['source_layers'],'protocol_growth_by_actual_request':protocol,'root_peak_bytes_known':peak,'minimum_budget_margins':minima,'qualification_pending_independent_actual_readback':True})
except Exception as e:
 failure={'schema':'xar.e04.a41-executor-failure.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'stage':args.stage,'error':repr(e),'parent':parent,'completed_phase_results':results,'protocol_growth_known':protocol,'protocol_actual_unknown_until_verified_if_missing':True,'qualification_granted':False,'remaining_scope_not_automatically_retried':True,'root_peak_bytes_known':peak}
 ref=write(B/('A41-'+args.stage.upper()+'-EXECUTOR-FAILURE.actual-a01.json'),failure);print(json.dumps({'actual_failure':ref,'error':repr(e)}),flush=True);raise
