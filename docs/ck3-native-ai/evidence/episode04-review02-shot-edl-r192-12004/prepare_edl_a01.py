"""Bounded editorial preparation only; no media body, run creation or render."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.metadata, json, os, shutil, subprocess, sys

ROOT = Path('D:/workspace/ck3_eternal_recurrence')
BASE = Path('C:/ck3-e04-resume-20261015-a01')
OUT = Path(__file__).resolve().parent
EP = ROOT / 'promo/ck3_native_war_ai/episode-04-march-logistics'
CAP = BASE / 'capacity-r192-r09-a01/R192-CAPACITY.actual-root-a01.json'
LIMIT = 131072
def now(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def raw(path):
    p=Path(path)
    if p.stat().st_size>600000: raise ValueError('large payload read refused: '+str(p))
    return p.read_bytes()
def load(path): return json.loads(raw(path).decode('utf-8-sig'))
def pin(path):
    p=Path(path); b=raw(p)
    return {'path':str(p),'bytes':len(b),'sha256':digest(b),'verification':'fresh-small-file-bytes'}
def write(name,value):
    b=value if isinstance(value,bytes) else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    used=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    if used+len(b)>LIMIT: raise ValueError('128KiB output cap')
    with (OUT/name).open('xb') as f:f.write(b)
def call(argv,env=None):
    r=subprocess.run(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return r,{'argv':argv,'exit_code':r.returncode,'stdout':r.stdout.decode('utf-8','replace'),'stderr':r.stderr.decode('utf-8','replace')}

def main():
    observed=now(); cap=load(CAP)
    assert cap['admitted'] is True and datetime.now(timezone.utc)<datetime.fromisoformat(cap['quota_review_at_utc'])
    _,mid=call([sys.executable,'-B',str(ROOT/'tools/ck3_live_run_id.py'),'machine'])
    machine=mid['stdout'].strip(); assert machine==cap['machine_id']
    _,head=call(['git','rev-parse','HEAD']);head=head['stdout'].strip()
    assert head=='60de49f61d23b9c3437af4544c3f12bb28445429'
    r,release_command=call(['gh','api','repos/XenoAmess/xar_promo_toolchain/releases/latest'])
    assert r.returncode==0
    release=json.loads(r.stdout); assert not release['draft'] and not release['prerelease']
    wheel=next(x for x in release['assets'] if x['name'].endswith('.whl'))
    requirement=raw(ROOT/'tools/requirements-promo-toolchain.txt').decode('utf-8')
    assert wheel['browser_download_url'] in requirement and wheel['digest'].split(':',1)[1] in requirement
    write('official-release.actual.raw.json',r.stdout)
    assert importlib.metadata.version('xar-promo-toolchain')==release['tag_name'].removeprefix('v')
    distribution=importlib.metadata.distribution('xar-promo-toolchain')
    direct=json.loads(distribution.read_text('direct_url.json'))
    assert direct['url']==wheel['browser_download_url'] and direct['archive_info']['hashes']['sha256']==wheel['digest'].split(':',1)[1]
    prefix=[sys.executable,'-B','-X','utf8','-m','xar_promo']
    probes=[]
    for args in (['--version'],['--help'],['plan','--help'],['validate','--help']):
        _,result=call(prefix+args);assert result['exit_code']==0;probes.append(result)
    write('TOOLCHAIN.actual.json',{'machine_id':machine,'observed_at_utc':observed,'scope':'fresh independent EDL preparation query; not copied R192 release evidence','source_head':head,'official_query':{k:v for k,v in release_command.items() if k!='stdout'},'release_response':pin(OUT/'official-release.actual.raw.json'),'release_tag':release['tag_name'],'published_at':release['published_at'],'wheel':{k:wheel[k] for k in ('name','size','digest','browser_download_url')},'installed_version':distribution.version,'installed_origin':direct,'interpreter':sys.executable,'cli_probes':probes})

    media_path=Path('D:/workspace/ck3_native_war_ai_promo_work/e04-r191-media-audit-bounded-a01/portable-media-facts.actual-a01.json')
    media=load(media_path)
    strict_path=BASE/'r191-portable-candidate-a01/reader-derived-a03/STRICT-SOURCE-FACTS.actual.json'
    strict=load(strict_path)
    assert strict['positive_debit_sum']==11 and len(strict['positive_writer_source_rows'])==7
    assert strict['bounds']['event_exact_PTS'] is False
    old=load(EP/'review02/edit-decision-a01/edit-decision69.json')
    method=load(BASE/'review02-composer-candidate-a01/input-config.methodology.json')
    measured=load(BASE/'review02-audio-rest68-edge731-a03/production-inputs69.merged.json')
    pngplan=load(BASE/'review02-full23-plan-a03/FULL23-JOIN-PLAN.actual-a03.json')
    assert len(old['cues'])==len(method['cues'])==len(measured['cues'])==69
    assert [x['id'] for x in old['cues']]==[x['id'] for x in method['cues']]==[x['id'] for x in measured['cues']]
    assert old['total_frames']==method['total_frames']==58406
    card_by={x['cue_id']:x['card_id'] for x in pngplan['cue_card_mapping']}
    candidates=[
      {'id':'R191_SIEGE','state':'RAW_COMPLETE_BUSINESS_EVENT_PROVEN_SELECTION_PENDING','source':pin(media_path),'raw_inherited':media['raw'],'raw_hash_fresh_in_this_lane':False,'frames':3359,'encoded_end_seconds':111.966,'review_window_seconds':[0,111.966],'selection':None,'native_fact':{'callback':8,'date_raw':53148192,'positive_writer_count':7,'physical_debit_sum':11,'source':pin(strict_path)},'native_event_PTS':None,'continuous_clean':False,'cues':['C01-05','C03-01','C03-02','C03-03','C06-01'],'limit':'Native writer evidence is strict; UTC/native day completion is not encoded PTS. Inspect exact scene first; 82.9820883 wall seconds are paused tail, not gameplay advancement.'},
      {'id':'R175_LOCKED_HALT','state':'EXISTING_RAW_CANDIDATES_REVIEW_PENDING','source':pin(ROOT/'docs/ck3-native-ai/episode04-r12-locked-halt-r0175-12004.md'),'review_windows_seconds':[[0,4],[4,24],[24,43.5]],'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C01-04','C04-05','C04-06','C04-07'],'limit':'24s onward notification; candidate ranges are not clean approval. Exact96.7percent/cutoff50percent retain original R175 identity.'},
      {'id':'R176_LOCKED_REROUTE','state':'EXISTING_RAW_CANDIDATES_REVIEW_PENDING','source':pin(ROOT/'docs/ck3-native-ai/episode04-r13-locked-reroute-r0176-12004.md'),'raw_inherited':{'bytes':60656946,'sha256':'e8eccb2e36b143a94ee73f6f481a792d79adc55df9e387ad1284ef3216c40535'},'review_windows_seconds':[[0,4],[4,10],[10,20]],'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C01-06','C04-01','C04-02','C04-03','C04-04','C04-06','C04-08','C06-03'],'limit':'Alternate endpoint is outside45s raw; historical13days/8days remain native data-card facts, not filmed endpoint.'},
      {'id':'R09_FORWARD_NEW','state':'AWAIT_ROOT_ACTUAL_R192','expected_run_id':cap['run_id'],'raw_inherited':None,'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C02-11','C02-12','C05-06','C05-08','C05-09','C05-10','C05-14','C06-05','C06-06'],'limit':'Paused same-date split/merge only; bind full identity/physical rows/roleweights/both stock/caps/commander. Do not prefill250 or commander34232 as newly observed.'},
      {'id':'R09_REVERSE_NEW','state':'AWAIT_SEPARATE_ROOT_ADMISSION_AND_ACTUAL','expected_run_id':None,'raw_inherited':None,'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C02-11','C02-12','C05-06','C05-08','C05-09','C05-10','C05-14','C06-05','C06-06'],'limit':'Independent normal cold load from exact same baseline; freeze reverse direction before action. No capacity or run allocated by this plan.'},
      {'id':'R173_BOARDING','state':'EXISTING_RAW_CANDIDATES_REVIEW_PENDING','source':pin(ROOT/'docs/ck3-native-ai/episode04-r0173-boarding-halt-12004.md'),'review_windows_seconds':[[147.5,153.5],[153.5,161.6],[168.9,174.9]],'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C04-09','C04-10','C05-13','C06-08'],'limit':'3gold belongs to R173; neither R1781gold nor generic wallet difference substitutes. Halt is not in this raw.'},
      {'id':'R174_UNLOCKED_HALT','state':'EXISTING_RAW_CANDIDATES_REVIEW_PENDING','source':pin(ROOT/'docs/ck3-native-ai/episode04-r0174-common-t0-control-12004.md'),'review_windows_seconds':[[0,4],[4,20]],'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C06-10'],'limit':'Independent R174 illustration only; cannot splice as continuous R173 postboarding Halt. Left-upper tooltip obstruction to review.'},
      {'id':'R177_COASTAL','state':'EXISTING_RAW_CANDIDATES_REVIEW_PENDING','source':pin(ROOT/'docs/ck3-native-ai/episode04-r0177-coastal-normalprep-12004.md'),'review_windows_seconds':[[0,4],[4,10],[10,15]],'selection':None,'native_event_PTS':None,'continuous_clean':False,'cues':['C01-02','C06-07'],'limit':'Independent coastal arrival Broll, not R13 endpoint/ABC result; visual transition bracket(4,10] only.'},
      {'id':'REVIEW01_HISTORY','state':'HISTORICAL_APPENDIX_ONLY','source':pin(ROOT/'docs/handover/2026-10-06-war-episode04-review01-delivery.md'),'selection':None,'continuous_clean':False,'cues':['C05-16'],'limit':'Keep original1.20.0.3/William source label. No reuse as Robert/.4 numbers, ABCwinner or fresh clean credit.'}
    ]
    rows=[]
    for oldrow,audio in zip(old['cues'],measured['cues']):
        key=oldrow['id']; ap=Path(audio['audio']['path'])
        assert ap.is_file() and ap.stat().st_size==audio['audio']['bytes']
        rows.append({'id':key,'timeline_frames':[oldrow['start_frame'],oldrow['end_frame_exclusive']],'speech_seconds':oldrow['actual_speech_seconds'],'text_sha256':oldrow['text_sha256'],'audio_artifact_id_future':audio['audio_artifact_id'],'audio_source_inherited':audio['audio'],'source_card_id':card_by[key],'candidate_ids':[c['id'] for c in candidates if key in c['cues']],'movie_visual_artifact_id':None,'capture_clip':None,'continuous_clean':False})
    write('EDIT-CANDIDATES.actual-a01.json',{'schema':'xar.e04.review02.candidate-edl.v1','machine_id':machine,'observed_at_utc':observed,'source_head':head,'scope':'Candidate EDL, not bind_payloads visuals; null bindings intentionally fail production promotion','fps':30,'total_frames':58406,'duration_seconds':58406/30,'reuse_existing_audio':True,'provider_calls':0,'source_card_count':23,'candidates':candidates,'cues':rows,'actual_movie_created':False,'render_ready':False,'human_signoff':False,'promotion_required':['per-cue exactly one actual preserved visual_artifact_id with source-explanation-card role OR capture_clip with continuous_clean=true','capture clip receipt+raw+control artifacts, exact measured duration, actual frame range','1080p mixed composer geometry review; no engine replacement','new native run and exact production-inputs-v1 preservation under separate render capacity']})

    paths=[CAP,EP/'review02/r184-shot-priority-2026-10-16.md',EP/'review02/edit-decision-a01/edit-decision69.json',EP/'review02/subtitles-actual69-a01/CHECK.actual.json',BASE/'review02-audio-rest68-edge731-a03/production-inputs69.merged.json',BASE/'review02-audio-rest68-edge731-a03/narration69.timeline.actual.json',BASE/'review02-composer-candidate-a01/input-config.methodology.json',BASE/'review02-composer-candidate-a01/promo-project.methodology.json',BASE/'review02-render-inputs-a03-materialized-a01/project/promo-project.json',BASE/'review02-static-raster-production-a01/raster-manifest.actual.json',BASE/'review02-full23-plan-a03/FULL23-JOIN-PLAN.actual-a03.json',BASE/'review02-full23-plan-a03/ROOT-EXACT-ARGV.NOT-EXECUTED-a03.json',ROOT/'promo/ck3_native_war_ai/integration/src/war_ai_promo/episode04_review02.py',ROOT/'promo/ck3_native_war_ai/integration/src/war_ai_promo/composer.py',BASE/'review02-real-dry-plan-a02/review02_png_composer.py',BASE/'review02-real-dry-plan-a02/prepare_png_run_a02.py',BASE/'review02-real-dry-plan-a02/run_png_pipeline_a02.py',media_path,strict_path,BASE/'r191-portable-candidate-a01/reader-derived-a03/ANALYSIS.actual.json']
    paths += [EP/f'review02/story-a0{i}/claim-shot-agent-map.json' for i in range(2,6)]
    write('INPUTPINS.actual.json',{'machine_id':machine,'observed_at_utc':now(),'source_head':head,'fresh_small_file_pins':[pin(p) for p in paths],'audio_metadata_stat_count':69,'audio_body_reads':0,'PNG_body_reads':0,'raw_body_reads':0,'full_payload_reads':0,'render_reservation_bytes':cap['render_reserved_bytes'],'native_render_run_exists':(BASE/'review02-methodology-FHD-run-a03/run-manifest.json').exists(),'prior_run_roots_not_created_by_this_lane':True,'volumes_at_start':{v:{'free_bytes':shutil.disk_usage(v).free} for v in ['C:/','D:/']}})

    config=BASE/'review02-render-inputs-a03-materialized-a01/project/promo-project.json'
    work=OUT/'PROPOSED_NATIVE_PLAN_WORKDIR_MUST_NOT_EXIST'
    assert not work.exists()
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(ROOT/'promo/ck3_native_war_ai/integration/src')
    planargv=prefix+['plan',str(config),'--workdir',str(work),'--composer','war_ai_promo.episode04_review02:compose','--validate-only']
    _,actualplan=call(planargv,env=env)
    write('NATIVE-PLAN.actual.json',{'machine_id':machine,'observed_at_utc':now(),**actualplan,'workdir_exists_after':work.exists(),'new_run_created':False,'media_calls':0,'result_scope':'Actual CLI plan against existing config; missing preserved native production input is a real pre-render dependency, not media RED'})
    assert not work.exists()
    write('ROOT-DELIVERY.actual-a01.json',{'machine_id':machine,'observed_at_utc':now(),'source_head':head,'scope':'EDL+exact small input pins+fresh release/CLI plan only','files':[pin(p) for p in OUT.iterdir() if p.is_file()],'output_limit_bytes':LIMIT,'actual_current_output_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'new_run_created':False,'render_or_media_or_SDK_or_desktop_calls':0,'raw_or_audio_or_PNG_body_reads':0,'source_tree_mutations':0,'R09_actual_credit_added':0,'clean_credit_added':0})
    print(json.dumps({'status':'DELIVERED','directory':str(OUT),'bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'plan_exit':actualplan['exit_code'],'plan_stderr':actualplan['stderr']},ensure_ascii=False))
if __name__=='__main__':main()
