"""Original h_china holding proof against checkout source; no installed CK3.

Four tests exercise the actual pure production functions with SYNTHETIC_ONLY
DTOs. They do not import the live adapter or read machine configuration, a
historical screenshot, an external inventory, or any installed game file.
"""
import ast
import copy
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / 'tools/ck3_mod_acceptance_cases/xqol_adapter.py'
TREE = ast.parse(TARGET.read_text(encoding='utf-8-sig'))
NAMES = {'require', 'owned_hegemony_ids', 'prove_original_song_holding'}
NODES = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in NAMES]
if {node.name for node in NODES} != NAMES:
    raise AssertionError('The actual public adapter holding-proof functions are missing')
NAMESPACE = {}
exec(compile(ast.Module(body=NODES, type_ignores=[]), str(TARGET), 'exec'), NAMESPACE)
PROVE = NAMESPACE['prove_original_song_holding']
OWNED = NAMESPACE['owned_hegemony_ids']


class OriginalHolding(unittest.TestCase):
    def setUp(self):
        self.frame = {'played_character': {'character_id': 20}, 'date_raw': 120,
                      'paused': True, 'active_event': None}
        self.root = {'campaign_root_context_ready': True, 'campaign_root_context': {
            'player_character_id': 20, 'date_raw': 120,
            'government': {'key': 'celestial_government'}, 'independent': True,
            'primary_title': {'title_id': 30, 'tier_raw': 5, 'tier_key': 'empire'},
            'held_title_partition': [
                {'title': {'title_id': 30, 'tier_raw': 5, 'tier_key': 'empire'}, 'primary': True},
                {'title': {'title_id': 40, 'tier_raw': 6, 'tier_key': 'hegemony'}, 'primary': False}]}}
        self.holder = {'title_holder': {'schema': 'xar.ck3.title-holder.v1', 'schema_version': 1,
            'available': True, 'status': 'available', 'title_id': 40, 'title_key': 'h_china',
            'title_key_available': True, 'title_key_status': 'available', 'title_key_unavailable_reason': None,
            'actor_character_id': 20, 'holder_character_id': 20, 'holder_is_player': True,
            'holder_in_player_realm': True, 'date_raw': 120,
            'title_tier_raw': 6, 'title_tier_key': 'hegemony'}}

    def call(self):
        return PROVE(self.root, [self.holder], self.frame, 20)

    def test_original_holding_can_be_nonprimary_without_fake_primary_key(self):
        result = self.call()
        self.assertTrue(result['held_not_required_primary'])
        self.assertEqual(result['title_key'], 'h_china')
        self.assertNotIn('key', self.root['campaign_root_context']['primary_title'])
        # More than one actual held hegemony is a finite query pool, not a
        # reason to require h_china as primary or pick a historical full ID.
        self.root['campaign_root_context']['held_title_partition'].append(
            {'title': {'title_id': 41, 'tier_raw': 6, 'tier_key': 'hegemony'}, 'primary': False})
        other = copy.deepcopy(self.holder)
        other['title_holder'].update(title_id=41, title_key='h_other')
        self.assertEqual(OWNED(self.root, self.frame, 20), [40, 41])
        result = PROVE(self.root, [other, self.holder], self.frame, 20)
        self.assertEqual(result['title_id'], 40)
        self.assertEqual(len(result['queried_owned_hegemony_keys']), 2)

    def test_current_native_stable_key_and_full_id_are_mandatory(self):
        for field, value in [('title_key', 'e_song'), ('title_key', ''), ('title_key', None),
                             ('title_key', 'h_中'), ('title_key', 40), ('title_id', True),
                             ('title_id', 0), ('title_id', 2**31), ('title_id', 41)]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.holder)
                self.holder['title_holder'][field] = value
                with self.assertRaises(ValueError):
                    self.call()
                self.holder = original
        del self.holder['title_holder']['title_key']
        with self.assertRaises(ValueError):
            self.call()

    def test_actual_owned_title_and_native_holder_agreement_are_mandatory(self):
        original = copy.deepcopy(self.root)
        self.root['campaign_root_context']['held_title_partition'].pop()
        with self.assertRaises(ValueError):
            self.call()
        self.root = original
        for field, value in [('available', False), ('status', 'unavailable'), ('schema_version', True),
                             ('title_key_available', False), ('title_key_available', 1),
                             ('title_key_status', 'unavailable'), ('title_key_unavailable_reason', 'read_failed'),
                             ('holder_character_id', 21), ('actor_character_id', 21),
                             ('holder_is_player', False), ('holder_in_player_realm', False),
                             ('date_raw', 121), ('title_tier_raw', 5)]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.holder)
                self.holder['title_holder'][field] = value
                with self.assertRaises(ValueError):
                    self.call()
                self.holder = original
        with self.assertRaises(ValueError):
            PROVE(self.root, [self.holder, self.holder], self.frame, 20)

    def test_original_actor_government_independence_and_date_are_mandatory(self):
        for field, value in [('player_character_id', 21), ('date_raw', 121),
                             ('government', {'key': 'steppe_admin_government'}), ('independent', False)]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.root)
                self.root['campaign_root_context'][field] = value
                with self.assertRaises(ValueError):
                    self.call()
                self.root = original
        for field, value in [('paused', False), ('active_event', {'instance_id': 1})]:
            with self.subTest(field=field, value=value):
                original = copy.deepcopy(self.frame)
                self.frame[field] = value
                with self.assertRaises(ValueError):
                    self.call()
                self.frame = original


if __name__ == '__main__':
    unittest.main(verbosity=2)
