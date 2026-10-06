from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_admission_refresh_source_builder import (
    post_admission_refresh_source, missing_demanded40_source,
    zero_count_unused_data_source, negative_count_diagnostic_source,
)
from test_scoped_ordered_refill_service import MemoryRoute, row as source_row


class CurrentPostAdmissionRefreshService12003Tests(unittest.TestCase):
    def test_real_service_independent_numeric_frontier_raw_repeats_zero_and_partial(self):
        outputs = {}

        def query(name, leaf):
            source = source_row()
            source['current_post_admission_refresh_inputs_v1'] = leaf
            before = deepcopy(source)
            service = MemoryRoute(source)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(source, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['army_strengths'][0]['current_soldiers'], 160)
            self.assertEqual(returned['army_strengths'][0]['current_supply_change_monthly_raw'], 700000)
            self.assertEqual(returned['source']['revision'], 42)
            self.assertEqual(returned['source']['native_revision'], 7)
            observed = returned['army_strengths'][0]['current_post_admission_refresh_inputs_v1']
            self.assertEqual(observed, leaf)
            projected = returned['current_post_admission_refresh_inputs_v1'][0]['projection']
            self.assertEqual(projected['observed_current_post_admission_refresh_inputs'], leaf)
            self.assertEqual(projected['projection_stage'], 'post24df4c3_pre24df4c7')
            self.assertEqual(projected['native_calls_executed'], 0)
            self.assertEqual(projected['native_writes_executed'], 0)
            for flag in ('actual_refresh_execution_ready', 'actual_next_occurrence_ready',
                         'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
                         'actual_post_stage_observed', 'future_tick_ready'):
                self.assertFalse(projected[flag])
            for army in projected['occurrences']:
                self.assertEqual(army['actual_army_24_raw_i32'], 777)
                self.assertEqual(army['actual_army_28_raw_i64'], -888)
                self.assertEqual([army[f'actual_army_{offset}_raw_u8'] for offset in ('20', '21', '30', '31')],
                                 [2, 3, 4, 5])
            outputs[name] = returned
            return projected

        complete = query('nonempty-physical-repeats-fallback-and-wrap', post_admission_refresh_source())
        self.assertTrue(complete['conditional_numeric_frontier_ready'])
        self.assertTrue(complete['numeric_24_inputs_ready'])
        self.assertTrue(complete['numeric_28_inputs_ready'])
        self.assertEqual(complete['last_verified_stage'], 'post24df4c3_pre24df4c7')
        self.assertEqual([army['raw_full_id_u32'] for army in complete['occurrences']],
                         [11, 11, 13, 0xFE00000E])
        self.assertEqual([army['prospective_army_24_i32'] for army in complete['occurrences']], [4, 4, 0, 0])
        self.assertEqual([army['prospective_army_28_i64'] for army in complete['occurrences']], [10, 10, 0, -7])
        first = complete['occurrences'][0]
        arrgs = first['arrg_occurrences']
        self.assertEqual([arrg['raw_full_id_u32'] for arrg in arrgs], [100, 100, 0xFE000066, 103, 104])
        self.assertEqual([arrg['identity_valid'] for arrg in arrgs], [True, True, True, False, False])
        self.assertEqual(arrgs[0]['arrg_resolution']['object_identity'], arrgs[1]['arrg_resolution']['object_identity'])
        self.assertEqual([arrg['numeric_24_running_after_i32'] for arrg in arrgs], [2147483640, -16, 4, 4, 4])
        self.assertEqual([arrg['numeric_28_running_after_i64'] for arrg in arrgs],
                         [9223372036854775803, -10, 10, 10, 10])
        self.assertEqual(arrgs[2]['arrg_resolution']['selection'], 'native_fallback')
        self.assertEqual(arrgs[2]['arrg_resolution']['selected_full_id_u32'], 102)
        self.assertIsNone(arrgs[3]['arrg_resolution']['selected_full_id_u32'])
        self.assertTrue(arrgs[3]['ready'])
        self.assertIsNone(arrgs[3]['current_38_raw_i32'])
        self.assertIsNone(arrgs[4]['value_40_raw_i64'])

        partial = query('missing-demanded40-preserves24', missing_demanded40_source())
        self.assertFalse(partial['conditional_numeric_frontier_ready'])
        self.assertTrue(partial['numeric_24_inputs_ready'])
        self.assertFalse(partial['numeric_28_inputs_ready'])
        affected = partial['occurrences'][0]
        self.assertTrue(affected['arrg_rows_ready'])
        self.assertEqual(affected['prospective_army_24_i32'], 4)
        self.assertIsNone(affected['prospective_army_28_i64'])
        self.assertEqual(affected['numeric_28_known_prefix_i64'], 0)
        self.assertEqual(affected['numeric_28_known_prefix_occurrence_count'], 0)
        self.assertIsNone(affected['arrg_occurrences'][1]['numeric_28_running_after_i64'])
        self.assertEqual(affected['arrg_occurrences'][1]['numeric_28_contribution_i64'], 9223372036854775803)
        self.assertEqual(affected['last_verified_stage'], 'post24df452_pre24df455')
        self.assertEqual([army['prospective_army_28_i64'] for army in partial['occurrences'][1:]], [10, 0, -7])

        empty = query('count0-unused-data-genuine-zero', zero_count_unused_data_source())
        self.assertTrue(empty['conditional_numeric_frontier_ready'])
        self.assertEqual([army['prospective_army_24_i32'] for army in empty['occurrences']], [0] * 4)
        self.assertEqual([army['prospective_army_28_i64'] for army in empty['occurrences']], [0] * 4)
        for army in empty['occurrences']:
            self.assertIsNone(army['original_arrg_references']['data_identity'])
            self.assertIsNone(army['original_arrg_references']['data_present'])
            self.assertEqual(army['arrg_occurrences'], [])

        negative = query('negative-count-diagnostic-not-empty', negative_count_diagnostic_source())
        self.assertFalse(negative['conditional_numeric_frontier_ready'])
        affected = negative['occurrences'][2]
        self.assertEqual(affected['original_arrg_references']['count_raw_i32'], -1)
        self.assertFalse(affected['numeric_24_inputs_ready'])
        self.assertFalse(affected['numeric_28_inputs_ready'])
        self.assertIsNone(affected['prospective_army_24_i32'])
        self.assertIsNone(affected['prospective_army_28_i64'])
        self.assertIn('negative_original_arrg_count_not_modeled_as_empty', affected['missing_inputs'])
        self.assertEqual([negative['occurrences'][index]['prospective_army_24_i32'] for index in (0, 1, 3)],
                         [4, 4, 0])
        self.assertEqual([negative['occurrences'][index]['prospective_army_28_i64'] for index in (0, 1, 3)],
                         [10, 10, -7])
        output = os.environ.get('XAR_POST_ADMISSION_REFRESH_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
