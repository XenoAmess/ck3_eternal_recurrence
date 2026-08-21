"""Exact-PID CK3 client binding and private client-area capture."""

from __future__ import annotations

from dataclasses import dataclass, field
import ctypes
from pathlib import Path
import time

from .model import Rect
from ..errors import AgentError


EXPECTED_CLIENT_SIZE = (2560, 1440)


def _client_rect(hwnd: int) -> Rect:
    import win32gui

    left, top = win32gui.ClientToScreen(hwnd, (0, 0))
    right, bottom = win32gui.ClientToScreen(
        hwnd, win32gui.GetClientRect(hwnd)[2:4]
    )
    return int(left), int(top), int(right), int(bottom)


def _root_window(hwnd: int) -> int:
    import win32gui

    return int(win32gui.GetAncestor(hwnd, 2))  # GA_ROOT


def _eligible_windows(pid: int) -> list[tuple[int, Rect]]:
    import win32gui
    import win32process

    found: list[tuple[int, Rect]] = []

    def callback(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, actual_pid = win32process.GetWindowThreadProcessId(hwnd)
        if actual_pid != pid:
            return
        rect = _client_rect(hwnd)
        size = rect[2] - rect[0], rect[3] - rect[1]
        if size == EXPECTED_CLIENT_SIZE:
            found.append((int(hwnd), rect))

    win32gui.EnumWindows(callback, None)
    return sorted(found)


@dataclass(frozen=True)
class BoundGameWindow:
    process: object = field(repr=False, compare=False)
    pid: int
    hwnd: int
    client_rect: Rect
    executable: str
    creation_date: str

    @classmethod
    def bind_session(
        cls, session: object, expected_executable: Path
    ) -> "BoundGameWindow":
        from ..runtime import _process_identity, _same_executable

        process = getattr(session, "process", None)
        pid = int(getattr(process, "pid", -1))
        creation_date = str(getattr(session, "ck3_creation_date", ""))
        identity = _process_identity(pid)
        if (
            process is None
            or process.poll() is not None
            or identity is None
            or identity.get("creation_date") != creation_date
            or not _same_executable(identity.get("executable", ""), expected_executable)
            or not _same_executable(process.image_path(), expected_executable)
        ):
            raise AgentError("cannot bind UI to an unauthenticated CK3 process object")
        candidates = _eligible_windows(pid)
        if len(candidates) != 1:
            raise AgentError(
                f"expected exactly one 2560x1440 CK3 client for PID {pid}, "
                f"found {candidates!r}"
            )
        hwnd, rect = candidates[0]
        return cls(
            process=process,
            pid=pid,
            hwnd=hwnd,
            client_rect=rect,
            executable=str(expected_executable.resolve()),
            creation_date=creation_date,
        )

    def verify_process(self) -> None:
        from ..runtime import _process_identity, _same_executable

        if self.process.poll() is not None:
            raise AgentError("bound CK3 process object has exited")
        identity = _process_identity(self.pid)
        if (
            identity is None
            or identity.get("creation_date") != self.creation_date
            or not _same_executable(identity.get("executable", ""), self.executable)
            or not _same_executable(self.process.image_path(), self.executable)
        ):
            raise AgentError("bound CK3 process identity changed")

    def verify(self) -> None:
        self.verify_process()
        candidates = _eligible_windows(self.pid)
        if candidates != [(self.hwnd, self.client_rect)]:
            raise AgentError(
                "bound CK3 HWND/client geometry changed or became ambiguous: "
                f"expected={(self.hwnd, self.client_rect)!r}, actual={candidates!r}"
            )

    def acquire_foreground(self) -> None:
        import pyautogui
        import win32api
        import win32con
        import win32gui
        import win32process

        pyautogui.FAILSAFE = True
        self.verify()
        if _root_window(win32gui.GetForegroundWindow()) == self.hwnd:
            return
        user32 = ctypes.windll.user32
        last_error: Exception | None = None
        for _ in range(3):
            foreground = win32gui.GetForegroundWindow()
            current_thread = win32api.GetCurrentThreadId()
            foreground_thread = (
                win32process.GetWindowThreadProcessId(foreground)[0]
                if foreground
                else 0
            )
            target_thread = win32process.GetWindowThreadProcessId(self.hwnd)[0]
            attached: list[int] = []
            try:
                for thread in {foreground_thread, target_thread}:
                    if thread and thread != current_thread:
                        if user32.AttachThreadInput(current_thread, thread, True):
                            attached.append(thread)
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                win32gui.BringWindowToTop(self.hwnd)
                pyautogui.keyDown("alt")
                try:
                    win32gui.SetForegroundWindow(self.hwnd)
                finally:
                    pyautogui.keyUp("alt")
            except Exception as error:
                last_error = error
            finally:
                for thread in reversed(attached):
                    user32.AttachThreadInput(current_thread, thread, False)
            if _root_window(win32gui.GetForegroundWindow()) == self.hwnd:
                self.verify()
                return
            time.sleep(0.2)
        raise AgentError(f"CK3 client could not obtain foreground: {last_error}")

    def require_foreground(self) -> None:
        import win32gui

        self.verify()
        if _root_window(win32gui.GetForegroundWindow()) != self.hwnd:
            raise AgentError("bound CK3 client lost foreground; refusing input")

    def require_client_unobscured(self) -> None:
        """Reject every visible top-level window above and intersecting CK3."""
        import win32gui

        blockers: list[tuple[int, tuple[int, int, int, int]]] = []
        reached_target = False

        def intersects(first: Rect, second: Rect) -> bool:
            return (
                max(first[0], second[0]) < min(first[2], second[2])
                and max(first[1], second[1]) < min(first[3], second[3])
            )

        def callback(hwnd: int, _: object) -> None:
            nonlocal reached_target
            root = _root_window(hwnd)
            if root == self.hwnd:
                reached_target = True
                return
            if reached_target or not win32gui.IsWindowVisible(root):
                return
            if win32gui.IsIconic(root):
                return
            rect = tuple(int(value) for value in win32gui.GetWindowRect(root))
            if rect[2] <= rect[0] or rect[3] <= rect[1]:
                return
            if intersects(self.client_rect, rect):
                blockers.append((int(root), rect))

        win32gui.EnumWindows(callback, None)
        if not reached_target:
            raise AgentError("bound CK3 top-level window disappeared from Z order")
        if blockers:
            raise AgentError(f"CK3 client is obscured by top-level windows: {blockers!r}")

    def require_unobscured(self, client_point: tuple[int, int]) -> None:
        import win32gui
        import win32process

        screen_point = (
            self.client_rect[0] + client_point[0],
            self.client_rect[1] + client_point[1],
        )
        hit = int(win32gui.WindowFromPoint(screen_point))
        root = _root_window(hit)
        _, actual_pid = win32process.GetWindowThreadProcessId(root)
        if root != self.hwnd or actual_pid != self.pid:
            raise AgentError(
                f"visible target is obscured by hwnd={root}, pid={actual_pid}"
            )

    def require_cursor_target(
        self, client_point: tuple[int, int], *, tolerance: int = 2
    ) -> None:
        import win32gui
        import win32process

        self.require_foreground()
        self.require_client_unobscured()
        expected = (
            self.client_rect[0] + client_point[0],
            self.client_rect[1] + client_point[1],
        )
        actual = tuple(int(value) for value in win32gui.GetCursorPos())
        if (
            abs(actual[0] - expected[0]) > tolerance
            or abs(actual[1] - expected[1]) > tolerance
        ):
            raise AgentError(
                f"cursor left the authenticated visible target: {actual!r} != {expected!r}"
            )
        root = _root_window(int(win32gui.WindowFromPoint(actual)))
        _, actual_pid = win32process.GetWindowThreadProcessId(root)
        if root != self.hwnd or actual_pid != self.pid:
            raise AgentError(
                f"cursor target changed to hwnd={root}, pid={actual_pid}"
            )

    def capture(self) -> object:
        from PIL import ImageGrab

        self.require_foreground()
        self.require_client_unobscured()
        image = ImageGrab.grab(bbox=self.client_rect, all_screens=True)
        self.require_foreground()
        self.require_client_unobscured()
        if image.size != EXPECTED_CLIENT_SIZE:
            raise AgentError(f"captured CK3 client has size {image.size}")
        return image

    def capture_patch(self, client_rect: Rect) -> object:
        """Capture a validated client-relative patch without OCR or persistence."""
        from PIL import ImageGrab

        if (
            len(client_rect) != 4
            or any(type(value) is not int for value in client_rect)
            or client_rect[0] < 0
            or client_rect[1] < 0
            or client_rect[2] <= client_rect[0]
            or client_rect[3] <= client_rect[1]
            or client_rect[2] > EXPECTED_CLIENT_SIZE[0]
            or client_rect[3] > EXPECTED_CLIENT_SIZE[1]
        ):
            raise AgentError(f"invalid CK3 client patch rectangle: {client_rect!r}")
        screen_rect = (
            self.client_rect[0] + client_rect[0],
            self.client_rect[1] + client_rect[1],
            self.client_rect[0] + client_rect[2],
            self.client_rect[1] + client_rect[3],
        )
        self.require_foreground()
        self.require_client_unobscured()
        image = ImageGrab.grab(bbox=screen_rect, all_screens=True)
        self.require_foreground()
        self.require_client_unobscured()
        expected_size = (
            client_rect[2] - client_rect[0],
            client_rect[3] - client_rect[1],
        )
        if image.size != expected_size:
            raise AgentError(
                f"captured CK3 target patch has size {image.size}, expected {expected_size}"
            )
        return image
