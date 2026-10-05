import unittest
from xar_autoplayer.bridge.normal_exit_process_observer_v1 import (
    RetainedProcessObserver, PROCESS_QUERY_LIMITED_INFORMATION, SYNCHRONIZE,
    WAIT_OBJECT_0, WAIT_TIMEOUT, WAIT_FAILED,
)


class FakeApi:
    def __init__(self, pid=43, creation=133000000000000043):
        self.pid, self.creation = pid, creation
        self.calls = []
        self.wait_result, self.code = WAIT_TIMEOUT, 259
        self.wait_error = self.code_error = None

    def open_process(self, access, pid):
        self.calls.append(('open', access, pid)); return 77

    def process_id(self, handle):
        self.calls.append(('pid', handle)); return self.pid

    def creation_filetime(self, handle):
        self.calls.append(('creation', handle)); return self.creation

    def wait(self, handle, timeout_ms):
        self.calls.append(('wait', handle, timeout_ms))
        if self.wait_error: raise self.wait_error
        return self.wait_result

    def exit_code(self, handle):
        self.calls.append(('exit', handle))
        if self.code_error: raise self.code_error
        return self.code

    def close(self, handle): self.calls.append(('close', handle))


class ObserverTests(unittest.TestCase):
    def pin(self, api):
        return RetainedProcessObserver(api, 43, 133000000000000043,
                                       clock=lambda: 100, token_factory=lambda: 'original')

    def test_query_only_access_and_original_handle(self):
        api = FakeApi()
        with self.pin(api) as observer:
            observer.verify_before_dispatch()
            api.wait_result, api.code = WAIT_OBJECT_0, 0
            facts = observer.observe(123)
        self.assertEqual(api.calls[0], ('open', SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, 43))
        self.assertEqual(sum(c[0] == 'open' for c in api.calls), 1)
        self.assertEqual(facts['retained_handle_token'], 'original')
        self.assertTrue(facts['process_exit_observed'])
        self.assertEqual(api.calls[-1], ('close', 77))

    def test_exact_creation_rejects_float_and_bool_without_opening(self):
        for value in [True, 133000000000000043.0]:
            api = FakeApi()
            with self.assertRaises(ValueError): RetainedProcessObserver(api, 43, value)
            self.assertEqual(api.calls, [])

    def test_pid_reuse_rejects_and_closes_original_handle(self):
        for api in [FakeApi(pid=44), FakeApi(creation=133000000000000044)]:
            with self.assertRaises(ValueError): self.pin(api)
            self.assertEqual(api.calls[-1], ('close', 77))

    def test_preconfirm_rechecks_exact_identity(self):
        api = FakeApi()
        with self.pin(api) as observer:
            api.creation += 1
            with self.assertRaises(ValueError): observer.verify_before_dispatch()
        self.assertFalse(any(c[0] == 'exit' for c in api.calls))

    def test_preconfirm_rejects_already_dead_process(self):
        api = FakeApi()
        with self.pin(api) as observer:
            api.wait_result = WAIT_OBJECT_0
            with self.assertRaises(ValueError): observer.verify_before_dispatch()

    def test_timeout_code_zero_is_not_exit(self):
        api = FakeApi(); api.code = 0
        with self.pin(api) as observer: facts = observer.observe(0)
        self.assertFalse(facts['process_exit_observed'])
        self.assertEqual(facts['wait_state'], 'timeout')
        self.assertEqual(facts['exit_code'], 0)

    def test_signaled_259_is_real_nonzero_exit(self):
        api = FakeApi(); api.wait_result = WAIT_OBJECT_0
        with self.pin(api) as observer: facts = observer.observe()
        self.assertTrue(facts['process_exit_observed'])
        self.assertEqual(facts['exit_code'], 259)

    def test_wait_failure_still_independently_reads_exit_code(self):
        api = FakeApi(); api.wait_error = OSError('injected'); api.code = 0
        with self.pin(api) as observer: facts = observer.observe()
        self.assertEqual(facts['wait_result'], WAIT_FAILED)
        self.assertEqual(facts['exit_code'], 0)
        self.assertFalse(facts['process_exit_observed'])
        self.assertTrue(any(c[0] == 'exit' for c in api.calls))

    def test_exit_code_read_failure_does_not_establish_exit(self):
        api = FakeApi(); api.wait_result = WAIT_OBJECT_0; api.code_error = OSError('injected')
        with self.pin(api) as observer: facts = observer.observe()
        self.assertIsNone(facts['exit_code'])
        self.assertFalse(facts['process_exit_observed'])

    def test_native_bool_exit_code_rejected(self):
        api = FakeApi(); api.wait_result = WAIT_OBJECT_0; api.code = False
        with self.pin(api) as observer: facts = observer.observe()
        self.assertIsNone(facts['exit_code'])
        self.assertFalse(facts['process_exit_observed'])

    def test_wait_bounds_and_closed_handle(self):
        api = FakeApi()
        observer = self.pin(api)
        for value in [-1, 30_001, True, 1.0]:
            with self.assertRaises(ValueError): observer.observe(value)
        observer.close(); observer.close()
        with self.assertRaises(RuntimeError): observer.observe()
        self.assertEqual(sum(c[0] == 'close' for c in api.calls), 1)

    def test_cleanup_failure_does_not_erase_independent_exit_fact(self):
        api = FakeApi(); api.wait_result = WAIT_OBJECT_0; api.code = 0
        def fail_close(handle): raise OSError('injected close failure')
        api.close = fail_close
        with self.pin(api) as observer: facts = observer.observe()
        self.assertTrue(facts['process_exit_observed'])
        self.assertEqual(facts['exit_code'], 0)
        self.assertIn('injected close failure', observer.close_error)


if __name__ == '__main__': unittest.main()
