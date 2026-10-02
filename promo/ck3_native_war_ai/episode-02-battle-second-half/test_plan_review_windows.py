"""Small FFprobe fixture for pending review navigation, with no video decoder."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import plan_review_windows as review


class ReviewWindowPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        raw = root / "raw.mkv"
        raw.write_bytes(b"raw remains unopened by review planner")
        probe = root / "ffprobe.json"
        probe.write_text(json.dumps({"streams": [{"index": 0, "codec_type": "video"}],
                                     "frames": [{"stream_index": 0,
                                                 "best_effort_timestamp_time": value}
                                                for value in ("0.000", "0.033", "0.067",
                                                              "0.100", "0.500", "0.533")]}),
                         encoding="utf-8")
        self.manifest = root / "source-manifest.json"
        self.manifest.write_text(json.dumps({"status": "PENDING_CLEAN_REVIEW",
                                             "adapter_eligible": False,
                                             "human_1x_review_performed": False,
                                             "clean_spans": [],
                                             "raw": review.identity(raw),
                                             "ffprobe": review.identity(probe)}),
                                 encoding="utf-8")
        self.sha = review.identity(self.manifest)["sha256"]

    def test_selects_real_endpoints_and_rejects_cross_gap(self) -> None:
        result = review.plan(self.manifest, self.sha,
                             [("before", "0.020", "0.100"),
                              ("cross-gap", "0.067", "0.533")])
        first, second = result["windows"]
        self.assertEqual((first["exact_begin_pts_seconds"], first["exact_end_pts_seconds"]),
                         ("0.033", "0.100"))
        self.assertEqual(first["machine_status"], "PTS_CANDIDATE_UNREVIEWED")
        self.assertEqual(second["machine_status"], "GAP_REJECTED")
        self.assertEqual(second["gaps_over_0_2_seconds"][0]["gap_seconds"], "0.400")
        self.assertFalse(result["raw_sha256_rehashed_this_run"])
        self.assertFalse(result["clean_spans_certified"])

    def test_rejects_manifest_sha_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "manifest SHA-256 differs"):
            review.plan(self.manifest, "0" * 64, [("before", "0", "0.100")])


if __name__ == "__main__":
    unittest.main()
