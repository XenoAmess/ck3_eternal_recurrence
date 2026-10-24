"""A failed host before CK3 startup can release resources without business credit."""
import json
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import ck3_mod_acceptance_allocate as allocation


class PrelaunchHostFailureTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='prelaunch-host-failure-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.run = self.root / 'R0084'
        self.run.mkdir()
        (self.run / 'case-output').mkdir()
        (self.run / 'controls').mkdir()
        self.keeper = self.root / 'keeper'
        self.keeper.mkdir()
        state = self.root / 'case/state'
        state.mkdir(parents=True)
        argv = ['python', 'host.py', '--output', str(self.run / 'native-report.json')]
        self.freeze = {'run_id': self.run.name, 'screen_task': 'screen-a53',
                       'state_dir': str(state), 'argv': argv}
        frozen = self.write(self.run / 'frozen-argv.json', self.freeze)
        ready = self.write(self.run / 'ready-context.json',
            {'run_id': self.run.name, 'run_dir': str(self.run),
             'keeper_root': str(self.keeper), 'frozen_argv': frozen})
        host = self.write(self.run / 'host-started.json',
            {'run_id': self.run.name, 'pid': 42, 'supervisor_pid': 43,
             'argv': argv, 'actual_popen_retained': True})
        supervisor = self.write(self.run / 'host-supervisor-started.json', {'pid': 43})
        self.exited = {'run_id': self.run.name, 'pid': 42, 'returncode': 1,
                       'actual_original_popen_wait': True, 'normal_ck3_exit_inferred': False}
        exited = self.write(self.run / 'host-original-process-exit.json', self.exited)
        stderr = self.run / 'host-stderr.log'
        stderr.write_text('ValueError: normal exit requires the actual public prepared profile\n')
        readiness = self.write(self.run / 'case-output/readiness-window-result.json',
            {'status': 'READINESS_TIMEOUT', 'binding': {'run_id': self.run.name}})
        entry = self.write(self.run / 'case-output/entry-run-result.json',
            {'run_id': self.run.name, 'launcher_exit_code': 0,
             'case_error': 'TimeoutError: Original case readiness budget elapsed',
             'business_acceptance': 'RED_OR_INCOMPLETE'})
        prepared = state.parent / 'prepared/prepared-case.json'
        runtime = self.root / 'runtime.json'
        context = self.root / 'reviewed-context.json'
        context.write_text('{}')
        common = ['--runtime', str(runtime), '--prepared-case', str(prepared)]
        public_run = self.write(self.root / 'public-run.json',
            {'schema': 'ck3-recorded-actual-command-v1', 'exit_code': 2,
             'finished_at_utc': 'actual', 'argv': ['python', 'entry.py', 'run',
             *common, '--run-context', str(context)]})
        public_allocate = self.write(self.root / 'public-allocate.json',
            {'schema': 'ck3-recorded-actual-command-v1', 'exit_code': 0,
             'finished_at_utc': 'actual', 'argv': ['python', 'entry.py', 'allocate',
             *common, '--keeper-output', str(self.keeper)]})
        keeper_value = {'task_id': 'screen-a53', 'thread_exited': True,
                        'failure': None, 'game_actions': False}
        keeper = self.write(self.keeper / 'report.json', keeper_value)
        parent = self.write(self.run / 'keeper-actual-parent-exit.json',
            {'run_id': self.run.name, 'keeper_actual_exit_code': 0,
             'keeper_report': keeper_value})
        self.bundle = {'schema': 'ck3-mod-acceptance-prelaunch-host-failure-closure-v1',
            'run_id': self.run.name, 'keeper_root': str(self.keeper),
            'ready_context': ready, 'host_started': host, 'host_supervisor': supervisor,
            'host_exit': exited, 'host_stderr': allocation.pin(stderr),
            'readiness_result': readiness, 'entry_run_result': entry,
            'public_run': public_run, 'public_allocate': public_allocate,
            'keeper_report': keeper, 'keeper_parent_exit': parent,
            'normal_close_qualified': False, 'business_pass': False}
        self.close = self.root / 'close.json'
        self.save()
        self.release = {'task': {'last_sequence': 11}}
        self.bus = {'tasks': [{'task_id': 'screen-a53', 'state': 'done',
                               'resources': [], 'last_sequence': 12}]}

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')
        return allocation.pin(path)

    def save(self):
        self.write(self.close, self.bundle)

    def check(self):
        with patch.object(allocation, 'closed_lease', return_value=True), \
             patch.object(allocation, 'runtime_process_inventory', return_value={'blockers': []}):
            return allocation.previous_prelaunch_host_failure_closure(
                self.run, self.freeze, self.close, self.keeper, self.release, self.bus)

    def menu_initialization_failure(self) -> None:
        """Authored minimal replay of actual R0036's pre-session report/stack shape."""
        live = self.root / 'R0084'
        state = Path(self.freeze['state_dir'])
        self.freeze.update(identity_allocation={'machine_id': 'machine-test'}, source_root=str(self.root / 'sdk'))
        selected = self.root / 'host.py'
        selected.write_text('# exact selected host fixture\n')
        argv = ['python', '-B', '-X', 'utf8', str(selected), '--frontend-mod-load-observation']
        self.freeze['argv'] = argv
        files = {str(selected.resolve()): {key: value for key, value in allocation.pin(selected).items() if key != 'path'}}
        identity = {}
        for path_key, sha_key in (('game_executable', 'game_sha256'), ('dll', 'dll_sha256'), ('injector', 'injector_sha256')):
            path = self.root / path_key
            path.write_bytes(b'never execute authored native identity')
            reference = allocation.pin(path)
            files[str(path.resolve())] = {key: value for key, value in reference.items() if key != 'path'}
            identity.update({path_key: str(path), sha_key: reference['sha256']})
        self.freeze['files'] = files
        runtime_manifest = {'path': str(self.root / 'manifest.json'), 'bytes': 2, 'sha256': 'a' * 64}
        self.freeze['runtime_manifest'] = runtime_manifest
        frozen = self.write(live / 'frozen-argv.json', self.freeze)
        prepared_path = state.parent / 'prepared/prepared-case.json'
        prepared = self.write(prepared_path, {'startup': {'mode': 'workshop_cache'}, 'runtime_manifest': runtime_manifest})
        self.menu_refs = {
            'frozen_argv': frozen,
            'ready_context': self.write(live / 'ready-context.json', {'run_id': live.name,
                'run_dir': str(live), 'keeper_root': str(self.keeper), 'frozen_argv': frozen, 'prepared_case': prepared}),
            'prepared_case': prepared,
            'host_started': self.write(live / 'host-started.json', {'run_id': live.name, 'pid': 42,
                'supervisor_pid': 43, 'argv': argv, 'actual_popen_retained': True}),
            'host_exit': self.bundle['host_exit'], 'host_supervisor': self.bundle['host_supervisor'],
            'keeper_report': self.bundle['keeper_report'], 'keeper_parent_exit': self.bundle['keeper_parent_exit'],
            'keeper_process': self.write(live / 'keeper-process.json', {'pid': 44}),
        }
        self.menu_report = {'status': 'RED', 'phase': 'initializing-mcp', 'error': 'ExceptionGroup: original factory failed',
            'finished_at': '2026-10-24T03:00:41.073202+00:00', 'steps': [], 'session': {'report': None, 'error': None},
            'managed_session_done': False, 'managed_session_thread_finished': False, 'cleanup_ok': False,
            'frontend_mod_load_launch': {'status': 'WAITING_FOR_ACTUAL_SINGLE_MENU_LAUNCH'},
            'state_dir': str(state), 'agent_source_root': self.freeze['source_root'], 'identity': identity,
            'native_wire': str(live / 'native-report.native-wire.jsonl')}
        self.menu_refs['native_report'] = self.write(live / 'native-report.json', self.menu_report)
        stderr = live / 'native-report.server-stderr.log'
        stderr.write_text('in native_server\nregistration_mcp.py\ncontrols = Controls(service, driver)\n'
                          'driver.episode_projection == "native_campaign"\nValueError: One original ordinary service/driver\n')
        self.menu_refs['server_stderr'] = allocation.pin(stderr)
        failure = 'ValueError: Actual shared host failed; preserve error and do not replay'
        self.menu_refs['readiness_result'] = self.write(live / 'case-output/readiness-window-result.json',
            {'status': 'READINESS_ERROR', 'binding': {'run_id': live.name}, 'error': failure})
        self.menu_refs['entry_result'] = self.write(live / 'case-output/entry-run-result.json',
            {'run_id': live.name, 'case_error': failure, 'business_acceptance': 'RED_OR_INCOMPLETE'})
        self.bundle = {'schema': 'ck3-mod-acceptance-prelaunch-host-failure-closure-v1',
            'closure_kind': 'menu-mcp-initialization-before-native-session', 'machine_id': 'machine-test',
            'observed_at_utc': '2026-10-24T03:10:00+00:00', 'run_id': live.name, 'keeper_root': str(self.keeper),
            'normal_close_qualified': False, 'typed_normal_exit_proven': False, 'business_pass': False,
            'release_pass': False, 'native_cleanup_qualified': None, 'original_evidence': self.menu_refs}
        self.release = {'task': {'last_sequence': 11, 'state': 'done', 'resources': []}}
        self.save()

    def check_menu(self):
        with patch.object(allocation, 'closed_lease', return_value=True), \
             patch.object(allocation, 'runtime_process_inventory', return_value={'blockers': []}), \
             patch('psutil.pid_exists', return_value=False):
            return allocation.previous_prelaunch_host_failure_closure(
                self.run, self.freeze, self.close, self.keeper, self.release, self.bus)

    def test_r36_shape_preserves_false_cleanup_and_no_game_exit_credit(self):
        self.menu_initialization_failure()
        result = self.check_menu()['failure_cleanup']
        self.assertFalse(result['original_cleanup_ok'])
        self.assertIsNone(result['original_ck3_exit_code'])
        self.assertIsNone(result['native_cleanup_qualified'])
        self.assertFalse(result['normal_close_qualified'])
        self.assertFalse(result['business_pass'])

    def test_menu_failure_rejects_native_session_or_faked_complete_report(self):
        self.menu_initialization_failure()
        original = copy.deepcopy(self.menu_report)
        for change in ({'session': {'report': {'pid': 7}, 'error': None}}, {'cleanup_ok': True},
                       {'managed_session_thread_finished': True}, {'phase': 'native-ready'},
                       {'frontend_mod_load_launch': {'status': 'ACTUAL_SINGLE_MENU_LAUNCH_RECORDED'}}, {'readiness': None}):
            with self.subTest(change=change):
                self.menu_refs['native_report'] = self.write(self.run / 'native-report.json', {**original, **change})
                self.save()
                with self.assertRaises(ValueError):
                    self.check_menu()

    def test_menu_failure_rejects_native_wire_wrong_factory_and_boolean_wait(self):
        self.menu_initialization_failure()
        wire = self.run / 'native-report.native-wire.jsonl'
        wire.write_text('{"type":"hello"}\n')
        with self.assertRaisesRegex(ValueError, 'native communication'):
            self.check_menu()
        wire.unlink()
        self.exited['returncode'] = True
        self.menu_refs['host_exit'] = self.write(self.run / 'host-original-process-exit.json', self.exited)
        self.save()
        with self.assertRaisesRegex(ValueError, 'Popen wait1'):
            self.check_menu()

    def test_menu_failure_rejects_unknown_fields_and_actual_process_presence(self):
        self.menu_initialization_failure()
        self.bundle['unknown'] = True
        self.save()
        with self.assertRaisesRegex(ValueError, 'Exact menu'):
            self.check_menu()
        del self.bundle['unknown']
        self.save()
        with patch.object(allocation, 'closed_lease', return_value=True), \
             patch.object(allocation, 'runtime_process_inventory', return_value={'blockers': ['actual CK3']}), \
             patch('psutil.pid_exists', return_value=False):
            with self.assertRaisesRegex(ValueError, 'absence not proven'):
                allocation.previous_prelaunch_host_failure_closure(
                    self.run, self.freeze, self.close, self.keeper, self.release, self.bus)

    def test_saved_registrar_failure_accepts_actual_split_popen_shape(self):
        # Synthetic paths/lease, actual R0014 intent/process/wait field layout.
        state = Path(self.freeze['state_dir'])
        self.freeze['identity_allocation'] = {'machine_id': 'machine-test'}
        frozen = self.write(self.run / 'frozen-argv.json', self.freeze)
        prepared = self.write(self.root / 'common/prepared-d1-a01/prepared-case.json', {
            'startup': {'mode': 'saved_campaign', 'state_dir': str(state)}})
        self.bundle['prepared_case'] = prepared
        ready = {'run_id': self.run.name, 'run_dir': str(self.run),
                 'keeper_root': str(self.keeper), 'frozen_argv': frozen,
                 'prepared_case': prepared}
        self.bundle['ready_context'] = self.write(self.run / 'ready-context.json', ready)
        context = self.root / 'reviewed-context.json'
        self.write(context, ready)
        registrar = state / 'profile/mod-content/product/common/on_action/prepare.txt'
        stderr = self.run / 'host-stderr.log'
        trace = ('  File "shared-host.py", line 4148, in run\n'
            '    saved_campaign = prepare_saved_campaign(args, spec)\n'
            '  File "shared-host.py", line 591, in prepare_saved_campaign\n'
            '    raise ValueError("saved campaign product-only profile contains a cold-start registrar: " + str(path))\n'
            'ValueError: saved campaign product-only profile contains a cold-start registrar: ' + str(registrar) + '\n')
        stderr.write_text(trace, encoding='utf-8')
        self.bundle['host_stderr'] = allocation.pin(stderr)
        intent = {'at_utc': '2026-10-18T09:37:27.610345+00:00', 'ticket': 'a' * 64,
                  'run_id': self.run.name, 'frozen_argv': frozen,
                  'admitted_lease': {'task_id': self.freeze['screen_task']},
                  'proof': self.write(self.run / 'proof.json', {'reviewed': True}),
                  'challenge': self.write(self.run / 'challenge.json', {'nonce': 'actual'})}
        self.bundle['launch_intent'] = self.write(self.run / 'launch-intent.json', intent)
        host = json.loads((self.run / 'host-started.json').read_bytes())
        host.update({'at_utc': '2026-10-18T09:37:30.219670+00:00', 'supervisor_pid': 22016,
                     'admitted_lease': intent['admitted_lease'],
                     'direct_review': {key: intent[key] for key in ('proof', 'challenge')}})
        self.bundle['host_started'] = self.write(self.run / 'host-started.json', host)
        self.exited['at_utc'] = '2026-10-18T09:37:35.614307+00:00'
        self.bundle['host_exit'] = self.write(self.run / 'host-original-process-exit.json', self.exited)
        self.bundle['host_supervisor'] = self.write(self.run / 'host-supervisor-started.json', {
            'at_utc': '2026-10-18T09:37:27.625332+00:00', 'pid': 13664,
            'argv': ['python', 'launcher.py', '--run-root', str(self.run),
                     '--keeper-root', str(self.keeper), '--launch-ticket', intent['ticket'],
                     '--proof', intent['proof']['path'], '--challenge', intent['challenge']['path'], '--supervise']})
        for mode, code, pid in [('run', 2, 20320), ('allocate', 0, 21000)]:
            operation = self.root / 'common/operations' / (mode + '-a01')
            argv = ['python', 'entry.py', '--runtime', str(self.root / 'runtime.json'),
                    '--prepared-case', prepared['path']]
            argv += ['--run-context', str(context)] if mode == 'run' else ['--keeper-output', str(self.keeper)]
            argv.append(mode)
            self.bundle['public_' + mode] = self.write(operation / 'intent.json', {
                'machine_id': 'machine-test', 'at_utc': 'actual-start', 'stage': mode, 'argv': argv})
            self.bundle['public_' + mode + '_process'] = self.write(operation / 'original-process.json', {
                'machine_id': 'machine-test', 'pid': pid, 'create_time': 1792316243.6579444, 'argv': argv})
            self.bundle['public_' + mode + '_exit'] = self.write(operation / 'original-exit.json', {
                'machine_id': 'machine-test', 'pid': pid, 'completed_at_utc': 'actual-end',
                'actual_original_popen_wait': True, 'returncode': code})
        self.early_exit_result()
        result = self.check()['failure_cleanup']
        self.assertEqual(result['original_host_exit_code'], 1)
        self.assertFalse(result['normal_close_qualified'])
        self.assertFalse(result['business_pass'])
        self.assertIsNone(result['original_ck3_exit_code'])
        self.assertIn('public_run_exit', result['original_evidence'])
        self.assertIn('public_allocate_process', result['original_evidence'])
        self.assertEqual(result['supervisor_binding']['launcher_popen_pid'], 13664)
        self.assertEqual(result['supervisor_binding']['actual_supervise_pid'], 22016)
        self.assertFalse(result['supervisor_binding']['parent_child_relationship_observed'])
        intent['ticket'] = 'b' * 64
        self.bundle['launch_intent'] = self.write(self.run / 'launch-intent.json', intent)
        self.save()
        with self.assertRaisesRegex(ValueError, 'launch ticket/lease chain'):
            self.check()
        intent['ticket'] = 'a' * 64
        self.bundle['launch_intent'] = self.write(self.run / 'launch-intent.json', intent)
        self.save()
        exit_path = Path(self.bundle['public_run_exit']['path'])
        ended = json.loads(exit_path.read_bytes())
        ended['actual_original_popen_wait'] = False
        self.bundle['public_run_exit'] = self.write(exit_path, ended)
        self.save()
        with self.assertRaisesRegex(ValueError, 'retained wait'):
            self.check()
        ended['actual_original_popen_wait'] = True
        self.bundle['public_run_exit'] = self.write(exit_path, ended)
        self.save()
        (self.run / 'native-report.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'native/game/control'):
            self.check()
        (self.run / 'native-report.json').unlink()
        stderr.write_text('ValueError: arbitrary saved campaign failure\n')
        self.bundle['host_stderr'] = allocation.pin(stderr)
        self.save()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_exact_failed_host_resources_only(self):
        value = self.check()
        self.assertEqual(value['mode'], 'previous-shared-prelaunch-host-failure')
        self.assertEqual(value['failure_cleanup']['original_host_exit_code'], 1)
        self.assertFalse(value['failure_cleanup']['business_pass'])
        self.assertFalse(value['failure_cleanup']['normal_close_qualified'])
        self.assertIsNone(value['failure_cleanup']['original_ck3_exit_code'])

    def test_exit_zero_cannot_claim_this_failure_route(self):
        self.exited['returncode'] = 0
        self.bundle['host_exit'] = self.write(self.run / 'host-original-process-exit.json', self.exited)
        self.save()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_projection_hash_failure_keeps_resource_only_credit(self):
        path = self.run / 'host-stderr.log'
        path.write_text('ValueError: effective host differs from reviewed projection\n')
        self.bundle['host_stderr'] = allocation.pin(path)
        self.save()
        value = self.check()['failure_cleanup']
        self.assertFalse(value['normal_close_qualified'])
        self.assertFalse(value['business_pass'])
        self.assertIsNone(value['original_ck3_exit_code'])

    def test_unrecognized_host_failure_is_rejected(self):
        path = self.run / 'host-stderr.log'
        path.write_text('ValueError: arbitrary failure after starting game\n')
        self.bundle['host_stderr'] = allocation.pin(path)
        self.save()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_gui_inventory_rejection_keeps_prelaunch_failure_credit(self):
        path = self.run / 'host-stderr.log'
        path.write_text('ValueError: normal-exit private V1 does not support enabled mod GUI files\n')
        self.bundle['host_stderr'] = allocation.pin(path)
        self.save()
        value = self.check()['failure_cleanup']
        self.assertFalse(value['normal_close_qualified'])
        self.assertFalse(value['business_pass'])

    def early_exit_result(self):
        self.bundle['readiness_result'] = self.write(self.run / 'case-output/readiness-window-result.json', {
            'status': 'READINESS_HOST_EXIT_BEFORE_REPORT', 'binding': {'run_id': self.run.name},
            'host_exit_before_report': {**{key: self.bundle[key] for key in
                ('host_started', 'host_exit', 'host_stderr')}, 'host_returncode': 1,
                'native_report_observed': False, 'normal_close_qualified': False,
                'native_exit_zero_proven': False, 'business_pass': False}})
        self.bundle['entry_run_result'] = self.write(self.run / 'case-output/entry-run-result.json', {
            'run_id': self.run.name, 'launcher_exit_code': 0,
            'case_error': 'ValueError: Original shared host exited before report: retained exit 1',
            'business_acceptance': 'RED_OR_INCOMPLETE'})
        self.save()

    def allocated_profile_failure(self) -> None:
        """Replay R0001's background launcher shim, ticket, and original wait fields."""
        from test_steam_offline_state_probe import native_sample
        steam = native_sample().to_wire()
        machine = steam['machine_id']
        self.freeze['identity_allocation'] = {'machine_id': machine}
        selected = self.root / 'shared-host.py'
        selected.write_text('# frozen selected host fixture\n')
        profile_path = self.run / 'normal-exit-binding/normal-exit-managed-profile.json'
        profile = self.write(profile_path, {'state_directory': self.freeze['state_dir'],
            'evidence_directory': str(self.run)})
        argv = ['python', '-B', '-X', 'utf8', str(selected), '--output',
            str(self.run / 'native-report.json'), '--normal-exit-managed-profile', str(profile_path),
            '--normal-exit-managed-profile-sha256', profile['sha256']]
        self.freeze['argv'] = argv
        self.freeze['files'] = {str(selected.resolve()): {
            key: value for key, value in allocation.pin(selected).items() if key != 'path'}}
        frozen = self.write(self.run / 'frozen-argv.json', self.freeze)
        prepared = self.write(self.root / 'prepared/prepared-case.json', {
            'startup': {'mode': 'fixture', 'state_dir': self.freeze['state_dir']}})
        ready = {'run_id': self.run.name, 'run_dir': str(self.run), 'keeper_root': str(self.keeper),
            'frozen_argv': frozen, 'prepared_case': prepared, 'normal_exit_managed_profile': profile}
        self.bundle['ready_context'] = self.write(self.run / 'ready-context.json', ready)
        self.bundle['prepared_case'] = prepared
        self.bundle['normal_exit_managed_profile'] = profile
        receipt = self.write(self.run / 'steam-offline.json', steam)
        admission = {'schema': 'ck3-mod-acceptance-background-offline-admission-v1',
            'machine_id': machine, 'observed_at_utc': steam['observed_at_utc'], 'receipt': receipt,
            'steam_pid': steam['steam']['pid'], 'steam_birth_filetime': steam['steam']['birth_filetime'],
            'observation_method': 'native_current_user_byte', 'background_only': True}
        lease = {'schema': 'xar.promo.screen-lease-cas/v1', 'task_id': self.freeze['screen_task'],
            'sequence': 11, 'screen_resource': 'ck3-screen:acquired'}
        intent = {'schema': 'ck3-mod-acceptance-background-launch-intent-v1',
            'run_id': self.run.name, 'frozen_argv': frozen, 'ticket': 'a' * 64,
            'admitted_lease': lease, 'steam_offline_receipt': receipt,
            'background_admission': admission, 'at_utc': '2026-10-24T18:00:45+00:00'}
        self.bundle['launch_intent'] = self.write(self.run / 'launch-intent.json', intent)
        self.bundle['host_supervisor'] = self.write(self.run / 'host-supervisor-started.json', {
            'pid': 23044, 'machine_id': machine, 'at_utc': '2026-10-24T18:00:46+00:00',
            'original_popen_identity': {'pid': 23044, 'birth_filetime': '134373384451646822'},
            'argv': ['python', 'launcher.py', '--run-root', str(self.run), '--keeper-root', str(self.keeper),
                     '--steam-offline-receipt', receipt['path'], '--supervise', '--launch-ticket', 'a' * 64]})
        self.bundle['host_started'] = self.write(self.run / 'host-started.json', {
            'run_id': self.run.name, 'pid': 5428, 'supervisor_pid': 25944, 'argv': argv,
            'actual_popen_retained': True, 'at_utc': '2026-10-24T18:00:47+00:00',
            'admitted_lease': lease, 'background_offline_admission': admission})
        self.exited.update(pid=5428, at_utc='2026-10-24T18:00:48+00:00')
        self.bundle['host_exit'] = self.write(self.run / 'host-original-process-exit.json', self.exited)
        terminal = 'This selected projection derives the actual profile once; supplied replacement is forbidden'
        stderr = self.run / 'host-stderr.log'
        stderr.write_text(f'Traceback (most recent call last):\n  File "{selected}", line 5229, in <module>\n'
            f'    raise SystemExit(main())\n  File "{selected}", line 5222, in main\n'
            f"    raise ValueError('{terminal}')\nValueError: {terminal}\n")
        self.bundle['host_stderr'] = allocation.pin(stderr)
        context = self.write(self.root / 'reviewed-context.json', ready)
        for key, mode, code in [('public_run', 'run', 2), ('public_allocate', 'allocate', 0)]:
            original = json.loads(Path(self.bundle[key]['path']).read_bytes())
            original['argv'][original['argv'].index('--prepared-case') + 1] = prepared['path']
            value = {'machine_id': machine, 'argv': original['argv'], 'original_wait_returncode': code,
                'started_at_utc': '2026-10-24T18:00:42+00:00', 'elapsed_seconds': 5.5}
            if mode == 'run':
                value.update(run_id=self.run.name, finished_at_utc='2026-10-24T18:00:49+00:00')
            self.bundle[key] = self.write(Path(self.bundle[key]['path']), value)
        self.early_exit_result()

    def test_allocated_profile_background_shim_chain_has_resource_credit_only(self):
        self.allocated_profile_failure()
        result = self.check()['failure_cleanup']
        binding = result['supervisor_binding']
        self.assertEqual((binding['launcher_popen_pid'], binding['actual_supervise_pid']), (23044, 25944))
        self.assertFalse(binding['parent_child_relationship_observed'])
        self.assertIsNone(result['native_cleanup_qualified'])
        self.assertIsNone(result['original_ck3_exit_code'])
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['normal_close_qualified'])

    def test_allocated_profile_background_chain_rejects_wrong_ticket_or_wait(self):
        self.allocated_profile_failure()
        for key, field, bad in [('launch_intent', 'ticket', 'b' * 64),
                                ('public_run', 'original_wait_returncode', 0),
                                ('host_supervisor', 'pid', True)]:
            path = Path(self.bundle[key]['path'])
            original = json.loads(path.read_bytes())
            self.bundle[key] = self.write(path, {**original, field: bad})
            self.save()
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check()
            self.bundle[key] = self.write(path, original)
        self.save()

    def test_allocated_profile_terminal_without_frozen_main_stack_is_rejected(self):
        self.allocated_profile_failure()
        path = self.run / 'host-stderr.log'
        path.write_text(path.read_text().replace('in main', 'in run_game'))
        self.bundle['host_stderr'] = allocation.pin(path)
        self.early_exit_result()
        with self.assertRaisesRegex(ValueError, 'pre-game main stack'):
            self.check()

    def test_allocated_profile_unknown_cause_is_rejected(self):
        self.allocated_profile_failure()
        path = self.run / 'host-stderr.log'
        path.write_text('ValueError: unrelated late game failure\n')
        self.bundle['host_stderr'] = allocation.pin(path)
        self.early_exit_result()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_bound_early_host_exit_does_not_require_readiness_timeout(self):
        self.early_exit_result()
        value = self.check()['failure_cleanup']
        self.assertFalse(value['normal_close_qualified'])
        self.assertFalse(value['business_pass'])

    def test_early_host_exit_cannot_rebind_original_receipt(self):
        self.early_exit_result()
        path = self.run / 'case-output/readiness-window-result.json'
        value = json.loads(path.read_text(encoding='utf-8'))
        value['host_exit_before_report']['host_exit']['sha256'] = '0' * 64
        self.bundle['readiness_result'] = self.write(path, value)
        self.save()
        with self.assertRaisesRegex(ValueError, 'RED/readiness result'):
            self.check()

    def test_native_report_presence_rejects_prelaunch_claim(self):
        (self.run / 'native-report.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'native/game/control'):
            self.check()

    def cache_identity_failure(self):
        state = Path(self.freeze['state_dir'])
        self.freeze['identity_allocation'] = {'machine_id': 'machine-test'}
        frozen = self.write(self.run / 'frozen-argv.json', self.freeze)
        profile = self.write(state.parent / 'prepared/profile-preparation.json', {
            'schema': 'ck3-mod-acceptance-prepared-workshop-cache-v1',
            'state_dir': str(state), 'fixture_mounted': False,
            'campaign_started': False, 'cache_content_copied': False})
        prepared = self.write(state.parent / 'prepared/prepared-case.json', {
            'case': 'workshop_cache', 'startup': {'mode': 'workshop_cache'},
            'preparation': {'profile_preparation': profile}})
        self.bundle['prepared_case'] = prepared
        self.bundle['profile_preparation'] = profile
        self.bundle['ready_context'] = self.write(self.run / 'ready-context.json', {
            'run_id': self.run.name, 'run_dir': str(self.run), 'keeper_root': str(self.keeper),
            'frozen_argv': frozen, 'prepared_case': prepared})
        stderr = self.run / 'host-stderr.log'
        stderr.write_text('  File "host_entry.py", line 185, in main\n'
            '    profile = helper.create_profile(args, runtime, manifest)\n'
            '  File "ck3_mod_acceptance_normal_exit_profile.py", line 87, in create_profile\n'
            '  File "ck3_mod_acceptance_normal_exit_profile.py", line 48, in project_profile\n'
            'ValueError: public preparation and selected runtime identities differ\n')
        self.bundle['host_stderr'] = allocation.pin(stderr)
        run = json.loads(Path(self.bundle['public_run']['path']).read_bytes())
        allocate = json.loads(Path(self.bundle['public_allocate']['path']).read_bytes())
        self.bundle['public_run'] = self.write(self.run / 'public-run-original-command.json', {
            'argv': run['argv'], 'at_utc': 'original-start', 'machine_id': 'machine-test'})
        public_exit = {'run_id': self.run.name, 'machine_id': 'machine-test', 'pid': 50,
            'actual_original_popen_wait': True, 'returncode': 2, 'at_utc': 'original-end',
            'business_pass_inferred': False}
        self.bundle['public_run_exit'] = self.write(self.run / 'public-run-original-exit.json', public_exit)
        start = {'argv': allocate['argv'], 'pid': 51, 'at_utc': 'allocation-start'}
        self.bundle['public_allocate_start'] = self.write(self.run / 'root-allocation-original-command.json', start)
        self.bundle['public_allocate'] = self.write(self.run / 'root-allocation-completion.json',
            {**start, 'returncode': 0, 'completed_at_utc': 'allocation-end'})
        self.bundle['pre_game_red'] = self.write(self.run / 'root-pre-game-red.json', {
            'run_id': self.run.name, 'machine_id': 'machine-test', 'host_actual_wait': self.exited,
            'public_actual_wait': public_exit, 'native_report_exists': False,
            'actual_ck3_inventory': [], 'game_launch_not_observed': True,
            'normal_exit_pass': False, 'cache_load_pass': False})
        self.early_exit_result()

    def test_cache_identity_failure_accepts_actual_split_original_receipts_only(self):
        self.cache_identity_failure()
        result = self.check()['failure_cleanup']
        self.assertEqual(result['original_host_exit_code'], 1)
        self.assertTrue(result['original_host_wait_proven'])
        self.assertFalse(result['normal_close_qualified'])
        self.assertFalse(result['typed_normal_exit_proven'])
        self.assertFalse(result['business_pass'])
        self.assertIsNone(result['original_ck3_exit_code'])
        self.assertIn('public_run_exit', result['original_evidence'])
        self.assertIn('public_allocate_start', result['original_evidence'])

    def test_cache_identity_failure_requires_original_host_exit_one(self):
        self.cache_identity_failure()
        self.exited['returncode'] = 2
        self.bundle['host_exit'] = self.write(self.run / 'host-original-process-exit.json', self.exited)
        self.save()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_cache_identity_message_without_prelaunch_projection_stack_is_rejected(self):
        self.cache_identity_failure()
        path = self.run / 'host-stderr.log'
        path.write_text('ValueError: public preparation and selected runtime identities differ\n')
        self.bundle['host_stderr'] = allocation.pin(path)
        self.early_exit_result()
        with self.assertRaisesRegex(ValueError, 'host exit/cause'):
            self.check()

    def test_cache_identity_failure_requires_actual_retained_public_wait(self):
        self.cache_identity_failure()
        path = self.run / 'public-run-original-exit.json'
        value = json.loads(path.read_bytes())
        value['actual_original_popen_wait'] = False
        self.bundle['public_run_exit'] = self.write(path, value)
        self.save()
        with self.assertRaisesRegex(ValueError, 'retained wait'):
            self.check()

    def test_cache_identity_failure_cannot_rebind_allocation_parent(self):
        self.cache_identity_failure()
        path = self.run / 'root-allocation-completion.json'
        value = json.loads(path.read_bytes())
        value['pid'] = 52
        self.bundle['public_allocate'] = self.write(path, value)
        self.save()
        with self.assertRaisesRegex(ValueError, 'parent completion'):
            self.check()

    def test_cache_identity_failure_requires_original_cache_and_empty_observation(self):
        self.cache_identity_failure()
        path = self.run / 'root-pre-game-red.json'
        value = json.loads(path.read_bytes())
        value['actual_ck3_inventory'] = [{'pid': 123}]
        self.bundle['pre_game_red'] = self.write(path, value)
        self.save()
        with self.assertRaisesRegex(ValueError, 'pre-game RED'):
            self.check()
        value['actual_ck3_inventory'] = []
        self.bundle['pre_game_red'] = self.write(path, value)
        path = Path(self.bundle['prepared_case']['path'])
        prepared = json.loads(path.read_bytes());prepared['case'] = 'not-cache'
        self.bundle['prepared_case'] = self.write(path, prepared)
        ready_path = self.run / 'ready-context.json'
        ready = json.loads(ready_path.read_bytes());ready['prepared_case'] = self.bundle['prepared_case']
        self.bundle['ready_context'] = self.write(ready_path, ready)
        self.save()
        with self.assertRaisesRegex(ValueError, 'original prepared cache'):
            self.check()



if __name__ == '__main__':
    unittest.main()
