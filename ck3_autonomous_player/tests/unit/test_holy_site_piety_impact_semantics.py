from __future__ import annotations
import json
from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
from xar_autoplayer.holy_site_planning_knowledge import query_holy_site_planning_knowledge_v1
from xar_autoplayer.holy_site_grade_value_knowledge import HOLY_SITE_GRADE_VALUE_KNOWLEDGE


class HolySitePietyImpactSemanticsTests(unittest.TestCase):
    def test_new_semantics_are_discoverable_and_match_maintainable_payload(self):
        result = query_holy_site_planning_knowledge_v1("promote")
        self.assertFalse(result["state_observed"])
        self.assertFalse(result["action_ready"])
        self.assertIsNone(result["native_legality"])
        value = result["knowledge"]["grade_value_comparison"]["modifier_semantics"]["piety_level_impact_mult"]
        self.assertEqual(value["meaning"], "amplifies modifiers granted by the current devotion level")
        self.assertIn("direct_piety_gain", value["does_not_itself_establish"])
        self.assertIn("devotion_level_increase", value["does_not_itself_establish"])
        self.assertIn("extra_personal_tenet_slots", value["does_not_itself_establish"])
        self.assertFalse(value["individual_level_benefit_consumers_verified"])
        self.assertFalse(value["separate_mecca_knight_term"]["is_piety_level_impact_formula"])
        self.assertFalse(value["separate_mecca_knight_term"]["actual_panel_net_increase_observed"])
        self.assertFalse(value["current_values_observed"])
        raw = PROJECT_ROOT.parent / "docs/ck3-native-ai/evidence/holy-site-major-grade-value12004/value-contract.json"
        self.assertEqual(json.loads(raw.read_text(encoding="utf-8")), HOLY_SITE_GRADE_VALUE_KNOWLEDGE)


if __name__ == "__main__":
    unittest.main()
