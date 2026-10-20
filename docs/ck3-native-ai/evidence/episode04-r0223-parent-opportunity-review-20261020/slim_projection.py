from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path(__file__).resolve().parent
p=root/'PACKETS-PROJECTION.actual.json';old=p.read_bytes();v=json.loads(old)
for x in v['packet_projections']:
 if 'frame' in x:
  f=x['frame'];x['frame']={k:f[k] for k in ('date_raw','revision','native_revision','episode_projection','local_player_id','player_armies','army_strengths','army_strengths_status','player_army_ids') if k in f}
  if 'played_character' in f:x['frame']['played_character']={k:f['played_character'].get(k) for k in ('character_id','alive')}
  if 'active_wars' in f:x['frame']['active_wars']=[{k:r.get(k) for k in ('war_id','player_side','player_is_primary_war_leader')} for r in f['active_wars']]
 if 'cash' in x:
  j=x['cash'].get('war_payment_observations_v1',{})
  x['cash']['war_payment_observations_v1']={k:j[k] for k in ('installed','install_failure_flags','controlled_window_admitted','current_session','sampling','read_complete','latest_sequence','natural_journal_status','records','natural_parent_returns') if k in j}
 if 'step' in x:x['step']={'body_keys':list(x['step'])}
v['derived_projection_correction']='Broad active-war province arrays removed; original packet pins and sources unchanged.'
new=root/'PACKETS-PROJECTION.compact-a02.actual.json';raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8');new.write_bytes(raw)
retirement=dict(machine_id=v['machine_id'],observed_at_utc=datetime.now(timezone.utc).isoformat(),
 retired_own_derived=dict(path=str(p),bytes=len(old),sha256=hashlib.sha256(old).hexdigest()),
 replacement=dict(path=str(new),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),
 reason='Overbroad new derived projection accidentally repeated full active-war province arrays; no source original or proof deleted',
 original_source_evidence_modified=False)
(root/'DERIVED-PROJECTION-CORRECTION.actual.json').write_bytes((json.dumps(retirement,indent=2)+'\n').encode('utf8'))
assert p.resolve().parent==root.resolve();p.unlink()
print(json.dumps({'projection':retirement['replacement'],'lane_bytes':sum(x.stat().st_size for x in root.rglob('*') if x.is_file())}))
for x in v['packet_projections']:
 if 'frame' in x:print(json.dumps(x))
