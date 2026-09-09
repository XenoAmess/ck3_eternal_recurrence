from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

import sys
from PIL import Image

PROMO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROMO))

from record_acceptance_run import (  # noqa: E402
    acceptance_argv,
    assess_visual_samples,
    ffmpeg_argv,
    sample_argv,
)


class RecordAcceptanceRunTests(unittest.TestCase):
    def test_ffmpeg_records_desktop_without_pointer(self) -> None:
        argv = ffmpeg_argv(Path("ffmpeg.exe"), Path("raw.mkv"))
        self.assertEqual(argv[argv.index("-draw_mouse") + 1], "0")
        self.assertIn("desktop", argv)
        self.assertFalse(any(value.startswith("title=") for value in argv))
        self.assertEqual(argv[-1], "raw.mkv")

    def test_sample_command_retains_validation_evidence(self) -> None:
        argv = sample_argv(Path("ffmpeg.exe"), Path("raw.mkv"), Path("samples"))
        self.assertIn("fps=1/120,scale=320:-2", argv)
        self.assertEqual(argv[-1], str(Path("samples") / "sample-%02d.png"))

    def test_visual_validation_rejects_black_stream(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            paths = [root / "one.png", root / "two.png"]
            for path in paths:
                Image.new("RGB", (32, 18), "black").save(path)
            report = assess_visual_samples(paths)
        self.assertEqual(report["result"], "RED")
        self.assertEqual(report["non_black_sample_count"], 0)

    def test_visual_validation_accepts_distinct_non_black_frames(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "one.png"
            second = root / "two.png"
            first_image = Image.new("RGB", (32, 18), "#293348")
            second_image = Image.new("RGB", (32, 18), "#5c3920")
            for x in range(0, 32, 2):
                for y in range(0, 18, 2):
                    first_image.putpixel((x, y), (210, 180, 90))
                    second_image.putpixel((x, y), (40, 170, 210))
            first_image.save(first)
            second_image.save(second)
            report = assess_visual_samples([first, second])
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["distinct_non_black_sample_count"], 2)

    def test_acceptance_runner_keeps_isolated_userdir(self) -> None:
        args = argparse.Namespace(
            python=Path("python.exe"),
            acceptance_runner=Path("runner.py"),
            source=Path("cache"),
            manifest=Path("manifest.json"),
            bridge_dll=Path("bridge.dll"),
            bridge_injector=Path("injector.exe"),
            bridge_pipe=None,
        )
        argv = acceptance_argv(args, Path("cell"))
        self.assertIn("--keep-userdir", argv)
        self.assertEqual(argv[argv.index("--artifacts-dir") + 1], "cell")


if __name__ == "__main__":
    unittest.main()
