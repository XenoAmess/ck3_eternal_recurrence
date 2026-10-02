"""Harmless Windows process fixtures for optional recorder Job containment."""
from __future__ import annotations

import json
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from contextlib import contextmanager

import recorder_job

BASE_PYTHON = getattr(sys, "_base_executable", sys.executable)


@unittest.skipUnless(sys.platform == "win32", "Windows Job API required")
class RecorderJobTests(unittest.TestCase):
    def wait_at_least(self, job: recorder_job.RecorderJob, minimum: int,
                    timeout: float = 5) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            active = recorder_job._active(job.job)
            if active >= minimum:
                return
            time.sleep(0.02)
        self.assertGreaterEqual(recorder_job._active(job.job), minimum)

    @contextmanager
    def fixture_root(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            try:
                yield root
            finally:
                stderr = root / "stderr.bin"
                if stderr.is_file():
                    # Job accounting can reach zero just before Windows drops
                    # the last inherited file handle. Do not race temp cleanup.
                    create_file = recorder_job._api(
                        "CreateFileW", wintypes.HANDLE, wintypes.LPCWSTR,
                        wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
                    deadline = time.monotonic() + 15
                    while True:
                        handle = create_file(str(stderr), 0x80000000, 0, None, 3, 0, None)
                        if handle != recorder_job.INVALID_HANDLE_VALUE:
                            recorder_job._close(handle)
                            break
                        if time.monotonic() >= deadline:
                            self.fail(f"fixture stderr handle remains open: WinError {ctypes.get_last_error()}")
                        time.sleep(0.05)

    @contextmanager
    def contained(self, job: recorder_job.RecorderJob, root: Path):
        try:
            yield job
        finally:
            if job.job is not None:
                try:
                    job.abort(receipt=root / "fixture-finally-abort.json",
                              unsafe_marker=root / "unsafe.json")
                finally:
                    if job.job is not None:
                        # Last-resort test cleanup; the test still fails if
                        # the Job abort itself could not prove an empty tree.
                        recorder_job._close(job.job)
                        job.job = None
                        job.process.wait(timeout=10)

    def test_normal_pipe_exit_proves_empty_tree(self) -> None:
        with self.fixture_root() as root:
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn(
                    [BASE_PYTHON, "-c", "import sys; sys.stdin.readline()"],
                    stderr=err, unsafe_marker=root / "unsafe.json",
                    start_receipt=root / "spawn.json",
                    failure_receipt=root / "spawn-red.json")
                with self.contained(job, root):
                    row = job.finish(receipt=root / "finish.json",
                                     unsafe_marker=root / "unsafe.json", timeout=5)
            self.assertEqual(row["state"], "NORMAL_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertEqual(row["returncode"], 0)
            self.assertFalse((root / "unsafe.json").exists())
            self.assertEqual(json.loads((root / "finish.json").read_text()), row)
            spawn = json.loads((root / "spawn.json").read_text())
            self.assertEqual(spawn["pid"], job.pid)
            flags = spawn["job_limit_flags_readback"]
            self.assertTrue(flags & recorder_job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
            self.assertFalse(flags & (recorder_job.JOB_OBJECT_LIMIT_BREAKAWAY_OK |
                                      recorder_job.JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK))
            self.assertEqual(job.abort(receipt=root / "late-abort.json",
                                       unsafe_marker=root / "unsafe.json")["state"],
                             "ALREADY_TREE_EMPTY")
            self.assertFalse((root / "late-abort.json").exists())

    def test_abort_kills_descendant_after_root_exits(self) -> None:
        with self.fixture_root() as root:
            parent = ("import subprocess,sys; "
                      "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                      "sys.stdin.readline()")
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn([BASE_PYTHON, "-c", parent],
                                         stderr=err, unsafe_marker=root / "unsafe.json",
                                         start_receipt=root / "spawn.json",
                                         failure_receipt=root / "spawn-red.json")
                with self.contained(job, root):
                    self.wait_at_least(job, 2)
                    job.process.communicate(b"q\n", timeout=5)
                    self.assertEqual(job.returncode, 0)
                    # The terminated root and live descendant may both remain
                    # in Job accounting until their process references clear.
                    self.assertGreaterEqual(recorder_job._active(job.job), 1)
                    row = job.abort(receipt=root / "abort.json",
                                    unsafe_marker=root / "unsafe.json")
            self.assertEqual(row["state"], "ABORT_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertTrue((root / "unsafe.json").exists())
            self.assertEqual(json.loads((root / "abort.json").read_text()), row)

    def test_normal_finish_with_descendant_is_red_and_marker_stays(self) -> None:
        with self.fixture_root() as root:
            parent = ("import subprocess,sys; "
                      "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                      "sys.stdin.readline()")
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn([BASE_PYTHON, "-c", parent],
                                         stderr=err, unsafe_marker=root / "unsafe.json",
                                         start_receipt=root / "spawn.json",
                                         failure_receipt=root / "spawn-red.json")
                with self.contained(job, root):
                    self.wait_at_least(job, 2)
                    row = job.finish(receipt=root / "finish.json",
                                     unsafe_marker=root / "unsafe.json", timeout=5)
            self.assertEqual(row["state"], "RED_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertTrue((root / "unsafe.json").exists())

    def test_assignment_failure_never_resumes_suspended_child(self) -> None:
        with self.fixture_root() as root:
            sentinel = root / "child-ran.txt"
            code = "from pathlib import Path; Path(%r).write_text('ran')" % str(sentinel)
            with (root / "stderr.bin").open("wb") as err:
                with mock.patch.object(recorder_job, "_assign_job", return_value=0):
                    with self.assertRaises(OSError):
                        recorder_job.spawn(
                            [BASE_PYTHON, "-c", code], stderr=err,
                            unsafe_marker=root / "unsafe.json",
                            start_receipt=root / "spawn.json",
                            failure_receipt=root / "spawn-red.json")
            self.assertFalse(sentinel.exists())
            self.assertTrue((root / "unsafe.json").exists())
            row = json.loads((root / "spawn-red.json").read_text())
            self.assertEqual(row["state"], "RED_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertIsNotNone(row["returncode"])

    def test_start_receipt_write_failure_kills_job_and_keeps_red_marker(self) -> None:
        with self.fixture_root() as root:
            start = root / "spawn.json"
            real_write = recorder_job._write_new

            def fail_start(path: Path, body: dict) -> None:
                if path == start:
                    raise OSError("fixture start receipt write failure")
                real_write(path, body)

            with (root / "stderr.bin").open("wb") as err:
                with mock.patch.object(recorder_job, "_write_new", side_effect=fail_start):
                    with self.assertRaisesRegex(OSError, "fixture start receipt"):
                        recorder_job.spawn(
                            [BASE_PYTHON, "-c", "import sys; sys.stdin.readline()"],
                            stderr=err, unsafe_marker=root / "unsafe.json",
                            start_receipt=start,
                            failure_receipt=root / "spawn-red.json")
            self.assertFalse(start.exists())
            self.assertTrue((root / "unsafe.json").exists())
            row = json.loads((root / "spawn-red.json").read_text())
            self.assertEqual(row["state"], "RED_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)

    def test_terminal_receipt_write_failure_keeps_red_marker(self) -> None:
        with self.fixture_root() as root:
            finish = root / "finish.json"
            real_write = recorder_job._write_new

            def fail_finish(path: Path, body: dict) -> None:
                if path == finish:
                    raise OSError("fixture terminal receipt write failure")
                real_write(path, body)

            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn(
                    [BASE_PYTHON, "-c", "import sys; sys.stdin.readline()"],
                    stderr=err, unsafe_marker=root / "unsafe.json",
                    start_receipt=root / "spawn.json",
                    failure_receipt=root / "spawn-red.json")
                with self.contained(job, root):
                    with mock.patch.object(recorder_job, "_write_new", side_effect=fail_finish):
                        with self.assertRaisesRegex(OSError, "fixture terminal receipt"):
                            job.finish(receipt=finish, unsafe_marker=root / "unsafe.json",
                                       timeout=5)
            self.assertIsNone(job.job)
            self.assertEqual(job.returncode, 0)
            self.assertTrue((root / "unsafe.json").exists())

    def test_actual_breakaway_flags_are_rejected_by_readback(self) -> None:
        job = recorder_job._new_job()
        try:
            unsafe = recorder_job._ExtendedLimit()
            unsafe.BasicLimitInformation.LimitFlags = (
                recorder_job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE |
                recorder_job.JOB_OBJECT_LIMIT_BREAKAWAY_OK)
            changed = recorder_job._set_job(
                job, recorder_job.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                recorder_job.ctypes.byref(unsafe), recorder_job.ctypes.sizeof(unsafe))
            if changed:
                with self.assertRaisesRegex(RuntimeError, "cannot contain descendants"):
                    recorder_job._verified_limit_flags(job)
            else:
                # The kernel itself rejected the unsafe setting.
                self.assertEqual(recorder_job._verified_limit_flags(job),
                                 recorder_job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
        finally:
            recorder_job._close(job)


if __name__ == "__main__":
    unittest.main()
