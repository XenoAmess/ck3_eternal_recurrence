from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "tools" / "extract_g2_goal_continuity.py"
SPEC = importlib.util.spec_from_file_location("extract_g2_goal_continuity", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load offline goal extractor: {SOURCE}")
extractor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)


def empty_receipt():
    return {"result": {"structured_content": {}}}


class GoalContinuityProjectionTests(unittest.TestCase):
    def test_missing_goal_remains_unobserved(self):
        report = extractor.summarize(empty_receipt(), empty_receipt())
        self.assertIsNone(report["comparison"]["goal_equal"])
        self.assertEqual(report["comparison"]["goal_status"], "not_observed")

    def test_plan_without_goal_field_is_not_consumption(self):
        report = extractor.summarize(
            empty_receipt(), empty_receipt(), {"plan": {"phase": "other"}}
        )
        self.assertEqual(report["normal_plan_consumption"]["status"], "not_observed")

    def test_explicit_fixture_plan_is_preserved_without_promotion(self):
        plan = {"plan": {"campaign_goal_plan_used": {
            "campaign_id": "fixture-only", "current_character_id": 200,
        }}}
        found = extractor.plan_goal_values(plan)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["value"], plan["plan"]["campaign_goal_plan_used"])
        report = extractor.summarize(empty_receipt(), empty_receipt(), plan)
        self.assertFalse(report["m7_complete_claimed"])


if __name__ == "__main__":
    unittest.main()
