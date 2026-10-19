"""Software-only probe qualification; no Queue/SDK/Game or file writes.

Tests prove counter/clock/exception mechanics, not runtime phase coverage or a
performance gain. Source-only owner integration still needs one natural batch.
"""
import unittest
from unittest.mock import patch

from queue_control_timing_v1 import QueueControlTimingV1


class Clock:
    def __init__(self):
        self.value = self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.value


class QueueControlTimingTests(unittest.TestCase):
    @patch("builtins.open", side_effect=AssertionError("probe attempted file I/O"))
    def test_disabled_and_budget_exhaustion_never_read_clock(self, blocked_open):
        clock = Clock()
        off = QueueControlTimingV1(machine_id="fixture-machine", clock=clock)
        self.assertFalse(off.arm_batch(1))
        with off.span("not_even_validated_when_off"):
            pass
        off.boundary(1, "rpc_end", at_utc="fixture-UTC")
        off.record_artifact_scan(elapsed_ns=1, metadata_ns=0, roots=1,
                                 entries=0, is_file_calls=0, stat_calls=0)
        off.settled_cycle()
        self.assertEqual(clock.calls, 0)
        self.assertEqual(off.finish_batch(at_utc="fixture-UTC", reason="off")["phase_totals"], {})
        on = QueueControlTimingV1(machine_id="fixture-machine", enabled=True, clock=clock)
        self.assertTrue(on.arm_batch(12, cycle_budget=1))
        with on.span("loop_step"):
            before = clock.calls
            on.settled_cycle()
        self.assertEqual(clock.calls, before)
        with on.span("atomic_write"):
            pass
        on.boundary(3, "rpc_end", at_utc="fixture-UTC")
        on.record_artifact_scan(elapsed_ns=1, metadata_ns=0, roots=1,
                                entries=0, is_file_calls=0, stat_calls=0)
        self.assertEqual(clock.calls, before)
        result = on.finish_batch(at_utc="fixture-UTC", reason="budget")
        self.assertTrue(result["budget_reached"])
        self.assertEqual(result["dropped_open_spans"], 1)
        self.assertEqual(result["open_spans"], 0)
        self.assertEqual(result["file_IO_by_probe"], 0)
        with self.assertRaises(ValueError):
            on.arm_batch(13)
        with self.assertRaises(ValueError):
            QueueControlTimingV1(machine_id="fixture-machine", enabled=True).arm_batch(1, cycle_budget=31)
        blocked_open.assert_not_called()

    @patch("builtins.open", side_effect=AssertionError("probe attempted file I/O"))
    def test_nested_scan_partition_boundaries_and_original_exception(self, blocked_open):
        clock = Clock()
        trace = QueueControlTimingV1(machine_id="fixture-machine", enabled=True, clock=clock)
        trace.arm_batch(12, cycle_budget=30)
        original = RuntimeError("original guard failed")
        with self.assertRaises(RuntimeError) as caught:
            with trace.span("consume_guard"):
                clock.value = 20
                trace.record_artifact_scan(elapsed_ns=15, metadata_ns=5, roots=4,
                                           entries=3, is_file_calls=3, stat_calls=2)
                raise original
        self.assertIs(caught.exception, original)
        with trace.span("relay_total"):
            clock.value = 22
            with trace.span("relay_ack_wait"):
                clock.value = 27
            clock.value = 30
        calls = clock.calls
        trace.boundary(13, "rpc_end", at_utc="fixture-UTC", monotonic_ns=19)
        self.assertEqual(clock.calls, calls)
        with self.assertRaises(ValueError):
            trace.boundary(13, "rpc_end", at_utc="fixture-UTC", monotonic_ns=19)
        trace.settled_cycle()
        result = trace.finish_batch(at_utc="fixture-UTC", reason="closed")
        totals = result["phase_totals"]
        self.assertEqual(totals["consume_guard"]["inclusive_ns"], 20)
        self.assertEqual(totals["consume_guard"]["exclusive_ns"], 5)
        self.assertEqual(totals["consume_guard"]["error_count"], 1)
        self.assertEqual(totals["artifact_metadata"]["exclusive_ns"], 5)
        self.assertEqual(totals["artifact_enumeration_iteration_other"]["exclusive_ns"], 10)
        self.assertEqual(totals["relay_total"]["inclusive_ns"], 10)
        self.assertEqual(totals["relay_total"]["exclusive_ns"], 5)
        self.assertEqual(totals["relay_ack_wait"]["exclusive_ns"], 5)
        self.assertEqual(result["artifact_scan_counts"],
                         {"roots": 4, "entries": 3, "is_file_calls": 3, "stat_calls": 2})
        self.assertFalse(result["nested_inclusive_totals_additive"])
        self.assertEqual(result["business_or_RPC_calls"], 0)
        self.assertEqual(result["file_IO_by_probe"], 0)
        self.assertFalse(trace.active)
        blocked_open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
