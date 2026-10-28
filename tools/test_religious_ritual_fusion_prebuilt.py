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
from typing import Literal
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
        self.root = Path(temporary.name).resolve()
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

    def inspect_cli(self, java: str, cli: Path, request: JsonObject, label: str, *,
                    command: Literal['inspect-save', 'inspect-save-v4'] = 'inspect-save') -> subprocess.CompletedProcess[bytes]:
        inputs = self.root / (label + '.request.json')
        inputs.write_text(json.dumps(request, allow_nan=False), encoding='utf-8')
        return subprocess.run([java, '-jar', str(cli), command, '--inputs', str(inputs),
            '--output', str(self.root / (label + '.report.json'))], cwd=self.root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=150, check=False)

    def test_real_java_cold_snapshot_wallet_crosses_saved_prepare_and_complete_ast_consumer(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        cli = Path(os.environ.get('RRF_FIXTURE_CLI_JAR', str(
            repository / 'mod_religious_ritual_fusion/tools/target/quarkus-app/quarkus-run.jar'))).resolve()
        self.assertTrue(cli.is_file(), 'Actual rebuilt Java CLI required; no skip is a pass')
        java = shutil.which('java')
        if java is None:
            raise AssertionError('Actual Java runtime required')
        cores = ['tenet_esotericism', 'tenet_astrology', 'tenet_communal_identity']
        current_text = authored_save(cores).replace('date=1066.9.16',
            'playthrough_id="authored-cold-wallet" date=1066.9.17').replace(
            'alive_data={variables={data={', 'alive_data={piety={currency=5400} variables={data={'
            '{flag="rrfa_piety_before" data={type=value identity=600000000}}'
            '{flag="rrf_charged_cost" data={type=value identity=50000000}}')
        observations: dict[str, JsonObject] = {}
        saves: dict[str, Path] = {}
        for label, text in (
                ('before', current_text.replace('currency=5400', 'currency=6000').replace(
                    'living={31254={rite=153', 'living={31254={rite=150').replace(
                    authored_reference('rrf_last_result_rite', '153'), '')),
                ('after', current_text.replace('currency=5400', 'currency=5500')),
                ('current', current_text)):
            save = self.root / ('cold-' + label + '-AUTHORED.ck3')
            save.write_text(text, encoding='utf-8'); saves[label] = save
            request = json_object({'schemaVersion': 4, 'machineId': 'authored-machine',
                'repository': str(repository), 'save': file_identity(save),
                'decoder': file_identity(Path(sys.executable)),
                'selection': {'tables': [{'kind': 'ACTOR', 'path': ['living'], 'ids': ['31254'], 'required': True}],
                              'projections': [], 'metadataRequired': True, 'structureCensus': False, 'structureRoots': []}})
            child = self.inspect_cli(java, cli, request, 'cold-' + label, command='inspect-save-v4')
            self.assertEqual(child.returncode, 0, child.stderr.decode('utf-8', errors='replace'))
            report_path = self.root / ('cold-' + label + '.report.json')
            observed = json_object(json.loads(report_path.read_bytes()))
            self.assertEqual(observed['businessAssessment'], 'NOT_ASSESSED')
            observations[label] = json_object(file_identity(report_path))
        fixture_request = json_object({'schemaVersion': 4, 'kind': 'cold_reload', 'mode': 'rite', 'actorHistoryId': '1128',
            'setup': {'type': 'saved_snapshot', 'actorId': '31254', 'sourceSave': file_identity(saves['current']),
                      'sourceInspection': observations['current'], 'expectedCurrentPiety': '5400',
                      'creationHistory': {'before': '6000', 'after': '5500', 'chargedCost': 500,
                                          'beforeInspection': observations['before'], 'afterInspection': observations['after']}},
            'expectedSelection': {'coreTenets': cores}})
        inputs = self.root / 'cold-fixture.request.json'; inputs.write_text(json.dumps(fixture_request), encoding='utf-8')
        fixture = self.root / 'java-cold-wallet'
        child = subprocess.run([java, '-jar', str(cli), 'fixture', '--repo-root', str(repository),
            '--output', str(fixture), '--machine-id', 'authored-machine', '--inputs', str(inputs)],
            cwd=self.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        self.assertEqual(child.returncode, 0, child.stderr.decode('utf-8', errors='replace'))
        cli_receipt = json_object(json.loads(child.stdout))
        self.assertEqual(set(cli_receipt), {'fixture', 'manifest', 'request', 'game_started', 'business_acceptance'})
        manifest = Path(str(fixture) + '.fixture.json')
        input_receipt = Path(str(fixture) + '.inputs.json')
        sidecar = json_object(json.loads(input_receipt.read_bytes()))
        self.assertEqual(sidecar['manifest'], file_identity(manifest))
        self.assertEqual(sidecar['request'], file_identity(fixture / '_rrfa_request.json'))
        self.assertEqual(sidecar['input_pins'],
                         [file_identity(saves['current']), observations['current'], observations['before'], observations['after']])
        emitted = json_object(json.loads(manifest.read_bytes()))
        self.assertEqual(len(json_object(emitted['files'])), 8)
        self.assertFalse(json_object(emitted['receipt'])['fixture_contains_business_effects'])
        trigger = fixture / 'common/scripted_triggers/rrfa_observation_triggers.txt'
        self.assertIn('piety = 5400\n    var:rrfa_piety_before = 6000', trigger.read_text(encoding='utf-8-sig'))
        product = self.root / 'cold-product'; product.mkdir()
        (product / 'descriptor.mod').write_text('name="Authored cold product"\n', encoding='utf-8')
        plain: JsonObject = {}
        for index, relative in enumerate(prepare.CONFIG_NAMES):
            path = self.root / ('cold-plain-' + str(index)); path.write_text('authored configuration\n', encoding='utf-8')
            plain[relative] = json_object(file_identity(path))
        contract = json_object(json.loads((repository / 'tools/ck3_mod_acceptance_cases/religious_ritual_fusion_cold_reload.json').read_bytes()))
        source = json_object(file_identity(saves['current']))
        context = json_object({'product': 'religious-ritual-fusion', 'case': 'cold_reload',
            'repo_root': str(repository), 'runtime_manifest': file_identity(self.shared),
            'state_dir': str(self.root / 'cold-state'), 'output': str(self.root / 'cold-prepared'), 'case_contract': contract,
            'saved_campaign': {'save': source['path'], 'bytes': source['bytes'], 'sha256': source['sha256'],
                               'player_id': 31254, 'date_raw': 53144376},
            'case_inputs': {'product_dir': str(product), 'plain_configuration': plain,
                            'prebuilt_fixture_manifest': file_identity(manifest),
                            'prebuilt_fixture_inputs': file_identity(input_receipt)}})
        selected_inputs = json_object(context['case_inputs'])
        expected_inputs = prepare.prebuilt_fixture_source_pins(selected_inputs)
        self.assertEqual(len(expected_inputs), 7)
        for field in ('prebuilt_fixture_inputs', 'prebuilt_fixture_manifest'):
            missing = {key: value for key, value in selected_inputs.items() if key != field}
            with self.subTest(missing=field), self.assertRaises(ValueError):
                prepare.prebuilt_fixture_inputs(missing)
        receipt_bytes = input_receipt.read_bytes()
        receipt_json = json_object(json.loads(receipt_bytes))
        for bad in (True, 1.0, None):
            wrong = json_object(copy.deepcopy(receipt_json))
            pins = wrong.get('input_pins')
            if not isinstance(pins, list):
                raise AssertionError('Actual input receipt must have its pin list')
            first = json_object(pins[0]); first['bytes'] = bad; pins[0] = first
            input_receipt.write_text(json.dumps(wrong), encoding='utf-8')
            changed_inputs = {**selected_inputs, 'prebuilt_fixture_inputs': file_identity(input_receipt)}
            with self.subTest(wrong_bytes=bad), self.assertRaises(ValueError):
                prepare.prebuilt_fixture_inputs(changed_inputs)
        wrong = json_object(copy.deepcopy(receipt_json)); wrong['request'] = observations['before']
        input_receipt.write_text(json.dumps(wrong), encoding='utf-8')
        with self.assertRaises(ValueError):
            prepare.prebuilt_fixture_inputs({**selected_inputs, 'prebuilt_fixture_inputs': file_identity(input_receipt)})
        input_receipt.write_bytes(receipt_bytes)
        with patch.object(prepare, '_engine', return_value=(ModuleType('authored_engine'),
                {'game_version': 'authored-only-no-game', 'exe_sha256': '0' * 64})):
            result = adapter.prepare_case(context)
        self.assertFalse(result['business_pass'])
        self.assertEqual(json_object(result['startup'])['mode'], 'saved_campaign')
        prepared = self.root / 'cold-prepared/profile-preparation.json'
        profile_request = self.root / 'cold-state/profile/mod-content/fixture/_rrfa_request.json'
        self.assertEqual(profile_request.read_bytes(), (fixture / '_rrfa_request.json').read_bytes())
        inventory = json_object(json.loads(prepared.read_bytes()))
        self.assertIn('mod-content/fixture/_rrfa_request.json', json_object(inventory['files']))
        compiled_path = self.root / 'cold-state/profile/mod-content/fixture/_case_contract.json'
        compiled = json_object(json.loads(compiled_path.read_bytes()))
        emitter = json_object(compiled['emitter'])
        self.assertEqual(emitter['input_receipt'], file_identity(input_receipt))
        self.assertEqual(emitter['fixture_request'], file_identity(fixture / '_rrfa_request.json'))
        self.assertEqual(emitter['input_pins'], [file_identity(saves['current']), observations['current'], observations['before'], observations['after']])
        selected_path = self.root / 'cold-selection-preparation.json'
        selected_path.write_text(json.dumps({'case_inputs': selected_inputs, 'preparation': result}), encoding='utf-8')
        isolated_env = {key: value for key, value in os.environ.items() if key.upper() != 'PYTHONPATH'}
        isolated = [sys.executable, '-I', str(repository / 'tools/test_ck3_mod_acceptance_case_imports.py'),
                    '--allocate-prebuilt-inputs-fixture', str(selected_path)]
        frozen = subprocess.run(isolated, cwd=self.root, env=isolated_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=150, check=False)
        self.assertEqual(frozen.returncode, 0, frozen.stderr.decode('utf-8', errors='replace'))
        self.assertEqual(json_object(json.loads(frozen.stdout))['prebuilt_external_filepins_frozen'], 7)
        inspect = json_object({'schemaVersion': 2, 'machineId': 'authored-machine', 'repository': str(repository),
            'save': file_identity(saves['current']), 'decoder': file_identity(Path(sys.executable)),
            'layout': {'actorTable': ['living'], 'riteTable': ['rites', 'database'],
                       'faithTable': ['faiths', 'database'], 'religionTable': ['religion', 'religions']},
            'selection': {'actorId': '31254', 'riteIds': ['150', '151', '153'], 'faithIds': ['13'], 'religionIds': ['8']},
            'expectation': {'type': 'fusion_selection', 'fixtureManifest': file_identity(manifest),
                            'preparedProfileInventory': file_identity(prepared), 'resultRiteId': '153'}})
        checked = self.inspect_cli(java, cli, inspect, 'cold-actual-prepared')
        self.assertEqual(checked.returncode, 0, checked.stderr.decode('utf-8', errors='replace'))
        verified = json_object(json.loads((self.root / 'cold-actual-prepared.report.json').read_bytes()))
        assessment = json_object(verified['assessment'])
        self.assertEqual(assessment['preparedFixtureRequest'], file_identity(profile_request))
        self.assertEqual(assessment['resultRiteId'], '153')
        marker = self.root / 'authored-decoder-invoked'; marker.unlink()
        current_report = self.root / 'cold-current.report.json'
        original = current_report.read_bytes(); current_report.write_bytes(original + b' ')
        rejected = self.inspect_cli(java, cli, inspect, 'cold-observation-tamper')
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(marker.exists(), 'Changed frozen evidence must fail before a decoder launch')
        with self.assertRaises(ValueError):
            prepare.prebuilt_fixture_inputs(selected_inputs)
        stale = subprocess.run(isolated, cwd=self.root, env=isolated_env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=150, check=False)
        self.assertNotEqual(stale.returncode, 0, 'Independent public import must reject changed external evidence')
        current_report.write_bytes(original)
        input_receipt.unlink()
        with self.assertRaises(ValueError):
            prepare.prebuilt_fixture_inputs(selected_inputs)
        rejected = self.inspect_cli(java, cli, inspect, 'cold-deleted-receipt')
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(marker.exists())

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
                legacy_inputs = json_object(context['case_inputs'])
                self.assertIsNone(prepare.prebuilt_fixture_inputs(legacy_inputs))
                self.assertFalse(Path(str(fixture) + '.inputs.json').exists())
                with self.assertRaises(ValueError):
                    prepare.prebuilt_fixture_inputs({**legacy_inputs, 'prebuilt_fixture_inputs': None})
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
