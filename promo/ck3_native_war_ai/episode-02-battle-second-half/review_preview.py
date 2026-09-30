"""Independent pending-review Episode 2 preview; never certifies production reels.

Uses immutable existing EdgeTTS audio, new reviewed subtitle mappings, candidate
raw windows, and existing calculation SVGs. No game or desktop interaction.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, importlib.metadata, json, os
from pathlib import Path
import shutil, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WORK = Path('D:/workspace/ck3_native_war_ai_promo_work')
DEFAULT_RUN = Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-20260930-a01')
FFBIN = Path('C:/Users/1/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin')
FONT = Path('C:/Windows/Fonts/msyh.ttc')
BG, INK, GOLD, MUTED = '#211813', '#F0E5CF', '#CBA56A', '#BBA98D'
CHAPTERS = ['opening','pursuit','knights','reinforcement','terminal','closing']
TITLES = ['开场与前情','追击三日','骑士事件','增援入账','终局与战分','结语与边界']
SPEECH = [77.808,268.992,328.752,332.712,269.232,88.056]
AUDIO_REL = [
 'episode02-a05-narration-20260928-a01/opening-render/opening/chapter-speech.mp3',
 'episode02-a05-current-count-tts-20260930-a01/render/pursuit/chapter-speech.mp3',
 'episode02-full-narration-20260928-a02/render/knights/chapter-speech.mp3',
 'episode02-final-narration-20260928-a01/reinforcement-render/reinforcement/chapter-speech.mp3',
 'episode02-final-narration-20260928-a01/terminal-render/terminal/chapter-speech.mp3',
 'episode02-final-narration-20260928-a01/terminal-render/closing/chapter-speech.mp3']
RAW = {
 'p': WORK/'episode02-e2-02-03-live-20260928-a01/recording-e2-02-03-a01/raw/e2-pursuit-d27-d32.mkv',
 'a1': WORK/'episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a01/raw/e2-09-terminal-a01.mkv',
 'a2': WORK/'episode02-terminal-pair-20260928-a05-live/recording-e2-09-terminal-a02/raw/e2-09-terminal-a02.mkv',
 'k4': WORK/'episode02-e2-04-d05-live-20260929-a07/recording-e2-04-d05-a07/raw/e2-04-d05.mkv',
 'j': WORK/'episode02-e2-06-d11-live-20260928-a01/recording-e2-06-d11-a01/raw/e2-06-d11.mkv'}
CARDS = ['e2-02-a05-calculation','e2-03-a05-calculation','e2-04-calculation',
 'e2-05a-calculation','e2-05b-calculation','e2-05c-calculation',
 'e2-06-a01-calculation','e2-07-a01-calculation','e2-09-a05-calculation']

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False,indent=2)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest().upper()

def command(run, name, argv):
    log = run/'logs'/name
    log.parent.mkdir(parents=True,exist_ok=True)
    for suffix in range(1,100):
        if not log.with_suffix('.argv.json').exists():break
        log=run/'logs'/f'{name}-a{suffix+1:02d}'
    write_json(log.with_suffix('.argv.json'),argv)
    start=time.monotonic()
    with log.with_suffix('.stdout.txt').open('xb') as out, log.with_suffix('.stderr.txt').open('xb') as err:
        p=subprocess.run(argv,stdout=out,stderr=err)
    receipt={'argv':argv,'exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start}
    write_json(log.with_suffix('.receipt.json'),receipt)
    if p.returncode: raise RuntimeError(f'{name}: exit {p.returncode}; see {log}.stderr.txt')
    return receipt

def title(path, heading, lines=(), eyebrow='战斗后半笔账', footer=''):
    im=Image.new('RGB',(1920,1080),BG); d=ImageDraw.Draw(im)
    d.line((65,55,1855,55),fill=GOLD,width=2)
    d.text((90,92),eyebrow,font=ImageFont.truetype(str(FONT),30),fill=GOLD)
    d.text((90,205),heading,font=ImageFont.truetype(str(FONT),65),fill=INK)
    y=385
    for line in lines:
        d.text((95,y),line,font=ImageFont.truetype(str(FONT),37),fill=MUTED);y+=85
    if footer:d.text((95,805),footer,font=ImageFont.truetype(str(FONT),30),fill=GOLD)
    d.line((0,870,1920,870),fill=GOLD,width=2)
    im.save(path)

def raster_svg(source, dest, historical=False):
    """Render simple checked-in SVG primitives with Pillow, omitting audit footers.

    Original SVG is preserved unchanged; machine receipt hashes stay in manifest.
    """
    im=Image.new('RGB',(2560,1440),BG);d=ImageDraw.Draw(im)
    for e in ET.parse(source).getroot():
        tag=e.tag.split('}')[-1];a=e.attrib
        def n(k,default=0):return float(a.get(k,default))
        if tag=='rect':
            box=(n('x'),n('y'),n('x')+n('width'),n('y')+n('height'))
            d.rounded_rectangle(box,radius=n('rx'),fill=a.get('fill'),outline=a.get('stroke'),width=int(n('stroke-width',1)))
        elif tag=='line':
            d.line((n('x1'),n('y1'),n('x2'),n('y2')),fill=a.get('stroke'),width=int(n('stroke-width',1)))
        elif tag=='text':
            text=''.join(e.itertext())
            if 'SHA-256' in text or 'CombatID' in text:continue
            if historical and n('y')==105 and a.get('text-anchor')=='end':text='历史案例 · 独立回放'
            f=ImageFont.truetype(str(FONT),int(n('font-size',32)))
            x=n('x')-(d.textlength(text,font=f) if a.get('text-anchor')=='end' else 0)
            d.text((x,n('y')),text,font=f,fill=a.get('fill',INK),anchor='ls')
    im.resize((1920,1080),Image.Resampling.LANCZOS).save(dest)

def prepare(run):
    run.mkdir(parents=True,exist_ok=False)
    assets=run/'assets';assets.mkdir()
    sources=run/'sources';sources.mkdir()
    source_groups=WORK/'episode02-a05-current-count-tts-20260930-a01/source-groups.json'
    base=WORK/'episode02-a05-current-count-tts-20260930-a01'
    preserve=[source_groups,base/'render/snapshot-draft.md',base/'subtitle-preflight/subtitle-input-fragments.json',
      base/'assembly-source-run/artifacts/raw/sha256/AC/ACDE81AE16D1DB589B605EC1FEC50457EF5E6BA30FF395B86CF6F5DE31F7B559.json']
    records=[]
    for i,p in enumerate(preserve):
        target=sources/f'{i:02d}-{p.name}';shutil.copyfile(p,target)
        records.append({'path':str(p),'snapshot':str(target),'sha256':sha(target)})
    for c in CARDS:
        p=ROOT/'cards'/f'{c}.svg';copy=sources/p.name;shutil.copyfile(p,copy)
        raster_svg(copy,assets/f'{c}.png',historical=c in CARDS[2:6])
        records.append({'path':str(p),'snapshot':str(copy),'sha256':sha(copy)})
    title(assets/'opening.png','战斗后半笔账', ['从追击、骑士事件，到增援与终局战分。','同一场战斗，逐段看清不同的账。'],eyebrow='CK3 原生战争机制 · 审阅稿')
    title(assets/'pursuit.png','追击：软伤怎样变成硬损失',['第 28 日输入 → 三日写回 → 面板读数','请留意人数、软伤池和真实阵亡的区别。'])
    title(assets/'knights.png','骑士事件：人与属性各有一笔账',['本章数字来自历史案例，分别展示独立回放。','骑士人数未变，并不意味着下一帧属性未变。'],footer='历史案例')
    title(assets/'reinforcement.png','增援：入场人数不等于立刻出伤',['先对齐参战账，再追到战宽和首次出伤。','关键入场对照镜头：此处待补拍。'])
    title(assets/'terminal.png','终局：战斗结果怎样进入战争账',['损失分子、八桶分母、系数与封顶。','清晰的终局结果面板：此处待补拍。'])
    title(assets/'closing.png','这一次，我们把后半笔账拆开看',['追击：软转硬，不只盯住面板人数。','骑士：事件、属性、名单分别核对。','增援与终局：先入账，再看下一步写回。'])
    title(assets/'closing-boundary.png','还有哪些画面需要补齐？',['增援关键对照与清晰终局镜头。','历史案例分别呈现，避免混成同一条因果链。','审阅重点：叙事、配音、字幕与剪辑节奏。'])
    for cid,t in zip(CHAPTERS,TITLES):title(assets/f'{cid}-end.png',t,['下一章继续这笔账。'] if cid!='closing' else ['感谢观看。'],eyebrow='战斗后半笔账')
    latest=json.load(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest',headers={'User-Agent':'ck3-review-preview'}),timeout=20))
    wheel=next(a for a in latest['assets'] if a['name'].endswith('.whl'))
    version=importlib.metadata.version('xar-promo-toolchain')
    if latest['tag_name'].lstrip('v')!=version:raise RuntimeError('installed wheel is not latest formal release')
    write_json(run/'environment.json',{'python':sys.executable,'python_version':sys.version,'wheel_version':version,'latest_release':latest['html_url'],'wheel_url':wheel['browser_download_url'],'wheel_sha256':wheel.get('digest'),'ffmpeg':str(FFBIN/'ffmpeg.exe'),'no_game_or_desktop':True})
    command(run,'promo-version',[sys.executable,'-m','xar_promo','--version'])
    command(run,'promo-help',[sys.executable,'-m','xar_promo','--help'])
    command(run,'promo-start-run-help',[sys.executable,'-m','xar_promo','start-run','--help'])
    command(run,'promo-build-help',[sys.executable,'-m','xar_promo','build','--help'])
    write_json(run/'source-freeze.json',records)
    config=json.loads((ROOT/'project/promo-project.json').read_text(encoding='utf-8-sig'))
    config['project']['id']='ck3-war-ai-episode02-review-preview'
    config['project']['title']='CK3 原生战争机制：战斗后半笔账（审阅稿）'
    write_json(run/'project-config.json',config)
    command(run,'start-run',[sys.executable,'-m','xar_promo','start-run',str(run/'project-config.json'),'--run-id','episode02-review-preview-20260930-a01','--run-directory',str(run/'native-run')])

def plan(run):
    a=run/'assets'
    def still(name,duration,kind='illustration'):return {'path':str(a/f'{name}.png'),'duration':duration,'kind':kind}
    def raw(key,start,duration,label=''):return {'path':str(RAW[key]),'start':start,'duration':duration,'kind':'candidate-raw','label':label,'clean':False}
    tracks=[
      [still('opening',12),raw('p',30,40,'独立前情画面'),still('opening',25.808),still('opening',8,'identity-reading-hold'),still('opening-end',2)],
      [raw('a1',350,50),still(CARDS[0],48.448,'calculation-card'),raw('a2',60,60),still(CARDS[1],110.544,'calculation-card'),still(CARDS[0],14,'reading-hold'),still(CARDS[1],22,'reading-hold'),still('pursuit-end',2)],
      [raw('k4',30,40,'当前骑士界面示意；历史案例镜头待补拍'),still(CARDS[2],88.232,'historical-card'),still(CARDS[3],102.432,'historical-card'),still(CARDS[4],24.24716075,'historical-card'),still(CARDS[5],73.84083925,'historical-card')]+[still(c,d,'reading-hold') for c,d in zip(CARDS[2:6],[16,8,8,8])]+[still('knights-end',2)],
      [still('reinforcement',40),raw('j',200,55,'A01 · 增援界面示意'),still(CARDS[6],101.584,'calculation-card'),still(CARDS[7],76.128,'calculation-card'),raw('j',350,60,'A01 · 增援界面示意'),still(CARDS[6],30,'reading-hold'),still(CARDS[7],24,'reading-hold'),still('reinforcement-end',2)],
      [raw('a1',245,24.967,'A05 · 终局前战争面板'),still('terminal',18.449),still(CARDS[8],225.816,'calculation-card'),still('terminal',12,'result-reading-hold'),still(CARDS[8],32,'reading-hold'),still('terminal-end',2)],
      [still('closing',30),raw('p',90,20,'独立前情画面'),still('closing-boundary',38.056),still('closing-end',2)]
    ]
    result=[];offset=0
    for i,(cid,clips) in enumerate(zip(CHAPTERS,tracks)):
        local=0
        for clip in clips:clip['local_start']=local;clip['global_start']=offset+local;local+=clip['duration']
        result.append({'id':cid,'title':TITLES[i],'global_start':offset,'duration':local,'speech_duration':SPEECH[i],'audio':str(WORK/AUDIO_REL[i]),'clips':clips})
        offset+=local
    return {'kind':'pending-human-review-preview','human_review':'not-provided','production_clean_admission':False,'width':1920,'height':1080,'fps':30,'total_duration':offset,'chapters':result}

def render_chapter(run, chapter, ass=None, trial=False, video_only=False):
    clips=chapter['clips'];limit=20 if trial else chapter['duration']
    if trial:clips=[dict(clips[0],duration=min(12,limit)),dict(clips[1],duration=8)]
    out=run/('trial.mp4' if trial else f"video-tracks/{chapter['id']}.mp4" if video_only else f"chapters/{chapter['id']}.mp4")
    out.parent.mkdir(exist_ok=True)
    argv=[str(FFBIN/'ffmpeg.exe'),'-hide_banner','-nostdin','-n']
    for c in clips:
        if c['kind']=='candidate-raw':argv+=['-threads','1','-ss',str(c['start']),'-t',str(c['duration']),'-i',c['path']]
        else:argv+=['-threads','1','-loop','1','-framerate','30','-t',str(c['duration']),'-i',c['path']]
    if not video_only:argv+=['-i',chapter['audio']]
    filters=[]
    for i,c in enumerate(clips):
        f=f'[{i}:v]setpts=PTS-STARTPTS,'
        if c['kind']=='candidate-raw':
            f+='scale=1600:900,pad=1920:1080:160:0:color=0x211813,'
        f+=f'setsar=1,format=yuv420p[v{i}]';filters.append(f)
    f=''.join(f'[v{i}]' for i in range(len(clips)))+f'concat=n={len(clips)}:v=1:a=0'
    if ass:
        escaped=str(ass).replace('\\','/').replace(':','\\:')
        f+=f",ass=filename='{escaped}'"
    f+='[video]';filters.append(f)
    if not video_only:filters.append(f'[{len(clips)}:a]apad,atrim=duration={limit},asetpts=PTS-STARTPTS[audio]')
    filterfile=run/'filters'/('trial.txt' if trial else chapter['id']+'.txt');filterfile.parent.mkdir(exist_ok=True)
    original_filter=filterfile
    for suffix in range(2,100):
        if not filterfile.exists():break
        filterfile=original_filter.with_name(original_filter.stem+f'-a{suffix:02d}.txt')
    if out.exists():out=out.with_name(out.stem+'-a02.mp4')
    with filterfile.open('x',encoding='utf-8') as f:f.write(';\n'.join(filters))
    argv+=['-filter_complex_threads','2','-/filter_complex',str(filterfile),'-map','[video]']
    if not video_only:argv+=['-map','[audio]','-c:a','aac','-b:a','160k','-ar','48000','-ac','2']
    argv+=['-t',str(limit),'-c:v','libx264','-preset','ultrafast','-crf','23','-threads','3','-fps_mode','passthrough','-movflags','+faststart',str(out)]
    receipt=command(run,'trial-render' if trial else chapter['id']+'-video' if video_only else chapter['id']+'-render',argv)
    return {'path':str(out),'duration':limit,'elapsed_seconds':receipt['elapsed_seconds'],'speed':limit/receipt['elapsed_seconds']}

def compose(*, run_directory=None, **kwargs):
    """Actual project composer entry, explicit preview only; CLI handles concrete run.

    Production project composers and their reel gates remain unchanged.
    """
    if run_directory is None:raise ValueError('explicit preview run_directory required')
    return plan(Path(run_directory))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','plan','trial','video','render','correct','join']);p.add_argument('--run',type=Path,default=DEFAULT_RUN);p.add_argument('--ass-dir',type=Path);p.add_argument('--chapters',default='pursuit,knights,reinforcement,terminal');args=p.parse_args();run=args.run
    if args.phase=='prepare':
        prepare(run);write_json(run/'timeline.json',plan(run));print(run);return
    if args.phase=='plan':
        for version in range(2,100):
            target=run/f'timeline-v{version}.json'
            if not target.exists():write_json(target,plan(run));print(target);return
        raise RuntimeError('timeline version space exhausted')
    versions=sorted(run.glob('timeline-v*.json'),key=lambda p:int(p.stem.split('-v')[-1]))
    timeline=json.loads((versions[-1] if versions else run/'timeline.json').read_text(encoding='utf-8'))
    if args.phase=='trial':
        c=timeline['chapters'][0];ass=args.ass_dir/'opening.ass' if args.ass_dir else WORK/'episode02-a05-current-count-tts-20260930-a01/provisional-subtitles/opening-provisional-card-layout.ass'
        result=render_chapter(run,c,ass,trial=True);write_json(run/'trial-receipt.json',result);print(json.dumps(result));return
    if args.phase in ['render','correct']:
        if not args.ass_dir:raise ValueError('new aligned ASS required for full review preview')
        preserved=run/('subtitles-a02' if args.phase=='correct' else 'subtitles')
        if preserved.exists():preserved=run/'subtitles-a03'
        preserved.mkdir()
        for c in timeline['chapters']:
            cid=c['id'];source=args.ass_dir/f'{cid}-aligned-review.ass'
            text=source.read_text(encoding='utf-8-sig')
            text=text.replace('[Events]','Style: Illustration,Microsoft YaHei,24,&H006AA5CB,&H006AA5CB,&H00131821,&H00131821,0,0,0,0,100,100,0,0,1,2,0,7,170,50,15,1\n\n[Events]')
            def at(s):return f'{int(s//3600)}:{int(s//60)%60:02d}:{s%60:05.2f}'
            for clip in c['clips']:
                if clip.get('label'):text+=f"\nDialogue: 3,{at(clip['local_start'])},{at(clip['local_start']+clip['duration'])},Illustration,,0,0,0,,{clip['label']}\n"
            with (preserved/f'{cid}.ass').open('x',encoding='utf-8') as f:f.write(text)
        write_json(run/(preserved.name+'-freeze.json'),[{'path':str(p),'sha256':sha(p)} for p in preserved.glob('*.ass')])
        def finish(c):
            video=run/'video-tracks'/f"{c['id']}.mp4"
            alternate=video.with_name(video.stem+'-a02.mp4')
            if alternate.exists():video=alternate
            if not video.exists():return render_chapter(run,c,preserved/f"{c['id']}.ass")
            out=run/'chapters'/f"{c['id']}.mp4";out.parent.mkdir(exist_ok=True)
            ass=str(preserved/f"{c['id']}.ass").replace('\\','/').replace(':','\\:')
            receipt=command(run,c['id']+'-subtitle-render',[str(FFBIN/'ffmpeg.exe'),'-hide_banner','-nostdin','-n','-threads','1','-i',str(video),'-i',c['audio'],'-vf',f"ass=filename='{ass}'",'-af',f"apad,atrim=duration={c['duration']}",'-t',str(c['duration']),'-c:v','libx264','-preset','ultrafast','-crf','23','-threads','3','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-fps_mode','passthrough','-movflags','+faststart',str(out)])
            return {'path':str(out),'elapsed_seconds':receipt['elapsed_seconds'],'duration':c['duration']}
        selected=[c for c in timeline['chapters'] if args.phase!='correct' or c['id'] in args.chapters.split(',')]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures=[pool.submit(render_chapter,run,c,preserved/f"{c['id']}.ass") if args.phase=='correct' else pool.submit(finish,c) for c in selected]
            results=[f.result() for f in futures]
        write_json(run/('corrected-chapter-render-receipts.json' if args.phase=='correct' else 'chapter-render-receipts.json'),results);print(json.dumps(results));return
    if args.phase=='video':
        def video_job(c):
            receipt=run/'logs'/f"{c['id']}-video.receipt.json"
            if receipt.exists() and json.loads(receipt.read_text())['exit_code']==0:
                return {'path':str(run/'video-tracks'/f"{c['id']}.mp4"),'reused_success':True}
            return render_chapter(run,c,video_only=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(video_job,timeline['chapters']))
        write_json(run/'video-render-receipts.json',results);print(json.dumps(results));return
    revised=(run/'timeline-v3.json').exists()
    concat=run/('concat-a02.txt' if revised else 'concat.txt')
    with concat.open('x',encoding='utf-8') as f:
        for c in timeline['chapters']:
            part=run/'chapters'/(c['id']+'.mp4');alternate=part.with_name(part.stem+'-a02.mp4')
            if alternate.exists():part=alternate
            f.write(f"file '{part.as_posix()}'\n")
    meta=run/('chapters-a02.ffmetadata' if revised else 'chapters.ffmetadata')
    with meta.open('x',encoding='utf-8') as f:
        f.write(';FFMETADATA1\n')
        for c in timeline['chapters']:
            f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['global_start']*1000)}\nEND={round((c['global_start']+c['duration'])*1000)}\ntitle={c['title']}\n")
    out=run/('CK3-War-AI-Episode02-Review-20260930-a02.mp4' if revised else 'CK3-War-AI-Episode02-Review-20260930-a01.mp4')
    command(run,'final-join',[str(FFBIN/'ffmpeg.exe'),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-f','ffmetadata','-i',str(meta),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(out)])
    write_json(run/('final-artifact-a02.json' if revised else 'final-artifact.json'),{'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out),'human_review':'not-provided','status':'pending-machine-validation-and-human-review','duration_expected':timeline['total_duration']})
    print(out)

if __name__=='__main__':main()
