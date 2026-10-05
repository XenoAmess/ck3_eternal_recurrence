import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def pin(p):
    p=Path(p);r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
p=HERE/'inspect_delta.py';s=p.read_text(encoding='utf-8');s=s.replace("for k in sorted(set(d1)|set(d2))", "for k in sorted(set(d1)|set(d2),key=lambda k:(k is not None,str(k)))")
s=s.replace("def entries(d):return {n['key']:n['value'] for n in d}","def entries(d):\n    out={}\n    for n in d:out.setdefault(n['key'],[]).append(n)\n    return out")
with (HERE/'inspect_delta_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
with (HERE/'INSPECTION-FAILURE-PRESERVED.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'failed_original_script':pin(p),'failure':'TypeError ordering None and string top AST keys in JSON-only inspector, before output write','replacement_script':pin(HERE/'inspect_delta_v2.py'),'fix':'Preserve complete duplicate-key AST groups, handle null keys explicitly','actual_save_AST_parse_count_unchanged':1,'old_saves_reparsed':False},f,ensure_ascii=False,indent=2);f.write('\n')
