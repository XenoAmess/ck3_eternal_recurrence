"""Synthetic amounts only; no production source, files, locks or probes."""
from datetime import datetime, timedelta, timezone
import json
import unittest
import storage_native30_65p5_overlay_v1 as m


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 19, tzinfo=timezone.utc)
        g = m.GIB
        self.old = dict(machine_id="synthetic", reservation_id="r", observed_at_utc=self.now.isoformat(),
            review_at_utc_unchanged=(self.now + timedelta(days=1)).isoformat(), effective_stage_peak_bytes=64*g,
            original_stage_peak_bytes=64*g, remaining_estimated_stage_peak_upper_bytes=64*g,
            conservative_whole_volume_used_project_upper_bytes=100*g, conservative_current_free_lower_bytes=100*g,
            current_reconciled_quota_upper_bound_bytes=174*g, current_reconciled_physical_required_free_bytes=84*g,
            quota_bytes_unchanged=200*g, retained_other_reservations_bytes_unchanged=6*g, retained_old_OUT_bytes_unchanged=4*g)
        self.sup = dict(machine_id="synthetic", reservation_id="r", status="DRAFT_NOT_ADMITTED",
            review_at_utc=self.old["review_at_utc_unchanged"], independent_added_peak_bytes=m.ADDED,
            effective_stage_peak_bytes=64*g+m.ADDED, original_stage_peak_bytes=64*g,
            native30_child_hard_limit_bytes=m.ADDED, native30_exact_output_root=m.ROOT,
            effective_category_caps_bytes=m.CAPS, system_growth_reserve_bytes=5*g, safety_margin_bytes=5*g)

    def run_overlay(self, old=None, sup=None, **kw):
        return m.overlay(json.dumps(self.old if old is None else old).encode(),
            json.dumps(self.sup if sup is None else sup).encode(), now=self.now, allow_draft_preview=True, **kw)

    def test_math_and_old_unchanged(self):
        before = json.dumps(self.old)
        result = self.run_overlay()
        self.assertEqual(result["quota_margin_bytes"], 49*m.GIB//2)
        self.assertEqual(json.dumps(self.old), before)
        self.assertFalse(result["heavy_permission"])

    def test_wrong_stage_or_category(self):
        for change in ({"independent_added_peak_bytes": m.GIB}, {"effective_stage_peak_bytes": 65*m.GIB},
                       {"effective_category_caps_bytes": {**m.CAPS, "Driver_log": 10*m.GIB}}):
            with self.assertRaises(ValueError): self.run_overlay(sup={**self.sup, **change})

    def test_unknown_incomplete_or_stale(self):
        for change in ({"retained_old_OUT_bytes_unchanged": None}, {"current_reconciled_quota_upper_bound_bytes": 0},
                       {"observed_at_utc": (self.now-timedelta(seconds=121)).isoformat()}):
            with self.assertRaises(ValueError): self.run_overlay(old={**self.old, **change})

    def test_low_floor_or_incomplete_signature(self):
        with self.assertRaises(ValueError): self.run_overlay(old={**self.old, "conservative_current_free_lower_bytes": 85*m.GIB})
        with self.assertRaises(ValueError): self.run_overlay(sup={**self.sup, "status": "ADMITTED"})

    def test_draft_has_no_default_permission(self):
        with self.assertRaises(ValueError):
            m.overlay(json.dumps(self.old).encode(), json.dumps(self.sup).encode(), now=self.now)


if __name__ == "__main__": unittest.main()
