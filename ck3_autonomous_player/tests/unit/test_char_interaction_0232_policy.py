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
DATE_RAW = 53349960


def _scope(type_key: str, character_id: int | None = None) -> dict[str, object]:
    raw_type = {
        "character": 4,
        "boolean": 2,
        "epidemic": 50,
        "province": 8,
        "landed_title": 5,
    }[type_key]
    return {
        "status": "available",
        "raw_type_index": raw_type,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": (
            {
                "status": "available",
                "kind": "character",
                "character_id": character_id,
            }
            if character_id is not None
            else {
                "status": "unavailable",
                "reason": (
                    "character_scope_identity_unavailable"
                    if type_key == "character"
                    else "generic_scope_payload_identity_not_closed"
                ),
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
        "resolved_name": f"option-{native_index}",
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
    identities = {
        "actor": 38609,
        "recipient": 39146,
        "secondary_actor": None,
        "secondary_recipient": None,
        "intermediary": None,
        "hook": None,
        "imprisoner": 38609,
        "imprisonment_target": 39146,
        "war_for_imprisonment_flavour": None,
    }
    scopes = [
        {
            "name": name,
            "name_identifier": 100 + index,
            "scope": _scope(
                "boolean" if name in {"hook", "war_for_imprisonment_flavour"}
                else "character",
                character_id,
            ),
        }
        for index, (name, character_id) in enumerate(identities.items())
    ]
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": 10,
        "date_raw": DATE_RAW,
        "current_event_instance_id": 19,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "char_interaction.0232",
        "calculated_event_id": 3670232,
        "runtime_stats_ordinal": 6212,
        "root_scope": _scope("character", PLAYER_ID),
        "saved_scopes": scopes,
        "options": [_option(0, 0), _option(1, 1)],
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


def _recommend(context: dict[str, object], count: int = 2) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context, played_character_id=PLAYER_ID, snapshot_option_count=count
    )


class CharInteraction0232PolicyTests(unittest.TestCase):
    def test_r0088_exact_two_option_projection_selects_refusal(self) -> None:
        contract = DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS[
            "char_interaction.0232"
        ]
        self.assertEqual(contract["root_character_id"], "$player")
        self.assertNotIn("date_raw", contract)
        self.assertEqual(contract["selected_native_option_index"], 1)
        result = _recommend(_context())
        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_optimal"])
        source = query_vanilla_event_source_v1("char_interaction.0232")
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["source"]["definition"]["line"], 1678)
        self.assertEqual(
            [row["line"] for row in source["source"]["caller_candidates"]],
            [895, 1362, 1528],
        )

    def test_r0088_formal_planner_does_not_choose_generic_first(self) -> None:
        context = _context()
        response = {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": 10,
            "current_event_instance_id": 19,
            "date_raw": DATE_RAW,
            "current_event_window_context": copy.deepcopy(context),
            "queried_snapshot_id": "native:10",
            "queried_revision": 11,
            "queried_native_revision": 10,
        }
        snapshot = {
            "snapshot_id": "native:10",
            "revision": 11,
            "native_revision": 10,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {"character_id": PLAYER_ID, "alive": True},
            "active_event": {"instance_id": 19, "option_count": 2},
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
                "select-event-option-1",
                "select-event-option-2",
            },
        )
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-2")
        self.assertEqual(plan["event_decision"]["status"], "recommended")

    def test_other_scope_or_option_shape_blocks_instead_of_first_click(self) -> None:
        changes = (
            lambda c: c["options"][1].update(enabled=False),
            lambda c: c["options"][1].update(native_option_index=2),
            lambda c: c["saved_scopes"][6]["scope"]["typed_identity"].update(
                character_id=99999
            ),
            lambda c: c["saved_scopes"][0]["scope"]["typed_identity"].update(
                character_id=PLAYER_ID
            ),
            lambda c: c["saved_scopes"][5]["scope"].update(type_key="flag"),
        )
        for change in changes:
            with self.subTest(change=change):
                context = _context()
                change(context)
                result = _recommend(context)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_option_number"])

    def test_r0087_epidemic_1100_is_distinct_registry_contract(self) -> None:
        context = {
            **_context(),
            "event_definition_key": "epidemic_events.1100",
            "calculated_event_id": 1251100,
            "runtime_stats_ordinal": 638,
            "root_scope": _scope("character", PLAYER_ID),
            "saved_scopes": [
                {"name": "epidemic", "name_identifier": 201, "scope": _scope("epidemic")},
                {"name": "province", "name_identifier": 202, "scope": _scope("province")},
                {"name": "infected_county", "name_identifier": 203, "scope": _scope("landed_title")},
            ],
            "options": [_option(0, 0), _option(1, 1)],
        }
        result = _recommend(context, count=3)
        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["event_definition_key"], "epidemic_events.1100")


if __name__ == "__main__":
    unittest.main()
