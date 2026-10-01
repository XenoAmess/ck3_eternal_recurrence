#!/usr/bin/env python3
"""Verify frozen nonwar doctrine-choice inputs and actual knowledge bindings."""
from __future__ import annotations
import argparse, bisect, hashlib, json, re, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'ck3_autonomous_player/native_bridge/research'))
from scan_anchors import PeImage
SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MANIFEST = HERE / 'religion_doctrine12002_choices_abi.json'
NATIVE = ROOT / 'ck3_autonomous_player/native_bridge'

FUNCTIONS = [
    ('DoctrineCategoryWindow.GetDoctrineItems.reflection', 0x14FA960,
     'bool*(collection-wrapper): category-window+0x20, model construction unresolved'),
    ('DoctrineItem.ShouldDisplay.reflection', 0xEE4CC0, 'reflection; resolves TopScope; definition+0x1B8'),
    ('DoctrineItem.CanPick.reflection', 0xEE4E60, 'reflection; resolves TopScope; definition+0x1B8 and +0xE8'),
    ('TenetItem.ShouldDisplay.reflection', 0xEE46F0, 'reflection; resolves TopScope; definition+0x658'),
    ('TenetItem.CanPick.reflection', 0xEE47A0, 'reflection; resolves Character and TopScope'),
    ('TenetItem.CanPick.core', 0xEE0AD0, 'bool(TenetItem*,Character*,CScriptTopScope*)'),
    ('knows_doctrine.registration', 0x592AA0, 'trigger name registration and factory vtable'),
    ('knows_doctrine.factory', 0x2B30020, 'actual trigger factory; vtable0x47BCAB0'),
    ('knows_doctrine.trigger.evaluate', 0x2B2C130, 'character-scope full-generation resolution and native bool tail-call'),
    ('Character.KnowsDoctrine.core', 0x28B0C00, 'bool(Character*,DoctrineDefinition*)'),
    ('Character.TenetCanPick.extra_collection', 0x28B0B60, 'collection*(Character*); extension+0xC8, not doctrine knowledge E0'),
    ('Faith.IsUnreformed.reflection', 0x2444600, 'reflection calls native main-Rite boolean'),
    ('Faith.IsUnreformed.core', 0x2BD8960, 'bool(Faith*); resolves full main RiteID, reads Rite+0x8B0'),
    ('CDoctrineTypeDB.getter', 0x8FC740, 'database*(); global0x5C67198; may initialize when absent; provider does not call'),
]
SITES = [
    ('category_model_address', 0x14FA96C), ('category_items_registration_callback', 0x228BCF),
    ('doctrine_shown_registration_callback', 0xD7887), ('doctrine_pick_registration_callback', 0xD7AC8),
    ('doctrine_shown_definition_pointer', 0xEE4D2E), ('doctrine_shown_trigger_address', 0xEE4D35),
    ('doctrine_shown_trigger_eval', 0xEE4D3C), ('doctrine_pick_definition_pointer', 0xEE4ECE),
    ('doctrine_pick_shown_trigger', 0xEE4ED8), ('doctrine_pick_selectable_trigger', 0xEE4EE8),
    ('tenet_should_display_definition_pointer', 0xEE475E), ('tenet_should_display_trigger_address', 0xEE4765),
    ('tenet_should_display_trigger_eval', 0xEE476C), ('tenet_can_pick_core_call', 0xEE487C),
    ('tenet_can_pick_mode_byte', 0xEE0AE4), ('tenet_can_pick_mode5', 0xEE0AF1),
    ('tenet_can_pick_extra_collection', 0xEE0AF9), ('tenet_can_pick_mode0', 0xEE0B3A),
    ('tenet_can_pick_definition_pointer', 0xEE0B42), ('tenet_can_pick_shown_trigger', 0xEE0B49),
    ('tenet_can_pick_selectable_trigger', 0xEE0B59), ('knows_doctrine_name', 0x592AB1),
    ('knows_doctrine_factory_vtable', 0x592B19), ('knows_doctrine_instance_vtable', 0x2B30047),
    ('knowledge_trigger_character_generation', 0x2B2C17D), ('knowledge_bool_tail_call', 0x2B2C1A5),
    ('knowledge_character_extension', 0x28B0C0A), ('knowledge_extension_array', 0x28B0C19),
    ('knowledge_extension_count', 0x28B0C25), ('knowledge_default_actor_rite_ref', 0x28B0C51),
    ('knowledge_default_rite_generation', 0x28B0C78), ('knowledge_default_rite_array', 0x28B0C85),
    ('knowledge_default_rite_count', 0x28B0C91), ('knowledge_boolean_return', 0x28B0CC4),
    ('other_can_pick_collection', 0x28B0B70), ('unreformed_core_call', 0x2444611),
    ('unreformed_main_rite_ref', 0x2BD897B), ('unreformed_actual_rite_value', 0x2BD89AE),
]
CONSTANTS = {
    'kCharacterKnowsDoctrineRva': 0x28B0C00,
    'kCharacterKnowledgeExtensionOffset': 0x1C8,
    'kLearnedDoctrineArrayOffset': 0xE0, 'kLearnedDoctrineCountOffset': 0xEC,
    'kDefinitionRegistryArrayOffset': 0x50, 'kDefinitionRegistryCountOffset': 0x5C,
    'kDoctrineDatabasePointerRva': 0x5C67198,
}
LEAF_ENDS = {0x2BD8960: 0x2BD89B6}

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError('Not frozen CK3 1.20.0.2 executable')
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64); decoder.detail = True
    def read(rva, size):
        offset = pe.rva_to_offset(rva); return data[offset:offset+size]
    peoff = struct.unpack_from('<I', data, 0x3C)[0]
    pdata_rva, pdata_size = struct.unpack_from('<II', data, peoff+24+112+3*8)
    pdata = [struct.unpack_from('<III', read(pdata_rva+i, 12)) for i in range(0,pdata_size,12)]
    starts = [x[0] for x in pdata]
    spans, dump = [], []
    for name, rva, abi in FUNCTIONS:
        if rva in LEAF_ENDS:
            start,end,unwind = rva,LEAF_ENDS[rva],None
            if read(end-1,1)!=b'\xc3':raise ValueError('Reviewed leaf no longer ends in return')
        else:
            start,end,unwind = pdata[bisect.bisect_right(starts,rva)-1]
            if start != rva: raise ValueError(f'Unreviewed function boundary: {name}')
        raw = read(start,end-start)
        spans.append({'name':name,'rva':hex(start),'end_exclusive_rva':hex(end),
            'unwind_rva':hex(unwind) if unwind is not None else None,'abi':abi,
            'boundary_source':'reviewed_leaf' if unwind is None else 'PE_exception_directory',
            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':raw.hex(' ')})
        dump.append(f'\n{name} [{start:#x},{end:#x}) {abi}')
        dump.extend(f'{ins.address:09X} {ins.bytes.hex(" "):32s} {ins.mnemonic:8s} {ins.op_str}'
                    for ins in decoder.disasm(raw,start))
    instructions = []
    for name,rva in SITES:
        ins = next(decoder.disasm(read(rva,15),rva))
        instructions.append({'name':name,'rva':hex(rva),'bytes':ins.bytes.hex(' '),
            'instruction':f'{ins.mnemonic} {ins.op_str}',
            'rip_targets':[hex(ins.address+ins.size+op.mem.disp) for op in ins.operands
                if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP],
            'call_targets':[hex(op.imm) for op in ins.operands if op.type==X86_OP_IMM and ins.mnemonic in ('call','jmp')]})
    sources = '\n'.join((NATIVE/'include/xar_bridge'/name).read_text(encoding='utf-8-sig') for name in
        ('religion_doctrine12002_choices.hpp','religion_doctrine12002_intrinsic.hpp'))
    for name,value in CONSTANTS.items():
        match = re.search(rf'\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)', sources)
        if not match or int(match.group(1),0)!=value: raise ValueError('Actual provider differs: '+name)
    trigger_slot = struct.unpack('<Q',read(0x47BCAB0+0xC8,8))[0]-pe.image_base
    if trigger_slot!=0x2B2C130: raise ValueError('Actual knows_doctrine evaluator differs')
    stock_root = exe.parent.parent/'game'
    stock = []
    for rel,a,b in [('gui/window_rite_creation.gui',1236,1293),
                    ('gui/window_rite_creation.gui',1407,1418),
                    ('gui/window_rite_creation.gui',590,640),
                    ('common/scripted_guis/pam_scripted_guis.txt',82,92)]:
        path=stock_root/rel; raw=path.read_bytes(); lines=raw.decode('utf-8-sig').splitlines()
        stock.append({'path':rel,'file_sha256':hashlib.sha256(raw).hexdigest(),
            'first_line':a,'last_line':b,'text':'\n'.join(lines[a-1:b])})
    return {'schema':'xar.ck3_12002.doctrine_choice_knowledge_abi.v1','executable_sha256':SHA,
        'native_functions':spans,'semantic_instructions':instructions,
        'trigger_evaluator_slot':{'vtable_rva':'0x47bcab0','slot_offset':'0xc8','target_rva':hex(trigger_slot)},
        'provider_constants':{k:hex(v) for k,v in CONSTANTS.items()},'stock_windows':stock,
        'provider_implemented':True,'full_choices_ready':False,'live_verified':False,
        'unresolved':['full creation/reform model construction and mode semantics','CScriptTopScope construction',
            'Prophet perk component of GUI knowledge gate','final creation/reform cost and submission legality']}, '\n'.join(dump)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--record',action='store_true');args=p.parse_args()
    result,dump=extract(args.exe)
    if args.record: MANIFEST.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    elif json.loads(MANIFEST.read_text(encoding='utf-8'))!=result:raise ValueError('Exact native ABI manifest differs')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'native-disassembly.txt').write_text(dump,encoding='utf-8')
    receipt={'status':'GREEN','readiness':'static-confirmed','live_verified':False,'local_ck3_touched':False,
        'native_functions':len(FUNCTIONS),'semantic_instructions':len(SITES),'stock_windows':len(result['stock_windows']),
        'provider_constants':len(CONSTANTS),'executable_sha256':SHA,
        'abi_manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        'disassembly_sha256':hashlib.sha256(dump.encode()).hexdigest()}
    (args.output_dir/'result.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
