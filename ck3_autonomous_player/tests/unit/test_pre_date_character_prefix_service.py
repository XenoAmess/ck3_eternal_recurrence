from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pre_date_character_prefix_fixture import source_package, unavailable_availability_package, unavailable_owner_package
from pre_date_dated_append_fixture import id_list
from test_scoped_ordered_refill_service import MemoryRoute
from test_current_daily_assault_table_service import source_row
from test_daily_assault_placement_service import placement_source


class PreDateCharacterPrefixServiceTests(unittest.TestCase):
    def test_nonempty_prefix_false_true_false_failure_requests_and_admission_entrance(self):
        """FIRST source compound only; native whole-wire is a separate consumer."""
        outputs = {}
        def query(label, package):
            row = source_row(placement_source())
            row['current_pre_date_character_prefix_inputs_v1'] = deepcopy(package['prefix'])
            row['current_pre_date_pending_update_inputs_v1'] = deepcopy(package['pending'])
            row['current_daily_assault_roster_admission_v1'] = deepcopy(package['admission'])
            before = deepcopy(row)
            service = MemoryRoute(row)
            returned = service.query_army_strengths([row['army_id']], expected_revision=42)
            self.assertEqual(row, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['source']['native_revision'], 7)
            observed = returned['army_strengths'][0]
            self.assertEqual(observed['current_pre_date_character_prefix_inputs_v1'], package['prefix'])
            projection = observed['same_input_conditional_current_pre_date_character_prefix_v1']
            self.assertEqual(returned['current_pre_date_character_prefix_inputs_v1'][0]['projection'], projection)
            self.assertFalse(projection['actual_next_callback_ready'])
            self.assertFalse(projection['full_daily_assault_ready'])
            self.assertFalse(projection['physical_growth_replayed'])
            self.assertEqual((projection['native_calls_executed'], projection['native_writes_executed']), (0, 0))
            outputs[label] = returned
            return returned, projection

        returned, complete = query('nonempty-known-skip-sentinel-fallback-repeat-F-T-F', source_package())
        self.assertTrue(complete['conditional_prefix_inputs_ready'])
        self.assertTrue(complete['conditional_append_requests_ready'])
        self.assertTrue(complete['current_dispatch_join_ready'])
        self.assertEqual(complete['append_request_full_ids_u32'], [13, 14, 13, 16])
        self.assertEqual(complete['logical_80_full_ids_u32'], [7, 7, 13, 14, 13, 16])
        self.assertEqual(complete['logical_80_count_i32'], 6)
        self.assertEqual(complete['admission_entrance_occurrence_indices'], [1, 2, 3, 4, 5, 6])
        self.assertEqual([r['branch'] for r in complete['occurrences']],
                         ['earlier_known_skip', 'character_sentinel', 'character_tag_failure',
                          'availability_failure', 'character_prefix_pass', 'character_tag_failure', 'character_state_failure'])
        self.assertEqual(complete['occurrences'][2]['demanded_predicates'], [])
        self.assertEqual(complete['occurrences'][3]['demanded_predicates'], ['membership', 'basic_rule', 'availability'])
        self.assertEqual(complete['occurrences'][4]['demanded_fields'][-1], 'character_state_1c8_present')
        self.assertTrue(returned['current_daily_assault_roster_admission_inputs_v1'][0]['projection']['conditional_admission_ready'])
        self.assertTrue(returned['army_strengths'][0]['same_input_conditional_current_pre_date_pending_update_v1']['pending_counts_and_removal_requests_ready'])

        package = source_package(); package['prefix']['initial_80'] = id_list(None, count=2)
        _, p = query('requests-independent-of-initial80', package)
        self.assertTrue(p['conditional_append_requests_ready'])
        self.assertFalse(p['logical_80_result_ready'])
        self.assertEqual(p['append_request_full_ids_u32'], complete['append_request_full_ids_u32'])
        _, p = query('demanded-native-verdict-partial-with-independent-later', unavailable_availability_package())
        self.assertFalse(p['conditional_append_requests_ready'])
        self.assertEqual([r['source_native_index'] for r in p['request_prefix']], [2])
        self.assertEqual([r['source_native_index'] for r in p['independently_derived_requests']], [2, 5, 6])
        self.assertEqual(p['occurrences'][3]['unavailable_reason'], 'availability_native_verdict_unavailable')
        _, p = query('owner-load-required-before-character-tag', unavailable_owner_package())
        self.assertFalse(p['occurrences'][2]['ready'])
        self.assertEqual(p['occurrences'][2]['unavailable_reason'], 'unit_owner_174_raw_u32_unavailable')
        self.assertTrue(p['occurrences'][5]['ready'])
        package = source_package()
        for row in package['prefix']['occurrences']:
            if row['earlier_skip'] is False:
                row.update(earlier_skip=None, earlier_skip_source='unavailable')
        package['pending'] = None
        _, p = query('explicit-current-prefix-independent-of-earlier-unknown', package)
        self.assertTrue(p['conditional_append_requests_ready'])
        self.assertFalse(p['current_dispatch_join_ready'])
        self.assertEqual(p['append_request_full_ids_u32'], complete['append_request_full_ids_u32'])
        output = os.environ.get('XAR_PRE_DATE_CHARACTER_PREFIX_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
