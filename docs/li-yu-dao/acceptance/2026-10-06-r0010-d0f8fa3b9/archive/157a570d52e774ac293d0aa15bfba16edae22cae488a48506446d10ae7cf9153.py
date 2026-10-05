import json
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;RUN=BASE/'live-attempt-010'
d=json.loads((RUN/'COLD-SOURCE-INVENTORY.json').read_text(encoding='utf-8-sig'))
print('TOP',list(d))
for mod in d['enabled_mods']:print('MOD',json.dumps({k:v for k,v in mod.items() if k!='files'},ensure_ascii=False));print('C2FILES',json.dumps([f for f in mod['files'] if 'c2' in f.get('relative_path','')],ensure_ascii=False))
def visit(v,path=''):
    if isinstance(v,dict):
        if any(isinstance(x,str) and any(w in x for w in ['c2_runtime','c2_events','lifecycle','lyd_events','school_runtime']) for x in v.values()):print(path,json.dumps(v,ensure_ascii=False))
        for k,x in v.items():visit(x,path+'/'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):visit(x,path+'/'+str(i))
visit(d)
for f in sorted((RUN/'mcp-client-evidence-002').glob('00[2-3]*.sdk-result.json')):print('SDK',f.name)
