"""Pure production-normalizer regressions; SYNTHETIC_ONLY, no installed CK3.

These are the stable-key assertions from the new native packet consumer. They
exercise checkout source without an external host, DLL or machine paths.
"""
import argparse
import ast
import copy
import sys
import unittest
from pathlib import Path

PARSER = argparse.ArgumentParser(add_help=False)
PARSER.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
ARGS, UNITTEST_ARGS = PARSER.parse_known_args()
SOURCE = ARGS.repo_root / 'ck3_autonomous_player/src/xar_autoplayer/bridge/title_holder_contract.py'
TREE = ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
FUNCTIONS = {'title_holder_id', 'normalize_title_holder_v1'}
CONSTANTS = {'TITLE_HOLDER_V1_SCHEMA', '_TITLE_KEY', '_TITLE_KEY_PREFIX'}
NODES = [node for node in TREE.body if
         isinstance(node, (ast.Import, ast.ImportFrom)) or
         (isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS) or
         (isinstance(node, ast.Assign) and any(
             isinstance(target, ast.Name) and target.id in CONSTANTS for target in node.targets))]
if {node.name for node in NODES if isinstance(node, ast.FunctionDef)} != FUNCTIONS:
    raise RuntimeError('The actual title-holder normalization functions are missing')
if {target.id for node in NODES if isinstance(node, ast.Assign)
    for target in node.targets if isinstance(target, ast.Name)} != CONSTANTS:
    raise RuntimeError('The actual additive stable-key contract constants are missing')
NAMESPACE = {}
exec(compile(ast.Module(body=NODES, type_ignores=[]), str(SOURCE), 'exec'), NAMESPACE)
NORMALIZE = NAMESPACE['normalize_title_holder_v1']
KEY_FIELDS = ('title_key', 'title_key_available', 'title_key_status', 'title_key_unavailable_reason')


def packet():
    # The same synthetic identity/frame and DTO shape as consumer02; no live key.
    return {'schema': 'xar.ck3.title-holder.v1', 'schema_version': 1,
            'game_version': '1.20.0.4', 'executable_sha256': 'synthetic-only',
            'available': True, 'status': 'available', 'unavailable_reason': None,
            'snapshot_revision': 40, 'date_raw': 53236632,
            'title_id': 2115, 'actor_character_id': 29829,
            'title_tier_raw': 6, 'title_tier_key': 'hegemony',
            'holder_character_id': 29829, 'holder_is_player': True,
            'holder_in_player_realm': True,
            'holder_immediate_liege_character_id': 29097,
            'holder_top_liege_character_id': 29097,
            'title_key': 'h_china', 'title_key_available': True,
            'title_key_status': 'available', 'title_key_unavailable_reason': None}


def normalize(value):
    return NORMALIZE(value, expected_title_id=2115, expected_actor_character_id=29829,
                     expected_snapshot_revision=40, expected_date_raw=53236632)


class StableKeyContract(unittest.TestCase):
    def test_current4_complete_hegemony_key(self):
        value = packet()
        result = normalize(value)
        self.assertEqual(result['title_key'], 'h_china')
        self.assertIs(result['title_key_available'], True)
        self.assertIsNone(result['title_key_unavailable_reason'])
        self.assertIsNot(result, value)

    def test_key_unavailable_preserves_legal_base_holder(self):
        value = packet()
        value.update(title_key=None, title_key_available=False,
                     title_key_status='unavailable',
                     title_key_unavailable_reason='title_key_read_or_format_unavailable')
        result = normalize(value)
        self.assertIs(result['available'], True)
        self.assertEqual(result['holder_character_id'], 29829)
        self.assertIs(result['holder_is_player'], True)
        self.assertIs(result['title_key_available'], False)
        self.assertIsNone(result['title_key'])

    def test_partial_and_incoherent_key_fields_rejected(self):
        for field in KEY_FIELDS:
            with self.subTest(missing=field):
                value = packet()
                del value[field]
                with self.assertRaises(ValueError):
                    normalize(value)
        malformed = [('title_key', ''), ('title_key', 'h_中国'),
                     ('title_key', 'l_china'), ('title_key', 'e_china'),
                     ('title_key', 'h_' + 'x' * 1023), ('title_key_available', 1),
                     ('title_key_status', 'unavailable'),
                     ('title_key_unavailable_reason', 'unknown')]
        for field, replacement in malformed:
            with self.subTest(field=field, replacement=replacement):
                value = packet()
                value[field] = replacement
                with self.assertRaises(ValueError):
                    normalize(value)
        for bad_key, reason in [('h_china', 'unknown'), (None, ''), (None, None)]:
            with self.subTest(unavailable_key=bad_key, reason=reason):
                value = packet()
                value.update(title_key=bad_key, title_key_available=False,
                             title_key_status='unavailable', title_key_unavailable_reason=reason)
                with self.assertRaises(ValueError):
                    normalize(value)

    def test_original_scope_and_tier_guards_retained(self):
        for field, replacement in [('date_raw', 53236633), ('title_id', 2116),
                                   ('title_id', True), ('actor_character_id', 29830),
                                   ('snapshot_revision', 41), ('title_tier_raw', 5)]:
            with self.subTest(field=field):
                value = packet()
                value[field] = replacement
                with self.assertRaises(ValueError):
                    normalize(value)

    def test_historical_v1_allowed_but_old_current4_packet_rejected(self):
        value = {key: field for key, field in packet().items() if key not in KEY_FIELDS}
        with self.assertRaises(ValueError):
            normalize(value)
        value['game_version'] = '1.20.0.3'
        result = normalize(value)
        self.assertIs(result['available'], True)
        self.assertNotIn('title_key', result)

    def test_unavailable_base_cannot_publish_available_key(self):
        value = packet()
        value.update(available=False, status='unavailable', unavailable_reason='title_generation_unavailable')
        for field in ('title_tier_raw', 'title_tier_key', 'holder_character_id',
                      'holder_is_player', 'holder_in_player_realm',
                      'holder_immediate_liege_character_id', 'holder_top_liege_character_id'):
            value[field] = None
        with self.assertRaises(ValueError):
            normalize(value)
        value.update(title_key=None, title_key_available=False, title_key_status='unavailable',
                     title_key_unavailable_reason='title_holder_unavailable')
        self.assertIs(normalize(value)['available'], False)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *UNITTEST_ARGS])
