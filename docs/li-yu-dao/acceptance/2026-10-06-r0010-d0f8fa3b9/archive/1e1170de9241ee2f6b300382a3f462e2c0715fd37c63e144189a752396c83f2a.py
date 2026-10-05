from pathlib import Path
import json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
for rel in ['c3-i3b-current-main-delta-applicability-20261005-001','c3-i3b-optional-target-guard-candidate-20261005-001']:
    p=B/rel;v=json.loads((p/'INDEX.json').read_bytes());print('INDEX',rel)
    for k,value in v.items():
        if isinstance(value,list):print(k,'COUNT',len(value),'FIRST',str(value[:1])[:700])
        elif isinstance(value,dict):print(k,'KEYS',list(value)[:12],'SAMPLE',str(value)[:1000])
        else:print(k,value)
for rel in ['c3-i3b-preview-scope-review-20261005-001','c3-i3b-production-implementation-20261005-001','c3-i3b-detached-authority-implementation-20261005-001',
            'root-c3-guards-final-l0-20261005-001','root-c3-i3b-combination-l0-20261005-001']:
    p=B/rel;print('DIRECTORY',rel)
    print('ROOTFILES',[x.name for x in p.iterdir()])
    print('REPORT PATHS',[str(x.relative_to(p)) for x in p.rglob('REPORT.json')])
v=json.loads((B/'root-c3-guards-final-l0-20261005-001/policy/preview.json').read_bytes())
print('GUARDJSON',list(v))
for k,value in v.items():
    if k=='cases':print('cases',len(value),all(r['accepted']==r['expected'] and r['undefined_reads']==0 for r in value))
    elif k=='guard_removal_mutants':print(k,len(value))
    else:print(k,str(value)[:400])
