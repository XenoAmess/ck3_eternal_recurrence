#!/usr/bin/env python3
"""Verify the frozen nonwar Rite model ABI and stock creation distinction offline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MAP = HERE / 'religion_reform12002_rite_abi.json'
HEADER = ROOT / 'ck3_autonomous_player/native_bridge/include/xar_bridge/religion_reform12002_rite.hpp'
CONSTANTS = {
    'kRiteIsMainRva': 0x24F7E40, 'kRiteDivergenceToMainRva': 0x2BDFBA0,
    'kFaithHeresyThresholdRva': 0x2440920,
    'kRiteFounderCharacterIdOffset': 0x4BC, 'kRiteHeadCharacterIdOffset': 0x4C0,
}
SPANS = [
    ('Rite.IsMain.core', 0x24F7E40, 0x24F7EA2, 'bool(CRite*)'),
    ('Rite.IsMain.thunk', 0x24FC0E0, 0x24FC118, 'reflection wrapper'),
    ('Faith.GetHeresyThreshold.core', 0x2440920, 0x2440974, 'int64_t*(CFaith*,int64_t*out)'),
    ('Faith.GetHeresyThreshold.thunk', 0x24435C0, 0x24435F7, 'reflection wrapper'),
    ('FaithWindow.GetDivergence.core', 0x2618D00, 0x2618D59, 'int64_t*(FaithWindow*,int64_t*out)'),
    ('FaithWindow.GetDivergence.thunk', 0x261CC80, 0x261CCB7, 'reflection wrapper'),
    ('CurrentRite.divergence_to_main', 0x2BDFBA0, 0x2BDFCB8, 'int64_t*(int64_t*out,CRite*,optional tooltip*)'),
    ('Divergence.tenet_doctrine_native_sum', 0x2BDE770, 0x2BDF404, 'native evaluation; null tooltip branch writes only output'),
    ('Rite.founder.scope_link', 0x1AFE330, 0x1AFE391, 'CRiteFounderLink output full Character ref'),
    ('Rite.head.ref_getter', 0xD55CF0, 0xD55CFC, 'uint32_t*(CRite*,uint32_t*out)'),
    ('Rite.GetHeadOfRite.thunk', 0x24FC610, 0x24FC672, 'Character*(CRite*); preserves ref generation'),
    ('CreationWindow.draft_divergence', 0x14F14B0, 0x14F15C9, 'int64_t*(out,CreationWindow*)'),
    ('CreationWindow.divergence_creates_faith.thunk', 0x14FC910, 0x14FC95B, 'native draft >= creation define'),
]
REGISTRATIONS = [
    ('Rite.IsMain.registration', 0x4EE8D5, 0x4EE969),
    ('Faith.GetHeresyThreshold.registration', 0x4D368B, 0x4D3721),
    ('FaithWindow.GetDivergence.registration', 0x516731, 0x5167CD),
    ('Rite.GetHeadOfRite.registration', 0x4EFB4A, 0x4EFBE3),
    ('CreationWindow.new_faith_result.registration', 0x22E9C9, 0x22EA05),
]
SITES = [
    ('is_main_parent_faith_ref', 0x24F7E4F, 'mov r8d, dword ptr [rcx + 0x4b8]'),
    ('is_main_current_rite_ref', 0x24F7E91, 'mov eax, dword ptr [r9 + 8]'),
    ('is_main_faith_main_ref_comparison', 0x24F7E95, 'cmp dword ptr [rdx + 0x98], eax'),
    ('is_main_core_call', 0x24FC0F2, 'call 0x24f7e40'),
    ('threshold_main_rite_ref', 0x244092F, 'mov edx, dword ptr [rcx + 0x98]'),
    ('threshold_main_rite_modifier', 0x244095F, 'mov rcx, qword ptr [rcx + 0x7f8]'),
    ('threshold_native_define', 0x2440969, 'add rcx, qword ptr [rip + 0x3828418]'),
    ('threshold_core_call', 0x24435D7, 'call 0x2440920'),
    ('current_divergence_null_tooltip', 0x2618D45, 'xor r8d, r8d'),
    ('current_divergence_output_first', 0x2618D48, 'mov rcx, rbx'),
    ('current_divergence_actual_call', 0x2618D4B, 'call 0x2bdfba0'),
    ('divergence_current_rite_parent_faith', 0x2BDFBCB, 'mov edx, dword ptr [rdx + 0x4b8]'),
    ('divergence_main_rite_ref', 0x2BDFC05, 'mov r8d, dword ptr [rax + 0x98]'),
    ('divergence_current_doctrines', 0x2BDFC72, 'lea rax, [rbx + 0x7a0]'),
    ('divergence_current_tenets', 0x2BDFC96, 'lea r9, [rbx + 0x758]'),
    ('divergence_native_sum_call', 0x2BDFCA0, 'call 0x2bde770'),
    ('divergence_result_written', 0x2BDF1EF, 'mov qword ptr [rsi], rbx'),
    ('founder_native_full_character_ref', 0x1AFE37D, 'mov eax, dword ptr [rax + 0x4bc]'),
    ('founder_scope_character_type', 0x1AFE38A, 'mov dword ptr [rdx], 4'),
    ('head_native_full_character_ref', 0xD55CF0, 'mov eax, dword ptr [rcx + 0x4c0]'),
    ('creation_draft_tenets', 0x14F15AC, 'lea r9, [rbx + 0xb30]'),
    ('creation_draft_doctrines', 0x14F1584, 'lea rax, [rbx + 0xb78]'),
    ('creation_draft_native_sum_call', 0x14F15B6, 'call 0x2bde770'),
    ('creation_divergence_call', 0x14FC92A, 'call 0x14f14b0'),
    ('creation_own_threshold', 0x14FC92F, 'mov rcx, qword ptr [rip + 0x476c332]'),
    ('creation_threshold_ge', 0x14FC941, 'setge byte ptr [rsp + 0x40]'),
    ('is_main_registration_callback', 0x4EE959, 'lea rdx, [rip + 0x200d780]'),
    ('threshold_registration_callback', 0x4D3710, 'lea rdx, [rip + 0x1f6fea9]'),
    ('head_registration_callback', 0x4EFBD2, 'lea rdx, [rip + 0x200ca37]'),
    ('draft_result_registration_callback', 0x22E9EC, 'lea r8, [rip + 0x12cdf1d]'),
]
STOCK = [
    ('common/religion/rite_types/_rite_types.info', 31, 74),
    ('common/defines/00_defines.txt', 824, 836),
    ('common/on_action/religion_on_actions.txt', 3, 18),
    ('gui/window_rite_creation.gui', 488, 524),
]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError('Not the frozen CK3 1.20.0.2 PE')
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva, size):
        off=pe.rva_to_offset(rva); return data[off:off+size]
    source=HEADER.read_text(encoding='utf-8')
    for name,value in CONSTANTS.items():
        match=re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)',source)
        if not match or int(match.group(1),0)!=value:
            raise ValueError('Provider constant mismatch: '+name)
    spans=[]; dump=[]
    for name,start,end,*abi in SPANS+REGISTRATIONS:
        raw=read(start,end-start)
        spans.append({'name':name,'kind':'complete_function' if abi else 'registration_slice',
            'start_rva':hex(start),'end_exclusive_rva':hex(end),'abi':abi[0] if abi else None,
            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex(' ')})
        dump.append(f'\n{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:09X} {i.bytes.hex(" "):32s} {i.mnemonic:8s} {i.op_str}' for i in decoder.disasm(raw,start))
    sites=[]
    for name,rva,expected in SITES:
        ins=next(decoder.disasm(read(rva,15),rva)); actual=ins.mnemonic+' '+ins.op_str
        if actual!=expected:
            raise ValueError(f'{name}: expected {expected}, got {actual}')
        sites.append({'name':name,'rva':hex(rva),'bytes':ins.bytes.hex(' '),'instruction':actual,
            'rip_targets':[hex(ins.address+ins.size+op.mem.disp) for op in ins.operands if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP],
            'direct_targets':[hex(op.imm) for op in ins.operands if op.type==X86_OP_IMM and ins.mnemonic in ('call','jmp')]})
    td=0x5835DC8; col=0x4C12210; vt=0x45C5AA8
    if read(td+16, len(b'.?AVCRiteFounderLink@@\0')) != b'.?AVCRiteFounderLink@@\0':
        raise ValueError('Founder link exact RTTI differs')
    col_values=struct.unpack('<6I',read(col,24))
    if col_values[0]!=1 or col_values[1]!=0 or col_values[3]!=td or col_values[5]!=col:
        raise ValueError('Founder link COL differs')
    if struct.unpack('<Q',read(vt-8,8))[0]!=pe.image_base+col or struct.unpack('<Q',read(vt+4*8,8))[0]!=pe.image_base+0x1AFE330:
        raise ValueError('Founder link virtual slot differs')
    game=exe.parent.parent/'game'; stock=[]; windows=[]
    for rel,first,last in STOCK:
        p=game/rel; lines=p.read_text(encoding='utf-8-sig').splitlines()
        window='\n'.join(f'{i+1}: {v}' for i,v in enumerate(lines) if first<=i+1<=last)
        stock.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'first_line':first,'last_line':last,'window':window})
        windows.append(rel+'\n'+window)
    result={'schema':'religion_reform12002_rite_native_abi_v1','game_version':'1.20.0.2',
        'executable_sha256':SHA,'executable_size':len(data),'readiness':'static-confirmed',
        'local_ck3_touched':False,'live_verified':False,'provider_constants':CONSTANTS,
        'native_spans':spans,'semantic_instructions':sites,
        'founder_link_rtti':{'type_descriptor_rva':hex(td),'col_rva':hex(col),'vtable_rva':hex(vt),'slot_index':4,'callback_rva':'0x1afe330'},
        'stock_sources':stock,'unresolved':['exact creation date / derivation ancestry getter',
        'automatic divergence detachment scheduler and final predicate','creation command execution and independent result',
        'current provider central registration, MCP transport and paused live']}
    return result,'\n'.join(dump)+'\n\n'+'\n\n'.join(windows)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True,type=Path); p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--record',action='store_true'); args=p.parse_args()
    result,dump=extract(args.exe)
    if args.record: MAP.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    elif json.loads(MAP.read_text(encoding='utf-8')) != result: raise ValueError('Frozen ABI map differs')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'native-disassembly.txt').write_text(dump,encoding='utf-8')
    receipt={'status':'GREEN','readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'complete_functions':len(SPANS),'registration_slices':len(REGISTRATIONS),'semantic_instructions':len(SITES),
        'founder_link_rtti':result['founder_link_rtti'],'stock_sources':len(STOCK),
        'manifest_sha256':hashlib.sha256(MAP.read_bytes()).hexdigest(),'disassembly_sha256':hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir/'native-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt)); return 0

if __name__=='__main__': raise SystemExit(main())
