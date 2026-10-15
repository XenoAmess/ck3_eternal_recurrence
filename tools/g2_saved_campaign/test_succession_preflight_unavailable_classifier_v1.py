"""Portable classifier tests; no SDK, Game, desktop or external evidence needed."""
import copy
import unittest

from succession_preflight_unavailable_classifier_v1 import classify_succession_preflight_unavailable_v1 as classify


def body():
    frame={'schema':'xar.ck3.planning-source-frame/v1','status':'complete','snapshot_id':'native:82',
        'revision':7,'native_revision':82,'date_raw':12000,'actor_character_id':101,
        'episode_run_id':'offline-101','connection_generation':2,'bridge_pid':55}
    reason='adjacent_external_province_holders_unavailable'
    return {'status':'readonly_unavailable','selected_step':None,'snapshot_id':'native:82','revision':7,
        'planning_source_frame':frame,'plan':{'phase':'succession_preflight_root_unavailable',
            'selected_step':None,'reason':reason,'read_only':True,'replan_required':True},
        'result':{'schema':'xar.succession-preflight-unavailable.v1','status':'unavailable',
            'available':False,'read_only':True,'business_submission':False,'accepted':False,
            'replan_required':True,'replay_allowed':False,'succession_expectation_retained':False,
            'unavailable_reason':reason,'binding':dict(frame),'source':{
                'capability':'game.command.query-campaign-root-context-v1','query_sequence':9}}}


class Tests(unittest.TestCase):
    baseline={'actor_character_id':101,'episode_run_id':'offline-101','date_raw':11000}

    def test_forward_date_from_bootstrap_and_every_success_credit_false(self):
        result=classify(body(),initial_frame=self.baseline,game_pid=55)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['business_submission'])
        for k in result:
            if k.endswith('_verified') or k in ('date_advanced','lifestyle_applied','primitive_business_success'):
                self.assertFalse(result[k],k)

    def test_foreign_actor_episode_pid_and_backward_date_rejected(self):
        for key,value in [('actor_character_id',102),('episode_run_id','other'),('date_raw',12001)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                classify(body(),initial_frame={**self.baseline,key:value},game_pid=55)
        with self.assertRaises(ValueError):
            classify(body(),initial_frame=self.baseline,game_pid=56)

    def test_action_or_success_claim_and_bad_frame_rejected(self):
        mutations=[lambda x:x.update(selected_step='life-advance'),
            lambda x:x['result'].update(accepted=True),
            lambda x:x['result'].update(business_submission=True),
            lambda x:x['planning_source_frame'].update(snapshot_id='other')]
        for mutate in mutations:
            value=copy.deepcopy(body());mutate(value)
            with self.assertRaises(ValueError): classify(value,initial_frame=self.baseline,game_pid=55)

    def test_unknown_status_is_not_generalized(self):
        self.assertIsNone(classify({'status':'executed'}))


if __name__=='__main__':unittest.main()
