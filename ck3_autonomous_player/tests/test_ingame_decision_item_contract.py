from __future__ import annotations
import copy
import unittest
from xar_autoplayer.bridge.ingame_decision_item_contract import normalize_decision_item, STEP
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256

KEY = 'ervc_courtier_creator_decision'
BINDING = dict(native_revision=32, connection_generation=7, game_pid=8800,
               played_character_id=731, date_raw=9001)

def actual():
    return dict(schema='ck3-ingame-decision-item-v1', step=STEP, read_only=True,
        game_version='1.20.0.3', executable_sha256=EXE_SHA256, available=True,
        **BINDING, owner_thread_verified=True, frame_verified=True,
        source_abi_pins_verified=True, gui_owner_binding_verified=True,
        decisions_tree_complete=True, decisions_root_visible=True, row_owner_verified=True,
        row_scope_reference_available=True, group_count=7, row_count=21, matching_row_count=1,
        row_context_reference_key=0xFF00731, decision_key=KEY,
        detail_tree_complete=True, detail_root_visible=False, detail_definition_available=False,
        detail_definition_matches_target=False, detail_decision_key='',
        row_widget_datacontext_verified=False, action_qualified=False, unavailable_reason='')

class DecisionItemContractTests(unittest.TestCase):
    def test_actual_model_key_and_opaque_scope_key_are_observed(self):
        raw = actual()
        result = normalize_decision_item(raw, BINDING, KEY)
        self.assertEqual(result, raw)
        self.assertIsNot(result, raw)
        self.assertNotEqual(result['row_context_reference_key'], BINDING['played_character_id'])
        self.assertFalse(result['action_qualified'])

    def test_unavailable_preserves_actual_reason_without_credit(self):
        raw = actual(); raw.update(available=False, unavailable_reason='actual_keyed_decision_model_or_owner_unstable')
        self.assertEqual(normalize_decision_item(raw, BINDING, KEY), raw)

    def test_wrong_actual_key_or_duplicate_model_row_is_rejected(self):
        for key, value in [('decision_key', 'different_decision'), ('matching_row_count', 2)]:
            raw = actual(); raw[key] = value
            with self.assertRaises(ValueError): normalize_decision_item(raw, BINDING, KEY)

    def test_wrong_binding_or_boolean_native_number_is_rejected(self):
        for key in BINDING:
            for value in [BINDING[key]+1, True]:
                raw = actual(); raw[key] = value
                with self.assertRaises(ValueError): normalize_decision_item(raw, BINDING, KEY)

    def test_missing_owner_pin_or_complete_actual_census_is_rejected(self):
        for key in ['owner_thread_verified', 'source_abi_pins_verified', 'gui_owner_binding_verified',
                    'frame_verified', 'decisions_tree_complete', 'row_owner_verified']:
            raw = actual(); raw[key] = False
            with self.assertRaises(ValueError): normalize_decision_item(raw, BINDING, KEY)

    def test_action_credit_or_inconsistent_selected_definition_is_rejected(self):
        for key in ['action_qualified', 'row_widget_datacontext_verified', 'detail_definition_matches_target']:
            raw = actual(); raw[key] = True
            with self.assertRaises(ValueError): normalize_decision_item(raw, BINDING, KEY)
        raw = actual(); raw.update(detail_definition_available=True, detail_decision_key=KEY,
                                  detail_definition_matches_target=True, detail_root_visible=True,
                                  detail_tree_complete=True)
        self.assertTrue(normalize_decision_item(raw, BINDING, KEY)['detail_definition_matches_target'])
        raw['detail_tree_complete'] = False
        with self.assertRaises(ValueError): normalize_decision_item(raw, BINDING, KEY)

if __name__ == '__main__': unittest.main()
