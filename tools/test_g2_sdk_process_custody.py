"""SDK process custody tests using fake handles and factories only."""

from __future__ import annotations

import ctypes
import subprocess
from types import SimpleNamespace
import unittest
from unittest import mock

with mock.patch.object(ctypes, "WinDLL", create=True,
                       side_effect=AssertionError("native process API forbidden during import")), \
        mock.patch.object(subprocess, "Popen",
                          side_effect=AssertionError("process launch forbidden during import")):
    from g2_saved_campaign import sdk_process_custody as custody


PID = 1234
CREATED = 134_363_025_952_867_701
IMAGE = r"C:\isolated-sdk\python.exe"


class FakeProcessAPI:
    """Every observation must use this one handle, never a reopened PID."""

    def __init__(self):
        self.handle = object()
        self.creation_filetime = CREATED
        self.executable = IMAGE
        self.wait_result = 258
        self.exit_code = 259
        self.failures = {}
        self.calls = []

    def _call(self, name, value):
        self.calls.append((name, value))
        if name != "open_process" and value is not self.handle:
            raise AssertionError("API received a different handle")
        if name in self.failures:
            raise self.failures[name]

    def open_process(self, pid):
        self._call("open_process", pid)
        return self.handle

    def query_creation_filetime(self, handle):
        self._call("query_creation_filetime", handle)
        return self.creation_filetime

    def query_executable(self, handle):
        self._call("query_executable", handle)
        return self.executable

    def wait_zero(self, handle):
        self._call("wait_zero", handle)
        return self.wait_result

    def get_exit_code(self, handle):
        self._call("get_exit_code", handle)
        return self.exit_code

    def close_handle(self, handle):
        self._call("close_handle", handle)

    def count(self, name):
        return sum(actual == name for actual, _ in self.calls)


class ProcessGenerationTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeProcessAPI()
        for target, attribute in ((ctypes, "WinDLL"), (subprocess, "Popen")):
            patcher = mock.patch.object(
                target, attribute, create=True,
                side_effect=AssertionError("tests must use fake process custody only"),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def capture(self, **kwargs):
        result = custody.RetainedProcessGeneration.capture(PID, api=self.api, **kwargs)
        self.addCleanup(result.close)
        return result

    def test_exact_generation_and_image_are_retained(self):
        generation = self.capture(expected_executable=IMAGE,
                                  expected_creation_filetime=CREATED)
        self.assertEqual(generation.identity("sdk_application"), {
            "role": "sdk_application", "pid": PID,
            "creation_filetime": CREATED, "executable": IMAGE,
        })
        self.assertEqual(self.api.count("open_process"), 1)

    def test_public_generation_identity_is_readonly_and_detached(self):
        generation = self.capture()
        before = generation.identity("sdk_application")
        for attribute, value in (("pid", PID + 1), ("creation_filetime", CREATED + 1),
                                 ("executable", r"C:\replacement\python.exe")):
            with self.subTest(attribute=attribute), self.assertRaises(AttributeError):
                setattr(generation, attribute, value)
        detached = generation.identity("sdk_application")
        detached["pid"] = PID + 1
        self.assertEqual(generation.identity("sdk_application"), before)

    def test_wrong_creation_generation_is_rejected_and_closed(self):
        with self.assertRaises(custody.ProcessCustodyError):
            self.capture(expected_creation_filetime=CREATED + 1)
        self.assertEqual(self.api.count("open_process"), 1)
        self.assertEqual(self.api.count("close_handle"), 1)

    def test_wrong_executable_is_rejected_and_closed(self):
        with self.assertRaises(custody.ProcessCustodyError):
            self.capture(expected_executable=r"C:\other-sdk\python.exe")
        self.assertEqual(self.api.count("close_handle"), 1)

    def test_invalid_pid_is_rejected_before_open(self):
        for pid in (None, True, False, 0, -1, 1.5, "1234"):
            with self.subTest(pid=pid), self.assertRaises(custody.ProcessCustodyError):
                custody.RetainedProcessGeneration.capture(pid, api=self.api)
        self.assertEqual(self.api.count("open_process"), 0)

    def test_identity_query_failure_closes_retained_handle(self):
        for method in ("query_creation_filetime", "query_executable"):
            with self.subTest(method=method):
                api = FakeProcessAPI()
                api.failures[method] = OSError("fake identity query failed")
                with self.assertRaises(OSError) as raised:
                    custody.RetainedProcessGeneration.capture(PID, api=api)
                self.assertIs(raised.exception, api.failures[method])
                self.assertEqual(api.count("open_process"), 1)
                self.assertEqual(api.count("close_handle"), 1)

    def test_open_failure_has_no_handle_to_close(self):
        self.api.failures["open_process"] = OSError("fake open failed")
        with self.assertRaises(OSError) as raised:
            self.capture()
        self.assertIs(raised.exception, self.api.failures["open_process"])
        self.assertEqual(self.api.count("close_handle"), 0)

    def test_observation_uses_same_handle_without_reopening_pid(self):
        generation = self.capture()
        first = generation.observe()
        self.api.creation_filetime = CREATED + 100
        self.api.executable = r"C:\replacement\python.exe"
        second = generation.observe()
        self.assertEqual(self.api.count("open_process"), 1)
        self.assertEqual(self.api.count("query_creation_filetime"), 1)
        self.assertEqual(self.api.count("query_executable"), 1)
        for row in (first, second):
            self.assertEqual(row["pid"], PID)
            self.assertEqual(row["creation_filetime"], CREATED)
            self.assertEqual(row["executable"], IMAGE)
        self.assertEqual(self.api.count("wait_zero"), 2)

    def test_signaled_handle_proves_exit_even_when_exit_code_is_259(self):
        generation = self.capture()
        self.api.wait_result = 0
        for code in (0, 1, 259):
            with self.subTest(exit_code=code):
                self.api.exit_code = code
                row = generation.observe()
                self.assertIs(row["kernel_exit_observed"], True)
                self.assertEqual(row["wait_result"], 0)
                self.assertEqual(row["exit_code"], code)
                self.assertIsNone(row["observation_error"])
                with self.assertRaises(custody.ProcessCustodyError):
                    generation.require_live()

    def test_timeout_does_not_prove_exit_even_with_exit_code_zero(self):
        generation = self.capture()
        for code in (0, 259):
            with self.subTest(exit_code=code):
                self.api.exit_code = code
                row = generation.require_live()
                self.assertIs(row["kernel_exit_observed"], False)
                self.assertEqual(row["wait_result"], 258)
                self.assertEqual(row["exit_code"], code)

    def test_unknown_wait_result_remains_unknown(self):
        generation = self.capture()
        self.api.wait_result = 0xFFFFFFFF
        row = generation.observe()
        self.assertIsNone(row["kernel_exit_observed"])
        self.assertEqual(row["wait_result"], 0xFFFFFFFF)
        self.assertIsNotNone(row["observation_error"])
        with self.assertRaises(custody.ProcessCustodyError):
            generation.require_live()

    def test_wait_api_failure_remains_unknown(self):
        generation = self.capture()
        self.api.failures["wait_zero"] = OSError("fake wait failed")
        row = generation.observe()
        self.assertIsNone(row["kernel_exit_observed"])
        self.assertIsNone(row["wait_result"])
        self.assertIsNotNone(row["observation_error"])
        with self.assertRaises(custody.ProcessCustodyError):
            generation.require_live()

    def test_exit_code_failure_preserves_independent_signal_and_refuses_live(self):
        generation = self.capture()
        self.api.failures["get_exit_code"] = OSError("fake exit query failed")
        for wait_result, signaled in ((0, True), (258, False)):
            with self.subTest(wait_result=wait_result):
                self.api.wait_result = wait_result
                row = generation.observe()
                self.assertIs(row["kernel_exit_observed"], signaled)
                self.assertEqual(row["wait_result"], wait_result)
                self.assertIsNone(row["exit_code"])
                self.assertIsNotNone(row["observation_error"])
                with self.assertRaises(custody.ProcessCustodyError):
                    generation.require_live()

    def test_close_is_one_attempt_and_closed_observation_is_unknown(self):
        generation = self.capture()
        generation.close()
        generation.close()
        self.assertEqual(self.api.count("close_handle"), 1)
        waits = self.api.count("wait_zero")
        row = generation.observe()
        self.assertIsNone(row["kernel_exit_observed"])
        self.assertIsNotNone(row["observation_error"])
        self.assertEqual(self.api.count("wait_zero"), waits)


class MCPFactoryCaptureTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.api = FakeProcessAPI()
        self.child = SimpleNamespace(pid=PID)
        self.calls = []

        async def original(*args, **kwargs):
            self.calls.append((args, kwargs))
            return self.child

        self.original = original
        self.stdio = SimpleNamespace(_create_platform_compatible_process=original)
        for target, attribute in ((ctypes, "WinDLL"), (subprocess, "Popen")):
            patcher = mock.patch.object(
                target, attribute, create=True,
                side_effect=AssertionError("tests must use fake process factory only"),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def retain(self, **kwargs):
        return custody.retain_mcp_stdio_process(self.stdio, api=self.api, **kwargs)

    async def test_actual_factory_object_is_captured_once_with_arguments_preserved(self):
        command = object()
        env = {"fixture": "not-a-real-environment"}
        async with self.retain(expected_executable=IMAGE,
                               expected_creation_filetime=CREATED) as captured:
            self.assertIsNone(captured.generation)
            self.assertIsNone(captured.creator_process)
            with self.assertRaises(custody.ProcessCustodyError):
                captured.require_generation()
            returned = await self.stdio._create_platform_compatible_process(command, env=env)
            self.assertIs(returned, self.child)
            self.assertIs(captured.creator_process, self.child)
            generation = captured.require_generation()
            self.assertIs(generation, captured.generation)
            self.assertIsNone(captured.capture_error)
            self.assertEqual(generation.identity("sdk_application")["pid"], self.child.pid)
            self.assertEqual(self.calls, [((command,), {"env": env})])
            self.assertEqual(self.api.count("open_process"), 1)
            self.assertEqual(self.api.count("close_handle"), 0)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)
        self.assertEqual(self.api.count("close_handle"), 1)

    async def test_second_factory_call_is_rejected_before_original_invocation(self):
        async with self.retain() as captured:
            await self.stdio._create_platform_compatible_process("fixture-sdk")
            first = captured.require_generation()
            with self.assertRaises(custody.ProcessCustodyError):
                await self.stdio._create_platform_compatible_process("duplicate-sdk")
            self.assertEqual(len(self.calls), 1)
            self.assertIs(captured.require_generation(), first)
            self.assertEqual(self.api.count("open_process"), 1)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)
        self.assertEqual(self.api.count("close_handle"), 1)

    async def test_no_child_raises_and_does_not_fabricate_generation(self):
        with self.assertRaises(custody.ProcessCustodyError):
            async with self.retain() as captured:
                self.assertIsNone(captured.generation)
                self.assertIsNone(captured.creator_process)
        self.assertIsNone(captured.generation)
        self.assertIsNone(captured.creator_process)
        self.assertEqual(self.api.count("open_process"), 0)
        self.assertEqual(self.api.count("close_handle"), 0)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)

    async def test_factory_exception_preserves_error_without_inventing_child(self):
        primary = OSError("fake process factory failed")

        async def failed(*args, **kwargs):
            raise primary

        self.stdio._create_platform_compatible_process = failed
        with self.assertRaises(OSError) as raised:
            async with self.retain() as captured:
                await self.stdio._create_platform_compatible_process("fixture-sdk")
        self.assertIs(raised.exception, primary)
        self.assertIsNone(captured.generation)
        self.assertIsNone(captured.creator_process)
        self.assertEqual(self.api.count("open_process"), 0)
        self.assertIs(self.stdio._create_platform_compatible_process, failed)

    async def test_image_mismatch_retains_real_child_for_owner_cleanup(self):
        with self.assertRaises(custody.ProcessCustodyError) as raised:
            async with self.retain(expected_executable=r"C:\wrong-sdk\python.exe") as captured:
                returned = await self.stdio._create_platform_compatible_process("fixture-sdk")
                self.assertIs(returned, self.child)
                self.assertIs(captured.creator_process, returned)
                self.assertIsNone(captured.generation)
                self.assertIsInstance(captured.capture_error, custody.ProcessCustodyError)
                captured.require_generation()
        self.assertIs(captured.creator_process, self.child)
        self.assertIsNone(captured.generation)
        self.assertIs(raised.exception.__cause__, captured.capture_error)
        with self.assertRaises(custody.ProcessCustodyError):
            captured.require_generation()
        self.assertEqual(self.api.count("close_handle"), 1)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)

    async def test_invalid_child_pid_never_opens_or_fabricates_identity(self):
        self.child = SimpleNamespace(pid=True)
        with self.assertRaises(custody.ProcessCustodyError) as raised:
            async with self.retain() as captured:
                returned = await self.stdio._create_platform_compatible_process("fixture-sdk")
                self.assertIs(returned, self.child)
                captured.require_generation()
        self.assertIs(captured.creator_process, self.child)
        self.assertIsNone(captured.generation)
        self.assertIsNotNone(captured.capture_error)
        self.assertIs(raised.exception.__cause__, captured.capture_error)
        self.assertEqual(self.api.count("open_process"), 0)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)

    async def test_malformed_expected_identity_refuses_before_creating_child(self):
        for kwargs in ({"expected_executable": "relative-python.exe"},
                       {"expected_creation_filetime": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(custody.ProcessCustodyError):
                async with self.retain(**kwargs):
                    await self.stdio._create_platform_compatible_process("fixture-sdk")
            self.assertIs(self.stdio._create_platform_compatible_process, self.original)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.api.count("open_process"), 0)

    async def test_body_exception_is_preserved_and_restores_factory_and_closes_once(self):
        primary = RuntimeError("fake SDK body failed")
        with self.assertRaises(RuntimeError) as raised:
            async with self.retain() as captured:
                await self.stdio._create_platform_compatible_process("fixture-sdk")
                raise primary
        self.assertIs(raised.exception, primary)
        self.assertIs(captured.creator_process, self.child)
        self.assertIsNotNone(captured.generation)
        captured.generation.close()
        self.assertEqual(self.api.count("close_handle"), 1)
        self.assertIs(self.stdio._create_platform_compatible_process, self.original)


if __name__ == "__main__":
    unittest.main()
