"""Pre-generated fixture -> shared generic adapter -> actual profile closure.

The authored files exercise the filesystem consumer without CK3 or a Java
runtime. The product Maven suite separately exercises the Java producer.
"""
from __future__ import annotations

import copy
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch
import sys

from ck3_mod_acceptance_background_types import FilePin, JsonObject, JsonValue, json_object
import ck3_mod_acceptance_prepare as prepare
from ck3_mod_acceptance_cases import generic_product_adapter as adapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ck3_autonomous_player/src'))


def file_identity(path: Path) -> FilePin:
    raw = path.read_bytes()
    return FilePin(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def authored_snapshot_fixture(root: Path, version: int) -> JsonObject:
    """Authored filesystem contract only; actual Java business validation is tested separately."""
    if version not in (4, 5):
        raise ValueError('Authored snapshot version must be explicit')
    root = root.resolve()
    producer = root / 'repo/FixtureEmitter.java'
    producer.parent.mkdir(parents=True)
    producer.write_text('final class FixtureEmitter {}\n', encoding='utf-8')
    external: dict[str, FilePin] = {}
    for label in ('current-save', 'current', 'before', 'after'):
        path = root / (label + ('.ck3' if label == 'current-save' else '.json'))
        path.write_text('AUTHORED CONTRACT INPUT; NO GAME OR JAVA OBSERVATION\n', encoding='utf-8')
        external[label] = file_identity(path)
    fixture = root / 'snapshot'
    fixture.mkdir()
    (fixture / 'descriptor.mod').write_text('name="Authored passive snapshot"\n', encoding='utf-8')
    request = fixture / '_rrfa_request.json'
    request.write_text(json.dumps({'schemaVersion': version, 'kind': 'cold_reload', 'mode': 'rite',
        'actorHistoryId': '1128', 'setup': {
            'type': 'saved_snapshot' if version == 4 else 'completed_snapshot', 'actorId': '31254',
            'sourceSave': external['current-save'], 'sourceInspection': external['current'],
            'expectedCurrentPiety': '5400', 'creationHistory': {'before': '6000', 'after': '5500',
                'chargedCost': 500, 'beforeInspection': external['before'], 'afterInspection': external['after']}},
        'expectedSelection': {'coreTenets': ['tenet_esotericism', 'tenet_astrology', 'tenet_communal_identity']}}), encoding='utf-8')
    manifest = root / 'snapshot.fixture.json'
    files = {path.name: {'bytes': file_identity(path)['bytes'], 'sha256': file_identity(path)['sha256']}
             for path in sorted(fixture.iterdir())}
    manifest.write_text(json.dumps({'schema': 'ck3-mod-acceptance-prebuilt-fixture-v1',
        'product': 'religious-ritual-fusion', 'case_id': 'cold_reload', 'machine_id': 'authored-machine',
        'observed_at_utc': '2026-10-29T00:00:00Z', 'fixture_root': str(fixture),
        'producer_source_pins': [file_identity(producer)], 'files': files,
        'receipt': {'required_markers': ['RRFAT: TEST PASS faith_persisted_readback'],
            'required_product_markers_minimum': {}, 'fixture_contains_business_effects': False}}), encoding='utf-8')
    sidecar = root / 'snapshot.inputs.json'
    sidecar.write_text(json.dumps({'schema': 'rrf-prebuilt-fixture-inputs-v1', 'manifest': file_identity(manifest),
        'request': file_identity(request), 'input_pins': list(external.values())}), encoding='utf-8')
    return json_object({'prebuilt_fixture_manifest': file_identity(manifest),
                        'prebuilt_fixture_inputs': file_identity(sidecar)})


class PrebuiltFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.producer = self.repo / 'FixtureEmitter.java'
        self.producer.write_text('final class FixtureEmitter {}\n', encoding='utf-8')
        self.fixture = self.root / 'generated'
        (self.fixture / 'events').mkdir(parents=True)
        (self.fixture / 'descriptor.mod').write_text('name="Authored test fixture"\n', encoding='utf-8')
        (self.fixture / 'events/readback.txt').write_text('namespace = authored\n', encoding='utf-8-sig')
        self.shared = self.root / 'shared.json'
        self.shared.write_text(json.dumps({'machine_id': 'authored-machine'}), encoding='utf-8')
        files: JsonObject = {}
        for path in self.fixture.rglob('*'):
            if path.is_file():
                row = file_identity(path)
                files[path.relative_to(self.fixture).as_posix()] = {'bytes': row['bytes'], 'sha256': row['sha256']}
        self.manifest: JsonObject = json_object({
            'schema': 'ck3-mod-acceptance-prebuilt-fixture-v1', 'product': 'authored-product',
            'case_id': 'core', 'machine_id': 'authored-machine', 'observed_at_utc': '2026-10-24T00:00:00Z',
            'fixture_root': str(self.fixture.resolve()), 'producer_source_pins': [file_identity(self.producer)],
            'files': files, 'receipt': {'required_markers': ['AUTHORED: TEST PASS readback'],
                'required_product_markers_minimum': {}, 'fixture_contains_business_effects': True}})
        self.manifest_path = self.root / 'fixture.json'
        self.context: JsonObject = json_object({'product': 'authored-product', 'case': 'core',
            'repo_root': str(self.repo), 'runtime_manifest': file_identity(self.shared)})

    def frozen_manifest(self) -> FilePin:
        self.manifest_path.write_text(json.dumps(self.manifest, allow_nan=False), encoding='utf-8')
        return file_identity(self.manifest_path)

    def materialize(self) -> tuple[Path, prepare.PrebuiltFixtureReceipt, prepare.PrebuiltFixtureMaterialization]:
        return prepare.materialize_prebuilt_fixture(self.context, self.frozen_manifest(), self.root / 'copied')

    def test_snapshot_contract_helpers_are_strictly_type_checked_from_actual_ast(self) -> None:
        source = Path(prepare.__file__).resolve()
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        names = {'PrebuiltFixtureReceipt', 'PrebuiltFixtureMaterialization', 'PrebuiltFixtureInputs',
            '_prebuilt_checked_pin', 'prebuilt_fixture_inputs', 'prebuilt_fixture_source_pins',
            '_prebuilt_relative_path', 'pin'}
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        imports = ('from __future__ import annotations\nfrom pathlib import Path\nimport json, hashlib\n'
            'from typing import Literal, NotRequired, TypedDict\n'
            'from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field\n')
        target = self.root / 'actual_snapshot_contract_boundary.py'
        body: list[ast.stmt] = list(nodes)
        target.write_text(imports + ast.unparse(ast.Module(body=body, type_ignores=[])), encoding='utf-8')
        environment = dict(os.environ)
        environment['MYPYPATH'] = str(Path(__file__).resolve().parent)
        child = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'mypy', '--strict',
            '--strict-equality', '--follow-imports=silent', '--no-incremental', '--cache-dir', os.devnull, str(target)],
            capture_output=True, text=True, encoding='utf-8', env=environment, timeout=60)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)

    def test_snapshot_versions_keep_the_existing_sidecar_and_json_roundtrip(self) -> None:
        for version in (4, 5):
            with self.subTest(version=version):
                root = self.root / ('snapshot-v' + str(version))
                inputs = authored_snapshot_fixture(root, version)
                binding = prepare.prebuilt_fixture_inputs(inputs)
                self.assertIsNotNone(binding)
                if binding is None:
                    self.fail('Explicit snapshot binding required')
                self.assertEqual(prepare.prebuilt_fixture_inputs(json.loads(json.dumps(inputs))), binding)
                self.assertEqual(len(prepare.prebuilt_fixture_source_pins(inputs)), 7)
                context = json_object({**self.context, 'product': 'religious-ritual-fusion', 'case': 'cold_reload',
                    'repo_root': str(root / 'repo'), 'case_inputs': inputs})
                destination, receipt, materialized = prepare.materialize_prebuilt_fixture(
                    context, inputs['prebuilt_fixture_manifest'], root / 'copied')
                self.assertFalse(receipt['fixture_contains_business_effects'])
                self.assertEqual(materialized['input_receipt'], binding['receipt'])
                self.assertEqual(materialized['input_pins'], binding['input_pins'])
                frozen = json_object(json.loads((destination / '_rrfa_request.json').read_bytes()))
                self.assertEqual(frozen['schemaVersion'], version)
                self.assertEqual(json_object(frozen['setup'])['type'],
                                 'saved_snapshot' if version == 4 else 'completed_snapshot')

    def test_snapshot_schema_and_setup_cannot_cross_versions(self) -> None:
        changes: tuple[tuple[JsonValue, JsonValue], ...] = (
            (4, 'completed_snapshot'), (5, 'saved_snapshot'), (5, 'saved'),
            (True, 'completed_snapshot'), (5.0, 'completed_snapshot'), ('5', 'completed_snapshot'),
            (None, 'completed_snapshot'))
        for index, (version, setup_type) in enumerate(changes):
            with self.subTest(version=version, setup_type=setup_type):
                root = self.root / ('crossed-' + str(index))
                inputs = authored_snapshot_fixture(root, 5)
                request_path = root / 'snapshot/_rrfa_request.json'
                request = json_object(json.loads(request_path.read_bytes()))
                request['schemaVersion'] = version
                setup = json_object(request['setup']); setup['type'] = setup_type; request['setup'] = setup
                request_path.write_text(json.dumps(request), encoding='utf-8')
                manifest_path = root / 'snapshot.fixture.json'
                manifest = json_object(json.loads(manifest_path.read_bytes()))
                files = json_object(manifest['files'])
                identity = file_identity(request_path)
                files['_rrfa_request.json'] = {'bytes': identity['bytes'], 'sha256': identity['sha256']}
                manifest['files'] = files
                manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
                inputs['prebuilt_fixture_manifest'] = json_object(file_identity(manifest_path))
                sidecar_path = root / 'snapshot.inputs.json'
                sidecar = json_object(json.loads(sidecar_path.read_bytes()))
                sidecar['manifest'] = json_object(file_identity(manifest_path))
                sidecar['request'] = json_object(file_identity(request_path))
                sidecar_path.write_text(json.dumps(sidecar), encoding='utf-8')
                inputs['prebuilt_fixture_inputs'] = json_object(file_identity(sidecar_path))
                with self.assertRaisesRegex(ValueError, 'Version [45] requires|version must be an exact supported integer'):
                    prepare.prebuilt_fixture_inputs(inputs)

    def test_real_generic_prepare_consumes_roundtripped_manifest(self) -> None:
        product = self.root / 'product'
        product.mkdir()
        (product / 'descriptor.mod').write_text('name="Authored product"\n', encoding='utf-8')
        plain: JsonObject = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = self.root / ('plain-' + str(index))
            path.write_text('authored configuration\n', encoding='utf-8')
            plain[relative] = json_object(file_identity(path))
        contract = json_object({
                'product': 'authored-product', 'acceptance_scope': 'authored-core',
                'fixture_source': {'kind': 'prebuilt_manifest'},
                'post_start': {'government_key': 'feudal_government', 'primary_title_tier_key': 'duchy', 'independent': True},
                'required_startup': ['AUTHORED: ARMED'], 'forbidden_startup': ['AUTHORED: TEST FAIL']})
        inputs = json_object({'product_dir': str(product), 'plain_configuration': plain,
                              'prebuilt_fixture_manifest': self.frozen_manifest()})
        context = json_object({**self.context, 'state_dir': str(self.root / 'state'),
            'output': str(self.root / 'prepare'), 'case_contract': contract, 'case_inputs': inputs})
        identity = {'game_version': 'authored-only-no-game', 'exe_sha256': '0' * 64}
        with patch.object(prepare, '_engine', return_value=(ModuleType('authored_engine'), identity)):
            result = adapter.prepare_case(context)
        profile = self.root / 'state/profile'
        self.assertEqual((profile / 'mod-content/fixture/events/readback.txt').read_bytes(),
                         (self.fixture / 'events/readback.txt').read_bytes())
        compiled = json.loads((profile / 'mod-content/fixture/_case_contract.json').read_text(encoding='utf-8'))
        self.assertEqual(compiled['required_markers'], ['AUTHORED: TEST PASS readback'])
        self.assertEqual(compiled['emitter']['manifest'], file_identity(self.manifest_path))
        self.assertEqual(json.loads((profile / 'dlc_load.json').read_text())['enabled_mods'],
                         ['mod/product.mod', 'mod/fixture.mod'])
        self.assertFalse(result['business_pass'])
        self.assertEqual(result['runtime_status'], 'NOT_RUN')

    def test_content_change_and_extra_or_missing_files_rejected(self) -> None:
        cases = ('content', 'extra', 'missing')
        for kind in cases:
            with self.subTest(kind=kind):
                path = self.fixture / 'events/readback.txt'
                original = path.read_bytes()
                extra = self.fixture / 'extra.txt'
                if kind == 'content':
                    path.write_bytes(original + b'changed')
                elif kind == 'extra':
                    extra.write_bytes(b'extra')
                else:
                    path.unlink()
                with self.assertRaises(ValueError):
                    self.materialize()
                path.write_bytes(original)
                if extra.exists():
                    extra.unlink()
                self.assertFalse((self.root / 'copied').exists())

    def test_saved_fixture_reaches_actual_v2_inventory_and_canonical_host_copy(self) -> None:
        self.test_real_generic_prepare_consumes_roundtripped_manifest()
        from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer
        profile_path = self.root / 'state/profile'
        files = json.loads((self.root / 'prepare/profile-preparation.json').read_bytes())['files']
        source = self.root / 'authored-preflight-only.ck3'
        source.write_bytes(b'AUTHORED PREFLIGHT BYTES; NEVER LOADED IN CK3\n')
        identity = file_identity(source)
        context = json_object({'state_dir': str(self.root / 'state'), 'output': str(self.root / 'prepare'),
            'saved_campaign': {'save': identity['path'], 'bytes': identity['bytes'], 'sha256': identity['sha256'],
                               'player_id': 31254, 'date_raw': 53144328}})
        startup = adapter._saved_fixture_startup(context, json_object({'profile': str(profile_path), 'files': files}))
        saved = json_object(startup['saved_campaign'])
        args = argparse.Namespace(saved_campaign_save=source, saved_campaign_save_bytes=identity['bytes'],
            saved_campaign_save_sha256=identity['sha256'], saved_campaign_player_id=31254,
            saved_campaign_date_raw=53144328, saved_campaign_product_inventory=Path(str(saved['product_inventory'])))
        result = json_object(actual_host_preparer()(args, ProfileSpec(profile_path, self.root / 'state')))
        self.assertEqual(Path(str(result['copied_save_path'])).read_bytes(), source.read_bytes())
        self.assertEqual(result['profile_inventory_schema'], 'ck3-saved-campaign-profile-inventory-v2')
        wrong = json_object(context['saved_campaign'])
        wrong['date_raw'] = True
        context['saved_campaign'] = wrong
        with self.assertRaises(ValueError):
            adapter._saved_fixture_startup(context, json_object({'profile': str(profile_path), 'files': files}))

    def test_saved_campaign_prepare_keeps_engine_cache_out_of_public_json(self) -> None:
        # Exercise the actual saved branch after real _engine has inserted its
        # private (module, identity) cache. The older direct-helper test never
        # executed this production order and therefore missed the R9 failure.
        self.test_real_generic_prepare_consumes_roundtripped_manifest()
        from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer
        engine = self.repo / 'tools/fixture_engine_prepare.py'
        engine.parent.mkdir()
        engine.write_text("def engine_identity(repo, **kwargs):\n"
                          "    return {'game_version': 'authored-only-no-game', 'exe_sha256': '" + '0' * 64 + "'}\n",
                          encoding='utf-8')
        contract = json_object(json.loads((self.root / 'state/profile/mod-content/fixture/_case_contract.json').read_bytes())['config'])
        contract['startup_mode'] = 'saved_campaign'
        source = self.root / 'saved-branch-authored.ck3'
        source.write_bytes(b'AUTHORED PREPARE INPUT; NEVER LOADED IN CK3\n')
        identity = file_identity(source)
        saved = json_object({'save': identity['path'], 'bytes': identity['bytes'], 'sha256': identity['sha256'],
                             'player_id': 31254, 'date_raw': 53144352})
        context = json_object({**self.context, 'state_dir': str(self.root / 'cold-state'),
            'output': str(self.root / 'cold-prepare'), 'case_contract': contract, 'saved_campaign': saved,
            'shared_source_root': str(self.repo), 'game_dir': str(self.root / 'no-game'),
            'shared_game': {'version': 'authored-only-no-game', 'exe_sha256': '0' * 64},
            'case_inputs': json_object({'product_dir': str(self.root / 'product'),
                'plain_configuration': {relative: file_identity(self.root / ('plain-' + str(index)))
                                        for index, relative in enumerate(prepare.CONFIG_NAMES)},
                'prebuilt_fixture_manifest': self.frozen_manifest()})})
        with patch.object(prepare, '_engine', wraps=prepare._engine) as actual_engine:
            result = adapter.prepare_case(context)
        cached = actual_engine.call_args.args[0]['_selected_engine']
        self.assertIs(type(cached), tuple)
        self.assertIsInstance(cached[0], ModuleType)
        with self.assertRaisesRegex(ValueError, 'finite JSON type domain'):
            json_object(actual_engine.call_args.args[0])
        # Only public inputs reach the persisted startup, which remains strict
        # JSON and is consumed by the actual canonical saved-profile preparer.
        result = json_object(json.loads(json.dumps(result, allow_nan=False)))
        startup = json_object(result['startup'])
        self.assertEqual(startup['mode'], 'saved_campaign')
        seed = json_object(startup['saved_campaign'])
        self.assertEqual({key: value for key, value in seed.items() if key != 'product_inventory'}, saved)
        inventory = json.loads(Path(str(seed['product_inventory'])).read_bytes())
        self.assertEqual({row['descriptor']: row['source_role'] for row in inventory['projections']},
                         {'mod/product.mod': 'formal_product', 'mod/fixture.mod': 'case_fixture'})
        args = argparse.Namespace(saved_campaign_save=source, saved_campaign_save_bytes=identity['bytes'],
            saved_campaign_save_sha256=identity['sha256'], saved_campaign_player_id=31254,
            saved_campaign_date_raw=53144352, saved_campaign_product_inventory=Path(str(seed['product_inventory'])))
        copied = json_object(actual_host_preparer()(args, ProfileSpec(self.root / 'cold-state/profile', self.root / 'cold-state')))
        self.assertEqual(Path(str(copied['copied_save_path'])).read_bytes(), source.read_bytes())
        self.assertNotIn('_selected_engine', json.dumps(result))

    def test_actual_pre_product_profile_has_only_fixture_and_no_formal_product(self) -> None:
        self.test_real_generic_prepare_consumes_roundtripped_manifest()
        compiled = json.loads((self.root / 'state/profile/mod-content/fixture/_case_contract.json').read_bytes())
        contract = json_object(compiled['config'])
        contract['product_loading'] = 'absent'
        plain = json_object({relative: file_identity(self.root / ('plain-' + str(index)))
                             for index, relative in enumerate(prepare.CONFIG_NAMES)})
        context = json_object({**self.context, 'state_dir': str(self.root / 'absent-state'),
            'output': str(self.root / 'absent-prepare'), 'case_contract': contract,
            'case_inputs': {'product_dir': None, 'plain_configuration': plain,
                            'prebuilt_fixture_manifest': self.frozen_manifest()}})
        with patch.object(prepare, '_engine', return_value=(ModuleType('authored_engine'),
                {'game_version': 'authored-only-no-game', 'exe_sha256': '0' * 64})):
            result = adapter.prepare_case(context)
        profile = self.root / 'absent-state/profile'
        self.assertEqual(json.loads((profile / 'dlc_load.json').read_bytes())['enabled_mods'], ['mod/fixture.mod'])
        self.assertFalse((profile / 'mod-content/product').exists())
        self.assertFalse(result['business_pass'])

    def test_pre_product_seed_prepare_run_and_verify_preserves_absent_product_pins(self) -> None:
        """Offline transport exercises the exact completion path that failed in R43."""
        contract_path = Path(prepare.__file__).parent / 'ck3_mod_acceptance_cases/dynastic_esotericism_pre_product_seed.json'
        original = json_object(json.loads(contract_path.read_bytes()))
        original['product'] = self.context['product']
        self.context['case'] = 'pre_product_seed'
        self.manifest['case_id'] = 'pre_product_seed'
        self.manifest['receipt'] = {'required_markers': ['DESAF: TEST PASS legacy_seed_ready'],
            'required_product_markers_minimum': {}, 'fixture_contains_business_effects': False}
        plain: JsonObject = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = self.root / ('seed-plain-' + str(index))
            path.write_text('authored configuration\n', encoding='utf-8')
            plain[relative] = json_object(file_identity(path))
        product = self.root / 'seed-product'
        product.mkdir()
        (product / 'descriptor.mod').write_text('name="Authored product"\n', encoding='utf-8')

        from ck3_mod_acceptance_client import CaseClient

        class CompletionClient(CaseClient):
            def __init__(self, output: Path) -> None:
                self.output = output
                self.requests: list[JsonObject] = []

            def snapshot(self, allow_actor_change: bool = False,
                         require_event_free: bool = True) -> JsonObject:
                return {'date_raw': 53144328, 'paused': True, 'active_event': None,
                        'pending_character_interaction': None}

            def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90,
                                *, read_only_appointment: bool = False) -> JsonObject:
                self.requests.append(request)
                raw = request['required_assertions']
                if not isinstance(raw, list) or not all(isinstance(key, str) for key in raw):
                    raise ValueError('Original typed Root assertions required')
                evidence = self.output / 'authored-root-evidence.txt'
                evidence.write_text('Offline Root transport only; no CK3 or Save qualification.\n', encoding='utf-8')
                return json_object({'run_id': 'authored-seed-run', 'reviewer': '/root',
                    'assertions': {str(key): True for key in raw}, 'evidence': [file_identity(evidence)]})

            def checkpoint(self, name: str, value: JsonObject) -> Path:
                path = self.output / (name + '.json')
                path.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
                return path

            def log_bytes(self, name: str = 'debug.log', maximum: int = 64 * 1024 * 1024) -> bytes:
                return b'DESAF: TEST PASS legacy_seed_ready\n'

        for loading in ('absent', 'present'):
            with self.subTest(product_loading=loading):
                contract = copy.deepcopy(original)
                contract['product_loading'] = loading
                state = self.root / ('seed-state-' + loading)
                context = json_object({**self.context, 'state_dir': str(state),
                    'output': str(self.root / ('seed-prepare-' + loading)), 'case_contract': contract,
                    'case_spec': {'budgets': {'command_timeout': 300}},
                    'case_inputs': {'product_dir': None if loading == 'absent' else str(product),
                        'plain_configuration': plain, 'prebuilt_fixture_manifest': self.frozen_manifest()}})
                with patch.object(prepare, '_engine', return_value=(ModuleType('authored_engine'),
                        {'game_version': 'authored-only-no-game', 'exe_sha256': '0' * 64})):
                    prepared = adapter.prepare_case(context)
                self.assertIs(prepared['business_pass'], False)
                output = self.root / ('seed-run-' + loading)
                output.mkdir()
                context.update(run_id='authored-seed-run', output=str(output))
                client = CompletionClient(output)
                actual = adapter.run_case(context, client)
                self.assertEqual(len(client.requests), 1)
                self.assertIs(actual['case_contract_qualified'], True)
                self.assertIs(actual['gui_contract_qualified'], True)
                frames = actual['actual_native_frames']
                if not isinstance(frames, list):
                    self.fail('Actual fixture completion frame list required')
                self.assertEqual(len(frames), 2)
                self.assertEqual(json_object(frames[0])['day'], 0)
                persisted = json.loads((output / 'generic-product-case-result.json').read_bytes())
                self.assertEqual(persisted, json.loads(json.dumps(actual, allow_nan=False)))
                for key, relative in (('product_outer', 'mod/product.mod'),
                                      ('product_inner', 'mod-content/product/descriptor.mod')):
                    self.assertIn(key, persisted)
                    if loading == 'absent':
                        self.assertIsNone(persisted[key])
                    else:
                        self.assertEqual(persisted[key], file_identity(state / 'profile' / relative))
                verified = adapter.verify_case(context)
                self.assertEqual(verified['product_outer'], persisted['product_outer'])
                self.assertEqual(verified['product_inner'], persisted['product_inner'])
                self.assertIs(verified['business_pass'], False)
                self.assertIs(verified['product_release_pass'], False)

    def test_wrong_product_machine_and_fields_rejected(self) -> None:
        baseline = copy.deepcopy(self.manifest)
        variants: list[tuple[str, JsonValue]] = [('product', 'other'), ('case_id', 'other'), ('machine_id', 'other'),
                                                ('unknown', True), ('observed_at_utc', '2026-10-24T00:00:00')]
        for key, value in variants:
            with self.subTest(key=key):
                self.manifest = copy.deepcopy(baseline)
                self.manifest[key] = value
                with self.assertRaises(ValueError):
                    self.materialize()
                self.assertFalse((self.root / 'copied').exists())
        self.manifest = baseline

    def test_wrong_byte_type_marker_type_and_missing_field_rejected(self) -> None:
        baseline = copy.deepcopy(self.manifest)
        for value in (True, 1.0, None):
            with self.subTest(bytes=value):
                self.manifest = copy.deepcopy(baseline)
                files = json_object(self.manifest['files'])
                file = json_object(files['descriptor.mod'])
                file['bytes'] = value
                files['descriptor.mod'] = file
                self.manifest['files'] = files
                with self.assertRaises(ValueError):
                    self.materialize()
        self.manifest = copy.deepcopy(baseline)
        del self.manifest['receipt']
        with self.assertRaises(ValueError):
            self.materialize()
        self.manifest = copy.deepcopy(baseline)
        self.manifest['receipt'] = {'required_markers': [False], 'required_product_markers_minimum': {},
                                   'fixture_contains_business_effects': True}
        with self.assertRaises(ValueError):
            self.materialize()

    def test_traversal_and_unbound_manifest_rejected(self) -> None:
        baseline = copy.deepcopy(self.manifest)
        files = json_object(self.manifest['files'])
        files['../escape.txt'] = files['descriptor.mod']
        self.manifest['files'] = files
        with self.assertRaises(ValueError):
            self.materialize()
        self.manifest = baseline
        pin = self.frozen_manifest()
        self.manifest_path.write_bytes(self.manifest_path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            prepare.materialize_prebuilt_fixture(self.context, pin, self.root / 'copied')


if __name__ == '__main__':
    unittest.main()
