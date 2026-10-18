"""Replay only archived R205 small evidence; stdlib, no SDK/source paths opened."""
import collections,hashlib,json,sys,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
MACHINE='desktop-3fevhd2-1c74096080'
def need(v,msg):
 if not v:raise ValueError(msg)
def derive(rows):
 result=rows['r04/RESULT.actual.json'];q=rows['q/R205-Q-SCOUT.actual-a02.json'];frame=result['source_frame']
 need(result['machine_id']==q['machine_id']==MACHINE and frame['actor']==31254 and frame['origin']==2635,'Robert source binding')
 need(frame['date_raw']==53148192 and result['same_frame_fence'] is True and result['move_executed'] is False,'scout frame/actions')
 holding=rows['r04/holdings.json']['body']['war_occupation_targets_v1']
 side=dict(collections.Counter(r['territory_side'] for r in holding['rows']))
 previews=[]
 for item in result['observations']:
  preview=item['full_preview'];route=preview['route_preview'];cond=route['county_entry_condition_v1']
  need(preview['accepted'] is True and cond['native_condition_called'] is True and cond['native_condition_passes'] is False
   and cond['county_objects_differ'] is False and cond['identity_before_after_match'] is True,'actual same-county false')
  previews.append({'target':item['target'],'firsthop':item['firsthop'],'route':route['route_province_ids'],
   'condition':cond['native_condition_passes'],'county_objects_differ':cond['county_objects_differ'],
   'same_county_identity':cond['source_county_identity'],'P_trace_returned':cond['predicate_trace_v1']['native_predicate_returned']})
 modes=[]
 for row in q['rows']:
  slots=[s for o in row['ordered_occurrences'] for s in o['physical_slots']]
  counts=dict(collections.Counter('unknown' if s['native_unit_position_eligible'] is None else 'true' if s['native_unit_position_eligible'] else 'false' for s in slots))
  need(len(slots)==147 and all(s['final_shared_q_i32']==0 for s in slots),'q slots not all actual projected0')
  need(counts=={'false':21,'unknown':126},'position domain changed')
  modes.append({'mode':row['mode'],'input_basis':row['input_basis'],'physical_slots':len(slots),'q_zero':len(slots),
   'position':dict(true=counts.get('true',0),false=counts['false'],unknown=counts['unknown']),
   'conditional_positive_targets':sum(s['conditional_positive_target'] for s in slots)})
 red=rows['off/natural-a01-schema-RED.json'];need(red['is_error'] is True and red['request']['arguments']['expected_revision'] is None,'original schema RED changed')
 off={}
 for family,key in [('natural_phase','off/natural-a02.json'),('regular_core','off/regular-a02.json')]:
  row=rows[key];body=row['body'];state=body['army_observer_research_sampling_v1'][family]
  need(row['is_error'] is False and row['request']['arguments']['expected_revision']==5
   and body['queried_revision']==5 and body['queried_native_revision']==4 and body['queried_date_raw']==53148192,'real public/native OFF query')
  need(state['installed'] is True and state['available'] is True and state['capture_enabled'] is False and state['busy'] is False
   and state['clear_completed'] is True and state['active_captures']==state['retained_records']==state['epoch']==0,'OFF actual state')
  off[family]={'public_revision':5,'native_revision':4,'date_raw':53148192,'state':state,'at_utc':row['at']}
 save=rows['close/NORMAL-SAVE.actual.json'];boot=rows['close/bootstrap-result.json'];release=rows['close/SCREEN-RELEASE.actual.json']
 need(save['machine_id']==boot['machine_id']==release['machine_id']==MACHINE and save['actor_id']==31254 and save['date_raw']==53148192,'normal close binding')
 need(save['recording_scope']['status']=='NOT_STARTED' and save['observer_cleanup']['status']=='NOT_CONFIGURED','unconfigured hook overwritten')
 need(boot['session']['process_exit_code']==0 and boot['session']['exit_reason']=='process_exit'
  and boot['session']['shutdown']['cleanup_proven'] is True and boot['sdk_thread_exited'] is True,'normal exit0')
 cas=json.loads(release['stdout']);need(release['exit_code']==0 and release['task_done_resources_empty'] is True
  and cas['ok'] is True and cas['task']['state']=='done' and cas['task']['resources']==[],'CAS actual release')
 return {'machine_id':MACHINE,'run_id':'desktop-3fevhd2-1c74096080--vanilla--R0205','source_head':result['source_head'],
  'identity':{'actor_name':'Robert','actor_full_id':31254,'date_raw':53148192,'army_full_id':18,'origin':2635,
   'pid':frame['pid'],'generation':frame['generation'],'episode':frame['episode_run_id'],'creation_ft':save['process_creation_filetime_100ns']},
  'r04':{'status':result['status'],'war':4,'holding_rows':len(holding['rows']),'side_counts':side,'previews':previews,
   'initial_public_revision':result['initial_public_revision'],'ending_public_revision':result['ending_public_revision'],'same_frame_fence':True,'move_executed':False},
  'r06':{'modes':modes,'actual_ADD_observed':q['actual_ADD_observed'],'conditional_only':q['conditional_only'],
   'probe_install':'not run: Root reports no eligible target; no probe business qualification'},
  'off':off,'schema_RED_preserved':True,'normalclose':{'date_raw':save['date_raw'],'save_metadata_at':save['observed_at_utc'],
   'manual_OFF_after_Save_before_Exit':save['observed_at_utc']<off['natural_phase']['at_utc']<off['regular_core']['at_utc']<boot['at'],
   'observer_cleanup':'NOT_CONFIGURED','manual_OFF_confirmed_separately':True,'recording':'NOT_STARTED','process_exit_code':0,
   'CAS_done_resources_empty':True,'CAS_sequence':cas['task']['last_sequence'],'checkpoint_pin':save['checkpoint']},
  'new_claims':{'days':0,'Move':0,'recording':0,'R04_physical_county_positive':False,'R06_ADD':False,'formal_cue':False},
  'unchanged_progress':'research9/14 business6/11 dynamic0/11 ABC0/3; no added qualification'}
def main():
 index=json.loads((HERE/'source-index.json').read_text(encoding='utf-8'));need(index['machine_id']==MACHINE,'index machine')
 data={}
 with zipfile.ZipFile(HERE/'originals.zip') as archive:
  need(sorted(archive.namelist())==sorted(r['member'] for r in index['archive_members']),'archive members differ')
  for row in index['archive_members']:
   b=archive.read(row['member']);need(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'exact original pin differs')
   data[row['member']]=json.loads(b.decode('utf-8-sig'))
 actual=derive(data);expected=json.loads((HERE/'summary.actual.json').read_text(encoding='utf-8'))
 need(actual==expected,'literal projection differs');print(json.dumps({'result':'PASS','machine_id':MACHINE,'original_count':len(data),
  'SDK_calls':0,'large_Driver_reads':0,'media_reads':0,'scope':'exact archive pins + literal R205 scout/OFF/close replay only'},indent=2))
if __name__=='__main__':main()
