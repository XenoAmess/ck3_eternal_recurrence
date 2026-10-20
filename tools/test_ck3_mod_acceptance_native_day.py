"""Focused public-client/native-day producer and old-consumer contract tests."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from ck3_mod_acceptance_client import CaseClient
from ck3_mod_acceptance_native_day import project_native_day


def example_frame(date: int, revision: int) -> dict[str, object]:
    return {"date_raw": date, "revision": revision, "native_revision": revision,
        "paused": True, "map_ready": True, "active_event": None,
        "episode_projection": "native_campaign", "backend_id": "native-headless",
        "source": "injected-dll-named-pipe", "played_character": {
            "character_id": 31254, "alive": True, "source": "native"},
        "diagnostics": {"bridge_pid": 2052, "connection_generation": 1,
            "hello": {"pid": 2052, "connection_generation": 1, "ck3_build_match": True,
                "expected_ck3_version": "1.20.0.4", "expected_ck3_sha256": "EXAMPLE"}}}


def retained_inputs() -> tuple[dict[str, object], dict[str, object]]:
    actual, before = os.environ.get("XAR_NATIVE_DAY_ACTUAL"), os.environ.get("XAR_NATIVE_DAY_BEFORE")
    if actual and before:
        raw = json.loads(Path(actual).read_bytes())["rows"][0]
        opening = json.loads(Path(before).read_bytes())["rows"][-1]["after_snapshot"]
        return raw, opening
    first, after = example_frame(100, 10), example_frame(124, 11)
    return {"id": "authored-day", "ok": True, "error": None, "after_snapshot": after,
        "result": {"step": "life-advance-one-day", "source": "native-composite",
            "backend_id": "native-headless", "starting_date_raw": 100, "ending_date_raw": 124,
            "paused": True, "requested_horizon_days": 1, "active_event": None,
            "ordinary_events": [], "actions": [], "progress_status": "postcondition",
            "event_resolution": "none"}}, first


def capability_report(before: dict[str, object]) -> dict[str, object]:
    return {"steps": [], "readiness": before, "capabilities": {
        "action_steps": ["life-advance-one-day"], "bridge_capabilities": [
            "game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1",
            "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
            "game.command.query-current-event-window-context-v1"]}}


class Port:
    """Only backend publication is replaced; the real public method runs."""
    advance_day = CaseClient.advance_day
    validate_frame = CaseClient.validate_frame

    def __init__(self, output: Path, row: dict[str, object], before: dict[str, object]) -> None:
        self.output, self.row = output, row
        self.report = capability_report(before)
        self._seq, self._binding = 0, None
        hello = before["diagnostics"]["hello"]
        self.manifest = {"game": {"version": hello["expected_ck3_version"],
                                  "exe_sha256": hello["expected_ck3_sha256"]}}
        self.sent: list[dict[str, object]] = []
        self.error: Exception | None = None

    def guard(self, reserve: int = 90) -> dict[str, object]:
        if reserve != 90:
            raise ValueError("Original Quit reserve changed")
        return self.report

    def execute_plan(self, steps: list[dict[str, object]], name: str,
                     timeout: float | None = None, reserve: int = 90) -> list[dict[str, object]]:
        if reserve != 90:
            raise ValueError("Original execution reserve changed")
        self.sent.extend(steps)
        if self.error:
            raise self.error
        return [copy.deepcopy(self.row)]

    def checkpoint(self, name: str, value: object) -> Path:
        return CaseClient.checkpoint(self, name, value)


class NativeDayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw, self.before = retained_inputs()
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("XAR_NATIVE_DAY_SCRATCH"))
        self.addCleanup(self.temp.cleanup)
        self.port = Port(Path(self.temp.name), self.raw, self.before)

    def projected(self) -> dict[str, object]:
        return project_native_day(self.raw, self.before, allow_event_boundary=False)

    def test_actual_producer_projector_then_original_day_consumer(self) -> None:
        original = os.environ.get("XAR_NATIVE_DAY_ORIGINAL_CLIENT")
        projected = self.port.advance_day()
        self.assertEqual(projected["result"]["elapsed_hours"], 24)
        self.assertEqual(len(self.port.sent), 1)
        self.assertEqual(self.port.sent[0]["tool"], "ck3_execute_step")
        self.assertEqual(self.port.sent[0]["args"]["expected_revision"], self.before["revision"])
        self.assertEqual(self.raw["result"]["step"], "life-advance-one-day")
        if original:
            spec = importlib.util.spec_from_file_location("original_native_day_client", original)
            self.assertIsNotNone(spec)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            old_port = Port(Path(self.temp.name), projected, self.before)
            consumed = module.CaseClient.advance_day(old_port)
            self.assertEqual(consumed["result"]["elapsed_hours"], 24)

    def test_unsupported_and_actor_change_preserve_original_route(self) -> None:
        for actor_change in (False, True):
            port = Port(Path(self.temp.name), self.projected(), self.before)
            if not actor_change:
                port.report["capabilities"]["action_steps"] = []
            port.advance_day(allow_event_boundary=True, allow_actor_change=actor_change)
            self.assertEqual(port.sent[0]["kind"], "advance_day")
            self.assertNotIn("tool", port.sent[0])

    def test_unknown_dispatch_never_falls_back_or_repeats(self) -> None:
        self.port.error = TimeoutError("authored ACK lost")
        with self.assertRaises(TimeoutError):
            self.port.advance_day()
        self.assertEqual(len(self.port.sent), 1)
        self.assertEqual(self.port.sent[0]["tool"], "ck3_execute_step")

    def test_missing_typed_event_capability_preserves_original_route(self) -> None:
        self.port.row = self.projected()
        self.port.report["capabilities"]["bridge_capabilities"].remove(
            "game.command.query-current-event-window-context-v1")
        self.port.advance_day(allow_event_boundary=True)
        self.assertEqual(len(self.port.sent), 1)
        self.assertEqual(self.port.sent[0]["kind"], "advance_day")
        self.assertNotIn("tool", self.port.sent[0])

    def test_invalid_paused_owner_frame_prevents_dispatch(self) -> None:
        self.port.report["readiness"]["paused"] = False
        with self.assertRaises(ValueError):
            self.port.advance_day()
        self.assertEqual(self.port.sent, [])

    def test_bool_days_and_wrong_post_date_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.port.advance_day(True)
        self.assertEqual(self.port.sent, [])
        broken = copy.deepcopy(self.raw)
        broken["result"]["ending_date_raw"] += 24
        self.port.row = broken
        with self.assertRaises(ValueError):
            self.port.advance_day()
        self.assertEqual(len(self.port.sent), 1)

    def test_event_boundary_is_actual_full_after_frame(self) -> None:
        row = copy.deepcopy(self.raw)
        event = {"event_instance_id": 9, "event_id": "authored.event"}
        row["after_snapshot"]["active_event"] = event
        row["result"]["active_event"] = event
        row["result"]["event_resolution"] = "typed_query_required"
        self.port.row = row
        projected = self.port.advance_day(allow_event_boundary=True)
        self.assertEqual(projected["result"]["event_boundary"], row["after_snapshot"])
        self.assertEqual(projected["result"]["selected_event_options"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
