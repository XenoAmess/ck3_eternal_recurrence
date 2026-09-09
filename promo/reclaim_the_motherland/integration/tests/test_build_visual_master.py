from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROMO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROMO))

from build_visual_master import (  # noqa: E402
    EXPECTED_CHAPTERS,
    _video_filter,
    resolve_capture_start,
    validate_shot_manifest,
)


class BuildVisualMasterTests(unittest.TestCase):
    def test_resolves_capture_anchor_with_lead(self) -> None:
        timeline = {
            "events": [
                {
                    "path": "acceptance/cell/08_song_capital_map.png",
                    "seconds_from_capture_start": 101.25,
                }
            ]
        }
        self.assertEqual(
            resolve_capture_start(timeline, "08_song_capital_map.png", 4.25), 97.0
        )

    def test_manifest_requires_exact_approved_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.png"
            source.write_bytes(b"fixture")
            shots = [
                {
                    "id": chapter_id,
                    "duration_seconds": duration,
                    "source_kind": "still",
                    "source": str(source),
                }
                for chapter_id, duration in EXPECTED_CHAPTERS
            ]
            validated = validate_shot_manifest(
                {"kind": "rmtm-visual-shot-manifest", "shots": shots}
            )
        self.assertEqual([shot["id"] for shot in validated], [row[0] for row in EXPECTED_CHAPTERS])

    def test_capture_shot_needs_timeline_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source.mkv"
            source.write_bytes(b"fixture")
            shots = [
                {
                    "id": chapter_id,
                    "duration_seconds": duration,
                    "source_kind": "still",
                    "source": str(source),
                }
                for chapter_id, duration in EXPECTED_CHAPTERS
            ]
            shots[1]["source_kind"] = "capture"
            with self.assertRaisesRegex(ValueError, "anchor_event_suffix"):
                validate_shot_manifest(
                    {"kind": "rmtm-visual-shot-manifest", "shots": shots}
                )

    def test_left_gameplay_crop_excludes_acceptance_panel(self) -> None:
        self.assertEqual(
            _video_filter("left_gameplay"),
            "crop=1920:1080:0:180,fps=30,format=yuv420p",
        )
        with self.assertRaisesRegex(ValueError, "crop mode"):
            _video_filter("invented")


if __name__ == "__main__":
    unittest.main()
