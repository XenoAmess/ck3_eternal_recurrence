"""A failed host before CK3 startup can release resources without business credit."""
import json
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

    def test_native_report_presence_rejects_prelaunch_claim(self):
        (self.run / 'native-report.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'native/game/control'):
            self.check()


if __name__ == '__main__':
    unittest.main()
