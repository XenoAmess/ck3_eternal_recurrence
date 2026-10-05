"""Bounded encoded candidates from already audited closed media; no probe/hash of raw."""
import bisect, concurrent.futures, hashlib, json, re, subprocess, sys, time
from datetime import datetime,timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from PIL import Image

R=Path('C:/ck3-war-episode04-research-20261004-a01');O=R/'e4-shot-usability-r0177-parallel-a01'
EXPECTED=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def pin(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(p,v):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def bound(b):
    assert pin(b['path'])=={**b,'path':str(Path(b['path']).resolve())},'saved small input pin changed'
    return Path(b['path'])
PLAN=[
 {'run':'R0164','report':'recording-audit-r0164-a01/audit-attempt-a01/report.json','selections':[
  {'role':'supply_before_search','search_seconds':'873','packets':['native-live-positive-r0164-a01/responses/r0164-land-p05-012-001-health.json']},
  {'role':'supply_after_search','search_seconds':'899','packets':['native-live-positive-r0164-a01/responses/r0164-land-p05-018-002-health.json']} ]},
 {'run':'R0165','report':'recording-audit-r0165-a01/audit-attempt-a01/report.json','selections':[
  {'role':'integer_refill_before_search','search_seconds':'1140','packets':['root-pulse-r0165/r0165-p03/004.sample.json']},
  {'role':'integer_refill_after_search','search_seconds':'1180','packets':['root-pulse-r0165/r0165-p03/005.sample.json']} ]},
 {'run':'R0168','report':'r0168-capture-next-a01/audit-attempt-a01/report.json','selections':[
  {'role':'weighted_merge_transition_search','search_seconds':'3494.9','packets':['actual-merge-review-r0168-a01/ROOT-DELIVERY-a02.json']} ]},
 {'run':'R0171','report':'r0171-media-tools-a01/audit-attempt-a01/report.json','selections':[
  {'role':'halt_before_search','search_seconds':'882','packets':['native-live-r0171-a01/responses/r0171-halt-before-a01.json']},
  {'role':'halt_after_search','search_seconds':'898','packets':['native-live-r0171-a01/responses/r0171-halt-command-a01.json','native-live-r0171-a01/responses/r0171-halt-after-a01.json']} ]},
 {'run':'R0172','report':'r0172-media-tools-a01/audit-attempt-a01/report.json','selections':[
  {'role':'loss67_before_search','search_seconds':'401','packets':['native-live-r0172-a01/responses/root-r0172-batch01-a01-i08-inspect-strength.json']},
  {'role':'loss67_after_search','search_seconds':'421','packets':['native-live-r0172-a01/responses/root-r0172-batch01-a01-i09-inspect-strength.json']} ]},
]
def prepare(item):
    rp=R/item['report'];report=load(rp);assert report['state']=='PASS' and not report['errors']
    finish=load(bound(report['finish_receipt_identity']));fb=finish['body']
    assert not finish['is_error'] and fb['state']=='NORMAL_TREE_EMPTY' and fb['job']['returncode']==0 and fb['job']['job_active_processes']==0
    raw=Path(report['source_identity']['path']);assert raw.resolve()==(R/'r0177-raw-abc-a2-a01/raw.mkv').resolve(), 'Only the exact sealed first A2 tape is allowed'
    assert {**fb['raw'],'path':str(Path(fb['raw']['path']))}=={**report['source_identity'],'path':str(raw)}
    tablepin=report['probe_receipts']['video-frames']['stdout_identity'];frames=load(bound(tablepin))['frames'];assert len(frames)==report['decoded_frames']
    packetpin=report['probe_receipts']['video-packets']['stdout_identity'];packets=load(bound(packetpin))['packets']
    stream=report['video_stream'];tb=Fraction(stream['time_base']);assert tb==Fraction(1,1000)
    pts=[int(x['pts']) for x in frames];assert all(a<b for a,b in zip(pts,pts[1:]))
    packetbypts={int(x['pts']):x for x in packets}
    selected=[]
    for s in item['selections']:
        target=Decimal(s['search_seconds'])/Decimal(tb.numerator)*Decimal(tb.denominator)
        pos=bisect.bisect_left(pts,target);near=[i for i in (pos-1,pos) if 0<=i<len(pts)];idx=min(near,key=lambda i:abs(Decimal(pts[i])-target))
        assert pts[idx] in packetbypts
        selected.append({**s,'packet_pins':[pin(R/p) for p in s['packets']],
           'decoded_frame_index_zero_based':idx,'actual_pts':pts[idx],'time_base':str(tb),
           'actual_seconds':str(Decimal(pts[idx])*Decimal(tb.numerator)/Decimal(tb.denominator)),
           'saved_complete_frame_record':frames[idx],'saved_complete_packet_record':packetbypts[pts[idx]],
           'exact_native_event_frame_synchronization':False,'source_clock_labels_search_only':True,
           'root_direct_content_review':'PENDING','clean_span_certified':False})
    ffpin=report.get('strict_full_decode',{}).get('ffmpeg_identity')
    if ffpin is None:
        # R0164 prior audit had full frame decoding but no separate strict-decode producer.
        ffpin=load(R/'r0172-media-tools-a01/audit-attempt-a01/report.json')['strict_full_decode']['ffmpeg_identity']
    return {'run':item['run'],'audit':pin(rp),'finish':report['finish_receipt_identity'],'raw_prior_identity':report['source_identity'],
        'raw':raw,'source_after_audit':report['source_identity_after_audit'],'frame_table':tablepin,'packet_table':packetpin,
        'selections':selected,'ffmpeg_prior_identity':ffpin,'prior_strict_decode_available':bool(report.get('strict_full_decode'))}
def extract(job):
    out=O/'encoded-candidates-a01'/job['run'].lower();out.mkdir(parents=True,exist_ok=False)
    raw=job['raw'];before=raw.stat();assert before.st_size==job['raw_prior_identity']['bytes']
    oldmtime=job['source_after_audit'].get('mtime_ns')
    if oldmtime is not None:assert before.st_mtime_ns==oldmtime,'saved audited mtime changed'
    sels=sorted(job['selections'],key=lambda x:x['actual_pts']);targetpts=[x['actual_pts'] for x in sels]
    seek=max(Decimal(sels[0]['actual_seconds'])-Decimal(3),Decimal(0))
    # copyts retains the real input clock after bounded seek. showinfo is required to
    # verify every output against the complete saved decoded-frame and packet tables.
    filt='select='+ '+'.join('eq(pts\\,'+str(v)+')' for v in targetpts)+',showinfo'
    ff=Path(job['ffmpeg_prior_identity']['path']);assert ff.exists() and ff.stat().st_size==job['ffmpeg_prior_identity']['bytes']
    argv=[str(ff),'-hide_banner','-nostdin','-loglevel','info','-xerror','-copyts','-threads','2','-err_detect','explode',
      '-ss',str(seek),'-i',str(raw),'-map','0:v:0','-an','-filter_threads','1','-vf',filt,
      '-fps_mode','passthrough','-start_number','0','-frames:v',str(len(sels)),'-n',str(out/'candidate-%02d.png')]
    write(out/'argv.json',{'argv':argv,'global_selected_frame_indices':[x['decoded_frame_index_zero_based'] for x in sels],
       'global_actual_pts':targetpts,'bounded_seek_seconds':str(seek),'seek_not_event_sync':True,'raw_sha_repeated':False,'full_probe_repeated':False})
    started=time.monotonic_ns()
    with (out/'stdout.bin').open('xb') as stdout,(out/'stderr.bin').open('xb') as stderr:
        proc=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False)
    text=(out/'stderr.bin').read_text(encoding='utf-8',errors='replace')
    observed=[int(m.group(1)) for m in re.finditer(r'\[Parsed_showinfo_\d+[^\]]*\].*?\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:',text)]
    receipt={'returncode':proc.returncode,'elapsed_seconds':(time.monotonic_ns()-started)/1e9,'showinfo_actual_pts':observed,
       'argv':pin(out/'argv.json'),'stdout':pin(out/'stdout.bin'),'stderr':pin(out/'stderr.bin'),'all_partials_retained':True}
    write(out/'extraction-receipt.json',receipt)
    pngs=sorted(out.glob('candidate-*.png'));assert proc.returncode==0 and observed==targetpts and len(pngs)==len(sels),'bounded decode outputs did not match saved actual PTS; attempt retained'
    for s,p in zip(sels,pngs):
        with Image.open(p) as im:assert im.size==(1920,1080);dims=list(im.size)
        s['decoded_png']=pin(p);s['png_size']=dims;s['showinfo_pts_confirmed']=True
    after=raw.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'closed source stat drift'
    result={k:v for k,v in job.items() if k!='raw'};result.update({'state':'ACTUAL_PTS_BOUND_CANDIDATES_CONTENT_REVIEW_PENDING',
      'receipt':pin(out/'extraction-receipt.json'),'source_stat_stable':True,'prior_audited_mtime_available':oldmtime is not None,
      'new_raw_hash':False,'new_media_probe':False,'full_clean_or_human_signoff':False})
    write(out/'candidate-index.json',result)
    print(json.dumps({'run':job['run'],'candidates':[{'role':x['role'],'frame':x['decoded_frame_index_zero_based'],'PTS':x['actual_pts'],'seconds':x['actual_seconds'],'path':x['decoded_png']['path']} for x in sels],'elapsed':receipt['elapsed_seconds']},ensure_ascii=False),flush=True)
    return result
def main():
    assert Path(sys.executable).resolve()==EXPECTED.resolve()
    assert sum(len(x['selections']) for x in PLAN)==9 and sum(len(x['selections']) for x in PLAN)<=12
    write(O/'CANDIDATE-PLAN05.json',{'plan':PLAN,'total_candidate_budget':12,'first_attempt_candidate_count':9,
      'search_hints_only':True,'UTC_to_exact_timecode':False,'active_r0177_read':False,'sdk_ui_bus_git':0})
    jobs=[prepare(x) for x in PLAN]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(extract,jobs))
    write(O/'CANDIDATE-DELIVERY05.json',{'schema':'xar.e04.bounded-old-raw-encoded-candidates/v1','created_utc':datetime.now(timezone.utc).isoformat(),
      'state':'CANDIDATES_PTS_VERIFIED_ROOT_CONTENT_PENDING','new_candidates':9,'max_total':12,'results':results,
      'active_raw_reads':0,'new_raw_hashes':0,'new_full_probes':0,'clean_spans_certified':False,'human_signoff':False})
if __name__=='__main__':main()
