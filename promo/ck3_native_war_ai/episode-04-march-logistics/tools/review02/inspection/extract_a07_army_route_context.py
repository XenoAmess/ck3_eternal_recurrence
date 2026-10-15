"""Project a named saved post-Move Army query; no native query or action."""
from pathlib import Path
import argparse,datetime,hashlib,json
P=argparse.ArgumentParser(description=__doc__)
for name in ('scene','response','snapshot','move-complete','output'):P.add_argument('--'+name,type=Path,required=True)
P.add_argument('--army-id',type=int,required=True);a=P.parse_args();scene=a.scene.resolve()
def read(path,expected=None):
 path=path.resolve()
 if scene not in path.parents or path.suffix!='.json':raise ValueError('explicit saved JSON outside scene')
 b=path.read_bytes();pin={'path':path.relative_to(scene).as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 if expected and (pin['bytes']!=expected['bytes'] or pin['sha256']!=expected['sha256']):raise ValueError('original pin changed')
 return json.loads(b),pin
def frame(v):return {k:v[k] for k in ('source','snapshot_id','snapshot_revision','revision','native_revision','date_raw','paused','queried_snapshot_id','queried_revision','queried_native_revision','connection_generation','episode_run_id','queried_connection_generation','queried_episode_run_id') if k in v}
if a.output.exists():raise ValueError('append-only output exists')
response,rpin=read(a.response);move,mpin=read(a.move_complete);snapshot,spin=read(a.snapshot)
machine=response['machine_id']
if move['machine_id']!=machine or snapshot['machine_id']!=machine:raise ValueError('source machine differs')
ref=response['army_history_evidence']['raw_result_reference']
if ref!=move['full']['raw_result_reference']:raise ValueError('post-Move query references differ')
raw,pin=read(Path(ref['path']),ref)
armies=[(i,v) for i,v in enumerate(raw['army_strengths']) if v.get('army_id')==a.army_id]
if len(armies)!=1:raise ValueError('selected Army absent or duplicate')
i,army=armies[0];snapbody=snapshot['body']
# Snapshot wrappers use the actual saved body; keep absent route context absent.
player=snapbody.get('player_armies',[])
if not isinstance(player,list):player=[]
route=[{'json_pointer':f'/body/player_armies/{n}','literal':v} for n,v in enumerate(player) if v.get('army_id')==a.army_id]
out={'schema':'episode04.r0177.a07.postmove-current-route-literals.v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_response':rpin,'source_move_complete':mpin,'source_snapshot':spin,'source_raw':pin,'response_body_frame':frame(response['body']),'raw_frame':frame(raw),'snapshot_body_frame':frame(snapbody),
 'runtime_binding_literal':{k:move['binding'][k] for k in ('pid','create_filetime','generation','episode','actor_id','source_head','proof') if k in move['binding']},
 'identity':{k:army[k] for k in ('army_id','native_carmy_id','status') if k in army},
 'observations':[{'kind':kind,'json_pointer':f'/army_strengths/{i}/{key}','literal':army[key]} for key,kind in [('county_entry_inputs_v1','county_current_inputs'),('loss_application_inputs_v1','county_loss_application'),('current_movement_progress','county_current_movement')] if key in army],
 'snapshot_route_observations':route,'move_complete_army_literal':move.get('army'),
 'scope':'Post-Move current route and inputs only. Move ACK and nonempty route do not establish county arrival or loss.',
 'county_loss_causal_PASS':False,'new_query_or_action':False,'closed_receipt_observed':False}
b=(json.dumps(out,separators=(',',':'),ensure_ascii=False)+'\n').encode()
if len(b)>32*1024:raise ValueError('finite route projection bound exceeded')
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('xb') as f:f.write(b)
print(json.dumps({'path':str(a.output),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'identity':out['identity'],'snapshot_route_rows':len(route),'observations':out['observations']},ensure_ascii=False))
