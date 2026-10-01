#!/usr/bin/env python3
"""Freeze actual DoctrineItem display/pick callbacks and existing popup scope."""
from __future__ import annotations
import argparse, bisect, hashlib, json, re, struct, sys
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP

ROOT = Path(__file__).resolve().parent.parent
NATIVE = ROOT / 'ck3_autonomous_player/native_bridge'
sys.path.insert(0, str(NATIVE / 'research'))
from scan_anchors import PeImage
SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MANIFEST = Path(__file__).with_name('religion_doctrine12002_selection_abi.json')
FUNCTIONS = [
    ('DoctrineItem.ShouldDisplay.reflection', 0xEE4CC0, None),
    ('DoctrineItem.CanPick.reflection', 0xEE4E60, None),
    ('RiteCreationWindow.GetFaithScope', 0xC46360, 0xC46368),
    ('CJominiTopScope.reflection_type_getter', 0xF05190, None),
]
ANCHORS = {
    0xEE4D2E: ('mov', 'rcx, qword ptr [rsi + 0x28]'),
    0xEE4D35: ('add', 'rcx, 0x1b8'),
    0xEE4D3C: ('call', '0x372df30'),
    0xEE4ECE: ('mov', 'rdi, qword ptr [rdi + 0x28]'),
    0xEE4ED8: ('lea', 'rcx, [rdi + 0x1b8]'),
    0xEE4EDF: ('call', '0x372df30'),
    0xEE4EE8: ('lea', 'rcx, [rdi + 0xe8]'),
    0xEE4EF2: ('call', '0x372df30'),
    0xC46360: ('lea', 'rax, [rcx + 0xd0]'),
    0x1070BA0: ('lea', 'rax, [rcx + 0x888]'),
    0x14FA96C: ('lea', 'rax, [rcx + 0x20]'),
}
RIP_ANCHORS = {0xD7887: 0xEE4CC0, 0xD7AC8: 0xEE4E60, 0xF051B0: 0x54D7E08}

def extract(exe: Path):
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA: raise ValueError('Frozen executable mismatch')
    pe = PeImage(data); md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
    def read(rva, size):
        offset = pe.rva_to_offset(rva); return data[offset:offset + size]
    peoff = struct.unpack_from('<I', data, 0x3C)[0]
    pdata_rva, pdata_size = struct.unpack_from('<II', data, peoff+24+112+3*8)
    pdata = [struct.unpack('<III', read(pdata_rva+i, 12)) for i in range(0, pdata_size, 12)]
    starts = [row[0] for row in pdata]; spans, dump, anchors = [], [], {}
    for name, start, leaf_end in FUNCTIONS:
        if leaf_end is None:
            actual, end, unwind = pdata[bisect.bisect_right(starts, start)-1]
            if actual != start: raise ValueError('Function boundary mismatch: '+name)
        else:
            end, unwind = leaf_end, None
            if read(end-1, 1) != b'\xc3': raise ValueError('Reviewed leaf return mismatch')
        raw = read(start, end-start)
        spans.append({'name': name, 'rva': hex(start), 'end_exclusive_rva': hex(end),
            'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': raw.hex(' '),
            'boundary_source': 'PE_exception_directory' if unwind is not None else 'reviewed_leaf'})
        dump.append(f'\n{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:08X} {i.bytes.hex(" "):32s} {i.mnemonic} {i.op_str}' for i in md.disasm(raw, start))
    for rva, expected in ANCHORS.items():
        ins = next(md.disasm(read(rva, 15), rva))
        if (ins.mnemonic, ins.op_str) != expected: raise ValueError(f'Instruction {rva:X}: {ins.mnemonic} {ins.op_str}')
        anchors[hex(rva)] = {'bytes': ins.bytes.hex(' '), 'instruction': f'{ins.mnemonic} {ins.op_str}'}
    for rva, expected in RIP_ANCHORS.items():
        ins = next(md.disasm(read(rva, 15), rva))
        targets = [ins.address+ins.size+o.mem.disp for o in ins.operands if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]
        if targets != [expected]: raise ValueError(f'Reflection registration {rva:X} differs')
        anchors[hex(rva)] = {'bytes': ins.bytes.hex(' '), 'target_rva': hex(expected)}
    # Existing frozen producer proves popup array/stride and actual Prophet/knowledge gate.
    dependencies = [NATIVE/'research/religion_reform12002_choices_abi.json',
        ROOT/'research/religion_doctrine12002_choices_abi.json']
    source = (NATIVE/'include/xar_bridge/religion_doctrine12002_selection.hpp').read_text(encoding='utf-8-sig')
    constants = {'kDoctrineItemShouldDisplayCallbackRva':0xEE4CC0, 'kDoctrineItemCanPickCallbackRva':0xEE4E60,
        'kDoctrineShownTriggerOffset':0x1B8, 'kDoctrinePickTriggerOffset':0xE8}
    for name, value in constants.items():
        match = re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)', source)
        if not match or int(match.group(1), 0) != value: raise ValueError('Provider constant mismatch: '+name)
    stock = []
    for relative, first, last in [('gui/window_rite_creation.gui',1236,1255),
            ('gui/window_rite_creation.gui',1407,1418), ('common/scripted_guis/pam_scripted_guis.txt',82,92)]:
        blob = (exe.parent.parent/'game'/relative).read_bytes(); lines = blob.decode('utf-8-sig').splitlines()
        stock.append({'path': relative, 'file_sha256': hashlib.sha256(blob).hexdigest(), 'first_line': first,
            'last_line': last, 'text': '\n'.join(lines[first-1:last])})
    manifest = {'schema':'xar.ck3_12002.doctrine_current_popup_selection_abi.v1', 'executable_sha256':SHA,
        'native_functions':spans, 'semantic_instructions':anchors, 'stock_windows':stock,
        'provider_constants':{name:hex(value) for name,value in constants.items()},
        'reused_frozen_abi_sha256':{str(path.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in dependencies}, 'scope':'already_materialized_current_popup_candidates',
        'final_row_selection_gate':'ShouldDisplay AND CanPick AND (KnowsDoctrine OR HasProphet)',
        'unresolved':['all unopened doctrine-group popup construction','production paused snapshot'],
        'live_verified':False, 'local_ck3_touched':False}
    return manifest, '\n'.join(dump)+'\n'

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--exe',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--record',action='store_true'); a=p.parse_args()
    manifest,dump=extract(a.exe)
    if a.record: MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    elif json.loads(MANIFEST.read_text(encoding='utf-8')) != manifest: raise ValueError('ABI manifest differs')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    (a.output_dir/'native-disassembly.txt').write_text(dump,encoding='utf-8')
    result={'status':'GREEN','readiness':'static-confirmed','local_ck3_touched':False,'live_verified':False,
        'native_functions':len(FUNCTIONS),'semantic_instructions':len(ANCHORS)+len(RIP_ANCHORS),
        'stock_windows':len(manifest['stock_windows']),'executable_sha256':SHA,
        'abi_manifest_sha256':hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        'disassembly_sha256':hashlib.sha256(dump.encode()).hexdigest()}
    (a.output_dir/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2)); return 0
if __name__=='__main__':raise SystemExit(main())
