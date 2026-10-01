"""Verify 1.20.0.2 planner ownership and type anchors from an on-disk PE."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


SHA256 = 'AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D'
IMAGE_BASE = 0x140000000
CODE = {
    'planner_constructor_owner': (0x11B2885, '49 89 B4 24 A0 00 00 00'),
    'planner_widget': (0x21603AA, '48 8B 59 60'),
    'planner_stage': (0x11B8693, '48 63 81 E8 1A 00 00'),
    'planner_selected_type': (0x11B64C0, '48 8B 81 00 15 00 00'),
    'planner_factory_installs_slot': (0xB0AB48, '48 89 87 C0 03 00 00'),
    'host_factory_owner': (0xB0AEA7, '48 89 AE A0 00 00 00'),
    'host_scope_base': (0xB0AEDE, '48 8D 8E C8 00 00 00'),
    'host_factory_type': (0xB0AF0D, '48 89 86 38 02 00 00'),
    'host_factory_installs_slot': (0xB0AF25, '48 89 B5 D8 03 00 00'),
    'host_type_getter': (0x1643A70, '48 8B 81 38 02 00 00'),
    'activity_key_string_base': (0x3110394, '48 8D 4F 18'),
    'activity_key_string_capacity': (0x31103B2, '48 C7 41 18 0F 00 00 00'),
}
VTABLE = {
    'planner_slot0': (0x45325C8, 0x11B2E30),
    'planner_visibility': (0x45325C8 + 7 * 8, 0x21603A0),
    'planner_cost_slot11': (0x45325C8 + 11 * 8, 0xB1F0A0),
    'planner_cost_slot12': (0x45325C8 + 12 * 8, 0x11B5B30),
    'planner_secondary_slot0': (0x45326A0, 0x11D3404),
    'planner_notification_slot25': (0x45325C8 + 25 * 8, 0x11B6550),
}
RTTI = {
    'planner_primary': (0x45325C8, 0, '.?AVCActivityPlanner@@'),
    'planner_secondary': (0x45326A0, 0x10, '.?AVCActivityPlanner@@'),
    'host_primary': (0x457A138, 0, '.?AVCActivityListDetailHostView@@'),
    'host_secondary': (0x457A110, 0x10, '.?AVCActivityListDetailHostView@@'),
    'activity_type': (0x48BFE50, 0, '.?AVCActivityType@@'),
}


def verify(executable: Path) -> dict:
    raw = executable.read_bytes()
    image = pefile.PE(data=raw, fast_load=True)
    actual_sha = hashlib.sha256(raw).hexdigest().upper()
    failures = []
    rows = []
    if actual_sha != SHA256:
        failures.append('executable_sha256')
    if image.OPTIONAL_HEADER.ImageBase != IMAGE_BASE:
        failures.append('image_base')
    for name, (rva, expected_hex) in CODE.items():
        expected = bytes.fromhex(expected_hex)
        actual = image.get_data(rva, len(expected))
        match = actual == expected
        rows.append({'name': name, 'rva': hex(rva), 'expected': expected.hex(),
            'actual': actual.hex(), 'verified': match})
        if not match:
            failures.append(name)
    for name, (rva, target) in VTABLE.items():
        actual = struct.unpack('<Q', image.get_data(rva, 8))[0] - IMAGE_BASE
        match = actual == target
        rows.append({'name': name, 'rva': hex(rva), 'expected_target': hex(target),
            'actual_target': hex(actual), 'verified': match})
        if not match:
            failures.append(name)
    for name, (vt, expected_offset, expected_name) in RTTI.items():
        col = struct.unpack('<Q', image.get_data(vt - 8, 8))[0] - IMAGE_BASE
        signature, offset, _, descriptor = struct.unpack('<IIII', image.get_data(col, 16))
        actual_name = image.get_data(descriptor + 16, 160).split(b'\0')[0].decode('ascii')
        match = signature == 1 and offset == expected_offset and actual_name == expected_name
        rows.append({'name': name, 'vtable_rva': hex(vt), 'col_rva': hex(col),
            'object_offset': offset, 'type_name': actual_name, 'verified': match})
        if not match:
            failures.append(name)
    return {'schema': 'xar.ck3_12002.feast-planner-identity-abi.v1',
        'status': 'GREEN' if not failures else 'RED', 'verified': not failures,
        'game_version': '1.20.0.2', 'executable_sha256': actual_sha,
        'local_ck3_contacted': False, 'rows': rows, 'mismatches': failures}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = verify(args.exe)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'proof_count': len(result['rows']),
        'executable_sha256': result['executable_sha256'], 'mismatches': result['mismatches']}))
    return 0 if result['verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
