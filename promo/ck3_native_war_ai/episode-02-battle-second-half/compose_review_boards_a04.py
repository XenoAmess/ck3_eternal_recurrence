"""Draw exact UI crops beside explicitly labelled native-record explanations.

Only source pixels, rectangles and text are composed. No OCR or invented UI.
The bottom 180 pixels are reserved for Chinese and English subtitles.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT='C:/Windows/Fonts/msyh.ttc'
@lru_cache(maxsize=64)
def font(size):return ImageFont.truetype(FONT,size)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ref(p):
    p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
def write(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def fit_text(d,xy,text,max_width,size,color):
    while size>18 and d.textlength(text,font=font(size))>max_width:size-=1
    d.text(xy,text,font=font(size),fill=color)
def wrap(d,text,width,size):
    lines=[];line=''
    for c in text:
        if line and d.textlength(line+c,font=font(size))>width:lines.append(line);line=c
        else:line+=c
    if line:lines.append(line)
    return lines
def paste_fit(canvas,img,box):
    x,y,w,h=box;tmp=img.convert('RGB');scale=min(w/tmp.width,h/tmp.height)
    tmp=tmp.resize((round(tmp.width*scale),round(tmp.height*scale)),Image.Resampling.LANCZOS)
    canvas.paste(tmp,(x+(w-tmp.width)//2,y+(h-tmp.height)//2))
def source_crop(path,rect):
    src=Image.open(path);w,h=src.size;x1,y1,x2,y2=rect
    if not(0<=x1<x2<=w and 0<=y1<y2<=h):raise ValueError(f'crop out of source bounds: {path} {rect}')
    return src,src.crop(tuple(rect))
def board(root,key,row):
    source=Path(row['source_image']);src,crop=source_crop(source,row['crop_xyxy'])
    im=Image.new('RGB',(1920,1080),'#0D141C');d=ImageDraw.Draw(im)
    fit_text(d,(40,28),row['title'],1830,45,'#F6F2E8')
    fit_text(d,(44,100),row['case'],1820,26,'#82B8CB')
    d.line((40,145,1880,145),fill='#425461',width=2)
    fit_text(d,(40,164),row.get('ui_label','原界面定位'),930,27,'#BFCAD2')
    paste_fit(im,src,(40,210,930,310))
    # Annotation identifies the genuine crop inside the genuine overview.
    scale=min(930/src.width,310/src.height);ow=round(src.width*scale);oh=round(src.height*scale)
    ox=40+(930-ow)//2;oy=210+(310-oh)//2;x1,y1,x2,y2=row['crop_xyxy']
    d.rectangle((ox+round(x1*scale),oy+round(y1*scale),ox+round(x2*scale),oy+round(y2*scale)),outline='#E9C16B',width=3)
    extras=row.get('extra_ui',[])
    if extras:
        cols=2 if len(extras)>2 else len(extras);height=135 if len(extras)>2 else 230
        for i,item in enumerate(extras):
            _,small=source_crop(item['image'],item['crop_xyxy'])
            bx=40+(i%cols)*(930//cols);by=535+(i//cols)*145
            fit_text(d,(bx,by),item['label'],930//cols-12,24,'#E9C16B')
            paste_fit(im,small,(bx,by+30,930//cols-12,height-30))
    else:
        d.text((40,540),'原界面局部放大',font=font(26),fill='#E9C16B')
        paste_fit(im,crop,(40,580,930,230))
    d.rounded_rectangle((1015,190,1880,815),radius=18,fill='#172431',outline='#425461',width=2)
    fit_text(d,(1040,212),row['diagram_title'],812,32,'#E9C16B')
    lines=row.get('diagram_lines',[])
    if len(lines)>5:raise ValueError(f'too many diagram lines: {key}')
    y=282
    for number,line in enumerate(lines):
        chunks=wrap(d,line,770,32)
        if len(chunks)>2:raise ValueError(f'diagram text exceeds two lines: {key}/{number}')
        chosen=number==row.get('highlight_line',-1)
        if chosen:d.rounded_rectangle((1035,y-8,1855,y+len(chunks)*43+6),radius=8,fill='#3C3B29')
        for text in chunks:d.text((1050,y),text,font=font(32),fill='#F6F2E8' if chosen else '#D9E0E5');y+=43
        y+=18
    if y>810:raise ValueError(f'diagram exceeds content area: {key}')
    footer=wrap(d,row.get('footer',''),1790,24)
    if len(footer)>2:raise ValueError(f'footer exceeds two lines: {key}')
    for i,line in enumerate(footer):d.text((45,830+i*31),line,font=font(24),fill='#BEC6CC')
    d.rectangle((0,900,1920,1080),fill='#0B1016')
    out=root/'visuals'/f'{key}.png';out.parent.mkdir(exist_ok=True)
    with out.open('xb') as f:im.save(f,format='PNG')
    return {'kind':'still','image':str(out),'source_kind':row['source_kind'],'case':row['case'],'source_binding':ref(source),'source_crop':row['crop_xyxy'],'rendered_image':ref(out),'spec':row}
def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--story',required=True,type=Path);p.add_argument('--spec',required=True,type=Path);a=p.parse_args()
    a.run.mkdir(parents=True,exist_ok=False);shutil.copyfile(a.spec,a.run/'spec.json');shutil.copyfile(a.story,a.run/'story.json');shutil.copyfile(__file__,a.run/'board-composer-source.py')
    story=read(a.story);spec=read(a.spec)['utterances'];keys=[f"{c['id']}-{u['id']}" for c in story['chapters'] for u in c['utterances']]
    if set(keys)!=set(spec):raise ValueError(f'spec coverage mismatch missing={set(keys)-set(spec)} extra={set(spec)-set(keys)}')
    results={key:board(a.run,key,spec[key]) for key in keys}
    write(a.run/'edit.json',{'kind':'a04-six-chapter-ui-and-native-explanation','utterances':results,'human_signoff':'not-provided','production_clean_admission':False})
    write(a.run/'input-freeze.json',[ref(a.spec),ref(a.story),ref(__file__)])
    print(json.dumps({'boards':len(results),'edit':ref(a.run/'edit.json')}))
if __name__=='__main__':main()
