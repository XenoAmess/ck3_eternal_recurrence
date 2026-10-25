"""Original R0002 shapes -> real closure producer -> public predecessor branch.

Relocation, resealing, projected frozen files and absent processes are authored
inputs. The retained originals are independently checked on their actual machine.
"""
from __future__ import annotations

import argparse
import ast
import copy
import contextlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Literal, Protocol, runtime_checkable
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')]
import ck3_live_run_id as ids
import ck3_mod_acceptance_allocate as allocation
import ck3_mod_acceptance_unrun as unrun
import ck3_mod_acceptance as entry
from ck3_mod_acceptance_background_types import JsonObject, JsonValue, file_pin, json_object, object_field, text_field
from ck3_mod_acceptance_fresh_machine_bootstrap import MachineBinding


@runtime_checkable
class _PublicDispatch(Protocol):
    def __call__(self, args: argparse.Namespace) -> object: ...


@runtime_checkable
class _ReleaseReader(Protocol):
    def __call__(self, path: Path) -> object: ...


class OfflineTTLUnrunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix='AUTHORED_R2_TTL_')
        self.addCleanup(self.temp.cleanup)
        # Hosted Windows TEMP can use an 8.3 alias. The real producer pins
        # resolved paths, so authored frozen-file keys must use that same root.
        self.root = Path(self.temp.name).resolve()
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
        self.leaves['prepared_case'] = prepared
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

    @staticmethod
    def epoch_decimal(stamp: datetime) -> str:
        elapsed = stamp - datetime(1970, 1, 1, tzinfo=timezone.utc)
        return str(Decimal(elapsed.days * 86400 + elapsed.seconds)
                   + Decimal(elapsed.microseconds) / Decimal(1000000))

    def author_r0013_public_receipts(self) -> None:
        """Use R0013's recorded-Popen shape with explicitly authored identities."""
        for key, pid, birth_offset, code in (
                ('run_result', 26172, timedelta(microseconds=-7024), 2),
                ('allocator_result', 10128, timedelta(microseconds=1216), 0)):
            original = object_field(self.leaves, key)
            started = datetime.fromisoformat(text_field(original, 'started_at_utc'))
            finished = original.get('finished_at_utc', original.get('observed_at_utc'))
            value: JsonObject = {'machine_id': self.machine, 'argv': original['argv'], 'pid': pid,
                'process_create_time_seconds': self.epoch_decimal(started + birth_offset),
                'started_at_utc': started.isoformat(), 'original_wait_pending': False,
                'original_wait_returncode': code, 'finished_at_utc': finished}
            self.write(self.path(key), value)

    def author_plain_stop(self, raw: bytes | None = None, *, mtime_ns: int | None = None) -> JsonObject:
        """Author an old STOP shape and filesystem time; never historical evidence."""
        original = object_field(self.leaves, 'keeper_stop')
        observed = text_field(original, 'observed_at_utc')
        path = self.path('keeper_stop')
        path.write_bytes(raw if raw is not None else
            ('Root closed pre-intent offline TTL refusal; no host/native launched ' + observed).encode('utf-8'))
        if mtime_ns is None:
            stamp = datetime.fromisoformat(observed)
            mtime_ns = int(Decimal(self.epoch_decimal(stamp)) * Decimal(1000000000)) + 360000
        os.utime(path, ns=(path.stat().st_atime_ns, mtime_ns))
        return self.actual_pin(path)

    def validate_produced(self, result: unrun.UnrunBundleReport) -> JsonObject:
        reader: object = allocation.read_failed_runtime_release
        if not isinstance(reader, _ReleaseReader):
            self.fail('Actual canonical release reader unavailable')
        with patch.object(ids, 'current_machine_id', return_value=self.machine), patch.object(ids,
                'default_state_root', return_value=self.id_root), patch.object(allocation,
                'runtime_process_inventory', return_value={'blockers': []}):
            return unrun.validate_pre_intent_offline_ttl_refusal(self.live, self.frozen,
                Path(result['bundle']['path']), self.keeper,
                reader(Path(result['previous_release']['path'])),
                self.packet, self.args.next_state)

    def bind_authored_runtime_manifest(self, manifest: JsonObject) -> None:
        reference = self.write(self.root / 'recovery-runtime-manifest.json', manifest)
        self.frozen['runtime_manifest'] = reference
        prepared = object_field(self.leaves, 'prepared_case')
        prepared['runtime_manifest'] = reference
        self.leaves['prepared_case'] = prepared
        self.prepared_pin = self.write(self.path('prepared_case'), prepared)
        for key in ('ready', 'allocated_context', 'reviewed_context'):
            row = object_field(self.leaves, key)
            row['prepared_case'] = self.prepared_pin
            self.leaves[key] = row
        self.reseal_frozen()

    @staticmethod
    def authored_git(repo: Path, *arguments: str) -> str:
        return subprocess.run(['git', '-C', str(repo), *arguments], check=True,
            capture_output=True, text=True, encoding='utf-8', timeout=30).stdout.strip()

    def author_recovery_git_sources(self) -> tuple[Path, str, dict[Path, bytes]]:
        """A tiny real Git history represents the two old reader source paths."""
        repo = self.root / 'authored-recovery-source'
        (repo / 'tools').mkdir(parents=True)
        originals = {repo / 'tools/ck3_mod_acceptance_unrun.py': b'# authored original recovery reader\n',
                     repo / 'tools/ck3_mod_acceptance_allocate.py': b'# authored original allocator\n',
                     repo / 'tools/ordinary_input.py': b'# authored immutable ordinary input\n'}
        for path, raw in originals.items():
            path.write_bytes(raw)
        self.authored_git(repo, 'init', '-q')
        self.authored_git(repo, 'config', 'core.autocrlf', 'false')
        self.authored_git(repo, 'add', 'tools')
        self.authored_git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                          '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Authored original recovery sources')
        commit = self.authored_git(repo, 'rev-parse', 'HEAD')
        files = object_field(self.frozen, 'files')
        for path in originals:
            reference = self.actual_pin(path)
            files[str(path.resolve())] = {key: reference[key] for key in ('bytes', 'sha256')}
        self.frozen['files'], self.frozen['source_root'] = files, str(repo.resolve())
        self.bind_authored_runtime_manifest({'machine_id': self.machine, 'source_commit': commit})
        for path in originals:
            if path.name != 'ordinary_input.py':
                path.write_bytes(originals[path] + b'# authored current recovery fix\n')
        return repo, commit, originals

    def public_predecessor(self, result: unrun.UnrunBundleReport) -> JsonObject:
        """Execute the actual predecessor branch before identity/SCREEN mutation."""
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
        return json_object(namespace['closure'])

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
        self.assertEqual(self.public_predecessor(result)['mode'], result['validation']['mode'])

    def test_r0013_original_wait_plain_stop_producer_and_public_consumer_roundtrip(self) -> None:
        self.author_r0013_public_receipts()
        self.author_plain_stop()
        originals = {key: self.path(key).read_bytes() for key in ('run_result', 'allocator_result', 'keeper_stop')}
        result = self.produce()
        self.assertEqual(self.public_predecessor(result)['mode'], result['validation']['mode'])
        self.assertEqual(self.validate_produced(result)['mode'], result['validation']['mode'])
        bundle = json_object(json.loads(Path(result['bundle']['path']).read_bytes()))
        observation = object_field(bundle, 'keeper_stop_file_observation')
        actual = self.path('keeper_stop').stat()
        self.assertEqual(observation['schema'], 'ck3-original-plain-ttl-stop-file-v1')
        self.assertEqual(observation['file'], self.actual_pin(self.path('keeper_stop')))
        self.assertEqual(observation['device_id_decimal'], str(actual.st_dev))
        self.assertEqual(observation['file_id_decimal'], str(actual.st_ino))
        self.assertEqual(observation['mtime_ns_decimal'], str(actual.st_mtime_ns))
        self.assertEqual(observation['original_stop_at_utc'], object_field(self.leaves, 'keeper_stop')['observed_at_utc'])
        for key, raw in originals.items():
            self.assertEqual(self.path(key).read_bytes(), raw)

    def test_original_popen_wait_exact_fields_types_modes_and_both_start_orders(self) -> None:
        self.author_r0013_public_receipts()
        for key, mode, code in (('run_result', 'run', 2), ('allocator_result', 'allocate', 0)):
            operation: Literal['run', 'allocate'] = 'run' if mode == 'run' else 'allocate'
            value = json_object(json.loads(self.path(key).read_bytes()))
            self.assertEqual(unrun._ttl_public_exit(value, self.machine, operation, code), value['argv'])
            started = datetime.fromisoformat(text_field(value, 'started_at_utc'))
            for offset in (-1000, 1216):
                changed = {**value, 'process_create_time_seconds': self.epoch_decimal(started + timedelta(microseconds=offset))}
                self.assertEqual(unrun._ttl_public_exit(changed, self.machine, operation, code), value['argv'])
            invalid: list[tuple[str, JsonValue]] = [
                ('machine_id', 'wrong-machine'), ('pid', True), ('pid', 10128.0), ('pid', 0),
                ('pid', '10128'), ('original_wait_pending', True), ('original_wait_pending', 0),
                ('original_wait_returncode', True), ('original_wait_returncode', float(code)),
                ('original_wait_returncode', code + 1), ('process_create_time_seconds', 1792938472.469847),
                ('process_create_time_seconds', '1e9'), ('process_create_time_seconds', 'NaN'),
                ('process_create_time_seconds', '-1'), ('process_create_time_seconds', '01792938472'),
                ('process_create_time_seconds', ' 1792938472'), ('started_at_utc', '2026-10-24T11:03:27'),
                ('started_at_utc', '2026-10-25T00:00:00+00:00'),
                ('finished_at_utc', '2026-10-23T00:00:00+00:00'),
                ('finished_at_utc', '2026-10-24T11:05:12'),
                ('process_create_time_seconds', '9999999999.123456')]
            for field, bad in invalid:
                with self.subTest(mode=mode, field=field, bad=bad), self.assertRaises(ValueError):
                    unrun._ttl_public_exit({**value, field: bad}, self.machine, operation, code)
            for field in value:
                missing = {name: item for name, item in value.items() if name != field}
                with self.subTest(mode=mode, missing=field), self.assertRaises(ValueError):
                    unrun._ttl_public_exit(missing, self.machine, operation, code)
            with self.assertRaises(ValueError):
                unrun._ttl_public_exit({**value, 'exit_code': code}, self.machine, operation, code)
            wrong_mode: Literal['run', 'allocate'] = 'allocate' if operation == 'run' else 'run'
            with self.assertRaises(ValueError):
                unrun._ttl_public_exit(value, self.machine, wrong_mode, code)

    def test_json_stop_original_form_and_invalid_fields_are_preserved(self) -> None:
        path = self.path('keeper_stop')
        raw = path.read_bytes()
        original = object_field(self.leaves, 'keeper_stop')
        started = datetime.fromisoformat(text_field(object_field(self.leaves, 'run_result'), 'finished_at_utc'))
        finished = datetime.fromisoformat(text_field(object_field(self.leaves, 'keeper'), 'at_utc'))
        observed, observation = unrun._ttl_stop({'keeper_stop': self.actual_pin(path)}, path, self.machine, started, finished)
        self.assertEqual(observed, datetime.fromisoformat(text_field(original, 'observed_at_utc')))
        self.assertIsNone(observation)
        self.assertEqual(path.read_bytes(), raw)
        invalid: list[JsonObject] = [
            {**original, 'machine_id': 'wrong-machine'}, {**original, 'reason': 'Host launched'},
            {**original, 'observed_at_utc': None}, {**original, 'extra': False},
            {**original, 'observed_at_utc': started.replace(year=2025).isoformat()},
            {**original, 'observed_at_utc': finished.replace(year=2027).isoformat()}]
        invalid.extend({name: item for name, item in original.items() if name != key} for key in original)
        for changed in invalid:
            ref = self.write(path, changed)
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                unrun._ttl_stop({'keeper_stop': ref}, path, self.machine, started, finished)

    def test_plain_stop_body_time_mtime_and_read_identity_reject(self) -> None:
        path = self.path('keeper_stop')
        started = datetime.fromisoformat(text_field(object_field(self.leaves, 'run_result'), 'finished_at_utc'))
        finished = datetime.fromisoformat(text_field(object_field(self.leaves, 'keeper'), 'at_utc'))
        original_stop = text_field(object_field(self.leaves, 'keeper_stop'), 'observed_at_utc')
        prefix = 'Root closed pre-intent offline TTL refusal; no host/native launched '
        for text in ('no timestamp', prefix + original_stop + '\nextra',
                     'Root stopped after host/native launched ' + original_stop,
                     prefix + '2026-10-23T00:00:00+00:00', prefix + '2026-10-25T00:00:00+00:00',
                     prefix + '2026-10-24T11:05:11.674892'):
            ref = self.author_plain_stop(text.encode('utf-8'))
            with self.subTest(text=text), self.assertRaises(ValueError):
                unrun._ttl_stop({'keeper_stop': ref}, path, self.machine, started, finished)
        observed_ns = int(Decimal(self.epoch_decimal(datetime.fromisoformat(original_stop))) * Decimal(1000000000))
        for modified in (observed_ns - 1000,
                         int(Decimal(self.epoch_decimal(finished)) * Decimal(1000000000)) + 1000000000):
            ref = self.author_plain_stop(mtime_ns=modified)
            with self.subTest(modified=modified), self.assertRaises(ValueError):
                unrun._ttl_stop({'keeper_stop': ref}, path, self.machine, started, finished)
        ref = self.author_plain_stop()
        actual = path.stat()
        for field in ('st_dev', 'st_ino', 'st_mtime_ns', 'st_size'):
            changed = SimpleNamespace(**{key: getattr(actual, key) + (1 if key == field else 0)
                for key in ('st_dev', 'st_ino', 'st_mtime_ns', 'st_size')})
            with self.subTest(identity=field), patch.object(os, 'fstat', side_effect=[actual, changed]), self.assertRaises(ValueError):
                unrun._ttl_stop({'keeper_stop': ref}, path, self.machine, started, finished)
        with self.assertRaises(ValueError):
            unrun._ttl_stop({'keeper_stop': {**ref, 'extra': 1}}, path, self.machine, started, finished)

    def test_produced_stop_observation_rejects_missing_changed_types_and_later_mtime(self) -> None:
        self.author_r0013_public_receipts()
        self.author_plain_stop()
        result = self.produce()
        path = Path(result['bundle']['path'])
        original = json_object(json.loads(path.read_bytes()))
        observation = object_field(original, 'keeper_stop_file_observation')
        for field in ('device_id_decimal', 'file_id_decimal', 'mtime_ns_decimal', 'original_stop_at_utc'):
            for value in (None, True, 1, 'changed'):
                changed = {**original, 'keeper_stop_file_observation': {**observation, field: value}}
                self.write(path, changed)
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.validate_produced(result)
        self.write(path, {key: value for key, value in original.items() if key != 'keeper_stop_file_observation'})
        with self.assertRaises(ValueError):
            self.validate_produced(result)
        self.write(path, original)
        stop = self.path('keeper_stop')
        actual = stop.stat()
        os.utime(stop, ns=(actual.st_atime_ns, actual.st_mtime_ns + 1000))
        with self.assertRaises(ValueError):
            self.validate_produced(result)

    def test_reader_evolution_preserves_old_git_sources_and_checks_every_frozen_input(self) -> None:
        self.author_r0013_public_receipts()
        self.author_plain_stop()
        repo, commit, originals = self.author_recovery_git_sources()
        frozen_original = self.path('frozen').read_bytes()
        purpose_original = self.path('purpose').read_bytes()
        result = self.produce()
        bundle = json_object(json.loads(Path(result['bundle']['path']).read_bytes()))
        evolution = object_field(bundle, 'recovery_reader_evolution')
        self.assertEqual(evolution['schema'], 'ck3-prelaunch-recovery-reader-evolution-v1')
        self.assertEqual(evolution['original_source_commit'], commit)
        self.assertEqual(Path(text_field(evolution, 'source_root')), repo.resolve())
        self.assertEqual(evolution['original_runtime_manifest'], self.frozen['runtime_manifest'])
        rows = evolution['changed_recovery_sources']
        self.assertIsInstance(rows, list)
        if not isinstance(rows, list):
            self.fail('Authored source evolution rows required')
        self.assertEqual(len(rows), 2)
        relative_paths: set[str] = set()
        for value in rows:
            row = json_object(value)
            relative_paths.add(text_field(row, 'repository_relative_path'))
            original = Path(text_field(row, 'original_path'))
            retained = file_pin(row['original_snapshot'])
            self.assertEqual(Path(retained['path']).read_bytes(), originals[original])
            self.assertNotEqual(original.read_bytes(), originals[original])
            self.assertEqual(row['current_source'], self.actual_pin(original))
        self.assertEqual(relative_paths, {'tools/ck3_mod_acceptance_unrun.py', 'tools/ck3_mod_acceptance_allocate.py'})
        self.assertEqual(evolution['actual_recovery_reader'], self.actual_pin(Path(unrun.__file__)))
        self.assertEqual(evolution['actual_allocator_consumer'], self.actual_pin(Path(allocation.__file__)))
        from xar_autoplayer.bridge import runtime_input_contract_v1
        contract_source = runtime_input_contract_v1.__file__
        if not isinstance(contract_source, str):
            self.fail('Actual running input contract source required')
        self.assertEqual(evolution['actual_running_input_contract'], self.actual_pin(Path(contract_source)))
        facts = object_field(result['validation'], 'failure_cleanup')
        self.assertEqual(object_field(facts, 'original_inputs_verified')['immutable_inputs_checked'],
                         len(object_field(self.frozen, 'files')))
        self.assertEqual(self.validate_produced(result)['mode'], result['validation']['mode'])
        self.assertEqual(self.public_predecessor(result)['mode'], result['validation']['mode'])
        self.assertEqual(self.path('frozen').read_bytes(), frozen_original)
        self.assertEqual(self.path('purpose').read_bytes(), purpose_original)

    def test_reader_evolution_snapshot_and_descriptor_tampering_reject(self) -> None:
        self.author_recovery_git_sources()
        result = self.produce()
        path = Path(result['bundle']['path'])
        original = json_object(json.loads(path.read_bytes()))
        evolution = object_field(original, 'recovery_reader_evolution')
        rows = evolution['changed_recovery_sources']
        if not isinstance(rows, list):
            self.fail('Authored source evolution rows required')
        first = json_object(rows[0])
        snapshot = Path(file_pin(first['original_snapshot'])['path'])
        preserved = snapshot.read_bytes()
        snapshot.write_bytes(preserved + b'# tampered snapshot\n')
        with self.assertRaisesRegex(ValueError, 'Retained original recovery source differs'):
            self.validate_produced(result)
        snapshot.write_bytes(preserved)
        alterations: list[tuple[str, JsonValue]] = [
                ('original_source_commit', '0' * 40), ('source_root', str(self.root)),
                ('actual_recovery_reader', None), ('actual_allocator_consumer', None),
                ('actual_running_input_contract', None), ('changed_recovery_sources', [])]
        for field, value in alterations:
            self.write(path, {**original, 'recovery_reader_evolution': {**evolution, field: value}})
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'reader evolution differs'):
                self.validate_produced(result)
        self.write(path, {key: value for key, value in original.items() if key != 'recovery_reader_evolution'})
        with self.assertRaisesRegex(ValueError, 'reader evolution differs'):
            self.validate_produced(result)

    def test_reader_evolution_uses_exact_original_manifest_machine_and_git_commit(self) -> None:
        repo, commit, _ = self.author_recovery_git_sources()
        invalid_manifests: list[JsonObject] = [
                {'machine_id': 'other-machine', 'source_commit': commit},
                {'machine_id': self.machine, 'source_commit': True},
                {'machine_id': self.machine, 'source_commit': 'bad-commit'}]
        for serial, manifest in enumerate(invalid_manifests):
            self.bind_authored_runtime_manifest(manifest)
            self.args.output = self.root / ('wrong-manifest-' + str(serial))
            with self.subTest(manifest=manifest), self.assertRaises(ValueError):
                self.produce()
        self.authored_git(repo, 'add', 'tools')
        self.authored_git(repo, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                          '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Authored different reader sources')
        wrong_commit = self.authored_git(repo, 'rev-parse', 'HEAD')
        self.assertNotEqual(wrong_commit, commit)
        self.bind_authored_runtime_manifest({'machine_id': self.machine, 'source_commit': wrong_commit})
        self.args.output = self.root / 'wrong-git-blob'
        with self.assertRaisesRegex(ValueError, 'Original recovery Git blob'):
            self.produce()

    def test_reader_evolution_never_exempts_other_sources_launcher_or_gate(self) -> None:
        repo, _, originals = self.author_recovery_git_sources()
        ordinary = repo / 'tools/ordinary_input.py'
        for serial, path in enumerate((ordinary, self.path('launcher_source'), self.path('gate_source'))):
            raw = path.read_bytes()
            path.write_bytes(raw + b'# forbidden source drift\n')
            self.args.output = self.root / ('forbidden-source-' + str(serial))
            with self.subTest(source=path.name), self.assertRaises(ValueError):
                self.produce()
            path.write_bytes(raw)
        self.assertEqual(ordinary.read_bytes(), originals[ordinary])

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

    def test_noncanonical_temporary_root_reaches_the_real_source_guard(self) -> None:
        # A lexical alias reproduces the same key/ref mismatch on every runner;
        # no platform-specific short-name support or production bypass is needed.
        (self.root / 'alias-parent').mkdir()
        (self.root / 'alias-target').mkdir()
        alias = self.root / 'alias-parent' / '..' / 'alias-target'
        temporary = SimpleNamespace(name=str(alias), cleanup=lambda: None)
        harness = OfflineTTLUnrunTests()
        self.addCleanup(harness.doCleanups)
        with patch.object(tempfile, 'TemporaryDirectory', return_value=temporary):
            harness.setUp()
        self.assertEqual(harness.root, alias.resolve())
        result = harness.produce()
        facts = object_field(result['validation'], 'failure_cleanup')
        originals = object_field(facts, 'original_evidence')
        files = object_field(harness.frozen, 'files')
        for key in ('launcher_source', 'gate_source'):
            ref = file_pin(originals[key])
            self.assertEqual(object_field(files, ref['path']),
                             {'bytes': ref['bytes'], 'sha256': ref['sha256']})
        self.assertIs(facts['business_pass'], False)

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
                 '_ttl_public_exit', 'TTLStopFileObservation', '_ttl_stop',
                 'TTLRecoverySource', 'TTLReaderEvolution', '_ttl_recovery_sources',
                 'validate_pre_intent_offline_ttl_refusal', 'build_pre_intent_offline_ttl_bundle'}
        nodes = [copy.deepcopy(node) for node in source.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual(len(nodes), len(names))
        unit = ast.parse('''from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
from typing import Protocol, runtime_checkable, Literal, TypedDict
import argparse, hashlib, json, os, re, subprocess
from ck3_mod_acceptance import same_directory_control_peer
from ck3_mod_acceptance_background_types import FilePin, JsonObject, file_pin, json_object, object_field, text_field, strings_field
from ck3_mod_acceptance_unrun import SCHEMA, OFFLINE_TTL_KIND, UnrunBundleReport, _integer, _timestamp, _release_stages, _read, _write
''')
        unit.body.extend(nodes)
        temporary = self.root / 'exact_unrun_scope.py'
        temporary.write_text(ast.unparse(ast.fix_missing_locations(unit)), encoding='utf-8')
        with patch.dict(os.environ, {'MYPYPATH': os.pathsep.join((str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')))}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', os.devnull, str(temporary)])
        self.assertEqual(code, 0, stdout + stderr)

    def test_actual_allocator_counter_advance_keeps_only_immutable_snapshot_frozen(self) -> None:
        import test_ck3_mod_acceptance_r06_scope as public_fixture
        from xar_autoplayer.bridge.runtime_input_contract_v1 import validate_running_inputs
        self.author_r0013_public_receipts()
        self.author_plain_stop()
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


class OfflineTTLWriterLockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.harness = OfflineTTLUnrunTests()
        self.harness.setUp()
        self.addCleanup(self.harness.doCleanups)

    def writer_fixture(self) -> tuple[entry.Selection, argparse.Namespace, MachineBinding, unrun.UnrunBundleReport]:
        import test_ck3_mod_acceptance_r06_scope as public_fixture
        h = self.harness
        h.author_r0013_public_receipts()
        h.author_plain_stop()
        result = h.produce()
        current = public_fixture.PublicR06ScopeTests('runTest')
        current.setUp()
        self.addCleanup(current.doCleanups)
        current.prepare()
        runtime = json_object(json.loads(current.runtime_path.read_bytes()))
        runtime['allocation'] = {'lease_repo': text_field(h.frozen, 'source_root'),
            'task_bus': h.actual_pin(h.bus_root / 'bin/codex_task_bus.py')}
        h.write(current.runtime_path, runtime)
        selection = entry.Selection(current.runtime_path, current.products_path, 'war-episode04-r10',
            'r10-common-preparation', prepared_path=current.prepared_path)
        admission = h.root / 'writer-admissions'
        h.write(admission / '000001/allocation.json', {'live': str(h.live), 'run_id': h.live.name})
        binding: MachineBinding = {'machine_id': h.machine, 'state_root': str(h.id_root),
            'admission_root': str(admission)}
        args = argparse.Namespace(previous_live=h.live, previous_keeper=h.keeper,
            previous_failure_close=Path(result['bundle']['path']), previous_release=Path(result['previous_release']['path']))
        return selection, args, binding, result

    def test_actual_writer_lock_revalidates_real_ttl_reducer_before_intent(self) -> None:
        from collections.abc import Iterator
        h = self.harness
        selection, args, binding, result = self.writer_fixture()
        original_lock = ids._exclusive_file_lock
        original_reducer = unrun.validate_pre_intent_offline_ttl_refusal
        active, calls = [False], []

        @contextlib.contextmanager
        def locked(path: Path) -> Iterator[None]:
            with original_lock(path):
                active[0] = True
                try:
                    yield
                finally:
                    active[0] = False

        def fresh_bus(*arguments: object) -> JsonObject:
            self.assertTrue(active[0])
            calls.append('fresh_bus')
            return h.packet

        def reduce(previous: Path, freeze: object, close: Path, keeper: Path,
                release: object, bus: object, state: Path) -> JsonObject:
            self.assertTrue(active[0])
            calls.append('real_reducer')
            return original_reducer(previous, freeze, close, keeper, release, bus, state)

        with patch.object(ids, '_exclusive_file_lock', locked), patch.object(ids, 'current_machine_id', return_value=h.machine), \
                patch.object(ids, 'default_state_root', return_value=h.id_root), \
                patch.object(allocation, 'current_screen_absent', side_effect=fresh_bus), \
                patch.object(allocation, 'runtime_process_inventory', return_value={'blockers': []}), \
                patch.object(unrun, 'validate_pre_intent_offline_ttl_refusal', side_effect=reduce):
            record = allocation.claim_machine_admission(binding, selection, args, result['validation'])
        self.assertEqual(calls, ['fresh_bus', 'real_reducer'])
        intent = json_object(json.loads((record / 'intent.json').read_bytes()))
        closure = object_field(intent, 'closure')
        self.assertEqual(closure['mode'], result['validation']['mode'])
        self.assertIs(object_field(closure, 'failure_cleanup')['business_pass'], False)
        self.assertEqual(record.name, '000002')

    def test_changed_locked_evidence_refuses_without_consuming_machine_intent(self) -> None:
        from collections.abc import Iterator
        h = self.harness
        selection, args, binding, result = self.writer_fixture()
        original_lock = ids._exclusive_file_lock
        active = [False]
        admission = Path(binding['admission_root'])
        close = Path(result['bundle']['path'])
        original_close = close.read_bytes()

        @contextlib.contextmanager
        def locked(path: Path) -> Iterator[None]:
            with original_lock(path):
                active[0] = True
                try:
                    yield
                finally:
                    active[0] = False

        for mutation in ('screen', 'process', 'host', 'closure'):
            with self.subTest(mutation=mutation):
                packet = copy.deepcopy(h.packet)
                inventory: JsonObject = {'blockers': []}
                if mutation == 'screen':
                    tasks = packet['tasks']
                    if not isinstance(tasks, list):
                        self.fail('Authored task list required')
                    task = json_object(tasks[0])
                    task['resources'] = ['ck3-screen:acquired']
                    packet['tasks'] = [task]
                elif mutation == 'process':
                    inventory['blockers'] = [{'pid': 123, 'name': 'ck3.exe'}]

                def fresh_bus(*arguments: object) -> JsonObject:
                    self.assertTrue(active[0])
                    if mutation == 'host':
                        (h.live / 'host-started.json').write_text('{}', encoding='utf-8')
                    return packet

                def fresh_inventory(*arguments: object) -> JsonObject:
                    self.assertTrue(active[0])
                    return inventory

                if mutation == 'closure':
                    close.write_bytes(original_close + b' ')
                try:
                    with patch.object(ids, '_exclusive_file_lock', locked), \
                            patch.object(ids, 'current_machine_id', return_value=h.machine), \
                            patch.object(ids, 'default_state_root', return_value=h.id_root), \
                            patch.object(allocation, 'current_screen_absent', side_effect=fresh_bus), \
                            patch.object(allocation, 'runtime_process_inventory', side_effect=fresh_inventory):
                        with self.assertRaises(ValueError):
                            allocation.claim_machine_admission(binding, selection, args, copy.deepcopy(result['validation']))
                finally:
                    close.write_bytes(original_close)
                    (h.live / 'host-started.json').unlink(missing_ok=True)
                self.assertFalse((admission / 'machine.json').exists())
                self.assertFalse((admission / '000002').exists())

    def test_exact_new_allocator_helper_scope_is_strict(self) -> None:
        from mypy import api
        names = {'_TTLAdmissionEvidence', '_TTLAdmissionReducer', 'revalidate_pre_intent_offline_ttl_admission'}
        source = ast.parse((REPO / 'tools/ck3_mod_acceptance_allocate.py').read_text('utf-8-sig'))
        nodes = [copy.deepcopy(node) for node in source.body
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
        self.assertEqual(len(nodes), len(names))
        unit = ast.parse('''from __future__ import annotations
import argparse
from pathlib import Path
from typing import Protocol, runtime_checkable
from ck3_mod_acceptance import Selection, path_at, pin, read_json, same_directory_control_peer
from ck3_mod_acceptance_background_types import JsonObject, json_object, object_field, text_field
''')
        unit.body.extend(nodes)
        path = self.harness.root / 'exact_ttl_allocator_scope.py'
        path.write_text(ast.unparse(ast.fix_missing_locations(unit)), encoding='utf-8')
        with patch.dict(os.environ, {'MYPYPATH': os.pathsep.join((str(REPO / 'tools'), str(REPO / 'ck3_autonomous_player/src')))}):
            stdout, stderr, code = api.run(['--strict', '--strict-equality', '--follow-imports=silent',
                '--no-incremental', '--cache-dir', os.devnull, str(path)])
        self.assertEqual(code, 0, stdout + stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
