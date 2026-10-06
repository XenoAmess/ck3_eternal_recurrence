from pathlib import Path
import json,hashlib,copy
R=Path('C:/ck3-war-episode04-research-20261004-a01/e4-final-review01-a01')
A=R/'actual-row-binding-a02';O=R/'actual-row-binding-a03'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def new(p,d):
 with p.open('x',encoding='utf-8',newline='\n') as f:
  if isinstance(d,str):f.write(d)
  else:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
assert not O.exists();O.mkdir()
rows=read(A/'picture-rows.json');md=(A/'ROOT-READABLE-PICTURE-ROWS.md').read_text(encoding='utf-8')
mapping={
 '完整 ID 与 37 项 DATA 逐行核对':'完整兵团身份与满员数逐项核对',
 'B 两侧真实库存按原生定点顺序计算':'按合军权重加权并取整',
 '统帅27357→33388；变化原因未知':'统帅身份改变；变化原因未知',
 '门禁停止':'对照条件变化，停止观察',
 '严格 ABC 比较未授予':'有采样偏差，不作严格对照',
 '严格比较未授予':'有采样偏差，不作严格对照',
 'C 严格比较未授予':'C 有采样偏差，不作严格对照',
 'B 停止；C 比较限制':'B 停止观察；C 比较限制',
}
for row in rows:
 row['title']=mapping.get(row['title'],row['title'])
 notes=[]
 for line in row['record_note']:
  for a,b in mapping.items():line=line.replace(a,b)
  # Avoid repeating the same limit in one caption.
  line=line.replace('C 多次采样偏差，有采样偏差，不作严格对照','C 多次采样偏差，不作严格对照')
  line=line.replace('多次采样偏差；有采样偏差，不作严格对照','多次采样偏差，不作严格对照')
  assert len(line)<=33,(row['id'],line,len(line))
  notes.append(line)
 row['record_note']=notes
 assert len(row['title'])<=22
for a,b in mapping.items():md=md.replace(a,b)
md=md.replace('C 多次采样偏差，有采样偏差，不作严格对照','C 多次采样偏差，不作严格对照').replace('多次采样偏差；有采样偏差，不作严格对照','多次采样偏差，不作严格对照')
# Source narration is untouched in JSON. The readable prose retains exact words.
for old,row in zip(read(A/'picture-rows.json'),rows):assert old['text_zh']==row['text_zh'] and old['text_en']==row['text_en'] and old['visuals']==row['visuals']
new(O/'picture-rows.json',rows);new(O/'ROOT-READABLE-PICTURE-ROWS.md',md)
pipe=read(A/'pipeline-input-PENDING-Root-review.json');pipe['final']['picture_rows']=rows;pipe['final']['picture_rows_json']=pin(O/'picture-rows.json');new(O/'pipeline-input-PENDING-Root-review.json',pipe)
gate=read(A/'Root-final-row-review-PENDING.json');gate['picture_rows_json']=pin(O/'picture-rows.json');gate['audience_card_only_revision']='Root requested player-readable labels; exact narration/ASS/source windows/PCM unchanged';new(O/'Root-final-row-review-PENDING.json',gate)
delivery={'schema':'xar.e04.actual-final-row-binding-delivery.v1','state':'ACTUAL_ROWS_READY_ROOT_REVIEW_PENDING','rows':pin(O/'picture-rows.json'),'readable_rows':pin(O/'ROOT-READABLE-PICTURE-ROWS.md'),'gate_PENDING':pin(O/'Root-final-row-review-PENDING.json'),'pipeline_input_PENDING':pin(O/'pipeline-input-PENDING-Root-review.json'),'pipeline':pin(R/'candidate-a04/bc_pipeline.py'),'original_actual_bindings':pin(A/'ROOT-DELIVERY.json'),'seconds':1735.776,'frames':52074,'new_media_or_TTS_or_render':0,'Root_approved_for_render':False}
new(O/'ROOT-DELIVERY.json',delivery)
print(json.dumps({'delivery':pin(O/'ROOT-DELIVERY.json'),**delivery},ensure_ascii=False,indent=2))
