#!/usr/bin/env python3
"""Offline determinism and media-contract tests for chapter-gate SFX."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
import wave
from pathlib import Path

import generate_project_causality_chapter_sfx as sfx


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProjectCausalityChapterSfxTests(unittest.TestCase):
    def test_generation_is_deterministic_and_matches_audio_contract(self) -> None:
        with tempfile.TemporaryDirectory() as first_raw, tempfile.TemporaryDirectory() as second_raw:
            first = Path(first_raw)
            second = Path(second_raw)
            first_paths = sfx.generate(first)
            second_paths = sfx.generate(second)

            self.assertEqual(sorted(sfx.GENERATORS), sorted(path.name for path in first_paths))
            self.assertEqual(
                {_path.name: _sha256(_path) for _path in first_paths},
                {_path.name: _sha256(_path) for _path in second_paths},
            )
            for path in first_paths:
                with wave.open(str(path), "rb") as audio:
                    self.assertEqual(1, audio.getnchannels())
                    self.assertEqual(2, audio.getsampwidth())
                    self.assertEqual(sfx.SAMPLE_RATE, audio.getframerate())
                    self.assertEqual(sfx.SAMPLE_COUNT, audio.getnframes())


if __name__ == "__main__":
    unittest.main()
