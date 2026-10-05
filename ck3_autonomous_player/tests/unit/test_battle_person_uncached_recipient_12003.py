from copy import deepcopy
import unittest

from xar_autoplayer.bridge.battle_person_uncached_recipient_contract import normalize_uncached_recipient_inputs
from xar_autoplayer.simulation.battle_person_uncached_recipient_12003 import (
    compute_uncached_recipient_from_native_inputs_12003,
)


def family(first=(), second=()):
    def vector(rows):
        return {'count': len(rows), 'records': [
            {'native_index': i, 'marker_u8': marker, 'key_object': key,
             'key_id_i32': key_id, 'value_q64': value}
            for i, (key, key_id, value, marker) in enumerate(rows)]}
    return {'ready': True, 'first': vector(first), 'second': vector(second)}


def raw():
    return {
        'status': 'available', 'ready': True, 'character_id': 29829,
        'carrier_present': False, 'associated_full_id': 0xAB000001,
        'associated_resolved_full_id': 0xAB000001, 'associated_used_fallback': False,
        'associated_cache_440': 0,
        'seed_receiver': {name: None for name in (
            'first_full_id', 'first_resolved_full_id', 'first_used_fallback',
            'second_full_id', 'second_resolved_full_id', 'second_used_fallback', 'definition_object')},
        'seed_family': family(), 'fallback_key_object': 0x8888, 'fallback_key_id_i32': -1,
        'active_objects': {'count': 0, 'entries': []},
        'active_context': {'count': 0, 'entries': []},
        'removed_objects': {'count': 0, 'entries': []},
        'cap_i32': 2, 'active_flag4_multiplier_q64': 150000,
        'active_other_multiplier_q64': 50000, 'seed_boost_multiplier_q64': 25000,
        'positive_fallback_object': 0x9988, 'negative_fallback_object': 0x9977,
        'positive_fallback_magic_u32': 0, 'negative_fallback_magic_u32': 0,
        'downstream_inputs': {
            'trait_ids': {'count': 1, 'values_u32': [17]},
            'membership_ids': {'count': 0, 'values_u64': []},
            'membership_header_guard_raw': -2,
            'aggregate_properties': {'count': 1, 'keys_u16': [0x25D], 'values_q64': [10000]},
            'aggregate_context_selection': 'owned_model_10', 'aggregate_context_guard_raw': None,
            'member_multiplier_q64': None, 'clamp_lower_q64': -(1 << 63), 'clamp_upper_q64': (1 << 63) - 1,
        }, 'calculated_recipient_q64': 10000, 'reason': None,
    }


class UncachedRecipientTest(unittest.TestCase):
    def test_source_reducer_and_same_query_contract(self):
        checks = 0
        def eq(a, b):
            nonlocal checks
            self.assertEqual(a, b)
            checks += 1
        packet = raw()
        packet['seed_family'] = family([(0x1010, 17, 100000, 2)])
        packet['active_objects'] = {'count': 1, 'entries': [{
            'native_index': 0, 'object': 0x7777, 'magic_u32': 0x4744624F,
            'intrinsic_family': family([(0x1010, 17, 200000, 2)])}]}
        # First full-pointer context match applies; the later row is ignored.
        packet['active_context'] = {'count': 2, 'entries': [
            {'native_index': 0, 'object': 0x7777, 'flag_u8': 4},
            {'native_index': 1, 'object': 0x7777, 'flag_u8': 1}]}
        packet['removed_objects'] = {'count': 1, 'entries': [{
            'native_index': 0, 'object': 0x6666, 'magic_u32': 0x4744624F,
            'intrinsic_family': family([(0x1010, 17, 300000, 2)])}]}
        packet['downstream_inputs']['membership_ids'] = {'count': 1, 'values_u64': [0x7777]}
        packet['downstream_inputs']['member_multiplier_q64'] = 200000
        packet['calculated_recipient_q64'] = 660000
        result = compute_uncached_recipient_from_native_inputs_12003(packet)
        eq(result.value_q64, 660000)
        eq(result.calculation_ready, True)
        eq([r['accepted'] for r in result.ledger['reducer_trace']], [True, True, False])
        eq(result.ledger['kind1_records'][0]['value_q64'], 325000)
        eq(result.ledger['derived_temporary_map458'][0]['value_u64'], 0x7777)
        eq(normalize_uncached_recipient_inputs(packet)['calculated_recipient_q64'], 660000)
        eq(result.native_write_performed, False)
        eq(result.stage_start_baseline_supplied, False)
        eq(result.actual_entry_effectiveness_ready, False)

        switched = raw()
        switched['seed_family'] = family([(0x1010, 17, 100000, 2)])
        switched['removed_objects'] = {'count': 1, 'entries': [{
            'native_index': 0, 'object': 0x6666, 'magic_u32': 0x4744624F,
            'intrinsic_family': family(second=[(0x1010, 17, 400000, 2)])}]}
        result = compute_uncached_recipient_from_native_inputs_12003(switched)
        eq(result.value_q64, -390000)
        eq(len(result.ledger['kind1_records']), 0)
        eq(result.ledger['kind2_records'][0]['priority_u8'], 2)

        tied = raw()
        tied['cap_i32'], tied['seed_boost_multiplier_q64'] = 1, 0
        tied['seed_family'] = family([(0x1010, 17, 100000, 2), (0x2020, 18, 100000, 2)])
        tied['downstream_inputs']['trait_ids'] = {'count': None, 'values_u32': None}
        tied['downstream_inputs']['membership_ids'] = {'count': None, 'values_u64': None}
        tied['downstream_inputs']['membership_header_guard_raw'] = None
        tied['positive_fallback_object'] = tied['positive_fallback_magic_u32'] = None
        result = compute_uncached_recipient_from_native_inputs_12003(tied)
        eq(result.value_q64, 10000)
        eq(result.ledger['reducer_trace'][1]['branch'], 'invalidate_equal_group')
        eq(len(result.ledger['kind1_records']), 0)
        eq(len(result.ledger['seed_records']), 2)

        fallback = raw()
        fallback['seed_boost_multiplier_q64'] = 0
        fallback['seed_family'] = family([(None, None, 120000, 0)])
        fallback['downstream_inputs']['trait_ids'] = {'count': 1, 'values_u32': [0xFFFFFFFF]}
        result = compute_uncached_recipient_from_native_inputs_12003(fallback)
        eq(result.value_q64, 130000)
        eq(result.ledger['kind1_records'][0]['key_object'], 0x8888)
        eq(result.ledger['kind1_records'][0]['key_id_i32'], -1)

        large = raw()
        large['cap_i32'], large['seed_boost_multiplier_q64'] = 100, 0
        large['seed_family'] = family([(0x1000 + i * 16, i - 20, 100000 + i, 2)
                                       for i in reversed(range(40))])
        large['downstream_inputs']['trait_ids'] = {'count': 40, 'values_u32': [(i - 20) & 0xFFFFFFFF for i in range(40)]}
        result = compute_uncached_recipient_from_native_inputs_12003(large)
        eq(result.value_q64, 4010780)
        eq(result.calculation_ready, True)
        eq([r['key_object'] for r in result.ledger['reducer_trace']], [0x1000 + i * 16 for i in range(40)])

        equal_vectors = raw()
        equal_vectors['seed_boost_multiplier_q64'] = 0
        equal_vectors['seed_family'] = family([(0x1010, 17, 100000, 2)], [(0x1010, 17, 100000, 2)])
        result = compute_uncached_recipient_from_native_inputs_12003(equal_vectors)
        eq(result.value_q64, 110000)
        eq(result.ledger['kind1_records'][0]['kind'], 1)

        maximum_operand = raw()
        maximum_operand['seed_boost_multiplier_q64'] = 100003
        maximum_operand['seed_family'] = family([(0x1010, 17, 4611686018427387921, 2)])
        maximum_operand['calculated_recipient_q64'] = -9223233686274212953
        result = compute_uncached_recipient_from_native_inputs_12003(maximum_operand)
        eq(result.value_q64, -9223233686274212953)
        eq(result.ledger['kind1_records'][0]['value_q64'], -9223233686274222953)
        eq(normalize_uncached_recipient_inputs(maximum_operand)['calculated_recipient_q64'], -9223233686274212953)

        partial = deepcopy(packet)
        partial['downstream_inputs']['membership_header_guard_raw'] = 0
        partial.update(status='partial', ready=False, reason='actual inline default uninitialized', calculated_recipient_q64=None)
        result = compute_uncached_recipient_from_native_inputs_12003(partial)
        eq(result.calculation_ready, False)
        eq(result.value_q64, None)
        eq(normalize_uncached_recipient_inputs(partial)['downstream_inputs']['membership_ids']['values_u64'], [0x7777])
        empty = raw()
        empty['cap_i32'] = empty['seed_boost_multiplier_q64'] = None
        empty['downstream_inputs']['trait_ids'] = {'count': None, 'values_u32': None}
        empty['downstream_inputs']['membership_ids'] = {'count': None, 'values_u64': None}
        empty['downstream_inputs']['membership_header_guard_raw'] = None
        eq(compute_uncached_recipient_from_native_inputs_12003(empty).value_q64, 10000)
        eq(normalize_uncached_recipient_inputs(empty)['ready'], True)
        skipped = raw()
        skipped.update(status='not_applicable', associated_cache_440=1, calculated_recipient_q64=None)
        eq(normalize_uncached_recipient_inputs(skipped)['status'], 'not_applicable')
        print('uncached recipient new compound checks:', checks)
