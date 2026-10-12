"""Reduced Merit migration checks: no game, desktop, or native invocation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

MAIN=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(MAIN/'tools'))
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_appointment as appointment
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import xqol_government_adapter as gov
from test_ck3_mod_acceptance_appointment import frame, row

CASES=MAIN/'tools/ck3_mod_acceptance_cases'
CONTRACT_VALUE=json.loads((CASES/'xqol_meritocratic_appointments.json').read_bytes())

def collect(law,index):
    value=row(breakdown=None)
    observed=value['result']['title_appointment']
    requested=14770+index;actual=990+index;key='k_offline_'+str(index)
    observed.update(requested_title_id=requested,group_first_title_id=actual,resolved_title_id=actual,
                    current_window_title_id=actual,current_title_key=key,resolved_title_key=key,
                    effective_succession_law_key=law)
    value['result']['current_subject_id']=actual
    # No human candidate: that exclusion is real and is not a score PASS.
    for candidate in observed['candidates']:
        candidate['character_id']+=1000
        candidate['is_human_player']=False
        candidate['is_ai']=True
    proof=appointment.join_pages([value],frame(),requested_title_id=requested,
        requested_title_key='d_offline_'+str(index),expected_law=law)
    proof['run_id']='offline-draft-run'
    reference={'path':str((MAIN/('offline-draft-pool-'+str(index)+'.json')).resolve()),
               'bytes':1,'sha256':str(index+1)*64}
    slot={'requested_title_id':requested,'requested_title_key':'d_offline_'+str(index),
          'title_id':actual,'title_key':key,'law':law,
          'appointment_pool':reference,'direct_original_review':True}
    return slot,proof,reference


def setup():
    client=object.__new__(CaseClient)
    client.frozen={'run_id':'offline-draft-run'}
    client._appointment_receipts={}
    slots=[];pins={}
    for i,law in enumerate(CONTRACT_VALUE['appointment_laws']):
        slot,proof,reference=collect(law,i)
        slots.append(slot)
        client._appointment_receipts[reference['path']]=(reference,proof)
        pins[reference['path']]=reference
    return client,slots,pins


class LoadedLaws(unittest.TestCase):
    def test_current_merit_and_admin_support_pins_and_budgets(self):
        expected={'command_timeout':300,'readiness_timeout':400,'timeout':3000,
                  'hold_seconds':1800,'poll_interval':0.05}
        for name in ('meritocratic_appointments','administrative_appointments'):
            contract=json.loads((CASES/('xqol_'+name+'.json')).read_bytes())
            self.assertEqual(contract['original_budgets'],expected)
            self.assertEqual(contract['original_step_count'],2)
            self.assertEqual(contract['maximum_natural_days'],0)
            for relative,reference in contract['support_files'].items():
                raw=(CASES/relative).read_bytes()
                self.assertEqual(reference,{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            gov.validate_contract({'case':name,'case_contract':contract,
                'case_spec':{'budgets':expected},'shared_game':{'version':'1.20.0.4'}})
        self.assertEqual(len(CONTRACT_VALUE['support_files']),9)
        self.assertEqual(CONTRACT_VALUE['fixture_preparation']['amount'],2000)
        self.assertEqual(CONTRACT_VALUE['fixture_preparation']['applications'],1)

    def test_registry_scope_matches_contract_and_excludes_new_human_score_credit(self):
        registry=json.loads((MAIN/'tools/ck3_mod_acceptance_products.json').read_bytes())
        case=next(c for c in registry['products']['xqol']['cases'] if c['id']=='meritocratic_appointments')
        self.assertEqual(case['gui_contract']['gui_review_scope'],gov.MERIT_LOADED_POOL)
        self.assertEqual(CONTRACT_VALUE['gui_review_scope'],gov.MERIT_LOADED_POOL)
        self.assertEqual(case['gui_contract']['original_appointment_blocks'],CONTRACT_VALUE['appointment_laws'])
        self.assertTrue(case['gui_contract']['root_complete_candidate_pool_review_required'])
        self.assertFalse(case['gui_contract']['human_score_runtime_newly_covered'])
        self.assertNotIn('root_complete_candidate_and_tooltip_review_required',case['gui_contract'])
        self.assertEqual(CONTRACT_VALUE['representative_evidence_roles'],[])
        self.assertIn('NOT newly covered',' '.join(CONTRACT_VALUE['coverage_exclusions']))
        self.assertEqual(CONTRACT_VALUE['reused_shared_coverage'],
                         ['ordinary_appointments','administrative_appointments'])

    def test_one_complete_ai_only_pool_per_law_no_score_requirement(self):
        client,slots,pins=setup()
        with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]), \
             patch.object(appointment,'target_score',side_effect=AssertionError('No new human-score claim')):
            self.assertTrue(gov.verify_native_slots(client,slots,CONTRACT_VALUE,101,frame()))
        self.assertTrue(gov.verify_slots(slots,CONTRACT_VALUE,101))
        for slot in slots:
            self.assertEqual(slot['actual_holder_character_id'],201)
            self.assertNotIn('score_raw_off',slot)
            self.assertFalse(any(c['character_id']==101 for c in slot['candidates']))

    def test_actual_title_law_holder_and_manual_pool_cannot_be_replaced(self):
        for field,value in [('title_id',888),('title_key','k_wrong'),('law','other_law'),
                            ('requested_title_id',888),('requested_title_key','d_wrong'),
                            ('actual_holder_character_id',888),
                            ('candidates',[{'character_id':999,'eligible':True,'is_ai':True}])]:
            with self.subTest(field=field):
                client,slots,pins=setup();slots[0][field]=value
                with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]):
                    with self.assertRaises(ValueError):
                        gov.verify_native_slots(client,slots,CONTRACT_VALUE,101,frame())

    def test_receipt_cannot_cross_actor_date_pid_generation_or_run(self):
        for field,value in [('actor',102),('date',8001),('pid',1002),('generation',5),('run','wrong')]:
            with self.subTest(field=field):
                client,slots,pins=setup();current=frame()
                if field=='actor':current['played_character']['character_id']=value
                if field=='date':current['date_raw']=value
                if field=='pid':
                    current['diagnostics']['bridge_pid']=value;current['diagnostics']['hello']['pid']=value
                if field=='generation':
                    current['diagnostics']['connection_generation']=value
                    current['diagnostics']['hello']['connection_generation']=value
                if field=='run':client.frozen['run_id']=value
                with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]):
                    with self.assertRaises(ValueError):
                        gov.verify_native_slots(client,slots,CONTRACT_VALUE,101,current)
        client,slots,pins=setup();current=frame();current['native_revision']+=1
        with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]):
            self.assertTrue(gov.verify_native_slots(client,slots,CONTRACT_VALUE,101,current))

    def test_two_laws_distinct_titles_and_original_review_stay_required(self):
        client,slots,pins=setup()
        with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]):
            gov.verify_native_slots(client,slots,CONTRACT_VALUE,101,frame())
        broken=copy.deepcopy(slots);broken[1]['title_id']=broken[0]['title_id']
        with self.assertRaises(ValueError):gov.verify_slots(broken,CONTRACT_VALUE,101)
        broken=copy.deepcopy(slots);broken[0]['direct_original_review']=False
        with self.assertRaises(ValueError):gov.verify_slots(broken,CONTRACT_VALUE,101)
        with self.assertRaises(ValueError):gov.verify_slots(slots[:1],CONTRACT_VALUE,101)

    def test_old_representative_and_full_admin_do_not_use_reduced_branch(self):
        contract=copy.deepcopy(CONTRACT_VALUE);contract['gui_review_scope']=gov.MERIT_REPRESENTATIVE
        slots=[]
        for i,law in enumerate(contract['appointment_laws'],1):
            slots.append({'title_id':i,'law':law,'direct_original_review':True,'representative_toggle_reviewed':True,
                'candidates':[{'character_id':101,'eligible':True,'is_ai':False}],
                'independent_human_candidate':True,'score_off':5,'score_on':-999995,'score_restored':5,
                'auto_appointment_enabled_off':False,'auto_appointment_enabled_on':True,
                'auto_appointment_enabled_restored_score':False,'original_switch_enabled':False,
                'original_switch_restored':True,'final_switch_enabled':False})
        self.assertTrue(gov.verify_slots(slots,contract,101))
        for key,value in [('score_on',0),('independent_human_candidate',False),
                          ('original_switch_restored',False),('representative_toggle_reviewed',False)]:
            broken=copy.deepcopy(slots);broken[0][key]=value
            with self.assertRaises(ValueError):gov.verify_slots(broken,contract,101)
        admin={'case':'administrative_appointments','gui_review_scope':gov.MERIT_LOADED_POOL,
               'appointment_laws':[slots[0]['law']]}
        with self.assertRaises(ValueError):gov.verify_slots(slots[:1],admin,101)

    def test_run_case_request_and_coverage_are_truthful_and_holder_is_read_again(self):
        client,slots,pins=setup();calls=[];requests=[]
        client.snapshot=lambda:frame()
        client.validate_frame=lambda value:value
        client.log_bytes=lambda:b'offline-only'
        response={'completed':True,'current_scene_reviewed':True,'slots':slots,
                  'evidence':[{'path':'offline-reviewed.png','bytes':1,'sha256':'e'*64}]}
        def checkpoint(name,request,**kwargs):
            requests.append(request);return response
        client.root_checkpoint=checkpoint
        def execute(steps,name):
            calls.append(steps[0])
            if name=='qolf-government-root':
                return [{'result':{'campaign_root_context_ready':True,'campaign_root_context':{
                    'player_character_id':101,'date_raw':8000,'government':{'key':'meritocratic_government'},
                    'independent':True}},'after_snapshot':frame()}]
            return [{'result':{'title_holder':{'available':True,'status':'available',
                'title_id':steps[0]['args']['title_id'],'holder_character_id':201,
                'actor_character_id':101,'date_raw':8000}},'after_snapshot':frame()}]
        client.execute_plan=execute
        context={'case':'meritocratic_appointments','case_contract':CONTRACT_VALUE}
        with patch.object(entry,'pin',side_effect=lambda path:pins[str(Path(path).resolve())]), \
             patch.object(gov,'pin',return_value=response['evidence'][0]), \
             patch.object(gov,'actual_scope',return_value={'runtime_character_id':101}), \
             patch.object(gov.common,'run_plan',return_value={'after':frame()}), \
             patch.object(gov.common,'preserve_result',side_effect=lambda context,client,result:result):
            result=gov.run_case(context,client)
        self.assertEqual(requests[0]['typed_slot_fields'][-1],'appointment_pool')
        self.assertNotIn('appointment_pool_off',requests[0]['typed_slot_fields'])
        self.assertIsNone(requests[0]['original_million_penalty'])
        self.assertFalse(result['merit_human_score_runtime_newly_covered'])
        self.assertEqual(len(result['actual_holder_rows']),2)
        self.assertEqual([s['tool'] for s in calls],
            ['ck3_query_campaign_root_context_v1','ck3_query_title_holder_v1','ck3_query_title_holder_v1'])


if __name__=='__main__':
    unittest.main(verbosity=2)


