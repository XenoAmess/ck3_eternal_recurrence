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
from xar_autoplayer.vanilla_events.outcome import (  # noqa: E402
    evaluate_registered_event_material_postcondition_v1,
    plan_registered_event_material_postcondition_v1,
)
from xar_autoplayer.vanilla_events.policy import (  # noqa: E402
    recommend_registered_vanilla_event_option_v1,
)


PLAYER_ID = 31_853
THEOCRAT_ID = 56_125
EVENT_INSTANCE_ID = 4
DATE_RAW = 53_223_216
NATIVE_REVISION = 63


def _typed_identity(type_key: str, character_id: int | None) -> dict[str, object]:
    if type_key == "character" and character_id is not None:
        return {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "status": "unavailable",
        "reason": "generic_scope_payload_identity_not_closed",
    }


def _scope(type_key: str, *, character_id: int | None = None) -> dict[str, object]:
    raw_type_index = {
        "flag": 3,
        "character": 4,
        "landed_title": 5,
    }[type_key]
    return {
        "status": "available",
        "raw_type_index": raw_type_index,
        "type_key": type_key,
        "subtype": 0,
        "typed_identity": _typed_identity(type_key, character_id),
    }


def _saved_scope(
    name: str,
    type_key: str,
    *,
    character_id: int | None = None,
) -> dict[str, object]:
    return {
        "name": name,
        "name_identifier": {
            "sinful_theocrat": 19_434,
            "scandal_type": 19_443,
            "dummy_servant_gender": 21_917,
            "dummy_clergy_gender": 18_449,
            "scoped_primary_title": 19_529,
        }[name],
        "scope": _scope(type_key, character_id=character_id),
    }


def _option(rendered_index: int, native_index: int) -> dict[str, object]:
    rows = (
        [{
            "kind": "stress",
            "direction": "increase",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": True,
            "critical": False,
        }]
        if native_index == 2
        else []
    )
    return {
        "rendered_index": rendered_index,
        "native_option_index": native_index,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "resolved_name": f"fervor.1002 option {native_index}",
        "unavailable_reason": "",
        "effect_indicators": {
            "status": "available",
            "coverage": "played-character-event-icon-indicators-1.19.0.6-v1",
            "complete_effect_set": False,
            "rows": rows,
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
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": EVENT_INSTANCE_ID,
        "window_match_count": 1,
        "unavailable_reason": None,
        "event_definition_key": "fervor.1002",
        "calculated_event_id": 2_801_002,
        "runtime_stats_ordinal": 3_678,
        "root_scope": _scope("character", character_id=PLAYER_ID),
        "saved_scopes": [
            _saved_scope(
                "sinful_theocrat", "character", character_id=THEOCRAT_ID
            ),
            _saved_scope("scandal_type", "flag"),
            _saved_scope(
                "dummy_servant_gender", "character", character_id=1
            ),
            _saved_scope(
                "dummy_clergy_gender", "character", character_id=1
            ),
            _saved_scope("scoped_primary_title", "landed_title"),
        ],
        "options": [_option(index, index) for index in range(3)],
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


def _query_history(context: dict[str, object]) -> list[dict[str, object]]:
    return [{
        "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "ok": True,
        "result": {
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
        },
    }]


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": f"native:{NATIVE_REVISION}",
        "revision": NATIVE_REVISION + 1,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "backend_id": "native-headless",
        "played_character": {
            "character_id": PLAYER_ID,
            "alive": True,
            "stress_points": 20,
        },
        "active_event": {
            "instance_id": EVENT_INSTANCE_ID,
            "option_count": 3,
        },
    }


class Fervor1002PolicyTests(unittest.TestCase):
    def test_r860_projection_selects_source_reviewed_silence(self) -> None:
        result = _recommend(_context())

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_option_number"], 3)
        self.assertEqual(result["selected_native_option_index"], 2)
        self.assertEqual(result["selected_rendered_index"], 2)
        self.assertEqual(result["matched_option_variant_index"], None)
        self.assertEqual(result["failed_checks"], [])
        self.assertTrue(result["campaign_utility_ready"])
        self.assertEqual(
            result["choice_effect_profile"]["observable_postcondition"],
            {
                "metric": "played_character.stress_points",
                "expected_relation": "non_decreasing",
                "material_change_required_for_evidence": True,
            },
        )

    def test_portable_repeat_shape_does_not_bind_campaign_ids_or_date(self) -> None:
        context = _context()
        context["date_raw"] = DATE_RAW + 1461 * 24
        context["root_scope"] = _scope("character", character_id=40_001)
        context["saved_scopes"][0] = _saved_scope(
            "sinful_theocrat", "character", character_id=40_002
        )

        result = recommend_registered_vanilla_event_option_v1(
            context,
            played_character_id=40_001,
            snapshot_option_count=3,
        )

        self.assertEqual(result["status"], "recommended")
        self.assertEqual(result["selected_native_option_index"], 2)

    def test_identity_scope_and_option_drift_remain_fail_closed(self) -> None:
        wrong_root = _context()
        wrong_root["root_scope"] = _scope("character", character_id=40_001)
        theocrat_is_root = _context()
        theocrat_is_root["saved_scopes"][0] = _saved_scope(
            "sinful_theocrat", "character", character_id=PLAYER_ID
        )
        missing_scope = _context()
        missing_scope["saved_scopes"].pop()
        wrong_scope_type = _context()
        wrong_scope_type["saved_scopes"][1] = _saved_scope(
            "scandal_type", "landed_title"
        )
        reordered_options = _context()
        reordered_options["options"] = [_option(0, 1), _option(1, 0), _option(2, 2)]
        selected_disabled = _context()
        selected_disabled["options"][2]["enabled"] = False
        hidden_option = _context()
        hidden_option["options"][0]["shown"] = False
        fallback_option = _context()
        fallback_option["options"][1]["fallback"] = True

        cases = (
            ("wrong root", wrong_root, "root_character_id"),
            (
                "theocrat is root",
                theocrat_is_root,
                "scope:sinful_theocrat:unique_character_excludes",
            ),
            ("missing scope", missing_scope, "saved_scope_count"),
            ("wrong scope type", wrong_scope_type, "scope:scandal_type:type"),
            ("reordered options", reordered_options, "native_option_indices_exact"),
            ("selected disabled", selected_disabled, "option:2:projection"),
            ("hidden option", hidden_option, "option:0:projection"),
            ("fallback option", fallback_option, "option:1:projection"),
        )

        for label, context, failed_check in cases:
            with self.subTest(label=label):
                result = _recommend(context)
                self.assertEqual(result["status"], "blocked")
                self.assertIn(failed_check, result["failed_checks"])
                self.assertIsNone(result["selected_option_number"])

    def test_different_event_identity_is_not_registered(self) -> None:
        context = _context()
        context["event_definition_key"] = "fervor.1003"

        result = _recommend(context)

        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(result["failed_checks"], [])
        self.assertIsNone(result["selected_option_number"])

    def test_planner_uses_typed_option_three_and_material_contract(self) -> None:
        plan = choose_one_life_turn(
            _query_history(_context()),
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-3",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-3")
        self.assertEqual(plan["event_decision"]["status"], "recommended")
        self.assertEqual(
            plan["active_event"]["selected_native_option_index"], 2
        )
        self.assertEqual(
            plan["event_material_postcondition"],
            {
                "schema": "xar.ck3.vanilla-event-material-postcondition",
                "schema_version": 1,
                "event_definition_key": "fervor.1002",
                "selected_option_number": 3,
                "selected_native_option_index": 2,
                "metric": "played_character.stress_points",
                "expected_relation": "non_decreasing",
                "material_change_required_for_evidence": True,
                "status": "ready",
                "starting_snapshot_id": "native:63",
                "starting_revision": 64,
                "character_id": PLAYER_ID,
                "starting_value": 20,
                "unavailable_reason": None,
            },
        )

    def test_contract_drift_blocks_instead_of_using_degraded_first_option(self) -> None:
        context = _context()
        context["options"][2]["enabled"] = False
        plan = choose_one_life_turn(
            _query_history(context),
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-2",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_contract_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["event_decision"]["status"], "blocked")

    def test_material_postcondition_is_bound_and_evaluated(self) -> None:
        decision = _recommend(_context())
        expectation = plan_registered_event_material_postcondition_v1(
            decision,
            _snapshot()["played_character"],
            snapshot_id="native:63",
            revision=64,
        )
        self.assertIsNotNone(expectation)
        selection = {
            "postcondition_verified": True,
            "starting_snapshot_id": "native:63",
            "starting_revision": 64,
            "starting_played_character_stress": {
                "status": "available",
                "character_id": PLAYER_ID,
                "stress_points": 20,
            },
            "ending_played_character_stress": {
                "status": "available",
                "character_id": PLAYER_ID,
                "stress_points": 40,
            },
        }

        verified = evaluate_registered_event_material_postcondition_v1(
            expectation, selection
        )
        self.assertEqual(verified["status"], "verified_change")
        self.assertTrue(verified["relation_satisfied"])
        self.assertEqual(verified["delta"], 20)

        selection["ending_played_character_stress"]["stress_points"] = 10
        failed = evaluate_registered_event_material_postcondition_v1(
            expectation, selection
        )
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["unavailable_reason"], "stress_decreased")


if __name__ == "__main__":
    unittest.main()
