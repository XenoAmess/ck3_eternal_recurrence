from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
src=ROOT/'advance_materialized_checkpoint_a10.py';dst=ROOT/'advance_materialized_checkpoint_a11.py'
data=src.read_bytes()
old=b"m.require(all(values[key]==value for key,value in pair['source_values'].items() if key!='revision') and values['revision']==prior_request['expected_revision'],'Current native source/session changed after save, or provider revision differs from actual rejected request')"
new=b"m.require(values==review['source_values'],'Current source/session differs from the actual post-save root review snapshot')"
assert data.count(old)==1
data=data.replace(old,new).replace(b'scoped-a09-',b'scoped-a11-')
with dst.open('xb') as stream:stream.write(data)
def ident(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper()}
with (ROOT/'post-save-stamp-advance-derivation-a11.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump({'original':ident(src),'derived':ident(dst),
        'proof_source':'Actual root review was captured after the main save: provider6/native5/snapshot native:5. Pair.source_values was read before that save: provider5/native4. No day was submitted.',
        'only_logic_change':'Bind all current snapshot fields exactly to the post-save root review, rather than the pre-save request snapshot.',
        'only_label_change':'New create-only readonly/admission/day/finish request labels scoped-a11',
        'actual_checkpoint_sequence_read_from_saved_pair':True,'runtime_source_Dll_unchanged':True},stream,indent=2);stream.write('\n')
print(str(dst))
