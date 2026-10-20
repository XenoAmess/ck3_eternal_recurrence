from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path(__file__).resolve().parent
L=Path('C:/ck3-e04-resume-20261020-a01/r08-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0223/case-output')
def pin(p,b):return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
rows=[]
for name in ['r08-writer-control/observer-start.once.json','r08-writer-control/READY-OBSERVED.actual.json',
 'r08-writer-control/day.once.json','r08-1615-a01-day-once.actual-results.json','r10-common-preparation-result.json',
 'r08-observer-packets/r08-1615-a01-cash-after.common-view.json']:
 p=L/name
 if not p.is_file():rows.append(dict(path=str(p),exists=False));continue
 stat=p.stat();entry=dict(path=str(p),bytes=stat.st_size,mtime_ns=stat.st_mtime_ns)
 if stat.st_size>150000:entry['body_not_read']='greater than150KB exact-small-input bound';rows.append(entry);continue
 b=p.read_bytes();v=json.loads(b);entry['pin']=pin(p,b);entry['keys']=list(v)
 if name.endswith('cash-after.common-view.json'):
  body=v['body'];j=body['war_payment_observations_v1'];entry['projection']={k:body[k] for k in ['date_raw','played_character_id','player_army_ids','current_raw_context_v1','military_expenses','current_treasury']}
  entry['projection']['journal']={k:j[k] for k in ['sampling','current_session','natural_journal_status','records','natural_parent_returns']}
 elif name=='r10-common-preparation-result.json':entry['readiness']=v.get('readiness',{})
 elif 'actual-results' in name:
  entry['rows']=[{k:r[k] for k in r if k!='result'} for r in v.get('rows',[])]
  entry['result_summary']=[{k:r['result'][k] for k in r.get('result',{}) if any(s in k for s in ['clock','time','day','date','policy'])} for r in v.get('rows',[]) if isinstance(r.get('result'),dict)]
 else:entry['record']=v
 rows.append(entry)
value=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),rows=rows,
 mtime_role='filesystem stat provenance only, not execution timestamp or proof of temporal containment')
b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')
assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file())+len(b)<=131072,len(b)
out=root/'TIMING-CASH-READBACK.actual.json';out.write_bytes(b)
print(json.dumps(value,ensure_ascii=False))
