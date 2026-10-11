"""Byte-exact inverse checks for one unproven PAM delayed-boundary candidate.

Portable/static only: these checks do not prove paused D0 scheduling or that
the engine carries saved scopes across the new hidden event.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
CASES = HERE / 'ck3_mod_acceptance_cases'
DATA = CASES / 'xqol_followup_cases/pam_positive'
SAMPLE_KEY = 'xqol_followup_cases/pam_positive/fixture/common/scripted_effects/zqp_pam_sample_effects.txt'
EVENTS_KEY = 'xqol_followup_cases/pam_positive/fixture/events/zqp_pam_events.txt'
OLD_SAMPLE = {'bytes': 20593, 'sha256': '9d59d37136125367b5219988a65e33391ad8b9d1f40e732fa5c53072f62544da'}
OLD_EVENTS = {'bytes': 222, 'sha256': 'dd40084261bf225244ff7db4d8fe749065a054e63a813495c0b5c01c328e26e7'}
OLD_CONTRACT = {'bytes': 5217, 'sha256': 'cf720e3a30f56fe637118dbdf6fbf88811f3c972db5ca60d109523c47d785510'}
BOUNDARY_REGION = rb'(?ms)^ # ZQP78_BOUNDARY_CANDIDATE_BEGIN deferred_boundary\n.*?^ # ZQP78_BOUNDARY_CANDIDATE_END deferred_boundary\n'
DIAGNOSTIC_REGION = rb'(?ms)^# ZQP78_BOUNDARY_DIAGNOSTIC_ONLY_BEGIN read_only_helper\n.*?^# ZQP78_BOUNDARY_DIAGNOSTIC_ONLY_END read_only_helper\n'
EVENT_REGION = rb'(?ms)^# ZQP78_BOUNDARY_CANDIDATE_EVENT_BEGIN\n.*?^# ZQP78_BOUNDARY_CANDIDATE_EVENT_END\n'


def remove_one(raw, pattern):
    restored, count = re.subn(pattern, b'', raw)
    if count != 1:
        raise ValueError('Expected exactly one reviewed candidate region')
    return restored


def restore_pre_boundary_sample(raw):
    return remove_one(remove_one(raw, BOUNDARY_REGION), DIAGNOSTIC_REGION)


def restore_pre_boundary_events(raw):
    return remove_one(raw, EVENT_REGION)


def restore_pre_boundary_contract(value):
    restored = copy.deepcopy(value)
    restored['support_files'][SAMPLE_KEY] = copy.deepcopy(OLD_SAMPLE)
    restored['support_files'][EVENTS_KEY] = copy.deepcopy(OLD_EVENTS)
    return restored


class DelayedBoundaryCandidate(unittest.TestCase):
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

    def test_one_hidden_continuation_only_and_original_events_restore_exactly(self):
        from xqol_vanilla_contract import block
        raw = (CASES / EVENTS_KEY).read_bytes()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        self.check_pin(restore_pre_boundary_events(raw), OLD_EVENTS)
        event = block(raw.decode('utf-8-sig'), 'zqp120.3')
        self.assertEqual(event, 'zqp120.3 = { type = character_event hidden = yes immediate = { zqp_complete_positive_setup_after_slot_boundary_effect = yes } }')
        text = (CASES / SAMPLE_KEY).read_bytes().decode('utf-8-sig')
        setup = block(text, 'zqp_setup_positive_effect')
        suffix = block(text, 'zqp_complete_positive_setup_after_slot_boundary_effect')
        self.assertEqual(text.count('trigger_event = { id = zqp120.3 delayed = yes }'), 1)
        self.assertNotIn('set_personal_tenet', setup)
        self.assertNotIn('zqp_seed_one_async_reply_effect = yes', setup)
        for original_prior in ('set_character_faith = faith:nestorian',
                               'set_character_rite = rite:nestorian',
                               'set_piety_level = { value = 4 }',
                               'modifier = zqp_controlled_personal_slot_modifier years = 1'):
            self.assertIn(original_prior, setup)
            self.assertNotIn(original_prior, suffix)
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
        boundary = re.search(BOUNDARY_REGION, raw).group()
        self.assertNotIn(b'save_scope_as', boundary)
        self.assertNotIn(b'days =', boundary)
        self.assertNotIn(b'TEST READY', boundary)
        self.assertNotIn(b'TEST FAIL', boundary)

    def test_contract_inverse_preserves_all_original_gates_budgets_and_plan(self):
        contract = json.loads((CASES / 'xqol_pam_positive.json').read_bytes())
        restored = (json.dumps(restore_pre_boundary_contract(contract), ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        self.check_pin(restored, OLD_CONTRACT)
        for key in (SAMPLE_KEY, EVENTS_KEY):
            self.check_pin((CASES / key).read_bytes(), contract['support_files'][key])
        self.assertEqual(contract['original_step_count'], 35)
        self.assertEqual(contract['maximum_natural_days'], 12)
        self.assertEqual(contract['original_budgets']['readiness_timeout'], 400)
        self.check_pin((DATA / 'original-plan.json').read_bytes(), {
            'bytes': 19181, 'sha256': '18fa665dff2f47814512306de8dab714ec52c7a06600b115baaf91f423a2fe0f'})
        # The full old contract pin above also fixes every other support file,
        # reward source, required/forbidden literal, budget and fixture allowlist.


if __name__ == '__main__':
    unittest.main()
