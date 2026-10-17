"""Execute an explicitly admitted, source-bound motion batch once. No TTS/game.

The caller supplies this round's exact official-latest qualification and fresh
shared storage authorization. A failed child is preserved and never replayed.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['plan','plan-sha256','output','repo','package-root','ledger','allocation-reader','qualification','qualification-sha256','machine','ffmpeg','ffprobe','font']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--peak-bytes',type=int,required=True)
    p.add_argument('--workers',type=int,choices=[1,2],default=2)
    a=p.parse_args();folder=Path(__file__).resolve().parent
    sys.path.insert(0,str(folder));sys.path.insert(0,a.package_root)
    sys.path.insert(0,str(Path(a.repo)/'promo/ck3_faith_and_power/integration/src'))
    from faith_power_promo.mechanism_motion import pin,read,write,build
    from faith_power_promo import mechanism_motion
    from faith_power_promo.storage_carry_v3 import admit_v3
    now=lambda:datetime.now(timezone.utc).isoformat()
    if pin(a.plan)['sha256']!=a.plan_sha256:raise ValueError('Exact root-reviewed batch plan required')
    plan=read(a.plan);out=Path(a.output).resolve()
    if out.exists():raise ValueError('Write-once batch output exists; no automatic resume or retry')
    if (plan['machine_id']!=a.machine or pin(mechanism_motion.__file__)!=plan['producer']
        or plan['full_batch_render_admitted'] is not False or a.peak_bytes<plan['proposed_total_peak_bytes']):
        raise ValueError('Same-machine reviewed producer/plan and full conservative peak required')
    if pin(a.qualification)['sha256']!=a.qualification_sha256:raise ValueError('Exact same-round latest-final qualification required')
    for row in plan['rows']:
        if pin(row['spec']['path'])!=row['spec']:raise ValueError('Reviewed cue specification changed')
    admission_args={'repo':Path(a.repo),'ledger_path':Path(a.ledger),'package_root':Path(a.package_root),'output':out,
        'machine':a.machine,'allocation_reader':Path(a.allocation_reader)}
    admission=admit_v3(**admission_args,peak=a.peak_bytes)
    out.mkdir(parents=True);write(out/'storage-admission-v3.json',admission)
    start={'schema':'ck3-faith-power-source-motion-batch-attempt-v1','machine_id':a.machine,'started_at_utc':now(),
        'plan':pin(a.plan),'producer':pin(mechanism_motion.__file__),'driver':pin(__file__),
        'qualification':pin(a.qualification),'peak_new_bytes':a.peak_bytes,'workers':a.workers,
        'source_readbacks_rechecked_by_each_clip':True,'auto_retry':False,'TTS_requested':False,'game_or_screen_access':False}
    write(out/'BATCH-START.json',start)
    def one(row):
        output=out/row['cue_id']
        receipt=build(row['spec']['path'],output,repo=a.repo,package_root=a.package_root,ledger=a.ledger,
            allocation_reader=a.allocation_reader,qualification=a.qualification,qualification_sha256=a.qualification_sha256,
            machine=a.machine,ffmpeg=a.ffmpeg,ffprobe=a.ffprobe,font=a.font,peak_bytes=16*1024**2)
        receipt_pin=pin(output/'source-motion-v1.json')
        part={'kind':'mechanism-motion','video':receipt['video'],'source_motion_receipt':receipt_pin,
            'source_start_seconds':0,'duration_seconds':receipt['frames']['duration_seconds'],
            'disclosure':receipt['permanent_disclosure']+' · '+row['proof_label'],'live_result_depicted':False,
            'claim_ids':receipt['claim_ids'],'source_ref_ids':receipt['source_ref_ids']}
        result={'cue_id':row['cue_id'],'part':part,'receipt':receipt_pin,'full_decode_exit_code':receipt['full_decode_exit_code'],
            'actual_frames':receipt['frames'],'status':'ACTUAL_SOURCE_MOTION_RENDERED_UNREVIEWED_AT_1X'}
        print(json.dumps({'cue_id':row['cue_id'],'seconds':part['duration_seconds'],'bytes':part['video']['bytes'],'status':result['status']}),flush=True)
        return result
    done={};failures=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures={pool.submit(one,row):row for row in plan['rows']}
        for future in as_completed(futures):
            row=futures[future]
            try:done[row['cue_id']]=future.result()
            except BaseException as exc:
                failures.append({'cue_id':row['cue_id'],'exception_type':type(exc).__name__,'message':str(exc),'unknown_action_retried':False})
                for pending in futures:pending.cancel()
    closed=admit_v3(**admission_args,peak=1);write(out/'storage-close-v3.json',closed)
    ordered=[done[row['cue_id']] for row in plan['rows'] if row['cue_id'] in done]
    result={'schema':'ck3-faith-power-source-motion-batch-result-v1','machine_id':a.machine,'observed_at_utc':now(),
        'evidence_source':'Actual bounded source-only clip renders, exact local source rechecks, full decode and per-frame CFR PTS',
        'started':pin(out/'BATCH-START.json'),'plan':pin(a.plan),'producer':pin(mechanism_motion.__file__),'driver':pin(__file__),
        'rendered_count':len(ordered),'expected_count':len(plan['rows']),'complete':not failures and len(ordered)==len(plan['rows']),
        'failures':failures,'cues':ordered,'seconds':sum(c['part']['duration_seconds'] for c in ordered),
        'actual_video_bytes':sum(c['part']['video']['bytes'] for c in ordered),'actual_new_frames':sum(c['actual_frames']['count'] for c in ordered),
        'storage_admission':pin(out/'storage-admission-v3.json'),'storage_close':pin(out/'storage-close-v3.json'),
        'actual_live_results_depicted':False,'new_TTS_requests':0,'raw_gameplay_copied_or_looped':False,'human_1x_signoff':False}
    write(out/'BATCH-RESULT.json',result)
    print(json.dumps({'result':pin(out/'BATCH-RESULT.json'),'complete':result['complete'],'rendered_count':len(ordered),'seconds':result['seconds'],'actual_video_bytes':result['actual_video_bytes']}),flush=True)
    return 0 if result['complete'] else 1

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');raise SystemExit(main())
