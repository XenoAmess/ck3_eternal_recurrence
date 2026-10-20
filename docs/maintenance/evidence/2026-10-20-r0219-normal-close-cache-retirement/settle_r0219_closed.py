"""Independent typed closure, exact original monitor wait and short-CAS settlement."""
from capacity_common import *
from monitor_r06_scene_budget import measure
import psutil

S = ROOT.parent / 'r06-scene-a03'
RUN = M + '--vanilla--R0219'
D = S / 'driver-runs' / RUN
C = D / 'case-output'
refs = {}
def read(name, path):
    ref = pin(path); refs[name] = ref
    return exact(ref)

normal = read('typed_normal_close', C / 'normal-close-result.json')
assert normal['normal_close_qualified'] is True and normal['business_pass'] is False
assert normal['retained_handle']['actual_retained_os0'] is True
assert normal['retained_handle']['exit_code'] == 0
assert normal['native_zero_proof']['process_exit_code'] == 0
assert normal['native_zero_proof']['shutdown']['cleanup_proven'] is True
host = read('host_original_wait', D / 'host-original-process-exit.json')
assert host['actual_original_popen_wait'] is True and host['returncode'] == 0 and host['run_id'] == RUN
keeper = read('keeper_original_wait', D / 'keeper-actual-parent-exit.json')
assert keeper['keeper_actual_exit_code'] == 0 and keeper['keeper_report']['thread_exited'] is True
allocator = read('allocator_original_wait', ROOT / 'allocate-exec-a04/ORIGINAL-WAIT.actual.json')
public = read('public_original_wait', ROOT / 'run-exec-a04/ORIGINAL-WAIT.actual.json')
assert allocator['actual_original_popen_wait'] is True and allocator['returncode'] == 0
assert public['actual_original_popen_wait'] is True and public['returncode'] == 2
release = read('screen_release', S / 'SCREEN-RELEASE.actual-a01.json')
assert release['ok'] is True and release['task']['state'] == 'done'
assert release['task']['last_sequence'] == 7396 and release['task']['resources'] == []
error = read('preserved_case_error', C / 'case-error-preserved.json')
kp = read('keeper_process_identity', D / 'keeper-process.json')
monitor = read('component_monitor_owner', B / 'R0219-RAW-CANCEL-A02-FOUR-COMPONENT-MONITOR-OWNED.actual-a01.json')
expected = [(9956,1792489933.4353063), (kp['pid'],kp['create_time']), (monitor['pid'],monitor['create_time'])]
census=[]
for pid, created in expected:
    try:
        p=psutil.Process(pid); actual=p.create_time()
        assert abs(actual-created) > .001, ('Owned process still alive',pid)
        census.append({'pid':pid,'expected_creation_time':created,'current_pid_reused_creation_time':actual,'owned_identity_absent':True})
    except psutil.NoSuchProcess:
        census.append({'pid':pid,'expected_creation_time':created,'owned_identity_absent':True})
for pid in [host['pid'],allocator['pid'],public['pid'],15296]:
    assert not psutil.pid_exists(pid), ('Closed original PID currently exists; needs exact review',pid)
    census.append({'pid':pid,'current_pid_absent':True,'creation_identity_gap':'Original wait evidence retained; no original creation time asserted'})
recorders=[]; scan_errors=[]
for p in psutil.process_iter(['pid','name','create_time']):
    try:
        if (p.info['name'] or '').lower() in ['ffmpeg.exe','ffprobe.exe']: recorders.append(p.info)
    except (psutil.NoSuchProcess,psutil.AccessDenied) as e: scan_errors.append(repr(e))
assert not recorders
waitref=put(B/'R0219-CLEANUP-COMPONENT-MONITOR-ORIGINAL-WAIT.actual-a02.json',{
    'schema':'xar.e04.exact-component-monitor-original-wait.v1','machine_id':M,'observed_at_utc':now(),
    'original_exec_session_id':97528,'actual_original_wait_returncode':0,
    'actual_tool_observation':'write_stdin original session returned exit_code 0; final stdout monitor_exited true at 2026-10-20T10:23:31.676106+00:00',
    'owner':refs['component_monitor_owner'],'stop_flag':pin(B/'R0219-RAW-CANCEL-A02-FOUR-COMPONENT-MONITOR.STOP'),
    'journal':pin(B/'R0219-RAW-CANCEL-A02-FOUR-COMPONENT-MONITOR.actual.jsonl')})
ledger, identity, before = snapshot()
claim=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
assert claim['scene_remaining_future_bytes']==2*G and claim['reserved_future_bytes_by_volume']['C:/']==2*G+128*Mi
cap=exact(claim['scene_source_bound_capacity'])
measurement=measure(cap)
assert measurement['metadata_coverage_complete'] and not measurement['errors']
assert measurement['components']['raw']['logical_bytes']==0
retained = put(B/'R0219-NORMAL-CLOSED-BUSINESS-REFUSED-SETTLEMENT.actual-a01.json',{
    'schema':'xar.e04.r0219-normal-closed-business-refused-actual-settlement.v1','machine_id':M,'observed_at_utc':now(),
    'run_id':RUN,'scene_root':str(S),'normal_close_qualified':True,'business_pass':False,'actual_days':0,
    'R06_ADD_observed':False,'observer_worker_camera_executed':False,'typed_originals':refs,
    'original_component_monitor_wait':waitref,'owned_current_census':census,'recorders':recorders,
    'process_scan_errors':scan_errors,'global_process_absence_claimed':False,
    'measurement':measurement,'scene_future_before_bytes':2*G,'scene_future_after_bytes':0,
    'legacy42132678_unchanged':True,'retained_actual_already_in_whole_volume_used':True,
    'physical_or_unused_credit_bytes':0,'new_game_or_native_execution_admitted':False,
    'purpose_review_at_utc':'2026-10-22T10:22:22Z','automatic_renewal':False,
    'retention_reason':'Necessary Mar31 normal Save and typed normal close support successor admission; representative original MapReady refusal retained. No blanket permanent protection.',
    'scheme':pin(__file__)})
claim['scene_remaining_future_bytes']=0
claim['reserved_future_bytes_by_volume']['C:/']=128*Mi
claim['scene_execution_admitted']=False
claim['scene_prepare_execution_admitted']=False
claim['game_execution_admitted']=False
claim['heavy_write_execution_admitted_components']=[]
claim['scene_state']='R0219-actual-normal-closed-business-MapReady-refused-future0'
claim['last_closed_scene_run_id']=RUN
claim['scene_run_id']=None
claim['scene_settlement']=retained
claim['scene_retained_actual_logical_bytes']=measurement['logical_total_bytes']
claim['scene_retained_actual_allocated_unique_bytes']=measurement['allocated_unique_total_bytes']
after=balances(ledger); v=volumes(); check=budget(v,after)
assert after['known_future']['C:/']==128*Mi and after['legacy']['C:/']==42132678
result=commit_ledger(ledger,identity)
tx=put(B/'R0219-CLOSED-SETTLEMENT-TRANSACTION.actual-a01.json',{
    'machine_id':M,'observed_at_utc':now(),'ledger_before':before,'settlement':retained,
    'commit':result,'active_balances_after':after,'fresh_volumes':v,'budget_after':check,
    'physical_or_unused_credit_bytes':0,'shared128_remains_open':True,'old_1030_quota_not_automatically_renewed':True})
print(json.dumps({'settlement':retained,'transaction':tx,'components':measurement['components'],'budget_after':check},indent=2))
