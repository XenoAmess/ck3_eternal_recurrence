"""Pre-generated fixture -> shared generic adapter -> actual profile closure.

The authored files exercise the filesystem consumer without CK3 or a Java
runtime. The product Maven suite separately exercises the Java producer.
"""
from __future__ import annotations

import copy
import argparse
import hashlib
import json
from pathlib import Path
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



def run_empire_wire(bundle_path: Path) -> None:
    """Authored offline input -> real Java child/decoder -> public three consumers."""
    import os
    from ck3_mod_acceptance_background_types import object_field, text_field, file_pin
    bundle = json_object(json.loads(bundle_path.read_bytes()))
    repo = Path(text_field(bundle, 'repository'))
    case = text_field(bundle, 'case')
    run_id = text_field(bundle, 'run_id')
    root = bundle_path.parent
    request = json_object(json.loads(Path(file_pin(bundle.get('prepare'))['path']).read_bytes()))
    save = file_pin(request.get('startupSave'))
    config = json_object(json.loads((repo / 'tools/ck3_mod_acceptance_cases' / ('dynastic_esotericism_' + case + '.json')).read_bytes()))
    plain: JsonObject = {}
    for index, name in enumerate(prepare.CONFIG_NAMES):
        path = root / ('plain-' + str(index))
        path.write_text('authored configuration', encoding='utf-8')
        plain[name] = json_object(file_identity(path))
    output = root / 'public-consumers'
    output.mkdir()
    context = json_object({
        'product': 'dynastic-esotericism', 'case': case, 'run_id': None, 'repo_root': str(repo),
        'runtime_manifest': bundle['runtime'], 'state_dir': text_field(bundle, 'state'), 'output': str(output),
        'case_contract': config, 'case_spec': {'budgets': {'command_timeout': 120}},
        'saved_campaign': json_object({'save': save['path'], 'bytes': save['bytes'], 'sha256': save['sha256'],
                           'player_id': 1, 'date_raw': 100}),
        'case_inputs': json_object({'product_dir': text_field(bundle, 'release'), 'plain_configuration': plain,
                        'prebuilt_fixture_manifest': bundle['fixture'], 'empire_restore_s1_request': bundle['prepare'],
                        'post_start': json_object({'government_key': 'feudal_government', 'primary_title_tier_key': 'empire', 'independent': True})})})
    missing = copy.deepcopy(context)
    absent = object_field(missing, 'case_inputs')
    absent.pop('empire_restore_s1_request')
    missing['case_inputs'] = absent
    with unittest.TestCase().assertRaises((ValueError, KeyError)):
        adapter.prepare_case(missing)
    assert not (Path(text_field(bundle, 'state')) / 'profile').exists()
    with patch.object(prepare, '_engine', return_value=(None, {'game_version': 'authored-no-game', 'exe_sha256': '0' * 64})):
        prepared = adapter.prepare_case(context)
    assert prepared['business_pass'] is False
    compiled = json_object(json.loads((Path(text_field(bundle, 'state')) / 'profile/mod-content/fixture/_case_contract.json').read_bytes()))
    marker_values = compiled.get('required_markers')
    if not isinstance(marker_values, list):
        raise ValueError('authored fixture markers absent')
    markers: list[str] = []
    for marker in marker_values:
        if not isinstance(marker, str):
            raise ValueError('marker type')
        markers.append(marker)
    # Set fixture-local environment before importing the real client module.
    with patch.dict(os.environ, {'XAR_AUTOPLAYER_STATE_DIR': text_field(bundle, 'state')}):
        from ck3_mod_acceptance_client import CaseClient

    class WireClient(CaseClient):
        def __init__(self) -> None:
            self.done = False
            self._process = {'pid': 88, 'create_time': 1.0}

        def snapshot(self, allow_actor_change: bool = False, require_event_free: bool = True) -> JsonObject:
            return object_field(bundle, 'after_snapshot' if self.done else 'before_snapshot')

        def root_checkpoint(self, name: str, request: JsonObject, reserve: int = 90,
                            *, read_only_appointment: bool = False) -> JsonObject:
            before = name.endswith('-pre-confirm-read-only')
            key = 'pre_confirm' if before else 'verify'
            if before and request.get('no_game_actions') is not True:
                raise ValueError('read-only pre-confirm must precede the original action')
            if not before and not isinstance(request.get('shared_restore_pre_confirm'), dict):
                raise ValueError('public phase did not carry real Java pre-confirm qualification')
            raw_requirements = request.get('required_assertions')
            if not isinstance(raw_requirements, list):
                raise ValueError('requirements type')
            assertions: JsonObject = {}
            for requirement in raw_requirements:
                if not isinstance(requirement, str):
                    raise ValueError('requirement type')
                assertions[requirement] = True
            if not before:
                self.done = True
            return json_object({'run_id': run_id, 'reviewer': '/root', 'assertions': assertions,
                                'evidence': [bundle[key]], 'empire_restore_request': bundle[key]})

        def checkpoint(self, name: str, value: JsonObject) -> object:
            path = output / (name + '.json')
            path.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')
            return file_identity(path)

        def log_bytes(self, name: str = 'debug.log', maximum: int = 64 * 1024 * 1024) -> bytes:
            return ('\n'.join(markers) + '\n').encode('utf-8')

    context['run_id'] = run_id  # Allocation follows successful public preparation.
    actual = adapter.run_case(context, WireClient())
    assert actual['gui_contract_qualified'] is True and actual['business_pass'] is False
    verified = adapter.verify_case(context)
    assert verified['gui_contract_qualified'] is True and verified['product_release_pass'] is False
    # A Root boolean with no actual request cannot be admitted.
    with unittest.TestCase().assertRaises((ValueError, KeyError)):
        adapter._er_response_request({'run_id': run_id, 'reviewer': '/root',
            'assertions': {'qualified': True}, 'evidence': [bundle['prepare']]}, context)
    print('actual shared Java producer -> public prepare/phase/verify; authored offline only; engine_semantics_verified=false')


class EmpireTransportGuards(unittest.TestCase):
    def test_missing_s1_and_bare_root_boolean_reject_before_process(self) -> None:
        with self.assertRaises((ValueError, KeyError)):
            adapter._er_inputs({'case_inputs': {}})
        with self.assertRaises((ValueError, KeyError)):
            adapter._er_response_request({'run_id': 'authored', 'reviewer': '/root',
                'qualified': True, 'evidence': []}, {'run_id': 'authored'})

    def test_actual_modified_transport_scope_is_strict_without_copying_business_logic(self) -> None:
        import ast
        import subprocess
        source = Path(adapter.__file__).read_text(encoding='utf-8')
        tree = ast.parse(source)
        names = {'EmpireVerifier', 'EmpireEvidenceClient', '_er_enabled', '_er_pin', '_er_verifier',
                 '_er_inputs', '_er_reduce', '_er_response_request', '_er_root_phase', 'root_phase',
                 '_ordinary_root_phase'}
        chosen: list[ast.stmt] = [node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual(len(chosen), len(names))
        prelude = (
            'from __future__ import annotations\nimport hashlib\nfrom pathlib import Path\n'
            'from dataclasses import dataclass\nfrom typing import Literal, Protocol\n'
            'from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field\n'
            'def read_json(path: Path) -> JsonObject: raise NotImplementedError\n'
            'def pin(path: Path) -> FilePin: raise NotImplementedError\n'
            'def write_once(path: Path, value: JsonObject) -> None: raise NotImplementedError\n')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'actual_empire_transport_scope.py'
            path.write_text(prelude + ast.unparse(ast.Module(body=chosen, type_ignores=[])), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'mypy', '--strict',
                '--strict-equality', '--follow-imports=silent', '--no-incremental',
                '--cache-dir=' + str(Path(tmp) / 'cache'), str(path)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout.decode('utf-8', 'replace'))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--empire-wire':
        run_empire_wire(Path(sys.argv[2]))
    else:
        unittest.main()
