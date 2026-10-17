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
def verify(archive,manifest,repo):
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
  c=get(manifest['roles']['binding']);need(c['role']=='control' and c['run_id']==manifest['run_id'] and c['source_head']==manifest['source_head'] and c['machine_id']==manifest['machine_id'],'strict historical control binding differs')
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
  q2=get(manifest['roles']['baseline_query2']);need(q2['request']['tool']=='ck3_query_army_strengths' and q2['body']['query_sequence']==2 and q2['army_history_evidence']['raw_result_reference']['sha256']==base['raw_result_reference']['sha256'],'original query2 small complete-reference result differs')
  need(base['native_carmy_id']==base['native_resolution_admission']['native_carmy_id'] and bool(base['full_DATA_signature']),'baseline typed identity/full DATA absent')
  seen=[]
  for item in manifest['roles']['days']:
   d=get(item['complete']);clock=get(item['clock']);arm=get(item['arm']);status_packet=get(item['clock_response']);claim=get(item['action_claim']);absolute=item['absolute_day'];local=d['day'];segment=d['segment'];start=c['S0']['date_raw']+24*(absolute-1);target=start+24
   need(d['status']=='exact_day_and_readbacks_complete' and d['absolute_day']==absolute and d['date_raw']==target and d['starting_date_raw']==start,'exact day date/status differs')
   need(d['PID']==c['pid'] and d['create_filetime']==c['create_filetime'] and d['episode']==c['episode'] and d['run_id']==c['run_id'],'daily runtime lifetime differs')
   route=d['actual_route_state'];need(route['army_id']==c['army_id'] and route['owner_character_id']==c['actor_id'] and route['controllable'] is True and route['current_province_id']==c['start_province_id'] and route['route_read_status']=='complete_empty' and route['route_province_ids']==[] and route.get('move_target_province_id') is None and not route['in_combat'] and not route['retreating'] and route['army_state']!='embarked','control moved/fought/embarked or owner lost')
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
   slices.append({'segment_id':segment['segment_id'],'date_raw':close['date_raw'],'window':session['controlled_window_id'],'payment_epoch':sampling['epoch'],'natural_epoch':ad['natural_epoch'],'natural_records':j['natural_journal_status']['retained_records'],'payment_records':sampling['retained_records'],'production_consumer_result':result})
  need(len(slices)==2 and slices[0]['date_raw']==c['S0']['date_raw']+24*24 and slices[1]['date_raw']==c['S0']['date_raw']+32*24,'terminal segment duration differs')
  need(slices[0]['window']!=slices[1]['window'] and slices[0]['payment_epoch']!=slices[1]['payment_epoch'] and slices[0]['natural_epoch']!=slices[1]['natural_epoch'],'segments reused a fence/window')
  normal=get(manifest['roles']['normal_save']);boot=get(manifest['roles']['bootstrap']);release=get(manifest['roles']['screen_release']);saved=get(manifest['roles']['native_save_response']);checkpoint=saved['body']['checkpoint'];session=boot['session'];shutdown=session['shutdown'];bus=json.loads(release['stdout'])
  need(normal['machine_id']==boot['machine_id']==release['machine_id']==c['machine_id'] and normal['run_id']==release['run_id']==c['run_id'] and normal['date_raw']==c['S0']['date_raw']+32*24 and normal['actor_id']==c['actor_id'],'normal endpoint is another runtime/date')
  need(saved['is_error'] is False and saved['body']['accepted'] is True and checkpoint['status']=='saved' and checkpoint['date_raw']==normal['date_raw'] and checkpoint['episode_character_id']==c['actor_id'],'actual native normal checkpoint missing')
  need(session['ok'] is True and session['exit_reason']=='process_exit' and session['process_exit_code']==0 and shutdown['tree_gone'] is True and shutdown['cleanup_proven'] is True and shutdown['job_active_processes_final']==0 and boot['sdk_thread_exited'] is True and boot.get('sdk_error') is None and boot.get('supervisor_error') is None and boot['screen_lease']['thread_exited'] is True,'normal process/SDK/keeper closure unproven')
  recorder=boot['recorder'];need(recorder['state']=='NOT_STARTED' and recorder['capture_guard_thread_alive'] is False and recorder['directory'] is None and recorder['cleanup_error'] is None and boot['recording_started_automatically'] is False and normal['recording_scope']['status']=='NOT_STARTED' and normal['recording_scope']['recorder_started'] is False,'stationary control unexpectedly recorded or recorder cleanup unproven')
  need(release['exit_code']==0 and release['normal_exit_zero'] is True and bus['ok'] is True and bus['task']['state']=='done' and bus['task']['resources']==[],'actual exclusive screen release not done/empty')
 return {'status':'HISTORICAL_CONTROL32_AND_TWO_TERMINAL_WINDOWS_REPLAYED','producer_machine_id':c['machine_id'],'run_id':c['run_id'],'source_head':c['source_head'],'actual_distinct_completed_days':32,'segments':slices,'normal_exit0_and_screen_release':True,'scope':'strict control only; no independent treatment or pair credit','full_v2_qualified':False,'original_R07_v1_qualified':False,'zero_fee_proved':False,'SDK_calls':0,'archive_extracted_to_disk':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args();result=verify(a.archive,json.loads(a.manifest.read_text(encoding='utf-8-sig')),a.repo)
 raw=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if a.output:
  with a.output.open('x',encoding='utf-8',newline='\n') as f:f.write(raw)
 else:print(raw)
if __name__=='__main__':main()
