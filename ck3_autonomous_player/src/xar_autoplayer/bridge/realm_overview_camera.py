"""Peace camera policy and an independent native presentation mailbox client."""
from __future__ import annotations

import ctypes
import os
import platform
import threading
import uuid
from dataclasses import dataclass
from typing import Mapping

MAGIC = 0x43524158
MAPPING_BYTES = 131072
COUNTY_CAPACITY = 16384
EXACT_SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
STATUS = {0: "idle", 1: "submitted", 2: "settled", 3: "cancelled",
          4: "stale_actor", 5: "preempted", 6: "unavailable", 7: "target_changed",
          8: "bounds_available"}


class _Request(ctypes.Structure):
    _fields_ = [("mode", ctypes.c_uint32), ("actor", ctypes.c_int32),
                ("date_raw", ctypes.c_int32), ("reserved", ctypes.c_uint32),
                ("expires_uptime_ms", ctypes.c_uint64), ("hwnd", ctypes.c_uint64),
                ("padding", ctypes.c_float), ("title_key", ctypes.c_char * 128)]


class _Result(ctypes.Structure):
    _fields_ = [("request_sequence", ctypes.c_uint32), ("status", ctypes.c_uint32),
                ("actor", ctypes.c_int32), ("date_raw", ctypes.c_int32),
                ("county_count", ctypes.c_uint32), ("client_width", ctypes.c_uint32),
                ("client_height", ctypes.c_uint32), ("zoom_index", ctypes.c_int32),
                ("bounds", ctypes.c_int32 * 4), ("target", ctypes.c_float * 6),
                ("current", ctypes.c_float * 6), ("native_elapsed_us", ctypes.c_uint32),
                ("coverage_verified", ctypes.c_uint32),
                ("county_ids", ctypes.c_int32 * COUNTY_CAPACITY)]


class _Shared(ctypes.Structure):
    _fields_ = [("magic", ctypes.c_uint32), ("version", ctypes.c_uint32),
                ("pid", ctypes.c_uint32), ("reserved", ctypes.c_uint32),
                ("request_sequence", ctypes.c_int32), ("result_sequence", ctypes.c_int32),
                ("request", _Request), ("result", _Result)]


@dataclass
class PeaceRealmCameraPolicy:
    quiet_days: int = 30
    refresh_days: int = 30
    identity: tuple | None = None
    quiet_since: int | None = None
    last_realm_date: int | None = None
    last_hotspot: str | None = None
    mode: str = "idle"

    def observe(self, payload: Mapping, hotspot: Mapping | None) -> dict:
        """Use only the already captured planner frame, with independent timers."""
        frame = payload.get("source_frame") or {}
        date = frame.get("date_raw")
        identity = tuple(frame.get(k) for k in (
            "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation"))
        if type(date) is not int or type(identity[0]) is not int or identity[0] <= 0:
            return {"mode": "cancel", "reason": "incomplete_frame"}
        if identity != self.identity or (self.quiet_since is not None and date < self.quiet_since):
            self.identity, self.quiet_since = identity, None
            self.last_realm_date, self.last_hotspot, self.mode = None, None, "idle"
        blocked = (payload.get("map_ready") is not True or
                   payload.get("mandatory_choice") is True or
                   payload.get("has_active_event") is True or
                   payload.get("has_pending_interaction") is True)
        if blocked:
            self.quiet_since, self.last_realm_date = None, None
            old, self.mode = self.mode, "idle"
            return {"mode": "cancel" if old != "idle" else "hold", "reason": "mandatory_choice"}
        if hotspot is not None:
            self.quiet_since, self.last_realm_date = None, None
            key = str(hotspot["title_key"])
            changed = self.mode != "hotspot" or key != self.last_hotspot
            self.mode, self.last_hotspot = "hotspot", key
            return {"mode": "hotspot" if changed else "hold", "title_key": key,
                    "reason": str(hotspot.get("reason", "observed_war_hotspot"))}
        if payload.get("active_wars") or payload.get("has_player_armies"):
            self.quiet_since, self.last_realm_date = None, None
            old, self.mode = self.mode, "idle"
            return {"mode": "cancel" if old != "idle" else "hold", "reason": "war_or_army_without_land_anchor"}
        if self.quiet_since is None:
            self.quiet_since = date
        if date - self.quiet_since < self.quiet_days * 24:
            return {"mode": "hold", "reason": "peace_quiet_period",
                    "quiet_days_observed": (date - self.quiet_since) / 24}
        if self.last_realm_date is not None and date - self.last_realm_date < self.refresh_days * 24:
            return {"mode": "hold", "reason": "holding_realm_overview"}
        self.mode, self.last_realm_date = "realm", date
        return {"mode": "realm", "reason": "peace_realm_overview",
                "quiet_days_observed": (date - self.quiet_since) / 24}

    def retry_after_failure(self) -> None:
        self.last_realm_date, self.last_hotspot, self.mode = None, None, "idle"


def desktop1_game_window(pid: int, cached: int | None = None) -> int:
    """Check the exact PID/HWND and Desktop 1 without any desktop input."""
    import win32gui
    import win32process
    import winreg
    from .windows_virtual_desktop import window_virtual_desktop
    def owned(hwnd):
        return (win32gui.IsWindow(hwnd) and not win32gui.IsIconic(hwnd)
                and win32process.GetWindowThreadProcessId(hwnd)[1] == pid
                and win32gui.GetWindowText(hwnd) == "Crusader Kings III")
    if not cached or not owned(cached):
        windows = []
        win32gui.EnumWindows(lambda hwnd, _: windows.append(hwnd) if owned(hwnd) else None, None)
        if len(windows) != 1:
            raise ValueError("camera needs the unique owned CK3 window")
        cached = windows[0]
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops") as key:
        desktops, _ = winreg.QueryValueEx(key, "VirtualDesktopIDs")
    if not isinstance(desktops, bytes) or len(desktops) < 16 or len(desktops) % 16:
        raise ValueError("Desktop 1 identity is unavailable")
    first = str(uuid.UUID(bytes_le=desktops[:16]))
    if window_virtual_desktop(cached)["desktop_id"] != first:
        raise ValueError("CK3 window is outside Desktop 1")
    return cached


class NativeCameraPresentationClient:
    """Open the native-created mapping; never use the gameplay named pipe."""
    def __init__(self, pid: int):
        if (os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8
                or platform.machine().upper() not in {"AMD64", "X86_64"}
                or type(pid) is not int or pid <= 0):
            raise ValueError("camera presentation needs an exact Windows CK3 PID")
        self.pid, self._handle, self._view, self._hwnd = pid, None, None, None
        self._last_result_sequence, self._latest = -1, None
        self._lock = threading.Lock()
        self._kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
        self._kernel.OpenFileMappingW.restype = ctypes.c_void_p
        self._kernel.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                             ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
        self._kernel.MapViewOfFile.restype = ctypes.c_void_p
        self._kernel.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
        self._kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        self._kernel.GetTickCount64.restype = ctypes.c_uint64
        self._kernel.FlushProcessWriteBuffers.argtypes = []
        self._kernel.FlushProcessWriteBuffers.restype = None

    def _open(self):
        if self._view:
            return
        self._handle = self._kernel.OpenFileMappingW(
            0xF001F, False, f"Local\\XarCK3CameraPresentationV1-{self.pid}")
        if not self._handle:
            raise OSError("native presentation channel not deployed in this CK3 process")
        self._view = self._kernel.MapViewOfFile(self._handle, 0xF001F, 0, 0, MAPPING_BYTES)
        if not self._view:
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())
        shared = _Shared.from_address(self._view)
        if (shared.magic, shared.version, shared.pid) != (MAGIC, 1, self.pid):
            self.close()
            raise ValueError("native presentation channel identity mismatch")

    def _sequence(self, field: str) -> int:
        # Reviewed Windows AMD64 only: naturally aligned 32-bit loads are atomic.
        # The interpreter cannot hoist either load across the ctypes copy.
        return ctypes.c_uint32.from_address(self._view + getattr(_Shared, field).offset).value

    def _set_sequence(self, value: int):
        ctypes.c_uint32.from_address(self._view + _Shared.request_sequence.offset).value = value
        self._kernel.FlushProcessWriteBuffers()

    def submit(self, intent: Mapping, frame: Mapping, source_build: Mapping) -> dict:
        if (source_build.get("game_version") != "1.20.0.4" or
                str(source_build.get("executable_sha256", "")).upper() != EXACT_SHA):
            raise ValueError("realm camera requires the reviewed exact .4 build")
        with self._lock:
            self._open()
            self._hwnd = desktop1_game_window(self.pid, self._hwnd)
            modes = {"cancel": 0, "realm": 1, "hotspot": 2, "query": 3}
            request = _Request(mode=modes[intent["mode"]], actor=frame["actor_character_id"],
                               date_raw=frame["date_raw"],
                               expires_uptime_ms=self._kernel.GetTickCount64() + 10000,
                               hwnd=self._hwnd, padding=.32 if intent["mode"] == "realm" else .15)
            key = str(intent.get("title_key", "")).encode("ascii")
            if len(key) >= 128:
                raise ValueError("hotspot title key exceeds presentation channel limit")
            request.title_key = key
            sequence = (self._sequence("request_sequence") + 2) & 0xFFFFFFFE
            self._set_sequence(sequence - 1)
            ctypes.memmove(self._view + _Shared.request.offset, ctypes.byref(request), ctypes.sizeof(request))
            self._set_sequence(sequence)
            return {"status": "queued_native_presentation", "request_sequence": sequence,
                    "mode": intent["mode"], "reason": intent.get("reason"),
                    "native_command_pipe_used": False, "desktop": 1,
                    "camera_postcondition_verified": False}

    def latest(self) -> dict | None:
        with self._lock:
            if not self._view:
                return None
            sequence = self._sequence("result_sequence")
            if sequence & 1 or sequence == self._last_result_sequence:
                return self._latest
            result = _Result.from_buffer_copy(ctypes.string_at(
                self._view + _Shared.result.offset, ctypes.sizeof(_Result)))
            if sequence != self._sequence("result_sequence"):
                return self._latest
            if result.county_count > COUNTY_CAPACITY or result.status not in STATUS:
                raise ValueError("malformed native presentation receipt")
            self._last_result_sequence = sequence
            self._latest = {
                "schema": "xar.ck3.camera-presentation-actual/v1",
                "status": STATUS[result.status], "request_sequence": result.request_sequence,
                "actor_character_id": result.actor, "date_raw": result.date_raw,
                "county_count": result.county_count,
                "county_title_ids": list(result.county_ids[:result.county_count]),
                "bounds": list(result.bounds),
                "client_size": [result.client_width, result.client_height],
                "zoom_index": result.zoom_index, "target": list(result.target),
                "current": list(result.current), "native_elapsed_us": result.native_elapsed_us,
                "camera_postcondition_verified": result.status == 2 and result.zoom_index >= 0,
                "coverage_verified": bool(result.coverage_verified),
                "fit_model": "native_bucket_with_viewport_padding",
                "same_frame_with_gameplay_claim": False,
            }
            return self._latest

    def close(self):
        if self._view:
            self._kernel.UnmapViewOfFile(self._view)
            self._view = None
        if self._handle:
            self._kernel.CloseHandle(self._handle)
            self._handle = None
