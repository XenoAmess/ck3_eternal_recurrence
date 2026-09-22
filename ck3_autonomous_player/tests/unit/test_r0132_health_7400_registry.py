"""R0132 production frame for the source-reviewed health.7400 choice."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "r0132_health_7400_context.json"
)
PLAYER = 36403


def _context() -> dict[str, object]:
    evidence = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert evidence["source_formal_report_sha256"] == (
        "AE156BF039A0DB4A96EA50BBD5362229BB7E7BA9AD56EECA73FDD8E69346FB68"
    )
    assert evidence["source_command_history_index"] == 2498
    return evidence["context"]


def _recommend(context: dict[str, object]) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=PLAYER,
        snapshot_option_count=1,
    )


class R0132Health7400RegistryTests(unittest.TestCase):
    def test_natural_paused_frame_selects_source_reviewed_sole_option(self) -> None:
        context = _context()
        result = _recommend(context)
        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["failed_checks"], [])

        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "accepted": True,
                "status": "available",
                "snapshot_revision": 35,
                "current_event_instance_id": 29,
                "date_raw": 53439984,
                "current_event_window_context": context,
                "queried_snapshot_id": "native:35",
                "queried_revision": 36,
                "queried_native_revision": 35,
            },
        }]
        snapshot = {
            "snapshot_id": "native:35",
            "revision": 36,
            "native_revision": 35,
            "date_raw": 53439984,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": PLAYER, "alive": True},
            "active_event": {"instance_id": 29, "option_count": 1},
        }
        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(
            plan["event_decision"]["selected_native_option_index"], 0
        )

    def test_unreviewed_scope_or_option_shape_still_blocks(self) -> None:
        extra_scope = _context()
        extra_scope["saved_scopes"] = [{
            "name": "unreviewed",
            "scope": {"status": "available", "type_key": "character"},
        }]
        self.assertEqual(_recommend(extra_scope)["status"], "blocked")

        extra_option = _context()
        other = copy.deepcopy(extra_option["options"][0])
        other["rendered_index"] = 1
        other["native_option_index"] = 1
        extra_option["options"].append(other)
        self.assertEqual(_recommend(extra_option)["status"], "blocked")

        disabled = _context()
        disabled["options"][0]["enabled"] = False
        self.assertEqual(_recommend(disabled)["status"], "blocked")

        wrong_native = _context()
        wrong_native["options"][0]["native_option_index"] = 1
        self.assertEqual(_recommend(wrong_native)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
