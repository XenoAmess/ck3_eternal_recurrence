"""Actual Java producer -> public prepare -> CLI saved-AST consumer; authored save/decoder, no game."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import JsonObject, json_object
import ck3_mod_acceptance_prepare as prepare
from ck3_mod_acceptance_cases import generic_product_adapter as adapter
from test_prebuilt_fixture_prepare import file_identity


def authored_reference(name: str, identity: str) -> str:
    return '{flag="' + name + '" data={type=rite identity=' + identity + '}}'


def authored_rite(identity: str, cores: list[str], variables: str = '') -> str:
    status = ''.join('{tenet="' + key + '" status=core}' for key in cores)
    direct = ''.join('tenet="' + key + '" ' for key in cores)
    return identity + '={faith=13 data={tenets={' + status + '} ' + direct + '} ' + variables + '}'


def authored_save(cores: list[str]) -> str:
    """Explicitly invented game bytes exercise the complete parser, never live business evidence."""
    source_a = ['tenet_esotericism', 'tenet_legalism', 'tenet_astrology']
    source_b = ['tenet_esotericism', 'tenet_legalism', 'tenet_communal_identity']
    actor = 'living={31254={rite=153 alive_data={variables={data={' + ''.join(
        authored_reference(name, identity) for name, identity in (
            ('rrfa_source_a', '150'), ('rrfa_expected_b', '151'), ('rrf_last_result_rite', '153'))) + '}}}}}'
    items = ''.join('item={type=tenet key="' + key + '"}' for key in cores)
    variables = 'variables={data={' + authored_reference('rrf_origin_a', '150') + authored_reference(
        'rrf_origin_b', '151') + '} list={{name="rrf_origin_core_tenets" ' + items + '}}}'
    return ('meta_data={version="1.20.0.4"} date=1066.9.16 ' + actor
        + ' religion={religions={8={key="christianity"}}} faiths={database={13={religion=8 main_rite=0}}}'
        + ' rites={database={' + authored_rite('150', source_a) + authored_rite('151', source_b)
        + authored_rite('153', cores, variables) + '}}')


class ReligiousRitualFusionProducerPrepareTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.shared = self.root / 'shared.json'
        self.shared.write_text(json.dumps({'machine_id': 'authored-machine'}), encoding='utf-8')
        # SaveInspector launches the pinned real interpreter as an actual child with its unchanged
        # production argv. Only this temporary decoder's bytes and returned save text are authored.
        # Child cwd is the temporary root; nothing is written to the repository.
        (self.root / 'melt').write_text(
            'import pathlib, sys\n'
            'if sys.argv[2:] != ["-c", "--format", "ck3", "--unknown-key", "error"]: raise SystemExit(41)\n'
            'pathlib.Path("authored-decoder-invoked").write_text("AUTHORED_DECODER_ONLY", encoding="utf-8")\n'
            'sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())\n', encoding='utf-8')

    def inspect_cli(self, java: str, cli: Path, request: JsonObject, label: str) -> subprocess.CompletedProcess[bytes]:
        inputs = self.root / (label + '.request.json')
        inputs.write_text(json.dumps(request, allow_nan=False), encoding='utf-8')
        return subprocess.run([java, '-jar', str(cli), 'inspect-save', '--inputs', str(inputs),
            '--output', str(self.root / (label + '.report.json'))], cwd=self.root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=150, check=False)

    def test_real_java_three_and_four_core_producer_reaches_generic_prepare_with_manifest_frozen_metadata(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        default_jar = repository / 'mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar'
        cli = Path(os.environ.get('RRF_FIXTURE_CLI_JAR', str(default_jar))).resolve()
        self.assertTrue(cli.is_file(), 'Full Maven verify must produce the actual CLI before this integration test; no skip is a pass')
        java = shutil.which('java')
        self.assertIsNotNone(java, 'Actual Java runtime required for producer to public prepare closure')
        if java is None:
            raise AssertionError('Actual Java runtime unavailable')
        product = self.root / 'java-product'; product.mkdir()
        (product / 'descriptor.mod').write_text('name="Authored profile-only product"\n', encoding='utf-8')
        plain: JsonObject = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = self.root / ('java-plain-' + str(index)); path.write_text('authored configuration\n', encoding='utf-8')
            plain[relative] = json_object(file_identity(path))
        contract = json_object(json.loads((repository / 'tools/ck3_mod_acceptance_cases/religious_ritual_fusion_core.json').read_bytes()))
        phases = contract.get('gui_phases')
        if not isinstance(phases, list) or not phases:
            raise AssertionError('Actual core GUI phases required')
        requirements = json_object(phases[0]).get('requirements')
        self.assertIsInstance(requirements, list)
        if not isinstance(requirements, list):
            raise AssertionError('Actual core requirements required')
        self.assertFalse(any('exactly_three' in str(value) for value in requirements))
        three_prepared_pin: JsonObject | None = None
        for count, recipe in ((3, 'core-rite'), (4, 'core-rite-four')):
            with self.subTest(recipe=recipe):
                fixture = self.root / ('java-' + recipe)
                inputs_path = repository / ('mod_religious_ritual_fusion/tools/src/main/resources/acceptance/requests/' + recipe + '.json')
                child = subprocess.run([java, '-jar', str(cli), 'fixture', '--repo-root', str(repository),
                    '--output', str(fixture), '--machine-id', 'authored-machine', '--inputs', str(inputs_path)],
                    cwd=repository, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
                self.assertEqual(child.returncode, 0, child.stderr.decode('utf-8', errors='replace'))
                self.assertLessEqual(len(child.stdout) + len(child.stderr), 1024 * 1024)
                manifest = Path(str(fixture) + '.fixture.json')
                emitted = json_object(json.loads(manifest.read_bytes()))
                files = json_object(emitted['files']); metadata = fixture / '_rrfa_request.json'
                self.assertEqual(files['_rrfa_request.json'], {key: value for key, value in file_identity(metadata).items() if key != 'path'})
                metadata_value = json_object(json.loads(metadata.read_bytes()))
                expected = json_object(metadata_value['expectedSelection'])['coreTenets']
                self.assertIsInstance(expected, list)
                if not isinstance(expected, list):
                    raise AssertionError('Typed expected core array required')
                cores: list[str] = []
                for key in expected:
                    if not isinstance(key, str):
                        raise AssertionError('Canonical textual expected core key required')
                    cores.append(key)
                self.assertEqual(len(expected), count)
                context = json_object({'product': 'religious-ritual-fusion', 'case': 'core',
                    'repo_root': str(repository), 'runtime_manifest': file_identity(self.shared),
                    'state_dir': str(self.root / ('java-state-' + recipe)), 'output': str(self.root / ('java-prepare-' + recipe)),
                    'case_contract': contract, 'case_inputs': {'product_dir': str(product),
                        'plain_configuration': plain, 'prebuilt_fixture_manifest': file_identity(manifest)}})
                with patch.object(prepare, '_engine', return_value=(ModuleType('authored_engine'),
                        {'game_version': 'authored-only-no-game', 'exe_sha256': '0' * 64})):
                    result = adapter.prepare_case(context)
                profile = Path(str(context['state_dir'])) / 'profile'
                self.assertEqual((profile / 'mod-content/fixture/_rrfa_request.json').read_bytes(), metadata.read_bytes())
                prepared_path = Path(str(context['output'])) / 'profile-preparation.json'
                prepared = json_object(json.loads(prepared_path.read_bytes()))
                self.assertIn('mod-content/fixture/_rrfa_request.json', json_object(prepared['files']))
                compiled = json_object(json.loads((profile / 'mod-content/fixture/_case_contract.json').read_bytes()))
                self.assertEqual(json_object(compiled['emitter'])['manifest'], file_identity(manifest))
                self.assertFalse(result['business_pass'])
                # Feed the actual Java emitter manifest AND the actual public prepare inventory
                # straight into the unchanged CLI decoder/complete saved AST/comparator path.
                # The game bytes and decoder are explicitly authored and earn no live/edit/fee/reload credit.
                save = self.root / (recipe + '-AUTHORED.ck3')
                save.write_text(authored_save(cores), encoding='utf-8')
                request = json_object({'schemaVersion': 2, 'machineId': 'authored-machine',
                    'repository': str(repository), 'save': file_identity(save),
                    'decoder': file_identity(Path(sys.executable)),
                    'layout': {'actorTable': ['living'], 'riteTable': ['rites', 'database'],
                        'faithTable': ['faiths', 'database'], 'religionTable': ['religion', 'religions']},
                    'selection': {'actorId': '31254', 'riteIds': ['150', '151', '153'],
                        'faithIds': ['13'], 'religionIds': ['8']},
                    'expectation': {'type': 'fusion_selection', 'fixtureManifest': file_identity(manifest),
                        'preparedProfileInventory': file_identity(prepared_path), 'resultRiteId': '153'}})
                checked = self.inspect_cli(java, cli, request, recipe + '-actual-prepare')
                self.assertEqual(checked.returncode, 0, checked.stderr.decode('utf-8', errors='replace'))
                report = json_object(json.loads((self.root / (recipe + '-actual-prepare.report.json')).read_bytes()))
                self.assertEqual(report['schema'], 'rrf-save-inspection-v2')
                assessment = json_object(report['assessment'])
                self.assertEqual(assessment['type'], 'fixture_bound_selection_verified')
                self.assertEqual(assessment['fixtureManifest'], file_identity(manifest))
                self.assertEqual(assessment['preparedProfileInventory'], file_identity(prepared_path))
                self.assertEqual(assessment['preparedFixtureRequest'], file_identity(profile / 'mod-content/fixture/_rrfa_request.json'))
                self.assertEqual(assessment['preparedCaseContract'], file_identity(profile / 'mod-content/fixture/_case_contract.json'))
                self.assertEqual(assessment['expectedSelection'], {'coreTenets': cores})
                self.assertEqual((assessment['sourceARiteId'], assessment['sourceBRiteId'], assessment['resultRiteId']), ('150', '151', '153'))
                self.assertEqual(report['decoderExitCode'], 0)
                self.assertTrue(report['saveUnchanged']); self.assertFalse(report['gameStarted'])
                decoder_marker = self.root / 'authored-decoder-invoked'
                self.assertEqual(decoder_marker.read_text(encoding='utf-8'), 'AUTHORED_DECODER_ONLY')
                decoder_marker.unlink()
                # Actual prepared metadata drift is rejected before a decoder child can run.
                profile_metadata = profile / 'mod-content/fixture/_rrfa_request.json'
                profile_raw = profile_metadata.read_bytes()
                try:
                    profile_metadata.write_bytes(profile_raw + b' ')
                    rejected = self.inspect_cli(java, cli, request, recipe + '-prepared-tamper')
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertFalse(decoder_marker.exists())
                    self.assertFalse((self.root / (recipe + '-prepared-tamper.report.json')).exists())
                finally:
                    profile_metadata.write_bytes(profile_raw)
                # A syntactically valid full saved graph with a substituted source still fails comparison.
                wrong_source = self.root / (recipe + '-AUTHORED-wrong-source.ck3')
                wrong_source.write_text(authored_save(cores).replace(
                    'flag="rrf_origin_a" data={type=rite identity=150}',
                    'flag="rrf_origin_a" data={type=rite identity=151}'), encoding='utf-8')
                substituted = copy.deepcopy(request); substituted['save'] = json_object(file_identity(wrong_source))
                rejected = self.inspect_cli(java, cli, substituted, recipe + '-source-substitution')
                self.assertNotEqual(rejected.returncode, 0)
                self.assertTrue(decoder_marker.is_file())
                self.assertFalse((self.root / (recipe + '-source-substitution.report.json')).exists())
                decoder_marker.unlink()
                if count == 3:
                    three_prepared_pin = json_object(file_identity(prepared_path))
                else:
                    if three_prepared_pin is None:
                        raise AssertionError('Actual three-core preparation required for substitution regression')
                    crossed = copy.deepcopy(request)
                    crossed_expectation = json_object(crossed['expectation'])
                    crossed_expectation['preparedProfileInventory'] = three_prepared_pin
                    crossed['expectation'] = crossed_expectation
                    rejected = self.inspect_cli(java, cli, crossed, recipe + '-three-profile-substitution')
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertFalse(decoder_marker.exists())
                    self.assertFalse((self.root / (recipe + '-three-profile-substitution.report.json')).exists())
                # The original manifest is fixed before tampering. Both missing and modified metadata must be rejected.
                original_pin = file_identity(manifest); raw = metadata.read_bytes()
                for mutation in ('content', 'missing'):
                    if mutation == 'content': metadata.write_bytes(raw + b' ')
                    else: metadata.unlink()
                    with self.assertRaises(ValueError):
                        prepare.materialize_prebuilt_fixture(context, original_pin, self.root / ('rejected-' + recipe + mutation))
                    metadata.write_bytes(raw)


if __name__ == '__main__':
    unittest.main()
