"""Cached evidence from actual clock composites and native-state ingest; no game."""
from __future__ import annotations
import copy
import json
import unittest
from typing import Callable
from unittest.mock import patch

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot, _tactical_sentinel_status
from test_normal_three_day_route_window import _driver_case
from test_step_postcondition_primitive_identity import failure
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge import tactical_clock_diagnostics_v1 as tactical
from xar_autoplayer.bridge import exact_clock_failure_diagnostic_v1 as exact
from xar_autoplayer.bridge.cached_native_clock_summary_v1 import (
    CachedNativeClockCollectorV1, capture_native_clock_cache_v1,
    parse_cached_native_clock_summary_v1, PhaseV1, SampleV1,
    ObserverAvailableV1, MailboxAvailableV1, UnavailableV1,
)
from xar_autoplayer.bridge.driver import StepPostconditionError


def _mapping(value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise AssertionError("fixture requires a JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise AssertionError("fixture requires string keys")
        result[key] = item
    return result


def _heartbeat(sequence: int) -> dict[str, object]:
    return {
        "type": "heartbeat", "protocol_version": 1, "pid": 4242,
        "sequence": sequence, "monotonic_ms": 100000 + sequence,
        "main_thread_query_mailbox_v1": {
            "pump_epochs": 149850, "owner_verified_pump_epochs": 149850,
            "published_sequence": sequence, "completed_sequence": sequence - 1,
            "executor_started_requests": sequence, "executor_started_sequence": sequence,
            "executor_started_pump_epoch": 149850, "executed_requests": sequence - 1,
            "owner_tid": 17204, "current_tid": 17204, "failure": 0, "stop": False,
        },
        "snapshot_observer_12002": {
            "started_ms": 100010, "completed_ms": 100000, "last_read_ms": 9,
            "read_in_progress": True, "last_read_available": False, "snapshot_cached": False,
        },
    }


def _clock_case(kind: str, deny_cleanup_snapshot: bool = False) -> tuple[
    StepPostconditionError, list[str], int
]:
    if kind == "battle":
        driver, endpoint, plan, _, _ = _driver_case()
        packet = copy.deepcopy(driver.state._raw_state_snapshot)
        prior = endpoint.send_hook
    else:
        endpoint = FakeEndpoint()
        driver = native.NativeHeadlessGameplayDriver(
            endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=.03,
            life_advance_timeout_seconds=.03)
        endpoint.publish(_hello(
            "game.state.snapshot", "game.command.set-speed-3", "game.command.resume-map",
            "game.command.pause-map", "game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-cancel-tactical-daily-sentinel-v1-generation-N",
            "game.command.research-query-tactical-daily-sentinel-v1"))
        packet = _snapshot(1, date_raw=24000, speed=3,
                           played_character={"character_id": 40526, "alive": True})
        endpoint.publish(packet)
        plan, prior = {}, None
    sequence = 1
    endpoint.publish(_heartbeat(sequence))

    def answer(request: dict[str, object]) -> None:
        nonlocal sequence
        if request.get("type") != "execute_step":
            return
        step = request["step"]
        assert type(step) is str
        if step in {"resume-map", "pause-map"}:
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True,
                "result": {"step": step, "accepted": True, "status": "submitted"}})
            if step == "resume-map":
                running = copy.deepcopy(packet)
                running.update(revision=42, snapshot_id="native:42")
                running["state"].update(paused=False, speed=3)
                endpoint.publish(running)
        elif prior is not None:
            prior(request)
        else:
            result: dict[str, object] = {"step": step, "accepted": True, "status": "available"}
            if step.startswith("research-arm-tactical"):
                result["tactical_daily_sentinel"] = _tactical_sentinel_status(
                    state="armed", generation=42, starting_date_raw=24000, target_date_raw=24024,
                    observed_date_raw=24000, speed=3, mode="terminal_or_sentinel",
                    army_count=0, combat_count=0)
            elif step.startswith("research-cancel"):
                result["status"] = "canceled"
            endpoint.publish({"type": "command_result", "protocol_version": 1,
                "request_id": request["request_id"], "ok": True, "result": result})
        sequence += 1
        endpoint.publish(_heartbeat(sequence))

    endpoint.send_hook = answer
    blocked = 0
    denied = False
    original_take = driver.take_internal_semantic_snapshot
    original_wait = driver._wait_for_life_advance_snapshot

    def take() -> dict[str, object]:
        nonlocal blocked
        if denied:
            blocked += 1
            raise native.BridgeUnavailableError("synthetic cleanup snapshot unavailable")
        return _mapping(original_take())

    def wait(snapshot: dict[str, object], predicate: Callable[[dict[str, object]], bool],
             *, timeout_seconds: float) -> dict[str, object]:
        nonlocal denied
        result = _mapping(original_wait(snapshot, predicate, timeout_seconds=timeout_seconds))
        if deny_cleanup_snapshot and result.get("paused") is False and not predicate(result):
            denied = True
        return result

    driver.take_internal_semantic_snapshot = take
    driver._wait_for_life_advance_snapshot = wait
    error = None
    try:
        with patch.object(native, "_LIFE_ADVANCE_TIMELINE_RETRY_SECONDS", .001):
            try:
                if kind == "battle":
                    driver.execute_step(plan["selected_step"])
                else:
                    driver._advance_exact_day_with_sentinel(
                        original_take(), speed=3, actions=[])
            except StepPostconditionError as caught:
                error = caught
        assert isinstance(error, StepPostconditionError)
        commands: list[str] = []
        for frame in endpoint.frames:
            if frame.get("type") == "execute_step":
                command: object = frame.get("step")
                assert type(command) is str
                commands.append(command)
        return error, commands, blocked
    finally:
        driver.close()


class CachedClockSummaryTests(unittest.TestCase):
    def _assert_case(self, kind: str, deny: bool) -> None:
        error, commands, blocked = _clock_case(kind, deny)
        projection = (tactical.tactical_clock_failure_v1(error) if kind == "battle"
                      else exact.exact_clock_failure_diagnostic_v1(error))
        assert projection is not None
        summary = projection["cached_native_clock_summary_v1"]
        self.assertEqual(summary["not_on_wire"], ["active_hook_calls", "state"])
        self.assertIs(summary["cached_only"], True)
        self.assertIs(summary["atomic_observation"], False)
        self.assertIs(summary["native_event_time_verified"], False)
        phases: dict[PhaseV1, SampleV1] = {row["phase"]: row for row in summary["samples"]}
        self.assertIn("pre_resume", phases)
        self.assertIn("wait_final", phases)
        self.assertIn("cleanup_final", phases)
        self.assertEqual(commands.count("resume-map"), 1)
        self.assertEqual(projection["credit"], 0)
        self.assertIs(projection["never_replay"], True)
        final = phases["cleanup_final"]
        assert final["status"] == "available"
        observer: ObserverAvailableV1 | UnavailableV1 = final["observer"]
        mailbox: MailboxAvailableV1 | UnavailableV1 = final["mailbox"]
        assert observer["status"] == "available" and mailbox["status"] == "available"
        self.assertEqual(observer["value"]["started_ms"], "100010")
        self.assertEqual(observer["value"]["completed_ms"], "100000")
        self.assertEqual(observer["value"]["last_read_ms"], "9")
        self.assertIs(observer["value"]["last_read_available"], False)
        self.assertIs(observer["value"]["read_in_progress"], True)
        self.assertEqual(mailbox["value"]["owner_tid"], 17204)
        self.assertEqual(parse_cached_native_clock_summary_v1(json.loads(json.dumps(summary))), summary)
        if deny:
            self.assertGreater(blocked, 0)
            self.assertEqual(commands.count("pause-map"), 0)

    def test_battle_actual_failure_output(self) -> None:
        self._assert_case("battle", False)

    def test_exact_day_actual_failure_output(self) -> None:
        self._assert_case("exact", False)

    def test_battle_cleanup_snapshot_unavailable_still_preserves_cache(self) -> None:
        self._assert_case("battle", True)

    def test_exact_day_cleanup_snapshot_unavailable_still_preserves_cache(self) -> None:
        self._assert_case("exact", True)

    def test_runtime_types_missing_null_and_json_validation(self) -> None:
        base: dict[str, object] = {"connected": True, "bridge_pid": 4242,
            "connection_generation": 1, "last_heartbeat": _heartbeat(3)}
        for value in (True, 1.0, (1 << 53)):
            with self.subTest(value=value):
                diag = copy.deepcopy(base)
                heartbeat = _mapping(diag["last_heartbeat"])
                observer = _mapping(heartbeat["snapshot_observer_12002"])
                observer["started_ms"] = value
                heartbeat["snapshot_observer_12002"] = observer
                diag["last_heartbeat"] = heartbeat
                sample = capture_native_clock_cache_v1(diag, (4242, 1), "wait_final")
                assert sample["status"] == "available"
                self.assertEqual(sample["observer"]["status"], "unavailable")
        for raw, reason in (({}, "missing"), ({"started_ms": None}, "null"),
                            ({"started_ms": False}, "type")):
            with self.subTest(raw=raw):
                diag = copy.deepcopy(base)
                heartbeat = _mapping(diag["last_heartbeat"])
                heartbeat["snapshot_observer_12002"] = raw
                diag["last_heartbeat"] = heartbeat
                sample = capture_native_clock_cache_v1(diag, (4242, 1), "wait_final")
                assert sample["status"] == "available"
                unavailable = sample["observer"]
                assert unavailable["status"] == "unavailable"
                self.assertEqual(unavailable["reason"], reason)
        collector = CachedNativeClockCollectorV1((4242, 1))
        collector.capture("wait_final", base)
        summary = collector.summary()
        for wrong in (True, 1.0):
            bad = _mapping(json.loads(json.dumps(summary)))
            bad["bridge_pid"] = wrong
            self.assertIsNone(parse_cached_native_clock_summary_v1(bad))
        bad = _mapping(json.loads(json.dumps(summary)))
        samples = bad["samples"]
        assert type(samples) is list
        row = _mapping(samples[0])
        observer = _mapping(row["observer"])
        data = _mapping(observer["value"])
        data["started_ms"] = "01"
        observer["value"] = data
        row["observer"] = observer
        samples[0] = row
        self.assertIsNone(parse_cached_native_clock_summary_v1(bad))

    def test_cached_extension_keeps_original_exact_body_size_guard(self) -> None:
        error = failure()
        collector = CachedNativeClockCollectorV1((4242, 1))
        collector.capture("wait_final", {"connected": True, "bridge_pid": 4242,
            "connection_generation": 1, "last_heartbeat": _heartbeat(3)})
        error.step_result["before_cleanup_actions"] = [{"error": "x" * 9000}]
        self.assertIsNone(exact.exact_clock_failure_diagnostic_v1(error))
        error.step_result["cached_native_clock_summary_v1"] = collector.summary()
        self.assertIsNone(exact.exact_clock_failure_diagnostic_v1(error))
