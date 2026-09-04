#!/usr/bin/env python3
"""Fail-closed tests for the B3 explicit-AND live postprocessor."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parent))

import postprocess_zg361_b3_exact_and_wrapper_live as postprocess


class ExplicitAndLivePostprocessorTests(unittest.TestCase):
    def test_missing_evidence_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(postprocess.LiveVerdictError):
                postprocess.build_verdict(Path(directory))

    def test_hash_mismatch_fails_closed_before_interpretation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts-live" / "cell"
            artifacts.mkdir(parents=True)
            files = {
                "attempt_manifest": root / "attempt-manifest.json",
                "projection_manifest": root / "projection.json",
                "outer_report": root / "artifacts-live" / "report.json",
                "evidence_index": root / "artifacts-live" / "evidence-index.json",
                "cell_report": artifacts / "report.json",
                "final_error": artifacts / "final_error.log",
                "final_debug": artifacts / "final_debug.log",
                "loader_gate": artifacts / "03_loader_gate.json",
                "loader_progress": artifacts / "01_phase2_loader_stage_progress.jsonl",
            }
            for path in files.values():
                path.write_text("{}\n", encoding="utf-8")
            wrong_hashes = {name: "0" * 64 for name in files}
            with self.assertRaisesRegex(
                postprocess.LiveVerdictError, "identity mismatch"
            ):
                postprocess.build_verdict(root, expected_sha256=wrong_hashes)


if __name__ == "__main__":
    unittest.main()
