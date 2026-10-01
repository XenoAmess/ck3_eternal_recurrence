"""Exact new model/cache/Founder and corrected array-descriptor proof; no CK3."""
from pathlib import Path
import argparse,hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86 import X86_OP_MEM,X86_REG_RIP
from scan_anchors import PeImage
SHA='AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
SPANS={
 'inline_category_construction':(0x14F244E,0x14F24AD),
 'show_window_materialize':(0x14F1950,0x14F1E52),
 'show_window_sort':(0x14F1E60,0x14F2030),
 'show_window_gui_wrapper':(0x14FAA20,0x14FAAB4),
 'show_window_sort_gui_wrapper':(0x14FABB0,0x14FAC44),
 'actual_doctrine_array_index48':(0x1510920,0x1510985),
 'actual_doctrine_item_constructor':(0xEE1E80,0xEE1FD4),
 'rebuild_current_tenet_status_groups':(0x14F3E60,0x14F4338),
 'founder_registration':(0x22C060,0x22C242),
 'founder_typed_getter':(0x14FBBB0,0x14FBC12),
 'founder_full_id_leaf':(0x14F0E70,0x14F0E7C),
 'selected_slots_array_leaf':(0x14F0E90,0x14F0E98),
}
ANCHORS={
 0x14F244E:('mov','qword ptr [r14 + 0x888], r14'),
 0x14F24A2:('mov','dword ptr [r14 + 0x8d8], 0xffffffff'),
 0x14F19CF:('mov','dword ptr [r14 + 0x50], r10d'),
 0x14F19D3:('lea','rcx, [r10 + r10*8]'),
 0x14F19D7:('mov','rax, qword ptr [r9 + 0x790]'),
 0x14F19DE:('mov','rax, qword ptr [rax + rcx*8 + 0x28]'),
 0x14F19E7:('mov','rax, qword ptr [rax + 0xb08]'),
 0x14F19F6:('call','0xee3640'),0x14F1A02:('call','0xee35d0'),
 0x14F1A0B:('mov','r15, qword ptr [rax + 0x140]'),
 0x14F1A12:('movsxd','rax, dword ptr [rax + 0x14c]'),
 0x14F1A6D:('add','rdx, 0x48'),0x14F1A97:('call','0x372df30'),
 0x14F1B12:('call','0xee1e80'),0x14F1B91:('lea','rcx, [rcx + 0x48]'),
 0x1510953:('lea','rcx, [rbx + rbx*8]'),0x151095C:('lea','rax, [r8 + rcx*8]'),
 0x14F1E4D:('jmp','0x14f3e60'),0x14F3EA0:('call','0xee9290'),
 0x14F3EA7:('mov','dword ptr [r12 + 0xc], edi'),
 0x14FBBBE:('call','0x14f0e70'),0x14F0E70:('mov','eax, dword ptr [rcx + 0xcc]'),
 0x14F0E90:('lea','rax, [rcx + 0x790]'),
}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 data=a.exe.read_bytes();assert hashlib.sha256(data).hexdigest().upper()==SHA
 pe=PeImage(data);md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True;out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 result={'executable_sha256':SHA,'spans':{},'anchors':{},'layout':{'selected_slots':0x790,'actual_item_stride':0x48,'definition':0x28,'group':0xB08,'group_definition_sources':0x140,'category':0x888,'category_selected_slot':0x50,'category_doctrines':0x20,'category_tenets':0x38,'tenet_groups':0x7A8,'founder_full_id':0xCC},'scope':'actual_selected_slot_group_definition_sources and current materialized category caches'}
 for name,(start,end) in SPANS.items():
  o=pe.rva_to_offset(start);body=data[o:o+end-start];ins=list(md.disasm(body,start))
  (out/(name+'.txt')).write_text('\n'.join(f'{i.address:X} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf-8')
  result['spans'][name]={'start_rva':hex(start),'end_rva':hex(end),'sha256':hashlib.sha256(body).hexdigest()}
 for r,(mnemonic,op) in ANCHORS.items():
  o=pe.rva_to_offset(r);i=next(md.disasm(data[o:o+15],r));assert (i.mnemonic,i.op_str)==(mnemonic,op),(hex(r),i.mnemonic,i.op_str)
  result['anchors'][hex(r)]={'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
 for site,target in ((0x14FA982,0x4435128),(0x22C13A,0x14FBBB0)):
  o=pe.rva_to_offset(site);i=next(md.disasm(data[o:o+15],site));targets=[i.address+i.size+x.mem.disp for x in i.operands if x.type==X86_OP_MEM and x.mem.base==X86_REG_RIP];assert targets==[target]
  result['anchors'][hex(site)]={'bytes':i.bytes.hex(),'target_rva':hex(target)}
 descriptor=struct.unpack_from('<Q',data,pe.rva_to_offset(0x4435128))[0]-pe.image_base
 index=struct.unpack_from('<Q',data,pe.rva_to_offset(descriptor)+16)[0]-pe.image_base
 assert (descriptor,index)==(0x45657B8,0x1510920)
 result['corrected_array_descriptor']={'descriptor_rva':'0x4435128','vtable_rva':hex(descriptor),'index_getter_rva':hex(index),'stride':72,'historical_wrong_index_rva':'0x1514980','historical_wrong_stride':80}
 result.update(status='GREEN',local_ck3_touched=False,readiness='static-ready')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(f'GREEN model native spans={len(SPANS)} anchors={len(result["anchors"])}')
if __name__=='__main__':main()
