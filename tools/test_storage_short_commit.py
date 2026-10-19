"""Real owned-lock regression; never opens the production task bus."""
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import storage_short_commit as storage
from audit_storage_lock_boundaries import audit_source
from codex_task_bus import BusBusy, bus_lock, lock_wait_seconds


def probe_owned_bus(bus, result):
    # This subprocess is only allowed below our explicitly owned fixture.
    root = Path(os.environ["XAR_STORAGE_LOCK_TEST_ROOT"]).resolve()
    bus, result = Path(bus).resolve(), Path(result).resolve()
    if not bus.is_relative_to(root) or not result.is_relative_to(root):
        raise ValueError("test bus escaped owned root")
    try:
        with lock_wait_seconds(.1):
            with bus_lock(bus, require_existing=True):
                pass
        outcome = "acquired"
    except BusBusy:
        outcome = "busy"
    result.write_text(outcome, encoding="utf-8")


class ShortStorageCommitTests(unittest.TestCase):
    def setUp(self):
        configured = os.environ.get("XAR_STORAGE_LOCK_TEST_ROOT")
        if configured:
            parent = Path(configured).resolve()
        else:
            base = Path(__file__).resolve().parents[1] / ".task-tmp"
            base.mkdir(exist_ok=True)
            owner = tempfile.TemporaryDirectory(dir=base, prefix="storage-lock-owned-")
            self.addCleanup(owner.cleanup)
            parent = Path(owner.name).resolve()
        self.fixture_parent = parent
        self.temporary = tempfile.TemporaryDirectory(dir=parent, prefix="case-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bus = self.root / "owned-bus"
        self.head = self.root / "head.json"
        with bus_lock(self.bus):
            pass

    def probe(self, suffix):
        result = self.root / (suffix + ".txt")
        subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                        "--probe-owned", str(self.bus), str(result)],
                       check=True, timeout=10, capture_output=True,
                       env={**os.environ, "XAR_STORAGE_LOCK_TEST_ROOT": str(self.fixture_parent)})
        return result.read_text(encoding="utf-8")

    def test_slow_preparation_leaves_actual_bus_available(self):
        entered, release = threading.Event(), threading.Event()
        outcomes = []

        def caller():
            try:
                # Stand-in for slow process/system/body inspection, before CAS.
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("test preparation was not released")
                old = storage.snapshot_json(self.head)
                ready = storage.prepare(old, {"machine_id": "owned-fixture"})
                outcomes.append(storage.publish(ready, bus=self.bus))
            except BaseException as error:
                outcomes.append(error)

        worker = threading.Thread(target=caller)
        worker.start()
        try:
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.probe("while-preparing"), "acquired")
        finally:
            release.set()
            worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(outcomes), 1)
        self.assertIsInstance(outcomes[0], dict)
        self.assertTrue(outcomes[0]["adopted"])

    def test_owned_contention_is_busy_then_retryable(self):
        with bus_lock(self.bus, require_existing=True):
            self.assertEqual(self.probe("while-locked"), "busy")
        self.assertEqual(self.probe("after-release"), "acquired")

    def test_stale_preparation_cannot_overwrite_new_generation(self):
        old = storage.snapshot_json(self.head)
        first = storage.prepare(old, {"winner": "first"},
                                report=self.root / "first.json", report_bytes=b"{}\n")
        stale = storage.prepare(old, {"winner": "stale"},
                                report=self.root / "stale.json", report_bytes=b"{}\n")
        storage.publish(first, bus=self.bus)
        with self.assertRaises(storage.StorageConflict):
            storage.publish(stale, bus=self.bus)
        self.assertFalse((self.root / "stale.json").exists())
        self.assertEqual(storage.snapshot_json(self.head).value["winner"], "first")
        # A real conflict is re-prepared outside the lock, not replayed blindly.
        current = storage.snapshot_json(self.head)
        retry = storage.prepare(current, {"winner": "retry"})
        result = storage.publish(retry, bus=self.bus)
        self.assertEqual(result["storage_revision"], 2)

    def test_exact_guard_change_refuses_without_adopting(self):
        guard = self.root / "admission.json"
        guard.write_bytes(b"old")
        ready = storage.prepare(storage.snapshot_json(self.head), {"ok": True},
                                guards=[(guard, storage.exact_identity(guard))])
        guard.write_bytes(b"changed")
        with self.assertRaises(storage.StorageConflict):
            storage.publish(ready, bus=self.bus)
        self.assertFalse(self.head.exists())

    def test_no_body_reads_fsync_or_callbacks_under_commit_lock(self):
        ready = storage.prepare(storage.snapshot_json(self.head), {"ok": True},
                                report=self.root / "report.json", report_bytes=b"{}\n")
        original_lock = storage.bus_lock
        inside = [False]

        @contextmanager
        def tracked_lock(*args, **kwargs):
            with original_lock(*args, **kwargs):
                inside[0] = True
                try:
                    yield
                finally:
                    inside[0] = False

        original_read, original_fsync = Path.read_bytes, os.fsync

        def read(path):
            self.assertFalse(inside[0], "body read under bus lock")
            return original_read(path)

        def fsync(handle):
            self.assertFalse(inside[0], "fsync under bus lock")
            return original_fsync(handle)

        with patch.object(storage, "bus_lock", tracked_lock), \
                patch.object(Path, "read_bytes", read), patch.object(os, "fsync", fsync):
            storage.publish(ready, bus=self.bus)
        self.assertEqual(storage.snapshot_json(self.head).value["storage_revision"], 1)
        self.assertFalse(list(self.root.glob("*.prepared")))

    def test_existing_report_and_unbounded_guards_are_rejected(self):
        report = self.root / "immutable.json"
        report.write_bytes(b"original")
        with self.assertRaises(storage.StorageConflict):
            storage.prepare(storage.snapshot_json(self.head), {},
                            report=report, report_bytes=b"replacement")
        self.assertEqual(report.read_bytes(), b"original")
        with self.assertRaises(ValueError):
            storage.prepare(storage.snapshot_json(self.head), {},
                            guards=[(report, None)] * 9)

    def test_legacy_alias_and_hidden_callback_lock_patterns_are_retired(self):
        self.assertEqual(audit_source(b"from codex_task_bus import bus_lock as hold\nwith hold(p):\n    slow()\n"), [2])
        self.assertEqual(audit_source(b"import codex_task_bus as b\ndef hidden():\n    with b.bus_lock(p):\n        callback()\n"), [3])
        self.assertEqual(audit_source(b"from storage_short_commit import publish\npublish(ready,bus=p)\n"), [])

    def test_default_fixture_is_owned_and_probe_is_portable(self):
        with patch.dict(os.environ):
            os.environ.pop("XAR_STORAGE_LOCK_TEST_ROOT", None)
            other = ShortStorageCommitTests("test_owned_contention_is_busy_then_retryable")
            try:
                other.setUp()
                self.assertTrue(other.root.is_relative_to(other.fixture_parent))
                self.assertEqual(other.probe("portable-default"), "acquired")
            finally:
                other.doCleanups()


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--probe-owned":
        probe_owned_bus(sys.argv[2], sys.argv[3])
    else:
        unittest.main()
