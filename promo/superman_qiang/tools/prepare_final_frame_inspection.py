"""Extract actual delivered-video frames for a bounded root visual inspection."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
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
    ffmpeg=shutil.which('ffmpeg');assert ffmpeg
    jobs=[]
    for row in timeline['scenes']:
        begin=row['start_seconds']+row['lead_seconds']
        jobs.append((row['id']+'-paragraph',begin+2.0))
        jobs.append((row['id']+'-voice-tail-hold',begin+row['narration_seconds']+0.4))
    final=timeline['scenes'][-1]
    jobs.append(('final-stable-qr',final['end_seconds']-2.0))
    # Seven category cards in the encoded montage, using its declared guide span.
    montage=next(row for row in timeline['scenes'] if row['id']=='SQP-08')
    for i,layer in enumerate(montage['visual']['optional_layers']):
        fractions=layer.get('timing_fraction')
        if fractions:jobs.append((f'category-{i+1:02d}',montage['start_seconds']+montage['duration_seconds']*sum(fractions)/2))
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
    report={'created_at_utc':datetime.now(timezone.utc).isoformat(),'movie':str(movie),'movie_bytes':movie.stat().st_size,'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'frames':records,'contact_sheets':sheets,'root_direct_inspection':'pending','full_1x_human_playback':False,'human_signoff_granted':False}
    (out/'frame-index.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frame_count':len(records),'contact_sheets':sheets},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())
