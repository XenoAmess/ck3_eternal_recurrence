"""Tiny real Driver encode/record paths, in-memory write and trace sinks only."""
import json
import itertools
from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer.bridge import native_driver as native
from test_driver_state_write_timing_phases import driver_at


class PersistenceGrowthTimingTest(unittest.TestCase):
    def test_full_candidate_run_churn_and_exact_history_lengths(self):
        driver = driver_at(Path("unused-diagnostic-fixture"))
        traces, writes = [], []
        sink = mock.MagicMock()
        sink.__enter__.return_value.write.side_effect = traces.append
        started = itertools.count(1)
        def start(stage, **kwargs):
            return ("unused-trace", stage, next(started), None)
        with mock.patch.object(native, "start_army_timing", side_effect=start), \
                mock.patch.object(Path, "open", return_value=sink), \
                mock.patch.object(native, "write_bytes_atomic", side_effect=lambda path, payload, **kw: writes.append(payload)), \
                mock.patch.object(native, "driver_state_json_parts", wraps=native.driver_state_json_parts) as parts:
            driver._record_command("pause-map", ok=True, result={"status": "submitted"})
            driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
            driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
            driver._persist_driver_state(persistence_reason="succession_expectation")
            driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
        rows = [json.loads(line) for line in traces]
        encoded = [row for row in rows if row["stage"] == "driver.full_state_utf8_encoding"]
        full = [row for row in rows if row["stage"] == "driver.full_state_persistence"]
        self.assertEqual(parts.call_count, 5)
        self.assertEqual(len(writes), 5)
        self.assertEqual([row["candidate_append_run_length"] for row in full], [0, 1, 2, 0, 1])
        self.assertEqual([row["closed_candidate_run_length"] for row in full], [0, 0, 0, 2, 0])
        self.assertEqual([row["candidate_activation_churn_count"] for row in full], [0, 1, 1, 1, 2])
        self.assertEqual(full[3]["full_barrier_reason"], "succession_expectation")
        for parent, child in zip(full, encoded, strict=True):
            self.assertEqual(parent["persistence_attempt_id"], child["step"])
            self.assertEqual(parent["persistence_attempt_id"], child["persistence_attempt_id"])
        for row, payload in zip(encoded, writes, strict=True):
            history = json.loads(payload)["command_history"]
            self.assertEqual(row["history_rows"], len(history))
            self.assertEqual(row["history_json_bytes"], len(json.dumps(history, ensure_ascii=False, separators=(",", ":")).encode()))
        self.assertEqual(full[-1]["full_write_success_count"], 5)
        self.assertEqual(full[-1]["actual_wal_append_count"], 0)

    def test_failed_write_interrupts_run_and_disabled_timing_keeps_bytes(self):
        driver = driver_at(Path("unused-diagnostic-fixture"))
        traces, writes = [], []
        sink = mock.MagicMock()
        sink.__enter__.return_value.write.side_effect = traces.append
        def start(stage, **kwargs):
            return ("unused-trace", stage, 1, None)
        with mock.patch.object(native, "start_army_timing", side_effect=start), \
                mock.patch.object(Path, "open", return_value=sink), \
                mock.patch.object(native, "write_bytes_atomic", side_effect=lambda path, payload, **kw: writes.append(payload)):
            driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
            with mock.patch.object(native, "write_bytes_atomic", side_effect=OSError("fixture-write-failed")):
                driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
            self.assertTrue(driver._driver_state_dirty)
            self.assertIn("fixture-write-failed", driver._driver_state_error)
            driver._record_command("life-advance", ok=True, result={"elapsed_days": 8})
        full = [row for row in map(json.loads, traces) if row["stage"] == "driver.full_state_persistence"]
        self.assertEqual([row["full_write_success_count"] for row in full], [1, 1, 2])
        self.assertEqual([row["full_write_failure_count"] for row in full], [0, 1, 1])
        self.assertEqual([row["candidate_append_run_length"] for row in full], [1, 0, 1])
        self.assertEqual(full[1]["persistence_error_type"], "OSError")
        self.assertEqual(full[1]["closed_candidate_run_length"], 1)
        self.assertEqual(full[-1]["candidate_activation_churn_count"], 2)
        before = driver._encode_driver_state_locked()
        with mock.patch.object(native, "start_army_timing", return_value=None), \
                mock.patch.object(native, "write_bytes_atomic", side_effect=lambda path, payload, **kw: writes.append(payload)):
            driver._persist_driver_state(persistence_reason="close")
        self.assertEqual(writes[-1], before)
        self.assertEqual(driver._persistence_growth_timing_v1.successes, 2)


if __name__ == "__main__":
    unittest.main()
