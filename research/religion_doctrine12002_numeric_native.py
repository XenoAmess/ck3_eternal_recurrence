#!/usr/bin/env python3
"""Verify five exact 1.20.0.2 religious special cache fields against frozen EXE."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / 'ck3_autonomous_player/native_bridge/research'))
    from scan_anchors import PeImage
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    manifest_path = Path(__file__).with_name('religion_doctrine12002_numeric_abi.json')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    data = a.exe.read_bytes()
    if len(data) != manifest['executable_size'] or hashlib.sha256(data).hexdigest().upper() != manifest['executable_sha256']:
        raise ValueError('Exact CK3 build differs')
    pe = PeImage(data)
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    def read(rva: int, length: int) -> bytes:
        off = pe.rva_to_offset(rva)
        return data[off:off+length]
    disassembly = []
    for item in manifest['native_spans']:
        start, end = int(item['rva'], 16), int(item['end_rva_exclusive'], 16)
        raw = read(start, end-start)
        if raw != bytes.fromhex(item['bytes']) or hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('Span differs: '+item['name'])
        instructions = list(decoder.disasm(raw, start))
        if sum(i.size for i in instructions) != len(raw):
            raise ValueError('Disassembly does not cover native span: '+item['name'])
        disassembly += [item['name']+' '+item['kind']]
        disassembly += [f'{i.address:08X} {i.bytes.hex(" "):36} {i.mnemonic} {i.op_str}' for i in instructions]
    for field in manifest['fields']:
        if read(int(field['builtin_table_rva'], 16),16) != bytes.fromhex(field['builtin_table_bytes']) or \
           read(int(field['key_rva'], 16), len(field['key'])+1) != bytes.fromhex(field['key_bytes']):
            raise ValueError('Native key binding differs: '+field['key'])
    header = (root / 'ck3_autonomous_player/native_bridge/include/xar_bridge/religion_doctrine12002_numeric.hpp').read_text(encoding='utf-8')
    for name, offset in manifest['provider_constants'].items():
        if f'{name} = {offset};' not in header:
            raise ValueError('Provider offset differs: '+name)
    output = a.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'native-disassembly.txt').write_text('\n'.join(disassembly)+'\n', encoding='utf-8')
    result = {'status':'GREEN', 'readiness':'static-confirmed', 'local_ck3_touched':False,
              'live_verified':False, 'executable_sha256':manifest['executable_sha256'],
              'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              'native_span_count':len(manifest['native_spans']), 'actual_key_count':len(manifest['fields']),
              'provider_constant_count':len(manifest['provider_constants'])}
    (output / 'native-verification.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
