from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

from xar_autoplayer.bridge.war_contract import war_termination_negative_query_signature
from xar_autoplayer.war_termination_query_cadence_v1 import war_termination_query_policy_defer_v1
from xar_autoplayer.strategy import _stationary_objective_hold_target_date_raw


class WarTerminationCadenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = json.loads((ROOT / 'fixtures/termination_six_query_projection.json').read_text(encoding='utf-8'))['rows']

    def setup_case(self, war_id=33554458):
        current = next(row for row in self.actual if row['source_sequence'] == 1847)
        frame = current['planning_source_frame']
        wars = deepcopy(current['record']['result']['termination_query_context']['active_war_signature'])
        war = next(w for w in wars if w['war_id'] == war_id)
        snapshot = {
            'paused': True, 'map_ready': True, 'active_event': None,
            'pending_character_interaction': None, 'one_life_terminal_reason': None,
            'date_raw': frame['date_raw'], 'episode_run_id': frame['episode_run_id'],
            'played_character': {'character_id': frame['actor_character_id'], 'alive': True},
            'diagnostics': {'connection_generation': frame['connection_generation']},
        }
        records = [deepcopy(row['record']) for row in self.actual if row['record']['result']['war_termination_options']['war_id'] == war_id and row['source_sequence'] < 1847]
        return snapshot, wars, war, list(reversed(records))

    def eval(self, case):
        return war_termination_query_policy_defer_v1(*case)

    def test_actual_two_wars_each_defer_independently_with_unrelated_score_change(self):
        for war_id in (33554458, 50331679):
            result = self.eval(self.setup_case(war_id))
            self.assertEqual(result['status'], 'policy_deferred_after_two_no_action_queries')
            self.assertEqual(result['war_id'], war_id)
            self.assertFalse(result['fresh_native_result'])
            self.assertIsNone(result['native_legality'])
            self.assertEqual(result['business_action_credit'], 0)
            self.assertEqual(result['expires_date_raw'], 53222016 + 30*24)

    def test_first_query_or_same_day_duplicate_does_not_count_two(self):
        snapshot, wars, war, records = self.setup_case()
        self.assertIsNone(self.eval((snapshot, wars, war, records[:1])))
        duplicate = deepcopy(records[0])
        duplicate['result']['query_sequence'] += 1
        self.assertIsNone(self.eval((snapshot, wars, war, [duplicate,records[0]])))

    def test_expiry_requeries_then_one_monthly_renewal_is_allowed(self):
        snapshot, wars, war, records = self.setup_case()
        snapshot['date_raw'] = 53222016 + 30*24
        self.assertIsNone(self.eval((snapshot, wars, war, records)))
        renewal=deepcopy(records[0]); renewal['result']['query_sequence'] += 100
        renewal['result']['termination_query_context']['queried_date_raw']=snapshot['date_raw']
        snapshot['date_raw'] += 7*24
        result=self.eval((snapshot,wars,war,[renewal,*records]))
        self.assertEqual(result['expires_date_raw'],53222016+60*24)

    def test_new_war_role_actor_episode_connection_and_terminal_scores_requery(self):
        mutations=(
            lambda s,ws,w: ws.append({**deepcopy(w),'war_id':999}),
            lambda s,ws,w: w.__setitem__('player_is_primary_war_leader',False),
            lambda s,ws,w: s['played_character'].__setitem__('character_id',999),
            lambda s,ws,w: s.__setitem__('episode_run_id','different'),
            lambda s,ws,w: s['diagnostics'].__setitem__('connection_generation',4),
            lambda s,ws,w: w.__setitem__('player_relative_war_score',100),
            lambda s,ws,w: w.__setitem__('player_relative_war_score',-100),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                snapshot,wars,war,records=self.setup_case()
                mutate(snapshot,wars,war)
                self.assertIsNone(self.eval((snapshot,wars,war,records)))

    def test_cb_change_positive_exit_failed_query_and_submit_barrier_requery(self):
        snapshot,wars,war,records=self.setup_case()
        cb_change=deepcopy(records)
        options=cb_change[0]['result']['war_termination_options']
        options['active_casus_belli_identity']['database_index']=71
        cb_change[0]['result']['termination_query_context']['negative_decision_signature']=war_termination_negative_query_signature(options)
        self.assertIsNone(self.eval((snapshot,wars,war,cb_change)))
        positive=deepcopy(records)
        options=positive[0]['result']['war_termination_options']
        options['options']['white_peace']['recipient_response']={'status':'available','would_accept_now':True,'decision_status_raw':1}
        positive[0]['result']['termination_query_context']['negative_decision_signature']=war_termination_negative_query_signature(options)
        self.assertIsNone(self.eval((snapshot,wars,war,positive)))
        accepted=deepcopy(records)
        options=accepted[0]['result']['war_termination_options']
        options['options']['white_peace']['auto_accept_observable']=True
        options['options']['white_peace']['auto_accept']=True
        accepted[0]['result']['termination_query_context']['negative_decision_signature']=war_termination_negative_query_signature(options)
        self.assertIsNone(self.eval((snapshot,wars,war,accepted)))
        failed=deepcopy(records); failed[0]['ok']=False
        self.assertIsNone(self.eval((snapshot,wars,war,failed)))
        barrier={'step':'offer-white-peace-war-33554458','ok':True,'result':{'accepted':True}}
        self.assertIsNone(self.eval((snapshot,wars,war,[barrier,*records])))
        self.assertIsNone(self.eval((snapshot,wars,war,[{'step':'life-advance','ok':True,'result':{'war_action':{'status':'submitted'}}},*records])))
        event={'step':'resolve-current-event','ok':True,'result':{}}
        self.assertIsNone(self.eval((snapshot,wars,war,[records[0],event,records[1]])))

    def test_event_pending_and_hold_deadline(self):
        snapshot,wars,war,records=self.setup_case()
        result=self.eval((snapshot,wars,war,records))
        summary=[{'war_id':war['war_id'],'war_termination_query_policy_defer':result}]
        self.assertEqual(_stationary_objective_hold_target_date_raw(result['expires_date_raw']-24,summary),result['expires_date_raw'])
        snapshot['active_event']={'event_id':42}
        self.assertIsNone(self.eval((snapshot,wars,war,records)))
        snapshot['active_event']=None
        snapshot['pending_character_interaction']={'interaction_id':7}
        self.assertIsNone(self.eval((snapshot,wars,war,records)))
        snapshot['pending_character_interaction']=None
        snapshot['top_exclusive_modal_choice_hint']={'status':'present'}
        self.assertIsNone(self.eval((snapshot,wars,war,records)))

    def test_known_claim_cb_legal_day_is_not_hidden_by_monthly_lease(self):
        snapshot,wars,war,records=self.setup_case()
        war['player_side']='attacker'
        for item in wars:
            if item['war_id']==war['war_id']:
                item['player_side']='attacker'
        for record in records:
            result=record['result']; options=result['war_termination_options']; context=result['termination_query_context']
            options['player_side']='attacker'
            options['player_is_primary_war_leader']=True
            options['active_casus_belli_identity']={'database_index':70,'canonical_key':'claim_cb'}
            options['cb_allows_white_peace']=True
            options['war_duration_days']=360 if context['queried_date_raw']==records[0]['result']['termination_query_context']['queried_date_raw'] else 353
            for row in context['active_war_signature']:
                if row['war_id']==war['war_id']:
                    row['player_side']='attacker'
            context['negative_decision_signature']=war_termination_negative_query_signature(options)
            context['queried_war_duration_days']=options['war_duration_days']
        # The latest query was at day 360.  On day 365 the old lease must end.
        snapshot['date_raw']=records[0]['result']['termination_query_context']['queried_date_raw']+5*24
        self.assertIsNone(self.eval((snapshot,wars,war,records)))


if __name__=='__main__':
    unittest.main()
