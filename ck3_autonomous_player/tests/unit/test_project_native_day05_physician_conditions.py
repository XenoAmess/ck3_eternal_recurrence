from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/project_native_day05_physician_conditions.py"
ARTIFACT = (ROOT / "src/xar_autoplayer/simulation/data/"
            "ck3_1_19_0_6_episode01_day05_physician_conditions_v1.json")
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("day05_physician_projector", SCRIPT)
assert spec is not None and spec.loader is not None
projector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projector)


class Day05PhysicianProjectionTest(unittest.TestCase):
    def test_character_save_parser_preserves_court_position_and_skill_slots(self) -> None:
        sample = (
            "\t57392={\n\t\tfirst_name=\"Guy\"\n"
            "\t\tskill={\n\t\t\t1 3 2 7 2 1\n\t\t}\n"
            "\t\ttraits={\n\t\t\t70 49 67 22\n\t\t}\n"
            "\t\tcourt_data={\n\t\t\temployer=34333\n"
            "\t\t\tcourt_positions={\n\t\t\t\t834\n\t\t\t}\n\t\t}\n\t}\n"
        )
        self.assertEqual(projector.character_record(sample, 57392), {
            "character_id": 57392,
            "skills": [1, 3, 2, 7, 2, 1],
            "trait_ids": [70, 49, 67, 22],
            "court_employer_id": 34333,
            "court_position_ids": [834],
        })

    def test_learning_reader_uses_only_top_level_trait_modifier(self) -> None:
        source = (
            "just = {\n\tlearning = 1\n\tculture_modifier = {\n"
            "\t\tlearning = 99\n\t}\n}\n"
            "gluttonous = {\n\tstewardship = -2\n}\n"
        )
        self.assertEqual(projector.trait_learning_bonus(source, "just"), 1)
        self.assertEqual(projector.trait_learning_bonus(source, "gluttonous"), 0)

    def test_frozen_projection_keeps_static_and_live_evidence_separate(self) -> None:
        result = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(result["pre_event_court_physician_character_id"], 57392)
        self.assertEqual(result["pre_event_physician_learning_components"]["base_plus_frozen_trait_modifiers"], 10)
        self.assertEqual(result["static_projected_weights"], [40, 50])
        self.assertEqual(result["runtime_picker_weights_direct"], [40, 50])
        self.assertFalse(result["physician_id_at_picker_directly_observed"])
        self.assertFalse(result["physician_effective_learning_at_picker_directly_observed"])
        self.assertFalse(result["pre_list_physician_rank_up_outcome_observed"])


if __name__ == "__main__":
    unittest.main()
