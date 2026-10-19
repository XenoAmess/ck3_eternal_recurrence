import unittest

from xar_autoplayer.campaign_score_cadence_v1 import (
    date_to_raw, month_boundaries, ordinary_sample_candidate, plan_advance_cap, raw_to_date,
)


class CampaignScoreCadenceTests(unittest.TestCase):
    def test_frozen_native_clock_anchors_and_no_gregorian_leap_days(self):
        self.assertEqual(date_to_raw("1066.9.15"), 53144328)
        self.assertEqual(date_to_raw("1096.9.15"), 53407128)
        self.assertEqual(date_to_raw("1096.9.23"), 53407320)
        self.assertEqual(date_to_raw("1068.3.1") - date_to_raw("1068.2.28"), 24)
        for date in ("1066.9.15", "1068.2.28", "1096.9.15"):
            self.assertEqual(raw_to_date(date_to_raw(date)), date)
        for bad in ("1068.2.29", "1066.13.1", "1066.4.31"):
            with self.assertRaises(ValueError):
                date_to_raw(bad)
        with self.assertRaises(ValueError):
            raw_to_date(53144329)

    def test_360_monthly_boundaries_include_exact_endpoint_without_anchor_drift(self):
        rows = month_boundaries("1066.9.15")
        self.assertEqual(len(rows), 361)
        self.assertEqual(rows[1], ("1066.10.15", 53145048))
        self.assertEqual(rows[-1], ("1096.9.15", 53407128))
        self.assertEqual(len({raw for _, raw in rows}), 361)
        self.assertEqual([date for date, _ in month_boundaries("1068.1.31", 2)],
                         ["1068.1.31", "1068.2.28", "1068.3.31"])

    def test_cap_shortens_only_clock_target_and_requires_current_slot_before_advance(self):
        result = plan_advance_cap(date_to_raw("1066.10.12"), date_to_raw("1066.10.20"),
                                  start_date="1066.9.15", next_sample_index=1)
        self.assertEqual(result["target_date_raw"], date_to_raw("1066.10.15"))
        self.assertTrue(result["native_deadline_still_required"])
        self.assertEqual(plan_advance_cap(date_to_raw("1066.10.15"), date_to_raw("1066.10.23"),
                         start_date="1066.9.15", next_sample_index=1)["status"], "sample_due")
        self.assertEqual(plan_advance_cap(date_to_raw("1066.10.15"), date_to_raw("1066.10.23"),
                         start_date="1066.9.15", next_sample_index=2)["target_date_raw"], date_to_raw("1066.10.23"))

    def test_missed_slot_stays_missing_and_does_not_fabricate_or_block_next_target(self):
        result = plan_advance_cap(date_to_raw("1066.10.16"), date_to_raw("1066.10.24"),
                                  start_date="1066.9.15", next_sample_index=1)
        self.assertEqual(result["missed_sample_indices"], [1])
        self.assertEqual(result["next_sample_index"], 2)
        self.assertEqual(result["status"], "advance")
        self.assertEqual(result["target_date_raw"], date_to_raw("1066.10.24"))
        for date, status in (("1096.9.15", "endpoint_due"), ("1096.9.23", "endpoint_overshot")):
            result = plan_advance_cap(date_to_raw(date), date_to_raw(date) + 24,
                                     start_date="1066.9.15", next_sample_index=360)
            self.assertEqual(result["status"], status)
            self.assertIsNone(result["target_date_raw"])

    def candidate(self, actor=31254, date="1066.10.15", gold=-12345):
        return ordinary_sample_candidate({"date_raw": date_to_raw(date), "paused": True,
            "snapshot_id": "native:40", "revision": 41, "native_revision": 40,
            "episode_run_id": f"native-{actor}-fixture", "episode_character_id": actor,
            "played_character": {"character_id": actor, "alive": True},
            "played_character_gold": {"raw": gold, "scale": 100_000}, "active_wars": []},
            start_date="1066.9.15", machine_id="synthetic-fixture", observed_at_utc="synthetic",
            campaign_anchor={"campaign_id": "v20261019-fixture", "founder_character_id": 31254,
                             "founding_house_id": None, "founding_dynasty_id": None})

    def test_existing_month_frame_keeps_unknown_units_and_natural_successor_anchor(self):
        first, second = self.candidate(), self.candidate(40695, "1066.11.15")
        self.assertEqual(first["raw_metrics"]["gold"]["value"], "-0.12345")
        self.assertEqual(second["campaign_anchor"], first["campaign_anchor"])
        self.assertNotEqual(second["frame"]["actor_character_id"], first["frame"]["actor_character_id"])
        for name in ("gross_income", "total_expenses", "P_quality", "continuation_legal", "Q_realm"):
            self.assertEqual(first["raw_metrics"][name]["availability"], "unknown")
            self.assertIsNone(first["raw_metrics"][name]["value"])
        self.assertTrue(first["source_response_binding_pending"])
        self.assertEqual(first["new_RPC_calls"], 0)
        self.assertFalse(first["score_or_complete_history_claimed"])

    def test_nonboundary_is_not_relabelled_as_monthly_and_baseline_is_separate(self):
        self.assertIsNone(self.candidate(date="1066.10.16"))
        self.assertEqual(self.candidate(date="1066.9.15")["month_index"], 0)
        self.assertEqual(self.candidate(date="1096.9.15")["month_index"], 360)


if __name__ == "__main__":
    unittest.main()
