"""Synthetic native-shaped offline tests; no live CK3 qualification."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import r10_compare as c
from schema_source import SCHEMA

HERE=Path(__file__).resolve().parent
EPISODE=HERE.parents[2]

class Fixture:
    def __init__(self,root):
        self.root=Path(root);self.n=0
        self.proof=self.put('synthetic-proof',{'synthetic':True,'not_game_evidence':True})
        self.commander=self.put('commander',{'id':10})
        self.features=self.put('features',{'loaded':['synthetic-vanilla']})
        build={'version':'1.20.0.4','steam_build':25734779,'exe_sha256':c.EXE,'source_head':'a'*40,'native_dll_sha256':'b'*64}
        self.plan={'schema':'xar.e04.r10.plan.v1','status':'frozen','frozen_at_utc':'2026-01-01T00:00:00Z','plan_id':'SYNTHETIC-NOT-A-CASE','build':build,'normal_save':{'kind':'normal-native-checkpoint','bytes':123,'sha256':'c'*64,'save_receipt':self.proof,'normal_origin_proof':self.proof},'t0_raw':1000,'max_natural_days':90,'raw_per_day':24,'goal_province_id':30,'arrival_states':['regular'],'original_regiment_ids':[1,2],
          'baseline':None,'strategies':{'A':{'mode':'whole-direct','route_preview':self.proof},'B':{'mode':'split-rest-merge','rest_province_ids':[20,21],'site_actual_stock_increase_evidence':[self.proof,self.proof],'minimum_stock_raw':1000000,'maximum_deficit':0,'maximum_rest_days':2,'merge_province_id':30,'merge_destination_policy':'destination-main','commander_policy':'preserve-defined-result','r09_result':self.proof},'C':{'mode':'whole-via','waypoint_province_ids':[20],'route_preview':self.proof}},
          'report_days':[1],'compare_fees':False,'follow_after_arrival_to_day90':False,'post_arrival_policy':None,'event_policy':'Record ordinary events and continue fixed actual option policy.','wall_budget_seconds_per_arm':3600,'prerequisites':{'exact_clock':self.proof,'loss_refill_subject_qualification':self.proof,'B_microexperiment':self.proof,'boarding_payment':None,'maintenance_settlement':None}}
        self.plan['baseline']=self.ep('BASE',0)
        self.results={'schema':'xar.e04.r10.results.v1','plan_sha256':'d'*64,'arms':[]}
        for k,label in enumerate('ABC',1):
            rt={'machine_id':'synthetic-'+label,'started_at_utc':'2026-01-02T00:00:00Z','pid':100+k,'process_create_time_100ns':1000+k,'connection_generation':1,'episode':'synthetic-'+label,'player_character_id':7,'source_head':'a'*40,'native_dll_sha256':'b'*64,'source_proof':self.proof}
            cold=self.ep(label,0);obs=[self.ep(label,1),self.ep(label,2)]
            days=[]
            for n in (1,2):
                cl={'state':'triggered','generation':n,'starting_date_raw':1000+(n-1)*24,'target_date_raw':1000+n*24,'last_observed_date_raw':1000+n*24,'trigger_date_raw':1000+n*24,'speed':5,'mode':'terminal_or_sentinel','army_count':0,'combat_count':0,'completed_daily_ticks':1,'intermediate_pause_count':0,'overshoot_days':0,'signed_date_delta_from_target_raw':0,'abnormal':False,'pause_observed':True,'pause_wrapper_called':True,'trigger_reasons':['date_deadline']}
                pin=self.put(label+'clock'+str(n),{'machine_id':rt['machine_id'],'PID':rt['pid'],'create_filetime':rt['process_create_time_100ns'],'episode':rt['episode'],'clock':cl})
                days.append({'day':n,'clock_source':pin,'paused_snapshot':obs[n-1]['snapshot'],'strategy_army_ids':obs[n-1]['strategy_army_ids']})
            ex={'prespecified_policy_followed':True,'B_merge_destination_policy':None,'B_commander_policy':None,'B_rest_exit_records':[],'C_waypoint_observed_days':[],'evidence':[self.proof]}
            if label=='B':
                ex.update(B_merge_destination_policy='destination-main',B_commander_policy='preserve-defined-result',B_rest_exit_records=[{'province_id':p,'unit_id':u,'start_day':0,'end_day':1,'reason':'threshold','endpoint_day':1} for p,u in [(20,1),(21,2)]])
            if label=='C':ex['C_waypoint_observed_days']=[{'province_id':20,'day':1}]
            self.results['arms'].append({'label':label,'runtime':rt,'loaded_save_sha256':'c'*64,'cold_start':cold,'days':days,'observations':obs,'execution':ex,'disposition':{'kind':'arrived','day':2,'last_not_arrived_day':1,'reason':None,'evidence':[self.proof]},'ledger':{'loss_refill_qualified':True,'payment_qualified':False,'loss_physical_debits':0,'refill_physical_adds':0,'boarding_gold_raw':None,'maintenance_gold_raw':None,'other_cash_income_raw':None,'other_cash_expense_raw':None,'through_day':2,'evidence':[self.proof]},'deviations':[]})
    def put(self,name,obj):
        self.n+=1;p=self.root/(str(self.n)+'-'+name+'.json');raw=(json.dumps(obj,ensure_ascii=False)+'\n').encode();p.write_bytes(raw)
        return {'path':p.name,'bytes':len(raw),'sha256':c.digest(raw)}
    def edit(self,pin,fn):
        v=c.parse((self.root/pin['path']).read_bytes());fn(v);return self.put('edited',v)
    def ep(self,label,day):
        k=ord(label)-64 if label in 'ABC' else 0
        units=[(1,[1,2],10 if day==0 else 30 if day==2 else 20 if label=='C' else 11)]
        if label=='B' and day==1:units=[(1,[1],20),(2,[2],21)]
        rows=[];positions=[]
        for aid,regs,province in units:
            rs=[{'army_regiment_id':r,'current_soldiers':50,'maximum_soldiers':50,'scale':1} for r in regs]
            if label=='B' and day==2:rs.append({'army_regiment_id':3,'current_soldiers':1,'maximum_soldiers':1,'scale':1})
            data=[{'army_regiment_id':r['army_regiment_id'],'status':'available','native_data_record_count':1,'records':[{'record_index':0,'persistent_regiment_id':r['army_regiment_id']+100,'chunk_index':0,'current_soldiers':r['current_soldiers'],'maximum_soldiers':r['maximum_soldiers']}]} for r in rs]
            rows.append({'army_id':aid,'status':'available','regiment_count':len(rs),'current_soldiers':sum(r['current_soldiers'] for r in rs),'maximum_soldiers':sum(r['maximum_soldiers'] for r in rs),'regiment_strengths':rs,'regiment_replenishment_records_v1':data,'current_supply_raw':1000000,'current_supply_scale':100000,'current_supply_capacity_raw':30000000,'current_supply_capacity_scale':100000})
            moving=day==1 and label!='B'
            positions.append({'army_id':aid,'owner_character_id':7,'current_province_id':province,'army_state':'moving' if moving else 'regular','route_province_ids':[30] if moving else [],'route_read_status':'complete_nonempty' if moving else 'complete_empty','move_target_province_id':30 if moving else None})
        ids=[x[0] for x in units];snap={'date_raw':1000+day*24,'paused':True,'map_ready':True,'revision':day+10,'native_revision':day+9,'snapshot_id':label+':'+str(day),'played_character':{'character_id':7,'alive':True},'played_character_gold':{'raw':25000000,'scale':100000},'active_wars':[{'war_id':1,'player_side':'attacker'}],'player_armies':positions,'episode_run_id':'synthetic-'+label,'diagnostics':{'bridge_pid':100+k if k else 999,'connection_generation':1,'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':c.EXE}}}
        query={'accepted':True,'status':'available','army_strengths':rows,'army_strengths_query_scope':{'army_ids':ids,'published_scope_status':'available'},'queried_snapshot_id':snap['snapshot_id'],'queried_revision':snap['revision'],'queried_native_revision':snap['native_revision'],'queried_date_raw':snap['date_raw'],'queried_connection_generation':1,'queried_episode_run_id':snap['episode_run_id']}
        return {'day':day,'snapshot':self.put(label+'snapshot'+str(day),{'machine_id':'synthetic-'+label,'body':snap,'is_error':False}),'army_result':self.put(label+'query'+str(day),query),'strategy_army_ids':ids,'commander':{'source':self.commander,'pointer':'/id'},'loaded_features':{'source':self.features,'pointer':'/loaded'}}
    def check(self):return c.compare(self.plan,self.results,c.Evidence(self.root))

class Tests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.f=Fixture(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_schema_selfcheck(self):self.assertEqual(c.parse((HERE/'r10.schema.json').read_bytes()),SCHEMA)
    def test_valid_native_shape_keeps_extra_B_one_and_never_sums_supply(self):
        r=self.f.check();self.assertTrue(r['controlled_comparison_records_eligible']);self.assertIsNone(r['winner']);self.assertIsNone(r['D90_rows'])
        b=r['comparison_rows'][1];self.assertEqual((b['original_cohort_current'],b['all_strategy_current']),(100,101));self.assertIsNone(b['actual_fees']);self.assertFalse(b['wallet_net_is_military_cost'])
        self.assertEqual(r['common_date_rows'][0]['date_raw'],1024);self.assertEqual(len(r['common_date_rows'][0]['arms']['B']['units']),2)
    def test_query_snapshot_revision_must_match(self):
        e=self.f.results['arms'][0]['observations'][1];e['army_result']=self.f.edit(e['army_result'],lambda v:v.update(queried_revision=999))
        with self.assertRaisesRegex(ValueError,'frame differs'):self.f.check()
    def test_legacy_B_actual_is_not_deadline_censor(self):
        x=c.legacy_rejection(c.parse((EPISODE/'evidence/r0175-b-gate-stop/closed-terminal/B-closed-terminal-values.json').read_bytes()));self.assertFalse(x['accepted_as_R10_result']);self.assertEqual(x['observed_days'],38);self.assertEqual(x['remaining_days'],52);self.assertIsNone(x['London_endpoint_metrics'])
    def test_legacy_C_actual_fifteen_deviations_rejected(self):
        x=c.legacy_rejection(c.parse((EPISODE/'evidence/r0176-c-descriptive-march/normalized_C_result.json').read_bytes()));self.assertFalse(x['accepted_as_R10_result']);self.assertEqual(x['sampling_deviation_count'],15);self.assertEqual(x['actual_observation_preserved'],[75,77])
    def test_two_day_clock_is_not_one(self):
        e=self.f.results['arms'][0]['days'][1];e['clock_source']=self.f.edit(e['clock_source'],lambda v:v['clock'].update(last_observed_date_raw=1072,trigger_date_raw=1072))
        with self.assertRaisesRegex(ValueError,'start/target/end'):self.f.check()
    def test_arrival_gap_two_rejected(self):
        self.f.results['arms'][0]['disposition']['last_not_arrived_day']=0
        with self.assertRaisesRegex(ValueError,'wider than1day'):self.f.check()
    def test_stop_day_one_cannot_be_censored_at90(self):
        a=self.f.results['arms'][0];a['days']=a['days'][:1];a['observations']=a['observations'][:1];a['disposition'].update(kind='budget-censored',day=1,last_not_arrived_day=None)
        with self.assertRaisesRegex(ValueError,'day90'):self.f.check()
    def test_measurement_failure_preserved_and_no_comparison_rows(self):
        self.f.results['arms'][2]['deviations']=[{'kind':'measurement','description':'retained two-day gap','evidence':self.f.proof}]
        r=self.f.check();self.assertFalse(r['controlled_comparison_records_eligible']);self.assertIsNone(r['comparison_rows']);self.assertEqual(len(r['observations_only']),3)
    def test_world_event_is_not_silently_discarded_or_automatic_measurement_failure(self):
        self.f.results['arms'][2]['deviations']=[{'kind':'world-event','description':'NPC moved normally','evidence':self.f.proof}]
        r=self.f.check();self.assertTrue(r['controlled_comparison_records_eligible']);self.assertEqual(len(r['world_events_retained']),1)
    def test_unknown_current_cannot_be_zero(self):
        e=self.f.results['arms'][0]['observations'][1]
        e['army_result']=self.f.edit(e['army_result'],lambda v:v['army_strengths'][0]['regiment_strengths'][0].update(current_soldiers=None))
        with self.assertRaisesRegex(ValueError,'unknown/noninteger'):self.f.check()
    def test_opaque_normal_seed_different_sha_rejected(self):
        self.f.results['arms'][1]['loaded_save_sha256']='e'*64
        with self.assertRaisesRegex(ValueError,'normal save SHA'):self.f.check()
    def test_cold_observable_state_drift_rejected(self):
        e=self.f.results['arms'][1]['cold_start'];e['commander']={'source':self.f.put('wrongcommander',{'id':11}),'pointer':'/id'}
        with self.assertRaisesRegex(ValueError,'cold T0'):self.f.check()
    def test_duplicate_regiment_rejected(self):
        e=self.f.results['arms'][0]['observations'][1]
        e['army_result']=self.f.edit(e['army_result'],lambda v:v['army_strengths'][0]['regiment_strengths'].append(deepcopy(v['army_strengths'][0]['regiment_strengths'][0])))
        with self.assertRaisesRegex(ValueError,'complete regiment|duplicate/unknown'):self.f.check()
    def test_B_merge_policy_cannot_change_after_results(self):
        self.f.results['arms'][1]['execution']['B_merge_destination_policy']='reverse-after-seeing-result'
        with self.assertRaisesRegex(ValueError,'policy changed'):self.f.check()
    def test_B_threshold_must_be_actual(self):
        self.f.plan['strategies']['B']['minimum_stock_raw']=2000000
        with self.assertRaisesRegex(ValueError,'threshold not actually met'):self.f.check()
    def test_B_maximum_stay_not_reached(self):
        self.f.results['arms'][1]['execution']['B_rest_exit_records'][0]['reason']='maximum_rest_days'
        with self.assertRaisesRegex(ValueError,'did not reach cap'):self.f.check()
    def test_C_waypoint_must_be_actual_position(self):
        self.f.results['arms'][2]['execution']['C_waypoint_observed_days'][0]['province_id']=99
        self.f.plan['strategies']['C']['waypoint_province_ids']=[99]
        with self.assertRaisesRegex(ValueError,'waypoint lacks actual'):self.f.check()
    def test_fee_comparison_cannot_use_missing_R08(self):
        self.f.plan['compare_fees']=True
        with self.assertRaisesRegex(ValueError,'R07/R08'):self.f.check()
    def test_actual_fee_ledger_separate_from_wallet_net(self):
        self.f.plan['compare_fees']=True;self.f.plan['prerequisites'].update(boarding_payment=self.f.proof,maintenance_settlement=self.f.proof)
        for a in self.f.results['arms']:
            a['ledger'].update(payment_qualified=True,boarding_gold_raw=300000,maintenance_gold_raw=100000,other_cash_income_raw=200000,other_cash_expense_raw=0)
            e=a['observations'][1];e['snapshot']=self.f.edit(e['snapshot'],lambda v:v['body']['played_character_gold'].update(raw=24800000))
        r=self.f.check();a=r['comparison_rows'][0];self.assertEqual(a['wallet_net_raw'],-200000);self.assertEqual(a['actual_fees']['actual_military_and_boarding_total_raw'],400000)
    def test_no_D90_without_registered_uniform_policy(self):
        self.f.plan['follow_after_arrival_to_day90']=True
        with self.assertRaisesRegex(ValueError,'D90 continuation'):self.f.check()
    def test_path_escape_rejected(self):
        with self.assertRaisesRegex(ValueError,'escapes root'):c.Evidence(self.f.root).raw({'path':'../outside.json','bytes':1,'sha256':'0'*64})
    def test_changed_source_bytes_rejected(self):
        pin=self.f.results['arms'][0]['observations'][0]['army_result'];(self.f.root/pin['path']).write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'evidence missing/size'):self.f.check()
    def test_same_runtime_cannot_be_three_independent_arms(self):
        self.f.results['arms'][1]['runtime']=deepcopy(self.f.results['arms'][0]['runtime'])
        with self.assertRaisesRegex(ValueError,'independent normal cold'):self.f.check()
    def test_freeze_after_runtime_rejected(self):
        self.f.plan['frozen_at_utc']='2026-01-03T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'not frozen before'):self.f.check()
    def test_binary_pin_not_opened(self):
        with self.assertRaisesRegex(ValueError,'small text'):c.Evidence(self.f.root).raw({'path':'never-read.exe','bytes':1,'sha256':'0'*64})
    def test_earlier_arrival_in_daily_snapshot_cannot_be_omitted(self):
        a=self.f.results['arms'][0];a['days'][0]['paused_snapshot']=self.f.edit(a['days'][0]['paused_snapshot'],lambda v:v['body']['player_armies'][0].update(current_province_id=30,army_state='regular',route_province_ids=[],route_read_status='complete_empty',move_target_province_id=None))
        with self.assertRaisesRegex(ValueError,'daily independent snapshot scan'):self.f.check()
    def test_real_ninetieth_day_nonarrival_is_accepted_as_censor(self):
        a=self.f.results['arms'][0];template=c.parse((self.f.root/a['days'][0]['clock_source']['path']).read_bytes());a['days']=[]
        last=None
        for n in range(1,91):
            ep=self.f.ep('A',n)
            if n==2:ep['snapshot']=self.f.edit(ep['snapshot'],lambda v:v['body']['player_armies'][0].update(current_province_id=11,army_state='regular',route_province_ids=[],route_read_status='complete_empty',move_target_province_id=None))
            v=deepcopy(template);v['clock'].update(generation=n,starting_date_raw=1000+(n-1)*24,target_date_raw=1000+n*24,last_observed_date_raw=1000+n*24,trigger_date_raw=1000+n*24)
            a['days'].append({'day':n,'clock_source':self.f.put('clock90',v),'paused_snapshot':ep['snapshot'],'strategy_army_ids':ep['strategy_army_ids']})
            if n==1:first=ep
            last=ep
        a['observations']=[first,last];a['disposition'].update(kind='budget-censored',day=90,last_not_arrived_day=None);a['ledger']['through_day']=90
        r=self.f.check();self.assertTrue(r['controlled_comparison_records_eligible']);self.assertIsNone(r['comparison_rows'][0]['arrival_interval_days']);self.assertEqual(r['comparison_rows'][0]['observed_day'],90)

if __name__=='__main__':unittest.main(verbosity=2)
