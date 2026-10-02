"""Project media preparation for the audited 177-cue war episode with series BGM.

Old runs stay immutable. Preparation uses the formal wheel, retained native
evidence and existing project renderers. CLI composition owns the final mix.
"""
from __future__ import annotations
import argparse, concurrent.futures, copy, importlib.metadata, json, shutil, sys
from pathlib import Path
import review_story_a04 as p
import compose_review_boards_a04 as b
import fix_evidence_label_a06 as notice
from compose_research_a08 import exact, require, bykey, ORDER, R148, R149

P=Path(__file__).resolve().parent
PREVIOUS=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-brown-gold-research-20261002-a02')
MUSIC=Path('D:/workspace/ck3_native_war_ai_promo_work/v5-theme-film-attempt-001/run/artifacts/raw/sha256/FD/FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F.wav')
OUTPUT='CK3-War-AI-Episode02-BrownGold-BGM-20261002-a09.mp4'

def prepare(run):
    require(not run.exists(),'Fresh run directory required');run.mkdir(parents=True)
    for name in ('logs','sources','audit'):(run/name).mkdir()
    env=p.read(PREVIOUS/'sources/environment.json');wheel=exact(env['wheel'])
    latest=p.read(p.command(run,'latest-formal-release',['gh','release','view','--repo','XenoAmess/xar_promo_toolchain','--json','tagName,name,publishedAt,url,assets,isDraft,isPrerelease']))
    version=importlib.metadata.version('xar-promo-toolchain')
    require(not latest['isDraft'] and not latest['isPrerelease'] and latest['tagName'].lstrip('v')==version,'Latest formal wheel required')
    asset=next(a for a in latest['assets'] if a['name']==Path(wheel['path']).name)
    require(asset['digest'].split(':')[-1].upper()==wheel['sha256'],'Formal wheel hash differs')
    direct=json.loads(importlib.metadata.distribution('xar-promo-toolchain').read_text('direct_url.json'))
    require(direct['archive_info']['hashes']['sha256'].upper()==wheel['sha256'],'Installed wheel provenance differs')
    branch=p.command(run,'private-branch',['git','-C',str(P),'branch','--show-current']).read_text().strip()
    require(branch=='codex/war-series-brown-gold-20261001','Independent branch required')
    head=p.command(run,'source-head',['git','-C',str(P),'rev-parse','HEAD']).read_text().strip()
    p.write(run/'sources/environment.json',{'at_utc':p.stamp(),'python':sys.executable,'python_version':sys.version,'promo_version':version,'wheel':wheel,'installed_wheel_provenance':direct,'latest_release':latest,'branch':branch,'source_head':head,'main_venv_explicitly_selected':True,'no_master_intake':True,'pillow_version':importlib.metadata.version('Pillow'),'edge_tts_version':importlib.metadata.version('edge-tts')})
    for name,args in [('version',['--version']),('help',['--help']),('start-help',['start-run','--help']),('plan-help',['plan','--help']),('build-help',['build','--help']),('audit-help',['audit','--help']),('review-help',['review','--help']),('preserve-help',['preserve','--help'])]:p.command(run,'toolchain-'+name,[sys.executable,'-X','utf8','-m','xar_promo',*args])
    story_path=P/'project/review-story-a09-story.json';config=P/'project/review-story-a09-project.json';story=p.read(story_path)
    require([c['id'] for c in story['chapters']]==ORDER and len(bykey(story))==177,'Full audited 177-cue coverage required')
    for key,u in bykey(story).items():
        for lang,limit in [('zh',40),('en',100)]:require(p.ass_text(u[lang],limit).count(r'\N')<=1,'Subtitle overflow: '+key)
        require(u['facts'] and all(Path(f['source_path']).is_file() for f in u['facts']),'Missing original evidence: '+key)
    music=exact({'path':str(MUSIC),'bytes':30726160,'sha256':'FDA2464FB4B06CD9A2F0196E5C40CA311EB693EC263C996E4CCC24A6ADA8803F'})
    p.write(run/'music-policy.json',{'title':'Quiet Courtly Tension','source':music,'policy':'single existing war-series theme throughout; narration 0dB; music -17dB; same original loop; 2s fade in / 8s fade out; no normalization','reference_build':p.ref(P.parent/'build-records/v5-theme-fullfilm-20260924-r1.json'),'human_listening_signoff':'not-provided'})
    files=[(story_path,'story.json'),(config,'project-config.json'),(Path(__file__),'composer-source.py'),(Path(p.__file__),'producer-source.py'),(Path(b.__file__),'board-source.py'),(Path(notice.__file__),'notice-source.py'),(P/'boards_copy_a09.py','boards-copy-source.py'),(P/'native_mix_a09.py','native-mix-source.py')]
    for src,name in files:shutil.copyfile(src,run/'sources'/name)
    shutil.copyfile(config,run/'project-config.json');shutil.copyfile(story_path,run/'claim-catalog.json')
    p.write(run/'input-freeze.json',[p.ref(src) for src,name in files]+[p.ref(PREVIOUS/'timeline.json'),p.ref(PREVIOUS/'edit.json'),music])
    p.command(run,'start-run',[sys.executable,'-X','utf8','-m','xar_promo','start-run',str(run/'project-config.json'),'--run-id',run.name,'--run-directory',str(run/'native-run')])
    validate(run,'prepared')
    print(json.dumps({'status':'PREPARED','run':str(run),'promo_version':version,'cues':177,'music_sha256':music['sha256']}),flush=True)

def validate(run,name):
    for doc,label in [(run/'project-config.json','config'),(run/'native-run/run-manifest.json','run')]:p.command(run,'validate-'+name+'-'+label,[sys.executable,'-X','utf8','-m','xar_promo','validate',str(doc)])

def narrate(run):
    story=p.read(run/'sources/story.json');old=bykey(p.read(PREVIOUS/'timeline.json'));results=[];jobs=[]
    for c in story['chapters']:
        for u in c['utterances']:
            key=c['id']+'-'+u['id'];prior=old.get(key)
            if prior is None or prior['zh']!=u['zh']:jobs.append((c,u));continue
            for field in ('tts_raw','tts_trimmed'):exact(prior[field])
            request=p.read(PREVIOUS/'tts'/key/'request.json')
            require(request['request']['voice']=='zh-CN-XiaoxiaoNeural' and request['request']['rate']=='-5%','Retained voice differs')
            root=run/'tts'/key;root.mkdir(parents=True,exist_ok=False)
            result={**u,'chapter':c['id'],'key':key,'tts_raw':prior['tts_raw'],'tts_trimmed':prior['tts_trimmed'],'audio':prior['audio'],'duration':prior['duration'],'reused_processed_from':str(PREVIOUS/'timeline.json')}
            p.write(root/'request.json',request);p.write(root/'utterance.json',result);results.append(result)
    p.write(run/'fresh-tts-plan.json',{'fresh_keys':[c['id']+'-'+u['id'] for c,u in jobs],'fresh':len(jobs),'retained_verified_audio':len(results),'voice':'zh-CN-XiaoxiaoNeural','rate':'-5%'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(p.narrate_one,run,c,u) for c,u in jobs]
        for f in concurrent.futures.as_completed(futures):
            result=f.result();results.append(result);print(json.dumps({'new_tts':result['key'],'seconds':result['duration']}),flush=True)
    p.write(run/'tts-raw-receipts.json',results);p.timeline_from_audio(run,story,results)

def render(run):
    timeline=p.read(run/'timeline.json');edit=p.read(run/'edit.json');old=bykey(p.read(PREVIOUS/'timeline.json'));oldedit=p.read(PREVIOUS/'edit.json')
    require(1620<=timeline['total_duration']<=1920,'Measured narration outside project 27-32 minute budget')
    require(not (run/'chapters').exists(),'Fresh render attempt required')
    tasks=[]
    for c in timeline['chapters']:
        for i,start in enumerate(range(0,len(c['utterances']),8),1):
            items=c['utterances'][start:start+8];offset=items[0]['local_start'];local=[{**u,'local_start':u['local_start']-offset} for u in items]
            path=PREVIOUS/'chapters'/c['id']/f'chunk-{i:02d}'
            same=all(u['key'] in old and all(u[field]==old[u['key']][field] for field in ('zh','en','tts_trimmed','duration')) and edit['utterances'][u['key']]==oldedit['utterances'][u['key']] for u in items)
            same=same and (path/'subtitles.ass').is_file() and p.subtitles({**c,'utterances':local},edit).encode('utf-8')==(path/'subtitles.ass').read_bytes()
            tasks.append((c,i,items,path,same))
    p.write(run/'chunk-plan.json',[{'chapter':c['id'],'chunk':i,'keys':[u['key'] for u in items],'action':'exact-byte-copy' if same else 'fresh-render'} for c,i,items,path,same in tasks])
    def one(task):
        c,i,items,path,same=task;target=run/'chapters'/c['id']/f'chunk-{i:02d}'
        if same:
            pin=p.ref(path/'chunk.mp4');shutil.copytree(path,target);r={**p.ref(target/'chunk.mp4'),'duration_expected':sum(u['duration'] for u in items),'previous':pin};require(r['sha256']==pin['sha256'],'Copied chunk differs')
        else:
            renderer=notice.render_chunk_with_notice if any(edit['utterances'][u['key']].get('raw_notice_inset') for u in items) else p.render_chunk
            r=renderer(run,c,edit,items,i)
        print(json.dumps({'chunk':c['id']+'-'+str(i),'action':'copied' if same else 'rendered'}),flush=True);return c['id'],i,r
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,tasks))
    lookup={(c,i):r for c,i,r in results};chapters=[]
    for c in timeline['chapters']:
        root=run/'chapters'/c['id'];chunks=[lookup[c['id'],i] for cc,i,items,path,same in tasks if cc['id']==c['id']]
        p.write(root/'chunk-receipts.json',chunks);p.text_once(root/'concat.txt',''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n" for r in chunks));out=root/'chapter.mp4'
        p.command(run,c['id']+'-join',[str(p.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(root/'concat.txt'),'-c','copy','-movflags','+faststart',str(out)]);chapters.append({**p.ref(out),'duration_expected':c['duration']})
    p.write(run/'chapter-render-receipts.json',chapters);p.text_once(run/'concat.txt',''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n" for r in chapters))
    lines=[';FFMETADATA1']
    for c in timeline['chapters']:lines.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["global_start"]*1000)}',f'END={round((c["global_start"]+c["duration"])*1000)}',f'title={c["title"]}'])
    p.text_once(run/'chapters.ffmetadata','\n'.join(lines)+'\n');out=run/'dry-master.mp4'
    p.command(run,'dry-final-join',[str(p.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(run/'concat.txt'),'-f','ffmetadata','-i',str(run/'chapters.ffmetadata'),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(out)])
    p.write(run/'dry-master.json',{**p.ref(out),'duration_expected':timeline['total_duration'],'human_signoff':'not-provided','music':False,'cue_count':177})
    print(json.dumps({'dry_master':str(out),'duration':timeline['total_duration']}),flush=True)

def main():
    a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','narrate','boards','render']);a.add_argument('--run',type=Path,required=True);args=a.parse_args()
    if args.phase=='boards':
        from boards_copy_a09 import make_boards
        make_boards(args.run)
    else:{'prepare':prepare,'narrate':narrate,'render':render}[args.phase](args.run)
if __name__=='__main__':main()
