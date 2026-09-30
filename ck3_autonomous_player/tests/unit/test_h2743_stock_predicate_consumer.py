"""Two focused production consumer cases; all binary/build inputs are fixtures."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from xar_autoplayer.bridge.defender_dejure_exit_terms_v1 import (
    RESOURCES, SCHEMA, UNAVAILABLE_REASONS, normalize_defender_dejure_exit_terms_v1,
)
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.h2743_exit_readonly_transport import (
    BASELINE_STEP, bind_admitted_stock_predicates, query_h2743_exit_baseline,
)
from xar_autoplayer.h2743_stock_predicate_admission import (
    EVIDENCE_SCHEMA, PAIR_SCHEMA, PINS_SCHEMA, verify_admitted_stock_predicate_pair,
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fixture_pair(root, *, invalid_source_identity=False):
    """Synthetic bytes prove verifier behavior; never an actual native pair."""
    head = 'a' * 40
    checkout = root / 'checkout'
    source_path = checkout / 'native.cpp'
    source_path.parent.mkdir(parents=True)
    source_path.write_text('// synthetic consumer fixture only\n', encoding='utf-8')
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
    manifest = {'schema': 'xar.ck3.h2743.native-source-tracked.v1',
        'source_tree': str(checkout), 'source_head': head, 'base_head': 'b' * 40,
        'files': [{'relative_path': 'native.cpp',
                   'path': None if invalid_source_identity else str(source_path),
                   'size_bytes': source_path.stat().st_size, 'sha256': source_sha}]}
    manifest_sha = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest().upper()
    route = root / 'route.json'
    route_sha = write(route, {'source_head': head, 'full_route_closed': True,
        'game_launched': False, 'material_complete': False, 'action_literal': None,
        'closed_stages': ['parser', 'firstguard', 'handler', 'submit', 'permitted_callback',
                          'installed_callback', 'application_main_executor']})
    pair = {'schema': PAIR_SCHEMA, 'head': head,
        'candidate_identity_proposed': 'h2743-stock-predicate-application-main-v1',
        'stock_predicate_protocol': EVIDENCE_SCHEMA,
        'shared_native_source_manifest_sha256': manifest_sha,
        'route_receipt': {'path': str(route), 'sha256': route_sha}, 'source_quartet': {}}
    for name in ('xar_checkpoint.ck3', 'driver-state.json', 'first-heir-marriage-formal-v1.json',
                 'xar_ck3_bridge.dll'):
        path = root / 'seed' / name
        digest = write(path, {'synthetic': name})
        pair['source_quartet'][name] = {'path': str(path), 'sha256': digest}
    for kind in ('dll', 'injector'):
        build = root / kind
        asset = build / 'synthetic-binary.bin'
        asset_sha = write(asset, {'synthetic_binary': kind})
        for name in ('source-native-tracked-before.json', 'source-native-tracked-after.json'):
            assert write(build / name, manifest) == manifest_sha
        deps_sha = write(build / 'actual-dependencies.json', {
            'external_dependency_paths': [], 'project_source_headers': [
                {'path': 'native.cpp', 'sha256': source_sha}]})
        result_path, post_path = build / 'result.json', build / 'post.json'
        result_sha = write(result_path, {'head': head, 'source_inputs_unchanged': True,
            'game_launched': False, 'go_executed': False})
        post_sha = write(post_path, {'head': head, 'clean': True, 'source_file_lists_equal': True,
            'source_before_sha256': manifest_sha, 'source_after_sha256': manifest_sha,
            'deps_sha256': deps_sha})
        (build / 'build').mkdir()
        (build / 'build/CMakeCache.txt').write_text('CMAKE_BUILD_TYPE:STRING=Release\n'
            'XAR_CK3_ENABLE_H2743_STOCK_PREDICATE_READER_V1:BOOL=ON\n', encoding='utf-8')
        write(build / 'build-result.json', {'exit_code': 0})
        write(build / 'ctest-result.json', {'exit_code': 0})
        (build / 'ctest-stdout.txt').write_text('100% tests passed, 0 tests failed\n', encoding='utf-8')
        pair[kind] = {'path': str(asset), 'sha256': asset_sha, 'build_result': str(result_path),
                     'build_result_sha256': result_sha, 'postcheck': str(post_path), 'postcheck_sha256': post_sha}
    pair_path = root / 'pair.json'
    pair_sha = write(pair_path, pair)
    pins = {'schema': PINS_SCHEMA, 'pair_sha256': pair_sha, 'source_head': head,
        'source_manifest_sha256': manifest_sha, 'route_receipt_sha256': route_sha,
        'dll_sha256': pair['dll']['sha256'], 'injector_sha256': pair['injector']['sha256']}
    pins_path = root / 'pins.json'
    write(pins_path, pins)
    return pair_path, pins_path, checkout


def baseline(*, admitted=False):
    unavailable = {'status': 'unavailable', 'value': None,
                   'unavailable_reason': 'stock_condition_reader_unavailable'}
    false = {'status': 'observed', 'value': False, 'unavailable_reason': None}
    truce = {'schema': 'xar.ck3.defender-de-jure-truce-inputs.v1',
        **{key: deepcopy(false) for key in ('attacker_flexible_truces_perk',
            'attacker_government_is_nomadic', 'defender_government_is_nomadic', 'nomad_both')},
        **{key: deepcopy(unavailable) for key in ('short', 'long', 'border_raid_pair')},
        'evaluated_days': None, 'persisted_expiry_date_raw': None}
    body = {'schema': SCHEMA, 'war_id': 16777231, 'native_revision': 3, 'date_raw': 53217264,
        'casus_belli_database_index': 17, 'casus_belli_key': 'individual_county_de_jure_cb',
        'primary_attacker_character_id': 30097, 'primary_defender_character_id': 29829,
        'target_title_ids': [2128], 'target_title_holder_prestate': [{'title_id': 2128,
            'holder_character_id': 29829, 'holder_immediate_liege_character_id': None}],
        'primary_resource_balances': [{'character_id': actor, 'resource': resource,
            'value': {'raw': 0, 'scale': 100_000}} for actor in (30097, 29829) for resource in sorted(RESOURCES)],
        'primary_monthly_gold_income': [{'character_id': actor, 'value': {'raw': 0, 'scale': 100_000}}
                                       for actor in (30097, 29829)],
        'same_frame_stable': True, 'material_complete': False, 'truce_inputs_v1': truce,
        'border_raid_storage_candidate_v1': {'schema': 'xar.ck3.h2743-border-raid-storage-candidate.v1',
            'status': 'structural_candidate_only', 'candidate': False, 'storage_capacity': 8,
            'active_war_count': 1, 'matching_war_count': 0, 'unavailable_reason': None,
            'native_condition_observed': False}}
    for key, reason in UNAVAILABLE_REASONS.items():
        body[key] = None
        body[key + '_unavailable_reason'] = reason
    if admitted:
        body['h2743_stock_predicate_evidence_v1'] = {'schema': EVIDENCE_SCHEMA,
            'native_revision': 3, 'date_raw': 53217264, 'actor_character_id': 29829,
            'war_id': 16777231, 'attacker_character_id': 30097, 'defender_character_id': 29829,
            'paused': True, 'map_ready': True, 'application_main_thread_id': 77,
            'pump_epoch': 8, 'mailbox_sequence': 9, 'executor_invocations': 1,
            'same_frame_stable': True, 'stock_double_sample_stable': True,
            'stock_parties_bound': True, 'material_complete': False}
        truce['short'] = {'status': 'observed', 'value': True, 'unavailable_reason': None}
        truce['long'] = deepcopy(false)
        truce['border_raid_pair'] = {'status': 'unavailable', 'value': None,
                                   'unavailable_reason': 'stock_condition_definition_unavailable'}
    return body


def normalize(body, admission=None):
    return normalize_defender_dejure_exit_terms_v1(body, expected_war_id=16777231,
        expected_native_revision=3, expected_date_raw=53217264, expected_defender_id=29829,
        expected_attacker_id=30097, expected_target_title_ids=[2128], stock_predicate_admission=admission)


class StockPredicateConsumerTest(unittest.TestCase):
    def test_explicit_pair_and_independent_typed_values_preserve_default(self):
        with tempfile.TemporaryDirectory() as directory:
            pair, pins, checkout = fixture_pair(Path(directory))
            source, admission = verify_admitted_stock_predicate_pair(pair, pins_path=pins,
                native_source_checkout=checkout)
            self.assertFalse(source['native_condition_observed'])
            old = normalize(baseline())
            self.assertIsNone(old['truce_inputs_v1']['short']['value'])
            with self.assertRaises(ValueError):
                normalize(baseline(admitted=True))
            value = normalize(baseline(admitted=True), admission)
            self.assertIs(value['truce_inputs_v1']['short']['value'], True)
            self.assertIs(value['truce_inputs_v1']['long']['value'], False)
            self.assertIsNone(value['truce_inputs_v1']['border_raid_pair']['value'])
            self.assertFalse(value['material_complete'])
            self.assertIsNone(value['action_literal'])
            self.assertIsNone(value['truce_inputs_v1']['evaluated_days'])
            for key, field in [('native_revision', 4), ('war_id', 16777230),
                               ('defender_character_id', 29828), ('application_main_thread_id', True),
                               ('executor_invocations', 2), ('stock_double_sample_stable', False),
                               ('stock_parties_bound', False), ('material_complete', True)]:
                with self.subTest(key=key):
                    body = baseline(admitted=True)
                    body['h2743_stock_predicate_evidence_v1'][key] = field
                    with self.assertRaises(ValueError):
                        normalize(body, admission)
            body = baseline(admitted=True)
            del body['h2743_stock_predicate_evidence_v1']
            with self.assertRaises(ValueError):
                normalize(body, admission)
            body = baseline(admitted=True)
            body['truce_inputs_v1']['border_raid_pair']['unavailable_reason'] = 'invented'
            with self.assertRaises(ValueError):
                normalize(body, admission)
            body = baseline(admitted=True)
            body['casus_belli_database_index'] = 17.0
            with self.assertRaises(ValueError):
                normalize(body, admission)
            pins.write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError):
                verify_admitted_stock_predicate_pair(pair, pins_path=pins, native_source_checkout=checkout)
            bad_pair, bad_pins, bad_checkout = fixture_pair(Path(directory) / 'bad-provenance',
                invalid_source_identity=True)
            with self.assertRaises(ValueError):
                verify_admitted_stock_predicate_pair(bad_pair, pins_path=bad_pins,
                    native_source_checkout=bad_checkout)

    def test_production_transport_native_frame_and_replay_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            pair, pins, checkout = fixture_pair(Path(directory))
            _, admission = verify_admitted_stock_predicate_pair(pair, pins_path=pins,
                native_source_checkout=checkout)
            frame = {'map_ready': True, 'paused': True, 'date_raw': 53217264,
                'episode_run_id': 'native-29829-2bc2d599f7f9', 'played_character': {'character_id': 29829},
                'active_wars': [{'war_id': 16777231, 'player_side': 'defender',
                    'player_is_primary_war_leader': True, 'primary_opponent_character_id': 30097,
                    'targeted_title_ids': [2128]}], 'revision': 4, 'native_revision': 3,
                'snapshot_id': 'native:3', 'diagnostics': {'connection_generation': 1}}
            class Driver:
                def __init__(self):
                    self.frames = [deepcopy(frame), deepcopy(frame)]
                    self.body = baseline(admitted=True)
                def take_internal_semantic_snapshot(self):
                    return self.frames.pop(0)
                def _execute_primitive_step(self, step, **kwargs):
                    return {'step': BASELINE_STEP, 'accepted': True, 'status': 'baseline_only',
                        'query_sequence': 1, 'defender_de_jure_exit_terms_v1': deepcopy(self.body),
                        'backend_id': 'native-headless'}
            driver = Driver()
            bind_admitted_stock_predicates(driver, admission)
            self.assertEqual(query_h2743_exit_baseline(driver, expected_frame=frame)['queried_native_revision'], 3)
            driver.frames = [deepcopy(frame), deepcopy(frame)]
            with self.assertRaises(BridgeUnavailableError):
                query_h2743_exit_baseline(driver, expected_frame=frame)
            other = Driver()
            bind_admitted_stock_predicates(other, admission)
            other.frames[1]['revision'] = 5
            with self.assertRaises(BridgeUnavailableError):
                query_h2743_exit_baseline(other, expected_frame=frame)
            other = Driver()
            bind_admitted_stock_predicates(other, admission)
            other.frames[0]['active_wars'][0]['war_id'] = 16777231.0
            with self.assertRaises(BridgeUnavailableError):
                query_h2743_exit_baseline(other, expected_frame=frame)


if __name__ == '__main__':
    unittest.main()
