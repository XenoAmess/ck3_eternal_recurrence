"""New pure prepare-gate checks only; synthetic Strength/frame inputs."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import os
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
REPO = Path(os.environ.get('CK3_R06_BASE_REPO', str(ROOT)))
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO/'ck3_autonomous_player/src'))
PREPARE = REPO/'ck3_autonomous_player/native_bridge/research/refill_add_live_12004/prepare_live_refill_add.py'
spec = importlib.util.spec_from_file_location('positive_prepare_candidate', PREPARE)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def fixture(fraction=10000, current=80, maximum=100):
    chunks = []
    for index in range(7):
        chunks.append({
            'physical_index': index, 'current_soldiers': current if index == 0 else 0,
            'maximum_soldiers': maximum if index == 0 else 0,
            'owner_persistent_regiment_id': 50001, 'q_ordinal_raw': index,
            'army_regiment_id_raw': 11001 if index == 0 else -1,
            'exclusion_byte_14_raw': 0, 'state_raw': 0, 'context_unavailable_reason': None,
            'owner_resolved_full_id': 50001, 'owner_guard_138_raw': 0,
            'owner_definition_magic_38_raw': 0, 'origin_province_id': 1,
            'origin_province_788_raw': -1, 'origin_province_73c_raw': -1,
            'associated_arrg_resolved_full_id': 11001 if index == 0 else -1,
            'associated_arrg_magic_raw': 0x41725267, 'associated_army_raw_full_id': 12,
            'associated_army_resolved_full_id': 12, 'army_byte_1d4_raw': 0, 'army_byte_1ec_raw': 0,
            'native_army_in_combat': False, 'associated_unit_raw_full_id': 11,
            'associated_unit_resolved_full_id': 11, 'unit_170_raw': 0,
            'unit_position_province_magic_raw': 0x50726F76,
            'unit_position_owner_resolved_full_id': 777,
            'unit_position_holder_resolved_full_id': 777, 'native_unit_position_eligible': True})
    record = {'status': 'available', 'unavailable_reason': None, 'record_index': 0,
              'persistent_regiment_id': 50001, 'chunk_index': 0, 'chunk_army_regiment_id': 11001,
              'current_soldiers': current, 'maximum_soldiers': maximum,
              'effective_current_soldiers': current, 'state_raw': 0,
              'native_can_replenish': True, 'native_chunk_can_replenish': True,
              'persistent_monthly_replenishment_fraction_raw': 10000,
              'persistent_monthly_replenishment_fraction_scale': 100000,
              'persistent_prepared_replenishment_fraction_raw': fraction,
              'persistent_prepared_replenishment_fraction_scale': 100000}
    row = {'status': 'available', 'army_id': 11, 'native_carmy_id': 12,
           'regiment_count': 1, 'current_soldiers': current, 'maximum_soldiers': maximum,
           'regiment_strengths': [{'army_regiment_id': 11001, 'current_soldiers': current,
                                  'maximum_soldiers': maximum, 'scale': 1}],
           'regiment_replenishment_records_v1': [{
               'source': 'native_all_data_records', 'army_regiment_id': 11001,
               'status': 'available', 'ready': True, 'native_data_record_count': 1,
               'unavailable_reason': None, 'native_loss_writer_skipped': False,
               'loss_writer_admission_unavailable_reason': None, 'records': [record]}],
           'fixed_chunk0_preparation_inputs_v1': {
               'source': 'native_scoped_fixed_chunk0_preparation_inputs',
               'entry_kind': 'current_frozen_context_preparation', 'status': 'available', 'ready': True,
               'subject_army_id': 11, 'subject_carmy_id': 12,
               'referenced_persistent_ids_complete': True, 'unavailable_reason': None,
               'persistent_regiments': [{'persistent_regiment_id': 50001, 'fixed_chunk_index': 0,
                   'status': 'available', 'ready': True, 'unavailable_reason': None,
                   'fraction_scale': 100000, 'containing_guard_138_raw': 0,
                   'containing_definition_magic_38': 0,
                   'native_fixed_chunk0_can_replenish': True, 'fresh_fraction_raw': 10000}]},
           'scoped_ordered_refill_inputs_v1': {
               'source': 'native_scoped_observed_prepared_ordered_refill', 'status': 'available',
               'unavailable_reason': None, 'subject_army_id': 11, 'subject_carmy_id': 12,
               'native_persistent_occurrence_count': 4, 'native_army_refresh_occurrence_count': 1,
               'persistent_occurrences': [{'stored_index': 1, 'persistent_regiment_id': 50001},
                                          {'stored_index': 3, 'persistent_regiment_id': 50001}],
               'army_refresh_occurrence_indices': [0],
               'persistent_regiments': [{'persistent_regiment_id': 50001,
                   'prepared_fraction_raw': fraction, 'unavailable_reason': None, 'chunks': chunks}]}}
    frame = {'paused': True, 'map_ready': True, 'snapshot_id': 'synthetic-only', 'revision': 3,
             'native_revision': 2, 'date_raw': 7, 'episode_run_id': 'synthetic',
             'diagnostics': {'bridge_pid': 123, 'connection_generation': 4,
                 'hello': {'expected_ck3_version': '1.20.0.4', 'expected_ck3_sha256': candidate.EXE_SHA}}}
    packet = {'accepted': True, 'queried_snapshot_id': frame['snapshot_id'], 'queried_revision': 3,
              'queried_native_revision': 2, 'queried_date_raw': 7,
              'queried_episode_run_id': 'synthetic', 'queried_connection_generation': 4,
              'army_strengths': [row]}
    return frame, packet


def parts(packet):
    row = packet['army_strengths'][0]
    return row, row['scoped_ordered_refill_inputs_v1'], row['regiment_replenishment_records_v1'][0]


class PositivePrepareGateTests(unittest.TestCase):
    def select(self, frame, packet, **kw):
        return candidate.select_positive_prepare_target(frame, packet, army_id=11, **kw)

    def test_positive_preserves_occurrence_order_and_conditional_boundary(self):
        f, p = fixture(); before = deepcopy((f, p)); v = self.select(f, p)
        self.assertEqual((f, p), before)
        self.assertEqual(v['conditional_shared_q_i32'], 10)
        self.assertEqual(v['selected_occurrence_stored_index'], 1)
        self.assertEqual([o['stored_index'] for o in v['ordered_occurrences']], [1, 3])
        self.assertFalse(v['actual_ADD_observed']); self.assertFalse(v['actual_preparation_observed'])
        self.assertEqual(v['ordered_refill_entry_mode'], 'observed_prepared')

    def test_zero_and_negative_shared_q_rejected(self):
        for args in ((0, 80, 100), (1, 80, 100), ((1 << 63)-1, 1, 100000)):
            with self.subTest(args=args), self.assertRaises(ValueError): self.select(*fixture(*args))

    def test_unknown_partial_and_stale_rejected(self):
        for change in ('unknown', 'partial', 'six', 'date', 'data'):
            f, p = fixture(); row, family, data = parts(p)
            if change == 'unknown': family['persistent_regiments'][0]['chunks'][0]['origin_province_788_raw'] = None
            if change == 'partial': family.update(status='partial', unavailable_reason='synthetic-partial')
            if change == 'six': family['persistent_regiments'][0]['chunks'].pop()
            if change == 'date': p['queried_date_raw'] += 1
            if change == 'data': data.update(status='partial', ready=False, unavailable_reason='synthetic-partial')
            with self.subTest(change=change), self.assertRaises(ValueError): self.select(f, p)

    def test_raw_position_false_or_unknown_rejected_even_when_projector_owner_matches(self):
        for value in (False, None):
            f, p = fixture(); parts(p)[1]['persistent_regiments'][0]['chunks'][0]['native_unit_position_eligible'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): self.select(f, p)

    def test_DATA_aliases_preserved_without_duplicate_physical_selection(self):
        f, p = fixture(); row, family, data = parts(p)
        alias = deepcopy(data['records'][0]); alias['record_index'] = 1
        data['records'].append(alias); data['native_data_record_count'] = 2
        row['current_soldiers'] *= 2; row['maximum_soldiers'] *= 2
        row['regiment_strengths'][0]['current_soldiers'] *= 2
        row['regiment_strengths'][0]['maximum_soldiers'] *= 2
        v = self.select(f, p)
        self.assertEqual([r['record_index'] for r in v['DATA_occurrences']], [0, 1])
        self.assertEqual(len(v['selected_eligibility']), 1)

    def test_q_index_differs_from_physical_and_later_overwrite_controls_selection(self):
        f, p = fixture(); chunks = parts(p)[1]['persistent_regiments'][0]['chunks']
        chunks[0]['q_ordinal_raw'] = 5
        chunks[2].update(maximum_soldiers=50, q_ordinal_raw=5)
        v = self.select(f, p)
        self.assertEqual((v['physical_slot'], v['q_index'], v['conditional_shared_q_i32']), (0, 5, 5))
        self.assertEqual(v['ordered_occurrences'][0]['chunk_decisions'][0]['calculated_q'], 10)
        chunks[2]['maximum_soldiers'] = 1
        with self.assertRaises(ValueError): self.select(f, p)

    def test_first_positive_DATA_write_skips_earlier_zero_physical_slot(self):
        f, p = fixture(10000, 0, 1); row, family, data = parts(p)
        chunks = family['persistent_regiments'][0]['chunks']
        chunks[1] = {**deepcopy(chunks[0]), 'physical_index': 1, 'q_ordinal_raw': 1,
                     'current_soldiers': 80, 'maximum_soldiers': 100}
        record = {**deepcopy(data['records'][0]), 'record_index': 1, 'chunk_index': 1,
                  'current_soldiers': 80, 'effective_current_soldiers': 80, 'maximum_soldiers': 100}
        data['records'].append(record); data['native_data_record_count'] = 2
        row.update(current_soldiers=80, maximum_soldiers=101)
        row['regiment_strengths'][0].update(current_soldiers=80, maximum_soldiers=101)
        v = self.select(f, p)
        self.assertEqual((v['physical_slot'], v['conditional_shared_q_i32']), (1, 10))
        self.assertEqual(v['selected_occurrence_stored_index'], 1)

    def test_fixed_prepare_uses_fresh_conditional_basis_without_rewriting_observed148(self):
        f, p = fixture(0); before = deepcopy(p)
        with self.assertRaises(ValueError): self.select(f, p)
        v = self.select(f, p, mode='fixed_chunk0_prepare')
        self.assertEqual(p, before)
        self.assertEqual(v['conditional_shared_q_i32'], 10)
        self.assertIn('conditional_preparation', v['input_basis'])
        self.assertFalse(v['actual_preparation_observed'])

    def test_full_identity_and_same_query_disagreements_rejected(self):
        for key in ('owner_resolved_full_id', 'associated_army_resolved_full_id', 'current_soldiers'):
            f, p = fixture(); parts(p)[1]['persistent_regiments'][0]['chunks'][0][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError): self.select(f, p)

    def test_explicit_target_constraint_cannot_promote_zero_or_other_identity(self):
        f, p = fixture()
        for kw in ({'regiment': 50002}, {'slot': 1}, {'regiment': True}, {'slot': False}):
            with self.subTest(kw=kw), self.assertRaises(ValueError): self.select(f, p, **kw)

    def test_query_mode_mismatch_rejected(self):
        f, p = fixture(); p['ordered_refill_entry_mode'] = 'fixed_chunk0_prepare'
        with self.assertRaises(ValueError): self.select(f, p)

    def test_source_dir_uses_actual_existing_absolute_fixed_basename(self):
        existing = str(REPO/'ck3_autonomous_player/native_bridge/research/refill_add_live_12004')
        self.assertEqual(candidate.validate_source_dir(existing), existing)
        for value in ('refill_add_live_12004', str(ROOT/'does-not-exist/refill_add_live_12004'),
                      str(REPO/'ck3_autonomous_player/native_bridge/research'), None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidate.validate_source_dir(value)


if __name__ == '__main__': unittest.main()
