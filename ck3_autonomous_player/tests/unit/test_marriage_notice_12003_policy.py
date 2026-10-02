"""Source-bound continuation for the actual v10 marriage letter scope shape."""

from __future__ import annotations

import copy
import unittest

from test_vanilla_event_registry_policy import _option, _scope
from test_event_window_context_v1_bridge import _frame
from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.outcome import plan_registered_event_material_postcondition_v1
from xar_autoplayer.vanilla_events.policy import recommend_registered_vanilla_event_option_v1
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1


PLAYER = 31853
EVENT = "marriage_interaction.0010"


def _context() -> dict[str, object]:
    character_ids = {
        "actor": PLAYER,
        "recipient": 39761,
        "secondary_actor": 36403,
        "secondary_recipient": 16825238,
        "puppet_or_actor": PLAYER,
    }
    saved = [
        {"name": name, "scope": _scope("character", character_id=identity)}
        for name, identity in character_ids.items()
    ]
    saved.append({
        "name": "intermediary",
        "scope": {
            "status": "available", "raw_type_index": 4, "type_key": "character",
            "subtype": 0,
            "typed_identity": {
                "status": "unavailable", "reason": "character_scope_is_null",
            },
        },
    })
    saved.extend(
        {"name": name, "scope": _scope("boolean")}
        for name in (
            "is_puppet_action", "grand_wedding_promise", "matrilineal", "hook",
            "piety_cost_reduction", "influence_send_option", "herd_send_option",
        )
    )
    for index, row in enumerate(saved):
        row["name_identifier"] = index + 1
    context = _frame()
    option = context["options"][0]
    option.update(_option(0, 0))
    option["resolved_name"] = "EXCELLENT"
    option["unavailable_reason"] = ""
    option["effect_indicators"]["coverage"] = "played-character-event-icon-indicators-1.20.0.3-v1"
    option["effect_indicators"]["rows"] = []
    context.update({
        "event_definition_key": EVENT,
        "root_scope": _scope("character", character_id=PLAYER),
        "saved_scopes": saved,
        "current_event_instance_id": 13, "snapshot_revision": 80,
        "date_raw": 53328600,
        "provenance": {
            "root": "module+0x5C6A520->+0x10", "idler_vtable_rva": "0x44BC408",
            "manager_offset": "+0x28", "backend_id": "ck3-1.20.0.3-native-event-window-v1",
        },
    })
    return context


class MarriageNotice12003PolicyTests(unittest.TestCase):
    def test_current_letter_continues_without_material_or_historical_credit(self) -> None:
        knowledge = query_vanilla_event_knowledge_v1(EVENT, "1.20.0.3")
        self.assertEqual(knowledge["status"], "available")
        analysis = knowledge["analysis"]
        self.assertEqual(analysis["definition_lines"], "381-1039")
        self.assertEqual(analysis["source_sha256"], {
            "events/interaction_events/marriage_interaction_events.txt":
            "78C367BA0B32A374E5BE5D88F7660E7898EF9DBC44412049521F64A472E4DCA5",
        })
        self.assertEqual(analysis["readiness"], "static-ready")
        self.assertFalse(analysis["new_live_evidence"])
        for build in ("1.19.0.6", "1.20.0.2"):
            self.assertEqual(query_vanilla_event_knowledge_v1(EVENT, build)["status"], "unavailable")
        context = _context()
        context = normalize_current_event_window_context_v1(
            context, expected_event_instance_id=13, expected_date_raw=53328600,
            expected_snapshot_revision=80,
        )
        decision = recommend_registered_vanilla_event_option_v1(
            context, played_character_id=PLAYER, snapshot_option_count=1,
        )
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_option_number"], 1)
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["failed_checks"], [])
        self.assertEqual(decision["choice_effect_profile"]["selected_option_effects"], [])
        self.assertEqual(decision["choice_effect_profile"]["common_after_effects"], [])
        self.assertIsNone(decision["choice_effect_profile"]["observable_postcondition"])
        self.assertFalse(decision["campaign_utility_ready"])
        self.assertIsNone(plan_registered_event_material_postcondition_v1(
            decision, {"character_id": PLAYER, "stress_points": 34},
            snapshot_id="marriage-notice-static:80", revision=81,
        ))
        snapshot = {
            "snapshot_id": "native:80", "revision": 81, "native_revision": 80,
            "date_raw": 53328600, "paused": True, "backend_id": "native-headless",
            "played_character": {"character_id": PLAYER, "alive": True},
            "active_event": {"instance_id": 13, "option_count": 1},
        }
        history = [{
            "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "ok": True,
            "result": {
                "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "accepted": True, "status": "available", "snapshot_revision": 80,
                "current_event_instance_id": 13, "date_raw": 53328600,
                "current_event_window_context": context, "queried_snapshot_id": "native:80",
                "queried_revision": 81, "queried_native_revision": 80,
            },
        }]
        plan = choose_one_life_turn(
            history, snapshot=snapshot,
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "select-event-option-1"},
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")

    def test_root_and_sole_option_checks_are_preserved(self) -> None:
        for mutation in ("root", "disabled", "second_option"):
            with self.subTest(mutation=mutation):
                context = copy.deepcopy(_context())
                if mutation == "root":
                    context["root_scope"] = copy.deepcopy(context["saved_scopes"][5]["scope"])
                elif mutation == "disabled":
                    context["options"][0]["enabled"] = False
                else:
                    context["options"].append(_option(1, 1))
                result = recommend_registered_vanilla_event_option_v1(
                    context, played_character_id=PLAYER, snapshot_option_count=1,
                )
                self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
