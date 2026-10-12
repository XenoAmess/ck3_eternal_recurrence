"""Exercise actual normal_close with deterministic retained-handle outcomes.

Only the source AST is loaded. No client module import, native kernel, process,
game, GUI, public CLI, queue or task-bus call is made; checkpoints stay in RAM.
"""
import ast
import contextlib
import io
from pathlib import Path
from types import SimpleNamespace
import unittest

SOURCE = Path(__file__).resolve().parent / 'ck3_mod_acceptance_client.py'


def normal_close_method(clock):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8-sig'), str(SOURCE))
    methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'normal_close']
    if len(methods) != 1:
        raise AssertionError('Exactly one actual normal_close required')

    def require(ok, message):
        if not ok:
            raise ValueError(message)

    def no_review(_):
        raise AssertionError('No GUI result may be manufactured')

    namespace = dict(require=require, read_json=no_review, time=clock)
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace['normal_close']


class Clock:
    def __init__(self):
        self.elapsed = 0.0
        self.sleeps = 0

    def sleep(self, seconds):
        self.elapsed += seconds
        self.sleeps += 1


class Kernel:
    def __init__(self, signaled_from_call, exit_code):
        self.signaled_from_call = signaled_from_call
        self.exit_code = exit_code
        self.wait_calls = 0
        self.exit_reads = 0

    def WaitForSingleObject(self, handle, timeout):
        if (handle, timeout) != (123, 0):
            raise AssertionError('Original retained handle/zero-time poll changed')
        self.wait_calls += 1
        return 0 if self.wait_calls >= self.signaled_from_call else 258

    def GetExitCodeProcess(self, handle, pointer):
        if handle != 123:
            raise AssertionError('Wrong retained handle')
        self.exit_reads += 1
        pointer._obj.value = self.exit_code
        return 1


class MissingResponse:
    def is_file(self):
        return False

    def __str__(self):
        return 'RAM-only/missing-normal-quit-root-result.json'


class Output:
    def __truediv__(self, _):
        return MissingResponse()


class FakeClient:
    def __init__(self, clock, kernel):
        self.clock, self._kernel, self._handle = clock, kernel, 123
        self._process = dict(pid=404, create_time=1234.5, retained_synchronize_query_handle_acquired=True)
        self.frozen = dict(run_id='test-retained-process', screen_task='RAM-only')
        self._hold = 999.0
        self.live, self.keeper = Path('RAM-only-live'), Path('RAM-only-keeper')
        self.output = Output()
        self.selection = SimpleNamespace(normal_quit_automation=None)
        self.checkpoints, self.report_reads = {}, 0

    def remaining(self):
        return .2 - self.clock.elapsed

    def normal_quit_reviewer(self):
        return '/root'

    def checkpoint(self, name, value):
        self.checkpoints[name] = value
        return 'RAM-only/' + name + '.json'

    def read_report(self, allow_error=False):
        if allow_error is not True:
            raise AssertionError('Actual error must remain readable')
        self.report_reads += 1
        return dict(error='RuntimeError: actual native page failed', finished_at='original-finished',
            managed_session_thread_finished=True, cleanup_ok=True)

    def native_zero_proof(self, _):
        return None

    def native_failure_shutdown_proof(self, _):
        return None

    def execute_plan(self, *args, **kwargs):
        raise AssertionError('No runtime/queue operation permitted')


class ManualQuitRetainedExit(unittest.TestCase):
    def exercise(self, signaled_from_call, exit_code):
        clock = Clock()
        kernel = Kernel(signaled_from_call, exit_code)
        client = FakeClient(clock, kernel)
        with contextlib.redirect_stdout(io.StringIO()):
            result = normal_close_method(clock)(client, 'failed')
        self.assertFalse(result['business_pass'])
        self.assertFalse(result['normal_close_qualified'])
        self.assertFalse(result['failure_lifecycle_completed'])
        self.assertIsNone(result['root_normal_gui_review'])
        self.assertIsNone(result['native_zero_proof'])
        self.assertEqual(result['host_error'], 'RuntimeError: actual native page failed')
        self.assertEqual(client.checkpoints['actual-retained-handle-os-exit'], result['retained_handle'])
        return clock, kernel, result

    def test_signaled_handle_breaks_manual_wait_and_reads_actual_nonzero_exit(self):
        clock, kernel, result = self.exercise(2, 1)
        self.assertEqual(clock.sleeps, 0)
        self.assertEqual(kernel.exit_reads, 1)
        self.assertTrue(result['retained_handle']['signaled'])
        self.assertEqual(result['retained_handle']['exit_code'], 1)
        self.assertFalse(result['retained_handle']['actual_retained_os0'])

    def test_live_handle_keeps_polling_then_real_os0_does_not_forge_gui_or_normal_pass(self):
        clock, kernel, result = self.exercise(3, 0)
        self.assertEqual(clock.sleeps, 1)
        self.assertEqual(kernel.exit_reads, 1)
        self.assertTrue(result['retained_handle']['actual_retained_os0'])
        self.assertFalse(result['normal_close_qualified'])

    def test_original_deadline_stops_running_handle_without_manufacturing_exit(self):
        clock, kernel, result = self.exercise(100, 1)
        self.assertEqual(clock.sleeps, 2)
        self.assertEqual(kernel.exit_reads, 0)
        self.assertFalse(result['retained_handle']['signaled'])
        self.assertIsNone(result['retained_handle']['exit_code'])
        self.assertFalse(result['retained_handle']['actual_retained_os0'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
