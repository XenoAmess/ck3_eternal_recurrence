"""Read-only exact-build byte/ABI fixture verification; never opens CK3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_64, Cs


def identity(path: Path) -> dict:
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path.resolve()), 'bytes': path.stat().st_size, 'sha256': digest}


def verify(executable: Path, fixture_path: Path) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding='utf-8-sig'))
    if fixture['schema'] != 'ck3.knight-selector-death-static-abi.v1':
        raise ValueError('unexpected fixture schema')
    actual = identity(executable)
    expected = fixture['executable']
    if actual['bytes'] != expected['bytes'] or actual['sha256'] != expected['sha256']:
        raise ValueError('exact stock executable bytes differ')
    pe = pefile.PE(str(executable), fast_load=False)
    if pe.OPTIONAL_HEADER.ImageBase != int(expected['image_base'], 0):
        raise ValueError('image base differs')
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    checks = []

    def gate(name: str, passed: bool) -> None:
        checks.append({'name': name, 'pass': passed})
        if not passed:
            raise ValueError(name)

    for span in fixture['byte_spans']:
        start, end = int(span['start'], 0), int(span['end'], 0)
        data = pe.get_data(start, end - start)
        gate('static byte span ' + span['start'], len(data) == end - start and
             hashlib.sha256(data).hexdigest().upper() == span['sha256'])
    for anchor in fixture['semantic_anchors']:
        rva = int(anchor['rva'], 0)
        wanted = bytes.fromhex(anchor['bytes'])
        data = pe.get_data(rva, len(wanted))
        decoded = list(disassembler.disasm(data, rva))
        gate('anchor bytes ' + anchor['rva'], data == wanted)
        gate('anchor complete instruction ' + anchor['rva'], len(decoded) == 1 and
             decoded[0].size == len(wanted) and decoded[0].mnemonic == anchor['op'] and
             decoded[0].op_str == anchor['args'])
    prologues = []
    for hook in fixture['detour_admission']:
        rva = int(hook['rva'], 0)
        data = pe.get_data(rva, hook['patch_bytes'])
        instructions = list(disassembler.disasm(data, rva))
        gate('hook prefix exact bytes ' + hook['rva'], data.hex().upper() == hook['expected_hex'])
        gate('hook covers complete instructions ' + hook['rva'],
             sum(ins.size for ins in instructions) == hook['patch_bytes'])
        rip_relative = any('rip' in ins.op_str for ins in instructions)
        gate('hook RIP relocation classification ' + hook['rva'], rip_relative == hook['rip_relative'])
        prologues.append({'rva': hook['rva'], 'patch_bytes': hook['patch_bytes'],
                          'instruction_sizes': [ins.size for ins in instructions],
                          'requires_relocation': hook['requires_relocation'],
                          'jump_back_rva': hex(rva + hook['patch_bytes'])})
    return {'schema': 'ck3.knight-selector-death-static-verification.v1',
            'status': 'PASS_EXACT_BUILD_STATIC_BYTES', 'executable': actual,
            'fixture': identity(fixture_path), 'checks': checks, 'prologues': prologues,
            'no_game_launch': True, 'no_screen_input': True,
            'runtime_detour_verified': False, 'case_sole_cause_proven': False,
            'full_mutable_bundle_complete': False,
            'limits': 'The declared byte ranges are verification spans, not an assertion of complete function extents. Static equality is not a live trace.'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, default=Path(__file__).with_name('knight_selector_death_causality_11906_a01.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refusing to overwrite an existing attempt')
    report = verify(args.executable, args.fixture)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'receipt': identity(args.output), 'check_count': len(report['checks']),
                      'status': report['status']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
