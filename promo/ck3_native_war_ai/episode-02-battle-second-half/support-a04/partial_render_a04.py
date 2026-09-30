"""Re-encode two changed visual chunks; retain and bind all other exact bytes."""
from pathlib import Path
import importlib.util,json,shutil,concurrent.futures
ROOT=Path(__file__).resolve().parent
PRODUCER=Path('C:/w/ep2a04/promo/ck3_native_war_ai/episode-02-battle-second-half/review_story_a04.py')
spec=importlib.util.spec_from_file_location('producer_a04',PRODUCER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PREVIOUS=Path('C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a03');RUN=PREVIOUS.with_name('episode02-review-20260930-a04-a04')
timeline=m.read(RUN/'timeline.json');edit_path=ROOT/'edit-final-v2.json';edit=m.read(edit_path)
if [c['id'] for c in timeline['chapters']]!=['opening','pursuit','knights','reinforcement','terminal','closing'] or not 1620<=timeline['total_duration']<=1920:raise ValueError('complete film guard failed')
shutil.copyfile(__file__,RUN/'sources/partial-render-source.py');shutil.copyfile(edit_path,RUN/'edit.json')
m.write(RUN/'edit-input-freeze.json',{'edit':m.ref(edit_path),'images':[m.ref(Path(s['image'])) for s in edit['utterances'].values() if s['kind']!='raw-excerpt'],'raw_frozen_receipts':[s['source_binding'] for s in edit['utterances'].values() if s['kind']=='raw-excerpt'],'previous':m.ref(PREVIOUS/'final-artifact.json'),'visual_change_keys':['terminal-t031','closing-c004'],'narration_and_timing_unchanged':True})
changed={('terminal',4),('closing',1)};reused=[]
for c in timeline['chapters']:
    cid=c['id'];target=RUN/'chapters'/cid;target.mkdir(parents=True,exist_ok=False)
    for chunk in sorted((PREVIOUS/'chapters'/cid).glob('chunk-*')):
        if not chunk.is_dir():continue
        number=int(chunk.name.split('-')[-1])
        if (cid,number) in changed:continue
        shutil.copytree(chunk,target/chunk.name)
        reused.append({'chapter':cid,'chunk':number,'origin':m.ref(chunk/'chunk.mp4'),'copy':m.ref(target/chunk.name/'chunk.mp4'),'ass_origin':m.ref(chunk/'subtitles.ass')})
jobs=[]
for cid,index in sorted(changed):
    c=next(c for c in timeline['chapters'] if c['id']==cid);items=c['utterances'][(index-1)*8:index*8];jobs.append((c,items,index))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(m.render_chunk,RUN,c,edit,items,index) for c,items,index in jobs]
    fresh=[f.result() for f in futures]
m.write(RUN/'changed-chunk-render-receipts.json',fresh);m.write(RUN/'reused-chunk-receipts.json',reused)
results=[]
for c in timeline['chapters']:
    cid=c['id'];target=RUN/'chapters'/cid;chunks=[]
    for index,begin in enumerate(range(0,len(c['utterances']),8),1):
        path=target/f'chunk-{index:02d}'/'chunk.mp4';chunks.append({**m.ref(path),'duration_expected':sum(u['duration'] for u in c['utterances'][begin:begin+8]),'reused':(cid,index) not in changed,'previous_origin':str(PREVIOUS/'chapters'/cid/f'chunk-{index:02d}'/'chunk.mp4') if (cid,index) not in changed else None})
    m.write(target/'chunk-receipts.json',chunks)
    concat=target/'concat.txt';m.text_once(concat,''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n" for r in chunks));out=target/'chapter.mp4'
    m.command(RUN,cid+'-chapter-join',[str(m.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(out)])
    results.append({**m.ref(out),'duration_expected':c['duration']})
m.write(RUN/'chapter-render-receipts.json',results)
concat=RUN/'concat.txt';m.text_once(concat,''.join("file '"+r['path'].replace(chr(92),'/')+"'\n"+f"duration {r['duration_expected']:.9f}\n" for r in results));meta=RUN/'chapters.ffmetadata';lines=[';FFMETADATA1']
for c in timeline['chapters']:lines.extend(['[CHAPTER]','TIMEBASE=1/1000',f'START={round(c["global_start"]*1000)}',f'END={round((c["global_start"]+c["duration"])*1000)}',f'title={c["title"]}'])
m.text_once(meta,'\n'.join(lines)+'\n');out=RUN/'CK3-War-AI-Episode02-Review-20260930-a04.mp4'
m.command(RUN,'final-join',[str(m.FFMPEG),'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-f','ffmetadata','-i',str(meta),'-map','0','-map_metadata','1','-map_chapters','1','-c','copy','-movflags','+faststart',str(out)])
report={**m.ref(out),'duration_expected':timeline['total_duration'],'human_signoff':'not-provided','status':'pending-independent-machine-check-and-frame-review','visual_change_keys':['terminal-t031','closing-c004'],'previous_retained_final':m.ref(PREVIOUS/'CK3-War-AI-Episode02-Review-20260930-a04.mp4')};m.write(RUN/'final-artifact.json',report);print(json.dumps(report))
