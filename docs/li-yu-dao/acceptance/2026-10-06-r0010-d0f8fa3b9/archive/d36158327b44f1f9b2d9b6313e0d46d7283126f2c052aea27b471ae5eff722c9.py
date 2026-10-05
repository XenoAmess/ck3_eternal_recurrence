from pathlib import Path
from fnmatch import fnmatchcase
from datetime import datetime,timezone
import ast,hashlib,json,re,difflib
O=Path(__file__).resolve().parent
B=Path('C:/workspace/ck3_lyd_runtime_20261004')
CURRENT=Path('C:/workspace/ck3_eternal_recurrence/mod_li_yu_dao')
BEFORE=Path('C:/lr9s2/mod_li_yu_dao')
MANIFEST=B/'r9-root-head-export-20261005-002/production/mod_li_yu_dao.manifest.json'
STAGING=MANIFEST.with_name('mod_li_yu_dao')
S=O/'snapshot-001';S.mkdir(exist_ok=False)
def sha(data):return hashlib.sha256(data).hexdigest()
def ref(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':sha(data)}
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def copy(data,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data)
def authority(root):
    raw=(root/'tools/build_release.py').read_bytes()
    tree=ast.parse(raw.decode('utf-8-sig'))
    values={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in {'REQUIRED_RUNTIME_FILES','RUNTIME_FAMILIES','SOURCE_ONLY_DIRS','RUNTIME_DIRS'}:
                if isinstance(node.value,ast.Call):
                    assert isinstance(node.value.func,ast.Name) and node.value.func.id=='frozenset'
                    values[name]=frozenset(ast.literal_eval(node.value.args[0]))
                else:values[name]=ast.literal_eval(node.value)
    assert len(values)==4
    return values,ref(root/'tools/build_release.py')
def collect(root,values):
    actual=set();unexpected=[]
    for path in root.rglob('*'):
        rel=path.relative_to(root).as_posix();parts=rel.split('/')
        if any(part in values['SOURCE_ONLY_DIRS'] for part in parts):continue
        assert not path.is_symlink(),rel
        if not path.is_file():continue
        allow=rel in values['REQUIRED_RUNTIME_FILES'] or (len(parts)==3 and any(fnmatchcase(rel,p) for p in values['RUNTIME_FAMILIES']))
        if allow:actual.add(rel)
        elif parts[0] in values['RUNTIME_DIRS'] or rel=='descriptor.mod':unexpected.append(rel)
    assert not unexpected and values['REQUIRED_RUNTIME_FILES']<=actual,(unexpected,values['REQUIRED_RUNTIME_FILES']-actual)
    return sorted(actual)
raw=MANIFEST.read_bytes();assert sha(raw)=='295e101d1bbefff3aeb2f18d5856f7f5b46ab2c2971005753d2eea6706939d15'
manifest=json.loads(raw);old={r['path']:r for r in manifest['files']}
v_before,authority_before=authority(BEFORE);v_after,authority_after=authority(CURRENT)
assert v_before==v_after
before_paths=collect(BEFORE,v_before);after_paths=collect(CURRENT,v_after)
assert before_paths==after_paths==sorted(old) and len(after_paths)==70
before_rows=[];after_rows=[];runtime_delta=[]
for rel in before_paths:
    a=(BEFORE/rel).read_bytes();b=(CURRENT/rel).read_bytes();stage=(STAGING/rel).read_bytes()
    assert a==stage and len(a)==old[rel]['size'] and sha(a)==old[rel]['sha256'],rel
    before_path=S/'before'/rel;after_path=S/'after'/rel
    copy(a,before_path);copy(b,after_path)
    r_before={'path':rel,'file':ref(before_path),'original_file':ref(BEFORE/rel),'staging_file':ref(STAGING/rel)}
    r_after={'path':rel,'file':ref(after_path),'original_file':ref(CURRENT/rel)}
    before_rows.append(r_before);after_rows.append(r_after)
    if a!=b:
        patch=''.join(difflib.unified_diff(a.decode('utf-8-sig').splitlines(True),b.decode('utf-8-sig').splitlines(True),fromfile='R9/'+rel,tofile='CURRENT/'+rel)).encode('utf-8')
        diff_path=S/'diff'/(rel+'.diff');copy(patch,diff_path)
        runtime_delta.append({'path':rel,'before':r_before['file'],'after':r_after['file'],'diff':ref(diff_path)})
for row in after_rows:
    actual=(CURRENT/row['path']).read_bytes();assert len(actual)==row['file']['bytes'] and sha(actual)==row['file']['sha256']
static_path=B/'root-c3-guards-final-l0-20261005-001/product/static.json'
static=json.loads(static_path.read_bytes())
assert static['result']=='GREEN' and static['runtime_file_count']==70
assert {r['path']:r['file']['sha256'] for r in after_rows}==static['runtime_sha256']
result={'schema':'lyd.r10.independent-full-runtime-snapshot.v1','status':'CURRENT_SOURCE_ONLY_70_REVIEW_INPUT_FROZEN',
 'utc':datetime.now(timezone.utc).isoformat(),'R9_manifest':ref(MANIFEST),'R9_git_sha_from_manifest':manifest['git_sha'],
 'R9_source_root':str(BEFORE),'current_source_root':str(CURRENT),'authority_before':authority_before,'authority_after':authority_after,
 'authority_constants_equal':True,'before_rows':before_rows,'after_rows':after_rows,'runtime_delta':runtime_delta,
 'changed_count':len(runtime_delta),'unchanged_count':70-len(runtime_delta),'added_paths':[],'removed_paths':[],
 'root_static_receipt':ref(static_path),'root_static70_current_bytes_exact':True,'readback_current_second_pass_exact':True,
 'final_Git_export':None,'native':'NOT_RUN','tests_executed':0,'main_mutations':0,'Git_calls':0}
save(S/'RUNTIME-SNAPSHOT.json',result)
print(json.dumps({'status':'PASS','before_count':70,'after_count':70,'changed_count':len(runtime_delta),'changed_paths':[r['path'] for r in runtime_delta],
 'root_static70_exact':True,'snapshot':ref(S/'RUNTIME-SNAPSHOT.json')},ensure_ascii=False))
