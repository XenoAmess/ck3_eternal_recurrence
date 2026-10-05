from pathlib import Path
import json,hashlib
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
def show(rel):
    p=B/rel;raw=p.read_bytes();v=json.loads(raw);print('REF',str(p),len(raw),hashlib.sha256(raw).hexdigest())
    print('KEYS',list(v))
    if 'APPLIED' in p.name:
        for k,value in v.items():
            if isinstance(value,list):print(k,'COUNT',len(value),'FIRST',value[:1])
            elif isinstance(value,dict):print(k,'DICTKEYS',list(value))
            else:print(k,value)
    elif 'INDEX' in p.name:
        files=v.get('files',[]);print('PAYLOAD',v.get('payload_files',v.get('file_count')),len(files),'FIRST',files[:1]);print('REPORTS',[r.get('path') for r in files if any(x in r.get('path','').lower() for x in ['report','applied','root-apply','source-input','current-main'])][:25])
    else:print(json.dumps(v,ensure_ascii=False)[:3500])
for rel in ['root-c3-i3b-apply-20261005-001/APPLIED.json','root-c3-optional-guards-apply-20261005-001/APPLIED.json',
    'c3-i3b-current-main-delta-applicability-20261005-001/INDEX.json','lyd-i3b-detached-authority-source-review-20261005-001/review-package-002/INDEX.json',
    'c3-i3b-optional-target-guard-candidate-20261005-001/INDEX.json','c3-i3b-optional-target-guard-candidate-20261005-001/handoff-001/ROOT-APPLY-INPUTS.json',
    'c2-preview-scopefix-full-candidate-20261005-003/INDEX.json','c2-preview-scopefix-full-candidate-20261005-003/DELTA.json',
    'r9-root-head-export-20261005-002/production/mod_li_yu_dao.manifest.json']:
    show(rel)
