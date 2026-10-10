"""Portable candidate tests; no game, cache files, or immutable seed reads."""
import copy
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('candidate_builder', HERE / 'build_candidate.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
_, after = builder.render()
cache = types.ModuleType('candidate_graphics_cache')
cache.__file__ = str(builder.ROOT / builder.HELPER)
exec(compile(after[builder.HELPER], cache.__file__, 'exec'), cache.__dict__)


def sig(n):
    return {'bytes': n, 'sha256': str(n % 10) * 64}


def ref(name, n):
    return {'path': str((HERE / name).resolve()), **sig(n)}


class ReviewedPythonCacheCompatibilityTests(unittest.TestCase):
    def setUp(self):
        host = 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        self.source = {'manifest': ref('source.json', 1), 'source_index': ref('source-index.json', 2),
                       'native_index': ref('native-index.json', 3), 'host_relative': host,
                       'profile_features': {'shader_cache_reuse': True},
                       'entry_environment': {'PYTHONPATH_parts': ['source_root/tools']},
                       'files': {host: sig(10), 'ck3_autonomous_player/src/xar_autoplayer/mcp/service.py': sig(11),
                                 'native/bridge.cpp': sig(12)}, 'native_files': {'native/bridge.cpp': sig(12)}}
        self.target = copy.deepcopy(self.source)
        self.target.update(manifest=ref('target.json', 4), source_index=ref('target-index.json', 5),
                           native_index=ref('target-native-index.json', 6))
        self.target['files'][host] = sig(20)
        self.target['files']['ck3_autonomous_player/src/xar_autoplayer/mcp/service.py'] = sig(21)
        self.target['files']['tests/test_pause.py'] = sig(22)
        self.original = {'runtime': {'game': {'version': 'fixture'}, 'exe': sig(30), 'host': sig(10),
                        'native': {'dll': sig(31), 'injector': sig(32)}, 'host_features': {'saved': True},
                        'source_core_sha256': 'a' * 64, 'native_files_sha256': 'b' * 64,
                        'prepare_only_paths': ['tools/prepare.py']},
                         'profile': {'graphics': sig(40), 'gui': sig(41), 'descriptors': [sig(42)],
                                     'DLC': ['fixture'], 'settings': sig(43)}}
        self.current = copy.deepcopy(self.original)
        self.current['runtime'].update(host=sig(20), source_core_sha256='c' * 64)
        self.seed_pin = ref('manifest.json', 7)
        self.seed = {'source_origin': ref('origin.json', 8)}
        self.review_pin = ref('review.json', 9)
        self.review = {'schema': 'ck3-mod-acceptance-reviewed-python-cache-compatibility-v1',
                       'seed': self.seed_pin, 'source_origin': self.seed['source_origin'],
                       'source_key_sha256': cache._digest(self.original),
                       'target_key_sha256': cache._digest(self.current),
                       'source_delta': cache._python_delta(self.source['files'], self.target['files']),
                       'native_source_delta': {}, 'reviewer': 'fixture reviewer', 'direct_reviewed': True,
                       'reason': 'Explicit Python-only diagnostic change; engine inputs unchanged',
                       'qualification': cache.QUALIFICATION, 'startup_qualified': False, 'business_pass': False}
        for side, audit in (('source', self.source), ('target', self.target)):
            self.review[side + '_manifest'] = audit['manifest']
            self.review[side + '_index'] = audit['source_index']
            self.review[side + '_native_index'] = audit['native_index']

    def assess(self):
        with patch.object(cache, '_checked', return_value=self.review):
            return cache._reviewed_python_compatibility(self.review_pin, self.seed_pin, self.seed,
                                                       self.original, self.current, self.source, self.target)

    def test_reviewed_python_change_retains_both_full_keys(self):
        audit = self.assess()
        self.assertNotEqual(audit['source_key_sha256'], audit['target_key_sha256'])
        self.assertEqual(audit['source_runtime_key'], self.original['runtime'])
        self.assertEqual(audit['target_runtime_key'], self.current['runtime'])
        self.assertIsNone(audit['engine_cache_hit'])
        self.assertIs(audit['business_pass'], False)

    def test_review_and_exact_index_bindings_are_mandatory(self):
        for field, value in (('direct_reviewed', 1), ('reviewer', ''), ('source_index', ref('wrong.json', 2)),
                             ('target_key_sha256', 'f' * 64), ('source_delta', {}), ('business_pass', True)):
            with self.subTest(field=field):
                old = self.review[field]
                self.review[field] = value
                with self.assertRaises(ValueError): self.assess()
                self.review[field] = old

    def test_game_native_and_profile_changes_are_rejected_even_if_reviewed(self):
        changes = [('runtime', 'exe'), ('runtime', 'native'), ('runtime', 'game'), ('runtime', 'host_features'),
                   ('profile', 'graphics'), ('profile', 'gui'), ('profile', 'descriptors'),
                   ('profile', 'DLC'), ('profile', 'settings')]
        for section, field in changes:
            with self.subTest(section=section, field=field):
                old = self.current[section][field]
                self.current[section][field] = {'changed': True}
                self.review['target_key_sha256'] = cache._digest(self.current)
                with self.assertRaises(ValueError): self.assess()
                self.current[section][field] = old
        self.review['target_key_sha256'] = cache._digest(self.current)

    def test_non_python_and_unindexed_host_changes_are_rejected(self):
        self.target['native_files']['native/bridge.cpp'] = sig(99)
        self.review['native_source_delta'] = cache._python_delta(self.source['native_files'], self.target['native_files'])
        with self.assertRaises(ValueError): self.assess()
        self.target['native_files'] = copy.deepcopy(self.source['native_files'])
        self.review['native_source_delta'] = {}
        self.target['files'][self.target['host_relative']] = sig(99)
        self.review['source_delta'] = cache._python_delta(self.source['files'], self.target['files'])
        with self.assertRaises(ValueError): self.assess()

    def test_seed_path_preserves_default_rejection_and_full_origin_validation(self):
        seed = {'schema': cache.SEED_SCHEMA_V2, 'qualification': cache.QUALIFICATION,
                'startup_qualified': False, 'business_pass': False, 'source_origin': self.seed['source_origin'],
                'graphics_projection': {}, 'cache_key': self.original,
                'cache_key_sha256': cache._digest(self.original)}
        selection = types.SimpleNamespace(state_dir=HERE, manifest={}, runtime={})
        with patch.object(cache, '_checked', return_value=seed), \
             patch.object(cache, '_origin', return_value=({}, {}, {}, self.original, {})) as origin, \
             patch.object(cache, 'business_files', return_value={}), \
             patch.object(cache, '_profile_key_v2', return_value=self.current['profile']), \
             patch.object(cache, '_runtime_key', return_value=self.current['runtime']):
            with self.assertRaisesRegex(ValueError, '^Graphics cache key mismatch$'):
                cache._seed(self.seed_pin, selection, {})
            origin.assert_called_once()
            seed['cache_key_sha256'] = 'f' * 64
            with self.assertRaisesRegex(ValueError, '^Original graphics cache key mismatch$'):
                cache._seed(self.seed_pin, selection, {}, compatibility_pin=self.review_pin)

    def test_legacy_seed_cannot_use_exception_and_origin_errors_propagate(self):
        seed = {'schema': cache.SEED_SCHEMA, 'qualification': cache.QUALIFICATION,
                'startup_qualified': False, 'business_pass': False}
        with patch.object(cache, '_checked', return_value=seed):
            with self.assertRaisesRegex(ValueError, 'requires explicit v2 seed'):
                cache._seed(self.seed_pin, None, {}, compatibility_pin=self.review_pin)
        seed.update(schema=cache.SEED_SCHEMA_V2, source_origin=self.seed['source_origin'])
        with patch.object(cache, '_checked', return_value=seed), \
             patch.object(cache, '_origin', side_effect=ValueError('Frozen origin changed')):
            with self.assertRaisesRegex(ValueError, '^Frozen origin changed$'):
                cache._seed(self.seed_pin, None, {}, compatibility_pin=self.review_pin)


if __name__ == '__main__':
    unittest.main()
