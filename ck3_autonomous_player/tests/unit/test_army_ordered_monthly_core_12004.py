"""One new conditional manager-stage composition scene; no native execution."""
from copy import deepcopy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, 'Z:/ck3_mod_rewrite/ck3_autonomous_player/src')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from army_ordered_monthly_core_12004 import ENTRY_KIND, EXE_SHA256, project_army_ordered_monthly_core_12004

FRAME = 'one-explicit-regular-core-entry'


def occurrence(index, token, identity, *, raw=None, fallback=False):
    return {'entry_frame_id': FRAME, 'stored_index': index,
            'physical_token': token, 'raw_full_id': identity if raw is None else raw,
            'resolved_full_id': identity, 'used_fallback': fallback}


def persistent(token, identity, current, fraction):
    chunks = []
    for index in range(7):
        chunk = {field: None for field in (
            'owner_resolved_full_id', 'owner_guard_138_raw', 'origin_province_id',
            'origin_province_788_raw', 'origin_province_73c_raw',
            'associated_arrg_resolved_full_id', 'associated_army_raw_full_id',
            'associated_army_resolved_full_id', 'army_byte_1d4_raw', 'army_byte_1ec_raw',
            'associated_unit_raw_full_id', 'associated_unit_resolved_full_id', 'unit_170_raw',
            'unit_position_owner_resolved_full_id', 'unit_position_holder_resolved_full_id',
            'owner_definition_magic_38_raw', 'associated_arrg_magic_raw',
            'unit_position_province_magic_raw', 'native_army_in_combat',
            'native_unit_position_eligible', 'context_unavailable_reason')}
        chunk.update(physical_index=index, current_soldiers=current if index == 0 else 0,
                     maximum_soldiers=100 if index == 0 else 0,
                     owner_persistent_regiment_id=identity, q_ordinal_raw=index,
                     army_regiment_id_raw=1000 + index, exclusion_byte_14_raw=0,
                     state_raw=0, owner_resolved_full_id=identity, owner_guard_138_raw=0,
                     owner_definition_magic_38_raw=0x52656769, origin_province_788_raw=-1,
                     origin_province_73c_raw=-1, associated_arrg_resolved_full_id=-1,
                     associated_arrg_magic_raw=0)
        chunks.append(chunk)
    return {'entry_frame_id': FRAME, 'physical_token': token, 'resolved_full_id': identity,
            'prepared_fraction_raw': fraction, 'unavailable_reason': None, 'chunks': chunks}


def army(token, identity, data_tokens):
    records = [{'record_index': index, 'persistent_regiment_id': 10 if p == 'A' else 20,
                'persistent_physical_token': p, 'chunk_index': 0, 'state_raw': 0}
               for index, p in enumerate(data_tokens)]
    arrg = occurrence(0, 'ArRg-' + token, identity + 100)
    arrg.update(resolved_magic_14_raw=0x41725267,
                data_snapshot={'entry_frame_id': FRAME, 'status': 'available',
                    'army_regiment_id': identity + 100, 'native_loss_writer_skipped': False,
                    'native_record_count': len(records), 'records': records})
    return {'entry_frame_id': FRAME, 'physical_token': token, 'resolved_full_id': identity,
            'native_arrg_occurrence_count': 1, 'arrg_occurrences': [arrg]}


def stage():
    return {'game_version': '1.20.0.4', 'exe_sha256': EXE_SHA256,
            'entry_kind': ENTRY_KIND, 'entry_frame_id': FRAME,
            'native_persistent_occurrence_count': 3,
            'persistent_occurrences': [occurrence(0, 'A', 10), occurrence(1, 'A', 10), occurrence(2, 'B', 20)],
            'persistent_objects': [persistent('A', 10, 80, 10000), persistent('B', 20, 20, 50000)],
            'native_army_refresh_occurrence_count': 3,
            'army_refresh_occurrences': [occurrence(0, 'Y', 40), occurrence(1, 'X', 30), occurrence(2, 'Y', 40)],
            'army_objects': [army('X', 30, ['A', 'A']), army('Y', 40, ['A', 'B'])]}


class OrderedMonthlyCore12004Tests(unittest.TestCase):
    def test_all_manager_occurrences_share_physical_state_then_refresh_in_original_order(self):
        observed = stage()
        before = deepcopy(observed)
        output = project_army_ordered_monthly_core_12004(observed)
        self.assertTrue(output['conditional_regular_core_current_maximum_ready'])
        self.assertEqual(observed, before)
        self.assertNotIn('fresh_fraction', observed)
        final = {c['physical_token']: c['current_soldiers'] for c in output['physical_chunks'] if c['chunk_index'] == 0}
        self.assertEqual(final, {'A': 100, 'B': 70})
        self.assertEqual([r['physical_token'] for r in output['persistent_occurrences']], ['A', 'A', 'B'])
        self.assertEqual([r['writes'][0]['before_current'] for r in output['persistent_occurrences']], [80, 90, 20])
        refreshes = output['army_refresh_occurrences']
        self.assertEqual([r['physical_token'] for r in refreshes], ['Y', 'X', 'Y'])
        self.assertEqual([r['regiment_refresh_occurrences'][0]['conditional_current_maximum']['current_soldiers']
                          for r in refreshes], [170, 200, 170])
        self.assertEqual([r['raw_persistent_full_id'] for r in refreshes[1]['regiment_refresh_occurrences'][0]['DATA_bindings']], [10, 10])
        for r in refreshes:
            self.assertEqual(r['regiment_refresh_occurrences'][0]['conditional_current_maximum']['source_contract_game_version'], '1.20.0.3')
        self.assertFalse(output['actual_post_stage_observed'])
        self.assertFalse(output['full_monthly_ready'])
        self.assertFalse(output['manager_statistics_replayed'])
        once = stage()
        once['persistent_occurrences'] = [occurrence(0, 'A', 10), occurrence(1, 'B', 20)]
        once['native_persistent_occurrence_count'] = 2
        reference = project_army_ordered_monthly_core_12004(once)
        self.assertEqual(next(c['current_soldiers'] for c in reference['physical_chunks']
                              if c['physical_token'] == 'A' and c['chunk_index'] == 0), 90)

        fallback = {'game_version': '1.20.0.4', 'exe_sha256': EXE_SHA256,
            'entry_kind': ENTRY_KIND, 'entry_frame_id': FRAME,
            'native_persistent_occurrence_count': 2,
            'persistent_occurrences': [occurrence(0, 'fallback', -1, raw=16777217, fallback=True),
                                       occurrence(1, 'fallback', -1, raw=33554433, fallback=True)],
            'persistent_objects': [persistent('fallback', -1, 80, 10000)],
            'native_army_refresh_occurrence_count': 0, 'army_refresh_occurrences': [], 'army_objects': []}
        aliased = project_army_ordered_monthly_core_12004(fallback)
        self.assertTrue(aliased['conditional_regular_core_current_maximum_ready'])
        self.assertEqual(aliased['physical_chunks'][0]['current_soldiers'], 100)
        self.assertEqual([r['raw_full_id'] for r in aliased['persistent_occurrences']], [16777217, 33554433])
        self.assertEqual([r['resolved_full_id'] for r in aliased['persistent_occurrences']], [-1, -1])
        self.assertEqual([r['writes'][0]['before_current'] for r in aliased['persistent_occurrences']], [80, 90])

        incomplete = stage()
        incomplete['persistent_occurrences'].pop()
        missing = project_army_ordered_monthly_core_12004(incomplete)
        self.assertEqual(missing['status'], 'unavailable')
        self.assertEqual(missing['physical_chunks'], [])
        self.assertEqual(missing['army_refresh_occurrences'], [])
        mixed = stage()
        mixed['persistent_occurrences'][1]['entry_frame_id'] = 'pre-cleanup-frame'
        with self.assertRaisesRegex(ValueError, 'different entry frames'):
            project_army_ordered_monthly_core_12004(mixed)


if __name__ == '__main__':
    unittest.main()
