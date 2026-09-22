from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


PLAYER_ID = 36_403
PHYSICIAN_ID = 50_397_184
INSTANCE_ID = 17
DATE_RAW = 53_334_696
NATIVE_REVISION = 170


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4 if character_id is not None else 3,
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
                "reason": "generic_scope_payload_identity_not_closed",
            }
        ),
    }


def _saved(name: str, scope: dict[str, object]) -> dict[str, object]:
    return {"name": name, "name_identifier": 100 + len(name), "scope": scope}


def _context(*, physician: bool = True) -> dict[str, object]:
    scopes = [
        _saved("sick_character", _scope("character", character_id=PLAYER_ID)),
        _saved("disease_type", _scope("flag")),
    ]
    if physician:
        scopes.insert(
            0,
            _saved("physician", _scope("character", character_id=PHYSICIAN_ID)),
        )
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": INSTANCE_ID,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "health.1101",
        "calculated_event_id": 4_211_101,
        "runtime_stats_ordinal": 6_532,
        "root_scope": _scope("character", character_id=PLAYER_ID),
        "saved_scopes": scopes,
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "I have recovered.",
                "unavailable_reason": "",
                "effect_indicators": {
                    "status": "available",
                    "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
                    "complete_effect_set": False,
                    "rows": [
                        {
                            "kind": "trait",
                            "operation": "remove",
                            "trait": {
                                "status": "available",
                                "native_id": 109,
                                "key": "ill",
                            },
                        }
                    ],
                },
                "effect_preview": {
                    "status": "unavailable",
                    "reason": "indicator_subset_has_no_completeness_signal",
                },
                "resource_deltas": {"status": "unavailable"},
                "relationship_deltas": {"status": "unavailable"},
            }
        ],
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


def _recommend(context: dict[str, object]) -> dict[str, object]:
    return recommend_registered_vanilla_event_option_v1(
        context, played_character_id=PLAYER_ID, snapshot_option_count=1
    )


class Health1101PolicyTests(unittest.TestCase):
    def test_r0085_physician_and_r200_no_physician_variants(self) -> None:
        for physician in (True, False):
            with self.subTest(physician=physician):
                result = _recommend(_context(physician=physician))
                self.assertEqual(result["status"], "recommended")
                self.assertEqual(result["selected_option_number"], 1)
                self.assertEqual(result["selected_native_option_index"], 0)
                self.assertEqual(result["failed_checks"], [])
                self.assertFalse(result["semantic_decision_ready"])

    def test_relational_and_option_projection_drift_still_blocks(self) -> None:
        changes = (
            (
                "sick character is not player",
                lambda c: c["saved_scopes"][1]["scope"]["typed_identity"].update(
                    character_id=PHYSICIAN_ID
                ),
            ),
            (
                "physician is player",
                lambda c: c["saved_scopes"][0]["scope"]["typed_identity"].update(
                    character_id=PLAYER_ID
                ),
            ),
            (
                "disease type is not flag",
                lambda c: c["saved_scopes"][2]["scope"].update(type_key="value"),
            ),
            (
                "unexpected scope",
                lambda c: c["saved_scopes"].append(
                    _saved("unknown", _scope("flag"))
                ),
            ),
            (
                "hidden sole option",
                lambda c: c["options"][0].update(shown=False),
            ),
            (
                "wrong native option",
                lambda c: c["options"][0].update(native_option_index=1),
            ),
        )
        for name, change in changes:
            with self.subTest(name=name):
                context = _context()
                change(context)
                result = _recommend(context)
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["selected_option_number"])

    def test_formal_planner_selects_only_typed_option(self) -> None:
        context = _context()
        result = {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": NATIVE_REVISION,
            "current_event_instance_id": INSTANCE_ID,
            "date_raw": DATE_RAW,
            "current_event_window_context": copy.deepcopy(context),
            "queried_snapshot_id": "native:170",
            "queried_revision": 171,
            "queried_native_revision": NATIVE_REVISION,
        }
        snapshot = {
            "snapshot_id": "native:170",
            "revision": 171,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {
                "character_id": PLAYER_ID,
                "alive": True,
                "stress_points": 0,
            },
            "active_event": {"instance_id": INSTANCE_ID, "option_count": 1},
        }

        plan = choose_one_life_turn(
            [
                {
                    "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                    "ok": True,
                    "result": result,
                }
            ],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        self.assertEqual(plan["event_decision"]["status"], "recommended")
        self.assertEqual(plan["active_event"]["selected_native_option_index"], 0)


if __name__ == "__main__":
    unittest.main()
