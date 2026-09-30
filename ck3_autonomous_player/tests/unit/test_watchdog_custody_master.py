from __future__ import annotations

import builtins
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from xar_autoplayer import runtime  # noqa: E402


class WatchdogCustodyMasterTests(unittest.TestCase):
    def test_import_failure_records_child_without_changing_master_cleanup(self) -> None:
        for receipt_nonce, writer_fails in (("nonce", False), ("other", False), ("nonce", True)):
            with self.subTest(receipt_nonce=receipt_nonce, writer_fails=writer_fails), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                record = root / "ck3.json"
                ready = root / "ready.json"
                marker = root / "unsafe.json"
                marker.write_text("unchanged", encoding="ascii")
                argv = [str(runtime.PROCESS_WATCHDOG), "90", "parent.exe", "creation", receipt_nonce,
                        str(ready), str(record), str(marker), "not_a_game.exe"]
                original_import = builtins.__import__

                def fail_windows_import(name, *arguments, **keywords):
                    if name == "win32api":
                        raise ImportError("injected watchdog import failure")
                    return original_import(name, *arguments, **keywords)

                # Execute the production producer up to its first Windows import.
                with patch.object(sys, "argv", argv), patch.object(os, "getpid", lambda: 102), \
                     patch.object(os, "getppid", lambda: 101), patch.object(builtins, "__import__", fail_windows_import):
                    with self.assertRaisesRegex(ImportError, "injected watchdog import failure"):
                        runpy.run_path(str(runtime.PROCESS_WATCHDOG), run_name="watchdog_import_fault")
                early = record.with_name(f"ck3.{receipt_nonce}.watchdog_start.json")
                published = json.loads(early.read_text(encoding="utf-8"))
                self.assertEqual((published["watchdog_pid"], published["watchdog_parent_pid"]), (102, 101))
                self.assertFalse(ready.exists())
                if receipt_nonce != "nonce":
                    # A stale record at the expected filename is still ignored.
                    early.rename(record.with_name("ck3.nonce.watchdog_start.json"))

                exited = set()
                closed = []
                image_queries = []
                stops = []
                commands = []
                captured = {}
                elapsed = [0.0]

                def image(handle, unused):
                    image_queries.append(handle)
                    if handle in exited:
                        raise OSError("image unavailable after exit")
                    return f"python-{handle}.exe"

                def identity(process_id):
                    return {"pid": process_id, "parent_pid": 90, "name": "pythonw.exe",
                            "executable": f"python-{process_id}.exe", "creation_date": "creation",
                            "command_line": f"python-{process_id}.exe script.py nonce"}

                def sleep(duration):
                    self.assertEqual(duration, 0.1)
                    elapsed[0] += duration
                    exited.add(102)

                def stop(process_id, creation, parent_pid, nonce):
                    stops.append((process_id, creation, parent_pid, nonce))
                    exited.add(process_id)
                    runtime._forget_fallback_watchdog(process_id)
                    return True

                def write_diagnostic(path, payload):
                    self.assertEqual(path, record.with_suffix(".watchdog_bootstrap.json"))
                    captured.update(payload)
                    if writer_fails:
                        raise OSError("injected diagnostic write failure")

                modules = {
                    "win32api": SimpleNamespace(OpenProcess=lambda rights, inherit, process_id: process_id,
                        CloseHandle=closed.append, CommandLineToArgv=lambda command: command.split()),
                    "win32con": SimpleNamespace(SYNCHRONIZE=1, PROCESS_QUERY_INFORMATION=2,
                        PROCESS_QUERY_LIMITED_INFORMATION=4, PROCESS_VM_READ=8),
                    "win32process": SimpleNamespace(GetProcessTimes=lambda handle: {
                        "CreationTime": datetime(2026, 9, 30, tzinfo=timezone.utc)},
                        GetModuleFileNameEx=image, GetExitCodeProcess=lambda handle: 7 if handle in exited else 259),
                    "win32event": SimpleNamespace(WaitForSingleObject=lambda handle, wait: 0 if handle in exited else 258),
                }
                runtime._FALLBACK_WATCHDOG_COMMAND_LINES.clear()
                runtime._FALLBACK_WATCHDOG_PROCESSES.clear()
                runtime._WATCHDOG_PROCESS_CUSTODY.clear()
                with patch.dict(sys.modules, modules), patch.object(runtime, "_process_identity", identity), \
                     patch.object(runtime, "create_process_via_windows_management", lambda command: commands.append(command) or 101), \
                     patch.object(runtime, "_stop_authenticated_watchdog", stop), \
                     patch.object(runtime, "write_json_atomic", write_diagnostic), \
                     patch.object(runtime.time, "monotonic", lambda: elapsed[0]), patch.object(runtime.time, "sleep", sleep):
                    with self.assertRaisesRegex(runtime.UnsafeCleanupError, "bootstrap PID 101 did not become ready"):
                        runtime._start_process_watchdog(90, Path("parent.exe"), "creation", "nonce", ready,
                                                        record, marker, root / "not_a_game.exe")
                self.assertGreaterEqual(elapsed[0], 10)
                self.assertLess(elapsed[0], 10.2)
                self.assertEqual(stops, [(101, "creation", 90, "nonce")])
                self.assertEqual(marker.read_text(encoding="ascii"), "unchanged")
                self.assertFalse(ready.exists())
                self.assertFalse(captured["ck3_launch_attempted"])
                self.assertIsNone(captured["actual_pid"])
                self.assertIsNone(captured["cleanup_error"])
                self.assertNotIn("watchdog_absence_proven", captured)
                before = {entry["pid"]: entry for entry in captured["held_watchdogs_before_cleanup"]}
                after = {entry["pid"]: entry for entry in captured["held_watchdogs_after_cleanup"]}
                expected = {101, 102} if receipt_nonce == "nonce" else {101}
                self.assertEqual(set(before), expected)
                self.assertEqual(set(after), expected)
                self.assertEqual(before[101]["held_handle_returncode"], 259)
                self.assertEqual(after[101]["held_handle_returncode"], 7)
                if receipt_nonce == "nonce":
                    self.assertEqual(before[102]["argv_while_alive"][0], "python-102.exe")
                    self.assertEqual(before[102]["held_handle_wait_status"], 0)
                    self.assertEqual(after[102]["held_handle_returncode"], 7)
                self.assertEqual(set(closed), expected)
                self.assertEqual(len(closed), len(expected))
                self.assertEqual(set(image_queries), expected)
                self.assertEqual(len(image_queries), len(expected))
                self.assertFalse(runtime._WATCHDOG_PROCESS_CUSTODY)
                self.assertEqual(len(commands), 1)
                self.assertIn(" -B ", commands[0])
                self.assertNotIn(" -I ", commands[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
