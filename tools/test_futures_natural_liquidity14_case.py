"""Actual new public case/purpose/queue/client consumers. Authored IO; no Game or financial effect execution."""
from __future__ import annotations
import copy,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'ck3_autonomous_player/src'))
sys.path.insert(0,str(ROOT/'tools'))
from ck3_mod_acceptance_background_types import (
    FUTURES_NATURAL14_CASE_V1, futures_natural14_contract_matches_v1,
    FUTURES_NATURAL14_CONTRACT_V1, FUTURES_NATURAL14_PHASES_V1, FUTURES_NATURAL14_SCOPE_V1,
    FUTURES_NATURAL14_CONTRACT_V2, futures_natural14_contract_matches_v2,
    ProductAcceptancePurposeV1, continuous14_case_scope_matches_v1)
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_queue import validate_steps
import test_product_acceptance_purpose as purpose_fixture
import test_continuous14_clock_diagnostic as clock_fixture
import test_futures_gui_transactions_case as archive_fixture

CONFIG=ROOT/'tools/ck3_mod_acceptance_cases/financial_markets_futures_natural_liquidity14.json'

class FuturesNaturalLiquidity14CaseTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.config=json.loads(CONFIG.read_bytes())
        # Preserve every original v1 test against the exact historical contract.
        self.config['acceptance_scope']=FUTURES_NATURAL14_SCOPE_V1
        self.config['futures_natural_liquidity14_contract']=copy.deepcopy(FUTURES_NATURAL14_CONTRACT_V1)
        self.config['gui_phases']=copy.deepcopy(FUTURES_NATURAL14_PHASES_V1)
        self.context={'product':'financial-markets','case':FUTURES_NATURAL14_CASE_V1,
            'case_contract':self.config,'run_id':'authored-no-game-run','output':str(self.root),
            'case_inputs':{'post_start':{'government_key':'feudal_government','primary_title_tier_key':'duchy','independent':True}}}
        self.context=adapter.resolve_post_start(self.context);self.config=self.context['case_contract']
        self.compiled={'config':self.config};self.binding={'authored_test_compiled_pin':True}

    def diagnostic(self):
        host,calls=clock_fixture.actual_host()
        value=clock_fixture.experiment(host)
        self.assertEqual(calls.count('resume-map'),1)
        self.assertEqual(sum(x.startswith('research-arm-')for x in calls),1)
        return value

    def metadata(self,name):
        p=self.root/name;p.write_text(json.dumps({'authored_io_only':name}),encoding='utf-8');return archive_fixture.file_pin(p)

    def archive(self,name,date):
        p=self.root/(name+'.archive.json')
        source=self.root/(name+'-source.ck3');source.write_bytes(('AUTHORED ONLY '+name).encode())
        saved=self.root/(name+'.ck3');saved.write_bytes(source.read_bytes())
        value=copy.deepcopy(archive_fixture.ACTUAL_R37_ARCHIVE)
        value.update(source=archive_fixture.file_pin(source),archive=archive_fixture.file_pin(saved),date_raw=date)
        value['original_checkpoint_result']['checkpoint'].update(path=str(source.resolve()),size=source.stat().st_size,
            sha256=archive_fixture.file_pin(source)['sha256'],date_raw=date)
        p.write_text(json.dumps(value),encoding='utf-8');return archive_fixture.file_pin(p)

    def reviews(self):
        refs=[self.archive('baseline',clock_fixture.START),self.archive('orders',clock_fixture.START),
              self.archive('terminal',clock_fixture.START+336)]
        note=self.metadata('authored-complete-reconciliation.json');responses={}
        for spec,reference in zip(self.config['gui_phases'],refs):
            responses[spec['id']]={'run_id':self.context['run_id'],'reviewer':'/root',
                'assertions':{key:True for key in spec['requirements']},'evidence':[reference,note],
                'physical_archive':reference,'audit':note,'raw':note,'whole':note}
        responses[self.config['gui_phases'][1]['id']]['sell_orders']={name:{'status':'NOT_PLACED',
            'reason':'Authored test has no financial execution','evidence':[]}for name in ('short','reduce')}
        terminal=responses[self.config['gui_phases'][2]['id']]
        terminal.update(physical_archives=refs,evidence=refs+[note],futures_natural_liquidity14={name:{'status':'NOT_OBSERVED',
            'reason':'Authored test has no counterpart or real fill','evidence':[]}for name in ('short','reduce')})
        return responses,refs,note

    def test_exact_new_scope_and_two_legacy_cases_remain_separate(self):
        self.assertTrue(futures_natural14_contract_matches_v1('financial-markets',FUTURES_NATURAL14_CASE_V1,self.config))
        self.assertTrue(adapter._futures_natural14_enabled(self.context))
        self.assertFalse(adapter._continuous14_enabled(self.context))
        self.assertFalse(adapter._futures_gui_transactions_enabled(self.context))
        for name in ('financial_markets_clock_cadence_continuous14.json','financial_markets_futures_gui_transactions.json'):
            old=json.loads((CONFIG.parent/name).read_bytes())
            self.assertFalse(futures_natural14_contract_matches_v1('financial-markets',old['case_id'],old))
        self.assertEqual(self.config['continuous14_contract']['physical_saves'],2)
        self.assertEqual(self.config['futures_natural_liquidity14_contract']['physical_save_maximum'],3)

    def test_unsafe_bounds_scope_cells_and_actor_changes_reject_before_any_action(self):
        for key,value in [('maximum_natural_days',True),('maximum_natural_days',15),('allow_actor_change',True),
                          ('pending_interaction_policy','observe_unanswered_inbox'),('fixture_emitter',{})]:
            with self.subTest(key=key,value=value):
                bad=copy.deepcopy(self.context);bad['case_contract'][key]=value
                with self.assertRaises(ValueError):adapter._futures_natural14_enabled(bad)
        for key,value in [('physical_save_maximum',4),('physical_save_max_bytes',True),('cells',['short','reduce','long']),('force_counterparty_or_funds',True)]:
            bad=copy.deepcopy(self.context);bad['case_contract']['futures_natural_liquidity14_contract'][key]=value
            with self.assertRaises(ValueError):adapter._futures_natural14_enabled(bad)

    def test_actual_purpose_loader_and_queue_accept_only_the_pinned_new_case(self):
        fixture=purpose_fixture.ProductPurposeTests(methodName='runTest');fixture.setUp();self.addCleanup(fixture.doCleanups)
        fixture.contract=copy.deepcopy(self.config)
        fixture.prepared.update(product='financial-markets',case=FUTURES_NATURAL14_CASE_V1)
        fixture.frozen.update(mod_key='financial-markets',cell=FUTURES_NATURAL14_CASE_V1)
        purpose_fixture.write(fixture.frozen_path,fixture.frozen)
        fixture.context.update(product='financial-markets',case=FUTURES_NATURAL14_CASE_V1,frozen_argv=purpose_fixture.pin(fixture.frozen_path))
        fixture.refresh_contract();fixture.produce();loaded=fixture.consume()
        self.assertEqual(loaded.purpose.clock_purpose,'continuous14_diagnostic')
        report={'steps':[],'mcp_tools':{'tools':[{'name':'ck3_execute_step','inputSchema':{}}]}}
        step={'id':'one-original','kind':'continuous14_diagnostic','timeout':240}
        self.assertEqual(validate_steps([step],report,fixture.frozen),['one-original'])
        report['continuous14_diagnostic']={'state':'INCOMPLETE_NEVER_REPLAY'}
        with self.assertRaises(ValueError):validate_steps([step],report,fixture.frozen)

    def test_real_client_consumes_original_host_status_only_result_and_keeps_180_reserve(self):
        value=self.diagnostic();client=object.__new__(CaseClient);calls=[];reserves=[]
        client.selection=SimpleNamespace(adapter_context=lambda:self.context)
        client.manifest={'game':{'version':'1.21.0','exe_sha256':clock_fixture.CK3_1210.executable_sha256}};client._binding=None;client._seq=0
        client.guard=lambda reserve:reserves.append(reserve)or{'steps':[]}
        client.remaining=lambda:500
        def execute(steps,name,timeout=None,reserve=90):
            calls.append((steps,reserve));return[{'result':copy.deepcopy(value)}]
        client.execute_plan=execute
        self.assertEqual(client.continuous14_diagnostic()['result']['elapsed_hours'],336)
        self.assertEqual(reserves,[180]);self.assertEqual(calls[0][1],180)
        client.remaining=lambda:434
        with self.assertRaises(ValueError):client.continuous14_diagnostic()
        self.assertEqual(len(calls),1)

    def test_actual_adapter_three_phase_order_one_interval_and_not_observed_results(self):
        responses,refs,note=self.reviews();value=self.diagnostic();calls=[]
        class Port:
            def snapshot(inner):return clock_fixture.frame()
            def root_checkpoint(inner,name,request,reserve=90):
                calls.append(name);return copy.deepcopy(responses[name])
            def checkpoint(inner,name,facts):
                p=self.root/(name+'.json');p.write_text(json.dumps(facts),encoding='utf-8');return p
            def continuous14_diagnostic(inner):calls.append('one-original-interval');return{'result':value}
            def advance_day(inner,*a,**k):raise AssertionError('Never an ordinary/day1 route')
            def execute_plan(inner,*a,**k):raise AssertionError('No automatic GUI/observer/business setter')
        with patch.object(adapter,'compiled_contract',return_value=(self.compiled,self.binding)):
            facts=adapter.run_case(self.context,Port());verified=adapter.verify_case(self.context)
        expected=[self.config['gui_phases'][0]['id'],self.config['gui_phases'][1]['id'],'one-original-interval',self.config['gui_phases'][2]['id']]
        self.assertEqual(calls,expected);self.assertEqual(facts['retained_physical_checkpoint_count'],3)
        self.assertEqual(facts['observed_cells'],[]);self.assertEqual(facts['not_observed_cells'],['short','reduce'])
        self.assertFalse(verified['business_pass']);self.assertFalse(verified['financial_daily_coverage_verified'])

    def test_client_rejects_malformed_retained_steps_before_dispatch(self):
        client=object.__new__(CaseClient)
        client.selection=SimpleNamespace(adapter_context=lambda:self.context)
        client.manifest={'game':{'version':'1.21.0'}};client._seq=0
        client.remaining=lambda:500
        client.execute_plan=lambda *a,**k:self.fail('Malformed history must never dispatch Native control')
        for steps in (True,[5],[{'plan':False}]):
            client.guard=lambda reserve:{'steps':steps}
            with self.subTest(steps=steps),self.assertRaises(ValueError):client.continuous14_diagnostic()
        self.assertEqual(client._seq,0)

    def test_missing_alias_wrong_date_or_extra_archive_cannot_close_three_save_graph(self):
        original,refs,note=self.reviews();value=self.diagnostic()
        for defect in ('extra','alias','missing-evidence'):
            bad=copy.deepcopy(original);terminal=bad[self.config['gui_phases'][2]['id']]
            if defect=='extra':terminal['physical_archives'].append(refs[0])
            elif defect=='alias':bad[self.config['gui_phases'][1]['id']]['physical_archive']=refs[0]
            else:terminal['evidence']=[]
            with self.subTest(defect=defect),self.assertRaises(ValueError):
                adapter._futures_natural14_review(self.context,self.compiled,bad,value)
        bad=copy.deepcopy(original);middle=bad[self.config['gui_phases'][1]['id']]
        receipt=json.loads(Path(refs[1]['path']).read_bytes());receipt['date_raw']+=24
        Path(refs[1]['path']).write_text(json.dumps(receipt),encoding='utf-8')
        with self.assertRaises(ValueError):adapter._futures_natural14_review(self.context,self.compiled,bad,value)

    def test_submission_or_endpoint_correlation_cannot_be_claimed_as_a_fill(self):
        phases,refs,note=self.reviews();value=self.diagnostic();terminal=phases[self.config['gui_phases'][2]['id']]
        terminal['futures_natural_liquidity14']['short']={'status':'OBSERVED','reason':'two endpoints have equal amount'}
        with self.assertRaises(ValueError):adapter._futures_natural14_review(self.context,self.compiled,phases,value)

    def test_real_review_accepts_two_finite_same_side_operations_only_with_three_role_pins(self):
        phases,refs,note=self.reviews();value=self.diagnostic()
        orders=phases[self.config['gui_phases'][1]['id']]['sell_orders']
        cells=phases[self.config['gui_phases'][2]['id']]['futures_natural_liquidity14']
        for name,native,permanent in [('short','5001','231'),('reduce','5002','232')]:
            orders[name]={'status':'PLACED','side':'SELL','lots':1,'leverage':2 if name=='short' else 1,
                'close_position_id':None if name=='short'else'150','order_native_id':native,'order_id':permanent,
                'account_native_id':'54','contract_native_id':'253','gui_actions':[{'query':note,'activation':note}],
                'reservation_reconciliation':note}
            assertions={'actual_original_order_filled_quantity_from_source_and_terminal_records',
                'actual_position_and_permanent_ids_and_selected_side_bound',
                'actual_independent_counterparty_account_holder_and_beneficiary_not_self',
                'actual_paired_collateral_fees_cash_and_unrelated_assets_reconciled',
                'actual_short_side_leverage2'if name=='short'else'actual_old_long150_exposure_reduced_by_original_reduce_order'}
            cells[name]={'status':'OBSERVED','order_native_id':native,'order_id':permanent,
                'before_archive':refs[0],'order_archive':refs[1],'after_archive':refs[2],
                'assertions':{key:True for key in assertions},'order_position_reconciliation':note,
                'margin_cash_fee_counterparty_reconciliation':note}
        result=adapter._futures_natural14_review(self.context,self.compiled,phases,value)
        self.assertEqual(result['observed_cells'],['short','reduce']);self.assertFalse(result['business_pass'])
        # The authored fields exercise consumer admission only, not financial script execution or live fill credit.
        for key,replacement in [('side','BUY'),('close_position_id','10'),('order_native_id','5001')]:
            bad=copy.deepcopy(phases);bad[self.config['gui_phases'][1]['id']]['sell_orders']['reduce'][key]=replacement
            with self.subTest(key=key),self.assertRaises(ValueError):
                adapter._futures_natural14_review(self.context,self.compiled,bad,value)

    def test_original_status_gap_owner_drift_or_missing_terminal_remains_partial(self):
        phases,refs,note=self.reviews();value=self.diagnostic()
        for defect in ('missing-sample','bad-count','owner-drift'):
            bad=copy.deepcopy(value)
            if defect=='missing-sample':bad['samples'].pop()
            elif defect=='bad-count':bad['samples'][-1]['day']=13
            else:bad['samples'][-1]['owner_after']['diagnostics']['connection_generation']+=1
            with self.subTest(defect=defect),self.assertRaises(ValueError):adapter._futures_natural14_diagnostic(bad)
        self.assertEqual(adapter._futures_natural14_verify(self.context)['status'],'PARTIAL_NOT_COMPLETED')

    def _real_plan_client(self):
        # Existing isolated queue fixture: no real lease/bus/CK3 or subprocess.
        # Keep CaseClient.execute_plan itself intact; fake only queue transport and completion.
        import test_ck3_mod_acceptance_queue_inprocess as queue_fixture
        fixture=queue_fixture.InprocessQueueTests(methodName='runTest')
        fixture.setUp();self.addCleanup(fixture.doCleanups)
        client=fixture.client
        client.selection.adapter_context=lambda:self.context
        client.selection.case={'id':FUTURES_NATURAL14_CASE_V1,'normal_close':{'reserve_seconds':180}}
        client.manifest={'game':{'version':'1.21.0','exe_sha256':clock_fixture.CK3_1210.executable_sha256}}
        client._binding=None;client._seq=0
        return fixture,client

    def test_real_execute_plan_preserves_declared_natural14_reserve_through_queue_and_await(self):
        fixture,client=self._real_plan_client();value=self.diagnostic();calls=[];reserves=[];waits=[]
        def guard(reserve=90,**kwargs):
            reserves.append(reserve);return {'steps':[]}
        client.guard=guard
        def enqueue(live,path,name,*,deadline=None):
            calls.append((live,path,name,deadline))
            return {'status':'AUTHORED_TRANSPORT_ACK_NOT_LIVE_EVIDENCE'}
        fixture.module.enqueue=enqueue
        def await_steps(steps,timeout=None,reserve=90):
            waits.append((copy.deepcopy(steps),timeout,reserve))
            return [{'id':steps[0]['id'],'ok':True,'finished_at':'authored-completion-only',
                     'result':copy.deepcopy(value)}]
        client.await_steps=await_steps
        with patch.object(fixture.client_module.subprocess,'run',side_effect=AssertionError('No real subprocess')):
            row=client.continuous14_diagnostic()
            self.assertEqual(row['result'],value)
            with self.assertRaises(FileExistsError):
                client.execute_plan(waits[0][0],calls[0][2][:-5],timeout=255,reserve=180)
        self.assertEqual(reserves,[180,180,180]);self.assertEqual(len(calls),1);self.assertEqual(len(waits),1)
        expected=[{'id':'case-continuous14-diagnostic-0001','kind':'continuous14_diagnostic','timeout':240}]
        self.assertEqual(waits,[(expected,255,180)])
        self.assertEqual(json.loads(calls[0][1].read_bytes()),{'steps':expected})
        queued=json.loads((client.output/'case-continuous14-diagnostic-0001.queue-result.json').read_bytes())
        self.assertEqual(queued['execution_mode'],'IN_PROCESS_PINNED_QUEUE_LIBRARY')
        self.assertFalse(queued['argv_executed']);self.assertEqual(queued['exit_code'],0)

    def test_real_execute_plan_rejects_ordinary_tool_or_changed_interval_with_180_before_write(self):
        fixture,client=self._real_plan_client()
        exact=[{'id':'case-continuous14-diagnostic-0001','kind':'continuous14_diagnostic','timeout':240}]
        attempts=[([{'id':'case-continuous14-diagnostic-0001','tool':'ck3_take_snapshot','args':{}}],255),
                  (exact,254),(exact,True),
                  ([dict(exact[0],timeout=240.0)],255),
                  ([dict(exact[0],unexpected=True)],255),(exact+exact,255)]
        client.guard=lambda *a,**k:self.fail('Invalid reserve must reject before guard or plan writes')
        with patch.object(fixture.client_module.subprocess,'run',side_effect=AssertionError('No real subprocess')):
            for steps,timeout in attempts:
                with self.subTest(steps=steps,timeout=timeout),self.assertRaises(ValueError):
                    client.execute_plan(steps,'case-continuous14-diagnostic-0001',timeout=timeout,reserve=180)
        self.assertEqual(list(client.output.iterdir()),[])

    def test_real_execute_plan_rejects_fake_natural_case_or_changed_declared_close_before_write(self):
        fixture,client=self._real_plan_client()
        steps=[{'id':'case-continuous14-diagnostic-0001','kind':'continuous14_diagnostic','timeout':240}]
        original=copy.deepcopy(self.context)
        client.guard=lambda *a,**k:self.fail('Fake natural case must reject before guard or plan writes')
        cases=[]
        foreign=copy.deepcopy(original);foreign['case']='clock-cadence-continuous14';cases.append((foreign,180))
        false_contract=copy.deepcopy(original);false_contract['case_contract']['maximum_natural_days']=15
        cases.append((false_contract,180));cases.append((original,90));cases.append((original,True))
        for selected,declared in cases:
            client.selection.adapter_context=lambda selected=selected:selected
            client.selection.case={'id':FUTURES_NATURAL14_CASE_V1,'normal_close':{'reserve_seconds':declared}}
            with self.subTest(selected=selected['case'],declared=declared),self.assertRaises(ValueError):
                client.execute_plan(steps,'case-continuous14-diagnostic-0001',timeout=255,reserve=180)
        self.assertEqual(list(client.output.iterdir()),[])


class FuturesNaturalOwnedPositionV2Tests(unittest.TestCase):
    """Source-derived producer DTO fixtures; no SAVE reader, finance scripts or Game."""
    def setUp(self):
        self.fixture=FuturesNaturalLiquidity14CaseTests(methodName='runTest')
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.root=self.fixture.root;self.config=json.loads(CONFIG.read_bytes())
        self.context=copy.deepcopy(self.fixture.context);self.context['case_contract']=self.config
        self.context=adapter.resolve_post_start(self.context);self.config=self.context['case_contract']
        self.compiled={'config':self.config};self.binding=self.fixture.binding
        self.sequence=0

    def _record(self,kind,native,permanent,numbers=None,references=None):
        return {'type':kind,'nativeId':native,'permanentId':{'present':True,'decimal':permanent},
            'exactIntegers':numbers or {},'scopeReferences':references or {},
            'issuanceReceipt':{'observed':False,'fields':{}}}

    def _ref(self,native,kind='story'):
        return {'serializedType':kind,'nativeId':native}

    def _endpoint(self,phase,receipt,rows):
        import hashlib
        self.sequence+=1;prefix='producer-dto-'+str(self.sequence)
        saved=json.loads(Path(receipt['path']).read_bytes())['archive']
        coverage={'passes':2,'completeStreamBytes':str(saved['bytes']),'completeStreamSha256':saved['sha256']}
        audit={'financialCertified':False,'audit':{'financial':{'financialCertified':False,'second':[],
            'first':{'save':saved,'streamingCoverage':coverage,'audit':{'assessment':'CANDIDATE_INVARIANTS_HOLD'},
                'stories':copy.deepcopy(rows)}}}}
        canonical=[{'nativeId':r['nativeId'],'canonicalTokenSha256':
            hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()}for r in rows]
        raw={'financialCertified':False,'request':{'save':saved},'fullStreamPasses':1,
            'inputUnchangedAtGuards':True,'completeStreamBytes':str(saved['bytes']),
            'completeStreamSha256':saved['sha256'],'stories':[{'id':r['nativeId'],
            'producerCanonicalTokenSha256':c['canonicalTokenSha256']}for r,c in zip(rows,canonical)]}
        whole={'digest':{'save':saved,'completePasses':2,'inputUnchanged':True,
            'completeStreamBytes':str(saved['bytes']),'completeStreamSha256':saved['sha256'],'records':canonical}}
        result={}
        for key,value in [('audit',audit),('raw',raw),('whole',whole)]:
            path=self.root/(prefix+'-'+key+'.json');path.write_text(json.dumps(value),encoding='utf-8')
            result[key]=archive_fixture.file_pin(path);phase['evidence'].append(result[key])
        return result

    def reviews(self,side='short',placed=True,observed=False):
        # IDs deliberately differ from old LONG150 and historical SHORT191.
        own='short'if side=='short'else'long';opposite='long'if own=='short'else'short'
        account=self._record('xfm_finance_account','54','2',{'xfm_account_id':'2'},
            {'xfm_holder':self._ref('42','char'),'xfm_beneficial_owner':self._ref('42','char')})
        counter=self._record('xfm_finance_account','6795','1839',{'xfm_account_id':'1839'},
            {'xfm_holder':self._ref('99','char'),'xfm_beneficial_owner':self._ref('99','char')})
        contract=self._record('xfm_futures_contract','1163','6',{'xfm_contract_id':'6'})
        position=self._record('xfm_futures_position','1001','77',{'xfm_status':'0','xfm_lots':'1','xfm_mark_cents':'120'},
            {'xfm_contract':self._ref('1163'),'xfm_'+own+'_account':self._ref('54'),
                'xfm_'+opposite+'_account':self._ref('6795')})
        baseline_rows=[account,counter,contract,position]
        refs=[self.fixture.archive(name,date)for name,date in [('v2-baseline',clock_fixture.START),
            ('v2-orders',clock_fixture.START),('v2-terminal',clock_fixture.START+336)]]
        source=self.fixture.archive('v2-source',clock_fixture.START)
        note=self.fixture.metadata('v2-Root-financial-reconciliation.json')
        phases={}
        for spec,receipt in zip(self.config['gui_phases'],refs):
            phases[spec['id']]={'run_id':self.context['run_id'],'reviewer':'/root',
                'assertions':{key:True for key in spec['requirements']},
                'evidence':[note,receipt],'physical_archive':receipt}
        first,middle,last=[phases[s['id']]for s in self.config['gui_phases']]
        first['evidence'].append(source)
        source_reports=self._endpoint(first,source,baseline_rows)
        saved=json.loads(Path(source['path']).read_bytes())['archive']
        self.context['saved_campaign']={'save':saved['path'],'bytes':saved['bytes'],'sha256':saved['sha256'],
            'date_raw':clock_fixture.START,'player_id':42}
        first['target_position']={'native_id':'1001','position_id':'77','account_native_id':'54','account_id':'2',
            'contract_native_id':'1163','contract_id':'6','side':side,'source_archive':source,
            **{'source_'+k:v for k,v in source_reports.items()}}
        first.update(self._endpoint(first,refs[0],baseline_rows))
        order=self._record('xfm_futures_order','5001','501',{'xfm_side':'1'if own=='short'else'2',
            'xfm_leverage':'1','xfm_reduce_order':'1','xfm_remaining_lots':'1','xfm_filled_gross_cents':'0'},
            {'xfm_account':self._ref('54'),'xfm_contract':self._ref('1163'),'xfm_close_position':self._ref('1001')})
        middle.update(self._endpoint(middle,refs[1],baseline_rows+([order]if placed else [])))
        final_rows=copy.deepcopy(baseline_rows+([order]if placed else []))
        if observed:
            final_rows[3]['exactIntegers'].update(xfm_lots='0',xfm_status='2')
            final_rows[-1]['exactIntegers'].update(xfm_remaining_lots='0',xfm_filled_gross_cents='120')
            receipt_side='buy'if own=='short'else'sell';other='sell'if receipt_side=='buy'else'buy'
            p1=self._record('xfm_futures_position','6001','78',{'xfm_fill_receipt_version':'1',
                'xfm_fill_'+receipt_side+'_order_id':'501','xfm_fill_'+receipt_side+'_account_id':'2',
                'xfm_fill_'+other+'_account_id':'1839','xfm_fill_'+receipt_side+'_intent':'1',
                'xfm_fill_'+receipt_side+'_close_source_id':'77','xfm_fill_slice_source_position_id':'77',
                'xfm_fill_lots':'1','xfm_fill_mark_cents':'120'}, {'xfm_contract':self._ref('1163')})
            final_rows.append(p1)
        last.update(self._endpoint(last,refs[2],final_rows));last['physical_archives']=refs
        last['evidence'].extend(refs)
        if placed:
            operation={'status':'PLACED','side':'BUY'if own=='short'else'SELL','lots':1,'leverage':1,
                'close_position_id':'77','order_native_id':'5001','order_id':'501','account_native_id':'54',
                'contract_native_id':'1163','gui_actions':[{'query':note,'activation':note}],
                'reservation_reconciliation':note}
        else:operation={'status':'NOT_PLACED','reason':'Actual permission unavailable in authored fixture','evidence':[note]}
        middle['close_orders']={'reduce':operation}
        cell={'status':'NOT_OBSERVED','reason':'No verified fill in this authored fixture','evidence':[note]}
        if observed:
            cell={'status':'OBSERVED','order_native_id':'5001','order_id':'501',
                'before_archive':refs[0],'order_archive':refs[1],'after_archive':refs[2],
                'p1_position_native_id':'6001','assertions':{key:True for key in {
                    'actual_original_close_and_P1_slice_source_and_owned_side_bound',
                    'actual_remaining_leg_holder_and_beneficiary_constraints_reconciled',
                    'actual_paired_collateral_fees_cash_and_unrelated_assets_reconciled',
                    'actual_no_self_trade_synthetic_counterparty_or_forced_fill'}},
                'order_position_reconciliation':note,'margin_cash_fee_counterparty_reconciliation':note}
        last['futures_natural_liquidity14']={'reduce':cell}
        return phases,refs,note

    def review(self,phases):
        return adapter._futures_natural14_review(self.context,self.compiled,phases,self.fixture.diagnostic())

    def mutate_audit(self,phases,index,mutate):
        phase=phases[self.config['gui_phases'][index]['id']]
        old=phase['audit'];value=json.loads(Path(old['path']).read_bytes())
        mutate(value['audit']['financial']['first']['stories'])
        self.sequence+=1;path=self.root/('mutated-authored-dto-'+str(self.sequence)+'.json')
        path.write_text(json.dumps(value),encoding='utf-8');phase['audit']=archive_fixture.file_pin(path)
        phase['evidence'].append(phase['audit'])

    def test_canonical_v2_is_explicit_and_v1_remains_strict_150_two_SELL(self):
        self.assertTrue(futures_natural14_contract_matches_v2('financial-markets',FUTURES_NATURAL14_CASE_V1,self.config))
        self.assertFalse(futures_natural14_contract_matches_v1('financial-markets',FUTURES_NATURAL14_CASE_V1,self.config))
        self.assertTrue(futures_natural14_contract_matches_v1('financial-markets',FUTURES_NATURAL14_CASE_V1,self.fixture.config))
        self.assertEqual(self.fixture.config['futures_natural_liquidity14_contract']['reduce_position_id'],150)
        self.assertEqual(self.fixture.config['futures_natural_liquidity14_contract']['submitted_side'],'SELL')
        self.assertEqual(self.fixture.config['futures_natural_liquidity14_contract']['cells'],['short','reduce'])
        self.assertEqual(self.config['continuous14_contract'],self.fixture.config['continuous14_contract'])
        self.assertEqual([s['at_day']for s in self.config['gui_phases']],[0,0,14])
        for key,value in [('opening_orders',1),('reduce_lots',2),('order_leverage',2),('observer_arm',0)]:
            bad=copy.deepcopy(self.config);bad['futures_natural_liquidity14_contract'][key]=value
            self.assertFalse(futures_natural14_contract_matches_v2('financial-markets',FUTURES_NATURAL14_CASE_V1,bad))

    def test_actual_SHORT_close_BUY_and_LONG_close_SELL_each_join_new_P1_source(self):
        for side in ('short','long'):
            with self.subTest(side=side):
                phases,refs,note=self.reviews(side,observed=True);result=self.review(phases)
                self.assertEqual(result['observed_cells'],['reduce'])
                self.assertEqual(result['close_orders']['reduce']['side'],'BUY'if side=='short'else'SELL')
                self.assertFalse(result['business_pass']);self.assertFalse(result['financial_daily_coverage_verified'])

    def test_placed_unfilled_and_unplaced_are_NOT_OBSERVED_without_endpoint_SELL_gate(self):
        for placed in (True,False):
            with self.subTest(placed=placed):
                phases,refs,note=self.reviews(placed=placed);result=self.review(phases)
                self.assertEqual(result['observed_cells'],[]);self.assertEqual(result['not_observed_cells'],['reduce'])
                self.assertNotIn('short',result['close_orders'])

    def test_wrong_side_target_owner_missing_and_pending_source_fail_closed(self):
        for defect in ('side','target','owner','missing','closed','pending'):
            with self.subTest(defect=defect):
                phases,refs,note=self.reviews()
                first=phases[self.config['gui_phases'][0]['id']]
                if defect=='side':first['target_position']['side']='long'
                elif defect=='target':first['target_position']['position_id']='191'
                elif defect=='owner':self.context['saved_campaign']['player_id']=99
                elif defect=='missing':del first['target_position']['source_raw']
                elif defect=='closed':self.mutate_audit(phases,0,lambda rows:rows[3]['exactIntegers'].update(xfm_status='2'))
                else:self.mutate_audit(phases,0,lambda rows:rows[3]['exactIntegers'].update(xfm_pending_payment='0'))
                with self.assertRaises(ValueError):self.review(phases)

    def test_wrong_close_side_leverage_target_or_extra_opening_SHORT_is_rejected(self):
        for defect in ('side','leverage','target','extra','extra_audit','old_payload'):
            with self.subTest(defect=defect):
                phases,refs,note=self.reviews();middle=phases[self.config['gui_phases'][1]['id']]
                if defect=='side':middle['close_orders']['reduce']['side']='SELL'
                elif defect=='leverage':middle['close_orders']['reduce']['leverage']=2
                elif defect=='target':middle['close_orders']['reduce']['close_position_id']='150'
                elif defect=='extra':middle['close_orders']['short']=copy.deepcopy(middle['close_orders']['reduce'])
                elif defect=='extra_audit':
                    self.mutate_audit(phases,1,lambda rows:rows.append(self._record(
                        'xfm_futures_order','7001','502',{'xfm_side':'2','xfm_leverage':'2'},
                        {'xfm_account':self._ref('54')})))
                else:middle['sell_orders']={}
                with self.assertRaises(ValueError):self.review(phases)

    def test_P1_wrong_order_source_intent_or_contract_cannot_substitute(self):
        defects=[('xfm_fill_buy_order_id','999'),('xfm_fill_buy_account_id','1839'),('xfm_fill_buy_close_source_id','150'),
            ('xfm_fill_slice_source_position_id','150'),('xfm_fill_buy_intent','0'),
            ('xfm_fill_receipt_version','0'),('xfm_fill_lots','2')]
        for key,value in defects:
            with self.subTest(key=key):
                phases,refs,note=self.reviews(observed=True)
                self.mutate_audit(phases,2,lambda rows:rows[-1]['exactIntegers'].update({key:value}))
                with self.assertRaises(ValueError):self.review(phases)
        phases,refs,note=self.reviews(observed=True)
        self.mutate_audit(phases,2,lambda rows:rows[-1]['scopeReferences'].update(xfm_contract=self._ref('253')))
        with self.assertRaises(ValueError):self.review(phases)

    def test_dates_or_reserved_fee_without_P1_or_exposure_decrease_cannot_observe(self):
        for defect in ('no_P1','no_decrease','not_filled','bad_counterparty'):
            with self.subTest(defect=defect):
                phases,refs,note=self.reviews(observed=True)
                def mutate(rows):
                    if defect=='no_P1':rows.pop()
                    elif defect=='no_decrease':rows[3]['exactIntegers']['xfm_lots']='1'
                    elif defect=='not_filled':rows[4]['exactIntegers']['xfm_remaining_lots']='1'
                    else:rows[1]['scopeReferences']['xfm_beneficial_owner']=self._ref('42','char')
                self.mutate_audit(phases,2,mutate)
                with self.assertRaises(ValueError):self.review(phases)

    def test_source_quartet_and_same_checkpoint_EOF_and_canonical_hash_are_required(self):
        for defect in ('startup','raw_EOF','whole_hash','audit_EOF'):
            with self.subTest(defect=defect):
                phases,refs,note=self.reviews();first=phases[self.config['gui_phases'][0]['id']]
                if defect=='startup':self.context['saved_campaign']['sha256']='0'*64
                else:
                    key='audit'if defect=='audit_EOF'else'raw'
                    value=json.loads(Path(first[key]['path']).read_bytes())
                    if defect=='raw_EOF':value['fullStreamPasses']=0
                    elif defect=='whole_hash':value['stories'][0]['producerCanonicalTokenSha256']='0'*64
                    else:value['audit']['financial']['first']['streamingCoverage']['passes']=1
                    self.sequence+=1;path=self.root/('bad-EOF-'+str(self.sequence)+'.json')
                    path.write_text(json.dumps(value),encoding='utf-8');first[key]=archive_fixture.file_pin(path)
                    first['evidence'].append(first[key])
                with self.assertRaises(ValueError):self.review(phases)

    def test_three_distinct_archives_required_in_0_0_14_order(self):
        for defect in ('alias','extra','missing'):
            phases,refs,note=self.reviews();last=phases[self.config['gui_phases'][2]['id']]
            if defect=='alias':phases[self.config['gui_phases'][1]['id']]['physical_archive']=refs[0]
            elif defect=='extra':last['physical_archives'].append(refs[0])
            else:last['physical_archives'].pop()
            with self.subTest(defect=defect),self.assertRaises(ValueError):self.review(phases)

    def test_v2_actual_adapter_reuses_one_status_interval_and_verifies_v2_result(self):
        phases,refs,note=self.reviews();value=self.fixture.diagnostic();calls=[]
        class Port:
            def snapshot(inner):return clock_fixture.frame()
            def root_checkpoint(inner,name,request,reserve=90):
                calls.append(name);return copy.deepcopy(phases[name])
            def checkpoint(inner,name,facts):
                p=self.root/(name+'.json');p.write_text(json.dumps(facts),encoding='utf-8');return p
            def continuous14_diagnostic(inner):calls.append('one-status-only-interval');return{'result':value}
        with patch.object(adapter,'compiled_contract',return_value=(self.compiled,self.binding)):
            result=adapter.run_case(self.context,Port());verified=adapter.verify_case(self.context)
        self.assertEqual(result['schema'],'ck3-futures-natural-liquidity14-result-v2')
        self.assertEqual(calls,[self.config['gui_phases'][0]['id'],self.config['gui_phases'][1]['id'],
            'one-status-only-interval',self.config['gui_phases'][2]['id']])
        self.assertEqual(verified['not_observed_cells'],['reduce'])

    def test_v2_real_execute_plan_retains_180_reserve_and_exact_240_255_once_lane(self):
        self.fixture.context=self.context;self.fixture.config=self.config
        # Reuse the existing real CaseClient + isolated in-process queue assertions.
        self.fixture.test_real_execute_plan_preserves_declared_natural14_reserve_through_queue_and_await()

    def test_v2_rejects_changed_interval_and_ordinary_tool_with_180_before_any_write(self):
        self.fixture.context=self.context;self.fixture.config=self.config
        self.fixture.test_real_execute_plan_rejects_ordinary_tool_or_changed_interval_with_180_before_write()


if __name__=='__main__':unittest.main()
