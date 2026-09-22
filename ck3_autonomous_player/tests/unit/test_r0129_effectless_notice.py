"""Regression for the R0129 native option-4 faith-unlock notice frame."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.registry import (
    query_vanilla_event_knowledge_v1,
)


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "r0129_great_holy_war_0011_context.json"
)
PLAYER = 36403


def _context() -> dict[str, object]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert document["source_formal_report_sha256"] == (
        "2707E485278965761879C60F6858988B0458CED27BB333391BF5E1F566B9AE2F"
    )
    assert document["source_command_history_index"] == 2152
    return document["context"]


def _recommend(context: dict[str, object]) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=PLAYER,
        snapshot_option_count=5,
    )


class R0129EffectlessNoticeTests(unittest.TestCase):
    def test_original_paused_frame_selects_only_native_four(self) -> None:
        context = _context()
        result = _recommend(context)

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 5)
        self.assertEqual(result["selected_native_option_index"], 4)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["matched_option_variant_index"], 0)
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(
            result["choice_effect_profile"]["selected_option_effects"], []
        )
        self.assertEqual(
            result["choice_effect_profile"]["non_gameplay_after_presentation"],
            ["custom_tooltip"],
        )

        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "accepted": True,
                "status": "available",
                "snapshot_revision": 80,
                "current_event_instance_id": 25,
                "date_raw": 53392944,
                "current_event_window_context": context,
                "queried_snapshot_id": "native:80",
                "queried_revision": 81,
                "queried_native_revision": 80,
            },
        }]
        snapshot = {
            "snapshot_id": "native:80",
            "revision": 81,
            "native_revision": 80,
            "date_raw": 53392944,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": PLAYER, "alive": True},
            "active_event": {"instance_id": 25, "option_count": 5},
        }
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-5",
            },
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-5")
        self.assertEqual(
            plan["event_decision"]["selected_native_option_index"], 4
        )

    def test_original_scope_and_option_drift_fail_closed(self) -> None:
        changed_scope = _context()
        changed_scope["saved_scopes"][-1]["name"] = "unreviewed_scope"
        scope_result = _recommend(changed_scope)
        self.assertEqual(scope_result["status"], "blocked")
        self.assertIn("saved_scope_names_exact", scope_result["failed_checks"])

        second_option = _context()
        extra = copy.deepcopy(second_option["options"][0])
        extra["rendered_index"] = 1
        extra["native_option_index"] = 3
        second_option["options"].append(extra)
        option_result = _recommend(second_option)
        self.assertEqual(option_result["status"], "blocked")
        self.assertIsNone(option_result["selected_native_option_index"])

        incomplete_frame = _context()
        incomplete_frame["snapshot_revision"] = None
        frame_result = _recommend(incomplete_frame)
        self.assertEqual(frame_result["status"], "blocked")
        self.assertIn(
            "effectless_notice_same_event_frame",
            frame_result["failed_checks"],
        )

    def test_empty_native_indicators_do_not_replace_source_proof(self) -> None:
        for mutation in ("source_sha256", "option_effect", "after_effect"):
            with self.subTest(mutation=mutation):
                knowledge = query_vanilla_event_knowledge_v1(
                    "great_holy_war.0011"
                )
                review = knowledge["analysis"][
                    "source_reviewed_effectless_notice"
                ]
                if mutation == "source_sha256":
                    review["definition_sha256"] = "0" * 64
                elif mutation == "option_effect":
                    review["option_effects_by_native_index"]["4"] = [
                        "unreviewed_gameplay_effect"
                    ]
                else:
                    review["after_effects"] = [{
                        "kind": "unreviewed_gameplay_effect",
                        "gameplay_effect": True,
                    }]
                with mock.patch(
                    "xar_autoplayer.vanilla_events.policy."
                    "query_vanilla_event_knowledge_v1",
                    return_value=knowledge,
                ):
                    result = _recommend(_context())
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(
                    result["unavailable_reason"],
                    "registered_effectless_notice_source_review_invalid",
                )

    def test_previous_three_scope_variant_remains_exact(self) -> None:
        old_shape = _context()
        old_shape["saved_scopes"].pop()
        old_shape["options"][0]["native_option_index"] = 3
        result = _recommend(old_shape)
        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 3)
        self.assertIsNone(result["matched_option_variant_index"])


if __name__ == "__main__":
    unittest.main()
