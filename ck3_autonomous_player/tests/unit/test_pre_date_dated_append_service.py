from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pre_date_dated_append_fixture import source, partial_date_source, missing_clock_source, id_list
from test_scoped_ordered_refill_service import MemoryRoute
from test_current_daily_assault_table_service import source_row
from test_daily_assault_placement_service import placement_source
from pre_date_pending_update_fixture import source as pending_source, arrg
from daily_assault_roster_admission_fixture import roster_admission_source, references
from xar_autoplayer.bridge.army_pre_date_dated_append_contract import normalize_current_pre_date_dated_append_inputs_v1
from xar_autoplayer.simulation.army_daily_assault_placement_12003 import (
    CONDITIONAL_PLACEMENT_STAGE_12003, ExplicitDailyAssaultPlacementStage12003,
    project_daily_assault_placement_prefix_12003,
)
from xar_autoplayer.simulation.army_daily_assault_roster_admission_12003 import daily_assault_roster_admission_requests_12003


class PreDateDatedAppendServiceTests(unittest.TestCase):
    def test_nonempty_dated_append_same_query_current_pending_admission_and_placement(self):
        """One new complete-service compound; never invoke prior test methods."""
        outputs = {}
        pending = pending_source(mode='existing', pending_ids=(), roster=(13, 13), queue=(99, 99))
        # Dated C8 IDs are distinct from the primary50 roster. These two
        # entrances share one unchanged captured50/68/pending context; they
        # are not advertised as replaying the remaining native caller prefix.
        admission = roster_admission_source()
        selected = deepcopy(admission['occurrences'][2])  # Army13 / Siege5 / ArRg400, empty current pending.
        admission['occurrences'] = [deepcopy(selected), deepcopy(selected)]
        for index, row in enumerate(admission['occurrences']): row['native_index'] = index
        admission['original_roster'] = deepcopy(pending['original_roster'])
        admission['removal_queue'] = deepcopy(pending['removal_queue'])
        for row, admitted in zip(pending['occurrences'], admission['occurrences']):
            row['original_army_resolution'] = deepcopy(admitted['original_army_resolution'])
            row['original_arrg_references'] = deepcopy(admitted['original_arrg_references'])
            row['arrg_occurrences'] = [arrg(0, 400)]
            row['pending_setup']['existing_references'] = references([])
        stage = ExplicitDailyAssaultPlacementStage12003(CONDITIONAL_PLACEMENT_STAGE_12003,
            {'scope': 'explicit held current state after dated logical prefix only', 'actual_next_callback_ready': False})

        def query(name, leaf, native_parent=None):
            row = source_row(placement_source()) if native_parent is None else deepcopy(native_parent)
            row['current_pre_date_pending_update_inputs_v1'] = deepcopy(pending)
            row['current_daily_assault_roster_admission_v1'] = deepcopy(admission)
            if leaf is not None:
                row['current_pre_date_dated_append_inputs_v1'] = deepcopy(leaf)
            before = deepcopy(row)
            class Route(MemoryRoute):
                def snapshot(self):
                    snapshot = super().snapshot()
                    snapshot['player_armies'] = [{'army_id': row['army_id']}]
                    snapshot['date_raw'] = 2147483640  # Held native fixture clock, not an inferred calendar.
                    return snapshot
            service = Route(row)
            returned = service.query_army_strengths([row['army_id']], expected_revision=42)
            self.assertEqual(row, before)
            self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
            self.assertEqual(returned['status'], 'available')
            self.assertEqual(returned['native_readiness'], {'current_strength': True, 'full_monthly': False})
            self.assertEqual(returned['source']['native_revision'], 7)
            self.assertEqual(returned['army_strengths'][0]['current_soldiers'], row['current_soldiers'])
            dated = returned['current_pre_date_dated_append_inputs_v1'][0]['projection']
            observed = returned['army_strengths'][0]
            if leaf is not None:
                self.assertEqual(observed['current_pre_date_dated_append_inputs_v1'], leaf)
            self.assertFalse(dated['actual_next_callback_ready'])
            self.assertFalse(dated['full_daily_assault_ready'])
            self.assertFalse(dated['remaining_character_unit_prefix_replayed'])
            self.assertFalse(dated['physical_growth_replayed'])
            self.assertEqual((dated['native_calls_executed'], dated['native_writes_executed']), (0, 0))
            self.assertEqual(dated['preserved_prefix_inputs'], ['manager_50_5c', 'manager_68_74', 'manager_pending_130'])
            outputs[name] = {'service': returned}
            return returned, dated

        returned, complete = query('nonempty-wrap-repeat-fallback-first-match', source())
        self.assertTrue(complete['clock_ready'])
        self.assertEqual(complete['tomorrow_date_low_i32'], -2147483632)
        self.assertTrue(complete['conditional_append_requests_ready'])
        self.assertEqual(complete['append_request_full_ids_u32'], [31, 31, 0xFE00001E])
        self.assertEqual(complete['logical_158_full_ids_u32'], [7, 7, 31, 31, 0xFE00001E])
        self.assertEqual(complete['logical_158_count_i32'], 5)
        self.assertEqual([d['branch'] for d in complete['occurrences']],
                         ['first_due_date_append'] * 3 + ['valid_combat_skip', 'nonpositive_date_count_skip', 'all_dates_later_skip'])
        observed = returned['army_strengths'][0]
        pending_projection = observed['same_input_conditional_current_pre_date_pending_update_v1']
        self.assertTrue(pending_projection['pending_counts_and_removal_requests_ready'])
        self.assertTrue(pending_projection['updated_pending_values_ready'])
        self.assertEqual(pending_projection['pending_lists'][0]['conditional_full_ids_u32'], [400, 400])
        admitted = returned['current_daily_assault_roster_admission_inputs_v1'][0]['projection']
        self.assertTrue(admitted['conditional_admission_ready'])
        requests = daily_assault_roster_admission_requests_12003(admitted)
        self.assertGreater(len(requests), 0)
        placed = project_daily_assault_placement_prefix_12003(
            observed['current_daily_assault_table_v1'], requests, input_stage=stage)
        self.assertTrue(placed['conditional_placement_ready'])
        self.assertGreater(placed['applied_request_count'], 0)
        self.assertFalse(placed['actual_next_callback_ready'])
        outputs['nonempty-wrap-repeat-fallback-first-match']['conditional_placement'] = placed

        no_initial = source()
        no_initial['initial_158'] = id_list(None, count=2)
        _, p = query('independent-initial158', no_initial)
        self.assertTrue(p['conditional_append_requests_ready'])
        self.assertFalse(p['logical_158_result_ready'])
        self.assertEqual(p['append_request_full_ids_u32'], complete['append_request_full_ids_u32'])
        _, p = query('required-date-failure-prefix-and-independent-later', partial_date_source())
        self.assertFalse(p['conditional_append_requests_ready'])
        self.assertEqual(p['request_prefix'], [])
        self.assertEqual([r['source_native_index'] for r in p['independently_derived_requests']], [2])
        _, p = query('clock-unavailable-independent-no-date-branches', missing_clock_source())
        self.assertFalse(p['clock_ready'])
        self.assertTrue(p['occurrences'][3]['ready'])
        self.assertTrue(p['occurrences'][4]['ready'])
        empty = missing_clock_source()
        empty.update(status='available', ready=True, unavailable_reason='')
        empty['source_c8'] = id_list([], count=-3); empty['occurrences'] = []
        _, p = query('signed-nonpositive-source-no-clock-demand', empty)
        self.assertTrue(p['conditional_append_requests_ready'])
        self.assertEqual(p['append_request_full_ids_u32'], [])
        self.assertFalse(p['clock_ready'])
        _, p = query('older-producer-family-absent', None)
        self.assertFalse(p['conditional_append_requests_ready'])

        # Transport must reject changed original generations/order and an
        # invented tomorrow operand rather than silently recomputing the wire.
        wrong = source(); wrong['tomorrow_date_low_i32'] += 1
        with self.assertRaises(ValueError): normalize_current_pre_date_dated_append_inputs_v1(wrong)
        wrong = source(); wrong['occurrences'][2]['original_request_full_id_u32'] = 30
        with self.assertRaises(ValueError): normalize_current_pre_date_dated_append_inputs_v1(wrong)
        wrong = source(); wrong['occurrences'][0]['date_entries'].append(
            {'native_index': 2, 'pointer_identity': None, 'pointer_present': None, 'date_low_raw_i32': None})
        with self.assertRaises(ValueError): normalize_current_pre_date_dated_append_inputs_v1(wrong)

        native_directory = os.environ.get('XAR_PRE_DATE_DATED_APPEND_NATIVE_DIR')
        if native_directory:
            for path in sorted(Path(native_directory).glob('*.json')):
                native = json.loads(path.read_text(encoding='utf-8-sig'))
                _, p = query('native-wire-' + path.stem,
                             native['current_pre_date_dated_append_inputs_v1'], native)
                outputs['native-wire-' + path.stem]['dated'] = p
        output = os.environ.get('XAR_PRE_DATE_DATED_APPEND_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps(outputs, indent=2) + '\n', encoding='utf-8')
