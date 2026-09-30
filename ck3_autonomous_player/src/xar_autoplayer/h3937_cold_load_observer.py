"""Optional, bounded observations of one authenticated CK3 cold load.

This module never starts CK3 or sends game input.  A caller must own the
screen before enabling desktop captures.  Native semantic readiness remains
the only authority for the H3937 queries.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import Callable


SAMPLE_SECONDS = 20.0
CAPTURE_SECONDS = 120.0
CAPTURE_TIMEOUT_SECONDS = 12.0
MAX_SAMPLES = 96
MAX_FRAMES = 15
MAX_FRAME_BYTES = 16 * 1024 * 1024
MAX_TOTAL_FRAME_BYTES = MAX_FRAMES * MAX_FRAME_BYTES


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_once(path: Path, value: dict[str, object]) -> str:
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write("\n")
    return _sha256(path)


def _pid_from_capabilities(capabilities: dict[str, object]) -> int | None:
    diagnostics = capabilities.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return None
    pid = diagnostics.get("bridge_pid")
    return pid if type(pid) is int and pid > 0 else None


def _same_executable(actual: str, expected: Path) -> bool:
    return os.path.normcase(os.path.abspath(actual)) == os.path.normcase(
        os.path.abspath(str(expected)))


def _windows_process_counters(pid: int, expected_executable: Path) -> dict[str, object]:
    """Read process identity, CPU and I/O from one pinned Windows handle."""
    if os.name != "nt":
        raise OSError("Windows process counters unavailable on this platform")

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

        def as_int(self) -> int:
            return (int(self.high) << 32) | int(self.low)

    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes",
            "other_bytes")]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.QueryFullProcessImageNameW.argtypes = (
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD))
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(FileTime), ctypes.POINTER(FileTime),
        ctypes.POINTER(FileTime), ctypes.POINTER(FileTime))
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.GetProcessIoCounters.argtypes = (
        wintypes.HANDLE, ctypes.POINTER(IoCounters))
    kernel32.GetProcessIoCounters.restype = wintypes.BOOL
    # PROCESS_QUERY_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION.
    handle = kernel32.OpenProcess(0x0400 | 0x1000, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), "OpenProcess failed")
    try:
        image = ctypes.create_unicode_buffer(32768)
        image_length = wintypes.DWORD(len(image))
        if not kernel32.QueryFullProcessImageNameW(
                handle, 0, image, ctypes.byref(image_length)):
            raise OSError(ctypes.get_last_error(), "QueryFullProcessImageNameW failed")
        executable = image.value
        if not _same_executable(executable, expected_executable):
            raise ValueError("CK3 PID executable identity mismatch")
        created, exited, kernel, user = (FileTime() for _ in range(4))
        if not kernel32.GetProcessTimes(
                handle, ctypes.byref(created), ctypes.byref(exited),
                ctypes.byref(kernel), ctypes.byref(user)):
            raise OSError(ctypes.get_last_error(), "GetProcessTimes failed")
        io = IoCounters()
        if not kernel32.GetProcessIoCounters(handle, ctypes.byref(io)):
            raise OSError(ctypes.get_last_error(), "GetProcessIoCounters failed")
        return {
            "pid": pid, "executable": executable,
            "creation_time_100ns": created.as_int(),
            "cpu_kernel_100ns": kernel.as_int(),
            "cpu_user_100ns": user.as_int(),
            "read_ops": int(io.read_ops), "write_ops": int(io.write_ops),
            "read_bytes": int(io.read_bytes), "write_bytes": int(io.write_bytes),
        }
    finally:
        kernel32.CloseHandle(handle)


def _windows_window_probe(pid: int) -> dict[str, object]:
    from .native_session import (
        _probe_frontend_window_responsiveness, _visible_process_windows,
    )
    import win32gui

    handles = _visible_process_windows(pid)
    foreground = int(win32gui.GetForegroundWindow())
    rows = []
    for hwnd in handles[:8]:
        responded, error, hung = _probe_frontend_window_responsiveness(
            hwnd, timeout_milliseconds=100)
        rows.append({
            "hwnd": hwnd, "minimized": bool(win32gui.IsIconic(hwnd)),
            "wm_null_responded": responded, "wm_null_error": error,
            "is_hung_app_window": hung,
        })
    return {"visible_window_count": len(handles),
            "foreground_owned_by_pid": foreground in handles,
            "windows": rows,
            "window_rows_truncated": len(handles) > len(rows)}


_CAPTURE_SCRIPT = (
    "from pathlib import Path\n"
    "from PIL import ImageGrab\n"
    "from io import BytesIO\n"
    "import os,sys\n"
    "with Path(sys.argv[1]).open('xb') as output:\n"
    "    image_bytes = BytesIO()\n"
    "    ImageGrab.grab().save(image_bytes, format='PNG')\n"
    "    payload = image_bytes.getvalue()\n"
    "    if len(payload) > int(sys.argv[2]):\n"
    "        raise ValueError('PNG exceeds bounded capture bytes')\n"
    "    output.write(payload)\n"
    "    output.flush()\n"
    "    os.fsync(output.fileno())\n"
)


class ColdLoadObserver:
    """Append-only diagnostic sampler with a single bounded capture subprocess."""

    def __init__(
        self, output_dir: Path, expected_executable: Path,
        screen_lease_check: Callable[[], object], *,
        clock: Callable[[], float] = time.monotonic,
        process_probe: Callable[[int, Path], dict[str, object]] = _windows_process_counters,
        window_probe: Callable[[int], dict[str, object]] = _windows_window_probe,
        popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
        timer_factory: Callable[..., threading.Timer] = threading.Timer,
    ) -> None:
        if not callable(screen_lease_check):
            raise ValueError("cold-load capture requires a screen lease check")
        output_dir.mkdir(parents=False, exist_ok=False)
        self.output_dir = output_dir
        self.expected_executable = expected_executable
        self.screen_lease_check = screen_lease_check
        self.clock = clock
        self.process_probe = process_probe
        self.window_probe = window_probe
        self.popen = popen
        self.timer_factory = timer_factory
        self.started = clock()
        self.last_sample = float("-inf")
        self.next_capture = self.started
        self.pid: int | None = None
        self.creation_time: int | None = None
        self.last_process: dict[str, object] | None = None
        self.capture: tuple[
            int, float, subprocess.Popen[bytes], threading.Timer, threading.Event,
        ] | None = None
        self.sample_receipts: list[dict[str, object]] = []
        self.frame_receipts: list[dict[str, object]] = []
        self.process_samples = 0
        self.window_samples = 0
        self.captured_frames = 0
        self.capture_reds = 0
        self.total_frame_bytes = 0
        self.fatal_reason: str | None = None
        self.closed = False
        self.plan_sha256 = _write_once(output_dir / "plan.json", {
            "schema": "xar.h3937.cold-load-observer-plan.v1",
            "created_at_utc": _utc_now(), "expected_executable": str(expected_executable),
            "sample_seconds": SAMPLE_SECONDS, "capture_seconds": CAPTURE_SECONDS,
            "capture_timeout_seconds": CAPTURE_TIMEOUT_SECONDS,
            "max_samples": MAX_SAMPLES, "max_frames": MAX_FRAMES,
            "max_frame_bytes": MAX_FRAME_BYTES,
            "max_total_frame_bytes": MAX_TOTAL_FRAME_BYTES,
            "gameplay_actions": 0, "date_advance_authorized": False,
            "screen_lease_required_for_every_frame": True,
        })

    def _receipt(self, kind: str, number: int, payload: dict[str, object]) -> None:
        path = self.output_dir / f"{kind}-{number:04d}.json"
        digest = _write_once(path, payload)
        row = {"path": str(path), "sha256": digest}
        (self.sample_receipts if kind == "sample" else self.frame_receipts).append(row)

    def _finish_capture(self, *, forced_reason: str | None = None) -> None:
        if self.capture is None:
            return
        number, began, process, timer, timeout_fired = self.capture
        # Cancel and join the independent timer before qualifying a frame.
        # cancel() alone cannot stop a callback already killing/reaping.
        timer.cancel()
        timer.join(timeout=4)
        watchdog_alive = timer.is_alive()
        if watchdog_alive:
            self.fatal_reason = "capture watchdog thread remained after bounded join"
        # A helper completed after its deadline remains RED even if the next
        # readiness poll or close() first notices a successful exit.
        if forced_reason is None and (
                watchdog_alive or timeout_fired.is_set()
                or self.clock() - began >= CAPTURE_TIMEOUT_SECONDS):
            forced_reason = "capture helper exceeded 12s deadline"
        pending = self.output_dir / f"frame-{number:04d}.pending.png"
        final = self.output_dir / f"frame-{number:04d}.png"
        status = "RED_CAPTURE_FAILED"
        error: str | None = forced_reason
        if forced_reason is not None and process.poll() is None:
            for _ in range(2):
                try:
                    process.kill()  # Popen uses the exact owned process handle.
                    process.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired):
                    pass
                if process.poll() is not None:
                    break
        helper_alive = process.poll() is None
        if helper_alive:
            self.fatal_reason = "capture helper remained after bounded kill"
        returncode = process.poll()
        size = pending.stat().st_size if pending.exists() else 0
        partial_sha = _sha256(pending) if pending.exists() else None
        dimensions: list[int] | None = None
        if forced_reason is None and returncode == 0 and 0 < size <= MAX_FRAME_BYTES:
            try:
                self.screen_lease_check()
            except Exception as failure:
                self.fatal_reason = "screen lease lost during capture"
                error = f"{type(failure).__name__}: {failure}"[:256]
            else:
                try:
                    # Pin the same game process again immediately before a
                    # screenshot is qualified.  The process may have exited
                    # or its PID may have been reused during ImageGrab.
                    if self.pid is None or self.creation_time is None:
                        raise ValueError("CK3 process identity absent at frame finish")
                    identity = self.process_probe(self.pid, self.expected_executable)
                    if (identity.get("pid") != self.pid
                            or identity.get("creation_time_100ns") != self.creation_time
                            or not _same_executable(
                                str(identity.get("executable", "")),
                                self.expected_executable)):
                        raise ValueError("CK3 PID, creation time or EXE changed during capture")
                except (OSError, ValueError) as failure:
                    error = f"{type(failure).__name__}: {failure}"[:256]
                    self.fatal_reason = "CK3 process identity unavailable during capture"
                else:
                    try:
                        from PIL import Image
                        with Image.open(pending) as image:
                            if image.format != "PNG":
                                raise ValueError("capture is not PNG")
                            dimensions = list(image.size)
                            image.verify()
                        if final.exists():
                            raise FileExistsError(final)
                        pending.rename(final)
                        status = "CAPTURED_UNREVIEWED"
                    except (OSError, ValueError) as failure:
                        error = f"{type(failure).__name__}: {failure}"[:256]
        elif error is None:
            error = ("capture helper return code or frame size invalid: "
                     f"returncode={returncode}, bytes={size}")
        artifact = final if status == "CAPTURED_UNREVIEWED" else pending
        artifact_size = artifact.stat().st_size if artifact.exists() else 0
        self.total_frame_bytes += artifact_size
        if status == "CAPTURED_UNREVIEWED":
            self.captured_frames += 1
        else:
            self.capture_reds += 1
        self._receipt("frame", number, {
            "schema": "xar.h3937.cold-load-frame.v1",
            "finished_at_utc": _utc_now(), "elapsed_seconds": round(self.clock() - self.started, 3),
            "capture_duration_seconds": round(self.clock() - began, 3),
            "pid": self.pid, "creation_time_100ns": self.creation_time,
            "status": status, "path": str(artifact), "bytes": artifact_size,
            "sha256": _sha256(artifact) if artifact.exists() else None,
            "pending_sha256_before_finalize": partial_sha,
            "dimensions": dimensions, "returncode": returncode,
            "capture_helper_alive": helper_alive,
            "capture_watchdog_alive": watchdog_alive,
            "error": error, "image_visual_reviewed": False,
            "desktop_interaction": False,
        })
        self.capture = None

    def _start_capture(self, now: float) -> None:
        number = len(self.frame_receipts)
        if number >= MAX_FRAMES or self.total_frame_bytes >= MAX_TOTAL_FRAME_BYTES:
            return
        # The 20s sample and the screenshot start are separate moments.
        # Check the exact game handle identity again immediately before spawn.
        try:
            if self.pid is None or self.creation_time is None:
                raise ValueError("CK3 identity absent before capture")
            identity = self.process_probe(self.pid, self.expected_executable)
            if (identity.get("pid") != self.pid
                    or identity.get("creation_time_100ns") != self.creation_time
                    or not _same_executable(
                        str(identity.get("executable", "")),
                        self.expected_executable)):
                raise ValueError("CK3 PID, creation time or EXE changed before capture")
        except (OSError, ValueError) as failure:
            self.fatal_reason = (
                f"CK3 process identity unavailable before capture: "
                f"{type(failure).__name__}")
            return
        try:
            self.screen_lease_check()
        except Exception as failure:
            self.fatal_reason = f"screen lease lost: {type(failure).__name__}"
            return
        pending = self.output_dir / f"frame-{number:04d}.pending.png"
        if pending.exists() or (self.output_dir / f"frame-{number:04d}.png").exists():
            self.fatal_reason = "capture target already exists"
            return
        try:
            with (self.output_dir / f"frame-{number:04d}.stdout.bin").open("xb") as out, (
                    self.output_dir / f"frame-{number:04d}.stderr.bin").open("xb") as err:
                process = self.popen(
                    [sys.executable, "-c", _CAPTURE_SCRIPT, str(pending),
                     str(MAX_FRAME_BYTES)],
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
        except (OSError, subprocess.SubprocessError) as failure:
            self.capture_reds += 1
            self._receipt("frame", number, {
                "schema": "xar.h3937.cold-load-frame.v1",
                "finished_at_utc": _utc_now(), "elapsed_seconds": round(now - self.started, 3),
                "pid": self.pid, "creation_time_100ns": self.creation_time,
                "status": "RED_CAPTURE_START", "path": str(pending),
                "bytes": 0, "sha256": None,
                "error": f"{type(failure).__name__}: {failure}"[:256],
                "image_visual_reviewed": False, "desktop_interaction": False,
            })
            self.next_capture = now + CAPTURE_SECONDS
            return
        timeout_fired = threading.Event()

        def enforce_deadline() -> None:
            if process.poll() is None:
                timeout_fired.set()
                try:
                    process.kill()  # Bound by the exact owned process handle.
                    process.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired):
                    pass

        try:
            remaining = max(0.0, CAPTURE_TIMEOUT_SECONDS - (self.clock() - now))
            timer = self.timer_factory(remaining, enforce_deadline)
            timer.daemon = True
            timer.start()
        except Exception as failure:
            try:
                process.kill()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                self.fatal_reason = "capture helper remained after watchdog start failure"
            self._receipt("frame", number, {
                "schema": "xar.h3937.cold-load-frame.v1",
                "finished_at_utc": _utc_now(), "elapsed_seconds": round(now - self.started, 3),
                "pid": self.pid, "creation_time_100ns": self.creation_time,
                "status": "RED_WATCHDOG_START", "path": str(pending),
                "bytes": pending.stat().st_size if pending.exists() else 0,
                "sha256": _sha256(pending) if pending.exists() else None,
                "error": f"{type(failure).__name__}: {failure}"[:256],
                "capture_helper_alive": process.poll() is None,
                "image_visual_reviewed": False, "desktop_interaction": False,
            })
            self.capture_reds += 1
            self.next_capture = now + CAPTURE_SECONDS
            return
        self.capture = (number, now, process, timer, timeout_fired)
        self.next_capture = now + CAPTURE_SECONDS

    def tick(self, capabilities: dict[str, object]) -> str | None:
        if self.closed:
            return "observer already closed"
        now = self.clock()
        if self.capture is not None:
            _, began, process, _, timeout_fired = self.capture
            if process.poll() is not None:
                self._finish_capture()
            elif timeout_fired.is_set() or now - began >= CAPTURE_TIMEOUT_SECONDS:
                self._finish_capture(forced_reason="capture helper timed out")
        if self.fatal_reason is not None:
            return self.fatal_reason
        if now - self.last_sample < SAMPLE_SECONDS or len(self.sample_receipts) >= MAX_SAMPLES:
            return None
        self.last_sample = now
        pid = _pid_from_capabilities(capabilities)
        row: dict[str, object] = {
            "schema": "xar.h3937.cold-load-sample.v1",
            "sampled_at_utc": _utc_now(),
            "elapsed_seconds": round(now - self.started, 3),
            "pid": pid, "process": None, "window": None,
            "status": "unavailable", "error": None,
        }
        if pid is not None:
            try:
                process = self.process_probe(pid, self.expected_executable)
                creation = process.get("creation_time_100ns")
                if type(creation) is not int or creation <= 0:
                    raise ValueError("process creation time unavailable")
                if (process.get("pid") != pid
                        or not _same_executable(
                            str(process.get("executable", "")),
                            self.expected_executable)):
                    raise ValueError("CK3 PID executable identity mismatch")
                if self.pid is None:
                    self.pid, self.creation_time = pid, creation
                elif pid != self.pid or creation != self.creation_time:
                    self.fatal_reason = "CK3 PID or creation time changed"
                    raise ValueError(self.fatal_reason)
                row["process"] = process
                self.process_samples += 1
                if self.last_process is not None:
                    row["delta_since_prior"] = {
                        key: (process[key] - self.last_process[key])
                        for key in ("cpu_kernel_100ns", "cpu_user_100ns",
                                    "read_ops", "write_ops", "read_bytes", "write_bytes")
                        if type(process.get(key)) is int
                        and type(self.last_process.get(key)) is int
                    }
                self.last_process = process
                try:
                    row["window"] = self.window_probe(pid)
                    row["status"] = "sampled"
                    self.window_samples += 1
                except Exception as failure:
                    row["status"] = "window_unavailable"
                    row["error"] = f"{type(failure).__name__}: {failure}"[:256]
                if now >= self.next_capture and self.capture is None:
                    self._start_capture(now)
            except Exception as failure:
                row["error"] = f"{type(failure).__name__}: {failure}"[:256]
                if isinstance(failure, ValueError) and "identity mismatch" in str(failure):
                    self.fatal_reason = "CK3 executable identity mismatch"
        self._receipt("sample", len(self.sample_receipts), row)
        return self.fatal_reason

    def close(self) -> None:
        if self.closed:
            return
        if self.capture is not None:
            _, _, process, _, _ = self.capture
            self._finish_capture(forced_reason=(
                "observer closed before capture completed"
                if process.poll() is None else None))
        if self.fatal_reason in {
            "capture helper remained after bounded kill",
            "capture helper remained after watchdog start failure",
            "capture watchdog thread remained after bounded join",
        }:
            raise RuntimeError(self.fatal_reason)
        self.closed = True

    def report(self) -> dict[str, object]:
        try:
            plan_unchanged = (
                _sha256(self.output_dir / "plan.json") == self.plan_sha256)
        except OSError:
            plan_unchanged = False
        if self.fatal_reason is not None or not plan_unchanged:
            diagnostic_status = "RED_FATAL"
        elif self.process_samples == 0:
            diagnostic_status = "UNAVAILABLE"
        elif self.capture_reds:
            diagnostic_status = (
                "PARTIAL_CAPTURE_RED" if self.captured_frames else "RED_CAPTURE_UNAVAILABLE")
        elif self.captured_frames == 0:
            diagnostic_status = "PROCESS_ONLY"
        else:
            diagnostic_status = "OBSERVED_UNREVIEWED"
        return {
            "schema": "xar.h3937.cold-load-observer-report.v1",
            "enabled": True, "diagnostic_status": diagnostic_status,
            "output_dir": str(self.output_dir),
            "plan_sha256": self.plan_sha256,
            "plan_unchanged": plan_unchanged,
            "pid": self.pid, "creation_time_100ns": self.creation_time,
            "sample_count": len(self.sample_receipts),
            "process_samples": self.process_samples,
            "window_samples": self.window_samples,
            "frame_count": len(self.frame_receipts),
            "captured_unreviewed_frames": self.captured_frames,
            "capture_reds": self.capture_reds,
            "frame_bytes": self.total_frame_bytes,
            "sample_receipts": self.sample_receipts,
            "frame_receipts": self.frame_receipts,
            "fatal_reason": self.fatal_reason, "closed": self.closed,
            "semantic_readiness_inferred": False,
        }
