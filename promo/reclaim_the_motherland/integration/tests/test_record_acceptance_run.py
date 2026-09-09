from __future__ import annotations

import argparse
import unittest
from pathlib import Path

import sys

PROMO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROMO))

from record_acceptance_run import acceptance_argv, ffmpeg_argv  # noqa: E402


class RecordAcceptanceRunTests(unittest.TestCase):
    def test_ffmpeg_records_only_ck3_window_without_pointer(self) -> None:
        argv = ffmpeg_argv(Path("ffmpeg.exe"), "Crusader Kings III", Path("raw.mkv"))
        self.assertIn("title=Crusader Kings III", argv)
        self.assertEqual(argv[argv.index("-draw_mouse") + 1], "0")
        self.assertNotIn("desktop", argv)
        self.assertEqual(argv[-1], "raw.mkv")

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
