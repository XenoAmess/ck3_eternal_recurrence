#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_acceptance as acceptance  # noqa: E402
import run_zhongguo_acceptance as capture  # noqa: E402
PLAYER = 32_904
EVENT_KEY = "ep3_story_cycle_admin_eunuch.8030"
PRODUCT_EVENT_KEY = "zg361p2c.2"
JINGCHA_EVENT_KEY = "zg361.40"
ANNUAL_SUMMARY_EVENT_KEY = "zg361.1"


def _scope(type_key: str, character_id: int | None = None) -> dict[str, object]:
    identity: dict[str, object]
    if character_id is None:
        identity = {"status": "unavailable", "reason": "not_identity_bearing"}
    else:
        identity = {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        }
    return {
        "status": "available",
        "type_key": type_key,
        "typed_identity": identity,
    }


def _context(native_indices: tuple[int, ...] = (0, 1, 3)) -> dict[str, object]:
    scope_types = {
        "story": "story",
        "eunuch": "character",
        "emperor": "character",
        "admin_title": "landed_title",
        "student": "character",
        "rival": "character",
        "background_throne_room_scope": "character",
    }
    character_ids = {
        "eunuch": 31_801,
        "emperor": PLAYER,
        "student": 33_596_937,
        "rival": 16_834_604,
        "background_throne_room_scope": 31_440,
    }
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": EVENT_KEY,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [
            {
                "name": name,
                "scope": _scope(type_key, character_ids.get(name)),
            }
            for name, type_key in scope_types.items()
        ],
        "options": [
            {
                "rendered_index": rendered,
                "native_option_index": native,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for rendered, native in enumerate(native_indices)
        ],
    }


def _product_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": PRODUCT_EVENT_KEY,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [
            {"name": "zg361_p2c_summary_cycle", "scope": _scope("value")},
            {"name": "zg361_p2c_summary_case", "scope": _scope("value")},
        ],
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
        ],
    }


def _jingcha_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": JINGCHA_EVENT_KEY,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
            for index in range(2)
        ],
    }


def _annual_summary_context() -> dict[str, object]:
    return {
        "schema": "current-event-window-context-v1",
        "schema_version": 1,
        "status": "available",
        "window_match_count": 1,
        "event_definition_key": ANNUAL_SUMMARY_EVENT_KEY,
        "root_scope": _scope("character", PLAYER),
        "saved_scopes": [
            {"name": name, "scope": _scope("value")}
            for name in (
                "zg361_n_375",
                "zg361_n_35",
                "zg361_n_325",
                "zg361_n_elim",
            )
        ],
        "options": [
            {
                "rendered_index": 0,
                "native_option_index": 0,
                "shown": True,
                "enabled": True,
                "fallback": False,
                "cancel": False,
            }
        ],
    }


class _Service:
    def __init__(
        self,
        event_key: str = EVENT_KEY,
        event_instance_id: int = 621,
        option_count: int = 4,
        date_raw: int = 53_366_664,
    ) -> None:
        self.event_key = event_key
        self.event_instance_id = event_instance_id
        self.option_count = option_count
        self.date_raw = date_raw

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "native:8",
            "revision": 91,
            "native_revision": 8,
            "date_raw": self.date_raw,
            "paused": True,
            "speed": 5,
            "map_ready": True,
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 1001},
            "active_event": {
                "instance_id": self.event_instance_id,
                "option_count": self.option_count,
            },
        }


def _identity(service: _Service, context: dict[str, object]) -> dict[str, object]:
    return {
        "event_instance_id": service.event_instance_id,
        "snapshot_revision": 91,
        "event_definition_key": service.event_key,
        "query": {"current_event_window_context": context},
    }


class Phase2ReviewedVanillaWaitTests(unittest.TestCase):
    def test_reviewed_helper_resolves_existing_extended_contract(self) -> None:
        service = _Service()
        snapshot = service.snapshot()
        identity = _identity(service, _context())
        with mock.patch.object(
            capture,
            "_drain_known_timeline_interrupt",
            return_value={
                "result": "GREEN",
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            },
        ) as drain:
            result = capture.drain_reviewed_vanilla_event_interruption_native(
                service,
                snapshot=snapshot,
                identity=identity,
            )

        self.assertEqual(result["result"], "GREEN")
        kwargs = drain.call_args.kwargs
        self.assertEqual(kwargs["event_key"], EVENT_KEY)
        self.assertEqual(kwargs["player"], PLAYER)
        self.assertEqual(kwargs["connection_generation"], 1)
        self.assertEqual(kwargs["contract"]["root_character_id"], PLAYER)
        self.assertEqual(kwargs["contract"]["selected_option_number"], 4)

    def test_reviewed_product_helper_resolves_central_summary_contract(self) -> None:
        service = _Service(PRODUCT_EVENT_KEY, 622, 1)
        snapshot = service.snapshot()
        identity = _identity(service, _product_context())
        with mock.patch.object(
            capture,
            "_drain_known_timeline_interrupt",
            return_value={
                "result": "GREEN",
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        ) as drain:
            result = (
                capture.drain_reviewed_phase2_product_event_interruption_native(
                    service,
                    snapshot=snapshot,
                    identity=identity,
                )
            )

        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["registry_contract_source"],
            "phase2_central_timeline_registry",
        )
        kwargs = drain.call_args.kwargs
        self.assertEqual(kwargs["event_key"], PRODUCT_EVENT_KEY)
        self.assertEqual(kwargs["contract"]["root_character_id"], PLAYER)
        self.assertEqual(kwargs["contract"]["selected_option_number"], 1)
        self.assertEqual(
            kwargs["contract"]["scope_types"],
            {
                "zg361_p2c_summary_cycle": "value",
                "zg361_p2c_summary_case": "value",
            },
        )

    def test_reviewed_product_helper_resolves_r598_jingcha_contract(self) -> None:
        service = _Service(JINGCHA_EVENT_KEY, 623, 2, 53_366_688)
        snapshot = service.snapshot()
        identity = _identity(service, _jingcha_context())
        with mock.patch.object(
            capture,
            "_drain_known_timeline_interrupt",
            return_value={
                "result": "GREEN",
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        ) as drain:
            result = (
                capture.drain_reviewed_phase2_product_event_interruption_native(
                    service,
                    snapshot=snapshot,
                    identity=identity,
                )
            )

        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["registry_contract_source"],
            "phase2_product_timeline_registry",
        )
        kwargs = drain.call_args.kwargs
        self.assertEqual(kwargs["event_key"], JINGCHA_EVENT_KEY)
        self.assertEqual(kwargs["contract"]["root_character_id"], PLAYER)
        self.assertEqual(
            kwargs["contract"]["date_policy"],
            "manager-recovery-product-window",
        )
        self.assertEqual(kwargs["contract"]["selected_option_number"], 1)
        self.assertEqual(kwargs["contract"]["selected_native_option_index"], 0)

    def test_reviewed_product_helper_resolves_r603_annual_summary_contract(self) -> None:
        service = _Service(ANNUAL_SUMMARY_EVENT_KEY, 626, 1, 53_375_616)
        snapshot = service.snapshot()
        identity = _identity(service, _annual_summary_context())
        with mock.patch.object(
            capture,
            "_drain_known_timeline_interrupt",
            return_value={
                "result": "GREEN",
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            },
        ) as drain:
            result = (
                capture.drain_reviewed_phase2_product_event_interruption_native(
                    service,
                    snapshot=snapshot,
                    identity=identity,
                )
            )

        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(
            result["registry_contract_source"],
            "phase2_product_timeline_registry",
        )
        kwargs = drain.call_args.kwargs
        self.assertEqual(kwargs["event_key"], ANNUAL_SUMMARY_EVENT_KEY)
        self.assertEqual(kwargs["contract"]["root_character_id"], PLAYER)
        self.assertEqual(
            kwargs["contract"]["date_policy"],
            "manager-recovery-product-window",
        )
        self.assertEqual(kwargs["contract"]["selected_option_number"], 1)
        self.assertEqual(kwargs["contract"]["selected_native_option_index"], 0)

    def test_reviewed_vanilla_then_product_events_reach_target(self) -> None:
        service = _Service()
        context = _context()

        def drain(
            _service: object, *, snapshot: object, identity: object
        ) -> dict[str, object] | None:
            self.assertIsInstance(snapshot, dict)
            if identity["event_definition_key"] != EVENT_KEY:
                return None
            self.assertEqual(identity["event_definition_key"], EVENT_KEY)
            service.event_key = PRODUCT_EVENT_KEY
            service.event_instance_id = 622
            service.option_count = 1
            return {
                "result": "GREEN",
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            }

        def drain_product(
            _service: object, *, snapshot: object, identity: object
        ) -> dict[str, object]:
            self.assertIsInstance(snapshot, dict)
            if identity["event_definition_key"] == PRODUCT_EVENT_KEY:
                service.event_key = JINGCHA_EVENT_KEY
                service.event_instance_id = 623
                service.option_count = 2
                service.date_raw = 53_366_688
            else:
                self.assertEqual(identity["event_definition_key"], JINGCHA_EVENT_KEY)
                service.event_key = "zg361we.360"
                service.event_instance_id = 624
            return {
                "result": "GREEN",
                "selected_option_number": 1,
                "selected_native_option_index": 0,
            }

        def identity(_service: object, _snapshot: object) -> dict[str, object]:
            if service.event_key == EVENT_KEY:
                return _identity(service, context)
            if service.event_key == PRODUCT_EVENT_KEY:
                return _identity(service, _product_context())
            if service.event_key == JINGCHA_EVENT_KEY:
                return _identity(service, _jingcha_context())
            return {
                "event_instance_id": 624,
                "snapshot_revision": 91,
                "event_definition_key": "zg361we.360",
                "query": {},
            }

        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            capture,
            "pause_bound_native_event_for_definition_query",
            side_effect=lambda *_args, **_kwargs: {
                "snapshot": service.snapshot(),
                "evidence": {"result": "GREEN"},
            },
        ), mock.patch.object(
            capture, "query_event_definition_identity", side_effect=identity
        ), mock.patch.object(
            capture,
            "drain_reviewed_vanilla_event_interruption_native",
            side_effect=drain,
        ) as vanilla_selection, mock.patch.object(
            capture,
            "drain_reviewed_phase2_product_event_interruption_native",
            side_effect=drain_product,
        ) as product_selection:
            result = capture.wait_for_native_event_definition(
                service,
                Path(temporary),
                stem="reviewed",
                expected_event_definition_key="zg361we.360",
                clear_unexpected_single_option_events=False,
                clear_reviewed_vanilla_event_interruptions=True,
                clear_reviewed_product_event_interruptions=True,
            )

        self.assertEqual(result["identity"]["event_definition_key"], "zg361we.360")
        self.assertEqual(vanilla_selection.call_count, 3)
        self.assertEqual(
            [
                call.kwargs["identity"]["event_definition_key"]
                for call in vanilla_selection.call_args_list
            ],
            [EVENT_KEY, PRODUCT_EVENT_KEY, JINGCHA_EVENT_KEY],
        )
        self.assertEqual(product_selection.call_count, 2)
        evidence = result["evidence"]
        self.assertEqual(len(evidence["cleared_reviewed_vanilla_interruptions"]), 1)
        self.assertEqual(
            evidence["reviewed_vanilla_decisions"][0]["result"], "GREEN"
        )
        self.assertEqual(len(evidence["cleared_reviewed_product_interruptions"]), 2)
        self.assertEqual(
            evidence["reviewed_product_decisions"][0]["result"], "GREEN"
        )
        self.assertEqual(
            evidence["reviewed_product_decisions"][1]["result"], "GREEN"
        )

    def test_drifted_reviewed_projection_remains_red_without_selection(self) -> None:
        service = _Service()
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(
            capture,
            "pause_bound_native_event_for_definition_query",
            return_value={
                "snapshot": service.snapshot(),
                "evidence": {"result": "GREEN"},
            },
        ), mock.patch.object(
            capture,
            "query_event_definition_identity",
            return_value=_identity(service, _context((0, 1, 2))),
        ), mock.patch.object(
            capture,
            "drain_reviewed_vanilla_event_interruption_native",
            side_effect=acceptance.RunnerError("reviewed projection drift"),
        ) as selection:
            with self.assertRaisesRegex(
                acceptance.RunnerError,
                "reviewed vanilla event contract blocked",
            ):
                capture.wait_for_native_event_definition(
                    service,
                    Path(temporary),
                    stem="drifted",
                    expected_event_definition_key="zg361we.360",
                    clear_unexpected_single_option_events=False,
                    clear_reviewed_vanilla_event_interruptions=True,
                )
        selection.assert_called_once()


if __name__ == "__main__":
    unittest.main()
