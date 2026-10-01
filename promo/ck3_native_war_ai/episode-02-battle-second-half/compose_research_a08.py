"""Build a fresh finite-research review candidate; never invent human signoff.

The previous run remains immutable. Equal text and verified audio may be reused;
new text receives fresh TTS. Changed chunk audio is rebuilt and global timings
are recalculated. The original timed a02 notice inset remains independently
labelled. Every phase writes new files and preserves partial/failed output.
"""
from __future__ import annotations
import argparse, concurrent.futures, copy, importlib.metadata, json, shutil, sys
from pathlib import Path
import compose_review_boards_a04 as boards
import review_story_a04 as producer
import fix_evidence_label_a06 as notice

P=Path(__file__).resolve().parent
V7=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-native-supplement-20261001-a01')
AUDIO=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a03')
R=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-13-reinforcement-full-frame')
R148=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-identifier-append-live-20261002-a12/scoped-ui-research-attempt-01')
R149=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-06-d11-full-frame-live-20261002-a13/scoped-ui-research-attempt-01')
OUTPUT='CK3-War-AI-Episode02-BrownGold-Research-20261002-a08.mp4'
ORDER=['opening','pursuit','knights','reinforcement','terminal','closing']
def require(v,m):
    if not v:raise ValueError(m)
def bykey(story):return {c['id']+'-'+u['id']:u for c in story['chapters'] for u in c['utterances']}
def exact(expected):
    actual=producer.ref(expected['path'])
    require(actual['bytes']==expected['bytes'] and actual['sha256']==expected['sha256'].upper(),'Changed preserved input: '+expected['path'])
    return actual
def prepare(run):
    require(not run.exists(),'Fresh run directory required')
    run.mkdir(parents=True)
    for n in ['logs','sources','audit']:(run/n).mkdir()
    previous_environment=producer.read(V7/'sources/environment.json')
    wheel=exact(previous_environment['wheel'])
    latest=producer.read(producer.command(run,'latest-formal-release',['gh','release','view','--repo','XenoAmess/xar_promo_toolchain','--json','tagName,name,publishedAt,url,assets,isDraft,isPrerelease']))
    version=importlib.metadata.version('xar-promo-toolchain')
    require(not latest['isDraft'] and not latest['isPrerelease'] and latest['tagName'].lstrip('v')==version,'Install latest formal wheel before this new run')
    asset=next(a for a in latest['assets'] if a['name']==Path(wheel['path']).name)
    require(asset['digest'].split(':')[-1].upper()==wheel['sha256'],'Latest formal wheel SHA differs')
    url=json.loads(importlib.metadata.distribution('xar-promo-toolchain').read_text('direct_url.json'))
    archive=url.get('archive_info') or {};h=(archive.get('hashes')or{}).get('sha256') or archive.get('hash','').removeprefix('sha256=')
    require(h.upper()==wheel['sha256'],'Installed wheel provenance differs')
    producer.write(run/'release-query.json',{'queried_at_utc':producer.stamp(),'release':latest,'wheel':wheel})
    branch=producer.command(run,'source-branch',['git','-C',str(P),'branch','--show-current']).read_text(encoding='utf-8').strip()
    require(branch=='codex/war-series-brown-gold-20261001','Independent video branch required')
    head=producer.command(run,'source-head',['git','-C',str(P),'rev-parse','HEAD']).read_text(encoding='utf-8').strip()
    environment={'at_utc':producer.stamp(),'python':sys.executable,'python_version':sys.version,'promo_version':version,'wheel':wheel,'installed_wheel_provenance':url,'pillow_version':importlib.metadata.version('Pillow'),'edge_tts_version':importlib.metadata.version('edge-tts'),'ffmpeg':str(producer.FFMPEG),'ffprobe':str(producer.FFPROBE),'branch':branch,'source_head':head,'main_venv_explicitly_selected':True,'no_master_intake':True}
    producer.write(run/'sources/environment.json',environment)
    for name,args in [('version',['--version']),('help',['--help']),('start-help',['start-run','--help']),('preserve-help',['preserve','--help']),('validate-help',['validate','--help']),('audit-help',['audit','--help']),('review-help',['review','--help'])]:producer.command(run,'toolchain-'+name,[sys.executable,'-X','utf8','-m','xar_promo',*args])
    story_path=P/'project/review-story-a08-story.json';config=P/'project/review-story-a08-project.json';story=producer.read(story_path)
    require([c['id']for c in story['chapters']]==ORDER,'Six original chapters required')
    require(len(bykey(story))==167,'Full 167-cue coverage required')
    for c in story['chapters']:
        for u in c['utterances']:
            for language,limit in [('zh',40),('en',100)]:require(producer.ass_text(u[language],limit).count(r'\N')<=1,'Subtitle exceeds two lines: '+c['id']+'-'+u['id']+'-'+language)
            require(u['facts'] and all(Path(f['source_path']).is_file()for f in u['facts']),'Missing original claim evidence: '+c['id']+'-'+u['id'])
    for src,name in [(story_path,'story.json'),(config,'project-config.json'),(Path(__file__),'composer-source.py'),(Path(producer.__file__),'producer-source.py'),(Path(boards.__file__),'board-source.py'),(Path(notice.__file__),'notice-source.py')]:shutil.copyfile(src,run/'sources'/name)
    shutil.copyfile(config,run/'project-config.json');shutil.copyfile(story_path,run/'claim-catalog.json')
    producer.write(run/'input-freeze.json',[producer.ref(p)for p in (story_path,config,Path(__file__),Path(producer.__file__),Path(boards.__file__),Path(notice.__file__),V7/'timeline.json',V7/'edit.json',V7/'claim-catalog.json')])
    producer.command(run,'start-run',[sys.executable,'-X','utf8','-m','xar_promo','start-run',str(run/'project-config.json'),'--run-id',run.name,'--run-directory',str(run/'native-run')])
    for p,n in [(run/'project-config.json','config'),(run/'native-run/run-manifest.json','run')]:producer.command(run,'validate-'+n,[sys.executable,'-X','utf8','-m','xar_promo','validate',str(p)])
    print(json.dumps({'status':'PREPARED','run':str(run),'latest_version':version}))
def narrate(run):
    story=producer.read(run/'sources/story.json');old=bykey(producer.read(AUDIO/'timeline.json'));results=[];jobs=[]
    for c in story['chapters']:
        for u in c['utterances']:
            key=c['id']+'-'+u['id'];prior=old[key]
            if prior['zh']!=u['zh']:jobs.append((c,u));continue
            for field in ['tts_raw','tts_trimmed']:exact(prior[field])
            request=producer.read(AUDIO/'tts'/key/'request.json')
            require(request['request']['voice']=='zh-CN-XiaoxiaoNeural' and request['request']['rate']=='-5%','Original voice policy differs')
            root=run/'tts'/key;root.mkdir(parents=True,exist_ok=False)
            r={**u,'chapter':c['id'],'key':key,'tts_raw':prior['tts_raw'],'tts_trimmed':prior['tts_trimmed'],'audio':prior['audio'],'duration':prior['duration'],'reused_processed_from':str(AUDIO/'timeline.json')}
            producer.write(root/'request.json',request);producer.write(root/'utterance.json',r);results.append(r)
    producer.write(run/'fresh-tts-plan.json',{'changed_keys':[c['id']+'-'+u['id']for c,u in jobs],'retained_verified_audio':len(results),'voice':'zh-CN-XiaoxiaoNeural','rate':'-5%'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6)as pool:
        futures=[pool.submit(producer.narrate_one,run,c,u)for c,u in jobs]
        for f in concurrent.futures.as_completed(futures):
            r=f.result();results.append(r);print(json.dumps({'new_tts':r['key'],'seconds':r['duration']}),flush=True)
    producer.write(run/'tts-raw-receipts.json',results);producer.timeline_from_audio(run,story,results)
def make_boards(run):
    story=producer.read(run/'sources/story.json');edit=copy.deepcopy(producer.read(V7/'edit.json'));specs={}
    for c in story['chapters']:
        for u in c['utterances']:
            v=u.get('visual',{});
            if v.get('kind')!='research_closure_card':continue
            key=c['id']+'-'+u['id'];reinforce=c['id']=='reinforcement';phase='before'if u['id']in('r022','r028')else'after'
            source=(R149/(phase+'-width-window.png'))if reinforce else (R148/'after-full-battle-final-desktop-original.png')
            crop=[819,950,1740,1440]if reinforce else [819,1053,1740,1440]
            extras=[]
            if u['id']in('k024','k025'):
                who='victim'if u['id']=='k024'else'killer';source=R148/('after-'+who+'-character-window.png');crop=[0,0,680,900]
                extras=[{'image':str(R148/(p+'-'+who+'-character-window.png')),'crop_xyxy':[0,0,680,900],'label':date+'：原版人物页'}for p,date in [('before','12.29'),('after','12.30')]]
            if u['id']=='r037':extras=[{'image':str(R149/(p+'-width-window.png')),'crop_xyxy':[819,950,1740,1440],'label':date+'：完整战斗窗与军力提示'}for p,date in [('before','12.14'),('after','12.15')]]
            row={'title':v['focus'],'case':'本轮R0149｜1066.12.14 → 12.15'if reinforce else'本轮R0148｜1066.12.29 → 12.30','source_image':str(source),'crop_xyxy':crop,'ui_label':'原版完整画面定位','diagram_title':'原生记录解释与原版界面','diagram_lines':v['diagram_lines'],'footer':'加入事件边界与暂停UI时间分开；此处显示真实暂停原图。'if reinforce else'本轮受控击杀；与前段独立致残、a02通知录像分开。','source_kind':'actual-ui-and-separately-labelled-original-native-record','extra_ui':extras}
            shot=boards.board(run,key,row);shot['evidence']=u['facts'];edit['utterances'][key]=shot;specs[key]=row
    edit.update({'kind':'a08-finite-research-and-complete-native-ui','human_signoff':'not-provided','production_clean_admission':False})
    producer.write(run/'board-spec.json',specs);producer.write(run/'edit.json',edit)
    producer.write(run/'visual-input-freeze.json',[producer.ref(p)for p in sorted({Path(s['image'])for s in edit['utterances'].values()if s.get('kind')!='raw-excerpt'})])
    print(json.dumps({'new_boards':len(specs),'coverage':len(edit['utterances'])}))
def render(run):
    timeline=producer.read(run/'timeline.json');edit=producer.read(run/'edit.json');prior=producer.read(V7/'timeline.json');oldedit=producer.read(V7/'edit.json');old=bykey(prior)
    require(1620<=timeline['total_duration']<=1920,'Narrated duration outside authorized 27–32 minutes')
    require(not(run/'chapters').exists(),'New render attempt required after partial render')
    tasks=[]
    for c in timeline['chapters']:
        for index,begin in enumerate(range(0,len(c['utterances']),8),1):
            items=c['utterances'][begin:begin+8];offset=items[0]['local_start'];local=[{**u,'local_start':u['local_start']-offset}for u in items]
            ass=producer.subtitles({**c,'utterances':local},edit);path=V7/'chapters'/c['id']/f'chunk-{index:02d}'
            same=all(u['zh']==old[u['key']]['zh'] and u['en']==old[u['key']]['en'] and u['tts_trimmed']==old[u['key']]['tts_trimmed'] and u['duration']==old[u['key']]['duration'] and edit['utterances'][u['key']]==oldedit['utterances'][u['key']]for u in items)
            same=same and ass.encode('utf-8')==(path/'subtitles.ass').read_bytes()
            tasks.append((c,index,items,path,same))
    producer.write(run/'chunk-plan.json',[{'chapter':c['id'],'chunk_index':i,'keys':[u['key']for u in items],'action':'exact-byte-copy'if same else'fresh-research-render'}for c,i,items,path,same in tasks])
    def one(task):
        c,i,items,path,same=task;target=run/'chapters'/c['id']/f'chunk-{i:02d}'
        if same:
            pin=producer.ref(path/'chunk.mp4');shutil.copytree(path,target);actual=producer.ref(target/'chunk.mp4');require(actual['sha256']==pin['sha256'],'Copied chunk bytes differ');r={**actual,'duration_expected':sum(u['duration']for u in items),'previous':pin}
        else:
            renderer=notice.render_chunk_with_notice if any(edit['utterances'][u['key']].get('raw_notice_inset')for u in items)else producer.render_chunk
            r=renderer(run,c,edit,items,i)
        print(json.dumps({'chunk':c['id']+'-'+str(i),'action':'copied'if same else'rendered'}),flush=True)
        return (c['id'],i,r)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:results=list(pool.map(one,tasks))
    lookup={(c,i):r for c,i,r in results};chapters=[]
    for c in timeline['chapters']:
        root=run/'chapters'/c['id'];chunks=[lookup[c['id'],i]for cc,i,items,path,same in tasks if cc['id']==c['id']]
        producer.write(root/'chunk-receipts.json',chunks);concat=root/'concat.txt';producer.text_once(concat,''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n"for r in chunks));out=root/'chapter.mp4'
        producer.command(run,c['id']+'-chapter-join',[str(producer.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)]);chapters.append({**producer.ref(out),'duration_expected':c['duration']})
    producer.write(run/'chapter-render-receipts.json',chapters);concat=run/'concat.txt';producer.text_once(concat,''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n"for r in chapters))
    meta=run/'chapters.ffmetadata';lines=[';FFMETADATA1']
    for c in timeline['chapters']:lines.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["global_start"]*1000)}',f'END={round((c["global_start"]+c["duration"])*1000)}',f'title={c["title"]}'])
    producer.text_once(meta,'\n'.join(lines)+'\n');out=run/OUTPUT
    producer.command(run,'final-join',[str(producer.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-f','ffmetadata','-i',str(meta),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(out)])
    producer.write(run/'final-artifact.json',{**producer.ref(out),'duration_expected':timeline['total_duration'],'human_signoff':'not-provided','production_clean_admission':False,'whole_previous_AAC_reused':False,'status':'pending-machine-check-and-human-full-review'})
    print(json.dumps({'final':str(out),'duration':timeline['total_duration']}))
def audit(run):
    final=producer.read(run/'final-artifact.json');exact(final)
    probe=producer.read(producer.command(run,'final-audit-probe',[str(producer.FFPROBE),'-v','error','-show_format','-show_streams','-show_chapters','-of','json',final['path']]))
    producer.write(run/'audit/final-probe.json',probe)
    video=next(s for s in probe['streams']if s['codec_type']=='video');audio=next(s for s in probe['streams']if s['codec_type']=='audio');checks={}
    checks['video']=video['codec_name']=='h264' and video['width']==1920 and video['height']==1080 and video['r_frame_rate']=='30/1'
    checks['audio']=audio['codec_name']=='aac' and int(audio['sample_rate'])==48000 and audio['channels']==2
    checks['duration']=abs(float(probe['format']['duration'])-final['duration_expected'])<0.15
    producer.command(run,'full-AV-decode',[str(producer.FFMPEG),'-hide_banner','-nostdin','-v','error','-i',final['path'],'-map','0:v:0','-map','0:a:0','-f','null','-'])
    checks['full_AV_decode']=True
    chapters=producer.read(run/'timeline.json')['chapters'];require(len(probe.get('chapters',[]))==6,'Six embedded chapters required')
    for i,(c,actual)in enumerate(zip(chapters,probe['chapters'])):checks['chapter_'+str(i)]=abs(float(actual['start_time'])-c['global_start'])<.01 and actual.get('tags',{}).get('title')==c['title']
    for c in chapters:
        for u in c['utterances']:checks[u['key']]=bool(u['facts']) and Path(u['audio']).is_file() and producer.ass_text(u['zh'],40).count(r'\N')<=1 and producer.ass_text(u['en'],100).count(r'\N')<=1
    require(all(checks.values()),'Machine audit failed; see retained evidence')
    producer.write(run/'audit/machine-report.json',{'at_utc':producer.stamp(),'artifact':final,'checks':checks,'passed':True,'human_signoff':'not-provided','full_1x_human_review':False})
    print(json.dumps({'machine_checks':len(checks),'passed':True,'human_review':'pending'}))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','narrate','boards','render','audit']);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    {'prepare':prepare,'narrate':narrate,'boards':make_boards,'render':render,'audit':audit}[a.phase](a.run)
if __name__=='__main__':main()
