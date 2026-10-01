"""Verify the native balance branches used by the 1.20 law source adapter."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pefile

CONTRACT = Path(__file__).with_name('ck3_12002_realm_law_source_resources_abi.json')


def verify(executable: Path) -> list[str]:
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    data = executable.read_bytes()
    build = contract['build']
    if len(data) != build['size'] or hashlib.sha256(data).hexdigest().upper() != build['sha256']:
        raise ValueError('exact executable identity mismatch')
    pe = pefile.PE(data=data, fast_load=True)
    checked = []
    for span in contract['instruction_spans']:
        start, end = int(span['rva'], 16), int(span['end_rva'], 16)
        content = pe.get_data(start, end - start)
        if len(content) != end - start or hashlib.sha256(content).hexdigest().upper() != span['sha256']:
            raise ValueError(f"{span['name']}: balance ABI changed")
        checked.append(span['name'])
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    args = parser.parse_args()
    names = verify(args.exe)
    print(f'ck3_12002_realm_law_source_resources_abi: {len(names)}/{len(names)} GREEN')
