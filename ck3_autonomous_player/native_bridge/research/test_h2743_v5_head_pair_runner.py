"""Focused no-launch identity checks for the new H2743 v5 pair."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


RUNNER = Path(__file__).with_name("run_h2743_dejure_readonly_v3.py")


def load_runner():
    spec = importlib.util.spec_from_file_location("h2743_v5_head_pair_test_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("H2743 runner module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HeadStoragePairTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = load_runner()

    def test_new_pair_binds_exact_binaries_builds_and_source(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        runner.verify_head_storage_pair()
        self.assertEqual(runner.DLL_SHA, runner.HEAD_STORAGE_DLL_SHA)
        self.assertEqual(runner.INJECTOR_SHA, runner.HEAD_STORAGE_INJECTOR_SHA)
        self.assertEqual(runner.candidate_manifest_sha256(), runner.HEAD_STORAGE_PAIR_SHA)
        self.assertIsNotNone(runner.provenance_source_hashes())
        self.assertTrue(runner.is_storage_candidate())

    def test_legacy_attempt15_keeps_its_original_identity(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        runner.select_candidate(runner.STORAGE_CANDIDATE)
        self.assertEqual(runner.DLL, runner.STORAGE_DLL)
        self.assertEqual(runner.DLL_SHA, runner.STORAGE_DLL_SHA)
        self.assertEqual(runner.INJECTOR, runner.BASE_INJECTOR)
        self.assertEqual(runner.INJECTOR_SHA, runner.BASE_INJECTOR_SHA)
        self.assertIsNone(runner.candidate_manifest_sha256())
        self.assertIsNone(runner.provenance_source_hashes())
        self.assertTrue(runner.is_storage_candidate())

    def test_rehashed_manifest_with_wrong_head_is_rejected(self) -> None:
        runner = self.runner
        data = json.loads(runner.HEAD_STORAGE_PAIR.read_text(encoding="utf-8"))
        data["head"] = "0" * 40
        with tempfile.TemporaryDirectory(prefix="h2743-v5-pair-test-") as folder:
            changed = Path(folder) / "pair.json"
            changed.write_text(json.dumps(data), encoding="utf-8")
            digest = hashlib.sha256(changed.read_bytes()).hexdigest().upper()
            with patch.object(runner, "HEAD_STORAGE_PAIR", changed), \
                    patch.object(runner, "HEAD_STORAGE_PAIR_SHA", digest):
                with self.assertRaisesRegex(RuntimeError, "identity or boundary changed"):
                    runner.verify_head_storage_pair()

    def test_wrong_pinned_build_receipt_is_rejected(self) -> None:
        runner = self.runner
        with patch.object(runner, "HEAD_STORAGE_DLL_RESULT_SHA", "0" * 64):
            with self.assertRaisesRegex(RuntimeError, "pair entry changed"):
                runner.verify_head_storage_pair()

    def test_old_prepared_attempt_cannot_be_reused_by_new_candidate(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        old_attempt = runner.BASE_ROOT / "attempt-15-dejure-baseline-no-launch"
        self.assertTrue(old_attempt.is_dir())
        with self.assertRaisesRegex(RuntimeError, "READY absent"):
            runner.prepared_state(old_attempt)

    def test_help_exposes_both_distinct_candidate_names(self) -> None:
        result = subprocess.run([sys.executable, str(RUNNER), "--help"],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("war-storage-candidate-v5-head24c51", result.stdout)
        self.assertIn("war-storage-candidate-v5,", result.stdout)
        self.assertIn("--seal-no-launch", result.stdout)
        self.assertIn("--prepare-live-profile", result.stdout)
        self.assertIn("--prepare-no-launch", result.stdout)

    def test_static_only_check_never_spawns_a_child(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        with patch.object(runner.subprocess, "run", side_effect=AssertionError("child spawned")), \
                patch.object(runner.subprocess, "Popen", side_effect=AssertionError("child spawned")):
            result = runner.check_static(static_only=True)
        self.assertEqual(result["candidate_kind"], runner.HEAD_STORAGE_CANDIDATE)
        self.assertEqual(result["cli_help_probes"], "not_run_static_only")
        self.assertEqual(result["process_module_map_probe"], "not_run_static_only")
        self.assertIs(result["task_bus_file_checked"], False)

    def test_static_seal_is_append_only_and_not_live_ready(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        with tempfile.TemporaryDirectory(prefix="h2743-v5-static-seal-") as folder, \
                patch.object(runner, "ROOT", Path(folder)), \
                patch.object(runner, "check_static", return_value={"status": "test-static"}) as checked, \
                patch.object(runner.subprocess, "run", side_effect=AssertionError("child spawned")), \
                patch.object(runner.subprocess, "Popen", side_effect=AssertionError("child spawned")):
            runner.static_seal("attempt-900001-dejure-baseline-no-launch")
            attempt = Path(folder) / "attempt-900001-dejure-baseline-no-launch"
            self.assertEqual([entry.name for entry in attempt.iterdir()], ["static-seal.json"])
            seal = json.loads((attempt / "static-seal.json").read_text(encoding="utf-8"))
            self.assertEqual(seal["status"], "STATIC_SEALED_LIVE_PREPARE_PENDING")
            self.assertIs(seal["child_process_started"], False)
            self.assertIs(seal["screen_lease_checked"], False)
            runner.verify_static_seal(attempt)
            with self.assertRaises(FileExistsError):
                runner.static_seal("attempt-900001-dejure-baseline-no-launch")
            seal["candidate_dll_sha256"] = "0" * 64
            (attempt / "static-seal.json").write_text(json.dumps(seal), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "static seal changed"):
                runner.verify_static_seal(attempt)
            checked.assert_called_with(static_only=True)

    def test_sealed_live_prepare_requires_a_screen_before_child_probes(self) -> None:
        runner = self.runner
        runner.select_candidate(runner.HEAD_STORAGE_CANDIDATE)
        with tempfile.TemporaryDirectory(prefix="h2743-v5-static-seal-") as folder, \
                patch.object(runner, "ROOT", Path(folder)), \
                patch.object(runner, "check_static", return_value={"status": "test-static"}), \
                patch.object(runner, "screen_lease", side_effect=RuntimeError("no screen lease")), \
                patch.object(runner.subprocess, "run", side_effect=AssertionError("child spawned")), \
                patch.object(runner.subprocess, "Popen", side_effect=AssertionError("child spawned")):
            runner.static_seal("attempt-900002-dejure-baseline-no-launch")
            with self.assertRaisesRegex(RuntimeError, "no screen lease"):
                runner.prepare_no_launch("attempt-900002-dejure-baseline-no-launch",
                                         "h2743-test-task", sealed_attempt=True)


if __name__ == "__main__":
    unittest.main()
