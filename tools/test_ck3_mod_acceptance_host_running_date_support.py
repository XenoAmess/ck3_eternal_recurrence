"""Global host projection + actual R27 clock gap; no game or process control."""
from __future__ import annotations

import ast
import asyncio
import copy
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Protocol, runtime_checkable
import unittest
from unittest.mock import patch

from ck3_mod_acceptance_background_types import (
    FilePin, JsonObject, HostRunningDateProjectionV1, json_object,
    RUNNING_DATE_BASE_HOST_SHA256, RUNNING_DATE_SUPPORT_RELATIVE,
    project_running_date_host, validate_host_running_date_projection,
)
from ck3_mod_acceptance_build_runtime import build_host_running_date_support, HostSupportStorageV1
from ck3_mod_acceptance import Selection
from ck3_mod_acceptance_launcher import validate_frozen_host_running_date_support


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / 'fixtures/host-running-date-support'
MACHINE = 'authored-host-support-test-machine'


def pin(path: Path) -> FilePin:
    raw = path.read_bytes()
    return FilePin(path=str(path.resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def write_json(path: Path, value: object) -> None:
    path.write_bytes((json.dumps(value, allow_nan=False, ensure_ascii=False) + '\n').encode('utf-8'))


def object_row(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError('Object required')
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError('String key required')
        result[key] = item
    return result


@runtime_checkable
class HostAPI(Protocol):
    def campaign_pause_frame_binding(self, snapshot: object, *, allow_running: bool = False) -> dict[str, object]: ...
    def _campaign_pending_running_date(self, source: dict[str, object], snapshot: dict[str, object],
                                       error: RuntimeError) -> dict[str, object]: ...


@runtime_checkable
class RunningHarness(Protocol):
    actions: list[str]
    async def run(self) -> dict[str, object]: ...


@runtime_checkable
class RunningTestModule(Protocol):
    def Harness(self, observations: list[dict[str, object]], *, timeout: float = 2.0,
                plain: bool = False) -> RunningHarness: ...


def load_guard_and_classifier(host: Path) -> HostAPI:
    """Extract the actual production definitions, preserving their import route."""
    names = {'_campaign_pause_frame_rejection_detail', 'campaign_pause_frame_binding', '_campaign_pending_running_date'}
    tree = ast.parse(host.read_bytes())
    nodes: list[ast.stmt] = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes if isinstance(node, ast.FunctionDef)} != names:
        raise ValueError('Actual host guard/classifier closure missing')
    module = ModuleType('authored_host_replay')
    module.__file__ = str(host)
    module.__dict__['copy'] = copy
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(host), 'exec'), module.__dict__)
    if not isinstance(module, HostAPI):
        raise ValueError('Actual host API closure differs')
    return module


class HostRunningDateSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='common-host-support-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'canonical-source'
        canonical = self.source / RUNNING_DATE_SUPPORT_RELATIVE
        canonical.parent.mkdir(parents=True)
        canonical.write_bytes((HERE.parent / RUNNING_DATE_SUPPORT_RELATIVE).read_bytes())
        self.canonical = canonical
        self.git('init', '-q')
        self.git('-c', 'core.autocrlf=false', 'add', '.')
        self.git('-c', 'user.name=authored-fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'authored canonical helper fixture')
        self.commit = self.git('rev-parse', 'HEAD')
        self.base_host = self.root / 'immutable-base-host.py'
        self.base_raw = gzip.decompress((FIXTURES / 'base-host.py.txt.gz').read_bytes())
        self.base_host.write_bytes(self.base_raw)
        self.assertEqual(hashlib.sha256(self.base_raw).hexdigest(), RUNNING_DATE_BASE_HOST_SHA256)
        self.manifest_path = self.root / 'manifest.base.json'
        self.base_runtime_path = self.root / 'runtime.base.json'
        self.old_sdk = self.root / 'old-sdk'
        self.old_sdk.mkdir()
        self.sdk_sentinel = self.old_sdk / 'unchanged-sdk.txt'
        self.sdk_sentinel.write_bytes(b'old selected SDK; never imported or changed by support')
        self.paths: JsonObject = {'host': str(self.base_host), 'source_root': str(self.old_sdk)}
        for key in ('source_index', 'native_source_index', 'dll', 'injector', 'initial'):
            path = self.root / (key + '.data')
            path.write_bytes(b'{}')
            self.paths[key] = str(path)
        self.manifest: JsonObject = {'schema': 'ck3-mod-acceptance-shared-runtime-v1', 'machine_id': MACHINE,
            'host': {'path_key': 'host', 'bytes': pin(self.base_host)['bytes'], 'sha256': pin(self.base_host)['sha256']},
            'source_root': {'path_key': 'source_root'}, 'capabilities': {}}
        for key in ('source_index', 'native_source_index'):
            reference = pin(Path(str(self.paths[key])))
            self.manifest[key] = {'path_key': key, 'bytes': reference['bytes'], 'sha256': reference['sha256']}
        native: JsonObject = {}
        for key in ('dll', 'injector'):
            reference = pin(Path(str(self.paths[key])))
            native[key] = {'path_key': key, 'bytes': reference['bytes'], 'sha256': reference['sha256']}
        self.manifest['native'] = native
        self.locations = {key: self.root / key for key in ('repo', 'game', 'userdir', 'artifacts')}
        for path in self.locations.values():
            path.mkdir()
        game_exe = self.locations['game'] / 'binaries/ck3.exe'
        game_exe.parent.mkdir()
        game_exe.write_bytes(b'authored game identity; never executed')
        self.manifest['game'] = {'version': 'authored', 'exe_sha256': pin(game_exe)['sha256']}
        write_json(self.manifest_path, self.manifest)
        self.base_runtime: JsonObject = {'schema': 'ck3-mod-acceptance-runtime-v1', 'machine_id': MACHINE,
            'python': sys.executable, 'repo_root': str(self.locations['repo']),
            'game_dir': str(self.locations['game']), 'userdir_root': str(self.locations['userdir']),
            'artifacts_root': str(self.locations['artifacts']), 'manifest': json_object(pin(self.manifest_path)),
            'paths': self.paths}
        write_json(self.base_runtime_path, self.base_runtime)
        self.grant_path = self.root / 'storage.actual.json'
        current = datetime.now(timezone.utc)
        self.grant: JsonObject = {'schema': 'ck3-shared-host-support-storage-v1', 'machine_id': MACHINE,
            'approved_root': str(self.root / 'global-runtime'), 'observed_at_utc': current.isoformat(),
            'expires_at_utc': (current + timedelta(minutes=10)).isoformat(),
            'max_write_bytes': 2 * 1024 * 1024, 'required_free_bytes': 1,
            'volume_used_cap_bytes': shutil.disk_usage(self.root).total}
        write_json(self.grant_path, self.grant)
        self.output = self.root / 'global-runtime/host-support-v1'

    def git(self, *arguments: str) -> str:
        return subprocess.run(['git', *arguments], cwd=self.source, capture_output=True,
                               check=True).stdout.decode('utf-8').strip()

    def build(self) -> Path:
        with patch('ck3_live_run_id.current_machine_id', return_value=MACHINE):
            result = build_host_running_date_support(self.base_runtime_path, self.source, self.commit,
                                                     self.output, self.grant_path)
        return Path(result['path'])

    def projection(self) -> JsonObject:
        return json_object(json.loads((self.output / 'host-support-projection.json').read_bytes()))

    def test_real_builder_to_validator_preserves_sdk_native_game_and_original_host(self) -> None:
        runtime_path = self.build()
        runtime = json_object(json.loads(runtime_path.read_bytes()))
        manifest = json_object(json.loads((self.output / 'manifest.json').read_bytes()))
        for key in ('native', 'game', 'source_root', 'source_index', 'native_source_index'):
            self.assertEqual(manifest[key], self.manifest[key])
        self.assertEqual(self.base_host.read_bytes(), self.base_raw)
        self.assertEqual(self.sdk_sentinel.read_bytes(), b'old selected SDK; never imported or changed by support')
        self.assertEqual((self.output / 'campaign_running_date_publication_v1.py').read_bytes(), self.canonical.read_bytes())
        self.assertEqual(json_object(runtime['paths'])['source_root'], str(self.old_sdk))
        references = validate_host_running_date_projection(manifest['host_support_projection'],
                                                           self.output / 'shared-host.py', MACHINE)
        self.assertEqual(len(references), 7)
        self.assertEqual(HostRunningDateProjectionV1.parse(self.projection()).to_json(), self.projection())
        with self.assertRaises(ValueError):
            self.build()

    def test_actual_r27_failure_replays_through_unchanged_guard_then_new_absolute_import(self) -> None:
        self.build()
        actual = json_object(json.loads((FIXTURES / 'r27-failure.actual.json').read_bytes()))
        before = object_row(json_object(actual['before_running_frame'])['snapshot'])
        failed = object_row(json_object(actual['failed_running_frame'])['snapshot'])
        retained = copy.deepcopy(failed)
        old = load_guard_and_classifier(self.base_host)
        source = old.campaign_pause_frame_binding(before, allow_running=True)
        try:
            old.campaign_pause_frame_binding(failed, allow_running=True)
        except RuntimeError as error:
            detail = json_object(getattr(error, 'ck3_campaign_pause_frame_diagnostic'))
            self.assertEqual(detail['first_failed_condition'], 31)
            conditions = detail['conditions']
            if not isinstance(conditions, list):
                self.fail('Actual rejected conditions missing')
            self.assertEqual([json_object(row)['index'] for row in conditions if json_object(row)['failed']], [31])
            with self.assertRaises(RuntimeError) as frozen:
                old._campaign_pending_running_date(source, failed, error)
            self.assertIs(frozen.exception, error)
            shadow = ModuleType('campaign_running_date_publication_v1')
            with patch.dict(sys.modules, {'campaign_running_date_publication_v1': shadow}):
                current = load_guard_and_classifier(self.output / 'shared-host.py')
                pending = current._campaign_pending_running_date(source, failed, error)
                loaded = sys.modules['_ck3_shared_running_date_support_v1']
            self.assertEqual(pending['date'], 53144352)
            self.assertEqual(pending['pending_mailbox_date'], 53144328)
            self.assertEqual(Path(str(loaded.__file__)).resolve(),
                             (self.output / 'campaign_running_date_publication_v1.py').resolve())
            with self.assertRaises(RuntimeError):
                current.campaign_pause_frame_binding(failed, allow_running=True)
        else:
            self.fail('The actual R27 rejected frame must never earn admission')
        self.assertEqual(failed, retained)

    def test_same_global_host_and_complete_source_pins_reach_two_product_selections(self) -> None:
        runtime_path = self.build()
        products_path = self.root / 'products.json'
        case: JsonObject = {'id': 'core', 'status': 'ready', 'startup': {'mode': 'workshop_cache', 'state_dir': '{run_dir}/state'},
            'initial_plan': self.paths['initial'], 'required_mcp_tools': [], 'phases': [],
            'budgets': {'command_timeout': 300, 'readiness_timeout': 900, 'timeout': 4800, 'poll_interval': .5, 'hold_seconds': 900}}
        write_json(products_path, {'schema': 'ck3-mod-acceptance-products-v1',
                                   'products': {'first': {'cases': [case]}, 'second': {'cases': [case]}}})
        first = Selection(runtime_path, products_path, 'first', 'core')
        second = Selection(runtime_path, products_path, 'second', 'core')
        self.assertEqual(first.argv[4], second.argv[4])
        self.assertEqual(first.argv[4], str((self.output / 'shared-host.py').resolve()))
        pinned = {str(path.resolve()) for path, _ in first.required_pins}
        for reference in validate_host_running_date_projection(pin(self.output / 'host-support-projection.json'),
                                                               self.output / 'shared-host.py', MACHINE):
            self.assertIn(reference['path'], pinned)

    def test_real_projection_to_frozen_launcher_requires_every_support_pin(self) -> None:
        self.build()
        receipt = pin(self.output / 'host-support-projection.json')
        refs = validate_host_running_date_projection(receipt, self.output / 'shared-host.py', MACHINE)
        files: JsonObject = {reference['path']: {'bytes': reference['bytes'], 'sha256': reference['sha256']}
                             for reference in refs}
        frozen: JsonObject = {'runtime_manifest': json_object(pin(self.output / 'manifest.json')),
                              'identity_allocation': {'machine_id': MACHINE}}
        validate_frozen_host_running_date_support(frozen, files, self.output / 'shared-host.py')
        for reference in refs:
            missing = {key: value for key, value in files.items() if key != reference['path']}
            with self.subTest(missing=reference['path']), self.assertRaises(ValueError):
                validate_frozen_host_running_date_support(frozen, missing, self.output / 'shared-host.py')

    def test_actual_r27_gap_then_authored_coherent_frames_use_existing_producer_once(self) -> None:
        """Retained failure is real; later full frames are explicitly authored."""
        self.build()
        actual = json_object(json.loads((FIXTURES / 'r27-failure.actual.json').read_bytes()))
        before = object_row(json_object(actual['before_running_frame'])['snapshot'])
        failed = object_row(json_object(actual['failed_running_frame'])['snapshot'])
        retained = copy.deepcopy(failed)
        start = int(str(before['date_raw']))
        failed_mailbox = object_row(object_row(object_row(failed['diagnostics'])['last_heartbeat'])['main_thread_query_mailbox_v1'])

        def authored_frame(revision: int, *, date: int = start, paused: bool = False,
                           mailbox_date: int | None = None) -> dict[str, object]:
            frame = copy.deepcopy(before)
            initial = revision == 10  # Existing inert harness's preflight sentinel.
            frame['revision'] = before['revision'] if initial else revision
            frame['native_revision'] = before['native_revision'] if initial else revision - 1
            frame['snapshot_id'] = 'native:' + str(frame['native_revision'])
            frame['date_raw'], frame['paused'] = date, paused
            diagnostics = object_row(frame['diagnostics'])
            heartbeat = object_row(diagnostics['last_heartbeat'])
            mailbox = object_row(heartbeat['main_thread_query_mailbox_v1'])
            mailbox.update(date_raw=date if mailbox_date is None else mailbox_date, paused=paused,
                           ready=paused, consecutive_verified=2 if paused else 0,
                           paused_main_thread_observed=paused)
            if not initial:
                mailbox['owner_verified_pump_epochs'] = int(str(failed_mailbox['owner_verified_pump_epochs'])) + revision
            heartbeat['main_thread_query_mailbox_v1'] = mailbox
            diagnostics['last_heartbeat'] = heartbeat
            frame['diagnostics'] = diagnostics
            return frame

        source = HERE.parent / 'ck3_autonomous_player/tests/unit/test_campaign_running_date_convergence.py'
        spec = importlib.util.spec_from_file_location('authored_r27_inert_producer', source)
        if spec is None or spec.loader is None:
            self.fail('Existing inert producer tests unavailable')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'XAR_PAUSE_TEST_HOST': str(self.output / 'shared-host.py')}):
            spec.loader.exec_module(module)
        if not isinstance(module, RunningTestModule):
            self.fail('Existing inert producer contract changed')
        with patch.object(module, 'actual_frame', authored_frame):
            harness = module.Harness([failed, authored_frame(8, date=start + 24),
                                      authored_frame(9, date=start + 24, paused=True)])
            result = asyncio.run(harness.run())
        self.assertEqual(result['elapsed_hours'], 24)
        self.assertIs(result['requested_interval_complete'], True)
        self.assertIs(object_row(result['after'])['paused'], True)
        self.assertEqual(harness.actions, ['pause-map', 'set-speed-1', 'resume-map', 'pause-map'])
        with patch.object(module, 'actual_frame', authored_frame):
            never_coherent = module.Harness([failed], timeout=.3)
            with self.assertRaises(TimeoutError):
                asyncio.run(never_coherent.run())
        self.assertEqual(never_coherent.actions, ['pause-map', 'set-speed-1', 'resume-map'])
        self.assertEqual(failed, retained)

    def test_exact_schema_types_times_and_serialization_roundtrip(self) -> None:
        self.build()
        row = self.projection()
        invalid: list[JsonObject] = [{**row, 'unknown': True}, {key: value for key, value in row.items() if key != 'observed_at_utc'}]
        for bad in (None, True, 1.0, '', '2026-10-23', '2026-10-23T19:00:00', '2026-10-23T19:00:00+01:00',
                    '2999-01-01T00:00:00Z'):
            invalid.append(json_object({**row, 'observed_at_utc': bad}))
        for bad in (True, 1.0, -1, None):
            helper = json_object(row['helper'])
            invalid.append({**row, 'helper': {**helper, 'bytes': bad}})
        for bad_row in invalid:
            with self.subTest(row=bad_row), self.assertRaises(ValueError):
                HostRunningDateProjectionV1.parse(bad_row)
        self.assertEqual(HostRunningDateProjectionV1.parse(json.loads(json.dumps(row))).to_json(), row)

    def test_corruption_wrong_route_and_other_host_edits_fail_before_use(self) -> None:
        self.build()
        receipt_path = self.output / 'host-support-projection.json'
        host = self.output / 'shared-host.py'
        reference = pin(receipt_path)
        with self.assertRaises(ValueError):
            validate_host_running_date_projection(reference, self.base_host, MACHINE)
        with self.assertRaises(ValueError):
            validate_host_running_date_projection(reference, host, 'wrong-machine')
        original = host.read_bytes()
        host.write_bytes(original + b'\n# undeclared other change\n')
        with self.assertRaises(ValueError):
            validate_host_running_date_projection(reference, host, MACHINE)
        host.write_bytes(original)
        helper = self.output / 'campaign_running_date_publication_v1.py'
        helper.write_bytes(helper.read_bytes() + b'\n# changed\n')
        with self.assertRaises(ValueError):
            validate_host_running_date_projection(reference, host, MACHINE)
        with self.assertRaises(ValueError):
            project_running_date_host(self.base_raw + b'\n', pin(self.canonical))

    def test_storage_integer_and_expiry_contract_does_not_grant_extra_budget(self) -> None:
        for key, value in (('max_write_bytes', True), ('required_free_bytes', 1.0),
                           ('volume_used_cap_bytes', None), ('expires_at_utc', '2000-01-01T00:00:00Z')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                HostSupportStorageV1.parse({**self.grant, key: value}, MACHINE)
        write_json(self.grant_path, {**self.grant, 'max_write_bytes': 1})
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
