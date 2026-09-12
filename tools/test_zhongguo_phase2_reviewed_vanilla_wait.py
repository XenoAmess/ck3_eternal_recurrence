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


class _Service:
    def __init__(self) -> None:
        self.event_key = EVENT_KEY
        self.event_instance_id = 621

    def snapshot(self) -> dict[str, object]:
        return {
            "snapshot_id": "native:8",
            "revision": 91,
            "native_revision": 8,
            "date_raw": 53_366_664,
            "paused": True,
            "speed": 5,
            "map_ready": True,
            "played_character": {"character_id": PLAYER, "alive": True},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 1001},
            "active_event": {
                "instance_id": self.event_instance_id,
                "option_count": 4,
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

    def test_exact_reviewed_projection_selects_d_then_reaches_product(self) -> None:
        service = _Service()
        context = _context()

        def drain(
            _service: object, *, snapshot: object, identity: object
        ) -> dict[str, object]:
            self.assertIsInstance(snapshot, dict)
            self.assertEqual(identity["event_definition_key"], EVENT_KEY)
            service.event_key = "zg361we.360"
            service.event_instance_id = 622
            return {
                "result": "GREEN",
                "selected_option_number": 4,
                "selected_native_option_index": 3,
            }

        def identity(_service: object, _snapshot: object) -> dict[str, object]:
            if service.event_key == EVENT_KEY:
                return _identity(service, context)
            return {
                "event_instance_id": 622,
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
        ) as selection:
            result = capture.wait_for_native_event_definition(
                service,
                Path(temporary),
                stem="reviewed",
                expected_event_definition_key="zg361we.360",
                clear_unexpected_single_option_events=False,
                clear_reviewed_vanilla_event_interruptions=True,
            )

        self.assertEqual(result["identity"]["event_definition_key"], "zg361we.360")
        selection.assert_called_once()
        evidence = result["evidence"]
        self.assertEqual(len(evidence["cleared_reviewed_vanilla_interruptions"]), 1)
        self.assertEqual(
            evidence["reviewed_vanilla_decisions"][0]["result"], "GREEN"
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
