#!/usr/bin/env python3
"""Freeze actual CK3 conversion flag expiry counters; never access a game process."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'ck3_autonomous_player/native_bridge/research'))
from scan_anchors import PeImage

SHA = 'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d'
MANIFEST = HERE / 'conversion_outcome12002_state_abi.json'
HEADER = HERE.parent / 'ck3_autonomous_player/native_bridge/include/xar_bridge/conversion_outcome12002_state.hpp'
CONSTANTS = {'kFlagExpiryCounterOffset': 0x0C, 'kFlagCurrentCounterOffset': 0x28,
             'kBaselineFulfillmentOffset': 0x300}
SPANS = [
    ('add_character_flag.registration', 0x5DC8B0, 0x5DC954, 'registration only; not called'),
    ('CharacterFlagEffect.construct', 0x2D5CF20, 0x2D5CF9E, 'constructor attribution; not called'),
    ('CharacterFlagEffect.execute', 0x2D56680, 0x2D56830, 'effect attribution; not called'),
    ('FlagSet.insert_or_replace', 0x3728420, 0x37285AE, 'void(FlagSet+8,key,payload,duration); not called'),
    ('FlagSet.update', 0x3727600, 0x372789A, 'void(FlagSet*); increments counter then expires; not called'),
    ('FlagRows.normalize_counter', 0x887360, 0x8873A8, 'void(FlagSet+8); mutating normalizer; not called'),
    ('FlagRow.serialize', 0x888870, 0x8889EE, 'serializer attribution; not called'),
    ('FlagRow.deserialize', 0x888CD0, 0x888D36, 'deserializer attribution; not called'),
]
SITES = [
    ('effect_script_data', 0x2D567CE, 'mov', None),
    ('effect_flag_collection', 0x2D567E3, 'call', 0x1D67200),
    ('effect_actual_duration', 0x2D567F6, 'call', 0x374D370),
    ('effect_flagset_subobject', 0x2D567FE, 'lea', None),
    ('effect_insert', 0x2D5680A, 'call', 0x3728420),
    ('empty_rows_reset_counter', 0x3728438, 'mov', None),
    ('native_flag_row_type', 0x3728440, 'lea', None),
    ('duration_positive', 0x3728459, 'test', None),
    ('actual_current_counter', 0x372845E, 'mov', None),
    ('actual_expiry_from_counter', 0x3728461, 'add', None),
    ('permanent_sentinel', 0x3728466, 'mov', None),
    ('row_stride', 0x372849B, 'add', None),
    ('actual_row_key_write', 0x3728502, 'mov', None),
    ('actual_expiry_write', 0x3728506, 'mov', None),
    ('update_counter_increment', 0x3727636, 'inc', None),
    ('update_reads_counter', 0x372763C, 'mov', None),
    ('update_expiry_comparison', 0x3727643, 'cmp', None),
    ('update_normalizes_rows', 0x372764E, 'call', 0x887360),
    ('expired_row_remove', 0x3727674, 'dec', None),
    ('normalizer_reads_expiry', 0x887384, 'mov', None),
    ('normalizer_subtracts_counter', 0x88738E, 'sub', None),
    ('normalizer_writes_expiry', 0x887395, 'mov', None),
    ('normalizer_resets_counter', 0x8873A3, 'mov', None),
    ('serializer_permanent_check', 0x88895D, 'cmp', None),
    ('serializer_actual_expiry', 0x888985, 'mov', None),
    ('parser_actual_expiry_field', 0x888CFB, 'lea', None),
]
REUSED = [
    ('religion_conversion12002_gates_abi.json', 'target knowledge / existing atom lookup / flag presence / full Rite identity'),
    ('religion12002_native_abi.json', 'actual Character.GetSpiritualFulfillment 0x28BCE40'),
    ('religion_conversion12002_outcome_abi.json', 'actual baseline at Character+0x1B0 -> +0x300'),
]
STOCK = [
    ('common/scripted_effects/pam_effects.txt', 11516, 11524, 'faith_conversion_recently_converted'),
    ('common/scripted_effects/00_religion_effects.txt', 1460, 1511, 'conversion_memory_recently_created'),
    ('events/religion_events/faith_conversion_events.txt', 456, 541, 'recent_convert'),
]

def extract(exe: Path, game: Path) -> tuple[dict, str, str]:
    data = exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError('Not the frozen CK3 1.20.0.2 executable')
    pe = PeImage(data); md = Cs(CS_ARCH_X86, CS_MODE_64); md.detail = True
    def read(rva, size):
        at = pe.rva_to_offset(rva)
        return data[at:at+size]
    header = HEADER.read_text(encoding='utf-8-sig')
    for name, value in CONSTANTS.items():
        m = re.search(rf'\b{name}\s*=\s*(0x[0-9A-Fa-f]+)', header)
        if not m or int(m[1], 0) != value:
            raise ValueError('Actual source constant differs: '+name)
    spans, dump = [], []
    for name, start, end, abi in SPANS:
        raw = read(start, end-start); ins = list(md.disasm(raw, start))
        if not ins or ins[-1].address + ins[-1].size != end:
            raise ValueError('Instruction coverage differs: '+name)
        spans.append({'name': name, 'start_rva': hex(start), 'end_exclusive_rva': hex(end),
            'kind': 'complete_function_body', 'abi': abi, 'bytes': raw.hex(' '),
            'sha256': hashlib.sha256(raw).hexdigest()})
        dump.append(f'\n{name} [{start:#x},{end:#x})')
        dump.extend(f'{i.address:X} {i.bytes.hex(" "):32s} {i.mnemonic:8s} {i.op_str}' for i in ins)
    sites = []
    for name, rva, mnemonic, target in SITES:
        i = next(md.disasm(read(rva, 15), rva))
        direct = [o.imm for o in i.operands if o.type == X86_OP_IMM]
        if i.mnemonic != mnemonic or (target is not None and target not in direct):
            raise ValueError('Semantic instruction differs: '+name)
        sites.append({'name': name, 'rva': hex(rva), 'bytes': i.bytes.hex(' '),
                      'instruction': i.mnemonic+' '+i.op_str})
    reused = []
    for name, semantics in REUSED:
        raw = (HERE/name).read_bytes()
        old = json.loads(raw)
        if old['executable_sha256'].lower() != SHA:
            raise ValueError('Reused proof is for another build: '+name)
        reused.append({'path': 'research/'+name, 'sha256': hashlib.sha256(raw).hexdigest(),
                       'semantics': semantics, 'reverified': False})
    stocks, stock_dump = [], []
    for relative, first, last, key in STOCK:
        raw = (game/relative).read_bytes(); lines = raw.decode('utf-8-sig').splitlines()
        selected = '\n'.join(lines[first-1:last])
        if key not in selected or len(lines[first-1:last]) != last-first+1:
            raise ValueError('Actual stock key window differs: '+key)
        stocks.append({'path': relative, 'first_line': first, 'last_line': last,
                       'sha256': hashlib.sha256(raw).hexdigest(), 'key': key, 'text': selected})
        stock_dump.append(f'\n{relative}:{first}-{last}\n'+selected)
    return {'schema': 'ck3_12002_religion_conversion_outcome_state_abi_v1',
        'game_version': '1.20.0.2', 'executable_sha256': SHA,
        'readiness': 'static-confirmed', 'local_ck3_touched': False, 'live_verified': False,
        'provider_constants': {k: hex(v) for k, v in CONSTANTS.items()},
        'native_spans': spans, 'semantic_instructions': sites, 'reused_native_proofs': reused,
        'stock_evidence': stocks, 'expiry_unit': 'native_flag_updates',
        'expiry_is_game_calendar_date': False,
        'remaining_updates': 'actual signed row+0x0C minus actual FlagSet+0x28, only expiry > -1',
        'unresolved': ['paused live flag/knowledge/current/baseline samples',
                       'conversion causality and delayed narrative events are not asserted']}, \
        '\n'.join(dump)+'\n', '\n'.join(stock_dump)+'\n'

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--exe', type=Path, required=True); p.add_argument('--game', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True); p.add_argument('--record', action='store_true')
    a = p.parse_args(); record, disassembly, stock = extract(a.exe, a.game)
    if a.record:
        MANIFEST.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    elif json.loads(MANIFEST.read_text(encoding='utf-8')) != record:
        raise ValueError('Recorded state ABI differs')
    a.output_dir.mkdir(parents=True, exist_ok=True)
    (a.output_dir/'native-disassembly.txt').write_text(disassembly, encoding='utf-8')
    (a.output_dir/'stock-evidence.txt').write_text(stock, encoding='utf-8')
    receipt = {'status': 'GREEN', 'readiness': 'static-confirmed', 'live_verified': False,
        'local_ck3_touched': False, 'executable_sha256': SHA,
        'complete_function_bodies': len(SPANS), 'semantic_instructions': len(SITES),
        'source_constants': len(CONSTANTS), 'reused_proofs_not_retested': len(REUSED),
        'stock_windows': len(STOCK), 'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        'disassembly_sha256': hashlib.sha256(disassembly.encode()).hexdigest(),
        'stock_sha256': hashlib.sha256(stock.encode()).hexdigest()}
    (a.output_dir/'native-verification.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
