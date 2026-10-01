"""Freeze the exact current Rite creation window publication and readonly root ABI."""
from __future__ import annotations
import argparse, hashlib, json, re, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
ROOT = NATIVE.parent.parent
SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
CONSTANTS = {'kDraftIdlerVtableRva':0x44BC408,'kDraftHandlerVtableRva':0x44BA890,
    'kDraftWindowPrimaryVtableRva':0x4565C30,'kDraftWindowSecondaryVtableRva':0x4565C08,
    'kDraftWindowVisibilityRva':0x21603A0,'kDraftHandlerFromIdlerOffset':0x88,
    'kDraftWindowFromHandlerOffset':0x278,'kDraftWindowOwnerOffset':0xA0,
    'kDraftWindowRiteIdOffset':0xC8,'kDraftWindowActorIdOffset':0xCC}
SPANS = [('CRiteCreationWindow.constructor',0x14F21F0,0x14F268F),
    ('CIngameInterfaceHandler.publish_rite_creation_window',0xB07EE0,0xB07F6C),
    ('CWindow.IsVisible',0x21603A0,0x2160430),
    ('root_idler_handler_layout_reused_accessor',0xB20140,0xB201FF)]
SITES = [('window_allocator_size',0xB07EF1),('window_constructor_call',0xB07F09),
    ('window_owner_publication',0xB07F18),('window_owned_handler',0x14F2264),
    ('window_primary_vtable',0x14F2289),('window_secondary_vtable',0x14F2293),
    ('window_initial_rite_and_actor_absent',0x14F229E),('window_visibility_ui_root',0x21603AA),
    ('jomini_global_root',0xB20148),('idler_from_root',0xB20158),
    ('handler_from_idler',0xB2017E)]

def extract(exe:Path)->tuple[dict,str]:
    data=exe.read_bytes()
    if hashlib.sha256(data).hexdigest().upper()!=SHA:raise ValueError('Not the frozen CK3 1.20.0.2 executable')
    pe=PeImage(data); cs=Cs(CS_ARCH_X86,CS_MODE_64); cs.detail=True
    def read(rva:int,size:int)->bytes:
        at=pe.rva_to_offset(rva); return data[at:at+size]
    source=(NATIVE/'include/xar_bridge/religion_reform12002_window.hpp').read_text(encoding='utf-8-sig')
    for key,value in CONSTANTS.items():
        match=re.search(r'\b'+re.escape(key)+r'\s*=\s*(0x[0-9A-Fa-f]+)',source)
        if not match or int(match.group(1),0)!=value:raise ValueError('Actual source constant differs: '+key)
    spans=[]; dumps=[]
    for name,start,end in SPANS:
        raw=read(start,end-start)
        spans.append({'name':name,'start_rva':hex(start),'end_exclusive_rva':hex(end),
            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex(' ')})
        dumps.append(name+'\n'+'\n'.join(f'{i.address:08X} {i.mnemonic:8} {i.op_str}' for i in cs.disasm(raw,start)))
    sites=[]
    for name,rva in SITES:
        i=next(cs.disasm(read(rva,15),rva))
        sites.append({'name':name,'rva':hex(rva),'bytes':i.bytes.hex(' '),'instruction':i.mnemonic+' '+i.op_str,
            'rip_targets':[hex(i.address+i.size+o.mem.disp) for o in i.operands if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP],
            'call_targets':[hex(o.imm) for o in i.operands if o.type==X86_OP_IMM and i.mnemonic=='call']})
    classes=[]
    for cls,expected,vt,col,offset in [('CRiteCreationWindow',0x57A59F0,0x4565C30,0x4B71388,0),
        ('CRiteCreationWindow',0x57A59F0,0x4565C08,0x4B712C0,16)]:
        name=('.?AV'+cls+'@@').encode()+b'\0'
        at=data.find(name)
        if at<0 or pe.offset_to_rva(at)-16!=expected:raise ValueError('Exact RTTI mismatch '+cls)
        fields=struct.unpack('<6I',read(col,24))
        if fields[0]!=1 or fields[1]!=offset or fields[3]!=expected or fields[5]!=col:
            raise ValueError('Exact COL mismatch '+cls)
        if struct.unpack('<Q',read(vt-8,8))[0]!=pe.image_base+col:raise ValueError('Vtable COL mismatch')
        count=4 if offset else 10
        classes.append({'class':cls,'type_descriptor_rva':hex(expected),'col_rva':hex(col),
            'base_offset':offset,'vtable_rva':hex(vt),'function_rvas':[
                hex(struct.unpack('<Q',read(vt+8*j,8))[0]-pe.image_base) for j in range(count)]})
    return {'schema':'ck3_12002_current_rite_creation_window_static_abi_v1','game_version':'1.20.0.2',
        'executable_sha256':SHA,'executable_size':len(data),'readiness':'static-confirmed',
        'source_constants':{k:hex(v) for k,v in CONSTANTS.items()},'complete_functions':spans,
        'semantic_instructions':sites,'exact_class_vtables':classes,
        'reused_root_evidence':'ck3_1_20_0_2_event_window_context.json; ck3_1_20_0_2_title_map.json',
        'scope':'existing visible current player CRiteCreationWindow draft only; no window creation/opening',
        'live_verified':False,'local_ck3_touched':False},'\n\n'.join(dumps)+'\n'

def main()->int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--record',action='store_true')
    a=p.parse_args(); result,dump=extract(a.exe)
    manifest=HERE/'religion_reform12002_window_abi.json'
    if a.record:manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    elif json.loads(manifest.read_text(encoding='utf-8'))!=result:raise ValueError('Frozen ABI differs')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'native-disassembly.txt').write_text(dump,encoding='utf-8')
    receipt={'status':'GREEN','readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'complete_functions':len(SPANS),'semantic_instructions':len(SITES),'exact_class_vtables':len(result['exact_class_vtables']),
        'source_constants':len(CONSTANTS),'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
    (a.output_dir/'native-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))
    return 0
if __name__=='__main__':raise SystemExit(main())
