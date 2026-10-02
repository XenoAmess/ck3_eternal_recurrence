from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from xar_autoplayer import runtime as candidate
from xar_autoplayer import watchdog_process_custody as helper


class Backend:
    def __init__(self) -> None:
        self.exited = set()
        self.closed = []
        self.images = []
        self.api = SimpleNamespace(OpenProcess=lambda rights, inherit, process_id: process_id,
            CloseHandle=self.closed.append, CommandLineToArgv=lambda command: command.split())
        self.constants = SimpleNamespace(SYNCHRONIZE=1, PROCESS_QUERY_INFORMATION=2,
            PROCESS_QUERY_LIMITED_INFORMATION=4, PROCESS_VM_READ=8)
        self.process = SimpleNamespace(GetProcessTimes=lambda handle: {
            "CreationTime": datetime(2026, 9, 30, tzinfo=timezone.utc)},
            GetModuleFileNameEx=self.image, GetExitCodeProcess=lambda handle: 7 if handle in self.exited else 259)
        self.events = SimpleNamespace(WaitForSingleObject=lambda handle, wait: 0 if handle in self.exited else 258)

    def image(self, handle: int, unused: int) -> str:
        self.images.append(handle)
        if handle in self.exited:
            raise OSError("no image after exit")
        return f"python-{handle}.exe"

    def identity(self, process_id: int) -> dict[str, object]:
        return {"pid": process_id, "parent_pid": 90, "name": "pythonw.exe",
            "executable": f"python-{process_id}.exe", "creation_date": "20260930000000.000000+000",
            "command_line": f"python-{process_id}.exe -B script.py nonce"}

    def modules(self):
        return {"win32api": self.api, "win32con": self.constants,
            "win32process": self.process, "win32event": self.events}


class DiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        candidate._FALLBACK_WATCHDOG_COMMAND_LINES.clear()
        candidate._FALLBACK_WATCHDOG_PROCESSES.clear()
        candidate._WATCHDOG_PROCESS_CUSTODY.clear()
        self.backend = Backend()

    def test_held_child_exit_does_not_requery_image(self) -> None:
        with patch.dict(sys.modules, self.backend.modules()):
            custody = helper.WatchdogProcessCustody(self.backend.identity)
            custody.retain(101)
            self.backend.exited.add(101)
            observation = custody.snapshot()[0]
            custody.close()
        self.assertEqual(observation["held_handle_returncode"], 7)
        self.assertEqual(observation["held_handle_wait_status"], 0)
        self.assertEqual(self.backend.images, [101])
        self.assertEqual(self.backend.closed, [101])

    def test_rebind_keeps_bootstrap_popen_and_custody(self) -> None:
        process = SimpleNamespace(wait=lambda timeout: None)
        with patch.dict(sys.modules, self.backend.modules()):
            custody = helper.WatchdogProcessCustody(self.backend.identity)
            custody.retain(101)
            custody.retain(102)
            candidate._FALLBACK_WATCHDOG_PROCESSES[101] = process
            candidate._FALLBACK_WATCHDOG_COMMAND_LINES[101] = "command"
            candidate._WATCHDOG_PROCESS_CUSTODY[101] = custody
            candidate._rebind_fallback_watchdog(101, 102)
            self.assertIs(candidate._FALLBACK_WATCHDOG_PROCESSES[102], process)
            self.assertIs(candidate._WATCHDOG_PROCESS_CUSTODY[102], custody)
            candidate._forget_fallback_watchdog(102)
        self.assertEqual(sorted(self.backend.closed), [101, 102])

    def test_unrelated_early_receipt_does_not_open_handle(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, self.backend.modules()):
            receipt = Path(directory) / "start.json"
            receipt.write_text(json.dumps({"schema": "xar.watchdog-early-start.v1",
                "nonce": "other", "parent_pid": 90, "watchdog_pid": 102}), encoding="ascii")
            custody = helper.WatchdogProcessCustody(self.backend.identity)
            custody.retain_early_receipt(receipt, 90, "nonce")
            self.assertEqual(custody.snapshot(), [])

    def test_real_start_timeout_keeps_actual_child_handle_facts(self) -> None:
        captured = {}
        ticks = [0.0]
        commands = []

        def tick() -> float:
            ticks[0] += 0.01
            return ticks[0]

        def stop(process_id, *arguments):
            self.backend.exited.add(process_id)
            candidate._forget_fallback_watchdog(process_id)
            return True

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record_file = root / "ck3.json"
            start = root / "ck3.nonce.watchdog_start.json"
            start.write_text(json.dumps({"schema": "xar.watchdog-early-start.v1",
                "nonce": "nonce", "parent_pid": 90, "watchdog_parent_pid": 101,
                "watchdog_pid": 102}), encoding="ascii")
            with patch.dict(sys.modules, self.backend.modules()), \
                patch.object(candidate, "_process_identity", self.backend.identity), \
                patch.object(candidate, "create_process_via_windows_management", lambda command: commands.append(command) or 101), \
                patch.object(candidate, "_nonce_bound_watchdog_identities", lambda *values, **keywords: [] if self.backend.exited == {101, 102} else [self.backend.identity(101), self.backend.identity(102)]), \
                patch.object(candidate, "_authenticated_watchdog_state", lambda *values: "running"), \
                patch.object(candidate, "_stop_authenticated_watchdog", stop), \
                patch.object(candidate, "write_json_atomic", lambda path, payload: captured.update(payload)), \
                patch.object(candidate, "WATCHDOG_READY_TIMEOUT_SECONDS", 0.03), \
                patch.object(candidate.time, "monotonic", tick), \
                patch.object(candidate.time, "sleep", lambda duration: None):
                with self.assertRaises(candidate.UnsafeCleanupError):
                    candidate._start_process_watchdog(90, Path("parent.exe"), "creation", "nonce",
                        root / "ready.json", record_file, root / "unsafe-marker.json", root / "not_a_game.exe")
        before = {item["pid"]: item for item in captured["held_watchdogs_before_cleanup"]}
        after = {item["pid"]: item for item in captured["held_watchdogs_after_cleanup"]}
        self.assertEqual(set(before), {101, 102})
        self.assertEqual(before[102]["argv_while_alive"][0], "python-102.exe")
        self.assertEqual(after[102]["held_handle_wait_status"], 0)
        self.assertEqual(after[102]["held_handle_returncode"], 7)
        self.assertEqual(after[101]["held_handle_returncode"], 7)
        self.assertFalse(captured["watchdog_absence_proven"])
        self.assertFalse(captured["ck3_launch_attempted"])
        self.assertIn("no authenticated ready PID", captured["watchdog_cleanup_errors"][-1])
        self.assertNotIn(" -I ", commands[0])
        self.assertEqual(sorted(self.backend.closed), [101, 102])


if __name__ == "__main__":
    unittest.main(verbosity=2)
