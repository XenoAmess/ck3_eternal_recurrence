"""Exact Doctrine all-slot materialization-equivalence evidence; no CK3."""
from pathlib import Path
import argparse, hashlib, json
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage
SHA='AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
SPANS={
 'scope_rebuild':(0x14F8820,0x14F892B),
 'faith_scope_constructor':(0xEE5BF0,0xEE5CC5),
 'scope_copy':(0x373AF40,0x373AFDE),
 'scope_selected_list_copy':(0x373A450,0x373A667),
 'draft_selection_scope_refresh':(0x14F8660,0x14F8815),
 'draft_initial_scope_caller':(0x14F772A,0x14F7758),
 'draft_selected_definition_flag_list':(0x2592190,0x25923A5),
 'doctrine_item_cost_only_update':(0xEE21B0,0xEE2298),
 'doctrine_cache_clear':(0xEE3640,0xEE369B),
 'tenet_cache_clear':(0xEE35D0,0xEE3634),
}
ANCHORS={
 0x14F8851:('call','0xee5bf0'),
 0x14F8861:('lea','rdx, [rsi + 0x730]'),
 0x14F886D:('call','0x373a450'),
 0x14F8872:('mov','dword ptr [rsp + 0x20], 4'),
 0x14F888F:('call','0x373a110'),
 0x14F8894:('lea','rcx, [rsi + 0xd0]'),
 0x14F88A0:('call','0x373af40'),
 0xEE5C5C:('mov','eax, 0xd'),
 0xEE5CB8:('mov','qword ptr [rdi + 8], rax'),
 0x14F7739:('lea','rcx, [r14 + 0xb28]'),
 0x14F7740:('call','0x2592190'),
 0x14F774C:('mov','edx, dword ptr [r15 + 8]'),
 0x14F7753:('call','0x14f8820'),
 0x14F86FE:('mov','rdx, rax'),
 0x14F8704:('call','0x14f4de0'),
 0x14F87BA:('call','0x2592190'),
 0x14F87BF:('mov','edx, dword ptr [r13 + 8]'),
 0x14F87C6:('call','0x14f8820'),
 0x25921C4:('mov','rsi, qword ptr [rcx + 8]'),
 0x25921F2:('mov','dword ptr [rsp + 0x20], 0x28'),
 0x2592292:('mov','rsi, qword ptr [r13 + 0x50]'),
 0x25922BB:('mov','dword ptr [rsp + 0x20], 0x27'),
}
STOCK={
 'common/religion/doctrine_types/_doctrine_types.info':[(72,95)],
 'common/religion/doctrine_types/20_doctrines.txt':[(1087,1097),(1238,1255)],
 'gui/window_rite_creation.gui':[(987,995),(1247,1256)],
 'common/scripted_guis/pam_scripted_guis.txt':[(82,92)],
}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--exe',type=Path,required=True);p.add_argument('--stock-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 data=a.exe.read_bytes();assert hashlib.sha256(data).hexdigest().upper()==SHA
 pe=PeImage(data);md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 result={'executable_sha256':SHA,'game_version':'1.20.0.2','spans':{},'anchors':{},'stock':{},'reused_evidence':[
  'religion_reform12002_group_model_abi.json:12 spans / 25 anchors; ShowWindow14F1950, actual constructorEE1E80, group140, selected790/stride48',
  'religion_reform12002_choices_abi.json:EE4E60 definition-only CanPick; trigger372DF30; initialized prophet/native knowledge bindings',
  'research/religion_doctrine12002_selection_abi.json:EE4CC0 definition-only ShouldDisplay; corrected stride supplied by R6',
 ],'materialization_equivalence':{'doctrine':True,'scope':'all actual selected-slot group definition sources in one current draft','requires_fake_item':False,'requires_scope_construction':False,'requires_show_window':False,'tenet':'separate religion_reform12002_tenet_sources research'},'local_ck3_touched':False,'readiness':'research'}
 for name,(start,end) in SPANS.items():
  o=pe.rva_to_offset(start);body=data[o:o+end-start];ins=list(md.disasm(body,start))
  (out/(name+'.txt')).write_text('\n'.join(f'{i.address:X} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n',encoding='utf-8')
  result['spans'][name]={'start_rva':hex(start),'end_rva':hex(end),'sha256':hashlib.sha256(body).hexdigest(),'instruction_count':len(ins)}
 for r,(mnemonic,op) in ANCHORS.items():
  o=pe.rva_to_offset(r);i=next(md.disasm(data[o:o+15],r));assert (i.mnemonic,i.op_str)==(mnemonic,op),(hex(r),i.mnemonic,i.op_str)
  result['anchors'][hex(r)]={'bytes':i.bytes.hex(),'mnemonic':i.mnemonic,'operands':i.op_str}
 for site,target in ((0x14F883F,0x54DBC00),):
  o=pe.rva_to_offset(site);i=next(md.disasm(data[o:o+15],site));ts=[i.address+i.size+x.mem.disp for x in i.operands if x.type==X86_OP_MEM and x.mem.base==X86_REG_RIP];assert ts==[target]
  result['anchors'][hex(site)]={'bytes':i.bytes.hex(),'target_rva':hex(target)}
 for rel,ranges in STOCK.items():
  raw=(a.stock_root/rel).read_bytes();lines=raw.decode('utf-8-sig').splitlines()
  result['stock'][rel]={'sha256':hashlib.sha256(raw).hexdigest(),'excerpts':[{'first_line':first,'last_line':last,'text':'\n'.join(lines[first-1:last])} for first,last in ranges]}
 result['status']='GREEN'
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(f'GREEN fullchoices new native spans={len(SPANS)} anchors={len(result["anchors"])}; Doctrine materialization-equivalence closed')
if __name__=='__main__':main()
