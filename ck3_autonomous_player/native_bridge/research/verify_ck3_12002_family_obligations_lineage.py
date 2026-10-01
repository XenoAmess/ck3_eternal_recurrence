"""Verify the exact native MatchOffer child-house preview and its field sources."""
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
CONTRACT = HERE / 'ck3_12002_family_obligations_lineage_abi.json'

def verify(exe: Path) -> dict:
    manifest = json.loads(CONTRACT.read_text(encoding='utf-8'))
    data = exe.read_bytes()
    if len(data) != manifest['build']['executable_size'] or hashlib.sha256(data).hexdigest().upper() != manifest['build']['executable_sha256']:
        raise ValueError('exact CK3 executable changed')
    pe = PeImage(data)
    def read(rva: int, count: int) -> bytes:
        offset = pe.rva_to_offset(rva)
        return data[offset:offset + count]
    for span in manifest['native_spans']:
        start, end = int(span['rva_start'], 0), int(span['rva_end_exclusive'], 0)
        if hashlib.sha256(read(start, end - start)).hexdigest() != span['sha256']:
            raise ValueError(f"native span changed: {span['name']}")
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for row in manifest['semantic_checks']:
        ins = next(decoder.disasm(read(int(row['rva'], 0), 15), int(row['rva'], 0)))
        actual = {'bytes': ins.bytes.hex(' ').upper(), 'instruction': f'{ins.mnemonic} {ins.op_str}',
                  'rip_targets': [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
                                  if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP],
                  'immediates': [hex(op.imm) for op in ins.operands if op.type == X86_OP_IMM]}
        if any(actual[key] != row[key] for key in actual):
            raise ValueError(f"native input changed: {row['name']}")
    vtable = manifest['vtable']
    pointers = struct.unpack('<3Q', read(int(vtable['rva'], 0), 24))
    if tuple(value - 0x140000000 for value in pointers) != tuple(int(value, 0) for value in vtable['entries']):
        raise ValueError('MatchOffer getter vtable changed')
    source = (HERE.parent / 'include/xar_bridge/ck3_12002_family_obligations_lineage.hpp').read_text(encoding='utf-8-sig')
    for name, value in manifest['source_constants'].items():
        matched = re.search(rf'\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)', source)
        if not matched or int(matched.group(1), 0) != int(value, 0):
            raise ValueError(f'native source constant changed: {name}')
    return {'status': 'GREEN', 'readiness': 'static-ready', 'live_verified': False,
            'process_access': False, 'native_spans': len(manifest['native_spans']),
            'semantic_instructions': len(manifest['semantic_checks']),
            'vtable_entries': len(vtable['entries']),
            'contract_sha256': hashlib.sha256(CONTRACT.read_bytes()).hexdigest()}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
