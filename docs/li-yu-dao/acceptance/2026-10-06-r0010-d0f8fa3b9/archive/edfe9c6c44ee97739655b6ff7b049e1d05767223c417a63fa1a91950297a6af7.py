from pathlib import Path
import json,hashlib,difflib
O=Path(__file__).resolve().parent;M=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao');R9=Path('C:/lr9s2/mod_li_yu_dao')
P=O/'production-author-inputs-001';P.mkdir(exist_ok=False)
def sha(d):return hashlib.sha256(d).hexdigest()
def ref(p):
    d=p.read_bytes();return {'path':str(p),'bytes':len(d),'sha256':sha(d)}
def files(root):
    return {p.relative_to(root).as_posix():p for p in (root/'tools').rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('test_') and p.suffix not in {'.pyc','.pyo'}}
def copy(d,p):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(d)
a=files(R9);b=files(M);assert set(a)==set(b)
rows=[];delta=[]
for rel in sorted(a):
    x=a[rel].read_bytes();y=b[rel].read_bytes()
    before=P/'before'/rel;after=P/'after'/rel
    copy(x,before);copy(y,after)
    row={'path':rel,'before':ref(before),'after':ref(after),'current_original':ref(b[rel])};rows.append(row)
    if x!=y:
        patch=''.join(difflib.unified_diff(x.decode('utf-8-sig').splitlines(True),y.decode('utf-8-sig').splitlines(True),fromfile='R9/'+rel,tofile='CURRENT/'+rel)).encode('utf-8')
        diff=P/'diff'/(rel+'.diff');copy(patch,diff)
        delta.append({**row,'diff':ref(diff)})
lineage=json.loads((O/'lineage-002/COMPLETE-RUNTIME-LINEAGE.json').read_bytes())
expected={r['path'] for r in lineage['production_authored_current_exact_bound']}
assert {r['path'] for r in delta}==expected,({r['path'] for r in delta}-expected,expected-{r['path'] for r in delta})
for row in rows:assert ref(M/row['path'])['sha256']==row['after']['sha256']
result={'schema':'lyd.r10.mod-production-author-source-closure-review.v1','status':'SOURCE_ONLY_REVIEWED',
 'scope':'Complete mod tools non-test input closure, including generators, templates, data, build/static helpers and reference JSON. Complete runtime70 is separately reviewed. README/docs/fixtures/test bodies and entire native/Python export are outside this production-source scope.',
 'before_source_root':str(R9),'current_source_root':str(M),'source_input_count':len(rows),'changed_source_input_count':len(delta),
 'unchanged_source_input_count':len(rows)-len(delta),'added_paths':[],'removed_paths':[],'all_rows':rows,'source_delta':delta,
 'changed_source_paths_exactly_match_12_reviewed_C2_C3_I3b_authors':True,
 'C2_current_template_CRLF_to_LF_only':'392 CRLF lines in source candidate normalize byte-exact to current LF; runtime bytes remain unchanged by normalization.',
 'source_lineage':ref(O/'lineage-002/COMPLETE-RUNTIME-LINEAGE.json'),'tests_executed':0,'native':'NOT_RUN','Git_calls':0,'main_mutations':0}
with (P/'FULL-MOD-PRODUCTION-SOURCE-REVIEW.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'status':'SOURCE_ONLY_REVIEWED','source_input_count':len(rows),'source_delta_count':len(delta),'review':ref(P/'FULL-MOD-PRODUCTION-SOURCE-REVIEW.json')}))
