from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from xar_autoplayer.bridge.service import GameplayBridgeService
from army_selected_title_holder_owner_relation_compiled_wire_builder import (
    load_compiled_selected_title_holder_owner_relation_wire,
)

_FAMILY = 'current_selected_title_holder_owner_relation_v1'
_LIMITS = (
    'actual_refresh_execution_ready', 'actual_next_occurrence_ready',
    'changed_selection_context_ready', 'changed_relationship_context_ready',
    'full_callback_ready', 'full_daily_assault_ready', 'full_monthly_ready',
    'actual_post_stage_observed', 'future_tick_ready',
)


class MemorySelectedTitleHolderOwnerRelationRoute(GameplayBridgeService):
    def __init__(self, source: dict):
        self.source, self.calls = source, []

    def snapshot(self):
        return {
            'paused': True, 'revision': 42, 'native_revision': 7, 'date_raw': 10000,
            'snapshot_id': 'synthetic-selected-title-holder-current-frame',
            'backend_id': 'pure-memory-fixture',
            'player_armies': [{'army_id': self.source['army_id']}], 'active_wars': [],
            'diagnostics': {'hello': {'game_version': '1.20.0.3'}},
        }

    def capabilities(self):
        return {'action_steps': ['query-army-strengths-v1']}

    def execute_step(self, step, *, expected_revision=None):
        self.calls.append((step, expected_revision))
        return {
            'status': 'available', 'army_strengths': [deepcopy(self.source)],
            'native_readiness': {'current_strength': True, 'full_monthly': False},
        }


class ArmyCurrentSelectedTitleHolderOwnerRelationService12003Tests(unittest.TestCase):
    def test_first_compiled_selected_title_holder_owner_relation_through_service_normalizer_and_current_projection(self):
        wire = load_compiled_selected_title_holder_owner_relation_wire(
            os.environ['XAR_ARMY_SELECTED_TITLE_HOLDER_OWNER_RELATION_WIRE'])
        expected_tail = {
            'invalid-first-province-undemanded': 0, 'direct-equal': 1,
            'native-false-owner-zero': 0, 'native-true-holder-zero': 1,
            'native-true-highbit-fullgen': 1, 'requested-generation-fallbacks': 1,
            'missing-holder-parent-tier-one': 1, 'missing-holder-other-tier': 1,
            'null-inner-stores-undemanded': 1, 'missing-callable': None,
        }
        expected_relation = {
            name: None if name in {
                'invalid-first-province-undemanded', 'direct-equal', 'missing-callable',
            } else name != 'native-false-owner-zero'
            for name in expected_tail
        }
        outputs = {}
        actual_occurrences = 0
        for name, native_row in wire['samples'].items():
            with self.subTest(sample=name):
                source = deepcopy(native_row)
                before = deepcopy(source)
                leaf = native_row.get(_FAMILY)
                service = MemorySelectedTitleHolderOwnerRelationRoute(source)
                returned = service.query_army_strengths(
                    [native_row['army_id']], expected_revision=42)
                self.assertEqual(source, before)
                self.assertEqual(service.calls, [('query-army-strengths-v1', 42)])
                self.assertEqual(returned['status'], 'available')
                self.assertEqual(
                    returned['native_readiness'],
                    {'current_strength': True, 'full_monthly': False})
                normalized = returned['army_strengths'][0]
                for field in ('current_soldiers', 'maximum_soldiers', 'ai_base_power_raw'):
                    self.assertEqual(normalized[field], native_row[field])
                for field in ('current_army_flag20_inputs_v1', 'current_army_flag21_inputs_v1'):
                    if field in native_row:
                        self.assertEqual(normalized[field], native_row[field])
                self.assertEqual(normalized.get(_FAMILY), leaf)
                projected = returned[_FAMILY][0]['projection']
                self.assertEqual(
                    projected['observed_current_selected_title_holder_owner_relation_inputs'], leaf)
                self.assertEqual(projected['source_provenance']['revision'], 42)
                self.assertEqual(projected['source_provenance']['native_revision'], 7)
                self.assertEqual(projected['source_provenance']['game_version'], '1.20.0.3')
                for field in _LIMITS:
                    self.assertFalse(projected[field])
                self.assertEqual(projected['native_calls_executed'], 0)
                self.assertEqual(projected['native_writes_executed'], 0)
                if leaf is None:
                    self.assertFalse(projected['ready'])
                    self.assertFalse(projected['current_shared_tail_inputs_ready'])
                    self.assertEqual(projected['occurrences'], [])
                    outputs[name] = returned
                    continue
                actual_occurrences += len(leaf['occurrences'])
                self.assertEqual(projected['ready'], leaf['ready'])
                self.assertEqual(projected['ready'], expected_tail[name] is not None)
                self.assertEqual(len(projected['occurrences']), 2)
                self.assertEqual(
                    [row['native_index'] for row in projected['occurrences']], [0, 1])
                self.assertEqual(
                    projected['occurrences'][0]['raw_full_id_u32'],
                    projected['occurrences'][1]['raw_full_id_u32'])
                self.assertEqual(
                    projected['current_shared_tail_inputs_ready'],
                    leaf['current_shared_tail_inputs_ready'])
                self.assertEqual(
                    [(row['native_index'], row['raw_full_id_u32']) for row in projected['occurrences']],
                    [(row['native_index'], row['raw_full_id_u32']) for row in leaf['occurrences']])
                self.assertEqual(
                    [(row['native_index'], row['raw_full_id_u32']) for row in projected['occurrences']],
                    [(row['native_index'], row['raw_full_id_u32'])
                     for row in leaf['original_roster']['occurrences']])
                for observed, occurrence in zip(leaf['occurrences'], projected['occurrences']):
                    for field in (
                        'original_army_resolution', 'same_query_army_selection_matched',
                        'unit_selections', 'holder_requested_full_id_u32',
                        'holder_character_full_id_u32', 'holder_character_resolution',
                        'selected_unit_owner_174_raw_u32', 'holder_owner_equal',
                        'native_relation_demanded', 'native_relation_returned',
                        'native_holder_owner_relation', 'derived_current_shared_tail_raw_u8',
                        'current_shared_tail_inputs_ready', 'ready',
                    ):
                        self.assertEqual(occurrence[field], observed[field])
                    relation = occurrence['native_holder_owner_relation']
                    self.assertIs(relation, expected_relation[name])
                    self.assertEqual(
                        occurrence['derived_current_shared_tail_raw_u8'], expected_tail[name])
                    self.assertEqual(
                        occurrence['native_relation_demanded'],
                        name not in {'invalid-first-province-undemanded', 'direct-equal'})
                    self.assertEqual(
                        occurrence['native_relation_returned'], expected_relation[name] is not None)
                    if name == 'native-false-owner-zero':
                        self.assertEqual(occurrence['selected_unit_owner_174_raw_u32'], 0)
                    elif name == 'native-true-holder-zero':
                        self.assertEqual(occurrence['holder_character_full_id_u32'], 0)
                    if occurrence['native_relation_returned']:
                        self.assertIs(type(relation), bool)
                        self.assertTrue(occurrence['native_relation_demanded'])
                        self.assertTrue(occurrence['ready'])
                        self.assertEqual(
                            occurrence['derived_current_shared_tail_raw_u8'], int(relation))
                    else:
                        self.assertIsNone(relation)
                    if occurrence['holder_owner_equal'] is True:
                        self.assertFalse(occurrence['native_relation_demanded'])
                        self.assertFalse(occurrence['native_relation_returned'])
                        self.assertEqual(occurrence['derived_current_shared_tail_raw_u8'], 1)
                    if occurrence['native_relation_demanded'] and not occurrence['native_relation_returned']:
                        self.assertFalse(occurrence['ready'])
                        self.assertIsNone(occurrence['derived_current_shared_tail_raw_u8'])
                    owner = occurrence['selected_unit_owner_174_raw_u32']
                    if owner is not None:
                        self.assertIs(type(owner), int)
                        self.assertGreaterEqual(owner, 0)
                        self.assertLessEqual(owner, 0xFFFFFFFF)
                outputs[name] = returned
        output = os.environ.get('XAR_ARMY_SELECTED_TITLE_HOLDER_OWNER_RELATION_CASE_OUTPUT')
        if output:
            Path(output).write_text(json.dumps({
                'qualification': (
                    'genuine compiled whole native query/serializer samples; no baseline or transplant; '
                    'new selected-title same-context relation only; world/callbacks and Service envelope synthetic'),
                'actual_compound_cases': 1, 'actual_new_native_samples': len(wire['samples']),
                'actual_occurrences': actual_occurrences, 'outputs': outputs,
            }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
