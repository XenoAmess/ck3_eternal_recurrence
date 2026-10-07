from pathlib import Path
from hashlib import sha256
import json,difflib
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=Path(__file__).parent
old=B/'i4-argument-author-r17-source-review-fix-20261007-002/author_i4_arguments.py'
before=old.read_text(encoding='utf-8')
needle="need(ref(row['path'])==row,'Actual descriptor differs');return json.loads(Path(row['path']).read_bytes())"
new="actual=ref(row['path']);need(Path(actual['path']).resolve()==Path(row['path']).resolve() and actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'],'Actual descriptor differs');return json.loads(Path(row['path']).read_bytes())"
assert before.count(needle)==1;after=before.replace(needle,new)
S=O/'source003';S.mkdir(exist_ok=False)
(S/'author_i4_arguments.py').write_bytes(after.encode('utf-8'))
for name in ['SOURCE-BINDING.actual.json','SOURCE-CONTRACTS.json']:(S/name).write_bytes((old.parent/name).read_bytes())
(O/'SOURCE002-to-SOURCE003.patch').write_bytes(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='SOURCE002/author_i4_arguments.py',tofile='SOURCE003/author_i4_arguments.py')).encode('utf-8'))
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
manifest={'before':ref(old),'after':ref(S/'author_i4_arguments.py'),'patch':ref(O/'SOURCE002-to-SOURCE003.patch'),'reason':'Actual PREPARED guard descriptor uses Windows backslash path, ref normalizes slash spelling. Compare resolved same path+exact raw bytes/SHA. Original descriptor stays unchanged.','game_SDK_calls':0,'formal_credit':None}
(O/'SOURCE003-DELTA.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(manifest))
