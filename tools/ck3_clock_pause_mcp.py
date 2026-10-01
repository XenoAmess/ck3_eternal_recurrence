"""Desired pause through one qualified SPACE and independent native clock reads.

Authoritative generic owner: this repository. Project callers supply frozen
profile data and an official MCP client; they cannot select a PID, key or command.
The existing native bridge/DLL/session is neither attached nor changed here.
"""
from __future__ import annotations

import argparse
import copy
import ctypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

import ck3_native_profile_mcp as native

SCHEMA = "ck3.clock-pause-profile-receipt.v1"


class _SpaceKeyboardInput(ctypes.Structure):
    _fields_ = [("virtual_key", ctypes.c_uint16), ("scan_code", ctypes.c_uint16),
                ("flags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("extra_info", ctypes.c_size_t)]


class _SpaceInputUnion(ctypes.Union):
    # INPUT's union also contains a 32-byte x64 MOUSEINPUT. Preserve that ABI
    # extent without exposing a mouse or arbitrary-key driver.
    _fields_ = [("keyboard", _SpaceKeyboardInput), ("abi_extent", ctypes.c_byte * 32)]


class _SpaceInput(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("payload", _SpaceInputUnion)]


def shortcut_contract(profile: dict) -> dict:
    executable = Path(profile["guard"]["target"]["executable"])
    if executable.name.lower() != "ck3.exe" or executable.parent.name.lower() != "binaries":
        raise RuntimeError("pause qualification requires the verified CK3 installation layout")
    source = executable.parent.parent / "game/gui/shortcuts.shortcuts"
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest.lower() != profile["pause_shortcut_sha256"].lower():
        raise RuntimeError("installed pause shortcut source SHA-256 changed")
    lines = raw.decode("utf-8-sig").splitlines()
    assignments = [line for line in lines if re.match(r'^\s*pause\s*=', line)]
    if len(assignments) != 1 or not re.fullmatch(r'\s*pause\s*=\s*"SPACE"\s*(?:#.*)?', assignments[0]):
        raise RuntimeError('installed shortcut must uniquely bind pause="SPACE"')
    return {"path": str(source.resolve()), "sha256": digest, "bytes": len(raw),
            "shortcut": "pause", "key": "SPACE", "source": "verified CK3 installation"}


def load_profile(path: Path) -> dict:
    profile = native._load_profile_common(path, {"pause_shortcut_sha256"})
    digest = profile["pause_shortcut_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("pause_shortcut_sha256 requires SHA-256")
    shortcut_contract(profile)
    return profile


class ClockPauseBackend(native.NativeProfileBackend):
    def __init__(self) -> None:
        if ctypes.sizeof(ctypes.c_void_p) != 8 or ctypes.sizeof(_SpaceInput) != 40:
            raise RuntimeError("fixed SPACE input requires the qualified Windows x64 INPUT ABI")
        self._user = ctypes.WinDLL("user32", use_last_error=True)
        self._user.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self._user.GetAsyncKeyState.restype = ctypes.c_short
        self._user.SendInput.argtypes = [ctypes.c_uint32, ctypes.POINTER(_SpaceInput), ctypes.c_int]
        self._user.SendInput.restype = ctypes.c_uint32
        self._user.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        self._user.GetWindowThreadProcessId.restype = ctypes.c_uint32
        self._user.GetKeyboardLayout.argtypes = [ctypes.c_uint32]
        self._user.GetKeyboardLayout.restype = ctypes.c_void_p

    def key_state(self) -> dict:
        return {name: bool(self._user.GetAsyncKeyState(code) & 0x8000) for name, code in (
            ("shift", 0x10), ("control", 0x11), ("alt", 0x12),
            ("left_windows", 0x5B), ("right_windows", 0x5C), ("space", 0x20))}

    def keyboard_langid(self, profile: dict) -> int:
        target = profile["guard"]["target"]
        pid = ctypes.c_uint32()
        thread = int(self._user.GetWindowThreadProcessId(target["hwnd"], ctypes.byref(pid)))
        if not thread or pid.value != target["pid"]:
            raise RuntimeError("pause keyboard layout target thread is unavailable or mismatched")
        layout = self._user.GetKeyboardLayout(thread)
        if not layout:
            raise RuntimeError("pause keyboard layout is unknown")
        return int(layout) & 0xFFFF

    def press_pause(self) -> dict:
        def send_space(key_up: bool) -> int:
            event = _SpaceInput(type=1, payload=_SpaceInputUnion(keyboard=_SpaceKeyboardInput(
                virtual_key=0, scan_code=0x39, flags=0x0008 | (0x0002 if key_up else 0), time=0, extra_info=0)))
            sent = int(self._user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)))
            if sent != 1:
                raise RuntimeError(f"fixed SPACE {'key-up' if key_up else 'key-down'} SendInput ACK failed: sent={sent}; no retry")
            return sent
        down = send_space(False)
        try:
            time.sleep(0.05)
        finally:
            up = send_space(True)  # One paired release even if the pulse wait fails.
        return {"input_method": "fixed-windows-scan-code", "scan_code": 0x39,
                "key_down_ack_count": down, "key_up_ack_count": up, "pulse_seconds": 0.05,
                "ack_is_business_postcondition": False}

    def capture(self, path: Path) -> dict:
        return native.desktop.NativeDesktopBackend().capture(path)


class ClockPauseProfileService(native.NativeClockProfileService):
    def __init__(self, profile: dict, *, backend=None) -> None:
        super().__init__(profile, backend=backend or ClockPauseBackend())
        self.shortcut = shortcut_contract(profile)
        self._clock_binding = None
        self._failed_dispatch = None
        self.pause_timeout_seconds = 5.0
        self.pause_poll_seconds = 0.05

    def _target(self) -> dict:
        target = self.profile["guard"]["target"]
        return {**{key: target[key] for key in ("pid", "hwnd", "process_create_time", "executable",
                "executable_sha256", "build_id")}, "game_version": self.profile["game_version"],
                "userdir": str(Path(self.profile["userdir"]).resolve())}

    def _receipt(self, operation: str, value: dict) -> dict:
        self._sequence += 1
        directory = Path(self.profile["evidence_directory"]) / self.session_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._sequence:04d}-{operation}.json"
        result = {"schema": SCHEMA, "session_id": self.session_id,
                  "profile_sha256": self.profile["profile_sha256"], "target_identity": self._target(),
                  "recorded_at_utc": datetime.now(timezone.utc).isoformat(), **value,
                  "receipt_path": str(path)}
        with path.open("x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, indent=2)
            output.write("\n")
        return result

    def _clock(self) -> tuple[dict, dict]:
        self.guard()
        clock = self.backend.read_clock(self.profile)
        observation = self.guard()
        contract = clock.get("source_contract", {})
        if (type(clock.get("date_raw")) is not int or clock["date_raw"] <= 0
                or type(clock.get("paused")) is not bool or type(clock.get("speed")) is not int
                or not 1 <= clock["speed"] <= 5 or type(clock.get("local_player_id")) is not int
                or clock["local_player_id"] < 0 or type(clock.get("played_character_id")) is not int
                or clock["played_character_id"] <= 0 or clock.get("process_access") != 0x410
                or str(contract.get("executable_sha256", "")).lower() != self._target()["executable_sha256"].lower()
                or self.profile["game_version"] != "1.20.0.2"):
            raise RuntimeError("qualified native campaign clock is unavailable or mismatched")
        binding = tuple(contract.get(key) for key in ("executable_sha256", "header_sha256", "source_sha256", "reader_sha256"))
        if any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value) for value in binding):
            raise RuntimeError("native clock source evidence is incomplete")
        if self._clock_binding is None:
            self._clock_binding = binding
        elif self._clock_binding != binding:
            raise RuntimeError("native clock source contract changed during controller session")
        return copy.deepcopy(clock), observation

    def clock(self) -> dict:
        with self._lock:
            clock, after = self._clock()
            return self._receipt("clock", {"status": "native_clock_verified", "clock": clock,
                "observation_after": after, "uses_desktop_input": False, "uses_injection": False,
                "writes_process_memory": False, "uses_ocr": False})

    def inspect(self) -> dict:
        with self._lock:
            shortcut = shortcut_contract(self.profile)
            clock, after = self._clock()
            return self._receipt("inspect", {"status": "clock_pause_profile_verified", "clock": clock,
                "observation_after": after, "shortcut_contract": shortcut, "uses_desktop_input": False,
                "uses_injection": False, "writes_process_memory": False, "uses_ocr": False})

    def pause(self) -> dict:
        with self._lock:
            if self._failed_dispatch is not None:
                return self._failed_dispatch  # Preserve the first unresolved input; never redispatch.
            attempts = 0
            input_ack = None
            before = after = None
            captures = {}
            try:
                self.guard()
                shortcut = shortcut_contract(self.profile)
                self.backend.poll(self.profile)
                before, observation = self._clock()
                if not before["paused"]:
                    directory = Path(self.profile["evidence_directory"]) / self.session_id
                    directory.mkdir(parents=True, exist_ok=True)
                    stem = f"{self._sequence+1:04d}-pause"
                    captures["before"] = self.backend.capture(directory / f"{stem}-before.png")
                    self._keys_released()
                    # Capture and qualification can take time: reread the native
                    # clock with full foreground/offline/crash guards before input.
                    before, observation = self._clock()
                    shortcut = shortcut_contract(self.profile)
                    if not before["paused"]:
                        self._keys_released()
                        if self.backend.keyboard_langid(self.profile) != 0x0409:
                            raise RuntimeError("pause requires confirmed target English keyboard LANGID=0x0409")
                        self.guard()
                        attempts = 1
                        # Consume this dispatch before calling the driver or
                        # writing evidence. A failed receipt must never reopen it.
                        self._failed_dispatch = {"schema": SCHEMA, "session_id": self.session_id,
                            "profile_sha256": self.profile["profile_sha256"], "target_identity": self._target(),
                            "status": "RED", "desired_paused": True, "input_dispatch_attempts": 1,
                            "reason": "fixed pause dispatch unresolved; no receipt committed"}
                        input_ack = self.backend.press_pause()
                deadline = time.monotonic() + self.pause_timeout_seconds
                while True:
                    after, observation = self._clock()
                    if after["date_raw"] < before["date_raw"] or after["local_player_id"] != before["local_player_id"]:
                        raise RuntimeError("native clock or local player changed during pause")
                    if after["paused"]:
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("desired pause was not observed before deadline; input is not replayed")
                    time.sleep(self.pause_poll_seconds)
                if attempts:
                    captures["after"] = self.backend.capture(directory / f"{stem}-after.png")
                    after, observation = self._clock()
                    if (not after["paused"] or after["date_raw"] < before["date_raw"]
                            or after["local_player_id"] != before["local_player_id"]):
                        raise RuntimeError("desired pause changed during evidence readback; input is not replayed")
                result = self._receipt("pause", {"status": "gameplay_pause_verified", "desired_paused": True,
                    "clock_before": before, "clock_after": after, "observation_after": observation,
                    "shortcut_contract": shortcut, "captures": captures, "input_dispatch_attempts": attempts,
                    "input_driver_ack": input_ack,
                    "uses_desktop_input": bool(attempts), "uses_injection": False,
                    "writes_process_memory": False, "uses_ocr": False})
                self._failed_dispatch = None
                return result
            except Exception as error:
                value = {"status": "RED", "desired_paused": True,
                    "clock_before": before, "clock_after": after, "captures": captures,
                    "input_dispatch_attempts": attempts, "reason": f"{type(error).__name__}: {error}",
                    "input_driver_ack": input_ack,
                    "uses_desktop_input": bool(attempts), "uses_injection": False,
                    "writes_process_memory": False, "uses_ocr": False}
                if attempts:
                    self._failed_dispatch.update(value)
                result = self._receipt("pause", value)
                if attempts:
                    self._failed_dispatch = result
                return result

    def _keys_released(self) -> None:
        states = self.backend.key_state()
        expected = {"shift", "control", "alt", "left_windows", "right_windows", "space"}
        if not isinstance(states, dict) or set(states) != expected or any(type(value) is not bool for value in states.values()):
            raise RuntimeError("pause key and modifier state is unknown")
        if any(states.values()):
            raise RuntimeError("pause key or modifier is already held")


def create_server(service: ClockPauseProfileService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer("CK3 qualified desired pause")
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_clock_pause_profile_v1() -> dict[str, object]:
        return service.inspect()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_read_profile_native_clock_v1() -> dict[str, object]:
        return service.clock()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_pause_profile_gameplay_v1() -> dict[str, object]:
        return service.pause()
    for name in ("ck3_query_clock_pause_profile_v1", "ck3_read_profile_native_clock_v1", "ck3_pause_profile_gameplay_v1"):
        native._forbid_unknown_tool_arguments_v1(server, name)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    create_server(ClockPauseProfileService(load_profile(args.profile))).run(transport="stdio")


if __name__ == "__main__":
    main()
