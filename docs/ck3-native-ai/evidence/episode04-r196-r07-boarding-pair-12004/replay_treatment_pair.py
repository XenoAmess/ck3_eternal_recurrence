"""Offline historical control evidence replay. No SDK/game/desktop or extraction.

ZIP members retain exact original bytes. --repo supplies the pinned production
Python consumers; installed CK3/Steam/native bytes are neither read nor inferred.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,zipfile
sys.dont_write_bytecode=True
def need(x,m):
 if not x:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def module(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def verify(archive,manifest,repo,control_root):
 repo=Path(repo).resolve();raw=Path(archive).read_bytes();need(len(raw)==manifest['archive']['bytes'] and sha(raw)==manifest['archive']['sha256'],'archive exact bytes differ')
 for row in manifest['production_consumer_sources']:
  p=repo/row['repository_path'];b=p.read_bytes();need(len(b)==row['bytes'] and sha(b)==row['sha256'],'production consumer source changed '+row['repository_path'])
 sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src')]
 from xar_autoplayer.bridge.war_payment_observations_v1 import normalize_journal
 from xar_autoplayer.bridge.native_driver import _normalize_tactical_daily_sentinel_status as norm,_validate_tactical_daily_sentinel_arm as va,_validate_tactical_daily_sentinel_stop as vs
 consumer=module(repo/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/r07_v2_contract.py','portable_r195_production_r07')
 with zipfile.ZipFile(archive) as z:
  entries={x['member']:x for x in manifest['entries']};need(len(entries)==len(manifest['entries']),'duplicate logical original identity')
  need(z.namelist()==[manifest['archive']['container_member']],'archive container member set differs')
  need(sum(x.file_size for x in z.infolist())<=16*1024*1024,'archive inflation exceeds16MiB memory budget')
  payload=z.read(manifest['archive']['container_member']);need(len(payload)==manifest['archive']['container_bytes'] and sha(payload)==manifest['archive']['container_sha256'],'lossless container exact bytes differ')
  cursor=0
  for row in manifest['entries']:
   need(row['offset']==cursor and row['bytes']>0,'original byte ranges overlap or leave gaps');cursor+=row['bytes']
  need(cursor==len(payload),'original byte index leaves trailing data')
  cache={}
  def get(name):
   if name not in cache:
    r=entries[name];b=payload[r['offset']:r['offset']+r['bytes']];need(len(b)==r['bytes'] and sha(b)==r['sha256'],'original entry exact bytes differ '+name);cache[name]=json.loads(b.decode('utf-8-sig'))
   return cache[name]
  for name in entries:get(name)
  c=get(manifest['roles']['binding']);need(c['role']=='treatment' and c['run_id']==manifest['run_id'] and c['source_head']==manifest['source_head'] and c['machine_id']==manifest['machine_id'],'strict historical treatment binding differs')
  by_source={row['original_path'].replace('\\','/').casefold():row['member'] for row in manifest['entries']}
  def source(path):
   need(path.replace('\\','/').casefold() in by_source,'required raw source omitted '+path)
   return get(by_source[path.replace('\\','/').casefold()])
  def frame(packet,date):return consumer.snapshot_body(packet,{'machine_id':c['machine_id'],'episode':c['episode'],'pid':c['pid'],'generation':c['generation'],'actor_id':c['actor_id']},date)
  def raw_families(stage):
   packets=[source(p) for p in stage['sources']]
   found=[p for p in packets if 'army_observer_research_sampling_v1' in p.get('body',{}) and p['body'].get('step')=='query-army-observer-research-sampling-v1']
   need(len(found)==1,'exact one original family query required')
   return found[0]['body']['army_observer_research_sampling_v1']
  for member in manifest['roles']['stage_chain']:
   stage=get(member);need(stage['binding']==c,'stage chain belongs to another runtime')
   previous=None
   for path in stage.get('sources',[]):
    packet=source(path);need(packet['machine_id']==c['machine_id'] and packet['is_error'] is False,'stage raw source machine/error differs')
    if packet['request']['tool']=='ck3_take_snapshot':previous=frame(packet,stage['date_raw'])
    elif 'expected_revision' in packet['request'].get('arguments',{}):
     need(previous is not None and packet['request']['arguments']['expected_revision']==previous['revision'],'stage raw request lost independent revision fence')
     body=packet['body']
     if 'queried_native_revision' in body:need(body['queried_native_revision']==previous['native_revision'],'stage raw response is another native frame')
  base=get(manifest['roles']['baseline']);need(base['binding']==c and base['date_raw']==c['S0']['date_raw'] and base.get('baseline_recovery',{}).get('original_query_not_replayed') is True,'actual recovered baseline differs')
  q2=get(manifest['roles']['baseline_query']);need(q2['request']['tool']=='ck3_query_army_strengths' and q2['body']['query_sequence']==base['baseline_recovery']['original_query_sequence'] and q2['army_history_evidence']['raw_result_reference']['sha256']==base['raw_result_reference']['sha256'],'original query2 small complete-reference result differs')
  need(base['native_carmy_id']==base['native_resolution_admission']['native_carmy_id'] and bool(base['full_DATA_signature']),'baseline typed identity/full DATA absent')
  seen=[]
  for item in manifest['roles']['days']:
   d=get(item['complete']);clock=get(item['clock']);arm=get(item['arm']);status_packet=get(item['clock_response']);claim=get(item['action_claim']);absolute=item['absolute_day'];local=d['day'];segment=d['segment'];start=c['S0']['date_raw']+24*(absolute-1);target=start+24
   need(d['status']=='exact_day_and_readbacks_complete' and d['absolute_day']==absolute and d['date_raw']==target and d['starting_date_raw']==start,'exact day date/status differs')
   need(d['PID']==c['pid'] and d['create_filetime']==c['create_filetime'] and d['episode']==c['episode'] and d['run_id']==c['run_id'],'daily runtime lifetime differs')
   route=d['actual_route_state'];need(route['army_id']==c['army_id'] and route['owner_character_id']==c['actor_id'] and route['controllable'] is True and not route['in_combat'] and not route['retreating'],'selected treatment army owner/control/combat changed')
   if absolute<=30:need(route['current_province_id']==c['start_province_id'] and route['route_province_ids']==[1032] and route['move_target_province_id']==1032 and route['army_state']!='embarked','prearrival treatment route differs')
   else:need(route['current_province_id']==1032 and route['route_read_status']=='complete_empty' and route['route_province_ids']==[] and route['move_target_province_id'] is None and route['army_state']=='embarked','actual sea arrival on day31/32 differs')
   step=f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-0'
   need(arm['machine_id']==c['machine_id'] and arm['is_error'] is False and arm['request']['tool']=='ck3_execute_step' and arm['request']['arguments']['step']==step,'original exactday Arm source differs')
   armed=norm(arm['body']['tactical_daily_sentinel']);va(arm['body'],armed,arm_step=step,starting_date_raw=start,target_date_raw=target,speed=5,mode='terminal_or_sentinel',watch_army_ids=(),sentinel_scope='exact_one_day')
   need(status_packet['machine_id']==c['machine_id'] and status_packet['is_error'] is False and status_packet['request']['tool']=='ck3_execute_step' and status_packet['request']['arguments']['step']=='research-query-tactical-daily-sentinel-v1','original exactday status source differs')
   stopped=norm(status_packet['body']['tactical_daily_sentinel']);vs(stopped,arm_status=armed,starting_date_raw=start,target_date_raw=target,ending_date_raw=target,elapsed_days=1,speed=5,mode='terminal_or_sentinel',watch_army_ids=())
   need(stopped==d['clock']==clock['clock'] and clock['arm_generation']==armed['generation'] and clock['date_raw']==target,'clock canonical/raw mismatch')
   need(claim['day']==local and claim['date_raw']==start and claim['target_date_raw']==target,'original once-day claim differs')
   seen.append(absolute)
  need(sorted(seen)==list(range(1,33)) and len(seen)==32,'control must contain exact32 distinct completed days')
  slices=[]
  for segment in manifest['roles']['segments']:
   ad=get(segment['admission']);close=get(segment['journal_close']);cash=get(segment['terminal_cash']);before=get(segment['terminal_before']);off=get(segment['payment_off_readback']);naturaloff=get(segment['natural_off_readback'])
   need(all(v['binding']==c for v in (ad,close,off,naturaloff)) and ad['result']=='actual-window-admitted' and close['date_raw']==before['body']['date_raw'],'segment canonical identity/date differs')
   need(ad['sampling']['capture_enabled'] is True and ad['sampling']['retained_records']==0 and ad['absolute_day_offset']==segment['absolute_day_offset'],'new segment initial empty fence differs')
   families=ad['family_actual'];need(len(families)==9 and all(row['capture_enabled'] is (name=='natural_phase') and row['installed'] and row['available'] and not row['busy'] and (row['capture_enabled'] or row['clear_completed'] and row['retained_records']==0) for name,row in families.items()),'natural-only/other8-off segment fence differs')
   j=normalize_journal(cash['body']['war_payment_observations_v1'],snapshot=before['body'],machine_id=c['machine_id']);session=j['current_session'];sampling=j['sampling']
   binding={'machine_id':c['machine_id'],'episode':c['episode'],'pid':c['pid'],'create_filetime':c['create_filetime'],'generation':c['generation'],'actor_id':c['actor_id'],'unit_id':c['army_id'],'payment_epoch':sampling['epoch'],'window_id':session['controlled_window_id'],'date_raw':close['date_raw'],'segment_id':segment['segment_id'],'previous_latest_sequence':ad['baseline_latest_sequence']}
   closed_families=raw_families(close)
   need(sampling['epoch']==ad['sampling']['epoch']==close['sampling']['epoch'] and session['controlled_window_id']==ad['session']['controlled_window_id']==close['session']['controlled_window_id'] and closed_families['natural_phase']['epoch']==ad['natural_epoch']==close['natural_epoch']==families['natural_phase']['epoch'],'segment payment/natural identities differ')
   need(raw_families(ad)==families and raw_families(naturaloff)==naturaloff['families'],'natural fences canonical/raw differ')
   need(closed_families['natural_phase']['capture_enabled'] is True and closed_families['natural_phase']['retained_records']==j['natural_journal_status']['retained_records'],'terminal natural family source differs')
   result=consumer.consume_window(cash,before,binding,normalize_journal)
   need(off['window_off'] is True and off['sampling']['capture_enabled'] is False and off['sampling']['busy'] is False and off['sampling']['clear_completed'] is True and off['sampling']['retained_records']==0,'payment OFF/clear fence missing')
   need(naturaloff['actual_all_off_cleared'] is True and len(naturaloff['families'])==9 and all(not x['capture_enabled'] and not x['busy'] and x['clear_completed'] and x['retained_records']==0 for x in naturaloff['families'].values()),'natural all-OFF/clear fence missing')
   need(j['read_complete'] and not j['overwritten'] and not j['publication_failures'] and j['natural_journal_status']['read_complete'] and not j['natural_journal_status']['overwritten_records'] and not j['natural_journal_status']['failed_appends'],'terminal journal lost/partial')
   slices.append({'segment_id':segment['segment_id'],'date_raw':close['date_raw'],'window':session['controlled_window_id'],'payment_epoch':sampling['epoch'],'natural_epoch':ad['natural_epoch'],'natural_records':j['natural_journal_status']['retained_records'],'payment_records':sampling['retained_records'],'production_consumer_result':result,'raw_payment_record_summary':[{'journal_sequence':r['journal_sequence'],'kind':r['kind'],'amount_raw':r['amount_raw'],'resource_kind_raw':r['resource_kind_raw'],'component_raw':r['component_raw'],'caller_return_rva':r['caller_return_rva'],'before_character_id':r['before']['character_id'],'after_character_id':r['after']['character_id'],'before_army_id':r['before']['army_id'],'after_army_id':r['after']['army_id'],'requested_unit_id':r['before']['requested_unit_id'],'source_boarding_call_chain_matches_flag':r['source_boarding_call_chain_matches']} for r in j['records']]})
  need(len(slices)==2 and slices[0]['date_raw']==c['S0']['date_raw']+24*24 and slices[1]['date_raw']==c['S0']['date_raw']+32*24,'terminal segment duration differs')
  need(slices[0]['window']!=slices[1]['window'] and slices[0]['payment_epoch']!=slices[1]['payment_epoch'] and slices[0]['natural_epoch']!=slices[1]['natural_epoch'],'segments reused a fence/window')
  # Reuse the already sealed R195 production result; do not replay old control.
  control_root=Path(control_root)
  for name,pin in manifest['control_source_refs'].items():
   b=(control_root/name).read_bytes();need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'sealed control evidence changed '+name)
  cm=json.loads((control_root/'R195-CONTROL-EVIDENCE.manifest-a01.json').read_text(encoding='utf-8'));cr=json.loads((control_root/'PRODUCTION-REPLAY.actual-a01.json').read_text(encoding='utf-8'))
  need(cr['actual_distinct_completed_days']==32 and cr['normal_exit0_and_screen_release'] is True and cr['source_head']==c['source_head'],'existing control replay source/status differs')
  with zipfile.ZipFile(control_root/cm['archive']['file']) as cz:cp=cz.read(cm['archive']['container_member'])
  need(len(cp)==cm['archive']['container_bytes'] and sha(cp)==cm['archive']['container_sha256'],'existing control container differs')
  ce={e['member']:e for e in cm['entries']}
  def cg(member):
   row=ce[member];raw=cp[row['offset']:row['offset']+row['bytes']];need(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'control baseline original changed');return json.loads(raw.decode('utf-8-sig'))
  cb=cg(cm['roles']['binding']);baseline_control=cg(cm['roles']['baseline']);compare=get(manifest['roles']['compare'])
  need(cb['role']=='control' and cb['run_id']!=c['run_id'] and (cb['pid'],cb['create_filetime'])!=(c['pid'],c['create_filetime']),'not independent fresh runtimes')
  for key in ('S0','source_head','bridge_dll_sha256','executable_sha256','actor_id','army_id'):need(cb[key]==c[key],'cross-arm source identity differs '+key)
  for key in ('date_raw','full_DATA_signature','current_soldiers','maximum_soldiers','current_supply_raw','active_wars','treasury_observation','current_commander_id'):need(baseline_control[key]==base[key],'actual independent common-S0 baseline differs '+key)
  need(compare['independent_common_S0_baselines_match'] is True,'Root actual baseline compare absent')
  move=get(manifest['roles']['move_ACK']);claim=get(manifest['roles']['move_claim']);moved=get(manifest['roles']['move_readback']);movement=moved['movement']
  need(claim['kind']=='move' and claim['tool']=='ck3_move_army' and claim['arguments']['army_id']==c['army_id'] and claim['arguments']['target_province_id']==1032 and claim['date_raw']==c['S0']['date_raw'] and move['binding']==c and moved['binding']==c,'actual one normal first-sea Move source differs')
  need(movement['first_route_edge_weight_cost_raw']==3000000 and movement['current_edge_movement_rate_raw']==100000 and movement['first_route_edge_remaining_duration']=={'raw':3000000,'scale':100000} and movement['current_province_definition_byte_1b_u8']==1 and movement['first_route_target_province_definition_byte_1b_u8']==0,'actual initial30day first-sea native operands differ')
  days={x['absolute_day']:get(x['complete']) for x in manifest['roles']['days']};day30=days[30]['actual_movement_progress'];need(day30['accumulated_movement_weight_raw']==3000000 and day30['first_route_edge_weight_cost_raw']==3000000 and day30['first_route_edge_remaining_duration']=={'raw':0,'scale':100000} and day30['first_edge_arrival_provider_byte_e_u8']==0,'actual day30 equality/zeroETA edge absent')
  positives=[q for part in slices for q in part['production_consumer_result']['selected_army_boarding_callbacks']]
  need(all(q['requested_amount_raw']>0 and q['payer_character_id']==c['actor_id'] and q['requested_public_unit_id']==c['army_id'] and q['returned_balance_matches_requested_sub'] is True for q in positives),'boarding payer/unit/positive SUB mismatches')
  control_boarding=[q for part in cr['segments'] for q in part['production_consumer_result']['selected_army_boarding_callbacks']]
  need(not control_boarding,'stationary control includes selected-army boarding callback')
  film=get(manifest['roles']['film']);need(film['machine_id']==c['machine_id'] and film['run_id']==c['run_id'] and film['dayrunner_exit_code']==0 and film['start']['capture_source']['owned_ck3_pid']==c['pid'] and film['finish']['state']=='NORMAL_TREE_EMPTY','actual single recording technical lifecycle differs')
  pair={'independent_common_S0_two_fresh_arms':True,'same_source_native_actor_army_fullDATA_commander_treasury':True,'same_exact_days_per_arm':32,'control_stationary_throughout':True,'treatment_one_normal_Move_and_day31_actual_embark':True,'selected_army_positive_sourcequalified_SUB_callbacks':positives,'control_selected_army_boarding_callbacks':[],'R195_production_replay_reused_without_rerun':True,'R07_v2_core_evidence_observed_before_normal_close':bool(positives),'full_pair_formal_release_qualified':False,'normal_close_terminal_append_required':True,'film_dynamic_and_human_signoff':False,'original_R07_v1_qualified':False,'zero_fee_proved':False,'maintenance_attribution':'unclosed'}
 return {'status':'HISTORICAL_TREATMENT32_TWO_TERMINAL_WINDOWS_AND_COMMON_S0_PAIR_REPLAYED','producer_machine_id':c['machine_id'],'run_id':c['run_id'],'source_head':c['source_head'],'actual_distinct_completed_days':32,'segments':slices,'pair_assessment':pair,'normal_close_included':False,'full_v2_qualified':False,'original_R07_v1_qualified':False,'zero_fee_proved':False,'SDK_calls':0,'archive_extracted_to_disk':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--control-root',type=Path,required=True);a=p.parse_args();result=verify(a.archive,json.loads(a.manifest.read_text(encoding='utf-8-sig')),a.repo,a.control_root)
 raw=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if a.output:
  with a.output.open('x',encoding='utf-8',newline='\n') as f:f.write(raw)
 else:print(raw)
if __name__=='__main__':main()
