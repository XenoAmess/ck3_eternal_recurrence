#!/usr/bin/env python3
"""Verify frozen CK3 1.20.0.2 conversion input getters without accessing CK3."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ck3_autonomous_player/native_bridge/research'))
from scan_anchors import PeImage

SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MANIFEST = HERE / 'religion_conversion12002_gates_abi.json'
HEADER = HERE.parent / 'ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12002_religion_conversion_gates.hpp'
CONSTANTS = {
    'kRiteStorageSlotRva': 0x5D1E2F8, 'kRiteKnowledgeRva': 0x2BDBDE0,
    'kExistingAtomLookupRva': 0x3F8A3A0, 'kAtomPoolRva': 0x5DC1390,
    'kCharacterFlagCollectionRva': 0x1D67200,
    'kCharacterScriptDataOffset': 0x1B0, 'kCharacterDummyOffset': 0x1A5,
    'kFlagRowsOffset': 0x10, 'kFlagCountOffset': 0x1C,
    'kFlagRowStride': 0x20, 'kFlagKeyOffset': 0x08,
}
SPANS = [
    ('knows_rite_level.registration', 0x57E440, 0x57E4D8, 'registration_factory'),
    ('RiteKnowledgeValueTrigger.value', 0x2AEA480, 0x2AEA5BD, 'int64_t*(Trigger*,out,scope)'),
    ('Character.GetRiteKnowledge', 0x2BDBDE0, 0x2BDC39A, 'int64_t*(out,Character*,Rite*)'),
    ('Rite.IsMainRite', 0x24F7E40, 0x24F7EA2, 'bool(Rite*)'),
    ('Character.KnowsDoctrine', 0x28B0A30, 0x28B0AF2, 'bool(Character*,Doctrine*)'),
    ('Character.KnowsTenet', 0x28B0C00, 0x28B0CCD, 'bool(Character*,Tenet*)'),
    ('has_character_flag.registration', 0x5ABF50, 0x5ABFE8, 'registration_factory'),
    ('CharacterFlagTrigger.parse', 0x2B7A440, 0x2B7A4D8, 'parser; insertion API not called by provider'),
    ('CharacterFlagTrigger.evaluate', 0x2B7A630, 0x2B7A748, 'bool(Trigger*,scope)'),
    ('CharacterFlagCollection.resolve', 0x1D67200, 0x1D6734B, 'FlagSet*(indexedScriptData*)'),
    ('StringAtom.existing_lookup', 0x3F8A3A0, 0x3F8A4B0, 'uint32_t*(pool,out,StringView*); complete chained body'),
    ('StringAtom.pool_accessor', 0x3F8A800, 0x3F8A8D3, 'pool address; provider binds existing inline object'),
    ('Character.GetRite', 0x28D2F90, 0x28D2FCD, 'Rite*(Character*); storage lookup with full generation'),
]
SITES = [
    ('knowledge_core_call', 0x2AEA519), ('knowledge_main_rite_test', 0x2BDBE2A),
    ('target_doctrine_rows', 0x2BDBE35), ('target_doctrine_count', 0x2BDBE3C),
    ('doctrine_eligible_flag', 0x2BDBE53), ('doctrine_known_call', 0x2BDBE62),
    ('target_tenet_rows', 0x2BDBF63), ('target_tenet_count', 0x2BDBF6A),
    ('tenet_eligible_flag', 0x2BDC041), ('tenet_known_call', 0x2BDC058),
    ('branch_parent_main_rite', 0x2BDC0DE), ('main_tenet_rows', 0x2BDC191),
    ('main_tenet_known_call', 0x2BDC23B), ('zero_eligible_is_zero', 0x2BDC267),
    ('knowledge_numerator_scale', 0x2BDC27B), ('knowledge_denominator_scale', 0x2BDC285),
    ('native_flag_dummy_check', 0x2B7A6AD), ('native_flag_script_data', 0x2B7A6BA),
    ('native_flag_collection_call', 0x2B7A6C6), ('flag_rows', 0x2B7A6F9),
    ('flag_count', 0x2B7A6FD), ('flag_row_key_compare', 0x2B7A710),
    ('flag_row_stride', 0x2B7A715), ('indexed_flag_set', 0x1D67265),
    ('atom_pool_address', 0x3F8A820), ('existing_key_out', 0x3F8A490),
    ('absent_key_out', 0x3F8A49E), ('rite_storage_slot', 0x28D2F90),
    ('rite_generation_compare', 0x28D2FC0),
]

def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError('Not the frozen 1.20.0.2 executable')
    pe = PeImage(data)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    header = HEADER.read_text(encoding='utf-8-sig')
    for name, value in CONSTANTS.items():
        m = re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)', header)
        if not m or int(m[1], 0) != value:
            raise ValueError(f'Actual source constant differs: {name}')
    def read(rva, size):
        at = pe.rva_to_offset(rva)
        return data[at:at+size]
    spans, dump = [], []
    for name, start, end, abi in SPANS:
        raw = read(start, end-start)
        spans.append({'name': name, 'start_rva': hex(start), 'end_exclusive_rva': hex(end),
                      'abi': abi, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': raw.hex(' ')})
        dump.append(f'\n{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:X} {i.bytes.hex(" "):32s} {i.mnemonic:8s} {i.op_str}' for i in md.disasm(raw, start))
    instructions = []
    for name, rva in SITES:
        i = next(md.disasm(read(rva, 15), rva))
        instructions.append({'name': name, 'rva': hex(rva), 'bytes': i.bytes.hex(' '),
                             'instruction': i.mnemonic + ' ' + i.op_str})
    return {'schema': 'ck3_12002_religion_conversion_gates_abi_v1', 'game_version': '1.20.0.2',
            'executable_sha256': SHA, 'readiness': 'static-confirmed',
            'local_ck3_touched': False, 'live_verified': False,
            'provider_constants': {k: hex(v) for k, v in CONSTANTS.items()},
            'native_spans': spans, 'semantic_instructions': instructions,
            'state_rite_dependency': 'religion_rite_governance12002_state_rite; existing exact ABI reused',
            'unresolved': ['live paused knowledge/flag samples', 'native AI reevaluation scheduler',
                           'final conversion legality/cost supplied by other dedicated components']}, '\n'.join(dump)+'\n'

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--record', action='store_true')
    a = p.parse_args()
    record, disassembly = extract(a.exe)
    if a.record:
        MANIFEST.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    elif json.loads(MANIFEST.read_text(encoding='utf-8')) != record:
        raise ValueError('Recorded native ABI differs')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir/'native-disassembly.txt').write_text(disassembly, encoding='utf-8')
    receipt = {'status': 'GREEN', 'readiness': 'static-confirmed', 'live_verified': False,
               'local_ck3_touched': False, 'executable_sha256': SHA,
               'native_spans': len(SPANS), 'semantic_instructions': len(SITES),
               'source_constants': len(CONSTANTS),
               'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
               'disassembly_sha256': hashlib.sha256(disassembly.encode()).hexdigest()}
    (a.output_dir/'native-verification.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
