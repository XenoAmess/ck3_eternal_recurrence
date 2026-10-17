"""Byte-exact movement checks for an unproven two-phase PAM candidate.

Static only: early actor availability and slot-cache refresh between the
engine's two startup hooks still require an actual qualified D0 observation.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from test_ck3_mod_acceptance_xqol_minimal_scope import (
    restore_minimal_sample, restore_minimal_plan, restore_minimal_pam_contract)
from test_ck3_mod_acceptance_xqol_prepare_compatibility import PREVIOUS_PREPARE, SUPPORT_KEY

HERE = Path(__file__).resolve().parent
CASES = HERE / 'ck3_mod_acceptance_cases'
DATA = CASES / 'xqol_followup_cases/pam_positive'
SAMPLE_KEY = 'xqol_followup_cases/pam_positive/fixture/common/scripted_effects/zqp_pam_sample_effects.txt'
EVENTS_KEY = 'xqol_followup_cases/pam_positive/fixture/events/zqp_pam_events.txt'
HOOK_KEY = 'xqol_followup_cases/pam_positive/fixture/common/on_action/zqp_startup_on_actions.txt'
OLD_SAMPLE = {'bytes': 20593, 'sha256': '9d59d37136125367b5219988a65e33391ad8b9d1f40e732fa5c53072f62544da'}
OLD_EVENTS = {'bytes': 222, 'sha256': 'dd40084261bf225244ff7db4d8fe749065a054e63a813495c0b5c01c328e26e7'}
OLD_CONTRACT = {'bytes': 5217, 'sha256': 'eb44bc2e1c9b352e67749b8bc2f5040ab0c82b8298f2497023f2e95448fce910'}
OLD_HOOK = {'bytes': 205, 'sha256': 'd4995251d275b8c956f9da48731a9a5a92066a29a0a9e1054c6daa657f800b7f'}
PRIOR_REGION = rb'(?ms)^# ZQP80_MOVED_ORIGINAL_PRIOR_BEGIN\n(.*?)^# ZQP80_MOVED_ORIGINAL_PRIOR_END\n'
SUFFIX_REGION = rb'(?ms)^# ZQP80_MOVED_ORIGINAL_SUFFIX_BEGIN\n(.*?)^# ZQP80_SYNCHRONOUS_SUFFIX_END\n'
TWO_PHASE_REGION = rb'(?ms)^# ZQP80_EARLY_PRIOR_BEGIN\n.*?^# ZQP80_SYNCHRONOUS_SUFFIX_END\n'
DIAGNOSTIC_REGION = rb'(?ms)^# ZQP78_BOUNDARY_DIAGNOSTIC_ONLY_BEGIN read_only_helper\n.*?^# ZQP78_BOUNDARY_DIAGNOSTIC_ONLY_END read_only_helper\n'
EVENT_REGION = rb'(?ms)^# ZQP78_BOUNDARY_CANDIDATE_EVENT_BEGIN\n.*?^# ZQP78_BOUNDARY_CANDIDATE_EVENT_END\n'


def remove_one(raw, pattern):
    restored, count = re.subn(pattern, b'', raw)
    if count != 1:
        raise ValueError('Expected exactly one reviewed candidate region')
    return restored


def restore_pre_boundary_sample(raw):
    raw = restore_minimal_sample(raw)
    # Reconstruct from the actual moved bytes, not from a stored replacement.
    priors = re.findall(PRIOR_REGION, raw)
    suffixes = re.findall(SUFFIX_REGION, raw)
    if len(priors) != 1 or len(suffixes) != 1:
        raise ValueError('Expected one original prior and one original suffix')
    prior = priors[0]
    private_remove = b'every_personal_tenet = { scope:zqp_early_song = { remove_personal_tenet = prev } }'
    if prior.count(private_remove) != 1:
        raise ValueError('Expected the one scope-equivalent early remove-all')
    prior = prior.replace(private_remove, private_remove.replace(b'zqp_early_song', b'actor'), 1)
    restored, count = re.subn(TWO_PHASE_REGION, lambda _: b'zqp_setup_positive_effect = {\n' + prior + suffixes[0], raw)
    if count != 1:
        raise ValueError('Expected exactly one two-phase candidate region')
    return remove_one(restored, DIAGNOSTIC_REGION)


def restore_pre_boundary_events(raw):
    return remove_one(raw, EVENT_REGION)


def restore_pre_boundary_contract(value):
    restored = restore_minimal_pam_contract(value)
    restored['support_files'][SAMPLE_KEY] = copy.deepcopy(OLD_SAMPLE)
    restored['support_files'][EVENTS_KEY] = copy.deepcopy(OLD_EVENTS)
    restored['support_files'][HOOK_KEY] = copy.deepcopy(OLD_HOOK)
    return restored


class TwoPhaseCandidate(unittest.TestCase):
    def check_pin(self, raw, expected):
        self.assertEqual(len(raw), expected['bytes'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), expected['sha256'])

    def test_sample_inverse_restores_entire_original_not_just_business_fragments(self):
        raw = (CASES / SAMPLE_KEY).read_bytes()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        restored = restore_pre_boundary_sample(raw)
        self.check_pin(restored, OLD_SAMPLE)
        # Any weakening in the moved suffix still changes the reconstructed pin.
        altered = raw.replace(b'free_personal_tenet_slots >= 2 }\n  set_personal_tenet',
                              b'free_personal_tenet_slots >= 1 }\n  set_personal_tenet', 1)
        self.assertNotEqual(altered, raw)
        self.assertNotEqual(hashlib.sha256(restore_pre_boundary_sample(altered)).hexdigest(),
                            OLD_SAMPLE['sha256'])

    def test_two_hooks_execute_prior_and_suffix_once_without_hidden_startup_dispatch(self):
        from xqol_vanilla_contract import block
        raw = (CASES / EVENTS_KEY).read_bytes()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        self.check_pin(restore_pre_boundary_events(raw), OLD_EVENTS)
        event = block(raw.decode('utf-8-sig'), 'zqp120.3')
        self.assertEqual(event, 'zqp120.3 = { type = character_event hidden = yes immediate = { zqp_complete_positive_setup_after_slot_boundary_effect = yes } }')
        text = (CASES / SAMPLE_KEY).read_bytes().decode('utf-8-sig')
        hook = (CASES / HOOK_KEY).read_bytes().decode('utf-8-sig')
        early = block(text, 'zqp_prepare_positive_prior_early_effect')
        setup = block(text, 'zqp_setup_positive_effect')
        suffix = block(text, 'zqp_complete_positive_setup_after_slot_boundary_effect')
        self.assertIn('on_game_start = { on_actions = { zqp120_early_start } }', hook)
        self.assertIn('character:han_8052 = { zqp_prepare_positive_prior_early_effect = yes }', hook)
        self.assertIn('on_game_start_after_lobby = { on_actions = { zqp120_start } }', hook)
        self.assertIn('random_player = { zqp_initialize_effect = yes }', hook)
        self.assertEqual(hook.count('ZQP120: TEST BEGIN engine_startup'), 1)
        self.assertNotIn('trigger_event', hook)
        self.assertNotIn('id = zqp120.1', text)
        self.assertNotIn('id = zqp120.3', text)
        self.assertNotIn('delayed =', text)
        self.assertNotIn('set_personal_tenet', setup)
        self.assertNotIn('zqp_seed_one_async_reply_effect = yes', setup)
        for original_prior in ('set_character_faith = faith:nestorian',
                               'set_character_rite = rite:nestorian',
                               'set_piety_level = { value = 4 }',
                               'modifier = zqp_controlled_personal_slot_modifier years = 1'):
            self.assertEqual(early.count(original_prior), 1)
            self.assertNotIn(original_prior, setup)
            self.assertNotIn(original_prior, suffix)
        self.assertIn('NOT = { has_character_flag = zqp_positive_prior_initialized }', early)
        self.assertEqual(early.count('add_character_flag = zqp_positive_prior_initialized'), 1)
        self.assertIn('limit = { has_pam_dlc_trigger = yes free_personal_tenet_slots = 1 }', early)
        self.assertIn('scope:zqp_early_song = { remove_personal_tenet = prev }', early)
        for forbidden in ('set_player_character', 'random_player', 'set_personal_tenet',
                          'zqp_seed_one_async_reply_effect', 'TEST READY',
                          'save_scope_as = actor', 'save_scope_as = puppet_or_actor',
                          'save_scope_as = xqol_startup_actor'):
            self.assertNotIn(forbidden, early)
        self.assertLess(setup.index('add_character_flag = zqp_positive_suffix_attempted'),
                        setup.index('has_character_flag = zqp_positive_prior_initialized'))
        for predicate in ('faith = faith:nestorian rite = rite:nestorian piety_level >= 4',
                          'NOT = { any_personal_tenet = { always = yes } }',
                          'has_pam_dlc_trigger = yes free_personal_tenet_slots >= 2'):
            self.assertIn(predicate, setup)
        self.assertEqual(setup.count('zqp_complete_positive_setup_after_slot_boundary_effect = yes'), 1)
        self.assertIn('ZQP120: TEST FAIL early_prior_or_two_slots_D0', setup)
        self.assertNotIn('trigger_event', setup)
        self.assertEqual(suffix.count('set_personal_tenet = '), 2)
        self.assertIn('limit = { has_pam_dlc_trigger = yes free_personal_tenet_slots >= 2 }', suffix)
        self.assertIn('zqp_seed_one_async_reply_effect = yes', suffix)

    def test_new_diagnostics_only_read_and_do_not_recreate_saved_scopes(self):
        from xqol_vanilla_contract import block
        raw = (CASES / SAMPLE_KEY).read_bytes()
        text = raw.decode('utf-8-sig')
        helper = block(text, 'zqp_diagnose_slot_boundary_state78_effect')
        self.assertEqual(set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*=', helper)), {
            'zqp_diagnose_slot_boundary_state78_effect', 'if', 'limit', 'else',
            'is_ai', 'this', 'piety_level', 'any_personal_tenet', 'always',
            'free_personal_tenet_slots', 'debug_log', 'zqp_diagnose_controlled_slot_state77_effect'})
        for target in ('actor', 'puppet_or_actor', 'xqol_startup_actor'):
            self.assertIn('this = scope:' + target, helper)
        setup = block(text, 'zqp_setup_positive_effect')
        self.assertEqual(set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*(?:>=|<=|=)', setup)), {
            'zqp_setup_positive_effect', 'if', 'limit', 'NOT', 'has_character_flag',
            'add_character_flag', 'debug_log', 'zqp_observe_personal_setup_state63_effect',
            'zqp_diagnose_slot_boundary_state78_effect', 'faith', 'rite',
            'piety_level', 'any_personal_tenet', 'always', 'has_pam_dlc_trigger',
            'free_personal_tenet_slots', 'zqp_complete_positive_setup_after_slot_boundary_effect', 'else'})
        initializer = block(text, 'zqp_initialize_effect')
        self.assertEqual(initializer.count('set_player_character = scope:zqp_song'), 1)
        for target in ('actor', 'puppet_or_actor', 'xqol_startup_actor'):
            self.assertEqual(initializer.count('save_scope_as = ' + target + '\n'), 1)

    def test_contract_inverse_preserves_all_original_gates_budgets_and_plan(self):
        contract = json.loads((CASES / 'xqol_pam_positive.json').read_bytes())
        historical = restore_pre_boundary_contract(contract)
        historical['support_files'][SUPPORT_KEY] = copy.deepcopy(PREVIOUS_PREPARE)
        restored = (json.dumps(historical, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        self.check_pin(restored, OLD_CONTRACT)
        for key in (SAMPLE_KEY, EVENTS_KEY, HOOK_KEY):
            self.check_pin((CASES / key).read_bytes(), contract['support_files'][key])
        self.assertEqual(contract['original_step_count'], 35)
        self.assertEqual(contract['maximum_natural_days'], 12)
        self.assertEqual(contract['original_budgets']['readiness_timeout'], 400)
        self.check_pin(restore_minimal_plan((DATA / 'original-plan.json').read_bytes()), {
            'bytes': 19181, 'sha256': '18fa665dff2f47814512306de8dab714ec52c7a06600b115baaf91f423a2fe0f'})
        # The full old contract pin above also fixes every other support file,
        # reward source, required/forbidden literal, budget and fixture allowlist.


if __name__ == '__main__':
    unittest.main()
