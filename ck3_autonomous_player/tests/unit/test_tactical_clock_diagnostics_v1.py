"""Offline clock diagnostics: synthetic endpoints, fake CPU and memory-only sinks."""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import threading
import textwrap
import types
import unittest
from unittest.mock import patch

from test_normal_three_day_route_window import _driver_case
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge import tactical_clock_diagnostics_v1 as diagnostic
from xar_autoplayer.bridge.driver import StepPostconditionError
from xar_autoplayer.bridge.exact_clock_wait_progress_v1 import WaitProgressV1, project_wait_progress_v1

FIXTURE = Path(__file__).parent / "fixtures/a11_original_failed_route_window_5279.json"
PROVENANCE = {
    "machine_id": "xenoamess-full-tower-eb9d2c1186",
    "observed_at_utc": "2026-10-20T12:46:15.066335+00:00",
    "raw_bytes": 7407,
    "raw_sha256": "90989721c68092de13bbaa080f4253d15de2c5b8fc39d5067ce50e13db275d1a",
    "bound_receipt_sha256": "7f54b37d794b1ff4232c7f3f8c4e40afd199f3ad7765cc44f80ba99d79f1d720",
    "source_json_path": "$.command_history[5278]",
    "public_response_sequence": 10534,
    "sequence_binding": "same step/error; original row has no public or native request ID",
}


def actual_row():
    raw = FIXTURE.read_bytes()
    assert len(raw) == PROVENANCE["raw_bytes"]
    assert hashlib.sha256(raw).hexdigest() == PROVENANCE["raw_sha256"]
    return json.loads(raw)


def execute_case(mode="success", *, early=False):
    driver, endpoint, plan, _, _ = _driver_case(early_arrival=early)
    old_hook = endpoint.send_hook
    original_packet = copy.deepcopy(driver.state._raw_state_snapshot)
    if mode != "success":
        def answer(frame):
            step = frame.get("step")
            if step in {"resume-map", "pause-map"}:
                if mode == "resume_unknown" and step == "resume-map":
                    return
                endpoint.publish({
                    "type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": True,
                    "result": {"step": step, "accepted": True, "status": "submitted"},
                })
                if step == "resume-map":
                    packet = copy.deepcopy(original_packet)
                    packet.update(revision=42, snapshot_id="native:42")
                    packet["state"].update(paused=False, speed=3)
                    endpoint.publish(packet)
            elif mode == "arm_rejected" and str(step).startswith("research-arm-tactical"):
                endpoint.publish({
                    "type": "command_result", "protocol_version": 1,
                    "request_id": frame["request_id"], "ok": False,
                    "error": "synthetic arm rejection",
                })
            else:
                old_hook(frame)
        endpoint.send_hook = answer
    result = error = None
    try:
        result = driver.execute_step(
            plan["selected_step"], expected_revision=int(driver.take_snapshot()["revision"]))
    except Exception as caught:
        error = caught
    wire = [frame["step"] for frame in endpoint.frames if frame.get("type") == "execute_step"]
    return driver, endpoint, result, error, wire


class Tests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ)
        self.environment.start()
        os.environ.pop("XAR_CK3_ARMY_TIMING_JSONL", None)
        self.addCleanup(self.environment.stop)
        retry = patch.object(native, "_LIFE_ADVANCE_TIMELINE_RETRY_SECONDS", 0.01)
        retry.start()
        self.addCleanup(retry.stop)

    def case(self, mode="success", *, early=False):
        values = execute_case(mode, early=early)
        self.addCleanup(values[0].close)
        return values

    def test_native_success_and_early_stop_keep_one_resume_without_cleanup(self):
        for early in (False, True):
            with self.subTest(early=early):
                driver, _, result, error, wire = self.case(early=early)
                self.assertIsNone(error)
                self.assertEqual(wire.count("resume-map"), 1)
                self.assertNotIn("pause-map", wire)
                self.assertEqual(result["elapsed_days"], 2 if early else 3)
                self.assertEqual(result["progress_status"], "postcondition")
                summary = result["tactical_clock_wait_progress_v1"]
                self.assertFalse(summary["native_event_time_verified"])
                self.assertIsNone(driver._exact_clock_wait_progress_v1)

    def test_failed_cleanup_keeps_four_returned_pause_receipts(self):
        driver, endpoint, _, error, wire = self.case("stall")
        self.assertIsInstance(error, StepPostconditionError)
        self.assertEqual(wire.count("resume-map"), 1)
        self.assertEqual(wire.count("pause-map"), 4)
        receipts = [row for row in error.step_result["actions"] if row.get("step") == "pause-map"]
        self.assertEqual(len(receipts), 4)
        self.assertTrue(all(row["result"]["status"] == "submitted" for row in receipts))
        value = diagnostic.tactical_clock_failure_v1(error)
        self.assertEqual(value["credit"], 0)
        self.assertTrue(value["never_replay"])
        self.assertIsNone(value["step_result"]["tactical_daily_sentinel"])
        self.assertEqual(value["step_result"]["armed_tactical_daily_sentinel"]["state"], "armed")
        self.assertLess(value["wait_progress"]["elapsed_ms"], 500)
        before = copy.deepcopy(error.step_result)
        packet = copy.deepcopy(driver.state._raw_state_snapshot)
        packet.update(revision=43, snapshot_id="native:43")
        packet["state"].update(paused=True, date_raw=packet["state"]["date_raw"] + 24)
        endpoint.publish(packet)
        self.assertEqual(error.step_result, before)
        self.assertIsNone(driver._exact_clock_wait_progress_v1)

    def test_unknown_resume_is_never_replayed(self):
        _, _, _, error, wire = self.case("resume_unknown")
        self.assertIsInstance(error, StepPostconditionError)
        self.assertEqual(wire.count("resume-map"), 1)
        self.assertIsNotNone(diagnostic.tactical_clock_failure_v1(error))

    def test_arm_rejection_installs_no_wait_collector_or_resume(self):
        driver, _, _, error, wire = self.case("arm_rejected")
        self.assertIsInstance(error, StepPostconditionError)
        self.assertNotIn("resume-map", wire)
        self.assertIsNone(driver._exact_clock_wait_progress_v1)
        self.assertIsNone(driver._exact_clock_observation_v1)

    def test_actual_historical_row_has_no_invented_pause_or_stop_evidence(self):
        row = actual_row()
        before = copy.deepcopy(row)
        error = StepPostconditionError(
            row["error"].removeprefix("StepPostconditionError: "),
            selected_step=row["command"], step_result=row["result"])
        value = diagnostic.tactical_clock_failure_v1(error)
        self.assertIsNotNone(value)
        self.assertEqual(value["step_result"]["external_pause_count"], 0)
        self.assertFalse(value["step_result"]["managed_failure_cleanup"]["attempted"])
        self.assertIsNone(value["step_result"]["tactical_daily_sentinel"])
        self.assertEqual(len(value["step_result"]["actions"]), 3)
        for action in value["step_result"]["actions"]:
            self.assertNotEqual(action["step"], "pause-map")
            self.assertIsNone(action["result"]["request_id"])
            self.assertIsNone(action["result"]["native_request_id"])
        self.assertEqual(value["credit"], 0)
        self.assertIsNone(value["wait_progress"])
        self.assertEqual(row, before)
        self.assertLessEqual(len(json.dumps(value).encode()), diagnostic.MAX_BYTES)

    def test_outer_plan_mutation_preserves_readonly_primitive_identity(self):
        row = actual_row()
        error = StepPostconditionError(
            "synthetic wrapper", selected_step=row["command"], step_result=row["result"])
        error.selected_step = "life-advance"
        value = diagnostic.tactical_clock_failure_v1(error)
        self.assertEqual(value["selected_step"], "life-advance")
        self.assertEqual(value["primitive_step"], row["command"])
        with self.assertRaises(AttributeError):
            error.primitive_step = "life-advance"
        foreign = StepPostconditionError(
            "foreign origin", selected_step="life-advance", step_result=row["result"])
        self.assertIsNone(diagnostic.tactical_clock_failure_v1(foreign))

    def test_scalar_types_remain_unknown_without_coercion(self):
        row = actual_row()
        for invalid in (True, 53274624.0):
            changed = copy.deepcopy(row["result"])
            changed["starting_date_raw"] = invalid
            value = diagnostic.build_tactical_clock_failure_v1(
                row["command"], row["command"], changed, None)
            self.assertIsNone(value["step_result"]["starting_date_raw"])
        changed = copy.deepcopy(row["result"])
        changed["actions"][0]["result"]["accepted"] = 0
        value = diagnostic.build_tactical_clock_failure_v1(
            row["command"], row["command"], changed, None)
        self.assertIsNone(value["step_result"]["actions"][0]["result"]["accepted"])

    def test_wait_decoder_rejects_float_bucket_zero_generation_and_empty_identity(self):
        driver, _, _, _, _ = self.case()
        snapshot = driver.take_internal_semantic_snapshot()
        baseline = WaitProgressV1(snapshot, 17).freeze(snapshot)
        self.assertIsNotNone(diagnostic.project_tactical_wait_progress_v1(baseline))
        for key, invalid in (
            ("bucket_ms", 5000.0), ("arm_generation", 0),
            ("identity", [0, 0, 0, ""]), ("identity", [4242, 1, 707, ""]),
        ):
            with self.subTest(key=key, invalid=invalid):
                changed = copy.deepcopy(baseline)
                changed[key] = invalid
                self.assertIsNone(project_wait_progress_v1(changed))
                self.assertIsNone(diagnostic.project_tactical_wait_progress_v1(changed))
        limited = {
            "schema": "xar.exact-clock-wait-progress.v1",
            "limit_exceeded": True, "native_event_time_verified": False,
        }
        self.assertEqual(diagnostic.project_tactical_wait_progress_v1(limited), limited)

    def test_ingest_and_finally_have_no_condition_collector_lock_inversion(self):
        driver, _, _, _, _ = self.case()
        snapshot = driver.take_internal_semantic_snapshot()
        observer = diagnostic.TacticalClockObservationV1()
        observer.start(driver, snapshot, 17)
        progress = observer.progress
        self.assertIsNotNone(progress)
        errors = []
        def ingest():
            try:
                driver._ingest({
                    "type": "heartbeat", "protocol_version": 1, "pid": 4242,
                    "sequence": 1, "monotonic_ms": 1,
                })
            except Exception as error:
                errors.append(error)
        def finish():
            try:
                observer.finish(driver, snapshot)
            except Exception as error:
                errors.append(error)
        progress.lock.acquire()
        threads = [threading.Thread(target=ingest), threading.Thread(target=finish)]
        try:
            threads[0].start()
            with driver.state._condition:
                pass
            threads[1].start()
            acquired = driver.state._condition.acquire(timeout=1)
            self.assertTrue(acquired)
            if acquired:
                driver.state._condition.release()
        finally:
            progress.lock.release()
        for thread in threads:
            thread.join(2)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertIsNone(driver._exact_clock_wait_progress_v1)
        frozen = copy.deepcopy(observer.summary)
        progress.received("heartbeat", {"pid": 4242}, (True, 1, 4242))
        self.assertEqual(observer.summary, frozen)

    def test_finishing_old_observer_preserves_foreign_collector(self):
        driver, _, _, _, _ = self.case()
        snapshot = driver.take_internal_semantic_snapshot()
        observer = diagnostic.TacticalClockObservationV1()
        observer.start(driver, snapshot, 17)
        foreign = WaitProgressV1(snapshot, 18)
        driver._exact_clock_wait_progress_v1 = foreign
        observer.finish(driver, snapshot)
        self.assertIs(driver._exact_clock_wait_progress_v1, foreign)
        driver._exact_clock_wait_progress_v1 = None

    def test_cpu_is_fake_and_timing_sink_is_memory_only(self):
        driver, _, _, _, _ = self.case()
        snapshot = driver.take_internal_semantic_snapshot()
        owner = types.SimpleNamespace(
            _exact_clock_wait_progress_v1=None, _exact_clock_observation_v1=None)
        rows = []
        class Writer:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def write(self, text):
                rows.append(json.loads(text))
        class Cpu:
            def __init__(self, pid):
                self.calls, self.closed = 0, False
            def sample(self):
                self.calls += 1
                return {
                    "creation_filetime": 777, "kernel_100ns": self.calls * 100,
                    "user_100ns": self.calls * 200, "host_monotonic_ms": 100 + self.calls,
                }
            def close(self):
                assert owner._exact_clock_observation_v1 is None
                self.closed = True
        def start(owner, snapshot):
            clock = diagnostic.ClockObservationV1("unused", snapshot, cpu_factory=Cpu)
            owner._exact_clock_observation_v1 = clock
            return clock
        with patch.object(diagnostic, "start_clock_observation_v1", start), patch(
                "pathlib.Path.open", lambda *args, **kwargs: Writer()):
            observer = diagnostic.TacticalClockObservationV1()
            observer.start(owner, snapshot, 17)
            advanced = copy.deepcopy(snapshot)
            advanced["date_raw"] += 24
            advanced["paused"] = True
            observer.clock.observe(advanced)
            observer.finish(owner, advanced)
        self.assertTrue(observer.clock.cpu.closed)
        self.assertEqual(rows[-1]["phase"], "resume_to_paused_final")
        self.assertTrue(all(row["cpu_delta_from_resume_100ns"] is not None for row in rows))

    def test_real_lf_encoder_matches_legacy_bytes_after_append_and_unicode(self):
        source = textwrap.dedent(inspect.getsource(native.NativeHeadlessGameplayDriver._encode_driver_state_locked))
        single_join = 'b"".join((*serialized_parts, b"\\n"))'
        self.assertEqual(source.count(single_join), 1)
        legacy = source.replace(single_join, 'b"".join(serialized_parts) + b"\\n"')
        namespace = dict(vars(native))
        exec(compile(legacy, "<legacy-lf-encode>", "exec"), namespace)
        encode = namespace["_encode_driver_state_locked"]
        driver, _, _, _, _ = self.case()
        for scenario in ("full", "append", "unicode"):
            if scenario == "append":
                driver._record_command("synthetic-only", ok=True, result={"value": 1})
            if scenario == "unicode":
                driver._record_command(
                    "synthetic-only", ok=True, result={"value": "\u7f57\u8d1d\u5c14", "tuple": (1, 2)})
            before = copy.deepcopy(driver._command_history)
            old_fields, new_fields = {}, {}
            with driver._driver_state_lock:
                old_bytes = encode(driver, persistence_fields=old_fields)
                new_bytes = driver._encode_driver_state_locked(persistence_fields=new_fields)
            self.assertEqual(old_bytes, new_bytes)
            self.assertTrue(old_bytes.endswith(b"\n"))
            self.assertEqual(old_fields, new_fields)
            self.assertEqual(driver._command_history, before)
