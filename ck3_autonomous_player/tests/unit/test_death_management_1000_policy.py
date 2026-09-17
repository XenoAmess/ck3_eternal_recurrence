from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


PLAYER_ID = 31_853
DEAD_SPOUSE_ID = 25_583
EVENT_INSTANCE_ID = 3
DATE_RAW = 53_156_616
NATIVE_REVISION = 62


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    if character_id is None:
        typed_identity: dict[str, object] = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    else:
        typed_identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "status": "available",
        "raw_type_index": 4 if character_id is not None else 1,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": typed_identity,
    }


def _saved_scope(
    name: str, type_key: str, *, character_id: int | None = None
) -> dict[str, object]:
    return {
        "name": name,
        "name_identifier": len(name) + 100,
        "scope": _scope(type_key, character_id=character_id),
    }


def _neutral_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": EVENT_INSTANCE_ID,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "death_management.1000",
        "calculated_event_id": 5_121_000,
        "runtime_stats_ordinal": 8_799,
        "root_scope": _scope("character", character_id=PLAYER_ID),
        "saved_scopes": [
            _saved_scope("new_memory", "character_memory"),
            _saved_scope(
                "surviving_consort", "character", character_id=PLAYER_ID
            ),
            _saved_scope(
                "dead_character", "character", character_id=DEAD_SPOUSE_ID
            ),
            _saved_scope("deceased_character_stress", "value"),
            _saved_scope("realm", "landed_title"),
        ],
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 1,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "I hope you found peace.",
                "unavailable_reason": "",
                "effect_indicators": {
                    "status": "available",
                    "coverage": (
                        "played-character-event-icon-indicators-1.19.0.6-v1"
                    ),
                    "complete_effect_set": False,
                    "rows": [
                        {
                            "kind": "stress",
                            "direction": "increase",
                            "magnitude": {"status": "unavailable"},
                            "affected_by_trait": False,
                            "critical": False,
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
        context,
        played_character_id=PLAYER_ID,
        snapshot_option_count=3,
    )


class DeathManagement1000PolicyTests(unittest.TestCase):
    def test_r849_neutral_projection_selects_authored_option_two(self) -> None:
        result = _recommend(_neutral_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 2)
        self.assertEqual(result["selected_native_option_index"], 1)
        self.assertEqual(result["selected_rendered_index"], 0)
        self.assertEqual(result["option_projection_source"], "base_contract")
        self.assertEqual(result["failed_checks"], [])
        self.assertFalse(result["semantic_decision_ready"])
        self.assertFalse(result["semantic_optimal"])

    def test_source_bound_projection_does_not_authorize_an_unknown_event(self) -> None:
        context = _neutral_context()
        context["event_definition_key"] = "unknown_single_option.1"

        result = _recommend(context)

        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(
            result["unavailable_reason"],
            "event_definition_key_not_registered",
        )
        self.assertIsNone(result["selected_option_number"])

    def test_liked_and_disliked_templates_stay_coupled_to_their_native_rows(
        self,
    ) -> None:
        cases = (("like", 0, 1, 0), ("dislike", 2, 3, 1))
        for scope_name, native_index, option_number, variant_index in cases:
            with self.subTest(scope_name=scope_name):
                context = _neutral_context()
                context["saved_scopes"].append(
                    _saved_scope(scope_name, "flag")
                )
                context["options"][0]["native_option_index"] = native_index

                result = _recommend(context)

                self.assertEqual(result["status"], "recommended")
                self.assertEqual(result["selected_option_number"], option_number)
                self.assertEqual(
                    result["selected_native_option_index"], native_index
                )
                self.assertEqual(
                    result["matched_option_variant_index"], variant_index
                )
                self.assertEqual(result["failed_checks"], [])

    def test_projection_rejects_nonsole_hidden_or_disabled_rows(self) -> None:
        cases: tuple[tuple[str, list[dict[str, object]], str], ...] = (
            (
                "second rendered row",
                [
                    copy.deepcopy(_neutral_context()["options"][0]),
                    {
                        **copy.deepcopy(_neutral_context()["options"][0]),
                        "rendered_index": 1,
                        "native_option_index": 0,
                        "shown": False,
                        "enabled": False,
                    },
                ],
                "option_variant_projection",
            ),
            (
                "hidden sole row",
                [{**copy.deepcopy(_neutral_context()["options"][0]), "shown": False}],
                "option_variant_projection",
            ),
            (
                "disabled sole row",
                [{**copy.deepcopy(_neutral_context()["options"][0]), "enabled": False}],
                "option_variant_projection",
            ),
        )
        for label, options, failed_check in cases:
            with self.subTest(label=label):
                context = _neutral_context()
                context["options"] = options

                result = _recommend(context)

                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_projection_rejects_index_and_template_semantic_drift(self) -> None:
        cases: tuple[tuple[str, dict[str, object], str], ...] = (
            (
                "unknown authored index",
                {"native_option_index": 7},
                "option_variant_projection",
            ),
            (
                "liked option without like template scope",
                {"native_option_index": 0},
                "saved_scope_names_exact",
            ),
        )
        for label, option_changes, failed_check in cases:
            with self.subTest(label=label):
                context = _neutral_context()
                context["options"][0].update(option_changes)

                result = _recommend(context)

                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_native_option_index"])

    def test_planner_uses_typed_registry_action_despite_generic_readiness_false(
        self,
    ) -> None:
        context = _neutral_context()
        result = {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": NATIVE_REVISION,
            "current_event_instance_id": EVENT_INSTANCE_ID,
            "date_raw": DATE_RAW,
            "current_event_window_context": copy.deepcopy(context),
            "queried_snapshot_id": "native:62",
            "queried_revision": 63,
            "queried_native_revision": NATIVE_REVISION,
        }
        snapshot = {
            "snapshot_id": "native:62",
            "revision": 63,
            "native_revision": NATIVE_REVISION,
            "date_raw": DATE_RAW,
            "paused": True,
            "backend_id": "native-headless",
            "played_character": {
                "character_id": PLAYER_ID,
                "alive": True,
                "stress_points": 0,
            },
            "active_event": {
                "instance_id": EVENT_INSTANCE_ID,
                "option_count": 3,
            },
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
                "select-event-option-2",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-2")
        self.assertEqual(plan["event_decision"]["status"], "recommended")
        self.assertEqual(
            plan["active_event"]["selected_native_option_index"], 1
        )
        self.assertFalse(plan["active_event"]["semantic_decision_ready"])
        self.assertNotIn("degraded_decision", plan["active_event"])


if __name__ == "__main__":
    unittest.main()
