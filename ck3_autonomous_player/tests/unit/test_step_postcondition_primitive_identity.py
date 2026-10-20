"""Primitive failure identity survives a planner's outer step annotation."""
from __future__ import annotations

import json
import unittest
from typing import get_type_hints

from xar_autoplayer.bridge.driver import CallbackGameplayDriver, StepPostconditionError
from xar_autoplayer.bridge.exact_clock_failure_diagnostic_v1 import (
    MESSAGE, build_exact_clock_failure_v1, exact_clock_failure_diagnostic_v1,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.exact_clock_wait_progress_v1 import WaitProgressV1


def failure(step: str = "life-advance-one-day", message: str = MESSAGE) -> StepPostconditionError:
    payload = build_exact_clock_failure_v1(
        original_error=RuntimeError(MESSAGE), starting_date_raw=100,
        target_date_raw=124, speed=1, arm_status=None, starting=None,
        last_frame=None, cleanup_before_frame=None, actions=[],
        action_start=0, cleanup_start=0,
    )
    return StepPostconditionError(message, selected_step=step, step_result=dict(payload))


class StepPostconditionPrimitiveIdentityTests(unittest.TestCase):
    def test_valid_inner_failure_retains_typed_primitive(self) -> None:
        error = failure()
        progress = WaitProgressV1({}, 1, clock=lambda: 0).freeze(None)
        error.step_result["wait_progress"] = progress
        before = json.dumps(error.step_result, sort_keys=True)
        projected = exact_clock_failure_diagnostic_v1(error)
        self.assertIsNotNone(projected)
        assert projected is not None
        self.assertEqual(projected["wait_progress"], progress)
        self.assertIs(get_type_hints(exact_clock_failure_diagnostic_v1)["error"], object)
        self.assertEqual(get_type_hints(exact_clock_failure_diagnostic_v1)["return"], dict[str, object] | None)
        self.assertEqual(error.primitive_step, "life-advance-one-day")
        self.assertEqual(error.selected_step, "life-advance-one-day")
        self.assertEqual(get_type_hints(type(error).primitive_step.fget)["return"], str)
        self.assertEqual(json.dumps(error.step_result, sort_keys=True), before)

    def test_real_service_outer_wrap_preserves_original_identity_and_message(self) -> None:
        error = failure()
        before = json.dumps(error.step_result, sort_keys=True)
        prior_projection = exact_clock_failure_diagnostic_v1(error)
        calls: list[tuple[str, int | None]] = []

        def execute(step: str, revision: int | None) -> dict[str, object]:
            calls.append((step, revision))
            raise error

        service = object.__new__(GameplayBridgeService)
        service.driver = CallbackGameplayDriver(
            backend_id="pure-ram", snapshot=lambda: {}, execute=execute,
            action_steps=("life-advance",),
        )
        planned = {"plan": {"selected_step": "life-advance", "policy": "synthetic-siege"},
                   "revision": 1, "snapshot_id": "synthetic:1"}
        with self.assertRaises(StepPostconditionError) as caught:
            service._execute_planned_turn_without_unhandled_capture(planned)
        self.assertIs(caught.exception, error)
        self.assertEqual(error.selected_step, "life-advance")
        self.assertEqual(error.primitive_step, "life-advance-one-day")
        self.assertEqual(error.plan, planned["plan"])
        self.assertEqual(calls, [("life-advance", 1)])
        self.assertEqual(str(error), MESSAGE)
        self.assertEqual(json.dumps(error.step_result, sort_keys=True), before)
        self.assertEqual(exact_clock_failure_diagnostic_v1(error), prior_projection)
        with self.assertRaises(AttributeError):
            setattr(error, "primitive_step", "foreign-step")

    def test_unknown_exception_has_no_typed_failure_projection(self) -> None:
        self.assertIsNone(exact_clock_failure_diagnostic_v1(RuntimeError(MESSAGE)))

    def test_foreign_primitive_or_schema_cannot_be_promoted(self) -> None:
        foreign = failure("query-army-strengths")
        foreign.selected_step = "life-advance-one-day"
        self.assertIsNone(exact_clock_failure_diagnostic_v1(foreign))
        malformed = failure()
        malformed.step_result["schema"] = "synthetic.foreign.v1"
        self.assertIsNone(exact_clock_failure_diagnostic_v1(malformed))

    def test_original_error_text_and_zero_credit_validation_remain(self) -> None:
        error = failure()
        self.assertEqual(str(error), MESSAGE)
        self.assertIsNotNone(exact_clock_failure_diagnostic_v1(error))
        self.assertIsNone(exact_clock_failure_diagnostic_v1(failure(message="changed message")))
        for credit in (True, 0.0, 1):
            with self.subTest(credit=credit):
                changed = failure()
                changed.step_result["credit"] = credit
                self.assertIsNone(exact_clock_failure_diagnostic_v1(changed))


if __name__ == "__main__":
    unittest.main()
