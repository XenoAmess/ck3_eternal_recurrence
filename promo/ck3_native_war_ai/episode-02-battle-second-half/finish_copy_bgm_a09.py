"""Mix, verify and sample the new a09 movie, with no manufactured signoff."""
from pathlib import Path
import argparse,json,os,sys,math,shutil,re,concurrent.futures,importlib.metadata
import numpy as np
from PIL import Image,ImageDraw
from xar_promo import probe_and_write_bound_media
from xar_promo.operations import preserve_artifact
from xar_promo.project import load_document
from xar_promo.runlog import append_phase_record,append_automated_audit_record
from xar_promo.evidence import bind_external_artifact,write_sampling_plan_v2,write_evidence_bundle_v2
import review_story_a04 as p
import compose_review_boards_a04 as b
import fix_evidence_label_a06 as notice
from compose_copy_bgm_a09 import P,OUTPUT,exact,require,validate
from boards_copy_a09 import DETAILS

def mix(run):
    validate(run,'before-mix');os.environ['PYTHONPATH']=str(P)+os.pathsep+str(P.parent/'integration/src')
    for group,expected in [('xar_promo.adapters','ck3-native-war-ai-v1'),('xar_promo.presets','ck3-native-war-ai-longform-zh-v2')]:
        require(any(e.name==expected for e in importlib.metadata.entry_points(group=group)),'Missing installed project integration entry point: '+expected)
    source=P/'native_mix_a09.py';shutil.copyfile(source,run/'sources/native-mix-source-a02.py')
    p.write(run/'sources/native-mix-a02-binding.json',{'at_utc':p.stamp(),'source':p.ref(source),'reason':'Public subtitle ABI verified; single-segment direct remux preserves AAC skip metadata. Earlier source snapshot retained.'})
    attempt=run/'native-build-attempt-01';manifest=run/'native-run/run-manifest.json'
    common=[str(manifest),'--workdir',str(attempt),'--composer','native_mix_a09:compose']
    p.command(run,'native-read-only-plan',[sys.executable,'-X','utf8','-m','xar_promo','plan',*common]);require(not attempt.exists(),'Plan created proposed workdir')
    p.command(run,'native-series-bgm-build',[sys.executable,'-X','utf8','-m','xar_promo','build',*common])
    out=attempt/OUTPUT;require(out.is_file(),'Native build did not produce movie')
    p.write(run/'final-artifact.json',{**p.ref(out),'duration_expected':p.read(run/'timeline.json')['total_duration'],'music':p.read(run/'music-policy.json'),'human_signoff':'not-provided','production_clean_admission':False,'status':'pending-machine-and-human-review'})
    validate(run,'after-mix');print(json.dumps({'final':str(out),'BGM':True}),flush=True)

def audit(run):
    final=p.read(run/'final-artifact.json');exact(final);validate(run,'before-final-audit-a02')
    probe=p.read(p.command(run,'final-audit-probe',[str(p.FFPROBE),'-v','error','-show_format','-show_streams','-show_chapters','-of','json',final['path']]));p.write(run/'audit/final-probe.json',probe)
    v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio');timeline=p.read(run/'timeline.json');edit=p.read(run/'edit.json');checks={}
    checks['geometry_and_codec']=v['codec_name']=='h264' and (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
    checks['audio_codec_and_shape']=a['codec_name']=='aac' and a['sample_rate']=='48000' and a['channels']==2
    checks['duration']=abs(float(probe['format']['duration'])-final['duration_expected'])<.15
    checks['six_chapters']=len(probe['chapters'])==6
    checks['177_cues']=sum(len(c['utterances']) for c in timeline['chapters'])==177
    for c,actual in zip(timeline['chapters'],probe['chapters']):checks['chapter_'+c['id']]=abs(float(actual['start_time'])-c['global_start'])<.01 and abs(float(actual['end_time'])-c['global_start']-c['duration'])<.1 and actual['tags']['title']==c['title']
    for c in timeline['chapters']:
        for u in c['utterances']:
            checks['cue_'+u['key']]=bool(u['facts']) and all(Path(f['source_path']).is_file() for f in u['facts']) and Path(u['audio']).is_file() and Path(edit['utterances'][u['key']]['image']).is_file() and all(p.ass_text(u[lang],lim).count(r'\N')<=1 for lang,lim in [('zh',40),('en',100)])
    checks['timed_original_notice']=edit['utterances']['knights-k035']['raw_notice_inset']==notice.RAW_INSETS['knights-k035']
    p.command(run,'full-AV-decode',[str(p.FFMPEG),'-hide_banner','-nostdin','-v','error','-xerror','-i',final['path'],'-map','0:v:0','-map','0:a:0','-f','null','-']);checks['full_AV_decode']=True
    volume=p.command(run,'final-volume-detect',[str(p.FFMPEG),'-hide_banner','-nostdin','-i',final['path'],'-map','0:a:0','-af','volumedetect','-f','null','-'])
    stderr=(run/'logs/final-volume-detect.stderr.txt').read_text(encoding='utf-8',errors='replace');mean=float(re.search(r'mean_volume: ([\-\d.]+) dB',stderr).group(1));peak=float(re.search(r'max_volume: ([\-\d.]+) dB',stderr).group(1));checks['audio_no_clipping']=peak<-.05
    p.write(run/'audit/audio-levels.json',{'subject':final,'mean_dbfs':mean,'peak_dbfs':peak,'sample_rate':48000,'human_listening_signoff':'not-provided'})
    musicproof(run,final,timeline);checks['series_music_at_all_sample_windows']=p.read(run/'audit/music-presence.json')['passed']
    checks['all_checks']=all(checks.values());p.write(run/'audit/machine-report.json',{'at_utc':p.stamp(),'artifact':final,'checks':checks,'passed':all(checks.values()),'human_signoff':'not-provided','full_1x_human_review':False})
    require(all(checks.values()),'Machine audit failed; all diagnostics retained')
    print(json.dumps({'checks':len(checks),'all_passed':True,'mean_dbfs':mean,'peak_dbfs':peak,'BGM_proved':True}),flush=True)

def musicproof(run,final,timeline):
    """Compare decoded movie-minus-narration against the exact looped music stem.

    This tests actual encoded audio; a config field alone cannot pass it.
    Whole stems remain retained. Chapter midpoints and loop interiors cover the
    film; the original fixed-gain policy includes its two exterior fades.
    """
    root=run/'audio-proof';root.mkdir(exist_ok=False);duration=timeline['total_duration'];music=final['music']['source'];dry=p.read(run/'dry-master.json')
    p.command(run,'music-source-probe',[str(p.FFPROBE),'-v','error','-show_format','-show_streams','-of','json',music['path']]);source_duration=float(p.read(run/'logs/music-source-probe.stdout.txt')['format']['duration'])
    def decode(name,path,loop=False,af=None):
        argv=[str(p.FFMPEG),'-hide_banner','-nostdin','-loglevel','error','-n']
        if loop:argv+=['-stream_loop','-1']
        argv+=['-i',path,'-map','0:a:0']
        if af:argv+=['-af',af]
        argv+=['-t',f'{duration:.6f}','-ar','8000','-ac','1','-c:a','pcm_f32le','-f','f32le',str(root/(name+'.f32'))]
        p.command(run,'audio-proof-'+name,argv)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(decode,'actual',final['path']),pool.submit(decode,'narration',dry['path']),pool.submit(decode,'music',music['path'],True,f'volume=-17dB,afade=t=in:d=2,afade=t=out:st={duration-8:.6f}:d=8')]
        for future in futures:future.result()
    actual=np.fromfile(root/'actual.f32',dtype='<f4');voice=np.fromfile(root/'narration.f32',dtype='<f4');bgm=np.fromfile(root/'music.f32',dtype='<f4');n=min(len(actual),len(voice),len(bgm));actual=actual[:n];voice=voice[:n];bgm=bgm[:n]
    require(abs(n/8000-duration)<.1,'Decoded audio does not span movie duration')
    # Codec/resampling can move decoded samples. Fit only one whole-film lag;
    # the same fixed lag is then held for every independently sampled window.
    begin=8000*30;length=8000*8;expected=voice+bgm
    lags=range(-240,241);errors=[float(np.mean((actual[begin+lag:begin+lag+length]-expected[begin:begin+length])**2)) for lag in lags];lag=list(lags)[int(np.argmin(errors))]
    points={round(c['global_start']+c['duration']/2,3) for c in timeline['chapters']}
    points.update(round(t+min(source_duration/2,40),3) for t in np.arange(0,duration,source_duration) if t+min(source_duration/2,40)<duration-10)
    points.update([5.,duration-12.]);rows=[]
    for seconds in sorted(points):
        i=round(seconds*8000);stop=min(i+4*8000,n-abs(lag));i=max(i,abs(lag));residual=actual[i+lag:stop+lag]-voice[i:stop];target=bgm[i:stop]
        rms=lambda x:float(np.sqrt(np.mean(x*x)));voice_rms=rms(voice[i:stop]);music_rms=rms(target)
        correlation=float(np.corrcoef(residual,target)[0,1]);error_rms=rms(residual-target);gain=float(np.dot(residual,target)/np.dot(target,target))
        passed=music_rms>1e-6 and correlation>.90 and .85<gain<1.15 and error_rms/music_rms<.5
        rows.append({'seconds':seconds,'duration':(stop-i)/8000,'music_rms_dbfs':20*math.log10(music_rms),'voice_rms_dbfs':20*math.log10(max(voice_rms,1e-12)),'actual_residual_music_correlation':correlation,'actual_residual_expected_music_gain':gain,'residual_error_ratio':error_rms/music_rms,'passed':passed})
    p.write(run/'audit/music-presence.json',{'at_utc':p.stamp(),'subject':final,'exact_original_theme':music,'music_duration':source_duration,'policy_music_gain_db':-17,'narration_gain_db':0,'global_lag_samples_at_8000Hz':lag,'whole_duration_decoded_seconds':n/8000,'windows':rows,'passed':all(row['passed'] for row in rows),'retained_decoded_stems':[p.ref(root/(name+'.f32')) for name in ('actual','narration','music')],'method':'decoded final AAC minus independently decoded new dry narration, compared with exact source theme loop after fixed gain/fades; one fixed sample lag','full_human_listening':False})

def frames(run):
    final=p.read(run/'final-artifact.json');timeline=p.read(run/'timeline.json');root=run/'frame-review';root.mkdir(exist_ok=False);targets={}
    for c in timeline['chapters']:
        targets['chapter-'+c['id']]=(c['global_start']+1,'chapter entry')
        for u in c['utterances']:
            if u['key'] in DETAILS or u['key'] in ('knights-k024','knights-k025','knights-k030','reinforcement-r005','reinforcement-r037'):targets[u['key']]=(u['global_start']+min(2,u['duration']/2),'updated copy/formula/name/growth/original UI')
            if u['key']=='knights-k035':
                for t in (.5,3.):targets['notice-'+str(t)]=(u['global_start']+t,'original timed notice')
    rows=[]
    for key,(seconds,scope) in targets.items():
        out=root/(key+'.png');p.command(run,'frame-'+key,[str(p.FFMPEG),'-hide_banner','-nostdin','-n','-ss',f'{seconds:.6f}','-i',final['path'],'-frames:v','1','-threads','1',str(out)]);rows.append({'key':key,'seconds':seconds,'scope':scope,'frame':p.ref(out)})
    p.write(root/'frame-index.json',{'artifact':final,'frames':rows,'human_full_1x_review':False,'root_actual_frame_review':'pending'})
    for start in range(0,len(rows),4):
        sheet=Image.new('RGB',(1920,1160),b.BG);d=ImageDraw.Draw(sheet)
        for i,row in enumerate(rows[start:start+4]):
            x=i%2*960;y=i//2*580;d.text((x+12,y+7),row['key']+f' {row["seconds"]:.3f}s',font=b.font(24),fill=b.GOLD);im=Image.open(row['frame']['path']).resize((960,540),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+40))
        with (root/f'contact-{start//4+1:02d}.jpg').open('xb') as f:sheet.save(f,quality=94)
    print(json.dumps({'frames':len(rows),'sheets':(len(rows)+3)//4,'actual_review':'pending'}),flush=True)

def review(run):
    final=p.read(run/'final-artifact.json');bound=run/'audit/native-bound-media-probe.json'
    probe_and_write_bound_media(str(p.FFPROBE),Path(final['path']),output_path=bound,audit_directory=run/'audit/native-bound-probe-command')
    storyboard=run/'human-review-storyboard.json';p.write(storyboard,{'chapters':[{'id':c['id'],'title':c['title'],'start_seconds':round(c['global_start'],6),'end_seconds':round(c['global_start']+c['duration'],6)} for c in p.read(run/'timeline.json')['chapters']]})
    args=[sys.executable,'-X','utf8','-m','xar_promo','review',final['path'],'--storyboard',str(storyboard),'--probe',str(bound),'--output-directory',str(run/'pending-human-review'),'--audit-directory',str(run/'native-review-audit'),'--ffmpeg',str(p.FFMPEG)]
    p.command(run,'native-review-read-only-plan',args+['--plan-only']);p.command(run,'native-pending-human-review',args)
    print(json.dumps({'human_review':'pending','package':str(run/'pending-human-review')}),flush=True)

def native_audit(run):
    """CLI integrity audit of real final frame evidence; no invented OCR."""
    manifest=run/'native-run/run-manifest.json';root=manifest.parent
    loaded=load_document(manifest,check_files=True);record=next(x for x in loaded.run.artifacts if x.artifact_id=='a09-deliverable')
    producer={'adapter_id':'ck3-native-war-ai-v1','tool':'FFmpeg','tool_version':'9.0.1','operation':'extract actual final MP4 frame at recorded timestamp','execution':'external'}
    subject=bind_external_artifact(root/record.path,project_root=root,artifact_id='a09-final-source',collection='derived',role='deliverable',label=OUTPUT,media_type='video/mp4',producer=producer)
    frames=p.read(run/'frame-review/frame-index.json')['frames'];rows=[];frame_paths={}
    for i,row in enumerate(frames):
        r=preserve_artifact(manifest,Path(row['frame']['path']),artifact_id=f'a09-frame-{i:02d}',collection='derived',role='frame',label=row['key'],media_type='image/png');frame_paths[round(row['seconds'],6)]=root/r.path
        rows.append({'id':row['key'],'kind':'video','source':subject,'start_seconds':round(row['seconds'],6),'end_seconds':round(row['seconds'],6)})
    plan_path=root/'a09-frame-evidence-plan.json';bundle=root/'a09-frame-evidence-bundle.json'
    plan=write_sampling_plan_v2(plan_path,rows,project_root=root,interval_seconds=1,required_roles=['frame'],external_producers={'frame':producer})
    submissions=[{'sample_id':s['id'],'role':'frame','path':str(frame_paths[round(float(s['timestamp_seconds']),6)]),'media_type':'image/png','producer':producer} for s in plan['samples']]
    write_evidence_bundle_v2(bundle,project_root=root,plan_path=plan_path,submissions=submissions)
    p.command(run,'native-real-frame-integrity-audit',[sys.executable,'-X','utf8','-m','xar_promo','audit',str(manifest),'--subject-artifact-id','a09-deliverable','--evidence-bundle',str(bundle),'--report',str(root/'a09-frame-integrity-audit.json'),'--report-artifact-id','a09-frame-integrity-audit'])
    validate(run,'after-cli-frame-audit');print(json.dumps({'native_integrity_audit':'passed','frame_count':len(frames),'human_signoff':'not-provided'}),flush=True)

def preserve(run):
    """Keep major evidence in CAS and all other process bytes indexed in place."""
    validate(run,'before-archive');manifest=run/'native-run/run-manifest.json';final=p.read(run/'final-artifact.json');loaded=load_document(manifest,check_files=True);require(not loaded.run.signoffs,'No signoff was provided')
    require(p.read(run/'audit/machine-report.json')['passed'],'Machine audit required')
    paths=[x for x in sorted(run.rglob('*')) if x.is_file() and 'native-run' not in x.parts]
    external=[x for x in sorted(Path('C:/Users/1/ck3-e2-copy-bgm-20261002-a01').rglob('*')) if x.is_file() and not any(part.startswith('preserve-attempt') for part in x.parts)]
    pins=[p.ref(x) for x in paths+external]
    p.write(run/'retained-process-index.json',{'at_utc':p.stamp(),'subject':final,'files':pins,'external_retained_audio':[{'key':u['key'],'raw':u['tts_raw'],'trimmed':u['tts_trimmed']} for c in p.read(run/'timeline.json')['chapters'] for u in c['utterances']],'music':final['music']['source'],'no_previous_assets_removed':True,'active_archive_wrapper_excluded_until_process_exit':True,'human_signoff':'not-provided'})
    for pin in pins:exact(pin)
    p.write(run/'retention-verification.json',{'at_utc':p.stamp(),'files_checked_twice':len(pins),'all_hashes_match':True,'index':p.ref(run/'retained-process-index.json')})
    selected=[('retained-process-index.json','a09-process-index'),('retention-verification.json','a09-retention-verification'),('timeline.json','a09-timeline'),('edit.json','a09-edit'),('music-policy.json','a09-music-policy'),('audit/machine-report.json','a09-machine-report'),('audit/music-presence.json','a09-music-presence'),('audit/audio-levels.json','a09-audio-levels'),('frame-review/final-frame-quality.json','a09-frame-quality'),('audit/native-bound-media-probe.json','a09-bound-probe'),('delivery/final-delivery.json','a09-client-delivery')]
    for name,aid in selected:preserve_artifact(manifest,run/name,artifact_id=aid,collection='derived',role='process-evidence',label=Path(name).name,media_type='application/json')
    append_phase_record(manifest,phase_id='a09-full-editorial-audit-prepared-media',status='succeeded',artifact_ids=['a09-timeline','a09-edit'],detail='177 audited bilingual cues; 100 fresh and 77 exact verified retained voice takes; 98 updated boards; source evidence retained. Prior versions unchanged.')
    append_automated_audit_record(manifest,check_id='a09-final-media-and-real-music',status='passed',subject_artifact_id='a09-deliverable',report_artifact_id='a09-machine-report')
    append_phase_record(manifest,phase_id='a09-limited-final-frame-inspection',status='succeeded',artifact_ids=['a09-frame-quality'],detail='Root inspected actual final frames. No full human1x viewing/listening or signoff.')
    append_phase_record(manifest,phase_id='a09-single-authorized-onedrive-video',status='succeeded',artifact_ids=['a09-client-delivery'],detail='One final MP4 only; client metadata readback is recorded separately from independent remote byte verification.')
    validate(run,'after-archive');p.write(run/'native-preservation-complete.json',{'at_utc':p.stamp(),'manifest':p.ref(manifest),'indexed_files':len(pins),'human_signoffs':0})
    print(json.dumps({'indexed_files':len(pins),'human_signoffs':0}),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['mix','audit','frames','review','native_audit','preserve']);a.add_argument('--run',required=True,type=Path);args=a.parse_args();globals()[args.phase](args.run)
