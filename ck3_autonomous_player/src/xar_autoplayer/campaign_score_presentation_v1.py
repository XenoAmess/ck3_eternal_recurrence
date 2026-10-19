"""Pure presentation for campaign-development-score/v1 reports.

No game, native bridge, host identity or current-film dependency. Pillow is
imported only when drawing; callers supply regular/bold Chinese font paths.
"""
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path

FPS = 30
DURATION_SECONDS = 15
FRAMES = DURATION_SECONDS * FPS
WIDTH, HEIGHT = 2560, 1440
KEYS = "LEMUDH"
WEIGHTS = {"L": Q(1,4), "E": Q(1,4), "M": Q(3,20), "U": Q(1,10), "D": Q(3,20), "H": Q(1,10)}

def need(condition, message):
 if not condition:
  raise ValueError(message)

@lru_cache(maxsize=32)
def _font(path, size):
 try:
  from PIL import ImageFont
 except ImportError as exc:
  raise RuntimeError("Pillow is required to draw campaign scores") from exc
 return ImageFont.truetype(path, size)

def validate_report(s):
 need(s['schema']=='xar.ck3.campaign-development-score/v1' and s['qualification']['status'] in ('FINAL_STATE_ONLY','BOUNDED_INCOMPLETE','COMPLETE_COMPARABLE','NOT_COMPARABLE') and set(s['scores'])==set(KEYS),'Score v1 contract')
 for k in KEYS:
  r=s['scores'][k];lo=Q(r['lower']);hi=Q(r['upper']);need(0<=lo<=hi<=100 and Q(str(r['weight']))==WEIGHTS[k] and type(r['known'])is bool,'Domain score format_interval/weight');need(r['value'] is None or (r['known'] and lo==hi==Q(r['value'])),'No fabricated exact domain');need(type(r['label_zh'])is str and len(r['label_zh'])<=30,'Bounded domain label')
 a=s['aggregate']['A_state'];need(Q(a['lower'])==sum(Q(s['scores'][k]['lower'])*WEIGHTS[k] for k in KEYS) and Q(a['upper'])==sum(Q(s['scores'][k]['upper'])*WEIGHTS[k] for k in KEYS),'Weighted state format_interval')
 need(a['value'] is None or Q(a['lower'])==Q(a['upper'])==Q(a['value']),'No format_interval midpoint presented as exact');score30=s['aggregate']['S30'];need(type(score30['available'])is bool and (score30['available'] or score30['value'] is None),'Unavailable thirty-year score')
 if s['qualification']['status']!='COMPLETE_COMPARABLE':need(not score30['available'] and score30['value'] is None,'Incomplete history cannot become thirty-year score')
 need(len(s['display_steps'])<=32 and len(s['facts'])<=64 and len(s['unknown_fields'])<=128 and len(s['sources'])<=128,'Finite score explanation')
 need(all(type(x['source_refs'])is list for x in s['display_steps']+s['facts']) and type(s['snapshot']['date'])is str,'Explicit fact sources and actual date');return s

def format_number(x,direction=None):
 q=Q(x);scaled=q*10
 if direction=='down':n=scaled.numerator//scaled.denominator
 elif direction=='up':n=-((-scaled.numerator)//scaled.denominator)
 else:
  if q.denominator==1:return str(q.numerator)
  n=(scaled+Q(1,2)).numerator//(scaled+Q(1,2)).denominator
 return ('≈' if direction is None else '')+str(n//10)+'.'+str(n%10)

def format_interval(r):return format_number(r['value']) if r.get('value') is not None else format_number(r['lower'],'down')+'–'+format_number(r['upper'],'up')

def storyboard(s):
 validate_report(s);chapters=[{'id':'scope','start_frame':0,'end_frame':30,'title':'先看清评分口径'}]
 for i,k in enumerate(KEYS):chapters.append({'id':k,'start_frame':30+i*45,'end_frame':75+i*45,'title':s['scores'][k]['label_zh']})
 chapters += [{'id':'aggregate','start_frame':300,'end_frame':360,'title':'合成当前局面评分'},{'id':'facts','start_frame':360,'end_frame':FRAMES,'title':'主要得失与未确认信息'}];return chapters

def draw_score_frame(s,frame,font_path,bold_font_path,summary=False,campaign_title='战役发展报告'):
 FONT=Path(font_path);BOLD=Path(bold_font_path)
 try:
  from PIL import Image,ImageDraw
 except ImportError as exc:
  raise RuntimeError("Pillow is required to draw campaign scores; install it in your chosen Python environment") from exc
 need(type(frame)is int and 0<=frame<FRAMES,'Declared animation frame');chapters=storyboard(s);ch=next(c for c in chapters if c['start_frame']<=frame<c['end_frame']);img=Image.new('RGB',(2560,1440),'#0c1522');d=ImageDraw.Draw(img);cache={}
 def font(n,bold=False):
  key=(n,bold)
  if key not in cache:cache[key]=_font(str(BOLD if bold else FONT),n)
  return cache[key]
 def text(x,y,t,n=30,fill='#d9e3ec',bold=False):d.text((x,y),str(t),font=font(n,bold),fill=fill)
 def wrap(t,width,n=30):
  lines=[];line=''
  for c in str(t).replace('\n',' '):
   if d.textlength(line+c,font=font(n))>width and line:lines.append(line);line=''
   line+=c
  if line:lines.append(line)
  return lines
 def paragraph(x,y,t,width,n=30,lines=3,fill='#a9b9c9'):
  rows=wrap(t,width,n)
  for j,line in enumerate(rows[:lines]):text(x,y+j*(n+14),line if j<lines-1 or len(rows)<=lines else line[:-1]+'…',n,fill)
 def panel(box):d.rounded_rectangle(box,24,fill='#142337',outline='#2b4054',width=2)
 text(86,54,campaign_title,30,'#c8ae72');text(86,104,'战役局面评分',60,'#f2f0e9',True)
 text(88,194,'存档日期 '+s['snapshot']['date']+'    当前统治者 '+str(s['snapshot'].get('actor_name') or s['snapshot']['actor_id']),30,'#a9b9c9')
 qual=s['qualification']['status'];warning='完整可比评分' if qual=='COMPLETE_COMPARABLE' else '历史采样不完整 · 仅评价已确认的当前局面';text(88,250,warning,32,'#e2ba70',True)
 active=KEYS.index(ch['id']) if ch['id'] in KEYS else 5 if summary or ch['id'] in ('aggregate','facts') else -1
 for i,k in enumerate(KEYS):
  row=s['scores'][k];x=88+(i%2)*768;y=326+(i//2)*224;panel((x,y,x+730,y+198));on=summary or i<=active;color='#69c8b3' if on else '#536a7d';text(x+26,y+20,row['label_zh'],33,'#f0eee6',True);text(x+568,y+28,str(int(WEIGHTS[k]*100))+'%',27,'#a6b6c7')
  shown=format_interval(row) if on else '待展开';text(x+26,y+74,shown,43,color,True);text(x+300,y+88,'已确认' if row['value'] is not None else '数据区间',25,'#9db0c1')
  bx=x+28;by=y+153;bw=674;d.rounded_rectangle((bx,by,bx+bw,by+16),8,fill='#263b50')
  if on:
   progress=1 if summary or i<active or ch['id'] not in KEYS else min(1,(frame-ch['start_frame'])/12);lo=float(Q(row['lower']))/100;hi=float(Q(row['upper']))/100
   if hi>0:d.rectangle((bx,by,bx+bw*hi*progress,by+16),fill='#345b65')
   if lo>0:d.rectangle((bx,by,bx+bw*lo*progress,by+16),fill=color)
   if lo!=hi:d.line((bx+bw*hi*progress,by-5,bx+bw*hi*progress,by+22),fill='#dcbd78',width=3)
 panel((1656,326,2472,1000));text(1690,354,ch['title'] if not summary else '当前局面总览',38,'#e8d3a2',True)
 a=s['aggregate']['A_state'];text(1690,422,'当前局面 A',27,'#a9b9c9');text(1690,466,format_interval(a),70,'#77d0bb',True);text(1690,562,'满分 100 · 六项按权重相加',25,'#a9b9c9')
 if active>=0:
  subtotal={'lower':str(sum(Q(s['scores'][k]['lower'])*WEIGHTS[k] for k in KEYS[:active+1])),'upper':str(sum(Q(s['scores'][k]['upper'])*WEIGHTS[k] for k in KEYS[:active+1])),'value':None};text(1690,620,'已展开项目贡献 '+format_interval(subtotal),30,'#d9e3ec')
 if ch['id'] in KEYS and not summary:
  step=next((x for x in s['display_steps'] if x['id']==ch['id']),None);paragraph(1690,690,(step['value_text']+'。'+step['explanation_zh']) if step else '按已确认数据计算；缺失信息保留上下界，不代入猜测值。',738,30,5)
 else:paragraph(1690,680,s['qualification']['reason_zh'],738,30,5)
 panel((88,1044,2472,1312));s30=s['aggregate']['S30'];text(120,1070,'三十年总分  '+(format_interval(s30) if s30['available'] else '无法完整计算'),36,'#e8d3a2',True)
 facts=s['facts'][:2] if ch['id']!='facts' and not summary else s['facts'][:3];line='   ·   '.join(x['label_zh']+'：'+x['value_text'] for x in facts);paragraph(120,1138,line or '等待有来源的数据；当前不作确定结论。',2320,29,2)
 missing='；'.join(x['name'] for x in s['unknown_fields'][:6]);text(120,1250,'未确认：'+(missing[:83]+'…' if len(missing)>83 else missing or '当前必需字段已覆盖'),24,'#9bafc1')
 text(88,1352,'区间表示证据允许的范围，不是误差条或预测；当前局面分不等于完整三十年成绩。',25,'#8298aa');d.rectangle((0,1428,int(2560*(frame+1)/FRAMES),1440),fill='#c7ad74');return img

def synthetic_report():
 scores={k:{'label_zh':label,'weight':str(WEIGHTS[k]),'lower':'0','upper':'100','value':None,'known':False} for k,label in zip(KEYS,['领地与生产','财政与偿付','军事保障','治理稳定','家族与宗族','合法继承'])};return {'schema':'xar.ck3.campaign-development-score/v1','qualification':{'status':'FINAL_STATE_ONLY','reason_zh':'仅为软件构造例：没有开局基线和360个月历史。当前状态区间不能冒充三十年总成绩。'},'snapshot':{'date':'软件构造例','actor_id':'fixture','actor_name':'示例人物'},'scores':scores,'aggregate':{'A_state':{'lower':'0','upper':'100','value':None},'A_end':None,'S30':{'lower':'0','upper':'1000','value':None,'available':False},'delta_from_baseline':None},'display_steps':[{'id':k,'title_zh':scores[k]['label_zh'],'value_text':'0–100','explanation_zh':'软件构造例，未知数据保留区间，不把中点展示为实际成绩。','source_refs':[]} for k in KEYS],'facts':[{'label_zh':'证据范围','value_text':'软件构造例，不是实机成绩','source_refs':[]}],'unknown_fields':[{'name':'开局基线、月度历史','reason_zh':'本例未提供'}],'sources':[]}
