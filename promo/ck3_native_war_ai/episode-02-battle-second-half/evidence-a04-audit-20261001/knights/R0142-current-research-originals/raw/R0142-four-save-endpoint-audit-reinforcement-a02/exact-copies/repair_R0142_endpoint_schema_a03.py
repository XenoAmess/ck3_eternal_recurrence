from pathlib import Path
import json,hashlib
b=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
p=b/'decode_R0142_four_endpoints_a02.py';q=b/'decode_R0142_four_endpoints_a03.py'
raw=p.read_bytes();old=b"a['state']=='combat'";new=b"a['army_state']=='combat'"
assert raw.count(old)==1
raw=raw.replace(old,new)
oldname=b'R0142-four-save-endpoint-audit-reinforcement-a01';newname=b'R0142-four-save-endpoint-audit-reinforcement-a02'
assert raw.count(oldname)==1
with q.open('xb')as f:f.write(raw.replace(oldname,newname))
compile(q.read_text(encoding='utf-8'),str(q),'exec')
o=b/newname.decode();o.mkdir(exist_ok=False)
for name in ['monitor-original-schema-inspection.json','four-pair-input-shapes.json','actual-army-schema-a02.json']:
 with(o/name).open('xb')as f:f.write((b/oldname.decode()/name).read_bytes())
print(json.dumps({'path':str(q),'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest().upper(),'previous_schema_failure_preserved':True}))
