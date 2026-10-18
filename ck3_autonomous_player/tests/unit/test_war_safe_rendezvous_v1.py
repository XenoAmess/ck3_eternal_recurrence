"""Actual separated positions; hypothetical same-frame route qualifications."""
import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer import strategy
from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.war_safe_rendezvous_v1 import (review_safe_war_rendezvous_v1,
    assess_rendezvous_locked_route_v1)

FIXTURES = Path(__file__).parents[1] / 'fixtures'
HOSTILES = (402653372, 436207707, 654311862)
MOVER, ANCHOR = 486539625, 167772577


def material():
    actual = json.loads((FIXTURES/'p79_actual658_separated_armies.json').read_text(encoding='utf-8'))
    old = json.loads((FIXTURES/'p66_actual105107_origin_exposure.json').read_text(encoding='utf-8'))
    s = copy.deepcopy(old['semantic_schema_scaffold'])
    s.update({k:actual['planning_source_frame'][k] for k in ('snapshot_id','native_revision','revision','date_raw','episode_run_id')})
    s['diagnostics']['connection_generation'] = 20
    s['diagnostics']['hello']['connection_generation'] = 20
    war = copy.deepcopy(actual['war_progress_before'])
    own = war.pop('player_armies')
    # Hypothetical complete current snapshot fields are explicit; actual658's
    # compact war progress is not asserted to publish ownership or occupation.
    for a in own:
        a.update(owner_character_id=40695,controllable=True,route_read_status='complete_empty')
    war.update(player_side='defender',player_is_primary_war_leader=True,
        targeted_title_ids=[2230],allied_armies=copy.deepcopy(own),
        objective_province_states=[{'province_id':p,'occupation_observable':True,'is_occupied':False}
                                  for p in (2619,2623,8755)])
    s.update(active_wars=[war],player_armies=own,active_event=None,pending_character_interaction=None,history=[])
    s['army_strengths'] = [{**r,'scope_role':'player' if r['army_id'] in (MOVER,ANCHOR) else 'active_war_enemy',
        'war_ids':[war['war_id']]} for r in actual['strength_rows']]
    s.update(army_strengths_status='available',army_strengths_queried_snapshot_id=s['snapshot_id'],
        army_strengths_queried_revision=s['revision'])
    baseline = {'policy':'one-life-turn-v1','phase':'native_war_stationary_objective_hold_sentinel',
        'selected_step':f'war-objective-hold-sentinel-advance-war-100663323-army-{ANCHOR}-at-2619-until-{s["date_raw"]+168}',
        'reason':'original stationary defense','active_attack_allowed':False}
    caps={nd.PREVIEW_MOVE_ARMY_CAPABILITY,nd.MOVE_ARMY_CAPABILITY,
          nd.QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY,nd.WAR_OBJECTIVES_CAPABILITY,nd.MERGE_ARMIES_CAPABILITY}
    steps=set(nd._action_steps(sorted(caps),None,None,s['active_wars'],s['player_armies'],paused=True))
    return actual,old,baseline,s,steps,caps


def history(s,old):
    # Software Native schema fixtures, not actual new preview/H1 receipts.
    lease=copy.deepcopy(old['actual105']['query_frame'])
    for rk,sk in (('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
                  ('queried_native_revision','native_revision'),('queried_date_raw','date_raw'),
                  ('queried_episode_run_id','episode_run_id')):
        lease[rk]=s[sk]
    lease.update(queried_connection_generation=20,queried_actor_character_id=40695)
    preview=copy.deepcopy(old['actual103']['route_preview'])
    preview.update(army_id=MOVER,origin_province_id=2623,target_province_id=2619,
        previewed_date_raw=s['date_raw'],route_province_ids=[2619])
    def timed(ident,current,route,arrivals):
        return {'timeline_observable':True,'army_id':ident,'current_province_id':current,
            'effective_origin_province_id':current,'route_province_ids':route,'arrival_date_raws':arrivals}
    hostile=[timed(e['army_id'],e['current_province_id'],e['route_province_ids'],
        [s['date_raw']+24*(30+i) for i in range(len(e['route_province_ids']))])
        for e in s['active_wars'][0]['enemy_armies']]
    def h(ident,current,target,route,arrivals):
        return {'status':'available','date_raw':s['date_raw'],'snapshot_revision':s['native_revision'],
            'subject_army_id':ident,'target_province_id':target,'hostile_army_ids':list(HOSTILES),
            'subject_route':timed(ident,current,route,arrivals),'hostile_routes':copy.deepcopy(hostile),
            'horizon_start_date_raw':s['date_raw'],'horizon_end_date_raw':s['date_raw']+24,
            'one_day_contact_free':True,'conflicts':[]}
    return [
        {'index':1,'command':strategy.preview_move_army_step(MOVER,2619),'ok':True,'result':{**lease,'route_preview':preview}},
        {'index':2,'command':strategy.query_route_contact_horizon_step(MOVER,2619,HOSTILES),'ok':True,
         'result':{**lease,'route_contact_horizon':h(MOVER,2623,2619,[2619],[s['date_raw']+48])}},
        {'index':3,'command':strategy.query_route_contact_horizon_step(ANCHOR,2619,HOSTILES),'ok':True,
         'result':{**lease,'route_contact_horizon':h(ANCHOR,2619,2619,[],[])}},
    ]


def service_plan(b,s,h,steps,caps):
    ss=copy.deepcopy(s);ss['history']=h
    driver=CallbackGameplayDriver(backend_id='native-headless',snapshot=lambda:copy.deepcopy(ss),
        execute=lambda *_:(_ for _ in ()).throw(AssertionError('zero Native/MCP')),action_steps=tuple(steps))
    original=driver.capabilities
    driver.capabilities=lambda:{**original(),'bridge_capabilities':list(caps)}
    # Keep a real ordinary return, then exercise the unmodified public choose
    # return chain through siege/general/origin/H3937 and Service admission.
    with mock.patch.object(strategy,'_choose_one_life_turn_core',return_value=b):
        return GameplayBridgeService(driver).plan_turn()['plan']


class SafeRendezvousTests(unittest.TestCase):
    def test_seven_before_eight_at_first_waypoint_is_not_origin_safety(self):
        _,old,b,s,steps,caps=material();h=history(s,old)
        h[0]['result']['route_preview']['route_province_ids']=[2624,2619]
        h[1]['result']['route_contact_horizon']['subject_route'].update(
            route_province_ids=[2624,2619],arrival_date_raws=[s['date_raw']+192,s['date_raw']+240])
        # Explicit hypothetical Native-schema counterexample: origin2623 and
        # waiting friend2619 remain safe, but a hostile reaches2624 atday7.
        for row in h[1:]:
            enemy=row['result']['route_contact_horizon']['hostile_routes'][0]
            enemy.update(route_province_ids=[2624],arrival_date_raws=[s['date_raw']+168])
        horizon=h[1]['result']['route_contact_horizon']
        from xar_autoplayer.bridge.war_contract import normalize_route_contact_horizon
        normalized=normalize_route_contact_horizon(horizon,expected_subject_army_id=MOVER,
            expected_target_province_id=2619,expected_hostile_army_ids=HOSTILES,
            expected_date_raw=s['date_raw'],expected_snapshot_revision=s['native_revision'])
        self.assertTrue(normalized['one_day_contact_free'])
        from xar_autoplayer.war_route_origin_exposure_v1 import assess_origin_exposure_v1
        self.assertFalse(assess_origin_exposure_v1(normalized,subject_army_id=MOVER,
            origin_province_id=2623,target_province_id=2619,hostile_army_ids=HOSTILES,
            date_raw=s['date_raw'],native_revision=s['native_revision'])['veto'])
        exposure=assess_rendezvous_locked_route_v1(normalized)
        self.assertTrue(exposure['veto'])
        self.assertEqual(exposure['known_route_conflicts'][0]['province_id'],2624)
        p=service_plan(b,s,h,steps,caps)
        self.assertNotEqual(p.get('selected_step'),f'move-army-{MOVER}-to-2619')
        # When the semantic route agrees, the ORIGINAL static route audit
        # already rejects the same path, independent of one-day contact.
        enemy=copy.deepcopy(s['active_wars'][0]['enemy_armies'][0])
        enemy.update(move_target_province_id=2624,route_province_ids=[2624])
        self.assertEqual(strategy._audit_war_route([2624,2619],origin_province_id=2623,
            target_province_id=2619,enemies=[enemy])['status'],'unsafe')

    def test_actual_local_opportunity_is_not_global_superiority_or_battle_permission(self):
        actual,_,b,s,steps,caps=material()
        self.assertEqual([a['current_province_id'] for a in actual['war_progress_before']['player_armies']],[2619,2623])
        self.assertEqual([a['current_province_id'] for a in actual['war_progress_after']['player_armies']],[2619,2623])
        p=service_plan(b,s,[],steps,caps)
        self.assertEqual(p['selected_step'],f'preview-move-army-{MOVER}-to-2619')
        evidence=p['war_safe_rendezvous_v1']
        self.assertEqual(evidence['observed_own_total'],2034)
        self.assertEqual(evidence['observed_all_hostile_total'],2521)
        self.assertEqual(evidence['local_opportunities'][0]['observed_current_soldiers'],1465)
        self.assertIn(654311862,evidence['all_hostile_army_ids'])
        self.assertIsNone(evidence['battle_win_probability']);self.assertFalse(p['active_attack_allowed'])

    def test_complete_service_sequence_requires_each_friendly_horizon_before_move(self):
        _,old,b,s,steps,caps=material();h=history(s,old)
        for count,expected in ((1,h[1]['command']),(2,h[2]['command']),(3,f'move-army-{MOVER}-to-2619')):
            with self.subTest(count=count):
                p=service_plan(b,s,h[:count],steps,caps)
                self.assertEqual(p['selected_step'],expected);self.assertFalse(p['active_attack_allowed'])
        moved=service_plan(b,s,h,steps,caps)
        self.assertEqual(moved['war_safe_rendezvous_v1']['stage'],'move_candidate')
        self.assertFalse(moved['war_safe_rendezvous_v1']['arrival_guaranteed'])
        # The existing, independently guarded consolidation chooses the merge
        # after actual arrival; this consumer never invents CanMerge success.
        arrived=copy.deepcopy(s)
        for army in arrived['player_armies']:
            army['current_province_id']=2619
        consolidation=strategy._preoffensive_army_consolidation(arrived,
            controlled_armies=arrived['player_armies'],war_id=100663323)
        self.assertEqual(consolidation['step'],f'merge-armies-{ANCHOR}-with-{MOVER}')
        self.assertIs(review_safe_war_rendezvous_v1(b,commands=h,snapshot=arrived,
            action_steps=steps,bridge_capabilities=caps),b)

    def test_locked_origin_waiting_army_and_source_scope_guards(self):
        _,old,b,s,steps,caps=material();h=history(s,old)
        for change in ('origin_7_before_8','anchor_entry','contact','stale_native','scope','strength_frame',
                       'event','committed_friend','missing_occupation','missing_merge','other_war'):
            ss,hh=copy.deepcopy((s,h));cc=set(caps)
            if change in ('origin_7_before_8','anchor_entry'):
                hh[1]['result']['route_contact_horizon']['subject_route']['arrival_date_raws']=[s['date_raw']+192]
                for row in hh[1:]:
                    enemy=row['result']['route_contact_horizon']['hostile_routes'][0]
                    enemy.update(route_province_ids=[2623 if change=='origin_7_before_8' else 2619],arrival_date_raws=[s['date_raw']+168])
            elif change=='contact':hh[-1]['result']['route_contact_horizon']['one_day_contact_free']=False
            elif change=='stale_native':hh[-1]['result']['queried_native_revision']-=1
            elif change=='scope':
                for row in hh[1:]:row['result']['route_contact_horizon']['hostile_army_ids'].pop()
            elif change=='strength_frame':ss['army_strengths_queried_snapshot_id']='native:1'
            elif change=='event':ss['active_event']={'instance_id':1}
            elif change=='committed_friend':ss['player_armies'][1].update(move_target_province_id=2623,route_province_ids=[2623],army_state='moving')
            elif change=='missing_occupation':ss['active_wars'][0]['objective_province_states']=[]
            elif change=='missing_merge':cc.remove(nd.MERGE_ARMIES_CAPABILITY)
            else:ss['active_wars'].append(copy.deepcopy(ss['active_wars'][0]))
            with self.subTest(change=change):
                p=service_plan(b,ss,hh,steps,cc)
                self.assertNotEqual(p.get('selected_step'),f'move-army-{MOVER}-to-2619')
                self.assertIsNot(p.get('active_attack_allowed'),True)
        original={'phase':'native_war_general_battle_model_rejected','selected_step':None,'active_attack_allowed':False}
        self.assertIs(review_safe_war_rendezvous_v1(original,commands=h,snapshot=s,
            action_steps=steps,bridge_capabilities=caps),original)


if __name__=='__main__':unittest.main()
