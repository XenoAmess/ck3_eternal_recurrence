"""Replay only a normal-close metadata append; never rerun payment consumers."""
from pathlib import Path
import argparse,hashlib,json,zipfile
def need(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def verify(archive,manifest,pair_result):
 raw=Path(archive).read_bytes();need(len(raw)==manifest['archive']['bytes'] and sha(raw)==manifest['archive']['sha256'],'append archive pin differs')
 pb=Path(pair_result).read_bytes();need(len(pb)==manifest['production_pair_replay']['bytes'] and sha(pb)==manifest['production_pair_replay']['sha256'],'actual historical production result changed');pair=json.loads(pb)
 with zipfile.ZipFile(archive) as z:
  rows={r['member']:r for r in manifest['entries']};need(set(z.namelist())==set(rows) and len(z.namelist())==len(rows),'append members differ');cache={}
  for name,r in rows.items():
   b=z.read(name);need(len(b)==r['bytes'] and sha(b)==r['sha256'],'append original exact bytes differ');cache[name]=json.loads(b.decode('utf-8-sig'))
  get=lambda role:cache[manifest['roles'][role]]
  normal=get('normal_save');observed=get('bootstrap_observed');boot=get('bootstrap');release=get('screen_release');saved=get('native_save');before=get('after_snapshot');c=manifest['binding'];session=boot['session'];shutdown=session['shutdown'];checkpoint=saved['body']['checkpoint'];bus=json.loads(release['stdout'])
  need(all(v['machine_id']==c['machine_id'] for v in (normal,observed,boot,release,saved,before)),'normal close source machine differs')
  need(normal['source_head']==c['source_head']==pair['source_head'] and normal['run_id']==release['run_id']==observed['run_id']==pair['run_id']==c['run_id'],'normal close source/run differs')
  need(normal['pid']==session['pid']==c['pid'] and normal['process_creation_filetime_100ns']==c['create_filetime'] and normal['episode_run_id']==c['episode'] and normal['actor_id']==c['actor_id'] and normal['date_raw']==53148960,'normal close runtime/date differs')
  need(saved['is_error'] is False and saved['body']['accepted'] is True and checkpoint['status']=='saved' and checkpoint['date_raw']==normal['date_raw'] and checkpoint['episode_character_id']==c['actor_id'],'normal checkpoint not actually saved')
  frame=before['body'];diag=frame.get('diagnostics') or {};need(before['is_error'] is False and frame['paused'] is True and frame['date_raw']==normal['date_raw'] and frame['episode_run_id']==c['episode'] and diag['bridge_pid']==c['pid'] and diag['connection_generation']==c['generation'],'independent post-save frame differs')
  armies=[a for a in frame['player_armies'] if a['army_id']==c['army_id']];need(len(armies)==1 and armies[0]['current_province_id']==1032 and armies[0]['army_state']=='embarked' and armies[0]['route_province_ids']==[],'saved endpoint is not the actual sea empty-route army')
  need(session['ok'] is True and session['exit_reason']=='process_exit' and session['process_exit_code']==0 and shutdown['tree_gone'] is True and shutdown['cleanup_proven'] is True and shutdown['job_active_processes_final']==0,'normal process tree exit0 not complete')
  need(boot['sdk_thread_exited'] is True and boot.get('sdk_error') is None and boot.get('supervisor_error') is None and boot['screen_lease']['thread_exited'] is True and boot['recorder']['state']=='NORMAL_TREE_EMPTY','SDK/keeper/recorder final lifecycle incomplete')
  need(observed['normal_exit_zero'] is True and release['exit_code']==0 and release['normal_exit_zero'] is True and bus['ok'] is True and bus['task']['state']=='done' and bus['task']['resources']==[],'screen actual CAS release not done/empty')
  prior=pair['pair_assessment'];positive=prior['selected_army_positive_sourcequalified_SUB_callbacks'];need(prior['independent_common_S0_two_fresh_arms'] is True and prior['same_exact_days_per_arm']==32 and prior['control_stationary_throughout'] is True and prior['treatment_one_normal_Move_and_day31_actual_embark'] is True and bool(positive),'actual paired research core incomplete')
 return {'schema':'xar.e04.r195-r196-r07-v2-research-core-closure.v1','producer_machine_id':c['machine_id'],'source_head':c['source_head'],'run_ids':[manifest['control_run_id'],c['run_id']],'R07_v2_research_core_closed':True,'two_fresh_arm_pair_complete':True,'exact_days_each':32,'positive_sourcequalified_personal_SUB':positive,'normal_checkpoint':normal['checkpoint'],'both_arms_normal_exit0':True,'screen_released_and_resources_empty':True,'old_control_replayed':False,'payment_consumer_replayed_in_close_append':False,'single_window_consumer_outputs_full_v2_qualified_remain_false':True,'original_R07_v1_qualified':False,'zero_fee_proved':False,'maintenance_attribution':'unclosed','film_dynamic_qualified':False,'film_PTS_coverage_qualified':False,'film_human_signoff':False,'SDK_calls':0,'archive_extracted_to_disk':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--pair-result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=verify(a.archive,json.loads(a.manifest.read_text(encoding='utf-8')),a.pair_result)
 with a.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
if __name__=='__main__':main()
