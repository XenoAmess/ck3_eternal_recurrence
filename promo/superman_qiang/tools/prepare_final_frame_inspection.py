"""Extract actual delivered-video frames for a bounded root visual inspection."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from PIL import Image,ImageDraw,ImageFont


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--attempt-directory',type=Path,required=True)
    p.add_argument('--movie',type=Path,required=True)
    p.add_argument('--output-directory',type=Path,required=True)
    a=p.parse_args()
    movie=a.movie.resolve(strict=True)
    timeline=json.loads((a.attempt_directory/'build/timeline.json').read_bytes())
    out=a.output_directory.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'tool-source.py').write_bytes(Path(__file__).read_bytes())
    ffmpeg=shutil.which('ffmpeg');assert ffmpeg
    jobs=[]
    for row in timeline['scenes']:
        begin=row['start_seconds']+row['lead_seconds']
        jobs.append((row['id']+'-paragraph',begin+2.0))
        jobs.append((row['id']+'-voice-tail-hold',begin+row['narration_seconds']+0.4))
    final=timeline['scenes'][-1]
    jobs.append(('final-stable-qr',final['end_seconds']-2.0))
    # Sample actual encoded optional-layer times, rather than the visual guide.
    montage=next(row for row in timeline['scenes'] if row['id']=='SQP-08')
    graph=a.attempt_directory/'build/filtergraphs/SQP-08.filter'
    windows=re.findall(r"enable='between\(t,([0-9.]+),([0-9.]+)\)'",graph.read_text(encoding='utf-8'))
    assert len(windows)==7, 'Use the seven actual rendered card windows.'
    for i,(start,end) in enumerate(windows):
        jobs.append((f'category-{i+1:02d}',montage['start_seconds']+(float(start)+float(end))/2))
    records=[]
    for index,(label,timepoint) in enumerate(jobs,1):
        frame=out/f'{index:02d}-{label}.png'
        argv=[ffmpeg,'-hide_banner','-nostdin','-v','error','-ss',f'{timepoint:.6f}','-i',str(movie),'-frames:v','1','-n',str(frame)]
        result=subprocess.run(argv,capture_output=True)
        (out/f'{index:02d}-command.json').write_text(json.dumps({'argv':argv,'exit_code':result.returncode},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (out/f'{index:02d}-stderr.txt').write_bytes(result.stderr)
        result.check_returncode()
        assert frame.is_file()
        records.append({'label':label,'timestamp_seconds':timepoint,'path':str(frame),'bytes':frame.stat().st_size,'sha256':hashlib.sha256(frame.read_bytes()).hexdigest()})
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    sheets=[]
    for first in range(0,len(records),10):
        rows=records[first:first+10]
        sheet=Image.new('RGB',(1280,386*((len(rows)+1)//2)),(18,14,18));draw=ImageDraw.Draw(sheet)
        for i,record in enumerate(rows):
            picture=Image.open(record['path']).convert('RGB');picture.thumbnail((640,360))
            x=(i%2)*640;y=(i//2)*386;sheet.paste(picture,(x,y))
            draw.text((x+8,y+360),f"{record['label']} · {record['timestamp_seconds']:.2f}s",font=font,fill='white')
        file=out/f'contact-{first//10+1:02d}.jpg';sheet.save(file,quality=92);sheets.append(str(file))
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'movie':str(movie),'movie_bytes':movie.stat().st_size,'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'frames':records,'contact_sheets':sheets,'montage_filtergraph':str(graph),'montage_filtergraph_sha256':hashlib.sha256(graph.read_bytes()).hexdigest(),'tool_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'root_direct_inspection':'pending','full_1x_human_playback':False,'human_signoff_granted':False}
    (out/'frame-index.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frame_count':len(records),'contact_sheets':sheets},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
