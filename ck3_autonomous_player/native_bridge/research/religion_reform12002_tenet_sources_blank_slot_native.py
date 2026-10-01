"""Exact native missing-selected-Tenet -> default-definition slot proof; no CK3."""
from pathlib import Path
import argparse,hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86 import X86_OP_MEM,X86_REG_RIP
from scan_anchors import PeImage

SHA='ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
SPAN_SHA='715c7e94807fc7a722bb7f3971a907d8727a8da4dc6981a33146bff443c71ec0'
ANCHORS={
 0x14F70B0:'lea rsi, [r14 + 0xb28]',
 0x14F70B7:'lea r12, [r14 + 0x778]',
 0x14F7185:'cmp r15d, dword ptr [rsi + 0x14]',
 0x14F7189:'jge 0x14f7195',
 0x14F718B:'mov rax, qword ptr [rsi + 8]',
 0x14F718F:'mov r13, qword ptr [rcx + rax]',
 0x14F7195:'mov r13, qword ptr [rip + 0x4828524]',
 0x14F719C:'mov edx, dword ptr [r14 + 0x784]',
 0x14F71E2:'imul rdx, rax, 0x70',
 0x14F7205:'mov r8, r13',
 0x14F7212:'call 0xee0220',
 0x14F7247:'imul rcx, rax, 0x70',
 0x14F7252:'mov r8, r13',
 0x14F725F:'call 0xee0220',
 0x14F7264:'inc dword ptr [r12 + 0xc]',
 0x14F7281:'jl 0x14f7180',
}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 data=a.exe.read_bytes();assert hashlib.sha256(data).hexdigest()==SHA
 pe=PeImage(data);md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 start,end=0x14F6E40,0x14F7E1F
 opt=struct.unpack_from('<I',data,0x3C)[0]+24;pdva,pdsize=struct.unpack_from('<II',data,opt+112+3*8);off=pe.rva_to_offset(pdva)
 assert (start,end)in{(b,e)for b,e,_ in struct.iter_unpack('<III',data[off:off+pdsize])}
 raw=data[pe.rva_to_offset(start):pe.rva_to_offset(start)+end-start];assert hashlib.sha256(raw).hexdigest()==SPAN_SHA
 result={'schema':'xar.ck3_12002.tenet_empty_selected_slot_native.v1','executable_sha256':SHA,'new_span':{'start_rva':hex(start),'end_exclusive_rva':hex(end),'sha256':SPAN_SHA},'anchors':[],'local_ck3_touched':False,'native_default_definition_global_rva':'0x5d1f6c0','empty_slot_native_semantics':'missing draft-selected definition -> native default singleton -> actual slot constructor with real slot index'}
 for rva,expected in ANCHORS.items():
  off=pe.rva_to_offset(rva);i=next(md.disasm(data[off:off+15],rva));actual=f'{i.mnemonic} {i.op_str}';assert actual==expected,(hex(rva),actual)
  row={'rva':hex(rva),'bytes':i.bytes.hex(),'instruction':actual}
  if rva==0x14F7195:
   targets=[i.address+i.size+x.mem.disp for x in i.operands if x.type==X86_OP_MEM and x.mem.base==X86_REG_RIP];assert targets==[0x5D1F6C0];row['rip_targets']=[hex(x)for x in targets]
  result['anchors'].append(row)
 result['status']='GREEN';a.output_dir.mkdir(parents=True,exist_ok=True)
 (a.output_dir/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(f'GREEN one new native blank-slot span / {len(ANCHORS)} anchors / exact default global5D1F6C0; no CK3')


if __name__=='__main__':main()
