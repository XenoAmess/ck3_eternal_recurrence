"""Freeze battle-score strength buckets from the pinned EXE; no game attachment."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import capstone
import pefile

EXE_SHA = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
SPANS = {
    "battle_score": (0x25BBE70, 0x25BC264),
    "character_buckets": (0x292FC40, 0x293084E),
    "regiment_buckets": (0x2930850, 0x2930A8C),
    "mercenary_bucket": (0x2930A90, 0x2930D2C),
    "order_bucket": (0x2930D30, 0x2930FCC),
    "tooltip": (0xC78980, 0xC793D1),
    "current_max_labels": (0xC7D6B0, 0xC7D80C),
    "levy_selector": (0x290E410, 0x290E6BA),
    "levy_quantity": (0x29075E0, 0x29076D5),
    "knights": (0x28FDD40, 0x28FE087),
    "title_membership": (0x28AB770, 0x28AB879),
    "nomadic_quantity": (0x294A390, 0x294A4AC),
    "nomadic_conversion": (0x232DE50, 0x232E0F9),
}
LABELS = {
    "LIST_LEVIES_STRING": 0x40D9448,
    "LIST_KNIGHTS_STRING": 0x40D9460,
    "LIST_MAA_STRING": 0x40D9420,
    "LIST_HERD_STRING": 0x40D9430,
    "LIST_EVENT_TROOPS_STRING": 0x40D93E8,
    "LIST_MERCENARIES_STRING": 0x40D9408,
    "LIST_HOLY_ORDERS_STRING": 0x40D9500,
    "CURRENT": 0x40D8C68,
    "MAX": 0x40D58F4,
}
ANCHORS = {
    0x25BBFED: ("mov", "r8b, 2"),
    0x25BBFF5: ("call", "0x292fc40"),
    0x25BC084: ("cmovl", "esi, eax"),
    0x25BC172: ("cmovl", "rcx, r8"),
    0x292FDBE: ("mov", "dword ptr [rsi], edx"),
    0x292FEA4: ("mov", "dword ptr [rsi + 0xe0], ebx"),
    0x293009B: ("mov", "dword ptr [rsi + 0xa0], r8d"),
    0x2930219: ("add", "dword ptr [rsi + 0x80], edi"),
    0x2930350: ("lea", "r9, [rsi + 0x20]"),
    0x2930428: ("add", "rdx, 0x418"),
    0x293042F: ("lea", "r9, [rsi + 0xc0]"),
    0x2930976: ("cmp", "dword ptr [r14 + 0x138], 1"),
    0x2930F10: ("add", "dword ptr [r10 + 0x60], edx"),
    0xC78A69: ("lea", "rax, [rip + 0x34609f0]"),
    0xC78C38: ("lea", "rax, [rip + 0x34607e1]"),
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract(exe: Path, out: Path) -> dict:
    data = exe.read_bytes()
    if sha(data) != EXE_SHA:
        raise ValueError("Pinned CK3 1.19.0.6 EXE required")
    out.mkdir(parents=True, exist_ok=False)
    pe = pefile.PE(data=data, fast_load=True)
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    cs.detail = True
    result = {"schema": "xar.war-film-denominator.v1", "exe_sha256": EXE_SHA,
              "exe_bytes": len(data), "exe_path": str(exe.resolve()),
              "python": sys.executable, "python_version": sys.version,
              "packages": {n: importlib.metadata.version(n) for n in ("capstone", "pefile")},
              "live": False, "spans": {}, "anchors": {}, "labels": {},
              "scope": "Byte and label verification; semantic claims are reviewed in the companion document."}
    decoded = {}
    for name, (start, end) in SPANS.items():
        raw = pe.get_data(start, end-start)
        instructions = list(cs.disasm(raw, start))
        if sum(i.size for i in instructions) != len(raw):
            raise ValueError(f"Incomplete instruction coverage: {name}")
        decoded.update({i.address: i for i in instructions})
        lines = []
        for i in instructions:
            refs = [hex(i.address+i.size+o.mem.disp) for o in i.operands
                    if o.type == capstone.x86.X86_OP_MEM and o.mem.base == capstone.x86.X86_REG_RIP]
            lines.append(f"{i.address:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}" + (" ; RIP="+','.join(refs) if refs else ""))
        assembly = ('\n'.join(lines)+'\n').encode()
        (out/f'{name}.asm.txt').write_bytes(assembly)
        result['spans'][name] = {"start": hex(start), "end_exclusive": hex(end),
                                 "sha256": sha(raw), "bytes_hex": raw.hex(),
                                 "instructions": len(instructions), "assembly_sha256": sha(assembly)}
    for address, expected in ANCHORS.items():
        i = decoded[address]
        if (i.mnemonic, i.op_str) != expected:
            raise ValueError(f"Anchor differs at {address:#x}: {i.mnemonic} {i.op_str}")
        result['anchors'][hex(address)] = {'bytes': i.bytes.hex(), 'instruction': ' '.join(expected)}
    loc = exe.parent.parent/'game/localization/english/gui/realm_window_l_english.yml'
    source = loc.read_bytes()
    result['localization'] = {'relative_path': 'game/localization/english/gui/realm_window_l_english.yml', 'sha256': sha(source)}
    for key, rva in LABELS.items():
        if pe.get_data(rva, len(key)+1) != key.encode()+b'\0':
            raise ValueError(f"Label differs: {key}")
        rows = [{'line': n, 'text': line} for n,line in enumerate(source.decode('utf-8-sig').splitlines(),1) if line.lstrip().startswith(key+':')]
        if key.startswith('LIST_') and len(rows) != 1:
            raise ValueError(f"Missing or ambiguous localization: {key}")
        result['labels'][key] = {'rva': hex(rva), 'localization': rows}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    r=extract(args.exe,args.out)
    print(json.dumps({'result':'PASS','spans':len(r['spans']),'anchors':len(r['anchors']),'labels':len(r['labels']),'live':False}))
