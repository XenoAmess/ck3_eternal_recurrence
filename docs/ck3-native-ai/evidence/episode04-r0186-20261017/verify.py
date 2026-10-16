"""Verify R186's selective portable evidence; never contact a game or SDK."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

BUNDLE=Path(__file__).resolve().parent

def need(ok,message):
    if not ok:
        raise ValueError(message)

def sha(body):
    return hashlib.sha256(body).hexdigest()

def read_json(name):
    return json.loads((BUNDLE/name).read_text(encoding='utf-8-sig'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-git-source',action='store_true')
    parser.add_argument('--repo',type=Path,default=BUNDLE.parents[3])
    parser.add_argument('--external-sources',action='store_true')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    index=read_json('source-index.json')
    for row in index['original_files']+index['exact_subtree_files']+index['generated_files']:
        p=(BUNDLE/row['relative_path']).resolve()
        need(p.is_relative_to(BUNDLE),'evidence path escaped bundle')
        body=p.read_bytes()
        need(len(body)==row['bytes'] and sha(body)==row['sha256'],'bytes/SHA mismatch: '+row['relative_path'])
    git_checks=0
    if args.verify_git_source:
        for row in index['runtime_git_source_pins']:
            body=subprocess.check_output(['git','show',row['commit']+':'+row['repo_path']],cwd=args.repo)
            need(len(body)==row['bytes'] and sha(body)==row['sha256'],'runtime Git source pin mismatch')
            need(f'{zlib.crc32(body)&0xffffffff:08x}'==row['crc32_hex'],'runtime source CRC mismatch')
            git_checks+=1
    facts=read_json('portable-facts.actual-a01.json')
    need(facts['native_completed_days']==14 and facts['requested_days']==28,'day plan/count mismatch')
    need(facts['initial_date_raw']==53148432 and facts['last_completed_date_raw']==53148768,'completed date mismatch')
    need(facts['day15_modal_arrival']['date_raw']==53148792 and not facts['day15_modal_arrival']['counted_as_completed_day'],'modal day was promoted')
    need(facts['video']['decoded_timeline']['frames']==1101 and facts['video']['container_duration_seconds']==36.7,'media frame/time mismatch')
    need(facts['full_AV_decode_exit']==0 and facts['full_AV_decode_diagnostic']=='' and not facts['premature_end_reported'],'media integrity mismatch')
    need(not facts['min_wall_100_met'] and not facts['encoded_frame_end_100_seconds_met'],'minimum-duration failure was changed')
    need(not any(facts['claims'].values()),'qualification promoted')
    for day in range(1,15):
        d=read_json(f'd{day:02d}-complete.actual.json')
        need(d['date_raw']==53148432+24*day,'wrong actual completed day')
        need(d['sentinel']['completed_daily_ticks']==1 and d['sentinel']['overshoot_days']==0 and d['sentinel']['pause_observed'],'daily sentinel contract mismatch')
    result=read_json('film-result.actual.json')
    need(result['completed_days']==14 and result['recorder_ready_to_resume_ack_seconds']==3.8324387,'R186 result/handoff mismatch')
    payment=read_json('r186-payment-after-a01.response.json')['body']
    pw=payment['war_payment_observations_v1']
    need(pw['sampling']['retained_records']==4 and pw['sampling']['qualified_records']==0 and len(pw['natural_parent_returns'])==30,'payment counts mismatch')
    need([x['before']['army_id'] for x in pw['records']]==[188,33,202,212],'callback caller identity mismatch')
    need(pw['overwritten']==0 and pw['natural_journal_status']['overwritten_records']==0 and not pw['qualified_boarding_debits'],'payment coverage/qualification mismatch')
    values=payment['current_raw_context_v1']['values']
    need(all(values[key]==0 for key in ['value_2c0','value_2c8','value_28','value_30']),'current raw context mismatch')
    parents=read_json('natural-army_natural_phase_observations_v1.exact.json')
    need(parents['subject_full_carmy_id_u32']==18 and len(parents['records'])==30,'natural parent scope mismatch')
    posts=[x for x in parents['records'] if x['scope']['phase']=='post_date']
    need(len(posts)==15 and all(x['scope']['saved_mask02_admitted'] is False for x in posts),'post-date admission mismatch')
    loss=read_json('natural-actual_loss_writer_observations_v1.exact.json')
    need(loss['event_count']==0 and loss['overwritten_events']==3238 and loss['oldest_available_sequence']==3239 and loss['latest_sequence']==3750,'loss coverage boundary changed')
    supply=read_json('natural-actual_supply_callback_observations_v1.exact.json')
    need(supply['event_count']==0 and supply['overwritten_events']==0,'supply boundary changed')
    r06=read_json('r06/ACTUAL-ANALYSIS.json')
    for w in r06['candidate_widgets']:
        full=w['full_candidate'];local=full['local_definition_entry_only'];entry=local['entries'][0]
        need(full['unavailable_reason']=='candidate_parent_depth_exhausted' and full['failure_diagnostic']['ancestor_depth']==8,'full R06 boundary changed')
        need(local['status']=='available' and local['stable_double_read'] and entry['entry_mode_40']==0 and entry['entry_flag_4c']==0,'local R06 observation mismatch')
        need(not entry['direct_value_present'] and not entry['provider_present'] and entry['provider_slot2_rva'] is None and not full['native_receiver_selected'],'provider/native receiver invented')
    event=read_json('event02-context.response.json')['body']
    need(event['event_definition_key']=='pam_bull_events.0004' and event['current_event_instance_id']==2,'event identity mismatch')
    need(event['options'][0]['rendered_index']==0 and event['options'][0]['native_option_index']==0 and event['options'][0]['resolved_name']=='就这样吧。','first displayed option mismatch')
    selection=read_json('event02-select-first-once.response.json')['body']['event_selection']
    need(selection['postcondition_verified'] and selection['old_event_instance_id']==2 and selection['new_event_instance_id'] is None and selection['selected_option_number']==1,'event postcondition mismatch')
    observations=read_json('observations.actual.json')
    need(observations['event_after']['active_event'] is None and not any(observations['claims'].values()),'independent after-state or claims changed')
    external_checks=0
    if args.external_sources:
        cache={}
        for row in index['exact_subtree_files']:
            ref=row['source_ref'];path=ref['path']
            if path not in cache:
                body=Path(path).read_bytes();need(len(body)==ref['bytes'] and sha(body)==ref['sha256'],'external Driver reference mismatch');cache[path]=body
            need(cache[path][row['source_byte_start']:row['source_byte_end_exclusive']]==(BUNDLE/row['relative_path']).read_bytes(),'exact Driver subtree offset mismatch')
            external_checks+=1
        ref=r06['source_response'];body=Path(ref['path']).read_bytes()
        need(len(body)==ref['bytes'] and sha(body)==ref['sha256'],'external R06 response pin mismatch')
        for row in r06['exact_raw_subtree_spans']:
            need(body[row['original_byte_start']:row['original_byte_end_exclusive']]==(BUNDLE/'r06'/row['file']).read_bytes(),'exact R06 subtree offset mismatch')
            external_checks+=1
    size=sum(p.stat().st_size for p in BUNDLE.rglob('*') if p.is_file())
    need(size<=1048576,'1MiB evidence ceiling exceeded')
    need(not any(p.suffix.lower() in ['.mkv','.png','.ck3','.dll','.exe'] for p in BUNDLE.rglob('*') if p.is_file()),'large asset copied')
    report={'schema':'xar.e04.r186.portable-verification.v1','machine_id':index['machine_id'],'status':'PASS_SELECTED_BYTES_AND_SEMANTICS_ONLY','checked_originals':len(index['original_files']),'checked_exact_subtrees':len(index['exact_subtree_files']),'checked_generated_records':len(index['generated_files']),'checked_Git_SHA_CRC_pins':git_checks,'checked_external_offsets':external_checks,'checked_exact_days':14,'bundle_bytes':size,'full_portable_closure_claimed':False,'new_live_actions':0,'business_or_clean_or_signoff_granted':False}
    if args.report:
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    main()
