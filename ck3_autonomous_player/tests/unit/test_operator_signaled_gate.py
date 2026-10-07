"""Production Operator preflight regression for a signaled stale CK3 PID."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer import operator_mcp


class OperatorSignaledGateRegressionTests(unittest.TestCase):
    def test_preflight_excludes_only_signaled_matching_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "python.exe"
            executable.write_bytes(b"offline regression")
            job = operator_mcp.OperatorJobProfile(
                name="managed", command=(str(executable),), working_directory=root,
                exclusive_process_names=("ck3.exe",), required_paths=(), absent_paths=(), controls={},
            )
            profile = operator_mcp.OperatorProfile(
                source_path=root / "operator.json", source_sha256="fixture",
                target_id="operator-a", display_name="Operator A",
                expected_token_user="operator", expected_desktop="desktop", expected_machine="machine",
                endpoint_transport="stdio", endpoint_host="127.0.0.1", endpoint_port=9876,
                advertised_url=None, state_directory=root / "state", jobs={"managed": job}, steam=None,
            )
            identity = operator_mcp.HostIdentity("operator", "desktop", "machine", 100)
            # First reproduce the actual stale PID; then retain timeout and
            # inaccessible matching entries while ignoring another image.
            for retained in ([], [139513, 139514]):
                with self.subTest(retained=retained):
                    rows = [(777, "python.exe"), (139512, "ck3.exe")]
                    rows.extend((pid, "ck3.exe") for pid in retained)
                    cursor = -1

                    def fill(pointer):
                        nonlocal cursor
                        cursor += 1
                        if cursor >= len(rows):
                            return False
                        pointer._obj.th32ProcessID, pointer._obj.szExeFile = rows[cursor]
                        return True

                    def first(snapshot, pointer):
                        self.assertEqual(snapshot, 900)
                        return fill(pointer)

                    def next_entry(snapshot, pointer):
                        self.assertEqual(snapshot, 900)
                        return fill(pointer)

                    def open_process(access, inherit, pid):
                        self.assertEqual(access, 0x00100000)
                        self.assertFalse(inherit)
                        self.assertNotEqual(pid, 777)
                        return None if pid == 139514 else pid

                    def wait(handle, timeout):
                        self.assertEqual(timeout, 0)
                        return 0 if handle == 139512 else 258

                    kernel = SimpleNamespace(
                        CreateToolhelp32Snapshot=mock.Mock(return_value=900),
                        Process32FirstW=mock.Mock(side_effect=first),
                        Process32NextW=mock.Mock(side_effect=next_entry),
                        OpenProcess=mock.Mock(side_effect=open_process),
                        WaitForSingleObject=mock.Mock(side_effect=wait),
                        CloseHandle=mock.Mock(return_value=True),
                    )
                    service = operator_mcp.OperatorService(profile, identity_probe=lambda: identity)
                    with (
                        mock.patch.object(operator_mcp.os, "name", "nt"),
                        mock.patch.object(operator_mcp.ctypes, "WinDLL", return_value=kernel, create=True),
                    ):
                        result = service.preflight_job("operator-a", "managed")
                    self.assertEqual(result["observations"]["process_gates"]["ck3.exe"], retained)
                    self.assertEqual(result["result"], "RED" if retained else "GREEN")
                    self.assertEqual(result["failed_checks"], ["process_absent:ck3.exe"] if retained else [])
                    self.assertEqual(result["process_gate_errors"], {})
                    kernel.CreateToolhelp32Snapshot.assert_called_once_with(0x00000002, 0)
                    self.assertEqual(kernel.OpenProcess.call_args_list, [
                        mock.call(0x00100000, False, pid) for pid in [139512, *retained]
                    ])
                    self.assertEqual(kernel.WaitForSingleObject.call_args_list, [
                        mock.call(pid, 0) for pid in [139512, *retained] if pid != 139514
                    ])
                    self.assertEqual(kernel.CloseHandle.call_args_list, [
                        mock.call(pid) for pid in [139512, *retained, 900] if pid != 139514
                    ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
