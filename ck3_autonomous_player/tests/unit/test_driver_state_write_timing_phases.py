"""Frozen production persistence, fake history only; no endpoint or live reads."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock

import xar_autoplayer.environment as environment
import xar_autoplayer.bridge.native_driver as native
from xar_autoplayer.bridge import army_query_timing as timing

timing_name = timing.__name__
candidate_write = environment.write_bytes_atomic


def _reference_atomic_write(path, payload, **_):
    """Previous pathlib write/close/replace contract, without diagnostics."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def driver_at(folder):
    driver = object.__new__(native.NativeHeadlessGameplayDriver)
    driver.pipe_name = "fixture-pipe"
    driver.state_dir = folder
    driver._session_bridge_pid = 23
    driver._episode_character_id = 7
    driver._episode_run_id = "fixture-run"
    driver._last_checkpoint = None
    driver._command_history = []
    driver._driver_state_history_json = native.DriverStateHistoryJsonCache()
    driver._rollback_war_failures = []
    driver._rollback_war_failures_migration_required = False
    driver._managed_restore_transaction = None
    driver._succession_expectation = None
    driver._succession_lifecycle = None
    driver._campaign_goal = None
    driver._driver_state_lock = threading.RLock()
    driver._history_lock = driver._driver_state_lock
    driver._driver_state_write_lock = threading.Lock()
    driver._driver_state_dirty = False
    driver._driver_state_error = None
    return driver


class TempWritePhasesTests(unittest.TestCase):
    def test_production_history_defer_mutation_and_save_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            log = folder / "stages.jsonl"
            driver = driver_at(folder)
            writes = []
            def recorded(path, payload, **kwargs):
                writes.append(len(payload))
                return candidate_write(path, payload, **kwargs)
            with mock.patch.dict(sys.modules, {timing_name: timing}), \
                    mock.patch.dict(os.environ, {"XAR_CK3_ARMY_TIMING_JSONL": str(log)}), \
                    mock.patch.object(native, "write_bytes_atomic", recorded), \
                    mock.patch.object(os, "fsync", side_effect=RuntimeError("unexpected fsync")):
                driver._record_command("query-council", ok=True,
                    result={"query_sequence": 9, "payload": "\u8bb0\u5f55" * 128})
                self.assertEqual(writes, [])
                self.assertTrue(driver._driver_state_dirty)
                driver._record_command("move-army-501-to-11", ok=True,
                    result={"request_id": "fixture-idempotency", "status": "submitted_pending"})
                self.assertEqual(len(writes), 1)
                checkpoint = {"history_index": 3, "episode_character_id": 7,
                    "episode_run_id": "fixture-run", "size": 4, "sha256": "a" * 64, "date_raw": 53300000}
                driver._last_checkpoint = checkpoint
                receipt = driver._record_command("save-checkpoint", ok=True,
                    result={"checkpoint": checkpoint})
                self.assertEqual(len(writes), 2)
                self.assertEqual(receipt["scope"], "WRITE_REPLACE_RETURNED_NOT_FSYNC")
                self.assertEqual(receipt["status"], "replaced")
                self.assertTrue(receipt["save_binding_verified"])
                expected = (json.dumps(driver._driver_state_payload_locked(),
                    ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
                self.assertEqual(driver._native_driver_state_path().read_bytes(), expected)
                self.assertFalse(driver._driver_state_dirty)
                rows = [json.loads(line) for line in log.read_text("utf-8").splitlines()]
                phases = {name: [row for row in rows if row["stage"] == name] for name in
                    ("driver.full_state_temp_open", "driver.full_state_temp_stream_write", "driver.full_state_temp_close")}
                for samples in phases.values():
                    self.assertEqual([row["payload_bytes"] for row in samples], writes)
                self.assertEqual([row["command"] for row in json.loads(expected)["command_history"]],
                    ["query-council", "move-army-501-to-11", "save-checkpoint"])

    def test_atomic_open_write_close_replace_failure_equivalence(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ):
            os.environ.pop("XAR_CK3_ARMY_TIMING_JSONL", None)
            for fault in ("open", "write", "close", "replace"):
                observations = []
                for writer in (_reference_atomic_write, candidate_write):
                    trace = []
                    class Stream:
                        def __enter__(self):
                            return self
                        def __exit__(self, *args):
                            self.close()
                        def write(self, data):
                            trace.append("write")
                            if fault == "write":
                                raise OSError("fixture-write")
                            return len(data)
                        def close(self):
                            trace.append("close")
                            if fault == "close":
                                raise OSError("fixture-close")
                    def open_file(*args, **kwargs):
                        trace.append("open")
                        if fault == "open":
                            raise OSError("fixture-open")
                        return Stream()
                    def replace(*args):
                        trace.append("replace")
                        raise OSError("fixture-replace")
                    with mock.patch.dict(sys.modules, {timing_name: timing}), \
                            mock.patch.object(Path, "open", side_effect=open_file), \
                            mock.patch.object(os, "replace", side_effect=replace):
                        with self.assertRaises(OSError) as error:
                            writer(Path(tmp) / "state.json", b"history", timing_step="fixture")
                    observations.append((trace, str(error.exception)))
                self.assertEqual(observations[0], observations[1], fault)

    def test_production_failed_write_retains_dirty_history_and_prior_state(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ):
            os.environ.pop("XAR_CK3_ARMY_TIMING_JSONL", None)
            driver = driver_at(Path(tmp))
            driver._record_command("pause-map", ok=True, result={"status": "submitted"})
            old = driver._native_driver_state_path().read_bytes()
            with mock.patch.object(native, "write_bytes_atomic", side_effect=OSError("fixture-io")):
                driver._record_command("move-army-501-to-11", ok=True, result={"status": "submitted_pending"})
            self.assertTrue(driver._driver_state_dirty)
            self.assertIn("fixture-io", driver._driver_state_error)
            self.assertEqual(driver._native_driver_state_path().read_bytes(), old)
            with mock.patch.object(native, "write_bytes_atomic", candidate_write):
                driver._persist_driver_state()
            self.assertFalse(driver._driver_state_dirty)
            self.assertEqual(len(json.loads(driver._native_driver_state_path().read_bytes())["command_history"]), 2)

    def test_default_atomic_write_never_starts_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(timing, "start_army_timing", side_effect=AssertionError("unexpected diagnostics")), \
                mock.patch.object(os, "fsync", side_effect=AssertionError("unexpected fsync")):
            target = Path(tmp) / "state.json"
            payload = b"exact atomic bytes\n"
            candidate_write(target, payload)
            self.assertEqual(target.read_bytes(), payload)
            self.assertFalse(target.with_name(target.name + ".tmp").exists())

    def test_diagnostic_destination_failure_does_not_change_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked_parent = root / "not-a-directory"
            blocked_parent.write_bytes(b"marker")
            with mock.patch.dict(os.environ, {"XAR_CK3_ARMY_TIMING_JSONL": str(blocked_parent / "timing.jsonl")}):
                target = root / "state.json"
                candidate_write(target, b"committed", timing_step="fixture")
            self.assertEqual(target.read_bytes(), b"committed")


if __name__ == "__main__":
    unittest.main()
