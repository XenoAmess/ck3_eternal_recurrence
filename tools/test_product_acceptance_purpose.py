"""Public purpose producer -> original host loader/driver clock; no game launch."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import (
    FilePin, JsonObject, JsonValue, ProductAcceptanceClockV1, file_pin, json_object, strings_field,
    product_acceptance_purpose_v1, write_product_acceptance_purpose_v1,
)

REPO = Path(__file__).resolve().parents[1]
HOST = REPO / 'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'


def pin(path: Path) -> FilePin:
    raw = path.read_bytes()
    return file_pin({'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding='utf-8')


@runtime_checkable
class Loader(Protocol):
    def __call__(self, args: argparse.Namespace) -> ProductAcceptanceClockV1 | None: ...


@runtime_checkable
class ClockDriver(Protocol):
    progress_governor: object
    def _campaign_advance_deadline_v1(self, starting: dict[str, object], target_date_raw: int) -> dict[str, object] | None: ...
    def cap_campaign_advance_plan_v1(self, planned: dict[str, object]) -> dict[str, object]: ...


@runtime_checkable
class DriverFactory(Protocol):
    def __call__(self) -> ClockDriver: ...


class OriginalR05Boundary:
    progress_governor: object = SimpleNamespace(scope=None)

    def _campaign_advance_deadline_v1(self, starting: dict[str, object], target_date_raw: int) -> dict[str, object] | None:
        raise RuntimeError('Actual independent progress scope absent')

    def cap_campaign_advance_plan_v1(self, planned: dict[str, object]) -> dict[str, object]:
        raise RuntimeError('Ordinary progress governor must bind before AUTO')


def actual_recording_driver(clock: ProductAcceptanceClockV1 | None) -> ClockDriver:
    tree = ast.parse(HOST.read_text(encoding='utf-8-sig'))
    server = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'native_server')
    driver = next(node for node in server.body if isinstance(node, ast.ClassDef) and node.name == 'RecordingDriver')
    # Execute the actual class source, retaining the selected parent seam. The
    # authored parent reproduces the observed R0001 refusal without any pipe.
    namespace: dict[str, object] = {'NativeHeadlessGameplayDriver': OriginalR05Boundary, 'product_clock': clock}
    exec(compile(ast.Module(body=[driver], type_ignores=[]), str(HOST), 'exec'), namespace)
    factory = namespace['RecordingDriver']
    if not isinstance(factory, DriverFactory):
        raise ValueError('Actual host driver class absent')
    return factory()


class ProductPurposeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'unit-run'
        self.root.mkdir()
        self.state = self.root / 'state'
        self.pipe = r'\\.\pipe\unit-product-purpose'
        self.purpose_path = self.root / 'product-acceptance-purpose.json'
        self.contract: JsonObject = {'schema': 'ck3-mod-acceptance-product-case-v1',
            'product': 'unit-product', 'case_id': 'core', 'execution_purpose': 'product_acceptance',
            'maximum_natural_days': 400}
        self.contract_path = self.root / 'contract.json'
        write(self.contract_path, self.contract)
        self.prepared_path = self.root / 'prepared.json'
        self.prepared: JsonObject = json_object({'schema': 'ck3-mod-acceptance-prepared-case-v1',
            'product': 'unit-product', 'case': 'core', 'runtime_manifest': {'unit': True},
            'case_inputs': {'unit': True}, 'contract': pin(self.contract_path)})
        write(self.prepared_path, self.prepared)
        self.frozen_path = self.root / 'frozen-argv.json'
        self.frozen: JsonObject = {'run_id': 'unit-run', 'mod_key': 'unit-product', 'cell': 'core',
            'state_dir': str(self.state), 'runtime_manifest': {'unit': True},
            'identity_allocation': {'machine_id': 'authored-unit-machine'},
            'argv': [sys.executable, '-B', '-X', 'utf8', str(HOST),
                '--agent-source-root', str(REPO), '--state-dir', str(self.state), '--bridge-pipe', self.pipe,
                '--output', str(self.root / 'native-report.json'), '--saved-campaign-save', 'authored-not-loaded.ck3',
                '--product-acceptance-purpose', str(self.purpose_path)]}
        write(self.frozen_path, self.frozen)
        self.context_path = self.root / 'root-reviewed-context.json'
        self.context: JsonObject = json_object({'schema': 'ck3-mod-acceptance-run-context-v1',
            'run_id': 'unit-run', 'run_dir': str(self.root), 'product': 'unit-product', 'case': 'core',
            'case_inputs': {'unit': True}, 'reviewer': '/root',
            'prepared_case': pin(self.prepared_path), 'frozen_argv': pin(self.frozen_path)})
        self.refresh_context()

    def refresh_context(self) -> None:
        write(self.context_path, self.context)
        write(self.root / 'ready-context.json', {'run_id': 'unit-run',
            'prepared_case': self.context['prepared_case'], 'frozen_argv': self.context['frozen_argv']})

    def produce(self) -> None:
        write_product_acceptance_purpose_v1(self.purpose_path, self.context_path,
            host_path=HOST, state_dir=self.state, bridge_pipe=self.pipe)

    def consume(self) -> ProductAcceptanceClockV1:
        spec = importlib.util.spec_from_file_location('actual_product_purpose_host', HOST)
        if spec is None or spec.loader is None:
            raise ValueError('Actual host unavailable')
        module: ModuleType = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loader = getattr(module, 'load_product_acceptance_clock_v1')
        if not isinstance(loader, Loader):
            raise ValueError('Actual host purpose consumer absent')
        result = loader(argparse.Namespace(product_acceptance_purpose=self.purpose_path,
            output=self.root / 'native-report.json', state_dir=self.state, bridge_pipe=self.pipe,
            agent_source_root=REPO, saved_campaign_server=True, frontend_fixture_start_policy=None))
        if not isinstance(result, ProductAcceptanceClockV1):
            raise ValueError('Actual host did not bind the purpose')
        return result

    def frame(self, day: int = 0) -> dict[str, object]:
        return {'date_raw': 53144328 + 24 * day, 'paused': True, 'map_ready': True,
            'played_character': {'character_id': 31254}, 'diagnostics': {
                'pipe_name': self.pipe, 'bridge_pid': 29452, 'connection_generation': 1}}

    def test_real_producer_host_loader_and_original_driver_dispatch_beyond_r05_thirty_days(self) -> None:
        self.produce()
        clock = self.consume()
        self.assertEqual(clock.purpose.maximum_natural_days, 400)
        self.assertEqual(clock.purpose.machine_id, 'authored-unit-machine')
        driver = actual_recording_driver(clock)
        first = driver._campaign_advance_deadline_v1(self.frame(), 53144352)
        self.assertIsNotNone(first)
        after_thirty = driver._campaign_advance_deadline_v1(self.frame(31), 53144328 + 32 * 24)
        self.assertIsNotNone(after_thirty)
        with self.assertRaisesRegex(ValueError, 'rewound'):
            driver._campaign_advance_deadline_v1(self.frame(30), 53144328 + 31 * 24)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            driver._campaign_advance_deadline_v1(self.frame(400), 53144328 + 401 * 24)
        with self.assertRaisesRegex(ValueError, 'R05 AUTO'):
            driver.cap_campaign_advance_plan_v1({})
        with self.assertRaises(FileExistsError):
            self.produce()

    def test_unbound_purpose_preserves_the_actual_r0001_refusal_and_r05_guard(self) -> None:
        driver = actual_recording_driver(None)
        with self.assertRaisesRegex(RuntimeError, 'Actual independent progress scope absent'):
            driver._campaign_advance_deadline_v1(self.frame(), 53144352)
        with self.assertRaisesRegex(RuntimeError, 'bind before AUTO'):
            driver.cap_campaign_advance_plan_v1({})

    def test_changed_original_root_review_unknown_fields_and_wrong_purpose_are_rejected(self) -> None:
        original = copy.deepcopy(self.context)
        for key, value in [('reviewer', '/child'), ('case', 'other')]:
            self.context = copy.deepcopy(original)
            self.context[key] = value
            self.refresh_context()
            with self.assertRaises(ValueError):
                self.produce()
            self.assertFalse(self.purpose_path.exists())
        self.context = original
        self.refresh_context()
        self.produce()
        baseline = json_object(json.loads(self.purpose_path.read_bytes()))
        changes: list[tuple[str, JsonValue]] = [('purpose', 'r05'), ('extra', True), ('machine_id', 'other')]
        for key, changed_value in changes:
            row = copy.deepcopy(baseline)
            row[key] = changed_value
            with self.assertRaises(ValueError):
                product_acceptance_purpose_v1(row, purpose_path=self.purpose_path,
                    host_path=HOST, state_dir=self.state, bridge_pipe=self.pipe)
        self.context_path.write_bytes(self.context_path.read_bytes() + b' ')
        with self.assertRaises(ValueError):
            self.consume()

    def test_actual_public_run_produces_purpose_before_the_existing_reviewed_launcher(self) -> None:
        from ck3_mod_acceptance import Selection
        self.context['keeper_root'] = str(self.root / 'keeper')
        self.context['steam_offline_receipt'] = str(self.root / 'offline-not-launched.json')
        self.refresh_context()
        launcher = self.root / 'authored-launcher-not-executed.py'
        launcher.write_text('# Never executed by this non-game regression.\n', encoding='utf-8')
        selection = object.__new__(Selection)
        selection.context, selection.context_path = self.context, self.context_path
        selection.argv = strings_field(self.frozen, 'argv')
        selection.runtime_environment = {}
        selection.run_dir, selection.state_dir = self.root, self.state
        selection.runtime_path = self.root / 'runtime.json'
        selection.runtime = {'reviewed_launcher': pin(launcher)}
        selection.locations = {'python': Path(sys.executable), 'repo_root': REPO}
        selection.adapter_path = REPO / 'tools/ck3_mod_acceptance_cases/generic_product_adapter.py'

        def observed_launch(argv: list[str], *, cwd: Path, env: dict[str, str], check: bool) -> subprocess.CompletedProcess[str]:
            self.assertTrue(self.purpose_path.is_file())
            self.assertEqual(self.consume().purpose.maximum_natural_days, 400)
            return subprocess.CompletedProcess(argv, 1)

        with patch.object(selection, 'preflight', return_value={'blockers': []}), patch('ck3_mod_acceptance.subprocess.run', side_effect=observed_launch):
            result = selection.run()
        self.assertEqual(result['launcher_exit_code'], 1)
        self.assertEqual(result['business_acceptance'], 'NOT_ASSESSED')

    def test_budget_bool_float_missing_null_and_cross_native_identity_refuse(self) -> None:
        for value in [True, 400.0, None, -1, 401]:
            self.contract['maximum_natural_days'] = value
            write(self.contract_path, self.contract)
            self.prepared['contract'] = json_object(pin(self.contract_path))
            write(self.prepared_path, self.prepared)
            self.context['prepared_case'] = json_object(pin(self.prepared_path))
            self.refresh_context()
            with self.assertRaises(ValueError):
                self.produce()
        self.contract['maximum_natural_days'] = 400
        write(self.contract_path, self.contract)
        self.prepared['contract'] = json_object(pin(self.contract_path))
        write(self.prepared_path, self.prepared)
        self.context['prepared_case'] = json_object(pin(self.prepared_path))
        self.refresh_context()
        self.produce()
        clock = self.consume()
        clock.deadline(self.frame(), 53144352, r05_scope_bound=False)
        with self.assertRaises(ValueError):
            clock.deadline(self.frame(), 53144376, r05_scope_bound=False)
        with self.assertRaises(ValueError):
            clock.deadline(self.frame(), 53144352, r05_scope_bound=True)
        changed = self.frame(1)
        changed['played_character'] = {'character_id': 99}
        with self.assertRaises(ValueError):
            clock.deadline(changed, 53144376, r05_scope_bound=False)


if __name__ == '__main__':
    unittest.main()
