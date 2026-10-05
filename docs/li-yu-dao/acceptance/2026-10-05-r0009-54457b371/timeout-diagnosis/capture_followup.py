import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

root=Path(r'C:\workspace\ck3_lyd_runtime_20261004\live-attempt-009')
out=Path(__file__).parent/'snapshot-002'
out.mkdir(exist_ok=False)
paths=list((root/'mcp-client-evidence-001').glob('0056-*'))+list((root/'mcp-client-evidence-001').glob('0057-*'))
native=root/'native-evidence/8ffcb8420953481eade4610f3ff61781'
paths += [native/'0052-decision-confirm_outcome.json',native/'0055-event-select.json',native/'0056-snapshot.json']
claims=root/'native-state/native-session/ingame-decision-item-actions'
paths += list(claims.glob('96fb70500892b3e1220cef32ad6a132cf2e9adc578ef79e66e60fab1057655d8*'))
paths += [root/'mcp-client-evidence-001/server.stderr.log',root/'root-mcp-start-exec-001/stdout.bin']
manifest={'start_utc':datetime.now(timezone.utc).isoformat(),'fixed_prefix_policy':True,'files':[]}
for p in paths:
    stat=p.stat()
    with p.open('rb') as stream:
        data=stream.read(stat.st_size)
    after=p.stat()
    rel=p.relative_to(root)
    dst=out/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('xb') as stream:
        stream.write(data)
    manifest['files'].append({'source':str(p),'relative':str(rel),'prefix_byte_bound':stat.st_size,'copied_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source_before_mtime_ns':stat.st_mtime_ns,'source_after_mtime_ns':after.st_mtime_ns,'source_after_bytes':after.st_size,'changed_during_read':(stat.st_size,stat.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)})
    if p.name.endswith(('.request.json','.response.json')):
        print('FILE',str(rel),data.decode('utf-8'))
    elif rel.parts[0]=='native-evidence':
        value=json.loads(data)
        print('NATIVE',str(rel),'bytes',len(data),'recorded',value.get('recorded_at_utc'),'status',value.get('status'))
        result=value.get('result',{})
        print('RESULT',json.dumps({k:v for k,v in result.items() if not isinstance(v,(list,dict))},ensure_ascii=False))
        for k in ('event_selection',):
            if k in result:
                print(k,json.dumps(result[k],ensure_ascii=False))
        for k in ('snapshot','snapshot_before','snapshot_after'):
            s=value.get(k)
            if s:
                print(k,json.dumps({kk:s.get(kk) for kk in ('revision','native_revision','date_raw','paused','active_event','played_character_gold','played_character_prestige','played_character_piety')},ensure_ascii=False))
manifest['end_utc']=datetime.now(timezone.utc).isoformat()
(out/'capture-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CAPTURE',json.dumps({'output':str(out),'files':len(manifest['files']),'total_bytes':sum(v['copied_bytes'] for v in manifest['files']),'changed':[v['relative'] for v in manifest['files'] if v['changed_during_read']]},ensure_ascii=False))
