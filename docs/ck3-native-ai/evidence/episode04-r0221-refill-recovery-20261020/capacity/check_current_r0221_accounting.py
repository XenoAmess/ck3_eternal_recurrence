"""Read-only phase gate: latest literal guard row, live ledger, fresh volumes; no bypass."""
from packet_common import *
import argparse, subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--receipt',required=True)
a=p.parse_args();out=Path(a.receipt).resolve()
assert out.is_relative_to(ROOT) and not out.exists()
observed=now();errors=[];result={}
try:
 actual_machine=subprocess.run([sys.executable,'-B','-X','utf8',str(R/'tools/ck3_live_run_id.py'),'machine'],capture_output=True,text=True,check=True).stdout.strip()
 assert actual_machine==M
 for attempt in range(5):
  ledger,identity,ledger_ref=snapshot()
  c=next(x for x in ledger['claims'] if x['task_id']==T and x['state']=='active')
  path=Path(c['scene_component_monitor_journal']).resolve()
  assert path.is_relative_to(B)
  try:
   with path.open('rb') as f:
    size=f.seek(0,2);start=max(0,size-32768);f.seek(start);tail=f.read()
   lines=tail.splitlines(keepends=True)
   raw=lines[-1];assert raw.endswith(b'\n'),'Latest JSONL append not complete; retry, never select earlier GREEN'
   row=json.loads(raw)
   _,after_identity,_=snapshot()
   assert identity==after_identity,'Ledger changed while selecting latest row; retry'
   break
  except (OSError,ValueError,AssertionError):
   if attempt==4:raise
   time.sleep(.1)
 age=(datetime.now(timezone.utc)-datetime.fromisoformat(row['observed_at_utc'])).total_seconds()
 assert 0<=age<=30,'Latest guard observation exceeds30s; do not use earlier GREEN'
 assert row['machine_id']==c['machine_id']==M and row['run_id']==c['scene_run_id']==M+'--vanilla--R0221'
 assert c['scene_execution_admitted'] and c['game_execution_admitted']
 assert row['measurement_coverage_complete'] is True and not row['coverage_failures'] and not row['scan_errors']
 assert c['scene_complete_accounting_coverage'] is True
 assert row['budget_status']==c['scene_accounting_budget_status']=='GREEN' and row['alarms']==[]
 assert c['scene_remaining_future_bytes']==row['scene_unspent_after_bytes']
 assert c['scene_component_unspent_future_bytes']=={k:v['unspent_future_bytes'] for k,v in row['components'].items()}
 assert c['scene_confirmed_occupancy_lower_bound_bytes']=={k:v['confirmed_occupancy_lower_bound_bytes'] for k,v in row['components'].items()}
 assert c['scene_hardcap_total_bytes']==2304*Mi and c['shared_remaining_future_bytes']==128*Mi
 capref=c['scene_source_bound_capacity'];cap=exact(capref)
 assert cap['machine_id']==M and cap['run_id']==row['run_id'] and Path(cap['scene_root']).resolve()==S
 assert cap['source_head']==c['source_head']=='4fc8d0f4cae53735274475bd3e7fc3afbb958f7c'
 assert cap['native_tree']==c['native_tree']=='fee86631356f556271445157523c62abfd62951e'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(DEADLINE.replace('Z','+00:00'))
 active=balances(ledger);assert active==row['active_balances']
 v=volumes();checks=budget(v,active);shared=shared_measure(c['shared_accounting_excludes'])
 assert min(checks['C_floor_margin_bytes'],checks['C_quota_margin_bytes'],checks['D_floor_margin_bytes'])>=0
 result={'base_scene_capacity':capref,'ledger':ledger_ref,'literal_latest_guard_row':{
  'path':str(path),'byte_offset':start+sum(len(x) for x in lines[:-1]),'bytes':len(raw),
  'sha256':hashlib.sha256(raw).hexdigest(),'observed_at_utc':row['observed_at_utc'],'age_seconds':age,
  'row':row},'fresh_volumes':v,'fresh_budget':checks,'collective_shared':shared}
except Exception as error:
 errors.append(repr(error))
receipt=put(out,{'schema':'xar.e04.r0221-readonly-current-accounting-phase-gate.v1',
 'machine_id':M,'observed_at_utc':observed,'finished_at_utc':now(),'run_id':M+'--vanilla--R0221',
 'admitted':not errors,'budget_status':'RED' if errors else 'GREEN','errors':errors,**result,
 'latest_RED_or_gap_never_skipped_to_select_old_GREEN':True,'ledger_or_capacity_mutated':False,
 'new_camera_or_worker_action_executed':False,'physical_or_unused_credit_bytes':0,
 'scope_is_capacity_check_only_all_existing_canonical_Root_UI_source_admission_guards_remain':True,
 'helper':pin(__file__)})
print(json.dumps({'receipt':receipt,'budget_status':'RED' if errors else 'GREEN','errors':errors,
 'budget':result.get('fresh_budget')}),flush=True)
if errors:raise SystemExit(2)
