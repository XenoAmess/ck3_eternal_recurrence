"""Portable focused checks for the original independent QOL case port."""
import argparse
import copy
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

options, remaining = argparse.ArgumentParser(add_help=False).parse_known_args()
parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--support-repo',type=Path,default=Path(__file__).resolve().parents[1])
parser.add_argument('--client-source',type=Path)
options,remaining=parser.parse_known_args()
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(options.support_repo/'tools'))
import ck3_mod_acceptance_cases
ck3_mod_acceptance_cases.__path__.insert(0,str(HERE/'ck3_mod_acceptance_cases'))
from ck3_mod_acceptance_cases import xqol_followup_common as common
from ck3_mod_acceptance_cases import xqol_government_adapter as government
from ck3_mod_acceptance_cases import xqol_pam_adapter as pam
from test_ck3_mod_acceptance_xqol_pam_boundary import (
    restore_pre_boundary_sample, restore_pre_boundary_contract)
from test_ck3_mod_acceptance_xqol_prepare_compatibility import (
    ReviewedPrepareCompatibility, PREVIOUS_PREPARE, SUPPORT_KEY)

def config(name):
    return json.loads((HERE/'ck3_mod_acceptance_cases'/('xqol_'+name+'.json')).read_bytes())

def context(name):
    value=config(name)
    return {'case':name,'case_contract':value,'case_spec':{'budgets':value['original_budgets']},
            'shared_game':{'version':'1.20.0.4'}}

class OriginalCases(unittest.TestCase):
    def test_original_plans_keep_steps_days_and_literal_contracts(self):
        expected={'administrative_appointments':(2,0),'meritocratic_appointments':(2,0),
                  'prison_payment':(5,1),'selfpaid_ransom':(30,12),'pam_positive':(35,12),'pam_negative':(35,12)}
        for name,(count,days) in expected.items():
            with self.subTest(case=name):
                ctx=context(name);steps,changes=common.bind_plan(ctx)
                self.assertEqual(len(steps),count)
                self.assertEqual(sum(s.get('kind')=='advance_day' for s in steps),days)
                for step in steps:
                    if step.get('tool')=='ck3_query_engine_log_literals_v1':
                        for field,value in step.get('expect',{}).items():
                            if field.endswith('.literal'):
                                self.assertEqual(value,step['args']['literals'][int(field.split('.')[1])])
                refs=[]
                def walk(value):
                    if isinstance(value,dict):
                        if set(value)=={'$ref'}:refs.append(value['$ref'])
                        else:
                            for child in value.values():walk(child)
                    elif isinstance(value,list):
                        for child in value:walk(child)
                walk(steps)
                identifiers={'qolf-anchor',*(s['id'] for s in steps)}
                for ref in refs:self.assertIn(ref.split('.')[1],identifiers)
                raw=common.read(common.base(ctx)/'original-plan.json')
                self.assertEqual([s['id'] for s in raw['steps']],[s['id'] for s in steps])

    def test_original_case_specific_budgets_and_tamper_rejection(self):
        for name,timeout,hold in [('administrative_appointments',3000,1800),('meritocratic_appointments',3000,1800),
                                  ('prison_payment',2400,900),('selfpaid_ransom',4500,600),
                                  ('pam_positive',4500,600),('pam_negative',4500,600)]:
            ctx=context(name);ctx['case_contract']['support_files']={}
            common.validate_contract(ctx)
            self.assertEqual(ctx['case_spec']['budgets']['timeout'],timeout)
            self.assertEqual(ctx['case_spec']['budgets']['hold_seconds'],hold)
            ctx['case_spec']['budgets']=copy.deepcopy(ctx['case_spec']['budgets'])
            ctx['case_spec']['budgets']['hold_seconds']+=1
            with self.assertRaises(ValueError):common.validate_contract(ctx)

    def test_log_failure_and_duplicate_are_not_success(self):
        required=['ORIGINAL PASS a','ORIGINAL DONE b'];forbidden=['ORIGINAL FAIL']
        self.assertEqual(common.observe(b'ORIGINAL PASS a\nORIGINAL DONE b\n',required,forbidden)['required'],dict.fromkeys(required,1))
        for raw in (b'ORIGINAL PASS a\n',b'ORIGINAL PASS a\nORIGINAL DONE b\nORIGINAL FAIL\n',
                    b'ORIGINAL PASS a\nORIGINAL PASS a\nORIGINAL DONE b\n'):
            with self.assertRaises(ValueError):common.observe(raw,required,forbidden)

    def test_government_current_saved_actor_rejects_old_root(self):
        markers=['ZQAGOV: QUAL BEGIN native','ZQAGOV: QUAL PASS native','ZQAGOV: QUAL DONE native']
        contract={'required_markers':markers,'forbidden_markers':['ZQAGOV: QUAL FAIL']}
        raw=('\n'.join([markers[0],markers[1],
             '[12:00:00][D][effectimpl.cpp:1]: Character (Internal ID: 121 - Historical ID example)',
             'Root: Robert (Internal ID: 999 - Historical ID norman)',
             'Saved event targets:','zqagov_actual_player: Character (Internal ID: 121 - Historical ID example)',markers[2]])+'\n').encode()
        proof=government.actual_scope(raw,contract)
        self.assertEqual(proof['runtime_character_id'],121)
        self.assertTrue(proof['old_ROOT_not_used'])
        with self.assertRaises(ValueError):government.actual_scope(raw.replace(b'zqagov_actual_player: Character (Internal ID: 121',b'zqagov_actual_player: Character (Internal ID: 999'),contract)

    def test_original_appointment_score_eligibility_successor_boundaries(self):
        slot={'title_id':51,'law':'appointment_succession_law','direct_original_review':True,
              'full_candidates_reviewed':True,'eligibility_and_score_breakdown_reviewed':True,
              'candidates':[{'character_id':121,'eligible':True,'is_ai':False},{'character_id':122,'eligible':True,'is_ai':True}],
              'independent_human_candidate':True,'score_off':53.5,'score_on':-999946.5,'score_restored':53.5,
              'auto_appointment_enabled_off':False,'auto_appointment_enabled_on':True,
              'auto_appointment_enabled_restored_score':False,'original_switch_enabled':True,
              'original_switch_restored':True,'final_switch_enabled':True,'chosen_character_id':122,
              'actual_successor_character_id':122,'native_appointment_confirmed':True}
        contract={'appointment_laws':['appointment_succession_law']}
        self.assertTrue(government.verify_slots([slot],contract,121))
        for field,value in [('score_on',0),('actual_successor_character_id',123),('chosen_character_id',121),
                            ('full_candidates_reviewed',False),('original_switch_restored',False)]:
            broken=copy.deepcopy(slot);broken[field]=value
            with self.assertRaises(ValueError):government.verify_slots([broken],contract,121)

    def test_pam_requires_exact_existing_two_read_optins(self):
        ctx=context('pam_positive');ctx['case_contract']['support_files']={}
        ctx['case_spec'].update(opt_in_read_only_mcp_tools=pam.TOOLS,required_mcp_tools=pam.TOOLS)
        pam.validate_contract(ctx)
        for tools in ([],pam.TOOLS[:1],pam.TOOLS+['invented_tool']):
            ctx['case_spec']['opt_in_read_only_mcp_tools']=tools
            with self.assertRaises(ValueError):pam.validate_contract(ctx)

    def test_pam_positive_slot_diagnostics_are_read_only_and_inverse_exact(self):
        from xqol_vanilla_contract import block
        ctx=context('pam_positive')
        raw=(common.base(ctx)/'fixture/common/scripted_effects/zqp_pam_sample_effects.txt').read_bytes()
        raw=restore_pre_boundary_sample(raw)
        pattern=rb'(?ms)^ *# ZQP77_SLOT_DIAGNOSTIC_ONLY_BEGIN [^\r\n]+\r?\n.*?^ *# ZQP77_SLOT_DIAGNOSTIC_ONLY_END [^\r\n]+\r?\n'
        inverse,count=re.subn(pattern,b'',raw)
        self.assertEqual(count,4)
        self.assertEqual(len(inverse),18737)
        self.assertEqual(hashlib.sha256(inverse).hexdigest(),
                         '8d72393e24aafc71c9860fcb7c2b7ff431ef7e312f7af19a58930c1d7cd5ab3a')
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        text=raw.decode('utf-8-sig')
        helper=block(text,'zqp_diagnose_controlled_slot_state77_effect')
        assignments=set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*=',helper))
        self.assertEqual(assignments,{'zqp_diagnose_controlled_slot_state77_effect','if','limit','else',
            'has_character_modifier','has_pam_dlc_trigger','free_personal_tenet_slots','debug_log'})
        for region in re.findall(pattern,raw):
            if b'read_only_helper' in region.splitlines()[0]:continue
            self.assertEqual(set(re.findall(rb'\b([A-Za-z_][A-Za-z_0-9]*)\s*=',region)),
                             {b'debug_log',b'zqp_diagnose_controlled_slot_state77_effect'})
        self.assertEqual(text.count('zqp_diagnose_controlled_slot_state77_effect = yes'),3)
        for phase in ('before_controlled_slot_guard','inside_guard_after_add','after_controlled_slot_guard'):
            self.assertEqual(text.count('ZQPSLOT120: PHASE '+phase),1)

    def test_pam_positive_slot_diagnostic_pin_is_only_contract_change(self):
        ctx=context('pam_positive')
        common.validate_contract(ctx)
        original=restore_pre_boundary_contract(ctx['case_contract'])
        original['support_files'][SUPPORT_KEY] = copy.deepcopy(PREVIOUS_PREPARE)
        key='xqol_followup_cases/pam_positive/fixture/common/scripted_effects/zqp_pam_sample_effects.txt'
        original['support_files'][key]={'bytes':18737,
            'sha256':'8d72393e24aafc71c9860fcb7c2b7ff431ef7e312f7af19a58930c1d7cd5ab3a'}
        restored=(json.dumps(original,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        self.assertEqual(hashlib.sha256(restored).hexdigest(),
                         'd9c09fcb6d785bb25ed0c301a0f1ae3e4ba3b8356365fe29e31b34ca806270ab')

    def test_stock_projection_retains_rewards_and_rejects_changed_body(self):
        keys=('conversion_tenet_acts_of_the_apostles_effect','conversion_tenet_mendicant_preachers_effect')
        stock=b'\xef\xbb\xbf'+('\n'.join(k+' = {\n value = 10 # brace }\n text = "{literal}"\n}\n' for k in keys)+'unrelated = { value = 42 }\n').encode()
        wrappers='\n'.join(k+' = {\n debug_log = "before"\n value = 10 # brace }\n text = "{literal}"\n debug_log = "after"\n}\n' for k in keys).encode()
        result,proof=common.stock_reward_projection(stock,wrappers)
        self.assertTrue(result.startswith(b'\xef\xbb\xbf'))
        self.assertIn(b'unrelated = { value = 42 }\n',result)
        self.assertTrue(proof['inverse_entire_stock_file_byte_exact'])
        with self.assertRaises(ValueError):common.stock_reward_projection(stock,wrappers.replace(b'value = 10',b'value = 11',1))
        with self.assertRaises(ValueError):common.stock_reward_projection(stock+stock[3:],wrappers)

    def test_consumption_never_requeues_original_days(self):
        import inspect,ast
        tree=ast.parse(inspect.getsource(common.run_plan))
        called={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertNotIn('advance_day',called)
        self.assertNotIn('execute_plan',called)
        self.assertIn('read_report',called)

    def test_common_wait_uses_original_business_budget_only_for_literal_true(self):
        path=options.client_source or options.support_repo/'tools/ck3_mod_acceptance_client.py'
        spec=importlib.util.spec_from_file_location('_original_wait_client',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for declared,success in [(True,True),(False,False),(1,False),(None,False)]:
            with self.subTest(declared=declared), tempfile.TemporaryDirectory() as directory:
                client=object.__new__(module.CaseClient)
                client.output=Path(directory);client.live=client.output/'synthetic-run';client.state=client.output/'synthetic-state'
                client.frozen={'run_id':'synthetic-run','screen_task':'synthetic-screen'}
                client.context={'frozen_argv':{'path':'synthetic-frozen','bytes':1,'sha256':'d'*64}}
                client.selection=types.SimpleNamespace(prepared={'preparation':{'initial_plan_original_business':declared}},
                    case={'budgets':{'readiness_timeout':400,'timeout':4500}},
                    runtime={'manifest':{'path':'synthetic-manifest','bytes':1,'sha256':'e'*64}})
                reports=iter([{'phase':'initial-plan','steps':[]},{'phase':'hold','steps':[{'finished_at':'actual'}]}])
                current_report=None
                def read_report(allow_error=False):
                    nonlocal current_report
                    if allow_error:current_report=next(reports)
                    return current_report
                client.read_report=read_report;client.guard=lambda:None;client.retain_process=lambda:None
                client.retain_held_process=lambda report:False
                with patch.object(module.time,'monotonic',side_effect=[0,1,401,402]),patch.object(module.time,'sleep'):
                    if success:self.assertEqual(client.wait_hold()['phase'],'hold')
                    else:
                        with self.assertRaises(TimeoutError):client.wait_hold()

class RansomAtomicReceipt(unittest.TestCase):
    """Static/script-shape checks and an exact arithmetic model, not CK3 proof."""

    phases = ('normal_full', 'normal_any', 'pillage_full', 'pillage_any')
    effect_key = ('xqol_followup_cases/liege_shared_ransom/fixture/common/'
                  'scripted_effects/zqlr_liege_ransom_effects.txt')
    region = re.compile(rb'(?ms)^([ ]*)# ZQLR85_ATOMIC_RECEIPT_BEGIN ([^\r\n]+)\n'
                        rb'.*?^\1# ZQLR85_ATOMIC_RECEIPT_END \2\n')

    def fixture(self):
        return (HERE/'ck3_mod_acceptance_cases'/self.effect_key).read_bytes()

    def test_exact_inverse_bom_pin_and_original_contract(self):
        raw = self.fixture()
        self.assertTrue(raw.startswith(b'\xef\xbb\xbf'))
        self.assertNotIn(b'\r', raw)
        regions = list(self.region.finditer(raw))
        self.assertEqual(len(regions), 13)
        labels = {m.group(2).decode('ascii') for m in regions}
        self.assertEqual(labels, {'before', 'after_values', 'after_verified',
            'court_setup normal', 'court_setup pillage',
            *('reset '+phase for phase in self.phases),
            *('delayed '+phase for phase in self.phases)})

        def undo(match):
            if match.group(2).startswith(b'delayed '):
                return match.group(1)+b'gold >= var:zqlr_expected_captor NOT = { gold > var:zqlr_expected_captor }\n'
            if match.group(2).startswith(b'court_setup '):
                return match.group(1)+b'scope:zqlr_payer = { add_courtier = scope:zqlr_first add_courtier = scope:zqlr_second }\n'
            return b''

        inverse = self.region.sub(undo, raw)
        self.assertEqual(len(inverse), 30264)
        self.assertEqual(hashlib.sha256(inverse).hexdigest(),
                         '7f5014508c6e2d36b51f8b8966d9d8740178e17467d824f016fc1670bc63e861')
        ctx = context('liege_shared_ransom')
        common.validate_contract(ctx)
        contract = ctx['case_contract']
        self.assertEqual(contract['support_files'][self.effect_key],
                         {'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()})
        old_contract = copy.deepcopy(contract)
        old_contract['support_files'][SUPPORT_KEY] = copy.deepcopy(PREVIOUS_PREPARE)
        old_contract['support_files'][self.effect_key] = {
            'bytes':30264, 'sha256':'7f5014508c6e2d36b51f8b8966d9d8740178e17467d824f016fc1670bc63e861'}
        self.assertEqual(hashlib.sha256((json.dumps(old_contract,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest(),
                         '52877e54d11256a9d061fccd00c744b86e888a350b7005f60e8c26212a76b900')
        self.assertEqual(len(contract['required_markers']), 22)
        self.assertEqual(contract['original_step_count'], 30)
        self.assertEqual(contract['maximum_natural_days'], 12)
        self.assertEqual(contract['original_budgets'], {
            'command_timeout':300, 'readiness_timeout':400, 'timeout':4500,
            'hold_seconds':600, 'poll_interval':0.05})
        wrapper_key = self.effect_key.replace('zqlr_liege_ransom_effects.txt', 'zqlr_stock_ransom_observer.txt')
        wrapper = (HERE/'ck3_mod_acceptance_cases'/wrapper_key).read_bytes()
        self.assertEqual((len(wrapper), hashlib.sha256(wrapper).hexdigest()),
                         (6086, '1028fcd76a75c1fb9ea43fc23d5353e46d6d9dbc658c1c772218904b913042a6'))

    def test_four_phase_resets_original_gate_and_saved_strict_deltas(self):
        from xqol_vanilla_contract import block
        text = self.fixture().decode('utf-8-sig')
        before = block(text, 'zqlr_stock_before_effect')
        after = block(text, 'zqlr_stock_after_effect')
        for phase in self.phases:
            flag = 'zqlr_stock_'+phase+'_verified'
            dispatch = block(text, 'zqlr_dispatch_'+phase+'_effect')
            delayed = block(text, 'zqlr_observe_'+phase+'_effect')
            self.assertIn('remove_character_flag = '+flag, dispatch)
            self.assertLess(dispatch.index('remove_character_flag = '+flag), dispatch.index('xqol_bulk_ransom_'))
            self.assertIn('remove_character_flag = '+flag, before)
            self.assertEqual(text.count('add_character_flag = '+flag), 1)
            self.assertIn('has_character_flag = zqlr_wait_'+phase+' } add_character_flag = '+flag, after)
            self.assertIn('has_character_flag = '+flag, delayed)
            self.assertIn('var:xqol_last_bulk_ransom_count = 1 var:zqlr_stock_calls = 1', delayed)
            self.assertNotRegex(delayed, r'(?m)^\s*gold\s*[><=]')
            self.assertIn('var:zqlr_payer = { gold >= ', delayed)
            for side in ('captor', 'payer'):
                self.assertIn('var:zqlr_stock_'+side+'_delta >= var:zqlr_stock_receipt_amount '
                              'NOT = { var:zqlr_stock_'+side+'_delta > var:zqlr_stock_receipt_amount }', delayed)
            self.assertIn('var:zqlr_stock_receipt_amount >= var:zqlr_expected_amount '
                          'NOT = { var:zqlr_stock_receipt_amount > var:zqlr_expected_amount }', delayed)
        for side, value in [('captor','gold'), ('payer','scope:payer.gold')]:
            self.assertIn('set_variable = { name = zqlr_stock_'+side+'_before value = '+value+' }', before)
            self.assertIn('set_variable = { name = zqlr_stock_'+side+'_after value = '+value+' }', after)
        self.assertIn('set_variable = { name = zqlr_stock_receipt_amount value = var:zqlr_expected_amount }', before)
        self.assertIn('name = zqlr_stock_captor_delta value = var:zqlr_stock_captor_after', after)
        self.assertIn('name = zqlr_stock_captor_delta subtract = var:zqlr_stock_captor_before', after)
        self.assertIn('name = zqlr_stock_payer_delta value = var:zqlr_stock_payer_before', after)
        self.assertIn('name = zqlr_stock_payer_delta subtract = var:zqlr_stock_payer_after', after)
        gate = after.index('var:zqlr_stock_calls = 1')
        first_flag = after.index('add_character_flag = zqlr_stock_normal_full_verified')
        for original in ('scope:payer = var:zqlr_payer',
                         'scope:prisoner = { is_alive = yes is_ruler = no is_imprisoned = no',
                         'scope:payer = { gold >= scope:zqlr_actor.var:zqlr_stock_expected_payer_after NOT = { gold > scope:zqlr_actor.var:zqlr_stock_expected_payer_after } }',
                         'gold >= var:zqlr_stock_expected_captor_after NOT = { gold > var:zqlr_stock_expected_captor_after }'):
            self.assertIn(original, after[gate:first_flag])

    def test_court_setup_only_adds_children_not_already_in_the_payer_court(self):
        regions = {m.group(2).decode('ascii'):m.group(0).decode('utf-8')
                   for m in self.region.finditer(self.fixture())}
        for phase in ('normal', 'pillage'):
            region = regions['court_setup '+phase]
            self.assertEqual(len(re.findall(r'\bif\s*=', region)), 2)
            self.assertEqual(region.count('is_courtier_of = scope:zqlr_payer'), 2)
            self.assertNotIn('else', region)
            for child in ('first', 'second'):
                scope = 'scope:zqlr_'+child
                self.assertEqual(region.count('add_courtier = '+scope), 1)
                self.assertIn('limit = { '+scope+' = { NOT = { is_courtier_of = scope:zqlr_payer } } }\n'
                              '   add_courtier = '+scope, region)
                # Exact guard model, not an engine claim; structure above binds it.
                for already_in_court, expected_calls in ((True, 0), (False, 1)):
                    calls = []
                    if not already_in_court:
                        calls.append(scope)
                    self.assertEqual(len(calls), expected_calls)

    def test_exact_receipt_model_rejects_wrong_amount_duplicate_missing_or_wrong_phase(self):
        # Mirrors the structurally checked exact gates above; not an engine emulator.
        def accepted(captor_before, captor_after, payer_before, payer_after, amount,
                     calls=1, receipt=True, phase='pillage_full', expected_phase='pillage_full',
                     same_payer=True, released=True, fresh_eligible=True, delayed_captor='2599.32'):
            cb, ca, pb, pa, expected = map(Decimal, (captor_before,captor_after,payer_before,payer_after,amount))
            verified = calls == 1 and same_payer and released and ca == cb+expected and pa == pb-expected
            # The delayed captor wallet is intentionally not a transaction-time operand.
            return verified and receipt and phase == expected_phase and ca-cb == expected and pb-pa == expected and fresh_eligible

        good = ('2528', '2603', '76', '1', '75')
        self.assertTrue(accepted(*good))
        self.assertTrue(accepted(*good, delayed_captor='2607.91'))
        for bad in [('2528','2602.99999','76','1','75'),
                    ('2528','2603','76','1.00001','75'),
                    ('2528','2603','76','1','74')]:
            self.assertFalse(accepted(*bad))
        for kwargs in ({'calls':2}, {'receipt':False}, {'phase':'normal_full'},
                       {'same_payer':False}, {'released':False}, {'fresh_eligible':False}):
            self.assertFalse(accepted(*good, **kwargs))


if __name__=='__main__':
    unittest.main(argv=[sys.argv[0],*remaining])
