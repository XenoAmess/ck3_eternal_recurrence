from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
R=B/'r10-root-head-export-20261005-001'
v=json.loads((R/'REPORT.json').read_bytes());print('EXPORT KEYS',list(v));print(json.dumps(v,ensure_ascii=False)[:6500])
P=B/'root-c3-failed-tests-final-l0-20261005-001'
print('FINAL TEST ROOT',[p.name for p in P.iterdir()])
for path in P.rglob('*.json'):
    v=json.loads(path.read_bytes());print('RECEIPT',str(path.relative_to(P)),'KEYS',list(v),'SUMMARY',{k:x for k,x in v.items() if isinstance(x,(str,bool,int,float))})
