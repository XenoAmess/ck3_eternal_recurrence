"""New synthetic C common-horizon contracts; no SDK or old suite execution."""
import argparse
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument('--policy-root',type=Path,default=Path(__file__).parent)
parser.add_argument('--scratch-root',type=Path)
parser.add_argument('--signed-id-candidate',action='store_true',help='Offline only: compile the exact one-line signed-ID candidate without writing its borrowed source')
args,remaining=parser.parse_known_args();sys.argv=[sys.argv[0]]+remaining
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
h=module(Path(__file__).with_name('common_horizon.py'),'C_synthetic_horizon')
r=module(Path(__file__).with_name('phased_relay.py'),'C_synthetic_relay')
a=module(args.policy_root/'strategy_c_next_decision.py','C_synthetic_existing_adapter')
if args.signed_id_candidate:
    path=args.policy_root/'strategy_c_next_decision.py'
    source=path.read_text(encoding='utf-8')
    old="and record['persistent_regiment_id'] >= 0"
    new="and -(2**31) <= record['persistent_regiment_id'] < 2**31"
    if source.count(old)!=1:raise ValueError('exact reviewed one-line candidate site missing')
    exec(compile(source.replace(old,new),str(path),'exec'),a.__dict__)
c=a.c

def observation(day,current=8):
    records=[{'status':'available','unavailable_reason':None,'record_index':0,
        'persistent_regiment_id':200,'chunk_index':0,'chunk_army_regiment_id':101,
        'current_soldiers':current,'maximum_soldiers':10}]
    return {'binding':{'machine_id':'SYNTHETIC-machine','pid':1,'process_create_time_100ns':2,
        'connection_generation':3,'episode':'SYNTHETIC-episode','snapshot_id':f'SYNTHETIC-{day}',
        'revision':day+1,'native_revision':day+1,'native_carmy_id':9,'paused':True,
        'controllable':True,'in_combat':False,'retreating':False,'move_target_observable':False},
        'endpoint':{'day':day,'date_raw':24000+day*24,'commander_id':11,
            'cohort_regiments':[{'army_regiment_id':101,'current_soldiers':current,'maximum_soldiers':10}],
            'cohort_current':current,'cohort_maximum':10,'all_strategy_current':current+1,
            'all_strategy_maximum':11,'treasury_raw':9000000-day,
            'units':[{'army_id':7,'current_province_id':30,'state':'stationary','route':[],
                'target':None,'scale':100000,'stock_raw':10000000-day,'capacity_raw':30000000,
                'current_soldiers':current+1,'maximum_soldiers':11}],
            'DATA':[{'army_regiment_id':rid,'source':'native_all_data_records','status':'available',
                'ready':True,'unavailable_reason':None,'native_data_record_count':len(rows),'records':rows}
                for rid,rows in ((101,records),(102,[]))]},
        'decision_inputs':{'all_regiment_ids':[101,102]},
        'clock':{'state':'triggered','starting_date_raw':24000+(day-1)*24,
            'target_date_raw':24000+day*24,'last_observed_date_raw':24000+day*24,
            'trigger_date_raw':24000+day*24,'generation':day,'speed':5,'completed_daily_ticks':1,
            'overshoot_days':0,'signed_date_delta_from_target_raw':0,'abnormal':False,
            'pause_observed':True,'mode':'terminal_or_sentinel','army_count':0,'combat_count':0,
            'trigger_reasons':['date_deadline'],'pause_wrapper_called':True,'intermediate_pause_count':0}}

def fixture():
    plan={'status':'frozen','follow_after_arrival_to_day90':True,'post_arrival_policy':h.POLICY,
        't0_raw':24000,'raw_per_day':24,'max_natural_days':90,'goal_province_id':30,
        'original_regiment_ids':[101],'arrival_states':['stationary'],
        'strategies':{'C':{'mode':'whole-via','waypoint_province_ids':[20],'route_preview':{}}}}
    before=observation(1)
    previous={'phase':'marching','target_index':1,'last_day':1,'last_clock_generation':1,
        'binding':before['binding'],'army_id':7,'commander_id':11,'cohort_maxima':[[101,10]],
        'last_not_arrived_day':1,'arrivals':[{'province_id':20,'day':1,
            'observed_interval_days':[0,1],'exact_arrival_tick':None}],
        'pending_route':[30],'ready_province':20,'reason':None}
    arrived_observation=observation(2)
    arrived=c.observe(plan,previous,arrived_observation)
    state=h.bind_first_arrival(plan,previous,arrived,arrived_observation,adapter=a)
    return plan,previous,state

class CommonHorizonCases(unittest.TestCase):
    def test_first_arrival_anchor_and_natural_values_remain_separate(self):
        plan,previous,state=fixture();original=deepcopy(state)
        updated=h.observe_common_horizon(plan,state,observation(3,7),adapter=a)
        self.assertEqual(updated['last_day'],3)
        for key in ('phase','target_index','arrivals','common_horizon_anchor'):
            self.assertEqual(updated[key],state[key])
        self.assertEqual(state,original)
        self.assertEqual(len(state['common_horizon_anchor']['data_identity_max']['groups']),2)
        with self.assertRaisesRegex(ValueError,'actual first final arrival'):
            h.bind_first_arrival(plan,state,state,observation(2),adapter=a)
    def test_state_writer_pins_previous_marching_and_refuses_late_backfill(self):
        plan,previous,arrived=fixture();arrived.pop('common_horizon_anchor')
        with tempfile.TemporaryDirectory(dir=args.scratch_root,prefix='C-horizon-anchor-') as directory:
            relay=r.CStages.__new__(r.CStages)
            relay.plan=plan;relay.horizon=h;relay.adapter=a;relay.io=SimpleNamespace(case=Path(directory))
            relay.log=Path(directory)/'state-pins.jsonl'
            relay.evidence=SimpleNamespace(json=lambda value:r.load(r.checked(value)))
            before=relay.save_state(previous,observation(1),{})
            relay.save_state(arrived,observation(2),{})
            anchor=relay.saved()['state']['common_horizon_anchor']
            self.assertEqual(anchor['previous_state_source'],before)
            self.assertEqual(r.load(r.checked(before))['state']['phase'],'marching')
            with self.assertRaisesRegex(ValueError,'actual first final arrival'):
                relay.save_state(arrived,observation(2),{})
    def test_policy_terminal_clock_and_readonly_are_explicit(self):
        plan,_,state=fixture()
        for field,value in (('follow_after_arrival_to_day90',False),('post_arrival_policy','wait-somewhere')):
            wrong=deepcopy(plan);wrong[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                h.observe_common_horizon(wrong,state,observation(3),adapter=a)
        missing=deepcopy(state);missing.pop('common_horizon_anchor')
        with self.assertRaisesRegex(ValueError,'no historical backfill'):
            h.observe_common_horizon(plan,missing,observation(3),adapter=a)
        with self.assertRaisesRegex(ValueError,'terminal C cannot restart'):
            c.observe(plan,state,observation(3))
        for day in (2,4):
            with self.subTest(day=day),self.assertRaisesRegex(ValueError,'exactly the next'):
                h.observe_common_horizon(plan,state,observation(day),adapter=a)
        bad=observation(3);bad['clock']['completed_daily_ticks']=2
        with self.assertRaises(ValueError):h.observe_common_horizon(plan,state,bad,adapter=a)
        readonly=h.read_common_horizon_endpoint(plan,state,observation(2),adapter=a)
        self.assertEqual(readonly['arrivals'],state['arrivals'])
        self.assertEqual(readonly['last_day'],2)
    def test_data_identity_order_max_subject_and_goal_cannot_change(self):
        plan,_,state=fixture()
        for kind in ('persistent','max','order','missing_empty','commander','CArmy','goal'):
            obs=observation(3)
            if kind=='persistent':obs['endpoint']['DATA'][0]['records'][0]['persistent_regiment_id']=201
            elif kind=='max':obs['endpoint']['DATA'][0]['records'][0]['maximum_soldiers']=11
            elif kind=='order':obs['endpoint']['DATA'].reverse()
            elif kind=='missing_empty':obs['endpoint']['DATA'].pop()
            elif kind=='commander':obs['endpoint']['commander_id']=12
            elif kind=='CArmy':obs['binding']['native_carmy_id']=10
            else:obs['endpoint']['units'][0]['current_province_id']=31
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                h.observe_common_horizon(plan,state,obs,adapter=a)
    def test_signed_persistent_fullid_is_retained_and_out_of_range_rejected(self):
        plan,previous,state=fixture();arrived=c.observe(plan,previous,observation(2))
        first=observation(2);first['endpoint']['DATA'][0]['records'][0]['persistent_regiment_id']=-(2**31)
        state=h.bind_first_arrival(plan,previous,arrived,first,adapter=a)
        nextday=observation(3);nextday['endpoint']['DATA'][0]['records'][0]['persistent_regiment_id']=-(2**31)
        updated=h.observe_common_horizon(plan,state,nextday,adapter=a)
        self.assertEqual(updated['common_horizon_anchor'],state['common_horizon_anchor'])
        for invalid in (-(2**31)-1,2**31,True,None):
            wrong=deepcopy(nextday);wrong['endpoint']['DATA'][0]['records'][0]['persistent_regiment_id']=invalid
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):
                h.observe_common_horizon(plan,state,wrong,adapter=a)
    def relay(self,plan,state):
        relay=r.CStages.__new__(r.CStages);relay.plan=plan;relay.adapter=a;relay.c=c;relay.horizon=h
        self.states=[deepcopy(state)];self.days=0;self.packets=0
        relay.saved=lambda:{'state':self.states[-1]}
        def packet(name,**kwargs):self.packets+=1;return observation(self.states[-1]['last_day']),{}
        relay.packet=packet
        relay.save_state=lambda state,obs,refs:self.states.append(deepcopy(state))
        def day(obs,refs):
            self.days+=1;actual=observation(obs['endpoint']['day']+1)
            return actual,{},actual['clock']
        relay.exact_day=day
        return relay
    def test_bounded_stage_stops_at_original90_then_makes_no_request(self):
        plan,_,state=fixture();state.update(last_day=89,last_clock_generation=89,binding=observation(89)['binding'])
        relay=self.relay(plan,state);result=relay.advance_common_horizon(30)
        self.assertEqual((result['day'],self.days),(90,1))
        self.assertEqual(result['arrivals'],state['arrivals'])
        before=self.packets;result=relay.advance_common_horizon(1)
        self.assertEqual((result['new_requests'],self.packets-before,self.days),(0,0,1))
        relay.horizon=None
        with self.assertRaisesRegex(ValueError,'helper module pin'):relay.advance_common_horizon(1)
    def test_recovery_uses_original_claim_and_status_without_arm_or_resume(self):
        plan,_,state=fixture();relay=self.relay(plan,state);start=24048
        with tempfile.TemporaryDirectory(dir=args.scratch_root,prefix='C-horizon-recover-') as directory:
            case=Path(directory);binding={'SYNTHETIC':True}
            (case/f'C-day-{start}.once.claim.json').write_text(json.dumps(
                {'binding':binding,'starting_date_raw':start,'target_date_raw':start+24}),encoding='utf-8')
            resume={'arm_response':{'SYNTHETIC':'original-arm'}};calls=[]
            def request(name,tool,arguments):
                calls.append((name,arguments['step']))
                return {'body':{'tactical_daily_sentinel':observation(3)['clock']}},{},{'SYNTHETIC':'status'}
            relay.io=SimpleNamespace(case=case,binding=binding,action_original=lambda key:resume,
                request=request,snap=lambda name:({},{}))
            relay.evidence=SimpleNamespace(json=lambda ref:{'body':{'tactical_daily_sentinel':{'SYNTHETIC':'original-arm'}}})
            relay.nd=SimpleNamespace(_normalize_tactical_daily_sentinel_status=lambda value:value,
                _validate_tactical_daily_sentinel_arm=lambda *x,**kw:None,
                _validate_tactical_daily_sentinel_stop=lambda *x,**kw:None)
            relay.meta={'synthetic':True};relay.packet=lambda *x,**kw:(observation(3),{})
            relay.recover_day(start,common_horizon=True)
            self.assertEqual(calls,[('C-recover-clock-status','research-query-tactical-daily-sentinel-v1')])
            self.assertEqual(self.states[-1]['last_day'],3)
            self.assertEqual(self.states[-1]['arrivals'],state['arrivals'])

if __name__=='__main__':unittest.main()
