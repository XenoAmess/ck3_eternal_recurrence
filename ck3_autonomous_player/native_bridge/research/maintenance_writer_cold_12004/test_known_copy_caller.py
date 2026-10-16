from pathlib import Path
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import struct
import sys

R=Path(__file__).resolve().parent
REL=Path('ck3_autonomous_player/native_bridge/research/maintenance_writer_cold_12004')

def need(ok,message):
    if not ok:
        raise RuntimeError(message)

p=R/'consume_writer_actual.py'
spec=importlib.util.spec_from_file_location('candidate_actual_reader',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
# Independent byte-decoding of the already-held source prologue. No EXE reads.
b=bytes.fromhex(m.COPY_PROLOGUE_HEX)
need(b[:15]==bytes.fromhex('48895c2410488974241848897c2420'),'Saved-reg prologue differs')
cursor=15
push_bytes=0
while cursor<len(b):
    if b[cursor]==0x55:
        push_bytes+=8;cursor+=1
    elif b[cursor:cursor+2] in [bytes([0x41,x]) for x in range(0x54,0x58)]:
        push_bytes+=8;cursor+=2
    else:
        break
need(b[cursor:cursor+4]==bytes.fromhex('488d6c24'),'RBP LEA differs')
rbp_displacement=int.from_bytes(b[cursor+4:cursor+5],'little',signed=True)
cursor+=5
need(b[cursor:cursor+3]==bytes.fromhex('4881ec'),'RSP allocation differs')
allocation=int.from_bytes(b[cursor+3:cursor+7],'little')
entry_rsp=0x100008
rsp=entry_rsp-push_bytes-allocation
rbp=entry_rsp-push_bytes+rbp_displacement
need(push_bytes==40 and entry_rsp-rsp==0x178 and entry_rsp-rbp==0x78,'Source-derived return-slot offsets differ')
stack=bytearray(0x400)
stack_base=entry_rsp-0x200
native_return=0x140123456 # Synthetic caller; never a game/source observation.
struct.pack_into('<Q',stack,entry_rsp-stack_base,native_return)
def read_slot(address):
    return struct.unpack_from('<Q',stack,address-stack_base)[0]

start=dict(admission_generation=7,module_base=0x140000000,module_size=102518784)
regs=dict(rsp=rsp,rbp=rbp,r9=0x300000,rsi=0x200000)
row=dict(slot=0,RIP_after_rva=0x28A645B,registers=regs,context=regs['r9'],character=regs['rsi'])
leaf=dict(source_entry_rva='28A63E0',source_raw_sha256=m.COPY_SOURCE_SHA,capture_ordinal=1,
          admission_generation=7,prologue_matches=True,frame_relation_matches=True,
          register_context_matches=True,identity_after=True,return_slot_address=entry_rsp,
          read_before_complete=True,read_after_complete=True,
          return_before=read_slot(rsp+0x178),return_after=read_slot(rbp+0x78),
          return_stable=True,candidate_return_absolute=native_return,candidate_return_rva=0x123456)
row['known_copy_caller_v1']=leaf
results=[]
value=m.project_known_copy_caller(row,start,3)
need(value['caller_return_rva']==0x123456 and value['thread_generation']==3
     and value['admission_generation']==7 and value['instruction_start'] is None
     and value['known_c_d_producer'] is False,'Source-derived synthetic stack caller failed')
results.append(dict(case='source_prologue_to_real_synthetic_stack_slot',pass_=True,game_credit=False))
changed=copy.deepcopy(row)
changed['known_copy_caller_v1'].update(return_after=native_return+8,return_stable=False,
                                     candidate_return_absolute=None,candidate_return_rva=None)
value=m.project_known_copy_caller(changed,start,3)
need(value['caller_return_absolute'] is None and not value['return_stable'],'Changed slot was projected as a caller')
results.append(dict(case='two_completed_reads_changed_return_stays_unknown',pass_=True,game_credit=False))
bad_frame=copy.deepcopy(row)
bad_frame['registers']['rbp']+=8
bad_frame['known_copy_caller_v1'].update(frame_relation_matches=False,identity_after=False,
    return_slot_address=None,read_before_complete=False,read_after_complete=False,
    return_before=None,return_after=None,return_stable=False,
    candidate_return_absolute=None,candidate_return_rva=None)
value=m.project_known_copy_caller(bad_frame,start,3)
need(value['caller_return_absolute'] is None and value['return_slot_address'] is None,
     'Unqualified synthetic stack layout gained a caller')
results.append(dict(case='wrong_frame_retains_unavailable_and_no_slot_read',pass_=True,game_credit=False))
legacy=copy.deepcopy(row)
del legacy['known_copy_caller_v1']
need(m.project_known_copy_caller(legacy,start,3) is None,'Old raw was required to invent stack bytes')
results.append(dict(case='legacy_raw_has_no_caller_value',pass_=True,game_credit=False))
report=dict(schema='xar.e04.known-copy-caller.focused-stack-test.v1',status='PASS',
    at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python_optimization=sys.flags.optimize,
    candidate_reader_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
    source_prologue_hex=m.COPY_PROLOGUE_HEX,push_bytes=push_bytes,stack_allocation=allocation,
    source_derived_rsp_offset=entry_rsp-rsp,source_derived_rbp_offset=entry_rsp-rbp,
    cases=results,native_compile_executed=False,native_fixture_executed=False,CK3_observed=False,
    maintenance_attribution='unclosed')
parser=argparse.ArgumentParser(description='Focused synthetic known-copy caller stack tests; no runtime actions')
parser.add_argument('--output',type=Path,required=True)
out=parser.parse_args().output
with out.open('x',encoding='utf-8') as f:
    json.dump(report,f,separators=(',',':'))
print(json.dumps({'status':'PASS','cases':len(results),'receipt':str(out),'bytes':out.stat().st_size}))
