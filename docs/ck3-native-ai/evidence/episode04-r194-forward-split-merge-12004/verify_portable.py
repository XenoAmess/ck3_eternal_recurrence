"""Portable R194 exact small DTO replay. Stdlib only, no SDK/current checkout/raw."""
from pathlib import Path
import argparse,ast,hashlib,io,json,sys,types,zipfile
def need(v,s):
 if not v:raise ValueError(s)
def wire(v):return json.loads(json.dumps(v,ensure_ascii=False))
def digest(b):return hashlib.sha256(b).hexdigest()
def archive(b):
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  need(len(z.namelist())<=128 and sum(v.file_size for v in z.infolist())<=6*1024*1024,'Bounded archive required');m=json.loads(z.read('MANIFEST.json'));need(set(z.namelist())==set(m['members'])|{'MANIFEST.json'},'Exact member set')
  d={}
  for n,p in m['members'].items():
   need(not n.startswith('/') and '..' not in Path(n).parts,'Safe member names');v=z.read(n);need(len(v)==p['bytes'] and digest(v)==p['sha256'],'Member exactpin changed '+n);d[n]=v
 return m,d
def module(name,b):
 m=types.ModuleType(name);m.__file__='<portable:'+name+'>';sys.modules[name]=m;exec(compile(b,m.__file__,'exec'),m.__dict__);return m
def replay(data):
 for n in ('xar_autoplayer','xar_autoplayer.bridge'):
  p=types.ModuleType(n);p.__path__=[];sys.modules[n]=p
 for n in ('army_regiment_character_role_12004','army_replenishment_records_contract','army_split_merge_observation_12004','army_split_transfer_assertions_12004'):
  module('xar_autoplayer.bridge.'+n,data['production/'+n+'.py'])
 transfer=sys.modules['xar_autoplayer.bridge.army_split_transfer_assertions_12004'];obs=sys.modules['xar_autoplayer.bridge.army_split_merge_observation_12004'];relay=module('r194_historical_relay',data['production/root_relay.py']);role=module('r194_historical_role',data['production/army_split_unrelated_role_transfer_12004.py'])
 j=lambda n:json.loads(data[n]);result=j('analysis/NUMERIC-ANALYSIS.actual-a01.json');endpoints=[j('original/F'+str(i)+'-ENDPOINT.actual.json') for i in range(3)];stored=[j('original/F'+str(i)+'-packet.actual.json') for i in range(3)];f0,f1,f2=[v['packet'] for v in stored]
 proof=j('original/runtime-actor-identity.actual-a01.json');context=j('original/allocated-context.actual-a01.json');config=j('original/controller-input.actual.json');binding=relay.admission(context,proof,run_id=result['run_id'],source=result['source_head'],sequence=194,machine=result['machine_id'],minimum_sequence=1)
 need(result['source_head']==config['source_head']==proof['source_head']=='d7135ca3bf40c33c2d5416242ce844077f1e8cbe','New exact actual source')
 for e,p,s in zip(endpoints,(f0,f1,f2),stored):
  need(e['run_id']==s['run_id']==result['run_id'] and s['binding']==binding,'Own actual run binding');relay.validate_frame(p['frame'],binding);q=p['query'];need(q['accepted'] is True and [q[k] for k in ('queried_snapshot_id','queried_revision','queried_native_revision')]==[p['frame'][k] for k in ('snapshot_id','revision','native_revision')],'Own queried frame')
 need(len({p['frame']['date_raw'] for p in (f0,f1,f2)})==1,'No game time advance')
 split=transfer.assert_fresh_split_transfer_12004(f0['frame'],f1['frame'],source_army_id=93,pre_strengths=f0['query'],post_strengths=f1['query'],pre_commander=f0['commanders']['93'],post_commanders={int(k):v for k,v in f1['commanders'].items()});need(wire(split)==result['split_assertion_recomputed'],'Actual production split replay')
 need(wire(role.qualify_unrelated_role_removal(f0,f1,source_army_id=93))==result['finite_split_unrelated_policy'],'Actual finite role policy replay')
 child=split['identity']['sibling_army_id'];maps=[{a['army_id']:a for a in p['query']['army_strengths']} for p in (f0,f1,f2)]
 need(wire(relay.compare_data_roles(transfer,[maps[1][93],maps[1][child]],[maps[2][93]]))==result['merge_DATA_roles'],'Production merge physical/role replay')
 need(wire(relay.compare_merge_supply(f1,f2,[93,child]))==result['merge_supply'],'Production native stock formula replay')
 need(wire(obs.compare_split_merge_cohorts([maps[1][i] for i in (18,94,95)],[maps[2][i] for i in (18,94,95)]))==result['merge_unrelated_strict'],'Original strict merge unrelated replay')
 observed=[transfer._observe([a for a in p['query']['army_strengths'] if a['status']=='available']) for p in (f0,f1,f2)];need(observed[0][1]==observed[1][1]==observed[2][1] and observed[0][2]==observed[1][2]==observed[2][2],'Global physical identity/current/max/state/occurrences equal')
 actualtotals=[{'unique_physical_slots':len(v[1]),'physical_current_max':[sum(w[i] for w in v[1].values()) for i in (0,1)],'cached_current_max':[sum(a[k] for a in p['query']['army_strengths'] if a['status']=='available') for k in ('current_soldiers','maximum_soldiers')]} for p,v in zip((f0,f1,f2),observed)];need(actualtotals==result['global_physical_and_cached_F0_F1_F2'],'Actual physical/cache layer totals')
 for stage,e in zip(result['selected_three_frames'],endpoints):
  for a in stage['armies']:need(a['current_refill_classification']==e['current_refill_classification'][str(a['public_army_id'])],'Current flags literal endpoint projection')
 claim=j('original/merge.once.claim.json');ack=j('original/merge.submission.actual.json');need(claim['army_ids']==[93,child] and ack['body']['accepted'] is True and ack['body']['war_action']['postcondition_verified'] is True,'Unique actual merge claim/ACK')
 ui=j('original/SURVIVOR-UI.actual-a05.json');before=j('original/GUI-before.json')['body'];body=j('original/GUI-window.json')['body'];after=j('original/GUI-after.json')['body'];relay.validate_frame(before,binding);relay.validate_frame(after,binding);relay.same_frame(before,after)
 nodes=[n for n in ast.parse(data['production/r09_next_a07.py'].decode('utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name=='survivor_window_matches'];need(len(nodes)==1,'Exact a07 pure GUI predicate');ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<a07-pure-GUI>','exec'),ns)
 need(ns['survivor_window_matches'](body,before,after,army_id=93,native_id=maps[2][93]['native_carmy_id'],binding=binding),'Actual native survivor GUI independently matches')
 need(ui['survivor_army_window_visible_verified'] is True and ui['additional_UI_Select_count']==0 and ui['no_new_split_or_merge'] is True,'Actual GUI no extra military action')
 film=j('original/FILM-CONTROLLER.actual.json');need(film.get('error') is None and film['action_and_endpoint_chain_complete'] is True and film['survivor_UI_visible_verified'] is True and film['recorder_finish']['state']=='NORMAL_TREE_EMPTY' and film['recorder_finish']['job']['returncode']==0 and film['recorder_finish']['job']['job_active_processes']==0,'Actual completed controller and recorder')
 _,pair=archive(data['pair/r193-reverse-pair-evidence.zip']);old=j('original/F0-ENDPOINT.actual.json');pairbaseline=json.loads(pair['original/baseline-ENDPOINT.actual.json']);pairproof=json.loads(pair['original/runtime-actor-identity.actual-a01.json'])
 need(old['normal_save_sha256']==pairbaseline['normal_save_sha256'] and old['frozen_observable']==pairbaseline['frozen_observable'],'Independent pair same S0/full F0')
 need((proof['pid'],proof['process_creation_filetime_100ns'])!=(pairproof['pid'],pairproof['process_creation_filetime_100ns']),'Independent actual cold lifetime')
 need(result['numeric_forward_sameS0_reconfirmation'] is True and result['candidate_R09_business_close'] is True and result['R09_closed_or_7of14_automatically_counted'] is False,'Credit candidate boundary')
 need(result['merge_supply']['upper_clamp_observed'] is False and result['merge_supply']['distinct_pre_stock_observed'] is False,'No invented clamp/distinct-stock positive')
 return {'numeric_forward_sameS0_reconfirmation':True,'production_pure_replay':True,'actual_survivor_GUI_native_readback_verified':True,'candidate_R09_business_close':True,'R09_closed_or_7of14_automatically_counted':False,'dynamic_clean_human_qualified':False,'full_Driver_save_video_body_reads':0,'SDK_game_actions':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);a=p.parse_args();need(a.archive.stat().st_size<=1024*1024,'1MiB portable bound');m,d=archive(a.archive.read_bytes());print(json.dumps({'status':'R194_PORTABLE_PRODUCTION_REPLAY_PASS','members':len(d),**replay(d)}))
if __name__=='__main__':main()
