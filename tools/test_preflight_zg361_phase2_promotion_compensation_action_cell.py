#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from preflight_zg361_phase2_promotion_compensation_action_cell import (  # noqa: E402
    run_preflight,
)


class PromotionCompensationNoLaunchPreflightTests(unittest.TestCase):
    def test_static_contract_is_green_but_readiness_stays_live_pending(self) -> None:
        report = run_preflight()
        self.assertEqual(report["result"], "GREEN")
        self.assertEqual(report["readiness"], "live-pending")
        self.assertFalse(report["production_live"])
        self.assertFalse(report["ck3_launch_attempted"])
        self.assertFalse(report["formal_runner_registered"])
        self.assertEqual(report["failed_checks"], [])
        self.assertTrue(all(report["checks"].values()))
        source = report["source_checkpoint"]
        self.assertEqual(source["expected_option_count"], 3)
        self.assertIn("zg361_pp_prompt_subject", source["required_saved_character_scopes"])


if __name__ == "__main__":
    unittest.main()
