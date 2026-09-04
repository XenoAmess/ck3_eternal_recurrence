#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from preflight_zg361_phase2_promotion_source_checkpoint_capture import (  # noqa: E402
    run_preflight,
)


class PromotionSourceCaptureNoLaunchPreflightTests(unittest.TestCase):
    def test_explicit_live_entry_is_static_green_but_live_pending(self) -> None:
        report = run_preflight()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "static-ready-live-pending")
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["ck3_launch_attempted"])
        self.assertFalse(report["service_instantiated"])
        self.assertFalse(report["checkpoint_written"])
        self.assertFalse(report["capture_artifact_written"])
        self.assertTrue(report["provider_default_off"])
        self.assertTrue(report["incomplete_for_canonical_4_entry_registry"])
        self.assertFalse(report["canonical_registry_ready"])
        self.assertEqual(report["failed_checks"], [])
        self.assertTrue(all(report["checks"].values()))
        merge = report["deterministic_merge_input"]
        self.assertEqual(merge["schema_version"], 2)
        self.assertEqual(merge["entry_index"], 0)
        self.assertEqual(len(merge["required_handler_order"]), 4)


if __name__ == "__main__":
    unittest.main()
