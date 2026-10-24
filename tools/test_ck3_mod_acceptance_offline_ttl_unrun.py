"""Original R0002 shapes -> real closure producer -> public predecessor branch.

Relocation, resealing, projected frozen files and absent processes are authored
inputs. The retained originals are independently checked on their actual machine.
"""
from __future__ import annotations

import argparse
import ast
import copy
import contextlib
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')]
import ck3_live_run_id as ids
import ck3_mod_acceptance_allocate as allocation
import ck3_mod_acceptance_unrun as unrun
import ck3_mod_acceptance as entry
from ck3_mod_acceptance_background_types import JsonObject, JsonValue, file_pin, json_object, object_field, text_field


@runtime_checkable
class _PublicDispatch(Protocol):
    def __call__(self, args: argparse.Namespace) -> object: ...


class OfflineTTLUnrunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='AUTHORED_R2_TTL_')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = json_object(json.loads((REPO / 'tools/fixtures/ck3_R0002_pre_intent_offline_ttl.json').read_bytes()))
        self.machine = text_field(self.source, 'machine_id')
        self.leaves = json_object(self.relocate(self.source['leaves']))
        self.refs = json_object(self.relocate(self.source['source_pins']))
        for key in ('launcher_source', 'gate_source'):
            target = self.path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text_field(self.leaves, key).encode('utf-8'))
        self.frozen = object_field(self.leaves, 'frozen')
        self.live = self.path('frozen').parent
        self.keeper = self.path('keeper').parent
        self.state = Path(text_field(self.frozen, 'state_dir'))
        (self.live / 'controls').mkdir(parents=True)
        (self.state / 'profile').mkdir(parents=True)
        self.contract_pin = self.write(self.path('contract'), self.leaves['contract'])
        prepared = object_field(self.leaves, 'prepared_case')
        prepared['contract'] = self.contract_pin
        self.prepared_pin = self.write(self.path('prepared_case'), prepared)
        self.frozen_pin = self.write(self.path('frozen'), self.frozen)
        self.profile_pin = self.write(self.path('normal_exit_profile'), self.leaves['normal_exit_profile'])
        host_argv = self.frozen['argv']
        if not isinstance(host_argv, list):
            raise ValueError('Original host arguments required')
        host_argv[host_argv.index('--normal-exit-managed-profile-sha256') + 1] = self.profile_pin['sha256']
        self.frozen['argv'] = host_argv
        run_stdout = object_field(self.leaves, 'run_stdout')
        run_stdout['host_argv'] = host_argv
        self.leaves['run_stdout'] = run_stdout
        for key in ('ready', 'allocated_context', 'reviewed_context'):
            row = object_field(self.leaves, key)
            row.update({'prepared_case': self.prepared_pin, 'frozen_argv': self.frozen_pin,
                        'normal_exit_managed_profile': self.profile_pin})
            self.leaves[key] = row
            self.write(self.path(key), row)
        purpose = object_field(self.leaves, 'purpose')
        purpose['reviewed_context'] = self.actual_pin(self.path('reviewed_context'))
        self.write(self.path('purpose'), purpose)
        for key in ('keeper', 'keeper_parent_exit', 'keeper_ready', 'keeper_stop', 'run_result',
                    'allocator_result', 'run_stdout', 'run_stderr', 'offline_receipt', 'counter', 'root_release'):
            self.write(self.path(key), self.leaves[key])
        stdout = self.leaves['allocator_stdout']
        if not isinstance(stdout, list):
            raise ValueError('Original allocator stdout stream required')
        self.path('allocator_stdout').write_text('\n'.join(json.dumps(row) for row in stdout), encoding='utf-8')
        self.bus_root = self.root / 'bus'
        release = object_field(self.leaves, 'root_release')
        self.write(self.bus_root / 'tasks' / (text_field(self.frozen, 'screen_task') + '.json'), release['task'])
        (self.bus_root / 'events.jsonl').write_text(json.dumps(release['event']) + '\n', encoding='utf-8')
        # The bus binary is a pinned authored file; canonical event/task proof
        # generation and the release reader execute their real implementations.
        bus_cli = self.bus_root / 'bin/codex_task_bus.py'
        bus_cli.parent.mkdir(parents=True)
        bus_cli.write_bytes(b'# authored bus transport\n')
        files = object_field(self.frozen, 'files')
        bus_pin = self.actual_pin(bus_cli)
        files[str(bus_cli.resolve())] = {name: bus_pin[name] for name in ('bytes', 'sha256')}
        self.frozen['files'] = files
        self.reseal_frozen()
        self.packet: JsonObject = {'tasks': [{**object_field(release, 'task'), 'age_seconds': 1, 'stale': False}]}
        self.args = argparse.Namespace(previous_live=self.live, keeper_root=self.keeper,
            allocator_result=self.path('allocator_result'), allocator_stdout=self.path('allocator_stdout'),
            pre_intent_offline_run_result=self.path('run_result'), public_run_stdout=self.path('run_stdout'),
            public_run_stderr=self.path('run_stderr'), root_screen_release=self.path('root_release'),
            next_state=self.root / 'next/state', task_bus_root=self.bus_root,
            release_sequence=8607, done_sequence=8607, output=self.root / 'closure')
        self.id_root = self.path('counter').parents[2]

    def relocate(self, value: JsonValue) -> JsonValue:
        if isinstance(value, str):
            normalized = value.replace('\\', '/')
            if len(normalized) > 2 and normalized[1:3] == ':/':
                return str(self.root / normalized[0] / normalized[3:])
            return value
        if isinstance(value, list):
            return [self.relocate(item) for item in value]
        if isinstance(value, dict):
            return {str(self.relocate(key)): self.relocate(item) for key, item in value.items()}
        return value

    def path(self, key: str) -> Path:
        return Path(text_field(object_field(self.refs, key), 'path'))

    @staticmethod
    def actual_pin(path: Path) -> JsonObject:
        raw = path.read_bytes()
        return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def write(self, path: Path, value: object) -> JsonObject:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return self.actual_pin(path)

    def reseal_frozen(self) -> None:
        ref = self.write(self.path('frozen'), self.frozen)
        for key in ('ready', 'allocated_context', 'reviewed_context'):
            row = object_field(self.leaves, key)
            row['frozen_argv'] = ref
            self.write(self.path(key), row)
        purpose = object_field(self.leaves, 'purpose')
        purpose['reviewed_context'] = self.actual_pin(self.path('reviewed_context'))
        self.write(self.path('purpose'), purpose)

    def produce(self) -> unrun.UnrunBundleReport:
        with patch.object(ids, 'current_machine_id', return_value=self.machine), patch.object(ids,
                'default_state_root', return_value=self.id_root), patch.object(allocation,
                'current_screen_absent', return_value=self.packet), patch.object(allocation,
                'runtime_process_inventory', return_value={'blockers': []}):
            return unrun.build_bundle(self.args)

    def test_actual_producer_consumer_roundtrip_preserves_refusal_and_consumed_purpose(self) -> None:
        purpose = self.path('purpose').read_bytes()
        result = self.produce()
        self.assertEqual(json.loads(json.dumps(self.source)), self.source)
        facts = object_field(result['validation'], 'failure_cleanup')
        self.assertEqual(result['validation']['mode'], 'previous-shared-allocated-pre-intent-offline-ttl-refused')
        self.assertIsNone(facts['original_host_exit_code'])
        self.assertIsNone(facts['original_ck3_exit_code'])
        self.assertEqual(facts['original_keeper_exit_code'], 0)
        for key in ('normal_close_qualified', 'typed_normal_exit_proven', 'business_pass', 'release_pass',
                    'historical_receipt_is_current_offline_admission'):
            self.assertIs(facts[key], False)
        self.assertEqual(self.path('purpose').read_bytes(), purpose)
        self.assertEqual(object_field(facts, 'original_inputs_verified')['immutable_inputs_checked'], 3)
        # Execute the public allocator's entire original predecessor branch,
        # stopping before the later identity/SCREEN mutation. No historical
        # Selection is instantiated merely to read old evidence.
        source = ast.parse((REPO / 'tools/ck3_mod_acceptance_allocate.py').read_text('utf-8-sig'))
        branches = [node for node in ast.walk(source) if isinstance(node, ast.If)
                    and ast.unparse(node.test) == 'bootstrap_path' and node.orelse
                    and ast.unparse(node.orelse[0]).startswith('previous = args.previous_live.resolve()')]
        self.assertEqual(len(branches), 1)
        refs = file_pin(result['bundle'])
        namespace: dict[str, object] = {**vars(allocation), 'args': SimpleNamespace(previous_live=self.live,
            previous_keeper=self.keeper, previous_release=Path(result['previous_release']['path']), latest_screen_release=None),
            'selection': SimpleNamespace(state_dir=self.args.next_state), 'machine': self.machine,
            'state_root': self.id_root, 'binding': {'machine_id': self.machine, 'state_root': str(self.id_root)},
            'failure_path': Path(refs['path']), 'bus_packet': self.packet}
        with patch.object(ids, 'current_machine_id', return_value=self.machine), patch.object(ids,
                'default_state_root', return_value=self.id_root), patch.object(allocation,
                'runtime_process_inventory', return_value={'blockers': []}):
            exec(compile(ast.Module(body=branches[0].orelse, type_ignores=[]), '<actual-public-predecessor-branch>', 'exec'), namespace)
        self.assertEqual(json_object(namespace['closure'])['mode'], result['validation']['mode'])

    def test_false_credit_float_bool_and_wrong_source_are_rejected(self) -> None:
        baseline = copy.deepcopy(object_field(self.leaves, 'run_result'))
        for code in (True, 2.0, 0):
            changed = {**baseline, 'exit_code': code}
            self.write(self.path('run_result'), changed)
            with self.subTest(code=code), self.assertRaises(ValueError):
                self.produce()
            self.args.output = self.root / ('closure-' + str(code))
        self.write(self.path('run_result'), baseline)
        self.path('launcher_source').write_bytes(b'# altered launcher\n')
        with self.assertRaises(ValueError):
            self.produce()

    def test_fresh_receipt_same_state_or_actual_host_evidence_refuse(self) -> None:
        self.args.next_state = self.state
        with self.assertRaisesRegex(ValueError, 'separate next state'):
            self.produce()
        self.args.next_state, self.args.output = self.root / 'next/state', self.root / 'fresh-closure'
        receipt = object_field(self.leaves, 'offline_receipt')
        receipt['observed_at_utc'] = '2026-10-24T11:03:20+00:00'
        native = object_field(receipt, 'native_evidence')
        native['observed_at_utc'] = receipt['observed_at_utc']
        receipt['native_evidence'] = native
        self.write(self.path('offline_receipt'), receipt)
        with self.assertRaisesRegex(ValueError, 'expired'):
            self.produce()
        receipt['observed_at_utc'] = '2026-10-24T11:02:14.411214+00:00'
        native['observed_at_utc'] = receipt['observed_at_utc']
        receipt['native_evidence'] = native
        self.write(self.path('offline_receipt'), receipt)
        (self.live / 'host-started.json').write_text('{}', encoding='utf-8')
        self.args.output = self.root / 'host-closure'
        with self.assertRaisesRegex(ValueError, 'launch/native/control/save'):
            self.produce()

    def test_exact_modified_production_scope_is_strict(self) -> None:
        from mypy import api
        path = REPO / 'tools/ck3_mod_acceptance_unrun.py'
        source = ast.parse(path.read_text('utf-8-sig'))
        names = {'_UnrunProcessInventory', '_ttl_pin', '_ttl_original', '_ttl_allocator_stdout',
                 'validate_pre_intent_offline_ttl_refusal', 'build_pre_intent_offline_ttl_bundle'}
        nodes = [copy.deepcopy(node) for node in source.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual(len(nodes), len(names))
        unit = ast.parse('''from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable, Literal
import argparse, hashlib, json, os
from ck3_mod_acceptance import same_directory_control_peer
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field, strings_field
from ck3_mod_acceptance_unrun import SCHEMA, OFFLINE_TTL_KIND, UnrunBundleReport, _integer, _timestamp, _release_stages, _read, _write
''')
        unit.body.extend(nodes)
        temporary = self.root / 'exact_unrun_scope.py'
        temporary.write_text(ast.unparse(ast.fix_missing_locations(unit)), encoding='utf-8')
        with patch.dict(os.environ, {'MYPYPATH': os.pathsep.join((str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')))}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', str(self.root / 'mypy-cache'), str(temporary)])
        self.assertEqual(code, 0, stdout + stderr)

    def test_actual_allocator_counter_advance_keeps_only_immutable_snapshot_frozen(self) -> None:
        import test_ck3_mod_acceptance_r06_scope as public_fixture
        from xar_autoplayer.bridge.runtime_input_contract_v1 import validate_running_inputs
        result = self.produce()
        proof = object_field(result['validation'], 'failure_cleanup')
        counter = file_pin(object_field(proof, 'original_evidence')['counter'])
        self.assertNotEqual(Path(counter['path']), self.path('counter'))
        original = self.path('counter').read_bytes()
        harness = public_fixture.PublicR06ScopeTests('runTest')
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        catalog = json_object(json.loads(harness.products_path.read_bytes()))
        products = object_field(catalog, 'products')
        product = object_field(products, 'war-episode04-r10')
        product['runtime_mod_key'] = 'dynastic-esotericism'
        products['war-episode04-r10'], catalog['products'] = product, products
        harness.products_path = harness.root / 'products.json'
        harness.write(harness.products_path, catalog)
        harness.machine = self.machine
        harness.manifest['machine_id'] = self.machine
        harness.write(harness.manifest_path, harness.manifest)
        harness.runtime['manifest'] = self.actual_pin(harness.manifest_path)
        harness.write(harness.runtime_path, harness.runtime)
        harness.prepare()
        args = argparse.Namespace(**vars(harness.args('allocate')))
        args.attempt, args.keeper_output = 'a01', harness.root / 'next-keeper'
        args.previous_live, args.previous_keeper = self.live, self.keeper
        args.previous_release = Path(result['previous_release']['path'])
        args.previous_failure_close = Path(result['bundle']['path'])
        args.first_machine_bootstrap, args.latest_screen_release = None, None
        admission = harness.root / 'machine-admission'
        admission.mkdir()

        def process(argv: list[str], **kwargs: object) -> SimpleNamespace:
            if argv[0] == 'git':
                return SimpleNamespace(returncode=0, stdout=b'', stderr=b'')
            return SimpleNamespace(returncode=0, stdout=b'{"task":{"last_sequence":1}}', stderr=b'')

        def finish(*args_unused: object) -> int:
            args.keeper_output.mkdir(exist_ok=True)
            harness.write(args.keeper_output / 'report.json', {'authored_keeper_completion': True})
            return 0

        dispatch: object = entry.native_dispatch
        if not isinstance(dispatch, _PublicDispatch):
            raise ValueError('Actual public dispatcher unavailable')
        with contextlib.ExitStack() as stack:
            for name, value in [('actual_machine_binding', {'machine_id': self.machine, 'state_root': str(self.id_root)}),
                    ('shared_bus_history', ([], True)), ('current_screen_absent', self.packet),
                    ('runtime_process_inventory', {'blockers': []}), ('claim_machine_admission', admission),
                    ('keeper_command', ['authored-no-OS-launch']), ('wait_for_keeper_ready', {'authored': True})]:
                stack.enter_context(patch.object(allocation, name, return_value=value))
            stack.enter_context(patch.object(ids, 'current_machine_id', return_value=self.machine))
            stack.enter_context(patch.object(ids, 'default_state_root', return_value=self.id_root))
            stack.enter_context(patch.object(allocation, 'wait_for_allocated_keeper', side_effect=finish))
            stack.enter_context(patch.object(subprocess, 'run', side_effect=process))
            keeper_launch = stack.enter_context(patch.object(subprocess, 'Popen', return_value=Mock(pid=987654)))
            stack.enter_context(patch('psutil.Process', return_value=SimpleNamespace(create_time=lambda: 1)))
            with contextlib.redirect_stdout(io.StringIO()):
                dispatch(args)
        keeper_launch.assert_called_once()
        ledger = json_object(json.loads((harness.root / 'single-use-ledger/allocated.json').read_bytes()))
        next_live = Path(text_field(ledger, 'live'))
        frozen = json_object(json.loads((next_live / 'frozen-argv.json').read_bytes()))
        self.assertTrue(text_field(frozen, 'run_id').endswith('--R0003'))
        self.assertNotEqual(self.path('counter').read_bytes(), original)
        self.assertEqual(Path(counter['path']).read_bytes(), original)
        files = object_field(frozen, 'files')
        self.assertNotIn(str(self.path('counter')), files)
        self.assertIn(counter['path'], files)
        self.assertGreater(validate_running_inputs(next_live, frozen)['immutable_inputs_checked'], 30)


if __name__ == '__main__':
    unittest.main(verbosity=2)
