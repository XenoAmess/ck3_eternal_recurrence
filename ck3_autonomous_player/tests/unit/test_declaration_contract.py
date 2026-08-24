from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.declaration_contract import (
    declare_war_step,
    normalize_declarable_wars,
    parse_declare_war_step,
)
from xar_autoplayer.strategy import choose_one_life_turn


def _declaration() -> dict[str, object]:
    return {
        "declaration_id": "808-17-0",
        "target_character_id": 808,
        "casus_belli_index": 17,
        "casus_belli_key": "county_conquest_cb",
        "configuration_index": 0,
        "claimant_character_id": -1,
        "target_title_ids": [91],
    }


class NativeDeclarationContractTests(unittest.TestCase):
    def test_normalization_keeps_semantic_key_and_opaque_choice(self) -> None:
        normalized = normalize_declarable_wars([_declaration()])

        self.assertEqual(normalized[0]["declaration_id"], "808-17-0")
        self.assertEqual(normalized[0]["casus_belli_key"], "county_conquest_cb")
        self.assertEqual(normalized[0]["source"], "native")
        self.assertEqual(declare_war_step("808-17-0"), "declare-war-808-17-0")
        self.assertEqual(
            parse_declare_war_step("declare-war-808-17--1"), "808-17--1"
        )

    def test_normalization_rejects_a_choice_id_that_changed_meaning(self) -> None:
        changed = _declaration()
        changed["configuration_index"] = 1
        with self.assertRaisesRegex(ValueError, "declaration_id"):
            normalize_declarable_wars([changed])

    def test_planner_queries_then_requires_war_entry_evidence(self) -> None:
        commands = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
        ]
        discovery = choose_one_life_turn(
            commands,
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [],
            },
            action_steps={"query-declarable-wars", "life-advance"},
        )
        self.assertEqual(discovery["selected_step"], "query-declarable-wars")

        declaration = choose_one_life_turn(
            commands,
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [_declaration()],
            },
            action_steps={
                "query-declarable-wars",
                "declare-war-808-17-0",
                "life-advance",
            },
        )
        self.assertEqual(declaration["phase"], "native_war_entry_evidence_required")
        self.assertIsNone(declaration["selected_step"])
        self.assertEqual(
            declaration["declaration"]["casus_belli_key"],
            "county_conquest_cb",
        )
        self.assertIn(
            "game.command.query-combat-simulation-inputs",
            declaration["required_capabilities"],
        )
        self.assertIn(
            "game.forecast.combat-monte-carlo-v1",
            declaration["required_capabilities"],
        )

    def test_submitted_declaration_advances_before_another_query(self) -> None:
        plan = choose_one_life_turn(
            [
                {"index": 1, "command": "save-checkpoint", "ok": True},
                {
                    "index": 2,
                    "command": "declare-war-808-17-0",
                    "ok": True,
                },
            ],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [],
            },
            action_steps={"query-declarable-wars", "life-advance"},
        )
        self.assertEqual(plan["selected_step"], "life-advance")


if __name__ == "__main__":
    unittest.main()
