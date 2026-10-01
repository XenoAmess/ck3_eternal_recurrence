"""Verify the 1.20 recovery county ABI from EXE bytes only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_REG_RIP, X86_OP_IMM
from scan_anchors import PeImage

EXACT_SHA = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
DEFAULT_EXE = Path('Z:/ck3_mod_rewrite/artifacts/migrations/2026-09-30/post-update-1.20.0.2/installation/binaries/ck3.exe')


def verify(exe: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    binary = exe.read_bytes()
    digest = hashlib.sha256(binary).hexdigest().upper()
    if digest != EXACT_SHA or manifest['executable_sha256'] != digest:
        raise ValueError('not the frozen 1.20.0.2 executable')
    pe = PeImage(binary)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    for span in manifest['source_contract']['exact_function_spans']:
        start, end = int(span['start_rva'], 0), int(span['end_rva'], 0)
        offset = pe.rva_to_offset(start)
        if hashlib.sha256(binary[offset:offset + end - start]).hexdigest().upper() != span['sha256']:
            raise ValueError(f"function bytes differ: {span['name']}")
    observations = {}
    direct_edges = 0
    rip_edges = 0
    for row in manifest['instruction_checks']:
        rva = int(row['rva'], 0)
        offset = pe.rva_to_offset(rva)
        ins = next(decoder.disasm(binary[offset:offset+15], rva))
        actual = {
            'bytes': ins.bytes.hex(' '),
            'instruction': f'{ins.mnemonic} {ins.op_str}'.strip(),
            'rip_targets': [hex(ins.address + ins.size + operand.mem.disp) for operand in ins.operands if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP],
            'direct_targets': [hex(operand.imm) for operand in ins.operands if operand.type == X86_OP_IMM and ins.mnemonic in ('call', 'jmp')],
        }
        if any(actual[key] != row[key] for key in actual):
            raise ValueError(f'instruction differs: {hex(rva)}')
        observations[rva] = actual['instruction']
        direct_edges += len(actual['direct_targets'])
        rip_edges += len(actual['rip_targets'])
    for row in manifest['vtable_checks']:
        address = int(row['vtable_rva'], 0) + row['index'] * 8
        actual = struct.unpack_from('<Q', binary, pe.rva_to_offset(address))[0] - pe.image_base
        if actual != int(row['target_rva'], 0):
            raise ValueError(f"vtable differs: {row['name']}")
    rtti = manifest['rtti']
    vtable = int(rtti['vtable_rva'], 0)
    col = struct.unpack_from('<Q', binary, pe.rva_to_offset(vtable) - 8)[0] - pe.image_base
    if col != int(rtti['complete_object_locator_rva'], 0):
        raise ValueError('county modifier RTTI COL differs')
    type_rva = struct.unpack_from('<I', binary, pe.rva_to_offset(col) + 12)[0]
    if type_rva != int(rtti['type_descriptor_rva'], 0):
        raise ValueError('county modifier RTTI type differs')
    name = pe.rva_to_offset(type_rva) + 16
    actual_name = binary[name:binary.index(b'\0', name)].decode('ascii')
    if actual_name != rtti['decorated_type_name']:
        raise ValueError('county modifier RTTI name differs')

    # The decisive register/result shape is independently expected here.
    expected_shape = {
        0x1AF9E86: 'cmp word ptr [rax], 5',
        0x1AF9E8C: 'mov edx, dword ptr [rax + 8]',
        0x1AF9EC0: 'cmp dword ptr [rcx + 0x10], edx',
        0x1AF5D5B: 'mov rbp, r8',
        0x1AF5D5E: 'mov rdi, rdx',
        0x1AF5D61: 'mov rbx, rcx',
        0x1AF5D78: 'mov rax, qword ptr [rdx + 0x48]',
        0x1AF5D7C: 'cmp dword ptr [rax + 0x64], 2',
        0x1AF5E40: 'cmp qword ptr [rdx], rbp',
        0x1AF5E45: 'add rdx, 0x48',
        0x1AF5E63: 'mov rax, qword ptr [rdx + 8]',
        0x1AF5E67: 'mov qword ptr [rbx], rax',
        0x1AF5E6C: 'mov byte ptr [rbx + 8], al',
        0x1AF5ECE: 'mov byte ptr [rbx + 8], 0',
        0x1AF5ED7: 'mov rax, rbx',
        0x1AF8B0E: 'mov r8, qword ptr [rbx + 0x60]',
        0x1AF8B12: 'lea rcx, [rsp + 0x20]',
        0x1AF8B17: 'call 0x1af5d40',
        0x1AF8B1C: 'cmp byte ptr [rsp + 0x28], 0',
    }
    if any(observations[rva] != expected for rva, expected in expected_shape.items()):
        raise ValueError('native county/full-generation/sret16 call shape differs')
    return {
        'verification': 'passed',
        'game_version': '1.20.0.2',
        'executable_sha256': digest,
        'manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        'function_spans': len(manifest['source_contract']['exact_function_spans']),
        'instruction_checks': len(manifest['instruction_checks']),
        'direct_call_jump_edges': direct_edges,
        'rip_edges': rip_edges,
        'vtable_checks': len(manifest['vtable_checks']),
        'rtti_checks': 3,
        'semantic_call_shape_checks': len(expected_shape),
        'process_accessed': False,
        'live_validated': False,
        'remaining_days_available': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, default=DEFAULT_EXE)
    parser.add_argument('--manifest', type=Path, default=Path(__file__).with_suffix('.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.exe, args.manifest)
    rendered = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered, end='')


if __name__ == '__main__':
    main()
