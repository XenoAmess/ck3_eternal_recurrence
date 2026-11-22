"""Software only: real shared prepare/run/verify and CaseClient composition; no Game or delivery claim."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import ck3_mod_acceptance_client as client_module
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
import test_continuous14_clock_diagnostic as prepare_fixture
import test_futures_gui_transactions_case as archive_fixture
import test_issuer_refund_toast_case as issuer_fixture

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'tools/ck3_mod_acceptance_cases/financial_markets_news_delivery_daily.json'


class DayPort(issuer_fixture.CapturePort):
    """The inherited real CaseClient.advance_day only ports the actual queue/SDK boundary."""
    def __init__(self, owner, context):
        super().__init__(owner, context)
        self.selection.case = {'id': 'news-delivery-daily', 'normal_close': {'reserve_seconds': 180}}
        self.mode = 'empty'; self.query_order = []
        self.dto_mutation = getattr(owner, 'dto_mutation', None)

    def guard(self, reserve=90, **kwargs):
        report = super().guard(reserve, **kwargs)
        report['readiness'] = self.full(self.date)
        return report

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        rows = super().execute_plan(steps, name, timeout, reserve)
        self.query_order.extend([step['id'] for step in steps])
        for row in rows[1:]:
            dto = row['result']
            # Authored software rendered strings, never raw localization keys or live delivery evidence.
            dto['title'] = '新币进入市场'; dto['description'] = '一位发行者公布了新的市场状态。'
            for scope in dto['saved_gui_scopes']:
                if scope['name'] == 'xfm_news_actor': scope['identity'] = '31915'
            if self.mode == 'empty':
                dto.update(stage='empty', queue_count=0, title='', description='', saved_gui_scopes=[])
            if self.dto_mutation is not None:
                self.dto_mutation(dto)
        # The port owns authored software artifacts before the real capture author reads them.
        (self.output / (name + '.actual-results.json')).write_text(json.dumps({'rows': rows}), encoding='utf-8')
        return rows


class RunPort(DayPort):
    def __init__(self, owner, context):
        super().__init__(owner, context)
        self.operator_reviewer = '/root'; self._hold = 9999999999.; self.requests = []
        self._process = {'pid': 999, 'birth_filetime_100ns': '123'}

    def log_bytes(self): return b''

    def checkpoint(self, name, value):
        result = super().checkpoint(name, value)
        if name.endswith('-awaiting'):
            phase = name.removesuffix('-awaiting'); self.requests.append(phase)
            if phase == adapter.NEWS_DELIVERY_DAILY_PHASES[0][0]:
                response = self.owner.baseline
            else:
                response = self.owner.terminal(self)
            adapter.write_once(self.output / (phase + '-root-result.json'), response)
        return result


class NewsDeliveryDailyTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='news-delivery-daily-software-'); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.context = prepare_fixture.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(product='financial-markets', case='news-delivery-daily',
            case_contract=json.loads(CONFIG.read_bytes()), run_id='authored-news-delivery-daily',
            case_spec={'budgets': {'command_timeout': 300}})
        saved = self.context['saved_campaign']; self.date = saved['date_raw']; self.actor = saved['player_id']
        save = {k:saved[v] for k,v in [('path','save'),('bytes','bytes'),('sha256','sha256')]}
        self.source = self.put('source-archive.json', {'schema':'ck3-financial-checkpoint-archive-v1',
            'machine_id':'software-machine', 'exact_copy':True, 'same_file':False, 'date_raw':self.date, 'archive':save})
        self.context['case_inputs']['news_delivery_daily'] = {'source_archive':self.source, 'scenario_id':'authored-daily-news'}
        self.note = self.put('software-no-actual-Game-evidence.json', {'software_only':True})
        self.base = self.archive('baseline', self.date)
        self.baseline = self.phase(0, source_archive=self.source, baseline_archive=self.base,
            baseline_audit=self.note, baseline_raw=self.note, baseline_whole=self.note, cold_comparison=self.note)
        self.port = None; self.force_observed = False; self.report_mutation = None; self.dto_mutation = None

    def put(self, name, value):
        path = self.root / name; path.write_text(json.dumps(value), encoding='utf-8'); return adapter.pin(path)

    def archive(self, name, date):
        source = self.root / (name + '-source.ck3'); target = self.root / (name + '-external.ck3')
        source.write_bytes(('authored-software-' + name).encode()); target.write_bytes(source.read_bytes())
        receipt = copy.deepcopy(archive_fixture.ACTUAL_R37_ARCHIVE); actual = adapter.pin(source)
        receipt.update(machine_id='software-machine', source=actual, archive=adapter.pin(target), date_raw=date)
        receipt['original_checkpoint_result']['checkpoint'].update(path=actual['path'], size=actual['bytes'], sha256=actual['sha256'], date_raw=date)
        return self.put(name + '-archive.json', receipt)

    def phase(self, index, **extras):
        value = {'run_id':self.context['run_id'], 'reviewer':'/root',
            'assertions':{k:True for k in adapter.NEWS_DELIVERY_DAILY_PHASES[index][2]}, 'evidence':[], **extras}
        value['evidence'] = [self.source, self.base, self.note] if hasattr(self,'base') else [self.source,self.note]
        for item in extras.values():
            if isinstance(item,dict) and set(item)=={'path','bytes','sha256'} and item not in value['evidence']:value['evidence'].append(item)
        return value

    def terminal(self, port):
        captures = [adapter.pin(p) for p in sorted(port.output.glob('*-current-toast-capture.json'))]
        end = self.archive('terminal', port.date)
        value = self.phase(1, physical_archives=[self.base,end], terminal_audit=self.note,
            terminal_raw=self.note, terminal_whole=self.note, news_reconciliation=self.note,
            daily_captures=captures, toast={'status':'NOT_OBSERVED','reason':'Authored software EMPTY is not live delivery','evidence':[self.note]})
        value['evidence'] += [end,*captures]
        if self.force_observed:
            capture = adapter.read_json(captures[-1]['path']); joins = []
            for i,q in enumerate(capture['queries']):
                dto = adapter.read_json(q['dto']['path'])
                gui = [{'name':s['name'],'kind':'CHARACTER' if s['observed_tag']==4 else 'STORY',
                    'observedTag':s['observed_tag'],'available':True,'identity':s['identity'],'unavailableReason':''} for s in dto['saved_gui_scopes']]
                identity = {a:dto[b] for a,b in {'snapshotId':'snapshot_id','nativeRevision':'native_revision','publicRevision':'public_revision',
                    'gamePid':'game_pid','connectionGeneration':'connection_generation','querySequence':'query_sequence','ownerThreadId':'owner_thread_id',
                    'completedApplicationFrame':'completed_application_frame','viewerCharacterId':'viewer_played_character_id','dateRaw':'date_raw'}.items()}
                report = {'schema':'xfm-news-toast-source-join-candidate-v1','machineId':'software-machine',
                    'request':{'schemaVersion':1,'machineId':'software-machine','repository':self.context['repo_root'],
                        'toast':q['dto'],'save':adapter.read_json(end['path'])['archive'],'decoder':self.note},
                    'producers':{'authored_software_no_reader_execution':True},'newsScriptSources':[self.note],
                    'toast':{'identity':identity,'stage':'VISIBLE_PENDING_FRAME' if i==0 else 'VISIBLE',
                        'title':dto['title'],'description':dto['description'],'guiScopes':gui,'scriptScopes':[]},
                    'assessment':'UNAVAILABLE' if i==0 else 'LOCAL_NATIVE_JOIN_MATCH','reason':'NATIVE_OBJECT_NOT_VISIBLE' if i==0 else 'NONE',
                    'entries':[] if i==0 else [{'storyId':'90','sourceStoryId':'70','newsId':'140','eventId':'2','kind':7,'day':'290','scene':20,'actorCharacterId':31915}],
                    'sources':[] if i==0 else [{'storyId':'70','storyCycle':'xfm_finance_coin','factCounter':'2','lastFact':'2','kind':7,'scene':20,'actorCharacterId':31915}],
                    'passes':[] if i==0 else [{},{},{}], 'sourceJoinMatched':i==1,
                    'deliveryConfirmed':False,'allHumanDeliveryConfirmed':False,'gameStarted':False,'financialCertified':False}
                if self.report_mutation is not None:self.report_mutation(report,i)
                joins.append(self.put('join-' + str(i)+'.json',report))
            localizations = [adapter.pin(ROOT / ('mod_financial_markets/localization/'+folder+'/'+name)) for folder,name in
                [('simp_chinese','xfm_news_l_simp_chinese.yml'),('english','xfm_news_l_english.yml')]]
            value['toast'] = {'status':'OBSERVED','capture':captures[-1],'joins':joins,'localization_sources':localizations}
            value['evidence'] += joins+localizations
        return value

    def run_case(self, mode='empty'):
        adapter.prepare_case(self.context)
        port = RunPort(self,self.context); port.mode=mode; self.port=port
        with patch.object(client_module,'native_day_request_count',return_value=0):
            facts = adapter.run_case(self.context,port)
        return facts

    def test_real_saved_prepare_run_verify_three_empty_days_stop_without_business_credit(self):
        facts=self.run_case();self.assertEqual(len(self.port.calls),3);self.assertEqual(self.port.requests,[p[0]for p in adapter.NEWS_DELIVERY_DAILY_PHASES])
        self.assertEqual(facts['daily_attempts_with_queries'],3);self.assertEqual(facts['natural_days_advanced'],3)
        self.assertEqual(facts['status'],'NOT_OBSERVED');self.assertFalse(facts['case_contract_qualified'])
        review=adapter.verify_case(self.context);self.assertEqual(review['status'],'NOT_OBSERVED');self.assertFalse(review['business_pass'])

    def test_real_caseclient_day_is_one_plan_followed_immediately_by_exact_two_queries(self):
        self.run_case()
        for steps in self.port.calls:
            self.assertEqual(len(steps),3);self.assertEqual(steps[0]['kind'],'advance_day');self.assertEqual(steps[0]['days'],1)
            self.assertEqual([s['tool']for s in steps[1:]],['ck3_query_current_interface_toast_v1']*2)
        self.assertTrue(all(x==180 for x in self.port.reserves))

    def test_real_native_day_composition_does_not_fall_back_or_add_another_clock(self):
        adapter.prepare_case(self.context);port=DayPort(self,self.context);before=port.full(port.date);before['revision']=17
        with patch.object(client_module,'native_day_request_count',return_value=2), \
                patch.object(client_module,'fresh_native_day_before',return_value=before), \
                patch.object(client_module,'project_native_day',side_effect=lambda row,*a,**k:row):
            row=port.advance_day(allow_event_boundary=True,current_toast_queries=True)
        self.assertEqual(len(port.calls),1);first=port.calls[0][0]
        self.assertEqual(first['tool'],'ck3_execute_step');self.assertFalse(first['fresh_revision'])
        self.assertEqual(first['args'],{'step':client_module.NATIVE_DAY_STEP,'expected_revision':17})
        self.assertEqual(adapter.read_json(row['current_toast_capture']['path'])['case'],'news-delivery-daily')

    def test_real_prepare_json_boundary_resolves_poststart_and_keeps_original_config(self):
        before=copy.deepcopy(self.context['case_contract']);self.run_case();self.assertEqual(self.context['case_contract'],before)
        passive=Path(self.context['state_dir'])/'profile/mod-content/fixture/common/story_cycles/xfma_news_delivery_daily_passive.txt'
        self.assertTrue(passive.is_file());self.assertNotIn('effect',passive.read_text('utf-8-sig'))

    def test_visible_remote_news_candidate_stops_after_first_day_and_exact_join_gets_only_local_credit(self):
        self.force_observed=True;facts=self.run_case('visible');self.assertEqual(len(self.port.calls),1)
        self.assertTrue(facts['local_native_news_observed']);self.assertFalse(facts['business_pass'])
        self.assertFalse(facts['all_human_delivery_pass']);self.assertTrue(adapter.verify_case(self.context)['local_native_news_observed'])
        self.assertFalse(facts['localization_rendered_text_pass'])

    def test_wrong_source_event_revision_cannot_be_a_local_positive(self):
        self.force_observed=True
        self.report_mutation=lambda report,i:report['sources'][0].update(factCounter='3') if i else None
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_wrong_recipient_or_remote_actor_cannot_be_borrowed(self):
        self.force_observed=True
        self.report_mutation=lambda report,i:report['entries'][0].update(actorCharacterId=self.actor) if i else None
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_wrong_native_content_is_not_replaced_by_localization(self):
        self.force_observed=True
        original=DayPort.execute_plan
        def changed(port,*args,**kwargs):
            rows=original(port,*args,**kwargs)
            for row in rows[1:]:row['result']['title']='Unrelated title'
            name=args[1];(port.output/(name+'.actual-results.json')).write_text(json.dumps({'rows':rows}),encoding='utf-8')
            return rows
        with patch.object(DayPort,'execute_plan',changed),self.assertRaises(ValueError):self.run_case('visible')

    def test_typed_rendered_copy_must_not_replace_original_native_text(self):
        self.force_observed=True
        self.report_mutation=lambda report,i:report['toast'].update(title='Different authored rendered title')
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_missing_original_named_identity_is_not_filled_from_rendered_text_or_viewer(self):
        self.force_observed=True
        self.dto_mutation=lambda dto:dto.update(saved_gui_scopes=[s for s in dto['saved_gui_scopes']
            if s['name'] != 'xfm_news_display_entry'])
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_empty_original_rendered_description_cannot_be_a_local_positive(self):
        self.force_observed=True
        self.dto_mutation=lambda dto:dto.update(description='')
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_rendered_description_utf8_byte_limit_is_not_a_character_limit(self):
        self.force_observed=True
        self.dto_mutation=lambda dto:dto.update(description='财' * (32768 // 3 + 1))
        with self.assertRaises(ValueError):self.run_case('visible')

    def test_unknown_flags_and_bool_numeric_limits_are_rejected_before_prepare(self):
        config=self.context['case_contract']
        for key,value in [('maximum_daily_attempts',True),('stop_on_visible_candidate',1),('maximum_natural_days',4)]:
            bad=copy.deepcopy(self.context);bad['case_contract']['news_delivery_daily_contract'][key]=value
            with self.assertRaises(ValueError):adapter._news_delivery_daily_enabled(bad)
        self.assertEqual(config['news_delivery_daily_contract']['maximum_daily_attempts'],3)

    def test_old_issuer_and_continuous_contracts_do_not_gain_new_composition(self):
        for name in ['financial_markets_issuer_refund_toast.json','financial_markets_clock_cadence_continuous14.json']:
            c=copy.deepcopy(self.context);c['case_contract']=json.loads((CONFIG.parent/name).read_bytes());c['case']=c['case_contract']['case_id']
            self.assertFalse(adapter.news_delivery_daily_plan_matches(c,[], 'case-natural-day-0001',300))

    def test_plan_cannot_add_gui_rename_query_or_an_extra_day(self):
        self.run_case();steps=self.port.calls[0];name=steps[0]['id']
        for change in ['day','query','extra']:
            bad=copy.deepcopy(steps)
            if change=='day':bad[0]['days']=2
            elif change=='query':bad[1]['tool']='ck3_execute_step'
            else:bad.append(copy.deepcopy(bad[-1]))
            self.assertFalse(adapter.news_delivery_daily_plan_matches(self.context,bad,name,300))

    def test_third_day_failure_propagates_without_retry_or_fourth_day(self):
        original=CaseClient.advance_day;calls=[]
        def fail(client,*args,**kwargs):
            calls.append(1)
            if len(calls)==3:raise RuntimeError('Authored UNKNOWN third day')
            return original(client,*args,**kwargs)
        with patch.object(CaseClient,'advance_day',fail),self.assertRaises(RuntimeError):self.run_case()
        self.assertEqual(len(calls),3)

    def test_missing_one_original_capture_is_not_three_days_of_observation(self):
        self.run_case();path=self.port.output/'generic-product-case-result.json';facts=adapter.read_json(path)
        final=facts['root_phases'][adapter.NEWS_DELIVERY_DAILY_PHASES[1][0]];final['daily_captures'].pop()
        path.write_text(json.dumps(facts),encoding='utf-8')
        with self.assertRaises(ValueError):adapter.verify_case(self.context)

    def test_event_boundary_stops_without_query_retry_or_selecting_an_option(self):
        def boundary(port,*args,**kwargs):
            full=port.full(port.date)
            return {'result':{'requested_days':1,'requested_interval_complete':False,
                'event_boundary':{'kind':'authored-software-event-boundary'},'before':full,'after':full,'elapsed_hours':0}}
        with patch.object(CaseClient,'advance_day',boundary):facts=self.run_case()
        self.assertEqual(self.port.calls,[]);self.assertEqual(facts['daily_attempts_with_queries'],0)
        self.assertEqual(facts['natural_days_advanced'],0);self.assertEqual(facts['status'],'NOT_OBSERVED')

    def test_missing_original_capture_or_receipt_alias_is_rejected_by_real_verifier(self):
        self.run_case();path=self.port.output/'generic-product-case-result.json';facts=adapter.read_json(path)
        final=facts['root_phases'][adapter.NEWS_DELIVERY_DAILY_PHASES[1][0]];final['physical_archives'][1]=final['physical_archives'][0]
        path.write_text(json.dumps(facts),encoding='utf-8')
        with self.assertRaises(ValueError):adapter.verify_case(self.context)



class ControlledDebtDayCompositionTests(unittest.TestCase):
    """Real CaseClient admission/capture; only queue/SDK/Game responses are software ports."""
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='controlled-debt-day-software-');self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.context=prepare_fixture.Continuous14PrepareJsonBoundaryTests().context(self.root)
        self.context.update(product='financial-markets',case='debt-aid-news-engine-fixture',
            case_contract=json.loads((CONFIG.parent/'financial_markets_debt_aid_news_engine_fixture.json').read_bytes()),
            run_id='authored-controlled-debt-no-Game',case_spec={'budgets':{'command_timeout':300}})
        self.actor=self.context['saved_campaign']['player_id']

    def port(self,context=None):
        class DebtCapturePort(issuer_fixture.CapturePort):
            def guard(self,reserve=90,**kwargs):
                report=super().guard(reserve,**kwargs)
                report['readiness']=self.full(self.date)
                return report
        p=DebtCapturePort(self,context or self.context)
        p.selection.case={'id':'debt-aid-news-engine-fixture','normal_close':{'reserve_seconds':180}}
        return p

    def test_actual_generic_to_caseclient_two_days_capture_correct_case_without_another_clock(self):
        p=self.port()
        with patch.object(client_module,'native_day_request_count',return_value=0):
            for day in (1,2):
                row=adapter._advance_fixture_day(p,self.context['case_contract'],day,300)
                capture=adapter.read_json(row['current_toast_capture']['path'])
                self.assertEqual(capture['schema'],'ck3-controlled-debt-aid-news-day-capture-v1')
                self.assertEqual(capture['case'],'debt-aid-news-engine-fixture')
                self.assertEqual(len(capture['queries']),2);self.assertIn('day_projection',capture)
                self.assertEqual(adapter.read_json(capture['plan']['path'])['steps'],p.calls[-1])
        self.assertEqual(len(p.calls),2)
        for steps in p.calls:
            self.assertEqual(steps[0],{'id':steps[0]['id'],'kind':'advance_day','days':1,'timeout':300,'allow_event_boundary':True})
            self.assertEqual([s['tool']for s in steps[1:]],['ck3_query_current_interface_toast_v1']*2)
        self.assertTrue(all(r==180 for r in p.reserves))

    def test_actual_native_day_path_keeps_the_original_step_and_exact_two_queries(self):
        p=self.port();readiness=p.full(p.date);before=copy.deepcopy(readiness);before['revision']=17
        with patch.object(client_module,'native_day_request_count',return_value=2), \
                patch.object(client_module,'fresh_native_day_before',return_value=before) as fresh_before, \
                patch.object(client_module,'project_native_day',side_effect=lambda row,*a,**k:row):
            row=p.advance_day(allow_event_boundary=True,current_toast_queries=True)
        fresh_before.assert_called_once_with(readiness,readiness,allow_event_boundary=True)
        self.assertEqual(p.reserves,[180,180])
        self.assertEqual(len(p.calls),1);self.assertEqual(len(p.calls[0]),3)
        self.assertEqual(p.calls[0][0]['tool'],'ck3_execute_step');self.assertIs(p.calls[0][0]['fresh_revision'],False)
        self.assertEqual(p.calls[0][0]['args'],{'step':client_module.NATIVE_DAY_STEP,'expected_revision':17})
        self.assertEqual(adapter.read_json(row['current_toast_capture']['path'])['case'],'debt-aid-news-engine-fixture')

    def test_actual_execute_plan_admits_only_exact_shape_and180_before_queue_boundary(self):
        class QueueBoundary(Exception):pass
        p=self.port();name='case-natural-day-0001'
        steps=[{'id':name,'kind':'advance_day','days':1,'timeout':300,'allow_event_boundary':True}]+[
            {'id':name+'-toast0'+str(i),'kind':'tool','tool':'ck3_query_current_interface_toast_v1','args':{}}for i in(1,2)]
        calls=[]
        def guard(reserve=90,**kwargs):calls.append(reserve);raise QueueBoundary('Authored transport boundary, no queue invocation')
        p.guard=guard
        with self.assertRaises(QueueBoundary):CaseClient.execute_plan(p,steps,name,300,reserve=180)
        self.assertEqual(calls,[180])
        for defect in ('extra-row','wrong-query','two-days','query-args','renamed','float-timeout','wrong-close'):
            bad=copy.deepcopy(steps);bad_name=name;timeout=300
            if defect=='extra-row':bad.append(copy.deepcopy(bad[-1]))
            if defect=='wrong-query':bad[1]['tool']='ck3_execute_step'
            if defect=='two-days':bad[0]['days']=2
            if defect=='query-args':bad[1]['args']={'write':True}
            if defect=='renamed':bad_name='unbound-one-day'
            if defect=='float-timeout':timeout=300.0
            if defect=='wrong-close':p.selection.case['normal_close']['reserve_seconds']=90
            with self.assertRaises(ValueError,msg=defect):CaseClient.execute_plan(p,bad,bad_name,timeout,reserve=180)
            p.selection.case['normal_close']['reserve_seconds']=180
        self.assertEqual(calls,[180],'Invalid source plans stop before the actual queue boundary')

    def test_cross_case_bool_numeric_changed_phase_and_extra_contract_fields_reject_before_day(self):
        mutations=[lambda c:c.update(product='other'),lambda c:c.update(case='spot'),
            lambda c:c['case_contract'].update(maximum_natural_days=3),
            lambda c:c['case_contract']['controlled_fixture_contract'].update(fund_eligible=0),
            lambda c:c['case_contract']['controlled_fixture_contract'].update(physical_save_maximum=3.0),
            lambda c:c['case_contract']['controlled_fixture_contract'].update(controlled_API_claims_cents=[2000.0,1000]),
            lambda c:c['case_contract']['controlled_fixture_contract'].update(unknown=True),
            lambda c:c['case_contract']['gui_phases'][1].update(at_day=True),
            lambda c:c['case_contract']['gui_phases'][2].update(requirements=[])]
        for mutate in mutations:
            changed=copy.deepcopy(self.context);mutate(changed);p=self.port(changed)
            with self.assertRaises(ValueError),patch.object(client_module,'native_day_request_count',return_value=0):
                p.advance_day(allow_event_boundary=True,current_toast_queries=True)
            self.assertEqual(p.calls,[])
        c=copy.deepcopy(self.context);c['case_contract']['post_start']={'government_key':'authored','primary_title_tier_key':'duchy','independent':True}
        self.assertTrue(adapter._controlled_debt_aid_news_toast_enabled(c),'Ordinary resolved post-start data does not change exact debt scope')

    def test_unrelated_natural_news_crisis_has_no_new_day_toast_privilege(self):
        c=copy.deepcopy(self.context);c.update(case='news-crisis',case_contract=json.loads((CONFIG.parent/'financial_markets_news_crisis.json').read_bytes()))
        self.assertFalse(adapter._controlled_debt_aid_news_toast_enabled(c))
        p=self.port(c);p.selection.case['id']='news-crisis'
        with self.assertRaises(ValueError):p.advance_day(allow_event_boundary=True,current_toast_queries=True)
        self.assertEqual(p.calls,[])

if __name__=='__main__':unittest.main()
