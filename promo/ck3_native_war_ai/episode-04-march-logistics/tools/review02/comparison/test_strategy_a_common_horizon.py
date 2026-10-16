"""Only new common-horizon wiring; synthetic exact-day transport, no live calls."""
from copy import deepcopy
from pathlib import Path
import unittest

import r10_compare as c
import strategy_a as a
import test_strategy_a_stages as original_setup


class CommonHorizon(unittest.TestCase):
    preview = original_setup.WiringTests.preview
    moving = original_setup.WiringTests.moving

    def setUp(self):
        original_setup.WiringTests.setUp(self)
        self.f.plan.update(follow_after_arrival_to_day90=True,
                           post_arrival_policy='hold-arrival-position-until-day90')
        self.initial=a.admit(self.f.plan,self.arm['runtime'],'c'*64,
                             self.arm['cold_start'],self.preview_pin,self.e)

    def arrived(self):
        state=self.moving()
        for n in (0,1):
            ep=deepcopy(self.arm['observations'][n]);day=deepcopy(self.arm['days'][n])
            ep['snapshot']=self.f.edit(ep['snapshot'],lambda x:x['body'].update(speed=5))
            day['paused_snapshot']=ep['snapshot'];state=a.update(state,day,ep,self.e)
        return state

    def third(self,change_commander=False):
        ep=self.f.ep('A',3)
        def frame(x):
            x['body'].update(speed=5)
            x['body']['played_character_gold']['raw']=25100000
            x['body']['player_armies'][0].update(current_province_id=30,controllable=True)
        ep['snapshot']=self.f.edit(ep['snapshot'],frame)
        def counts(q):
            row=q['army_strengths'][0];row.update(current_soldiers=99,current_supply_raw=2000000)
            row['regiment_strengths'][0]['current_soldiers']=49
            row['regiment_replenishment_records_v1'][0]['records'][0]['current_soldiers']=49
        ep['army_result']=self.f.edit(ep['army_result'],counts)
        if change_commander:
            ep['commander']={'source':self.f.put('new-commander',{'id':11}),'pointer':'/id'}
        day=deepcopy(self.arm['days'][1]);day.update(day=3,paused_snapshot=ep['snapshot'])
        day['clock_source']=self.f.edit(day['clock_source'],lambda x:x['clock'].update(
            generation=3,starting_date_raw=1048,target_date_raw=1072,
            last_observed_date_raw=1072,trigger_date_raw=1072))
        return ep,day

    def wire_day(self,state,ep,day):
        v=self.live;before=state['observations'][-1]
        v.endpoint=lambda name:ep if name.startswith('post-status') else before
        v.snap=lambda *x,**k:(c.body(self.e.json(ep['snapshot'])),{})
        calls=[]
        def request(name,tool,args):
            calls.append((tool,deepcopy(args)));v.serial+=1
            body={'accepted':True}
            if name=='arm-one-date-day':body['tactical_daily_sentinel']={'state':'armed','generation':3}
            if name=='date-only-status':body={'tactical_daily_sentinel':self.e.json(day['clock_source'])['clock']}
            row={'machine_id':'synthetic-A','body':body,'is_error':False}
            p=original_setup.h.write_new(self.root/f'common-horizon-response-{v.serial}.json',row)
            return row,{},original_setup.h.pin(p)
        v.request=request
        return calls

    def test_real_exact_day_wiring_allows_natural_current_stock_wallet_and_preserves_arrival(self):
        v=self.live;state=self.arrived();anchor=deepcopy(state['arrival_actual'])
        v.state=lambda:state;v.args.days=1
        ep,day=self.third();calls=self.wire_day(state,ep,day)
        result=v.advance_common_horizon();out=original_setup.h.load(result['state']['path'])
        self.assertEqual(len(out['days']),3)
        self.assertEqual(out['first_arrival_day'],2);self.assertEqual(out['arrival_actual'],anchor)
        self.assertEqual((out['actual']['cohort_current'],out['actual']['units'][0]['stock_raw'],out['actual']['treasury_raw']),
                         (99,2000000,25100000))
        self.assertEqual([args['step'] for _,args in calls],
            ['research-arm-tactical-daily-sentinel-v1-1048-to-1072-speed-5-mode-terminal-a-0',
             'resume-map','research-query-tactical-daily-sentinel-v1'])
        self.assertTrue(result['first_arrival_preserved']);self.assertFalse(result['Move_submitted'])
        self.assertFalse(result['absolute_D90_reached'])
        with self.assertRaisesRegex(RuntimeError,'arrival reached'):v.advance()

    def test_commander_change_missing_policy_and_absolute90_refuse_before_any_new_request(self):
        v=self.live;arrived=self.arrived();ep,day=self.third(change_commander=True)
        changed=a.update(arrived,day,ep,self.e);v.args.days=1
        v.request=lambda *x:self.fail('guard must reject before any request')
        v.endpoint=lambda *x:self.fail('guard must reject before any new frame')
        v.state=lambda:changed
        with self.assertRaisesRegex(RuntimeError,'commander/cohort/DATA/max changed'):v.advance_common_horizon()
        # A commander change after a real exact_day is retained as an executed
        # day and its bad independent endpoint, rather than erased as no advance.
        v.state=lambda:arrived;calls=self.wire_day(arrived,ep,day)
        with self.assertRaisesRegex(RuntimeError,'commander/cohort/DATA/max changed'):v.advance_common_horizon()
        stopped=original_setup.h.load(v.attempt/'HOLD-INTERRUPTION.actual.json')
        self.assertTrue(stopped['actual_day_executed']);self.assertEqual(stopped['date_raw'],1072)
        actual=original_setup.h.load(stopped['actual_state']['path'])
        self.assertEqual((actual['actual']['commander_id'],actual['first_arrival_day']),(11,2))
        self.assertEqual(len(calls),3)
        v.request=lambda *x:self.fail('guard must reject before any request')
        v.endpoint=lambda *x:self.fail('guard must reject before any new frame')
        v.state=lambda:arrived
        saved=v.plan['post_arrival_policy'];v.plan['post_arrival_policy']=None
        with self.assertRaisesRegex(RuntimeError,'prespecified'):v.advance_common_horizon()
        v.plan['post_arrival_policy']=saved
        ended=deepcopy(arrived);ended['days']=[None]*90;v.state=lambda:ended
        with self.assertRaisesRegex(RuntimeError,'before absolute day90'):v.advance_common_horizon()


if __name__=='__main__':unittest.main()
