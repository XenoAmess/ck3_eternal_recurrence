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
from ck3_mod_acceptance_native_day import project_native_day, obj, integer
from ck3_mod_acceptance_cases.faith_e02_pilgrimage_adapter import BudgetedClient


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
    snapshot = CaseClient.snapshot

    def __init__(self, output: Path, row: dict[str, object], before: dict[str, object]) -> None:
        self.output, self.row = output, row
        self.report = capability_report(before)
        self.fresh_before = copy.deepcopy(before)
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
        if len(steps) == 1 and steps[0].get("tool") == "ck3_take_snapshot":
            return [{"id": steps[0]["id"], "result": copy.deepcopy(self.fresh_before)}]
        if self.error:
            raise self.error
        return [copy.deepcopy(self.row)]

    def world_calls(self) -> list[dict[str, object]]:
        return [step for step in self.sent if step.get("tool") != "ck3_take_snapshot"]

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
        self.assertEqual(len(self.port.world_calls()), 1)
        self.assertEqual(self.port.world_calls()[0]["tool"], "ck3_execute_step")
        self.assertEqual(self.port.world_calls()[0]["args"]["expected_revision"], self.before["revision"])
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
        self.assertEqual(len(self.port.world_calls()), 1)
        self.assertEqual(self.port.world_calls()[0]["tool"], "ck3_execute_step")

    def test_missing_typed_event_capability_preserves_original_route(self) -> None:
        self.port.row = self.projected()
        self.port.report["capabilities"]["bridge_capabilities"].remove(
            "game.command.query-current-event-window-context-v1")
        self.port.advance_day(allow_event_boundary=True)
        self.assertEqual(len(self.port.world_calls()), 1)
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
        self.assertEqual(len(self.port.world_calls()), 1)

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


    def test_retained_229_report_binds_fresh_230_before_single_dispatch(self) -> None:
        wire = os.environ.get("XAR_NATIVE_DAY_REFRESH_WIRE")
        before, fresh = example_frame(100, 229), example_frame(100, 230)
        if wire:
            frames: dict[int, dict[str, object]] = {}
            for raw in Path(wire).read_bytes().splitlines():
                record = obj(json.loads(raw), "retained MCP record")
                message = obj(record.get("message"), "retained MCP message")
                if record.get("direction") == "server-to-client" and message.get("id") in (855, 857):
                    result = obj(message.get("result"), "retained MCP result")
                    frames[integer(message.get("id"), "MCP id")] = obj(
                        result.get("structuredContent"), "retained snapshot")
            before, fresh = frames[855], frames[857]
        self.assertEqual(before["revision"], 229)
        self.assertEqual(fresh["revision"], 230)
        after = copy.deepcopy(fresh)
        after["date_raw"] = integer(fresh["date_raw"], "fresh date") + 24
        after["revision"] = 231
        after["native_revision"] = integer(fresh["native_revision"], "fresh native revision") + 1
        row = copy.deepcopy(self.raw)
        row["after_snapshot"] = after  # Authored ending frame, not a new live day.
        value = obj(row["result"], "authored result")
        value.update(starting_date_raw=fresh["date_raw"], ending_date_raw=after["date_raw"])
        row["result"] = value
        port = Port(Path(self.temp.name), row, before)
        port.fresh_before = fresh
        result = port.advance_day()
        self.assertEqual(result["result"]["elapsed_hours"], 24)
        self.assertEqual(len(port.sent), 2)
        self.assertEqual(port.sent[0]["tool"], "ck3_take_snapshot")
        self.assertEqual(len(port.world_calls()), 1)
        self.assertEqual(port.world_calls()[0]["args"]["expected_revision"], 230)
        self.assertIs(port.world_calls()[0]["fresh_revision"], False)

    def test_fresh_before_owner_build_pause_event_or_date_failure_never_dispatches(self) -> None:
        for changed in ("actor", "build", "paused", "event", "date"):
            with self.subTest(changed=changed):
                port = Port(Path(self.temp.name), self.raw, self.before)
                if changed == "actor":
                    port.fresh_before["played_character"]["character_id"] += 1
                elif changed == "build":
                    port.fresh_before["diagnostics"]["hello"]["expected_ck3_sha256"] = "wrong"
                elif changed == "paused":
                    port.fresh_before["paused"] = False
                elif changed == "event":
                    port.fresh_before["active_event"] = {"instance_id": 5}
                else:
                    port.fresh_before["date_raw"] += 24
                with self.assertRaises(ValueError):
                    port.advance_day()
                self.assertEqual(port.world_calls(), [])
                self.assertEqual(len(port.sent), 1)

    def test_p3_counts_readonly_before_and_dispatch_without_double_charging(self) -> None:
        budgeted = BudgetedClient(self.port, 2)
        budgeted.advance_day()
        self.assertEqual(budgeted.public_requests_used, 2)
        self.assertEqual(len(self.port.sent), 2)
        self.assertEqual(len(self.port.world_calls()), 1)
        refused = Port(Path(self.temp.name), self.raw, self.before)
        with self.assertRaises(ValueError):
            BudgetedClient(refused, 1).advance_day()
        self.assertEqual(refused.sent, [])


    def test_fresh_event_zero_hour_boundary_reaches_original_journey_and_first_option(self) -> None:
        # Reuse owned modal I/O, but execute the actual Journey.run/drain/event
        # implementations. Only unrelated activity-identity I/O stops the finite
        # consumer after its independent event disappearance has been observed.
        import test_faith_e02_pilgrimage_event_policy as modal

        class StopAfterDrain(Exception):
            pass

        class BoundaryClient(modal.ModalClient):
            def __init__(self, path: Path) -> None:
                super().__init__(path)
                self.event_key = "synthetic.unregistered"
                self.displayed = [modal.option(0, 2, "first"), modal.option(1, 6, "later")]
                self.install()
                self.next_event = copy.deepcopy(self.current["active_event"])
                self.current["active_event"] = None
                self.day_sent: list[dict[str, object]] = []
                self.day_boundary: dict[str, object] = {}
                self.conservative_claim = 0

            def advance_day(self, days: int = 1, timeout: float = 300,
                            allow_event_boundary: bool = False,
                            allow_actor_change: bool = False) -> dict[str, object]:
                before = copy.deepcopy(self.current)
                port = Port(self.output, {}, before)
                port.fresh_before = copy.deepcopy(before)
                port.fresh_before["revision"] += 1
                port.fresh_before["active_event"] = copy.deepcopy(self.next_event)
                counted = BudgetedClient(port, 2)
                row = counted.advance_day(days, timeout, allow_event_boundary, allow_actor_change)
                self.conservative_claim = counted.public_requests_used
                self.day_sent = port.sent
                self.day_boundary = row
                self.current = copy.deepcopy(row["after_snapshot"])
                return row

        class JourneyConsumer(modal.JOURNEY._Journey):
            def observe_identity(self, frame: dict[str, object], reason: str) -> dict[str, object]:
                if reason == "after_actual_interruption":
                    raise StopAfterDrain("Finite activity-read seam after real event drain")
                self.last_identity_date = integer(frame.get("date_raw"), "fixture date")
                return frame

        context, _, binding, identity = modal.PilgrimageEventPolicyTests().make(self.temp.name)
        client = BoundaryClient(Path(self.temp.name))
        journey = JourneyConsumer(context, client, binding, identity, {})
        with self.assertRaises(StopAfterDrain):
            journey.run()
        row = client.day_boundary
        value = obj(row["result"], "pre-day boundary")
        self.assertEqual(row["source"], "actual-pre-day-snapshot-event-boundary")
        self.assertIs(row["world_dispatch_attempted"], False)
        self.assertEqual(row["id"], "case-snapshot-0001")
        self.assertEqual(value["elapsed_hours"], 0)
        self.assertIs(value["requested_interval_complete"], False)
        self.assertNotIn("native_day_raw_result", row)
        self.assertEqual([step["tool"] for step in client.day_sent], ["ck3_take_snapshot"])
        self.assertEqual(client.conservative_claim, 2)
        self.assertEqual(journey.result["day_requests"], 1)
        self.assertEqual(journey.result["elapsed_hours"], 0)
        self.assertEqual(journey.result["observed_days"], 0)
        receipt = journey.result["event_receipts"][0]
        self.assertTrue(receipt["ack_accepted"])
        self.assertTrue(receipt["old_instance_gone_in_independent_snapshot"])
        self.assertIsNone(receipt["independent_after_snapshot"]["active_event"])
        selections = modal.PilgrimageEventPolicyTests.selections(client)
        self.assertEqual(len(selections), 1)
        self.assertEqual(selections[0]["option_number"], 3)
        captured = json.loads(Path(receipt["offline_analysis_input"]["path"]).read_text(encoding="utf-8"))
        self.assertEqual(captured["typed_context"]["current_event_instance_id"], 9)
        self.assertEqual(captured["typed_context"]["options"][0]["native_option_index"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
