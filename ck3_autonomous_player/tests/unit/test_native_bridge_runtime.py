from __future__ import annotations

import os
import io
import hashlib
import inspect
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.errors import AgentError, UnsafeCleanupError  # noqa: E402
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
    _pinned_injector_creation_utc,
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


class _FakeInjector:
    def __init__(self, *, returncode: int = 0, stdout: bytes = b"PASS",
                 stderr: bytes = b"", timeout: bool = False,
                 reap_unproven: bool = False) -> None:
        self.pid = 517
        self._handle = 123
        self.returncode: int | None = None
        self.final_returncode = returncode
        self.output = (stdout, stderr)
        self.timeout = timeout
        self.reap_unproven = reap_unproven
        self.events: list[str] = []
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()

    def communicate(self, timeout: float) -> tuple[bytes, bytes]:
        self.events.append(f"communicate:{timeout}")
        if self.timeout and timeout == 30.0:
            raise subprocess.TimeoutExpired(["fake-injector"], timeout)
        if self.reap_unproven and timeout == 5:
            raise subprocess.TimeoutExpired(["fake-injector"], timeout)
        self.returncode = 1 if self.timeout else self.final_returncode
        return self.output

    def poll(self) -> int | None:
        return self.returncode

    def kill(self) -> None:
        self.events.append("kill")
        if not self.reap_unproven:
            self.returncode = 1


class NativeBridgeInjectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\test",
            dll_path=Path("C:/native/xar_ck3_bridge.dll"),
            injector_path=Path("C:/native/xar_ck3_bridge_injector.exe"),
        )

    def test_existing_injector_cli_receives_pid_and_dll(self) -> None:
        process = SimpleNamespace(pid=4123)
        child = _FakeInjector(stdout=b"PASS\r\n")
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", return_value=child
        ) as popen, mock.patch(
            "xar_autoplayer.runtime._pinned_injector_creation_utc",
            side_effect=lambda _child: child.events.append("identity") or
            "2026-09-30T00:00:00.000000+00:00",
        ):
            report = _inject_native_bridge(process, self.config)
        self.assertEqual(
            popen.call_args.args[0],
            [
                str(self.config.injector_path),
                "4123",
                str(self.config.dll_path),
            ],
        )
        self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(child.events, ["identity", "communicate:30.0"])
        self.assertEqual(report["pid"], 517)
        self.assertEqual(report["creation_utc"], "2026-09-30T00:00:00.000000+00:00")
        self.assertEqual(report["returncode"], 0)
        self.assertEqual(report["stdout_sha256"], hashlib.sha256(b"PASS\r\n").hexdigest().upper())
        self.assertEqual(report["stderr_sha256"], hashlib.sha256(b"").hexdigest().upper())
        self.assertEqual(report["complete_process_tree_proven"], False)
        self.assertTrue(report["injector_root_reaped"])
        self.assertEqual(report["role_query_authorized"], False)

    def test_injector_failure_reports_return_code_and_output(self) -> None:
        process = SimpleNamespace(pid=4123)
        child = _FakeInjector(returncode=3, stdout=b"partial output\n",
                              stderr=b"FAIL: InjectLibrary error=5\n")
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", return_value=child
        ), mock.patch(
            "xar_autoplayer.runtime._pinned_injector_creation_utc",
            return_value="2026-09-30T00:00:00.000000+00:00",
        ), self.assertRaisesRegex(
            NativeInjectorError, "rc=3.*InjectLibrary error=5"
        ) as failure:
            _inject_native_bridge(process, self.config)
        self.assertEqual(failure.exception.attestation["status"], "RED_RETURN_CODE")
        self.assertTrue(failure.exception.attestation["injector_root_reaped"])
        self.assertFalse(failure.exception.attestation["complete_process_tree_proven"])

    def test_injection_completes_before_primary_thread_resume(self) -> None:
        calls: list[str] = []
        process = SimpleNamespace(resume=lambda: calls.append("resume"))
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge",
            side_effect=lambda *_args: calls.append("inject"),
        ):
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(calls, ["inject", "resume"])

    def test_launch_still_assigns_suspended_ck3_to_job_before_injection(self) -> None:
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

    def test_root_exit_cannot_clear_marker_without_injector_tree_proof(self) -> None:
        process = SimpleNamespace(injector_attestation={
            "injector_root_reaped": True,
            "complete_process_tree_proven": False,
        })
        with self.assertRaisesRegex(UnsafeCleanupError, "process tree cleanup is unproven"):
            _require_injector_cleanup_before_marker_clear(process)
        process.injector_attestation = None
        _require_injector_cleanup_before_marker_clear(process)
        process.injector_attestation = {"injector_root_reaped": True,
                                        "complete_process_tree_proven": True}
        _require_injector_cleanup_before_marker_clear(process)
        process.injector_attestation = "invalid"
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_disabled_launch_resumes_without_invoking_injector(self) -> None:
        process = mock.Mock()
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge"
        ) as inject:
            _resume_with_native_bridge(process, None)
        inject.assert_not_called()
        process.resume.assert_called_once_with()

    def test_injector_timeout_is_a_launch_error(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        child = _FakeInjector(timeout=True, stdout=b"partial")
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", return_value=child,
        ), mock.patch(
            "xar_autoplayer.runtime._pinned_injector_creation_utc",
            return_value="2026-09-30T00:00:00.000000+00:00",
        ), self.assertRaisesRegex(NativeInjectorError, "could not complete") as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(child.events, ["communicate:30.0", "kill", "communicate:5"])
        self.assertEqual(child.returncode, 1)
        self.assertTrue(failure.exception.attestation["injector_root_reaped"])
        self.assertEqual(failure.exception.attestation["stdout_sha256"],
                         hashlib.sha256(b"partial").hexdigest().upper())
        process.resume.assert_not_called()

    def test_timeout_without_reap_keeps_cleanup_unproven(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        child = _FakeInjector(timeout=True, reap_unproven=True)
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", return_value=child,
        ), mock.patch(
            "xar_autoplayer.runtime._pinned_injector_creation_utc",
            return_value="2026-09-30T00:00:00.000000+00:00",
        ), self.assertRaises(NativeInjectorError) as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertFalse(failure.exception.attestation["injector_root_reaped"])
        self.assertFalse(process.injector_attestation["injector_root_reaped"])
        self.assertIsNone(failure.exception.attestation["stdout_sha256"])
        self.assertIsNone(failure.exception.attestation["stderr_sha256"])
        with self.assertRaisesRegex(UnsafeCleanupError, "unsafe marker retained"):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()

    def test_real_dummy_timeout_reaps_exact_child_before_resume(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows pinned process handle required")
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        real_popen = subprocess.Popen
        spawned: list[subprocess.Popen[bytes]] = []

        def spawn_dummy(_command: list[str], **kwargs: object) -> subprocess.Popen[bytes]:
            child = real_popen(
                [sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
            spawned.append(child)
            return child

        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", side_effect=spawn_dummy,
        ), mock.patch(
            "xar_autoplayer.runtime.NATIVE_BRIDGE_INJECT_TIMEOUT_SECONDS", 0.02,
        ), self.assertRaises(NativeInjectorError) as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(len(spawned), 1)
        self.assertIsNotNone(spawned[0].poll())
        self.assertTrue(failure.exception.attestation["injector_root_reaped"])
        self.assertFalse(failure.exception.attestation["complete_process_tree_proven"])
        self.assertEqual(failure.exception.attestation["pid"], spawned[0].pid)
        process.resume.assert_not_called()

    def test_exited_dummy_injector_with_live_descendant_retains_marker(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows process descendant fixture required")
        import win32api
        import win32con
        import win32event
        import win32process

        process = SimpleNamespace(pid=4123)
        real_popen = subprocess.Popen
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "descendant.pid"
            parent_code = (
                "import pathlib, subprocess, sys; "
                "child=subprocess.Popen([sys.executable, '-c', "
                "'import time; time.sleep(60)'], stdout=subprocess.DEVNULL, "
                "stderr=subprocess.DEVNULL); "
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid))"
            )

            def spawn_parent(_command: list[str], **kwargs: object) -> subprocess.Popen[bytes]:
                return real_popen([sys.executable, "-c", parent_code, str(pid_file)],
                                  **kwargs)

            with mock.patch("xar_autoplayer.runtime.subprocess.Popen",
                            side_effect=spawn_parent):
                report = _inject_native_bridge(process, self.config)
            self.assertTrue(report["injector_root_reaped"])
            self.assertFalse(report["complete_process_tree_proven"])
            descendant_pid = int(pid_file.read_text(encoding="utf-8"))
            rights = (win32con.PROCESS_QUERY_INFORMATION
                      | win32con.PROCESS_TERMINATE | win32con.SYNCHRONIZE)
            handle = win32api.OpenProcess(rights, False, descendant_pid)
            try:
                self.assertEqual(win32process.GetExitCodeProcess(handle),
                                 win32con.STILL_ACTIVE)
                with self.assertRaisesRegex(UnsafeCleanupError, "unsafe marker retained"):
                    _require_injector_cleanup_before_marker_clear(process)
            finally:
                if win32process.GetExitCodeProcess(handle) == win32con.STILL_ACTIVE:
                    win32api.TerminateProcess(handle, 1)
                self.assertEqual(win32event.WaitForSingleObject(handle, 5000),
                                 win32event.WAIT_OBJECT_0)
                win32api.CloseHandle(handle)

    def test_pinned_handle_creation_survives_fast_exit_and_pid_reuse(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows pinned process handle required")
        with subprocess.Popen([sys.executable, "-c", "pass"],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as child:
            child.communicate(timeout=5)
            created = _pinned_injector_creation_utc(child)
        self.assertIn("+00:00", created)
        reused_pid = SimpleNamespace(pid=child.pid, _handle=123)
        old_time = datetime(2026, 9, 29, tzinfo=timezone.utc)
        with mock.patch("win32process.GetProcessTimes",
                        return_value={"CreationTime": old_time}) as pinned, mock.patch(
            "xar_autoplayer.runtime._process_identity",
            side_effect=AssertionError("PID lookup can observe a reused process"),
        ) as lookup:
            self.assertEqual(_pinned_injector_creation_utc(reused_pid),
                             "2026-09-29T00:00:00.000000+00:00")
        pinned.assert_called_once_with(123)
        lookup.assert_not_called()

    def test_missing_pinned_handle_refuses_before_resume(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        child = _FakeInjector()
        child._handle = None
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.Popen", return_value=child,
        ), self.assertRaises(NativeInjectorError) as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(failure.exception.attestation["status"], "RED_IDENTITY")
        self.assertTrue(failure.exception.attestation["injector_root_reaped"])
        process.resume.assert_not_called()

    def test_popen_constructor_error_keeps_marker_without_child_proof(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        with mock.patch("xar_autoplayer.runtime.subprocess.Popen",
                        side_effect=OSError("dummy constructor error")), self.assertRaises(
            NativeInjectorError
        ) as failure:
            _resume_with_native_bridge(process, self.config)
        self.assertEqual(failure.exception.attestation["status"],
                         "RED_SPAWN_UNPROVEN")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)
        process.resume.assert_not_called()


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
