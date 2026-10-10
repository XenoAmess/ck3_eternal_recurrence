"""Portable focused checks for the original independent QOL case port."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
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
            with self.subTest(declared=declared):
                client=object.__new__(module.CaseClient)
                client.selection=types.SimpleNamespace(prepared={'preparation':{'initial_plan_original_business':declared}},
                    case={'budgets':{'readiness_timeout':400,'timeout':4500}})
                reports=iter([{'phase':'initial-plan','steps':[]},{'phase':'hold','steps':[{'finished_at':'actual'}]}])
                current_report=None
                def read_report(allow_error=False):
                    nonlocal current_report
                    if allow_error:current_report=next(reports)
                    return current_report
                client.read_report=read_report;client.guard=lambda:None;client.retain_process=lambda:None
                client.retain_held_process=lambda report:False
                with patch.object(module.time,'monotonic',side_effect=[0,1,401]),patch.object(module.time,'sleep'):
                    if success:self.assertEqual(client.wait_hold()['phase'],'hold')
                    else:
                        with self.assertRaises(TimeoutError):client.wait_hold()

if __name__=='__main__':
    unittest.main(argv=[sys.argv[0],*remaining])
