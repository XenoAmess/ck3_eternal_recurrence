"""Small PTS selection tests; no CK3, FFmpeg, or raw video needed."""

from decimal import Decimal
import unittest

from plan_four_raw_pts_candidates import select_window


class CandidateWindowTests(unittest.TestCase):
    def test_requested_boundaries_are_not_assumed_to_be_frames(self) -> None:
        pts = [Decimal("269.900000"), Decimal("269.933000"),
               Decimal("269.967000"), Decimal("270.033000")]
        selected = select_window(pts, Decimal("269.9"), Decimal("270"))
        self.assertEqual(selected["exact_end_pts_seconds"], "269.967000")
        self.assertFalse(selected["requested_end_is_frame_pts"])
        self.assertEqual(selected["machine_status"], "PTS_CANDIDATE_UNREVIEWED")

    def test_known_gap_is_rejected_but_either_side_is_available_for_review(self) -> None:
        pts = [Decimal("250.000000"), Decimal("271.267000"),
               Decimal("278.833000"), Decimal("300.000000")]
        crossing = select_window(pts, Decimal("250"), Decimal("300"))
        self.assertEqual(crossing["machine_status"], "GAP_REJECTED")
        self.assertIn({"before_pts_seconds": "271.267000",
                       "after_pts_seconds": "278.833000",
                       "gap_seconds": "7.566000"},
                      crossing["gaps_over_0_2_seconds"])
        left = select_window([Decimal("271.200000"), Decimal("271.267000")],
                             Decimal("271.2"), Decimal("271.3"))
        right = select_window([Decimal("278.833000"), Decimal("278.900000")],
                              Decimal("278.8"), Decimal("279"))
        self.assertEqual(left["machine_status"], "PTS_CANDIDATE_UNREVIEWED")
        self.assertEqual(right["machine_status"], "PTS_CANDIDATE_UNREVIEWED")


if __name__ == "__main__":
    unittest.main()
