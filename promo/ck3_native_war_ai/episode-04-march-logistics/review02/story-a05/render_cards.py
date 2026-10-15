"""Render only native SVG for the final16 source cards."""
from pathlib import Path
from html import escape
import argparse

P={'bg':'#211813','panel':'#35291F','ink':'#F0E5CF','muted':'#BBA98D','gold':'#CBA56A','blue':'#9AAEAB','green':'#ABB582','red':'#CA7962'}
FONT='Microsoft YaHei, Noto Sans CJK SC, sans-serif'
CARDS=[
 {'id':'D13','title':'先看单位，再比较数字','kind':'SOURCE / 假设示例明确标注',
  'rows':[
   ('当前人数 / 满员人数','人；缓存行完整核对，实体DATA另核'),
   ('补给库存 / 军队容量','物资单位；不是士兵，也不是百分比'),
   ('当地用量 / 当地上限','兵员用量与支持人数同口径比较'),
   ('补给月变化','当前条件的变化量；不是已实现增加'),
   ('当前损耗比例 / 整数预算','比例与预算分开；不直接充作已扣兵'),
   ('假设：补给100 / 容量300','仅说明单位；不是Robert/.4本场读数')],
  'footer':['SOURCE current supply/capacity / current callback / ArRg cache vs physical DATA','库存、容量、当地上限和兵员数分别读；原版术语动态镜头仍需独立绑定']},
 {'id':'D14','title':'当前月率、实际支付、钱包净变化','kind':'SOURCE + R0173 BOARDING ACTUAL',
  'rows':[
   ('当前净收入','gross − 完整expenses；不重复扣军事月率'),
   ('当前军事月率 / 全部集结替代率','两种情景；不相加；都不是实际支付账'),
   ('R0173登船：本次实际personal SUB','254.48407 → 251.48407；扣3金币'),
   ('旅途区间费用','按账户/起止日期记录真实支出与其他收支'),
   ('钱包净变化','所有收支混合结果；不改名纯行军费'),
   ('实际军事维护费','归因/cadence仍unknown；R07对照仍缺')],
  'footer':['SOURCE exact4 cash getters / independent boarding writer+gateway+natural-parent chain','3金币只授本次登船，不是通用费率；本卡不授maintenance或ABC结果']},
 {'id':'D15','title':'合军：角色权重与实际库存分开核','kind':'SOURCE / 实际完整stock-cap-weights pair尚缺',
  'rows':[
   ('角色权重 wD / wS','读取native D权重；S用其当时native current'),
   ('份额各自取整','share_i = trunc0(w_i × 100000 / W)'),
   ('库存项各自取整','term_i = trunc0(share_i × 原stock_i / 100000)'),
   ('相加后按实际合后容量截断','先选将/刷新再读cap；大值保护分支HOLD'),
   ('R0176 selected93已确认范围','实体250守恒；不是stock/cap/weights实测'),
   ('仍需实际同边界数值','两侧与合后stock/cap/weights完整pair')],
  'footer':['SOURCE actual .4 2C55180：两stage trunc0 → sum → postcap clamp；仅已核正权重fast域','不移用旧 .3 B数值，不授R09全卡、补给合并实测或ABC胜负']}
]
def layout(card):
    texts=[{'text':card['id']+' / MARCH LOGISTICS','x':90,'y':85,'size':38,'color':'gold'},
           {'text':card['title'],'x':90,'y':178,'size':69,'color':'ink'},
           {'text':card['kind'],'x':90,'y':240,'size':34,'color':'muted'}]
    for i,(label,value) in enumerate(card['rows']):
        y=330+i*105
        texts += [{'text':label,'x':120,'y':y,'size':38,'color':'gold','max_x':1010,'max_y':y+15},
                  {'text':value,'x':1050,'y':y,'size':43,'color':'ink','max_x':2440,'max_y':y+15}]
    for i,line in enumerate(card['footer']):
        texts.append({'text':line,'x':90,'y':1030+i*45,'size':25,'color':'muted','max_x':2470,'max_y':1100})
    return texts
def render_svg(card):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="1440" viewBox="0 0 2560 1440">',
           '<title>'+escape(card['title'])+'</title>','<desc>Source/actual explanation; not gameplay capture or signoff.</desc>',
           '<rect width="2560" height="1440" fill="'+P['bg']+'"/>',
           '<rect x="90" y="275" width="2380" height="680" rx="12" fill="'+P['panel']+'"/>']
    for t in layout(card):
        parts.append('<text x="{x}" y="{y}" font-size="{size}" font-family="{font}" fill="{fill}">{value}</text>'.format(**t,font=FONT,fill=P[t['color']],value=escape(t['text'])))
    parts.append('</svg>\n')
    return '\n'.join(parts)
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    for card in CARDS:
        with (args.output_dir/(card['id']+'.svg')).open('x',encoding='utf-8',newline='\n') as out: out.write(render_svg(card))
if __name__=='__main__': main()
