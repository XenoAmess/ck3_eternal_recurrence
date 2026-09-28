"""Small-file fixture gates for the E2-05 postrun link audit."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit_e2_05_postrun_links as audit


def put(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class PostrunLinksTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.attempt = self.root / "a02-live"
        self.recorder = self.attempt / "recording-e2-05-d26-a01"
        self.session = self.attempt / "ck3-output"
        self.session.mkdir(parents=True)
        raw = self.recorder / "raw/e2-05-d26.mkv"
        raw.parent.mkdir(parents=True)
        raw.write_bytes(b"fixture-video")
        probe = self.recorder / "ffprobe.json"
        put(probe, {"frames": []})
        put(self.recorder / "recorder-intent.json", {
            "workdir": str(self.recorder), "session_output": str(self.session),
            "raw_path": str(raw)})
        put(self.recorder / "recorder-start.json", {"monotonic_ns": 100, "pid": 42})
        put(self.recorder / "recorder-end.json", {
            "monotonic_ns": 300, "ffmpeg_exit_code": 0,
            "interrupted": False, "raw": audit.identity(raw)})
        screenshot = self.recorder / "screens/d26.png"
        screenshot.parent.mkdir()
        screenshot.write_bytes(b"fixture screenshot")
        marks = self.recorder / "marks.jsonl"
        marks.write_text("".join(json.dumps(row) + "\n" for row in (
            {"kind": "recorder-start", "monotonic_ns": 100},
            {"kind": "d26-before", "monotonic_ns": 200,
             "date_raw": 53146848, "war_id": 4, "combat_id": 16777218,
             "approx_seconds_from_recorder_start": 100.0,
             "approx_seconds_are_not_video_pts": True,
             "screenshot": audit.identity(screenshot)},
            {"kind": "recorder-end", "monotonic_ns": 300})), encoding="utf-8")
        put(self.recorder / "recorder-final.json", {
            "result": "ENCODED_UNREVIEWED", "ffmpeg_exit_code": 0,
            "ffprobe_exit_code": 0, "clean_spans_certified": False,
            "human_review_completed": False, "raw": audit.identity(raw),
            "ffprobe_output": audit.identity(probe), "marks": audit.identity(marks)})
        put(self.session / "session-result.json", {"ok": True, "shutdown": {
            "ok": True, "tree_gone": True, "cleanup_proven": True,
            "final_ck3_inventory": {"processes": []}}})
        put(self.session / "capture-report.json", {
            "result": "ENVIRONMENT_SESSION_COMPLETE_NO_VIDEO",
            "environment_session_complete": True, "worker": {"ok": True},
            "cleanup_process_inventory": {"processes": []}})
        self.pts = self.root / "pts-audit.json"
        put(self.pts, {"schema": "xar.war-promo.raw-video-pts-audit/v1",
                       "result": "PTS_CONTINUOUS_UNREVIEWED",
                       "human_visual_review_completed": False,
                       "clean_spans_certified": False,
                       "recorder_intent": audit.identity(self.recorder / "recorder-intent.json"),
                       "recorder_final": audit.identity(self.recorder / "recorder-final.json"),
                       "raw": audit.identity(raw), "full_ffprobe": audit.identity(probe),
                       "frame_count_with_pts": 100,
                       "first_pts_seconds": "0.000", "last_pts_seconds": "599.967",
                       "gap_count": 0})
        self.raw = raw

    def test_valid_links_remain_candidate_without_rehashing_raw(self) -> None:
        original = audit.identity
        def guarded(path: Path):
            if Path(path).resolve() == self.raw:
                raise AssertionError("raw must not be rehashed by link audit")
            return original(path)
        with patch.object(audit, "identity", side_effect=guarded):
            result = audit.link(self.recorder, self.session, self.pts)
        self.assertEqual(result["result"], "MEDIA_PTS_CANDIDATE_UNREVIEWED")
        self.assertEqual(result["marks"][0]["date_raw"], 53146848)
        self.assertFalse(result["clean_spans_certified"])

    def test_missing_shutdown_ok_rejects(self) -> None:
        path = self.session / "session-result.json"
        value = audit.read_object(path)
        value["shutdown"]["ok"] = False
        put(path, value)
        with self.assertRaisesRegex(ValueError, "cleanup is not proven"):
            audit.link(self.recorder, self.session, self.pts)

    def test_mark_evidence_tampering_rejects(self) -> None:
        screen = self.recorder / "screens/d26.png"
        screen.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "small evidence byte/SHA differs"):
            audit.link(self.recorder, self.session, self.pts)


if __name__ == "__main__":
    unittest.main()
