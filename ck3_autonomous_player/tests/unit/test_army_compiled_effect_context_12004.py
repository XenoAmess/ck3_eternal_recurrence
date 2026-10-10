from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
MODULE_PATH = BASE / 'src/xar_autoplayer/bridge/army_compiled_effect_context_12004.py'
spec = importlib.util.spec_from_file_location('owned_context63', MODULE_PATH)
leaf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(leaf)
SOURCE = Path(__file__).resolve().parents[4] / 'SOURCE-CHILD-37652B0.json'


def source_nonnegative_pair(seed):
    """Independent finite U32 register interpretation of the retained body.

    Only the actually reached nonnegative arithmetic block is interpreted;
    no machine code, function pointer, allocator or game process is executed.
    """
    instructions = json.loads(SOURCE.read_text())['body']['instructions']
    registers = {'eax': seed}
    pair = [None, None]
    for ins in instructions:
        rva = ins['rva']
        if rva < 0x37652C7 or rva > 0x376530D:
            continue
        operands = ins['op_str'].split(', ')
        mnemonic = ins['mnemonic']
        dest = operands[0]
        if mnemonic == 'mov' and dest == 'dword ptr [rcx + 4]':
            pair[1] = 0
            continue
        if mnemonic == 'mov' and dest == 'dword ptr [rbx]':
            pair[0] = registers[operands[1]]
            continue
        def value(token):
            return registers[token] if token in registers else int(token, 0)
        if mnemonic == 'mov':
            new = value(operands[1])
        elif mnemonic == 'imul':
            new = value(operands[1]) * value(operands[2])
        elif mnemonic == 'sub':
            new = registers[dest] - value(operands[1])
        elif mnemonic == 'add':
            new = registers[dest] + value(operands[1])
        elif mnemonic == 'xor':
            new = registers[dest] ^ value(operands[1])
        elif mnemonic == 'shr':
            new = registers[dest] >> value(operands[1])
        elif mnemonic == 'shl':
            new = registers[dest] << value(operands[1])
        else:
            raise RuntimeError('Unmodeled retained instruction: ' + str(ins))
        registers[dest] = new & 0xFFFFFFFF
    if None in pair:
        raise RuntimeError('Retained block did not write both output words')
    return pair


class CompiledEffectContext12004(unittest.TestCase):
    def test_source_arguments_partial_inputs_and_no_historical_promotion(self):
        supplied = {
            'schema': leaf.INPUT_SCHEMA,
            'input_basis': leaf.INPUT_BASIS,
            'binding': {'snapshot_id': 'fixture:63', 'revision': 7, 'native_revision': 6},
            'caller_return_rva': 0x2639CA4,
            'compiled_receiver_token': 0x100040,
            'caller_context_token': 0x200050,
            'scope_kind_u16': 27,
            'scope_payload_u64': 0xFE000007,
            'scope_seed_i32': 0,
            'evaluation_flag_u8': 255,
        }
        original = deepcopy(supplied)
        for seed in (0, 1, 255, 256, 0x12345678, 0x7FFFFFFF):
            trial = deepcopy(supplied)
            trial['scope_seed_i32'] = seed
            row = leaf.project_army_compiled_effect_context_12004(trial)
            self.assertEqual(row['status'], 'available')
            self.assertEqual([row['conditional_rng_seed_u32'],
                              row['conditional_rng_counter_u32']], source_nonnegative_pair(seed))
            self.assertEqual(row['conditional_dispatch_context']['flag_u8'], 255)
            self.assertEqual(row['conditional_scope']['scope_payload_u64'], 0xFE000007)
            self.assertFalse(row['actual_invocation_observed'])
            self.assertFalse(row['history_append_observed'])
            self.assertFalse(row['callee_effects_ready'])
        self.assertEqual(supplied, original)
        negative = deepcopy(supplied)
        negative['scope_seed_i32'] = -1
        negative['caller_return_rva'] = 0x24DD7B6
        row = leaf.project_army_compiled_effect_context_12004(negative)
        self.assertEqual(row['status'], 'partial')
        self.assertIsNone(row['conditional_rng_seed_u32'])
        self.assertEqual(row['route']['definition_member_offset'], 0x230)
        self.assertIn('actual_393ee20_fallback_seed', row['missing_inputs'])
        for key in ('scope_kind_u16', 'scope_payload_u64', 'scope_seed_i32',
                    'evaluation_flag_u8', 'compiled_receiver_token', 'caller_context_token'):
            trial = deepcopy(supplied)
            del trial[key]
            row = leaf.project_army_compiled_effect_context_12004(trial)
            self.assertEqual(row['status'], 'partial')
            self.assertIn(key, row['missing_inputs'])
        for key, invalid in (('scope_seed_i32', True), ('scope_seed_i32', 0x80000000),
                             ('scope_payload_u64', 0xFFFFFFFF), ('scope_kind_u16', 9),
                             ('caller_return_rva', 0x2CC93CC)):
            trial = deepcopy(supplied)
            trial[key] = invalid
            self.assertFalse(leaf.project_army_compiled_effect_context_12004(trial)['argument_projection_ready'])
        historical = deepcopy(supplied)
        historical['input_basis'] = 'native_natural_compiled_effect_entry'
        self.assertEqual(leaf.project_army_compiled_effect_context_12004(historical)['status'], 'unavailable')
        self.assertEqual(leaf.project_army_compiled_effect_context_12004(None)['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
