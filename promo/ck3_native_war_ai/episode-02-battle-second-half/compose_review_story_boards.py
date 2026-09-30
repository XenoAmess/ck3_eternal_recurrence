"""Compose explanatory video boards from exact source pixels and code-drawn labels.

The original UI stays in an overview; the crop is enlarged without replacing its
numbers. Rectangles are source-pixel annotations, not screen input coordinates.
"""
from __future__ import annotations
import argparse, importlib.util, json, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SCRIPT=Path(__file__).resolve().with_name('review_story_a03.py')
spec=importlib.util.spec_from_file_location('review_story_a03',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
FONT='C:/Windows/Fonts/msyh.ttc'

def font(size):return ImageFont.truetype(FONT,size)
def create(run,row):
    root=run/'visuals';root.mkdir(exist_ok=True)
    out=root/(row['id']+'.png');overlay=root/(row['id']+'-annotations.png')
    first=Path(row['source']);w,h=Image.open(first).size
    if [w,h]!=row['dimensions']:raise ValueError(f'dimensions changed {first}')
    im=Image.new('RGBA',(1920,1080),(13,20,28,255));d=ImageDraw.Draw(im)
    d.text((40,36),row['title'],font=font(48),fill='#F6F2E8')
    d.text((44,112),row.get('case','原界面 · 暂停分析'),font=font(27),fill='#82B8CB')
    d.line((40,161,1880,161),fill='#425461',width=2)
    d.text((45,194),'原界面定位',font=font(28),fill='#BFCAD2')
    d.text((1050,194),row.get('detail_title','把原界面放大'),font=font(31),fill='#E9C16B')
    d.rectangle((0,900,1920,1080),fill='#0B1016')
    d.text((45,856),row.get('caption',''),font=font(25),fill='#BEC6CC')
    rect=row['rect'];x1,y1,x2,y2=rect
    if not (0<=x1<x2<=w and 0<=y1<y2<=h):raise ValueError('crop out of bounds')
    scale=min(920/w,590/h);ow,oh=round(w*scale),round(h*scale);oy=250
    if row.get('overview_top') is not None:oy=row['overview_top']
    # The overview and enlargement are inserted below the transparent annotation.
    d.rectangle((40,oy,40+ow,oy+oh),fill=(0,0,0,0))
    d.rectangle((40+round(x1*scale),oy+round(y1*scale),40+round(x2*scale),oy+round(y2*scale)),outline='#E9C16B',width=4)
    dx,dy,dw,dh=1050,310,810,460
    if row.get('records'):
        dy,dh=270,240
        d.text((1050,550),'同次原生记录（界面不显示）',font=font(27),fill='#82B8CB')
        for number,line in enumerate(row['records']):
            d.text((1050,604+number*58),line,font=font(34),fill='#F6F2E8')
    if row.get('comparison'):
        dy,dh=285,220
        d.text((1050,250),row.get('before_label','之前'),font=font(24),fill='#BFCAD2')
        d.text((1050,550),row.get('after_label','之后'),font=font(24),fill='#BFCAD2')
        d.rectangle((1050,285,1860,505),fill=(0,0,0,0))
        d.rectangle((1050,590,1860,810),fill=(0,0,0,0))
    else:d.rectangle((dx,dy,dx+dw,dy+dh),fill=(0,0,0,0))
    im.save(overlay)
    cropw,croph=x2-x1,y2-y1
    # Fit each actual crop inside its own rectangle, retaining aspect ratio.
    graph=[f'[0:v]scale={ow}:{oh}[overview]',f'[0:v]crop={cropw}:{croph}:{x1}:{y1},scale={dw}:{dh}:force_original_aspect_ratio=decrease,pad={dw}:{dh}:(ow-iw)/2:(oh-ih)/2:color=0x0D141C[detail]']
    args=[str(m.FFMPEG),'-hide_banner','-nostdin','-n','-i',str(first)]
    if row.get('comparison'):
        second=Path(row['comparison']);args+=['-i',str(second)];idx=2
        if Image.open(second).size!=(w,h):raise ValueError('comparison geometry differs')
        graph.append(f'[1:v]crop={cropw}:{croph}:{x1}:{y1},scale={dw}:{dh}:force_original_aspect_ratio=decrease,pad={dw}:{dh}:(ow-iw)/2:(oh-ih)/2:color=0x0D141C[after]')
    else:idx=1
    args+=['-i',str(overlay)]
    graph.extend([f'color=c=0x0D141C:s=1920x1080[base]',f'[base][overview]overlay=40:{oy}[a]',f'[a][detail]overlay={dx}:{dy}[b]'])
    if row.get('comparison'):graph.extend(['[b][after]overlay=1050:590[c]',f'[c][{idx}:v]overlay=0:0[final]'])
    else:graph.append(f'[b][{idx}:v]overlay=0:0[final]')
    graphpath=root/(row['id']+'-filter.txt');m.text_once(graphpath,';\n'.join(graph))
    args+=['-filter_complex_threads','1','-/filter_complex',str(graphpath),'-map','[final]','-frames:v','1',str(out)]
    m.command(run,'layout-'+row['id'],args)
    return {'id':row['id'],'source':m.ref(first),'comparison':m.ref(Path(row['comparison'])) if row.get('comparison') else None,'crop_rect':rect,'image':m.ref(out),'annotation':m.ref(overlay),'claim_policy':row.get('claim_policy','source UI only')}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--spec',type=Path,required=True);a=p.parse_args()
    a.run.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(a.spec,a.run/'layout-spec.json');shutil.copyfile(Path(__file__),a.run/'layout-composer-source.py')
    m.write(a.run/'input-freeze.json',[m.ref(a.spec),m.ref(Path(__file__)),m.ref(SCRIPT)])
    rows=m.read(a.spec)['layouts'];results=[create(a.run,r) for r in rows];m.write(a.run/'layout-receipts.json',results);print(json.dumps({'layouts':len(results)}))
if __name__=='__main__':main()
