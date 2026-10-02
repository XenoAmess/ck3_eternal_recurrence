"""No-launch fault tests for the H2743 profile CLI wait/renew cleanup path."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


RUNNER = Path(__file__).with_name("run_h2743_dejure_readonly_v3.py")


def load_runner():
    spec = importlib.util.spec_from_file_location("h2743_profile_cleanup_test_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("H2743 runner module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeProfileProcess:
    pid = 2743001

    def __init__(self, attempt: Path, *, renew_timeout: bool = True,
                 terminate_fails: bool = False, kill_fails: bool = False) -> None:
        self.attempt = attempt
        self.renew_timeout = renew_timeout
        self.terminate_fails = terminate_fails
        self.kill_fails = kill_fails
        self.returncode: int | None = None
        self.wait_count = 0
        self.terminate_count = 0
        self.kill_count = 0

    def wait(self, *, timeout: float) -> int:
        self.wait_count += 1
        if self.renew_timeout and self.wait_count == 1:
            raise subprocess.TimeoutExpired(["fake-profile-cli"], timeout)
        if self.returncode is None:
            raise subprocess.TimeoutExpired(["fake-profile-cli"], timeout)
        return self.returncode

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.terminate_count += 1
        if not (self.attempt / "prepare-profile-unsafe-cleanup.json").is_file():
            raise AssertionError("unsafe marker was not written before termination")
        if self.terminate_fails:
            raise OSError("synthetic terminate failure")
        self.returncode = 1

    def kill(self) -> None:
        self.kill_count += 1
        if self.kill_fails:
            raise OSError("synthetic kill failure")
        self.returncode = 1


class ProfileCliCleanupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = load_runner()

    def test_v5_direct_helper_call_stops_before_write_or_popen(self) -> None:
        self.runner.select_candidate(self.runner.HEAD_STORAGE_CANDIDATE)
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            with patch.object(self.runner, "write_new", side_effect=AssertionError("write reached")), \
                    patch.object(self.runner.subprocess, "Popen", side_effect=AssertionError("child spawned")):
                with self.assertRaisesRegex(RuntimeError, "LIVE_STOP_CAS_MIGRATION_PENDING"):
                    self.runner.call_profile_cli(attempt, attempt / "state", "prepare-profile",
                                                 ["prepare-profile"], "test-task")
            self.assertEqual(list(attempt.iterdir()), [])

    def call(self, attempt: Path, process: FakeProfileProcess, *, renew_fails: bool) -> dict[str, object]:
        with patch.object(self.runner.subprocess, "Popen", return_value=process), \
                patch.object(self.runner, "renew_screen_lease",
                             side_effect=RuntimeError("synthetic lease lost") if renew_fails else None):
            return self.runner.call_profile_cli(attempt, attempt / "state", "prepare-profile",
                                                ["prepare-profile"], "test-task" if renew_fails else None)

    def test_renew_failure_marks_red_before_stopping_and_reaping_child(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt)
            with self.assertRaisesRegex(RuntimeError, "synthetic lease lost"):
                self.call(attempt, process, renew_fails=True)
            marker = json.loads((attempt / "prepare-profile-unsafe-cleanup.json").read_text(encoding="utf-8"))
            result = json.loads((attempt / "prepare-profile-cleanup-result.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["status"], "RED_PROFILE_CLI_INTERRUPTED")
            self.assertTrue(marker["manual_recovery_required"])
            self.assertFalse(marker["process_tree_cleanup_proven"])
            self.assertEqual((process.terminate_count, process.kill_count), (1, 0))
            self.assertTrue(result["direct_child_reaped"])
            self.assertFalse(result["process_tree_cleanup_proven"])

    def test_failed_terminate_and_kill_keep_unsafe_marker_and_stop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt, terminate_fails=True, kill_fails=True)
            with self.assertRaisesRegex(RuntimeError, "cleanup unproven"):
                self.call(attempt, process, renew_fails=True)
            result = json.loads((attempt / "prepare-profile-cleanup-result.json").read_text(encoding="utf-8"))
            self.assertEqual((process.terminate_count, process.kill_count), (1, 1))
            self.assertFalse(result["direct_child_reaped"])
            self.assertEqual(len(result["cleanup_errors"]), 2)
            self.assertTrue((attempt / "prepare-profile-unsafe-cleanup.json").is_file())

    def test_failed_terminate_falls_back_to_kill_and_keeps_red_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt, terminate_fails=True)
            with self.assertRaisesRegex(RuntimeError, "synthetic lease lost"):
                self.call(attempt, process, renew_fails=True)
            result = json.loads((attempt / "prepare-profile-cleanup-result.json").read_text(encoding="utf-8"))
            self.assertEqual((process.terminate_count, process.kill_count), (1, 1))
            self.assertTrue(result["direct_child_reaped"])
            self.assertEqual(len(result["cleanup_errors"]), 1)
            self.assertTrue((attempt / "prepare-profile-unsafe-cleanup.json").is_file())

    def test_marker_write_failure_still_reaps_child_and_stops(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt)
            original_write_new = self.runner.write_new

            def fail_marker(path: Path, value: object) -> None:
                if path.name == "prepare-profile-unsafe-cleanup.json":
                    raise OSError("synthetic marker failure")
                original_write_new(path, value)

            # The fake process checks for a marker in terminate(), forcing
            # the fallback kill path after this deliberately failed write.
            with patch.object(self.runner, "write_new", side_effect=fail_marker):
                with self.assertRaisesRegex(RuntimeError, "cleanup unproven"):
                    self.call(attempt, process, renew_fails=True)
            result = json.loads((attempt / "prepare-profile-cleanup-result.json").read_text(encoding="utf-8"))
            self.assertEqual((process.terminate_count, process.kill_count), (1, 1))
            self.assertTrue(result["direct_child_reaped"])
            self.assertFalse(result["unsafe_marker_written"])

    def test_cleanup_receipt_write_failure_keeps_unsafe_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt)
            original_write_new = self.runner.write_new

            def fail_cleanup_receipt(path: Path, value: object) -> None:
                if path.name == "prepare-profile-cleanup-result.json":
                    raise OSError("synthetic receipt failure")
                original_write_new(path, value)

            with patch.object(self.runner, "write_new", side_effect=fail_cleanup_receipt):
                with self.assertRaisesRegex(RuntimeError, "cleanup receipt unavailable; manual recovery required"):
                    self.call(attempt, process, renew_fails=True)
            self.assertEqual((process.terminate_count, process.kill_count), (1, 0))
            self.assertIsNotNone(process.returncode)
            self.assertTrue((attempt / "prepare-profile-unsafe-cleanup.json").is_file())

    def test_successful_profile_cli_retains_original_receipt_shape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="h2743-profile-cleanup-") as folder:
            attempt = Path(folder)
            process = FakeProfileProcess(attempt, renew_timeout=False)
            process.returncode = 0
            result = self.call(attempt, process, renew_fails=False)
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(set(result), {"exit_code", "stdout_sha256", "stderr_sha256"})
            self.assertFalse((attempt / "prepare-profile-unsafe-cleanup.json").exists())
            self.assertEqual((process.terminate_count, process.kill_count), (0, 0))


if __name__ == "__main__":
    unittest.main()
