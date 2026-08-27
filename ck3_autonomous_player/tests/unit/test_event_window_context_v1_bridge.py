from __future__ import annotations

import copy
import unittest

from xar_autoplayer.bridge.event_window_context_contract import (
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
    normalize_current_event_window_context_v1,
)
from xar_autoplayer.bridge.driver import CallbackGameplayDriver
from xar_autoplayer.bridge.mcp_server import (
    _ck3_query_current_event_window_context_v1,
)
from xar_autoplayer.bridge.native_driver import _action_steps
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.strategy import choose_one_life_turn


EVENT_ID = 0x01000029
NATIVE_REVISION = 17
DATE_RAW = 741_221
EVENT_DEFINITION_KEY = "xar_test.0001"
CALCULATED_EVENT_ID = -712_345
RUNTIME_STATS_ORDINAL = 37
CHARACTER_ID = 42
SAVED_ROOT_NAME_IDENTIFIER = -2_130_706_232


def _scope(
    *,
    raw_type_index: int = 4,
    type_key: str = "character",
    subtype: int = 0,
    character_id: int | None = CHARACTER_ID,
) -> dict[str, object]:
    identity: dict[str, object]
    if character_id is not None:
        identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    else:
        identity = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
    return {
        "status": "available",
        "raw_type_index": raw_type_index,
        "type_key": type_key,
        "subtype": subtype,
        "typed_identity": identity,
    }


def _indicator_rows() -> list[dict[str, object]]:
    return [
        {
            "kind": "trait",
            "operation": "add",
            "trait": {"status": "available", "native_id": 123, "key": "brave"},
        },
        {
            "kind": "stress",
            "direction": "decrease",
            "magnitude": {"status": "unavailable"},
            "affected_by_trait": True,
            "critical": False,
        },
        {
            "kind": "death",
            "subject": "played_character",
            "direction": "not_applicable",
        },
        {
            "kind": "scheme",
            "subject": "played_character",
            "operation": "start",
            "direction": "not_applicable",
            "scheme": {"status": "available", "scheme_type_key": "murder"},
        },
        {"kind": "unknown", "raw_kind": 17},
    ]


def _frame(status: str = "available") -> dict[str, object]:
    available = status == "available"
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": status,
        "snapshot_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "current_event_instance_id": EVENT_ID,
        "window_match_count": 1 if available else 0,
        "unavailable_reason": None if available else "event_window_not_materialized",
        "event_definition_key": EVENT_DEFINITION_KEY if available else None,
        "calculated_event_id": CALCULATED_EVENT_ID if available else None,
        "runtime_stats_ordinal": (
            RUNTIME_STATS_ORDINAL if available else None
        ),
        "root_scope": _scope() if available else None,
        "saved_scopes": [
            {
                "name": "xar_scope_root_control",
                "name_identifier": SAVED_ROOT_NAME_IDENTIFIER,
                "scope": _scope(subtype=2),
            },
            {
                "name": "province_control",
                "name_identifier": 201,
                "scope": _scope(
                    raw_type_index=3,
                    type_key="province",
                    subtype=1,
                    character_id=None,
                ),
            },
        ] if available else None,
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 3,
                "shown": True,
                "enabled": False,
                "fallback": True,
                "cancel": True,
                "resolved_name": "Wait.",
                "unavailable_reason": "Not today",
                "effect_indicators": {
                    "status": "available",
                    "coverage": (
                        "played-character-event-icon-indicators-1.19.0.6-v1"
                    ),
                    "complete_effect_set": False,
                    "rows": _indicator_rows(),
                },
                "effect_preview": {
                    "status": "unavailable",
                    "reason": "indicator_subset_has_no_completeness_signal",
                },
                "resource_deltas": {"status": "unavailable"},
                "relationship_deltas": {"status": "unavailable"},
            }
        ] if available else None,
        "readiness": {
            "event_definition_identity_ready": available,
            "root_scope_ready": available,
            "saved_scopes_ready": available,
            "option_presentation_ready": available,
            "effect_indicators_ready": available,
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


def _snapshot() -> dict[str, object]:
    return {
        "snapshot_id": "snapshot-9",
        "revision": 9,
        "native_revision": NATIVE_REVISION,
        "date_raw": DATE_RAW,
        "paused": True,
        "backend_id": "native-headless",
        "active_event": {"instance_id": EVENT_ID, "option_count": 4},
    }


def _query_result(
    frame: dict[str, object] | None = None,
) -> dict[str, object]:
    materialized = copy.deepcopy(frame if frame is not None else _frame())
    mirrors = {
        key: copy.deepcopy(materialized[key])
        for key in (
            "schema",
            "schema_version",
            "date_raw",
            "current_event_instance_id",
            "window_match_count",
            "unavailable_reason",
            "event_definition_key",
            "calculated_event_id",
            "runtime_stats_ordinal",
            "root_scope",
            "saved_scopes",
            "options",
            "readiness",
            "provenance",
        )
    }
    return {
        "step": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "accepted": True,
        "status": materialized["status"],
        "query_sequence": 4,
        "snapshot_revision": NATIVE_REVISION,
        "current_event_window_context": materialized,
        "backend_id": "native-headless",
        "current_event_window_context_ready": materialized["readiness"][
            "option_presentation_ready"
        ],
        "current_event_effect_indicators_ready": materialized["readiness"][
            "effect_indicators_ready"
        ],
        "queried_snapshot_id": "snapshot-9",
        "queried_revision": 9,
        "queried_native_revision": NATIVE_REVISION,
        **mirrors,
    }


def _query_history(
    frame: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "command": QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        "ok": True,
        "result": _query_result(frame),
    }


class _Driver:
    def __init__(self) -> None:
        self.frame = _frame()

    def take_snapshot(self) -> dict[str, object]:
        return copy.deepcopy(_snapshot())

    def capabilities(self) -> dict[str, object]:
        return {
            "bridge_capabilities": [
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            ],
            "action_steps": [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP],
        }

    def execute_step(
        self, step: str, *, expected_revision: int
    ) -> dict[str, object]:
        assert step == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        assert expected_revision == 9
        return _query_result(self.frame)


class EventWindowContractTests(unittest.TestCase):
    def test_available_frame_is_strict_and_detached(self) -> None:
        original = _frame()
        normalized = normalize_current_event_window_context_v1(
            original,
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertEqual(normalized, original)
        normalized["options"][0]["resolved_name"] = "changed"
        self.assertEqual(original["options"][0]["resolved_name"], "Wait.")
        self.assertEqual(normalized["event_definition_key"], EVENT_DEFINITION_KEY)
        self.assertEqual(normalized["calculated_event_id"], CALCULATED_EVENT_ID)
        self.assertEqual(
            normalized["runtime_stats_ordinal"], RUNTIME_STATS_ORDINAL
        )
        self.assertEqual(
            normalized["root_scope"]["typed_identity"]["character_id"],
            CHARACTER_ID,
        )
        self.assertEqual(
            normalized["saved_scopes"][1]["scope"]["typed_identity"],
            {
                "status": "unavailable",
                "reason": "generic_scope_payload_identity_not_closed",
            },
        )

    def test_root_and_saved_scope_inventory_is_strict(self) -> None:
        normalized = normalize_current_event_window_context_v1(
            _frame(),
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertTrue(normalized["readiness"]["root_scope_ready"])
        self.assertTrue(normalized["readiness"]["saved_scopes_ready"])
        self.assertEqual(
            normalized["saved_scopes"][0]["name"],
            "xar_scope_root_control",
        )
        self.assertEqual(
            normalized["saved_scopes"][0]["name_identifier"],
            SAVED_ROOT_NAME_IDENTIFIER,
        )

        mutations: list[dict[str, object]] = []
        missing_root = _frame()
        missing_root["root_scope"] = None
        mutations.append(missing_root)
        wrong_character_index = _frame()
        wrong_character_index["root_scope"]["raw_type_index"] = 3
        mutations.append(wrong_character_index)
        stale_character = _frame()
        stale_character["root_scope"]["typed_identity"]["character_id"] = 0
        mutations.append(stale_character)
        fabricated_noncharacter = _frame()
        fabricated_noncharacter["saved_scopes"][1]["scope"][
            "typed_identity"
        ] = {
            "status": "available",
            "kind": "character",
            "character_id": CHARACTER_ID,
        }
        mutations.append(fabricated_noncharacter)
        duplicate_name = _frame()
        duplicate_name["saved_scopes"][1]["name"] = duplicate_name[
            "saved_scopes"
        ][0]["name"]
        mutations.append(duplicate_name)
        duplicate_identifier = _frame()
        duplicate_identifier["saved_scopes"][1][
            "name_identifier"
        ] = duplicate_identifier["saved_scopes"][0]["name_identifier"]
        mutations.append(duplicate_identifier)
        below_signed_int32 = _frame()
        below_signed_int32["saved_scopes"][0]["name_identifier"] = -(
            2**31
        ) - 1
        mutations.append(below_signed_int32)
        oversized = _frame()
        oversized["saved_scopes"] = [
            copy.deepcopy(oversized["saved_scopes"][0])
            for _ in range(1_025)
        ]
        mutations.append(oversized)
        unready = _frame()
        unready["readiness"]["saved_scopes_ready"] = False
        mutations.append(unready)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    normalize_current_event_window_context_v1(
                        mutation,
                        expected_event_instance_id=EVENT_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_unavailable_scope_inventory_remains_null_and_unready(self) -> None:
        unavailable = _frame("unavailable")
        normalized = normalize_current_event_window_context_v1(
            unavailable,
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertIsNone(normalized["root_scope"])
        self.assertIsNone(normalized["saved_scopes"])
        self.assertFalse(normalized["readiness"]["root_scope_ready"])
        self.assertFalse(normalized["readiness"]["saved_scopes_ready"])

        leaked_root = _frame("unavailable")
        leaked_root["root_scope"] = _scope()
        leaked_saved = _frame("unavailable")
        leaked_saved["saved_scopes"] = []
        falsely_ready = _frame("unavailable")
        falsely_ready["readiness"]["root_scope_ready"] = True
        for mutation in (leaked_root, leaked_saved, falsely_ready):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    normalize_current_event_window_context_v1(
                        mutation,
                        expected_event_instance_id=EVENT_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_multiple_authored_cancel_flags_are_preserved(self) -> None:
        original = _frame()
        second = copy.deepcopy(original["options"][0])
        second.update(
            {
                "rendered_index": 1,
                "native_option_index": 7,
                "cancel": True,
            }
        )
        original["options"].append(second)

        normalized = normalize_current_event_window_context_v1(
            original,
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )

        self.assertEqual(
            [option["cancel"] for option in normalized["options"]],
            [True, True],
        )

    def test_rejects_full_id_revision_locator_and_effect_drift(self) -> None:
        mutations = []
        wrong_id = _frame()
        wrong_id["current_event_instance_id"] = EVENT_ID & 0x00FFFFFF
        mutations.append(wrong_id)
        wrong_revision = _frame()
        wrong_revision["snapshot_revision"] = NATIVE_REVISION + 1
        mutations.append(wrong_revision)
        frontend = _frame()
        frontend["provenance"]["idler_vtable_rva"] = "0xDEADBEEF"
        mutations.append(frontend)
        preview = _frame()
        preview["options"][0]["effect_preview"]["status"] = "available"
        mutations.append(preview)
        duplicate = _frame()
        duplicate["extra"] = None
        mutations.append(duplicate)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    normalize_current_event_window_context_v1(
                        mutation,
                        expected_event_instance_id=EVENT_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_effect_indicator_subset_is_strict_but_not_a_full_preview(self) -> None:
        normalized = normalize_current_event_window_context_v1(
            _frame(),
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        option = normalized["options"][0]
        self.assertEqual(
            option["effect_indicators"]["rows"], _indicator_rows()
        )
        self.assertFalse(option["effect_indicators"]["complete_effect_set"])
        self.assertEqual(option["resource_deltas"], {"status": "unavailable"})
        self.assertEqual(
            option["relationship_deltas"], {"status": "unavailable"}
        )
        self.assertFalse(normalized["readiness"]["effect_preview_ready"])
        self.assertFalse(normalized["readiness"]["semantic_decision_ready"])

        mutations: list[dict[str, object]] = []
        unready = _frame()
        unready["readiness"]["effect_indicators_ready"] = False
        mutations.append(unready)
        wrong_coverage = _frame()
        wrong_coverage["options"][0]["effect_indicators"]["coverage"] = "full"
        mutations.append(wrong_coverage)
        claims_complete = _frame()
        claims_complete["options"][0]["effect_indicators"][
            "complete_effect_set"
        ] = True
        mutations.append(claims_complete)
        bad_trait = _frame()
        bad_trait["options"][0]["effect_indicators"]["rows"][0][
            "operation"
        ] = "benefit"
        mutations.append(bad_trait)
        bad_stress = _frame()
        bad_stress["options"][0]["effect_indicators"]["rows"][1][
            "magnitude"
        ] = {"status": "available", "value": 10}
        mutations.append(bad_stress)
        bad_death = _frame()
        bad_death["options"][0]["effect_indicators"]["rows"][2][
            "direction"
        ] = "gain"
        mutations.append(bad_death)
        bad_scheme = _frame()
        bad_scheme["options"][0]["effect_indicators"]["rows"][3][
            "scheme"
        ]["scheme_type_key"] = ""
        mutations.append(bad_scheme)
        known_unknown = _frame()
        known_unknown["options"][0]["effect_indicators"]["rows"][4][
            "raw_kind"
        ] = 2
        mutations.append(known_unknown)
        fabricated_resource = _frame()
        fabricated_resource["options"][0]["resource_deltas"] = {
            "status": "available",
            "rows": [],
        }
        mutations.append(fabricated_resource)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    normalize_current_event_window_context_v1(
                        mutation,
                        expected_event_instance_id=EVENT_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_unavailable_trait_and_scheme_identities_remain_typed(self) -> None:
        frame = _frame()
        rows = frame["options"][0]["effect_indicators"]["rows"]
        rows[0]["trait"] = {
            "status": "unavailable",
            "reason": "trait_identity_unavailable",
        }
        rows[3]["scheme"] = {
            "status": "unavailable",
            "reason": "scheme_type_identity_unavailable",
        }
        normalized = normalize_current_event_window_context_v1(
            frame,
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertEqual(
            normalized["options"][0]["effect_indicators"]["rows"][0][
                "operation"
            ],
            "add",
        )
        self.assertTrue(normalized["readiness"]["effect_indicators_ready"])

    def test_event_definition_identity_cross_fields_are_strict(self) -> None:
        mutations: list[dict[str, object]] = []
        for field, value in (
            ("event_definition_key", None),
            ("event_definition_key", ""),
            ("calculated_event_id", None),
            ("calculated_event_id", True),
            ("calculated_event_id", 2**31),
            ("runtime_stats_ordinal", None),
            ("runtime_stats_ordinal", -(2**31) - 1),
        ):
            mutation = _frame()
            mutation[field] = value
            mutations.append(mutation)
        unready = _frame()
        unready["readiness"]["event_definition_identity_ready"] = False
        mutations.append(unready)
        unavailable_with_identity = _frame("unavailable")
        unavailable_with_identity["event_definition_key"] = "leaked.key"
        mutations.append(unavailable_with_identity)
        unavailable_with_id = _frame("unavailable")
        unavailable_with_id["calculated_event_id"] = 0
        mutations.append(unavailable_with_id)
        unavailable_with_ordinal = _frame("unavailable")
        unavailable_with_ordinal["runtime_stats_ordinal"] = 0
        mutations.append(unavailable_with_ordinal)
        unavailable_ready = _frame("unavailable")
        unavailable_ready["readiness"][
            "event_definition_identity_ready"
        ] = True
        mutations.append(unavailable_ready)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    normalize_current_event_window_context_v1(
                        mutation,
                        expected_event_instance_id=EVENT_ID,
                        expected_date_raw=DATE_RAW,
                        expected_snapshot_revision=NATIVE_REVISION,
                    )

    def test_query_action_requires_paused_full_active_event(self) -> None:
        capability = [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY]
        self.assertEqual(
            _action_steps(
                capability,
                active_event={"instance_id": EVENT_ID},
                paused=True,
            ),
            [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP],
        )
        self.assertNotIn(
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            _action_steps(
                capability,
                active_event={"instance_id": EVENT_ID},
                paused=False,
            ),
        )
        self.assertNotIn(
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            _action_steps(
                capability,
                active_event={"instance_id": -1},
                paused=True,
            ),
        )

    def test_service_and_mcp_bind_full_event_and_revision(self) -> None:
        service = GameplayBridgeService(_Driver())
        result = service.query_current_event_window_context_v1(
            EVENT_ID, expected_revision=9
        )
        self.assertTrue(result["current_event_window_context_ready"])
        self.assertTrue(result["current_event_effect_indicators_ready"])
        self.assertEqual(result["binding"]["event_instance_id"], EVENT_ID)
        self.assertEqual(result["event_definition_key"], EVENT_DEFINITION_KEY)
        self.assertEqual(result["calculated_event_id"], CALCULATED_EVENT_ID)
        self.assertEqual(
            result["runtime_stats_ordinal"], RUNTIME_STATS_ORDINAL
        )
        self.assertTrue(
            result["readiness"]["event_definition_identity_ready"]
        )
        self.assertTrue(result["readiness"]["effect_indicators_ready"])
        self.assertFalse(result["readiness"]["effect_preview_ready"])
        self.assertFalse(result["readiness"]["semantic_decision_ready"])
        via_mcp = _ck3_query_current_event_window_context_v1(
            service, EVENT_ID, 9
        )
        self.assertEqual(via_mcp["binding"], result["binding"])
        with self.assertRaises(Exception):
            service.query_current_event_window_context_v1(
                EVENT_ID & 0x00FFFFFF, expected_revision=9
            )
        with self.assertRaises(Exception):
            service.query_current_event_window_context_v1(
                EVENT_ID, expected_revision=8
            )

    def test_planner_queries_before_using_synthetic_snapshot_options(self) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_window_query")
        self.assertEqual(
            plan["selected_step"],
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        )

    def test_planner_uses_authored_native_index_for_forced_choice(self) -> None:
        frame = _frame()
        frame["options"][0]["enabled"] = True
        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-4",
            },
        )

        self.assertEqual(
            plan["phase"], "active_event_forced_presentation_choice"
        )
        self.assertEqual(plan["selected_step"], "select-event-option-4")
        self.assertIn("not a semantic optimum", plan["reason"])
        self.assertEqual(
            plan["active_event"]["selected_rendered_index"], 0
        )
        self.assertEqual(
            plan["active_event"]["selected_native_option_index"], 3
        )
        self.assertFalse(plan["active_event"]["semantic_optimal"])

    def test_planner_blocks_zero_enabled_materialized_rows(self) -> None:
        zero = _frame()
        plan = choose_one_life_turn(
            [_query_history(zero)],
            snapshot=_snapshot(),
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP},
        )
        self.assertEqual(
            plan["phase"], "active_event_semantic_evidence_required"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["active_event"]["enabled_materialized_option_count"], 0
        )

    def test_planner_degraded_choice_avoids_explicit_death_then_cancel(
        self,
    ) -> None:
        frame = _frame()
        death = frame["options"][0]
        death.update(
            {
                "native_option_index": 1,
                "enabled": True,
                "cancel": False,
            }
        )
        cancel = copy.deepcopy(death)
        cancel.update(
            {
                "rendered_index": 1,
                "native_option_index": 4,
                "cancel": True,
            }
        )
        cancel["effect_indicators"]["rows"] = []
        ordinary = copy.deepcopy(cancel)
        ordinary.update(
            {
                "rendered_index": 2,
                "native_option_index": 7,
                "cancel": False,
            }
        )
        frame["options"].extend((cancel, ordinary))

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-2",
                "select-event-option-5",
                "select-event-option-8",
            },
        )

        self.assertEqual(plan["phase"], "active_event_degraded_minimal_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-8")
        decision = plan["event_decision"]
        self.assertEqual(
            decision["eligible_native_option_indices"], [1, 4, 7]
        )
        self.assertEqual(
            decision["explicit_player_death_native_option_indices"], [1]
        )
        self.assertTrue(decision["death_avoidance_applied"])
        self.assertTrue(decision["cancel_deprioritization_applied"])
        self.assertEqual(
            decision["final_candidate_native_option_indices"], [7]
        )
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_optimal"])

    def test_planner_degraded_choice_uses_lowest_native_not_rendered_index(
        self,
    ) -> None:
        frame = _frame()
        first = frame["options"][0]
        first.update(
            {
                "native_option_index": 7,
                "enabled": True,
                "cancel": False,
            }
        )
        first["effect_indicators"]["rows"] = []
        second = copy.deepcopy(first)
        second.update({"rendered_index": 1, "native_option_index": 2})
        frame["options"].append(second)

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-3",
                "select-event-option-8",
            },
        )

        self.assertEqual(plan["selected_step"], "select-event-option-3")
        self.assertEqual(
            plan["event_decision"]["selected_rendered_index"], 1
        )

    def test_planner_degraded_choice_is_bounded_when_all_options_mean_death(
        self,
    ) -> None:
        frame = _frame()
        first = frame["options"][0]
        first.update(
            {
                "native_option_index": 3,
                "enabled": True,
                "cancel": False,
            }
        )
        second = copy.deepcopy(first)
        second.update({"rendered_index": 1, "native_option_index": 1})
        frame["options"].append(second)

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=_snapshot(),
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-2",
                "select-event-option-4",
            },
        )

        self.assertEqual(plan["selected_step"], "select-event-option-2")
        decision = plan["event_decision"]
        self.assertFalse(decision["death_avoidance_applied"])
        self.assertEqual(
            decision["final_candidate_native_option_indices"], [1, 3]
        )

    def test_planner_degraded_choice_never_substitutes_an_unadvertised_step(
        self,
    ) -> None:
        frame = _frame()
        frame["options"][0]["enabled"] = True
        second = copy.deepcopy(frame["options"][0])
        second.update({"rendered_index": 1, "native_option_index": 7})
        frame["options"].append(second)

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=_snapshot(),
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP},
        )

        self.assertEqual(
            plan["phase"], "active_event_degraded_choice_unsupported"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "select-event-option-4")

    def test_same_frame_unavailable_does_not_repeat_query(self) -> None:
        plan = choose_one_life_turn(
            [_query_history(_frame("unavailable"))],
            snapshot=_snapshot(),
            action_steps={QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP},
        )

        self.assertEqual(plan["phase"], "active_event_window_unavailable")
        self.assertIsNone(plan["selected_step"])
        self.assertIn("event_window_not_materialized", plan["reason"])

    def test_stale_or_mismatched_query_result_is_ignored_and_requeried(
        self,
    ) -> None:
        mutations: list[tuple[str, object]] = [
            ("queried_snapshot_id", "snapshot-old"),
            ("queried_revision", 8),
            ("queried_native_revision", NATIVE_REVISION - 1),
            ("snapshot_revision", NATIVE_REVISION - 1),
            ("date_raw", DATE_RAW - 1),
            ("current_event_instance_id", EVENT_ID - 1),
        ]
        for field, value in mutations:
            with self.subTest(field=field):
                row = _query_history()
                row["result"][field] = value
                plan = choose_one_life_turn(
                    [row],
                    snapshot=_snapshot(),
                    action_steps={
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
                    },
                )
                self.assertEqual(plan["phase"], "active_event_window_query")

        context_mutations = [
            ("snapshot_revision", NATIVE_REVISION - 1),
            ("date_raw", DATE_RAW - 1),
            ("current_event_instance_id", EVENT_ID - 1),
        ]
        for field, value in context_mutations:
            with self.subTest(context_field=field):
                row = _query_history()
                row["result"]["current_event_window_context"][field] = value
                plan = choose_one_life_turn(
                    [row],
                    snapshot=_snapshot(),
                    action_steps={
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
                    },
                )
                self.assertEqual(plan["phase"], "active_event_window_query")

    def test_backend_without_typed_query_keeps_legacy_event_behavior(
        self,
    ) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot=_snapshot(),
            action_steps={"select-event-option-1"},
        )

        self.assertEqual(plan["phase"], "active_event")
        self.assertEqual(plan["selected_step"], "select-event-option-1")

    def test_typed_backend_pauses_before_query_instead_of_falling_back(self) -> None:
        snapshot = _snapshot()
        snapshot["paused"] = False
        plan = choose_one_life_turn(
            [],
            snapshot=snapshot,
            action_steps={"pause-map", "select-event-option-1"},
            bridge_capabilities={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            },
        )

        self.assertEqual(plan["phase"], "active_event_window_pause_required")
        self.assertEqual(plan["selected_step"], "pause-map")

    def test_typed_backend_never_uses_legacy_choice_when_query_is_missing(
        self,
    ) -> None:
        plan = choose_one_life_turn(
            [],
            snapshot=_snapshot(),
            action_steps={"select-event-option-1"},
            bridge_capabilities={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
            },
        )

        self.assertEqual(plan["phase"], "active_event_window_query_unavailable")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_step"],
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        )

    def test_service_auto_turn_queries_then_uses_authored_index(
        self,
    ) -> None:
        calls: list[tuple[str, int | None]] = []
        frame = _frame()
        frame["options"][0]["enabled"] = True
        snapshot = {
            **_snapshot(),
            "native_command_history": [],
        }

        def execute(step: str, revision: int | None) -> dict[str, object]:
            calls.append((step, revision))
            if step == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP:
                result = _query_result(frame)
                snapshot["native_command_history"].append(
                    {
                        "command": step,
                        "ok": True,
                        "result": copy.deepcopy(result),
                    }
                )
                return result
            return {"accepted": True, "step": step}

        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: copy.deepcopy(snapshot),
            execute=execute,
            action_steps=(
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-4",
            ),
        )

        service = GameplayBridgeService(driver)
        query = service.auto_turn()
        result = service.auto_turn()

        self.assertEqual(
            query["selected_step"], QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        )
        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["selected_step"], "select-event-option-4")
        self.assertEqual(
            calls,
            [
                (QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, 9),
                ("select-event-option-4", 9),
            ],
        )


if __name__ == "__main__":
    unittest.main()
