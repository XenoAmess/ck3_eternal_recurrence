"""NoGame: real public prepare/run/verify and CaseClient day/capture admission.

Only original transport/engine identity and Root financial-review data are authored ports.
These records do not prove any actual scene, death, custody, transfer or notification.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import ck3_mod_acceptance_prepare as preparation
import ck3_mod_acceptance_client as client_module
import test_continuous14_clock_diagnostic as prepare_fixture
import test_issuer_refund_toast_case as phase_fixture
import test_news_delivery_daily_case as day_fixture

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'tools/ck3_mod_acceptance_cases/financial_markets_crisis_scenes20_engine_fixture.json'


class Crisis20RunPort(phase_fixture.RefundRunPort):
    def __init__(self,owner,context,responses,day_port):
        super().__init__(owner,context,responses,None);self.day_port=day_port
        self._process=copy.deepcopy(day_port._process);self.pair_calls=[];self.pair_mode='empty';self.fail_pair=None;self.clock=None
        # Only the transport boundary is authored: these two completed SAVE rows
        # model the original S1/S2 status, not physical SAVE or money evidence.
        self.hostrows=[{'id':'authored-S'+str(i),'plan':{'tool':'ck3_save_checkpoint'},'ok':True,
            'finished_at':'authored-time','error':None,'result':{}}for i in (1,2)]
    def guard(self,reserve=90,**kwargs):
        self.owner.assertEqual(reserve,180)
        return {'steps':copy.deepcopy(self.hostrows),'control_inflight':False}
    def log_bytes(self):
        return ('\n'.join(['XFMAT: TEST PASS controlled_crisis20_'+part+'_recorded' for part in ('setup','dispatch','reentry')])).encode()
    def advance_day(self,**kwargs):
        self.day_calls.append(copy.deepcopy(kwargs))
        actual=self.day_port.advance_day(**kwargs);self.date=self.day_port.date
        capture=adapter.read_json(actual['current_toast_capture']['path'])
        self.hostrows.extend(adapter.read_json(capture['actual_results']['path'])['rows']);self.latest=capture
        self.responses[adapter.CRISIS20_PHASES[2][0]]['evidence'].append(actual['current_toast_capture'])
        return actual
    def execute_plan(self,steps,name,timeout=None,reserve=90):
        self.owner.assertTrue(adapter.crisis20_plan_matches(self.context,steps,name,timeout));self.owner.assertEqual(reserve,180)
        self.pair_calls.append((copy.deepcopy(steps),self.clock()if self.clock else 0))
        rows=[]
        for index,(step,query)in enumerate(zip(steps,self.latest['queries'])):
            dto=copy.deepcopy(adapter.read_json(query['dto']['path']));sequence=1000+len(self.pair_calls)*2+index
            dto.update(query_sequence=str(sequence),completed_application_frame=str(sequence),delivery_confirmed=False)
            if self.pair_mode=='empty':dto.update(stage='empty',queue_count=0,title='',description='',saved_gui_scopes=[])
            else:dto.update(stage='visible',queue_count=1,title='Same authored software head',description='No live delivery evidence')
            row={'id':step['id'],'plan':copy.deepcopy(step),'ok':True,'finished_at':'authored-software-time','error':None,
                'result':dto,'after_snapshot':self.day_port.full(self.date)}
            if self.fail_pair==len(self.pair_calls):row['result']['result_unknown']=True
            rows.append(row)
        self.hostrows.extend(copy.deepcopy(rows))
        adapter.write_once(self.output/'plans'/(name+'.json'),{'steps':steps})
        adapter.write_once(self.output/(name+'.actual-results.json'),{'rows':rows,'business_PASS_inferred':False})
        return rows
    def checkpoint(self,name,value):
        result=super().checkpoint(name,value)
        if name.endswith('-passive-window'):
            self.responses[adapter.CRISIS20_PHASES[2][0]]['evidence'].append(adapter.pin(result))
        return result


class ControlledCrisis20CaseTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix='crisis20-NoGame-');self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.context=prepare_fixture.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(case=adapter.CRISIS20_CASE,case_contract=json.loads(CONFIG.read_bytes()),
            run_id='authored-crisis20-no-Game',case_spec={'budgets':{'command_timeout':300}})
        self.actor=self.context['saved_campaign']['player_id'];self.date=self.context['saved_campaign']['date_raw']
        self.request={'schemaVersion':3,'caseId':adapter.CRISIS20_CASE,'controlledFixtureOnly':True,
            'playerAccountId':'21','aidCreditorAccountId':'22','scenes':[{'sceneId':i,'accountId':str(i)}for i in range(1,21)],
            'controls':dict(zip(('childAccountId','inheritedAccountId','assetAccountId','aidAccountId','restructureAccountId'),map(str,range(23,28))))}
        self.request_pin=self.put('request.json',self.request)
        self.source=self.archive('source',self.date)
        payload=adapter.read_json(self.source['path'])['archive']
        self.context['saved_campaign'].update(save=payload['path'],bytes=payload['bytes'],sha256=payload['sha256'])
        self.fixture=self.root/'authored-fixture';self.fixture.mkdir()
        files={}
        for name,value in [('descriptor.mod',b'name="Authored fixture; never a Game"\n'),('_xfma_request.json',json.dumps(self.request).encode())]:
            p=self.fixture/name;p.write_bytes(value);q=adapter.pin(p);files[name]={k:q[k]for k in ('bytes','sha256')}
        producers=[]
        for name in ('xfm_crisis_scenes.txt','xfm_crisis_progression.txt'):
            original=ROOT/('mod_financial_markets/common/scripted_effects/'+name)
            dst=Path(self.context['case_inputs']['product_dir'])/('common/scripted_effects/'+name)
            dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(original.read_bytes());producers.append(adapter.pin(original))
        self.manifest_value={'schema':'ck3-mod-acceptance-prebuilt-fixture-v1','product':'financial-markets',
            'case_id':adapter.CRISIS20_CASE,'machine_id':'software-machine','observed_at_utc':'2026-11-23T00:00:00Z',
            'fixture_root':str(self.fixture.resolve()),'producer_source_pins':producers,'files':files,
            'receipt':{'required_markers':['XFMAT: TEST PASS controlled_crisis20_'+v+'_recorded'for v in ('setup','dispatch','reentry')],
                'required_product_markers_minimum':{},'fixture_contains_business_effects':True}}
        self.manifest=self.put('fixture.json',self.manifest_value)
        self.context['runtime_manifest']=self.put('runtime.json',{'machine_id':'software-machine'})
        self.context['case_inputs'].update(prebuilt_fixture_manifest=self.manifest,
            controlled_crisis20={'schema':'ck3-controlled-crisis20-input-v1','request':self.request_pin,'source_archive':self.source})
        self.note=self.put('authored-original-Root-review-port.json',{'software_only':True,'not_engine':True})
        self.responses=self.phases()

    def put(self,name,value):
        path=self.root/name;path.write_text(json.dumps(value),encoding='utf-8');return adapter.pin(path)
    def archive(self,name,date):
        return phase_fixture.IssuerRefundToastCaseTests.archive(self,name,date)
    def phase(self,index,data):
        name,_,required=adapter.CRISIS20_PHASES[index]
        return {'run_id':self.context['run_id'],'reviewer':'/root','assertions':{k:True for k in required},
            'evidence':[self.note]+[data[k]for k in ('archive','audit','raw','whole')],'crisis20':data}
    def phases(self):
        phases={}
        stages=[]
        for index,date in enumerate((self.date,self.date,self.date+14*24)):
            stages.append({'schema':['ck3-crisis20-baseline-v1','ck3-crisis20-terminal-v1','ck3-crisis20-retained-v1'][index],
                'archive':self.archive('stage'+str(index),date),'audit':self.note,'raw':self.note,'whole':self.note})
        stages[0]['role_bindings']=[{'account_id':str(i),'actor_id':str(1000+i),'evidence':self.note}for i in range(1,28)]
        stages[0]['role_bindings'][20]['actor_id']=str(self.actor)
        stages[1]['scenes']=[{'scene_id':i,'status':'OBSERVED','account_id':str(i),'actor_id':str(1000+i),
            'claim_native_id':str(2000+i),'news_native_id':str(3000+i),'inheritance':'NO_HEIR_FROZEN','evidence':self.note}for i in range(1,21)]
        stages[1]['controls']=[{'role':role,'status':'OBSERVED','evidence':self.note}for role in ('player','child','estate','asset','aid','restructure')]
        stages[2]['journal']=[{'scene_id':i,'status':'OBSERVED','news_native_id':str(3000+i),'evidence':self.note}for i in range(1,21)]
        stages[2]['local_visible']=[{'scene_id':i,'status':'NOT_OBSERVED','capture':None,'joins':[],'localization_sources':[]}for i in range(1,21)]
        for i,stage in enumerate(stages):phases[adapter.CRISIS20_PHASES[i][0]]=self.phase(i,stage)
        return phases
    def prepare(self):
        return adapter.prepare_case(self.context)
    def day_port(self):
        port=day_fixture.ControlledDebtDayCompositionTests.port(self)
        port.selection.case={'id':adapter.CRISIS20_CASE,'normal_close':{'reserve_seconds':180}}
        return port
    def exercise(self):
        self.prepare();port=Crisis20RunPort(self,self.context,self.responses,self.day_port())
        with patch.object(client_module,'native_day_request_count',return_value=0):
            facts=adapter.run_case(self.context,port)
        return facts,adapter.verify_case(self.context),port

    def test_real_prepare_resolves_saved_poststart_private_engine_cache_and_new_source_binding(self):
        with patch.object(preparation,'_engine',wraps=preparation._engine)as observed:
            result=self.prepare()
        self.assertGreater(observed.call_count,0);self.assertEqual(result['startup']['mode'],'saved_campaign')
        self.assertFalse(result['business_pass']);self.assertNotIn('_selected_engine',json.dumps(result))
        self.assertEqual(adapter.read_json(Path(self.context['state_dir'])/'profile/mod-content/fixture/_case_contract.json')['config']['post_start'],self.context['case_inputs']['post_start'])
        self.assertEqual(adapter._c20_inputs(self.context)['request'],self.request)

    def test_real_generic_run_verify_separates_twenty_Root_reviewed_branches_journal_and_missing_visibility(self):
        facts,verified,port=self.exercise()
        self.assertEqual(facts['crisis20_terminal_scenes_observed'],20);self.assertEqual(facts['crisis20_journal_scenes_observed'],20)
        self.assertEqual(facts['crisis20_local_visible_scenes_observed'],0);self.assertTrue(facts['crisis20_backend_qualified'])
        self.assertFalse(facts['case_contract_qualified']);self.assertEqual(verified['result_boundary'],'PARTIAL')
        self.assertFalse(facts['local_twenty_scene_delivery_observed']);self.assertFalse(verified['business_pass']);self.assertFalse(verified['all_human_delivery_pass'])
        self.assertEqual(len(port.day_calls),14);self.assertEqual(len(port.day_port.calls),14)
        self.assertEqual(verified['crisis20_terminal_scenes_observed'],20)

    def test_unobserved_branch_retains_partial_without_borrowing_news_or_raising_to_twenty(self):
        body=self.responses[adapter.CRISIS20_PHASES[1][0]]['crisis20'];final=self.responses[adapter.CRISIS20_PHASES[2][0]]['crisis20']
        body['scenes'][0].update(status='NOT_OBSERVED',news_native_id=None,inheritance='UNKNOWN')
        final['journal'][0].update(status='NOT_OBSERVED',news_native_id=None)
        facts,verified,_=self.exercise()
        self.assertEqual(facts['crisis20_terminal_scenes_observed'],19);self.assertFalse(facts['case_contract_qualified'])
        self.assertEqual(verified['result_boundary'],'PARTIAL');self.assertFalse(verified['product_release_pass'])

    def test_request_rejects_forged_context_actor_bits_aliases_and_wrong_manifest_before_engine(self):
        for mutate in (lambda v:v.update(isAI=True),lambda v:v['scenes'][0].update(trait='shy'),
                lambda v:v['scenes'][0].update(accountId='2'),lambda v:v.update(controlledFixtureOnly=1),
                lambda v:v['scenes'][0].update(sceneId=True)):
            value=copy.deepcopy(self.request);mutate(value)
            with self.assertRaises(ValueError):adapter._c20_request(value)
        bad=copy.deepcopy(self.context);bad['case']='news-crisis'
        with self.assertRaises(ValueError):adapter._crisis20_enabled(bad)
        product=Path(self.context['case_inputs']['product_dir'])/'common/scripted_effects/xfm_crisis_progression.txt'
        product.write_text('# authored stale product\n',encoding='utf-8')
        with patch.object(preparation,'_engine')as engine:
            with self.assertRaisesRegex(ValueError,'terminal/selector'):self.prepare()
        engine.assert_not_called()

    def test_actual_caseclient_plan_admits_exact_three_rows_180_reserve_only_for_new_case(self):
        port=self.day_port()
        with patch.object(client_module,'native_day_request_count',return_value=0):
            row=adapter._advance_fixture_day(port,self.context['case_contract'],1,300)
        capture=adapter.read_json(row['current_toast_capture']['path'])
        self.assertEqual(capture['schema'],'ck3-controlled-crisis20-day-capture-v1');self.assertEqual(capture['case'],adapter.CRISIS20_CASE)
        self.assertEqual(len(port.calls),1);self.assertEqual(len(port.calls[0]),3);self.assertTrue(all(v==180 for v in port.reserves))
        steps=port.calls[0];self.assertTrue(adapter.crisis20_plan_matches(self.context,steps,capture['name'],300))
        invalid=copy.deepcopy(steps);invalid[1]['tool']='ck3_activate_scripted_widget_control_v1'
        self.assertFalse(adapter.crisis20_plan_matches(self.context,invalid,capture['name'],300))
        original=json.loads((CONFIG.parent/'financial_markets_news_crisis.json').read_bytes())
        old=dict(self.context,case='news-crisis',case_contract=original)
        self.assertFalse(adapter.crisis20_plan_matches(old,steps,capture['name'],300))

    def test_metadata_reader_refuses_small_SAVE_and_wrong_machine_without_payload_consumer(self):
        bad=copy.deepcopy(self.context);ref=self.put('not-json.ck3',{'fake':'metadata'})
        bad['case_inputs']['controlled_crisis20']['request']=ref
        with self.assertRaisesRegex(ValueError,'JSON'):adapter._c20_inputs(bad)
        archive=adapter.read_json(self.source['path']);archive['machine_id']='wrong-machine'
        bad=copy.deepcopy(self.context);bad['case_inputs']['controlled_crisis20']['source_archive']=self.put('wrong-machine.json',archive)
        with self.assertRaisesRegex(ValueError,'another machine'):adapter._c20_inputs(bad)

    def test_registry_appends_one_exact_case_and_does_not_relax_the_original_natural_case(self):
        product=json.loads((ROOT/'tools/ck3_mod_acceptance_products.json').read_bytes())['products']['financial-markets']
        self.assertEqual(len(product['cases']),25);self.assertEqual(product['cases'][-2]['id'],adapter.CRISIS20_CASE)
        self.assertEqual(product['cases'][-1]['id'],'futures-risk-engine-fixture')
        natural=json.loads((CONFIG.parent/'financial_markets_news_crisis.json').read_bytes())
        self.assertEqual(natural['maximum_natural_days'],14);self.assertNotIn('controlled_fixture_contract',natural)
        self.assertTrue(any('no forced death' in x for x in natural['source_save_requirements']))

    def sampling_port(self):
        self.prepare();port=Crisis20RunPort(self,self.context,self.responses,self.day_port())
        for index in (0,1):
            name=adapter.CRISIS20_PHASES[index][0]
            adapter.write_once(port.output/(name+'-accepted.json'),self.responses[name])
        with patch.object(client_module,'native_day_request_count',return_value=0):
            row=port.advance_day(days=1,timeout=300,allow_event_boundary=True,allow_actor_change=False,current_toast_queries=True)
        return port,row['current_toast_capture']

    def test_actual_passive_sampler_spaces_fifteen_pairs_without_advancing_or_inventing_rotation(self):
        port,capture=self.sampling_port();port.pair_mode='visible';wall=[100.0];port.clock=lambda:wall[0]
        def sleep(seconds):wall[0]+=seconds
        with patch.object(time,'monotonic',side_effect=port.clock),patch.object(time,'sleep',side_effect=sleep):
            ref=adapter._c20_sample_day(port,self.context,capture)
        window=adapter.read_json(ref['path']);self.assertEqual(len(window['pairs']),15)
        self.assertEqual(len(port.day_calls),1);self.assertFalse(window['rotation_guaranteed']);self.assertFalse(window['delivery_confirmed'])
        self.assertTrue(all(b[1]-a[1]>=2.99 for a,b in zip(port.pair_calls,port.pair_calls[1:])))
        self.assertEqual(len(adapter._c20_window(self.context,ref,{'evidence':[ref]},capture,self.date+24)),15)
        pair=adapter.read_json(window['pairs'][0]['path']);self.assertEqual(len(adapter.read_json(pair['actual_results']['path'])['rows']),2)
        self.assertTrue(all(s['tool']=='ck3_query_current_interface_toast_v1'for call,_ in port.pair_calls for s in call))

    def test_actual_passive_sampler_keeps_UNKNOWN_and_stops_without_another_submission_or_day(self):
        port,capture=self.sampling_port();port.fail_pair=1
        with self.assertRaisesRegex(ValueError,'without retry'):adapter._c20_sample_day(port,self.context,capture)
        self.assertEqual(len(port.pair_calls),1);self.assertEqual(len(port.day_calls),1)
        window=adapter.read_json(port.output/(port.latest['name']+'-passive-window.json'))
        self.assertEqual(window['reason'],'STOPPED_ORIGINAL_FAILURE_OR_PENDING_NO_RETRY');self.assertIsNotNone(window['failure'])
        self.assertEqual(len(window['attempted_ids']),2)
        pair=adapter.read_json(window['pairs'][0]['path'])
        self.assertTrue(adapter.read_json(pair['actual_results']['path'])['rows'][0]['result']['result_unknown'])

    def test_actual_passive_sampler_refuses_original_reserve_or_third_SAVE_before_queue(self):
        port,capture=self.sampling_port();port.hostrows.append({'id':'unexpected-S3','plan':{'tool':'ck3_save_checkpoint'},
            'ok':True,'finished_at':'authored-time','error':None,'result':{}})
        with self.assertRaisesRegex(ValueError,'without retry'):adapter._c20_sample_day(port,self.context,capture)
        self.assertEqual(port.pair_calls,[])
        self.assertFalse(adapter.crisis20_plan_matches(self.context,[{'kind':'tool','id':'bad','tool':'ck3_save_checkpoint','args':{}}],
            'case-natural-day-0001-passive-pair01',3))

    def test_real_caseclient_execute_plan_reserve_route_reaches_original_guard_only_for_exact_pair_and_case(self):
        port=self.day_port();name='case-natural-day-0001-passive-pair01'
        steps=[{'id':name+'-toast0'+str(i),'kind':'tool','tool':'ck3_query_current_interface_toast_v1','args':{}}for i in(1,2)]
        class OriginalGuardReached(Exception):pass
        with patch.object(port,'guard',side_effect=OriginalGuardReached):
            with self.assertRaises(OriginalGuardReached):
                client_module.CaseClient.execute_plan(port,steps,name,timeout=3,reserve=180)
            for invalid in (steps[:1],[dict(steps[0],tool='ck3_save_checkpoint'),steps[1]]):
                with self.assertRaises(ValueError):client_module.CaseClient.execute_plan(port,invalid,name,timeout=3,reserve=180)
            port.selection.case={'id':'debt-aid-news-engine-fixture','normal_close':{'reserve_seconds':180}}
            with self.assertRaises(ValueError):client_module.CaseClient.execute_plan(port,steps,name,timeout=3,reserve=180)

    def test_actual_passive_sampler_checks_reserve_before_any_query(self):
        port,capture=self.sampling_port()
        with patch.object(port,'remaining',return_value=182.0):
            with self.assertRaisesRegex(ValueError,'without retry'):adapter._c20_sample_day(port,self.context,capture)
        self.assertEqual(port.pair_calls,[])


    def test_actual_sampler_preserves_complete_pending_rows_and_missing_result_on_original_await_failure(self):
        port,capture=self.sampling_port();port.live=self.root/'authored-live';port.live.mkdir()
        pending=[]
        def fail_original_wait(steps,name,timeout=None,reserve=90):
            self.assertEqual(reserve,180);self.assertEqual(timeout,3)
            port.pair_calls.append((copy.deepcopy(steps),0))
            pending.extend([{'id':steps[0]['id'],'plan':copy.deepcopy(steps[0]),'ok':None,'finished_at':None,'error':None},
                {'id':steps[1]['id'],'plan':copy.deepcopy(steps[1]),'ok':None,'finished_at':None,'error':None,'result':None}])
            port.hostrows.extend(copy.deepcopy(pending))
            adapter.write_once(port.live/'native-report.json',{'phase':'hold','steps':port.hostrows})
            raise TimeoutError('Original await deadline; never replay')
        port.execute_plan=fail_original_wait
        port.read_report=lambda **kwargs:adapter.read_json(port.live/'native-report.json')
        with self.assertRaisesRegex(ValueError,'without retry'):adapter._c20_sample_day(port,self.context,capture)
        self.assertEqual(len(port.pair_calls),1);self.assertEqual(len(port.day_calls),1)
        window=adapter.read_json(port.output/(port.latest['name']+'-passive-window.json'));retained=window['failure_retention']
        self.assertNotIn('retention_error',retained)
        selected=adapter.read_json(retained['selected_original']['path'])
        self.assertEqual(selected['steps'],pending);self.assertNotIn('result',selected['steps'][0])
        self.assertIsNone(selected['steps'][1]['result']);self.assertEqual(len(retained['original_results']),1)
        self.assertIsNone(json.loads(Path(retained['original_results'][0]['original_result']['path']).read_bytes()))
        self.assertTrue(selected['source_report_observation']['observation_only_not_immutable_FilePin'])
        self.assertFalse(retained['new_query_or_await_or_retry'])
        # Later report mutation cannot revoke or rewrite the immutable capture or
        # turn the original pending action into NOT_DISPATCHED/success.
        frozen=copy.deepcopy(selected);(port.live/'native-report.json').write_text('{}',encoding='utf-8')
        self.assertEqual(adapter.read_json(retained['selected_original']['path']),frozen)


    def test_discovery_mode_prepares_only_with_explicit_exact_sidecar_and_cannot_enter_normal_credit(self):
        mode={'schema': 'ck3-controlled-crisis20-discovery-v1', 'discovery_only': True, 'read_only_finance': True, 'private_namespace': 'xfmc20d_', 'maximum_registry_rows': 65536, 'maximum_candidates': 52, 'maximum_typed_references': 104, 'per_role_maximum': 2, 'context_count': 20, 'case_credit': False}
        p=self.fixture/'_xfmc20_discovery_mode.json';p.write_text(json.dumps(mode),encoding='utf-8')
        self.manifest_value['files'][p.name]={k:v for k,v in adapter.pin(p).items()if k!='path'}
        self.manifest_value['receipt']['fixture_contains_business_effects']=False
        for relative in ('common/scripted_triggers/xfm_crisis_triggers.txt','common/script_values/xfm_debt_values.txt'):
            source=ROOT/'mod_financial_markets'/relative;target=Path(self.context['case_inputs']['product_dir'])/relative
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());self.manifest_value['producer_source_pins'].append(adapter.pin(source))
        self.manifest=self.put('discovery-fixture.json',self.manifest_value)
        self.context['case_inputs']['prebuilt_fixture_manifest']=self.manifest
        self.context['case_inputs']['controlled_crisis20']['discovery_only']=True
        self.prepare()
        self.assertTrue(adapter._c20_inputs(self.context,allow_discovery_preflight=True)['discovery_only'])
        with self.assertRaisesRegex(ValueError,'cannot grant normal'):adapter._c20_inputs(self.context)
        port=Crisis20RunPort(self,self.context,self.responses,self.day_port())
        with self.assertRaisesRegex(ValueError,'cannot grant normal'):adapter.run_case(self.context,port)
        self.assertEqual(port.day_calls,[]);self.assertEqual(port.pair_calls,[])

    def test_discovery_receipt_or_flag_without_the_exact_mode_cannot_prepare(self):
        context=copy.deepcopy(self.context);context['case_inputs']['controlled_crisis20']['discovery_only']=True
        with self.assertRaises(ValueError):adapter._c20_inputs(context,allow_discovery_preflight=True)
        context['case_inputs']['controlled_crisis20']['discovery_only']=1
        with self.assertRaisesRegex(ValueError,'Literal true'):adapter._c20_inputs(context,allow_discovery_preflight=True)


    def test_discovery_v2_real_prepare_requires_exact_full_role_capture_mode_and_still_cannot_grant_credit(self):
        mode={'schema':'ck3-controlled-crisis20-discovery-v2','discovery_only':True,'read_only_finance':True,'private_namespace':'xfmc20e_',
              'maximum_registry_rows':65536,'maximum_candidates':52,'maximum_typed_references':104,'per_role_maximum':2,'context_count':20,'case_credit':False,
              'complete_role_mask_bits':26,'complete_positive_recorded':True}
        p=self.fixture/'_xfmc20_discovery_mode.json';sequence=iter(range(8))
        def bind(actual):
            p.write_text(json.dumps(actual),encoding='utf-8')
            self.manifest_value['files'][p.name]={k:v for k,v in adapter.pin(p).items()if k!='path'}
            self.manifest=self.put('discovery-v2-'+str(next(sequence))+'.json',self.manifest_value)
            self.context['case_inputs']['prebuilt_fixture_manifest']=self.manifest
        self.manifest_value['receipt']['fixture_contains_business_effects']=False
        for relative in ('common/scripted_triggers/xfm_crisis_triggers.txt','common/script_values/xfm_debt_values.txt'):
            source=ROOT/'mod_financial_markets'/relative;target=Path(self.context['case_inputs']['product_dir'])/relative
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes());self.manifest_value['producer_source_pins'].append(adapter.pin(source))
        self.context['case_inputs']['controlled_crisis20']['discovery_only']=True
        bind(mode);self.prepare()
        self.assertTrue(adapter._c20_inputs(self.context,allow_discovery_preflight=True)['discovery_only'])
        with self.assertRaisesRegex(ValueError,'cannot grant normal'):adapter._c20_inputs(self.context)
        for key,value in [('private_namespace','xfmc20d_'),('complete_role_mask_bits',25),('complete_positive_recorded',False),('complete_positive_recorded',1)]:
            bad={**mode,key:value};bind(bad)
            with self.assertRaisesRegex(ValueError,'immutable discovery'):adapter._c20_inputs(self.context,allow_discovery_preflight=True)


if __name__=='__main__':unittest.main()
