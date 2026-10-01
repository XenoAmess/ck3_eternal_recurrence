"""Freeze popup scope/row/CanPick evidence in the exact 1.20.0.2 PE; no process reads."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage

SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
SPANS = {
 'doctrine_can_pick_registration': (0xD7A50, 0xD7B20),
 'doctrine_can_pick_wrapper': (0xEE4E60, 0xEE4F2D),
 'tenet_can_pick_registration': (0xD57D0, 0xD5942),
 'tenet_can_pick_wrapper_chained': (0xEE47A0, 0xEE48B9),
 'tenet_can_pick_core': (0xEE0AD0, 0xEE0B87),
 'current_scope_getter': (0xC46360, 0xC46369),
 'current_scope_wrapper': (0x14FBC60, 0x14FBC98),
 'scope_type_getter': (0xF05190, 0xF05198),
 'category_registration': (0x22CED0, 0x22D0D9),
 'category_getter_thunk': (0x14FBF30, 0x14FBF35),
 'category_getter': (0x1070BA0, 0x1070BA9),
 'category_items_wrapper': (0x14FA960, 0x14FA9B3),
 'doctrine_array_index': (0x1514980, 0x15149E9),
 'tenet_groups_getter': (0xB80140, 0xB80149),
 'tenet_groups_wrapper': (0x14FBD00, 0x14FBD58),
 'tenet_group_array_index': (0x1510530, 0x1510597),
 'group_tenets_wrapper': (0xEE49B0, 0xEE4A03),
 'tenet_array_index': (0xF076F0, 0xF07751),
 'prophet_database_getter': (0x8FCD40, 0x8FCD97),
 'prophet_cache_initialization': (0x31EA270, 0x31EA500),
 'existing_has_perk': (0x2919070, 0x2919090),
 'headed_current_rite_mode': (0x14F4400, 0x14F449B),
}
ANCHORS = {
 0xEE487C: ('call', '0xee0ad0'),
 0xEE4ECE: ('mov', 'rdi, qword ptr [rdi + 0x28]'),
 0xEE4ED8: ('lea', 'rcx, [rdi + 0x1b8]'), 0xEE4EDF: ('call', '0x372df30'),
 0xEE4EE8: ('lea', 'rcx, [rdi + 0xe8]'), 0xEE4EF2: ('call', '0x372df30'),
 0xC46360: ('lea', 'rax, [rcx + 0xd0]'), 0x1070BA0: ('lea', 'rax, [rcx + 0x888]'),
 0x14FA96C: ('lea', 'rax, [rcx + 0x20]'),
 0x15149C6: ('shl', 'rcx, 4'), 0xB80140: ('lea', 'rax, [rcx + 0x7a8]'),
 0x151056B: ('shl', 'rax, 5'), 0xEE49BC: ('lea', 'rax, [rcx + 8]'),
 0xF07720: ('imul', 'rcx, rbx, 0x70'),
 0x31EA331: ('mov', 'dword ptr [rsp + 0x50], 0xc'), 0x31EA377: ('mov', 'qword ptr [rdi + 0xef0], rax'),
}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--stock', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args(); data = a.exe.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != SHA: raise ValueError('Exact EXE mismatch')
    pe = PeImage(data); md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
    output = a.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    manifest = {'game_version': '1.20.0.2', 'executable_sha256': SHA,
        'scope': 'already_materialized_current_popup_candidates', 'spans': {}, 'instruction_anchors': {}}
    for name, (start, end) in SPANS.items():
        offset = pe.rva_to_offset(start); body = data[offset:offset+end-start]
        decoded = list(md.disasm(body, start))
        text = '\n'.join(f'{i.address:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in decoded)+'\n'
        (output/(name+'.txt')).write_text(text, encoding='utf-8')
        manifest['spans'][name] = {'start_rva': hex(start), 'end_rva': hex(end),
            'sha256': hashlib.sha256(body).hexdigest(), 'instruction_count': len(decoded)}
    for rva, (mnemonic, operands) in ANCHORS.items():
        o = pe.rva_to_offset(rva); i = next(md.disasm(data[o:o+15], rva))
        if i.mnemonic != mnemonic or not i.op_str.startswith(operands):
            raise ValueError(f'Anchor {rva:X}: expected {mnemonic} {operands}, got {i.mnemonic} {i.op_str}')
        manifest['instruction_anchors'][hex(rva)] = {'bytes': i.bytes.hex(), 'mnemonic': i.mnemonic, 'operands': i.op_str}
    # Binding descriptors are independent reflection registrations with the same CanPick name.
    for site, expected in ((0xD7AC8, 0xEE4E60), (0xD58B7, 0xEE47A0), (0x8FCD44, 0x5C67128), (0x31EA325, 0x48CC598)):
        o = pe.rva_to_offset(site); i = next(md.disasm(data[o:o+15], site))
        actual = [i.address+i.size+x.mem.disp for x in i.operands if x.type == X86_OP_MEM and x.mem.base == X86_REG_RIP]
        if actual != [expected]: raise ValueError(f'RIP anchor {site:X} mismatch: {actual}')
        manifest['instruction_anchors'][hex(site)] = {'bytes': i.bytes.hex(), 'target_rva': hex(expected)}
    o = pe.rva_to_offset(0x48CC598)
    if data[o:o+13] != b'prophet_perk\0': raise ValueError('Prophet key mismatch')
    # GetFaithScope's returned any type is CJominiTopScope*, not a new scope layout.
    meta = struct.unpack_from('<Q', data, pe.rva_to_offset(0x54D7E08))[0]-pe.image_base
    col = struct.unpack_from('<Q', data, pe.rva_to_offset(meta)-8)[0]-pe.image_base
    td = struct.unpack_from('<I', data, pe.rva_to_offset(col)+12)[0]
    o = pe.rva_to_offset(td)+16; typename = data[o:data.index(b'\0', o)].decode()
    if 'CJominiTopScope' not in typename: raise ValueError('Scope RTTI mismatch')
    manifest['scope_rtti'] = {'metadata_rva': '0x54D7E08', 'vtable_rva': hex(meta), 'type': typename}
    stock = {}
    for relative, first, last in (('gui/window_rite_creation.gui',1247,1256),
                                  ('gui/window_rite_creation.gui',1448,1478),
                                  ('common/scripted_guis/pam_scripted_guis.txt',82,92)):
        path = a.stock/relative; blob = path.read_bytes(); lines = blob.decode('utf-8-sig').splitlines()
        stock[f'{relative}:{first}'] = {'file_sha256': hashlib.sha256(blob).hexdigest(),
            'first_line': first, 'last_line': last, 'text': '\n'.join(lines[first-1:last])}
    manifest['stock'] = stock
    manifest['status'] = 'GREEN'; manifest['local_ck3_touched'] = False
    (output/'result.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'GREEN exact PE spans={len(SPANS)} anchors={len(manifest["instruction_anchors"])} stock=3')
    return 0
if __name__ == '__main__': raise SystemExit(main())
