"""Verify the 1.20 break-betrothal source binding against an executable file."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
from scan_anchors import PeImage, verify

HERE = Path(__file__).resolve().parent


def verify_break(exe: Path) -> dict:
    manifest_path = HERE / 'ck3_12002_family_obligations_break_abi.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    failures = verify(exe, manifest_path)
    if failures:
        raise ValueError('; '.join(failures))
    data = exe.read_bytes()
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instructions = {}
    for row in manifest['semantic_checks']:
        rva = int(row['rva'], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(data[offset:offset + 15], rva))
        rip = [hex(ins.address + ins.size + op.mem.disp) for op in ins.operands
               if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP]
        direct = [hex(op.imm) for op in ins.operands
                  if op.type == X86_OP_IMM and ins.mnemonic in ('call', 'jmp')]
        if (ins.bytes.hex(' ').upper(), f'{ins.mnemonic} {ins.op_str}', rip, direct) != (
            row['bytes'], row['instruction'], row['rip_targets'], row['direct_targets']):
            raise ValueError(f'Changed {row["purpose"]}: {row["rva"]}')
        instructions[row['purpose']] = ins
    source = (HERE.parent / 'include/xar_bridge/ck3_12002_family_obligations_break.hpp').read_text(encoding='utf-8-sig')
    constants = {}
    for name, expected in manifest['source_constants'].items():
        match = re.search(rf'\b{re.escape(name)}\s*=\s*(0x[0-9A-Fa-f]+)', source)
        if not match or int(match.group(1), 0) != int(expected, 0):
            raise ValueError(f'Changed source constant {name}')
        constants[name] = int(expected, 0)
    for row in manifest['native_constant_bindings']:
        ins = instructions[row['purpose']]
        kind = row['kind']
        if kind == 'rip':
            values = [ins.address + ins.size + o.mem.disp for o in ins.operands
                      if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]
        elif kind == 'displacement':
            values = [o.mem.disp for o in ins.operands if o.type == X86_OP_MEM]
        else:
            values = [o.imm for o in ins.operands if o.type == X86_OP_IMM]
        if values != [constants[row['constant']]]:
            raise ValueError(f'Native instruction disagrees with {row["constant"]}')
    return {'status': 'GREEN', 'readiness': 'static-ready', 'local_ck3_touched': False,
            'live_verified': False, 'executable_sha256': hashlib.sha256(data).hexdigest(),
            'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            'span_count': len(manifest['signature_anchors']),
            'semantic_instruction_count': len(manifest['semantic_checks']),
            'source_binding_count': len(manifest['native_constant_bindings']),
            'known_gaps': manifest['known_gaps']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify_break(args.exe)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
