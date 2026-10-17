"""Closed AUTO361 projection, never a Native or game execution."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(REPO / "tools"))
from g2_saved_campaign.natural_succession_sentinel_boundary_v1 import classify_natural_boundary


class ActualNaturalBoundaryPolicy(unittest.TestCase):
    def test_actual361_uses_plan_speed_policy_and_inner_decision_epoch(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" /
                              "p50r1_auto361_natural_boundary_projection.json").read_bytes())
        body, arguments = fixture["body"], fixture["arguments"]
        preserved = copy.deepcopy(body)
        self.assertEqual(body["plan"]["timeline_policy"], "war_stationary_objective_hold_speed_5")
        self.assertEqual(body["result"]["timeline_policy"], "decision_epoch")
        result = classify_natural_boundary(body, **arguments)
        self.assertEqual(result["category"], "natural_succession_boundary_observed")
        self.assertEqual(result["natural_boundary_end"], {
            "date_raw": 53338848, "actor_character_id": 40695,
            "episode_run_id": "native-31254-8d3a8440eb30", "native_revision": 9042,
        })
        self.assertEqual(result["actual_elapsed_days"], 7)
        self.assertTrue(result["paired_after_metrics_still_required"])
        self.assertFalse(result["replay_allowed"])
        self.assertFalse(result["business_success_inferred"])
        self.assertEqual(result["business_cycle_credit"], 0)
        for policy in ("decision_epoch", "war_stationary_objective_hold_speed_4"):
            changed = copy.deepcopy(body)
            changed["plan"]["timeline_policy"] = policy
            with self.subTest(policy=policy), self.assertRaisesRegex(ValueError, "objective-hold natural boundary terms differ"):
                classify_natural_boundary(changed, **arguments)
        self.assertEqual(body, preserved)


if __name__ == "__main__":
    unittest.main(verbosity=2)
