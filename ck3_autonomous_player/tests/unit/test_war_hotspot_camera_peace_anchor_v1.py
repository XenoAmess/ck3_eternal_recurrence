"""New camera RED cases only; no Game, desktop input or old matrix replay."""
from copy import deepcopy
import unittest

from xar_autoplayer.bridge.war_hotspot_camera import (
    LandedProvinceIndex, follow_war_hotspot, select_war_hotspot,
)


def frame():
    return {'snapshot_id': 'observed-frame-21', 'revision': 21, 'native_revision': 701,
            'date_raw': 148433440, 'paused': True, 'map_ready': True,
            'played_character': {'character_id': 29829, 'alive': True},
            'active_wars': []}


def observed_root(snapshot):
    return {'status': 'available', 'query_sequence': 5,
            'queried_snapshot_id': snapshot['snapshot_id'],
            'queried_revision': snapshot['revision'],
            'queried_native_revision': snapshot['native_revision'],
            'campaign_root_context': {
                'status': 'available', 'snapshot_revision': snapshot['native_revision'],
                'date_raw': snapshot['date_raw'], 'player_character_id': 29829,
                'capital_province_id': 12,
                'readiness': {'ready': False, 'capital_ready': True,
                              'held_title_partition_ready': True,
                              'selected_game_rule_tokens_ready': False},
                'held_title_partition': []}}


class PeaceCameraAnchorTests(unittest.TestCase):
    def test_observed_peace_anchor_binding_and_army_zero_compound(self):
        index = LandedProvinceIndex({12: 'b_observed_capital', 34: 'b_observed_county'},
                                    {12: 'c_capital', 34: 'c_county'}, ())
        snapshot = frame()
        root = observed_root(snapshot)

        class Service:
            def __init__(self):
                self.calls = []
                self.verified = True

            def center_map_on_landed_title_v1(self, title_key, *, expected_revision):
                self.calls.append((title_key, expected_revision))
                return {'status': 'centered', 'title': {'key': title_key},
                        'camera_center': {'postcondition_verified': self.verified}}

        with self.subTest(branch='peace_capital_optional_unknown'):
            service = Service()
            result = follow_war_hotspot(service, snapshot, index, campaign_root_result=root)
            self.assertEqual(service.calls, [('b_observed_capital', 21)])
            self.assertEqual(result['hotspot']['reason'], 'player_capital')
            self.assertEqual(result['hotspot']['province_id'], 12)
            self.assertEqual(result['hotspot']['query_sequence'], 5)
            self.assertIsNone(result['hotspot']['army_id'])
            self.assertFalse(root['campaign_root_context']['readiness']['ready'])

        with self.subTest(branch='held_county_fallback_uses_observed_province'):
            fallback = deepcopy(root)
            fallback['campaign_root_context']['capital_province_id'] = 999
            fallback['campaign_root_context']['held_title_partition'] = [
                {'title': {'title_id': 81, 'tier_raw': 2, 'tier_key': 'county'}, 'capital_province_id': 34},
                {'title': {'title_id': 79, 'tier_raw': 2, 'tier_key': 'county'}, 'capital_province_id': 12},
                {'title': {'title_id': 77, 'tier_raw': 3, 'tier_key': 'duchy'}, 'capital_province_id': 34},
            ]
            hotspot = select_war_hotspot(snapshot, index, campaign_root_result=fallback)
            self.assertEqual((hotspot['reason'], hotspot['held_title_id'], hotspot['title_key']),
                             ('player_held_county_capital', 79, 'b_observed_capital'))

        with self.subTest(branch='war_priorities_and_real_army_zero'):
            war = deepcopy(snapshot)
            war['active_wars'] = [{'war_id': 9, 'allied_armies': [
                {'army_id': 5, 'controllable': True, 'in_combat': True, 'current_province_id': 34},
                {'army_id': 0, 'controllable': True, 'in_combat': True, 'current_province_id': 12},
            ], 'war_objective_province_ids': [34]}]
            hotspot = select_war_hotspot(war, index, campaign_root_result=root)
            self.assertEqual((hotspot['reason'], hotspot['army_id'], hotspot['province_id']), ('battle', 0, 12))
            armies = war['active_wars'][0]['allied_armies']
            armies[0]['in_combat'] = False
            armies[1].update(in_combat=False, army_state='sieging')
            self.assertEqual(select_war_hotspot(war, index, campaign_root_result=root)['reason'], 'siege')
            armies[1].update(army_state='idle', move_target_province_id=34)
            self.assertEqual(select_war_hotspot(war, index, campaign_root_result=root)['reason'], 'moving_player_army')
            armies.clear()
            objective = select_war_hotspot(war, index, campaign_root_result=root)
            self.assertEqual(objective['reason'], 'war_objective')
            self.assertIsNone(objective['army_id'])

        for key, value in (('queried_snapshot_id', 'old'), ('queried_revision', 20),
                           ('queried_native_revision', 700), ('query_sequence', 0)):
            with self.subTest(branch='reject_stale_envelope', field=key):
                stale = deepcopy(root)
                stale[key] = value
                service = Service()
                result = follow_war_hotspot(service, snapshot, index, campaign_root_result=stale)
                self.assertEqual(result['status'], 'no_observable_land_hotspot')
                self.assertEqual(service.calls, [])
        for key, value in (('player_character_id', 42), ('date_raw', 7), ('snapshot_revision', 700)):
            with self.subTest(branch='reject_wrong_root_identity', field=key):
                stale = deepcopy(root)
                stale['campaign_root_context'][key] = value
                self.assertIsNone(select_war_hotspot(snapshot, index, campaign_root_result=stale))

        for invalid in (None, 0, False, -1, 999):
            with self.subTest(branch='no_invented_land_anchor', capital=invalid):
                missing = deepcopy(root)
                missing['campaign_root_context']['capital_province_id'] = invalid
                self.assertIsNone(select_war_hotspot(snapshot, index, campaign_root_result=missing))
        with self.subTest(branch='no_unbound_or_unready_anchor'):
            self.assertIsNone(select_war_hotspot(snapshot, index))
            unready = deepcopy(root)
            unready['campaign_root_context']['readiness']['capital_ready'] = False
            self.assertIsNone(select_war_hotspot(snapshot, index, campaign_root_result=unready))
            not_map = {**snapshot, 'map_ready': False}
            self.assertIsNone(select_war_hotspot(not_map, index, campaign_root_result=root))
        with self.subTest(branch='peace_follow_requires_native_verified_postcondition'):
            service = Service()
            service.verified = False
            with self.assertRaisesRegex(ValueError, 'verified native postcondition'):
                follow_war_hotspot(service, snapshot, index, campaign_root_result=root)
            self.assertEqual(service.calls, [('b_observed_capital', 21)])


if __name__ == '__main__':
    unittest.main(verbosity=2)
