"""Cross-view checks through the production fixed-refill callback consumer."""
import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge import gui_callback_binding_12004_contract as callback_contract
from xar_autoplayer.bridge.gui_callback_binding_12004_contract import (
    SOURCE_RECEIVER_12004, normalize_callback_binding_rows_12004)


def entry(depth=0):
    return dict(ancestor_depth=depth, entry_type_48=635, entry_mode_40=3,
                entry_flag_4c=0, direct_value_present=False, provider_present=True,
                provider_vtable_rva=0x1000, provider_slot2_rva=0x2000,
                direct_owner_full_id=None, direct_owner_identity_verified=False)


def local(rows=None):
    rows = [entry()] if rows is None else rows
    return dict(source='native_gui_type635_local_definition_entry_only_12004',
                scope='local_definition_entry_only', status='available', unavailable_reason=None,
                receiver_type_id=635, ancestor_depth=0, current_variable_table_observed=False,
                native_receiver_selected=False, receiver_variable_index=0, declared_type_id=635,
                raw_definition_entry_count=1, local_definition_active_raw=1,
                definition_present=True, local_entry_present=bool(rows), stable_double_read=True,
                entries=copy.deepcopy(rows))


def full(rows=None):
    rows = [entry()] if rows is None else rows
    return dict(source='native_gui_type635_definition_candidates_12004', status='available',
                unavailable_reason=None, receiver_type_id=635, current_variable_table_observed=False,
                native_receiver_selected=False, receiver_variable_index=0, declared_type_id=635,
                stable_double_read=True, entries=copy.deepcopy(rows),
                local_definition_entry_only=local())


def consume(candidate):
    expression = dict(chain_count_24_raw=0, final_type_id_30=1, final_kind_34_raw=3,
                      final_target_38_rva=0x1303D40, final_user_data_40_present=True,
                      receiver_type_id_48=635, receiver_flag_4c_raw=0, chain_calls=[],
                      receiver_entry_candidates_12004=candidate)
    callback = dict(index=0, callback_vtable_rva=0x40000, callback_slot2_rva=0x3AA30E0,
                    indirect_target_3aa30e0=dict(native_target_8_rva=0x3A9F960,
                                              receiver_f0_present=True,
                                              expression_3a9f960=expression))
    frame = dict(native_revision=9, connection_generation=2, pump_epoch=7, ticket_sequence=3,
                 game_pid=42, thread_id=43, played_character_full_id=31254, date_raw=53147928,
                 owner_thread_verified=True, frame_stable=True, gui_owner_stable=True)
    raw = dict(callback_binding_source_12004=dict(SOURCE_RECEIVER_12004), truncated=False,
               root_available=True, refill_receiver_frame_12004=frame,
               widgets=[dict(standard_click_binding_12004=dict(
                   button_base_slot13=True, group='fallback', callbacks=[callback]))])
    projected = dict(widgets=[dict(vtable_rva=0x50000)])
    result = normalize_callback_binding_rows_12004(raw, projected)
    candidate = result['widgets'][0]['standard_click_binding_12004']['callbacks'][0][
        'indirect_target_3aa30e0']['expression_3a9f960']['receiver_entry_candidates_12004']
    return candidate, result


class LocalFullConsistencyTests(unittest.TestCase):
    def test_matching_depth0_survives_with_independent_ancestor_rows(self):
        candidate = full([entry(), entry(2)])
        got, result = consume(candidate)
        self.assertEqual(got, candidate)
        self.assertFalse(result['click_action_available'])
        # Matching direct-owner fields use the same complete descriptor comparison.
        direct = entry()
        direct.update(entry_mode_40=1, direct_value_present=True, provider_present=False,
                      provider_vtable_rva=None, provider_slot2_rva=None,
                      direct_owner_full_id=31254, direct_owner_identity_verified=True)
        candidate = full([direct]); candidate['local_definition_entry_only'] = local([direct])
        self.assertEqual(consume(candidate)[0], candidate)

    def test_individually_valid_descriptor_disagreements_are_rejected(self):
        changes = [dict(provider_slot2_rva=0x2001), dict(provider_vtable_rva=0x1001),
                   dict(entry_mode_40=2), dict(entry_flag_4c=1),
                   dict(direct_value_present=True),
                   dict(provider_present=False, provider_vtable_rva=None, provider_slot2_rva=None),
                   dict(entry_mode_40=1, direct_value_present=True, provider_present=False,
                        provider_vtable_rva=None, provider_slot2_rva=None,
                        direct_owner_full_id=31254, direct_owner_identity_verified=True)]
        for change in changes:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'depth0 entries differ'):
                candidate = full()
                candidate['local_definition_entry_only']['entries'][0].update(change)
                consume(candidate)
        # Both sides stay valid direct-owner entries, but complete IDs/verification differ.
        direct = changes[-1]
        for change in (dict(direct_owner_full_id=31255), dict(direct_owner_identity_verified=False)):
            with self.subTest(direct=change), self.assertRaisesRegex(ValueError, 'depth0 entries differ'):
                candidate = full()
                candidate['entries'][0].update(direct)
                candidate['local_definition_entry_only']['entries'][0].update(direct)
                candidate['local_definition_entry_only']['entries'][0].update(change)
                consume(candidate)

    def test_no_match_and_match_cannot_contradict_each_other(self):
        for full_rows, local_rows in (([], [entry()]), ([entry()], [])):
            with self.subTest(full_rows=full_rows), self.assertRaisesRegex(ValueError, 'depth0 entries differ'):
                candidate = full(full_rows)
                candidate['local_definition_entry_only'] = local(local_rows)
                consume(candidate)
        # An ancestor candidate is compatible with an independently complete local no-match.
        candidate = full([entry(1)])
        candidate['local_definition_entry_only'] = local([])
        got, _ = consume(candidate)
        self.assertFalse(got['local_definition_entry_only']['local_entry_present'])
        self.assertEqual(got['entries'][0]['ancestor_depth'], 1)

    def test_unavailable_or_absent_other_view_does_not_create_a_false_join(self):
        repo = Path(callback_contract.__file__).resolve().parents[4]
        evidence = repo / 'docs/ck3-native-ai/evidence/r184-r06-local-prefix-12004.json'
        actual = json.loads(evidence.read_bytes())
        candidate = copy.deepcopy(actual['actual_tree']['candidate_widgets'][0]['expression'][
            'receiver_entry_candidates_12004'])
        failure = copy.deepcopy(candidate)
        candidate['local_definition_entry_only'] = local()
        got, _ = consume(candidate)
        self.assertEqual({k: v for k, v in got.items() if k != 'local_definition_entry_only'}, failure)
        self.assertEqual(got['local_definition_entry_only']['status'], 'available')
        candidate = full()
        del candidate['local_definition_entry_only']
        self.assertEqual(consume(candidate)[0], candidate)
        unknown = local()
        unknown.update(status='unavailable', unavailable_reason='local_prefix_shared_budget_exhausted',
                       stable_double_read=False, entries=[], receiver_variable_index=None,
                       declared_type_id=None, raw_definition_entry_count=None,
                       local_definition_active_raw=None, definition_present=None,
                       local_entry_present=None)
        candidate['local_definition_entry_only'] = unknown
        self.assertEqual(consume(candidate)[0], candidate)


if __name__ == '__main__':
    unittest.main()
