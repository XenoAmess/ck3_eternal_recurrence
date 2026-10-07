from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,psutil
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=Path(__file__).parent;RUN=B/'live-attempt-017'
def now():return datetime.now(timezone.utc).isoformat()
def ref(p):
 b=p.read_bytes();return {'path':p.resolve().as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p):return json.loads(p.read_bytes())
def put(n,v):
 p=O/n
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
releasep=B/'r17-root-screen-release-20261007-001/RELEASE.actual.json';release=load(releasep)
afterp=B/'r17-root-screen-release-20261007-001/BUS-AFTER-RELEASE.parsed.json';after=load(afterp)
need_release=release['ok'] is True and release['task']['resources']==release['event']['resources']==[] and release['event']['sequence']==3506
if not need_release:raise ValueError('Expected actual retained R17 release seq3506')
if any('ck3-screen:acquired' in x['resources'] for x in after['tasks']):raise ValueError('Actual after-list retains screen occupancy')
runtimep=B/'r17-helper-identity-holder-inputs-20261007-001/RUNTIME.actual.json';runtime=load(runtimep)
server=runtime['game_original_handle_owner']['server_process']
expected={'game':(14608,1791332614.2963333),'client':(13408,1791333031.5885065),'server':(server['pid'],server['create_time']),'keeper':(20436,1791332451.9545596),'holder':(14208,1791333766.1629004)}
started=now();identities={};managed=[];unknown_python=[];enumeration_errors=[];count=0
service_names={'ck3_native_profile_mcp.py','persistent_native_mcp_queue_28.py','retain_helper_handles.py','screen_lease_entry_r0017.py'}
for proc in psutil.process_iter(['pid','name','exe','create_time','cmdline'],ad_value=None):
 try:
  row=proc.info;count+=1
  for role,(pid,ctime) in expected.items():
   if row['pid']==pid:
    identities[role]={'role':role,'pid':pid,'create_time':ctime,'pid_currently_present':True,'current_create_time':row['create_time'],'same_original_identity_alive':row['create_time']==ctime,'current_name':row['name'],'observation':'READ_ONLY_PSUTIL_CURRENT_PROCESS_ENUMERATION_NOT_HANDLE_EXIT_PROOF'}
  name=(row.get('name') or '').lower();exe=Path(row['exe']).name.lower() if row.get('exe') else '';args=row.get('cmdline')
  scripts={Path(x).name.lower() for x in args or [] if isinstance(x,str)}
  ck3=name=='ck3.exe' or exe=='ck3.exe'
  svc=bool(scripts & service_names)
  if ck3 or svc:
   managed.append({'pid':row['pid'],'create_time':row['create_time'],'name':row['name'],'exe':row['exe'],'matched_kind':'ck3_game' if ck3 else 'managed_native_service','matched_scripts':sorted(scripts & service_names)})
  if (name.startswith('python') or exe.startswith('python')) and args is None:
   unknown_python.append({'pid':row['pid'],'create_time':row['create_time'],'name':row['name'],'cmdline_unavailable':True})
 except (psutil.NoSuchProcess,psutil.AccessDenied) as e:
  enumeration_errors.append({'pid':proc.pid,'error':type(e).__name__})
for role,(pid,ctime) in expected.items():
 identities.setdefault(role,{'role':role,'pid':pid,'create_time':ctime,'pid_currently_present':False,'current_create_time':None,'same_original_identity_alive':False,'observation':'READ_ONLY_PSUTIL_CURRENT_PROCESS_ENUMERATION_NOT_HANDLE_EXIT_PROOF'})
same_absent=all(x['same_original_identity_alive'] is False for x in identities.values())
v={'schema':'lyd.root.actual-postrelease-process-absence.v1','observed_at_utc':now(),'observation_started_at_utc':started,'source_head':'c706a74f9d00dd842b7edce8901fb3417344fd9c','root_screen_task':release['task']['task_id'],'release_receipt':ref(releasep),'after_list':ref(afterp),'runtime_identity_source':ref(runtimep),'same_original_identities_absent':same_absent,'no_current_managed_game_or_native_services':not managed and not unknown_python,'remaining_managed_game_or_native_services':managed,'original_identities':list(identities.values()),'ck3_exe_live_count':sum(x['matched_kind']=='ck3_game' for x in managed),'unresolved_python_processes':unknown_python,'enumerated_process_count':count,'enumeration_errors':enumeration_errors,'reopened_original_process':False,'original_HANDLE_exit0_credit':False,'SDK_calls':0,'game_actions':0,'process_signals':0,'bus_calls':0,'main_writes':0}
rr=put('ACTUAL-PROCESS-ABSENCE.json',v)
print(json.dumps({'receipt':rr,'status':v['same_original_identities_absent'] and v['no_current_managed_game_or_native_services'],'observed_at_utc':v['observed_at_utc'],'identities':v['original_identities'],'ck3_exe_live_count':v['ck3_exe_live_count'],'remaining_services':managed,'unknown_python':unknown_python},ensure_ascii=False,indent=2))
if not same_absent or managed or unknown_python:raise SystemExit(1)
