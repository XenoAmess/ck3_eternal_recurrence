"""Safety checks for the sparse E2-05 review sampler; no CK3 or real raw I/O."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import sample_e2_05_raw_visual_index as sampler


def make_tiny_fixture(root: Path) -> tuple[Path, Path, list[str]]:
    recording = root / "live" / "recording"
    raw_dir = recording / "raw"
    raw_dir.mkdir(parents=True)
    audit = root / "audit"
    audit.mkdir()
    raw = raw_dir / "source.mkv"
    raw.write_bytes(b"tiny-test-fixture")
    probe = recording / "ffprobe.json"
    probe.write_text(json.dumps({"frames": [
        {"media_type": "video", "best_effort_timestamp_time": "0.000000"},
        {"media_type": "video", "best_effort_timestamp_time": "0.033000"},
    ]}), encoding="utf-8")
    row = lambda p: {"path": str(p), "bytes": p.stat().st_size,
                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest().upper()}
    stat = lambda p: {"bytes": p.stat().st_size, "mtime_ns": p.stat().st_mtime_ns}
    links = audit / "postrun-links.json"
    links.write_text(json.dumps({
        "result": "MEDIA_PTS_CANDIDATE_UNREVIEWED",
        "raw_from_prior_full_sha_audit": row(raw),
        "raw_stat_during_link_audit": stat(raw),
        "ffprobe_from_prior_full_sha_audit": row(probe),
        "ffprobe_stat_during_link_audit": stat(probe),
        "video_pts_summary": {"missing_pts_count": 0, "nonmonotonic_count": 0,
                              "gap_count": 0},
    }), encoding="utf-8")
    output = root / "episode02-e2-05-a02-visual-index-20260929-a01"
    argv = ["sampler", "--postrun-links", str(links), "--postrun-links-sha256",
            hashlib.sha256(links.read_bytes()).hexdigest(), "--raw", str(raw),
            "--ffprobe-json", str(probe), "--output", str(output), "--seek", "0"]
    return raw, output, argv


@contextmanager
def patched_fixture_identity(argv: list[str]):
    links_path = Path(argv[2])
    links = json.loads(links_path.read_text(encoding="utf-8"))
    with patch.object(sampler, "EXPECTED_LINK_SHA256", argv[4].upper()), \
            patch.object(sampler, "EXPECTED_RAW_SHA256",
                         links["raw_from_prior_full_sha_audit"]["sha256"]), \
            patch.object(sampler, "EXPECTED_FFPROBE_SHA256",
                         links["ffprobe_from_prior_full_sha_audit"]["sha256"]):
        yield


class SparseSamplerSafetyTests(unittest.TestCase):
    def test_fractional_seek_uses_exact_argv_and_unique_receipt_name(self) -> None:
        self.assertEqual(sampler.seek_text(Decimal("210.033000")), "210.033")
        self.assertEqual(sampler.seek_label(Decimal("210.033000")), "210p033")
        self.assertEqual(sampler.seek_label(Decimal("0")), "000")
        self.assertEqual(sampler.seek_label(Decimal("-0")), "000")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, output, argv = make_tiny_fixture(root)
            argv[-1] = "210.033000"

            def failed_ffmpeg(command, *, stdout, stderr, check):
                self.assertEqual(command[command.index("-ss") + 1], "210.033")
                self.assertEqual(Path(command[-1]).name, "seek-210p033.png")
                Path(command[-1]).write_bytes(b"partial")
                return SimpleNamespace(returncode=7)

            with patched_fixture_identity(argv), patch.object(sampler, "EXTERNAL_PARENT", root), \
                    patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sampler.subprocess, "run", side_effect=failed_ffmpeg), \
                    patch.object(sys, "argv", argv), self.assertRaises(RuntimeError):
                sampler.main()
            receipt = json.loads((output / "seek-210p033.exit.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt["requested_seek_seconds"], "210.033")
            self.assertEqual(receipt["png_or_partial"]["bytes"], 7)

    def test_unbounded_or_colliding_seek_rejected_before_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, output, argv = make_tiny_fixture(root)
            for invalid in ("NaN", "Infinity", "1e-300", "210.1234567"):
                argv[-1] = invalid
                with self.subTest(invalid=invalid), \
                        patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                        patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
                    sampler.main()
                self.assertFalse(output.exists())
            argv[-1] = "210.123456789012345678901234567890"
            argv.extend(["--seek", "210.123456789012345678901234567891"])
            with patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
                sampler.main()
            self.assertFalse(output.exists())
            argv[-3:] = ["0", "--seek", "-0"]
            with patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
                sampler.main()
            self.assertFalse(output.exists())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg tools are unavailable")
    def test_real_ffmpeg_select_logs_only_written_first_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "three-frames.mkv"
            still = root / "first-frame.png"
            subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i", "testsrc=size=32x32:rate=10:duration=0.3",
                            "-frames:v", "3", "-c:v", "ffv1", str(source)],
                           check=True, capture_output=True)
            command = [shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "info",
                       "-nostdin", "-n", "-threads", "1", "-filter_threads", "1",
                       "-ss", "0", "-copyts", "-i", str(source), "-map", "0:v:0",
                       "-an", "-vf", r"select=eq(n\,0),showinfo", "-frames:v", "1",
                       "-compression_level", "1", str(still)]
            completed = subprocess.run(command, check=True, capture_output=True)
            self.assertEqual(sampler.unique_showinfo_pts(completed.stderr), 0)
            self.assertEqual(sampler.png_dimensions(still), (32, 32))
            probe = subprocess.run([shutil.which("ffprobe"), "-v", "error",
                                    "-select_streams", "v:0", "-show_frames",
                                    "-show_entries", "frame=best_effort_timestamp_time",
                                    "-of", "json", str(source)],
                                   check=True, capture_output=True)
            source_first_pts = json.loads(probe.stdout)["frames"][0]["best_effort_timestamp_time"]
            self.assertEqual(source_first_pts, "0.000000")

    def test_self_consistent_other_run_is_rejected_by_frozen_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, output, argv = make_tiny_fixture(root)
            with patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sys, "argv", argv), self.assertRaises(ValueError):
                sampler.main()
            self.assertFalse(output.exists())

    def test_output_must_be_new_flat_external_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "live"
            source.mkdir()
            good = root / "episode02-e2-05-a02-visual-index-20260929-a01"
            sampler.validate_output_directory(good, root, [source])
            for bad in (
                Path("relative/episode02-e2-05-a02-visual-index-20260929-a01"),
                source / good.name,
                root / "audit",
            ):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    sampler.validate_output_directory(bad, root, [source])
            good.mkdir()
            with self.assertRaises(ValueError):
                sampler.validate_output_directory(good, root, [source])

    def test_showinfo_requires_unique_n_zero_frame(self) -> None:
        frame = b"[Parsed_showinfo_0 @ 0] n:   0 pts: 33 pts_time:0.033\n"
        self.assertEqual(str(sampler.unique_showinfo_pts(frame)), "0.033")
        for bad in (b"no video frame\n", frame + frame,
                    b"[Parsed_showinfo_0 @ 0] n:   1 pts: 33 pts_time:0.033\n"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                sampler.unique_showinfo_pts(bad)

    def test_failed_seek_keeps_argv_streams_exit_and_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, output, argv = make_tiny_fixture(root)

            def failed_ffmpeg(command, *, stdout, stderr, check):
                self.assertEqual(command[command.index("-vf") + 1],
                                 r"select=eq(n\,0),showinfo")
                stdout.write(b"stdout-partial\x00")
                stderr.write(b"stderr-failure\x00")
                Path(command[-1]).write_bytes(b"PNG-partial")
                return SimpleNamespace(returncode=13)

            with patched_fixture_identity(argv), patch.object(sampler, "EXTERNAL_PARENT", root), \
                    patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sampler.subprocess, "run", side_effect=failed_ffmpeg), \
                    patch.object(sys, "argv", argv), self.assertRaises(RuntimeError):
                sampler.main()
            self.assertTrue((output / "seek-000.intent.json").is_file())
            self.assertEqual((output / "seek-000.ffmpeg.stdout.bin").read_bytes(),
                             b"stdout-partial\x00")
            self.assertEqual((output / "seek-000.ffmpeg.stderr.bin").read_bytes(),
                             b"stderr-failure\x00")
            self.assertEqual((output / "seek-000.png").read_bytes(), b"PNG-partial")
            exit_record = json.loads((output / "seek-000.exit.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_record["result"], "RED_PARTIAL_PRESERVED")
            self.assertEqual(exit_record["ffmpeg_exit_code"], 13)
            self.assertFalse((output / "sample-index.json").exists())

    def test_source_drift_during_seek_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw, output, argv = make_tiny_fixture(root)

            def drifting_ffmpeg(command, *, stdout, stderr, check):
                stdout.write(b"stdout-before-drift")
                stderr.write(b"stderr-before-drift")
                Path(command[-1]).write_bytes(b"PNG-partial")
                raw.write_bytes(b"changed-after-launch")
                return SimpleNamespace(returncode=0)

            with patched_fixture_identity(argv), patch.object(sampler, "EXTERNAL_PARENT", root), \
                    patch.object(sampler.shutil, "which", return_value="ffmpeg-fake"), \
                    patch.object(sampler.subprocess, "run", side_effect=drifting_ffmpeg), \
                    patch.object(sys, "argv", argv), self.assertRaises(RuntimeError):
                sampler.main()
            exit_record = json.loads((output / "seek-000.exit.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_record["result"], "RED_PARTIAL_PRESERVED")
            self.assertTrue(any("source_after" in error for error in exit_record["errors"]))
            self.assertEqual((output / "seek-000.ffmpeg.stderr.bin").read_bytes(),
                             b"stderr-before-drift")
            self.assertEqual((output / "seek-000.png").read_bytes(), b"PNG-partial")
            self.assertFalse((output / "sample-index.json").exists())


if __name__ == "__main__":
    unittest.main()
