"""Root-only fresh typed baseline for an actual control or treatment binding.

Uses the existing pinned controller's Stage/frame/army/normalizers/guard. No
legacy observable bool, recovery reuse, new SDK client, action or global gate.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
from types import SimpleNamespace
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
def need(x,m):
 if not x:raise RuntimeError(m)
def pin(p,limit=1048576):
 p=Path(p);need(p.is_file() and not p.is_symlink() and 0<p.stat().st_size<=limit,'bounded real metadata/source required');raw=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def same(a,b):return isinstance(a,dict) and isinstance(b,dict) and Path(a.get('path','')).resolve()==Path(b.get('path','')).resolve() and a.get('bytes')==b.get('bytes') and a.get('sha256')==b.get('sha256')
def read(p):pin(p);return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):
 raw=(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode();need(len(raw)<=128*1024,'bounded new receipt required')
 with Path(p).open('xb') as f:f.write(raw)
 return pin(p)
def load_controller(c):
 controller=c['controller'];need(same(pin(controller['path']),controller),'actual controller pin changed')
 # Direct-file import needs its actual pinned package directory in cold Python.
 path=Path(controller['path']);sys.path.insert(0,str(path.resolve().parent))
 spec=importlib.util.spec_from_file_location('r07_actual_typed_baseline_controller',path);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 return m
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binding',type=Path,required=True);p.add_argument('--attempt',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--execute-live',action='store_true');a=p.parse_args()
 need(a.execute_live,'explicit Root --execute-live required');need(not a.output.exists(),'new immutable front required')
 c=read(a.binding);need(c.get('role') in ('control','treatment'),'actual fresh control or treatment binding required')
 repo=Path(c['repo']);sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src')]
 from xar_autoplayer.bridge.army_split_merge_observation_12004 import read_bound_native_army_resolution
 helper=pin(Path(sys.modules[read_bound_native_army_resolution.__module__].__file__))
 ctl=load_controller(c);ctl.current_guard(c).check();ctl.process_lifetime(c)
 scene=Path(c['assets_root']);meta=scene/'r07-v2-stages';meta.mkdir(exist_ok=True);need(not (meta/'segment-01.baseline.actual.json').exists(),'baseline exists; inspect it, do not repeat')
 need(not any(meta.glob('segment-01.*.action-claim.json')),'initial source already mutated by a later stage; do not create a fresh baseline')
 write(meta/'segment-01.typed-baseline.once.claim.json',{'machine_id':c['machine_id'],'at_utc':datetime.now(timezone.utc).isoformat(),'binding':pin(a.binding),'entry':pin(__file__),'typed_consumer':helper,'attempt':a.attempt,'retry_forbidden':True,'fresh_query_not_recovery':True})
 l=ctl.relay().Stage(SimpleNamespace(binding=a.binding,segment=1,attempt=a.attempt,operation='baseline'));request=l.request
 def readonly_only(suffix,tool,fields):
  need(tool in ('ck3_take_snapshot','ck3_query_army_strengths','ck3_query_army_commander_candidates_v1','ck3_query_war_cash_current_resources_private_v1'),'fresh baseline submits only established read-only query tools')
  if tool=='ck3_query_war_cash_current_resources_private_v1':need(fields.get('payment_sampling')=='query' and 'payment_window_contract' not in fields,'baseline may not enable/disable a payment window')
  return request(suffix,tool,fields)
 l.request=readonly_only
 s,army=l.frame('baseline-before');need(s['date_raw']==c['S0']['date_raw'],'not the actual independent S0 date')
 need(army.get('current_province_id')==c['start_province_id'] and army.get('route_read_status')=='complete_empty' and army.get('route_province_ids')==[] and army.get('move_target_province_id') is None and army.get('army_state')!='embarked','independent stationary S0 required')
 row,ref,armyframe=l.army();resolution=read_bound_native_army_resolution(row,army_id=c['army_id']);data=l.data_norm(row.get('regiment_replenishment_records_v1'))
 need(bool(data) and sum(len(r['records']) for r in data)>0 and all(r['ready'] is True and r['status']=='available' for r in data) and type(row.get('current_soldiers')) is int and row['current_soldiers']>0,'actual wholeDATA source not qualified')
 command,commandframe=l.readonly('baseline-current-commander','ck3_query_army_commander_candidates_v1',{'army_id':c['army_id']})
 repo=Path(c['repo']);sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src')]
 from xar_autoplayer.bridge.army_split_merge_observation_12004 import read_bound_current_commander
 commander=read_bound_current_commander(command['body'],commandframe,army_id=c['army_id'],native_carmy_id=row['native_carmy_id'])
 j,b,cashframe=l.cash('baseline-cash');need(not j['controlled_window_admitted'] and not j['sampling']['capture_enabled'],'baseline payment already active; cannot reenable or clear')
 for frame in (armyframe,commandframe,cashframe):need(frame['date_raw']==s['date_raw'] and frame['revision']==s['revision'] and frame['native_revision']==s['native_revision'],'baseline read-only fields crossed their actual paused source frame')
 value=l.out('baseline',{'date_raw':s['date_raw'],'route':army,'current_soldiers':row['current_soldiers'],'maximum_soldiers':row['maximum_soldiers'],'current_supply_raw':row['current_supply_raw'],
  'full_DATA_signature':ctl.stable_DATA_signature(data),'current_commander_id':commander,'native_carmy_id':row['native_carmy_id'],'raw_result_reference':ref,'active_wars':s.get('active_wars'),'treasury_observation':b.get('current_treasury'),
  'native_resolution_admission':resolution,'typed_baseline_entry':pin(__file__),'typed_consumer_candidate':helper,'fresh_baseline_not_recovered':True})
 print(json.dumps({'front':write(a.output,value),'canonical':pin(meta/'segment-01.baseline.actual.json'),'role':c['role'],'SDK_client_created_by_entry':False,'new_actions_submitted':False}))
if __name__=='__main__':main()
