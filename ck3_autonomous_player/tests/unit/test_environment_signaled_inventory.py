"""Production inventory regression for R74's signaled stale PID 139512."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer import environment
from xar_autoplayer.errors import UnsafeCleanupError


class SignaledInventoryRegressionTests(unittest.TestCase):
    def test_signaled_dead_image_failure_is_excluded_without_hiding_live_errors(self):
        alive_pid, stale_pid = 300, 139512
        entries = [
            {"pid": alive_pid, "parent_pid": 1, "name": "ck3.exe"},
            {"pid": stale_pid, "parent_pid": 1, "name": "ck3.exe"},
        ]
        tasklist = subprocess.CompletedProcess(
            ["tasklist"], 0,
            '"System Idle Process","0","Services","0","8 K"\n'
            '"ck3.exe","300","Console","1","100 K"\n'
            '"ck3.exe","139512","Console","1","100 K"\n',
            "",
        )
        executable = r"C:\game\ck3.exe"

        for wait_result in (0, 258):
            with self.subTest(wait_result=wait_result):
                def open_process(access, inherit, pid):
                    self.assertFalse(inherit)
                    self.assertIn(access, (0x00001000, 0x00100000))
                    if access == 0x00100000:
                        self.assertEqual(pid, stale_pid)
                        return -pid
                    return pid

                def query_image(handle, flags, buffer, length):
                    self.assertEqual(flags, 0)
                    if handle == stale_pid:
                        return False
                    self.assertEqual(handle, alive_pid)
                    buffer.value = executable
                    length._obj.value = len(executable)
                    return True

                def get_times(handle, creation, exit_time, kernel_time, user_time):
                    self.assertEqual(handle, alive_pid)
                    ticks = 116_444_736_000_000_000 + 10_000_000
                    creation._obj.dwHighDateTime = ticks >> 32
                    creation._obj.dwLowDateTime = ticks & 0xFFFFFFFF
                    return True

                def wait(handle, timeout):
                    self.assertEqual(handle, -stale_pid)
                    self.assertEqual(timeout, 0)
                    return wait_result

                def exit_code(handle, code):
                    code._obj.value = 259
                    return True

                kernel = SimpleNamespace(
                    OpenProcess=mock.Mock(side_effect=open_process),
                    QueryFullProcessImageNameW=mock.Mock(side_effect=query_image),
                    GetProcessTimes=mock.Mock(side_effect=get_times),
                    WaitForSingleObject=mock.Mock(side_effect=wait),
                    GetExitCodeProcess=mock.Mock(side_effect=exit_code),
                    CloseHandle=mock.Mock(return_value=True),
                )
                with (
                    mock.patch.object(environment.os, "name", "nt"),
                    mock.patch.object(environment.subprocess, "run", return_value=tasklist) as run,
                    mock.patch.object(environment, "_toolhelp_process_entries", return_value=entries) as snapshot,
                    mock.patch.object(environment.ctypes, "WinDLL", return_value=kernel, create=True),
                    mock.patch.object(environment.ctypes, "get_last_error", return_value=31, create=True),
                ):
                    if wait_result == 0:
                        inventory = environment.ck3_process_inventory()
                        for field in ("tasklist_pids", "native_pids", "wmi_pids"):
                            self.assertEqual(inventory[field], [alive_pid])
                        self.assertEqual(inventory["inventory_backend"], "tasklist+toolhelp32")
                        self.assertEqual(inventory["processes"], [{
                            "pid": alive_pid, "parent_pid": 1, "name": "ck3.exe",
                            "executable": executable,
                            "creation_date": "19700101000001.000000+000",
                        }])
                    else:
                        with self.assertRaisesRegex(
                            UnsafeCleanupError,
                            r"Toolhelp process 139512 image query failed: winerror=31",
                        ):
                            environment.ck3_process_inventory()
                run.assert_called_once()
                snapshot.assert_called_once()
                self.assertEqual(kernel.OpenProcess.call_args_list, [
                    mock.call(0x00001000, False, alive_pid),
                    mock.call(0x00001000, False, stale_pid),
                    mock.call(0x00100000, False, stale_pid),
                ])
                self.assertEqual(kernel.QueryFullProcessImageNameW.call_count, 2)
                kernel.GetProcessTimes.assert_called_once()
                kernel.WaitForSingleObject.assert_called_once_with(-stale_pid, 0)
                kernel.GetExitCodeProcess.assert_not_called()
                self.assertEqual(kernel.CloseHandle.call_args_list, [
                    mock.call(alive_pid), mock.call(-stale_pid), mock.call(stale_pid),
                ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
