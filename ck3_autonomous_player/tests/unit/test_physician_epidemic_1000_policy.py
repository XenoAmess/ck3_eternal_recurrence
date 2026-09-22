from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn  # noqa: E402
from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    query_vanilla_event_source_v1,
)


PLAYER_ID = 36403
PHYSICIAN_ID = 50397184
COURTIER_ID = 33594572
DATE_RAW = 53350560


def _scope(type_key: str, character_id: int | None = None) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4 if type_key == "character" else 50,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": (
            {"status": "available", "kind": "character", "character_id": character_id}
            if character_id is not None
            else {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            }
        ),
    }


def _option(rendered_index: int, native_index: int) -> dict[str, object]:
    return {
        "rendered_index": rendered_index,
        "native_option_index": native_index,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": f"native-{native_index}",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
            "complete_effect_set": False,
            "rows": [],
        },
        "effect_preview": {
            "status": "unavailable",
            "reason": "indicator_subset_has_no_completeness_signal",
        },
        "resource_deltas": {"status": "unavailable"},
        "relationship_deltas": {"status": "unavailable"},
    }


def _context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 20,
        "date_raw": DATE_RAW,
        "current_event_instance_id": 21,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "physician_epidemic_events.1000",
        "calculated_event_id": 5581000,
        "runtime_stats_ordinal": 9666,
        "root_scope": _scope("character", PLAYER_ID),
        "saved_scopes": [
            {"name": "epidemic", "name_identifier": 101, "scope": _scope("epidemic")},
            {"name": "epidemic_scope", "name_identifier": 102, "scope": _scope("epidemic")},
            {"name": "physician", "name_identifier": 103, "scope": _scope("character", PHYSICIAN_ID)},
            {"name": "zealous_courtier", "name_identifier": 104, "scope": _scope("character", COURTIER_ID)},
        ],
        "options": [_option(0, 1), _option(1, 2)],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        },
        "provenance": {
            "root": "module+0x570F7B8->+0x10",
            "idler_vtable_rva": "0x40B1D30",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.19.0.6-native-event-window-v1",
        },
    }


def _recommend(context: dict[str, object], count: int = 3) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context, played_character_id=PLAYER_ID, snapshot_option_count=count
    )


class PhysicianEpidemic1000PolicyTests(unittest.TestCase):
    def test_exact_r0089_shape_selects_bounded_resistance_option(self) -> None:
        contract = DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[
            "physician_epidemic_events.1000"
        ]
        self.assertEqual(contract["root_character_id"], "$player")
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["native_option_indices"], (1, 2))
        result = _recommend(_context())
        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_optimal"])

        source = query_vanilla_event_source_v1(
            "physician_epidemic_events.1000"
        )
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["source"]["definition"]["line"], 8)
        self.assertEqual(
            [row["line"] for row in source["source"]["caller_candidates"]],
            [35],
        )

    def test_formal_planner_uses_registry_not_generic_fallback(self) -> None:
        context = _context()
        response = {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": 20,
            "current_event_instance_id": 21,
            "date_raw": DATE_RAW,
            "current_event_window_context": copy.deepcopy(context),
            "queried_snapshot_id": "native:20",
            "queried_revision": 21,
            "queried_native_revision": 20,
        }
        snapshot = {
            "snapshot_id": "native:20",
            "revision": 21,
            "native_revision": 20,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": PLAYER_ID, "alive": True},
            "active_event": {"instance_id": 21, "option_count": 3},
        }
        plan = choose_one_life_turn(
            [{
                "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "ok": True,
                "result": response,
            }],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-2",
                "select-event-option-3",
            },
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-2")
        self.assertEqual(plan["event_decision"]["status"], "recommended")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 1)

    def test_other_projection_blocks_without_first_click(self) -> None:
        changes = (
            lambda c: c["options"][0].update(native_option_index=0),
            lambda c: c["options"][1].update(enabled=False),
            lambda c: c["saved_scopes"][2]["scope"]["typed_identity"].update(character_id=PLAYER_ID),
            lambda c: c["saved_scopes"][3]["scope"]["typed_identity"].update(character_id=PHYSICIAN_ID),
            lambda c: c["saved_scopes"][0]["scope"].update(type_key="flag"),
            lambda c: c["saved_scopes"].append({"name": "unknown", "scope": _scope("epidemic")}),
        )
        for change in changes:
            with self.subTest(change=change):
                context = _context()
                change(context)
                result = _recommend(context)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_option_number"])
        self.assertEqual(_recommend(_context(), count=2)["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
