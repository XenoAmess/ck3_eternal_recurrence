"""Only after real typed normal close, resource release and original guard wait0."""
from packet_common import *
from scene_a04_consumed_measure import measure
import argparse, psutil
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--allocator-original-wait',required=True)
p.add_argument('--public-original-wait',required=True)
a=p.parse_args()
ledger,identity,before=snapshot(); c=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
base_ref=c['scene_source_bound_capacity']; cap=exact(base_ref); RUN=cap['run_id']
assert RUN==M+'--vanilla--R0220'
D=Path(cap['component_roots']['driver']); C=D/'case-output'; refs={}
def read(name,path):
 ref=pin(path); refs[name]=ref; return exact(ref)
normal=read('normal_close',C/'normal-close-result.json')
assert normal['normal_close_qualified'] is True and normal['business_pass'] is False
assert normal['retained_handle']['actual_retained_os0'] is True and normal['retained_handle']['exit_code']==0
assert normal['native_zero_proof']['process_exit_code']==0 and normal['native_zero_proof']['shutdown']['cleanup_proven'] is True
host=read('host_original_wait',D/'host-original-process-exit.json')
assert host['actual_original_popen_wait'] is True and host['returncode']==0 and host['run_id']==RUN
keeper=read('keeper_original_wait',D/'keeper-actual-parent-exit.json')
assert keeper['keeper_actual_exit_code']==0 and keeper['keeper_report']['thread_exited'] is True
allocator=read('allocator_original_wait',a.allocator_original_wait)
public=read('public_original_wait',a.public_original_wait)
assert allocator['machine_id']==public['machine_id']==M
assert allocator['actual_original_popen_wait'] is True and allocator['returncode']==0
assert public['actual_original_popen_wait'] is True and public['returncode']==0
release=read('screen_release',S/'SCREEN-RELEASE.actual-a01.json')
assert release['ok'] and release['task']['state']=='done' and release['task']['resources']==[]
assert release['task']['task_id']==exact(cap['frozen_argv'])['screen_task']
entry=read('entry_run_result',C/'entry-run-result.json')
r06=entry['case_result']['r06_refill_one_day']
assert r06['status']=='STOPPED_ERROR_PRESERVED_NO_REPLAY'
assert r06['actual_days']==0 and r06['full_R06_qualified'] is False
assert r06['error']['message']=='Canonical R06 camera Start absent'
assert r06['cleanup']['normal_Save_verified'] is True and r06['cleanup']['sampling_OFF_clear_verified'] is True
wait=read('accounting_guard_original_wait',B/'R0220-CONSUMED-GUARD-ORIGINAL-WAIT.actual-a01.json')
assert wait['actual_original_wait_returncode']==0
kp=read('keeper_identity',D/'keeper-process.json')
gp=read('accounting_guard_identity',B/'R0220-CONSUMED-GUARD-OWNED.actual-a01.json')
census=[]
for pid,creation in [(normal['retained_handle']['pid'],normal['retained_handle']['create_time']),(kp['pid'],kp['create_time']),(gp['pid'],gp['create_time'])]:
 try:
  q=psutil.Process(pid); actual=q.create_time(); assert abs(actual-creation)>.001,('Owned exact process still alive',pid)
  census.append({'pid':pid,'expected_creation_time':creation,'current_pid_reused_creation_time':actual,'owned_identity_absent':True})
 except psutil.NoSuchProcess: census.append({'pid':pid,'expected_creation_time':creation,'owned_identity_absent':True})
recorders=[]
for q in psutil.process_iter(['pid','name']):
 if (q.info['name'] or '').lower() in ['ffmpeg.exe','ffprobe.exe']: recorders.append(q.info)
assert recorders==[]
pair=[measure(cap),measure(cap)]
assert all(x['metadata_coverage_complete'] and not x['errors'] for x in pair)
assert all(x['components']['raw']['logical_bytes']==0 for x in pair)
old_remaining=c['scene_remaining_future_bytes']
assert c['reserved_future_bytes_by_volume']['C:/']==old_remaining+128*Mi
ref=put(B/'R0220-NORMAL-CLOSED-SOURCE-EXPIRED-SETTLEMENT.actual-a01.json',{
 'schema':'xar.e04.r0220-actual-normal-closed-unexecuted-camera-refusal-settlement.v1',
 'machine_id':M,'observed_at_utc':now(),'run_id':RUN,'scene_root':str(S),'base_capacity':base_ref,
 'normal_close_qualified':True,'business_pass':False,'actual_days':r06['actual_days'],
 'public_original_wait0_is_not_R06_business_PASS':True,'R06_actual_error':r06['error'],
 'standalone_case_error_file_exists':(C/'case-error-preserved.json').exists(),
 'error_preserved_in_actual_entry_result_not_manufactured_as_a_new_original':True,
 'Root_reported_no_camera_external_observer_or_clock':True,
 'native_internal_sampling_ON_accepted':r06.get('sampling_ON',{}).get('accepted') is True,
 'native_internal_sampling_OFF_clear_verified':r06['cleanup']['sampling_OFF_clear_verified'],
 'typed_originals':refs,'owned_current_census':census,'ffmpeg_ffprobe_census':recorders,
 'global_process_absence_claimed':False,'original_host_keeper_allocator_exits_proven_by_original_waits':True,
 'complete_closed_measurements':pair,'scene_unspent_before_bytes':old_remaining,'scene_unspent_after_bytes':0,
 'all_actual_scene_bytes_remain_inside_whole_volume_used':True,'physical_or_unused_credit_bytes':0,
 'legacy42132678_and_system4GiB_not_released':True,'shared128_still_open':True,
 'purpose_review_at_utc':'2026-10-22T11:10:00Z','automatic_renewal':False,
 'retention_reason':'Representative Source TTL failure and exact normal-close/resource-release support successor analysis. Necessary source Mar31 S0 remains independently protected; no blanket permanent build/profile protection.',
 'scheme':pin(__file__)})
c.setdefault('retained_scene_history',[]).append({'run_id':RUN,'scene_root':str(S),'capacity':base_ref,'settlement':ref,
 'carry_only_existing_actual':True,'future_bytes':0,'actual_logical_bytes':pair[-1]['logical_total_bytes'],
 'actual_allocated_unique_bytes':pair[-1]['allocated_unique_total_bytes']})
c['scene_remaining_future_bytes']=0;c['reserved_future_bytes_by_volume']['C:/']=128*Mi
c['scene_component_unspent_future_bytes']={key:0 for key in cap['component_ceiling_bytes']}
c['scene_execution_admitted']=False;c['scene_prepare_execution_admitted']=False
c['game_execution_admitted']=False;c['raw_execution_admitted']=False
c['scene_state']='R0220-actual-normal-closed-source-expired-no-camera-no-day-future0'
c['scene_settlement']=ref;c['last_closed_scene_run_id']=RUN;c['scene_run_id']=None
active=balances(ledger); v=volumes(); checks=budget(v,active)
ledger['current_finite_scope'].update(execution_admission_state=c['scene_state'],known_C_work_package_future_bytes=active['known_future']['C:/'],
 scene_unspent_future_bytes=0,last_observed_at_utc=now(),C_last_observed_free_bytes=v['C:/']['free_bytes'],C_quota_margin_bytes=checks['C_quota_margin_bytes'])
commit=commit_ledger(ledger,identity)
tx=put(B/'R0220-ACTUAL-CLOSED-SETTLEMENT-TRANSACTION.actual-a01.json',{
 'machine_id':M,'observed_at_utc':now(),'ledger_before':before,'settlement':ref,'commit':commit,
 'active_balances':active,'fresh_volumes':v,'budget':checks,'physical_or_unused_credit_bytes':0,
 'successor_scope_not_reserved':True})
print(json.dumps({'settlement':ref,'transaction':tx,'actual_components':pair[-1]['components'],'budget':checks},indent=2))
