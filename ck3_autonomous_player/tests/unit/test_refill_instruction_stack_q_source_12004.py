"""New q-load seam counterexamples only; constructed wire is not live evidence."""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import unittest

base = Path(__file__).resolve().parents[2]
candidate = Path(os.environ.get('XAR_Q_SEAM_SOURCE_ROOT', base))
existing = Path(os.environ.get('XAR_Q_SEAM_EXISTING_ROOT', base))
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
m = load('new_q_seam', candidate/'src/xar_autoplayer/bridge/army_instruction_local_refill_add_12004.py')
# Reuse the old fixture constructor without executing its test suite.
fixture = load('q_fixture_only', existing/'tests/unit/test_army_instruction_local_refill_add_12004.py')
fixture.m = m

def sample(before=80, q=10, index=5):
    rows, binding = fixture.sample(before, q)
    rows[0]['schema'] = 'xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
    window = bytearray(28); struct.pack_into('<I', window, index*4, q)
    for hit in rows[1:3]:
        seven = bytearray.fromhex(hit['physical_seven_hex'])
        struct.pack_into('<i', seven, hit['physical_slot']*0x24+12, index)
        hit.update(q_index=index, physical_seven_hex=seven.hex(),
                   stack_q_source_complete=True, stack_q_window_28_hex=window.hex())
    return rows, binding

def consume(rows, binding):
    return m.normalize_instruction_local_refill_add_12004(fixture.wire(rows), binding)

class StackQSeamTests(unittest.TestCase):
    def test_q_index_is_independent_of_physical_slot_wrap_zero_negative(self):
        for before, q in [(0xFFFFFFFF,1),(80,0),(0,0xFFFFFFFF)]:
            with self.subTest(before=before,q=q):
                rows, binding = sample(before, q)
                item = consume(rows, binding)
                seam = item['instruction_stack_q_source_v1']
                self.assertEqual(item['physical_slot'],0)
                self.assertEqual(seam['q_index'],5)
                self.assertEqual(seam['stack_selected_u32'],q)
                self.assertEqual(item['after_current_u32'],(before+q)&0xFFFFFFFF)
                self.assertEqual(item['raw_sha256'],hashlib.sha256(fixture.wire(rows)).hexdigest())

    def test_wrong_stack_EDX_incomplete_boolean_or_bounded_window_rejected(self):
        edits = [lambda h:h.update(stack_q_window_28_hex='00'*28),
                 lambda h:h.update(stack_q_source_complete=False),
                 lambda h:h.update(stack_q_source_complete=1),
                 lambda h:h.update(stack_q_window_28_hex='00'*27),
                 lambda h:h.update(q_index=7),lambda h:h.update(q_index=True)]
        for i, edit in enumerate(edits):
            rows, binding = sample(); edit(rows[2])
            with self.subTest(case=i), self.assertRaises(ValueError): consume(rows,binding)

    def test_unselected_q_mutation_between_boundaries_rejected(self):
        rows, binding = sample()
        changed = bytearray.fromhex(rows[2]['stack_q_window_28_hex']); changed[0]=1
        rows[2]['stack_q_window_28_hex'] = changed.hex()
        with self.assertRaisesRegex(ValueError,'unchanged'): consume(rows,binding)

    def test_using_physical_slot_as_q_index_or_relabeling_v2_rejected(self):
        rows, binding = sample()
        wrong = bytearray(28); struct.pack_into('<I',wrong,0,10)
        for h in rows[1:3]: h['stack_q_window_28_hex']=wrong.hex()
        with self.assertRaisesRegex(ValueError,'EDX'): consume(rows,binding)
        rows, binding = fixture.sample()
        rows[0]['schema']='xar.ck3.refill_ADD_12004.hwprobe_raw.v3'
        with self.assertRaises(ValueError): consume(rows,binding)

    def test_new_q_seam_preserves_independent_item_not_natural_NET_or_toggle_credit(self):
        rows, binding = sample()
        net={'actual_ADD_observed':False,'raw_current_net':-80,
             'missing_inputs':['instruction_local_ADD_producer_not_published']}
        item=m.attach_instruction_local_refill_add_12004(net,fixture.wire(rows),binding)
        self.assertFalse(item['actual_ADD_observed'])
        self.assertFalse(item['instruction_and_NET_parent_join_ready'])
        self.assertEqual(item['raw_current_net'],-80)
        observed=item['instruction_local_ADD_v1']
        self.assertTrue(observed['actual_ADD_observed'])
        for key in ('natural_attribution_ready','full_window_coverage_ready',
                    'toggle_effect_proven','refill_business_qualification_granted'):
            self.assertIs(observed[key],False)
        self.assertIsNone(observed['native_core_token'])
        self.assertFalse(observed['instruction_stack_q_source_v1']['uncapped_request_observed'])
        self.assertFalse(observed['instruction_stack_q_source_v1']['individual_permission_branches_observed'])

if __name__=='__main__': unittest.main()
