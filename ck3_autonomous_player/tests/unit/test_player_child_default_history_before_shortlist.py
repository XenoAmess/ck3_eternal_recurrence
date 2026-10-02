"""Actual compact slots regression; unobserved fresh full-value terms remain absent."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from xar_autoplayer.guy_default_marriage_policy import (
    choose_specified_child_default_value,
    shortlist_specified_child_default_candidates,
)


FIXTURE = (Path(__file__).resolve().parents[1] / "fixtures"
           / "robert_guy_b594_compact_history_slots.json")


class PlayerChildDefaultBoundedSlotsTest(unittest.TestCase):
    def test_history_exclusion_precedes_bounded_value_slots(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8-sig"))
        native = fixture["subject_result"]
        legal_rows = [row for row in native["family_candidates"]
                      if row["recipient_answer_status_raw"] != 2]
        legality = {**native, "schema": "xar.ck3.player-child-marriage-subject.v1",
                    "played_character_id": legal_rows[0]["played_character_id"],
                    "native_legal_candidates": legal_rows}
        excluded = frozenset(fixture["existing_exclusions"])
        values = [{"schema": "xar.ck3.player-child-marriage-value.v1", "read_only": True,
                   "advertised": False, "native_revision": item["native_revision"],
                   "legality_query_sequence": item["legality_query_sequence"],
                   "played_character_id": item["rows"][0]["actor_character_id"],
                   "subject_character_id": item["rows"][0]["heir_character_id"],
                   "candidate_character_id": item["rows"][0]["candidate_character_id"],
                   "request_matrilineal_option": False, "status": item["status"], "row": item["rows"][0]}
                  for item in fixture["observed_full_value_results"]]
        self.assertEqual(len(native["family_candidates"]), 189)
        self.assertEqual(shortlist_specified_child_default_candidates(legality, limit=2),
                         [37909, 37571])
        shortlist = shortlist_specified_child_default_candidates(
            legality, limit=2, excluded_candidate_ids=excluded)
        self.assertEqual(shortlist, fixture["expected_fresh_shortlist"])
        self.assertEqual(shortlist, [37689, 37513])
        self.assertTrue(excluded.isdisjoint(shortlist))
        decision = choose_specified_child_default_value(
            legality, values, split_successor_verified=True, rejected_candidate_ids=excluded)
        self.assertIsNone(decision["selected_candidate_character_id"])
        self.assertEqual(decision["reason"], "incomplete_top_two_full_value_comparison")


if __name__ == "__main__":
    unittest.main()
