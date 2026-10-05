import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
root=Path(r'C:\workspace\ck3_lyd_runtime_20261004\live-attempt-009')
out=Path(__file__).parent/'snapshot-003'
out.mkdir(exist_ok=False)
paths=list((root/'mcp-client-evidence-001').glob('0058-*'))+[root/'native-evidence/8ffcb8420953481eade4610f3ff61781/0057-checkpoint.json']
manifest={'start_utc':datetime.now(timezone.utc).isoformat(),'policy':'fixed initial byte bound; read only source; new external copies','files':[]}
summary={}
for src in paths:
    before=src.stat()
    with src.open('rb') as stream:
        data=stream.read(before.st_size)
    after=src.stat()
    target=out/src.relative_to(root)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    info={'source':str(src),'relative':str(src.relative_to(root)),'prefix_byte_bound':before.st_size,'copied_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source_before_mtime_ns':before.st_mtime_ns,'source_after_mtime_ns':after.st_mtime_ns,'source_after_bytes':after.st_size,'changed_during_read':(before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns)}
    manifest['files'].append(info)
    decoded=json.loads(data)
    if src.name.endswith('checkpoint.json'):
        summary={'source':str(src),'sha256':info['sha256'],'bytes':len(data),'status':decoded['status'],'recorded_at_utc':decoded['recorded_at_utc'],'checkpoint':decoded['result']['checkpoint'],'submission':decoded['result']['submission'],'frame':{k:decoded['snapshot_after'][k] for k in ('revision','native_revision','date_raw','paused','active_event','played_character_gold','played_character_prestige','played_character_piety')}}
    elif src.name.endswith('response.json'):
        print('RESPONSE',json.dumps(decoded,ensure_ascii=False))
manifest['end_utc']=datetime.now(timezone.utc).isoformat()
(out/'capture-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'checkpoint-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
