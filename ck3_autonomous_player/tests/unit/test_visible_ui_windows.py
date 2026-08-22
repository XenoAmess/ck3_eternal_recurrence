from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.control.executor import _prepare_left_click_batch  # noqa: E402
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.vision.window import BoundGameWindow, _client_rect  # noqa: E402


HELPER = ROOT / "tests" / "helpers" / "visible_ui_window_helper.py"
RUN_INTEGRATION = (
    os.name == "nt" and os.environ.get("XAR_RUN_VISIBLE_UI_INTEGRATION") == "1"
)


def _wait_json(path: Path, timeout: float = 10.0) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except (FileNotFoundError, OSError, json.JSONDecodeError) as error:
            last_error = error
        time.sleep(0.05)
    raise AssertionError(f"helper evidence did not arrive: {path}: {last_error}")


class _PinnedHelperProcess:
    def __init__(self, process: subprocess.Popen[bytes], executable: Path) -> None:
        self._process = process
        self.pid = process.pid
        self._executable = executable

    def poll(self) -> int | None:
        return self._process.poll()

    def image_path(self) -> str:
        import win32process

        actual = Path(
            win32process.GetModuleFileNameEx(int(self._process._handle), 0)
        ).resolve()
        if actual != self._executable:
            raise AssertionError(
                f"pinned helper handle image differs: {actual} != {self._executable}"
            )
        return str(actual)


@unittest.skipUnless(
    RUN_INTEGRATION,
    "set XAR_RUN_VISIBLE_UI_INTEGRATION=1 to exercise the real Win32 desktop",
)
class VisibleUiWindowsIntegrationTests(unittest.TestCase):
    def _start(
        self, root: Path, name: str, *, overlay: bool = False
    ) -> tuple[subprocess.Popen[bytes], dict[str, object], Path]:
        ready = root / f"{name}-ready.json"
        events = root / f"{name}-events.json"
        executable = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
        command = [
            str(executable),
            str(HELPER),
            "--ready",
            str(ready),
            "--events",
            str(events),
        ]
        if overlay:
            command.append("--overlay")
        environment = os.environ.copy()
        site_packages = Path(sys.prefix) / "Lib" / "site-packages"
        environment["XAR_HELPER_SITE_PACKAGES"] = str(site_packages)
        python_paths = (
            site_packages,
            site_packages / "win32",
            site_packages / "win32" / "lib",
            site_packages / "pythonwin",
        )
        environment["PYTHONPATH"] = os.pathsep.join(
            value
            for value in (
                *(str(path) for path in python_paths),
                environment.get("PYTHONPATH", ""),
            )
            if value
        )
        environment["PATH"] = os.pathsep.join(
            (
                str(site_packages / "pywin32_system32"),
                environment.get("PATH", ""),
            )
        )
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            env=environment,
        )
        try:
            payload = _wait_json(ready)
        except BaseException:
            process.terminate()
            process.wait(timeout=5)
            error = process.stderr.read().decode("utf-8", errors="replace")
            raise AssertionError(f"Win32 helper failed: {error}")
        self.assertEqual(payload["pid"], process.pid)
        return process, payload, events

    @staticmethod
    def _close(process: subprocess.Popen[bytes], hwnd: int) -> None:
        import win32con
        import win32gui

        if process.poll() is None:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                process.wait(timeout=5)
            except BaseException:
                process.terminate()
                process.wait(timeout=5)

    def test_real_window_binding_obstruction_and_single_target_click(self) -> None:
        import win32api
        import win32con
        import win32gui

        with tempfile.TemporaryDirectory(prefix="xar-visible-win32-") as temporary:
            root = Path(temporary)
            target, ready, events = self._start(root, "target")
            overlay: subprocess.Popen[bytes] | None = None
            overlay_hwnd = 0
            hwnd = int(ready["hwnd"])
            try:
                self.assertEqual(ready["dpi"], 96)
                expected_rect = tuple(int(value) for value in ready["client_rect"])
                self.assertEqual(_client_rect(hwnd), expected_rect)
                self.assertEqual(
                    (expected_rect[2] - expected_rect[0], expected_rect[3] - expected_rect[1]),
                    (2560, 1440),
                )

                executable = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
                pinned = _PinnedHelperProcess(target, executable)
                creation = "integration-created"
                identity = {
                    "pid": target.pid,
                    "parent_pid": os.getpid(),
                    "name": "ck3.exe",
                    "creation_date": creation,
                    "executable": "",
                }
                session = types.SimpleNamespace(
                    process=pinned, ck3_creation_date=creation
                )
                with mock.patch(
                    "xar_autoplayer.runtime._process_identity",
                    return_value=identity,
                ):
                    binding = BoundGameWindow.bind_session(session, executable)
                    self.assertEqual(
                        binding.audit_binding()["process"]["wmi_executable"], ""
                    )

                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.1)
                    binding.require_foreground()
                    binding.require_client_unobscured()

                    overlay, overlay_ready, _overlay_events = self._start(
                        root, "overlay", overlay=True
                    )
                    overlay_hwnd = int(overlay_ready["hwnd"])
                    if overlay_ready["foreground"]:
                        with self.assertRaisesRegex(AgentError, "lost foreground"):
                            binding.require_foreground()
                    else:
                        # Foreground-lock policy can leave the target active;
                        # the topmost overlay must still be rejected by the
                        # independent Z-order/pixel obstruction guard.
                        binding.require_foreground()
                    with self.assertRaisesRegex(AgentError, "obscured"):
                        binding.require_client_unobscured()
                    win32gui.SetWindowPos(
                        overlay_hwnd,
                        win32con.HWND_TOPMOST,
                        0,
                        0,
                        0,
                        0,
                        win32con.SWP_NOMOVE
                        | win32con.SWP_NOSIZE
                        | win32con.SWP_NOACTIVATE,
                    )
                    time.sleep(0.1)
                    with self.assertRaisesRegex(AgentError, "obscured"):
                        binding.require_client_unobscured()
                    self._close(overlay, overlay_hwnd)
                    overlay = None

                    binding.request_foreground_without_input()
                    point = (
                        binding.client_rect[0] + 600,
                        binding.client_rect[1] + 557,
                    )
                    win32api.SetCursorPos(point)
                    binding.require_cursor_target((600, 557))
                    submit = _prepare_left_click_batch()
                    self.assertEqual(submit(), (2, 0))
                    receipt = _wait_json(events)
                    self.assertEqual(receipt["down"], 1)
                    self.assertEqual(receipt["up"], 1)
                    self.assertEqual(receipt["completed_clicks"], 1)
                    self.assertEqual(receipt["outside"], 0)
            finally:
                if overlay is not None:
                    self._close(overlay, overlay_hwnd)
                self._close(target, hwnd)


if __name__ == "__main__":
    unittest.main()
