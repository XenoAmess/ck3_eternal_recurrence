from __future__ import annotations

import types
import unittest
from unittest import mock

from xar_autoplayer.windows_process import (
    WindowsProcessCreationError,
    create_process_via_windows_management,
)


class _Property:
    def __init__(self, value: object = None) -> None:
        self.Value = value


class _Properties:
    def __init__(self, values: dict[str, object]) -> None:
        self.values = values

    def __call__(self, name: str) -> _Property:
        return _Property(self.values.get(name))


class _Input:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def Properties_(self, name: str) -> _Property:
        target = _Property()
        original_type = type(target)

        class BoundProperty(original_type):
            @property
            def Value(bound_self) -> object:
                return self.values.get(name)

            @Value.setter
            def Value(bound_self, value: object) -> None:
                self.values[name] = value

        return BoundProperty()


class WindowsProcessTests(unittest.TestCase):
    @mock.patch("xar_autoplayer.windows_process.os.name", "nt")
    def test_direct_management_create_returns_pid_without_shell(self) -> None:
        parameters = _Input()
        method = mock.Mock()
        method.InParameters.SpawnInstance_.return_value = parameters
        process_class = mock.Mock()
        process_class.Methods_.return_value = method
        output = mock.Mock()
        output.Properties_ = _Properties({"ReturnValue": 0, "ProcessId": 321})
        service = mock.Mock()
        service.Get.return_value = process_class
        service.ExecMethod_.return_value = output
        pythoncom = mock.Mock()
        client = mock.Mock()
        client.GetObject.return_value = service
        win32com = types.ModuleType("win32com")
        win32com.client = client
        modules = {
            "pythoncom": pythoncom,
            "win32com": win32com,
            "win32com.client": client,
        }
        with mock.patch.dict("sys.modules", modules):
            pid = create_process_via_windows_management(
                '"C:\\Python\\pythonw.exe" worker.py', "C:\\work"
            )
        self.assertEqual(pid, 321)
        self.assertEqual(parameters.values["CurrentDirectory"], "C:\\work")
        self.assertIn("pythonw.exe", str(parameters.values["CommandLine"]))
        pythoncom.CoInitialize.assert_called_once_with()
        pythoncom.CoUninitialize.assert_called_once_with()

    @mock.patch("xar_autoplayer.windows_process.os.name", "nt")
    def test_nonzero_provider_result_fails_closed(self) -> None:
        parameters = _Input()
        method = mock.Mock()
        method.InParameters.SpawnInstance_.return_value = parameters
        process_class = mock.Mock()
        process_class.Methods_.return_value = method
        output = mock.Mock()
        output.Properties_ = _Properties({"ReturnValue": 5, "ProcessId": None})
        service = mock.Mock()
        service.Get.return_value = process_class
        service.ExecMethod_.return_value = output
        pythoncom = mock.Mock()
        client = mock.Mock()
        client.GetObject.return_value = service
        win32com = types.ModuleType("win32com")
        win32com.client = client
        with mock.patch.dict(
            "sys.modules",
            {
                "pythoncom": pythoncom,
                "win32com": win32com,
                "win32com.client": client,
            },
        ):
            with self.assertRaisesRegex(WindowsProcessCreationError, "returned 5"):
                create_process_via_windows_management("worker.exe")

    @mock.patch("xar_autoplayer.windows_process.os.name", "nt")
    def test_modern_dispatch_exec_method_name_is_supported(self) -> None:
        parameters = _Input()
        method = mock.Mock()
        method.InParameters.SpawnInstance_.return_value = parameters
        process_class = mock.Mock()
        process_class.Methods_.return_value = method
        output = mock.Mock()
        output.Properties_ = _Properties({"ReturnValue": 0, "ProcessId": 654})
        service = types.SimpleNamespace(
            Get=mock.Mock(return_value=process_class),
            ExecMethod=mock.Mock(return_value=output),
        )
        pythoncom = mock.Mock()
        client = mock.Mock()
        client.GetObject.return_value = service
        win32com = types.ModuleType("win32com")
        win32com.client = client
        with mock.patch.dict(
            "sys.modules",
            {
                "pythoncom": pythoncom,
                "win32com": win32com,
                "win32com.client": client,
            },
        ):
            pid = create_process_via_windows_management("worker.exe")

        self.assertEqual(pid, 654)
        service.ExecMethod.assert_called_once_with(
            "Win32_Process", "Create", parameters
        )
        pythoncom.CoInitialize.assert_called_once_with()
        pythoncom.CoUninitialize.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
