from pathlib import Path
import json,sys
b=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0142-four-save-endpoint-audit-reinforcement-a02')
v=json.loads((b/'before-pre-ui-checkpoint-full-selected-saved-projection.json').read_text(encoding='utf-8'))
def shape(v,level=0):
 if not isinstance(v,list):return v
 if level>2:return {'count':len(v),'keys':[r.get('key')for r in v][:30]}
 return [{'key':r['key'],'value':shape(r['value'],level+1)}for r in v]
s=[{'path':r['path'],'shape':shape(r['entries'])}for r in v['objects']['matched_combat_blocks']]
with(b/'saved-combat-original-shape-a01.json').open('x',encoding='utf-8',newline='\n')as f:json.dump(s,f,ensure_ascii=False,indent=2);f.write('\n')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(s,ensure_ascii=False))
