from __future__ import annotations

import os
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
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    DEFAULT_NATIVE_BRIDGE_PIPE,
    NATIVE_BRIDGE_DISABLED,
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
    NativeBridgeLaunchConfig,
    _ck3_launch_command,
    _create_suspended_process,
    _inject_native_bridge,
    _native_bridge_child_environment,
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
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\test",
            dll_path=Path("C:/native/xar_ck3_bridge.dll"),
            injector_path=Path("C:/native/xar_ck3_bridge_injector.exe"),
        )

    def test_existing_injector_cli_receives_pid_and_dll(self) -> None:
        process = SimpleNamespace(pid=4123)
        result = SimpleNamespace(returncode=0, stdout="PASS", stderr="")
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.run", return_value=result
        ) as run:
            _inject_native_bridge(process, self.config)
        self.assertEqual(
            run.call_args.args[0],
            [
                str(self.config.injector_path),
                "4123",
                str(self.config.dll_path),
            ],
        )
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertFalse(run.call_args.kwargs["check"])

    def test_injector_failure_reports_return_code_and_output(self) -> None:
        process = SimpleNamespace(pid=4123)
        result = SimpleNamespace(
            returncode=3,
            stdout="partial output\n",
            stderr="FAIL: InjectLibrary error=5\n",
        )
        with mock.patch(
            "xar_autoplayer.runtime.subprocess.run", return_value=result
        ), self.assertRaisesRegex(
            AgentError, "rc=3.*InjectLibrary error=5"
        ):
            _inject_native_bridge(process, self.config)

    def test_injection_completes_before_primary_thread_resume(self) -> None:
        calls: list[str] = []
        process = SimpleNamespace(resume=lambda: calls.append("resume"))
        with mock.patch(
            "xar_autoplayer.runtime._inject_native_bridge",
            side_effect=lambda *_args: calls.append("inject"),
        ):
            _resume_with_native_bridge(process, self.config)
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
            "xar_autoplayer.runtime.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["injector"], 30),
        ), self.assertRaisesRegex(AgentError, "could not complete"):
            _inject_native_bridge(process, self.config)


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
