from pathlib import Path
from datetime import datetime,timezone
import collections,hashlib,json
ROOT=Path(__file__).resolve().parent
L=Path('C:/ck3-e04-resume-20261020-a01/r08-scene-a02/driver-runs/desktop-3fevhd2-1c74096080--vanilla--R0223/case-output')
files=['r08-writer-control/C-D-WRITERS.actual.json','r08-writer-control/ROOT-WINDOW-RESULT.actual.json',
 'r08-writer-control/watch/ACTUAL-WRITERS.json',
 'r08-initial-inputs/r08-1615-a01-initial-before.common-view.json',
 'r08-initial-inputs/r08-1615-a01-initial-cash.common-view.json',
 'r08-observer-packets/r08-1615-a01-before.common-view.json',
 'r08-observer-packets/r08-1615-a01-day-once.common-view.json',
 'r08-observer-packets/r08-1615-a01-independent-after.common-view.json',
 'r08-observer-packets/r08-1615-a01-cash-before.common-view.json',
 'r08-observer-packets/r08-1615-a01-cash-after.common-view.json']
def pin(p,raw):return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
projections=[]
for name in files:
 p=L/name;b=p.read_bytes();assert len(b)<100000
 v=json.loads(b);body=v.get('body',v)
 out={'pin':pin(p,b),'body_keys':list(body)}
 if 'before.common-view' in name or 'independent-after' in name:
  out['frame']={k:body[k] for k in body if any(x in k for x in ['date','army','armies','war','player','played','episode','revision','maintenance','econom']) and k!='diagnostics'}
 elif 'cash' in name:
  out['cash']={k:body[k] for k in ['date_raw','played_character_id','player_army_ids','current_raw_context_v1','military_expenses','current_treasury','player_monthly_total_expenses','war_payment_observations_v1'] if k in body}
 elif 'day-once' in name:out['step']=body
 projections.append(out)
p=L/'r08-writer-control/watch/writer.raw.ndjson';raw=p.read_bytes();assert len(raw)==35583
rows=[json.loads(x) for x in raw.splitlines() if x.strip()];kinds=collections.Counter(x['kind'] for x in rows)
keep=[]
for kind in kinds:
 selected=[x for x in rows if x['kind']==kind]
 if kind in ('start','ready','data','terminal','writer','exception') or len(selected)==1:keep.extend(selected)
value=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
 read_only=True,packet_projections=projections,raw=pin(p,raw),raw_kind_counts=dict(kinds),selected_raw_rows=keep,
 SDK_query_game_DR_actions=0,consumer_selector_executions=0)
out=ROOT/'PACKETS-PROJECTION.actual.json';out.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps({'out':pin(out,out.read_bytes()),'raw_kinds':dict(kinds)}))
for x in projections:
 if 'frame' in x:print(json.dumps(x,ensure_ascii=False))
print(json.dumps({'selected_raw_rows':keep},ensure_ascii=False))
