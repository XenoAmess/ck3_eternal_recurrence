"""Only the two newly requested error-dispatch regressions; no old matrix."""
import types
import unittest

import test_candidate as original_tests

H = original_tests.helper


def payload():
    return H.build_exact_clock_failure_v1(
        original_error=original_tests.BridgeUnavailableError(H.MESSAGE),
        starting_date_raw=100, target_date_raw=124, speed=3, arm_status={"generation": 147},
        starting=original_tests.frame(), last_frame=original_tests.frame(paused=False),
        cleanup_before_frame=None, actions=[], action_start=0, cleanup_start=0)


class DispatchTests(unittest.TestCase):
    def test_foreign_error_is_not_selected_or_mutated(self):
        foreign = original_tests.BridgeUnavailableError(H.MESSAGE)
        foreign.step_result = payload()
        foreign.selected_step = "life-advance-one-day"
        before = dict(foreign.__dict__)
        self.assertIsNone(H.exact_clock_failure_diagnostic_v1(foreign))
        self.assertEqual(foreign.__dict__, before)
        self.assertEqual(str(foreign), H.MESSAGE)

    def test_wrong_step_rejected_expected_typed_error_still_selected(self):
        error = original_tests.StepPostconditionError(
            H.MESSAGE, selected_step="other-step", step_result=payload())
        self.assertIsNone(H.exact_clock_failure_diagnostic_v1(error))
        self.assertEqual(error.selected_step, "other-step")
        error.selected_step = "life-advance-one-day"
        projected = H.exact_clock_failure_diagnostic_v1(error)
        self.assertEqual(set(projected), set(H._DIAGNOSTIC))
        self.assertEqual(projected["schema"], H.SCHEMA)
        projected["armed_reply"]["generation"] = 1
        self.assertEqual(error.step_result["armed_reply"]["generation"], 147)
        error.step_result["unexpected_body"] = {"full_actions": []}
        self.assertIsNone(H.exact_clock_failure_diagnostic_v1(error))


if __name__ == "__main__":
    unittest.main(verbosity=2)
