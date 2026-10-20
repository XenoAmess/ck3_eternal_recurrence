"""Read actual completed selected receipts and publish bounded qualification/readback."""
from pathlib import Path
import ctypes,datetime as dt,hashlib,json,os,subprocess,sys
from ctypes import wintypes as w
O=Path(__file__).parent;R=Path('D:/workspace/ck3_eternal_recurrence');B=Path('C:/w/e04a41')
PLAN=O/'A41-RELOCATION-WORKER-PLAN.prepared-a04.json'
CAP=O.parent/'capacity/A41-C-NATIVE-SOURCE-BOUND.actual-a03.json'
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
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True,encoding='utf-8').strip()
plan=load(PLAN);assert pin(PLAN)['sha256']=='e0497d35bbc2fb3baea252161c31d6917f940f67ff0534517a4e43f9578e54a2'
main_path=B/'ROOT-A41-MAIN-RELOCATION-QUALIFICATION.actual-a01.json';main=load(main_path)
worker_path=B/'A41-WORKER-PHASES-COMPLETED.actual-a01.json';worker=load(worker_path)
assert main['production_bytes_qualified'] is True and main['focused_UI_cold_qualified'] is True
assert worker['actual_clean_invocation_HEAD']=='31ff77a0f07fb21f528c88e56314cbb093972703'
assert not git('status','--porcelain') and git('rev-parse','HEAD')==worker['actual_clean_invocation_HEAD']
assert git('rev-parse','HEAD:ck3_autonomous_player/native_bridge')==plan['native_tree']
for ref in plan['entry_dependencies']:assert pin(ref['path'])==ref
live=B/'refill-worker-live-a01';v5=B/'refill-worker-cold-a01'
def worker_actual(root,flags):
 report=load(root/'native-msvc-result.json');assert report['built'] is True and report['status']=='built' and report['build_succeeded'] is True
 exclusion=report['defender_exclusions'];receipt=load(exclusion['receipt']);manifest=load(exclusion['manifest'])
 assert receipt['status']=='verified' and receipt['admin_token'] is True and receipt['system_token_sid']=='S-1-5-18' and receipt['missing_requested_paths']==[]
 assert pin(exclusion['receipt'])['sha256']==exclusion['receipt_sha256']
 cache={}
 for line in (root/'CMakeCache.txt').read_text(encoding='utf-8').splitlines():
  if '=' in line and ':' in line.split('=',1)[0]:cache[line.split(':',1)[0]]=line.split('=',1)[1]
 assert all(cache.get(k)==v for k,v in flags.items())
 outputs=[]
 for row in manifest['files']:
  actual=pin(row['path']);assert actual['bytes']==row['size'] and actual['sha256']==row['sha256']
  assert any(p['path']==row['path'] and p['sha256']==row['sha256'] for p in receipt['files'])
  outputs.append({'target':row['target'],**actual})
 return {'source_dir':report['source_dir'],'build_result':pin(root/'native-msvc-result.json'),'SYSTEM_receipt':pin(exclusion['receipt']),'manifest':pin(exclusion['manifest']),
  'cmake_defines':flags,'outputs':outputs,'original_snapshot_source_head':plan['source_layers']['worker_original_snapshot_source_head'],
  'original_snapshot_manifest':plan['worker_source_manifest'],'actual_clean_invocation_HEAD':worker['actual_clean_invocation_HEAD'],'current_canonical_thirteen_input_equivalence':plan['worker_existing_frozen_input_equivalence']}
live_actual=worker_actual(live,plan['worker_live_flags']);v5_actual=worker_actual(v5,plan['worker_V5_flags'])
coldpath=B/'refill-worker-cold-evidence-a01/FOCUSED-WORKER-COLD.actual.json';cold=load(coldpath)
assert cold['status']=='PASS' and cold['case_count']==2 and len(cold['cases'])==2 and all(c['status']=='PASS' for c in cold['cases'])
assert cold['CK3_actual_ADD_observed'] is False
outputs=[{'target':'xar_ck3_bridge',**pin(plan['carrier_DLL']['path'])}]
assert outputs[0]['sha256']==plan['carrier_DLL']['sha256']
for target in ['xar_ck3_bridge_injector','xar_ck3_bridge_host']:
 row=next(x for x in main['relocated_EXEs'] if x['target']==target);actual=pin(row['destination']['path']);assert actual==row['destination'];outputs.append({'target':target,**actual})
protocol=main['protocol_growth_by_actual_request']+worker['protocol_growth_by_actual_request']
assert len(protocol)==3 and sum(x['derived_fixed_protocol_growth_bytes'] for x in protocol)<=33554432
actual_root=sum((Path(base)/name).stat().st_size for base,ds,fs in os.walk(B,followlinks=False) for name in fs)
q={'schema':'xar.e04.a41-coherent-relocation-worker-qualification.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'status':'PASS_SELECTED_SCOPE_ONLY',
 'source_head':plan['original_compile_source_head'],'native_build_source_head':plan['original_compile_source_head'],
 'native_build_source_head_role':'Original main carrier and relocated production EXE compilation; worker snapshot origin is separately recorded, never relabelled.',
 'native_tree':plan['native_tree'],'actual_clean_invocation_HEAD':worker['actual_clean_invocation_HEAD'],'actual_source_layers':plan['source_layers'],
 'production_bytes_qualified':True,'focused_cold_qualified':True,'all_feature_flags':plan['all_feature_flags'],'outputs':outputs,
 'original_main_compile':{'source_head':plan['original_compile_source_head'],'native_tree':plan['native_tree'],'actual_public_result':plan['original_public_producer_result'],'original_failure_preserved':plan['original_failure'],'new_main_compilation_performed':False},
 'main_actual_qualification':pin(main_path),'worker_live':live_actual,'worker_V5':v5_actual,'worker_focused_cold':pin(coldpath),'worker_execution_phases':pin(worker_path),
 'selected_actual_counts':{'production_original_compile_targets':3,'relocated_EXEs':3,'new_live_worker_build_targets':1,'new_V5_build_targets':2,'new_exact_SYSTEM_EXEs':6,'UI_cold_cases':1,'V5_owned_cold_cases':2},
 'fixed_protocol_growth_actual_contract_derived_bytes':sum(x['derived_fixed_protocol_growth_bytes'] for x in protocol),'fixed_protocol_conservative_charge_bytes':33554432,'protocol_growth_by_actual_request':protocol,
 'native_root_logical_bytes_observed_before_this_receipt':actual_root,'native_root_peak_bytes_known':max(actual_root,main['root_peak_bytes_known'],worker['root_peak_bytes_known']),
 'producer_plan':pin(PLAN),'capacity':pin(CAP),'historical_a40_OS1223_and_closed_incomplete_attempt':plan['original_incomplete_closure'],
 'a41_first_prefile_failure_preserved':plan['preparation_correction']['actual_first_failure'],'readonly_API_diagnosis':plan['preparation_correction']['read_only_API_diagnosis_before_second_relocation_attempt'],
 'scope_limits':['No new main compilation is claimed; original source93 and exact relocation are distinct actual layers.','Existing snapshotfd5 is source-only input, exact current13 equality; no a37 Q, result or capacity reused.','UI and owned V5 finite evidence only; no CK3 live ADD, SDK, game, screen, external process DR or global business qualification.','Installed policy/runtime/task/action/ACL unchanged; ordinary fixed SYSTEM registration only, no runas/UAC.'],
 'remaining_heavy_write_bytes':0,'game_or_SDK_or_screen_or_live_observer_executed':False}
qpath=B/'ROOT-A41-COHERENT-QUALIFICATION.actual-a01.json';qref=write(qpath,q)
# Exercise the unchanged public R06 receipt verifier, using actual completed artifacts.
sys.path.insert(0,str(R/'tools'));from ck3_mod_acceptance_cases.r06_refill_one_day import verify_producer
observer=next(x for x in live_actual['outputs'] if x['target']=='refill_add_hwprobe_12004')
producer={'qualification':qref,'build_result':live_actual['build_result'],'SYSTEM_receipt':live_actual['SYSTEM_receipt'],'cold_result':pin(coldpath),
 'source_dir':live_actual['source_dir'],'observer_exe':observer['path'],'observer_exe_sha256':observer['sha256'],
 'native_build_source_head':plan['original_compile_source_head'],'native_tree':plan['native_tree'],'carrier_module_path':outputs[0]['path'],'carrier_source_epoch':20261018,'cmake_defines':plan['worker_live_flags']}
assert verify_producer(producer,machine_id=plan['machine_id'],native_tree=plan['native_tree'])['status']=='PASS_SELECTED_SCOPE_ONLY'
readback={'schema':'xar.e04.a41-public-receipt-verifier-readback.v1','machine_id':plan['machine_id'],'observed_at_utc':now(),'status':'PUBLIC_R06_VERIFY_PRODUCER_ACTUAL_RECEIPTS_PASS','qualification':qref,'public_producer_arguments':producer,
 'verifier_source':pin(R/'tools/ck3_mod_acceptance_cases/r06_refill_one_day.py'),'outputs_rehashed':outputs,'worker_live_and_V5_EXEs_rehashed':live_actual['outputs']+v5_actual['outputs'],
 'no_guard_modified':True,'no_project_EXE_reexecuted':True,'no_game_or_SDK_or_screen':True}
ref=write(B/'A41-INDEPENDENT-PUBLIC-VERIFIER-READBACK.actual-a01.json',readback)
print(json.dumps({'qualification':qref,'actual_public_verifier_readback':ref,'producer_arguments':producer,'native_root_bytes_before_receipts':actual_root,'protocol_logical_growth_contract_bytes':q['fixed_protocol_growth_actual_contract_derived_bytes']}),flush=True)
