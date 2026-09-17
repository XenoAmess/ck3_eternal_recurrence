from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn  # noqa: E402
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


PLAYER_ID = 31_853
PHYSICIAN_ID = 44_001
EVENT_INSTANCE_ID = 4
DATE_RAW = 53_213_088
NATIVE_REVISION = 862


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    identity: dict[str, object]
    if character_id is None:
        identity = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    else:
        identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "status": "available",
        "raw_type_index": 4 if character_id is not None else 1,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": identity,
    }


def _saved_scope(
    name: str, type_key: str, *, character_id: int | None = None
) -> dict[str, object]:
    return {
        "name": name,
        "name_identifier": len(name) + 500,
        "scope": _scope(type_key, character_id=character_id),
    }


def _option(rendered_index: int, native_index: int) -> dict[str, object]:
    return {
        "rendered_index": rendered_index,
        "native_option_index": native_index,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": f"health.1001 option {native_index}",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": (
                "played-character-event-icon-indicators-1.19.0.6-v1"
            ),
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


def _context(*, physician_id: int | None = None) -> dict[str, object]:
    saved_scopes = [
        _saved_scope(
            "sick_character", "character", character_id=PLAYER_ID
        ),
        _saved_scope("disease_type", "flag"),
    ]
    native_indices = (0, 6)
    if physician_id is not None:
        saved_scopes.insert(
            0,
            _saved_scope(
                "physician", "character", character_id=physician_id
            ),
        )
        native_indices = (3, 4, 6)
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": EVENT_INSTANCE_ID,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "health.1001",
        "calculated_event_id": 4_571_001,
        "runtime_stats_ordinal": 9_001,
        "root_scope": _scope("character", character_id=PLAYER_ID),
        "saved_scopes": saved_scopes,
        "options": [
            _option(rendered, native)
            for rendered, native in enumerate(native_indices)
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
        context,
        played_character_id=PLAYER_ID,
        snapshot_option_count=7,
    )


class Health1001PolicyTests(unittest.TestCase):
    def test_r858_no_physician_projection_selects_search(self) -> None:
        result = _recommend(_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 1)
        self.assertEqual(result["selected_native_option_index"], 0)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["matched_option_variant_index"], 0)
        self.assertEqual(result["failed_checks"], [])

    def test_physician_projection_selects_safe_treatment(self) -> None:
        result = _recommend(_context(physician_id=PHYSICIAN_ID))

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 4)
        self.assertEqual(result["selected_native_option_index"], 3)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertIsNone(result["matched_option_variant_index"])
        self.assertEqual(result["failed_checks"], [])

    def test_scope_relationship_drift_remains_fail_closed(self) -> None:
        cases = (
            (
                "unexpected physician in no-physician rows",
                _saved_scope(
                    "physician", "character", character_id=PHYSICIAN_ID
                ),
                "saved_scope_names_exact",
            ),
            (
                "sick character is not the player",
                None,
                "scope:sick_character:character_id",
            ),
        )
        for label, extra_scope, failed_check in cases:
            with self.subTest(label=label):
                context = _context()
                if extra_scope is not None:
                    context["saved_scopes"].append(extra_scope)
                else:
                    context["saved_scopes"][0] = _saved_scope(
                        "sick_character", "character", character_id=40_002
                    )

                result = _recommend(context)

                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_planner_uses_typed_registry_search_action(self) -> None:
        context = _context()
        query_result = {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": NATIVE_REVISION,
            "current_event_instance_id": EVENT_INSTANCE_ID,
            "date_raw": DATE_RAW,
            "current_event_window_context": copy.deepcopy(context),
            "queried_snapshot_id": f"native:{NATIVE_REVISION}",
            "queried_revision": NATIVE_REVISION + 1,
            "queried_native_revision": NATIVE_REVISION,
        }
        snapshot = {
            "snapshot_id": f"native:{NATIVE_REVISION}",
            "revision": NATIVE_REVISION + 1,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {
                "character_id": PLAYER_ID,
                "alive": True,
            },
            "active_event": {
                "instance_id": EVENT_INSTANCE_ID,
                "option_count": 7,
            },
        }

        plan = choose_one_life_turn(
            [
                {
                    "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                    "ok": True,
                    "result": query_result,
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
        self.assertEqual(
            plan["active_event"]["selected_native_option_index"], 0
        )
        self.assertEqual(
            plan["event_decision"]["matched_option_variant_index"], 0
        )


if __name__ == "__main__":
    unittest.main()
