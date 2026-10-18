"""Stdlib byte/record verifier; field semantics require the linked source review."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
b=(r/'route-24AAD80.actual.bin').read_bytes()
v=json.loads((r/'source-contract.json').read_bytes())
if len(b)!=704 or hashlib.sha256(b).hexdigest()!='ce60c96b74109f03453b2d077c8acd0e5d6a080aa3003b56179614960fabc090':raise SystemExit('raw pin mismatch')
cursor=0x24AAD80
for row in v['instructions']:
 d=bytes.fromhex(row['bytes'])
 if row['rva']!=cursor or b[cursor-0x24AAD80:cursor-0x24AAD80+len(d)]!=d:raise SystemExit('instruction record gap/bytes')
 cursor+=len(d)
if cursor!=0x24AB040 or b[-15:]!=b'\xcc'*15 or b[-16]!=0xc3:raise SystemExit('body/padding boundary')
for row in v['field_pins']:
 d=bytes.fromhex(row['bytes']);o=row['rva']-0x24AAD80
 if b[o:o+len(d)]!=d:raise SystemExit('field operand bytes mismatch')
print(json.dumps(dict(status='GREEN',scope='record-and-source-byte-integrity',semantic_correctness_verified=False,live_execution_performed=False,machine_id=v['machine_id'],new_exe_reads=0)))
