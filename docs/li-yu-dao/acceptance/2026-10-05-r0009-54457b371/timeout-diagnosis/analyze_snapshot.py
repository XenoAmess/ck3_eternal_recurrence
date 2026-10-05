import json
from pathlib import Path

base = Path(__file__).parent / 'snapshot-001'
manifest = json.loads((base/'capture-manifest.json').read_text(encoding='utf-8'))
print('LARGE FILES',json.dumps(sorted([{'path':v['relative'], 'bytes':v['copied_bytes']} for v in manifest['files']], key=lambda v:-v['bytes'])[:10],ensure_ascii=False))
for suffix in ('session.json', 'ROOT-ACTUAL-CLIENT-INVENTORY.json', 'root-mcp-start-exec-001/INPUTS.json'):
    p = (base/'mcp-client-evidence-001'/suffix) if suffix == 'session.json' else base/suffix
    print('SAVED', suffix, p.read_text(encoding='utf-8'))
for name in ('0048-0048-detach-review-confirm.native-01.json', '0050-0050-detach-sign.native-01.json','0051-0051-detach-signed-save.native-01.json', '0052-0052-detach-final-select.native-01.json','0054-0054-post-review-timeout-observe.native-01.json','0055-0055-detach-current-review-query.native-01.json'):
    p = base/'mcp-client-evidence-001'/name
    data=json.loads(p.read_text(encoding='utf-8'))
    print('NATIVE',name, 'TOP', [(k,type(v).__name__,len(v) if isinstance(v,(str,list,dict)) else v) for k,v in data.items()])
    for k,v in data.items():
        if isinstance(v,dict):
            print('CHILD',k,[(kk,type(vv).__name__,len(vv) if isinstance(vv,(str,list,dict)) else vv) for kk,vv in v.items()])
        elif isinstance(v,list):
            print('LIST',k,'LENGTH',len(v),'FIRST',str(v[0])[:1000] if v else None,'LAST',str(v[-1])[:1000] if v else None)
        elif not isinstance(v,str) or len(v)<200:
            print('SCALAR',k,v)
data=json.loads((base/'native-state/native-session/driver-state.json').read_text(encoding='utf-8'))
print('DRIVER TOP',[(k,type(v).__name__,len(v) if isinstance(v,(str,list,dict)) else v) for k,v in data.items()])
for k,v in data.items():
    if isinstance(v,dict):
        print('DRIVER CHILD',k,[(kk,type(vv).__name__,len(vv) if isinstance(vv,(str,list,dict)) else vv) for kk,vv in v.items()])
    elif isinstance(v,list):
        print('DRIVER LIST',k,'LENGTH',len(v),'LAST',str(v[-1])[:2000] if v else None)
    elif not isinstance(v,str) or len(v)<500:
        print('DRIVER SCALAR',k,v)
