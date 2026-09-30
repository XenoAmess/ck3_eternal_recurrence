"""Produce an evidence-bound, narrated UI review revision without game control.

Project policy and FFmpeg composition live here. Generic TTS/probe/immutable-run
operations use the selected formal xar-promo wheel. Every output path is new.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, importlib.metadata, json, math, shutil, subprocess, sys, textwrap, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xar_promo.tts import EdgeTtsProvider, TtsRequest
from xar_promo.render import ass_burn_in_filter

FFBIN = Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
FFMPEG, FFPROBE = FFBIN/'ffmpeg.exe', FFBIN/'ffprobe.exe'

def stamp(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest().upper()
def ref(path):
    p=Path(path); return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2)
def text_once(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def command(run,name,args):
    log=run/'logs'/name
    if log.with_suffix('.argv.json').exists():raise FileExistsError(log)
    write(log.with_suffix('.argv.json'),args);started=time.monotonic()
    with log.with_suffix('.stdout.txt').open('xb') as out,log.with_suffix('.stderr.txt').open('xb') as err:
        p=subprocess.run(args,stdout=out,stderr=err,shell=False)
    receipt={'at_utc':stamp(),'argv':args,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-started}
    write(log.with_suffix('.receipt.json'),receipt)
    if p.returncode:raise RuntimeError(f'{name}: {p.returncode}; see {log}.stderr.txt')
    return log.with_suffix('.stdout.txt')
def probe(run,name,path):
    out=command(run,name,[str(FFPROBE),'-v','error','-show_format','-show_streams','-of','json',str(path)])
    return read(out)

def prepare(run,story_path,environment_path):
    run.mkdir(parents=True,exist_ok=False)
    environment=read(environment_path)
    release=json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest',headers={'User-Agent':'ck3-story-a04-run'}),timeout=30))
    wheel=next(a for a in release['assets'] if a['name'].endswith('.whl'))
    if release['draft'] or release['prerelease'] or release['tag_name'].lstrip('v')!=importlib.metadata.version('xar-promo-toolchain'):
        raise RuntimeError('selected interpreter does not have latest formal release')
    if wheel['digest'].split(':')[-1].upper()!=environment['wheel_sha256']:
        raise RuntimeError('selected wheel differs from this run latest release query')
    write(run/'release-query.json',{'queried_at_utc':stamp(),'release':release})
    story=read(story_path)
    if [c['id'] for c in story['chapters']] != ['opening','pursuit','knights','reinforcement','terminal','closing']:raise ValueError('full a04 requires the original six chapters in order')
    for c in story['chapters']:
        if not c['utterances']:raise ValueError('empty chapter')
        for u in c['utterances']:
            if not u['zh'].strip() or not u['en'].strip():raise ValueError('missing bilingual utterance')
            for language,limit in [('zh',40),('en',100)]:
                if ass_text(u[language],limit).count(r'\N')>1:
                    raise ValueError(f'too many subtitle lines before TTS: {c["id"]}/{u["id"]}/{language}')
    for source,name in [(story_path,'story.json'),(environment_path,'environment.json'),(Path(__file__),'producer-source.py')]:
        target=run/'sources'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
    write(run/'input-freeze.json',[ref(story_path),ref(environment_path),ref(__file__)])
    config={'format_version':1,'kind':'xar_promo_project_config',
      'project':{'id':'ck3-war-ai-episode02-story-review-a03','title':'四倍兵力，还能只看人数吗？'},
      'pipeline':{'adapter':'ck3-native-war-ai-v1','preset':'ck3-native-war-ai-longform-zh-v2'},
      'locales':{'narration':'zh-CN','subtitles':['zh-CN','en']},
      'constraints':{'duration_limit_seconds':1920},
      'chapters':[{'id':c['id'],'type':'documentary','state':'planned','title':{'zh-CN':c['title']},'cues':[],'artifact_ids':[]} for c in story['chapters']]}
    write(run/'project-config.json',config)
    command(run,'start-run',[sys.executable,'-m','xar_promo','start-run',str(run/'project-config.json'),'--run-id',run.name,'--run-directory',str(run/'native-run')])
    for target,name in [(run/'project-config.json','config'),(run/'native-run/run-manifest.json','run')]:
        command(run,'validate-'+name,[sys.executable,'-m','xar_promo','validate',str(target)])
    print(json.dumps({'run':str(run),'utterances':sum(len(c['utterances']) for c in story['chapters'])}))

def narrate_one(run,chapter,utterance,raw_only=False):
    key=f"{chapter['id']}-{utterance['id']}";root=run/'tts'/key;root.mkdir(parents=True,exist_ok=False)
    request=TtsRequest(utterance['zh'],voice='zh-CN-XiaoxiaoNeural',rate='-5%',cache_salt='episode02-story-a04')
    provider=EdgeTtsProvider();write(root/'request.json',{'provider':{'id':provider.identity.provider_id,'tool_version':provider.identity.tool_version},'request':request.cache_payload()})
    media=None
    for attempt in range(1,4):
        work=root/f'attempt-{attempt:02d}';work.mkdir();audio=work/'speech.mp3';begin=stamp()
        try:
            provider.synthesize(request,audio)
            if not audio.is_file() or audio.stat().st_size<512:raise RuntimeError('empty TTS output')
            write(work/'receipt.json',{'started_at_utc':begin,'finished_at_utc':stamp(),'status':'produced','media':ref(audio)})
            media=audio;break
        except Exception as e:
            write(work/'failure.json',{'started_at_utc':begin,'finished_at_utc':stamp(),'error':f'{type(e).__name__}: {e}','partial':ref(audio) if audio.is_file() else None})
            if attempt==3:raise
            time.sleep(attempt*2)
    draft={**utterance,'chapter':chapter['id'],'key':key,'tts_raw':ref(media)}
    write(root/'utterance-raw.json',draft)
    return draft if raw_only else trim_one(run,draft)

def trim_one(run,draft):
    key=draft['key'];root=run/'tts'/key;media=Path(draft['tts_raw']['path']);trimmed=root/'speech-trimmed.wav'
    # Trim only exterior silence. The two reversals retain all internal pauses.
    filt='silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB:start_silence=0.04,areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB:start_silence=0.04,areverse,apad=pad_dur=0.18'
    command(run,key+'-trim',[str(FFMPEG),'-hide_banner','-nostdin','-n','-i',str(media),'-af',filt,'-ar','48000','-ac','2','-c:a','pcm_s16le',str(trimmed)])
    info=probe(run,key+'-probe',trimmed);duration=float(info['format']['duration'])
    duration=math.ceil(duration*30)/30
    result={**draft,'audio':str(trimmed),'duration':duration,'tts_trimmed':ref(trimmed)}
    write(root/'utterance.json',result)
    return result

def narrate(run,raw_only=False):
    story=read(run/'sources/story.json');jobs=[(c,u) for c in story['chapters'] for u in c['utterances']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futures=[pool.submit(narrate_one,run,c,u,raw_only) for c,u in jobs]
        results=[f.result() for f in futures]
    if raw_only:
        write(run/'tts-raw-receipts.json',results);print(json.dumps({'raw_utterances':len(results),'postprocess_pending':True}));return
    timeline_from_audio(run,story,results)

def reuse_narration(run,previous):
    """Reuse only equal text/provider requests; changed sentences get new attempts."""
    story=read(run/'sources/story.json');old=read(previous/'tts-raw-receipts.json');bykey={r['key']:r for r in old};results=[]
    for chapter in story['chapters']:
        for u in chapter['utterances']:
            key=f"{chapter['id']}-{u['id']}";prior=bykey.get(key)
            if prior and prior['zh']==u['zh']:
                media=Path(prior['tts_raw']['path'])
                if ref(media)!=prior['tts_raw']:raise ValueError('reused TTS bytes changed')
                root=run/'tts'/key;root.mkdir(parents=True,exist_ok=False)
                request=read(previous/'tts'/key/'request.json')
                if request['request']['voice']!='zh-CN-XiaoxiaoNeural' or request['request']['rate']!='-5%':raise ValueError('reused provider policy changed')
                draft={**u,'chapter':chapter['id'],'key':key,'tts_raw':prior['tts_raw'],'reused_from':str(previous/'tts'/key/'utterance-raw.json')}
                write(root/'request.json',request);write(root/'utterance-raw.json',draft);results.append(draft)
            else:results.append(narrate_one(run,chapter,u,raw_only=True))
    write(run/'tts-raw-receipts.json',results);print(json.dumps({'raw_utterances':len(results),'reused':sum('reused_from' in r for r in results),'postprocess_pending':True}))

def finish_narration(run):
    story=read(run/'sources/story.json');drafts=read(run/'tts-raw-receipts.json')
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futures=[pool.submit(trim_one,run,d) for d in drafts];results=[f.result() for f in futures]
    timeline_from_audio(run,story,results)

def reuse_processed_narration(run,previous):
    """Bind unchanged Chinese narration bytes without re-trimming retained audio."""
    story=read(run/'sources/story.json');old=read(previous/'timeline.json')
    bykey={u['key']:u for c in old['chapters'] for u in c['utterances']};results=[]
    for chapter in story['chapters']:
        for u in chapter['utterances']:
            key=f"{chapter['id']}-{u['id']}";prior=bykey[key]
            if prior['zh']!=u['zh']:raise ValueError('Chinese text changed; fresh TTS required')
            for field in ['tts_raw','tts_trimmed']:
                if ref(prior[field]['path'])!=prior[field]:raise ValueError('prior audio bytes changed')
            root=run/'tts'/key;root.mkdir(parents=True,exist_ok=False)
            request=read(previous/'tts'/key/'request.json')
            if request['request']['voice']!='zh-CN-XiaoxiaoNeural' or request['request']['rate']!='-5%':raise ValueError('voice policy changed')
            r={**u,'chapter':chapter['id'],'key':key,'tts_raw':prior['tts_raw'],'tts_trimmed':prior['tts_trimmed'],'audio':prior['audio'],'duration':prior['duration'],'reused_processed_from':str(previous/'timeline.json')}
            write(root/'request.json',request);write(root/'utterance.json',r);results.append(r)
    write(run/'tts-raw-receipts.json',results);timeline_from_audio(run,story,results)

def timeline_from_audio(run,story,results):
    bykey={r['key']:r for r in results};timeline=[];global_start=0
    for c in story['chapters']:
        items=[];local=0
        for u in c['utterances']:
            r=dict(bykey[f"{c['id']}-{u['id']}"]);r['local_start']=local;r['global_start']=global_start+local;local+=r['duration'];items.append(r)
        timeline.append({'id':c['id'],'title':c['title'],'global_start':global_start,'duration':local,'utterances':items});global_start+=local
    report={'kind':'pending-human-review','human_signoff':'not-provided','production_clean_admission':False,'total_duration':global_start,'chapters':timeline,'voice':'zh-CN-XiaoxiaoNeural','rate':'-5%','chapter_tail_hold_seconds':0,'fps':30,'width':1920,'height':1080}
    write(run/'timeline.json',report);print(json.dumps({'duration':global_start,'utterances':len(results)}))

def at(t):return f'{int(t//3600)}:{int(t//60)%60:02d}:{t%60:05.2f}'
def ass_text(text,limit):
    if any(c in text for c in '{}'):raise ValueError('subtitle contains ASS control braces')
    lines=[]
    for line in text.splitlines():
        lines.extend(textwrap.wrap(line,width=limit,break_long_words=True,break_on_hyphens=False))
    return r'\N'.join(lines)
def subtitles(chapter,edit):
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Chinese,Microsoft YaHei,35,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00101010,0,0,0,0,100,100,0,0,1,1,0,8,110,110,0,1
Style: English,Arial,25,&H00C8C8C8,&H00FFFFFF,&H00101010,&H00101010,0,0,0,0,100,100,0,0,1,1,0,8,110,110,0,1
Style: Source,Microsoft YaHei,27,&H00E4DACA,&H00FFFFFF,&H80101010,&H80101010,0,0,0,0,100,100,0,0,3,8,0,7,32,32,20,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    rows=[]
    for u in chapter['utterances']:
        begin=at(u['local_start']);end=at(u['local_start']+u['duration'])
        for style,language,limit in [('Chinese','zh',40),('English','en',100)]:
            text=ass_text(u[language],limit)
            if text.count(r'\N')>1:raise ValueError(f"more than 2 subtitle lines: {u['key']} {language}")
            # Explicit top positions bypass libass collision relocation. All four
            # possible lines stay in the dedicated y900..1080 subtitle band.
            y=(910 if text.count(r'\N') else 935) if language=='zh' else (1008 if text.count(r'\N') else 1030)
            position=r'{\an8\pos(960,'+str(y)+')}'
            rows.append(f'Dialogue: 0,{begin},{end},{style},,0,0,0,,{position}{text}')
        shot=edit['utterances'][u['key']]
        if shot.get('kind')=='raw-excerpt' and shot.get('case'):
            rows.append(f'Dialogue: 1,{begin},{end},Source,,0,0,0,,{ass_text(shot["case"],60)}')
    return header+'\n'.join(rows)+'\n'

def render_chunk(run,chapter,edit,items,index):
    cid=chapter['id'];root=run/'chapters'/cid/f'chunk-{index:02d}';root.mkdir(parents=True,exist_ok=False)
    offset=items[0]['local_start'];duration=sum(u['duration'] for u in items)
    local=[{**u,'local_start':u['local_start']-offset} for u in items]
    ass=root/'subtitles.ass';text_once(ass,subtitles({**chapter,'utterances':local},edit))
    argv=[str(FFMPEG),'-hide_banner','-nostdin','-n'];filters=[]
    for i,u in enumerate(local):
        shot=edit['utterances'][u['key']];visual=Path(shot['image'])
        if shot.get('kind')=='raw-excerpt':
            argv+=['-threads','1','-ss',str(shot['start']),'-t',str(min(u['duration'],shot['source_duration'])),'-i',str(visual)]
            filters.append(f'[{i}:v]setpts=PTS-STARTPTS,scale=1920:900:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:0:color=0x0D141C,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration={u["duration"]},trim=duration={u["duration"]},format=yuv420p[v{i}]')
        else:
            argv+=['-threads','1','-loop','1','-framerate','30','-t',str(u['duration']),'-i',str(visual)]
            filters.append(f'[{i}:v]trim=duration={u["duration"]},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v{i}]')
    for u in local:argv+=['-i',u['audio']]
    n=len(local);filters.append(''.join(f'[v{i}]' for i in range(n))+f'concat=n={n}:v=1:a=0,'+ass_burn_in_filter(ass)+'[video]')
    for i,u in enumerate(local):filters.append(f'[{n+i}:a]apad,atrim=duration={u["duration"]},asetpts=PTS-STARTPTS[a{i}]')
    filters.append(''.join(f'[a{i}]' for i in range(n))+f'concat=n={n}:v=0:a=1[audio]')
    graph=root/'filter.txt';text_once(graph,';\n'.join(filters));out=root/'chunk.mp4'
    argv+=['-filter_complex_threads','2','-/filter_complex',str(graph),'-map','[video]','-map','[audio]','-t',str(duration),'-c:v','libx264','-preset','ultrafast','-crf','22','-threads','3','-r','30','-fps_mode','cfr','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart',str(out)]
    command(run,f'{cid}-chunk-{index:02d}-render',argv);return {**ref(out),'duration_expected':duration}

def render_chapter(run,chapter,edit):
    # Bound decoder input count: six parallel chapters, at most eight stills each.
    cid=chapter['id'];root=run/'chapters'/cid;root.mkdir(parents=True,exist_ok=False)
    items=chapter['utterances'];chunks=[]
    for index,begin in enumerate(range(0,len(items),8),1):chunks.append(render_chunk(run,chapter,edit,items[begin:begin+8],index))
    write(root/'chunk-receipts.json',chunks)
    concat=root/'concat.txt';text_once(concat,''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n" for r in chunks))
    out=root/'chapter.mp4'
    command(run,cid+'-chapter-join',[str(FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)])
    return {**ref(out),'duration_expected':chapter['duration']}

def render(run,edit_path):
    timeline=read(run/'timeline.json');edit=read(edit_path)
    if [c['id'] for c in timeline['chapters']] != ['opening','pursuit','knights','reinforcement','terminal','closing']:raise ValueError('full a04 requires original six chapters')
    if not 1620 <= timeline['total_duration'] <= 1920:raise ValueError(f"actual narration {timeline['total_duration']:.3f}s outside authorized 27-32min content range")
    if any(c['duration']<=0 for c in timeline['chapters']):raise ValueError('empty narrated chapter')
    for c in timeline['chapters']:
        for u in c['utterances']:
            shot=edit['utterances'][u['key']]
            if not Path(shot['image']).is_file():raise FileNotFoundError(shot['image'])
    shutil.copyfile(edit_path,run/'edit.json')
    stills=sorted(set(Path(s['image']) for s in edit['utterances'].values() if s.get('kind')!='raw-excerpt'))
    rawrefs=[s['source_binding'] for s in edit['utterances'].values() if s.get('kind')=='raw-excerpt']
    write(run/'edit-input-freeze.json',{'edit':ref(edit_path),'images':[ref(p) for p in stills],'raw_frozen_receipts':rawrefs,'raw_binding_method':'exact frozen source receipt plus current size; no repeated whole raw hash'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(render_chapter,run,c,edit) for c in timeline['chapters']];results=[f.result() for f in futures]
    write(run/'chapter-render-receipts.json',results)
    concat=run/'concat.txt';text_once(concat,''.join(f"file '{r['path'].replace(chr(92),'/')}'\n"+f"duration {r['duration_expected']:.9f}\n" for r in results))
    meta=run/'chapters.ffmetadata';lines=[';FFMETADATA1']
    for c in timeline['chapters']:lines.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["global_start"]*1000)}',f'END={round((c["global_start"]+c["duration"])*1000)}',f'title={c["title"]}'])
    text_once(meta,'\n'.join(lines)+'\n');out=run/'CK3-War-AI-Episode02-Review-20260930-a04.mp4'
    command(run,'final-join',[str(FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-f','ffmetadata','-i',str(meta),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(out)])
    report={**ref(out),'duration_expected':timeline['total_duration'],'human_signoff':'not-provided','status':'pending-independent-machine-check-and-frame-review'};write(run/'final-artifact.json',report);print(json.dumps(report))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','narrate','narrate-raw','reuse-narration','reuse-processed-narration','finish-narration','render']);p.add_argument('--run',required=True,type=Path);p.add_argument('--story',type=Path);p.add_argument('--environment',type=Path);p.add_argument('--edit',type=Path);p.add_argument('--previous',type=Path);a=p.parse_args()
    if a.phase=='prepare':prepare(a.run,a.story,a.environment)
    elif a.phase in ['narrate','narrate-raw']:narrate(a.run,a.phase=='narrate-raw')
    elif a.phase=='reuse-narration':reuse_narration(a.run,a.previous)
    elif a.phase=='reuse-processed-narration':reuse_processed_narration(a.run,a.previous)
    elif a.phase=='finish-narration':finish_narration(a.run)
    else:render(a.run,a.edit)
if __name__=='__main__':main()
