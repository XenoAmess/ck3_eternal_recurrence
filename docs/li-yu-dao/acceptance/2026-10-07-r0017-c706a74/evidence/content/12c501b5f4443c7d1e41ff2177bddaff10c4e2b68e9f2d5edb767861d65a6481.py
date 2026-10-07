from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
for rel in ['r17-actual-sdk-metadata-20261007-001/RESULT.json','r17-actual-consumer-source-20261007-001/INDEX.json','live-attempt-017/PREPARED.json']:
 p=B/rel;v=json.loads(p.read_bytes());print(rel,list(v));print(json.dumps(v,ensure_ascii=False)[:15500])
run=B/'live-attempt-017'
for p in run.iterdir():
 if p.is_dir():
  for q in p.iterdir():
   if q.is_file() and q.name in ['ready.json','CLIENT-START.actual.json','RESULT.json']:print('CANDIDATE',q.as_posix(),q.stat().st_size)
for p in B.iterdir():
 if p.is_dir() and 'r17' in p.name.lower() and any(x in p.name.lower() for x in ['baseline','B0','initial','client','query','checkpoint','preservation']):
  print('PACKAGE',p.as_posix())
  for q in p.iterdir():
   if q.is_file() and q.name in ['INDEX.json','RESULT.json','INPUT.json']:print('FILE',q.as_posix(),q.stat().st_size)
