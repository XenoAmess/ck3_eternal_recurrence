"""Plan or freeze pinned Episode04 text increments; no provider or media execution."""
from pathlib import Path
import argparse
import hashlib
import json
import re

SCHEMA='ck3.e04.final-BC-oral-request.v1'
SCRIPT_INPUTS=('final_C_terminal_source','final_chinese_body','final_claim_ledger','source_review')
def need(value,message):
    if not value: raise ValueError(message)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def write_new(path,obj):
    raw=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream: stream.write(raw)
def read_pin(pin,request_dir):
    need(isinstance(pin,dict) and set(pin)=={'path','bytes','sha256'},'pin must have exact path/bytes/sha256 keys')
    need(isinstance(pin['path'],str) and pin['path'] and type(pin['bytes']) is int and pin['bytes']>=0,'invalid pin path/bytes')
    need(re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None,'invalid lowercase SHA256')
    path=Path(pin['path'])
    if not path.is_absolute(): path=request_dir/path
    raw=path.read_bytes()
    need(len(raw)==pin['bytes'] and digest(raw)==pin['sha256'],'pin bytes/hash mismatch: '+pin['path'])
    return raw
def paragraphs(raw):
    rows=re.findall(r'^\[(C\d\d-\d\d)\] (.+)$',raw.decode('utf-8-sig'),re.M)
    expected=[f'C{chapter:02d}-{part:02d}' for chapter,count in enumerate((8,12,12,11,16,10),1) for part in range(1,count+1)]
    need([key for key,_ in rows]==expected,'final body must preserve exactly69 ordered unique paragraph IDs')
    return dict(rows)
def load_request(path):
    obj=json.loads(path.read_bytes())
    need(obj.get('schema')==SCHEMA,'unknown request schema')
    need(obj['final_audio_clock'] is None and obj['final_video_duration'] is None,'script stage cannot invent final audio/video clock')
    need(obj['ABC_winner'] is None,'this source cut does not grant a controlled winner')
    need(obj['C_controlled_comparison_eligibility']=='NOT_GRANTED','C sampling deviation cannot be relabelled controlled')
    root_sampling_requirements(obj,path)
    current_Main_subject_scope(obj,path)
    return obj
def root_sampling_requirements(request,path):
    pin=request.get('current_C_Root_basis_source')
    need(pin is not None,'latest actual Root sampling receipt is required')
    raw=read_pin(pin,path.parent)
    receipt=json.loads(raw)
    need(receipt.get('start_raw')==53148432 and receipt.get('absolute_end_raw')==53150592,'Root sampling receipt changed original T0/END')
    need(receipt.get('descriptive_continuation_only') is True and receipt.get('controlled_comparison_eligibility_granted') is False,'Root receipt does not preserve descriptive-only boundary')
    need(receipt.get('old_STOP_unchanged') is True and receipt.get('no_budget_reset') is True,'Root receipt changed STOP or budget')
    source_rows=receipt.get('sampling_protocol_deviations')
    need(isinstance(source_rows,list) and bool(source_rows),'Root receipt has no actual deviation list')
    windows=[]
    for row in source_rows:
        need(isinstance(row,dict),'Root sampling row malformed')
        actual=row.get('actual_days')
        need(type(actual) is int and actual>1 and type(row.get('planned_max_target_days')) is int and row['planned_max_target_days']==1,'Root actual/planned sampling policy malformed')
        after=row.get('source_after_raw',row.get('actual_date_raw'))
        need(type(after) is int,'Root sampling row has no actual end date')
        before=row.get('source_before_raw',after-actual*24)
        need(type(before) is int and after-before==actual*24 and before>=53148432,'Root actual sampling dates mismatch')
        need((before-53148432)%24==0 and (after-53148432)%24==0,'Root sampling date not on source day basis')
        need(row.get('window_one_day_sampling_eligible') is False and row.get('arm_controlled_comparison_eligibility_not_granted') is True,'Root deviation relabelled eligible/controlled')
        windows.append([(before-53148432)//24,(after-53148432)//24])
    need(len({tuple(row) for row in windows})==len(windows),'Root receipt repeats a sampling window')
    return windows,digest(raw)
def validate_sampling_deviations(deviations,request,path):
    need(isinstance(deviations,list),'sampling deviations must be an explicit list')
    windows,_=root_sampling_requirements(request,path)
    required={tuple(row) for row in windows}
    observed=set()
    for row in deviations:
        need(isinstance(row,dict),'sampling deviation row malformed')
        window=row.get('observed_days')
        need(isinstance(window,list) and len(window)==2 and all(type(day) is int for day in window),'sampling window malformed')
        pair=tuple(window)
        need(pair not in observed,'duplicate sampling window')
        observed.add(pair)
        need(type(row.get('planned_max_days')) is int and row['planned_max_days']==1,'planned one-day policy relabelled')
        need(type(row.get('actual_days')) is int and row['actual_days']==window[1]-window[0] and row['actual_days']>1 and row.get('one_day_eligible') is False,'sampling deviation relabelled')
        need(row.get('source_pin') is not None,'final sampling deviation must have an actual source pin')
        read_pin(row['source_pin'],path.parent)
    need(observed==required,'final deviations do not match latest pinned Root receipt; update the receipt for any later deviations')
def current_Main_subject_scope(request,path):
    root=json.loads(read_pin(request['current_C_Root_basis_source'],path.parent))
    linked=root.get('Root_scope_addendum')
    scope_pin=request.get('current_C_Main_scope_source')
    if linked is None:
        need(scope_pin is None,'Main scope cannot be invented without an actual Root-linked addendum')
        return None,None
    need(scope_pin is not None,'Root Mainpartial scope requires its exact linked source pin')
    need(scope_pin['bytes']==linked['bytes'] and scope_pin['sha256']==linked['sha256'],'Main scope pin is not the exact actual Root-linked source')
    raw=read_pin(scope_pin,path.parent)
    scope=json.loads(raw)
    need(scope.get('schema')=='ck3.e04.abc.required-cohort-scope/v1','unknown actual Main scope schema')
    need(scope.get('episode_run_id')==root['episode_run_id'] and scope.get('start_raw')==53148432 and scope.get('absolute_end_raw')==53150592,'Main scope changed episode/T0/END')
    need(scope.get('actual_new_scope_granted') is True and scope.get('required_Main_rows_available') is True,'actual Main scope was not granted/available')
    need(scope.get('full_native_snapshots_and_roster_preserved_without_projection') is True and scope.get('no_unknown_value_coerced_to_zero_or_transport') is True,'scope lost full provenance or coerced unknown health')
    need(scope.get('comparison_controlled_eligibility')=='NOT_GRANTED_DESCRIPTIVE_ONLY','Main scope cannot restore controlled comparison')
    need(scope.get('required_public_ids')==[0] and scope.get('required_native_carmy_ids')==[0] and scope.get('required_commander_character_ids')==[27357],'Main scope changed required original identity/commander')
    need(scope.get('required_full_regiments')==27 and scope.get('required_full_DATA')==37,'Main scope changed original cohort counts')
    unknown=scope.get('unassessed_current_CUnit_ids')
    need(isinstance(unknown,list) and all(type(item) is int and item>=0 for item in unknown) and len(set(unknown))==len(unknown),'unassessed IDs malformed')
    need(scope.get('excluded_health') is None,'unassessed health must remain explicit NULL')
    need(isinstance(scope.get('actual_global_scope_status_preserved'),str),'global health scope missing')
    descriptor={'kind':'required_Main_original_cohort','required_public_ids':[0],'required_native_carmy_ids':[0],
      'required_full_regiments':27,'required_full_DATA':37,
      'global_health_status':scope['actual_global_scope_status_preserved'],
      'unassessed_CUnit_ids':unknown,'unassessed_health':None,'all_player_total_soldiers':None}
    return descriptor,digest(raw)
def validate_Main_subject_binding(C,ledger,review,request,path):
    descriptor,sha=current_Main_subject_scope(request,path)
    if descriptor is None:return
    need(C.get('subject_scope')==descriptor,'normalized C must describe Main original cohort, not all-player total/complete health')
    need(review.get('C_subject_scope')==descriptor and review.get('C_Main_scope_source_sha256')==sha,'source review must bind exact actual Mainpartial scope')
    need(ledger.get('C_subject_scope')==descriptor and ledger.get('C_Main_scope_source_sha256')==sha,'ledger must preserve exact Mainpartial subject and unknowns')
def plan(request,path):
    base=paragraphs(read_pin(request['baseline_A_body'],path.parent))
    current=paragraphs(read_pin(request['preserved_B_candidate_body'],path.parent))
    candidates=[key for key in base if base[key]!=current[key]]
    draft=paragraphs(read_pin(request['current_partial_draft_body'],path.parent))
    draft_ids=[key for key in base if base[key]!=draft[key]]
    reuse=json.loads(read_pin(request['C05_01_reuse_proof'],path.parent))
    need(reuse['text_zh']==base['C05-01']==current['C05-01'],'C05-01 current text differs from proven original audio')
    need(digest(base['C05-01'].encode('utf-8'))==reuse['text_sha256'],'C05-01 text hash differs')
    need(reuse['actual_PCM_samples']==527040 and reuse['actual_seconds']==21.96,'original C05-01 PCM proof differs')
    required_windows,sampling_sha=root_sampling_requirements(request,path)
    Main_scope,Main_scope_sha=current_Main_subject_scope(request,path)
    missing=[key for key in SCRIPT_INPUTS if request['future'][key] is None]
    return {'schema':'ck3.e04.final-BC-oral-plan.v1','status':'PENDING_ACTUAL_C_AND_SOURCE_REVIEW' if missing else 'INPUTS_PRESENT_NOT_YET_REVIEWED',
      'B_candidate_changed_ids_vs_actual_A':candidates,
      'current_partial_draft_changed_ids_vs_A':draft_ids,
      'C05_01_audio_change_current':False,'C05_01_picture_refresh':True,
      'current_C_subject_scope':Main_scope,'current_C_Main_scope_source_sha256':Main_scope_sha,
      'possible_C_sentence_slots':['C05-05','C05-14','C05-16','C06-10'],
      'final_audio_changed_ids':None,'final_subtitle_changed_ids':None,
      'required_sampling_deviation_windows':required_windows,
      'required_sampling_Root_receipt_sha256':sampling_sha,
      'missing_script_inputs':missing,'C_endpoint':None,'final_audio_clock':None,'ABC_winner':None,
      'TTS_media_SDK_UI_Game_process_control_Git_calls':0,'human_signoff':False}
def validate_freeze(request,path):
    base=paragraphs(read_pin(request['baseline_A_body'],path.parent))
    need(all(request['future'][key] is not None for key in SCRIPT_INPUTS),'actual final C/body/ledger/NO_BLOCK source review are not all supplied')
    raw={key:read_pin(request['future'][key],path.parent) for key in SCRIPT_INPUTS}
    body=paragraphs(raw['final_chinese_body'])
    ledger=json.loads(raw['final_claim_ledger'])
    review=json.loads(raw['source_review'])
    C=request['future']['normalized_C_result']
    need(isinstance(C,dict) and C.get('closed') is True,'C has no actual closed result')
    need(C.get('controlled_comparison_eligibility')=='NOT_GRANTED','C controlled eligibility cannot be restored by continuation')
    need(C.get('winner') is None and C.get('applied_refill_payment_ledger') is None,'unproved winner/applied ledger')
    required_C=('status','source_sha256','episode_run_id','common_T0_raw','absolute_END_raw','observed_terminal_date_raw',
                'actual_days_used','sampling_deviations','London_endpoint_metrics','observed_arrival_interval_days')
    need(all(key in C for key in required_C),'normalized C result must explicitly include required nullable fields')
    need(C['source_sha256']==digest(raw['final_C_terminal_source']),'normalized C source is not pinned to actual terminal')
    need(C['common_T0_raw']==53148432 and C['absolute_END_raw']==53150592,'original absolute budget changed')
    need(type(C['observed_terminal_date_raw']) is int and C['observed_terminal_date_raw']>=53148432,'terminal date unknown/before original start')
    need(type(C.get('global_budget_breach')) is bool,'terminal must explicitly record any global budget breach')
    need(C['global_budget_breach']==(C['observed_terminal_date_raw']>53150592),'actual budget breach/date mismatch; original END must remain unchanged')
    need((C['observed_terminal_date_raw']-53148432)/24==C['actual_days_used'],'terminal elapsed date mismatch')
    validate_sampling_deviations(C['sampling_deviations'],request,path)
    validate_Main_subject_binding(C,ledger,review,request,path)
    changed=[key for key in base if base[key]!=body[key]]
    need(review.get('source_review_status')=='NO_BLOCK' and review.get('final_freeze') is True,'final source-semantic review is not NO_BLOCK/frozen')
    need(review.get('changed_paragraph_ids')==changed,'review changed IDs do not match actual Chinese text')
    need(review.get('chinese_body_sha256')==digest(raw['final_chinese_body']) and review.get('chinese_ledger_sha256')==digest(raw['final_claim_ledger']),'review body/ledger hash mismatch')
    need(review.get('C_terminal_source_sha256')==digest(raw['final_C_terminal_source']),'review C source hash mismatch')
    _,sampling_sha=root_sampling_requirements(request,path)
    need(review.get('C_sampling_Root_receipt_sha256')==sampling_sha,'final semantic review must bind the latest exact Root sampling receipt')
    need(review.get('ABC_winner') is None and 'ABC_results' in review,'final result/winner must be explicit and nullable')
    need(review.get('C_controlled_comparison_eligibility')=='NOT_GRANTED','source review grants unsupported C comparison')
    claims=ledger.get('claims')
    need(isinstance(claims,list) and len(claims)==69,'final authoritative ledger must retain69 claims')
    claim_by_id={row['id']:row for row in claims}
    need(set(claim_by_id)==set(body),'ledger claim identities differ')
    for key in changed:
        claim=claim_by_id[key]
        text=claim.get('claim_summary',claim.get('new_text_zh'))
        need(text==body[key] and bool(claim.get('source_keys')),'changed claim text/source binding missing: '+key)
    need(ledger.get('ABC_winner') is None,'ledger must not imply controlled winner')
    output={'schema':'ck3.e04.final-BC-script-freeze-validation.v1','status':'PASS_PINNED_FINAL_SOURCE_TEXT_REVIEW',
      'audio_changed_ids':changed,'exact_reused_Chinese_ids':[key for key in base if key not in changed],
      'picture_refresh_ids':sorted(set(request['picture_refresh_ids'])|set(changed)),
      'C05_01_audio_changed':'C05-01' in changed,'paragraphs':69,
      'affected_audio_chapters':sorted({'E4-'+key[1:3] for key in changed}),
      'ABC_results':review['ABC_results'],'ABC_winner':None,
      'C_controlled_comparison_eligibility':'NOT_GRANTED','actual_final_audio_clock':None,
      'final_subtitle_changed_ids':None,'new_TTS_requests':0,'human_signoff':False}
    return output,raw
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('plan','validate-freeze','freeze'))
    parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--output-dir',type=Path)
    args=parser.parse_args()
    try:
        request=load_request(args.request)
        if args.command=='plan':
            need(args.output is not None,'plan needs new --output')
            result=plan(request,args.request)
            write_new(args.output,result)
        else:
            result,raw=validate_freeze(request,args.request)
            if args.command=='validate-freeze':
                need(args.output is not None,'validate-freeze needs new --output')
                write_new(args.output,result)
            else:
                need(args.output_dir is not None,'freeze needs new --output-dir')
                args.output_dir.mkdir(parents=True,exist_ok=False)
                write_new(args.output_dir/'request-snapshot.json',args.request.read_bytes())
                for key,value in raw.items():
                    write_new(args.output_dir/(key+('.md' if key=='final_chinese_body' else '.json')),value)
                write_new(args.output_dir/'AUDIO-DIFF-AND-REUSE.json',result)
        print(json.dumps(result,ensure_ascii=False))
    except ValueError as error:
        if args.output is not None and not args.output.exists():
            write_new(args.output,{'status':'NOT_READY_OR_SOURCE_CONTRACT_REJECTED','reason':str(error),'new_TTS_requests':0})
        print(json.dumps({'status':'NOT_READY_OR_SOURCE_CONTRACT_REJECTED','reason':str(error)},ensure_ascii=False))
        raise SystemExit(2)
if __name__=='__main__': main()
