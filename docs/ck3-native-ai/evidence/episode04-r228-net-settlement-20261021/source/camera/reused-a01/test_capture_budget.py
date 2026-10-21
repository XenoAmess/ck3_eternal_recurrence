"""Focused fake-Job tests; no desktop, game, SDK or media executable."""
from __future__ import annotations

from pathlib import Path
import tempfile
import threading
import unittest

from capture_budget_monitor import CaptureByteBudget, CaptureBudgetFailure, from_capacity
from capture_recorder import OwnedRecorder

HERE = Path(__file__).resolve().parent


class FakeKeeper:
    def require_live(self) -> None:
        pass


class FakeJob:
    def __init__(self) -> None:
        self.finishes = 0
        self.aborts = 0
        self.closed = False
        self.entered = threading.Event()
        self.release = threading.Event()
        self.release.set()

    def poll(self) -> int | None:
        return 0 if self.closed else None

    def finish(self, *, receipt: Path, unsafe_marker: Path, timeout: int) -> dict[str, object]:
        self.finishes += 1
        self.entered.set()
        if not self.release.wait(2):
            raise TimeoutError("Fake Job release did not arrive")
        self.closed = True
        return {"state": "NORMAL_TREE_EMPTY", "job_active_processes": 0, "original_wait": 0}

    def abort(self, *, receipt: Path, unsafe_marker: Path) -> dict[str, object]:
        self.aborts += 1
        self.closed = True
        return {"state": "ABORTED_TREE_EMPTY", "job_active_processes": 0, "original_wait": 0}


class NoDesktopRecorder(OwnedRecorder):
    def _check_capture_source(self) -> dict[str, object]:
        return {"fake_geometry_unchanged": True}


def configured(root: Path, *, raw_limit: int = 128) -> tuple[NoDesktopRecorder, FakeJob]:
    budget = CaptureByteBudget(root, root / "raw.mkv", raw_limit, 4096, raw_limit + 64, 8192)
    recorder = NoDesktopRecorder(root, FakeKeeper(), root / "unused-offline.json",
        {"assets_root": str(root), "machine_id": "synthetic-no-game"}, budget_monitor=budget)
    job = FakeJob()
    recorder.directory = root
    recorder.job = job
    recorder.start_ns = 0
    recorder.start_at = "synthetic"
    return recorder, job


def start_watch(recorder: NoDesktopRecorder) -> threading.Thread:
    thread = threading.Thread(target=recorder._watch_capture_source, daemon=True)
    recorder.capture_guard_thread = thread
    thread.start()
    return thread


class BudgetTests(unittest.TestCase):
    def test_ordinary_finish_once(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            (root / "raw.mkv").write_bytes(b"new fake raw")
            recorder, job = configured(root)
            watch = start_watch(recorder)
            result = recorder.finish()
            recorder.finish()
            recorder.close()
            self.assertFalse(watch.is_alive())
            self.assertEqual(job.finishes, 1)
            self.assertEqual(job.aborts, 0)
            self.assertEqual(result["state"], "NORMAL_TREE_EMPTY")
            self.assertIs(result["budget_qualified"], True)
            self.assertEqual(result["job"]["original_wait"], 0)

    def test_budget_watcher_and_concurrent_finish_no_deadlock(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            (root / "raw.mkv").write_bytes(b"x" * 32)
            recorder, job = configured(root, raw_limit=16)
            job.release.clear()
            watch = start_watch(recorder)
            self.assertTrue(job.entered.wait(2))
            closer = threading.Thread(target=recorder.finish, daemon=True)
            closer.start()
            job.release.set()
            watch.join(2)
            closer.join(2)
            recorder.close()
            self.assertFalse(watch.is_alive())
            self.assertFalse(closer.is_alive())
            self.assertEqual(job.finishes, 1)
            self.assertEqual(job.aborts, 0)
            result = recorder.result
            assert result is not None
            self.assertEqual(result["state"], "RED_CAPTURE_BUDGET")
            self.assertIs(result["budget_qualified"], False)
            self.assertIs(result["partial_assets_retained"], True)
            self.assertEqual((root / "raw.mkv").stat().st_size, 32)
            self.assertEqual(result["job"], {"state": "NORMAL_TREE_EMPTY", "job_active_processes": 0, "original_wait": 0})

    def test_aggregate_limit_and_final_flush_recheck(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            (root / "raw.mkv").write_bytes(b"x")
            (root / "metadata.bin").write_bytes(b"x" * 64)
            budget = CaptureByteBudget(root, root / "raw.mkv", 128, 32, 256, 512)
            with self.assertRaises(CaptureBudgetFailure) as caught:
                budget()
            self.assertEqual(caught.exception.facts["reason"], "aggregate_soft_stop")
            recorder, job = configured(root, raw_limit=16)
            (root / "raw.mkv").write_bytes(b"x" * 128)
            result = recorder.finish()
            self.assertEqual(job.finishes, 1)
            self.assertEqual(result["state"], "RED_CAPTURE_BUDGET")
            self.assertIs(result["capture_budget_failure"]["raw_hard_ceiling_exceeded"], True)

    def test_scope_and_numeric_alias_rejection(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                CaptureByteBudget(root, root.parent / "not-camera.mkv", 8, 16, 12, 32)
            with self.assertRaises(ValueError):
                CaptureByteBudget(root, root / "raw.mkv", True, 16, 12, 32)
            fields: dict[str, object] = {"camera_root": str(root), "raw_path": str(root / "raw.mkv"),
                "raw_soft_stop_bytes": 8, "aggregate_soft_stop_bytes": 16,
                "raw_ceiling_bytes": 12, "aggregate_ceiling_bytes": 32}
            self.assertEqual(from_capacity(root, root / "raw.mkv", 12,
                {"capture_budget_monitor": fields}).raw_ceiling_bytes, 12)
            with self.assertRaises(ValueError):
                from_capacity(root, root / "raw.mkv", 13, {"capture_budget_monitor": fields})
            with self.assertRaises(ValueError):
                from_capacity(root, root / "raw.mkv", 12, {})

    def test_existing_geometry_failure_keeps_primary_reason(self) -> None:
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            (root / "raw.mkv").write_bytes(b"x" * 128)
            recorder, job = configured(root, raw_limit=16)
            recorder.capture_guard_error = "synthetic geometry changed"
            result = recorder.finish()
            self.assertEqual(job.finishes, 1)
            self.assertEqual(result["state"], "RED_CAPTURE_SOURCE_CHANGED")
            self.assertEqual(result["capture_guard_error"], "synthetic geometry changed")
            self.assertIs(result["budget_qualified"], False)


if __name__ == "__main__":
    unittest.main()
