"""Single capacity coordinator: complete actual plus dynamically restored unspent."""
from packet_common import *
from scene_a05_consumed_measure import measure
import psutil

STOP=B/'R06-ACTUAL-UNSPENT-GUARD.STOP'
OWNER=B/'R06-ACTUAL-UNSPENT-GUARD-OWNED.actual-a01.json'
assert not STOP.exists() and not OWNER.exists()
approval_ref=pin(B/'ROOT-NEW-FINITE-1315Z-APPROVAL.actual-a01.json')
approval=exact(approval_ref)
oldwait_ref=pin(ROOT/'capacity/r06-1230-a01/R0220-CONSUMED-GUARD-ORIGINAL-WAIT.actual-a01.json')
assert exact(oldwait_ref)['actual_original_wait_returncode']==0
ledger,_,_=snapshot(); own=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
BASE_REF=own['scene_source_bound_capacity']; CAP=exact(BASE_REF)
assert CAP['run_id']==own['scene_run_id'] and CAP['machine_id']==M
assert Path(CAP['scene_root']).resolve()==S and approval['actual_plus_unspent_mode_approved'] is True
HARD=dict(CAP['component_ceiling_bytes']); assert sum(HARD.values())==2304*Mi
owner_ref=put(OWNER,{'machine_id':M,'observed_at_utc':now(),'pid':os.getpid(),'create_time':psutil.Process().create_time(),
 'argv':psutil.Process().cmdline(),'source':pin(__file__),'measurement_source':pin(B/'scene_a05_consumed_measure.py'),
 'base_scene_capacity':BASE_REF,'conversion_approval':approval_ref,'predecessor_original_wait':oldwait_ref,
 'stop_flag':str(STOP),'deadline_utc':DEADLINE,'interval_seconds':15,
 'all_observations_outside_global_CAS_lock':True,'no_SDK_screen_game_or_payload_hash_actions':True})
part=1; first=True
while not STOP.exists():
    committed=False
    for attempt in range(3):
        ledger,identity,before=snapshot()
        c=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
        assert c['scene_execution_admitted'] is True, 'Do not reopen a settled scene'
        assert c['native_a41_remaining_future_bytes']==0 and c['shared_remaining_future_bytes']==128*Mi
        assert c['scene_source_bound_capacity']==BASE_REF
        pair=[]; failures=[]
        for _ in range(2):
            try: pair.append(measure(CAP))
            except (OSError,AssertionError) as error: failures.append(repr(error))
        complete=len(pair)==2 and not failures and all(x['metadata_coverage_complete'] and not x['errors'] for x in pair)
        components={}; alarms=[]
        for key,ceiling in HARD.items():
            if complete:
                logical=[x['components'][key]['logical_bytes'] for x in pair]
                allocated=[x['components'][key]['allocated_unique_bytes'] for x in pair]
                consumed=min(*logical,*allocated)
                remaining=max(0,ceiling-consumed)
                if max(*logical,*allocated)>ceiling: alarms.append('COMPONENT_LOGICAL_OR_ALLOCATED_HARDCAP_EXCEEDED:'+key)
            else:
                logical=allocated=None; consumed=None; remaining=ceiling
            components[key]={'hardcap_bytes':ceiling,'complete_logical_bytes':logical,
              'complete_allocated_unique_bytes':allocated,'confirmed_occupancy_lower_bound_bytes':consumed,
              'unspent_future_bytes':remaining}
        if not complete: alarms.append('UNKNOWN_OR_PARTIAL_MEASUREMENT_FULL_SCENE_FUTURE_RESTORED_RED')
        remaining=sum(x['unspent_future_bytes'] for x in components.values())
        old_remaining=c['scene_remaining_future_bytes']
        path=B/('R06-ACTUAL-UNSPENT-GUARD.actual-part%04d.jsonl'%part)
        if path.exists() and path.stat().st_size>240*1024:
            part+=1; path=B/('R06-ACTUAL-UNSPENT-GUARD.actual-part%04d.jsonl'%part)
            assert not path.exists()
        c['scene_hardcap_total_bytes']=2304*Mi
        c['scene_component_hardcap_bytes']=HARD
        c['scene_remaining_future_bytes']=remaining
        c['reserved_future_bytes_by_volume']['C:/']=remaining+128*Mi
        c['scene_component_unspent_future_bytes']={k:x['unspent_future_bytes'] for k,x in components.items()}
        c['scene_confirmed_occupancy_lower_bound_bytes']={k:x['confirmed_occupancy_lower_bound_bytes'] for k,x in components.items()}
        c['scene_complete_accounting_coverage']=complete
        c['scene_accounting_observed_at_utc']=now()
        c['scene_future_accounting_mode']='original-hardcaps-minus-current-paired-complete-minimum-occupancy; partial restores fullscene'
        c['scene_consumed_conversion_authority']=approval_ref
        c['scene_component_monitor_journal']=str(path)
        c['scene_accounting_guard_owner']=owner_ref
        c['physical_or_unused_credit_bytes']=0
        active=balances(ledger); v=volumes(); checks=budget(v,active)
        for k in ['C_quota_margin_bytes','C_floor_margin_bytes','D_floor_margin_bytes']:
            if checks[k]<0: alarms.append(k+'_NEGATIVE')
        expired=datetime.now(timezone.utc)>=datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))
        if expired: alarms.append('NEW_FINITE_1315Z_HARD_DEADLINE_REACHED')
        shared=shared_measure(c['shared_accounting_excludes'])
        c['scene_accounting_budget_status']='RED' if alarms else 'GREEN'
        c['new_heavy_writes_require_GREEN_fresh_accounting']=True
        ledger['current_finite_scope'].update(known_C_work_package_future_bytes=active['known_future']['C:/'],
          last_observed_at_utc=now(),C_last_observed_free_bytes=v['C:/']['free_bytes'],
          D_last_observed_free_bytes=v['D:/']['free_bytes'],C_quota_margin_bytes=checks['C_quota_margin_bytes'],
          scene_hardcap_total_bytes=2304*Mi,scene_unspent_future_bytes=remaining)
        ledger['updated_at_utc']=now()
        try: commit=commit_ledger(ledger,identity); committed=True
        except (StorageConflict,FileExistsError) as error:
            print(json.dumps({'machine_id':M,'observed_at_utc':now(),'CAS_conflict_retry_outside_lock':repr(error),'attempt':attempt+1}),flush=True)
            continue
        row={'schema':'xar.e04.r06-1315-complete-actual-plus-unspent-live-guard.v1','machine_id':M,'observed_at_utc':now(),
          'run_id':CAP['run_id'],'components':components,'measurement_coverage_complete':complete,
          'coverage_failures':failures[:5],'scan_errors':[e for x in pair for e in x['errors']][:5],
          'scene_unspent_before_bytes':old_remaining,'scene_unspent_after_bytes':remaining,
          'scene_future_delta_bytes':remaining-old_remaining,'active_balances':active,'fresh_volumes':v,
          'budget':checks,'shared_actual_logical_bytes':shared['logical_bytes'],
          'quota_review_at_utc':DEADLINE,'alarms':alarms,'budget_status':'RED' if alarms else 'GREEN',
          'ledger_before':before,'ledger_after':commit['ledger_after'],'short_CAS_hold_seconds':commit['lock_hold_seconds'],
          'original_component_hardcaps_and_all_raw_temp_Save_budgets_unchanged':True,
          'whole_volume_actual_not_decreased_or_deducted':True,'physical_or_unused_credit_bytes':0,
          'unknown_values_not_treated_as_zero':True,'payload_body_bytes_read':0,'game_SDK_screen_actions':0}
        raw=(json.dumps(row,separators=(',',':'))+'\n').encode()
        assert len(raw)<32768 and (not path.exists() or path.stat().st_size+len(raw)<256*1024)
        with path.open('ab') as f: f.write(raw); f.flush()
        if first:
            initial=put(B/'R06-ACTUAL-UNSPENT-FIRST-CONVERSION.actual-a01.json',{
              'machine_id':M,'observed_at_utc':now(),'Root_approval':approval_ref,'owner':owner_ref,
              'predecessor_original_wait':oldwait_ref,'base_scene_capacity':BASE_REF,
              'complete_observations':pair,'actual_conversion':row,'commit':commit,
              'method_is_continuously_recomputed_not_a_fixed_remaining_balance':True,
              'physical_or_unused_credit_bytes':0})
            print(json.dumps({'initial_actual_conversion':initial,'guard_owner':owner_ref}),flush=True)
            first=False
        print(json.dumps({'machine_id':M,'at':row['observed_at_utc'],'coverage_complete':complete,
          'scene_unspent_bytes':remaining,'known_C_future_bytes':active['known_future']['C:/'],
          'C_quota_margin_bytes':checks['C_quota_margin_bytes'],'D_floor_margin_bytes':checks['D_floor_margin_bytes'],
          'shared_logical_bytes':shared['logical_bytes'],'alarms':alarms,'journal':str(path)}),flush=True)
        break
    assert committed, 'Three short CAS conflicts: stop and inspect; no blind reservation change'
    if expired: break
    time.sleep(15)
print(json.dumps({'machine_id':M,'observed_at_utc':now(),'guard_exited':True,'exact_stop_flag_present':STOP.exists()}),flush=True)
