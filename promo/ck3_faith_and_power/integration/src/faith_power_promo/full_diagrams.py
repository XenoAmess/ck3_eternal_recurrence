"""Native SVG/Pillow mechanism diagrams; no game assets, browser or screen.

The SVG source stays editable. Only explicitly requested preview boards become
PNG. These illustrations explain fixed-source rules and do not depict gameplay.
"""
from html import escape
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 2560, 1440
BACKGROUND = '#211813'
PANEL = '#32251d'
PANEL_ACTIVE = '#49371f'
GOLD = '#d5b26b'
TEXT = '#f0e5cf'
MUTED = '#b9a98f'
POSITIONS = [(120, 304), (920, 304), (1720, 304), (120, 706), (920, 706), (1720, 706)]
BOX_WIDTH, BOX_HEIGHT = 720, 292


def wrap(value, font, width):
    lines, current = [], ''
    for character in value:
        if current and font.getlength(current + character) > width:
            lines.append(current)
            current = ''
        current += character
    if current:
        lines.append(current)
    return lines


def layout(board, font_file, active=0):
    """One measured layout drives SVG and PNG without hidden font shrinking."""
    if not 0 <= active < len(board['nodes']):
        raise ValueError('Unknown active node')
    fonts = {size: ImageFont.truetype(str(font_file), size=size) for size in (28, 32, 40, 44, 66)}
    commands = [
        ('text', 120, 58, board['id']+'  '+board['title'], 66, TEXT),
        ('text', 120, 152, '机制图解 · 来源 1.20.0.4 · 非实机界面／结果', 32, GOLD),
        ('text', 120, 222, board['logic_line'], 32, TEXT),
    ]
    for left,right,_label in board.get('edges',[]):
        x1,y1=POSITIONS[left];x2,y2=POSITIONS[right]
        if y1==y2 and x2>x1:
            commands.append(('arrow',x1+BOX_WIDTH+12,y1+BOX_HEIGHT//2,x2-12,y2+BOX_HEIGHT//2))
    for index, (node, (x,y)) in enumerate(zip(board['nodes'], POSITIONS)):
        commands.append(('box',x,y,BOX_WIDTH,BOX_HEIGHT,index==active))
        title_lines=wrap(node['title'],fonts[44],BOX_WIDTH-64)
        if len(title_lines)>2:
            raise ValueError('Node title exceeds two lines: '+board['id'])
        line_y=y+24
        for title in title_lines:
            commands.append(('text',x+32,line_y,title,44,GOLD if index==active else TEXT))
            line_y+=56
        line_y+=14
        for paragraph in node['lines']:
            for line in wrap(paragraph,fonts[32],BOX_WIDTH-64):
                if line_y+42>y+BOX_HEIGHT-16:
                    raise ValueError('Node content exceeds its measured box: '+board['id']+'/'+str(index))
                commands.append(('text',x+32,line_y,line,32,TEXT if index==active else MUTED))
                line_y+=42
    footer='来源 '+', '.join(board['claim_ids'])+'  ·  '+board['proof_layer']
    commands.append(('text',120,1050,footer,28,MUTED))
    commands.append(('text',120,1086,'本图不宣告当前按钮合法、操作已提交或业务已完成。',28,MUTED))
    for command in commands:
        if command[0]=='text' and command[1]+fonts[command[4]].getlength(command[3])>2440:
            raise ValueError('Text leaves safe horizontal bounds: '+board['id']+'/'+command[3])
    measure_draw=ImageDraw.Draw(Image.new('RGB',(WIDTH,HEIGHT)))
    for command in commands:
        if command[0]=='text':
            _,x,y,value,size,_colour=command
            bounds=measure_draw.textbbox((x,y),value,font=fonts[size],anchor='lt')
            if bounds[0]<120 or bounds[2]>2440 or bounds[3]>1120:
                raise ValueError('Measured glyph pixels leave source-diagram safe rectangle')
    return commands,fonts


def render_svg(board,font_file,font_family,active=0):
    commands,_=layout(board,font_file,active)
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
          '<title>'+escape(board['title'])+'</title>',
          '<desc>'+escape(json.dumps({'proof_layer':board['proof_layer'],'claim_ids':board['claim_ids'],
              'source_ref_ids':board.get('source_ref_ids',[]),'native_business_verified':False},ensure_ascii=False))+'</desc>',
          f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BACKGROUND}"/>']
    for command in commands:
        if command[0]=='arrow':
            _,x1,y1,x2,y2=command
            body.append(f'<path d="M{x1},{y1} L{x2},{y2} M{x2-12},{y2-10} L{x2},{y2} L{x2-12},{y2+10}" fill="none" stroke="{GOLD}" stroke-width="3"/>')
        elif command[0]=='box':
            _,x,y,w,h,focused=command
            body.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{PANEL_ACTIVE if focused else PANEL}" stroke="{GOLD if focused else "#69533c"}" stroke-width="{3 if focused else 2}"/>')
        else:
            _,x,y,value,size,colour=command
            body.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" font-family="{escape(font_family)}" font-size="{size}" fill="{colour}">{escape(value)}</text>')
    body.append('</svg>')
    return '\n'.join(body)+'\n'


def render_png(board,font_file,destination,active=0):
    commands,fonts=layout(board,font_file,active)
    image=Image.new('RGBA',(WIDTH,HEIGHT),BACKGROUND)
    draw=ImageDraw.Draw(image)
    for command in commands:
        if command[0]=='arrow':
            _,x1,y1,x2,y2=command
            draw.line((x1,y1,x2,y2),fill=GOLD,width=3)
            draw.polygon(((x2,y2),(x2-12,y2-10),(x2-12,y2+10)),fill=GOLD)
        elif command[0]=='box':
            _,x,y,w,h,focused=command
            draw.rounded_rectangle((x,y,x+w,y+h),radius=20,
                fill=PANEL_ACTIVE if focused else PANEL,outline=GOLD if focused else '#69533c',width=3 if focused else 2)
        else:
            _,x,y,value,size,colour=command
            draw.text((x,y),value,font=fonts[size],fill=colour,anchor='lt')
    path=Path(destination)
    with path.open('xb') as handle:image.save(handle,format='PNG',compress_level=6)
    if path.stat().st_size>15*1024**2:
        raise ValueError('Preview PNG exceeds its admitted maximum; original output retained')
    return path


def render_native_card(spec,font_file,destination):
    """Read exact JSON fields into a visibly labelled native-observation plate."""
    import hashlib
    from datetime import datetime, timezone
    from .full_episode import Inputs, pointer
    inputs=Inputs({})
    fonts={size:ImageFont.truetype(str(font_file),size) for size in (28,32,40,56)}
    image=Image.new('RGB',(WIDTH,HEIGHT),BACKGROUND); draw=ImageDraw.Draw(image)
    draw.text((120,58),spec['title'],font=fonts[56],fill=TEXT,anchor='lt')
    draw.text((120,148),'原生读回 · 独立查询数据图 · 不是游戏UI',font=fonts[32],fill=GOLD,anchor='lt')
    draw.text((120,205),spec.get('subtitle','本次机制实验的实际数据'),font=fonts[28],fill=MUTED,anchor='lt')
    rows=[];y=284
    if fonts[56].getlength(spec['title'])>2320:raise ValueError('Native graphic title too wide')
    if not 1<=len(spec['rows'])<=6:raise ValueError('Use 1–6 narrow native fields per card')
    for row in spec['rows']:
        if fonts[32].getlength(row['caption'])>2180:raise ValueError('Native graphic caption too wide')
        source=inputs.bound(row['file'])
        value=pointer(json.loads(source.read_text('utf-8')),row['json_pointer'])
        rendered=native_display(value,row.get('format','json'))
        if any(ord(char)<32 for char in rendered):raise ValueError('Select a narrow printable native field')
        lines=wrap(rendered,fonts[32],2180)
        if len(lines)>2:raise ValueError('Native field too large: select a narrower pointer')
        draw.rounded_rectangle((120,y,2440,y+118),radius=14,fill=PANEL,outline='#69533c',width=2)
        draw.text((144,y+10),row['caption'],font=fonts[32],fill=GOLD,anchor='lt')
        for index,line in enumerate(lines):draw.text((144,y+52+index*34),line,font=fonts[32],fill=TEXT,anchor='lt')
        rows.append({**row,'observed_value':value,'rendered_value':rendered})
        y+=132
    if y>1080:raise ValueError('Native graphic leaves reserved safe rectangle')
    draw.text((120,1090),spec.get('footer','本次867年阿拔斯机制实验 · 数据图解'),font=fonts[28],fill=MUTED,anchor='lt')
    path=Path(destination)
    with path.open('xb') as stream:image.save(stream,format='PNG',compress_level=6)
    record={'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()}
    receipt={'schema':'ck3-faith-power-native-readback-card-v1','machine_id':spec['machine_id'],
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'evidence_source':'Exact JSON pointers read from bound original receipts and directly rendered values',
        'title':spec['title'],'image':record,'rows':rows,'claims':spec.get('claim_ids',[]),'game_UI_depicted':False}
    target=path.with_suffix('.json')
    with target.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2)
    return path,target


def native_display(value,format_name):
    """Small declared display conversions; original values stay in the sidecar."""
    if format_name=='piety_points':
        return str(value['raw']/value['scale']).removesuffix('.0')+' 虔诚'
    if format_name=='piety_quote':
        return str(value['costs_raw']['piety']/value['raw_scale']).removesuffix('.0')+' 虔诚'
    if format_name=='rank':
        if type(value) is not bool:raise ValueError('Rank needs an observed boolean')
        return '主要圣地' if value else '普通圣地'
    if format_name=='yes_no':
        if type(value) is not bool:raise ValueError('Boolean display needs an observed boolean')
        return '是' if value else '否'
    if format_name=='active':
        if type(value) is not bool:raise ValueError('Active display needs an observed boolean')
        return '已激活' if value else '未激活'
    if format_name=='artifact_count':return str(len(value))+' 件供奉圣物'
    if format_name=='faith_name':
        if value not in {50,51}:raise ValueError('Unknown experiment faith identity')
        return {50:'逊尼派',51:'什叶派'}[value]
    if format_name=='rite_name':
        if value!=15:raise ValueError('Unknown experiment rite identity')
        return '马立克派'
    if format_name=='known_or_unknown' and value is None:return '未知'
    if format_name not in {'json','known_or_unknown'}:raise ValueError('Unknown native display format')
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))
