"""Verify frozen CK3 nonmilitary clerical AI inputs and actual native loading.

Only reads an executable and frozen stock files. No process, desktop, pipe,
Steam, command submission, provider or counter-policy is involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ck3_autonomous_player/native_bridge/research'))
from scan_anchors import PeImage

EXACT_SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MAP = HERE / 'religion_rite_governance12002_ai_native.json'
SPANS = [
    ('CCharacterInteraction.parse_virtual_thunk', 0x2FD9D60, 0x2FD9D6C),
    ('CCharacterInteraction.parse_body_with_embedded_tables', 0x3145760, 0x3147E61),
    ('AITarget.parse_wrapper', 0x314A7C0, 0x314A7E2),
    ('AITarget.parse_loop_complete_chained_body', 0x314BB60, 0x314BE4B),
    ('AITarget.parse_fields', 0x292E2C0, 0x292E522),
    ('ByTier.parse_dispatch', 0x3105390, 0x3105504),
    ('ByTier.parse_initialize_with_embedded_table', 0x287F6A0, 0x287F9D0),
    ('ByTier.parse_values', 0x287F9D0, 0x287FE08),
]
SITES = [0x2FD9D67, 0x314781A, 0x3145AC2, 0x31053C2,
         0x31053DA, 0x287F6D4, 0x287F6D8, 0x287F701, 0x287F833,
         0x287FB3B, 0x287FB4A, 0x287FB50, 0x3147039,
         0x31471A4, 0x31471AF, 0x314A7D8, 0x314BBF2,
         0x292E30B, 0x292E32A, 0x292E334, 0x292E33E, 0x292E34F, 0x292E35E]
TOKEN_ROWS = [
    ('ai_targets', 0x46F1CD8, 0x3335),
    ('ai_recipients', 0x46F1AA8, 0x330E),
    ('ai_frequency_by_tier', 0x46FAA28, 0x3C29),
    ('rulers_in_clerical_region', 0x4701318, 0x42C5),
    ('clerical_region_rulers_in_realm', 0x4701328, 0x42C6),
]
STOCK_WINDOWS = {
    'common/character_interactions/pam_interactions.txt': [
        (1528, 1798), (1800, 1847), (4461, 4596),
        (4645, 4693), (4697, 4887), (4889, 5102), (5105, 5271)],
    'common/scripted_triggers/pam_scripted_triggers.txt': [
        (2973, 2985), (5317, 5326), (5426, 5431)],
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract(exe: Path) -> tuple[dict, str]:
    data = exe.read_bytes()
    if digest(data) != EXACT_SHA:
        raise ValueError('Expected the frozen 1.20.0.2 executable')
    pe = PeImage(data)
    def read(rva: int, size: int) -> bytes:
        off = pe.rva_to_offset(rva)
        return data[off:off+size]
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    spans, text = [], []
    for name, start, end in SPANS:
        raw = read(start, end-start)
        spans.append({'name': name, 'start_rva': hex(start),
                      'end_exclusive_rva': hex(end), 'sha256': digest(raw),
                      'bytes': raw.hex(' '),
                      'kind': 'complete reviewed body; embedded tables retained where named'})
        text.append(f'\n{name} [{start:#x},{end:#x})\n')
        # Some complete PE bodies include jump-table data. Semantic sites below
        # are decoded separately; sequential decoding is a viewing aid only.
        text.extend(f'{i.address:08x} {i.bytes.hex(" "):32} {i.mnemonic:8} {i.op_str}\n'
                    for i in decoder.disasm(raw, start))
    sites = []
    for rva in SITES:
        ins = next(decoder.disasm(read(rva, 15), rva))
        sites.append({'rva': hex(rva), 'bytes': ins.bytes.hex(' '),
                      'instruction': f'{ins.mnemonic} {ins.op_str}',
                      'direct_targets': [hex(o.imm) for o in ins.operands
                                         if o.type == X86_OP_IMM and ins.mnemonic in ('call', 'jmp')],
                      'rip_targets': [hex(ins.address+ins.size+o.mem.disp) for o in ins.operands
                                      if o.type == X86_OP_MEM and o.mem.base == X86_REG_RIP]})
    tokens = []
    for name, row, token in TOKEN_ROWS:
        address, ordinal = struct.unpack('<QQ', read(row, 16))
        srva = address-pe.image_base
        actual = read(srva, len(name)+1)
        if actual != name.encode()+b'\0' or ordinal != token+1:
            raise ValueError(f'Frozen token row mismatch: {name}')
        tokens.append({'name': name, 'table_row_rva': hex(row),
                       'string_rva': hex(srva), 'table_ordinal': ordinal,
                       'reviewed_runtime_token': hex(token), 'row_bytes': read(row, 16).hex(' ')})
    enum = list(struct.unpack('<57I', read(0x4766290, 57*4)))
    if enum[51:53] != [0x42C5, 0x42C6]:
        raise ValueError('Actual AI recipient enum mapping changed')
    rtti_name = read(0x5538F20, len('.?AVCCharacterInteraction@@')+1)
    if rtti_name != b'.?AVCCharacterInteraction@@\0':
        raise ValueError('Exact CharacterInteraction RTTI differs')
    col = read(0x4F834C0, 24)
    if struct.unpack('<6I', col) != (1, 0x2750, 4, 0x5538F10, 0x4F515C0, 0x4F834C0):
        raise ValueError('CharacterInteraction COL differs')
    prefix = [v-pe.image_base for v in struct.unpack('<6Q', read(0x48C2228, 48))]
    if prefix[4] != 0x2FD9D60:
        raise ValueError('Actual virtual parser slot differs')
    result = {'schema': 'ck3_12002_religion_rite_governance_ai_native_v1',
              'game_version': '1.20.0.2', 'executable_sha256': EXACT_SHA,
              'executable_size': len(data), 'readiness': 'research',
              'static_confirmed_scope': 'actual interaction loading and native recipient enum mapping',
              'local_ck3_touched': False, 'provider_implemented': False,
              'counter_policy_changed': False, 'live_verified': False,
              'complete_native_spans': spans, 'semantic_instructions': sites,
              'token_rows': tokens,
              'interaction_rtti': {'type_descriptor_rva': '0x5538f10', 'name_rva': '0x5538f20',
                                   'COL_rva': '0x4f834c0', 'COL_bytes': col.hex(' '),
                                   'vtable_rva': '0x48c2228', 'vtable_prefix_rvas': [hex(v) for v in prefix]},
              'recipient_enum': {'array_rva': '0x4766290', 'count': 57,
                                 'tokens': [hex(t) for t in enum],
                                 'nonmilitary_governance_slots': {'rulers_in_clerical_region': 51,
                                                                'clerical_region_rulers_in_realm': 52}},
              'unresolved': ['runtime AI scheduling and interpretation of frequency units',
                             'actual clerical recipient enumeration consumers',
                             'send-option selection and native AI intention roll',
                             'native final CanSend, reasons, cost and acceptance for each target',
                             'actual outcomes and next-turn/cold readback']}
    return result, ''.join(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe', required=True, type=Path)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    result, disassembly = extract(args.exe)
    if args.record:
        MAP.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    elif json.loads(MAP.read_text(encoding='utf-8')) != result:
        raise ValueError('Reviewed native map differs from the frozen executable')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records, chunks = [], []
    for rel, windows in STOCK_WINDOWS.items():
        path = args.game/rel
        raw = path.read_bytes()
        lines = raw.decode('utf-8-sig').splitlines()
        records.append({'path': rel, 'sha256': digest(raw), 'windows': windows})
        chunks.append(f'FILE {rel} SHA256 {digest(raw)}\n')
        for start, end in windows:
            if not 1 <= start <= end <= len(lines):
                raise ValueError((rel, start, end))
            chunks.extend(f'{i+1:5}: {lines[i]}\n' for i in range(start-1, end))
    outputs = {'native-disassembly.txt': disassembly, 'stock-evidence-windows.txt': ''.join(chunks)}
    for name, content in outputs.items():
        (args.output_dir/name).write_text(content, encoding='utf-8')
    receipt = {'schema': 'ck3_12002_religion_rite_governance_ai_receipt_v1', 'status': 'GREEN',
               'readiness': 'research', 'static_confirmed_native_loading': True,
               'native_ai_schedule_verified': False, 'local_ck3_touched': False,
               'executable_sha256': EXACT_SHA, 'native_spans': len(SPANS),
               'semantic_instructions': len(SITES), 'recipient_enum_rows': 57,
               'nonmilitary_clerical_enum_rows': 2, 'sources': records,
               'map_sha256': digest(MAP.read_bytes()), 'script_sha256': digest(Path(__file__).read_bytes()),
               'artifacts': {str(args.output_dir/name): digest((args.output_dir/name).read_bytes()) for name in outputs}}
    (args.output_dir/'verification.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
