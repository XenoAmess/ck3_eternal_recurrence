from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.marriage_contract import (
    QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
    arrange_marriage_step,
    normalize_arrange_marriage_choices,
    parse_arrange_marriage_step,
)
from xar_autoplayer.strategy import choose_one_life_turn


def _choice() -> dict[str, object]:
    return {
        "choice_id": "707-808",
        "played_character_id": 707,
        "candidate_character_id": 808,
    }


class NativeMarriageContractTests(unittest.TestCase):
    def test_normalization_preserves_full_generation_handles(self) -> None:
        normalized = normalize_arrange_marriage_choices([_choice()])

        self.assertEqual(normalized[0]["choice_id"], "707-808")
        self.assertEqual(normalized[0]["source"], "native")
        self.assertEqual(
            arrange_marriage_step("707-808"),
            "arrange-marriage-707-808",
        )
        self.assertEqual(
            parse_arrange_marriage_step("arrange-marriage-707-808"),
            "707-808",
        )

    def test_normalization_rejects_a_relabelled_choice(self) -> None:
        changed = _choice()
        changed["candidate_character_id"] = 809
        with self.assertRaisesRegex(ValueError, "choice_id"):
            normalize_arrange_marriage_choices([changed])

    def test_planner_queries_then_submits_before_first_war(self) -> None:
        commands = [{"index": 1, "command": "save-checkpoint", "ok": True}]
        discovery = choose_one_life_turn(
            commands,
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "arrange_marriage_choices": [],
                "declarable_wars": [],
            },
            action_steps={
                QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "query-declarable-wars",
            },
        )
        self.assertEqual(
            discovery["selected_step"],
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
        )

        selected = choose_one_life_turn(
            commands,
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "arrange_marriage_choices": [_choice()],
                "declarable_wars": [],
            },
            action_steps={
                QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "arrange-marriage-707-808",
                "query-declarable-wars",
            },
        )
        self.assertEqual(selected["selected_step"], "arrange-marriage-707-808")

        after_submission = choose_one_life_turn(
            [
                *commands,
                {
                    "index": 2,
                    "command": "arrange-marriage-707-808",
                    "ok": True,
                },
            ],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "arrange_marriage_choices": [],
                "declarable_wars": [],
            },
            action_steps={"query-declarable-wars"},
        )
        self.assertEqual(after_submission["selected_step"], "query-declarable-wars")


if __name__ == "__main__":
    unittest.main()
