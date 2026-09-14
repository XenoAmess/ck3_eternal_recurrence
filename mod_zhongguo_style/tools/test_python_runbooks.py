from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest import mock

import run_phase2_cut_pipeline
import run_phase2_validate_only_preflight


class PythonRunbookTests(unittest.TestCase):
    def test_cut_parser_preserves_explicit_paths(self) -> None:
        args = run_phase2_cut_pipeline.parser().parse_args([
            "--repository", "repo", "--python", "python.exe", "build",
            "--cut", "character-led", "--toolchain", "toolchain",
            "--capture", "capture", "--seed-preflight", "seed.json",
            "--tts-cache", "cache", "--work-dir", "work",
            "--source-review-receipt", "review.json",
        ])
        self.assertEqual(args.cut, "character-led")
        self.assertEqual(args.handler, run_phase2_cut_pipeline.build)
        self.assertEqual(args.ffmpeg, "ffmpeg")

    def test_toolchain_verifier_rejects_dirty_checkout(self) -> None:
        with mock.patch.object(run_phase2_cut_pipeline.subprocess, "run") as run:
            run.return_value.returncode = 0
            with mock.patch.object(
                run_phase2_cut_pipeline,
                "output",
                side_effect=["dirty.txt", "head", "head"],
            ):
                with self.assertRaisesRegex(RuntimeError, "dirty"):
                    run_phase2_cut_pipeline.verify_toolchain(Path("toolchain"))

    def test_sha_helpers_return_uppercase_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "fixture.bin"
            fixture.write_bytes(b"abc")
            expected = "BA7816BF8F01CFEA414140DE5DAE2223B00361A396177A9CB410FF61F20015AD"
            self.assertEqual(run_phase2_cut_pipeline.file_sha256(fixture), expected)
            self.assertEqual(run_phase2_validate_only_preflight.sha256(fixture), expected)


if __name__ == "__main__":
    unittest.main()
