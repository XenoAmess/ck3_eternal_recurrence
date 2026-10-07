from pathlib import Path
from hashlib import sha256
import json,difflib
O=Path(__file__).parent;old=O/'source003/author_i4_arguments.py'
before=old.read_text(encoding='utf-8')
needle="need(type(c['current_event_instance_id']) is int and c['current_event_instance_id']>=0,'Actual event instance required')"
new=needle+"\n        need(type(s.get('active_event')) is dict and s['active_event'].get('instance_id')==c['current_event_instance_id'],'Fresh snapshot event instance differs')"
assert before.count(needle)==1;after=before.replace(needle,new)
S=O/'source004';S.mkdir(exist_ok=False);(S/'author_i4_arguments.py').write_bytes(after.encode('utf-8'))
for name in ['SOURCE-BINDING.actual.json','SOURCE-CONTRACTS.json']:(S/name).write_bytes((old.parent/name).read_bytes())
(O/'SOURCE003-to-SOURCE004.patch').write_bytes(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='SOURCE003/author_i4_arguments.py',tofile='SOURCE004/author_i4_arguments.py')).encode())
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
v={'before':ref(old),'after':ref(S/'author_i4_arguments.py'),'patch':ref(O/'SOURCE003-to-SOURCE004.patch'),'reason':'Synthetic contract test17 exposed query context instance different from fresh snapshot active event; require exact same instance before selection. No source ordinals inferred.','preserved_failed_suite':ref(O/'suite-source003/RESULT.fixture.json'),'game_SDK_calls':0,'formal_credit':None}
(O/'SOURCE004-DELTA.json').write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(v))
