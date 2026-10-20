from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
root=Path(__file__).resolve().parent
old=root/'TIMING-CASH-READBACK.actual.json'
original=old.read_bytes();v=json.loads(original)
for row in v['rows']:
    if 'rows' in row:
        row['rows']=[{k:r[k] for k in ('id','plan','started_at','ok','finished_at') if k in r} for r in row['rows']]
v['derived_projection_notice']='Host operation row metadata and clock result only; redundant after_snapshot and active_wars omitted. Original actual-results untouched.'
new=(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')
out=root/'TIMING-CASH-READBACK.compact-a02.actual.json'
correction=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
 retired_derived=dict(path=old.name,bytes=len(original),sha256=hashlib.sha256(original).hexdigest()),
 replacement=dict(path=out.name,bytes=len(new),sha256=hashlib.sha256(new).hexdigest()),
 reason='Remove redundant full after_snapshot/active_wars copied into own derived projection; retain exact source pins and small timing/clock/cash facts. No source actual evidence changed.',
 size_rule='All serialized bytes measured before write; both transient and final root <=131072.')
receipt=(json.dumps(correction,ensure_ascii=False,indent=2)+'\n').encode('utf8')
size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
assert size+len(new)+len(receipt)<=131072,(size,len(new),len(receipt))
out.write_bytes(new)
(root/'TIMING-DERIVED-COMPACTION.actual.json').write_bytes(receipt)
assert old.resolve().parent==root.resolve()
old.unlink()
print(json.dumps(correction));print('final_root_bytes',sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
