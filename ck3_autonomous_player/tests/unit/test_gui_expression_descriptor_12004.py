"""Source-qualified descriptor scalars retain unknown business identity."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[2]
CONTRACT = BASE / 'src/xar_autoplayer/bridge/gui_callback_binding_12004_contract.py'
spec = importlib.util.spec_from_file_location('expression_contract_12004', CONTRACT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    descriptor = {
        'chain_count_24_raw': 1, 'final_type_id_30': 9, 'final_kind_34_raw': 4,
        'final_target_38_rva': 0x10000, 'final_user_data_40_present': False,
        'receiver_type_id_48': 0xFFFFFFFF, 'receiver_flag_4c_raw': 255,
        'chain_calls': [{'index': 0, 'type_id_0': 7, 'kind_4_raw': 2,
                         'native_target_8_rva': 0x20000, 'user_data_10_present': True}],
    }
    binding = {'button_base_slot13': True, 'group': 'fallback', 'callbacks': [{
        'index': 0, 'callback_vtable_rva': 0x40000, 'callback_slot2_rva': 0x3AA30E0,
        'indirect_target_3aa30e0': {'native_target_8_rva': 0x3A9F960,
                                  'receiver_f0_present': True,
                                  'expression_3a9f960': descriptor},
    }]}
    return {'callback_binding_source_12004': dict(module.SOURCE_EXPRESSION_12004),
            'truncated': False, 'root_available': True,
            'widgets': [{'standard_click_binding_12004': binding}]}, {'widgets': [{'vtable_rva': 0x50000}]}


def descriptor(raw):
    return raw['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0']['expression_3a9f960']


class ExpressionDescriptor12004Tests(unittest.TestCase):
    def test_source_scalar_pair_preserves_order_and_no_action_credit(self):
        raw, projected = sample()
        result = module.normalize_callback_binding_rows_12004(raw, projected)
        self.assertEqual(result['widgets'][0]['standard_click_binding_12004'], raw['widgets'][0]['standard_click_binding_12004'])
        self.assertIs(result['callback_method_name_available'], False)
        self.assertIs(result['click_action_available'], False)

    def test_source_profile_hash_mismatch_rejected(self):
        raw, projected = sample()
        raw['callback_binding_source_12004']['expression_layout_bytes_sha256'] = '0' * 64
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)

    def test_missing_descriptor_cannot_borrow_new_profile(self):
        raw, projected = sample()
        del raw['widgets'][0]['standard_click_binding_12004']['callbacks'][0]['indirect_target_3aa30e0']['expression_3a9f960']
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)

    def test_old_profile_cannot_borrow_descriptor_layout(self):
        raw, projected = sample(); raw['callback_binding_source_12004'] = dict(module.SOURCE_INDIRECT_12004)
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)

    def test_typed_integer_and_chain_ordinal_rejected(self):
        for field, value in [('receiver_type_id_48', True), ('receiver_flag_4c_raw', 256), ('chain_count_24_raw', True)]:
            with self.subTest(field=field):
                raw, projected = sample(); descriptor(raw)[field] = value
                with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)
        raw, projected = sample(); descriptor(raw)['chain_calls'][0]['index'] = True
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)

    def test_chain_count_mismatch_and_module_escape_rejected(self):
        raw, projected = sample(); descriptor(raw)['chain_count_24_raw'] = 0
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)
        raw, projected = sample(); descriptor(raw)['chain_calls'][0]['native_target_8_rva'] = module.IMAGE_BYTES_12004
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)

    def test_noncallable_kind_has_no_invented_function(self):
        raw, projected = sample(); descriptor(raw)['final_kind_34_raw'] = 2
        with self.assertRaises(ValueError): module.normalize_callback_binding_rows_12004(raw, projected)
        descriptor(raw)['final_target_38_rva'] = 0
        result = module.normalize_callback_binding_rows_12004(raw, projected)
        self.assertIs(result['click_action_available'], False)

    def test_native_code_pins_equal_lossless_source_evidence(self):
        evidence = json.loads((BASE.parent / 'docs/ck3-native-ai/evidence/military-refill-expression-call-chain-12004.json').read_text(encoding='utf-8'))
        header = (BASE / 'native_bridge/include/xar_bridge/ck3_12004_gui_expression_descriptor.hpp').read_text(encoding='utf-8')
        joined = []
        for function in evidence['functions']:
            key = function['rva']
            match = re.search(r'kGuiExpression' + key + r'Bytes12004V1\{\{(.*?)\}\};', header, re.S)
            self.assertIsNotNone(match)
            actual = bytes(int(n, 16) for n in re.findall(r'0x([0-9A-F]{2})', match.group(1)))
            self.assertEqual(actual.hex(), function['hex'])
            self.assertEqual(len(actual), function['bytes'])
            self.assertEqual(hashlib.sha256(actual).hexdigest(), function['sha256'])
            joined.append(actual)
        self.assertEqual(hashlib.sha256(b''.join(joined)).hexdigest(), module.SOURCE_EXPRESSION_12004['expression_layout_bytes_sha256'])


if __name__ == '__main__': unittest.main()
