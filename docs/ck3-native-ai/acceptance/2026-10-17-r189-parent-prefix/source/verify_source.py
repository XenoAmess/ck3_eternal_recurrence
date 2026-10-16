"""stdlib-only held-byte verifier; does not open any EXE or run native code."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parent
def verify():
 raw=(ROOT/'3E4BC50.bin').read_bytes();meta=json.loads((ROOT/'3E4BC50.actual.json').read_bytes())
 assert len(raw)==604 and hashlib.sha256(raw).hexdigest()=='739ddc4eb092e1df091617be4a4724a0a673d41cfb76698a96a623bb82545c40'
 assert meta['all_extent_bytes_decoded'] and meta['decoded_bytes']==604 and meta['extent']['begin_rva']=='3E4BC50'
 cursor=0x3E4BC50;joined=b'';count=0
 for line in (ROOT/'3E4BC50.asm').read_text().splitlines():
  if not line or line.startswith(';'):continue
  address,hexbytes,*rest=line.split();part=bytes.fromhex(hexbytes)
  assert int(address,16)==cursor;cursor+=len(part);joined+=part;count+=1
 assert joined==raw and cursor==0x3E4BEAC and count==162
 pins={
  0x3E4BC6D:'4863b18c000000', # signed count from expressionblock+8C
  0x3E4BC7D:'7e61',           # <=0 skips first loop
  0x3E4BC90:'498b9780000000', # expressionblock+80 array
  0x3E4BCB5:'ff5028',         # provider vtable+28 dispatch, not slot2
  0x3E4BCC1:'e8cad6a2fc',     # helper879390, no callee source read
  0x3E4BCCE:'4983c630',       # first record stride30
  0x3E4BCE0:'41837f0c00',     # separate pre-expression count+C
  0x3E4BCF4:'0f8492010000',   # count0 -> success epilogue, after possible literal loop
  0x3E4BD20:'498b87b0000000', # variable index array+B0
  0x3E4BD3B:'3b4b0c',         # compare index to existing variable count
  0x3E4BD47:'480303',         # existing variable buffer pointer
  0x3E4BD50:'488b18',         # receiver pointer read from existing variable
  0x3E4BE5B:'498b4620',       # preparation record's final target+20
  0x3E4BE5F:'ffd0',           # target call, not a pure memory getter
  0x3E4BE68:'4983c540',       # pre-expression stride40
  0x3E4BE88:'32c0',0x3E4BE8C:'b001'}
 for address,hexbytes in pins.items():
  expected=bytes.fromhex(hexbytes);assert raw[address-0x3E4BC50:address-0x3E4BC50+len(expected)]==expected
 assert 0x3E4BC7F+struct.unpack_from('<b',raw,0x3E4BC7E-0x3E4BC50)[0]==0x3E4BCE0
 assert 0x3E4BCFA+struct.unpack_from('<i',raw,0x3E4BCF6-0x3E4BC50)[0]==0x3E4BE8C
 ledger=json.loads((ROOT/'IO-LEDGER.actual.json').read_bytes())
 assert ledger['bytes']==dict(metadata=40,function=604) and len(ledger['reads'])==4
 for stage in ('metadata','body'):
  receipt=json.loads((ROOT/('READ-'+stage+'.actual.json')).read_bytes())
  assert receipt['error'] is None and receipt['exe_stat_before']==receipt['exe_stat_after']
  assert not receipt['whole_EXE_hash_recomputed']
 result=dict(status='PASS_HELD_BYTES_AND_DECLARED_SOURCE_PINS',instruction_pins=len(pins),
  complete_body_bytes=604,linear_instruction_count=162,new_metadata_bytes=40,new_code_bytes=604,new_EXE_read_count=4,
  native_execution_performed=False,semantic_correctness_verified_by_test=False,
  evidence_boundary='Checks complete held bytes/branch destinations and source instruction pins; human source review supplies semantics. No provider/helper/transitive effects or R189 preparation counts are inferred.')
 return result
if __name__=='__main__':print(json.dumps(verify()))
