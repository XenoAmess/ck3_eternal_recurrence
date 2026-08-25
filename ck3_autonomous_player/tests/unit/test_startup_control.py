from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
SCRIPT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_ROOT))
sys.path.insert(0, str(SCRIPT_ROOT))

import run_no_bridge_main_menu_control as main_menu_control_cli  # noqa: E402

from xar_autoplayer.runtime import (  # noqa: E402
    NATIVE_BRIDGE_DLL_ENV,
    NATIVE_BRIDGE_INJECTOR_ENV,
    NATIVE_BRIDGE_MODE_ENV,
    NATIVE_BRIDGE_PIPE_ENV,
)
from xar_autoplayer.startup_control import (  # noqa: E402
    _bridge_injection_disabled,
    _no_bridge_main_menu_survival_control_locked,
    _no_bridge_startup_control_locked,
    _wait_for_new_crash_bundle,
    build_no_bridge_main_menu_survival_plan,
    build_no_bridge_startup_control_plan,
)


class NoBridgeEnvironmentTests(unittest.TestCase):
    def test_context_forces_disabled_and_restores_exact_environment(self) -> None:
        environment = {
            NATIVE_BRIDGE_MODE_ENV: "native-headless",
            NATIVE_BRIDGE_PIPE_ENV: r"\\.\pipe\prior",
            NATIVE_BRIDGE_DLL_ENV: "prior.dll",
            NATIVE_BRIDGE_INJECTOR_ENV: "prior-injector.exe",
            "UNRELATED": "kept",
        }
        baseline = dict(environment)
        with _bridge_injection_disabled(environment):
            self.assertEqual(environment[NATIVE_BRIDGE_MODE_ENV], "disabled")
            self.assertNotIn(NATIVE_BRIDGE_PIPE_ENV, environment)
            self.assertNotIn(NATIVE_BRIDGE_DLL_ENV, environment)
            self.assertNotIn(NATIVE_BRIDGE_INJECTOR_ENV, environment)
            self.assertEqual(environment["UNRELATED"], "kept")
        self.assertEqual(environment, baseline)


class NoBridgeStartupPlanTests(unittest.TestCase):
    def test_plan_is_read_only_and_binds_exact_checkpoint(self) -> None:
        spec = SimpleNamespace(
            state_dir=Path("C:/Temp/control-state"),
            profile_dir=Path("C:/Temp/control-state/profile"),
            game_exe=Path("C:/CK3/binaries/ck3.exe"),
        )
        checkpoint = {"sha256": "a" * 64, "load_save_name": "xar_checkpoint"}
        with mock.patch(
            "xar_autoplayer.startup_control.ensure_state_path_safe"
        ), mock.patch(
            "xar_autoplayer.startup_control.validate_cold_start_checkpoint_for_pipe",
            return_value=checkpoint,
        ) as validate, mock.patch(
            "xar_autoplayer.startup_control.launch"
        ) as launch_mock:
            plan = build_no_bridge_startup_control_plan(
                spec,
                checkpoint_pipe_name=r"\\.\pipe\exact-control",
                timeout_seconds=240,
            )

        validate.assert_called_once_with(spec, r"\\.\pipe\exact-control")
        launch_mock.assert_not_called()
        self.assertFalse(plan["execute"])
        self.assertFalse(plan["native_bridge"]["dll_injection"])
        self.assertFalse(plan["native_bridge"]["mcp"])
        self.assertFalse(plan["game_input"])
        self.assertFalse(plan["save_tree_write_allowed"])
        self.assertEqual(
            plan["acceptance_claim"], "diagnostic_outcome_and_cleanup_only"
        )
        self.assertEqual(plan["stable_profile_window_seconds"], 30.0)
        self.assertIn("-loadsave=xar_checkpoint", plan["launch_arguments"])

    def test_main_menu_plan_is_read_only_and_has_no_save_argument(self) -> None:
        spec = SimpleNamespace(
            state_dir=Path("C:/Temp/control-state"),
            profile_dir=Path("C:/Temp/control-state/profile"),
            game_exe=Path("C:/CK3/binaries/ck3.exe"),
        )
        with mock.patch(
            "xar_autoplayer.startup_control.ensure_state_path_safe"
        ), mock.patch(
            "xar_autoplayer.startup_control.validate_cold_start_checkpoint_for_pipe"
        ) as validate, mock.patch(
            "xar_autoplayer.startup_control.launch"
        ) as launch_mock:
            plan = build_no_bridge_main_menu_survival_plan(
                spec, timeout_seconds=240
            )

        validate.assert_not_called()
        launch_mock.assert_not_called()
        self.assertFalse(plan["execute"])
        self.assertEqual(
            plan["launch_target"], "main_menu_without_save_load"
        )
        self.assertFalse(plan["gameplay_functionality_claimed"])
        self.assertFalse(plan["map_ready_claimed"])
        self.assertFalse(plan["game_input"])
        self.assertFalse(plan["save_tree_write_allowed"])
        self.assertFalse(
            any("loadsave" in argument.casefold() for argument in plan["launch_arguments"])
        )
        self.assertFalse(
            any("continuelastsave" in argument.casefold() for argument in plan["launch_arguments"])
        )


class NoBridgeStartupLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-no-bridge-control-"
        )
        root = Path(self.temporary.name)
        self.spec = SimpleNamespace(
            state_dir=root,
            profile_dir=root / "profile",
            game_exe=root / "game" / "binaries" / "ck3.exe",
        )
        self.spec.profile_dir.mkdir(parents=True)
        self.checkpoint = {
            "name": "xar_checkpoint.ck3",
            "load_save_name": "xar_checkpoint",
            "sha256": "b" * 64,
        }
        self.save_snapshot = {"digest": "c" * 64, "files": {}}
        self.shutdown = {
            "ok": True,
            "cleanup_proven": True,
            "contract_errors": [],
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _common_patches(self, handle: object):
        return (
            mock.patch(
                "xar_autoplayer.startup_control.validate_cold_start_checkpoint_for_pipe",
                return_value=self.checkpoint,
            ),
            mock.patch(
                "xar_autoplayer.startup_control._save_snapshot",
                side_effect=(self.save_snapshot, self.save_snapshot),
            ),
            mock.patch(
                "xar_autoplayer.startup_control._crash_directory_names",
                return_value=frozenset({"old-crash"}),
            ),
            mock.patch(
                "xar_autoplayer.startup_control.launch", return_value=handle
            ),
            mock.patch(
                "xar_autoplayer.startup_control.stop_tracked",
                return_value=self.shutdown,
            ),
        )

    def test_stable_profile_window_uses_no_dll_launch_and_managed_stop(self) -> None:
        process = mock.Mock(pid=4242)
        process.poll.side_effect = (None, None)
        handle = SimpleNamespace(process=process)
        patches = self._common_patches(handle)
        with patches[0], patches[1], patches[2], patches[3] as launch_mock, patches[
            4
        ] as stop_mock, mock.patch(
            "xar_autoplayer.startup_control._profile_window_visible",
            return_value=True,
        ), mock.patch(
            "xar_autoplayer.startup_control.time.monotonic",
            side_effect=(0.0, 1.0, 3.1, 4.0),
        ), mock.patch(
            "xar_autoplayer.startup_control.time.sleep"
        ), mock.patch.dict(
            os.environ,
            {
                NATIVE_BRIDGE_MODE_ENV: "native-headless",
                NATIVE_BRIDGE_PIPE_ENV: r"\\.\pipe\should-not-leak",
                NATIVE_BRIDGE_DLL_ENV: "should-not-load.dll",
                NATIVE_BRIDGE_INJECTOR_ENV: "should-not-run.exe",
            },
            clear=False,
        ):
            report = _no_bridge_startup_control_locked(
                self.spec,
                checkpoint_pipe_name=r"\\.\pipe\checkpoint-owner",
                timeout_seconds=10.0,
                stable_seconds=2.0,
                poll_seconds=0.01,
            )

        launch_mock.assert_called_once_with(
            self.spec,
            native_bridge=None,
            load_save_name="xar_checkpoint",
        )
        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(report["exit_reason"], "stable_profile_window")
        self.assertFalse(report["native_bridge"]["dll_injection"])
        self.assertFalse(report["game_input"])
        self.assertFalse(report["map_ready_claimed"])
        self.assertTrue(report["save_tree_unchanged"])
        self.assertTrue(report["cleanup_proven"])
        self.assertTrue(report["ok"])

    def test_process_crash_records_complete_new_minidump(self) -> None:
        process = mock.Mock(pid=4343)
        process.poll.return_value = -1_073_741_819
        handle = SimpleNamespace(process=process)
        crash = {
            "path": "C:/Temp/profile/crashes/ck3_new",
            "complete": True,
            "minidump_recorded": True,
            "files": {"minidump.dmp": {"size": 123, "sha256": "d" * 64}},
        }
        patches = self._common_patches(handle)
        with patches[0], patches[1], patches[2], patches[3], patches[4] as stop_mock, mock.patch(
            "xar_autoplayer.startup_control._wait_for_new_crash_bundle",
            return_value=crash,
        ) as wait_crash, mock.patch(
            "xar_autoplayer.startup_control.time.monotonic",
            side_effect=(0.0, 1.0),
        ):
            report = _no_bridge_startup_control_locked(
                self.spec,
                checkpoint_pipe_name=r"\\.\pipe\checkpoint-owner",
                timeout_seconds=10.0,
                stable_seconds=2.0,
                poll_seconds=0.01,
            )

        wait_crash.assert_called_once_with(
            self.spec.profile_dir, frozenset({"old-crash"})
        )
        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(report["exit_reason"], "process_exit")
        self.assertEqual(report["process_exit_code"], -1_073_741_819)
        self.assertTrue(report["crash_bundle"]["minidump_recorded"])
        self.assertTrue(report["diagnostic_outcome_recorded"])
        self.assertEqual(
            report["acceptance_claim"],
            "diagnostic_outcome_and_cleanup_only",
        )
        self.assertFalse(report["gameplay_functionality_claimed"])
        # Top-level ok reports that the diagnostic control itself completed;
        # this branch deliberately proves that ok can coexist with a CK3 crash.
        self.assertTrue(report["ok"])

    def test_main_menu_survival_omits_loadsave_and_preserves_claim_boundary(
        self,
    ) -> None:
        process = mock.Mock(pid=4444)
        process.poll.side_effect = (None, None)
        handle = SimpleNamespace(process=process)
        with mock.patch(
            "xar_autoplayer.startup_control.validate_cold_start_checkpoint_for_pipe"
        ) as validate, mock.patch(
            "xar_autoplayer.startup_control._save_snapshot",
            side_effect=(self.save_snapshot, self.save_snapshot),
        ), mock.patch(
            "xar_autoplayer.startup_control._crash_directory_names",
            return_value=frozenset({"old-crash"}),
        ), mock.patch(
            "xar_autoplayer.startup_control.launch", return_value=handle
        ) as launch_mock, mock.patch(
            "xar_autoplayer.startup_control.stop_tracked",
            return_value=self.shutdown,
        ) as stop_mock, mock.patch(
            "xar_autoplayer.startup_control._profile_window_visible",
            return_value=True,
        ), mock.patch(
            "xar_autoplayer.startup_control.time.monotonic",
            side_effect=(0.0, 1.0, 3.1, 4.0),
        ), mock.patch(
            "xar_autoplayer.startup_control.time.sleep"
        ):
            report = _no_bridge_main_menu_survival_control_locked(
                self.spec,
                timeout_seconds=10.0,
                stable_seconds=2.0,
                poll_seconds=0.01,
            )

        validate.assert_not_called()
        launch_mock.assert_called_once_with(self.spec, native_bridge=None)
        stop_mock.assert_called_once_with(handle, require_running=False)
        self.assertEqual(
            report["kind"], "ck3_no_bridge_main_menu_survival_control"
        )
        self.assertEqual(
            report["launch_target"], "main_menu_without_save_load"
        )
        self.assertIsNone(report["checkpoint"])
        self.assertIsNone(report["checkpoint_pipe_name"])
        self.assertEqual(report["exit_reason"], "stable_profile_window")
        self.assertFalse(report["gameplay_functionality_claimed"])
        self.assertFalse(report["map_ready_claimed"])
        self.assertTrue(report["save_tree_unchanged"])
        self.assertTrue(report["cleanup_proven"])
        self.assertTrue(report["ok"])


class CrashBundleFixtureTests(unittest.TestCase):
    def test_new_bundle_manifest_hashes_minidump_and_exception(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="xar-no-bridge-crash-fixture-"
        ) as temporary:
            profile = Path(temporary)
            bundle = profile / "crashes" / "ck3_20260825_150000"
            bundle.mkdir(parents=True)
            (bundle / "minidump.dmp").write_bytes(b"fixture-minidump")
            (bundle / "exception.txt").write_text(
                "Unhandled Exception C0000005 at RVA 1DABD89\n",
                encoding="utf-8",
            )
            result = _wait_for_new_crash_bundle(
                profile,
                frozenset(),
                wait_seconds=0.1,
                quiet_seconds=0.0,
                poll_seconds=0.001,
            )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertTrue(result["complete"])
        self.assertTrue(result["minidump_recorded"])
        self.assertIn("minidump.dmp", result["files"])
        self.assertIn("RVA 1DABD89", result["exception_text"])


class MainMenuControlCliTests(unittest.TestCase):
    def test_default_is_dry_run_and_does_not_execute(self) -> None:
        spec = object()
        plan = {"kind": "dry-plan", "execute": False}
        with mock.patch.object(
            main_menu_control_cli, "make_spec", return_value=spec
        ), mock.patch.object(
            main_menu_control_cli,
            "build_no_bridge_main_menu_survival_plan",
            return_value=plan,
        ) as build, mock.patch.object(
            main_menu_control_cli, "no_bridge_main_menu_survival_control"
        ) as execute, mock.patch("builtins.print"):
            status = main_menu_control_cli.main(
                ["--state-dir", "C:/Temp/state", "--game-dir", "C:/CK3"]
            )

        self.assertEqual(status, 0)
        build.assert_called_once_with(spec, timeout_seconds=240.0)
        execute.assert_not_called()

    def test_execute_flag_is_the_only_execution_route(self) -> None:
        spec = object()
        report = {"kind": "execute-report", "ok": True}
        with mock.patch.object(
            main_menu_control_cli, "make_spec", return_value=spec
        ), mock.patch.object(
            main_menu_control_cli, "build_no_bridge_main_menu_survival_plan"
        ) as build, mock.patch.object(
            main_menu_control_cli,
            "no_bridge_main_menu_survival_control",
            return_value=report,
        ) as execute, mock.patch("builtins.print"):
            status = main_menu_control_cli.main(
                [
                    "--state-dir",
                    "C:/Temp/state",
                    "--game-dir",
                    "C:/CK3",
                    "--execute",
                ]
            )

        self.assertEqual(status, 0)
        build.assert_not_called()
        execute.assert_called_once_with(spec, timeout_seconds=240.0)


if __name__ == "__main__":
    unittest.main()
