"""Exact-PID CK3 client binding and private client-area capture."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path

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
    parent_pid: int

    @classmethod
    def bind_session(
        cls, session: object, expected_executable: Path
    ) -> "BoundGameWindow":
        from ..runtime import _process_identity, _same_executable

        process = getattr(session, "process", None)
        pid = int(getattr(process, "pid", -1))
        creation_date = str(getattr(session, "ck3_creation_date", ""))
        identity = _process_identity(pid)
        handle_image = process.image_path() if process is not None else None
        wmi_executable = str(identity.get("executable", "")) if identity else ""
        if (
            process is None
            or process.poll() is not None
            or identity is None
            or str(identity.get("name", "")).casefold() != "ck3.exe"
            or identity.get("creation_date") != creation_date
            or int(identity.get("parent_pid", 0)) != os.getpid()
            or not _same_executable(handle_image, expected_executable)
            or (
                wmi_executable
                and not _same_executable(wmi_executable, expected_executable)
            )
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
            parent_pid=int(identity["parent_pid"]),
        )

    def verify_process(self) -> dict[str, object]:
        from ..runtime import _process_identity, _same_executable

        if self.process.poll() is not None:
            raise AgentError("bound CK3 process object has exited")
        identity = _process_identity(self.pid)
        wmi_executable = str(identity.get("executable", "")) if identity else ""
        if (
            identity is None
            or str(identity.get("name", "")).casefold() != "ck3.exe"
            or int(identity.get("parent_pid", -1)) != self.parent_pid
            or identity.get("creation_date") != self.creation_date
            or (wmi_executable and not _same_executable(wmi_executable, self.executable))
            or not _same_executable(self.process.image_path(), self.executable)
        ):
            raise AgentError("bound CK3 process identity changed")
        return identity

    def verify(self) -> dict[str, object]:
        identity = self.verify_process()
        candidates = _eligible_windows(self.pid)
        if candidates != [(self.hwnd, self.client_rect)]:
            raise AgentError(
                "bound CK3 HWND/client geometry changed or became ambiguous: "
                f"expected={(self.hwnd, self.client_rect)!r}, actual={candidates!r}"
            )
        return identity

    def acquire_foreground(self) -> None:
        """Compatibility shim: foreground is a precondition, never synthesized."""
        self.require_foreground()

    def request_foreground_without_input(self) -> dict[str, object]:
        """Activate the exact bound HWND using window APIs, never key/mouse input.

        Windows foreground-lock policy can return focus to the calling shell
        immediately after CK3 appears.  This method permits one direct
        ``SetForegroundWindow`` call and, only if needed, one caller-to-current
        foreground-thread attachment followed by one more call.  It never uses
        Alt, ``SendInput`` or PyAutoGUI.  Attach and detach are exact mandatory
        pairs, every mutation reauthenticates the pinned process/HWND, and no
        failure is retried by this method.
        """
        import ctypes
        import win32api
        import win32gui
        import win32process

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.AttachThreadInput.argtypes = (
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.c_bool,
        )
        user32.AttachThreadInput.restype = ctypes.c_bool
        def target_identity() -> int:
            self.verify()
            target_thread, target_pid = win32process.GetWindowThreadProcessId(
                self.hwnd
            )
            if int(target_pid) != self.pid or int(target_thread) <= 0:
                raise AgentError("bound CK3 target thread identity differs")
            return int(target_thread)

        target_thread = target_identity()
        current_thread = int(win32api.GetCurrentThreadId())
        input_tick = int(win32api.GetLastInputInfo())

        def foreground_sample() -> tuple[int, int, int]:
            raw = int(win32gui.GetForegroundWindow())
            foreground = _root_window(raw) if raw else 0
            if not foreground:
                return 0, 0, 0
            thread, pid = win32process.GetWindowThreadProcessId(foreground)
            return foreground, int(thread), int(pid)

        def success_payload(
            *,
            mode: str,
            attached_fallback: bool,
            detach_succeeded: bool | None,
        ) -> dict[str, object]:
            if target_identity() != target_thread:
                raise AgentError("bound CK3 target thread changed after activation")
            foreground_after, foreground_thread_after, foreground_pid_after = (
                foreground_sample()
            )
            final_tick = int(win32api.GetLastInputInfo())
            if (
                foreground_after != self.hwnd
                or foreground_thread_after != target_thread
                or foreground_pid_after != self.pid
                or final_tick != input_tick
            ):
                raise AgentError("foreground activation postcondition differs")
            return {
                **base,
                "mode": mode,
                "attached_fallback": attached_fallback,
                "detach_succeeded": detach_succeeded,
                "foreground_hwnd_after": foreground_after,
                "foreground_thread_id_after": foreground_thread_after,
                "foreground_pid_after": foreground_pid_after,
                "last_input_tick_after": final_tick,
                # GetLastInputInfo is only a sampled session tick.  Equality is
                # recorded as an observation, never as proof that no human
                # input occurred.
                "observed_last_input_tick_unchanged": True,
            }

        foreground_before, foreground_thread, foreground_pid = foreground_sample()
        before_triple = (foreground_before, foreground_thread, foreground_pid)
        if not (
            before_triple == (0, 0, 0)
            or all(value > 0 for value in before_triple)
        ):
            raise AgentError(
                "initial foreground identity is incomplete: "
                f"{before_triple!r}"
            )
        base = {
            "format_version": 1,
            "target_pid": self.pid,
            "target_hwnd": self.hwnd,
            "target_thread_id": target_thread,
            "caller_thread_id": current_thread,
            "foreground_hwnd_before": foreground_before,
            "foreground_thread_id_before": foreground_thread,
            "foreground_pid_before": foreground_pid,
            "last_input_tick_before": input_tick,
            "synthetic_input": False,
        }
        if foreground_before == self.hwnd:
            return success_payload(
                mode="already_foreground",
                attached_fallback=False,
                detach_succeeded=None,
            )

        # One direct attempt is permitted.  Reauthenticate the exact target
        # immediately before the mutation and accept only the observed root
        # foreground postcondition.
        if target_identity() != target_thread:
            raise AgentError("bound CK3 target thread changed before activation")
        if int(win32api.GetLastInputInfo()) != input_tick:
            raise AgentError("user input changed before foreground activation")
        try:
            win32gui.SetForegroundWindow(self.hwnd)
        except Exception as error:
            raise AgentError(
                f"direct foreground activation failed: {error}"
            ) from error
        foreground_after_direct, _direct_foreground_thread, _direct_foreground_pid = (
            foreground_sample()
        )
        if foreground_after_direct == self.hwnd:
            return success_payload(
                mode="direct",
                attached_fallback=False,
                detach_succeeded=None,
            )

        # A single fallback may attach only the caller to one stable sampled
        # foreground thread.  Every attach/detach result is mandatory; no
        # target-thread attachment, Alt key, mouse event, or retry loop exists.
        fallback_foreground, fallback_thread, fallback_pid = foreground_sample()
        fallback_tick = int(win32api.GetLastInputInfo())
        if (
            not fallback_foreground
            or fallback_thread <= 0
            or fallback_pid <= 0
            or (
                fallback_foreground,
                fallback_thread,
                fallback_pid,
            )
            != before_triple
            or fallback_thread == current_thread
            or fallback_tick != input_tick
        ):
            raise AgentError(
                "foreground fallback precondition differs: "
                f"foreground={(fallback_foreground, fallback_thread, fallback_pid)!r}, "
                f"caller_thread={current_thread}, "
                f"last_input={(input_tick, fallback_tick)!r}"
            )
        if foreground_sample() != (
            fallback_foreground,
            fallback_thread,
            fallback_pid,
        ):
            raise AgentError("foreground changed before attached fallback")
        # Complete the potentially blocking process/WMI and desktop-enumeration
        # checks before joining input queues.  Between a successful attach and
        # its exact detach, only bounded local Win32 identity/geometry calls are
        # permitted so a slow COM provider cannot leave the queues joined.
        if target_identity() != target_thread:
            raise AgentError("bound CK3 target changed before attached fallback")
        if (
            foreground_sample()
            != (fallback_foreground, fallback_thread, fallback_pid)
            or int(win32api.GetLastInputInfo()) != input_tick
        ):
            raise AgentError("foreground changed after fallback authentication")
        attach_result: bool | None = None
        attach_error = 0
        detach_result: bool | None = None
        detach_error = 0
        detach_exception: BaseException | None = None
        activation_error: BaseException | None = None
        try:
            ctypes.set_last_error(0)
            attach_result = bool(
                user32.AttachThreadInput(current_thread, fallback_thread, True)
            )
            attach_error = ctypes.get_last_error()
            if not attach_result:
                raise AgentError(
                    "foreground fallback AttachThreadInput failed: "
                    f"{attach_error}"
                )
            immediate_target_thread, immediate_target_pid = (
                win32process.GetWindowThreadProcessId(self.hwnd)
            )
            if (
                not win32gui.IsWindow(self.hwnd)
                or not win32gui.IsWindowVisible(self.hwnd)
                or _root_window(self.hwnd) != self.hwnd
                or _client_rect(self.hwnd) != self.client_rect
                or int(immediate_target_thread) != target_thread
                or int(immediate_target_pid) != self.pid
                or foreground_sample()
                != (fallback_foreground, fallback_thread, fallback_pid)
                or int(win32api.GetLastInputInfo()) != input_tick
            ):
                raise AgentError("foreground fallback identity changed")
            win32gui.SetForegroundWindow(self.hwnd)
        except BaseException as error:
            activation_error = error
        finally:
            # None means an asynchronous interruption may have landed between
            # the native attach call and its Python result assignment.  Treat
            # that as possibly attached and attempt the exact detach once.
            if attach_result is not False:
                try:
                    ctypes.set_last_error(0)
                    detach_result = bool(
                        user32.AttachThreadInput(
                            current_thread, fallback_thread, False
                        )
                    )
                    detach_error = ctypes.get_last_error()
                except BaseException as error:
                    detach_exception = error
        if attach_result is False:
            if activation_error is None:  # pragma: no cover - guarded by raise above.
                raise AgentError(
                    "foreground fallback attach failed without an error record"
                )
            raise activation_error
        if detach_exception is not None:
            if not isinstance(detach_exception, Exception):
                if activation_error is not None:
                    detach_exception.add_note(
                        "foreground activation also failed: "
                        f"{type(activation_error).__name__}: {activation_error}"
                    )
                raise detach_exception
            if activation_error is not None:
                activation_error.add_note(
                    "foreground fallback detach raised: "
                    f"{type(detach_exception).__name__}: {detach_exception}"
                )
                raise activation_error
            raise AgentError(
                f"foreground fallback detach raised: {detach_exception}"
            ) from detach_exception
        if detach_result is not True:
            if activation_error is not None and not isinstance(
                activation_error, Exception
            ):
                activation_error.add_note(
                    f"foreground fallback detach also failed: {detach_error}"
                )
                raise activation_error
            raise AgentError(
                f"foreground fallback detach failed: {detach_error}"
            )
        if activation_error is not None:
            if not isinstance(activation_error, Exception):
                raise activation_error
            raise AgentError(
                f"foreground fallback activation failed: {activation_error}"
            ) from activation_error
        return success_payload(
            mode="attached_fallback",
            attached_fallback=True,
            detach_succeeded=detach_result,
        )

    def audit_binding(self) -> dict[str, object]:
        """Return the exact process/window identity bound to every UI receipt."""
        identity = self.verify()
        return {
            "process": {
                "pid": self.pid,
                "parent_pid": self.parent_pid,
                "name": "ck3.exe",
                "creation_date": self.creation_date,
                "executable": self.executable,
                "wmi_executable": str(identity.get("executable", "")),
                "handle_executable": self.executable,
            },
            "window": {
                "hwnd": self.hwnd,
                "client_rect": list(self.client_rect),
                "client_size": list(EXPECTED_CLIENT_SIZE),
            },
        }

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
            # Windows keeps visible 1x1 helper HWNDs at the desktop origin.
            # They cannot materially cover a multi-pixel control/probe, and
            # the final WindowFromPoint guard still authenticates the click
            # pixel itself.
            if rect[2] - rect[0] <= 1 and rect[3] - rect[1] <= 1:
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
