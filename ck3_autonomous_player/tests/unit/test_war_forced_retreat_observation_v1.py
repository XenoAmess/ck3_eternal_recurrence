"""Replay the actual1118/1119 priority failure through the whole Service."""
import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge import native_driver as nd
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.war_forced_retreat_observation_v1 import native_forced_retreat_observation_v1

FIXTURE=Path(__file__).parents[1]/'fixtures/p79_actual1118_forced_retreat.json'


def material():
    packet=json.loads(FIXTURE.read_text(encoding='utf-8'))
    s=copy.deepcopy(packet['actual_semantic'])
    caps=set(s['diagnostics']['hello']['capabilities'])
    steps=set(nd._action_steps(sorted(caps),s['active_event'],s['pending_character_interaction'],
        s['active_wars'],s['player_armies'],paused=True))
    # These composites are derived from the original clock capability closure
    # by the production driver's capabilities(), not native direct commands.
    steps.update(('life-advance','life-advance-one-day'))
    return packet,s,steps,caps


def plan(s,steps,caps):
    driver=CallbackGameplayDriver(backend_id='native-headless',snapshot=lambda:copy.deepcopy(s),
        execute=lambda *_:(_ for _ in()).throw(AssertionError('no Native/MCP')),
        action_steps=tuple(steps))
    original=driver.capabilities
    driver.capabilities=lambda:{**original(),'bridge_capabilities':list(caps)}
    return GameplayBridgeService(driver).plan_turn()['plan']


class ExistingNativeForcedRetreatTests(unittest.TestCase):
    def test_actual_whole_service_uses_original_global_audit_and_one_native_day(self):
        packet,s,steps,caps=material()
        self.assertEqual(packet['actual_blocked_plan']['required_observation'],'single-idle-controllable-army-binding')
        self.assertEqual(len(s['player_armies']),1)
        self.assertTrue(s['active_wars'][0]['objective_province_states'][0]['active_siege'])
        self.assertEqual(s['active_wars'][0]['player_relative_war_score'],-87)
        # No patched core, cached old plan, or invented history. The complete
        # ordinary Service path receives the unchanged actual semantic body.
        p=plan(s,steps,caps)
        self.assertEqual(p['phase'],'native_war_global_combat_retreat_progress')
        self.assertEqual(p['selected_step'],'life-advance-one-day')
        self.assertFalse(p['active_attack_allowed'])
        evidence=p['native_forced_retreat_observation_v1']
        self.assertEqual(evidence['army_ids'],[167772577])
        self.assertFalse(evidence['new_retreat_order']);self.assertFalse(evidence['contact_free_proven'])
        speed,_=nd._life_advance_timeline_policy(s,horizon_days=1,exact_one_day=True,available_action_steps=steps)
        self.assertEqual(speed,1)
        self.assertFalse(nd._noncombat_generic_exact_day_speed_five_ready(s,exact_one_day=True,
            result_step='life-advance-one-day',bridge_capabilities=caps,available_action_steps=steps))

    def test_whole_service_rejects_inconsistent_native_state_route_and_missing_clock(self):
        _,s,steps,caps=material()
        for change in('state','owner','route','idle','clock'):
            ss=copy.deepcopy(s);cc=set(caps)
            if change=='state':ss['player_armies'][0]['army_state_code']=1
            elif change=='owner':ss['player_armies'][0]['owner_character_id']=1
            elif change=='route':ss['player_armies'][0]['route_province_ids']=[2623]
            elif change=='idle':ss['player_armies'][0].update(army_state='regular',army_state_code=1,
                retreating=False,route_province_ids=[],route_read_status='complete_empty',move_target_province_id=None)
            else:cc.remove(next(iter(nd._TACTICAL_DAILY_SENTINEL_REQUIRED_CAPABILITIES)))
            with self.subTest(change=change):
                p=plan(ss,steps,cc)
                self.assertNotEqual(p.get('selected_step'),'life-advance-one-day')
                self.assertIsNot(p.get('active_attack_allowed'),True)

    def test_new_event_modal_and_non_native_state_are_not_retreat_permission(self):
        _,s,_,_=material()
        for change in('event','modal','dead','source','in_combat'):
            ss=copy.deepcopy(s)
            if change=='event':ss['active_event']={'instance_id':1}
            elif change=='modal':ss['top_exclusive_modal_choice_hint']={'status':'present'}
            elif change=='dead':ss['played_character']['alive']=False
            elif change=='source':ss['source']='software-input'
            else:ss['player_armies'][0]['in_combat']=True
            with self.subTest(change=change):self.assertIsNone(native_forced_retreat_observation_v1(ss,ss['player_armies']))


if __name__=='__main__':unittest.main()
