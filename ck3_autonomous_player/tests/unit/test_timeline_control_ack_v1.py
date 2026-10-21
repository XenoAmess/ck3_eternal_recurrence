"""Actual primitive producer to clock diagnostics; native endpoints are synthetic."""
from __future__ import annotations

import copy
import json
from typing import Literal
import unittest

from test_native_bridge_driver import FakeEndpoint, _hello, _snapshot
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge.tactical_clock_diagnostics_v1 import build_tactical_clock_failure_v1
from xar_autoplayer.bridge.route_contact_window_contract import advance_route_contact_window_step
from xar_autoplayer.bridge.timeline_control_ack_v1 import normalize_timeline_control_ack_v1

Step = Literal["pause-map", "resume-map"]


def _frame(step: Step, request_id: str = "step-1-0123456789ab") -> dict[str, object]:
    return {
        "type": "command_result", "protocol_version": 1, "request_id": request_id,
        "ok": True, "result": {"step": step, "accepted": True, "status": "submitted"},
    }


def _driver() -> tuple[native.NativeHeadlessGameplayDriver, FakeEndpoint]:
    endpoint = FakeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(
        endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=0.01)
    endpoint.publish(_hello("game.state.snapshot", "game.command.pause-map", "game.command.resume-map"))
    endpoint.publish(_snapshot(1, played_character={"character_id": 40526, "alive": True}))
    return driver, endpoint


def _commands(endpoint: FakeEndpoint) -> list[dict[str, object]]:
    return [frame for frame in endpoint.frames if frame.get("type") == "execute_step"]


class TimelineControlAckTests(unittest.TestCase):
    def _actual_producer_consumer(self, step: Step, internal: bool) -> None:
        driver, endpoint = _driver()
        frames: list[dict[str, object]] = []

        def answer(request: dict[str, object]) -> None:
            request_id = request["request_id"]
            assert type(request_id) is str
            frame = _frame(step, request_id)
            frames.append(copy.deepcopy(frame))
            endpoint.publish(frame)

        endpoint.send_hook = answer
        try:
            ack = driver._execute_primitive_step(
                step, internal_semantic_snapshot=internal, protocol_request_id="step-1-0123456789ab")
            self.assertEqual(ack["native_request_id"], "step-1-0123456789ab")
            self.assertNotIn("request_id", ack)
            self.assertIs(ack["accepted"], True)
            self.assertEqual(ack["status"], "submitted")
            self.assertEqual(frames, [_frame(step)])
            self.assertEqual(len(_commands(endpoint)), 1)
            primitive = advance_route_contact_window_step(11, 2585, (21,), horizon_days=3)
            result: dict[str, object] = {
                "step": primitive, "source": "native-tactical-daily-sentinel-composite",
                "sentinel_scope": "route_contact_window", "progress_status": "postcondition_failed",
                "watch_army_ids": [11], "actions": [{"step": step, "result": ack}],
            }
            decoded: object = json.loads(json.dumps(result))
            assert type(decoded) is dict
            diagnostic = build_tactical_clock_failure_v1(primitive, primitive, decoded, None)
            assert diagnostic is not None
            projected = diagnostic["step_result"]["actions"][0]["result"]
            self.assertEqual(projected["native_request_id"], ack["native_request_id"])
            self.assertIsNone(projected["request_id"])
            self.assertEqual(diagnostic["credit"], 0)
            self.assertIs(diagnostic["never_replay"], True)
        finally:
            driver.close()

    def test_actual_producer_pause_public(self) -> None:
        self._actual_producer_consumer("pause-map", False)

    def test_actual_producer_resume_public(self) -> None:
        self._actual_producer_consumer("resume-map", False)

    def test_actual_producer_pause_internal(self) -> None:
        self._actual_producer_consumer("pause-map", True)

    def test_actual_producer_resume_internal(self) -> None:
        self._actual_producer_consumer("resume-map", True)

    def test_rejected_original_wire_is_preserved(self) -> None:
        steps: tuple[Step, ...] = ("pause-map", "resume-map")
        for step in steps:
            with self.subTest(step=step):
                driver, endpoint = _driver()
                frame: dict[str, object] = {
                    "type": "command_result", "protocol_version": 1,
                    "request_id": "step-1-0123456789ab", "ok": False, "error": "original failure"}

                def answer(request: dict[str, object]) -> None:
                    endpoint.publish(frame)

                endpoint.send_hook = answer
                try:
                    with self.assertRaises(native._NativeCommandRejectedError) as caught:
                        driver._execute_primitive_step(step, internal_semantic_snapshot=True,
                                                       protocol_request_id="step-1-0123456789ab")
                    self.assertEqual(caught.exception.native_command_result_frame, frame)
                    self.assertNotIn("result", caught.exception.native_command_result_frame)
                    self.assertEqual(len(_commands(endpoint)), 1)
                finally:
                    driver.close()

    def test_actual_producer_rejects_bad_protocol_or_result_step_without_replay(self) -> None:
        changes: tuple[tuple[str, object], ...] = (
            ("protocol_version", True), ("protocol_version", 1.0),
            ("result", {"step": "resume-map", "accepted": True, "status": "submitted"}))
        for field, value in changes:
            with self.subTest(field=field, value=value):
                driver, endpoint = _driver()

                def answer(request: dict[str, object]) -> None:
                    frame = _frame("pause-map")
                    frame[field] = value
                    endpoint.publish(frame)

                endpoint.send_hook = answer
                try:
                    with self.assertRaises(native.BridgeUnavailableError):
                        driver._execute_primitive_step(
                            "pause-map", internal_semantic_snapshot=True,
                            protocol_request_id="step-1-0123456789ab")
                    self.assertEqual(len(_commands(endpoint)), 1)
                finally:
                    driver.close()

    def test_contract_rejects_malformed_frame(self) -> None:
        changes: tuple[tuple[str, object], ...] = (
            ("protocol_version", True), ("protocol_version", 1.0), ("protocol_version", 2),
            ("request_id", True), ("request_id", 1.0), ("request_id", 1),
            ("request_id", ""), ("request_id", "step-other"), ("request_id", None),
            ("type", "state_snapshot"), ("ok", 1), ("ok", False), ("result", None))
        for field, value in changes:
            with self.subTest(field=field, value=value):
                frame = _frame("pause-map")
                frame[field] = value
                with self.assertRaises(ValueError):
                    normalize_timeline_control_ack_v1(
                        frame, expected_step="pause-map", expected_request_id="step-1-0123456789ab")

    def test_contract_rejects_missing_field(self) -> None:
        for field in ("type", "protocol_version", "request_id", "ok", "result"):
            with self.subTest(field=field):
                frame = _frame("pause-map")
                del frame[field]
                with self.assertRaises(ValueError):
                    normalize_timeline_control_ack_v1(
                        frame, expected_step="pause-map", expected_request_id="step-1-0123456789ab")

    def test_contract_retains_only_canonical_id_without_reinterpreting_status(self) -> None:
        cases: tuple[tuple[Step, object], ...] = (
            ("pause-map", "submitted"), ("resume-map", "submitted"),
            ("pause-map", "already_paused"), ("resume-map", "already_running"),
            ("resume-map", "available"), ("resume-map", None))
        for step, status in cases:
            with self.subTest(step=step, status=status):
                frame = _frame(step)
                frame["result"] = {"step": step, "accepted": True, "status": status}
                before = copy.deepcopy(frame)
                binding = normalize_timeline_control_ack_v1(
                    frame, expected_step=step, expected_request_id="step-1-0123456789ab")
                self.assertEqual(json.loads(json.dumps(binding)), binding)
                self.assertEqual(frame, before)
                self.assertEqual(binding, {"native_request_id": "step-1-0123456789ab"})

    def test_contract_rejects_result_mismatch_and_identity_aliases(self) -> None:
        results: tuple[object, ...] = (
            {}, {"step": "resume-map", "accepted": True, "status": "submitted"},
            {"step": "pause-map", "accepted": True, "status": "submitted", "request_id": "alias"},
            {"step": "pause-map", "accepted": True, "status": "submitted", "native_request_id": "spoof"})
        for result in results:
            with self.subTest(result=result):
                frame = _frame("pause-map")
                frame["result"] = result
                with self.assertRaises(ValueError):
                    normalize_timeline_control_ack_v1(
                        frame, expected_step="pause-map", expected_request_id="step-1-0123456789ab")
