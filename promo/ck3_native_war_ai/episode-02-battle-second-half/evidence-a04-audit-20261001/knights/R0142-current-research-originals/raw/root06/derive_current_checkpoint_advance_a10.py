from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
src=ROOT/'advance_materialized_checkpoint_a09.py';dst=ROOT/'advance_materialized_checkpoint_a10.py'
data=src.read_bytes()
old=b"prior_request['parameters']['checkpoint_sequence']"
assert data.count(old)==1
data=data.replace(old,b"prior_request['checkpoint_sequence']")
old=b"m.require(values==pair['source_values'],'Current source/session changed after main before save')"
new=b"m.require(all(values[key]==value for key,value in pair['source_values'].items() if key!='revision') and values['revision']==prior_request['expected_revision'],'Current native source/session changed after save, or provider revision differs from actual rejected request')"
assert data.count(old)==1
data=data.replace(old,new)
with dst.open('xb') as stream:stream.write(data)
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT/'current-checkpoint-advance-derivation-a10.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump({'original':ident(src),'derived':ident(dst),
        'actual_schema_fix':'Private request parameters are top-level, as preserved in the actual 376-byte request',
        'actual_revision_rule':'Save increments provider revision; native revision/world/session/paused/date remain identical. Require current provider revision equals the original rejected BEGIN expected_revision.',
        'prior_failed_advance_a09_before_any_submission':True,'runtime_source_Dll_unchanged':True},stream,indent=2);stream.write('\n')
print(str(dst))
