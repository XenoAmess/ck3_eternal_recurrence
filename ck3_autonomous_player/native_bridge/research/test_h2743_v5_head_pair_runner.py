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


if __name__ == "__main__":
    unittest.main()
