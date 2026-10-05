from pathlib import Path
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
def ref(p):
    r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
for rel in ['c3-i3b-current-main-delta-applicability-20261005-001','lyd-i3b-detached-authority-source-review-20261005-001/review-package-002',
            'c3-i3b-optional-target-guard-candidate-20261005-001','c3-i3b-preview-scope-review-20261005-001',
            'c3-human-challenger-route-readonly-20261005-001','c2-preview-scopefix-full-candidate-20261005-003']:
    p=B/rel; print('PACKAGE',rel)
    for path in sorted(p.glob('*.json')):
        value=json.loads(path.read_bytes());print('REF',ref(path))
        if path.name=='INDEX.json':
            if 'files' in value:
                rows=value['files'];print('INDEX FILE COUNT',len(rows),'FIRST',rows[:1])
            else:print('INDEX SHAPE',type(value).__name__,'FIRSTKEYS',list(value)[:3],'FIRSTVALUE',str(next(iter(value.values())))[:240])
        elif path.name in {'REPORT.json','STATUS.json','RESULT.json'}:
            if path.name=='REPORT.json' and 'applicability' in rel:print(json.dumps(value,ensure_ascii=False))
            else:
                print('REPORTKEYS',list(value))
                for key in ['status','result','scope','tests','source_refs','cases','native','limitations','checks','outputs','runtime_delta','fixed_blocks']:
                    if key in value:print(key,json.dumps(value[key],ensure_ascii=False)[:3000])
applied=json.loads((B/'root-c3-i3b-apply-20261005-001/APPLIED.json').read_bytes())
print('ROOT26 PATHS',[r['path'] for r in applied['plan']['files']])
guards=json.loads((B/'root-c3-optional-guards-apply-20261005-001/APPLIED.json').read_bytes())
print('GUARDS INPUTS',json.dumps(guards['inputs']))
permanent=Path('C:/workspace/ck3_eternal_recurrence/docs/li-yu-dao/acceptance/2026-10-05-r0009-followup-source-l0/RESULT.json')
print('PERMANENT C2',ref(permanent));v=json.loads(permanent.read_bytes());print('KEYS',list(v));print(json.dumps(v,ensure_ascii=False)[:3500])
