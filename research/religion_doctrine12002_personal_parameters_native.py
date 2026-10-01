#!/usr/bin/env python3
"""One new exact-build proof: Character personal flag trigger and supported registry."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/native_bridge/research'))
from scan_anchors import PeImage
SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
CONSTANTS = {'kPersonalParameterCollectionGetterRva':0x28BD090,
    'kPersonalParameterDatabaseSlotRva':0x5D1DEB8,
    'kPersonalParameterCharacterExtensionOffset':0x1C8,
    'kPersonalParameterOwnedTenetsOffset':0x88,
    'kPersonalParameterDefinitionSetOffset':0x740,
    'kPersonalParameterSupportedSetOffset':0xF20}
SPANS = [('Character.has_personal_tenet_flag.validate',0x2B2BC30,0x2B2BD10),
    ('Character.has_personal_tenet_flag.evaluate',0x2B2BD10,0x2B2BDDF),
    ('Character.actual_owned_personal_tenets',0x28BD090,0x28BD12A),
    ('Tenet.parameter_registry.database_slot',0xA154B0,0xA15507)]
SITES = {0x2B2BC40:'call 0xa154b0',0x2B2BC49:'lea rcx, [rax + 0xf20]',
    0x2B2BC50:'call 0xb9de80',0x2B2BD64:'cmp qword ptr [rcx + 0x1c8], 0',
    0x2B2BD80:'call 0x28bd090',0x2B2BD88:'movsxd rax, dword ptr [rax + 0xc]',
    0x2B2BDA7:'add rcx, 0x740',0x2B2BDAE:'call 0xb9de80',
    0x28BD094:'mov rax, qword ptr [rcx + 0x1c8]',0x28BD0A0:'add rax, 0x88'}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();data=a.exe.read_bytes();assert hashlib.sha256(data).hexdigest()==SHA
    pe=PeImage(data);decoder=Cs(CS_ARCH_X86,CS_MODE_64)
    def read(rva,size):
        at=pe.rva_to_offset(rva);return data[at:at+size]
    header=(ROOT/'ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_personal_parameters.hpp').read_text(encoding='utf-8')
    for name,value in CONSTANTS.items():
        assert int(re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)',header).group(1),0)==value
    spans=[];dump=[]
    for name,start,end in SPANS:
        raw=read(start,end-start)
        spans.append({'name':name,'start_rva':hex(start),'end_exclusive_rva':hex(end),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex(' ')})
        dump.extend([name]+[f'{i.address:09X} {i.bytes.hex(" "):32s} {i.mnemonic} {i.op_str}' for i in decoder.disasm(raw,start)])
    sites=[]
    for at,expected in SITES.items():
        ins=next(decoder.disasm(read(at,15),at));actual=ins.mnemonic+' '+ins.op_str
        assert actual==expected,(hex(at),actual,expected)
        sites.append({'rva':hex(at),'instruction':actual,'bytes':ins.bytes.hex(' ')})
    assert struct.unpack('<i',read(0xA154B7,4))[0]+0xA154BB==0x5D1DEB8
    assert struct.unpack('<Q',read(0x47BEB30+25*8,8))[0]-pe.image_base==0x2B2BD10
    assert read(0x5A47A38+16,len('.?AVCHasPersonalTenetFlagTrigger@@')+1)==b'.?AVCHasPersonalTenetFlagTrigger@@\0'
    output=a.output_dir;output.mkdir(parents=True,exist_ok=True)
    manifest={'schema':'ck3_12002_character_personal_parameters_abi_v1','game_version':'1.20.0.2','executable_sha256':SHA,'executable_size':len(data),'readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,'constants':{k:hex(v) for k,v in CONSTANTS.items()},'complete_native_spans':spans,'semantic_instructions':sites,'trigger':{'type_descriptor_rva':'0x5a47a38','vtable_rva':'0x47beb30','evaluate_slot':25},'reused_frozen_abi':['religion_doctrine12002_tenet_abi.json: B9DE80 token membership and 3F4F900 token CString','religion_doctrine12002_tenet_rows_abi.json: Tenet CString+18/GDbo stable keys'], 'source_semantics':'Actual Character-owned collection; each supported token calls exact trigger membership on owned Tenet+740 only; extension absence is false; unknown supported registry key is unsupported; no Rite/Fulfillment merge','live_gap':'Paused production snapshot pending'}
    path=Path(__file__).with_name('religion_doctrine12002_personal_parameters_abi.json')
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    text='\n'.join(dump)+'\n';(output/'native-disassembly.txt').write_text(text,encoding='utf-8')
    receipt={'status':'GREEN','readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,'new_complete_native_spans':len(spans),'semantic_instructions':len(sites),'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'disassembly_sha256':hashlib.sha256(text.encode()).hexdigest()}
    (output/'native-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt));return 0
if __name__=='__main__':raise SystemExit(main())
