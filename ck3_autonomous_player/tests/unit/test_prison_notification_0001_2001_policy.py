from __future__ import annotations

import copy
import unittest
from unittest import mock

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1
from xar_autoplayer.vanilla_events.source_index import (
    query_vanilla_event_source_provenance_v1,
)


PLAYER = 36_403
CAPTOR = 34_676


def _scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available", "kind": "character",
            "character_id": character_id,
        },
    }


def _saved(name: str, scope: dict[str, object]) -> dict[str, object]:
    return {
        "name": name,
        "name_identifier": sum((index + 1) * ord(char) for index, char in enumerate(name)),
        "scope": scope,
    }


def _opaque(type_key: str, raw_type_index: int) -> dict[str, object]:
    return {
        "status": "available", "raw_type_index": raw_type_index,
        "type_key": type_key, "subtype": 0,
        "typed_identity": {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        },
    }


def _context(key: str, *, extra: bool = True) -> dict[str, object]:
    scopes = [
        _saved("prisoner", _scope(PLAYER)),
        _saved("imprisoner", _scope(CAPTOR)),
        _saved("bg_override_char", _scope(CAPTOR)),
        _saved("this_player", _scope(PLAYER)),
    ]
    if extra:
        scopes.append(_saved("new_memory", _opaque("character_memory", 6)))
    if extra and key.endswith(".0001"):
        scopes.extend([
            _saved("prisoner_memory", _scope(PLAYER)),
            _saved("other_house", _opaque("dynasty_house", 7)),
            _saved("char", _scope(CAPTOR)),
            _saved("target_char", _scope(PLAYER)),
            _saved("steps", _opaque("value", 8)),
        ])
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": key,
        "current_event_instance_id": 24 if key.endswith(".0001") else 25,
        "snapshot_revision": 100,
        "date_raw": 53_369_112,
        "unavailable_reason": None,
        "calculated_event_id": 1,
        "runtime_stats_ordinal": 1,
        "root_scope": _scope(PLAYER),
        "saved_scopes": scopes,
        "options": [{
            "rendered_index": 0,
            "native_option_index": 0,
            "shown": True,
            "enabled": True,
            "fallback": False,
            "cancel": False,
            "resolved_name": "acknowledge",
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
        }],
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
        context, played_character_id=PLAYER, snapshot_option_count=1,
    )


def _plan(context: dict[str, object]) -> dict[str, object]:
    history = [{
        "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "ok": True,
        "result": {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": 100,
            "current_event_instance_id": context["current_event_instance_id"],
            "date_raw": context["date_raw"],
            "current_event_window_context": context,
            "queried_snapshot_id": "native:100",
            "queried_revision": 101,
            "queried_native_revision": 100,
        },
    }]
    snapshot = {
        "snapshot_id": "native:100",
        "revision": 101,
        "native_revision": 100,
        "date_raw": context["date_raw"],
        "paused": True,
        "backend_id": "native-headless",
        "played_character": {"character_id": PLAYER, "alive": True},
        "active_event": {
            "instance_id": context["current_event_instance_id"],
            "option_count": 1,
        },
    }
    return choose_one_life_turn(
        history, snapshot=snapshot,
        action_steps={
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "select-event-option-1",
        },
    )


class PrisonNotificationPolicyTests(unittest.TestCase):
    def test_exact_stock_index_and_two_source_bound_acknowledgements(self) -> None:
        for key, definition_line in (
            ("prison_notification.0001", 6),
            ("prison_notification.2001", 269),
        ):
            with self.subTest(key=key):
                source = query_vanilla_event_source_provenance_v1(
                    key, "1.19.0.6"
                )
                self.assertEqual(source["status"], "available")
                self.assertEqual(source["definition"]["line"], definition_line)
                for extra in (False, True):
                    decision = _recommend(_context(key, extra=extra))
                    self.assertEqual(decision["status"], "recommended")
                    self.assertEqual(decision["selected_native_option_index"], 0)
                    self.assertEqual(decision["failed_checks"], [])

    def test_production_strategy_uses_registry_not_generic_fallback(self) -> None:
        for key in ("prison_notification.0001", "prison_notification.2001"):
            with self.subTest(key=key):
                plan = _plan(_context(key))
                self.assertEqual(plan["phase"], "active_event_registry_choice")
                self.assertEqual(plan["selected_step"], "select-event-option-1")
                self.assertEqual(plan["event_decision"]["status"], "recommended")
                self.assertNotIn("event_material_postcondition", plan)

    def test_role_or_option_drift_blocks_exact_key(self) -> None:
        key = "prison_notification.0001"
        for mutation, failed in (
            (lambda c: c["saved_scopes"][0]["scope"]["typed_identity"].update(character_id=CAPTOR), "scope:prisoner:character_id"),
            (lambda c: c["saved_scopes"][1]["scope"]["typed_identity"].update(character_id=PLAYER), "scope:imprisoner:differs_from"),
            (lambda c: c["saved_scopes"].pop(2), "r0109_authored_roles_present"),
            (lambda c: c["saved_scopes"].append(copy.deepcopy(c["saved_scopes"][0])), "r0109_all_scope_rows_named_unique"),
            (lambda c: c["options"][0].update(native_option_index=1), "native_option_indices_exact"),
            (lambda c: c["options"][0].update(enabled=False), "option:0:projection"),
        ):
            with self.subTest(failed=failed):
                context = _context(key)
                mutation(context)
                decision = _recommend(context)
                self.assertEqual(decision["status"], "blocked")
                self.assertIn(failed, decision["failed_checks"])
                plan = _plan(context)
                self.assertEqual(
                    plan["phase"],
                    "active_event_window_query"
                    if failed == "r0109_all_scope_rows_named_unique"
                    else "active_event_registry_contract_blocked",
                )
                if failed == "r0109_all_scope_rows_named_unique":
                    self.assertEqual(
                        plan["selected_step"],
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                    )
                else:
                    self.assertIsNone(plan["selected_step"])

    def test_source_hash_drift_blocks_even_sole_option(self) -> None:
        key = "prison_notification.2001"
        knowledge = query_vanilla_event_knowledge_v1(key)
        knowledge["analysis"]["source_sha256"][
            "events/prison_events/prison_notification_events.txt"
        ] = "0" * 64
        with mock.patch(
            "xar_autoplayer.vanilla_events.policy.query_vanilla_event_knowledge_v1",
            return_value=knowledge,
        ):
            decision = _recommend(_context(key))
        self.assertEqual(decision["status"], "blocked")
        self.assertIn(
            "r0109_exact_prison_notification_source", decision["failed_checks"]
        )


if __name__ == "__main__":
    unittest.main()
