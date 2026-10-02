"""The Episode 2 span gate must reject a gap without rejecting later footage."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from war_ai_promo.episode_two_pts_contract import validate_pts_span  # noqa: E402
from war_ai_promo.episode_two_subtitle_contract import identity  # noqa: E402


class EpisodeTwoPtsContractTests(unittest.TestCase):
    def test_separate_clean_intervals_can_pass_around_large_gap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "raw.mkv"
            raw.write_bytes(b"SOURCE VIDEO TEST BYTES")
            probe = root / "ffprobe.json"
            stamps = ("0.000", "0.033", "0.066", "0.100", "0.133",
                      "1.000", "1.033", "1.066", "1.100")
            probe.write_text(json.dumps({
                "streams": [{"codec_type": "video", "index": 0}],
                "frames": [{"stream_index": 0, "best_effort_timestamp_time": stamp}
                           for stamp in stamps],
            }), encoding="utf-8")
            recorder = root / "recorder-final.json"
            recorder.write_text(json.dumps({"schema": "xar.war-promo.bounded-recorder-final/v1",
                                            "result": "ENCODED_UNREVIEWED",
                                            "ffmpeg_exit_code": 0, "ffprobe_exit_code": 0,
                                            "video_pts_complete": True,
                                            "frame_pts_by_stream": {"0": {
                                                "count": len(stamps),
                                                "first_pts_time": stamps[0],
                                                "last_pts_time": stamps[-1]}},
                                            "raw": identity(raw),
                                            "ffprobe_output": identity(probe)}), encoding="utf-8")
            verified = identity(raw)
            for begin, end in ((0.0, .133), (1.0, 1.1)):
                outcome = validate_pts_span(raw, probe, recorder, begin, end,
                                            verified_raw_identity=verified)
                self.assertEqual(outcome["result"], "PTS_CONTINUOUS_SPAN_UNREVIEWED")
                self.assertEqual(outcome["frame_count"], 5 if begin == 0 else 4)
            with self.assertRaisesRegex(ValueError, "crosses a missing"):
                validate_pts_span(raw, probe, recorder, .1, 1.066,
                                  verified_raw_identity=verified)
            with self.assertRaisesRegex(ValueError, "boundary lies in"):
                validate_pts_span(raw, probe, recorder, .5, 1.1,
                                  verified_raw_identity=verified)
            raw.write_bytes(b"CHANGED SOURCE VIDEO")
            with self.assertRaisesRegex(ValueError, "raw identity"):
                validate_pts_span(raw, probe, recorder, 1.0, 1.1,
                                  verified_raw_identity=verified)


if __name__ == "__main__":
    unittest.main()
