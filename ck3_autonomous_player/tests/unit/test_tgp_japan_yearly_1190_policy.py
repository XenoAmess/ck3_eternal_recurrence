from __future__ import annotations

import copy
import unittest
from unittest import mock

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.outcome import (
    evaluate_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)
from xar_autoplayer.vanilla_events.registry import (
    query_vanilla_event_knowledge_v1,
)
from xar_autoplayer.vanilla_events.source_index import (
    query_vanilla_event_source_provenance_v1,
)


PLAYER = 36_403
EVENT_KEY = "tgp_japan_yearly_events.1190"


def _option(rendered: int, native: int, direction: str) -> dict[str, object]:
    return {
        "rendered_index": rendered,
        "native_option_index": native,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": "test option",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
            "complete_effect_set": False,
            "rows": [{
                "kind": "stress",
                "direction": direction,
                "magnitude": {"status": "unavailable"},
                "affected_by_trait": native == 1,
                "critical": False,
            }],
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
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "current_event_instance_id": 15,
        "snapshot_revision": 22,
        "date_raw": 53_314_008,
        "unavailable_reason": None,
        "calculated_event_id": 1,
        "runtime_stats_ordinal": 1,
        "provenance": {
            "root": "module+0x570F7B8->+0x10",
            "idler_vtable_rva": "0x40B1D30",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.19.0.6-native-event-window-v1",
        },
        "root_scope": {
            "status": "available",
            "raw_type_index": 4,
            "type_key": "character",
            "subtype": 0,
            "typed_identity": {
                "status": "available",
                "kind": "character",
                "character_id": PLAYER,
            },
        },
        "saved_scopes": [],
        "options": [
            _option(0, 0, "increase"),
            _option(1, 1, "decrease"),
            _option(2, 2, "decrease"),
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
    }


def _plan(
    context: dict[str, object], *, prestige_raw: int | None
) -> dict[str, object]:
    history = [{
        "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "ok": True,
        "result": {
            "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "accepted": True,
            "status": "available",
            "snapshot_revision": 22,
            "current_event_instance_id": 15,
            "date_raw": 53_314_008,
            "current_event_window_context": context,
            "queried_snapshot_id": "native:22",
            "queried_revision": 23,
            "queried_native_revision": 22,
        },
    }]
    snapshot = {
        "snapshot_id": "native:22",
        "revision": 23,
        "native_revision": 22,
        "date_raw": 53_314_008,
        "paused": True,
        "backend_id": "native-headless",
        "played_character": {
            "character_id": PLAYER,
            "alive": True,
            "stress_points": 0,
        },
        "played_character_prestige": (
            {"raw": prestige_raw, "scale": 100_000}
            if prestige_raw is not None else None
        ),
        "active_event": {"instance_id": 15, "option_count": 3},
    }
    return choose_one_life_turn(
        history,
        snapshot=snapshot,
        action_steps={
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            "select-event-option-2",
        },
    )


class TgpJapanYearly1190PolicyTests(unittest.TestCase):
    def test_portable_exact_source_has_both_yearly_callers(self) -> None:
        source = query_vanilla_event_source_provenance_v1(EVENT_KEY, "1.19.0.6")
        self.assertEqual(source["status"], "available")
        self.assertEqual(source["definition"]["line"], 4701)
        self.assertEqual(
            {
                (row["relative_path"], row["line"])
                for row in source["caller_candidates"]
            },
            {
                ("common/on_action/dlc/tgp/tgp_japan_yearly_on_actions.txt", 41),
                ("common/on_action/yearly_on_actions.txt", 3797),
            },
        )

    def test_registered_exact_source_and_native_one_choice(self) -> None:
        knowledge = query_vanilla_event_knowledge_v1(EVENT_KEY)
        self.assertEqual(knowledge["status"], "available")
        self.assertEqual(
            knowledge["analysis"]["source_sha256"]["events/dlc/tgp/tgp_japan_yearly_events_ariana.txt"],
            "B9F5799465E9B83B16C97086BC74F43ECD3949680AE1A78C081ED44ECD9B5FD6",
        )
        decision = recommend_registered_vanilla_event_option_v1(
            _context(), played_character_id=PLAYER, snapshot_option_count=3
        )
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_option_number"], 2)
        self.assertEqual(decision["selected_native_option_index"], 1)
        self.assertEqual(decision["failed_checks"], [])
        self.assertEqual(
            decision["choice_effect_profile"]["observable_postcondition"],
            {
                "metric": "played_character_prestige.raw",
                "expected_relation": "strictly_decreasing",
                "material_change_required_for_evidence": True,
            },
        )

    def test_wrong_indicator_scope_option_or_source_blocks(self) -> None:
        wrong_indicator = _context()
        wrong_indicator["options"][1]["effect_indicators"]["rows"][0][
            "direction"
        ] = "increase"
        extra_scope = _context()
        extra_scope["saved_scopes"] = [{"name": "unknown", "scope": {}}]
        wrong_options = _context()
        wrong_options["options"][0]["native_option_index"] = 3
        for context, failed in (
            (wrong_indicator, "r0100_selected_stress_decrease_indicator"),
            (extra_scope, "saved_scope_names_exact"),
            (wrong_options, "native_option_indices_exact"),
        ):
            with self.subTest(failed=failed):
                decision = recommend_registered_vanilla_event_option_v1(
                    context, played_character_id=PLAYER,
                    snapshot_option_count=3,
                )
                self.assertEqual(decision["status"], "blocked")
                self.assertIn(failed, decision["failed_checks"])
        knowledge = query_vanilla_event_knowledge_v1(EVENT_KEY)
        knowledge["analysis"]["source_sha256"]["events/dlc/tgp/tgp_japan_yearly_events_ariana.txt"] = "0" * 64
        with mock.patch(
            "xar_autoplayer.vanilla_events.policy.query_vanilla_event_knowledge_v1",
            return_value=knowledge,
        ):
            decision = recommend_registered_vanilla_event_option_v1(
                _context(), played_character_id=PLAYER, snapshot_option_count=3
            )
        self.assertEqual(decision["status"], "blocked")
        self.assertIn("r0100_exact_source", decision["failed_checks"])

    def test_formal_planner_requires_prestige_budget_and_readback(self) -> None:
        plan = _plan(_context(), prestige_raw=10_000_000)
        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-2")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 1)
        expectation = plan["event_material_postcondition"]
        self.assertEqual(expectation["status"], "ready")
        self.assertEqual(expectation["starting_value"], 10_000_000)
        for raw in (7_499_999, None):
            with self.subTest(raw=raw):
                blocked = _plan(_context(), prestige_raw=raw)
                self.assertEqual(
                    blocked["phase"],
                    "active_event_registry_material_observation_blocked",
                )
                self.assertIsNone(blocked["selected_step"])

    def test_independent_same_character_prestige_material_comparator(self) -> None:
        expectation = _plan(
            _context(), prestige_raw=10_000_000
        )["event_material_postcondition"]
        selection = {
            "postcondition_verified": True,
            "old_event_instance_id": 15,
            "new_event_instance_id": None,
            "starting_snapshot_id": "native:22",
            "starting_revision": 23,
            "ending_snapshot_id": "native:23",
            "ending_revision": 24,
            "starting_played_character_prestige": {
                "status": "available", "character_id": PLAYER,
                "prestige_raw": 10_000_000, "scale": 100_000,
            },
            "ending_played_character_prestige": {
                "status": "available", "character_id": PLAYER,
                "prestige_raw": 2_500_000, "scale": 100_000,
            },
        }
        result = evaluate_registered_event_material_postcondition_v1(
            expectation, selection
        )
        self.assertEqual(result["status"], "verified_change")
        self.assertEqual(result["delta"], -7_500_000)
        no_change = copy.deepcopy(selection)
        no_change["ending_played_character_prestige"]["prestige_raw"] = 10_000_000
        self.assertEqual(
            evaluate_registered_event_material_postcondition_v1(
                expectation, no_change
            )["unavailable_reason"],
            "prestige_not_decreased",
        )
        drift = copy.deepcopy(selection)
        drift["ending_played_character_prestige"]["character_id"] = PLAYER + 1
        self.assertEqual(
            evaluate_registered_event_material_postcondition_v1(
                expectation, drift
            )["status"],
            "failed",
        )


if __name__ == "__main__":
    unittest.main()
