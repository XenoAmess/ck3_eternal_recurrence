"""Actual public allocator/Selection -> existing producer -> canonical bind, no CK3."""
from __future__ import annotations
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')]
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocation
import ck3_mod_acceptance_prepare as preparation
import build_normal_exit_source_inventory_v1 as inventory
import test_ck3_mod_acceptance_r06_scope as public_fixture
import test_ck3_mod_acceptance_normal_exit_profile as binding_fixture


class AllocatedNormalExitTests(unittest.TestCase):
    write = public_fixture.PublicR06ScopeTests.write
    args = public_fixture.PublicR06ScopeTests.args
    allocate = public_fixture.PublicR06ScopeTests.allocate

    def setUp(self):
        public_fixture.PublicR06ScopeTests.setUp(self)
        catalog = entry.read_json(self.products_path)
        case = catalog['products']['war-episode04-r10']['cases'][0]
        case['required_mcp_tools'] += sorted(entry.NORMAL_EXIT_REQUIRED_MCP_TOOLS_V1)
        self.products_path = self.root / 'products.json'
        self.write(self.products_path, catalog)
        for tool in entry.NORMAL_EXIT_REQUIRED_MCP_TOOLS_V1:
            self.manifest['capabilities'][tool] = {'source_build_ready': True, 'actual_live_qualified': False}
        host = self.paths['host']
        host.write_text(host.read_text().replace("raise RuntimeError", "p.add_argument('--normal-exit-managed-profile')\np.add_argument('--normal-exit-managed-profile-sha256')\nraise RuntimeError"))
        self.manifest['host'].update({k: v for k, v in entry.pin(host).items() if k != 'path'})
        self.write(self.manifest_path, self.manifest)
        self.runtime['manifest'] = entry.pin(self.manifest_path)
        self.write(self.runtime_path, self.runtime)
        for name in ('ck3_mod_acceptance_normal_exit_profile.py', 'build_normal_exit_source_inventory_v1.py'):
            target = self.paths['source_root'] / 'tools' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((REPO / 'tools' / name).read_bytes())
        engine_source = self.paths['source_root'] / 'tools/fixture_engine_prepare.py'
        engine_source.write_text("import hashlib\ndef engine_identity(repo, *, game_dir, steam_manifest=None):\n return {'game_version': 'test-only', 'exe_sha256': hashlib.sha256((game_dir/'binaries/ck3.exe').read_bytes()).hexdigest()}\n")
        for relative in inventory.STOCK_GUI_PATHS:
            target = self.root / 'game/game' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# synthetic stock file\n')
        self.product = self.root / 'formal-product'
        self.product.mkdir()
        (self.product / 'descriptor.mod').write_text('name="Synthetic normal exit product"\n')
        self.plain = {}
        for name in preparation.CONFIG_NAMES:
            path = self.root / 'plain' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('synthetic plain config\n')
            self.plain[name] = entry.pin(path)
        self.write(self.root / 'inputs.json', {'state_dir': str(self.state),
            'saved_campaign': self.seed, 'case_inputs': self.inputs})

        def actual_profile(context):
            profile = preparation.materialize_product_profile(context, self.product, self.plain)
            profile = preparation.finish_product_profile(context, profile,
                provenance={'kind': 'SYNTHETIC_PUBLIC_ALLOCATE_NORMAL_EXIT_NO_GAME'})
            return {'startup': {'mode': 'saved_campaign', 'state_dir': str(self.state),
                'saved_campaign': {**self.seed, 'product_inventory': str(self.paths['inventory'])}},
                'initial_plan': entry.pin(self.paths['initial']), 'profile': profile,
                'runtime_status': 'NOT_RUN'}

        with patch.object(public_fixture.adapter, 'prepare_case', side_effect=actual_profile):
            entry.native_dispatch(self.args('prepare'))

    def selected(self, context):
        return entry.Selection(self.runtime_path, self.products_path, 'war-episode04-r10',
                               'r10-common-preparation', context, self.prepared_path)

    def test_actual_allocate_freezes_binding_and_reconstructed_selection_has_identical_argv(self):
        originals = self.allocate()
        frozen = entry.read_json(self.live / 'frozen-argv.json')
        selected = self.selected(self.live / 'ready-context.json')
        self.assertEqual(selected.argv, frozen['argv'])
        self.assertEqual(self.ready['normal_exit_managed_profile'],
                         entry.read_json(self.live / 'allocated-context.json')['normal_exit_managed_profile'])
        reference = self.ready['normal_exit_managed_profile']
        self.assertEqual(selected.argv[selected.argv.index('--normal-exit-managed-profile') + 1], reference['path'])
        self.assertEqual(selected.argv[selected.argv.index('--normal-exit-managed-profile-sha256') + 1], reference['sha256'])
        profile = entry.read_json(Path(reference['path']))
        args = SimpleNamespace(state_dir=self.state, output=self.live / 'native-report.json',
            normal_exit_managed_profile=Path(reference['path']), normal_exit_managed_profile_sha256=reference['sha256'])
        driver = SimpleNamespace()
        binding_fixture.host_binding()(driver, args)
        verified = inventory.verify_source_inventory_v1(profile['normal_exit_source_inventory'],
            driver.normal_exit_managed_profile)
        self.assertTrue(verified['static_sources_verified'])
        running = inventory.verify_source_inventory_v1(profile['normal_exit_source_inventory'],
            driver.normal_exit_managed_profile, input_phase='running')
        self.assertTrue(running['static_sources_verified'])
        required = [path for path, _ in selected.required_pins]
        generated = entry.normal_exit_static_binding_v1(reference, state_dir=self.state,
            run_dir=self.live, runtime_manifest=entry.file_pin(entry.pin(self.manifest_path)))['files']
        for row in generated:
            self.assertIn(Path(row['path']), required)
            self.assertEqual(frozen['files'][row['path']], {k: row[k] for k in ('bytes', 'sha256')})
        for name in ('ck3_mod_acceptance_normal_exit_profile.py', 'build_normal_exit_source_inventory_v1.py'):
            self.assertIn(str(self.paths['source_root'] / 'tools' / name), frozen['files'])
        before = {Path(row['path']): Path(row['path']).read_bytes() for row in generated}
        self.assertEqual(self.selected(self.live / 'ready-context.json').argv, selected.argv)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        with self.assertRaisesRegex(ValueError, 'already exists'):
            allocation.allocate_normal_exit_profile_v1(selected, self.live)
        self.assertEqual(self.prepared_path.read_bytes(), originals[self.prepared_path])

    def test_wrong_missing_null_and_false_equal_reference_are_rejected(self):
        self.allocate()
        original = copy.deepcopy(self.ready)
        for mode in ('missing', 'null', 'boolean-size', 'foreign-path', 'bad-digest'):
            context = copy.deepcopy(original)
            if mode == 'missing': context.pop('normal_exit_managed_profile')
            elif mode == 'null': context['normal_exit_managed_profile'] = None
            elif mode == 'boolean-size': context['normal_exit_managed_profile']['bytes'] = True
            elif mode == 'foreign-path': context['normal_exit_managed_profile']['path'] = str(self.root / 'foreign-profile')
            else: context['normal_exit_managed_profile']['sha256'] = '0' * 64
            path = self.live / (mode + '-context.json')
            self.write(path, context)
            with self.subTest(mode=mode):
                if mode == 'missing':
                    historical = self.selected(path)
                    self.assertNotIn('--normal-exit-managed-profile', historical.argv)
                    with patch.object(historical, 'preflight', side_effect=AssertionError('No launch preflight admitted')):
                        with self.assertRaisesRegex(ValueError, 'missing for launch'):
                            historical.run()
                else:
                    with self.assertRaises(ValueError):
                        self.selected(path)
        profile = Path(original['normal_exit_managed_profile']['path'])
        value = entry.read_json(profile)
        value['state_directory'] = str(self.root / 'wrong-state')
        self.write(profile, value)
        context = copy.deepcopy(original)
        context['normal_exit_managed_profile'] = entry.pin(profile)
        path = self.live / 'crossed-state-context.json'
        self.write(path, context)
        with self.assertRaisesRegex(ValueError, 'state/userdir/output'):
            self.selected(path)

    def test_explicit_three_tools_only_and_selected_builder_has_no_fallback(self):
        self.assertFalse(entry.normal_exit_tools_opted_in_v1([]))
        self.assertFalse(entry.normal_exit_tools_opted_in_v1(['ck3_take_snapshot']))
        for invalid in (None, True, [True], ['ck3_query_normal_exit_context_v1']):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                entry.normal_exit_tools_opted_in_v1(invalid)
        selected = self.selected(None)
        selected.case['required_mcp_tools'] = ['ck3_take_snapshot']
        live = self.root / 'synthetic-no-opt-in'
        live.mkdir()
        self.assertIsNone(allocation.allocate_normal_exit_profile_v1(selected, live))
        self.assertEqual(list(live.iterdir()), [])
        selected.case['required_mcp_tools'] = sorted(entry.NORMAL_EXIT_REQUIRED_MCP_TOOLS_V1)
        (self.paths['source_root'] / 'tools/build_normal_exit_source_inventory_v1.py').unlink()
        with self.assertRaises(FileNotFoundError):
            allocation.allocate_normal_exit_profile_v1(selected, live)
        self.assertFalse((live / 'normal-exit-binding').exists())

    def test_actual_modified_production_scope_is_strict(self):
        from mypy import api
        main = ast.parse((REPO / 'tools/ck3_mod_acceptance.py').read_text(encoding='utf-8-sig'))
        allocator = ast.parse((REPO / 'tools/ck3_mod_acceptance_allocate.py').read_text(encoding='utf-8-sig'))
        names = {'NormalExitAllocationBindingV1', 'NormalExitAllocatedContextV1',
                 'normal_exit_tools_opted_in_v1', 'normal_exit_static_binding_v1'}
        nodes = [copy.deepcopy(node) for node in main.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        nodes += [copy.deepcopy(node) for node in main.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'NORMAL_EXIT_REQUIRED_MCP_TOOLS_V1'
                          for target in node.targets)]
        nodes += [copy.deepcopy(node) for node in allocator.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                  and node.name in {'_NormalExitProfileProducerV1', 'allocate_normal_exit_profile_v1'}]
        self.assertEqual(len(nodes), 7)
        selected = next(node for node in main.body if isinstance(node, ast.ClassDef) and node.name == 'Selection')
        method = next(node for node in selected.body if isinstance(node, ast.FunctionDef) and node.name == 'build_argv')
        start = next(index for index, node in enumerate(method.body) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'normal_exit_enabled' for target in node.targets))
        unit = ast.parse('''from __future__ import annotations
import hashlib, importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol, TypedDict, runtime_checkable
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field
from ck3_mod_acceptance import _verification_file_pin_v1, _verification_checked_pin_v1, _verification_read_object_v1, _verification_actual_pin_v1
class Selection(Protocol):
    case: JsonObject
    context: JsonObject
    manifest: JsonObject
    runtime: JsonObject
    state_dir: Path
    run_dir: Path
    manifest_path: Path
    required_pins: list[tuple[Path, object]]
def consume(self: Selection, state: Path, argv: list[str]) -> None:
    pass
''')
        consumer = unit.body.pop()
        consumer.body = copy.deepcopy(method.body[start:start + 3])
        run = next(node for node in selected.body if isinstance(node, ast.FunctionDef) and node.name == 'run')
        self.assertIsInstance(run.body[0], ast.If)
        self.assertIn('normal_exit_managed_profile', ast.unparse(run.body[0]))
        consumer.body.append(copy.deepcopy(run.body[0]))
        unit.body.extend([*nodes, consumer])
        with tempfile.TemporaryDirectory(prefix='SYNTHETIC_NORMAL_EXIT_TYPE_SCOPE_') as temporary:
            path = Path(temporary) / 'allocated_normal_exit_scope.py'
            path.write_text(ast.unparse(ast.fix_missing_locations(unit)), encoding='utf-8')
            with patch.dict('os.environ', {'MYPYPATH': str(REPO / 'tools') + ';' + str(REPO / 'ck3_autonomous_player/src')}):
                stdout, stderr, code = api.run(['--strict', '--follow-imports=silent', '--no-incremental',
                    '--cache-dir', str(Path(temporary) / 'mypy-cache'), str(path)])
        self.assertEqual(code, 0, stdout + stderr)

    def test_historical_v1_v2_public_verifiers_keep_original_argv(self):
        """Run the two original hosted-RED consumer chains in a fresh process."""
        paths = [REPO / 'mod_living_artifacts/tools', REPO / 'tools', REPO,
                 REPO / 'ck3_autonomous_player/src']
        environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                       'PYTHONPATH': os.pathsep.join(map(str, paths))}
        completed = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', '-v',
            'test_threshold_acceptance_adapter.ThresholdAcceptanceTests.test_actual_v2_producer_public_selection_and_cli_exit',
            'test_threshold_acceptance_adapter.ThresholdAcceptanceTests.test_actual_frozen_v1_producer_legacy_public_verification_fresh_process'],
            cwd=REPO, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=180)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn('Ran 2 tests', completed.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
