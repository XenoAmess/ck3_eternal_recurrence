"""Reproduce the fixed .3 ordinary interaction prefixes, using file bytes only.

No process, native call, injection or source-tree write is performed. The
original projection was authored by wire_ordinary_native.py; this isolated
entry point reproduces its exact bytes without replaying its wiring edits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED_EXE_SHA256 = '94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6'
FIXED_RVAS = (0x89DA60, 0x3F7E240, 0xA055E0, 0x3076C90, 0x30796B0,
              0x30788E0, 0x3078880, 0x307BC80, 0x3076E50, 0x3078A60,
              0x3078C90, 0x307C040, 0x30773A0, 0x2968170, 0x37F06F0,
              0x3148DE0, 0x310CEE0, 0x372DF30, 0x307C460, 0x307C360)


def code_prefix(data: bytes, rva: int) -> bytes:
    if data[:2] != b'MZ':
        raise ValueError('not PE MZ')
    pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b'PE\0\0':
        raise ValueError('not PE signature')
    machine, sections = struct.unpack_from('<HH', data, pe_offset + 4)
    optional_size = struct.unpack_from('<H', data, pe_offset + 20)[0]
    if machine != 0x8664 or struct.unpack_from('<H', data, pe_offset + 24)[0] != 0x20B:
        raise ValueError('not AMD64 PE32+')
    section_start = pe_offset + 24 + optional_size
    matches = []
    for i in range(sections):
        offset = section_start + i * 40
        virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from('<IIII', data, offset + 8)
        flags = struct.unpack_from('<I', data, offset + 36)[0]
        if virtual_address <= rva and rva + 32 <= virtual_address + min(virtual_size, raw_size):
            if not flags & 0x20000000:
                raise ValueError('fixed prefix is not executable section bytes')
            raw = raw_offset + rva - virtual_address
            prefix = data[raw:raw + 32]
            if len(prefix) != 32:
                raise ValueError('prefix outside actual file')
            matches.append(prefix)
    if len(matches) != 1:
        raise ValueError('fixed RVA has no unique file section mapping')
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True, help='new external directory, never source tree')
    parser.add_argument('--verify-candidate', type=Path, required=True, help='readonly exact generated include to compare')
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    source_roots = {Path(__file__).resolve().parents[1], args.verify_candidate.resolve().parent.parent}
    for source_root in source_roots:
        if output_root == source_root or output_root.is_relative_to(source_root):
            raise ValueError('output must be outside generator and candidate source trees')
    data = args.exe.read_bytes()
    exe_sha = hashlib.sha256(data).hexdigest()
    if exe_sha != EXPECTED_EXE_SHA256:
        raise ValueError('exact installed .3 executable SHA mismatch; no generation')
    lines = ['// Generated from exact frozen .3 PE code prefixes by wire_ordinary_native.py.',
             '// No ASLR-dependent absolute vtable pointer bytes appear here.',
             f'constexpr std::array<CodePin, {len(FIXED_RVAS)}> kOrdinaryInteractionCodePinsV1{{{{']
    pins = []
    for rva in FIXED_RVAS:
        prefix = code_prefix(data, rva)
        lines.append('  {0x%X, {{%s}}},' % (rva, ', '.join(f'0x{x:02X}' for x in prefix)))
        pins.append({'rva': hex(rva), 'bytes': 32, 'sha256': hashlib.sha256(prefix).hexdigest()})
    lines.extend(['}};', ''])
    # Exact original Windows projection. Explicit CRLF also makes Linux
    # reproduction byte-identical to the reviewed source include.
    generated = '\r\n'.join(lines).encode('utf-8')
    candidate = args.verify_candidate.read_bytes()
    if candidate != generated:
        raise ValueError('readonly candidate is not exact current-file projection')
    args.output_root.mkdir(parents=True, exist_ok=False)
    output = args.output_root / 'ordinary_interaction_code_pins_v1.inc'
    output.write_bytes(generated)
    report = {'schema': 'ordinary-interaction-pins-file-reproduction-v1', 'status': 'PASS',
              'executable': str(args.exe.resolve()), 'executable_bytes': len(data), 'executable_sha256': exe_sha,
              'candidate': str(args.verify_candidate.resolve()), 'candidate_sha256': hashlib.sha256(candidate).hexdigest(),
              'generated': str(output.resolve()), 'generated_sha256': hashlib.sha256(generated).hexdigest(),
              'exact_bytes_equal': True, 'pin_count': len(pins), 'pins': pins,
              'input_scope': 'fixed file PE section bytes only', 'native_process_called': False,
              'source_tree_written': False, 'generator': str(Path(__file__).resolve()),
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output_root / 'REPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: 20 exact .3 prefixes reproduced; candidate SHA ' + report['candidate_sha256'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
