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


if __name__ == '__main__':
    unittest.main()
