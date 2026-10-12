"""Focused migration scope; static/mock checks, never a live acceptance claim."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

CASES = Path(__file__).resolve().parent / 'ck3_mod_acceptance_cases'
PAM_PREFIX = 'xqol_followup_cases/pam_positive/'
SP_MARKERS = ['ZQP120: TEST PASS '+name for name in
              ('acts_sp_before_exact','acts_sp_after_exact',
               'mendicant_sp_before_exact','mendicant_sp_after_exact')]
PAM_OLD_PINS = {
    'xqol_pam_adapter.py': (1177, 'f3d2ebfefbe15399a2259101239a2262daff707e7353cfaf9d6f012415b5b4cf'),
    PAM_PREFIX+'fixture/common/scripted_effects/zqp_pam_sample_effects.txt':
        (24167, 'd9ee497cee4fb7d78bb494aa01a77aea879ed420d7646edb012027513fa9c4dc'),
    PAM_PREFIX+'fixture/common/scripted_effects/zqp_reward_observer_wrappers.txt':
        (6321, '182b7cdbdc0cf7c1c7059a7832b9ad6efc0c5ba19935e8818fb6b6f8fda08700'),
    PAM_PREFIX+'original-plan.json':
        (19181, '18fa665dff2f47814512306de8dab714ec52c7a06600b115baaf91f423a2fe0f'),
}
OLD_GOVERNMENT_PIN = {'bytes':9738, 'sha256':'da485bf51688b6be7bc26a9bc0a50fdb5021c98f6c32da23de19c9e168be6bb9'}
OLD_SETUP = (b' zqp_initialize_spiritual_fulfillment_zero_effect = yes\n'
    b' set_variable = { name = zqp_stock_sp_major value = major_spiritual_fulfillment_value }\n'
    b' set_variable = { name = zqp_stock_sp_minor value = minor_spiritual_fulfillment_value }\n'
    b' set_variable = { name = zqp_sp_acts_expected value = major_spiritual_fulfillment_value }\n'
    b' set_variable = { name = zqp_sp_total_expected value = { value = major_spiritual_fulfillment_value add = minor_spiritual_fulfillment_value } }\n')
OLD_GUARD = (b'    var:zqp_stock_sp_major = 10\n    var:zqp_stock_sp_minor = 3\n'
    b'    spiritual_fulfillment >= 0\n    spiritual_fulfillment <= 0\n'
    b'    is_valid_for_legitimacy_change = yes\n')


def restore_minimal_sample(raw):
    for label, old in [('stock_resource_setup', OLD_SETUP), ('stock_resource_guard', OLD_GUARD),
                       ('stock_resource_readback', b'   debug_log = "ZQP120: READBACK GAP effect_synchronous_actor_legitimacy_raw"\n')]:
        pattern = rb'(?ms)^ *# ZQP_MINIMAL_SCOPE_BEGIN '+label.encode()+rb'\n.*?^ *# ZQP_MINIMAL_SCOPE_END '+label.encode()+rb'\n'
        raw, count = re.subn(pattern, lambda _:old, raw)
        if count != 1:
            raise ValueError('Expected one explicit minimal-scope region: '+label)
    return raw


def restore_minimal_plan(raw):
    value = json.loads(raw)
    for step in value['steps']:
        if step['id'] in ('qol-pam-positive-initial-root','qol-pam-positive-final-root'):
            step['expect'] = {
                'campaign_root_context.player_legitimacy_v1.status':'available',
                'campaign_root_context.player_legitimacy_v1.unavailable_reason':None,
                'campaign_root_context.player_legitimacy_v1.value.scale':100000,
                **step['expect']}
        if step['id']=='qol-pam-positive-final-results':
            step['args']['literals'][5:5] = SP_MARKERS
            step['expect'] = {'exists':True}
            for i, marker in enumerate(step['args']['literals']):
                step['expect']['matches.'+str(i)+'.literal'] = marker
                step['expect']['matches.'+str(i)+'.line_count'] = 1
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()


def restore_minimal_wrapper(raw):
    for name, condition, anchor, after in [
        ('acts_sp_before_exact','spiritual_fulfillment >= 0 spiritual_fulfillment <= 0',
         '   debug_log = "ZQP120: OBSERVE BEGIN acts_original_stock_reward"\n',False),
        ('acts_sp_after_exact','spiritual_fulfillment >= var:zqp_sp_acts_expected spiritual_fulfillment <= var:zqp_sp_acts_expected',
         '   if = { limit = { var:zqp_acts_calls > 1 } debug_log = "ZQP120: TEST FAIL duplicate_acts_reward_call" }\n',True),
        ('mendicant_sp_before_exact','spiritual_fulfillment >= var:zqp_sp_acts_expected spiritual_fulfillment <= var:zqp_sp_acts_expected',
         '   debug_log = "ZQP120: OBSERVE BEGIN mendicant_original_stock_reward"\n',False),
        ('mendicant_sp_after_exact','spiritual_fulfillment >= var:zqp_sp_total_expected spiritual_fulfillment <= var:zqp_sp_total_expected',
         '   if = { limit = { var:zqp_mendicant_calls > 1 } debug_log = "ZQP120: TEST FAIL duplicate_mendicant_reward_call" }\n',True)]:
        removed=('   if = { limit = { '+condition+' } debug_log = "ZQP120: TEST PASS '+name+'" }\n'
                 '   else = { debug_log = "ZQP120: TEST FAIL '+name+'" }\n').encode()
        anchor=anchor.encode()
        if raw.count(anchor)!=1:raise ValueError('Expected unique old observer anchor')
        raw=raw.replace(anchor,anchor+removed if after else removed+anchor,1)
    return raw


def restore_minimal_pam_contract(contract):
    value = copy.deepcopy(contract)
    if value.get('acceptance_scope') != 'focused_pam_positive_mod_callback_v1':
        return value
    value['acceptance_scope'] = 'original_pam_positive_only'
    del value['excluded_stock_resource_arithmetic']
    value['required_markers'][-1:-1] = SP_MARKERS
    for key,(size,sha) in PAM_OLD_PINS.items():
        value['support_files'][key] = {'bytes':size,'sha256':sha}
    return value


def restore_minimal_merit_contract(contract):
    value=copy.deepcopy(contract)
    if value.get('gui_review_scope')=='merit_two_law_representative_toggle_v1':
        for key in ('gui_review_scope','representative_evidence_roles','reused_shared_coverage','coverage_exclusions'):
            del value[key]
        value['support_files']['xqol_government_adapter.py']=dict(OLD_GOVERNMENT_PIN)
    return value


def restore_minimal_ui_adapter(raw):
    source=raw.decode('utf-8-sig')
    replacements=[
        ('from .xqol_ui import Controller, SLIDER_STAGES','from .xqol_ui import Controller, STAGES'),
        ("contract['readonly_step_count'] == 9 and contract.get('gui_review_scope') == 'representative_slider_v1' and\n            contract['focused_slider_order'] == SLIDER_STAGES and",
         "contract['readonly_step_count'] == 9 and contract['gui25_order'] == STAGES and"),
        ('Readonly9/representative slider and independent guard boundary changed','Original readonly9/UI25 and independent guard boundary changed'),
        ("'representative_slider_required': True, 'gui_review_scope': 'representative_slider_v1', 'prior_core_external_reference': prior,",
         "'original_gui25_required': True, 'prior_core_external_reference': prior,"),
        ("'original_readonly9': True, 'focused_slider': ui,","'original_readonly9': True, 'gui25': ui,")]
    for new,old in replacements:
        if source.count(new)!=1:raise ValueError('Minimal UI projection must be exact and unique')
        source=source.replace(new,old,1)
    return source.encode()


def restore_minimal_ui_contract(contract):
    from ck3_mod_acceptance_cases.xqol_ui import STAGES
    value={}
    for key,item in contract.items():
        if key in ('gui_review_scope','focused_slider_order','original_budgets'):continue
        value[key]=copy.deepcopy(item)
        if key=='readonly_step_count':value['gui25_order']=list(STAGES)
    value['new_scene_scope']='New actual Song owner/actor/title-key; original readonly9 and UI25. No defense/reverse/final6 replay.'
    value['guard_gap_rule']='Original guards cannot be marked true without actual evidence. Preserve UI25 guards GAP and qualify only through the independent original-assertion focused case.'
    return value


class FocusedMigration(unittest.TestCase):
    def test_pam_only_removed_stock_numeric_scope_preserves_old_fixture_inverse(self):
        sample=(CASES/PAM_PREFIX/'fixture/common/scripted_effects/zqp_pam_sample_effects.txt').read_bytes()
        old=restore_minimal_sample(sample)
        self.assertEqual((len(old),hashlib.sha256(old).hexdigest()),PAM_OLD_PINS[PAM_PREFIX+'fixture/common/scripted_effects/zqp_pam_sample_effects.txt'])
        text=sample.decode('utf-8-sig')
        self.assertNotIn('zqp_initialize_spiritual_fulfillment_zero_effect = yes',text)
        self.assertEqual(text.count('xqol_mass_conversion_dispatch_next_effect = yes'),1)
        for literal in ('var:zqp_acts_calls = 1','var:zqp_mendicant_calls = 1',
                        'accepted1_refused0_pending_removed','recipient_actual_nestorian_faith_and_rite'):
            self.assertIn(literal,text)
        wrapper=(CASES/PAM_PREFIX/'fixture/common/scripted_effects/zqp_reward_observer_wrappers.txt').read_bytes()
        old_wrapper=restore_minimal_wrapper(wrapper)
        self.assertEqual((len(old_wrapper),hashlib.sha256(old_wrapper).hexdigest()),
                         PAM_OLD_PINS[PAM_PREFIX+'fixture/common/scripted_effects/zqp_reward_observer_wrappers.txt'])
        self.assertTrue(wrapper.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'TEST FAIL acts_sp_',wrapper)
        self.assertNotIn(b'TEST FAIL mendicant_sp_',wrapper)
        for literal in (b'duplicate_acts_reward_call',b'duplicate_mendicant_reward_call'):
            self.assertIn(literal,wrapper)
        # Stock effects remain byte-identical within their observed wrappers.
        stock=Path(__file__).resolve().parents[1]/'Crusader Kings III/game/common/scripted_effects/pam_effects.txt'
        if stock.is_file():
            from ck3_mod_acceptance_cases.xqol_followup_common import stock_reward_projection
            _,proof=stock_reward_projection(stock.read_bytes(),wrapper)
            self.assertTrue(proof['inverse_entire_stock_file_byte_exact'])

    def test_pam_plan_keeps_natural_days_and_actor_but_excludes_stock_resource_thresholds(self):
        raw=(CASES/PAM_PREFIX/'original-plan.json').read_bytes();value=json.loads(raw)
        self.assertEqual(len(value['steps']),35)
        self.assertEqual(sum(s.get('kind')=='advance_day' for s in value['steps']),12)
        self.assertNotIn('player_legitimacy_v1',raw.decode())
        self.assertFalse(any('_sp_' in x for s in value['steps'] for x in s.get('args',{}).get('literals',[])))
        old=restore_minimal_plan(raw)
        self.assertEqual((len(old),hashlib.sha256(old).hexdigest()),PAM_OLD_PINS[PAM_PREFIX+'original-plan.json'])

    def test_merit_representative_keeps_real_human_score_and_restore_admin_stays_full(self):
        from ck3_mod_acceptance_cases import xqol_government_adapter as government
        contract=json.loads((CASES/'xqol_meritocratic_appointments.json').read_bytes())
        # Keep testing the old representative branch when current scope is reduced.
        contract['gui_review_scope']='merit_two_law_representative_toggle_v1'
        contract['representative_evidence_roles']=['human-score-off','human-score-on','human-score-restored']
        slots=[]
        for i,law in enumerate(contract['appointment_laws'],1):
            slots.append({'title_id':i,'law':law,'direct_original_review':True,'representative_toggle_reviewed':True,
                'candidates':[{'character_id':121,'eligible':True,'is_ai':False}],
                'independent_human_candidate':True,'score_off':5,'score_on':-999995,'score_restored':5,
                'auto_appointment_enabled_off':False,'auto_appointment_enabled_on':True,
                'auto_appointment_enabled_restored_score':False,'original_switch_enabled':False,
                'original_switch_restored':True,'final_switch_enabled':False})
        self.assertTrue(government.verify_slots(slots,contract,121))
        for field,value in [('score_on',0),('original_switch_restored',False),('independent_human_candidate',False),('representative_toggle_reviewed',False)]:
            broken=copy.deepcopy(slots);broken[0][field]=value
            with self.assertRaises(ValueError):government.verify_slots(broken,contract,121)
        administrative={'case':'administrative_appointments','appointment_laws':[slots[0]['law']]}
        with self.assertRaises(ValueError):government.verify_slots(slots[:1],administrative,121)
        self.assertEqual(len(contract['representative_evidence_roles']),3)

    def test_ui_representative_boundaries_cancel_save_restore_and_no_replay(self):
        from ck3_mod_acceptance_cases.xqol_ui import Controller,SLIDER_STAGES,STAGES
        from ck3_mod_acceptance_cases.xqol_ui_tail_adapter import validate_contract
        contract=json.loads((CASES/'xqol_ui_tail.json').read_bytes())
        context={'case_contract':contract,'case_spec':{'budgets':{
            'command_timeout':300,'readiness_timeout':400,'timeout':3000,'poll_interval':0.05,'hold_seconds':1800}}}
        validate_contract(context)
        self.assertEqual(contract['focused_slider_order'],SLIDER_STAGES)
        self.assertEqual(len(SLIDER_STAGES),7);self.assertEqual(len(STAGES),25)
        import inspect
        source=inspect.getsource(Controller.record)
        for gate in ('cancel_option_executed','save_option_executed','reopened_persisted_value',
                     'pending_naturally_completed','summary_count','no_script_pending_clear_or_setfaith'):
            self.assertIn(gate,source)
        self.assertTrue(contract['normal_close_required'])
        self.assertTrue(contract['guards_independent_supplement_required'])


if __name__=='__main__':unittest.main()
