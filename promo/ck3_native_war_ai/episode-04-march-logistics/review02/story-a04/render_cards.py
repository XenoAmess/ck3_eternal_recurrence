"""Render source/actual demonstration cards as native SVG only."""
from pathlib import Path
import argparse
from html import escape
import json

PALETTE = {"bg":"#211813", "panel":"#35291F", "ink":"#F0E5CF", "muted":"#BBA98D", "gold":"#CBA56A", "red":"#CA7962", "blue":"#9AAEAB", "green":"#ABB582"}
FONT = "Microsoft YaHei, Noto Sans CJK SC, sans-serif"

CARDS = [
 {"id":"D10", "title":"补员：许可、准备、实际人数", "kind":"SOURCE + ACTUAL LIMITED", "paragraphs":["C02-05","C02-06","C02-07","C02-08","C02-09"],
  "panels":[
   {"x":90,"y":290,"w":1160,"h":290,"label":"当前输入与普通准备", "lines":["当前许可 / 当前 fresh 比例", "依分支准备 → 保存 prepared 比例"],"color":"gold"},
   {"x":1310,"y":290,"w":1160,"h":290,"label":"随后请求与实际写回", "lines":["读取已保存比例 + 各物理槽当前条件", "请求可能拒绝或整数为0 → 独立核实际ADD"],"color":"blue"},
   {"x":90,"y":630,"w":1160,"h":300,"label":"R0176 / selected93 / 同帧实际", "lines":["4条 unique physical DATA；250/250", "当前两许可均 false；已存 prepared 均 0"],"color":"green"},
   {"x":1310,"y":630,"w":1160,"h":300,"label":"缓存时序：源码允许的可能", "lines":["当前许可 false 不等于旧正缓存已清零", "这不是本次实际补兵结果"],"color":"red"}],
  "footer":["SOURCE 262C6E0 / 262C680 / 262CAB0 / 262C9B0 / 2657EF0 / 2A98B88", "当前 fresh、已存 prepared、实际新增人数分别读；角色1/1不计入实体兵员"]},
 {"id":"D11", "title":"锁定后：首段保留，后程可改", "kind":"R0175 + R0176 ACTUAL", "paragraphs":["C03-08","C04-01","C04-02","C04-03","C04-04","C04-05","C04-06","C04-07","C04-08"],
  "panels":[
   {"x":90,"y":290,"w":1160,"h":300,"label":"R0175 / Halt 一次", "lines":["原 [1036, 8653, 1034, 1033]", "后 [1036]；首段进度保留", "2日后到1036；次日仍空路线"],"color":"gold"},
   {"x":1310,"y":290,"w":1160,"h":300,"label":"R0176 / alternate Move 一次", "lines":["原 [8653, 1034, 1033] → [8653, 8645]", "先到原front8653，再到替代8645", "替代终点：45秒raw片外独立读回"],"color":"green"},
   {"x":90,"y":640,"w":1160,"h":290,"label":"实际锁定输入 / Q100000", "lines":["96666 > 50000；95108 > 50000", "比较符源码为 >；等号未在两场实测"],"color":"blue"},
   {"x":1310,"y":640,"w":1160,"h":290,"label":"不同起算日，不同范围", "lines":["baseline → 替代终点 13自然日", "改令 → 同一替代终点 8自然日"],"color":"red"}],
  "footer":["ACTUAL source dcda / R0175、R0176为独立正常会话；原生结果与候选视频分开", "首段进度 ≠ 整条完成比例；首段时量 ≠ 整条ETA；不授ABC胜负或clean镜头"]},
 {"id":"D12", "title":"实体250守恒，角色与统帅另读", "kind":"R0176 SELECTED93 ACTUAL", "paragraphs":["C02-06","C06-05"],
  "panels":[
   {"x":90,"y":300,"w":740,"h":370,"label":"拆前 / CUnit93", "lines":["实体 DATA：250 / 250", "四条 physical ArRg673–676", "当前统帅 absent"],"color":"gold"},
   {"x":910,"y":300,"w":740,"h":370,"label":"拆后 / fresh162", "lines":["选中cohort实体合计250", "新队162独立发现", "统帅 Character34232"],"color":"blue"},
   {"x":1730,"y":300,"w":740,"h":370,"label":"合后 / 93存续", "lines":["原四条实体仍250 / 250", "162独立消失；93存续", "统帅 Character34232"],"color":"green"},
   {"x":90,"y":730,"w":2380,"h":200,"label":"另一路角色关联", "lines":["Army18空DATA/cache1/1 ArRg59消失 → 同一角色34232成为新162及合后93的统帅"],"color":"red"}],
  "footer":["三阶段同date53146632；只授具名selected93微例，原strict失败保留，R09全卡仍未闭", "1/1变化不记作实体补员、死亡、Character出生或Knight资格；库存/容量/权重未在此卡证明"]}
]

def layout(card):
    texts = [{"text":card["id"] + "  /  MARCH LOGISTICS", "x":90,"y":85,"size":38,"color":"gold"},
             {"text":card["title"],"x":90,"y":178,"size":69,"color":"ink"},
             {"text":card["kind"],"x":90,"y":240,"size":34,"color":"muted"}]
    rects = []
    for p in card["panels"]:
        rects.append(p)
        texts.append({"text":p["label"],"x":p["x"]+30,"y":p["y"]+60,"size":38,"color":p["color"],"max_x":p["x"]+p["w"]-25,"max_y":p["y"]+p["h"]-18})
        for i,line in enumerate(p["lines"]):
            texts.append({"text":line,"x":p["x"]+30,"y":p["y"]+125+i*63,"size":45,"color":"ink","max_x":p["x"]+p["w"]-25,"max_y":p["y"]+p["h"]-18})
    for i,line in enumerate(card["footer"]):
        texts.append({"text":line,"x":90,"y":1015+i*48,"size":25,"color":"muted","max_x":2470,"max_y":1100})
    return rects,texts

def render_svg(card):
    rects,texts = layout(card)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="1440" viewBox="0 0 2560 1440">',
             '<title>'+escape(card['title'])+'</title>',
             '<desc>Source/actual demonstration card, not gameplay footage or human signoff.</desc>',
             '<rect width="2560" height="1440" fill="'+PALETTE['bg']+'"/>']
    for p in rects:
        parts.append('<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'.format(**p,fill=PALETTE['panel'],stroke=PALETTE[p['color']]))
    for t in texts:
        parts.append('<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}">{value}</text>'.format(**t,font=FONT,fill=PALETTE[t['color']],value=escape(t['text'])))
    parts.append('</svg>\n')
    return '\n'.join(parts)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    for card in CARDS:
        with (args.output_dir/(card['id']+'.svg')).open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(render_svg(card))

if __name__=='__main__':
    main()
