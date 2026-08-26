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
        "root_scope": None,
        "saved_scopes": None,
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
                "effect_preview": {
                    "status": "unavailable",
                    "reason": "full_effect_preview_unavailable",
                },
            }
        ] if available else None,
        "readiness": {
            "event_definition_identity_ready": available,
            "option_presentation_ready": available,
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
        self.assertEqual(result["binding"]["event_instance_id"], EVENT_ID)
        self.assertEqual(result["event_definition_key"], EVENT_DEFINITION_KEY)
        self.assertEqual(result["calculated_event_id"], CALCULATED_EVENT_ID)
        self.assertEqual(
            result["runtime_stats_ordinal"], RUNTIME_STATS_ORDINAL
        )
        self.assertTrue(
            result["readiness"]["event_definition_identity_ready"]
        )
        self.assertFalse(result["readiness"]["effect_preview_ready"])
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

    def test_planner_blocks_zero_or_multiple_enabled_materialized_rows(
        self,
    ) -> None:
        zero = _frame()
        multiple = _frame()
        multiple["options"][0]["enabled"] = True
        second = copy.deepcopy(multiple["options"][0])
        second.update(
            {
                "rendered_index": 1,
                "native_option_index": 7,
                "cancel": False,
            }
        )
        multiple["options"].append(second)

        for frame, expected_count in ((zero, 0), (multiple, 2)):
            with self.subTest(expected_count=expected_count):
                plan = choose_one_life_turn(
                    [_query_history(frame)],
                    snapshot=_snapshot(),
                    action_steps={
                        QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
                        "select-event-option-4",
                        "select-event-option-8",
                    },
                )
                self.assertEqual(
                    plan["phase"],
                    "active_event_semantic_evidence_required",
                )
                self.assertIsNone(plan["selected_step"])
                self.assertEqual(
                    plan["active_event"][
                        "enabled_materialized_option_count"
                    ],
                    expected_count,
                )
                self.assertEqual(
                    plan["required_capabilities"],
                    [
                        "game.state.current-event-window-effect-preview",
                        "game.policy.current-event-semantic-decision",
                    ],
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


if __name__ == "__main__":
    unittest.main()
