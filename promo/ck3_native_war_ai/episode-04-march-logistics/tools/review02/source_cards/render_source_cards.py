"""Project-native source cards; SVG + at most3 preview PNGs, no providers."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
SIZE=(2560,1440)
SAFE_BOTTOM=1116
COLORS={'BG':'#211813','PANEL':'#35291F','INK':'#F0E5CF','MUTED':'#BBA98D','GOLD':'#CBA56A','RED':'#CA7962','BLUE':'#9AAEAB','GREEN':'#ABB582','PAPER':'#D9C39B','PAPER_INK':'#3E2C20','FAINT':'#61503C'}
PINNED_MAP_SHA='f6ab6a8371f5dda5f5d8d314cf9c61acc5c8c2fe2a8dc7c2de99daa1282c3cd6'
PINNED_SOURCES_SHA='796e24a8684068b93943d1085b32f6b246b863c11dc5f842c072b99f3a3084b2'

def need(ok,why):
    if not ok: raise ValueError(why)

def digest(path):
    data=Path(path).read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def _n(value): return f'{value:.3f}'.rstrip('0').rstrip('.')

class Scene:
    """One project scene graph renders to both editable SVG and preview pixels."""
    def __init__(self,regular,bold):
        self.paths=(Path(regular),Path(bold))
        self.faces={}
        self.elements=[]
        self.text_boxes=[]
    def face(self,size,bold=False):
        key=(size,bold)
        if key not in self.faces: self.faces[key]=ImageFont.truetype(str(self.paths[int(bold)]),size)
        return self.faces[key]
    def rect(self,bounds,fill='PANEL',stroke='FAINT',width=2):
        self.elements.append(('rect',tuple(bounds),COLORS.get(fill,fill),COLORS.get(stroke,stroke) if stroke else None,width))
    def line(self,points,color='GOLD',width=3):
        self.elements.append(('line',tuple(tuple(p) for p in points),COLORS.get(color,color),width))
    def arrow(self,start,end,color='GOLD',width=5):
        self.line([start,end],color,width)
        angle=math.atan2(end[1]-start[1],end[0]-start[0])
        pts=[end]+[(end[0]-18*math.cos(angle+d),end[1]-18*math.sin(angle+d)) for d in (-.48,.48)]
        self.elements.append(('polygon',tuple(pts),COLORS.get(color,color)))
    def text(self,bounds,value,size=45,color='INK',bold=False,min_size=None,align='left'):
        x,y,r,b=bounds
        need(r>x and b>y,'invalid text bounds')
        low=min_size if min_size is not None else size
        for candidate in range(size,low-1,-1):
            face=self.face(candidate,bold)
            wrapped=[]
            for paragraph in value.split('\n'):
                current=''
                for char in paragraph:
                    if current and face.getlength(current+char)>r-x-4:
                        wrapped.append(current)
                        current=char
                    else: current+=char
                wrapped.append(current)
            step=math.ceil(candidate*1.34)
            ascent,descent=face.getmetrics()
            baseline=y+ascent
            ink=[]
            for i,line in enumerate(wrapped):
                left= x if align=='left' else x+((r-x)-face.getlength(line))/2
                bb=face.getbbox(line,anchor='ls')
                ink.append((left+bb[0],baseline+i*step+bb[1],left+bb[2],baseline+i*step+bb[3]))
            if all(a>=x-1 and c<=r+1 and q>=y-1 and d<=b+1 for a,q,c,d in ink): break
        else: raise ValueError('Text does not fit assigned box: '+value)
        for i,(line,bb) in enumerate(zip(wrapped,ink)):
            left=x if align=='left' else x+((r-x)-face.getlength(line))/2
            self.elements.append(('text',left,baseline+i*step,line,candidate,COLORS.get(color,color),bold,face.getlength(line)))
            self.text_boxes.append({'value':line,'font_size':candidate,'assigned_bounds':list(bounds),'actual_ink_bounds':[round(v,3) for v in bb]})
        return candidate
    def panel(self,bounds,kicker,hero,body,color='GOLD',hero_size=68):
        x,y,r,b=bounds
        self.rect(bounds,stroke=color)
        self.text((x+30,y+22,r-30,y+82),kicker,34,color,True)
        self.text((x+30,y+99,r-30,y+220),hero,hero_size,color,True,min_size=48)
        self.text((x+30,y+241,r-30,b-22),body,45,'INK',False,min_size=36)
    def svg(self,metadata):
        out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="1440" viewBox="0 0 2560 1440" role="img">',
             '<!-- GENERATED FILE: edit the project source-card generator and regenerate. -->',
             '<title>'+html.escape(metadata['title'])+'</title>',
             '<desc>'+html.escape('源码机制解释卡；假设数字不代表实机结果。')+'</desc>',
             '<metadata>'+html.escape(json.dumps(metadata,ensure_ascii=False,sort_keys=True))+'</metadata>']
        for e in self.elements:
            if e[0]=='rect':
                _,(x,y,r,b),fill,stroke,width=e
                out.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(r-x)}" height="{_n(b-y)}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{width}"/>')
            elif e[0]=='line':
                _,pts,color,width=e
                out.append(f'<polyline points="'+ ' '.join(f'{_n(x)},{_n(y)}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="{width}"/>')
            elif e[0]=='polygon':
                _,pts,color=e
                out.append('<polygon points="'+' '.join(f'{_n(x)},{_n(y)}' for x,y in pts)+f'" fill="{color}"/>')
            else:
                _,x,baseline,value,size,color,bold,width=e
                out.append(f'<text x="{_n(x)}" y="{_n(baseline)}" font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" textLength="{_n(width)}" lengthAdjust="spacingAndGlyphs">'+html.escape(value)+'</text>')
        return '\n'.join(out+['</svg>',''])
    def preview(self,width):
        image=Image.new('RGB',SIZE,COLORS['BG'])
        draw=ImageDraw.Draw(image)
        for e in self.elements:
            if e[0]=='rect':
                _,bounds,fill,stroke,stroke_width=e
                draw.rectangle(bounds,fill=fill,outline=stroke,width=stroke_width)
            elif e[0]=='line':
                _,points,color,stroke_width=e
                draw.line(points,fill=color,width=stroke_width,joint='curve')
            elif e[0]=='polygon': draw.polygon(e[1],fill=e[2])
            else:
                _,x,baseline,value,size,color,bold,length=e
                draw.text((x,baseline),value,font=self.face(size,bold),fill=color,anchor='ls')
        return image.resize((width,round(width*9/16)),Image.Resampling.LANCZOS)

COPY={
 'D01':('补给0→0，仍可能继续损耗','假设：原生准入通过，本次变化为负','库存相同，不等于本次没有更新','成功更新后继续算供给预算；实际损失另看兵员写回。'),
 'D02':('零库存，没有另加一档','假设当次加载原版阈值表','零与9.99999同档，正好10在上一档','base分量仍要经过将领、舰队与合格人数条件。'),
 'D03':('先分别取整，再合计预算','假设人数199，供给5%，围城1%，劫掠0','9 + 1 = 10；先合成6%却会得到11','预算不等于实际死亡数；后续分配沿变化后的人数执行。'),
 'D04':('县剩余预算，先保存再分配','假设普通非负、无溢出的预算输入','R在首选写入前已固定','首选按请求q消耗预算，实际扣得不同也不重算R。'),
 'D05':('多层取整：49与50的差别','假设W3001、基础5%、修正0.33339、minimum100','先取有效比例，再计算整数人数','本卡只是安全整数域的假设输入，不是本场modifier或损失。'),
 'D06':('预算、请求、写回，逐层分开','假设有效供给分量5%','19名算0；20名才算出1','没有事件不代表整窗零损失；物理别名只核算一次。'),
 'D07':('平分迁移整条兵团记录','原生规则图解；字母块仅表示完整记录','普通路径不把每个持久兵槽切半','两边UI人数不保证严格各半，实际DATA与统帅仍须读回。'),
 'D08':('拆成两军，仍要看聚合用量','假设两军同省、贡献资格及其他军队不变','100变成50 + 50，省内用量仍可为6000','分兵是否改善压力，要看实际占用与各队真正去向。'),
 'D09':('1/1，还可能是角色记录','已闭合的条件路径；不是每次合军必发生','角色、统帅、骑士、物理兵员分开读取','构造时空DATA不代表所有角色记录永远无DATA；不授实际新生。'),
}

def make_scene(card,regular,bold):
    cid=card['id']
    title,kicker,hero,limit=COPY[cid]
    s=Scene(regular,bold)
    s.rect((0,0,*SIZE),'BG',None)
    s.rect((50,42,2510,1116),'BG','GOLD',3)
    s.line([(78,120),(2482,120)],'FAINT',2)
    s.text((112,142,2050,232),title,69,'INK',True,min_size=56)
    s.text((2130,156,2435,220),cid,38,'GOLD',True,align='center')
    s.text((120,241,2440,307),('假设算例  ·  ' if card['synthetic_example'] else '原生规则图解  ·  ')+kicker,34,'GOLD',min_size=30)
    s.text((120,316,2440,397),hero,54,'INK',True,min_size=44)
    if cid=='D01':
        s.panel((112,425,816,840),'01 入口库存','0','本次更新已经准入')
        s.panel((928,425,1632,840),'02 ADD后floor','0 + 负变化 → 0','负结果被压回0')
        s.panel((1744,425,2448,840),'03 继续执行','整数预算','成功返回，仍可能扣兵')
        s.arrow((828,630),(916,630)); s.arrow((1644,630),(1732,630))
    elif cid=='D02':
        for x,value,integer,base,col in [(112,'0','0','5%','GOLD'),(910,'9.99999','9','5%','GOLD'),(1708,'10.00000','10','0','BLUE')]:
            s.panel((x,425,x+740,840),'库存 → 向零取整数',value,f'integer {integer}\n该表base {base}',col)
        s.text((130,855,2430,930),'加载表（假设）：levels [60,10,0]  /  base [0,0,5000]',34,'MUTED')
    elif cid=='D03':
        s.rect((112,425,1232,855),'PANEL','GOLD')
        s.text((145,450,1190,510),'分别算两个整数预算',38,'GOLD',True)
        s.text((145,525,1190,685),'199 × 5% → 9\n199 × 1% → 1',55,'INK',True)
        s.text((145,712,1190,810),'9 + 1 = 10',68,'GREEN',True)
        s.rect((1328,425,2448,855),'PANEL','RED')
        s.text((1360,450,2410,510),'先合百分比，算法已不同',38,'RED',True)
        s.text((1360,535,2410,660),'199 × 6%',68,'INK',True)
        s.text((1360,712,2410,810),'→ 11',68,'RED',True)
    elif cid=='D04':
        for top,vals,note,col in [(425,['100','120','100','0'],'例A：R=0，不启动县剩余分配','BLUE'),(650,['100','40','40','60'],'例B：先存R=60，再做首选写入','GOLD')]:
            s.rect((112,top,2448,top+195),'PANEL',col)
            for i,(label,value) in enumerate(zip(['整军预算 B','首选人数 S','首选 P','剩余 R'],vals)):
                x=140+i*410
                s.text((x,top+18,x+370,top+73),label,32,'MUTED')
                s.text((x,top+77,x+370,top+170),value,62,col,True)
            s.text((1820,top+32,2400,top+175),note,38,col,True)
    elif cid=='D05':
        s.panel((112,425,816,855),'01 有效比例','F = 1666','5000 × 33339 ÷ 100000\n先向零取整',hero_size=62)
        s.panel((928,425,1632,855),'02 两个人数项','49 / 33','3001 × F ÷ 100000 → 49\n100 × M2 ÷ 100000 → 33',hero_size=62)
        s.panel((1744,425,2448,855),'03 按原顺序比较','B = 49','取两项较大，再cap到全军\n合到最后才取整会得50',hero_size=62)
        s.arrow((828,630),(916,630)); s.arrow((1644,630),(1732,630))
    elif cid=='D06':
        s.rect((112,420,1232,565),'PANEL','BLUE'); s.rect((1328,420,2448,565),'PANEL','GOLD')
        s.text((145,443,1195,545),'19 × 5% → 预算0',55,'BLUE',True)
        s.text((1360,443,2410,545),'20 × 5% → 预算1',55,'GOLD',True)
        for x,label,body in [(112,'整军整数预算','先按合格人数计算'),(928,'兵团整数请求','按顺序、分母分配'),(1744,'实际兵槽写回','cap / 取整 / 后态')]:
            s.rect((x,640,x+704,860),'PANEL','GOLD')
            s.text((x+24,662,x+680,735),label,45,'GOLD',True)
            s.text((x+24,760,x+680,838),body,36,'INK')
        s.arrow((828,745),(916,745)); s.arrow((1644,745),(1732,745))
    elif cid=='D07':
        s.rect((112,425,950,780),'PANEL','GOLD'); s.rect((1220,425,2448,780),'PANEL','GOLD')
        s.text((145,450,900,515),'拆分前：完整记录块',38,'GOLD',True)
        s.text((1250,450,2400,515),'拆分后：迁移整条记录',38,'GOLD',True)
        for i,label in enumerate(['记录 A','记录 B','记录 C']):
            x=145+i*250; s.rect((x,565,x+220,685),'PAPER','GOLD')
            s.text((x+14,589,x+206,658),label,38,'PAPER_INK',True,align='center')
        for x,y,label in [(1250,550,'A'),(1530,550,'B'),(1920,550,'C')]:
            s.rect((x,y,x+240,y+120),'PAPER','GOLD')
            s.text((x+14,y+22,x+226,y+93),'记录 '+label,38,'PAPER_INK',True,align='center')
        s.text((1260,700,1810,760),'原军',34,'MUTED'); s.text((1940,700,2380,760),'新军',34,'MUTED')
        s.arrow((975,620),(1195,620))
        s.text((135,840,2425,920),'新Army的stock字段复制原值；后续容量与实际库存独立读取。',40,'GOLD',True)
    elif cid=='D08':
        for y,label in [(425,'拆分前：选中100，其他5900'),(655,'拆分后：50 + 50，其他5900')]:
            s.text((130,y,1320,y+64),label,42,'INK',True)
            s.rect((135,y+95,2235,y+155),'PANEL','FAINT')
            limitx=135+2100*4000/6000
            s.rect((135,y+95,limitx,y+155),'GOLD',None)
            s.rect((limitx,y+95,2235,y+155),'RED',None)
            s.line([(limitx,y+78),(limitx,y+174)],'INK',3)
            s.text((limitx-170,y+167,limitx+330,y+220),'上限4000',30,'MUTED')
            s.text((2258,y+83,2445,y+158),'6000',45,'GOLD',True)
    elif cid=='D09':
        s.rect((112,420,2448,555),'PANEL','GOLD')
        s.text((145,442,2410,532),'处理旧角色 → 构造空DATA记录 → 关联角色 → 刷新1/1缓存',45,'GOLD',True,min_size=42)
        labels=[('角色记录','角色叶 + 完整ID\nDATA与predicate'),('现任统帅','独立typed readback\n不由F8猜任命'),('骑士成员','完整combat Knights\n另核membership'),('物理兵员','实际DATA兵槽\n不能由1/1代填')]
        for i,(label,body) in enumerate(labels):
            x=112+i*591
            s.rect((x,625,x+563,885),'PANEL','GOLD')
            s.text((x+22,646,x+541,719),label,45,'GOLD',True)
            s.text((x+22,752,x+541,865),body,36,'INK',min_size=32)
    else: raise ValueError('unknown card '+cid)
    s.text((114,970,2435,1018),'段号：'+' / '.join(card['paragraph_ids'])+'   ·   source：'+' / '.join(card['source_ids']),25,'GOLD',min_size=23)
    s.text((114,1021,2435,1082),limit,26,'MUTED',min_size=24)
    need(all(bb['actual_ink_bounds'][3]<=SAFE_BOTTOM for bb in s.text_boxes),'text enters subtitle region')
    return s

def generate(episode_root,output_dir,regular,bold,preview_ids=(),preview_width=1280):
    episode=Path(episode_root).resolve()
    mapping=episode/'review02/story-a03/claim-shot-agent-map.json'
    sources=episode/'review02/story-a03/source-index.json'
    need(digest(mapping)['sha256']==PINNED_MAP_SHA,'source-a03 map bytes changed')
    need(digest(sources)['sha256']==PINNED_SOURCES_SHA,'source-a03 source index changed')
    data=json.loads(mapping.read_text(encoding='utf-8'))
    cards=data['demonstration_cards']
    need({c['id'] for c in cards}==set(COPY),'nine source cards differ')
    need(len(preview_ids)<=3 and len(set(preview_ids))==len(preview_ids),'at most3 distinct preview PNGs')
    need(set(preview_ids)<=set(COPY),'unknown preview card')
    need(type(preview_width) is int and 640<=preview_width<=1280,'preview width640..1280')
    scenes={c['id']:make_scene(c,regular,bold) for c in cards}
    dest=Path(output_dir).resolve()
    dest.mkdir(parents=True,exist_ok=False)
    (dest/'svg').mkdir()
    if preview_ids: (dest/'preview').mkdir()
    metadata={'kind':'project-source-explanation-card-assets','canvas':[2560,1440],'subtitle_safe_from_y':1120,'font_family':'Microsoft YaHei',
      'font_inputs':{'regular':digest(regular),'bold':digest(bold)},'source_map':digest(mapping),'source_index':digest(sources),
      'machine_independent_generation':True,'no_raw_or_screenshot_inputs':True,'live_positive':False,'clean_or_signoff':False,'cards':[]}
    for c in cards:
        scene=scenes[c['id']]
        info={'card_id':c['id'],'title':COPY[c['id']][0],'paragraph_ids':c['paragraph_ids'],'source_ids':c['source_ids'],
          'proof_layer':'source-explanation / explicit hypothetical example','actual_game_values':None,'actual_shot':None}
        svg=scene.svg(info)
        ET.fromstring(svg)
        target=dest/'svg'/f"{c['id']}.svg"
        target.write_text(svg,encoding='utf-8',newline='\n')
        row={**info,'svg':{'path':target.relative_to(dest).as_posix(),**digest(target)},'text_box_count':len(scene.text_boxes),'all_text_ink_inside_assigned_bounds':True,
          'text_boxes':scene.text_boxes,'min_font_size':min(x['font_size'] for x in scene.text_boxes)}
        if c['id'] in preview_ids:
            image=scene.preview(preview_width)
            png=dest/'preview'/f"{c['id']}.png"
            image.save(png,format='PNG',optimize=True)
            row['preview']={'path':png.relative_to(dest).as_posix(),'size':list(image.size),**digest(png),'renderer':'same scene graph via Pillow; not an independent browser SVG rasterization'}
        metadata['cards'].append(row)
    (dest/'render-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    return metadata

def main():
    p=argparse.ArgumentParser(description='Render nine existing Episode04 source cards to editable SVG. No providers or movie render.')
    p.add_argument('--episode-root',required=True,type=Path)
    p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--font-regular',required=True,type=Path)
    p.add_argument('--font-bold',required=True,type=Path)
    p.add_argument('--preview-id',action='append',default=[])
    p.add_argument('--preview-width',default=1280,type=int)
    a=p.parse_args()
    result=generate(a.episode_root,a.output_dir,a.font_regular,a.font_bold,a.preview_id,a.preview_width)
    print(json.dumps({'status':'GENERATED_SOURCE_ASSETS_ONLY','svg_cards':len(result['cards']),'PNG_previews':len(a.preview_id),
                      'clean_or_human_signoff':False,'output':str(a.output_dir)},ensure_ascii=False))

if __name__=='__main__': main()
