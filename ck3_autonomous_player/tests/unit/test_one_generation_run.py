from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer.environment import EnvironmentSpec  # noqa: E402
from xar_autoplayer.one_generation_run import (  # noqa: E402
    native_one_generation_run,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig  # noqa: E402
import xar_autoplayer.one_generation_run as runner_module  # noqa: E402


class NativeOneGenerationRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="xar-one-generation-run-"
        )
        root = Path(self.temporary.name)
        self.spec = EnvironmentSpec(root / "state", root / "game")
        self.dll_path = root / "xar_ck3_bridge.dll"
        self.injector_path = root / "xar_ck3_bridge_injector.exe"
        self.dll_path.write_bytes(b"fake bridge dll")
        self.injector_path.write_bytes(b"fake bridge injector")
        self.config = NativeBridgeLaunchConfig(
            mode="native-headless",
            pipe_name=r"\\.\pipe\one-generation-test",
            dll_path=self.dll_path,
            injector_path=self.injector_path,
        )
        self.seed = {
            "name": "xar_checkpoint.ck3",
            "load_save_name": "xar_checkpoint",
            "path": str(root / "xar_checkpoint.ck3"),
            "size": 123,
            "sha256": "a" * 64,
            "saved_date_raw": 53_171_400,
            "history_index": 9,
        }
        self.seed_bundle = {
            "status": "verified_immutable_copy",
            "episode_character_id": 707,
            "episode_run_id": "native-707-test-run",
            "checkpoint": {
                "path": "seed/xar_checkpoint.ck3",
                "size": 123,
                "sha256": "a" * 64,
            },
            "driver_state": {
                "path": "seed/driver-state.json",
                "size": 456,
                "sha256": "b" * 64,
            },
            "manifest": {
                "path": "seed/manifest.json",
                "size": 789,
                "sha256": "c" * 64,
            },
            "source_checkpoint": self.seed,
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _run_with_core(self, core: dict[str, object]) -> dict[str, object]:
        with mock.patch.object(
            runner_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value=self.seed,
        ), mock.patch.object(
            runner_module,
            "_archive_seed_bundle",
            return_value=self.seed_bundle,
        ), mock.patch.object(
            runner_module,
            "native_auto_run",
            return_value=core,
        ) as core_mock:
            report = native_one_generation_run(
                self.spec,
                max_turns=50_000,
                timeout_seconds=7_200,
                readiness_timeout_seconds=30,
                checkpoint_every_eligible_advances=180,
                native_bridge=self.config,
            )
        core_mock.assert_called_once_with(
            self.spec,
            turn_count=50_000,
            timeout_seconds=7_200,
            readiness_timeout_seconds=30,
            cold_start_checkpoint=True,
            native_bridge=self.config,
            checkpoint_every_eligible_advances=180,
            completion_contract="one_generation",
        )
        return report

    def test_seed_bundle_archives_exact_checkpoint_and_driver_state(self) -> None:
        checkpoint = self.spec.profile_dir / "save games" / "xar_checkpoint.ck3"
        checkpoint.parent.mkdir(parents=True)
        checkpoint_bytes = b"fixed production checkpoint"
        checkpoint.write_bytes(checkpoint_bytes)
        state_path = self.spec.state_dir / "native-session" / "driver-state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(
            json.dumps(
                {
                    "episode_character_id": 707,
                    "episode_run_id": "native-707-test-run",
                }
            ),
            encoding="utf-8",
        )
        run_dir = self.spec.state_dir / "runs" / "fixture"
        run_dir.mkdir(parents=True)
        seed = {
            "path": str(checkpoint),
            "size": len(checkpoint_bytes),
            "sha256": hashlib.sha256(checkpoint_bytes).hexdigest(),
            "saved_date_raw": 53_171_400,
        }

        bundle = runner_module._archive_seed_bundle(
            self.spec, run_dir, seed
        )

        self.assertEqual(bundle["status"], "verified_immutable_copy")
        self.assertEqual(bundle["episode_character_id"], 707)
        for label in ("checkpoint", "driver_state", "manifest"):
            entry = bundle[label]
            path = run_dir / entry["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(path.stat().st_size, entry["size"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                entry["sha256"],
            )

    def test_wrapper_persists_terminal_report_and_sidecar(self) -> None:
        terminal = {
            "status": "verified",
            "episode_character_id": 707,
            "score": 125,
        }
        report = self._run_with_core(
            {
                "format_version": 1,
                "kind": "ck3_native_auto_run",
                "fixed_seed": self.seed,
                "status": "episode_complete",
                "outcome": "qualified",
                "terminal": terminal,
                "first_blocker": None,
                "ok": True,
            }
        )

        self.assertTrue(report["ok"])
        self.assertTrue(report["finalized"])
        self.assertEqual(report["kind"], "ck3_native_one_generation_run")
        report_path = Path(report["report_path"])
        self.assertTrue(report_path.is_file())
        persisted = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["run_id"], report["run_id"])
        terminal_entry = report["artifacts"]["terminal_settlement"]
        terminal_path = report_path.parent / terminal_entry["path"]
        self.assertEqual(
            json.loads(terminal_path.read_text(encoding="utf-8")), terminal
        )
        self.assertNotIn("first_blocker", report["artifacts"])

    def test_wrapper_persists_first_blocker_for_incomplete_run(self) -> None:
        blocker = {
            "observed_at": "2026-08-27T00:00:00Z",
            "turn_index": 12,
            "stage": "planning",
            "kind": "planner_blocked",
            "message": "pending interaction has no executable response",
        }
        report = self._run_with_core(
            {
                "format_version": 1,
                "kind": "ck3_native_auto_run",
                "fixed_seed": self.seed,
                "status": "blocked",
                "outcome": "failed",
                "terminal": None,
                "first_blocker": blocker,
                "ok": False,
            }
        )

        self.assertFalse(report["ok"])
        blocker_entry = report["artifacts"]["first_blocker"]
        blocker_path = Path(report["report_path"]).parent / blocker_entry["path"]
        self.assertEqual(
            json.loads(blocker_path.read_text(encoding="utf-8")), blocker
        )
        self.assertNotIn("terminal_settlement", report["artifacts"])

    def test_checkpoint_failure_falls_back_to_immutable_seed_archive(self) -> None:
        blocker = {
            "observed_at": "2026-08-27T00:00:00Z",
            "turn_index": 3,
            "stage": "checkpoint",
            "kind": "checkpoint_failed",
            "checkpoint_recovery_invalidated": True,
            "last_durable_checkpoint": None,
            "recoverable_from_checkpoint": False,
        }
        report = self._run_with_core(
            {
                "format_version": 1,
                "kind": "ck3_native_auto_run",
                "fixed_seed": self.seed,
                "status": "stopped_on_error",
                "outcome": "failed",
                "terminal": None,
                "first_blocker": blocker,
                "error": "OSError: fixture checkpoint failed",
                "ok": False,
            }
        )

        rebound = report["first_blocker"]
        self.assertTrue(rebound["recoverable_from_checkpoint"])
        self.assertEqual(
            rebound["recovery_fallback"], "immutable_seed_archive"
        )
        anchor = rebound["last_durable_checkpoint"]
        self.assertEqual(anchor["status"], "verified_immutable_seed_fallback")
        self.assertEqual(anchor["sha256"], "a" * 64)
        self.assertEqual(anchor["saved_date_raw"], 53_171_400)
        self.assertEqual(anchor["episode_character_id"], 707)
        self.assertTrue(anchor["path"].endswith("seed\\xar_checkpoint.ck3"))
        self.assertTrue(
            anchor["driver_state"]["path"].endswith(
                "seed\\driver-state.json"
            )
        )

    def test_seed_archive_failure_still_finalizes_first_blocker(self) -> None:
        with mock.patch.object(
            runner_module,
            "validate_cold_start_checkpoint_for_pipe",
            return_value=self.seed,
        ), mock.patch.object(
            runner_module,
            "_archive_seed_bundle",
            side_effect=OSError("fixture archive failed"),
        ), mock.patch.object(runner_module, "native_auto_run") as core_mock:
            report = native_one_generation_run(
                self.spec,
                max_turns=50,
                timeout_seconds=100,
                readiness_timeout_seconds=10,
                native_bridge=self.config,
            )

        self.assertFalse(report["ok"])
        self.assertTrue(report["finalized"])
        self.assertEqual(
            report["first_blocker"]["kind"],
            "runner_failed_before_core_report",
        )
        self.assertIn("fixture archive failed", report["error"])
        self.assertIn("first_blocker", report["artifacts"])
        self.assertNotIn("seed_checkpoint", report["artifacts"])
        core_mock.assert_not_called()

    def test_seed_validation_failure_still_finalizes_first_blocker(self) -> None:
        with mock.patch.object(
            runner_module,
            "validate_cold_start_checkpoint_for_pipe",
            side_effect=OSError("fixture seed validation failed"),
        ), mock.patch.object(
            runner_module, "_archive_seed_bundle"
        ) as archive_mock, mock.patch.object(
            runner_module, "native_auto_run"
        ) as core_mock:
            report = native_one_generation_run(
                self.spec,
                max_turns=50,
                timeout_seconds=100,
                readiness_timeout_seconds=10,
                native_bridge=self.config,
            )

        self.assertFalse(report["ok"])
        self.assertTrue(report["finalized"])
        self.assertEqual(
            report["first_blocker"]["kind"],
            "runner_failed_before_core_report",
        )
        self.assertFalse(
            report["first_blocker"]["recoverable_from_checkpoint"]
        )
        self.assertIsNone(
            report["first_blocker"]["last_durable_checkpoint"]
        )
        self.assertEqual(report["seed_bundle"]["status"], "validation_pending")
        self.assertIn("fixture seed validation failed", report["error"])
        report_path = Path(report["report_path"])
        self.assertTrue(report_path.is_file())
        self.assertIn("first_blocker", report["artifacts"])
        archive_mock.assert_not_called()
        core_mock.assert_not_called()

    def test_cli_dispatch_and_exit_code_follow_strict_report(self) -> None:
        for ok, expected_code in ((True, 0), (False, 1)):
            with self.subTest(ok=ok):
                stdout = io.StringIO()
                with mock.patch.object(
                    cli, "make_spec", return_value=self.spec
                ), mock.patch.object(
                    cli,
                    "configure_native_bridge_launch_environment",
                    return_value=self.config,
                ), mock.patch.object(
                    runner_module,
                    "native_one_generation_run",
                    return_value={"ok": ok, "status": "fixture"},
                ) as run_mock, contextlib.redirect_stdout(stdout):
                    code = cli.main(
                        [
                            "--bridge-mode",
                            "native-headless",
                            "native-one-generation",
                            "--max-turns",
                            "1234",
                        ]
                    )

                self.assertEqual(code, expected_code)
                run_mock.assert_called_once_with(
                    self.spec,
                    max_turns=1234,
                    timeout_seconds=604800,
                    readiness_timeout_seconds=300,
                    checkpoint_every_eligible_advances=3,
                )
                self.assertIn(f'"ok": {str(ok).lower()}', stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
