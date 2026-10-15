"""Narrow offline contract examples; these are synthetic DTOs, not live packets."""
from __future__ import annotations

from copy import deepcopy
import importlib
import os
from pathlib import Path
import sys
import types
import unittest

sys.dont_write_bytecode = True
SOURCE_ROOT = Path(os.environ.get('XAR_COMMANDER_CAPACITY_SOURCE_ROOT', Path(__file__).resolve().parents[2])).resolve()
ROOT = Path(os.environ.get('XAR_COMMANDER_CAPACITY_FALLBACK_ROOT', SOURCE_ROOT)).resolve()
PROJECTION = SOURCE_ROOT / 'ck3_autonomous_player/src/xar_autoplayer'
for name, paths in (
    ('xar_autoplayer', [PROJECTION, ROOT / 'ck3_autonomous_player/src/xar_autoplayer']),
    ('xar_autoplayer.bridge', [PROJECTION / 'bridge', ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge']),
):
    package = types.ModuleType(name)
    package.__path__ = [str(path) for path in paths]
    sys.modules[name] = package

capacity = importlib.import_module('xar_autoplayer.bridge.army_commander_conditional_capacity')
contract = importlib.import_module('xar_autoplayer.bridge.army_commander_candidates')
proposal = importlib.import_module('xar_autoplayer.commander_quality_formal_proposal_v1')
KEY = capacity.CONDITIONAL_SUPPLY_CAPACITY_V1_KEY


def _leaf(full='20000000', additive='5000000', multiplier='25000', result='31250000'):
    return {
        'schema': capacity.CONDITIONAL_SUPPLY_CAPACITY_V1_SCHEMA,
        'status': 'available', 'source_character_id': 30001, 'scale': 100000,
        'loaded_full_raw': full, 'additive_modifier_raw': additive,
        'multiplicative_modifier_raw': multiplier, 'conditional_capacity_raw': result,
        'assignment_applied': False,
        'assumption': 'candidate_aggregate_unchanged_after_assignment',
        'unavailable_reason': None,
        'provenance': dict(capacity.CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE),
    }


def _packet(schema='ck3_12004_army_commander_candidates_v1'):
    return {
        'schema': schema, 'status': 'available', 'snapshot_revision': 11,
        'date_raw': 53288448, 'army_id': 83886367, 'native_carmy_id': 50331794,
        'owner_character_id': 29829, 'eligibility_mode': 1,
        'collection_filter_now': False, 'collection_allow_guests': True,
        'current_commander': {'status': 'absent', 'character_id': None, 'unavailable_reason': None},
        'candidate_collection_complete': True, 'candidate_source_count': 1,
        'candidates': [{
            'character_id': 30001, 'available': True,
            'final_eligibility_observable': True, 'can_assign': False,
            'quality_observable': True, 'native_ai_base_quality': 25,
            'generic_advantage_points': 3, 'unavailable_reason': None,
        }],
        'unavailable_reason': None,
    }


def _normalize(packet):
    return contract.normalize_army_commander_candidates_v1(
        packet, expected_army_id=83886367,
        expected_snapshot_revision=11, expected_date_raw=53288448,
    )


class ConditionalCapacityTests(unittest.TestCase):
    def test_legacy_absence_null_and_build_gate(self):
        for schema in ('ck3_12003_army_commander_candidates_v1', 'ck3_12004_army_commander_candidates_v1'):
            with self.subTest(schema=schema):
                packet = _packet(schema)
                self.assertNotIn(KEY, _normalize(packet)['candidates'][0])
                packet['candidates'][0][KEY] = None
                self.assertIsNone(_normalize(packet)['candidates'][0][KEY])
        legacy = _packet('ck3_12003_army_commander_candidates_v1')
        legacy['candidates'][0][KEY] = _leaf()
        with self.assertRaisesRegex(ValueError, 'actual .4'):
            _normalize(legacy)

    def test_native_arithmetic_examples_include_slow_path_and_wrap(self):
        # Literal expectations cover native truncation, the fast/slow seam,
        # unbounded signed result and individual signed64 arithmetic wraps.
        cases = (
            ('20000000', '5000000', '25000', '31250000'),
            ('10000000', '-12000000', '0', '-2000000'),
            ('10000000', '0', '-100000', '0'),
            ('1', '-2', '-50000', '0'),
            ('3037000499', '0', '3036900499', '92233720309262'),
            ('3037000500', '0', '3036900500', '92233720370002'),
            ('9223372036854775807', '1', '0', '-9223372036854775808'),
            ('100000', '0', '9223372036854775807', '-9223372036854675809'),
            ('9223372036854775807', '0', '9223372036854675807', '-9223372036854775808'),
        )
        for values in cases:
            with self.subTest(values=values):
                packet = _packet()
                original = _leaf(*values)
                packet['candidates'][0][KEY] = original
                self.assertEqual(_normalize(packet)['candidates'][0][KEY], original)

    def test_unavailable_partial_inputs_and_independent_legality(self):
        packet = _packet()
        packet['candidates'][0][KEY] = _leaf()
        normalized = _normalize(packet)
        self.assertFalse(normalized['candidates'][0]['can_assign'])
        self.assertEqual(normalized['candidates'][0][KEY]['status'], 'available')
        frame = {'snapshot_id': 'synthetic:11', 'revision': 4, 'native_revision': 11, 'date_raw': 53288448}
        baseline = proposal.propose_commander_quality_v1(_normalize(_packet()), snapshot=frame, query_sequence=7)
        observed = proposal.propose_commander_quality_v1(normalized, snapshot=frame, query_sequence=7)
        self.assertEqual(observed, baseline)
        self.assertEqual(observed['status'], 'no_eligible_candidate')
        unavailable = _leaf()
        unavailable.update(status='unavailable', additive_modifier_raw=None,
                           conditional_capacity_raw=None,
                           unavailable_reason='candidate_aggregate_unavailable')
        packet['candidates'][0][KEY] = unavailable
        self.assertEqual(_normalize(packet)['candidates'][0][KEY], unavailable)

    def test_wrong_identity_derived_value_and_raw_shape_are_rejected(self):
        self.assertEqual(capacity.CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE["capacity_rva"], 0x2C53BF0)
        self.assertIs(type(capacity.CONDITIONAL_SUPPLY_CAPACITY_V1_PROVENANCE["loaded_full_rva"]), int)
        self.assertEqual(capacity.parse_conditional_capacity_raw64("-9223372036854775808"), -(1 << 63))
        self.assertIsNone(capacity.parse_conditional_capacity_raw64(None))
        for malformed in (True, 1, "9223372036854775808", "01", "-0"):
            with self.subTest(raw_parser=malformed):
                with self.assertRaises(ValueError):
                    capacity.parse_conditional_capacity_raw64(malformed)
        variants = []
        wrong_id = _leaf(); wrong_id['source_character_id'] = 30002
        variants.append(('source candidate', wrong_id))
        wrong_value = _leaf(); wrong_value['conditional_capacity_raw'] = '31250001'
        variants.append(('derived value', wrong_value))
        bool_raw = _leaf(); bool_raw['loaded_full_raw'] = True
        variants.append(('decimal string', bool_raw))
        integer_raw = _leaf(); integer_raw['loaded_full_raw'] = 20000000
        variants.append(('decimal string', integer_raw))
        unavailable_value = _leaf(); unavailable_value.update(status='unavailable', unavailable_reason='failed')
        variants.append(('null derived', unavailable_value))
        wrong_source = _leaf(); wrong_source['provenance']['capacity_rva'] = '0x2C53C10'
        variants.append(('provenance', wrong_source))
        missing = _leaf(); del missing['assignment_applied']
        variants.append(('fields', missing))
        for message, leaf in variants:
            with self.subTest(message=message):
                packet = _packet()
                packet['candidates'][0][KEY] = deepcopy(leaf)
                with self.assertRaisesRegex(ValueError, message):
                    _normalize(packet)


if __name__ == '__main__':
    unittest.main(verbosity=2)
