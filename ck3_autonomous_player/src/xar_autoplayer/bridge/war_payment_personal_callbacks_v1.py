"""Offline personal-wallet callback projection, separate from payment attribution.

Consumes existing small portable R07 evidence. No SDK/native-driver import,
game query, EXE/source locator, archive extraction or original-path fallback.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
import zipfile

EXE='98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518'
MASK=(1<<64)-1
def need(ok,msg):
 if not ok:raise ValueError(msg)
def integer(v,lo,hi):return type(v) is int and lo<=v<=hi
def signed(v):return integer(v,-(1<<63),(1<<63)-1)
def wrap(v):return ((v+(1<<63))&MASK)-(1<<63)
def fingerprint(raw):return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def same_session(a,b):
 keys=('pid','process_create_time_100ns','connection_generation','controlled_window_id','player_character_full_id','game_state_identity_witness')
 return all(integer(a.get(k),1,MASK) and a[k]==b.get(k) for k in keys) and a.get('same_owned_process_no_load_window') is True and b.get('same_owned_process_no_load_window') is True and a.get('loaded_game_epoch')==b.get('loaded_game_epoch')

def project_journal(j,*,machine_id,run_id,segment_id,source,prior_boarding=(),prior_boarding_ref=None):
 need(j.get('machine_id')==machine_id and j.get('game_version')=='1.20.0.4' and j.get('steam_build_id')==25734779 and j.get('executable_sha256','').lower()==EXE,'Exact historical source identity differs')
 need(j.get('installed') is True and j.get('install_failure_flags')==0 and j.get('controlled_window_admitted') is True and j.get('read_complete') is True and j.get('overwritten')==0 and j.get('publication_failures')==0,'Journal window incomplete or lost')
 sampling=j['sampling'];records=j['records'];current=j['current_session']
 need(sampling.get('available') is True and sampling.get('capture_enabled') is True and sampling.get('busy') is False and sampling.get('active_captures')==0 and type(records) is list and len(records)==sampling.get('retained_records'),'Frozen complete active-capture boundary missing')
 need(same_session(current,current) and j.get('balance_boundary')=='whole_original_callback_entry_return' and j.get('maintenance_attribution')=='unclosed','Session or causal boundary elevated')
 need([r['journal_sequence'] for r in records]==list(range(j['oldest_sequence'],j['latest_sequence']+1)),'Retained sequence gap; no absence inference')
 out=[]
 for index,row in enumerate(records):
  kind=row['kind'];need(integer(kind,0,4),'Unknown observer kind')
  if kind not in (2,3):continue
  b,a=row['before'],row['after'];entry,returned=row['entry_event'],row['returned_event']
  need(row.get('original_called') is True and row.get('original_returned') is True and row.get('tls_depth_exceeded') is False,'Incomplete original callback')
  need(all(f.get('capture_complete') is True and f.get('failed_reads')==0 for f in (b,a)),'Incomplete wallet frame')
  need(all(integer(entry.get(k),1,MASK) and entry[k]==returned.get(k) for k in ('clock_identity','thread_id')) and integer(entry.get('sequence'),1,MASK) and integer(returned.get('sequence'),entry['sequence']+1,MASK),'Callback event ordering differs')
  se,sr=row['session_entry'],row['session_return']
  need(same_session(se,sr) and same_session(se,current),'Cross-process/load/window callback')
  need(all(b.get(k)==a.get(k) for k in ('character','character_id','character_magic','character_extension','wrapper')) and integer(b.get('character'),1,MASK) and b['character_magic']==0x43686172 and integer(b['character_id'],0,(1<<32)-1) and integer(b['character_extension'],1,MASK),'Actual account identity unavailable')
  need(row['receiver']==b['wrapper']==b['character_extension']+0xF8 and row['second_pointer']==b['character'] and all(integer(f.get('wrapper_balance_bits'),0,MASK) and f['wrapper_balance_bits']==f.get('personal_gold_bits') for f in (b,a)),'Observed wrapper does not alias actual personal slot')
  amount=row['amount_raw'];need(signed(amount),'Signed callback amount missing')
  delta=amount if kind==2 else -amount
  need(a['wrapper_balance_bits']==(b['wrapper_balance_bits']+delta)&MASK,'Whole-callback returned balance does not match requested direction/amount')
  nd=se.get('native_date_raw');ad=se.get('absolute_day_raw')
  need(integer(nd,0,MASK) and integer(ad,0,MASK) and nd==sr.get('native_date_raw') and ad==sr.get('absolute_day_raw'),'Callback date unavailable or changed')
  source_boarding=row.get('source_boarding_call_chain_matches') is True
  prior_matches=[q for q in prior_boarding if q.get('segment_id')==segment_id and q.get('writer_sequence')==row['journal_sequence'] and q.get('payment_epoch')==sampling['epoch'] and q.get('controlled_window_id')==se['controlled_window_id'] and q.get('payer_character_id')==b['character_id'] and q.get('requested_amount_raw')==amount and q.get('entry_balance_bits')==b['wrapper_balance_bits'] and q.get('returned_balance_bits')==a['wrapper_balance_bits'] and q.get('returned_balance_matches_requested_sub') is True and q.get('account_kind')==0]
  known_boarding=(len(prior_matches)==1 and prior_boarding_ref is not None and kind==3 and row['caller_return_rva']==0x28B99B2 and source_boarding and amount==300000 and row.get('parent_gateway_resource')==0 and row.get('parent_gateway_component')==3 and row.get('parent_gateway_amount')==300000 and row.get('natural_parent_matches') is True)
  r=dict(run_id=run_id,segment_id=segment_id,source=source,json_pointer=f'/body/war_payment_observations_v1/records/{index}',journal_sequence=row['journal_sequence'],observer_kind=kind,operation='personal_ADD' if kind==2 else 'personal_SUB',native_date_raw=nd,native_date_low32=nd&0xffffffff,absolute_day_raw=ad,entry_event=entry,returned_event=returned,session_entry=se,session_return=sr,caller_return_rva=row['caller_return_rva'],caller_return_rva_hex=hex(row['caller_return_rva']),subject_character_full_id=b['character_id'],subject_character_pointer=b['character'],payer_character_full_id=b['character_id'] if known_boarding else None,subject_is_current_player=b['character_id']==se['player_character_full_id']==current['player_character_full_id'],own_player_personal_account_qualified=b['character_id']==se['player_character_full_id']==current['player_character_full_id'],receiver=row['receiver'],second_pointer=row['second_pointer'],resource_kind_raw=row['resource_kind_raw'],component_raw=row['component_raw'],parent_gateway_resource=row['parent_gateway_resource'],parent_gateway_component=row['parent_gateway_component'],amount_raw=amount,field_slot_address=row['receiver']+8,field_slot_address_hex=hex(row['receiver']+8),field_slot_alias='observed wrapper+8 == observed character_extension+0x100',before_balance_bits=b['wrapper_balance_bits'],after_balance_bits=a['wrapper_balance_bits'],whole_callback_balance_matches=True,balance_boundary='whole_original_callback_entry_return',source_boarding_call_chain_claimed=source_boarding,excluded_previously_qualified_boarding_300000=known_boarding,military_maintenance_paid_raw=None,military_maintenance_payer=None,military_maintenance_cadence=None,resource_name=None)
  context=row.get('generic_wallet_context_v1')
  if known_boarding:r['boarding_exclusion_reuses_prior_qualified_result']=prior_boarding_ref
  if context is not None:
   need(kind==2 and row['caller_return_rva']==0x28A6D7C and context.get('source_entry_rva')==0x28A6D10 and context.get('maintenance_attribution')=='unclosed','Generic context source mismatch')
   cb,ca=context['before'],context['after'];keys=('value_2c0','value_2c8','value_28','value_30')
   complete=cb.get('capture_complete') is True and cb.get('context_stable') is True and cb.get('failed_reads')==0 and all(signed(cb.get(k)) for k in keys)
   computed=wrap(cb['value_2c0']-cb['value_2c8']-(cb['value_28']+cb['value_30'])) if complete else None
   need(context.get('before_computed_add_raw')==computed and context.get('before_formula_matches_amount')==(computed==amount if complete else None),'Recorded formula projection differs')
   trace=context['parent_trace']
   r['generic_wallet_context']=dict(before=cb,after=ca,computed_add_raw=computed,formula_matches_amount=computed==amount if complete else None,parent_return_rva=trace.get('parent_return_rva'),parent_return_rva_hex=hex(trace['parent_return_rva']) if trace.get('parent_return_rva') is not None else None,parent_trace=trace,endpoint_c_d_equal=all(cb[k]==ca[k] for k in ('value_28','value_30')) if all(signed(frame.get(k)) for frame in (cb,ca) for k in ('value_28','value_30')) else None,c_d_producer_store_rva=None,refresh_trigger=None,meaning='raw_source_formula_and_unwind_only')
  out.append(r)
 summary=dict(run_id=run_id,segment_id=segment_id,window_id=current['controlled_window_id'],sampling_epoch=sampling['epoch'],retained_records=len(records),retained_kind_counts=dict(Counter(str(r['kind']) for r in records)),personal_callbacks=len(out),overwritten=0,publication_failures=0,read_complete=True,source=source)
 return dict(summary=summary,records=out)

def read_arm(root,prefix):
 root=Path(root);mp=root/(prefix+'.manifest-a01.json');mb=mp.read_bytes();need(len(mb)<=262144,'Manifest cap')
 m=json.loads(mb);entries={e['member']:e for e in m['entries']};need(len(entries)==len(m['entries']),'Duplicate source member')
 segments=m['roles']['segments'];wanted={s['terminal_cash'] for s in segments};need(len(wanted)==len(segments)==2,'Exactly two held terminal windows required')
 ap=root/m['archive']['file'];ab=ap.read_bytes();need(len(ab)<=1048576 and fingerprint(ab)=={k:m['archive'][k] for k in ('bytes','sha256')},'Portable archive pin differs')
 outputs=[];read_bytes=0;prior_boarding=[];prior_ref=None
 if prefix=='R196-TREATMENT-EVIDENCE':
  name='PRODUCTION-PAIR-REPLAY.actual-a01.json';rp=root/name;rb=rp.read_bytes();index=json.loads((root/'index.json').read_bytes())
  expected=next(p for p in index['evidence_files'] if p['file']==name)
  need(len(rb)<=32768 and fingerprint(rb)=={k:expected[k] for k in ('bytes','sha256')},'Original prior production pair replay pin differs')
  prior=json.loads(rb);need(prior.get('run_id')==m['run_id'] and prior.get('producer_machine_id')==m['machine_id'] and prior.get('source_head')==m['source_head'],'Prior replay producer identity differs')
  prior_boarding=prior['pair_assessment']['selected_army_positive_sourcequalified_SUB_callbacks']
  prior_ref=dict(file=name,json_pointer='/pair_assessment/selected_army_positive_sourcequalified_SUB_callbacks',**fingerprint(rb))
 with zipfile.ZipFile(ap) as z:
  member=m['archive']['container_member'];need(z.getinfo(member).file_size==m['archive']['container_bytes']<=16*1024*1024,'Bounded no-Driver logical container required')
  with z.open(member) as stream:
   for e in sorted((entries[k] for k in wanted),key=lambda e:e['offset']):
    need(e['bytes']<=1048576,'Cash packet cap');stream.seek(e['offset']);raw=stream.read(e['bytes']);read_bytes+=len(raw)
    need(fingerprint(raw)=={k:e[k] for k in ('bytes','sha256')},'Selected exact original packet changed')
    packet=json.loads(raw);need(packet.get('machine_id')==m['machine_id'] and packet.get('is_error') is False,'Original relay error/identity')
    segment=next(s for s in segments if s['terminal_cash']==e['member'])
    source=dict(manifest=mp.name,archive=ap.name,member=e['member'],offset=e['offset'],**fingerprint(raw))
    outputs.append(project_journal(packet['body']['war_payment_observations_v1'],machine_id=m['machine_id'],run_id=m['run_id'],segment_id=segment['segment_id'],source=source,prior_boarding=prior_boarding,prior_boarding_ref=prior_ref))
 return dict(machine_id=m['machine_id'],source_head=m['source_head'],manifest=mp.name,manifest_pin=fingerprint(mb),archive_pin=fingerprint(ab),selected_original_bytes=read_bytes,outputs=outputs)

def consume_pair(control_root,treatment_root):
 arms=[read_arm(control_root,'R195-CONTROL-EVIDENCE'),read_arm(treatment_root,'R196-TREATMENT-EVIDENCE')]
 need(arms[0]['machine_id']==arms[1]['machine_id'],'Historical arms from different producer machines')
 records=[r for a in arms for o in a['outputs'] for r in o['records']]
 credits=[r for r in records if r['observer_kind']==2];groups={}
 for row in credits:
  key=(row['native_date_low32'],row['absolute_day_raw'],row['caller_return_rva'],row['subject_character_full_id'],row['amount_raw'])
  groups.setdefault(key,[]).append(row['run_id'])
 for arm in arms:
  for output in arm['outputs']:del output['records']
 return dict(schema='xar.war-payment-personal-callback-pair.v1',machine_id=arms[0]['machine_id'],observed_at_utc=datetime.now(timezone.utc).isoformat(),scope='Four frozen terminal journals from two historical32-day arms; retained callback endpoints only',arms=arms,records=records,summary=dict(personal_callbacks=len(records),personal_ADD=len(credits),personal_SUB=sum(r['observer_kind']==3 for r in records),excluded_known_boarding_SUB=sum(r['excluded_previously_qualified_boarding_300000'] for r in records),remaining_nonboarding_personal_SUB=sum(r['observer_kind']==3 and not r['excluded_previously_qualified_boarding_300000'] for r in records),retained_c_share_SUB_caller_28A6E05=sum(r['observer_kind']==3 and r['caller_return_rva']==0x28A6E05 for r in records),retained_d_share_SUB_caller_28A6EC2=sum(r['observer_kind']==3 and r['caller_return_rva']==0x28A6EC2 for r in records),cross_arm_same_date_credit_groups=[dict(native_date_low32=k[0],absolute_day_raw=k[1],caller_return_rva_hex=hex(k[2]),subject_full_id=k[3],amount_raw=k[4],runs=v) for k,v in groups.items() if len(set(v))>1],temporal_repeated_settlement_established=False,paid_military_amount_raw=None,payer=None,cadence=None,c_d_producer_store_rva=None,maintenance_attribution='unclosed'),limits=['ADD and SUB are distinct callback directions, not payment category names.','No retained nonboarding SUB is not absence of military expense or other payer/resource/store paths.','Same-date credit replicated across independent arms is not a repeated monthly/daily cadence.','Equal context endpoints do not prove no intermediate writes; unwind parent does not identify c/d producer.','No EXE, SDK, Driver/save body, live process, desktop or old test matrix was accessed.'])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control-root',type=Path,required=True);p.add_argument('--treatment-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 row=consume_pair(a.control_root,a.treatment_root)
 with a.output.open('x',encoding='utf8',newline='\n') as f:json.dump(row,f,separators=(',',':'));f.write('\n')
 print(json.dumps(row['summary'],separators=(',',':')))
if __name__=='__main__':main()
