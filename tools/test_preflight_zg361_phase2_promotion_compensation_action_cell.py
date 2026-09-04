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
        self.assertFalse(report["ck3_started"])
        self.assertFalse(report["ck3_launch_attempted"])
        self.assertFalse(report["provider_live_result_claimed"])
        self.assertFalse(report["formal_runner_registered"])
        self.assertEqual(report["failed_checks"], [])
        self.assertTrue(all(report["checks"].values()))
        source = report["source_checkpoint"]
        self.assertEqual(source["expected_option_count"], 3)
        self.assertIn("zg361_pp_prompt_subject", source["required_saved_character_scopes"])
        self.assertIn("zg361pp.147 option-1", report["next_live_checkpoint"])
        for check in (
            "provider_source_contract_is_frozen",
            "fixed_native_allowlists_match_contract",
            "typed_unavailable_is_reader_and_schema_enforced",
            "mailbox_and_shared_bridge_are_wired",
            "driver_service_and_mcp_are_wired",
            "ack_is_excluded_from_provider_evidence",
        ):
            self.assertTrue(report["checks"][check])


if __name__ == "__main__":
    unittest.main()
