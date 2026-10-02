"""Real Episode 2 reels must carry source-bound clean and label evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import war_ai_promo  # noqa: E402

# Other integration tests may have imported an editable install first.
war_ai_promo.__path__.insert(0, str(Path(__file__).resolve().parent / "src" / "war_ai_promo"))
from war_ai_promo.episode_two_second_half import _artifact, _capture_audit_contract  # noqa: E402
from war_ai_promo.assemble_episode_two import _stream_coverage  # noqa: E402


class EpisodeTwoCaptureAuditTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.frame = Path(self.directory.name) / "label.png"
        self.frame.write_bytes(b"specific preserved source label frame")
        self.frame_sha = hashlib.sha256(self.frame.read_bytes()).hexdigest().upper()
        self.raw_sha = "A" * 64
        self.reel_sha = "B" * 64
        self.span = {"attempt_id": "episode02-real-001", "raw_video_sha256": self.raw_sha,
                     "raw_video_bytes": 1234}
        self.clean = {
            "schema": "ck3-war-ai.episode02.clean-span-audit.v1", "result": "GREEN",
            "attempt_id": self.span["attempt_id"], "span_id": "battle-clean",
            "raw_video_sha256": self.raw_sha, "raw_video_bytes": 1234,
            "report_sha256": "C" * 64, "timeline_sha256": "D" * 64,
            "evidence_index_sha256": "E" * 64,
            "begin_seconds": 10.0, "end_seconds": 20.0,
        }
        self.label = {
            "schema": "ck3-war-ai.episode02.source-label-audit.v1", "status": "visible",
            "attempt_id": self.span["attempt_id"], "raw_video_sha256": self.raw_sha,
            "reel_sha256": self.reel_sha,
            "label_text": "本段来自 episode02-real-001", "frame_at_seconds": 5.0,
            "frame_sha256": self.frame_sha, "frame_bytes": self.frame.stat().st_size,
        }
        self.bundle = SimpleNamespace(
            report=SimpleNamespace(sha256="C" * 64),
            timeline=SimpleNamespace(sha256="D" * 64),
            evidence_index=SimpleNamespace(sha256="E" * 64),
            raw_capture=SimpleNamespace(sha256=self.raw_sha, bytes=1234),
            clean_span=lambda _: SimpleNamespace(begin_seconds=10.0, end_seconds=20.0),
        )

    def test_real_receipts_bind_verified_bundle_and_visible_frame(self):
        _capture_audit_contract(self.clean, self.label, self.span, self.reel_sha, 30.0,
                                self.bundle, self.frame)

    def test_placeholder_and_stale_receipts_are_rejected(self):
        for changed, field, value in (("clean", "schema", "synthetic.clean-span.v1"),
                                      ("clean", "result", "RED"),
                                      ("clean", "raw_video_sha256", "F" * 64),
                                      ("clean", "timeline_sha256", "F" * 64),
                                      ("clean", "end_seconds", 19.0),
                                      ("label", "attempt_id", "older-attempt"),
                                      ("label", "reel_sha256", "F" * 64),
                                      ("label", "frame_at_seconds", 31.0),
                                      ("label", "frame_sha256", "F" * 64)):
            with self.subTest(changed=changed, field=field):
                clean, label = self.clean.copy(), self.label.copy()
                (clean if changed == "clean" else label)[field] = value
                with self.assertRaises(ValueError):
                    _capture_audit_contract(clean, label, self.span, self.reel_sha, 30.0,
                                            self.bundle, self.frame)

    def test_preserved_artifact_cannot_escape_native_run(self):
        root = Path(self.directory.name)
        run = root / "native-run"
        run.mkdir()
        outside = root / "outside.txt"
        outside.write_bytes(b"outside")
        row = SimpleNamespace(artifact_id="outside", path="../outside.txt", bytes=7,
                              sha256=hashlib.sha256(b"outside").hexdigest().upper())
        with self.assertRaisesRegex(ValueError, "escapes native run"):
            _artifact(SimpleNamespace(artifacts=[row]), run / "run-manifest.json", "outside")

    def test_full_length_music_bed_cannot_hide_short_narration_stream(self):
        probe = {"streams": [{"codec_type": "video", "duration": "60.000"},
                             {"codec_type": "audio", "duration": "42.000"}],
                 "format": {"duration": "60.000"}}
        with self.assertRaisesRegex(ValueError, "audio stream does not cover"):
            _stream_coverage(probe, 60000, "unmixed narration film")
        probe["streams"][1]["duration"] = "59.990"
        _stream_coverage(probe, 60000, "unmixed narration film")


if __name__ == "__main__":
    unittest.main()
