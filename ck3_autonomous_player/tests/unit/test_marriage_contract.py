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

    def test_empty_query_advances_once_then_refreshes_choices(self) -> None:
        commands = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {
                "index": 2,
                "command": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "ok": True,
                "result": {"arrange_marriage_choices": []},
            },
        ]
        snapshot = {
            "active_wars": [],
            "player_armies": [],
            "arrange_marriage_choices": [],
            "declarable_wars": [],
        }
        steps = {
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
            "life-advance",
            "query-declarable-wars",
        }

        wait = choose_one_life_turn(
            commands,
            snapshot=snapshot,
            action_steps=steps,
        )
        self.assertEqual(wait["selected_step"], "life-advance")

        refreshed = choose_one_life_turn(
            [
                *commands,
                {"index": 3, "command": "life-advance", "ok": True},
            ],
            snapshot=snapshot,
            action_steps=steps,
        )
        self.assertEqual(
            refreshed["selected_step"],
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
        )

    def test_failed_marriage_choice_forces_a_fresh_query(self) -> None:
        decision = choose_one_life_turn(
            [
                {"index": 1, "command": "save-checkpoint", "ok": True},
                {
                    "index": 2,
                    "command": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                    "ok": True,
                },
                {
                    "index": 3,
                    "command": "arrange-marriage-707-808",
                    "ok": False,
                    "error": "choice became stale",
                },
            ],
            snapshot={
                "active_wars": [],
                "player_armies": [],
                "arrange_marriage_choices": [],
                "declarable_wars": [],
            },
            action_steps={
                QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "life-advance",
                "query-declarable-wars",
            },
        )
        self.assertEqual(
            decision["selected_step"],
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
        )

    def test_existing_native_marriage_skips_a_second_proposal(self) -> None:
        decision = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot={
                "played_character": {
                    "character_id": 707,
                    "alive": True,
                    "betrothed_id": None,
                    "primary_spouse_id": 808,
                    "spouse_ids": [808],
                },
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
        self.assertEqual(decision["selected_step"], "query-declarable-wars")

    def test_submitted_native_proposal_waits_then_refreshes_until_observed(self) -> None:
        snapshot = {
            "played_character": {
                "character_id": 707,
                "alive": True,
                "betrothed_id": None,
                "primary_spouse_id": None,
                "spouse_ids": [],
            },
            "active_wars": [],
            "player_armies": [],
            "arrange_marriage_choices": [],
            "declarable_wars": [],
        }
        steps = {
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
            "life-advance",
            "query-declarable-wars",
        }
        commands = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {
                "index": 2,
                "command": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "ok": True,
            },
            {
                "index": 3,
                "command": "arrange-marriage-707-808",
                "ok": True,
                "result": {
                    "marriage_action": {
                        "status": "proposal_submitted",
                        "candidate_character_id": 808,
                    }
                },
            },
        ]

        waiting = choose_one_life_turn(
            commands,
            snapshot=snapshot,
            action_steps=steps,
        )
        self.assertEqual(waiting["selected_step"], "life-advance")

        refreshed = choose_one_life_turn(
            [
                *commands,
                {"index": 4, "command": "life-advance", "ok": True},
            ],
            snapshot=snapshot,
            action_steps=steps,
        )
        self.assertEqual(
            refreshed["selected_step"],
            QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
        )

    def test_repeated_empty_queries_do_not_block_the_rest_of_the_life(self) -> None:
        decision = choose_one_life_turn(
            [
                {"index": 1, "command": "save-checkpoint", "ok": True},
                *(
                    {
                        "index": index,
                        "command": QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                        "ok": True,
                    }
                    for index in range(2, 5)
                ),
            ],
            snapshot={
                "played_character": {
                    "character_id": 707,
                    "alive": True,
                    "betrothed_id": None,
                    "primary_spouse_id": None,
                    "spouse_ids": [],
                },
                "active_wars": [],
                "player_armies": [],
                "arrange_marriage_choices": [],
                "declarable_wars": [],
            },
            action_steps={
                QUERY_ARRANGE_MARRIAGE_CHOICES_STEP,
                "life-advance",
                "query-declarable-wars",
            },
        )
        self.assertEqual(decision["selected_step"], "query-declarable-wars")


if __name__ == "__main__":
    unittest.main()
