"""Replay bounded immutable R192/R193 DTOs with archived exact production sources.

No C paths, repository checkout, raw Driver/save/video, SDK, extraction or actions.
"""
from pathlib import Path
import argparse,hashlib,io,json,sys,types,zipfile
def need(v,s):
 if not v:raise ValueError(s)
def wire(v):return json.loads(json.dumps(v,ensure_ascii=False))
def digest(b):return hashlib.sha256(b).hexdigest()
def archive(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  need(len(z.namelist())<=128 and sum(v.file_size for v in z.infolist())<=4*1024*1024,'Bounded small archive required')
  manifest=json.loads(z.read('MANIFEST.json'));need(set(z.namelist())==set(manifest['members'])|{'MANIFEST.json'},'Member set differs')
  data={}
  for n,pin in manifest['members'].items():
   need(not n.startswith('/') and '..' not in Path(n).parts,'Unsafe member name')
   value=z.read(n);need(len(value)==pin['bytes'] and digest(value)==pin['sha256'],'Exact member changed '+n);data[n]=value
 return manifest,data
def load(name,b):
 m=types.ModuleType(name);m.__file__='<portable-source:'+name+'>';sys.modules[name]=m;exec(compile(b,m.__file__,'exec'),m.__dict__);return m
def replay(data):
 for name in ('xar_autoplayer','xar_autoplayer.bridge'):
  m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
 for n in ('army_regiment_character_role_12004','army_replenishment_records_contract','army_split_merge_observation_12004','army_split_transfer_assertions_12004'):
  load('xar_autoplayer.bridge.'+n,data['production/'+n+'.py'])
 transfer=sys.modules['xar_autoplayer.bridge.army_split_transfer_assertions_12004'];obs=sys.modules['xar_autoplayer.bridge.army_split_merge_observation_12004']
 relay=load('portable_r193_historical_relay',data['production/root_relay.py'])
 role=load('xar_autoplayer.bridge.army_split_unrelated_role_transfer_12004',data['production/army_split_unrelated_role_transfer_12004.py'])
 j=lambda n:json.loads(data[n])
 f0=j('original/F0-baseline.actual.json')['packet'];f1=j('original/F1-post-split.actual.json')['packet'];f2=j('analysis/POSTMERGE-PACKET.actual-a02.json')['packet'];result=j('analysis/REVERSE-PAIR-ANALYSIS.actual-a02.json')
 proof=j('original/runtime-actor-identity.actual-a01.json');context=j('original/allocated-context.actual-a01.json');H=result['source_head'];run=result['run_id']
 binding=relay.admission(context,proof,run_id=run,source=H,sequence=193,machine=result['machine_id'],minimum_sequence=1)
 for p in (f0,f1,f2):relay.validate_frame(p['frame'],binding)
 for n in ('before','fence'):relay.same_frame(j('original/recovery-'+n+'.json')['body'],f2['frame'])
 for aid,body in f2['commanders'].items():
  original=j('original/typed-'+aid+'.json')['body'];dto=original['army_commander_candidates'];expected={k:original[k] for k in ('accepted','read_only','queried_snapshot_id','queried_revision','queried_native_revision')};expected['army_commander_candidates']={k:dto[k] for k in ('army_id','native_carmy_id','date_raw','snapshot_revision','current_commander')}
  need(body==expected,'Recovered typed literal projection differs')
 split=transfer.assert_fresh_split_transfer_12004(f0['frame'],f1['frame'],source_army_id=93,pre_strengths=f0['query'],post_strengths=f1['query'],pre_commander=f0['commanders']['93'],post_commanders={int(k):v for k,v in f1['commanders'].items()})
 need(wire(split)==result['split_assertion_recomputed'],'Production split replay differs')
 need(wire(role.qualify_unrelated_role_removal(f0,f1,source_army_id=93))==result['split_finite_unrelated_role_policy'],'Finite unrelated role replay differs')
 maps=[{r['army_id']:r for r in p['query']['army_strengths']} for p in (f0,f1,f2)];child=16777378
 need(wire(relay.compare_data_roles(transfer,[maps[1][child],maps[1][93]],[maps[2][child]]))==result['merge_DATA_roles'],'Production reverse physical/role replay differs')
 need(wire(relay.compare_merge_supply(f1,f2,[child,93]))==result['merge_supply'],'Production reverse stock replay differs')
 need(wire(obs.compare_split_merge_cohorts([maps[1][i] for i in (18,94,95)],[maps[2][i] for i in (18,94,95)]))==result['merge_unrelated_strict'],'Merge unrelated strict differs')
 observations=[transfer._observe([r for r in p['query']['army_strengths'] if r['status']=='available']) for p in (f0,f1,f2)]
 need(observations[0][1]==observations[1][1]==observations[2][1] and observations[0][2]==observations[1][2]==observations[2][2],'Whole available physical values/aliases changed')
 need([sum(x[0] for x in v[1].values()) for v in observations]==[1935]*3 and all(len(v[1])==33 for v in observations),'Physical totals differ')
 need(result['global_physical_and_cached_F0_F1_F2']==[{'unique_physical_slots':33,'physical_current_max':[1935,1935],'cached_current_max':v} for v in ([1945,1945],[1944,1944],[1945,1945])],'Cache/physical layers mixed')
 _,forward=archive(data['forward/r192-forward-evidence.zip'])
 old_f0=json.loads(forward['original/F0-baseline.actual.json']);old_endpoint=json.loads(forward['original/F0-endpoint.actual.json'])
 current=j('original/baseline-ENDPOINT.actual.json')
 if old_endpoint is None:
  candidates=[json.loads(b) for n,b in forward.items() if n.endswith('.json') and b.startswith(b'{') and 'baseline' in n.lower() and 'ENDPOINT' in n]
  need(len(candidates)==1,'Exact forward baseline endpoint absent');old_endpoint=candidates[0]
 need(current['normal_save_sha256']==old_endpoint['normal_save_sha256'] and current['frozen_observable']==old_endpoint['frozen_observable'],'Pair frozen S0/full observable differs')
 oldproof=json.loads(next(b for n,b in forward.items() if n.endswith('runtime-actor-identity.actual-a01.json')))
 need((proof['pid'],proof['process_creation_filetime_100ns'])!=(oldproof['pid'],oldproof['process_creation_filetime_100ns']),'Actual independent cold lifetime missing')
 old_f1=json.loads(forward['original/F1-post-split-observation.actual.json'])['packet'];old_f2=json.loads(forward['analysis/POSTMERGE-PACKET.actual.json'])['packet'];forward_result=json.loads(forward['analysis/MERGE-ANALYSIS.actual.json'])
 need(wire(relay.compare_merge_supply(old_f1,old_f2,[93,child]))==forward_result['merge_supply'],'Forward production stock replay differs')
 need(result['merge_supply']['weights_raw']==[17500000,7500000] and forward_result['merge_supply']['weights_raw']==[7500000,17500000],'Directional weights differ')
 for stage in result['three_frame_current_refill_classification']:
  need(len(stage['physical_chunks'])==4 and all(c['containing_guard_138_raw']==1 and c['native_can_replenish'] is False and c['native_chunk_can_replenish'] is False and c['observed_prepared148_raw']==0 for c in stage['physical_chunks']),'Observed current flags differ')
 film=j('original/FILM-CONTROLLER.actual.json');media=j('original/portable-media-facts.actual-a01.json')
 need(film['error']=="RuntimeError('selected Army unavailable; cannot proceed')" and media['encoded_seconds']==65.033 and media['survivorUI_stage_executed'] is False,'Original RED/media changed')
 need(result['sameS0_two_directions_numeric_qualified'] is True and result['R09_full_card_closed'] is False and not result['upper_clamp_positive'] and not result['distinct_stock_observed'],'Card/stock claim changed')
 return {'sameS0_two_directions_numeric_qualified':True,'production_pure_consumers_replayed':True,'finite_unrelated_role_policy_replayed':True,'physical_current_max':[1935,1935],'unique_physical_slots':33,'R193_original_film_RED_preserved':True,'R09_full_card_closed':False,'raw_Driver_save_video_body_reads':0,'SDK_game_actions':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);a=p.parse_args();need(a.archive.stat().st_size<=1024*1024,'Portable1MiB bound');manifest,data=archive(a.archive.read_bytes());result=replay(data);print(json.dumps({'status':'PORTABLE_HISTORICAL_PRODUCTION_REPLAY_PASS','members':len(data),**result}))
if __name__=='__main__':main()
