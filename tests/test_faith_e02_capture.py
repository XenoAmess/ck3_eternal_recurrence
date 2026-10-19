"""Finite no-game tests for B1's scope, native-readback requirement and profile."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import faith_e02_capture_queue as queue
from ck3_mod_acceptance_cases import faith_e02_readonly_adapter as adapter


def step(tool, args=None, name='sample', **extra):
    return {'id': name, 'tool': tool, 'args': args or {}, 'continue_on_error': True,
            'fresh_revision': True, **extra}


def contract(save='C:/fixture/C2.ck3'):
    return {'schema': 'faith-engine-e02-saved-readonly-case-v1', 'machine_id': 'unit-fixture-not-a-machine',
            'product': adapter.PRODUCT, 'case': adapter.CASE,
            'saved_input': {'save': save, **adapter.SAVED_IDENTITY},
            'profile': {'enabled_mods': [], 'product_files': []},
            'scope': {'world_confirmation_allowed': False, 'day_advance_allowed': False,
                      'new_save_allowed': False, 'ordinary_campaign_credit': False,
                      'preparation_mod_mounted': False}}


def context(value):
    return {'product': adapter.PRODUCT, 'case': adapter.CASE, 'case_contract': value,
            'case_spec': {'required_mcp_tools': sorted(adapter.REQUIRED_TOOLS),
                          'opt_in_read_only_mcp_tools': sorted(adapter.READONLY_TOOLS),
                          'opt_in_holy_site_creation_ui': True,
                          'opt_in_holy_site_creation_create_once': False,
                          'opt_in_holy_site_relic_actions': False,
                          'opt_in_player_rite_creation_actions': False,
                          'initial_plan': 'fixture-initial.json'}}


class CapturePolicyTests(unittest.TestCase):
    def test_fresh_selector_and_readback_omit_revision_for_public_dispatch_binding(self):
        selector = step('ck3_select_holy_site_creation_type_v1', {'type_key': 'site_of_wisdom'})
        readback = step(queue.CREATION_QUERY, {}, 'later')
        plan = {'steps': [selector, readback]}
        queue.validate(plan)
        self.assertNotIn('expected_revision', selector['args'])
        self.assertNotIn('expected_revision', readback['args'])
        for index in (0, 1):
            bad = copy.deepcopy(plan)
            bad['steps'][index]['fresh_revision'] = False
            with self.subTest(index=index), self.assertRaises(ValueError):
                queue.validate(bad)
        with self.assertRaises(ValueError):
            queue.validate({'steps': [step(queue.CREATION_QUERY, {'expected_revision': None})]})

    def test_each_selector_requires_independent_fresh_context(self):
        actions = [
            ('ck3_open_holy_site_creation_window_v1', {}),
            ('ck3_select_holy_site_creation_type_v1', {'type_key': 'site_of_miracles'}),
            ('ck3_select_holy_site_creation_barony_v1', {'barony_title_id': 0}),
            ('ck3_set_holy_site_creation_artifact_selection_v1', {'artifact_id': 237, 'selected': True}),
        ]
        for tool, fields in actions:
            with self.subTest(tool=tool):
                action = step(tool, {'expected_revision': 3, **fields})
                readback = step(queue.CREATION_QUERY, {'expected_revision': 3}, 'later')
                self.assertFalse(queue.validate({'steps': [action, readback]})['native_legality_or_readback_success_inferred'])
                with self.assertRaisesRegex(ValueError, 'independent readback'):
                    queue.validate({'steps': [action]})
                readback['fresh_revision'] = False
                with self.assertRaisesRegex(ValueError, 'matching fresh'):
                    queue.validate({'steps': [action, readback]})

    def test_world_event_save_and_lifecycle_routes_refused(self):
        tools = ['ck3_create_holy_site_once_v1', 'ck3_confirm_holy_site_decision_v1',
                 'ck3_confirm_holy_site_adoption_decision_v1', 'ck3_save_checkpoint',
                 'ck3_select_event_option', 'ck3_execute_step', 'ck3_enshrine_holy_site_relic_v1',
                 'ck3_execute_player_rite_creation_action_v1', 'ck3_request_normal_exit_v1']
        for tool in tools:
            with self.subTest(tool=tool), self.assertRaises(ValueError):
                queue.validate({'steps': [step(tool)]})
        for kind in ['advance_day', 'finish_hold', 'tool-unchecked']:
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                queue.validate({'steps': [step('ck3_take_snapshot', kind=kind)]})

    def test_hidden_fields_bad_ids_booleans_and_unsupported_type_refused(self):
        base = step('ck3_select_holy_site_creation_type_v1', {'expected_revision': 3, 'type_key': 'site_of_wisdom'})
        later = step(queue.CREATION_QUERY, {'expected_revision': 3}, 'later')
        for changes in [dict(args={**base['args'], 'confirm': True}), dict(arguments={}),
                        dict(args={'expected_revision': True, 'type_key': 'site_of_wisdom'}),
                        dict(args={'expected_revision': 3, 'type_key': 'arbitrary_type'}),
                        dict(continue_on_error=False)]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                queue.validate({'steps': [{**base, **changes}, later]})
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            queue.validate({'steps': [step('ck3_take_snapshot'), step('ck3_get_capabilities')]})

    def test_faith_page_and_tooltip_close_are_observed_not_acknowledged(self):
        page = step('ck3_open_faith_window_v1', {'faith_id': 50, 'expected_revision': 3})
        readback = step('ck3_query_ingame_ui_window_v1', {'window_kind': 'faith', 'expected_revision': 3}, 'later')
        queue.validate({'steps': [page, readback]})
        readback['args']['window_kind'] = 'holy_site_creation'
        with self.assertRaises(ValueError):
            queue.validate({'steps': [page, readback]})
        receipt = 'a' * 32
        close = step('ck3_present_faith_power_ui_v1', {'expected_revision': 3, 'window_kind': 'tooltips',
                     'subject_id': 0, 'operation': 'close_tooltips', 'presentation_receipt': receipt})
        query = step('ck3_query_faith_power_ui_v1', {'expected_revision': 3, 'window_kind': 'tooltips',
                     'subject_id': 0, 'presentation_receipt': receipt}, 'later')
        queue.validate({'steps': [close, query]})
        close['args']['operation'] = 'open_clerical_preview'
        with self.assertRaises(ValueError):
            queue.validate({'steps': [close, query]})


class SavedCaptureTests(unittest.TestCase):
    def test_contract_blocks_missing_selector_extra_world_tool_and_enabled_action_lane(self):
        value = context(contract())
        adapter.validate_contract(value)
        bad = copy.deepcopy(value)
        bad['case_spec']['required_mcp_tools'].remove('ck3_select_holy_site_creation_barony_v1')
        with self.assertRaisesRegex(ValueError, 'four selectors'):
            adapter.validate_contract(bad)
        for change in ['ck3_create_holy_site_once_v1', 'ck3_save_checkpoint']:
            bad = copy.deepcopy(value); bad['case_spec']['required_mcp_tools'].append(change)
            with self.assertRaises(ValueError):
                adapter.validate_contract(bad)
        bad = copy.deepcopy(value); bad['case_spec']['opt_in_holy_site_creation_create_once'] = True
        with self.assertRaisesRegex(ValueError, 'selectors only'):
            adapter.validate_contract(bad)

    def test_frame_rejects_date_event_actor_pause_drift(self):
        value = contract()
        frame = {'paused': True, 'active_event': None, 'date_raw': 51394920,
                 'played_character': {'character_id': 15893}}
        adapter.validate_capture_frame(frame, value)
        for update in [{'paused': False}, {'active_event': {'instance_id': 8}}, {'date_raw': 51394944},
                       {'played_character': {'character_id': 31254}}]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                adapter.validate_capture_frame({**frame, **update}, value)

    def test_real_common_profile_is_vanilla_and_emits_no_fixture_or_startup_policy(self):
        with tempfile.TemporaryDirectory(prefix='faith-e02-profile-') as directory:
            root = Path(directory); save = root / 'C2.ck3'; save.write_bytes(b'unit-only saved input')
            identity = {'bytes': save.stat().st_size, 'sha256': adapter.pin(save)['sha256'],
                        'player_id': 15893, 'date_raw': 51394920}
            admission = root / 'admission.json'
            admission.write_text(json.dumps({'machine_id': 'unit-fixture-not-a-machine', 'active': True,
                'expires_at_utc': (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()}))
            config = {}
            for number, relative in enumerate(('pdx_settings.txt', 'tutorial.txt', 'presets.txt', 'player/game_rules/presets.txt')):
                path = root / ('config' + str(number)); path.write_bytes(b'')
                config[relative] = adapter.pin(path)
            output = root / 'prepare'; output.mkdir()
            with mock.patch.dict(adapter.SAVED_IDENTITY, identity, clear=True):
                value = context(contract(str(save)))
                value.update(saved_campaign=dict(value['case_contract']['saved_input']), state_dir=str(root / 'state'),
                             output=str(output), case_inputs={'storage_admission': adapter.pin(admission), 'configuration': config},
                             _selected_engine=(object(), {'game_version': 'fixture-only', 'exe_sha256': '0' * 64}))
                with mock.patch('ck3_live_run_id.current_machine_id', return_value='unit-fixture-not-a-machine'):
                    result = adapter.prepare_case(value)
            profile = Path(result['profile']['profile'])
            self.assertEqual(json.loads((profile / 'dlc_load.json').read_text()), {'enabled_mods': [], 'disabled_dlcs': []})
            self.assertFalse((profile / 'mod').exists())
            self.assertFalse((profile / 'mod-content').exists())
            self.assertFalse((output / 'frontend-fixture-start-policy.json').exists())
            self.assertFalse(result['business_pass'])
            self.assertEqual(result['startup']['saved_campaign']['player_id'], 15893)


if __name__ == '__main__':
    unittest.main()
