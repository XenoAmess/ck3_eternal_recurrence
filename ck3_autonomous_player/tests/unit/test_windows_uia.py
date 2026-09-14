from __future__ import annotations

from pathlib import Path
import unittest
from unittest import mock

from xar_autoplayer.windows_uia import (
    WindowsUiaError,
    _is_exact_shell_experience_host,
    dismiss_exact_notification_toast,
)


class _Array:
    def __init__(self, elements: list[object]) -> None:
        self._elements = elements
        self.Length = len(elements)

    def GetElement(self, index: int) -> object:
        return self._elements[index]


class WindowsUiaTests(unittest.TestCase):
    def test_notification_host_allowlist_is_exact(self) -> None:
        self.assertTrue(
            _is_exact_shell_experience_host(
                Path(
                    "C:/Windows/SystemApps/"
                    "ShellExperienceHost_cw5n1h2txyewy/ShellExperienceHost.exe"
                )
            )
        )
        self.assertFalse(
            _is_exact_shell_experience_host(Path("C:/Temp/ShellExperienceHost.exe"))
        )

    def test_exact_sender_and_button_are_invoked_semantically(self) -> None:
        sender = mock.Mock()
        sender.CurrentAutomationId = "SenderName"
        sender.CurrentName = "Realtek高清晰音频管理器"
        button = mock.Mock()
        button.CurrentAutomationId = "DismissButton"
        button.CurrentName = "将此通知移动到操作中心"
        button.CurrentIsEnabled = True
        invoke = mock.Mock()
        button.GetCurrentPattern.return_value.QueryInterface.return_value = invoke
        root = mock.Mock()
        root.CurrentProcessId = 42
        root.FindAll.return_value = _Array([sender, button])
        automation = mock.Mock()
        automation.ElementFromHandle.return_value = root
        module = mock.Mock()
        with mock.patch(
            "xar_autoplayer.windows_uia._window_process_id", return_value=42
        ), mock.patch(
            "xar_autoplayer.windows_uia._process_image_path",
            return_value=Path(
                "C:/Windows/SystemApps/"
                "ShellExperienceHost_fixture/ShellExperienceHost.exe"
            ),
        ), mock.patch(
            "xar_autoplayer.windows_uia._load_automation",
            return_value=(automation, module),
        ):
            result = dismiss_exact_notification_toast(
                7,
                sender_name="Realtek高清晰音频管理器",
                dismiss_name="将此通知移动到操作中心",
            )
        self.assertTrue(result["dismissed"])
        invoke.Invoke.assert_called_once_with()

    def test_wrong_process_path_fails_before_uia(self) -> None:
        with mock.patch(
            "xar_autoplayer.windows_uia._window_process_id", return_value=42
        ), mock.patch(
            "xar_autoplayer.windows_uia._process_image_path",
            return_value=Path("C:/Temp/ShellExperienceHost.exe"),
        ), mock.patch("xar_autoplayer.windows_uia._load_automation") as load:
            with self.assertRaisesRegex(WindowsUiaError, "not the exact"):
                dismiss_exact_notification_toast(
                    7,
                    sender_name="Realtek高清晰音频管理器",
                    dismiss_name="将此通知移动到操作中心",
                )
        load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
