from pathlib import Path
import hashlib,json
b=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
p=b/'decode_R0142_four_endpoints_a01.py';q=b/'decode_R0142_four_endpoints_a02.py'
raw=p.read_bytes();old=b"else2\n";new=b"else 2\n"
assert raw.count(old)==1
with q.open('xb')as f:f.write(raw.replace(old,new))
compile(q.read_text(encoding='utf-8'),str(q),'exec')
print(json.dumps({'new_file':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest().upper(),'old_syntax_failure_preserved':True}))
