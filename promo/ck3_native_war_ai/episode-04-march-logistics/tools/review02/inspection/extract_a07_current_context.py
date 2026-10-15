"""Read-only explicit saved Driver JSON projection; no query/action/qualification."""
from pathlib import Path
import argparse,datetime,hashlib,json
parser=argparse.ArgumentParser(description='Extract requested county and supply current literals from an exact saved Driver reference.')
parser.add_argument('--scene',type=Path,required=True)
parser.add_argument('--current',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
if args.output.exists():raise ValueError('append-only context target already exists')
current=json.loads(args.current.read_bytes())
source=current['sources'][0]['driver_evidence'][0]['raw_original']
scene=args.scene.resolve()
raw_path=(scene/source['path']).resolve()
if scene not in raw_path.parents or raw_path.suffix!='.json':raise ValueError('saved JSON reference outside scene')
rawbytes=raw_path.read_bytes()
if len(rawbytes)!=source['bytes'] or hashlib.sha256(rawbytes).hexdigest()!=source['sha256']:raise ValueError('exact Driver JSON changed')
raw=json.loads(rawbytes);rows=[]
framekeys=('source','game_version','executable_sha256','snapshot','snapshot_id','snapshot_revision','revision','native_revision','date_raw','paused','queried_snapshot_id','queried_revision','queried_native_revision','connection_generation','episode_run_id','queried_connection_generation','queried_episode_run_id')
for i,army in enumerate(raw['army_strengths']):
    ident={k:army[k] for k in ('army_id','native_carmy_id','status') if k in army}
    for key,kind in [('loss_application_inputs_v1','county_loss_application'),('current_movement_progress','county_current_movement')]:
        if key in army:rows.append({'kind':kind,'json_pointer':f'/army_strengths/{i}/{key}','identity':ident,'literal':army[key]})
    if army.get('army_id') not in (18,93):continue
    scalars={k:army[k] for k in ('army_id','native_carmy_id','status','current_supply_raw','current_supply_scale','current_supply_capacity_raw','current_supply_capacity_scale','current_supply_change_monthly_raw','current_supply_change_monthly_scale') if k in army}
    rows.append({'kind':'supply_current_scalar_sliver','json_pointer':f'/army_strengths/{i}','identity':ident,'literal':scalars,'projection':'explicit selected scalar fields; not a full Army row'})
    fields=('current_province_supply_contributors_v1','army_update_clock_v1','future_daily_supply_schedule_inputs_v1','source_derived_next_daily_supply_frame_inputs_v1','current_land_supply_rate_inputs_v1','current_land_resupply_v1')
    for key in fields:
        if key not in army:continue
        value=army[key];row={'kind':'supply_'+key,'json_pointer':f'/army_strengths/{i}/{key}','identity':ident}
        n=len(json.dumps(value,separators=(',',':')).encode())
        if key=='current_province_supply_contributors_v1' and n>65536:
            row.update({'literal_available_in_compact':False,'original_family_bytes_json_compact':n,'projection':'pointer only; full contributors family exceeds 64KiB; no truncated family fabricated'})
        else:row['literal']=value
        rows.append(row)
    key='monthly_loss_budget_inputs_v1'
    if isinstance(army.get(key),dict):
        rows.append({'kind':'supply_monthly_loss_budget_gate_sliver','json_pointer':f'/army_strengths/{i}/{key}','identity':ident,
          'literal':{k:army[key][k] for k in ('unit_native_170_raw','native_unit_in_combat','native_unit_gathering','army_gathering_count_raw') if k in army[key]},'projection':'explicit selected gate fields; not full family'})
out={'schema':'episode04.a07.current-context-literal-appendix.v1','machine_id':current['machine_id'],'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source':source,'frame_literal':{k:raw[k] for k in framekeys if k in raw},'observations':rows,'causal_business_PASS':False,'missing_fields_are_not_zero_filled':True,
 'scope':'Exact county movement/loss leaves and requested R05 current input families; not actual loss/refill/stock consequence'}
encoded=(json.dumps(out,separators=(',',':'),ensure_ascii=False)+'\n').encode();
if len(encoded)>=192*1024:raise ValueError('context exceeds finite compact bound')
target=args.output
target.parent.mkdir(parents=True,exist_ok=True)
with target.open('xb') as stream:stream.write(encoded)
print(json.dumps({'path':str(target),'bytes':len(encoded),'sha256':hashlib.sha256(encoded).hexdigest(),
 'observations':[{'kind':r['kind'],'identity':r['identity'],'literal_available': 'literal' in r,'compact_literal_bytes':len(json.dumps(r.get('literal'),separators=(',',':')).encode())} for r in rows]},indent=2))
