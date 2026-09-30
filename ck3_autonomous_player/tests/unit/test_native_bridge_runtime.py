from __future__ import annotations

import os
import hashlib
import json
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
from xar_autoplayer.windows_injector_job import ContainedInjectorResult  # noqa: E402
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
        temporary = tempfile.TemporaryDirectory(prefix="injector-evidence-test-")
        self.addCleanup(temporary.cleanup)
        self.evidence_dir = Path(temporary.name) / "attempt"
        digest = mock.patch("xar_autoplayer.runtime.sha256_file", return_value="a" * 64)
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
            "pinned_executable": command[0], "executable_sha256": "A" * 64,
            "job_limit_flags": 0x2008, "pre_resume_job_pids": [517],
            "resume_previous_count": 1, "returncode": returncode,
            "stdout_sha256": hashlib.sha256(stdout).hexdigest().upper(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest().upper(),
            "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
            "stdout_complete": True, "stderr_complete": True,
            "stdout_overflow": False, "stderr_overflow": False,
            "stdout_reader_error": None, "stderr_reader_error": None,
            "output_limit_bytes": 8 * 1024 * 1024,
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
            attestation = _inject_native_bridge(process, self.config, self.evidence_dir)
        run.assert_called_once_with(command, timeout_seconds=30.0)
        self.assertEqual(attestation["status"], "INJECTOR_EXIT_ZERO_TREE_PROVEN")
        self.assertTrue(attestation["complete_process_tree_proven"])
        self.assertEqual((self.evidence_dir / "stdout.bin").read_bytes(), b"PASS\r\n")
        self.assertEqual((self.evidence_dir / "stderr.bin").read_bytes(), b"")
        self.assertEqual(json.loads((self.evidence_dir / "job-report.json").read_text(
            encoding="utf-8"))["pid"], 517)
        self.assertEqual(attestation["evidence"]["assets"]["stdout"]["sha256"],
                         hashlib.sha256(b"PASS\r\n").hexdigest().upper())

    def test_injector_failure_reports_return_code_and_output(self) -> None:
        process = SimpleNamespace(pid=4123)
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command, returncode=3, stdout=b"partial output\n",
                              stderr=b"FAIL: InjectLibrary error=5\n")
        with mock.patch(
            "xar_autoplayer.runtime.run_contained_injector_command", return_value=result
        ), self.assertRaisesRegex(
            AgentError, "rc=3.*InjectLibrary error=5"
        ):
            _inject_native_bridge(process, self.config, self.evidence_dir)

    def test_unproven_job_blocks_ck3_resume_and_marker_clear(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command, tree=False, status="RED_TIMEOUT",
                              error="deadline expired")
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        process.resume.assert_not_called()
        self.assertFalse(process.injector_attestation["complete_process_tree_proven"])
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_contradictory_job_result_blocks_resume_and_marker_clear(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command, error="helper cleanup failed")
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        process.resume.assert_not_called()
        self.assertFalse(process.injector_attestation["complete_process_tree_proven"])
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_job_report_wrong_pid_blocks_resume_and_marker_clear(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command)
        result.report["pre_resume_job_pids"] = [518]
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        process.resume.assert_not_called()
        self.assertFalse(process.injector_attestation["complete_process_tree_proven"])
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_forged_target_pid_cannot_override_local_identity(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        result = self.outcome(command)
        result.report["target_ck3_pid"] = 9999
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=result), self.assertRaises(NativeInjectorError):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        process.resume.assert_not_called()
        self.assertEqual(process.injector_attestation["target_ck3_pid"], 4123)
        self.assertFalse(process.injector_attestation["complete_process_tree_proven"])
        self.assertEqual(json.loads((self.evidence_dir / "job-report.json").read_text(
            encoding="utf-8"))["target_ck3_pid"], 9999)
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_overflow_or_reader_error_cannot_claim_complete_output(self) -> None:
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        for field, invalid in (("stdout_overflow", True),
                               ("stderr_reader_error", "reader failed")):
            with self.subTest(field=field):
                process = SimpleNamespace(pid=4123, resume=mock.Mock())
                evidence_dir = self.evidence_dir / field
                result = self.outcome(command)
                result.report[field] = invalid
                with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                                return_value=result), self.assertRaises(NativeInjectorError):
                    _resume_with_native_bridge(process, self.config,
                                               injector_evidence_dir=evidence_dir)
                process.resume.assert_not_called()
                self.assertFalse(process.injector_attestation[
                    "complete_process_tree_proven"])
                self.assertTrue((evidence_dir / "job-report.json").is_file())

    def test_raw_evidence_write_failure_blocks_resume_and_keeps_marker(self) -> None:
        from xar_autoplayer import runtime

        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        command = [str(self.config.injector_path), "4123", str(self.config.dll_path)]
        real_write = runtime._write_injector_evidence

        def fail_stdout(path: Path, content: bytes) -> dict[str, object]:
            if path.name == "stdout.bin":
                raise OSError("fixture evidence disk failure")
            return real_write(path, content)

        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command",
                        return_value=self.outcome(command)), mock.patch.object(
            runtime, "_write_injector_evidence", side_effect=fail_stdout
        ), self.assertRaisesRegex(NativeInjectorError, "raw evidence"):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        process.resume.assert_not_called()
        self.assertEqual(process.injector_attestation["status"], "RED_EVIDENCE_WRITE")
        self.assertTrue((self.evidence_dir / "argv.json").is_file())
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_existing_attempt_directory_cannot_be_overwritten(self) -> None:
        process = SimpleNamespace(pid=4123, resume=mock.Mock())
        self.evidence_dir.mkdir()
        original = self.evidence_dir / "argv.json"
        original.write_bytes(b"historical-attempt")
        with mock.patch("xar_autoplayer.runtime.run_contained_injector_command") as helper, \
             self.assertRaisesRegex(NativeInjectorError, "evidence setup failed"):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        helper.assert_not_called()
        process.resume.assert_not_called()
        self.assertEqual(original.read_bytes(), b"historical-attempt")
        with self.assertRaises(UnsafeCleanupError):
            _require_injector_cleanup_before_marker_clear(process)

    def test_injection_completes_before_primary_thread_resume(self) -> None:
        calls: list[str] = []
        process = SimpleNamespace(resume=lambda: calls.append("resume"))
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge",
            side_effect=lambda *_args: (calls.append("inject") or
                                        {"injector_root_reaped": True,
                                         "complete_process_tree_proven": True}),
        ):
            _resume_with_native_bridge(process, self.config,
                                       injector_evidence_dir=self.evidence_dir)
        self.assertEqual(calls, ["inject", "resume"])

    def test_disabled_launch_resumes_without_invoking_injector(self) -> None:
        process = mock.Mock()
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge"
        ) as inject:
            _resume_with_native_bridge(process, None)
        inject.assert_not_called()
        process.resume.assert_called_once_with()

    def test_injector_timeout_is_a_launch_error(self) -> None:
        process = SimpleNamespace(pid=4123)
        with mock.patch(
            "xar_autoplayer.runtime.run_contained_injector_command",
            side_effect=subprocess.TimeoutExpired(["injector"], 30),
        ), self.assertRaisesRegex(AgentError, "could not complete"):
            _inject_native_bridge(process, self.config, self.evidence_dir)
        self.assertTrue((self.evidence_dir / "argv.json").is_file())
        self.assertTrue((self.evidence_dir / "call-error.json").is_file())


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
