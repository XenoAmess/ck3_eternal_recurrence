"""Portable lifecycle tests: no CK3, injector, handles or screen operations."""
from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / 'src'))
from xar_autoplayer import runtime
from xar_autoplayer.errors import AgentError

SPEC = importlib.util.spec_from_file_location('delayed_saved_host',
    PACKAGE / 'native_bridge/research/run_ck3_12002_mcp_live.py')
HOST = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOST)
MARKER = b'[21:29:31][D][gameapplication.cpp:635]: Setup completion (history loaded): 236.273023 seconds\n'
IN_GAME = b"[21:28:05][D][gameapplication.cpp:583]: Setting idler 'In Game' with init options\n"
R46_HISTORY = b'[13:56:24][D][gameapplication.cpp:635]: Setup completion (history loaded): 65.360176 seconds\n'
R46_IN_GAME = b"[13:56:31][D][gameapplication.cpp:583]: Setting idler 'In Game' with init options\n"


class RetainedProcess:
    def __init__(self, events):
        self.events = events
        self.pid = 71
        self.resumed = False
        self.returncode = None
        self.close = mock.Mock()

    def resume(self):
        if self.resumed:
            raise AssertionError('Original primary thread must not resume twice')
        self.events.append('resume')
        self.resumed = True

    def poll(self):
        return self.returncode

    def terminate_exact(self):
        self.events.append('cleanup-original-process')
        self.returncode = 1

    def wait(self, timeout):
        return self.returncode


class DelayedInjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / 'profile'
        (self.profile / 'logs').mkdir(parents=True)
        self.log = self.profile / 'logs/debug.log'
        self.events = []
        self.process = RetainedProcess(self.events)
        self.clock = 0.0
        self.epoch = runtime.time.time_ns()
        self.stop = False
        self.on_sleep = lambda: None
        self.config = runtime.NativeBridgeLaunchConfig('native-headless', r'\\.\pipe\same-managed-pipe',
            self.root / 'bridge.dll', self.root / 'injector.exe')
        self.config.dll_path.touch()
        self.config.injector_path.touch()
        self.inject = mock.Mock(side_effect=self.inject_once)

    def inject_once(self, process, config, evidence_dir):
        self.assertIs(process, self.process)
        self.assertIs(config, self.config)
        self.assertTrue(process.resumed)
        self.events.append('inject')
        return {'injector_root_reaped': True, 'complete_process_tree_proven': True}

    def sleep(self, seconds):
        self.clock += seconds
        self.on_sleep()

    def run_delayed(self, *, deadline=1.0, gate=None):
        with mock.patch.object(runtime.time, 'monotonic', side_effect=lambda: self.clock), \
             mock.patch.object(runtime.time, 'sleep', side_effect=self.sleep), \
             mock.patch.object(runtime, '_inject_native_bridge', self.inject):
            return runtime._resume_then_inject_after_saved_load(self.process, self.config,
                profile_dir=self.profile, log_epoch_ns=self.epoch, deadline=deadline,
                stop_requested=lambda: self.stop, before_process_create=gate,
                evidence_dir=self.root / 'injector-attempt')

    def test_same_process_resumes_once_then_marker_allows_one_injection(self):
        def publish():
            self.log.write_bytes(IN_GAME + MARKER if self.clock >= .5 else b'End loading of history\n')
        self.on_sleep = publish
        proof = self.run_delayed()
        self.assertEqual(self.events, ['resume', 'inject'])
        self.inject.assert_called_once()
        self.assertEqual(proof['target_ck3_pid'], 71)
        self.assertEqual(proof['text'], MARKER.decode().strip())
        self.assertEqual(proof['in_game_text'], IN_GAME.decode().strip())
        self.assertFalse(proof['native_identity_verified'])
        self.assertFalse(proof['business_pass'])
        with self.assertRaisesRegex(AgentError, 'unresumed, uninjected'):
            self.run_delayed()
        self.assertEqual(self.events, ['resume', 'inject'])

    def test_actual_r46_history_then_in_game_also_allows_one_injection(self):
        self.log.write_bytes(R46_HISTORY + R46_IN_GAME)
        os.utime(self.log, ns=(self.epoch + 1_000_000_000, self.epoch + 1_000_000_000))
        proof = self.run_delayed()
        self.assertEqual(self.events, ['resume', 'inject'])
        self.inject.assert_called_once()
        self.assertEqual(proof['text'], R46_HISTORY.decode().strip())
        self.assertEqual(proof['in_game_text'], R46_IN_GAME.decode().strip())

    def test_history_only_or_incomplete_in_game_preserves_deadline_without_injection(self):
        for payload in (R46_HISTORY, R46_HISTORY + R46_IN_GAME.rstrip(b'\n')):
            with self.subTest(payload=payload):
                self.events = []
                self.process = RetainedProcess(self.events)
                self.clock = 0
                self.log.write_bytes(payload)
                os.utime(self.log, ns=(self.epoch + 1_000_000_000, self.epoch + 1_000_000_000))
                with self.assertRaisesRegex(AgentError, 'original readiness deadline'):
                    self.run_delayed(deadline=.5)
                self.assertEqual(self.clock, .5)
                self.inject.assert_not_called()
                self.assertEqual(self.events, ['resume'])

    def test_missing_or_prior_epoch_marker_times_out_without_injection(self):
        for stale in (False, True):
            with self.subTest(stale=stale):
                self.process = RetainedProcess(self.events)
                self.clock = 0
                if stale:
                    self.log.write_bytes(IN_GAME + MARKER)
                    os.utime(self.log, ns=(self.epoch - 1_000_000_000, self.epoch - 1_000_000_000))
                with self.assertRaisesRegex(AgentError, 'original readiness deadline'):
                    self.run_delayed(deadline=.5)
                self.inject.assert_not_called()

    def test_stop_or_original_process_exit_prevents_injection(self):
        for reason in ('stop', 'exit'):
            with self.subTest(reason=reason):
                self.process = RetainedProcess(self.events)
                self.clock = 0
                self.stop = False
                def interrupt():
                    if reason == 'stop':
                        self.stop = True
                    else:
                        self.process.returncode = 7
                self.on_sleep = interrupt
                with self.assertRaisesRegex(AgentError, 'stopped|process exited'):
                    self.run_delayed()
                self.inject.assert_not_called()

    def test_lease_gate_cannot_extend_deadline_or_trigger_injection(self):
        self.log.write_bytes(IN_GAME + MARKER)
        # Establish a fresh fixture independently of filesystem clock resolution.
        os.utime(self.log, ns=(self.epoch + 1_000_000_000, self.epoch + 1_000_000_000))
        gates = []
        @contextmanager
        def gate():
            gates.append(self.process)
            if len(gates) == 2:
                self.clock = 2
            yield
        with self.assertRaisesRegex(AgentError, 'original readiness deadline'):
            self.run_delayed(gate=gate)
        self.assertEqual(gates, [self.process, self.process])
        self.inject.assert_not_called()
        self.assertEqual(self.events, ['resume'])

    def test_launch_timeout_uses_existing_original_job_watchdog_cleanup(self):
        state = self.root / 'state'
        (state / 'control').mkdir(parents=True)
        exe = self.root / 'binaries/ck3.exe'
        exe.parent.mkdir()
        exe.touch()
        spec = SimpleNamespace(state_dir=state, profile_dir=self.profile, game_exe=exe)
        job = object()
        created = False
        self.process.image_path = lambda: exe
        def create(*args, **kwargs):
            nonlocal created
            created = True
            self.assertEqual(args[2][runtime.NATIVE_BRIDGE_PIPE_ENV], self.config.pipe_name)
            self.assertEqual(args[0].count("-debug_mode"), 1)
            self.assertEqual(args[0].count("-loadsave=restored_campaign"), 1)
            return self.process
        def identity(pid):
            return {'name': 'python.exe' if pid == os.getpid() else 'ck3.exe',
                'executable': sys.executable if pid == os.getpid() else str(exe),
                'parent_pid': os.getpid(), 'creation_date': '20261009204613.000000+000'}
        def inventory():
            return {'processes': [dict(identity(71), pid=71)] if created else []}
        with mock.patch.object(runtime, 'ck3_processes', return_value=[]), \
             mock.patch.object(runtime, '_process_identity', side_effect=identity), \
             mock.patch.object(runtime, 'ck3_process_inventory', side_effect=inventory), \
             mock.patch.object(runtime, '_start_process_watchdog', return_value=(99, 'watchdog-time')), \
             mock.patch.object(runtime, '_create_kill_on_close_job', return_value=job), \
             mock.patch.object(runtime, '_create_suspended_process', side_effect=create), \
             mock.patch.object(runtime, '_assign_process_to_job') as assign, \
             mock.patch.object(runtime, '_job_active_processes', return_value=0), \
             mock.patch.object(runtime, '_close_job') as close_job, \
             mock.patch.object(runtime, '_stop_authenticated_watchdog') as stop_watchdog, \
             mock.patch.object(runtime.time, 'monotonic', side_effect=lambda: self.clock), \
             mock.patch.object(runtime.time, 'sleep', side_effect=self.sleep), \
             mock.patch.object(runtime, '_inject_native_bridge', self.inject):
            with self.assertRaisesRegex(AgentError, 'failed safely.*original readiness deadline'):
                runtime.launch(spec, native_bridge=self.config, load_save_name='restored_campaign',
                    debug_mode=True, verify_prepared_profile=False, native_bridge_after_saved_load=True,
                    native_bridge_injection_deadline=.5)
        assign.assert_called_once_with(job, self.process)
        close_job.assert_called_once_with(job)
        stop_watchdog.assert_called_once()
        self.process.close.assert_called_once()
        self.inject.assert_not_called()
        self.assertEqual(self.events, ['resume', 'cleanup-original-process'])
        self.assertFalse((state / 'control/unsafe-cleanup.json').exists())


class HostPolicyTests(unittest.TestCase):
    def test_explicit_flag_is_default_off_and_requires_saved_campaign(self):
        args = HOST.parser().parse_args([])
        self.assertFalse(args.saved_campaign_inject_after_load)
        args.saved_campaign_inject_after_load = True
        with self.assertRaisesRegex(SystemExit, 'requires an explicit saved campaign'):
            HOST.validate_saved_campaign_options(args)

    def test_host_latebinds_same_deadline_and_stop_to_original_launch(self):
        module = ModuleType('fake_managed_session')
        exec('def native_session(spec, **kwargs):\n launch(spec, native_bridge=kwargs["native_bridge"])\n return {}\n'
             'def _native_session_locked(*args, **kwargs):\n return {}\n', module.__dict__)
        process = SimpleNamespace(pid=71, saved_campaign_load_observation={'business_pass': False})
        handle = SimpleNamespace(command=['ck3.exe', '-loadsave=restored_campaign'], process=process)
        module.launch = mock.Mock(return_value=handle)
        stop = SimpleNamespace(is_set=lambda: False)
        args = SimpleNamespace(timeout=2100, hold_seconds=900, saved_campaign_inject_after_load=True,
            _saved_campaign_readiness_deadline=1234.0)
        record = {}
        with mock.patch('importlib.import_module', return_value=module):
            HOST.saved_campaign_session(object(), object(), args, stop, output_stream=None, launch_record=record)
        kwargs = module.launch.call_args.kwargs
        self.assertEqual(kwargs['native_bridge_injection_deadline'], 1234.0)
        self.assertIs(kwargs['native_bridge_stop_requested'], stop.is_set)
        self.assertTrue(kwargs['native_bridge_after_saved_load'])
        self.assertEqual(record['bridge_injection_stage'], 'after_saved_campaign_setup_completion')
        self.assertFalse(record['load_completion_observation']['business_pass'])


class SavedCampaignDebugModeTests(unittest.TestCase):
    def test_default_command_is_byte_for_byte_unchanged(self):
        spec = SimpleNamespace(game_exe=Path('game/ck3.exe'), profile_dir=Path('profile'))
        expected = [str(spec.game_exe), '-gdpr-compliant', '-userdir=' + str(spec.profile_dir),
                    '-loadsave=restored_campaign']
        self.assertEqual(runtime._ck3_launch_command(spec, load_save_name='restored_campaign'), expected)
        self.assertEqual(runtime._ck3_launch_command(spec, load_save_name='restored_campaign', debug_mode=False), expected)

    def test_explicit_true_adds_only_one_flag_to_the_original_saved_command(self):
        spec = SimpleNamespace(game_exe=Path('game/ck3.exe'), profile_dir=Path('profile'))
        normal = runtime._ck3_launch_command(spec, load_save_name='restored_campaign')
        debug = runtime._ck3_launch_command(spec, load_save_name='restored_campaign', debug_mode=True)
        self.assertEqual(debug, [normal[0], '-debug_mode', *normal[1:]])
        self.assertEqual(debug.count('-loadsave=restored_campaign'), 1)
        self.assertNotIn('-continuelastsave', debug)

    def test_mixed_boolean_types_are_rejected_before_any_process_check(self):
        for value in (0, 1, None, 'true', [], {}):
            with self.subTest(value=value), mock.patch.object(runtime, 'ck3_processes') as processes, \
                    mock.patch.object(runtime, 'native_bridge_launch_config_from_environment') as config:
                with self.assertRaisesRegex(AgentError, 'explicit boolean'):
                    runtime._ck3_launch_command(object(), debug_mode=value)
                with self.assertRaisesRegex(AgentError, 'explicit boolean'):
                    runtime.launch(object(), debug_mode=value)
                processes.assert_not_called()
                config.assert_not_called()

    def test_host_default_off_and_saved_only_policy(self):
        self.assertFalse(HOST.parser().parse_args([]).saved_campaign_debug_mode)
        for extra in ([], ['--saved-campaign-save', 'fake.ck3', '--server']):
            args = HOST.parser().parse_args(['--saved-campaign-debug-mode', *extra])
            with self.assertRaisesRegex(SystemExit, 'requires an explicit saved campaign'):
                HOST.validate_saved_campaign_options(args)
        for value in (0, 1, None, 'true', [], {}):
            args = HOST.parser().parse_args([])
            args.saved_campaign_debug_mode = value
            with self.subTest(value=value), self.assertRaisesRegex(SystemExit, 'explicit boolean'):
                HOST.validate_saved_campaign_options(args)

    def test_host_accepts_explicit_saved_diagnostic_without_reading_save_body(self):
        with tempfile.TemporaryDirectory() as directory:
            plan = Path(directory) / 'plan.json'
            plan.write_text('[]', encoding='utf-8')
            args = HOST.parser().parse_args(['--saved-campaign-debug-mode', '--fixture-profile',
                '--plan', str(plan), '--saved-campaign-save', str(Path(directory) / 'not-read.ck3'),
                '--saved-campaign-save-bytes', '1', '--saved-campaign-save-sha256', 'a' * 64,
                '--saved-campaign-player-id', '31254', '--saved-campaign-date-raw', '53144712',
                '--saved-campaign-product-inventory', str(Path(directory) / 'not-read.json')])
            HOST.validate_saved_campaign_options(args)
            self.assertTrue(args.saved_campaign_debug_mode)

    def test_wrapper_propagates_bool_and_requires_actual_debug_flag_agreement(self):
        for requested, actual in ((False, False), (True, True), (True, False), (False, True)):
            with self.subTest(requested=requested, actual=actual):
                module = ModuleType('fake_managed_session')
                exec('def native_session(spec, **kwargs):\n launch(spec, native_bridge=kwargs["native_bridge"])\n return {}\n'
                     'def _native_session_locked(*args, **kwargs):\n return {}\n', module.__dict__)
                command = ['ck3.exe', '-loadsave=restored_campaign']
                if actual:
                    command.insert(1, '-debug_mode')
                module.launch = mock.Mock(return_value=SimpleNamespace(command=command, process=SimpleNamespace(pid=71)))
                stop = SimpleNamespace(is_set=lambda: False)
                args = SimpleNamespace(timeout=2100, hold_seconds=900, saved_campaign_debug_mode=requested,
                    saved_campaign_inject_after_load=True, _saved_campaign_readiness_deadline=1234.0)
                record = {}
                with mock.patch('importlib.import_module', return_value=module):
                    HOST.saved_campaign_session(object(), object(), args, stop, output_stream=None, launch_record=record)
                kwargs = module.launch.call_args.kwargs
                self.assertIs(kwargs['debug_mode'], requested)
                self.assertEqual(kwargs['load_save_name'], 'restored_campaign')
                self.assertEqual(kwargs['native_bridge_injection_deadline'], 1234.0)
                self.assertIs(kwargs['native_bridge_stop_requested'], stop.is_set)
                self.assertEqual(record['argv_admitted'], requested == actual)
                self.assertIs(record['debug_mode'], requested)


class SharedReadinessDeadlineTests(unittest.IsolatedAsyncioTestCase):
    async def test_native_readiness_does_not_restart_expired_loading_budget(self):
        client = SimpleNamespace(call=mock.AsyncMock(), fresh=mock.AsyncMock())
        report = {}
        with mock.patch.object(HOST.time, 'monotonic', return_value=100.0):
            with self.assertRaisesRegex(TimeoutError, 'original readiness deadline'):
                await HOST.wait_for_saved_campaign(client, {'actor_character_id': 31254},
                    report=report, write=lambda: None, timeout=600,
                    managed_done=None, poll_interval=.5, readiness_deadline=99.0)
        client.call.assert_not_called()
        client.fresh.assert_not_called()
        self.assertEqual(report['saved_campaign_restore']['observations'], [])


if __name__ == '__main__':
    unittest.main()
