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
from xar_autoplayer.vanilla_events.bookmark_raiktor_policy import (
    recommend_robert_raiktor_option_v1,
)
from xar_autoplayer.bridge.war_entry_contract import (
    RAIKTOR_BOOKMARK_EVENT_SCOPE_CAPABILITY,
    query_war_entry_assessments_step,
)


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


def _r0065_grief_frame() -> dict[str, object]:
    frame = _frame()
    frame.update({
        "event_definition_key": "stress_threshold_special.1001",
        "calculated_event_id": 3_121_001,
        "runtime_stats_ordinal": 4_333,
        "root_scope": _scope(character_id=CHARACTER_ID),
        "saved_scopes": [
            {
                "name": "stress_character",
                "name_identifier": 20_928,
                "scope": _scope(character_id=CHARACTER_ID),
            },
            {
                "name": "deceased_character",
                "name_identifier": 19_883,
                "scope": _scope(character_id=36_403),
            },
        ],
    })
    first = frame["options"][0]
    first.update({
        "native_option_index": 0,
        "shown": True,
        "enabled": True,
        "fallback": False,
        "cancel": False,
        "unavailable_reason": "",
    })
    first["effect_indicators"]["rows"] = []
    frame["options"] = [
        {
            **copy.deepcopy(first),
            "rendered_index": rendered,
            "native_option_index": native,
        }
        for rendered, native in enumerate((0, 4, 7))
    ]
    return frame


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

    def test_stale_saved_character_keeps_inventory_without_fabricated_id(self) -> None:
        frame = _frame()
        frame["saved_scopes"][0]["scope"]["typed_identity"] = {
            "status": "unavailable",
            "reason": "character_scope_identity_unavailable",
        }
        normalized = normalize_current_event_window_context_v1(
            frame,
            expected_event_instance_id=EVENT_ID,
            expected_date_raw=DATE_RAW,
            expected_snapshot_revision=NATIVE_REVISION,
        )
        self.assertEqual(
            normalized["saved_scopes"][0]["scope"]["typed_identity"],
            {
                "status": "unavailable",
                "reason": "character_scope_identity_unavailable",
            },
        )

        stale_root = _frame()
        stale_root["root_scope"]["typed_identity"] = {
            "status": "unavailable",
            "reason": "character_scope_identity_unavailable",
        }
        wrong_reason = _frame()
        wrong_reason["saved_scopes"][0]["scope"]["typed_identity"] = {
            "status": "unavailable",
            "reason": "generic_scope_payload_identity_not_closed",
        }
        extra_field = _frame()
        extra_field["saved_scopes"][0]["scope"]["typed_identity"] = {
            "status": "unavailable",
            "reason": "character_scope_identity_unavailable",
            "character_id": CHARACTER_ID,
        }
        for mutation in (stale_root, wrong_reason, extra_field):
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

    def test_planner_prefers_matching_exact_build_registry_choice(self) -> None:
        frame = _frame()
        frame["event_definition_key"] = "tgp_travel_events.0030"
        frame["root_scope"] = _scope(character_id=CHARACTER_ID)
        frame["saved_scopes"] = [
            {
                "name": "travel_plan",
                "name_identifier": 301,
                "scope": _scope(
                    raw_type_index=5,
                    type_key="travel_plan",
                    character_id=None,
                ),
            },
            {
                "name": "poem_province",
                "name_identifier": 302,
                "scope": _scope(
                    raw_type_index=3,
                    type_key="province",
                    character_id=None,
                ),
            },
        ]
        first = frame["options"][0]
        first.update(
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
        )
        first["effect_indicators"]["rows"] = []
        second = copy.deepcopy(first)
        second.update({"rendered_index": 1, "native_option_index": 1})
        frame["options"] = [first, second]
        snapshot = _snapshot()
        snapshot["played_character"] = {
            "character_id": CHARACTER_ID,
            "alive": True,
            "stress_points": 42,
        }
        snapshot["active_event"]["option_count"] = 2

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-2",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-2")
        self.assertEqual(
            plan["event_decision"]["policy"],
            "exact-build-vanilla-event-registry-direct-projection-v1",
        )
        self.assertFalse(plan["event_decision"]["semantic_optimal"])
        self.assertTrue(plan["event_decision"]["campaign_utility_ready"])
        self.assertEqual(
            plan["event_campaign_utility"]["objective_id"],
            "reduce_stress_without_delaying_travel",
        )
        self.assertEqual(plan["event_campaign_utility"]["selected_rank"], 1)
        self.assertIsNone(
            plan["event_campaign_utility"]["cross_event_numeric_score"]
        )
        self.assertEqual(plan["event_material_postcondition"]["status"], "ready")
        self.assertEqual(
            plan["event_material_postcondition"]["starting_value"], 42
        )

    def test_r0065_grief_source_bound_choice_uses_typed_native_seven(
        self,
    ) -> None:
        frame = _r0065_grief_frame()
        snapshot = _snapshot()
        snapshot["played_character"] = {
            "character_id": CHARACTER_ID,
            "alive": True,
            "stress_points": 87,
        }
        snapshot["active_event"]["option_count"] = 9

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-5",
                "select-event-option-8",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-8")
        self.assertEqual(plan["event_decision"]["selected_native_option_index"], 7)
        self.assertEqual(plan["event_decision"]["matched_option_variant_index"], 3)
        self.assertFalse(plan["event_decision"]["semantic_optimal"])
        self.assertEqual(plan["event_material_postcondition"]["status"], "ready")
        self.assertEqual(
            plan["event_material_postcondition"]["starting_value"], 87
        )

    def test_r0065_grief_requires_positive_same_frame_stress(self) -> None:
        frame = _r0065_grief_frame()
        for stress_points in (0, None):
            with self.subTest(stress_points=stress_points):
                snapshot = _snapshot()
                snapshot["played_character"] = {
                    "character_id": CHARACTER_ID,
                    "alive": True,
                    "stress_points": stress_points,
                }
                snapshot["active_event"]["option_count"] = 9
                plan = choose_one_life_turn(
                    [_query_history(frame)],
                    snapshot=snapshot,
                    action_steps={
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                        "select-event-option-8",
                    },
                )
                self.assertEqual(
                    plan["phase"],
                    "active_event_registry_material_observation_blocked",
                )
                self.assertIsNone(plan["selected_step"])

    def test_planner_uses_r840_prison_release_registry_acknowledgement(
        self,
    ) -> None:
        player_id = 29_829
        imprisoner_id = 32_309
        prisoner_id = 34_730
        frame = _frame()
        frame["event_definition_key"] = "prison_notification.2002"
        frame["root_scope"] = _scope(character_id=player_id)
        frame["saved_scopes"] = [
            {
                "name": "imprisoner",
                "name_identifier": 40,
                "scope": _scope(character_id=imprisoner_id),
            },
            {
                "name": "new_memory",
                "name_identifier": 205,
                "scope": _scope(
                    raw_type_index=34,
                    type_key="character_memory",
                    character_id=None,
                ),
            },
            {
                "name": "prisoner",
                "name_identifier": 9_073,
                "scope": _scope(character_id=prisoner_id),
            },
            {
                "name": "bg_override_char",
                "name_identifier": 8_901,
                "scope": _scope(character_id=imprisoner_id),
            },
            {
                "name": "this_player",
                "name_identifier": 20_544,
                "scope": _scope(character_id=player_id),
            },
        ]
        option = frame["options"][0]
        option.update(
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "Imprisonment is a cruelty.",
            }
        )
        option["effect_indicators"]["rows"] = []
        snapshot = _snapshot()
        snapshot["played_character"] = {
            "character_id": player_id,
            "alive": True,
        }
        snapshot["active_event"]["option_count"] = 1

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        decision = plan["event_decision"]
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["failed_checks"], [])
        self.assertFalse(decision["semantic_optimal"])
        self.assertFalse(decision["campaign_utility_ready"])
        self.assertNotIn("event_material_postcondition", plan)

    def test_planner_uses_r842_withering_mind_registry_acknowledgement(
        self,
    ) -> None:
        player_id = 29_829
        frame = _frame()
        frame.update(
            {
                "date_raw": 53_204_496,
                "current_event_instance_id": 9,
                "event_definition_key": "health.7200",
                "calculated_event_id": 4_577_200,
                "runtime_stats_ordinal": 7_413,
                "root_scope": _scope(character_id=player_id),
                "saved_scopes": [],
            }
        )
        option = frame["options"][0]
        option.update(
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "I should get back to bed...",
                "unavailable_reason": "",
            }
        )
        option["effect_indicators"]["rows"] = [
            {
                "kind": "trait",
                "operation": "add",
                "trait": {
                    "status": "available",
                    "native_id": 123,
                    "key": "withering_mind",
                },
            }
        ]
        snapshot = _snapshot()
        snapshot.update(
            {
                "date_raw": 53_204_496,
                "played_character": {
                    "character_id": player_id,
                    "alive": True,
                },
            }
        )
        snapshot["active_event"] = {"instance_id": 9, "option_count": 1}

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        decision = plan["event_decision"]
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_option_number"], 1)
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["selected_rendered_index"], 0)
        self.assertEqual(decision["failed_checks"], [])
        self.assertFalse(decision["semantic_optimal"])
        self.assertFalse(decision["campaign_utility_ready"])
        self.assertNotIn("event_material_postcondition", plan)

    def test_planner_uses_r844_fragile_bones_registry_acknowledgement(
        self,
    ) -> None:
        player_id = 29_829
        frame = _frame()
        frame.update(
            {
                "date_raw": 53_204_496,
                "current_event_instance_id": 8,
                "event_definition_key": "health.7500",
                "calculated_event_id": 4_577_500,
                "runtime_stats_ordinal": 7_416,
                "root_scope": _scope(character_id=player_id),
                "saved_scopes": [],
            }
        )
        option = frame["options"][0]
        option.update(
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
                "resolved_name": "我应该走路再小心点。",
                "unavailable_reason": "",
            }
        )
        option["effect_indicators"]["rows"] = [
            {
                "kind": "trait",
                "operation": "add",
                "trait": {
                    "status": "available",
                    "native_id": 126,
                    "key": "fragile_bones",
                },
            }
        ]
        snapshot = _snapshot()
        snapshot.update(
            {
                "date_raw": 53_204_496,
                "played_character": {
                    "character_id": player_id,
                    "alive": True,
                },
            }
        )
        snapshot["active_event"] = {"instance_id": 8, "option_count": 1}

        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
            },
        )

        self.assertEqual(plan["phase"], "active_event_registry_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-1")
        decision = plan["event_decision"]
        self.assertEqual(decision["status"], "recommended")
        self.assertEqual(decision["selected_option_number"], 1)
        self.assertEqual(decision["selected_native_option_index"], 0)
        self.assertEqual(decision["selected_rendered_index"], 0)
        self.assertEqual(decision["failed_checks"], [])
        self.assertFalse(decision["semantic_optimal"])
        self.assertFalse(decision["campaign_utility_ready"])
        self.assertNotIn("event_material_postcondition", plan)

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

    def test_planner_blocks_multiple_options_without_semantic_policy(
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

        self.assertEqual(
            plan["phase"], "active_event_semantic_evidence_required"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertNotIn("event_decision", plan)
        self.assertIn("multiple materialized event options", plan["reason"])
        self.assertEqual(
            plan["active_event"]["enabled_materialized_option_count"], 3
        )

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


def _raiktor_frame_and_snapshot() -> tuple[dict[str, object], dict[str, object]]:
    frame = _frame()
    frame["event_definition_key"] = "bookmark.1071"
    frame["root_scope"] = _scope(character_id=CHARACTER_ID)
    frame["saved_scopes"] = [
        {
            "name": "byz_emperor",
            "name_identifier": 401,
            "scope": _scope(character_id=84),
        },
        {
            "name": "raiktor",
            "name_identifier": 402,
            "scope": _scope(character_id=77),
        },
    ]
    first = frame["options"][0]
    first.update(
        {
            "native_option_index": 0,
            "enabled": True,
            "fallback": False,
            "cancel": False,
            "resolved_name": "Claim the empire",
        }
    )
    first["effect_indicators"]["rows"] = []
    second = copy.deepcopy(first)
    second.update(
        {"rendered_index": 1, "native_option_index": 1, "resolved_name": "Coast"}
    )
    third = copy.deepcopy(first)
    third.update(
        {"rendered_index": 2, "native_option_index": 2, "resolved_name": "Decline"}
    )
    frame["options"] = [first, second, third]
    snapshot = _snapshot()
    snapshot["active_event"]["option_count"] = 3
    snapshot["played_character"] = {"character_id": CHARACTER_ID, "alive": True}
    snapshot["played_character_gold"] = {"raw": 20_000_000, "scale": 100_000}
    snapshot["active_wars"] = []
    snapshot["declarable_wars"] = []
    return frame, snapshot


class RobertRaiktorTypedConsumerTests(unittest.TestCase):
    def test_formal_planner_declines_without_power_instead_of_first_option(self) -> None:
        frame, snapshot = _raiktor_frame_and_snapshot()
        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-3",
            },
        )
        self.assertEqual(plan["phase"], "active_event_raiktor_source_reviewed_choice")
        self.assertEqual(plan["selected_step"], "select-event-option-3")
        self.assertFalse(plan["event_decision"]["native_power_observed"])

    def test_query_only_when_byzantine_holder_is_a_lawful_native_target(self) -> None:
        frame, snapshot = _raiktor_frame_and_snapshot()
        step = query_war_entry_assessments_step([84])
        snapshot["declarable_wars"] = [{"target_character_id": 84}]
        choice = recommend_robert_raiktor_option_v1(
            frame,
            snapshot,
            war_entry_assessments={},
            action_steps={step},
            cross_run_focus=None,
        )
        self.assertEqual(choice["status"], "query_required")
        self.assertEqual(choice["selected_step"], step)
        snapshot["declarable_wars"] = []
        choice = recommend_robert_raiktor_option_v1(
            frame,
            snapshot,
            war_entry_assessments={},
            action_steps={step},
            cross_run_focus=None,
        )
        self.assertEqual(choice["selected_native_option_index"], 2)
        choice = recommend_robert_raiktor_option_v1(
            frame,
            snapshot,
            war_entry_assessments={},
            action_steps={step},
            cross_run_focus=None,
            event_scope_query_supported=True,
        )
        self.assertEqual(choice["status"], "query_required")
        self.assertEqual(
            RAIKTOR_BOOKMARK_EVENT_SCOPE_CAPABILITY,
            "game.command.query-war-entry-assessments-raiktor-bookmark-saved-scope-v1",
        )

    def test_claim_requires_large_observed_own_power_margin(self) -> None:
        frame, snapshot = _raiktor_frame_and_snapshot()
        assessment = {
            84: {"actor_power_base_raw": 250_000, "target_power_total_raw": 190_000}
        }
        choice = recommend_robert_raiktor_option_v1(
            frame,
            snapshot,
            war_entry_assessments=assessment,
            action_steps=set(),
            cross_run_focus=None,
        )
        self.assertEqual(choice["selected_native_option_index"], 0)
        self.assertTrue(choice["source_capture_required_for_gen034_d"])
        assessment[84]["target_power_total_raw"] = 210_000
        choice = recommend_robert_raiktor_option_v1(
            frame,
            snapshot,
            war_entry_assessments=assessment,
            action_steps=set(),
            cross_run_focus=None,
        )
        self.assertEqual(choice["selected_native_option_index"], 2)

    def test_missing_saved_scope_blocks_instead_of_degraded_choice(self) -> None:
        frame, snapshot = _raiktor_frame_and_snapshot()
        frame["saved_scopes"] = frame["saved_scopes"][:1]
        plan = choose_one_life_turn(
            [_query_history(frame)],
            snapshot=snapshot,
            action_steps={
                QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                "select-event-option-1",
                "select-event-option-3",
            },
        )
        self.assertEqual(plan["phase"], "active_event_raiktor_contract_blocked")
        self.assertIsNone(plan["selected_step"])


if __name__ == "__main__":
    unittest.main()
