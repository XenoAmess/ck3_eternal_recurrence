from pathlib import Path
import json,hashlib
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
for rel in ['c2-preview-scopefix-full-candidate-20261005-003/DELTA.json','c3-i3b-detached-authority-implementation-20261005-001/INDEX.json',
    'c3-i3b-current-main-delta-applicability-20261005-001/CURRENT-TARGETBEFORE-SHA.json',
    'c3-i3b-optional-target-guard-candidate-20261005-001/handoff-001/ROOT-APPLY-INPUTS.json',
    'lyd-c3-native-primitives-independent-review-20261005-001/variant002-source-review-003/REPORT.json',
    'root-c3-guards-final-l0-20261005-001/policy/RESULT.json','root-c3-guards-final-l0-20261005-001/RESULT.json']:
    p=B/rel
    if not p.exists():print('MISSING',rel);continue
    data=p.read_bytes();v=json.loads(data);print('REF',rel,len(data),hashlib.sha256(data).hexdigest());print('KEYS',list(v))
    if 'c2-' in rel:
        value=v['complete_runtime_relative_to_frozen_544'];print('COMPLETE SHAPE',type(value).__name__)
        if isinstance(value,dict):
            print('COMPLETE KEYS',list(value))
            for k,x in value.items():print('SUB',k,type(x).__name__,len(x) if isinstance(x,(list,dict)) else x,str(x)[:900])
        else:print('ROWS',len(value),str(value[:1])[:900])
    elif 'CURRENT-' in rel:print('FILES SAMPLE',str(v)[:1200])
    elif 'variant002' in rel:
        for k,x in v.items():
            if isinstance(x,(dict,list)):print(k,len(x))
            else:print(k,x)
    elif 'INDEX' in rel:print('INDEX SAMPLE',str(v)[:700])
    else:print(json.dumps(v,ensure_ascii=False)[:1700])
