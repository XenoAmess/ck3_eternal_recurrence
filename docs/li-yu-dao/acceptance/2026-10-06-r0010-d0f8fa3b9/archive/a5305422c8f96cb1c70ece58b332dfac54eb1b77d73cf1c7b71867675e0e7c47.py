import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;SOURCE=HERE.parent/'r10-actual-eighth-post-join-readback-20261006-001/inspect_delta_v2.py'
def pin(p):
    p=Path(p);d=p.read_bytes();return {'path':str(p),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}
s=SOURCE.read_text(encoding='utf-8');mapping={'r10-actual-eighth-precommit-readback-20261006-001':'r10-actual-detach-second-precommit-readback-20261006-001','before187':'before235','post-JOIN':'post-DETACH'}
for old,new in mapping.items():s=s.replace(old,new)
with (HERE/'inspect_delta.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
with (HERE/'INSPECTOR-REUSE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'source':pin(SOURCE),'new':pin(HERE/'inspect_delta.py'),'parameter_changes':mapping,'JSON_cache_only':True,'old_save_reparse':False},f,ensure_ascii=False,indent=2);f.write('\n')
