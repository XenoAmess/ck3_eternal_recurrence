"""Pure G4 seam tests; fallback metadata is synthetic, never common qualification."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE if (HERE / 'c3_common_g4_observation.py').is_file() else HERE.parent))
import c3_common_g4_observation as seam

SYNTHETIC = 'SYNTHETIC_TEST_DATA_NOT_COMMON_RUNTIME'
SOURCE = None
EXPLICIT_BINDING = None
REPOSITORY_SOURCE_ROOT = HERE.parent


def parse_test_cli(argv):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--source-binding', type=Path)
    parser.add_argument('--repository-source-root', type=Path, default=REPOSITORY_SOURCE_ROOT)
    return parser.parse_known_args(argv)


def repository_test_binding(repo, temporary_root):
    """Pin four real repository DTOs in small, explicitly synthetic test metadata."""
    repo = repo.resolve(strict=True)
    def save(name, value):
        path = temporary_root / name
        raw = (json.dumps(value, indent=2) + '\n').encode('utf-8')
        path.write_bytes(raw)
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    files = {}
    for name in ('confucian_challenger_graph_v1', 'confucian_readonly_private_v1',
                 'nonwar_private_build', 'version_identity'):
        relative = 'ck3_autonomous_player/src/xar_autoplayer/bridge/' + name + '.py'
        raw = (repo / relative).read_bytes()
        files[relative] = {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    index = save('synthetic-source-index.json', {'fixture_kind': SYNTHETIC, 'files': files})
    head = '0' * 40  # Explicit test placeholder; never a claimed common source commit.
    receipt = save('synthetic-successor.json', {'fixture_kind': SYNTHETIC,
        'source_commit': head, 'source_root': str(repo), 'source_index': index})
    manifest = save('synthetic-manifest.json', {'fixture_kind': SYNTHETIC,
        'host_features': {'confucian_challenger_readonly': True},
        'capabilities': {seam.TOOL: {'source_build_ready': True}}})
    return {'schema': seam.SOURCE_SCHEMA, 'source_head': head, 'source_root': str(repo),
        'source_index': index, 'python_successor': receipt, 'manifest': manifest,
        'game': {'version': '1.20.0.4', 'executable_sha256':
            '98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518'},
        'native_basis': {'fixture_kind': SYNTHETIC, 'live_qualification': False}}


class CommonG4SeamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global SOURCE
        if EXPLICIT_BINDING is not None:
            SOURCE = json.loads(EXPLICIT_BINDING.read_text(encoding='utf-8-sig'))
        else:
            temporary = tempfile.TemporaryDirectory(prefix='c3-g4-synthetic-test-')
            cls.addClassCleanup(temporary.cleanup)
            SOURCE = repository_test_binding(REPOSITORY_SOURCE_ROOT, Path(temporary.name))
        cls.graph, cls.private, cls.dto_pins = seam.load_selected_dto(SOURCE)

    def fixture(self, *, empty=False):
        graph, private = self.graph, self.private
        frame = {'revision': 3, 'native_revision': 7, 'snapshot_id': 'native:7', 'date_raw': 53144712,
            'source': 'injected-dll-named-pipe', 'backend_id': 'native-headless', 'episode_projection': 'native_campaign',
            'paused': True, 'speed': 0, 'map_ready': True, 'one_life_terminal_reason': None,
            'played_character': {'character_id': 31254, 'alive': True},
            'diagnostics': {'connected': True, 'bridge_pid': 991, 'connection_generation': 2,
                'hello': {'pid': 991, 'connection_generation': 2, 'ck3_build_match': True,
                    'game_adapter_id': 'ck3-1.20.0.4-msvc-x64', 'expected_ck3_version': '1.20.0.4',
                    'expected_ck3_sha256': private.CK3_12004.executable_sha256}}}
        binding = private.query_binding(frame, 3)
        title = {'available': True, 'unavailable_reason': None, 'title_absent': False,
            'title_full_id': 0x81000001, 'native_title_class': 'CLandedTitle', 'holder_absent': False,
            'holder_character_full_id': 65865, 'holder_current_faith_full_id': 107,
            'title_properties': {'available': True, 'unavailable_reason': None,
                **{key: True for key in graph.PROPERTY_FIELDS}},
            'title_laws': {'available': True, 'unavailable_reason': None, 'native_count': 1,
                'complete_laws': [{'native_definition_id': 95, 'key': graph.LAW}],
                'expected_law_key': graph.LAW, 'expected_law_member': True}}
        relation = {'challenger_title_full_id': title['title_full_id'], 'available': True, 'unavailable_reason': None,
            'challenger_title': deepcopy(title), 'registered_sponsor_title': deepcopy(title),
            'scope_sponsor_available': True, 'scope_lookup_complete': True, 'scope_sponsor_unavailable_reason': None,
            'scope_lookup_faith_full_id': 107, 'scope_lookup_native_count': 1,
            'scope_lookup_faith_matches_collection': True, 'scope_matches_registered_pair': True,
            'scope_sponsor_title': deepcopy(title)}
        native = {'schema': graph.SCHEMA, 'game_version': '1.20.0.4',
            'executable_sha256': private.CK3_12004.executable_sha256, 'read_only': True,
            'available': True, 'graph_complete': True, 'unavailable_reason': None, 'capture_epoch': 44,
            'date_raw': binding['date_raw'], 'played_character_id': 31254, 'played_character_full_id': 31254,
            'requested_faith_full_ids': [107], 'faiths': [{'requested_faith_full_id': 107, 'available': True,
                'collection_complete': True, 'unavailable_reason': None, 'native_count': 0 if empty else 1,
                'complete_native_challenger_title_ids': [] if empty else [title['title_full_id']],
                'challengers': [] if empty else [relation]}], 'mod_owned_markers': None,
            'saved_owner_faith_variables': None, 'qualification': {key: private.ACTUAL4_ABI_INDEX_SHA256
                if key.endswith('_index_sha256') else value for key, value in graph.QUALIFICATION.items()}}
        step, domain, backend, nested, _ = private.OPERATIONS['challenger_graph']
        envelope = {'step': step, 'accepted': True, 'status': 'observed', 'private_build': True,
            'read_only': True, 'advertised': False, 'game_version': '1.20.0.4',
            'executable_sha256': private.CK3_12004.executable_sha256, 'domain_key': domain,
            'backend_id': private._operation_backend(backend, private.CK3_12004),
            'snapshot_revision': 7, 'date_raw': binding['date_raw'], nested: native}
        public = graph.project_native_graph_query(envelope, binding, [107])
        step = {'id': 'synthetic-common-G4-only', 'tool': seam.TOOL,
            'args': {'expected_revision': 3, 'faith_full_ids': [107]}, 'fresh_revision': False}
        plan = {'steps': [step]}
        packet = {'rows': [{'id': step['id'], 'plan': deepcopy(step), 'ok': True,
            'started_at': 'synthetic-start', 'finished_at': 'synthetic-finish', 'result': public}],
            'business_PASS_inferred': False}
        return frame, plan, packet

    def qualify(self, values):
        return seam.qualify_observation(*values, self.graph, self.private)

    def test_actual_selected_dto_handles_nonempty_common_row_without_business_or_owner_credit(self):
        values = self.fixture()
        before = deepcopy(values)
        result = self.qualify(values)
        self.assertEqual(values, before)
        self.assertEqual(result['complete_native_collections'][0]['complete_native_challenger_title_ids'], [0x81000001])
        self.assertEqual(result['sponsor_scope_rule'], 'challenger_holder_current_faith')
        for name in ('new_title_full_id', 'formal_C3_business_credit', 'saved_owner_faith_qualification',
                     'saved_collection_serialization_qualification'):
            self.assertIsNone(result[name])
        self.assertTrue(all(Path(row['path']).is_relative_to(Path(SOURCE['source_root'])) for row in self.dto_pins))

    def test_complete_empty_is_observation_only_not_saved_omission_evidence(self):
        result = self.qualify(self.fixture(empty=True))
        self.assertEqual(result['complete_native_collections'][0]['native_count'], 0)
        self.assertIsNone(result['saved_collection_serialization_qualification'])

    def test_legacy_profile_and_mismatched_original_plan_are_rejected(self):
        frame, plan, packet = self.fixture()
        with self.assertRaises(ValueError):
            self.qualify((frame, plan, {'schema': 'ck3.native-profile-receipt.v1'}))
        packet['rows'][0]['plan']['tool'] = 'ck3_query_profile_confucian_challenger_graph_v1'
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))

    def test_unknown_arguments_and_non_strict_revision_selectors_are_rejected(self):
        for invalid in (True, '3', 0):
            frame, plan, packet = self.fixture()
            plan['steps'][0]['args']['expected_revision'] = invalid
            with self.subTest(revision=invalid), self.assertRaises(ValueError): self.qualify((frame, plan, packet))
        for invalid in ([107, 107], (107,), ['107'], [True], [2**32-1]):
            frame, plan, packet = self.fixture()
            plan['steps'][0]['args']['faith_full_ids'] = invalid
            with self.subTest(selectors=invalid), self.assertRaises(ValueError): self.qualify((frame, plan, packet))
        frame, plan, packet = self.fixture()
        plan['steps'][0]['args']['unknown'] = 1
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))

    def test_actual_dto_rejects_cross_frame_and_forged_native_saved_owner_faith(self):
        frame, plan, packet = self.fixture()
        packet['rows'][0]['result']['queried_native_revision'] += 1
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))
        frame, plan, packet = self.fixture()
        packet['rows'][0]['result']['native_result']['confucian_challenger_graph']['saved_owner_faith_variables'] = {'107': 107}
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))

    def test_actual_dto_rejects_partial_collection_and_wrong_holder_faith_scope(self):
        frame, plan, packet = self.fixture()
        native = packet['rows'][0]['result']['native_result']['confucian_challenger_graph']
        native['faiths'][0]['native_count'] = 2
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))
        frame, plan, packet = self.fixture()
        native = packet['rows'][0]['result']['native_result']['confucian_challenger_graph']
        native['faiths'][0]['challengers'][0]['scope_lookup_faith_full_id'] = 108
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))

    def test_unavailable_or_unsuccessful_original_row_is_not_complete_observation(self):
        frame, plan, packet = self.fixture()
        packet['rows'][0]['ok'] = False
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))
        frame, plan, packet = self.fixture()
        public = packet['rows'][0]['result']
        native = public['native_result']['confucian_challenger_graph']
        native.update(available=False, graph_complete=False, faiths=None, unavailable_reason='synthetic_copy_failed')
        public['native_result']['status'] = 'unavailable'
        with self.assertRaises(ValueError): self.qualify((frame, plan, packet))

    def test_missing_or_false_shared_permission_is_rejected_before_dto_use(self):
        actual = seam.read_ref
        for features in ({}, {'confucian_challenger_readonly': False}, {'confucian_challenger_readonly': 1}):
            def read(reference, cap):
                value = actual(reference, cap)
                if reference == SOURCE['manifest']:
                    value['host_features'] = features
                return value
            with self.subTest(features=features), patch.object(seam, 'read_ref', side_effect=read), self.assertRaises(ValueError):
                seam.load_selected_dto(SOURCE)


    def test_repository_fallback_is_synthetic_and_cli_optional(self):
        if EXPLICIT_BINDING is not None:
            self.skipTest('Explicit frozen binding mode does not use the repository fallback')
        self.assertEqual(SOURCE['source_head'], '0' * 40)
        self.assertEqual(SOURCE['native_basis'], {'fixture_kind': SYNTHETIC, 'live_qualification': False})
        for key in ('source_index', 'python_successor', 'manifest'):
            self.assertEqual(seam.read_ref(SOURCE[key], 32768)['fixture_kind'], SYNTHETIC)
        self.assertEqual(len(self.dto_pins), 4)
        self.assertTrue(all(Path(row['path']).is_relative_to(REPOSITORY_SOURCE_ROOT.resolve())
                            for row in self.dto_pins))
        options, rest = parse_test_cli([])
        self.assertIsNone(options.source_binding)
        self.assertEqual(rest, [])
        with patch.object(sys, 'argv', ['unittest', '--unrelated-runner-argument']):
            imported = runpy.run_path(str(Path(__file__)), run_name='synthetic_import_only')
        self.assertIsNone(imported['SOURCE'])
        self.assertIsNone(imported['EXPLICIT_BINDING'])
        result = self.qualify(self.fixture(empty=True))
        self.assertEqual(result['status'], 'COMPLETE_NATIVE_COLLECTION_OBSERVED')
        self.assertIsNone(result['formal_C3_business_credit'])


if __name__ == '__main__':
    options, rest = parse_test_cli(sys.argv[1:])
    EXPLICIT_BINDING = options.source_binding
    REPOSITORY_SOURCE_ROOT = options.repository_source_root
    unittest.main(argv=[sys.argv[0], *rest])
