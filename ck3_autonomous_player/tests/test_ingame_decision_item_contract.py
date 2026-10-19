from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import unittest
from xar_autoplayer.bridge.ingame_decision_item_contract import normalize_decision_item, STEP
from xar_autoplayer.bridge.ingame_decisions_open_contract import EXE_SHA256
from xar_autoplayer.bridge.version_identity import CK3_12004

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

TERMS_KEY = 'create_hof_decision'


def selected_terms_packet():
    """Synthetic wire packet for the current production consumer, not native proof."""
    raw = actual()
    raw.update(game_version=CK3_12004.game_version,
               executable_sha256=CK3_12004.executable_sha256,
               decision_key=TERMS_KEY, detail_decision_key=TERMS_KEY,
               detail_definition_available=True, detail_definition_matches_target=True,
               detail_root_visible=True, detail_tree_complete=True,
               detail_actor_binding_verified=True,
               detail_actor_reference_key=BINDING['played_character_id'])
    raw['selected_terms'] = dict(
        schema='ck3-selected-decision-terms-v1', read_only=True,
        available=True, unavailable_reason=None,
        game_version=CK3_12004.game_version,
        executable_sha256=CK3_12004.executable_sha256,
        decision_key=TERMS_KEY, capture_epoch=99,
        date_raw=BINDING['date_raw'], played_character_id=BINDING['played_character_id'],
        context_verified=True, named_parameter_count=0,
        context_adapter='actual_empty_named_parameters_only', can_confirm=True,
        requirements_bypass_observed=True, requirements_bypass_raw=0,
        ordinary_legality_observed=True, ordinary_can_confirm=True,
        confirm_tooltip_available=True, confirm_tooltip='Synthetic confirm tooltip',
        requirements_description_available=True, requirements_description='Synthetic requirements',
        cost_description_available=True, cost_description='Synthetic cost',
        resource_quote_available=True,
        resource_quote=dict(raw_scale=100000,
                            resource_vector_raw=[15000000, 0, 20000000, 0, 0, 0, 0, 0, 0, 0],
                            native_affordable=True),
        cooldown_observed=True,
        cooldown=dict(present=False, current_counter_raw=2718, expiry_raw=None,
                      active=False, counter_unit='native_decision_clock_counter'),
        action_ready=False, decision_confirm_invoked=False)
    return raw


class SelectedDecisionTermsContractTests(unittest.TestCase):
    """Regression for a valid nested quote contradicting the actual outer detail."""

    def assert_accepts_without_mutation(self, raw):
        frozen = copy.deepcopy(raw)
        result = normalize_decision_item(raw, BINDING, TERMS_KEY)
        self.assertEqual(result, frozen)
        self.assertEqual(raw, frozen)
        self.assertIsNot(result, raw)
        return result

    def assert_rejects_outer_contradiction(self, changes):
        raw = selected_terms_packet()
        raw.update(changes)
        frozen = copy.deepcopy(raw)
        with self.assertRaisesRegex(ValueError, 'available selected terms '):
            normalize_decision_item(raw, BINDING, TERMS_KEY)
        self.assertEqual(raw, frozen)

    def test_available_terms_preserve_quote_without_action_credit(self):
        result = self.assert_accepts_without_mutation(selected_terms_packet())
        self.assertTrue(result['selected_terms']['ordinary_can_confirm'])
        self.assertFalse(result['selected_terms']['action_ready'])
        self.assertFalse(result['action_qualified'])

    def test_unavailable_terms_allow_unselected_hidden_other_actor(self):
        raw = selected_terms_packet()
        raw.update(detail_decision_key='other_decision', detail_definition_matches_target=False,
                   detail_root_visible=False, detail_tree_complete=False,
                   detail_actor_binding_verified=False,
                   detail_actor_reference_key=BINDING['played_character_id'] + 1)
        terms = raw['selected_terms']
        terms.update(available=False, unavailable_reason='selected_detail_not_qualified',
                     context_verified=False)
        for key in ('requirements_bypass_observed', 'ordinary_legality_observed',
                    'confirm_tooltip_available', 'requirements_description_available',
                    'cost_description_available', 'resource_quote_available', 'cooldown_observed'):
            terms[key] = False
        for key in ('can_confirm', 'requirements_bypass_raw', 'ordinary_can_confirm',
                    'confirm_tooltip', 'requirements_description', 'cost_description',
                    'resource_quote', 'cooldown'):
            terms[key] = None
        self.assert_accepts_without_mutation(raw)

    def test_legacy_exact4_packet_without_terms_remains_compatible(self):
        raw = selected_terms_packet()
        del raw['selected_terms']
        self.assert_accepts_without_mutation(raw)

    def test_native_false_and_unaffordable_are_valid_observations(self):
        raw = selected_terms_packet()
        raw['selected_terms'].update(can_confirm=False, ordinary_can_confirm=False)
        raw['selected_terms']['resource_quote']['native_affordable'] = False
        self.assert_accepts_without_mutation(raw)

    def test_available_terms_reject_different_selected_definition(self):
        self.assert_rejects_outer_contradiction(dict(
            detail_decision_key='other_decision', detail_definition_matches_target=False))

    def test_available_terms_reject_incomplete_hidden_detail(self):
        self.assert_rejects_outer_contradiction(dict(
            detail_tree_complete=False, detail_root_visible=False))

    def test_available_terms_reject_hidden_detail_with_complete_census(self):
        self.assert_rejects_outer_contradiction(dict(detail_root_visible=False))

    def test_available_terms_reject_false_actor_binding_with_matching_id(self):
        self.assert_rejects_outer_contradiction(dict(detail_actor_binding_verified=False))

    def test_available_terms_reject_different_full_actor_id(self):
        self.assert_rejects_outer_contradiction(dict(
            detail_actor_reference_key=BINDING['played_character_id'] + 1))

    def test_available_terms_reject_boolean_actor_reference(self):
        self.assert_rejects_outer_contradiction(dict(detail_actor_reference_key=True))

    def test_available_terms_reject_unavailable_outer_before_early_return(self):
        self.assert_rejects_outer_contradiction(dict(
            available=False, unavailable_reason='synthetic_outer_unavailable'))

    def test_generated_native_terms_packets_through_current_consumer(self):
        """Actual C++ component wire in an explicitly synthetic outer GUI model.

        The C++ fixture owns its fake memory/callbacks and serializes the leaf.
        Only the outer keyed model/revision/PID below is Python fixture-owned;
        this does not qualify the native full GUI, Driver, MCP, or live game.
        """
        wire_dir = os.environ.get('XAR_SELECTED_DECISION_TERMS_NATIVE_WIRE_DIR')
        if not wire_dir:
            self.skipTest('native component wire qualification requires its generated fixture directory')
        root = Path(wire_dir)
        expected = {
            'selected-empty-native-true.json', 'selected-native-false.json',
            'selected-signed-zero-vector.json', 'selected-bypass-nonzero.json',
            'selected-bypass-unavailable.json', 'selected-quote-unavailable.json',
            'selected-cost-text-getter-absent.json', 'selected-requirements-getter-absent.json',
            'selected-requirements-return-unavailable.json',
            'selected-definition-pointer-rejected.json',
        }
        expected.update(f'selected-entry-rejected-{i}.json' for i in range(8))
        expected.update(f'selected-freshness-rejected-{i}.json' for i in range(7))
        paths = sorted(root.glob('selected-*.json'))
        self.assertEqual({path.name for path in paths}, expected)
        # Frame() and Fixture::actor from the actual C++ producer fixture.
        binding = dict(BINDING, played_character_id=0x03000004, date_raw=53175816)
        available = unavailable = 0
        packets = {}
        for path in paths:
            with self.subTest(native_packet=path.name):
                body = path.read_bytes()
                terms = json.loads(body)
                key = 'other_decision' if path.name == 'selected-entry-rejected-5.json' else TERMS_KEY
                self.assertEqual(terms['decision_key'], key)
                self.assertEqual(terms['capture_epoch'], 17)
                outer = selected_terms_packet()
                outer.update(binding, decision_key=key, detail_decision_key=key,
                             detail_actor_reference_key=binding['played_character_id'])
                outer['selected_terms'] = terms  # Preserve the generated component verbatim.
                frozen = copy.deepcopy(outer)
                result = normalize_decision_item(outer, binding, key)
                self.assertEqual(result['selected_terms'], terms)
                self.assertEqual(outer, frozen)
                self.assertEqual(path.read_bytes(), body)
                self.assertFalse(result['selected_terms']['action_ready'])
                self.assertFalse(result['selected_terms']['decision_confirm_invoked'])
                available += terms['available'] is True
                unavailable += terms['available'] is False
                packets[path.name] = result['selected_terms']
        self.assertEqual((available, unavailable), (9, 16))
        self.assertIs(packets['selected-native-false.json']['ordinary_can_confirm'], False)
        for name in ('selected-bypass-nonzero.json', 'selected-bypass-unavailable.json'):
            self.assertIsNone(packets[name]['ordinary_can_confirm'])
        self.assertIsNone(packets['selected-quote-unavailable.json']['resource_quote'])
        self.assertEqual(packets['selected-signed-zero-vector.json']['resource_quote']['resource_vector_raw'],
                         [0, -250001, 0, 0, 0, 0, 1234567, 0, 0, 0])


if __name__ == '__main__': unittest.main()
