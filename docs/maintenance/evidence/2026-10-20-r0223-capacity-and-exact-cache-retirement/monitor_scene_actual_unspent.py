"""One combined guard and immediate task-bus RED alerts; no separate stale volume writer."""
from packet_1615_common import *
from scene_r08_measure import measure
import psutil,subprocess

def alert(row,path):
    message='machine_id:'+M+' R08 actual capacity RED at '+row['observed_at_utc']+' alarms='+','.join(row['alarms'])+' journal='+str(path)+'; no automatic pause or absence-of-actions claim. Stop new heavy/action stages and inspect latest complete ledger.'
    p=subprocess.run([sys.executable,'-B',str(R/'tools/codex_task_bus.py'),'notify','--task',T,'--to','e04-r06-resume-20261020-a02','--level','action','--message',message,'--repo',str(R)],capture_output=True,text=True)
    return {'returncode':p.returncode,'ok':p.returncode==0,'stderr':p.stderr[:300]}

def main():
    stop=B/'R08-ACTUAL-UNSPENT-GUARD.STOP';owner=B/'R08-ACTUAL-UNSPENT-GUARD-OWNED.actual-a01.json'
    assert not stop.exists() and not owner.exists()
    ledger,_,_=snapshot();c=next(c for c in ledger['claims'] if c['task_id']==T and c['state']=='active')
    capref=c['scene_source_bound_capacity'];cap=exact(capref)
    assert cap['machine_id']==M and cap['run_id'] is not None and cap['run_id']==c['scene_run_id']
    hard=dict(cap['component_ceiling_bytes']);assert sum(hard.values())==G and hard['raw']==0
    assert cap['actual_plus_unspent_accounting_authorized'] is True
    approval=cap['Root_accounting_authority']
    ownerref=put(owner,{'machine_id':M,'observed_at_utc':now(),'pid':os.getpid(),'create_time':psutil.Process().create_time(),
        'argv':psutil.Process().cmdline(),'source':pin(__file__),'measurement_source':pin(B/'scene_r08_measure.py'),
        'base_scene_capacity':capref,'accounting_authority':approval,'stop_flag':str(stop),'deadline_utc':DEADLINE,
        'interval_seconds':15,'one_combined_authoritative_stream':True,'immediate_RED_task_bus_notify':True,
        'no_SDK_game_screen_or_payload_hash_actions':True})
    part=1;first=True
    while not stop.exists():
        committed=False
        for attempt in range(3):
            ledger,identity,before=snapshot();c=next(c for c in ledger['claims'] if c['task_id']==T and c['state']=='active')
            assert c['scene_execution_admitted'] is True and c['scene_source_bound_capacity']==capref
            assert c['native_remaining_future_bytes']==0 and c['shared_remaining_future_bytes']==16*Mi
            pair=[];failures=[]
            for _ in range(2):
                try:pair.append(measure(cap))
                except (OSError,AssertionError) as e:failures.append(repr(e))
            complete=len(pair)==2 and not failures and all(x['metadata_coverage_complete'] and not x['errors'] for x in pair)
            groups={};alarms=[]
            for key,ceiling in hard.items():
                if complete:
                    logical=[x['components'][key]['logical_bytes'] for x in pair]
                    allocated=[x['components'][key]['allocated_unique_bytes'] for x in pair]
                    consumed=min(*logical,*allocated);remaining=max(0,ceiling-consumed)
                    if max(*logical,*allocated)>ceiling:alarms.append('COMPONENT_LOGICAL_OR_ALLOCATED_HARDCAP_EXCEEDED:'+key)
                else:logical=allocated=None;consumed=None;remaining=ceiling
                groups[key]={'hardcap_bytes':ceiling,'complete_logical_bytes':logical,'complete_allocated_unique_bytes':allocated,
                    'confirmed_occupancy_lower_bound_bytes':consumed,'unspent_future_bytes':remaining}
            if not complete:alarms.append('UNKNOWN_PARTIAL_FULL_SCENE_FUTURE_RESTORED_RED')
            remaining=sum(x['unspent_future_bytes'] for x in groups.values());previous=c['scene_remaining_future_bytes']
            path=B/('R08-ACTUAL-UNSPENT-GUARD.actual-part%04d.jsonl'%part)
            if path.exists() and path.stat().st_size>240*1024:
                part+=1;path=B/('R08-ACTUAL-UNSPENT-GUARD.actual-part%04d.jsonl'%part);assert not path.exists()
            c['scene_remaining_future_bytes']=remaining;c['reserved_future_bytes_by_volume']['C:/']=remaining+16*Mi
            c['scene_component_unspent_future_bytes']={k:g['unspent_future_bytes'] for k,g in groups.items()}
            c['scene_confirmed_occupancy_lower_bound_bytes']={k:g['confirmed_occupancy_lower_bound_bytes'] for k,g in groups.items()}
            c['scene_complete_accounting_coverage']=complete;c['scene_accounting_observed_at_utc']=now()
            c['scene_future_accounting_mode']='Fixed hardcaps minus paired complete minimum logical/uniqueallocated; shrink replenishes future; partial restores full1GiB and RED.'
            c['scene_component_monitor_journal']=str(path);c['scene_accounting_guard_owner']=ownerref;c['physical_or_unused_credit_bytes']=0
            active=balances(ledger);shared=shared_measure();v=volumes();q=budget(v,active)
            for k in ['C_quota_margin_bytes','C_floor_margin_bytes','D_floor_margin_bytes']:
                if q[k]<0:alarms.append(k+'_NEGATIVE')
            expired=datetime.now(timezone.utc)>=datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))
            if expired:alarms.append('NEW_FINITE_1615_HARD_DEADLINE_REACHED')
            c['scene_accounting_budget_status']='RED' if alarms else 'GREEN';c['new_heavy_writes_require_GREEN_fresh_accounting']=True
            ledger['current_finite_scope'].update(known_C_work_package_future_bytes=active['known_future']['C:/'],last_observed_at_utc=now(),
                C_last_observed_free_bytes=v['C:/']['free_bytes'],D_last_observed_free_bytes=v['D:/']['free_bytes'],C_quota_margin_bytes=q['C_quota_margin_bytes'],scene_unspent_future_bytes=remaining)
            try:tx=commit_ledger(ledger,identity);committed=True
            except (StorageConflict,FileExistsError) as e:
                print(json.dumps({'machine_id':M,'at':now(),'CAS_retry_outside_lock':repr(e),'attempt':attempt+1}),flush=True);continue
            row={'schema':'xar.e04.r08-1615-combined-actual-plus-unspent.v1','machine_id':M,'observed_at_utc':now(),'run_id':cap['run_id'],
                'components':groups,'measurement_coverage_complete':complete,'coverage_failures':failures[:5],
                'scan_errors':[e for x in pair for e in x['errors']][:5],'scene_unspent_before_bytes':previous,'scene_unspent_after_bytes':remaining,
                'active_balances':active,'fresh_volumes':v,'budget':q,'shared_actual_logical_bytes':shared['logical_bytes'],
                'quota_review_at_utc':DEADLINE,'alarms':alarms,'budget_status':'RED' if alarms else 'GREEN','base_scene_capacity':capref,
                'ledger_before':before,'ledger_after':tx['ledger_after'],'short_CAS_hold_seconds':tx['lock_hold_seconds'],
                'original_component_hardcaps_unchanged':True,'whole_volume_actual_legacy_shared_system_not_deducted':True,
                'physical_or_unused_credit_bytes':0,'unknown_values_not_zero':True,'payload_body_bytes_read':0,'SDK_game_screen_actions':0}
            raw=(json.dumps(row,separators=(',',':'))+'\n').encode();assert len(raw)<32768
            with path.open('ab') as f:f.write(raw);f.flush()
            if alarms:row['RED_notification']=alert(row,path)
            if first:
                ref=put(B/'R08-ACTUAL-UNSPENT-FIRST-CONVERSION.actual-a01.json',{'machine_id':M,'observed_at_utc':now(),
                    'guard_owner':ownerref,'base_capacity':capref,'complete_observations':pair,'actual_conversion':row,'transaction':tx,
                    'continuously_recomputed_not_fixed_credit':True})
                print(json.dumps({'first_conversion':ref,'owner':ownerref}),flush=True);first=False
            print(json.dumps({'machine_id':M,'at':row['observed_at_utc'],'coverage_complete':complete,'unspent':remaining,
                'C_quota_margin_bytes':q['C_quota_margin_bytes'],'shared':shared['logical_bytes'],'alarms':alarms,'journal':str(path)}),flush=True)
            break
        assert committed,'Three CAS conflicts; inspect before further writes'
        if expired:break
        time.sleep(15)
    print(json.dumps({'machine_id':M,'at':now(),'guard_exited':True,'exact_stop_flag_present':stop.exists()}),flush=True)

if __name__=='__main__':main()
