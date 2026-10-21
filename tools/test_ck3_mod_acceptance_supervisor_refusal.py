"""Supervisor admission refusal: resource closure without invented exit credit.

All artifacts and live IDs are synthetic and isolated. The public allocation
route, machine admission chain, pins, and ID counter remain real; only OS,
screen/keeper subprocesses, and the empty prepared profile are substituted.
"""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
import contextlib
import io
import json
import sys
import unittest

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import test_ck3_mod_acceptance_r06_scope as scope_fixture
import ck3_mod_acceptance as entry
import ck3_mod_acceptance_allocate as allocator
import ck3_mod_acceptance_launcher as launcher_consumer
from ck3_mod_acceptance_background_types import CONTROL_QUEUE_MODULE_ORDER_V1
import ck3_mod_acceptance_supervisor_refusal as subject
from ck3_mod_acceptance_legacy_launcher_fixture_v1 import materialize_legacy_launcher_fixture_v1
import ck3_live_run_id as ids


class SupervisorRefusalTests(unittest.TestCase):
    def setUp(self):
        fixture = scope_fixture.PublicR06ScopeTests('runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root = fixture.root
        self.machine = fixture.machine
        self.state_root = self.root / 'isolated-id-state'
        self.binding = {'machine_id': self.machine, 'state_root': str(self.state_root),
                        'admission_root': str(self.state_root / self.machine / '.shared-runtime-admissions-v1')}
        fixture.prepare()
        self.identity = ids.allocate_live_run_id('vanilla', state_root=self.state_root, machine_id=self.machine)
        self.live = self.root / 'previous' / self.identity.run_id
        self.live.mkdir(parents=True)
        (self.live / 'controls').mkdir()
        self.keeper = self.root / 'previous-keeper'
        self.keeper.mkdir()
        self.state = self.root / 'previous-state'
        (self.state / 'profile').mkdir(parents=True)
        prepared = deepcopy(entry.read_json(fixture.prepared_path))
        prepared['startup']['state_dir'] = str(self.state)
        prepared['preparation']['startup']['state_dir'] = str(self.state)
        self.prepared_path = self.root / 'previous-prepared/prepared-case.json'
        prepared_ref = self.write(self.prepared_path, prepared)
        selected = entry.Selection(fixture.runtime_path, fixture.products_path,
            'war-episode04-r10', 'r10-common-preparation', None, fixture.prepared_path)
        host_argv = list(selected.argv)
        for flag, value in (('--output', self.live / 'native-report.json'), ('--state-dir', self.state)):
            host_argv[host_argv.index(flag) + 1] = str(value)
        launcher = materialize_legacy_launcher_fixture_v1(self.root / 'historical-launcher')
        self.closure_bus_root = self.root / 'closure-bus'
        closure_bus = self.closure_bus_root / 'bin/codex_task_bus.py'
        self.write(closure_bus, {'synthetic_bus_source_never_executed': True})
        self.freeze = {'run_id': self.live.name, 'mod_key': 'vanilla',
            'execution_id': self.identity.execution_id, 'cell': 'r10-common-preparation',
            'screen_task': 'isolated-supervisor-refusal-a01', 'argv': host_argv,
            'state_dir': str(self.state), 'source_root': str(fixture.paths['source_root']),
            'runtime_manifest': entry.pin(fixture.manifest_path),
            'identity_allocation': {'machine_id': self.machine, 'state_root': str(self.state_root)},
            'lease_anchor': str(self.root / 'lease'),
            'previous_session_closed': True, 'previous_screen_released': True,
            'launch_requires_fresh_owned_cas_and_offline_direct_review': True,
            'files': {str(path.resolve()): {k: entry.pin(path)[k] for k in ('bytes', 'sha256')}
                      for path in (fixture.products_path, fixture.runtime_path, launcher, closure_bus)},
            'business_pass': False}
        frozen = self.write(self.live / 'frozen-argv.json', self.freeze)
        context = {'schema': 'ck3-mod-acceptance-run-context-v1', 'run_id': self.live.name,
            'run_dir': str(self.live), 'keeper_root': str(self.keeper), 'prepared_case': prepared_ref,
            'product': 'war-episode04-r10', 'case': 'r10-common-preparation',
            'case_inputs': prepared['case_inputs']}
        allocated = self.write(self.live / 'allocated-context.json', context)
        ready = self.write(self.live / 'ready-context.json', {**context, 'frozen_argv': frozen})
        frame = self.write(self.root / 'review/frame.json',
            {'schema': 'ck3.steam_fresh_desktop_frame.v1',
             'captured_at_utc': '2026-10-20T12:00:00+00:00'})
        image = self.write(self.root / 'review/image.fixture', {'synthetic_image_metadata_only': True})
        keeper_inputs = self.write(self.keeper / 'inputs.json', {'test_only': True})
        self.nonce, self.ticket = 'a' * 32, 'b' * 64
        challenge = self.write(self.root / 'review/challenge.json', {
            'schema': 'ck3-mod-acceptance-review-challenge-v1',
            'created_at_utc': '2026-10-20T12:09:00+00:00', 'nonce': self.nonce,
            'run_id': self.live.name, 'screen_task': self.freeze['screen_task'],
            'frozen_argv': frozen, 'keeper_root': str(self.keeper), 'keeper_inputs': keeper_inputs,
            'frame': frame, 'image': image, 'review_image': image, 'business_pass': False})
        proof = self.write(self.root / 'review/proof.json', {
            'schema': 'ck3-mod-acceptance-direct-review-v1', 'machine_id': self.machine,
            'run_id': self.live.name, 'screen_task': self.freeze['screen_task'],
            'frozen_argv': frozen, 'challenge': challenge, 'image': image, 'review_image': image,
            'reviewed_at_utc': '2026-10-20T12:09:00+00:00', 'reviewer': 'synthetic-test',
            'direct_image_review': True, 'steam_offline_confirmed': True, 'observed_nonce': self.nonce})
        self.reviewed_path = self.root / 'reviewed-context.json'
        self.write(self.reviewed_path, {**entry.read_json(self.live / 'ready-context.json'),
            'proof': proof['path'], 'challenge': challenge['path'],
            'observed_nonce': self.nonce, 'reviewer': 'synthetic-test'})
        intent = self.write(self.live / 'launch-intent.json', {
            'at_utc': '2026-10-20T12:10:00+00:00', 'ticket': self.ticket,
            'run_id': self.live.name, 'proof': proof, 'challenge': challenge, 'frozen_argv': frozen,
            'admitted_lease': {'task_id': self.freeze['screen_task']}, 'business_pass': False})
        supervisor_argv = [sys.executable, '-B', '-X', 'utf8', str(launcher),
            '--run-root', str(self.live), '--keeper-root', str(self.keeper),
            '--proof', proof['path'], '--challenge', challenge['path'], '--observed-nonce', self.nonce,
            '--reviewer', 'synthetic-test', '--supervise', '--launch-ticket', self.ticket]
        supervisor = self.write(self.live / 'host-supervisor-started.json', {
            'at_utc': '2026-10-20T12:10:01+00:00', 'pid': 987640,
            'argv': supervisor_argv, 'business_pass': False})
        stderr = self.write(self.live / 'host-supervisor-stderr.log', {
            'status': 'BLOCKED',
            'error': "ValueError('Direct review/challenge/Steam frame is stale or from the future')",
            'business_pass': False})
        public = [sys.executable, '-B', '-X', 'utf8', str(TOOLS / 'ck3_mod_acceptance.py'),
            '--runtime', str(fixture.runtime_path), '--products', str(fixture.products_path),
            '--product', 'war-episode04-r10', '--case', 'r10-common-preparation',
            '--prepared-case', str(self.prepared_path)]
        waits = {}
        for mode, code, pid, started, observed, extra in (
            ('run', 2, 987641, '12:09:59', '12:10:03', ['--run-context', str(self.reviewed_path)]),
            ('allocate', 0, 987642, '12:00:00', '12:11:00', ['--keeper-output', str(self.keeper)])):
            waits['public_' + mode + '_wait'] = self.write(self.root / ('public-' + mode + '-wait.json'), {
                'machine_id': self.machine, 'observed_at_utc': '2026-10-20T' + observed + '+00:00',
                'started_at_utc': '2026-10-20T' + started + '+00:00',
                'argv': public + extra + [mode], 'phase': mode, 'pid': pid,
                'actual_original_popen_wait': True, 'returncode': code})
        stop = self.keeper / 'STOP'
        stop.write_text('Synthetic test STOP: supervisor stale rejection before host; no game credit.\n', encoding='utf-8')
        keeper_value = {'schema': 'xar.promo.screen-lease-keeper/v1',
            'task_id': self.freeze['screen_task'], 'last_sequence': 10,
            'failure': None, 'thread_exited': True, 'entry_error': None, 'game_actions': False,
            'at_utc': '2026-10-20T12:10:20+00:00', 'screen_released': False}
        keeper = self.write(self.keeper / 'report.json', keeper_value)
        parent = self.write(self.live / 'keeper-actual-parent-exit.json', {
            'run_id': self.live.name, 'keeper_actual_exit_code': 0,
            'keeper_report': keeper_value, 'business_pass': False})
        task = {'schema': 'codex.task_bus.v1', 'task_id': self.freeze['screen_task'],
                'state': 'done', 'resources': [], 'last_sequence': 11}
        self.release = {'schema': 'codex.task_bus.v1', 'ok': True, 'task': task,
            'event': {'schema': 'codex.task_bus.v1', 'sequence': 11, 'kind': 'completed',
                      'task_id': self.freeze['screen_task'], 'state': 'done', 'resources': []}}
        self.release_path = self.root / 'screen-release.json'
        release = self.write(self.release_path, self.release)
        self.bus = {'schema': 'codex.task_bus.v1', 'ok': True,
                    'tasks': [{**task, 'age_seconds': 0, 'stale': False}]}
        self.counter_path = self.state_root / self.machine / 'vanilla/counter.json'
        self.bundle = {'schema': subject.SCHEMA, 'machine_id': self.machine,
            'observed_at_utc': '2026-10-20T12:12:00+00:00', 'run_id': self.live.name,
            'failure_stage': 'SUPERVISOR_ADMISSION_BEFORE_RETAIN_HOST',
            **{key: False for key in ('host_started', 'native_session_started', 'game_started',
                'normal_close_qualified', 'business_pass', 'supervisor_original_wait_proven')},
            'supervisor_original_wait_returncode': None,
            'ready': ready, 'frozen': frozen, 'allocated_context': allocated,
            'prepared_case': prepared_ref, 'launch_intent': intent,
            'supervisor_started': supervisor, 'supervisor_stderr': stderr, **waits,
            'keeper_STOP': entry.pin(stop), 'keeper_report': keeper, 'keeper_parent_exit': parent,
            'CAS_release': release, 'launcher_source': entry.pin(launcher),
            'counter': entry.pin(self.counter_path)}
        self.close = self.root / 'supervisor-refused-close.json'
        self.save()
        admission = Path(self.binding['admission_root'])
        self.write(admission / 'machine.json', self.binding)
        self.write(admission / '000001/allocation.json', {
            'run_id': self.live.name, 'live': str(self.live)})

    def write(self, path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        return entry.pin(path)

    def save(self):
        self.write(self.close, self.bundle)

    @contextlib.contextmanager
    def machine_and_os(self, blockers=None, supervisor_alive=False):
        with patch.object(ids, 'current_machine_id', return_value=self.machine), \
             patch.object(ids, 'default_state_root', return_value=self.state_root), \
             patch.object(allocator, 'runtime_process_inventory', return_value={'blockers': blockers or []}), \
             patch('psutil.pid_exists', return_value=supervisor_alive):
            yield

    def check(self, previous=None, freeze=None, bus=None):
        return subject.validate_supervisor_refusal(previous or self.live, freeze or self.freeze,
            self.close, self.keeper, self.release, self.bus if bus is None else bus)

    def change_original(self, key, transform):
        path = Path(self.bundle[key]['path'])
        value = entry.read_json(path)
        transform(value)
        self.bundle[key] = self.write(path, value)
        self.save()

    def allocate(self):
        fixture = self.fixture
        args = fixture.args('allocate')
        args.__dict__.update(attempt='a02', keeper_output=self.root / 'next-keeper',
            previous_release=self.release_path, first_machine_bootstrap=None,
            previous_failure_close=self.close, previous_live=self.live, previous_keeper=self.keeper,
            latest_screen_release=None)
        child = Mock(pid=987650)
        def process(argv, **unused):
            if argv[0] == 'git':
                return NS(returncode=0, stdout=b'', stderr=b'')
            return NS(returncode=0, stdout=b'{"task":{"last_sequence":12}}', stderr=b'')
        def finish(*unused):
            args.keeper_output.mkdir()
            self.write(args.keeper_output / 'report.json', {'test_only': True})
            return 0
        with contextlib.ExitStack() as stack:
            stack.enter_context(self.machine_and_os())
            for key, value in (
                ('actual_machine_binding', self.binding), ('shared_bus_history', ([], True)),
                ('current_screen_absent', self.bus), ('keeper_command', ['not-executed']),
                ('wait_for_keeper_ready', {'test_only': True})):
                stack.enter_context(patch.object(allocator, key, return_value=value))
            stack.enter_context(patch.object(allocator, 'wait_for_allocated_keeper', side_effect=finish))
            stack.enter_context(patch.object(allocator.subprocess, 'run', side_effect=process))
            launched = stack.enter_context(patch.object(allocator.subprocess, 'Popen', return_value=child))
            stack.enter_context(patch('psutil.Process', return_value=NS(create_time=lambda: 1)))
            with contextlib.redirect_stdout(io.StringIO()):
                result = entry.native_dispatch(args)
        launched.assert_called_once()
        return result

    def test_exact_stale_refusal_admits_resources_with_supervisor_wait_unknown(self):
        with self.machine_and_os():
            result = self.check()
        cleanup = result['failure_cleanup']
        self.assertFalse(cleanup['host_started'])
        self.assertFalse(cleanup['native_session_started'])
        self.assertFalse(cleanup['normal_close_qualified'])
        self.assertFalse(cleanup['business_pass'])
        self.assertIsNone(cleanup['original_host_exit_code'])
        self.assertIsNone(cleanup['original_ck3_exit_code'])
        self.assertFalse(cleanup['supervisor_original_wait_proven'])
        self.assertIsNone(cleanup['supervisor_original_wait_returncode'])
        self.assertNotIn('counter', cleanup['original_evidence'])

    def test_builder_writes_only_pinned_metadata_with_unknown_supervisor_wait(self):
        output = self.root / 'built-close.json'
        args = NS(previous_live=self.live, keeper_root=self.keeper,
            public_run_wait=Path(self.bundle['public_run_wait']['path']),
            public_allocate_wait=Path(self.bundle['public_allocate_wait']['path']),
            release=self.release_path, task_bus_root=self.closure_bus_root, output=output)
        with self.machine_and_os(), \
             patch.object(allocator, 'current_screen_absent', return_value=self.bus), \
             patch.object(subject, 'validate_supervisor_refusal', wraps=subject.validate_supervisor_refusal) as validate:
            result = subject.build_bundle(args)
        validate.assert_called_once()
        self.assertFalse(result['SDK_or_launch'])
        built = entry.read_json(output)
        self.assertEqual(built['schema'], subject.SCHEMA)
        self.assertFalse(built['supervisor_original_wait_proven'])
        self.assertIsNone(built['supervisor_original_wait_returncode'])
        self.assertEqual(built['frozen'], self.bundle['frozen'])

    def test_original_supervisor_wait_cannot_be_invented(self):
        for key, bad in (('supervisor_original_wait_proven', True),
                         ('supervisor_original_wait_returncode', 2)):
            with self.subTest(key=key), self.machine_and_os():
                old = self.bundle[key]
                self.bundle[key] = bad
                self.save()
                with self.assertRaises(ValueError):
                    self.check()
                self.bundle[key] = old
                self.save()

    def test_unknown_public_wait_is_rejected(self):
        path = Path(self.bundle['public_run_wait']['path'])
        original = entry.read_json(path)
        for key, bad in (('actual_original_popen_wait', False), ('returncode', None)):
            with self.subTest(key=key), self.machine_and_os():
                self.bundle['public_run_wait'] = self.write(path, {**original, key: bad})
                self.save()
                with self.assertRaises(ValueError):
                    self.check()

    def test_game_normal_or_business_credit_is_rejected(self):
        for key in ('host_started', 'native_session_started', 'game_started',
                    'normal_close_qualified', 'business_pass'):
            with self.subTest(key=key), self.machine_and_os():
                self.bundle[key] = True
                self.save()
                with self.assertRaises(ValueError):
                    self.check()
                self.bundle[key] = False
                self.save()

    def test_other_supervisor_exception_is_rejected(self):
        self.change_original('supervisor_stderr', lambda row: row.update(error="RuntimeError('unrelated')"))
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check()

    def test_host_presence_rejects_prehost_credit(self):
        self.write(self.live / 'host-started.json', {'pid': 1})
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check()

    def test_same_named_directory_cannot_rebind_run(self):
        wrong = self.root / 'other-location' / self.live.name
        wrong.mkdir(parents=True)
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check(previous=wrong)

    def test_other_machine_is_rejected(self):
        self.bundle['machine_id'] = 'other-test-machine'
        self.save()
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check()

    def test_live_runtime_or_supervisor_is_rejected(self):
        with self.machine_and_os(blockers=[{'pid': 987640}]), self.assertRaises(ValueError):
            self.check()
        with self.machine_and_os(supervisor_alive=True), self.assertRaises(ValueError):
            self.check()

    def test_later_real_counter_cannot_close_older_run(self):
        ids.allocate_live_run_id('vanilla', state_root=self.state_root, machine_id=self.machine)
        self.bundle['counter'] = entry.pin(self.counter_path)
        self.save()
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check()

    def test_current_task_must_be_released(self):
        wrong = deepcopy(self.bus)
        wrong['tasks'][0].update(state='running', resources=['ck3-screen:acquired'])
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check(bus=wrong)

    def test_original_pin_tampering_is_rejected(self):
        Path(self.bundle['supervisor_started']['path']).write_text('{}\n', encoding='utf-8')
        with self.machine_and_os(), self.assertRaises(ValueError):
            self.check()

    def test_public_allocate_real_chain_and_ids_preserve_failed_originals(self):
        originals = {Path(ref['path']): Path(ref['path']).read_bytes()
                     for key, ref in self.bundle.items()
                     if key != 'counter' and isinstance(ref, dict) and 'sha256' in ref}
        result = self.allocate()
        self.assertEqual(result['status'], 'ACTUAL_ALLOCATED_KEEPER_READY_NOT_RUN')
        self.assertNotEqual(Path(result['live']), self.live)
        self.assertEqual(entry.read_json(self.counter_path)['last_sequence'], 2)
        history = self.counter_path.with_name('allocations.jsonl')
        self.assertEqual(len(history.read_text(encoding='utf-8').splitlines()), 2)
        admitted = entry.read_json(Path(self.binding['admission_root']) / '000002/allocation.json')
        self.assertEqual(admitted['run_id'], Path(result['live']).name)
        # Real allocator and launcher use distinct source directories. Every
        # actual consumer sibling must be frozen under its own resolved path.
        new_live=Path(result['live'])
        frozen=entry.read_json(new_live/'frozen-argv.json')
        for name in CONTROL_QUEUE_MODULE_ORDER_V1:
            self.assertIn(str((self.root/(name+'.py')).resolve()),frozen['files'])
        with patch.object(launcher_consumer,'__file__',str(self.fixture.paths['launcher'])):
            launcher_consumer.frozen_run(new_live)
        closure = entry.read_json(Path(result['live']) / 'predecessor-admission.json')['closure']
        self.assertFalse(closure['failure_cleanup']['business_pass'])
        for path, original in originals.items():
            self.assertEqual(path.read_bytes(), original, str(path))

    def test_latest_machine_record_guard_is_not_bypassed_by_counter_and_release(self):
        # The numeric predecessor counter and CAS release still validate. A
        # later machine admission is independently authoritative and blocks it.
        with self.machine_and_os():
            self.check()
        later = self.root / 'later-red' / 'scope-test-machine--vanilla--R0002'
        self.write(Path(self.binding['admission_root']) / '000002/allocation.json',
            {'run_id': later.name, 'live': str(later)})
        counter = self.counter_path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'latest machine allocation'):
            self.allocate()
        self.assertEqual(self.counter_path.read_bytes(), counter)
        self.assertFalse((self.fixture.state.parent / 'single-use-ledger').exists())


if __name__ == '__main__':
    unittest.main()
