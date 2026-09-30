from __future__ import annotations

import os
import hashlib
import inspect
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.errors import AgentError, UnsafeCleanupError  # noqa: E402
from xar_autoplayer.windows_injector_job import (  # noqa: E402
    ContainedInjectorResult,
    MAX_INJECTOR_OUTPUT_BYTES,
    run_contained_injector_command,
)
from xar_autoplayer.runtime import (  # noqa: E402
    DEFAULT_NATIVE_BRIDGE_PIPE,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    NativeBridgeLaunchConfig,
    NativeInjectorError,
    _ck3_launch_command,
    _create_suspended_process,
    _inject_native_bridge,
    _native_bridge_child_environment,
    _require_injector_cleanup_before_marker_clear,
    _resume_with_native_bridge,
    launch,
    stop_tracked,
    configure_native_bridge_launch_environment,
    native_bridge_launch_config_from_environment,
)


class NativeBridgeLaunchConfigurationTests(unittest.TestCase):
    def test_disabled_mode_ignores_unusable_native_paths(self) -> None:
        config = native_bridge_launch_config_from_environment(
            {
                NATIVE_BRIDGE_MODE_ENV: NATIVE_BRIDGE_DISABLED,
                NATIVE_BRIDGE_DLL_ENV: "missing.dll",
                NATIVE_BRIDGE_INJECTOR_ENV: "missing.exe",
            }
        )
        self.assertIsNone(config)

    def test_pure_and_fallback_modes_remain_distinct(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-native-launch-") as temporary:
            root = Path(temporary)
            dll = root / "xar_ck3_bridge.dll"
            injector = root / "xar_ck3_bridge_injector.exe"
            dll.touch()
            injector.touch()
            pure = native_bridge_launch_config_from_environment(
                {
                    NATIVE_BRIDGE_MODE_ENV: "native-headless",
                    NATIVE_BRIDGE_DLL_ENV: str(dll),
                    NATIVE_BRIDGE_INJECTOR_ENV: str(injector),
                }
            )
            fallback = native_bridge_launch_config_from_environment(
                {
                    NATIVE_BRIDGE_MODE_ENV: "hybrid-fallback",
                    NATIVE_BRIDGE_PIPE_ENV: r"\\.\pipe\fallback-test",
                    NATIVE_BRIDGE_DLL_ENV: str(dll),
                    NATIVE_BRIDGE_INJECTOR_ENV: str(injector),
                }
            )
        self.assertEqual(pure.mode, "native-headless")
        self.assertEqual(pure.pipe_name, DEFAULT_NATIVE_BRIDGE_PIPE)
        self.assertEqual(fallback.mode, "hybrid-fallback")
        self.assertEqual(fallback.pipe_name, r"\\.\pipe\fallback-test")

    def test_enabled_mode_requires_both_binaries(self) -> None:
        with self.assertRaisesRegex(AgentError, "XAR_CK3_BRIDGE_DLL"):
            native_bridge_launch_config_from_environment(
                {NATIVE_BRIDGE_MODE_ENV: "native-headless"}
            )

    def test_cli_environment_configuration_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-native-cli-") as temporary:
            root = Path(temporary)
            dll = root / "bridge.dll"
            injector = root / "injector.exe"
            dll.touch()
            injector.touch()
            environment = {"UNCHANGED": "yes"}
            config = configure_native_bridge_launch_environment(
                "hybrid-fallback",
                pipe_name=r"\\.\pipe\configured",
                dll_path=dll,
                injector_path=injector,
                environment=environment,
            )
        self.assertEqual(config.mode, "hybrid-fallback")
        self.assertEqual(environment["UNCHANGED"], "yes")
        self.assertEqual(environment[NATIVE_BRIDGE_MODE_ENV], "hybrid-fallback")
        self.assertEqual(
            environment[NATIVE_BRIDGE_PIPE_ENV], r"\\.\pipe\configured"
        )

    def test_child_environment_contains_pipe_and_mode(self) -> None:
        config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\headless-test",
            dll_path=Path("bridge.dll"),
            injector_path=Path("injector.exe"),
        )
        environment = _native_bridge_child_environment(
            config,
            {
                "Path": "C:/Windows",
                "xar_ck3_bridge_pipe": "stale",
                "XAR_CK3_BRIDGE_MODE": "hybrid-fallback",
            },
        )
        self.assertEqual(environment["Path"], "C:/Windows")
        self.assertNotIn("xar_ck3_bridge_pipe", environment)
        self.assertEqual(environment[NATIVE_BRIDGE_PIPE_ENV], config.pipe_name)
        self.assertEqual(environment[NATIVE_BRIDGE_MODE_ENV], config.mode)

    def test_parser_exposes_disabled_pure_and_fallback_modes(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                cli.parser().parse_args(["doctor"]).bridge_mode, "disabled"
            )
            self.assertEqual(
                cli.parser()
                .parse_args(["--bridge-mode", "native-headless", "doctor"])
                .bridge_mode,
                "native-headless",
            )
            self.assertEqual(
                cli.parser()
                .parse_args(["--bridge-mode", "hybrid-fallback", "doctor"])
                .bridge_mode,
                "hybrid-fallback",
            )


class NativeBridgeInjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        digest = mock.patch("xar_autoplayer.runtime.sha256_file",
                            return_value="a" * 64)
        digest.start()
        self.addCleanup(digest.stop)
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\test",
            dll_path=Path("C:/native/xar_ck3_bridge.dll"),
            injector_path=Path("C:/native/xar_ck3_bridge_injector.exe"),
        )

    @staticmethod
    def outcome(command: list[str], *, returncode: int = 0,
                stdout: bytes = b"PASS\r\n", stderr: bytes = b"",
                tree: bool = True, status: str = "EXIT",
                error: str | None = None) -> ContainedInjectorResult:
        return ContainedInjectorResult({
            "schema": "xar.ck3.contained-injector-job.v1",
            "status": status, "argv": command, "pid": 517,
            "creation_utc": "2026-09-30T00:00:00.000000+00:00",
            "pinned_executable": command[0],
            "executable_sha256": "A" * 64,
            "job_limit_flags": 0x2008,
            "pre_resume_job_pids": [517],
            "resume_previous_count": 1,
            "returncode": returncode,
            "stdout_sha256": hashlib.sha256(stdout).hexdigest().upper(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest().upper(),
            "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
            "stdout_complete": True, "stderr_complete": True,
            "injector_root_reaped": True,
            "complete_process_tree_proven": tree,
            "job_active_final": 0 if tree else None,
            "job_pids_final": [] if tree else None,
        }, stdout, stderr, error)

    def test_existing_injector_cli_receives_pid_and_dll(self) -> None:
        process = SimpleNamespace(pid=4123)
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        with mock.patch(
            "xar_autoplayer.runtime.run_contained_injector_command",
            return_value=self.outcome(command),
        ) as run:
            report = _inject_native_bridge(process, self.config)
        run.assert_called_once_with(command, timeout_seconds=30.0)
        self.assertEqual(report["status"], "INJECTOR_EXIT_ZERO_TREE_PROVEN")
        self.assertEqual(report["schema"], "xar.ck3.native-injector-attempt.v1")
        self.assertEqual(report["contained_job_report"]["schema"],
                         "xar.ck3.contained-injector-job.v1")
        self.assertEqual(report["contained_job_report"]["status"], "EXIT")
        self.assertEqual(report["pid"], 517)
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["stdout_sha256"],
                         hashlib.sha256(b"PASS\r\n").hexdigest().upper())
        self.assertTrue(report["complete_process_tree_proven"])
        self.assertFalse(report["role_query_authorized"])

    def test_nonzero_return_preserves_diagnostic_and_refuses_resume(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command, returncode=3, stdout=b"partial output\n",
                              stderr=b"FAIL: InjectLibrary error=5\n")
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaisesRegex(
            NativeInjectorError, "rc=3.*InjectLibrary error=5"
        ) as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(failure.exception.attestation["status"], "RED_RETURN_CODE")
        self.assertTrue(failure.exception.attestation["complete_process_tree_proven"])
        process.resume.assert_not_called()

    def test_timeout_and_unproven_job_refuse_resume_and_marker_clear(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command, status="RED_TIMEOUT", tree=False,
                              error="timeout after 30 seconds")
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaisesRegex(
            NativeInjectorError, "timeout after 30 seconds"
        ):
            _resume_with_native_bridge(process, self.config)
        self.assertFalse(process.injector_attestation["complete_process_tree_proven"])
        self.assertEqual(process.injector_attestation["schema"],
                         "xar.ck3.native-injector-attempt.v1")
        self.assertEqual(process.injector_attestation["contained_job_report"]["status"],
                         "RED_TIMEOUT")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_helper_exception_keeps_marker_and_never_resumes(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        side_effect=OSError("dummy API failure")), self.assertRaises(
            NativeInjectorError
        ):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(process.injector_attestation["status"], "RED_JOB_CALL")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_exit_without_tree_proof_never_resumes(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=self.outcome(command, tree=False)), self.assertRaises(
            NativeInjectorError
        ):
            _resume_with_native_bridge(process, self.config)
        process.resume.assert_not_called()

    def test_malformed_job_report_keeps_marker_and_never_resumes(self) -> None:
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        invalid_fields = {
            "schema": None,
            "argv": None,
            "pid": True,
            "creation_utc": None,
            "pinned_executable": "C:/native/other.exe",
            "executable_sha256": "not-a-sha",
            "job_limit_flags": False,
            "pre_resume_job_pids": [],
            "resume_previous_count": False,
            "returncode": False,
            "job_active_final": False,
            "job_pids_final": None,
            "stdout_sha256": "0" * 64,
            "stdout_bytes": True,
            "stdout_complete": None,
        }
        for field, invalid in invalid_fields.items():
            with self.subTest(field=field):
                process = SimpleNamespace(pid=4123, resume=mock.Mock())
                result = self.outcome(command)
                result.report[field] = invalid
                with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                                return_value=result), self.assertRaises(NativeInjectorError):
                    _resume_with_native_bridge(process, self.config)
                self.assertEqual(process.injector_attestation["status"],
                                 "RED_JOB_REPORT_MISMATCH")
                self.assertFalse(process.injector_attestation[
                    "complete_process_tree_proven"])
                with self.assertRaises(UnsafeCleanupError):
                    _require_injector_cleanup_before_marker_clear(process)
                process.resume.assert_not_called()

    def test_injector_executable_byte_drift_keeps_marker(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=self.outcome(command)), mock.patch(
            "xar_autoplayer.runtime.sha256_file", return_value="b" * 64
        ), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(process.injector_attestation["status"],
                         "RED_JOB_REPORT_MISMATCH")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_slow_outer_executable_rehash_cannot_resume_ck3(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]

        def slow_hash(_path: Path) -> str:
            time.sleep(1.1)
            return "a" * 64

        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=self.outcome(command)), mock.patch(
            "xar_autoplayer.runtime.sha256_file", side_effect=slow_hash
        ), mock.patch("xar_autoplayer.runtime.NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS",
                      1.0), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(process.injector_attestation["status"], "RED_TIMEOUT")
        self.assertEqual(process.injector_attestation["deadline_phase"],
                         "post-helper executable/report validation")
        self.assertFalse(process.injector_attestation[
            "complete_process_tree_proven"])
        self.assertEqual(process.injector_attestation["contained_job_report"]["status"],
                         "EXIT")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_outer_hash_exception_keeps_marker(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=self.outcome(command)), mock.patch(
            "xar_autoplayer.runtime.sha256_file",
            side_effect=RuntimeError("dummy hash read failed")
        ), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(process.injector_attestation["status"],
                         "RED_JOB_REPORT_VALIDATION")
        self.assertFalse(process.injector_attestation[
            "complete_process_tree_proven"])
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_pre_ck3_resume_budget_is_separate_last_gate(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        valid = {
            "schema": "xar.ck3.native-injector-attempt.v1",
            "status": "INJECTOR_EXIT_ZERO_TREE_PROVEN",
            "injector_root_reaped": True,
            "complete_process_tree_proven": True,
        }

        def slow_inject(_process: object, _config: object) -> dict[str, object]:
            time.sleep(1.1)
            return dict(valid)

        with mock.patch("xar_autoplayer.runtime._inject_native_bridge",
                        side_effect=slow_inject), mock.patch(
            "xar_autoplayer.runtime.NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS", 1.0
        ), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(process.injector_attestation["status"], "RED_TIMEOUT")
        self.assertEqual(process.injector_attestation["deadline_phase"],
                         "pre-CK3-resume")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_slow_ck3_resume_retracts_success_and_keeps_marker(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock(
            side_effect=lambda: time.sleep(1.1)))
        valid = {
            "schema": "xar.ck3.native-injector-attempt.v1",
            "status": "INJECTOR_EXIT_ZERO_TREE_PROVEN",
            "injector_root_reaped": True,
            "complete_process_tree_proven": True,
        }
        with mock.patch("xar_autoplayer.runtime._inject_native_bridge",
                        return_value=dict(valid)), mock.patch(
            "xar_autoplayer.runtime.NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS", 1.0
        ), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config)
        process.resume.assert_called_once_with()
        self.assertEqual(process.injector_attestation["status"], "RED_TIMEOUT")
        self.assertEqual(process.injector_attestation["deadline_phase"],
                         "post-CK3-resume")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_injection_completes_before_primary_thread_resume(self) -> None:
        calls: list[str] = []
        process = SimpleNamespace(resume=lambda: calls.append("resume"))
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge",
            side_effect=lambda *_args: calls.append("inject"),
        ):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(calls, ["inject", "resume"])

    def test_launch_and_marker_clear_order_remains_guarded(self) -> None:
        source = inspect.getsource(launch)
        self.assertLess(source.index("process = _create_suspended_process("),
                        source.index("_assign_process_to_job(job_handle, process)"))
        self.assertLess(source.index("_assign_process_to_job(job_handle, process)"),
                        source.index("_resume_with_native_bridge(process, native_bridge)"))
        self.assertLess(source.index("_require_injector_cleanup_before_marker_clear(process)"),
                        source.rindex("unsafe_marker.unlink(missing_ok=True)"))
        stop_source = inspect.getsource(stop_tracked)
        self.assertLess(stop_source.index("_require_injector_cleanup_before_marker_clear(handle.process)"),
                        stop_source.index("handle.unsafe_marker.unlink(missing_ok=True)"))

    def test_root_exit_alone_cannot_clear_marker(self) -> None:
        process = SimpleNamespace(injector_attestation={
            "injector_root_reaped": True,
            "complete_process_tree_proven": False,
        })
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.injector_attestation["complete_process_tree_proven"] = True
        _require_injector_cleanup_before_marker_clear(process)

    def test_disabled_launch_resumes_without_invoking_injector(self) -> None:
        process = mock.Mock()
        with mock.patch("xar_autoplayer.runtime._inject_native_bridge") as inject:
            _resume_with_native_bridge(process, None)
        inject.assert_not_called()
        process.resume.assert_called_once_with()


class WindowsInjectorJobTests(unittest.TestCase):
    def setUp(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows Job containment required")
        self.python = str(Path(sys._base_executable).resolve())

    def test_exact_output_identity_and_empty_job(self) -> None:
        command = [self.python, "-c",
                   "import sys;sys.stdout.buffer.write(b'OUT\\r\\n');"
                   "sys.stderr.buffer.write(b'ERR\\n')"]
        result = run_contained_injector_command(command, timeout_seconds=5)
        self.assertIsNone(result.error)
        self.assertEqual(result.stdout, b"OUT\r\n")
        self.assertEqual(result.stderr, b"ERR\n")
        self.assertEqual(result.report["status"], "EXIT")
        self.assertEqual(result.report["returncode"], 0)
        self.assertTrue(result.report["injector_root_reaped"])
        self.assertTrue(result.report["complete_process_tree_proven"])
        self.assertEqual(result.report["pre_resume_job_pids"], [result.report["pid"]])
        self.assertEqual(result.report["job_active_final"], 0)
        self.assertEqual(result.report["job_pids_final"], [])
        self.assertEqual(result.report["resume_previous_count"], 1)
        self.assertTrue(os.path.samefile(result.report["pinned_executable"], self.python))
        self.assertEqual(result.report["stdout_sha256"],
                         hashlib.sha256(b"OUT\r\n").hexdigest().upper())

    def test_timeout_terminates_job_and_refuses_tree_proof(self) -> None:
        result = run_contained_injector_command(
            [self.python, "-c", "import time;time.sleep(30)"],
            timeout_seconds=2.0)
        self.assertEqual(result.report["status"], "RED_TIMEOUT")
        self.assertTrue(result.report["injector_root_reaped"])
        self.assertFalse(result.report["complete_process_tree_proven"])
        self.assertEqual(result.report["job_active_final"], 0)
        self.assertEqual(result.report["job_pids_final"], [])

    def test_large_two_pipe_output_is_bounded_and_complete(self) -> None:
        payload = 1024 * 1024
        result = run_contained_injector_command(
            [self.python, "-c", "import sys;"
             "sys.stdout.buffer.write(b'A'*1048576);"
             "sys.stderr.buffer.write(b'B'*1048576)"],
            timeout_seconds=5)
        self.assertIsNone(result.error)
        self.assertEqual(result.stdout, b"A" * payload)
        self.assertEqual(result.stderr, b"B" * payload)
        self.assertTrue(result.report["complete_process_tree_proven"])
        self.assertEqual(result.report["job_pids_final"], [])

    def test_slow_postproof_job_close_retracts_green(self) -> None:
        import win32api

        original = win32api.CloseHandle

        def slow_close(handle: object) -> None:
            time.sleep(1.2)
            original(handle)

        with mock.patch("win32api.CloseHandle", side_effect=slow_close):
            result = run_contained_injector_command(
                [self.python, "-c", "print('OK')"], timeout_seconds=1.0)
        self.assertEqual(result.report["status"], "RED_TIMEOUT")
        self.assertEqual(result.report["deadline_phase"], "post-Job cleanup")
        self.assertFalse(result.report["complete_process_tree_proven"])
        self.assertEqual(result.report["job_active_final"], 0)
        self.assertEqual(result.report["job_pids_final"], [])
        self.assertIsNotNone(result.error)

    def test_output_limit_terminates_job_and_refuses_tree_proof(self) -> None:
        result = run_contained_injector_command(
            [self.python, "-c", "import sys;sys.stdout.buffer.write(b'X'*1048576)"],
            timeout_seconds=5, output_limit_bytes=1024)
        self.assertEqual(result.report["status"], "RED_OUTPUT_OR_IO")
        self.assertFalse(result.report["complete_process_tree_proven"])
        self.assertTrue(result.report["stdout_overflow"])
        self.assertIsNone(result.stdout)
        self.assertEqual(result.report["job_active_final"], 0)

    def test_job_rejects_child_and_breakaway_before_root_exit(self) -> None:
        for flags in (0, 0x01000000):
            with self.subTest(flags=flags):
                code = (
                    "import subprocess,sys\n"
                    "try:\n"
                    f" subprocess.Popen([sys.executable,'-c','import time;time.sleep(2)'],"
                    f"stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
                    f"stderr=subprocess.DEVNULL,creationflags={flags})\n"
                    "except OSError:\n print('REJECTED',flush=True)\n"
                    "else:\n print('CREATED',flush=True)\n"
                )
                result = run_contained_injector_command(
                    [self.python, "-c", code], timeout_seconds=5)
                self.assertEqual(result.stdout.strip(), b"REJECTED")
                self.assertTrue(result.report["complete_process_tree_proven"])
                self.assertEqual(result.report["job_active_final"], 0)

    def test_job_assignment_error_never_resumes_root(self) -> None:
        with mock.patch("win32job.AssignProcessToJobObject",
                        side_effect=OSError("dummy assignment error")):
            result = run_contained_injector_command(
                [self.python, "-c", "print('should never run')"],
                timeout_seconds=5)
        self.assertEqual(result.report["status"], "RED_INTERNAL")
        self.assertIsNone(result.report["resume_previous_count"])
        self.assertFalse(result.report["complete_process_tree_proven"])
        self.assertTrue(result.report["injector_root_reaped"])

    def test_pre_resume_identity_and_assignment_time_count_toward_budget(self) -> None:
        import win32job
        import win32process

        for module, name in ((win32process, "GetProcessTimes"),
                             (win32job, "AssignProcessToJobObject")):
            with self.subTest(stage=name):
                original = getattr(module, name)
                calls = 0

                def delayed(*args: object) -> object:
                    nonlocal calls
                    calls += 1
                    time.sleep(1.1)
                    return original(*args)

                with mock.patch.object(module, name, side_effect=delayed):
                    result = run_contained_injector_command(
                        [self.python, "-c", "print('must not run')"],
                        timeout_seconds=1.0)
                self.assertEqual(calls, 1)
                self.assertEqual(result.report["status"], "RED_TIMEOUT")
                self.assertFalse(result.report["complete_process_tree_proven"])
                self.assertIsNone(result.report["resume_previous_count"])
                self.assertTrue(result.report["injector_root_reaped"])

    def test_expired_pipe_setup_cannot_call_createprocess(self) -> None:
        from xar_autoplayer import windows_injector_job

        original = windows_injector_job._inheritable_copy
        copies = 0

        def delayed_copy(handle: int) -> int:
            nonlocal copies
            copies += 1
            if copies == 1:
                time.sleep(1.1)
            return original(handle)

        with mock.patch.object(windows_injector_job, "_inheritable_copy",
                               side_effect=delayed_copy), mock.patch(
            "_winapi.CreateProcess", side_effect=AssertionError("must not spawn")
        ) as create:
            result = run_contained_injector_command(
                [self.python, "-c", "print('must not run')"],
                timeout_seconds=1.0)
        self.assertGreaterEqual(copies, 1)
        create.assert_not_called()
        self.assertEqual(result.report["status"], "RED_TIMEOUT")
        self.assertFalse(result.report["complete_process_tree_proven"])

    def test_wrong_pinned_executable_never_resumes_root(self) -> None:
        with mock.patch("win32process.GetModuleFileNameEx",
                        return_value=str(Path(self.python).parent / "other.exe")):
            result = run_contained_injector_command(
                [self.python, "-c", "print('should never run')"],
                timeout_seconds=5)
        self.assertEqual(result.report["status"], "RED_INTERNAL")
        self.assertIsNone(result.report["resume_previous_count"])
        self.assertFalse(result.report["complete_process_tree_proven"])

    def test_missing_pinned_creation_never_resumes_root(self) -> None:
        with mock.patch("win32process.GetProcessTimes", return_value={}):
            result = run_contained_injector_command(
                [self.python, "-c", "print('should never run')"],
                timeout_seconds=5)
        self.assertEqual(result.report["status"], "RED_INTERNAL")
        self.assertIsNone(result.report["resume_previous_count"])
        self.assertFalse(result.report["complete_process_tree_proven"])

    def test_unexpected_resume_count_fails_closed(self) -> None:
        with mock.patch("win32process.ResumeThread", return_value=0):
            result = run_contained_injector_command(
                [self.python, "-c", "print('should never run')"],
                timeout_seconds=5)
        self.assertEqual(result.report["status"], "RED_INTERNAL")
        self.assertEqual(result.report["resume_previous_count"], 0)
        self.assertFalse(result.report["complete_process_tree_proven"])

    def test_final_job_query_failure_never_proves_tree(self) -> None:
        import win32job

        original = win32job.QueryInformationJobObject
        pid_queries = 0

        def fail_final_pid_list(job: object, info_class: int) -> object:
            nonlocal pid_queries
            if info_class == win32job.JobObjectBasicProcessIdList:
                pid_queries += 1
                if pid_queries == 4:
                    raise OSError("dummy final Job PID query failure")
            return original(job, info_class)

        with mock.patch("win32job.QueryInformationJobObject",
                        side_effect=fail_final_pid_list):
            result = run_contained_injector_command(
                [self.python, "-c", "print('done')"], timeout_seconds=5)
        self.assertEqual(pid_queries, 4)
        self.assertEqual(result.report["status"], "RED_INTERNAL")
        self.assertTrue(result.report["injector_root_reaped"])
        self.assertFalse(result.report["complete_process_tree_proven"])

    def test_relative_or_missing_executable_fails_closed(self) -> None:
        for executable in ("python.exe", "D:/missing-r0368-injector.exe"):
            with self.subTest(executable=executable):
                result = run_contained_injector_command(
                    [executable], timeout_seconds=5)
                self.assertEqual(result.report["status"], "RED_INTERNAL")
                self.assertIsNone(result.report["pid"])
                self.assertFalse(result.report["complete_process_tree_proven"])

    def test_unbounded_or_invalid_budgets_cannot_spawn(self) -> None:
        for seconds, limit in ((float("inf"), 1024), (float("nan"), 1024),
                               (5, MAX_INJECTOR_OUTPUT_BYTES + 1)):
            with self.subTest(seconds=seconds, limit=limit), mock.patch(
                "_winapi.CreateProcess", side_effect=AssertionError("must not spawn")
            ):
                result = run_contained_injector_command(
                    [self.python, "-c", "print('not run')"],
                    timeout_seconds=seconds, output_limit_bytes=limit)
                self.assertEqual(result.report["status"], "RED_INVALID_INPUT_OR_PLATFORM")
                self.assertFalse(result.report["complete_process_tree_proven"])

class NativeBridgeCreateProcessTests(unittest.TestCase):
    def test_native_last_save_launch_uses_jomini_boot_argument(self) -> None:
        spec = SimpleNamespace(
            game_exe=Path("C:/game/ck3.exe"),
            profile_dir=Path("C:/profile"),
        )

        command = _ck3_launch_command(spec, continue_last_save=True)

        self.assertEqual(
            command,
            [
                "C:\\game\\ck3.exe",
                "-gdpr-compliant",
                "-userdir=C:\\profile",
                "-continuelastsave",
            ],
        )

    def test_native_exact_save_launch_uses_jomini_loadsave_argument(self) -> None:
        spec = SimpleNamespace(
            game_exe=Path("C:/game/ck3.exe"),
            profile_dir=Path("C:/profile"),
        )

        command = _ck3_launch_command(spec, load_save_name="xar_checkpoint")

        self.assertEqual(
            command,
            [
                "C:\\game\\ck3.exe",
                "-gdpr-compliant",
                "-userdir=C:\\profile",
                "-loadsave=xar_checkpoint",
            ],
        )

    def test_native_exact_save_rejects_conflicts_and_paths(self) -> None:
        spec = SimpleNamespace(
            game_exe=Path("C:/game/ck3.exe"),
            profile_dir=Path("C:/profile"),
        )

        with self.assertRaisesRegex(AgentError, "cannot combine"):
            _ck3_launch_command(
                spec,
                continue_last_save=True,
                load_save_name="xar_checkpoint",
            )
        with self.assertRaisesRegex(AgentError, "without a path"):
            _ck3_launch_command(spec, load_save_name="save games/other")
        with self.assertRaisesRegex(AgentError, "without a path"):
            _ck3_launch_command(spec, load_save_name="xar_checkpoint.ck3")

    def test_default_launch_keeps_null_environment_and_original_flags(self) -> None:
        create = mock.Mock(return_value=(object(), object(), 81, 91))
        win32process = SimpleNamespace(
            STARTUPINFO=mock.Mock(return_value=object()),
            CREATE_SUSPENDED=0x00000004,
            CREATE_UNICODE_ENVIRONMENT=0x00000400,
            CreateProcess=create,
        )
        with mock.patch.dict(sys.modules, {"win32process": win32process}):
            _create_suspended_process(["C:/game/ck3.exe"], Path("C:/game"))
        call = create.call_args.args
        self.assertEqual(call[5], win32process.CREATE_SUSPENDED)
        self.assertIsNone(call[6])

    def test_enabled_launch_passes_unicode_pipe_environment(self) -> None:
        environment = {
            "Path": "C:/Windows",
            NATIVE_BRIDGE_PIPE_ENV: r"\\.\pipe\runtime-test",
        }
        create = mock.Mock(return_value=(object(), object(), 82, 92))
        win32process = SimpleNamespace(
            STARTUPINFO=mock.Mock(return_value=object()),
            CREATE_SUSPENDED=0x00000004,
            CREATE_UNICODE_ENVIRONMENT=0x00000400,
            CreateProcess=create,
        )
        with mock.patch.dict(sys.modules, {"win32process": win32process}):
            _create_suspended_process(
                ["C:/game/ck3.exe"], Path("C:/game"), environment
            )
        call = create.call_args.args
        self.assertTrue(call[5] & win32process.CREATE_SUSPENDED)
        self.assertTrue(call[5] & win32process.CREATE_UNICODE_ENVIRONMENT)
        self.assertEqual(call[6], environment)


if __name__ == "__main__":
    unittest.main()
