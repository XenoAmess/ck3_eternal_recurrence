"""New product-case guards only. Synthetic fixtures confer no CK3 credit."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = next((p for p in HERE.parents if (p / 'AGENTS.md').is_file()), None)
if REPO is None:
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--repo', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    REPO = args.repo.resolve()
    sys.argv = [sys.argv[0], *remaining]
sys.path.insert(0, str(REPO / 'tools'))
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0, str(HERE / 'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import lyd_release012_keypaths_adapter as case


def frame(actor=31254):
    return {'revision': 8, 'native_revision': 7, 'snapshot_id': 'native:7',
        'date_raw': 53144712, 'paused': True, 'active_event': None,
        'played_character': {'character_id': actor, 'alive': True},
        'diagnostics': {'bridge_pid': 4321, 'connection_generation': 1}}


def event_packet():
    f = frame()
    f['active_event'] = {'instance_id': 101, 'options': [
        {'index': 0, 'option_number': 1, 'enabled': True},
        {'index': 1, 'option_number': 2, 'enabled': True}]}
    event = {'schema': 'current-event-window-context-v1', 'status': 'available',
        'window_match_count': 1, 'event_definition_key': 'lyd.1032',
        'current_event_instance_id': 101, 'snapshot_revision': 7, 'date_raw': 53144712,
        'root_scope': {'typed_identity': {'character_id': 31254}},
        'readiness': {k: True for k in ('event_definition_identity_ready', 'root_scope_ready',
            'saved_scopes_ready', 'option_presentation_ready')},
        'options': [{'native_option_index': 0, 'rendered_index': 0, 'shown': True, 'enabled': True},
                    {'native_option_index': 2, 'rendered_index': 1, 'shown': True, 'enabled': True}]}
    return {'frame': f, 'event': event}


class Client:
    operator_reviewer = '/root'

    def __init__(self, evidence=None, responses=None, current=None):
        self.current = copy.deepcopy(current or frame())
        self.evidence = evidence
        self.responses = list(responses or [])
        self.steps, self.requests = [], []
        self.reserves = []

    def snapshot(self, **kwargs):
        return copy.deepcopy(self.current)

    def validate_frame(self, value, **kwargs):
        case.binding(value)
        return value

    def execute_plan(self, steps, name):
        self.steps.extend(copy.deepcopy(steps))
        step = steps[0]
        key, tool = step['args'].get('decision_key'), step['tool']
        if tool == 'ck3_query_ingame_decision_item_v1':
            result = {'schema': 'ck3-ingame-decision-item-v1', 'read_only': True,
                'available': True, 'decision_key': key, 'game_pid': 4321,
                'connection_generation': 1, 'played_character_id': self.current['played_character']['character_id'],
                'date_raw': self.current['date_raw'], 'native_revision': self.current['native_revision']}
            result.update({k: True for k in ('owner_thread_verified', 'frame_verified',
                'source_abi_pins_verified', 'gui_owner_binding_verified', 'decisions_tree_complete',
                'decisions_root_visible', 'row_owner_verified')})
        elif tool == 'ck3_select_ingame_decision_item_v1':
            result = {'decision_key': key, 'action': 'select',
                'status': 'acknowledged_verification_pending', 'postcondition_verified': False}
        elif tool == case.EVENT:
            result = {'status': 'available', 'queried_revision': 8,
                'queried_native_revision': 7, 'queried_snapshot_id': 'native:7',
                'current_event_window_context': copy.deepcopy(self.typed)}
        else:
            result = {'accepted': True}
        return [{'id': step['id'], 'ok': True, 'result': result,
                 'after_snapshot': copy.deepcopy(self.current)}]

    def root_checkpoint(self, name, request, reserve=600):
        self.requests.append(copy.deepcopy(request))
        self.reserves.append(reserve)
        response = self.responses.pop(0)
        return {'run_id': 'SYNTHETIC', 'reviewer': '/root', **response}


class Release012Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        evidence = self.root / 'synthetic-review.txt'
        evidence.write_text('Offline only, not actual game evidence', encoding='utf-8')
        self.ref = case.pin(evidence)
        self.context = {'run_id': 'SYNTHETIC', 'output': str(self.root)}

    def test_actual_selected_identity_dynamic_but_cannot_switch_or_be_bool(self):
        for actor in (31254, 29829, 88888):
            self.assertEqual(case.binding(frame(actor))['actor'], actor)
        initial = case.binding(frame())
        with self.assertRaises(ValueError):
            case.same_scene(initial, frame(29829))
        with self.assertRaises(ValueError):
            case.binding(frame(True))

    def test_decision_navigation_pending_ACK_is_not_confirmation(self):
        client = Client()
        case.navigate(client, case.binding(frame()), 'test', 'lyd_enter_decision')
        self.assertEqual(len(client.steps), 3)
        self.assertTrue(all(s['fresh_revision'] is False and s['args']['expected_revision'] == 8
                            for s in client.steps))
        self.assertFalse(any('confirm' in s['tool'] or 'select_event_option' in s['tool'] for s in client.steps))

    def test_option_number_uses_actual_rendered_mapping_not_native_index(self):
        packet = event_packet()
        args, key = case.option_arguments(packet,
            {'event_definition_key': 'lyd.1032', 'native_option_index': 2}, {'lyd.1032': [2]}, set())
        self.assertEqual(args['option_number'], 2)
        self.assertEqual(key, (101, 2))
        self.assertEqual(args['expected_revision'], 8)

    def test_disabled_wrong_definition_and_consumed_choices_rejected(self):
        packet = event_packet()
        choice = {'event_definition_key': 'lyd.1032', 'native_option_index': 0}
        for changed, request, consumed in (
            (packet, {**choice, 'event_definition_key': 'lyd.1000'}, set()),
            (packet, choice, {(101, 0)}),
            (packet, {**choice, 'native_option_index': True}, set())):
            with self.assertRaises(ValueError):
                case.option_arguments(changed, request, {'lyd.1032': [0]}, consumed)
        packet['event']['options'][0]['enabled'] = False
        with self.assertRaises(ValueError):
            case.option_arguments(packet, choice, {'lyd.1032': [0]}, set())

    def test_factory_native0_cannot_bypass_actual_commit_admission(self):
        packet = event_packet()
        packet['event']['event_definition_key'] = 'lyd.430'
        request = {'event_definition_key': 'lyd.430', 'native_option_index': 0}
        with self.assertRaises(ValueError):
            case.option_arguments(packet, request, {'lyd.430': [0]}, set())
        args, _ = case.option_arguments(packet, request, {'lyd.430': [0]}, set(), commit_admitted=True)
        self.assertEqual(args['event_instance_id'], 101)

    def test_typed_context_requires_current_revision_and_actual_root(self):
        packet = event_packet()
        client = Client(current=packet['frame'])
        client.typed = packet['event']
        case.current_event(client, case.binding(frame()), 'typed-good')
        for field, value in (('snapshot_revision', 6), ('date_raw', 53144736)):
            client.typed = {**packet['event'], field: value}
            with self.assertRaises(ValueError):
                case.current_event(client, case.binding(frame()), 'typed-bad-' + field)
        client.typed = {**packet['event'], 'root_scope': {'typed_identity': {'character_id': 29829}}}
        with self.assertRaises(ValueError):
            case.current_event(client, case.binding(frame()), 'typed-bad-root')

    def test_partial_fact_does_not_become_PASS_and_abort_is_explicit(self):
        phase = {'id': 'T03', 'requirements': ['actual_cost_readback'], 'instructions': 'Review',
                 'maximum_option_actions': 1}
        for status, facts in [('complete', {'actual_cost_readback': False}), ('partial', {}), ('abort', {})]:
            client = Client(responses=[{'status': status, 'facts': facts, 'evidence': [self.ref]}])
            result = case.review_cell(self.context, client, case.binding(frame()), phase, set())
            self.assertFalse(result['qualified'])
            self.assertEqual(result['status'], status)
            self.assertEqual(client.steps, [])

    def test_new_head_needs_distinct_real_title_law_properties_and_ordered_cache(self):
        before = {'cache': [11, 22], 'title': {'legal_head_title_absent': True, 'head_title_full_id': None}}
        after = {'cache': [11, 22], 'title': {'head_title_full_id': 12345, 'legal_head_title_absent': False,
            'graph_available': True, 'faith_full_id': 107, 'native_title_holder_full_id': 31254,
            'title_properties': {'available': True, **{k: True for k in case.PROPERTIES}},
            'title_laws': {'available': True, 'temporal_head_of_faith_succession_law_member': True,
                'complete_laws': [{'native_definition_id': 95, 'key': 'temporal_head_of_faith_succession_law'}]}}}
        self.assertTrue(case.head_qualified(before, after, 31254, 107))
        for changed in ('cache', 'holder', 'property', 'law'):
            bad = copy.deepcopy(after)
            if changed == 'cache': bad['cache'].reverse()
            if changed == 'holder': bad['title']['native_title_holder_full_id'] = 29829
            if changed == 'property': bad['title']['title_properties'][case.PROPERTIES[0]] = False
            if changed == 'law': bad['title']['title_laws']['complete_laws'] = []
            self.assertFalse(case.head_qualified(before, bad, 31254, 107))

    def test_config_preserves_real_zero_day_and_no_second_stage_or_fixture_mandate(self):
        data = json.loads((HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths.json').read_text())
        self.assertIsNone(data['expected_actor_character_id'])
        self.assertEqual(data['maximum_natural_days'], 0)
        self.assertEqual(data['fixture_emitter']['path'], 'tools/prepare_lyd_vanilla_feedback_fixture.py')
        T33 = next(p for p in data['phases'] if p['id'] == 'T33')
        self.assertNotIn(1, T33['allowed_options']['lyd.1032'])
        self.assertFalse(next(p for p in data['phases'] if p['id'] == 'institution')['required'])
        self.assertNotIn('29829', (HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths_adapter.py').read_text())

    def configured_context(self, name):
        config = json.loads((HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths.json').read_text())
        output = self.root / name
        contract = output / 'state/profile/mod-content/fixture/_case_contract.json'
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps({'product': 'li-yu-dao', 'case': case.CASE, 'config': config}))
        return config, {**self.context, 'output': str(output), 'product': 'li-yu-dao',
                        'case': case.CASE, 'state_dir': str(output / 'state')}

    def test_confirmed_entry_catalogue_false_or_unknown_and_resource_partial_continue(self):
        key = 'all36_distinct_tenets_visible_in_original_personal_belief_catalogue'
        for observed_catalogue in (False, None):
            config, context = self.configured_context('catalogue-' + str(observed_catalogue))
            entry = next(p for p in config['phases'] if p['id'] == 'entry')
            self.assertEqual(len(entry['requirements']), 4)
            self.assertNotIn(key, entry['requirements'])
            responses = []
            for phase in config['phases']:
                facts = {k: True for k in phase['requirements']}
                if phase['id'] == 'entry' and observed_catalogue is not None:
                    facts[key] = observed_catalogue
                status = ('skip' if phase['id'] == 'institution' else 'partial'
                          if phase['id'] in {'personal_T01', 'T01', 'T33'} else 'complete')
                responses.append({'status': status, 'facts': facts, 'evidence': [self.ref],
                                  'reason': 'Actual resource/slot/elector requirement unavailable'})
            client = Client(responses=responses)
            with patch.object(case, 'religion', side_effect=[{'faith_id': 107, 'rite_id': 1},
                    {'faith_id': 107, 'rite_id': 2}]), patch.object(case, 'navigate', return_value={}), \
                    patch.object(case, 'native_head_bundle') as bundle:
                result = case.run_case(context, client)
            cells = {c['phase']: c for c in result['cells']}
            self.assertEqual(list(cells), [p['id'] for p in config['phases']])
            self.assertTrue(cells['entry']['qualified'])
            self.assertIs(cells['entry']['optional_observations'][key], observed_catalogue)
            self.assertTrue(cells['T03']['qualified'])
            self.assertFalse(cells['T01']['qualified'])
            self.assertFalse(result['case_contract_qualified'])
            self.assertFalse(result['all36_live_effect_credit'])
            self.assertFalse(result['whole_product_release_pass'])
            self.assertEqual(client.reserves, [600] * len(config['phases']))
            bundle.assert_not_called()

    def test_actual_entry_faith_or_rite_failure_still_stops(self):
        for label, enrolled in [('faith', {'faith_id': 108, 'rite_id': 2}),
                                ('rite', {'faith_id': 107, 'rite_id': 1})]:
            config, context = self.configured_context('bad-' + label)
            responses = [{'status': 'complete', 'facts': {k: True for k in p['requirements']},
                          'evidence': [self.ref]} for p in config['phases'][:2]]
            client = Client(responses=responses)
            with patch.object(case, 'religion', side_effect=[{'faith_id': 107, 'rite_id': 1}, enrolled]), \
                    patch.object(case, 'navigate', return_value={}), \
                    patch.object(case, 'native_head_bundle') as bundle:
                result = case.run_case(context, client)
            self.assertEqual([c['phase'] for c in result['cells']], ['baseline', 'entry'])
            self.assertFalse(result['cells'][-1]['qualified'])
            self.assertFalse(result['case_contract_qualified'])
            bundle.assert_not_called()

    def test_institution_skip_or_complete_without_enter_never_saves_or_qualifies(self):
        config = json.loads((HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths.json').read_text())
        phase = next(p for p in config['phases'] if p['id'] == 'institution')
        for status in ('skip', 'complete'):
            client = Client(responses=[{'status': status,
                'facts': {k: True for k in phase['requirements']}, 'evidence': [self.ref]}])
            with patch.object(case, 'native_head_bundle') as bundle:
                result = case.review_cell(self.context, client, case.binding(frame()), phase, set())
            self.assertFalse(result['qualified'])
            self.assertIsNone(result['actual_initial_political_bundle'])
            self.assertEqual(client.steps, [])
            bundle.assert_not_called()

    def test_institution_enter_precedes_actions_and_returns_once_initial_and_signed_bundles(self):
        config = json.loads((HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths.json').read_text())
        phase = next(p for p in config['phases'] if p['id'] == 'institution')
        initial = {'cache': [11, 22], 'title': {'legal_head_title_absent': True}, 'save': {'name': 'initial'}}
        signed = {**initial, 'save': {'name': 'signed'}}
        statuses = ['choose_option', 'read_precommit', 'admit_commit', 'enter_institution',
                    'enter_institution', 'read_precommit', 'complete']
        responses = [{'status': s, 'evidence': [self.ref],
            'facts': {k: True for k in phase['requirements']}} for s in statuses]
        client = Client(responses=responses)
        with patch.object(case, 'native_head_bundle', side_effect=[initial, signed]) as bundle:
            result = case.review_cell(self.context, client, case.binding(frame()), phase, set())
        self.assertEqual(bundle.call_count, 2)
        self.assertTrue(bundle.call_args_list[0].args[-1].endswith('-0004-initial'))
        self.assertTrue(bundle.call_args_list[1].args[-1].endswith('-0006-signed-precommit'))
        self.assertEqual(result['actual_initial_political_bundle'], initial)
        self.assertEqual(result['fresh_signed_precommit_bundle'], signed)
        self.assertFalse(result['factory_submitted_by_adapter'])
        self.assertEqual(client.steps, [])
        self.assertIn('before production actions', client.requests[1]['last_contract_error'])
        self.assertIn('once-only', client.requests[5]['last_contract_error'])
        self.assertTrue(all(r == 600 for r in client.reserves))

    def test_complete_representatives_never_invent_optional_HoF_cold_or_whole_PASS(self):
        config = json.loads((HERE / 'ck3_mod_acceptance_cases/lyd_release012_keypaths.json').read_text())
        contract = self.root / 'state/profile/mod-content/fixture/_case_contract.json'
        contract.parent.mkdir(parents=True)
        contract.write_text(json.dumps({'product': 'li-yu-dao', 'case': case.CASE, 'config': config}))
        context = {**self.context, 'product': 'li-yu-dao', 'case': case.CASE,
                   'state_dir': str(self.root / 'state')}
        responses = [{'status': 'skip'} if p['id'] == 'institution' else
            {'status': 'complete', 'facts': {k: True for k in p['requirements']}, 'evidence': [self.ref]}
            for p in config['phases']]
        client = Client(responses=responses)
        observed = iter([{'faith_id': 107, 'rite_id': 1}, {'faith_id': 107, 'rite_id': 2},
                         {'personal_tenet_keys': ['lyd_tenet_reverent_heaven']}])
        with patch.object(case, 'religion', side_effect=lambda *a, **k: next(observed)), \
             patch.object(case, 'navigate', return_value={}), \
             patch.object(case, 'native_head_bundle', return_value={'cache': [], 'title': {}, 'save': {}}):
            result = case.run_case(context, client)
        self.assertTrue(result['case_contract_qualified'])
        self.assertIsNone(result['new_head_title_id'])
        self.assertFalse(result['formal_B4_B5_C3_credit'])
        self.assertFalse(result['full_T33_second_stage_credit'])
        self.assertFalse(result['whole_product_release_pass'])
        verified = case.verify_case(context)
        self.assertTrue(verified['case_contract_qualified'])
        self.assertFalse(verified['business_pass'])


if __name__ == '__main__':
    unittest.main()
