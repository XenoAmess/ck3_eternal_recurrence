from pathlib import Path
import json,hashlib
ROOT=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/mcp-client-001')
for p in sorted(ROOT.iterdir()):
 if not p.name.startswith(('0024-','0025-')) or not ('.native-01.json' in p.name or '.sdk-result.json' in p.name):continue
 raw=p.read_bytes();v=json.loads(raw);print('FILE',json.dumps({'path':p.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}));print('TOP',list(v))
 if '.native-' in p.name:print('VALUE',json.dumps(v,ensure_ascii=False)[:2400])
 else:
  structured=v.get('structuredContent',{});print('SDK',json.dumps({'isError':v.get('isError'),'structuredContent':structured},ensure_ascii=False)[:2400])
