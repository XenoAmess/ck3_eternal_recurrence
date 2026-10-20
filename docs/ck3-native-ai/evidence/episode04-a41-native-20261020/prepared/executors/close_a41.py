from pathlib import Path
import ctypes,datetime as dt,hashlib,json,os,subprocess,sys
from ctypes import wintypes as w
O=Path(__file__).parent;R=Path('D:/workspace/ck3_eternal_recurrence');B=Path('C:/w/e04a41');P=Path('C:/Program Files/XAR CK3 Project EXE Broker')
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
cap_path=O.parent/'capacity/A41-C-NATIVE-SOURCE-BOUND.actual-a03.json';cap=load(cap_path)
q_path=B/'ROOT-A41-COHERENT-QUALIFICATION.actual-a01.json';q=load(q_path)
assert q['production_bytes_qualified'] is True and q['focused_cold_qualified'] is True
phase='worker_V5_two_owned_cases';fresh=cap['fresh_stage_helper']
assert pin(fresh['path'])==fresh
subprocess.run([str(R/'tools/.venv/Scripts/python.exe'),'-B','-X','utf8',fresh['path'],'--cap',str(cap_path),'--cap-sha256',pin(cap_path)['sha256'],'--phase',phase,'--worker-source-head',q['actual_clean_invocation_HEAD'],'--output',str(B/'CAPACITY-FRESH-CLOSE.actual-a01.json')],check=True,cwd=R,capture_output=True)
import pythoncom,win32com.client
pythoncom.CoInitialize();service=win32com.client.GetObject(r'winmgmts:{impersonationLevel=impersonate}!\\.\root\cimv2')
owned=[];hidden=[]
needles=['execute_a41.py','execute_a41_resume_a02.py','execute_a41_resume_a03.py','relocate_a40_declared_exes_a04.py']
for row in service.ExecQuery('SELECT ProcessId,ParentProcessId,CreationDate,ExecutablePath,CommandLine,Name FROM Win32_Process'):
 pid=int(row.ProcessId);name=str(row.Name or '');cmd=str(row.CommandLine or '');exe=str(row.ExecutablePath or '')
 cn=cmd.lower().replace('\\','/');en=exe.lower().replace('\\','/')
 match=any(str(O/n).lower().replace('\\','/') in cn for n in needles) or en.startswith(str(B).lower().replace('\\','/')+'/') or (str(B).lower().replace('\\','/') in cn and name.lower() in ['cmake.exe','ninja.exe','cl.exe','link.exe']) or ('run_native_msvc.py' in cn and str(B).lower().replace('\\','/') in cn)
 if match:owned.append({'pid':pid,'parent_pid':int(row.ParentProcessId),'creation_DMTF':str(row.CreationDate or ''),'name':name,'executable':exe,'command_line':cmd})
 if name.lower() in ['python.exe','pythonw.exe','cmake.exe','ninja.exe','cl.exe','link.exe'] and not cmd and not exe:hidden.append({'pid':pid,'name':name,'creation_DMTF':str(row.CreationDate or ''),'read_error':'No exposed executable/commandline; not attributed and not counted as proven global absence'})
assert not owned,owned
sched=win32com.client.Dispatch('Schedule.Service');sched.Connect()
task=sched.GetFolder(r'\XAR CK3 Project EXE Broker').GetTask('RegisterDeclaredProjectExecutables')
task_state={'running_instances':int(task.GetInstances(0).Count),'state':int(task.State),'last_task_result':int(task.LastTaskResult)}
assert task_state['running_instances']==0
installed={name:pin(P/name) for name in ['policy.json','installation-manifest.json','runtime-seal.json']}
site=load(O/'A41-READONLY-SITE-INSPECTION.actual-a01.json')
assert installed['policy.json']==site['installed_policy']['pin'] and installed['installation-manifest.json']==site['installed_manifest'] and installed['runtime-seal.json']==site['installed_runtime_seal']
history=[];parents={}
for p in sorted((B/'qualification-phases').glob('*/Popen.actual.json')):
 start=load(p);end_path=p.parent/'result.actual.json';end=load(end_path)
 assert start['child']==end['Popen']
 history.append({'phase_directory':str(p.parent),'child':start['child'],'original_wait_return_code':end['original_wait_return_code'],'Popen_receipt':pin(p),'terminal_result':pin(end_path)})
 parents[(start['parent']['pid'],start['parent']['creation_filetime'])]=start['parent']
assert len(history)==9 and sum(x['original_wait_return_code']==0 for x in history)==8
all_bytes=sum((Path(base)/n).stat().st_size for base,ds,fs in os.walk(B,followlinks=False) for n in fs)
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=w.HANDLE;k.GetProcessTimes.argtypes=[w.HANDLE,*[ctypes.POINTER(w.FILETIME)]*4];k.GetProcessTimes.restype=w.BOOL
c,e,kt,ut=[w.FILETIME() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut))
observer={'pid':os.getpid(),'creation_filetime':(c.dwHighDateTime<<32)|c.dwLowDateTime,'role':'This small metadata-only closure observer; terminates immediately after receipt'}
stamp=dt.datetime.now(dt.timezone.utc)
record={'schema':'xar.e04.a41-owned-writers-and-selected-scope-closure.v1','machine_id':q['machine_id'],'observed_at_utc':stamp.isoformat(),'status':'ALL_SELECTED_NATIVE_SCOPE_ACTUAL_PASS_OWNED_WRITERS_ZERO',
 'qualification':pin(q_path),'public_verifier_readback':pin(B/'A41-INDEPENDENT-PUBLIC-VERIFIER-READBACK.actual-a01.json'),'capacity_close_fresh':pin(B/'CAPACITY-FRESH-CLOSE.actual-a01.json'),
 'selected_scope_terminal':q['selected_actual_counts'],'remaining_heavy_write_bytes':0,'native_stages_scheduled_after_this_closure':[],
 'owned_writer_snapshot':{'matching_owned_active_processes':owned,'owned_writer_count_excluding_metadata_observer':0,'current_fixed_SYSTEM_task':task_state,'unattributed_hidden_processes':hidden,'global_process_absence_asserted':False,'metadata_observer':observer},
 'actual_direct_child_lifecycles':history,'actual_executor_parent_identities':list(parents.values()),
 'read_errors':['Public CMake/Ninja/compiler descendant historical PID/creation times are not individually exposed by their existing producer report. Their actual synchronous build completion and parent Popen wait are preserved, and current owned-path census is empty.','Fixed SYSTEM broker does not expose its process PID/creation FILETIME; each actual protected receipt proves SID18/admin and the fixed task now has running_instances=0. No SYSTEM PID is invented.'],
 'actual_installed_readback':installed,'installed_policy_manifest_runtime_seal_unchanged':True,
 'native_root_logical_bytes_before_this_small_receipt':all_bytes,'fixed_protocol_growth_contract_derived_bytes':q['fixed_protocol_growth_actual_contract_derived_bytes'],
 'aggregate_owned_logical_bytes_before_this_receipt':all_bytes+q['fixed_protocol_growth_actual_contract_derived_bytes'],
 'fixed_protocol_actual_is_contract_derivation_not_private_enumeration':True,'fixed_protocol_full_conservative_charge_bytes':33554432,'new_native_root_ceiling_bytes':771751936,'aggregate_ceiling_bytes':805306368,
 'current_runtime_inputs_readonly':{'old_A40_carrier_DLL':q['outputs'][0],'worker_original_snapshot_manifest':q['worker_live']['original_snapshot_manifest'],'source13_current_equivalence':q['worker_live']['current_canonical_thirteen_input_equivalence']},
 'retention':{'policy':pin(R/'docs/storage-retention-policy.json'),'purpose_review_at_utc':'2026-10-20T10:30:00Z','protection_auto_renew':False,
  'current_necessary_inputs_reason':'Actual new runtime and pending R06 scene consume qualified old DLL/new EXEs and exact original worker snapshot; original source-ACL before records remain unique restoration material. No active input deletion.',
  'build_default_expires_at_utc':(stamp+dt.timedelta(hours=336)).isoformat(),'small_record_default_expires_at_utc':(stamp+dt.timedelta(hours=4320)).isoformat(),
  'obsolete_unexecuted_preparations_review':'Derived prepared revisions are eligible for consolidation/reclamation under the common policy, not permanent protection because they were candidates. Preserve one small actual failure and its precise fixed diagnosis.',
  'expired_is_candidate_not_delete_authorization':True},
 'ledger_mutation_or_free_credit':False,'no_game_SDK_screen_live_observer_or_external_DR_executed':True}
out=B/'A41-SELECTED-SCOPE-CLOSED.actual-a01.json'
with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps({'closure':pin(out),'root_bytes_before_receipt':all_bytes,'aggregate_logical_before_receipt':record['aggregate_owned_logical_bytes_before_this_receipt'],'owned_writers':len(owned),'SYSTEM_running_instances':task_state['running_instances']}),flush=True)
