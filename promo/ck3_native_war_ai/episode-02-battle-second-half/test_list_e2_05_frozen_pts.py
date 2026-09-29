"""In-memory checks for strict E2-05 frozen probe frame indexing."""

from __future__ import annotations

import unittest

from list_e2_05_frozen_pts import strict_video_pts


def summary() -> dict:
    return {"frame_count_with_pts": 3, "first_pts_seconds": "0.000000",
            "last_pts_seconds": "0.067000", "missing_pts_count": 0,
            "nonmonotonic_count": 0, "gap_count": 0}


def probe() -> dict:
    return {"frames": [
        {"media_type": "video", "best_effort_timestamp_time": "0.000000"},
        {"media_type": "video", "best_effort_timestamp_time": "0.033000"},
        {"media_type": "video", "best_effort_timestamp_time": "0.067000"},
    ]}


class FrozenPtsTests(unittest.TestCase):
    def test_video_frame_indices_are_complete_and_ordered(self) -> None:
        data = probe()
        data["frames"].insert(1, {"media_type": "audio"})
        values, strings = strict_video_pts(data, summary())
        self.assertEqual(len(values), 3)
        self.assertEqual(strings, ["0.000000", "0.033000", "0.067000"])

    def test_missing_or_nonfinite_pts_is_red(self) -> None:
        for invalid in (None, "", "NaN", "Infinity", "-Infinity"):
            data = probe()
            if invalid is None:
                del data["frames"][1]["best_effort_timestamp_time"]
            else:
                data["frames"][1]["best_effort_timestamp_time"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                strict_video_pts(data, summary())

    def test_bad_summary_or_frame_sequence_is_red(self) -> None:
        for key, bad in (("missing_pts_count", 1), ("nonmonotonic_count", 1),
                         ("gap_count", 1), ("frame_count_with_pts", 2),
                         ("first_pts_seconds", "0.001000"),
                         ("last_pts_seconds", "0.066000")):
            frozen = summary()
            frozen[key] = bad
            with self.subTest(key=key), self.assertRaises(ValueError):
                strict_video_pts(probe(), frozen)
        for frames in ([], [{"media_type": "video"}],
                       [{"media_type": "video", "best_effort_timestamp_time": "0.000000"},
                        {"media_type": "video", "best_effort_timestamp_time": "0.000000"}],
                       [{"media_type": "video", "best_effort_timestamp_time": "0.000000"},
                        {"media_type": "video", "best_effort_timestamp_time": "0.300000"}]):
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                strict_video_pts({"frames": frames}, summary())


if __name__ == "__main__":
    unittest.main()
