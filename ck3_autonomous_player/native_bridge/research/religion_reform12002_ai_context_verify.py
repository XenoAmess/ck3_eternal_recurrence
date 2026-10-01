"""Freeze the actual AI holder/source fields; no process or native execution."""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64,CS_AC_WRITE
from capstone.x86 import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
from scan_anchors import PeImage
HERE=Path(__file__).resolve().parent
MAP=HERE/'religion_reform12002_ai_context_abi.json'
HEADER=HERE.parent/'include/xar_bridge/religion_reform12002_ai_context.hpp'
SHA='ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
REUSE='c44a4fe9c1fc3bdd2614999c4c587244801774b7a87a23bd562c1d6ec2fb36c9'
SPANS=[
    ('player_AI.readonly_getter',0x28CA250,0x28CA2D3),
    ('normal_AI.readonly_bool',0x28AC130,0x28AC14F),
    ('player_AI.readonly_bool',0x28AC150,0x28AC168),
    ('normal_AI.creator_evidence_only',0x1A2FA70,0x1A2FB01),
    ('actual_AI.constructor_and_holder_append_evidence_only',0x1ACBB90,0x1ACBD22),
]
SLICES=[
    ('holder.default_and_actual_array_initialize',0x1ACB5E5,0x1ACB638),
    ('normal_AI.field_read_and_default_check',0x1A2EDAC,0x1A2EDF6),
    ('normal_AI.restore_holder_default',0x1A2EDFD,0x1A2EE11),
    ('holder.retirement_terminal_only',0x1A2FA49,0x1A2FA63),
]
SITES=[
    ('player_getter_actor_full_id',0x28CA250),('player_getter_game_state_root',0x28CA258),
    ('player_getter_state_data',0x28CA25F),('player_getter_instance_array',0x28CA266),
    ('player_getter_instance_count',0x28CA26D),('player_getter_full_id_compare',0x28CA283),
    ('player_getter_instance_tag',0x28CA2AE),('player_getter_instance_ID',0x28CA2BA),
    ('player_getter_existing_special_AI',0x28CA2C3),('player_getter_default_AI',0x28CA2CB),
    ('normal_creator_living_data',0x1A2FA9D),('normal_existing_AI_pointer',0x1A2FAB2),
    ('normal_creator_holder',0x1A2FAB9),('normal_creator_default_AI_compare',0x1A2FABD),
    ('normal_creator_AI_tag',0x1A2FAC3),('normal_creator_mutating_constructor',0x1A2FACF),
    ('normal_AI_field_write',0x1A2FAE0),
    ('new_AI_actor_write_source',0x1ACBBEC),('new_AI_tag_write_source',0x1ACBBF4),
    ('actual_holder_array_count',0x1ACBC02),('actual_holder_array_capacity',0x1ACBC06),
    ('actual_holder_append_pointer',0x1ACBCDC),('actual_holder_increment_count',0x1ACBCE0),
    ('holder_default_AI_initialize',0x1ACB61D),('holder_array_initialize',0x1ACB622),
    ('holder_capacity_count_initialize',0x1ACB627),
    ('retire_normal_AI_call',0x1A2EDF1),('normal_AI_restore_default',0x1A2EE0A),
    ('retire_holder_pointer',0x1A2FA49),('retire_holder_call',0x1A2FA5E),
]
BINDINGS={'kAIContextStateDataOffset':0xA0,'kAIContextManagerOffset':0x2D48,
    'kAIContextHolderOffset':0x20,'kAIContextDefaultOffset':8,'kAIContextArrayOffset':0x10,
    'kAIContextCountOffset':0x1C,'kAIContextActorOffset':0x18,'kAIContextTypeOffset':0x28,
    'kAIContextActiveOffset':0x2C,'kAIContextSpecialOffset':0x2E}
def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--record',action='store_true');a=p.parse_args();data=a.exe.read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA:raise ValueError('Exact EXE differs')
    reused=(HERE/'religion_reform12002_schedule_abi.json').read_bytes()
    if hashlib.sha256(reused).hexdigest()!=REUSE:raise ValueError('Frozen schedule map differs')
    pe=PeImage(data);cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
    def read(rva,n):off=pe.rva_to_offset(rva);return data[off:off+n]
    header=HEADER.read_text(encoding='utf-8-sig')
    for name,value in BINDINGS.items():
        m=re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)',header)
        if not m or int(m[1],0)!=value:raise ValueError(name)
    spans=[];dump=[];readonly=[]
    for name,start,end in SPANS+SLICES:
        raw=read(start,end-start);ins=list(cs.disasm(raw,start))
        spans.append({'name':name,'start_rva':hex(start),'end_exclusive_rva':hex(end),
            'kind':'complete_function' if (name,start,end) in SPANS else 'slice',
            'bytes':raw.hex(' '),'sha256':hashlib.sha256(raw).hexdigest()})
        dump.append(f'{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:09X} {i.bytes.hex(" "):36s} {i.mnemonic} {i.op_str}' for i in ins)
        if '.readonly_' in name:
            calls=[hex(o.imm) for i in ins if i.mnemonic=='call' for o in i.operands if o.type==X86_OP_IMM]
            stores=[hex(i.address) for i in ins if any(o.type==X86_OP_MEM and o.access&CS_AC_WRITE for o in i.operands)]
            # The bool wrapper saves nonvolatile state on its own stack only.
            object_stores=[hex(i.address) for i in ins if any(o.type==X86_OP_MEM and o.access&CS_AC_WRITE and i.reg_name(o.mem.base) not in ('rsp','rbp') for o in i.operands)]
            if object_stores or calls not in ([],['0x28ca250']):raise ValueError(name)
            readonly.append({'name':name,'native_object_stores':object_stores,'calls':calls,'stack_stores':stores})
    instructions=[]
    for name,rva in SITES:
        i=next(cs.disasm(read(rva,15),rva))
        instructions.append({'name':name,'rva':hex(rva),'bytes':i.bytes.hex(' '),
            'instruction':f'{i.mnemonic} {i.op_str}',
            'rip_targets':[hex(i.address+i.size+o.mem.disp) for o in i.operands if o.type==X86_OP_MEM and o.mem.base==X86_REG_RIP],
            'direct_targets':[hex(o.imm) for o in i.operands if o.type==X86_OP_IMM and i.mnemonic in ('call','jmp')]})
    by={x['name']:x for x in instructions}
    for name,target in [('player_getter_game_state_root',0x5C68C50),('player_getter_default_AI',0x5D21A10)]:
        if by[name]['rip_targets']!=[hex(target)]:raise ValueError(name)
    for name,target in [('normal_creator_mutating_constructor',0x1ACBB90),('retire_normal_AI_call',0x1A2F760),('retire_holder_call',0x1ACBD30)]:
        if by[name]['direct_targets']!=[hex(target)]:raise ValueError(name)
    old=json.loads(reused);old_by={x['name']:x for x in old['semantic_instructions']}
    reused_names=['AI_state_constructor','AI_holder','player_AI_special','AI_manager_secondary_vtable']
    if old_by['AI_holder']['instruction']!='mov rax, qword ptr [rbp + 0x18]':raise ValueError('secondary holder relative offset')
    if old_by['AI_state_constructor']['direct_targets']!=['0x1a2e260']:raise ValueError('manager state constructor')
    result={'schema':'ck3_12002_religion_reform_ai_context_v1','exact_executable_sha256':SHA,
        'readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'reused_schedule_map_sha256':REUSE,'reused_schedule_anchors':[old_by[x] for x in reused_names],
        'native_spans':spans,'semantic_instructions':instructions,'readonly_native_entrypoints':readonly,
        'source_bindings':{k:hex(v) for k,v in BINDINGS.items()},
        'public_pointer_source':'actual holder array membership + same resolved actor pointer + full actor identity; default +8 excluded',
        'unresolved':['full general AI lifetime eligibility on later days','owned paused query integration and actual live table observation']}
    if a.record:MAP.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    elif json.loads(MAP.read_text(encoding='utf8'))!=result:raise ValueError('Reviewed AI context ABI differs')
    a.output_dir.mkdir(parents=True,exist_ok=True);native=a.output_dir/'native-disassembly.txt'
    native.write_text('\n'.join(dump)+'\n',encoding='utf8')
    receipt={'status':'GREEN','complete_functions':len(SPANS),'slices':len(SLICES),'semantic_instructions':len(SITES),
        'exact_executable_sha256':SHA,'local_ck3_touched':False,'live_verified':False,
        'abi_manifest_sha256':hashlib.sha256(MAP.read_bytes()).hexdigest(),'reused_schedule_map_sha256':REUSE,
        'native_disassembly_sha256':hashlib.sha256(native.read_bytes()).hexdigest()}
    (a.output_dir/'abi-verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
