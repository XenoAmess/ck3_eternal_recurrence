from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from daily_assault_roster_admission_fixture import (
    roster_admission_source, zero_roster_admission_source,
    fallback_war_metadata_unavailable_source, partial_pending_admission_source,
    matched_suppression_with_unread_tail_source, partial_raw_roster_source,
    reused_queue_pointer_metadata_unavailable_source,
)
from test_daily_assault_placement_service import placement_source
from test_current_daily_assault_table_service import source_row
from test_scoped_ordered_refill_service import MemoryRoute
from xar_autoplayer.simulation.army_daily_assault_roster_admission_12003 import (
    daily_assault_roster_admission_requests_12003,
)
from xar_autoplayer.simulation.army_daily_assault_placement_12003 import (
    CONDITIONAL_PLACEMENT_STAGE_12003, ExplicitDailyAssaultPlacementStage12003,
    project_daily_assault_placement_prefix_12003,
)


class DailyAssaultRosterAdmissionServiceTests(unittest.TestCase):
    def test_whole_raw_roster_current_admission_then_explicit_nonempty_placement(self) -> None:
        outputs = {}
        stage = ExplicitDailyAssaultPlacementStage12003(CONDITIONAL_PLACEMENT_STAGE_12003,
            {'scope': 'explicit held fixture pre-placement state', 'actual_next_callback_ready': False})

        def query(name, leaf):
            source = source_row(placement_source())
            if leaf is not None:
                source['current_daily_assault_roster_admission_v1'] = leaf
            before = deepcopy(source)
            service = MemoryRoute(source)
            returned = service.query_army_strengths([11], expected_revision=42)
            self.assertEqual(source, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['army_strengths'][0]['current_soldiers'], 160)
            self.assertEqual(returned['source']['native_revision'], 7)
            projection = returned['current_daily_assault_roster_admission_inputs_v1'][0]['projection']
            self.assertFalse(projection['actual_next_callback_ready'])
            self.assertFalse(projection['full_daily_assault_ready'])
            self.assertFalse(projection['earlier_dispatch_replayed'])
            self.assertEqual(projection['native_calls_executed'], 0)
            self.assertEqual(projection['native_writes_executed'], 0)
            outputs[name] = {'service': returned}
            return returned['army_strengths'][0], projection

        observed, complete = query('whole-original-roster-nonempty', roster_admission_source())
        self.assertTrue(complete['conditional_admission_ready'])
        self.assertEqual([r['raw_full_id_u32'] for r in complete['raw_roster_occurrences']],
                         [11, 11, 13, 0xFE00000E, 15])
        self.assertEqual(observed['current_daily_assault_roster_admission_v1']['occurrences'][3]
                         ['original_army_resolution']['selection'], 'native_fallback')
        self.assertFalse(complete['occurrences'][4]['gate']['verdict'])
        self.assertFalse(complete['occurrences'][4]['gate']['relation_lookup']['ready'])
        requests = daily_assault_roster_admission_requests_12003(complete)
        self.assertEqual([(r.siege_full_id_u32, r.army_full_id_u32, list(r.arrg_full_ids_u32)) for r in requests],
                         [(13, 11, [100, 100, 300]), (13, 11, [100, 100, 300]), (5, 13, [400]), (2, 14, [])])
        placed = project_daily_assault_placement_prefix_12003(
            observed['current_daily_assault_table_v1'], requests, input_stage=stage)
        self.assertTrue(placed['conditional_placement_ready'])
        self.assertEqual(placed['applied_request_count'], 4)
        self.assertEqual([g['physical_slot_i64'] for g in placed['projected_groups']], [0, 1, 2, 4, 7])
        self.assertEqual([g['siege_full_id_u32'] for g in placed['projected_groups']], [5, 13, 4, 1, 2])
        self.assertEqual(placed['projected_groups'][1]['army_full_ids_u32'], [11, 11])
        self.assertEqual(placed['projected_groups'][1]['arrg_full_ids_u32'], [100, 100, 300] * 2)
        self.assertEqual(placed['projected_groups'][0]['army_full_ids_u32'], [14, 13])
        self.assertEqual(placed['projected_groups'][0]['arrg_full_ids_u32'], [300, 400])
        self.assertEqual(placed['observed_current_table'], observed['current_daily_assault_table_v1'])
        self.assertFalse(placed['actual_next_callback_ready'])
        outputs['whole-original-roster-nonempty']['conditional_placement'] = placed

        _, optional = query('unused-fallback-war-fullid-unread', fallback_war_metadata_unavailable_source())
        self.assertTrue(optional['conditional_admission_ready'])
        self.assertEqual(optional['request_prefix'], complete['request_prefix'])
        _, reused = query('complete-reused-queue-independent-pointer-metadata', reused_queue_pointer_metadata_unavailable_source())
        self.assertTrue(reused['removal_queue_references_ready'])
        self.assertTrue(reused['conditional_admission_ready'])

        _, partial = query('partial-pending-preserves-army-and-prefix', partial_pending_admission_source())
        self.assertTrue(partial['raw_roster_references_ready'])
        self.assertFalse(partial['conditional_admission_ready'])
        self.assertTrue(partial['occurrences'][2]['army_append'])
        self.assertIsNone(partial['occurrences'][2]['arrg_append_full_ids_u32'])
        self.assertEqual([r['source_provenance']['original_roster_native_index'] for r in partial['request_prefix']], [0, 1])
        self.assertEqual([r['source_provenance']['original_roster_native_index'] for r in partial['independently_derived_requests']], [0, 1, 3])
        with self.assertRaises(ValueError):
            daily_assault_roster_admission_requests_12003(partial)
        prefix = daily_assault_roster_admission_requests_12003(partial, prefix_only=True)
        self.assertEqual(len(prefix), 2)

        _, matched = query('reached-membership-match-skips-unread-tail', matched_suppression_with_unread_tail_source())
        self.assertTrue(matched['conditional_admission_ready'])
        self.assertEqual(matched['occurrences'][0]['arrg_append_full_ids_u32'], [])
        _, raw_partial = query('raw-read-failure-keeps-original-native-order', partial_raw_roster_source())
        self.assertFalse(raw_partial['raw_roster_references_ready'])
        self.assertEqual([r['native_index'] for r in raw_partial['raw_roster_occurrences']], [0, 1, 2, 3, 4])
        self.assertIsNone(raw_partial['raw_roster_occurrences'][2]['raw_full_id_u32'])
        self.assertEqual([r['source_provenance']['original_roster_native_index'] for r in raw_partial['independently_derived_requests']], [0, 1, 3])
        _, zero = query('legal-zero-roster-unused-removal-input', zero_roster_admission_source())
        self.assertTrue(zero['conditional_admission_ready'])
        self.assertFalse(zero['removal_queue_references_ready'])
        self.assertEqual(daily_assault_roster_admission_requests_12003(zero), ())
        _, legacy = query('older-producer-new-family-unavailable', None)
        self.assertFalse(legacy['conditional_admission_ready'])

        output = os.environ.get('XAR_DAILY_ASSAULT_ROSTER_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
