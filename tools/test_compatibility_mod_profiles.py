"""Independent compatibility inputs through real prepare, host inventory and allocator.

Only the machine/process/keeper boundary is substituted by the existing public
allocator fixture. These tests never start CK3 and grant no live qualification.
"""
from __future__ import annotations

import copy
import argparse
import ast
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import FilePin, JsonObject, json_object, text_field, file_pin
import ck3_mod_acceptance_prepare as prepare
from ck3_mod_acceptance_cases import generic_product_adapter as generic


def authored_sources(root: Path) -> list[JsonObject]:
    values: list[JsonObject] = []
    for index, key in enumerate(('slots', 'dynastic')):
        directory = root / key
        (directory / 'common/on_action').mkdir(parents=True)
        (directory / 'descriptor.mod').write_text('name="' + key + '"\n', encoding='utf-8')
        # Genuine independent lifecycle input is legal for a formal_product role.
        (directory / 'common/on_action/start.txt').write_text('on_game_start_after_lobby = { }\n', encoding='utf-8')
        files = {path.relative_to(directory).as_posix(): prepare.pin(path)
                 for path in sorted(directory.rglob('*')) if path.is_file()}
        manifest = root / (key + '-release.json')
        manifest.write_text(json.dumps({'files': [
            {'path': relative, ('bytes' if index == 0 else 'size'): pin['bytes'], 'sha256': pin['sha256']}
            for relative, pin in files.items()]}), encoding='utf-8')
        values.append(json_object({'key': key, 'directory': str(directory.resolve()),
            'source_manifest': prepare.pin(manifest), 'files': files}))
    return values


class CompatibilityProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.values = authored_sources(self.root)

    def test_changed_production_contract_helpers_are_strictly_type_checked(self) -> None:
        """Compile the unchanged AST of the actual new typed contract boundary.

        The retained prepare engine has unrelated untyped legacy orchestration;
        this explicit scope does not claim that whole module is strict-clean.
        """
        source = Path(prepare.__file__).resolve()
        tree = ast.parse(source.read_text(encoding='utf-8-sig'))
        names = {'CompatibilityMod', '_compatibility_checked_pin', 'compatibility_mods',
            'compatibility_mod_source_pins', 'compatibility_mods_json', 'fixture_enabled_mods',
            '_prebuilt_relative_path', 'pin'}
        nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        imports = ('from __future__ import annotations\nfrom pathlib import Path\n'
            'from dataclasses import dataclass\nimport re, json, hashlib\n'
            'from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field\n')
        target = self.root / 'actual_compatibility_boundary.py'
        body: list[ast.stmt] = list(nodes)
        target.write_text(imports + ast.unparse(ast.Module(body=body, type_ignores=[])), encoding='utf-8')
        environment = dict(os.environ)
        environment['MYPYPATH'] = str(Path(__file__).resolve().parent)
        completed = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'mypy', '--strict',
            '--strict-equality', '--follow-imports=silent', '--no-incremental', '--cache-dir', os.devnull, str(target)],
            capture_output=True, text=True, encoding='utf-8', env=environment, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_absent_empty_and_null_are_distinct(self) -> None:
        self.assertEqual(prepare.compatibility_mods({}), ())
        self.assertEqual(prepare.compatibility_mods({'compatibility_mods': []}), ())
        invalid_values: tuple[object, ...] = (None, False, {}, '')
        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare.compatibility_mods({'compatibility_mods': value})

    def test_strict_roundtrip_and_malformed_sources(self) -> None:
        original = json.loads(json.dumps({'compatibility_mods': self.values}))
        mods = prepare.compatibility_mods(original)
        self.assertEqual(prepare.compatibility_mods_json(mods), self.values)
        pins = prepare.compatibility_mod_source_pins(original)
        self.assertEqual(len(pins), 6)
        mutations = ('field', 'duplicate', 'key', 'path', 'null_pin', 'bool_size', 'fraction', 'manifest')
        for mutation in mutations:
            changed = json_object(copy.deepcopy(original))
            values = changed['compatibility_mods']
            assert isinstance(values, list)
            row = json_object(values[0]); values[0] = row
            if mutation == 'field': row['alias'] = 'unsupported'
            elif mutation == 'duplicate': values.append(copy.deepcopy(row))
            elif mutation == 'key': row['key'] = '../escape'
            elif mutation == 'path': row['directory'] = str(self.root / 'slots/..')
            elif mutation == 'null_pin': row['source_manifest'] = None
            elif mutation in ('bool_size', 'fraction'):
                files = json_object(row['files']); row['files'] = files
                pin = json_object(files['descriptor.mod']); files['descriptor.mod'] = pin
                pin['bytes'] = True if mutation == 'bool_size' else 1.0
            else:
                files = json_object(row['files']); row['files'] = files
                files.pop('descriptor.mod')
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, FileNotFoundError)):
                prepare.compatibility_mods(changed)

    def test_actual_closure_and_original_manifest_drift_refuse(self) -> None:
        manifest = Path(str(json_object(self.values[0]['source_manifest'])['path']))
        original = manifest.read_bytes()
        manifest.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'changed'):
            prepare.compatibility_mods({'compatibility_mods': self.values})
        manifest.write_bytes(original)
        extra = self.root / 'slots/extra.txt'; extra.write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'closure differs'):
            prepare.compatibility_mods({'compatibility_mods': self.values})

    def test_restore_changes_only_explicit_independent_outer_paths(self) -> None:
        product = self.root / 'product'; product.mkdir()
        fixture = self.root / 'fixture'; fixture.mkdir()
        for directory in (product, fixture): (directory / 'descriptor.mod').write_bytes(b'name="authored"\n')
        plain: dict[str, FilePin] = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = self.root / ('plain' + str(index)); path.write_bytes(b'config\n'); plain[relative] = prepare.pin(path)
        contract: JsonObject = {'post_start': {}, 'required_startup': [], 'forbidden_startup': []}
        context = json_object({'state_dir': str(self.root / 'state'), 'output': str(self.root / 'output'), 'case_contract': contract})
        identity = {'game_version': 'authored-no-game', 'exe_sha256': '0' * 64}
        with patch.object(prepare, '_engine', return_value=(ModuleType('authored'), identity)):
            result = prepare.materialize_fixture_profile(context, fixture, product, plain,
                compatibility=prepare.compatibility_mods({'compatibility_mods': self.values}))
            profile = Path(text_field(result, 'profile'))
            snapshot = self.root / 'snapshot.json'
            rows = {relative: {'bytes': file_pin(pin)['bytes'], 'sha256': file_pin(pin)['sha256']}
                    for relative, pin in json_object(result['files']).items()}
            snapshot.write_text(json.dumps({'snapshot_kind': 'before-launch', 'snapshot_root': str(profile),
                'source_run_id': 'authored-not-live', 'files': rows}), encoding='utf-8')
            restored = prepare.restore_prepared_profile({**context, 'state_dir': str(self.root / 'retry'),
                'output': str(self.root / 'retry-output')}, snapshot)
        enabled = ['mod/compat_slots.mod', 'mod/compat_dynastic.mod', 'mod/product.mod', 'mod/fixture.mod']
        restored_profile = Path(text_field(restored, 'profile'))
        self.assertEqual(prepare.fixture_enabled_mods(restored_profile), enabled)
        receipt = json.loads(Path(file_pin(restored['preparation'])['path']).read_text(encoding='utf-8'))
        self.assertEqual(set(receipt['provenance']['changed_outer_paths']), set(enabled))
        self.assertEqual(receipt['provenance']['byte_exact_count'], len(rows) - 4)
        for relative in rows:
            before = (profile / relative).read_bytes(); after = (restored_profile / relative).read_bytes()
            if relative in enabled:
                self.assertNotEqual(before, after)
            else: self.assertEqual(before, after)


class PublicCompatibilityAllocationTests(unittest.TestCase):
    def test_producer_to_public_prepare_saved_host_and_actual_allocation_fingerprint(self) -> None:
        import ck3_mod_acceptance as entry
        import test_ck3_mod_acceptance_r06_scope as public_fixture
        from test_saved_campaign_profile_inventory_v2 import ProfileSpec, actual_host_preparer
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        fixture = public_fixture.PublicR06ScopeTests('runTest')
        # Give the real fixture a canonical parent before it derives any paths.
        with patch.object(public_fixture.options, 'scratch_root', Path(scratch.name).resolve()):
            fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = fixture.root
        producer_manifest = os.environ.get('XAR_COMPATIBILITY_PRODUCER_MANIFEST')
        values: object
        if producer_manifest:
            produced = json_object(json.loads(Path(producer_manifest).read_text(encoding='utf-8')))
            self.assertEqual(produced['schema'], 'ck3-mod-acceptance-compatibility-mods-v1')
            self.assertEqual(produced['machine_id'], fixture.machine)
            self.assertIs(produced['game_started'], False)
            values = json_object(produced['case_inputs'])['compatibility_mods']
        else: values = authored_sources(root)
        inputs = json_object({'compatibility_mods': values})
        mods = prepare.compatibility_mods(inputs)
        self.assertEqual([mod.key for mod in mods], ['slots', 'dynastic'])
        product = root / 'formal-product'; product.mkdir()
        (product / 'descriptor.mod').write_bytes(b'name="formal product"\n')
        source = root / 'emitted-fixture'; (source / 'events').mkdir(parents=True)
        (source / 'descriptor.mod').write_bytes(b'name="case fixture"\n')
        (source / 'events/assert.txt').write_bytes(b'namespace = authored\n')
        files = {path.relative_to(source).as_posix(): {'bytes': prepare.pin(path)['bytes'], 'sha256': prepare.pin(path)['sha256']}
                 for path in source.rglob('*') if path.is_file()}
        fixture_manifest = root / 'prebuilt-fixture.json'
        producer = Path(__file__).resolve().parents[1] / 'mod_religious_ritual_fusion/tools/src/main/java/org/xar/ck3/rrf/acceptance/FixtureEmitter.java'
        fixture.write(fixture_manifest, {'schema': 'ck3-mod-acceptance-prebuilt-fixture-v1', 'product': 'war-episode04-r10',
            'case_id': 'r10-common-preparation', 'machine_id': fixture.machine, 'observed_at_utc': '2026-10-25T00:00:00Z',
            'fixture_root': str(source), 'producer_source_pins': [prepare.pin(producer)], 'files': files,
            'receipt': {'required_markers': ['AUTHORED: TEST PASS'], 'required_product_markers_minimum': {}, 'fixture_contains_business_effects': True}})
        plain: JsonObject = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = root / ('config' + str(index)); path.write_bytes(b'plain\n'); plain[relative] = json_object(prepare.pin(path))
        save = root / 'source.ck3'; save.write_bytes(b'authored-not-game-save')
        fixture.seed = {**fixture.seed, 'save': str(save), 'bytes': save.stat().st_size, 'sha256': prepare.pin(save)['sha256']}
        contract = root / 'generic-contract.json'
        fixture.write(contract, {'product': 'war-episode04-r10', 'acceptance_scope': 'authored-core', 'startup_mode': 'saved_campaign',
            'fixture_source': {'kind': 'prebuilt_manifest'}, 'post_start': {'government_key': 'feudal_government', 'primary_title_tier_key': 'duchy', 'independent': True},
            'required_startup': ['AUTHORED: ARMED'], 'forbidden_startup': ['AUTHORED: TEST FAIL']})
        catalog = entry.read_json(fixture.products_path)
        catalog['products']['war-episode04-r10']['cases'][0]['adapter'] = {
            'module': 'tools.ck3_mod_acceptance_cases.generic_product_adapter', 'config': str(contract)}
        fixture.products_path = root / 'products.json'; fixture.write(fixture.products_path, catalog)
        fixture.inputs.update({'product_dir': str(product), 'plain_configuration': plain,
            'prebuilt_fixture_manifest': prepare.pin(fixture_manifest), 'compatibility_mods': values})
        fixture.inputs.pop('r06_refill_one_day')
        fixture.write(root / 'inputs.json', {'state_dir': str(fixture.state), 'saved_campaign': fixture.seed, 'case_inputs': fixture.inputs})
        identity = {'game_version': 'test-only', 'exe_sha256': prepare.pin(root / 'game/binaries/ck3.exe')['sha256']}
        with patch.object(entry.Selection, 'load_adapter', return_value=generic), \
             patch.object(prepare, '_engine', return_value=(ModuleType('authored'), identity)):
            result = entry.native_dispatch(argparse.Namespace(**vars(fixture.args('prepare'))))
            self.assertEqual(result['status'], 'CASE_PREPARED_NOT_ALLOCATED_NOT_RUN')
            original = fixture.prepared_path.read_bytes()
            fixture.allocate()
        prepared = entry.read_json(fixture.prepared_path)
        inventory_path = Path(prepared['startup']['saved_campaign']['product_inventory'])
        inventory = entry.read_json(inventory_path)
        enabled = ['mod/compat_slots.mod', 'mod/compat_dynastic.mod', 'mod/product.mod', 'mod/fixture.mod']
        self.assertEqual(inventory['enabled_mods'], enabled)
        self.assertEqual([row['source_role'] for row in inventory['projections']], ['formal_product'] * 3 + ['case_fixture'])
        profile = fixture.state / 'profile'
        args = argparse.Namespace(saved_campaign_save=save, saved_campaign_save_bytes=save.stat().st_size,
            saved_campaign_save_sha256=prepare.pin(save)['sha256'], saved_campaign_player_id=12,
            saved_campaign_date_raw=1000, saved_campaign_product_inventory=inventory_path)
        host = json_object(actual_host_preparer()(args, ProfileSpec(profile, fixture.state)))
        self.assertEqual(Path(str(host['copied_save_path'])).read_bytes(), save.read_bytes())
        self.assertEqual(host['profile_inventory_schema'], 'ck3-saved-campaign-profile-inventory-v2')
        frozen = entry.read_json(fixture.live / 'frozen-argv.json')
        references = prepare.compatibility_mod_source_pins({'compatibility_mods': values})
        for reference in references:
            actual = frozen['files'][reference['path']]
            self.assertEqual(actual['bytes'], reference['bytes']); self.assertEqual(actual['sha256'], reference['sha256'])
        copied = profile / 'mod-content/compat_dynastic/common/on_action/start.txt'
        self.assertEqual(frozen['files'][str(copied)]['sha256'], prepare.pin(copied)['sha256'])
        self.assertEqual(fixture.prepared_path.read_bytes(), original)
        # New selection validates originals before any live allocation or launch.
        changed = Path(references[0]['path']); original_source = changed.read_bytes()
        try:
            changed.write_bytes(original_source + b' ')
            with self.assertRaisesRegex(ValueError, 'changed'):
                entry.Selection(fixture.runtime_path, fixture.products_path, 'war-episode04-r10',
                    'r10-common-preparation', None, fixture.prepared_path)
        finally: changed.write_bytes(original_source)


if __name__ == '__main__':
    unittest.main()
