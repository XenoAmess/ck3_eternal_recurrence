#!/usr/bin/env python3
"""Exercise the production timeline through AF4's delayed AF5 delivery."""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player" / "src"))
sys.path.insert(0, str(ROOT / "tools"))

import zg361_phase2_promotion_source_production_entry as production


class ScheduledCompensationService:
    """Native service model: a selection schedules a game-date ticket.

    The clock cannot deliver the next event while paused. This models the
    production boundary R400's pure polling callback did not drive. Event
    lookup, contract validation, option selection and map controls all run
    through the actual production entry implementation.
    """

    def __init__(self, *, start_at_af5: bool = False,
                 af5_indices: tuple[int, ...] = (39, 40, 41)) -> None:
        self.date_raw = 53183256
        self.elapsed = 0.0
        self.revision = 4
        self.paused = True
        self.speed = 5
        self.active_instance: int | None = 85 if start_at_af5 else 84
        self.active_indices = af5_indices if start_at_af5 else (36, 37, 38)
        self.af5_indices = af5_indices
        self.pending_events: list[tuple[int, int, tuple[int, ...]]] = []
        self.actions: list[str] = []
        self.event_queries: list[tuple[int, tuple[int, ...]]] = []
        self.observed_paused_null = False
        self.running_days = 0

    def snapshot(self) -> dict[str, object]:
        if self.paused and self.active_instance is None:
            self.observed_paused_null = True
        return {
            "map_ready": True,
            "snapshot_id": f"native:{self.revision}",
            "revision": self.revision,
            "native_revision": self.revision,
            "date_raw": self.date_raw,
            "played_character": {"character_id": 32904},
            "diagnostics": {"connection_generation": 1, "bridge_pid": 400},
            "paused": self.paused,
            "speed": self.speed,
            "active_event": (
                {"instance_id": self.active_instance, "option_count": 42}
                if self.active_instance is not None else None
            ),
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int,
    ) -> dict[str, object]:
        self._require_revision(expected_revision)
        if not self.paused or event_instance_id != self.active_instance:
            raise AssertionError("event query must bind the current paused event")
        self.event_queries.append((event_instance_id, self.active_indices))
        context = {
            "schema": "current-event-window-context-v1",
            "schema_version": 1,
            "status": "available",
            "window_match_count": 1,
            "event_definition_key": "zg361comp.1",
            "current_event_instance_id": event_instance_id,
            "snapshot_revision": self.revision,
            "date_raw": self.date_raw,
            "root_scope": {
                "status": "available", "type_key": "character",
                "typed_identity": {
                    "status": "available", "kind": "character",
                    "character_id": 32904,
                },
            },
            "saved_scopes": [],
            "options": [
                {"rendered_index": index, "native_option_index": native,
                 "shown": True, "enabled": True,
                 "fallback": False, "cancel": False}
                for index, native in enumerate(self.active_indices)
            ],
        }
        return {
            "status": "available",
            "binding": {
                "snapshot_id": f"native:{self.revision}",
                "revision": self.revision, "native_revision": self.revision,
                "date_raw": self.date_raw, "event_instance_id": event_instance_id,
            },
            "current_event_window_context": context,
        }

    def query_zhongguo_promotion_source_progress_v1(
        self, request_nonce: str, *, expected_revision: int,
    ) -> dict[str, object]:
        self._require_revision(expected_revision)
        if not self.paused:
            raise AssertionError("progress observation requires a paused frame")
        return {
            "status": "available",
            "query_sequence": self.revision,
            "zhongguo_promotion_source_progress": {
                "widgets": [
                    {"effective_visible": {"status": "available", "value": i == 3}}
                    for i in range(5)
                ],
            },
        }

    def select_event_option(
        self, option_number: int, *, event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        self._require_revision(expected_revision)
        if not self.paused or event_instance_id != self.active_instance:
            raise AssertionError("selection crossed the current paused frame")
        if option_number != 37 or self.active_indices != (36, 37, 38):
            raise AssertionError("the timeline must use AF4 route 1 and park before AF5")
        self.actions.append("select-event-option-37")
        self.pending_events.append((self.date_raw + 24, 85, self.af5_indices))
        self.active_instance = None
        self.active_indices = ()
        self.revision += 1
        return {
            "accepted": True, "status": "submitted",
            "option_number": option_number, "option_index": option_number - 1,
            "event_selection": {
                "postcondition_verified": True,
                "old_event_instance_id": event_instance_id,
                "new_event_instance_id": None,
                "selected_option_number": option_number,
                "selected_native_option_index": option_number - 1,
            },
        }

    def execute_step(self, step: str, *, expected_revision: int) -> dict[str, object]:
        self._require_revision(expected_revision)
        self.actions.append(step)
        if step == "resume-map":
            if self.active_instance is not None:
                raise AssertionError("cannot resume through a visible event")
            self.paused = False
        elif step == "pause-map":
            self.paused = True
        elif step == "set-speed-5":
            self.speed = 5
        else:
            raise AssertionError(f"unexpected action: {step}")
        self.revision += 1
        return {"accepted": True, "status": "submitted"}

    def sleep(self, seconds: float) -> None:
        self.elapsed += seconds
        if self.paused:
            return
        self.date_raw += 24
        self.running_days += 1
        self.revision += 1
        due = [ticket for ticket in self.pending_events if ticket[0] <= self.date_raw]
        if due:
            ticket = due[0]
            self.pending_events.remove(ticket)
            _, self.active_instance, self.active_indices = ticket
            # CK3's modal event pauses delivery before the event query.
            self.paused = True

    def _require_revision(self, expected_revision: int) -> None:
        if expected_revision != self.revision:
            raise AssertionError("test service received a stale revision")


class AF5TimelineTests(unittest.TestCase):
    def drive(self, service: ScheduledCompensationService) -> dict[str, object]:
        return production.enter_promotion_source_checkpoint_v1(
            service,
            timeout_seconds=2.0,
            poll_interval_seconds=0.05,
            pause_on_event_definition_key="zg361comp.1",
            pause_on_event_option_number=42,
            clock=lambda: service.elapsed,
            sleeper=service.sleep,
        )

    def test_af4_selection_requires_running_day_before_af5_can_be_observed(self) -> None:
        service = ScheduledCompensationService()
        result = self.drive(service)
        self.assertEqual(result["result"], "GREEN")
        self.assertEqual(result["target_binding"]["event_instance_id"], 85)
        self.assertEqual(result["target_occurrence_index"], 2)
        self.assertEqual(service.actions, ["select-event-option-37", "resume-map"])
        self.assertTrue(service.observed_paused_null)
        self.assertEqual(service.running_days, 1)
        self.assertTrue(service.paused)
        self.assertEqual(service.date_raw, 53183280)
        self.assertEqual(service.pending_events, [])
        self.assertIn((84, (36, 37, 38)), service.event_queries)
        self.assertIn((85, (39, 40, 41)), service.event_queries)
        drains = result["timeline_interrupt_drains"]
        self.assertEqual(len(drains), 1)
        self.assertEqual(drains[0]["selection"]["option_number"], 37)
        self.assertEqual(drains[0]["selection"]["option_index"], 36)
        self.assertEqual(drains[0]["result"], "GREEN")

    def test_initial_af5_parks_without_actions_for_each_resource_projection(self) -> None:
        for indices in ((39, 40, 41), (40, 41), (41,)):
            with self.subTest(indices=indices):
                service = ScheduledCompensationService(start_at_af5=True, af5_indices=indices)
                before = copy.deepcopy(service.snapshot())
                result = self.drive(service)
                self.assertEqual(result["result"], "GREEN")
                self.assertEqual(result["target_binding"]["event_instance_id"], 85)
                self.assertEqual(result["target_occurrence_index"], 1)
                self.assertEqual(service.actions, [])
                self.assertEqual(service.running_days, 0)
                self.assertEqual(service.snapshot(), before)
                self.assertEqual(service.event_queries, [(85, indices)])


if __name__ == "__main__":
    unittest.main()
