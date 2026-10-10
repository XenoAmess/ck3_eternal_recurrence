"""Portable public I3b tests: actual pure guards/complete comparisons, no CK3."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parent
sys.path.insert(0,str(TOOLS))
from ck3_mod_acceptance_cases import lyd_i3b_formal_adapter as adapter


def frame(instance=119,revision=2):
    return {'snapshot_id':'native:'+str(revision-1),'revision':revision,'native_revision':revision-1,
        'date_raw':53144712,'paused':True,'map_ready':True,'episode_projection':'native_campaign',
        'played_character':{'character_id':31254},'active_event':{'instance_id':instance},
        'diagnostics':{'bridge_pid':901,'connection_generation':1}}


def scope(kind,key,identity):
    return {'status':'available','type_key':kind,
        'typed_identity':{'status':'available','kind':kind,key:identity}}


def packet(actual,data,result=False):
    prefix='lyd_i3b_result_event_' if result else 'lyd_i3b_event_'
    scopes=[{'name':'lyd_i3b_actor','scope':scope('character','character_id',31254)}]
    for key in ('serial','nonce') if result else ('serial','nonce','phase'):
        number=data['round'][key]
        scopes.append({'name':prefix+key,'scope':{'status':'available','type_key':'value',
            'numeric_value':{'raw_fixed_point':str(number*100000),'scale':100000,
                'decimal_value':str(number),'integer_value':str(number)}}})
    return {'status':'available','queried_snapshot_id':actual['snapshot_id'],
        'queried_revision':actual['revision'],'queried_native_revision':actual['native_revision'],
        'current_event_window_context':{'schema':'current-event-window-context-v1','status':'available',
            'snapshot_revision':actual['native_revision'],'date_raw':actual['date_raw'],
            'current_event_instance_id':actual['active_event']['instance_id'],
            'event_definition_key':'lyd.431' if result else 'lyd.430','window_match_count':1,
            'root_scope':scope('character','character_id',31254),'saved_scopes':scopes,
            'readiness':{key:True for key in ('event_definition_identity_ready','root_scope_ready','saved_scopes_ready','option_presentation_ready')},
            'options':[{'rendered_index':i,'native_option_index':native,'shown':True,'enabled':True,
                'fallback':False,'cancel':False} for i,native in enumerate([0] if result else [0,2,3])]}}


def query(actual,payload,key):
    return {'queried_snapshot_id':actual['snapshot_id'],'queried_revision':actual['revision'],
        'queried_native_revision':actual['native_revision'],'date_raw':actual['date_raw'],'game_pid':901,
        'connection_generation':1,'player_character_id':31254,'native_result':{key:payload}}


def assembly(actual,data):
    ids=[31254]+list(range(70000,70050))
    payload={'available':True,'date_raw':actual['date_raw'],'read_only':True,'predicates_complete':True,
        'faith_id':107,'played_rite_id':169,'complete_native_faith_member_ids':ids,
        'complete_native_faith_rite_ids':[169],
        'members':[{'character_id':cid,'faith_id':107,'rite_id':169,'complete':True,
            'alive':True,'adult':True,'imprisoned':False,'incapable':False,'is_ai':cid!=31254,
            'effective_learning':16} for cid in ids],
        'rites':[{'rite_id':169,'complete':True,'native_county_count':1,'county_title_ids':[2231]}]}
    return query(actual,payload,'confucian_assembly_predicates')


def cache(actual,data,bad=False):
    ids=data['baseline_cached_succession'][:-5] if bad else data['baseline_cached_succession']
    return query(actual,{'available':True,'date_raw':actual['date_raw'],'read_only':True,'roster_complete':True,
        'complete_cached_successor_ids':ids,'native_count':len(ids)},'actor_cached_succession')


class Guards(unittest.TestCase):
    def setUp(self): self.data=adapter.contract();self.actual=frame()

    def test_formal_admission_is_observation_without_precreated_title(self):
        source=packet(self.actual,self.data);old=copy.deepcopy(source)
        actual=adapter.admit_saved_startup_event({'expected':self.data['expected']},self.actual,source)
        self.assertEqual(actual['proof']['actual_numeric_terms'],{'serial':3,'nonce':6,'phase':2})
        self.assertEqual(actual['proof']['native_option_indices'],[0,2,3])
        self.assertIs(actual['business_pass'],False);self.assertEqual(source,old)

    def test_old_or_crossed_numeric_event_or_revision_refuses_admission(self):
        changes=[lambda p:p.update(queried_revision=99),
            lambda p:p['current_event_window_context'].update(event_definition_key='lyd_factory_diag.20'),
            lambda p:p['current_event_window_context']['root_scope']['typed_identity'].update(character_id=65865),
            lambda p:p['current_event_window_context']['saved_scopes'][2]['scope']['numeric_value'].update(integer_value='5'),
            lambda p:p['current_event_window_context']['options'][0].update(native_option_index=1),
            lambda p:p['current_event_window_context']['options'][0].update(enabled=False)]
        for change in changes:
            value=packet(self.actual,self.data);change(value)
            with self.subTest(change=change),self.assertRaises(ValueError):
                adapter.observe_event(self.actual,value,self.data['expected'],self.data)

    def test_fresh_G2_requires_full_roster_and_current_owner(self):
        reader=SimpleNamespace(HEAD='f'*40)
        witness=adapter.native_predicates(self.actual,assembly(self.actual,self.data),{'actual':'identity'},'a'*64,self.data,reader)
        self.assertEqual(len(witness['characters']),51)
        self.assertEqual(witness['human_character_ids'],[31254]);self.assertEqual(witness['rite_counties'],{'169':1})
        for key,value in [('game_pid',999),('connection_generation',2),('queried_revision',3)]:
            raw=assembly(self.actual,self.data);raw[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                adapter.native_predicates(self.actual,raw,{},'a'*64,self.data,reader)

    def test_missing_or_unknown_G2_predicates_cannot_use_historical_certificate(self):
        for change in [lambda p:p.update(predicates_complete=False),lambda p:p['members'].pop(),
            lambda p:p['members'][0].update(complete=False),lambda p:p['members'][0].update(is_ai=None),
            lambda p:p['rites'][0].update(native_county_count=2)]:
            raw=assembly(self.actual,self.data);change(raw['native_result']['confucian_assembly_predicates'])
            with self.subTest(change=change),self.assertRaises(ValueError):
                adapter.native_predicates(self.actual,raw,{},'a'*64,self.data,SimpleNamespace(HEAD='f'*40))

    def test_complete_changed_cache_is_observed_for_saved_red_evidence(self):
        ids=adapter.observe_cache(self.actual,cache(self.actual,self.data,bad=True))
        self.assertEqual(len(ids),40);self.assertNotEqual(ids,self.data['baseline_cached_succession'])
        raw=cache(self.actual,self.data);raw['native_result']['actor_cached_succession']['roster_complete']=False
        with self.assertRaises(ValueError): adapter.observe_cache(self.actual,raw)

    def test_no_completed_result_has_no_business_or_B5_credit(self):
        with tempfile.TemporaryDirectory() as temp:
            result=adapter.verify_case({'product':'li-yu-dao','case':'i3b-formal-b4','case_contract':self.data,'output':temp})
            self.assertIs(result['business_pass'],False)
            self.assertEqual(result['status'],'NOT_RUN_OR_PRESERVED_FAILURE')


def protection_fixture():
    reader=SimpleNamespace(one=lambda rows,key:next((r['value'] for r in rows if r['key']==key),None),
        replace_no_head=lambda value:value,number=lambda variables,key,required=False:None)
    top=[{'key':'culture','value':'4'}]
    alive=[{'key':'gold','value':[{'key':'value','value':'10'}]},
        {'key':'piety','value':[{'key':'currency','value':'20'}]},
        {'key':'prestige','value':[{'key':'currency','value':'30'}]},
        {'key':'lifestyle_xp','value':[{'key':'learning_lifestyle','value':'40'}]},
        {'key':'stress','value':'0'}]
    variables={'lyd_c2_completed_joins':{'number':'2'},'lyd_c2_serial':{'number':'3'},
        'lyd_r4_reset_count':{'number':'6'},'lyd_school_cooldown':{'tick':100}}
    actor={'character_id':31254,'rite_id':169,'entries':top,'alive_data':alive,'variables':variables,
        'AST_sha256':'c'*64,'landed_data':[{'key':'domain','value':[{'key':None,'value':'2230'},{'key':None,'value':'90001'}]},
            {'key':'laws','value':[{'key':None,'value':'old_law'}]},
            {'key':'succession','value':[{'key':None,'value':'40526'}]}]}
    titles={i:{'AST_sha256':str(i),'holder':31254}for i in (2230,2231,2232,2235,2262,2263,2264)}
    graph={'tenet_doctrine_rows':[{'key':'doctrine','value':'qualified'}],'AST_sha256':'g','variables':{}}
    baseline={'political7':{str(k):{'AST_sha256':v['AST_sha256'],'holder':'31254'}for k,v in titles.items()},
        'character_protections':{'31254':{'rite':'169','protected_top':{'culture':'4'},'protected_alive':{}}},
        'actor_protected_landed':copy.deepcopy(actor['landed_data']), 'actor_domain_ids':[2230],
        'graphs':{'faiths':{'107':copy.deepcopy(graph),'104':copy.deepcopy(graph)},'rites':{'169':copy.deepcopy(graph)}},
        'wallet':{'gold':'10','piety':'20','prestige':'30'},'XP':'40','saved_stress':'0',
        'C2_history':{'lyd_c2_completed_joins':variables['lyd_c2_completed_joins']},
        'C2_nonce_serial':variables['lyd_c2_serial'],'reset_count':variables['lyd_r4_reset_count'],
        'school_study_CD':{'lyd_school_cooldown':variables['lyd_school_cooldown']},'Rite_CD_locks':{'169':{'old_lock':None}}}
    baseline['actor_protected_landed'][0]['value'].pop()
    scan={'actor':actor,'selected':{31254:actor},'titles':titles,'held_by_protected':{31254:[2230,90001]},
        'faith_id':107,'actual_rites':[169],'faiths':{107:copy.deepcopy(graph),104:copy.deepcopy(graph)},'rites':{169:copy.deepcopy(graph)}}
    state={'stage':'success_postcommit','native_title':{'title_id':90001},'identity':{},'checkpoint_sha256':'a'*64,
        'saved_faith_semantics_version':'v2','faith_expected_factory_AST_delta':{'matches':True}}
    return reader,scan,baseline,state


class CompleteProtection(unittest.TestCase):
    def test_existing_complete_comparison_keeps_landed_wallet_history_CD_and_graphs(self):
        reader,scan,baseline,state=protection_fixture()
        result=adapter.evaluate_protection(scan,baseline,state,reader)
        self.assertTrue(result['protection_checks_match'])
        names={row['name'] for row in result['checks']}
        self.assertTrue({'actor_complete_protected_landed_projection','historical_0240_wallet_gold',
            'learning_XP_unchanged','C2_history_lyd_c2_completed_joins','Rite_169_complete_existing_CD_locks',
            'current_Faith_full_AST_only_declared_factory_delta'} <= names)

    def test_prior_failed_succession_and_political_AST_changes_fail_without_normalizing(self):
        for change in [lambda s:s['actor']['landed_data'][-1]['value'].append({'key':None,'value':'99999'}),
            lambda s:s['titles'][2230].update(AST_sha256='changed')]:
            reader,scan,baseline,state=protection_fixture();change(scan)
            self.assertFalse(adapter.evaluate_protection(scan,baseline,state,reader)['protection_checks_match'])

    def test_wallet_history_and_tenet_drift_each_fail(self):
        changes=[lambda s:s['actor']['alive_data'][0]['value'][0].update(value='9'),
            lambda s:s['actor']['variables'].update(lyd_c2_completed_joins={'number':'1'}),
            lambda s:s['faiths'][104].update(AST_sha256='changed'),
            lambda s:s['rites'][169]['variables'].update(old_lock={'tick':999})]
        for change in changes:
            reader,scan,baseline,state=protection_fixture();change(scan)
            self.assertFalse(adapter.evaluate_protection(scan,baseline,state,reader)['protection_checks_match'])


class FakeClient:
    def __init__(self,root,data,bad=False,reject=False):
        self.root,self.data,self.bad,self.reject=root,data,bad,reject
        self.instance,self.revision=119,2;self.calls=[];self.outputs={}
    def retain_process(self): return {'retained':True}
    def guard(self):return 500
    def snapshot(self,require_event_free=True):return frame(self.instance,self.revision)
    def execute_plan(self,steps,name,timeout=None):
        step=steps[0];tool=step['tool'];self.calls.append((tool,copy.deepcopy(step['args'])))
        actual=self.snapshot(False)
        if tool=='ck3_query_current_event_window_context_v1':result=packet(actual,self.data,self.instance!=119)
        elif tool=='ck3_save_checkpoint':self.revision+=1;result={'accepted':True,'step':'save-checkpoint','checkpoint':{'fake':name}}
        elif tool=='ck3_query_confucian_assembly_predicates_v1':result=assembly(actual,self.data)
        elif tool=='ck3_query_confucian_religious_title_v1':result={}
        elif tool=='ck3_query_actor_cached_succession_v1':result=cache(actual,self.data,bad=self.bad and self.instance!=119)
        elif tool=='ck3_select_event_option':
            if self.reject:raise TimeoutError('actual unknown select ACK')
            self.instance=777;self.revision+=1
            result={'accepted':True,'option_index':0,'option_number':1,'event_instance_id':119}
            self.last_selected=copy.deepcopy(result)
        else:raise AssertionError(tool)
        return [{'ok':True,'result':result}]
    def checkpoint(self,name,value):
        self.outputs[name]=value
        (self.root/(name+'.json')).write_text(json.dumps(value),encoding='utf-8')


def saved_facts(context,checkpoint,actual,assembly_query,title,data,post=False):
    return {'protection_match':not(post and context.get('bad_after')),'saved_business_match':True,
        'complete_cached_successor_ids':data['baseline_cached_succession'][:-5] if post and context.get('bad_after') else data['baseline_cached_succession'],
        'protection_checks':[{'matches':not(post and context.get('bad_after'))}for _ in range(88 if post else 87)],
        'saved_business_checks':[{'matches':True}], 'new_title_id':90001 if post else None}


class OnceOnly(unittest.TestCase):
    def test_fresh_B3_queries_two_saves_then_only_one_mutation_and_no_B5_credit(self):
        data=adapter.contract()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);client=FakeClient(root,data)
            context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp}
            with patch.object(adapter,'read_saved',side_effect=saved_facts):facts=adapter.run_case(context,client)
            self.assertTrue(facts['B4_pass']);self.assertFalse(facts['B5_pass']);self.assertFalse(facts['formal_institution_pass'])
            tools=[tool for tool,args in client.calls]
            self.assertEqual(tools.count('ck3_select_event_option'),1);self.assertEqual(tools.count('ck3_save_checkpoint'),2)
            self.assertLess(tools.index('ck3_query_confucian_assembly_predicates_v1'),tools.index('ck3_select_event_option'))
            verified=adapter.verify_case(context);self.assertTrue(verified['business_pass'])

    def test_actual_common_selection_dto_without_native_option_index_reaches_post_save(self):
        # Actual R47 common selection uses option_index; native_option_index is
        # an event-presentation field, absent from this action response.
        data=adapter.contract()
        with tempfile.TemporaryDirectory() as temp:
            client=FakeClient(Path(temp),data)
            context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp}
            with patch.object(adapter,'read_saved',side_effect=saved_facts):
                facts=adapter.run_case(context,client)
            self.assertEqual(client.last_selected['option_index'],0)
            self.assertNotIn('native_option_index',client.last_selected)
            self.assertTrue(facts['B4_pass'])
            self.assertEqual(sum(tool=='ck3_save_checkpoint'for tool,args in client.calls),2)
            self.assertIn('i3b-b4-post-saved-facts',client.outputs)
        for invented_alias in (False,True):
            with self.subTest(invented_alias=invented_alias),tempfile.TemporaryDirectory() as temp:
                client=FakeClient(Path(temp),data);original=client.execute_plan
                def wrong_shape(steps,name,timeout=None):
                    rows=original(steps,name,timeout)
                    if steps[0]['tool']=='ck3_select_event_option':
                        rows[0]['result'].pop('option_index')
                        if invented_alias:rows[0]['result']['native_option_index']=0
                    return rows
                context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp}
                with patch.object(client,'execute_plan',side_effect=wrong_shape),patch.object(adapter,'read_saved',side_effect=saved_facts),self.assertRaises(ValueError):
                    adapter.run_case(context,client)
                self.assertEqual(sum(tool=='ck3_select_event_option'for tool,args in client.calls),1)

    def test_changed_cache_still_saves_post_and_retains_false_88_checks(self):
        data=adapter.contract()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);client=FakeClient(root,data,bad=True)
            context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp,'bad_after':True}
            with patch.object(adapter,'read_saved',side_effect=saved_facts):facts=adapter.run_case(context,client)
            self.assertFalse(facts['business_pass']);self.assertEqual(len(facts['B4']['protection_checks']),88)
            self.assertEqual(sum(tool=='ck3_save_checkpoint'for tool,args in client.calls),2)
            self.assertFalse(adapter.verify_case(context)['business_pass'])

    def test_unknown_select_ack_is_never_replayed(self):
        data=adapter.contract()
        with tempfile.TemporaryDirectory() as temp:
            client=FakeClient(Path(temp),data,reject=True)
            context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp}
            with patch.object(adapter,'read_saved',side_effect=saved_facts),self.assertRaises(TimeoutError):
                adapter.run_case(context,client)
            self.assertEqual(sum(tool=='ck3_select_event_option'for tool,args in client.calls),1)

    def test_failed_fresh_B3_never_submits(self):
        data=adapter.contract()
        with tempfile.TemporaryDirectory() as temp:
            client=FakeClient(Path(temp),data)
            context={'product':'li-yu-dao','case':'i3b-formal-b4','run_id':'fake-run','case_contract':data,'output':temp}
            with patch.object(adapter,'read_saved',return_value={'protection_match':False}),self.assertRaises(ValueError):
                adapter.run_case(context,client)
            self.assertFalse(any(tool=='ck3_select_event_option'for tool,args in client.calls))


if __name__=='__main__': unittest.main(verbosity=2)
