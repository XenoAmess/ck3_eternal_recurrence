"""Offline observations; the genuine R0175 files remain historical .3 evidence."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

SOURCE_ROOT = Path(__file__).resolve().parents[3]
ROOT = Path(os.environ.get('CK3_E04_REFERENCE_ROOT', SOURCE_ROOT))
MODULE = SOURCE_ROOT / 'ck3_autonomous_player/src/xar_autoplayer/bridge/army_split_merge_observation_12004.py'
spec = importlib.util.spec_from_file_location('army_split_merge_observation_12004', MODULE)
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
EVIDENCE = ROOT / 'promo/ck3_native_war_ai/episode-04-march-logistics/evidence/r0175-B-merge-upper-cap'


def frame(revision, ids):
    return {'snapshot_id':f'native:{revision}', 'revision':revision+1, 'native_revision':revision,
            'paused':True,'map_ready':True,'date_raw':1234,'episode_run_id':'synthetic-only',
            'played_character':{'character_id':29829,'alive':True},
            'diagnostics':{'bridge_pid':567,'connection_generation':1},
            'player_armies':[{'army_id':i,'controllable':True,'owner_character_id':29829,
                              'current_province_id':1506} for i in ids]}


def strength(identity=9, predicate=None):
    row={'army_regiment_id':identity,'current_soldiers':1,'maximum_soldiers':1,'scale':1}
    data={'army_regiment_id':identity,'status':'available','ready':True,
          'native_data_record_count':0,'records':[]}
    if predicate is not None:
        data['native_loss_writer_skipped']=predicate
    return row,data


class SplitMergeObservationTests(unittest.TestCase):
    def test_actual_old_B_stays_failed_with_extra_1_1_and_changed_commander(self):
        pre=json.loads((EVIDENCE/'sources/pre-observation.json').read_text(encoding='utf-8'))
        post=json.loads((EVIDENCE/'sources/fresh-post-observation.json').read_text(encoding='utf-8'))
        result=contract.compare_split_merge_cohorts(pre['health']['army_strengths'],post['health']['army_strengths'])
        self.assertFalse(result['frozen_exact_cohort_pass'])
        self.assertEqual(result['added_ids'],[16778273])
        self.assertEqual(result['changed_original_strength_ids'],[])
        self.assertEqual(result['changed_original_DATA_ids'],[])
        self.assertEqual(result['original_before_current_max'],[6689,6747])
        self.assertEqual(result['original_after_current_max'],[6689,6747])
        self.assertEqual(result['whole_after_current_max'],[6690,6748])
        self.assertEqual(result['added_regiments'][0]['kind'],'unclassified_1_1')
        commanders=[]
        for name,observation in [('pre-commander-0.json',pre),('fresh-post-commander-0.json',post)]:
            packet=json.loads((EVIDENCE/'sources'/name).read_text(encoding='utf-8'))
            commanders.append(contract.read_bound_current_commander(packet,observation['before'],army_id=0,native_carmy_id=0))
        self.assertEqual(commanders,[27357,33388])
        terminal=json.loads((EVIDENCE/'terminal-sources/formal-B-terminal.json').read_text(encoding='utf-8'))
        self.assertEqual(terminal['status'],'STOPPED_GATE_INCOMPLETE')
        self.assertFalse(terminal['deadline_reached'])

    def test_1_1_does_not_supply_the_predicate_or_a_knight_label(self):
        row,data=strength()
        result=contract.classify_regiment_observation(row,data)
        self.assertEqual(result['kind'],'unclassified_1_1')
        self.assertIsNone(result['player_troop_class'])
        self.assertFalse(result['physical_soldier_write_observed'])

    def test_character_override_is_separate_from_birth_and_physical_writes(self):
        row,data=strength(predicate=True)
        result=contract.classify_regiment_observation(row,data)
        self.assertEqual(result['kind'],'character_override_1_1')
        self.assertFalse(result['birth_producer_observed'])
        self.assertFalse(result['physical_soldier_write_observed'])
        data['native_loss_writer_skipped']=False
        self.assertEqual(contract.classify_regiment_observation(row,data)['kind'],'noncharacter_empty_DATA')

    def test_fresh_split_uses_set_difference_and_independent_native_map(self):
        before,after=frame(5,[0,41]),frame(6,[0,777,41])
        packet={'accepted':True,'queried_snapshot_id':after['snapshot_id'],'queried_revision':after['revision'],
                'queried_native_revision':after['native_revision'],
                'army_strengths':[{'status':'available','army_id':0,'native_carmy_id':10},
                                  {'status':'available','army_id':777,'native_carmy_id':888}]}
        pre_packet={'accepted':True,'queried_snapshot_id':before['snapshot_id'],'queried_revision':before['revision'],
                    'queried_native_revision':before['native_revision'],
                    'army_strengths':[{'status':'available','army_id':0,'native_carmy_id':10}]}
        result=contract.identify_split_sibling(before,after,source_army_id=0,pre_strengths=pre_packet,post_strengths=packet)
        self.assertEqual(result['sibling_army_id'],777)
        self.assertEqual(result['native_carmy_ids'],{0:10,777:888})
        self.assertFalse(result['cohort_conservation_verified'])
        for mutation in ('same_frame','multiple_new','lost_old','wrong_mapping','new_date','new_process','new_episode','changed_generation','invalid_native'):
            a,p=copy.deepcopy(after),copy.deepcopy(packet)
            if mutation=='same_frame':a=copy.deepcopy(before)
            if mutation=='multiple_new':a['player_armies']+=frame(6,[778])['player_armies']
            if mutation=='lost_old':a['player_armies']=[r for r in a['player_armies'] if r['army_id']!=41]
            if mutation=='wrong_mapping':p['queried_native_revision']=5
            if mutation=='new_date':a['date_raw']+=24
            if mutation=='new_process':a['diagnostics']['bridge_pid']+=1
            if mutation=='new_episode':a['episode_run_id']='different'
            if mutation=='changed_generation':p['army_strengths'][0]['native_carmy_id']=11
            if mutation=='invalid_native':p['army_strengths'][1]['native_carmy_id']=-1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                contract.identify_split_sibling(before,a,source_army_id=0,pre_strengths=pre_packet,post_strengths=p)

    def test_partial_DATA_is_not_zero_and_duplicate_fullid_is_not_deduplicated(self):
        row,data=strength()
        army={'status':'available','regiment_count':1,'current_soldiers':1,'maximum_soldiers':1,
              'regiment_strengths':[row],'regiment_replenishment_records_v1':[data]}
        partial=copy.deepcopy(army)
        partial['regiment_replenishment_records_v1'][0]['status']='unavailable'
        for armies in ([partial],[army,army]):
            with self.assertRaises(ValueError):contract.compare_split_merge_cohorts(armies,[army])

    def test_known_absent_commander_stays_distinct_from_unavailable(self):
        f=frame(6,[0])
        packet={'accepted':True,'read_only':True,'queried_snapshot_id':f['snapshot_id'],
                'queried_revision':f['revision'],'queried_native_revision':f['native_revision'],
                'army_commander_candidates':{'army_id':0,'native_carmy_id':10,'date_raw':f['date_raw'],
                 'snapshot_revision':f['native_revision'],
                 'current_commander':{'status':'absent','character_id':None}}}
        self.assertIsNone(contract.read_bound_current_commander(packet,f,army_id=0,native_carmy_id=10))
        packet['army_commander_candidates']['current_commander']['status']='unavailable'
        with self.assertRaises(ValueError):
            contract.read_bound_current_commander(packet,f,army_id=0,native_carmy_id=10)


if __name__=='__main__':
    unittest.main()
