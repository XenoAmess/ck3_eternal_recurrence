"""Place one attested CK3 generation on Desktop1 without activating it.

No game input, desktop switch, process launch or termination is exposed here.
The caller owns the runtime admission; --deadline-utc retains its original end.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import importlib.metadata
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

from typing import Literal, NotRequired, Protocol, TypedDict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import ck3_live_run_id
from tools.g2_saved_campaign import background_foreground_contract_v1 as foreground_contract


ObservationPolicy = Literal["legacyDesktop1", "existingGameDesktop"]


class PlacementArguments(Protocol):
    launch_receipt: Path
    ui_dependencies: Path
    receipt: Path
    desktop_id: str
    expected_current_desktop_id: str | None
    deadline_utc: str
    wait_seconds: float
    observation_policy: ObservationPolicy


class LaunchReceipt(TypedDict):
    command: NotRequired[list[str]]
    creation_date: NotRequired[str]
    pid: int
    executable: NotRequired[str]
    creation_filetime: NotRequired[int]


class SourcePin(TypedDict):
    path: str
    sha256: str


class PlacementSource(TypedDict):
    producer: SourcePin
    machine_identity_provider: SourcePin
    foreground_contract: SourcePin
    machine_identity_api: Literal["ck3_live_run_id.current_machine_id"]


class DesktopObservation(TypedDict):
    window_hwnd: int
    on_current_virtual_desktop: bool
    desktop_id: str
    dwm_cloaked_flags: int


class UIDependencies(TypedDict):
    root: str
    versions: dict[str, str]
    module_origins: dict[str, str]
    entry_sha256: dict[str, str]


class PlacementReceipt(TypedDict):
    schema: Literal["xar.g2.managed-desktop1-placement/v1"]
    status: Literal["RED", "GREEN"]
    machine_id: str
    at_utc: str
    source: PlacementSource
    launch_receipt: str
    gameplay_input_sent: Literal[False]
    desktop_switches: Literal[0]
    process_launch_or_stop_calls: Literal[0]
    runtime_rendering_qualified: Literal[False]
    observation_policy: str
    pid: NotRequired[int]
    target_desktop_id: NotRequired[str]
    current_desktop_id: NotRequired[str]
    foreground_before: NotRequired[int]
    sta_hresult: NotRequired[int]
    hwnd: NotRequired[int]
    window_class: NotRequired[str]
    # Existing Python consumers require this exact integer; no JavaScript boundary.
    creation_filetime: NotRequired[int]
    before: NotRequired[DesktopObservation]
    dependencies: NotRequired[UIDependencies]
    after: NotRequired[DesktopObservation]
    window_rect: NotRequired[list[int]]
    client_rect: NotRequired[list[int]]
    foreground_after: NotRequired[int]
    current_desktop_after: NotRequired[str]
    topmost: NotRequired[bool]
    minimized: NotRequired[bool]
    current_desktop_unchanged: NotRequired[Literal[True]]
    foreground_unchanged: NotRequired[bool]
    foreground_observation: NotRequired[foreground_contract.JsonObject]
    background_assignment_verified: NotRequired[bool]
    observation_only: NotRequired[Literal[True]]
    window_mutations: NotRequired[Literal[0]]
    monitor_rect: NotRequired[list[int]]
    work_rect: NotRequired[list[int]]
    client_screen_rect: NotRequired[list[int]]
    fully_visible: NotRequired[Literal[True]]
    visible: NotRequired[bool]
    error: NotRequired[str]


def validate_observation_policy(value: object) -> ObservationPolicy:
    """Validate the explicit read-only observation mode without consulting the OS."""
    if isinstance(value, str):
        if value == "legacyDesktop1":
            return "legacyDesktop1"
        if value == "existingGameDesktop":
            return "existingGameDesktop"
    raise ValueError("unsupported observation policy")


def _positive_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(label + " must be an exact positive integer")
    return value


def _read_launch_document(path: Path) -> dict:
    """Bounded nonempty raw launch document; never normalized."""
    try:
        with path.open("rb") as stream:
            raw = stream.read(1048576 + 1)
    except OSError as error:
        raise ValueError("launch document unreadable") from error
    if not raw or len(raw) > 1048576:
        raise ValueError("bounded nonempty launch document required")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("launch document is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError("launch document must be a JSON object")
    return value


def _validate_java_owner_identity(value: dict) -> dict:
    """Match ordinary Java owner and its immutable HELLO; retain exact FILETIME."""
    owner_fields = {"schema", "machine_id", "session_id", "supervisor", "game", "configuration",
                    "native_hello", "launch_evidence", "stop_request_path", "terminal_path"}
    if set(value) != owner_fields or value.get("schema") != "xar.java-game-supervisor-owner/v1":
        raise ValueError("exact Java supervisor owner schema required")

    def text(item, label):
        if not isinstance(item, str) or not item.strip() or len(item) > 32768:
            raise ValueError(label + " must be bounded nonempty text")
        return item

    def absolute(item, label):
        result = Path(text(item, label))
        if not result.is_absolute():
            raise ValueError(label + " must be absolute")
        return result.resolve()

    def birth(item):
        if (not isinstance(item, str) or not item.isascii() or not item.isdecimal()
                or not 1 <= len(item) <= 20 or item[0] == "0" or int(item) > 0xffffffffffffffff):
            raise ValueError("canonical positive uint64 FILETIME string required")
        return int(item)

    def identity(item, birth_key, kind):
        if not isinstance(item, dict) or set(item) != {"pid", birth_key, "executable"}:
            raise ValueError("exact " + kind + " process identity required")
        if type(item["pid"]) is not int or not 1 <= item["pid"] <= 0xffffffff:
            raise ValueError("native process PID range required")
        image = absolute(item["executable"], kind + " executable")
        names = ("java.exe", "javaw.exe") if kind == "supervisor" else ("ck3.exe",)
        if image.name.casefold() not in names:
            raise ValueError(kind + " executable basename differs")
        return {"pid": item["pid"], "executable": item["executable"], "creation_filetime": birth(item[birth_key])}

    def reference(item, maximum):
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise ValueError("exact launch evidence reference required")
        path = absolute(item["path"], "evidence path")
        if type(item["bytes"]) is not int or not 0 < item["bytes"] <= maximum:
            raise ValueError("bounded positive evidence byte count required")
        digest = item["sha256"]
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)):
            raise ValueError("lowercase evidence SHA256 required")
        return path

    machine = text(value["machine_id"], "owner machine")
    session = text(value["session_id"], "owner session")
    game = identity(value["game"], "creation_filetime", "game")
    identity(value["supervisor"], "creation_filetime", "supervisor")
    # Native hello is metadata here. Never contact its pipe or reinterpret code pins.
    reference(value["native_hello"], 1048576)
    stop = absolute(value["stop_request_path"], "owner stop path")
    terminal = absolute(value["terminal_path"], "owner terminal path")
    if stop.name != "stop-request.json" or terminal.name != "terminal.json" or stop.parent != terminal.parent:
        raise ValueError("actual sibling owner control paths required")
    config = value["configuration"]
    if (not isinstance(config, dict) or config.get("schema") != "xar.java-game-launch-plan/v4"
            or config.get("session_id") != session or not isinstance(config.get("review"), dict)
            or config["review"].get("machine_id") != machine):
        raise ValueError("owner and configuration identities differ")
    request = text(config.get("request_id"), "configuration request")
    configured_game = config["review"].get("game_executable")
    if (not isinstance(configured_game, dict)
            or absolute(configured_game.get("path"), "configured Game") != Path(game["executable"]).resolve()):
        raise ValueError("configured Game executable differs from owner")
    evidence_root = absolute(config.get("evidence_root"), "launch evidence root")
    ref = value["launch_evidence"]
    event_path = reference(ref, 65536)
    if event_path.parent != evidence_root:
        raise ValueError("HELLO must be an actual direct child of launch evidence root")
    with event_path.open("rb") as stream:
        raw = stream.read(ref["bytes"] + 1)
    if len(raw) != ref["bytes"] or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError("HELLO bytes or SHA256 differ from owner reference")
    event = json.loads(raw.decode("utf-8"))
    fields = {"schema", "machine_id", "observed_at_utc", "request_id", "session_id", "event", "game",
              "accounting", "terminal", "terminal_kind", "detail"}
    if (not isinstance(event, dict) or set(event) != fields
            or event["schema"] != "xar.java-game-lifecycle-event/v1" or event["event"] != "HELLO"
            or event["machine_id"] != machine or event["session_id"] != session or event["request_id"] != request
            or event["terminal"] is not None or event["terminal_kind"] is not None):
        raise ValueError("owner requires its own exact HELLO lifecycle row")
    stamp = text(event["observed_at_utc"], "HELLO timestamp")
    try:
        instant = datetime.fromisoformat(stamp[:-1] + "+00:00" if stamp.endswith("Z") else stamp)
        if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
            raise ValueError("UTC instant required")
    except (TypeError, ValueError) as error:
        raise ValueError("HELLO UTC instant is invalid") from error
    hello_game = identity(event["game"], "creation_filetime_decimal", "game")
    if (hello_game["pid"] != game["pid"] or hello_game["creation_filetime"] != game["creation_filetime"]
            or Path(hello_game["executable"]).resolve() != Path(game["executable"]).resolve()):
        raise ValueError("HELLO Game generation differs from owner")
    return game


def parse_launch_receipt(value: object) -> LaunchReceipt:
    """Validate the file boundary before constructing the shared launch contract."""
    if not isinstance(value, dict):
        raise ValueError("launch receipt must be a JSON object")
    if value.get("schema") == "xar.java-game-supervisor-owner/v1":
        identity = _validate_java_owner_identity(value)
        return {"pid": identity["pid"], "executable": identity["executable"], "creation_filetime": identity["creation_filetime"]}
    if (any(key in value for key in ("supervisor", "launch_evidence"))
            or str(value.get("schema", "")).startswith("xar.java-game-supervisor-owner/")):
        raise ValueError("malformed Java owner document")
    command: object = value.get("command")
    creation_date: object = value.get("creation_date")
    if (not isinstance(command, list) or not command
            or not all(isinstance(item, str) and item for item in command)
            or not isinstance(creation_date, str) or not creation_date):
        raise ValueError("use the exact Root Game launch receipt with command and creation_date")
    arguments: list[str] = []
    for item in command:
        if not isinstance(item, str):
            raise ValueError("launch command arguments must be strings")
        arguments.append(item)
    return {"command": arguments, "creation_date": creation_date,
            "pid": _positive_integer(value.get("pid"), "launch pid")}


def _source_pin(path: Path) -> SourcePin:
    actual = path.resolve(strict=True)
    return {"path": str(actual), "sha256": hashlib.sha256(actual.read_bytes()).hexdigest()}


def _new_receipt(launch_receipt: Path) -> PlacementReceipt:
    identity_source = ck3_live_run_id.__file__
    if identity_source is None:
        raise RuntimeError("machine identity provider has no source path")
    contract_source = foreground_contract.__file__
    if contract_source is None or Path(contract_source).resolve() != Path(__file__).resolve().with_name("background_foreground_contract_v1.py"):
        raise RuntimeError("foreground contract belongs to another source root")
    machine_id = ck3_live_run_id.current_machine_id()
    if not isinstance(machine_id, str) or not ck3_live_run_id.SLUG_RE.fullmatch(machine_id):
        raise ValueError("machine identity provider returned an invalid machine ID")
    return {"schema": "xar.g2.managed-desktop1-placement/v1", "status": "RED",
            "machine_id": machine_id, "at_utc": datetime.now(timezone.utc).isoformat(),
            "source": {"producer": _source_pin(Path(__file__)),
                       "machine_identity_provider": _source_pin(Path(identity_source)),
                       "foreground_contract": _source_pin(Path(contract_source)),
                       "machine_identity_api": "ck3_live_run_id.current_machine_id"},
            "launch_receipt": str(launch_receipt.resolve()), "gameplay_input_sent": False,
            "desktop_switches": 0, "process_launch_or_stop_calls": 0,
            "runtime_rendering_qualified": False, "observation_policy": "legacyDesktop1"}


def _desktop_observation(value: dict[str, object]) -> DesktopObservation:
    current = value.get("on_current_virtual_desktop")
    desktop = value.get("desktop_id")
    cloaked = value.get("dwm_cloaked_flags")
    if (not isinstance(current, bool) or not isinstance(desktop, str)
            or not isinstance(cloaked, int) or isinstance(cloaked, bool) or cloaked < 0):
        raise ValueError("native desktop observation is malformed")
    return {"window_hwnd": _positive_integer(value.get("window_hwnd"), "window HWND"),
            "on_current_virtual_desktop": current, "desktop_id": str(uuid.UUID(desktop)),
            "dwm_cloaked_flags": cloaked}


def deadline_check(value: str) -> None:
    end = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if end.tzinfo is None or datetime.now(timezone.utc) >= end:
        raise RuntimeError("original runtime admission deadline reached or missing UTC offset")


class ProcessGeneration:
    """Keep an exact query/synchronization handle until the owner finishes."""

    def __init__(self, pid: int, executable: Path, *, creation_date=None, creation_filetime=None):
        if os.name != "nt" or type(pid) is not int or pid <= 0:
            raise ValueError("an exact positive Windows process PID is required")
        self.pid, self.executable = pid, executable.resolve()
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(ctypes.c_uint64)] * 4
        self.kernel.GetProcessTimes.restype = wintypes.BOOL
        self.kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        self.kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.handle = self.kernel.OpenProcess(0x00101000, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            values = [ctypes.c_uint64() for _ in range(4)]
            if not self.kernel.GetProcessTimes(self.handle, *(ctypes.byref(v) for v in values)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.creation_filetime = values[0].value
            if creation_filetime is not None and self.creation_filetime != creation_filetime:
                raise RuntimeError("process creation FILETIME differs from the pinned generation")
            if creation_date is not None:
                stamp = datetime.strptime(creation_date[:21], "%Y%m%d%H%M%S.%f").replace(
                    tzinfo=timezone(timedelta(minutes=int(creation_date[21:]))))
                actual = self.creation_filetime / 10_000_000 - 11_644_473_600
                if abs(actual - stamp.timestamp()) > .001:
                    raise RuntimeError("process creation date differs from the launch receipt")
            self.check()
        except BaseException:
            self.close()
            raise

    def check(self):
        if not self.handle or self.kernel.WaitForSingleObject(self.handle, 0) != 258:
            raise RuntimeError("pinned process is exited or its kernel state is unknown")
        length = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(length.value)
        if not self.kernel.QueryFullProcessImageNameW(self.handle, 0, image, ctypes.byref(length)):
            raise ctypes.WinError(ctypes.get_last_error())
        if Path(image.value).resolve() != self.executable:
            raise RuntimeError("pinned process image differs from the explicit executable")

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def game_generation(launch: object) -> ProcessGeneration:
    if isinstance(launch, dict) and launch.get("schema") == "xar.java-game-supervisor-owner/v1":
        identity = _validate_java_owner_identity(launch)
        return ProcessGeneration(identity["pid"], Path(identity["executable"]), creation_filetime=identity["creation_filetime"])
    validated = parse_launch_receipt(launch)
    executable = Path(validated["command"][0]).resolve()
    if executable.name.casefold() != "ck3.exe":
        raise ValueError("launch receipt is not the CK3 executable")
    return ProcessGeneration(validated["pid"], executable, creation_date=validated["creation_date"])


def check_game_window(generation, hwnd, classname=None):
    import win32gui
    import win32process
    generation.check()
    if (not win32gui.IsWindow(hwnd)
            or win32process.GetWindowThreadProcessId(hwnd)[1] != generation.pid
            or win32gui.GetWindowText(hwnd) != "Crusader Kings III"
            or (classname is not None and win32gui.GetClassName(hwnd) != classname)):
        raise RuntimeError("the exact Game HWND disappeared, changed generation or identity")


def wait_game_window(generation, seconds, deadline_utc):
    import win32gui
    import win32process
    if not 0 < seconds <= 300:
        raise ValueError("window wait must be finite and at most 300 seconds")
    end = time.monotonic() + seconds
    while True:
        deadline_check(deadline_utc)
        generation.check()
        windows = []
        def collect(hwnd, _):
            if (win32gui.IsWindowVisible(hwnd)
                    and win32process.GetWindowThreadProcessId(hwnd)[1] == generation.pid
                    and win32gui.GetWindowText(hwnd) == "Crusader Kings III"):
                windows.append(hwnd)
        win32gui.EnumWindows(collect, None)
        if len(windows) > 1:
            raise RuntimeError("multiple windows match this exact Game generation")
        if windows:
            check_game_window(generation, windows[0])
            return windows[0]
        if time.monotonic() >= end:
            raise TimeoutError("no unique Game HWND appeared within the bounded wait")
        time.sleep(.25)


def desktop_inventory() -> tuple[list[str], str]:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops") as key:
        raw, _ = winreg.QueryValueEx(key, "VirtualDesktopIDs")
        current, _ = winreg.QueryValueEx(key, "CurrentVirtualDesktop")
    if not isinstance(raw, bytes) or not raw or len(raw) % 16 or not isinstance(current, bytes) or len(current) != 16:
        raise RuntimeError("Shell desktop inventory is malformed")
    ids = [str(uuid.UUID(bytes_le=raw[i:i + 16])) for i in range(0, len(raw), 16)]
    current_id = str(uuid.UUID(bytes_le=current))
    if len(ids) != len(set(ids)) or current_id not in ids:
        raise RuntimeError("Shell desktop inventory is ambiguous")
    return ids, current_id


def explicit_pyvda(root):
    root = root.resolve(strict=True)
    versions = {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions(path=[str(root)])}
    if versions.get("pyvda") != "0.6.0" or versions.get("comtypes") != "1.4.16":
        raise RuntimeError("explicit UI root must contain pyvda0.6.0 and comtypes1.4.16")
    for name in ("pyvda", "comtypes"):
        for loaded_name, module in list(sys.modules.items()):
            if loaded_name == name or loaded_name.startswith(name + "."):
                origin = getattr(module, "__file__", None)
                if not origin or not Path(origin).resolve().is_relative_to(root):
                    raise RuntimeError("ambient UI dependency already loaded: " + loaded_name)
    sys.path.insert(0, str(root))
    import pyvda
    import comtypes
    origins = {name: str(Path(module.__file__).resolve())
               for name, module in (("pyvda", pyvda), ("comtypes", comtypes))}
    if any(not Path(path).is_relative_to(root) for path in origins.values()):
        raise RuntimeError("UI imports escaped the explicit dependency root")
    if getattr(pyvda, "__version__", None) != "0.6.0":
        raise RuntimeError("loaded pyvda version differs from its explicit metadata")
    return pyvda, {"root": str(root), "versions": versions, "module_origins": origins,
                  "entry_sha256": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                                   for name, path in origins.items()}}


def read_foreground_window_v1() -> tuple[int, int | None]:
    """Read HWND/PID with explicit native prototypes; races remain unknown."""
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.GetForegroundWindow.argtypes = []
    user.GetForegroundWindow.restype = wintypes.HWND
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowThreadProcessId.restype = wintypes.DWORD
    before = int(user.GetForegroundWindow() or 0)
    pid = wintypes.DWORD()
    try:
        thread = user.GetWindowThreadProcessId(before, ctypes.byref(pid)) if before else 0
        after = int(user.GetForegroundWindow() or 0)
    except OSError:
        return int(user.GetForegroundWindow() or 0), None
    if before != after or not thread or not pid.value:
        return after, None
    return after, int(pid.value)


def place(args: PlacementArguments) -> PlacementReceipt:
    data = _new_receipt(args.launch_receipt)
    primary: Exception | None = None
    ole = None
    initialized = False
    try:
        deadline_check(args.deadline_utc)
        raw_launch = _read_launch_document(args.launch_receipt)
        launch = parse_launch_receipt(raw_launch)
        data["pid"] = launch["pid"]
        import win32api
        import win32con
        import win32gui
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.windows_virtual_desktop import window_virtual_desktop
        ids, current = desktop_inventory()
        target_id = str(uuid.UUID(args.desktop_id))
        foreground, _ = read_foreground_window_v1()
        data.update({"target_desktop_id": target_id, "current_desktop_id": current,
                     "foreground_before": foreground})
        if target_id != ids[0]:
            raise RuntimeError("explicit target is not the current Shell Desktop1")
        if args.expected_current_desktop_id and current != str(uuid.UUID(args.expected_current_desktop_id)):
            raise RuntimeError("the active user desktop differs from the supplied fresh identity")
        ole = ctypes.WinDLL("ole32", use_last_error=True)
        ole.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
        ole.CoInitializeEx.restype = ctypes.c_long
        ole.CoUninitialize.argtypes = []
        ole.CoUninitialize.restype = None
        result = ole.CoInitializeEx(None, 2)
        data["sta_hresult"] = result & 0xffffffff
        if result not in (0, 1):
            raise RuntimeError("Shell placement requires an explicit STA apartment")
        initialized = True
        with game_generation(raw_launch) as generation:
            hwnd = wait_game_window(generation, args.wait_seconds, args.deadline_utc)
            classname = win32gui.GetClassName(hwnd)
            data.update({"hwnd": hwnd, "window_class": classname,
                         "creation_filetime": generation.creation_filetime,
                         "before": _desktop_observation(window_virtual_desktop(hwnd))})
            pyvda, dependencies = explicit_pyvda(args.ui_dependencies)
            data["dependencies"] = dependencies
            desktops = pyvda.get_virtual_desktops()
            if [str(uuid.UUID(str(d.id).strip("{}"))) for d in desktops] != ids:
                raise RuntimeError("pyvda desktop sequence differs from the Shell inventory")
            target = pyvda.VirtualDesktop(1)
            if str(uuid.UUID(str(target.id).strip("{}"))) != target_id:
                raise RuntimeError("pyvda Desktop1 identity changed")
            def guard() -> None:
                deadline_check(args.deadline_utc)
                check_game_window(generation, hwnd, classname)
                observed_ids, observed_current = desktop_inventory()
                after_foreground, after_pid = read_foreground_window_v1()
                checked_ids, checked_current = desktop_inventory()
                if target_id not in observed_ids or target_id not in checked_ids:
                    raise RuntimeError("the exact managed Game desktop disappeared")
                if checked_current != observed_current:
                    raise RuntimeError("user desktop changed during foreground sampling")
                observation = foreground_contract.classify_current_saved_launch_foreground_v1({
                    "foreground_before": foreground, "foreground_after": after_foreground,
                    "foreground_after_pid": after_pid, "desktop_before": current,
                    "desktop_after": checked_current, "game_pid": generation.pid,
                    "owned_auxiliary_pids": []})
                data.update({"foreground_after": observation.foreground_after,
                             "foreground_unchanged": observation.foreground_unchanged,
                             "foreground_observation": observation.to_wire(),
                             "current_desktop_after": observation.desktop_after})
                if not observation.permitted:
                    raise RuntimeError("background foreground denied: " + observation.classification)
            guard()
            view = pyvda.AppView(hwnd=hwnd)
            if view.hwnd != hwnd:
                raise RuntimeError("Shell AppView does not bind the exact Game HWND")
            view.move(target)
            guard()
            if window_virtual_desktop(hwnd)["desktop_id"] != target_id:
                raise RuntimeError("Desktop1 move was not materially observed")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            guard()
            monitor = win32api.GetMonitorInfo(win32api.MonitorFromWindow(hwnd, 2))["Monitor"]
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style = (style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_MINIMIZE | win32con.WS_MAXIMIZE)) | win32con.WS_POPUP
            if style >= 0x80000000:
                style -= 0x100000000
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            guard()
            left, top, right, bottom = monitor
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, left, top, right - left, bottom - top,
                win32con.SWP_NOACTIVATE | win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW)
            guard()
            final = _desktop_observation(window_virtual_desktop(hwnd))
            client = win32gui.GetClientRect(hwnd)
            actual_rect = win32gui.GetWindowRect(hwnd)
            actual_topmost = bool(win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST)
            actual_minimized = bool(win32gui.IsIconic(hwnd))
            observed_ids, observed_current = desktop_inventory()
            generation.check()
            data.update({"after": final, "window_rect": list(actual_rect),
                         "client_rect": list(client),
                         "topmost": actual_topmost, "minimized": actual_minimized})
            if (final["desktop_id"] != target_id or actual_minimized
                    or not actual_topmost or actual_rect != monitor
                    or client != (0, 0, right - left, bottom - top)
                    or target_id not in observed_ids or observed_current != current
                    or (current != target_id and (final["on_current_virtual_desktop"] is not False
                                                  or not final["dwm_cloaked_flags"] & 2))):
                raise RuntimeError("final Desktop1 geometry/topmost/nonmin qualification failed")
            deadline_check(args.deadline_utc)
            guard()
            data.update({"status": "GREEN", "current_desktop_unchanged": True,
                         "background_assignment_verified": current != target_id})
    except Exception as error:
        data["error"] = str(error)
        primary = error
    finally:
        if initialized and ole is not None:
            ole.CoUninitialize()
        data["at_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            with args.receipt.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
        except OSError as receipt_error:
            raise RuntimeError("placement receipt write failed; primary=" + repr(primary)) from receipt_error
    if primary is not None:
        raise primary
    return data


def observe_placement(args: PlacementArguments) -> PlacementReceipt:
    """Attest two stable read-only snapshots of the already placed Game."""
    if args.receipt.exists() or not args.receipt.parent.is_dir():
        raise ValueError("observation receipt must be new in an existing admitted directory")
    data = _new_receipt(args.launch_receipt)
    data.update(observation_only=True, window_mutations=0)
    primary = None
    try:
        policy = validate_observation_policy(getattr(args, "observation_policy", "legacyDesktop1"))
        data["observation_policy"] = policy
        deadline_check(args.deadline_utc)
        raw_launch = _read_launch_document(args.launch_receipt)
        launch = parse_launch_receipt(raw_launch)
        data["pid"] = launch["pid"]
        import win32api
        import win32con
        import win32gui
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.windows_virtual_desktop import window_virtual_desktop
        ids, current = desktop_inventory()
        target = str(uuid.UUID(args.desktop_id))
        if policy == "legacyDesktop1":
            if not ids or target != ids[0]:
                raise RuntimeError("requested target is not actual Shell Desktop1")
        elif target not in ids or target != current:
            raise RuntimeError("existing Game target must be in the inventory and current desktop")
        if args.expected_current_desktop_id and current != str(uuid.UUID(args.expected_current_desktop_id)):
            raise RuntimeError("current desktop differs from explicit observation admission")
        foreground, _ = read_foreground_window_v1()
        data.update(target_desktop_id=target, current_desktop_id=current, foreground_before=foreground)

        def rect(value):
            result = tuple(value)
            if (len(result) != 4 or any(type(item) is not int for item in result)
                    or result[2] <= result[0] or result[3] <= result[1]):
                raise RuntimeError("positive exact rectangle required")
            return result

        def contains(outer, inner):
            return (outer[0] <= inner[0] and outer[1] <= inner[1]
                    and inner[2] <= outer[2] and inner[3] <= outer[3])

        with game_generation(raw_launch) as generation:
            hwnd = wait_game_window(generation, args.wait_seconds, args.deadline_utc)
            classname = win32gui.GetClassName(hwnd)
            data.update(hwnd=hwnd, window_class=classname, creation_filetime=generation.creation_filetime)

            def snapshot():
                deadline_check(args.deadline_utc)
                check_game_window(generation, hwnd, classname)
                observed_ids, observed_current = desktop_inventory()
                observed_foreground, foreground_pid = read_foreground_window_v1()
                desktop = _desktop_observation(window_virtual_desktop(hwnd))
                monitor_handle = win32api.MonitorFromWindow(hwnd, 0)
                if not monitor_handle:
                    raise RuntimeError("Game has no actual intersecting monitor")
                info = win32api.GetMonitorInfo(monitor_handle)
                monitor, work = rect(info["Monitor"]), rect(info["Work"])
                window, client = rect(win32gui.GetWindowRect(hwnd)), rect(win32gui.GetClientRect(hwnd))
                origin = win32gui.ClientToScreen(hwnd, client[:2])
                end = win32gui.ClientToScreen(hwnd, client[2:])
                screen_client = rect((origin[0], origin[1], end[0], end[1]))
                visible = bool(win32gui.IsWindowVisible(hwnd))
                minimized = bool(win32gui.IsIconic(hwnd))
                topmost = bool(win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST)
                check_game_window(generation, hwnd, classname)
                if observed_ids != ids or observed_current != current or observed_foreground != foreground:
                    raise RuntimeError("desktop inventory/current desktop/foreground changed during observation")
                if desktop["window_hwnd"] != hwnd or desktop["desktop_id"] != target:
                    raise RuntimeError("Game HWND is not on actual Desktop1" if policy == "legacyDesktop1"
                                       else "Game HWND is not on the admitted current desktop")
                if current == target:
                    if not desktop["on_current_virtual_desktop"] or desktop["dwm_cloaked_flags"] != 0:
                        raise RuntimeError("current Game is cloaked or has inconsistent desktop membership")
                elif desktop["on_current_virtual_desktop"] or desktop["dwm_cloaked_flags"] != 2:
                    raise RuntimeError("noncurrent Game must have only actual Shell desktop cloaking")
                if not visible or minimized:
                    raise RuntimeError("Game must already be visible and non-minimized")
                frame_bounds = (monitor, work) if policy == "legacyDesktop1" else (monitor,)
                if not contains(monitor, work) or any(not contains(bounds, area)
                        for bounds in frame_bounds for area in (window, screen_client)):
                    raise RuntimeError("complete Game frame and client must be inside monitor work area"
                                       if policy == "legacyDesktop1" else
                                       "complete Game frame and client must be inside monitor with contained work area")
                return {"ids": list(observed_ids), "current": observed_current, "foreground": observed_foreground,
                    "foreground_pid": foreground_pid, "desktop": desktop, "monitor_handle": monitor_handle,
                    "monitor": monitor, "work": work, "window": window, "client": client,
                    "client_screen": screen_client, "visible": visible, "minimized": minimized, "topmost": topmost}

            before = snapshot()
            after = snapshot()
            if before != after:
                raise RuntimeError("Game observation changed between complete snapshots")
            deadline_check(args.deadline_utc)
            check_game_window(generation, hwnd, classname)
            final_ids, final_current = desktop_inventory()
            final_foreground, _ = read_foreground_window_v1()
            if final_ids != ids or final_current != current or final_foreground != foreground:
                raise RuntimeError("desktop or foreground changed before observation acceptance")
            observation = foreground_contract.classify_current_saved_launch_foreground_v1({
                "foreground_before": foreground, "foreground_after": final_foreground,
                "foreground_after_pid": after["foreground_pid"], "desktop_before": current,
                "desktop_after": final_current, "game_pid": generation.pid, "owned_auxiliary_pids": []})
            # Already-owned Game foreground is an observed fact, not an activation request.
            data.update(before=before["desktop"], after=after["desktop"],
                window_rect=list(after["window"]), client_rect=list(after["client"]),
                monitor_rect=list(after["monitor"]), work_rect=list(after["work"]),
                client_screen_rect=list(after["client_screen"]), topmost=after["topmost"],
                minimized=after["minimized"], visible=after["visible"], fully_visible=True,
                foreground_after=final_foreground, foreground_unchanged=True,
                foreground_observation=observation.to_wire(), current_desktop_after=final_current,
                current_desktop_unchanged=True, background_assignment_verified=current != target, status="GREEN")
    except Exception as error:
        data["status"] = "RED"
        data["error"] = str(error)
        primary = error
    finally:
        data["at_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            with args.receipt.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
        except OSError as receipt_error:
            raise RuntimeError("placement observation receipt write failed; primary=" + repr(primary)) from receipt_error
    if primary is not None:
        raise primary
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--desktop-id", required=True)
    parser.add_argument("--expected-current-desktop-id")
    parser.add_argument("--deadline-utc", required=True)
    parser.add_argument("--wait-seconds", type=float, default=30)
    parser.add_argument("--ui-dependencies", type=Path, required=False)
    parser.add_argument("--observe-only", action="store_true")
    parser.add_argument("--observation-policy", choices=("legacyDesktop1", "existingGameDesktop"),
                        default="legacyDesktop1")
    args = parser.parse_args()
    if args.observation_policy != "legacyDesktop1" and not args.observe_only:
        parser.error("nonlegacy observation policy requires --observe-only")
    if args.receipt.exists() or not args.receipt.parent.is_dir():
        parser.error("receipt must be a new file in the caller's admitted output directory")
    if args.observe_only:
        print(json.dumps(observe_placement(args), ensure_ascii=False))
    else:
        if args.ui_dependencies is None:
            parser.error("--ui-dependencies is required for placement")
        print(json.dumps(place(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
