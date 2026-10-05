from pathlib import Path
import ast,json
P=Path('C:/workspace/ck3_lyd_runtime_20261004/r10-claim-verifier-source-author-20261005-001')
text=(P/'author_source007-revision-002.py').read_text(encoding='utf-8')
tree=ast.parse(text)
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name=='reviewed_runtime':print(ast.get_source_segment(text,node))
for line_no,line in enumerate(text.splitlines(),1):
    if 'runtime_delta' in line or 'complete_source_diff' in line:print(line_no,line)
print('TEMPLATE',(P/'APPROVED-PINS.template.json').read_text(encoding='utf-8'))
for rel in ['c3-i3b-production-implementation-20261005-001/INDEPENDENT-REVIEW-002-REF.json',
            'c3-i3b-production-implementation-20261005-001/evidence/independent-variant002-review-003/REPORT.json',
            'c3-i3b-current-main-delta-applicability-20261005-001/COMPOSITION-CHECK.json']:
    path=P.parent/rel;v=json.loads(path.read_bytes());print('INPUT',rel,'KEYS',list(v))
    if 'REF' in rel:print(json.dumps(v,ensure_ascii=False))
    elif 'COMPOSITION' in rel:
        print({k:v[k] for k in v if not isinstance(v[k],(dict,list))})
    else:print(json.dumps(v,ensure_ascii=False)[:7500])
