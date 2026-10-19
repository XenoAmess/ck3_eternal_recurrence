"""Portable qualification: timing cannot become a business dependency."""
import unittest

from full_lifecycle_timing_v1 import FullLifecycleTimingV1


class Clock:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        value = next(self.values)
        if isinstance(value, Exception):
            raise value
        return value


class FullLifecycleTimingTests(unittest.TestCase):
    def test_default_off_has_no_clock_or_receipt_fields(self):
        clock = Clock([])
        timing = FullLifecycleTimingV1(clock=clock)
        timing.before_publish(3)
        self.assertEqual(timing.after_receipt(3), {})
        timing.discard()
        self.assertEqual(clock.calls, 0)

    def test_new_submission_two_endpoints_including_zero_day(self):
        clock = Clock([100, 9100])
        timing = FullLifecycleTimingV1(enabled=True, clock=clock)
        timing.before_publish(3)
        receipt = {"actual_days": 0, **timing.after_receipt(3)}
        self.assertEqual(receipt["full_wall_ns"], 9000)
        self.assertEqual(receipt["actual_days"], 0)
        self.assertEqual(clock.calls, 2)
        self.assertIsNone(timing.after_receipt(3)["full_wall_ns"])
        self.assertEqual(clock.calls, 2)

    def test_following_restart_and_wrong_sequence_do_not_invent_start(self):
        clock = Clock([100])
        following = FullLifecycleTimingV1(enabled=True, clock=clock)
        self.assertIsNone(following.after_receipt(3)["full_submit_monotonic_ns"])
        following.before_publish(4)
        self.assertIsNone(following.after_receipt(5)["full_wall_ns"])
        restarted = FullLifecycleTimingV1(enabled=True, clock=clock)
        self.assertIsNone(restarted.after_receipt(4)["full_wall_ns"])
        self.assertEqual(clock.calls, 1)

    def test_clock_failures_and_invalid_intervals_drop_only_metrics(self):
        for values in ([RuntimeError("start")], [100, RuntimeError("end")],
                       [100, 99], [True], [100, False]):
            with self.subTest(values=values):
                timing = FullLifecycleTimingV1(enabled=True, clock=Clock(values))
                timing.before_publish(3)
                self.assertEqual(timing.after_receipt(3), {})

    def test_publish_or_receipt_failure_keeps_original_exception(self):
        for stage in ("publish", "receipt"):
            with self.subTest(stage=stage):
                clock = Clock([100])
                timing = FullLifecycleTimingV1(enabled=True, clock=clock)
                original = OSError(stage)
                try:
                    timing.before_publish(3)
                    raise original
                except OSError as actual:
                    timing.discard()
                    self.assertIs(actual, original)
                self.assertEqual(timing.after_receipt(3), {})
                self.assertEqual(clock.calls, 1)


if __name__ == "__main__":
    unittest.main()
