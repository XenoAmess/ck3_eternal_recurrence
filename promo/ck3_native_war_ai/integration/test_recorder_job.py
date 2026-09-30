"""Harmless Windows process fixtures for optional recorder Job containment."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import recorder_job


@unittest.skipUnless(sys.platform == "win32", "Windows Job API required")
class RecorderJobTests(unittest.TestCase):
    def test_normal_pipe_exit_proves_empty_tree(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn(
                    [sys.executable, "-c", "import sys; sys.stdin.readline()"],
                    stderr=err, unsafe_marker=root / "unsafe.json",
                    failure_receipt=root / "spawn-red.json")
                row = job.finish(receipt=root / "finish.json",
                                 unsafe_marker=root / "unsafe.json", timeout=5)
            self.assertEqual(row["state"], "NORMAL_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertEqual(row["returncode"], 0)
            self.assertFalse((root / "unsafe.json").exists())
            self.assertEqual(json.loads((root / "finish.json").read_text()), row)
            self.assertEqual(job.abort(receipt=root / "late-abort.json",
                                       unsafe_marker=root / "unsafe.json")["state"],
                             "ALREADY_TREE_EMPTY")
            self.assertFalse((root / "late-abort.json").exists())

    def test_abort_kills_descendant_after_root_exits(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = ("import subprocess,sys; "
                      "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                      "sys.stdin.readline()")
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn([sys.executable, "-c", parent],
                                         stderr=err, unsafe_marker=root / "unsafe.json",
                                         failure_receipt=root / "spawn-red.json")
                deadline = time.monotonic() + 5
                while recorder_job._active(job.job) < 2 and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertEqual(recorder_job._active(job.job), 2)
                job.process.communicate(b"q\n", timeout=5)
                self.assertEqual(job.returncode, 0)
                self.assertEqual(recorder_job._active(job.job), 1)
                row = job.abort(receipt=root / "abort.json",
                                unsafe_marker=root / "unsafe.json")
            self.assertEqual(row["state"], "ABORT_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertTrue((root / "unsafe.json").exists())
            self.assertEqual(json.loads((root / "abort.json").read_text()), row)

    def test_normal_finish_with_descendant_is_red_and_marker_stays(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            parent = ("import subprocess,sys; "
                      "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                      "sys.stdin.readline()")
            with (root / "stderr.bin").open("wb") as err:
                job = recorder_job.spawn([sys.executable, "-c", parent],
                                         stderr=err, unsafe_marker=root / "unsafe.json",
                                         failure_receipt=root / "spawn-red.json")
                deadline = time.monotonic() + 5
                while recorder_job._active(job.job) < 2 and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertEqual(recorder_job._active(job.job), 2)
                row = job.finish(receipt=root / "finish.json",
                                 unsafe_marker=root / "unsafe.json", timeout=5)
            self.assertEqual(row["state"], "RED_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertTrue((root / "unsafe.json").exists())

    def test_assignment_failure_never_resumes_suspended_child(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sentinel = root / "child-ran.txt"
            code = "from pathlib import Path; Path(%r).write_text('ran')" % str(sentinel)
            with (root / "stderr.bin").open("wb") as err:
                with mock.patch.object(recorder_job, "_assign_job", return_value=0):
                    with self.assertRaises(OSError):
                        recorder_job.spawn(
                            [sys.executable, "-c", code], stderr=err,
                            unsafe_marker=root / "unsafe.json",
                            failure_receipt=root / "spawn-red.json")
            self.assertFalse(sentinel.exists())
            self.assertTrue((root / "unsafe.json").exists())
            row = json.loads((root / "spawn-red.json").read_text())
            self.assertEqual(row["state"], "RED_TREE_EMPTY")
            self.assertEqual(row["job_active_processes"], 0)
            self.assertIsNotNone(row["returncode"])


if __name__ == "__main__":
    unittest.main()
