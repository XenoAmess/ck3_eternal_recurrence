"""Software-only foreground producer/consumer regression tests.

All GUI/process/native calls are replaced before execution. No desktop, process,
SDK, recording or receipt file is created by this module.
"""
from __future__ import annotations

import ast
import base64
import ctypes
from contextlib import ExitStack
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
from types import ModuleType
from typing import Callable
import unittest
import zlib
from unittest.mock import patch

from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
from tools.g2_saved_campaign import current_saved_background_display_v1 as renderer
from tools.g2_saved_campaign import managed_desktop1_placement as placement

USER_DESKTOP = "11b2eee2-855d-4029-b35c-59adc9a19203"
GAME_DESKTOP = "964b3ff9-3cf7-4ba9-881b-47444f31cfbe"
OTHER_DESKTOP = "994b3ff9-3cf7-4ba9-881b-47444f31cfbe"
GAME_PID = 700
OBS_PID = 800


def observation(after: int = 12, pid: int | None = 200, desktop: str = USER_DESKTOP,
                auxiliary: list[int] | None = None) -> contract.LaunchForegroundObservationV1:
    return contract.classify_current_saved_launch_foreground_v1({
        "foreground_before": 11, "foreground_after": after, "foreground_after_pid": pid,
        "desktop_before": USER_DESKTOP, "desktop_after": desktop, "game_pid": GAME_PID,
        "owned_auxiliary_pids": [] if auxiliary is None else auxiliary})


def selected(source: str, names: set[str]) -> str:
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    if {node.name for node in nodes} != names:
        raise AssertionError("Actual selected functions differ")
    statements: list[ast.stmt] = list(nodes)
    return ast.unparse(ast.Module(body=statements, type_ignores=[]))


class ContractTests(unittest.TestCase):
    def test_user_windows_and_round_trip(self) -> None:
        for hwnd in (11, 12, 13):
            with self.subTest(hwnd=hwnd):
                value = observation(hwnd)
                self.assertTrue(value.permitted)
                self.assertEqual(value.foreground_unchanged, hwnd == 11)
                decoded: object = json.loads(json.dumps(value.to_wire()))
                self.assertEqual(contract.parse_current_saved_launch_foreground_v1(decoded), value)

    def test_owned_and_unknown_even_unchanged(self) -> None:
        for hwnd in (11, 12):
            for pid in (GAME_PID, OBS_PID, None):
                with self.subTest(hwnd=hwnd, pid=pid):
                    self.assertFalse(observation(hwnd, pid, auxiliary=[OBS_PID]).permitted)
        self.assertFalse(observation(desktop=OTHER_DESKTOP).permitted)

    def test_exact_wire_and_malicious_types(self) -> None:
        wire = observation().to_wire()
        malformed: list[contract.JsonObject] = []
        variants: tuple[tuple[str, contract.JsonValue], ...] = (("foreground_after", True), ("foreground_after", 12.0),
                           ("foreground_after_pid", 200.0), ("game_pid", True),
                           ("owned_auxiliary_pids", [OBS_PID, OBS_PID]),
                           ("classification", "UNCHANGED"), ("foreground_unchanged", True))
        for field, bad in variants:
            value = dict(wire)
            value[field] = bad
            malformed.append(value)
        missing = dict(wire)
        del missing["foreground_after_pid"]
        malformed.append(missing)
        extra = dict(wire)
        extra["alias"] = 1
        malformed.append(extra)
        for value in malformed:
            with self.subTest(value=value), self.assertRaises(ValueError):
                contract.parse_current_saved_launch_foreground_v1(value)


class _NativeFunction:
    def __init__(self, result: int) -> None:
        self.result = result
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self, *arguments: object) -> int:
        return self.result


class _Ole:
    def __init__(self) -> None:
        self.CoInitializeEx = _NativeFunction(0)
        self.CoUninitialize = _NativeFunction(0)


class _Generation:
    pid = GAME_PID
    creation_filetime = 134370617141148601  # Existing Python-only exact integer.

    def __enter__(self) -> _Generation:
        return self

    def __exit__(self, *arguments: object) -> None:
        return None

    def check(self) -> None:
        return None


class _ReceiptStream(io.StringIO):
    def __exit__(self, *arguments: object) -> None:
        return None


@dataclass
class _Arguments:
    launch_receipt: Path = Path("RAM-launch.json")
    ui_dependencies: Path = Path("RAM-dependencies")
    receipt: Path = Path("RAM-receipt.json")
    desktop_id: str = GAME_DESKTOP
    expected_current_desktop_id: str | None = USER_DESKTOP
    deadline_utc: str = "2099-01-01T00:00:00+00:00"
    wait_seconds: float = 30


class PlacementTests(unittest.TestCase):
    def run_placement(self, *, foreground_pid: int | None = 200,
                      current: str = USER_DESKTOP, switch_at: int = 0,
                      closed_old_user: bool = False) -> tuple[placement.PlacementReceipt, list[str]]:
        calls: list[str] = []
        samples = 0
        desktop = USER_DESKTOP
        stream = _ReceiptStream()
        gui = ModuleType("win32gui")
        constants = ModuleType("win32con")
        api = ModuleType("win32api")
        bridge = ModuleType("xar_autoplayer.bridge.windows_virtual_desktop")

        def sample() -> tuple[int, int | None]:
            nonlocal samples
            samples += 1
            return (11 if samples == 1 else 12), (200 if samples == 1 else foreground_pid)

        def inventory() -> tuple[list[str], str]:
            active = current if samples >= switch_at and switch_at else USER_DESKTOP
            return [GAME_DESKTOP, USER_DESKTOP, OTHER_DESKTOP], active

        def desktop_read(hwnd: int) -> dict[str, object]:
            return {"window_hwnd": hwnd, "on_current_virtual_desktop": desktop == USER_DESKTOP,
                    "desktop_id": desktop, "dwm_cloaked_flags": 2 if desktop == GAME_DESKTOP else 0}

        class Desktop:
            def __init__(self, number: int) -> None:
                self.id = (GAME_DESKTOP, USER_DESKTOP, OTHER_DESKTOP)[number - 1]

        class AppView:
            def __init__(self, *, hwnd: int) -> None:
                self.hwnd = hwnd

            def move(self, target: Desktop) -> None:
                nonlocal desktop
                calls.append("move")
                desktop = target.id

        vda = ModuleType("pyvda")
        setattr(vda, "get_virtual_desktops", lambda: [Desktop(1), Desktop(2), Desktop(3)])
        setattr(vda, "VirtualDesktop", Desktop)
        setattr(vda, "AppView", AppView)
        setattr(bridge, "window_virtual_desktop", desktop_read)
        setattr(gui, "GetClassName", lambda hwnd: "SDL_app")
        setattr(gui, "ShowWindow", lambda *args: calls.append("show-noactivate"))
        setattr(gui, "SetWindowLong", lambda *args: calls.append("style"))
        setattr(gui, "SetWindowPos", lambda *args: calls.append("position-noactivate"))
        setattr(gui, "GetWindowLong", lambda hwnd, flag: 8 if flag == -20 else 0)
        setattr(gui, "GetClientRect", lambda hwnd: (0, 0, 2560, 1440))
        setattr(gui, "GetWindowRect", lambda hwnd: (0, 0, 2560, 1440))
        setattr(gui, "IsIconic", lambda hwnd: False)
        setattr(gui, "IsWindow", lambda hwnd: not (closed_old_user and hwnd == 11))
        for name, value in {"SW_SHOWNOACTIVATE": 4, "GWL_STYLE": -16, "GWL_EXSTYLE": -20,
                            "WS_CAPTION": 1, "WS_THICKFRAME": 2, "WS_MINIMIZE": 4,
                            "WS_MAXIMIZE": 8, "WS_POPUP": 16, "HWND_TOPMOST": -1,
                            "SWP_NOACTIVATE": 16, "SWP_FRAMECHANGED": 32,
                            "SWP_SHOWWINDOW": 64, "WS_EX_TOPMOST": 8}.items():
            setattr(constants, name, value)
        setattr(api, "MonitorFromWindow", lambda *args: 1)
        setattr(api, "GetMonitorInfo", lambda *args: {"Monitor": (0, 0, 2560, 1440)})
        source: placement.SourcePin = {"path": "RAM-source", "sha256": "0" * 64}
        receipt: placement.PlacementReceipt = {
            "schema": "xar.g2.managed-desktop1-placement/v1", "status": "RED", "machine_id": "software-fixture",
            "at_utc": "2026-10-21T00:00:00+00:00", "source": {
                "producer": source, "machine_identity_provider": source, "foreground_contract": source,
                "machine_identity_api": "ck3_live_run_id.current_machine_id"},
            "launch_receipt": "RAM-launch.json", "gameplay_input_sent": False, "desktop_switches": 0,
            "process_launch_or_stop_calls": 0, "runtime_rendering_qualified": False}
        with ExitStack() as stack:
            stack.enter_context(patch.dict("sys.modules", {"win32api": api, "win32con": constants,
                "win32gui": gui, "xar_autoplayer.bridge.windows_virtual_desktop": bridge}))
            for patch_name, replacement in {
                "_new_receipt": lambda path: receipt,
                "read_foreground_window_v1": sample,
                "desktop_inventory": inventory,
                "game_generation": lambda launch: _Generation(),
                "wait_game_window": lambda *args: 99,
                "check_game_window": lambda *args: None,
                "deadline_check": lambda *args: None,
                "explicit_pyvda": lambda root: (vda, {"root": "RAM", "versions": {}, "module_origins": {}, "entry_sha256": {}}),
            }.items():
                stack.enter_context(patch.object(placement, patch_name, replacement))
            stack.enter_context(patch.object(ctypes, "WinDLL", lambda *args, **kwargs: _Ole()))
            stack.enter_context(patch.object(Path, "read_text", lambda *args, **kwargs: json.dumps({
                "command": ["ck3.exe"], "pid": GAME_PID, "creation_date": "20261021130837.000000+000"})))
            stack.enter_context(patch.object(Path, "open", lambda *args, **kwargs: stream))
            try:
                placement.place(_Arguments())
            except RuntimeError:
                pass
        decoded: object = json.loads(stream.getvalue())
        self.assertEqual(decoded, receipt)
        return receipt, calls

    def test_real_place_allows_user_switch_and_closed_old_window(self) -> None:
        receipt, calls = self.run_placement(closed_old_user=True)
        self.assertEqual(receipt["status"], "GREEN")
        self.assertEqual(receipt["client_rect"], [0, 0, 2560, 1440])
        self.assertFalse(receipt["foreground_unchanged"])
        observed = contract.parse_current_saved_launch_foreground_v1(receipt["foreground_observation"])
        self.assertTrue(observed.permitted)
        self.assertEqual(receipt["foreground_after"], observed.foreground_after)
        self.assertEqual(receipt["current_desktop_after"], observed.desktop_after)
        self.assertEqual(receipt["creation_filetime"], 134370617141148601)
        self.assertEqual(calls, ["move", "show-noactivate", "style", "position-noactivate"])

    def test_real_place_rejects_game_unknown_before_move(self) -> None:
        for pid in (GAME_PID, None):
            with self.subTest(pid=pid):
                receipt, calls = self.run_placement(foreground_pid=pid)
                self.assertEqual(receipt["status"], "RED")
                self.assertEqual(calls, [])

    def test_real_place_rejects_mid_pipeline_desktop_switch(self) -> None:
        receipt, calls = self.run_placement(current=OTHER_DESKTOP, switch_at=3)
        self.assertEqual(receipt["status"], "RED")
        self.assertLess(len(calls), 4)


class RenderedConsumerTests(unittest.TestCase):
    def actor_namespace(self) -> dict[str, object]:
        # Actual helper text inserted by the renderer, not a handwritten policy mirror.
        source = renderer._NAMESPACE.replace("__CONTRACT_SHA__", renderer.CONTRACT_SHA256)
        namespace: dict[str, object] = {"__name__": "software_actor", "N": Path(__file__).resolve().parents[2],
                                       "Path": Path, "sys": __import__("sys")}
        exec(compile(source, "<actual-rendered-actor-helpers>", "exec"), namespace)
        return namespace

    def test_actor_receipt_consumer_accepts_real_false_fact(self) -> None:
        namespace = self.actor_namespace()
        value = observation()
        receipt: contract.JsonObject = {"foreground_before": 11, "foreground_after": 12,
            "foreground_unchanged": False, "foreground_observation": value.to_wire(),
            "current_desktop_id": USER_DESKTOP, "current_desktop_after": USER_DESKTOP}
        invoke = namespace["_placement_foreground_permitted_v1"]
        self.assertTrue(callable(invoke))
        # exec a call to the original compiled function; no unchecked type cast.
        namespace.update(receipt=receipt, game_pid=GAME_PID)
        exec("result=_placement_foreground_permitted_v1(receipt,game_pid)", namespace)
        self.assertIs(namespace["result"], True)
        receipt["foreground_unchanged"] = True
        with self.assertRaises(ValueError):
            exec("result=_placement_foreground_permitted_v1(receipt,game_pid)", namespace)

    def test_actor_rejects_unknown_and_forged_auxiliary(self) -> None:
        namespace = self.actor_namespace()
        for value in (observation(pid=None), observation(auxiliary=[OBS_PID])):
            receipt: contract.JsonObject = {"foreground_before": 11, "foreground_after": 12,
                "foreground_unchanged": False, "foreground_observation": value.to_wire(),
                "current_desktop_id": USER_DESKTOP, "current_desktop_after": USER_DESKTOP}
            namespace.update(receipt=receipt, game_pid=GAME_PID)
            if value.owned_auxiliary_pids:
                with self.assertRaises(ValueError):
                    exec("result=_placement_foreground_permitted_v1(receipt,game_pid)", namespace)
            else:
                exec("result=_placement_foreground_permitted_v1(receipt,game_pid)", namespace)
                self.assertIs(namespace["result"], False)

    def test_renderer_rejects_wrong_preimage_and_wire_types(self) -> None:
        for raw in (b"foreign", b""):
            with self.assertRaises(ValueError):
                renderer.render_current_saved_background_display_v1(actor=b"", obs_desktop=b"",
                    capture_worker=raw, placement_sha256="0" * 64)
        with self.assertRaises(ValueError):
            renderer.render_current_saved_background_display_v1(actor=b"", obs_desktop=b"",
                capture_worker=b"", placement_sha256="g" * 64)

    def test_actual_capture_observer_classifies_owned_unknown_and_race(self) -> None:
        from types import SimpleNamespace
        import sys
        pin = hashlib.sha256(Path(placement.__file__).read_bytes()).hexdigest()
        source = renderer._GENERATION_HELPERS.replace("__CONTRACT_SHA__", renderer.CONTRACT_SHA256).replace("__PLACEMENT_SHA__", pin)
        source += "\n" + renderer._CAPTURE_FOREGROUND.replace("__CONTRACT_SHA__", renderer.CONTRACT_SHA256)
        calls: list[str] = []
        after = 12
        pid: int | None = 200
        drift = False
        sampling = 0

        def foreground() -> int:
            nonlocal sampling
            calls.append("foreground")
            sampling += 1
            return after + (1 if drift and sampling % 2 == 0 else 0)

        def process(hwnd: int) -> tuple[int, int | None]:
            return 1, pid

        gui = SimpleNamespace(GetForegroundWindow=foreground)
        processes = SimpleNamespace(GetWindowThreadProcessId=process)

        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        namespace: dict[str, object] = {"__file__": str(Path(__file__).resolve().parents[2] / "presentation-c23/capture.py"),
            "Path": Path, "sys": sys, "importlib": __import__("importlib"), "_sha": sha}
        exec(compile("from __future__ import annotations\n" + source, "<actual-rendered-capture-functions>", "exec"), namespace)
        with patch.dict(sys.modules, {"win32gui": gui, "win32process": processes}), patch.object(
                placement, "desktop_inventory", lambda: ([GAME_DESKTOP, USER_DESKTOP], USER_DESKTOP)):
            for after_value, pid_value, expected in ((12, 200, True), (11, 200, True),
                    (11, GAME_PID, False), (12, GAME_PID, False), (11, OBS_PID, False),
                    (12, OBS_PID, False), (11, None, False), (12, None, False)):
                after, pid = after_value, pid_value
                exec("result=_foreground_observation(11,'" + USER_DESKTOP + "',700,800).permitted", namespace)
                self.assertIs(namespace["result"], expected)
            drift = True
            sampling = 0
            after, pid = 12, 200
            exec("result=_foreground_observation(11,'" + USER_DESKTOP + "',700,800).permitted", namespace)
            self.assertIs(namespace["result"], False)
            calls.clear()
            namespace["_sha"] = lambda path: "0" * 64
            with self.assertRaises(RuntimeError):
                exec("_foreground_observation(11,'" + USER_DESKTOP + "',700,800)", namespace)
            self.assertEqual(calls, [])

    def test_actual_capture_write_envelope_machine_time_and_nested_roundtrip(self) -> None:
        import sys
        from datetime import datetime, timezone
        from typing import TypedDict
        pin = hashlib.sha256(Path(placement.__file__).read_bytes()).hexdigest()
        generation = renderer._GENERATION_HELPERS.replace("__CONTRACT_SHA__", renderer.CONTRACT_SHA256).replace("__PLACEMENT_SHA__", pin)
        namespace: dict[str, object] = {
            "__file__": str(Path(__file__).resolve().parents[2] / "presentation-c23/capture.py"),
            "Path": Path, "sys": sys, "importlib": __import__("importlib"),
            "TypedDict": TypedDict, "datetime": datetime, "timezone": timezone,
            "root": Path("RAM-capture"), "foreground_observation": observation()}
        def sha(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        namespace["_sha"] = sha
        exec(compile("from __future__ import annotations\n" + generation + "\n" + renderer._CAPTURE_RECEIPT,
                     "<actual-rendered-capture-receipt>", "exec"), namespace)
        stream = _ReceiptStream()
        class OutputPath:
            def __init__(self, path: object) -> None:
                if path != Path("RAM-capture/foreground-observation.json"):
                    raise AssertionError("Unexpected diagnostic output")
            def open(self, mode: str, *, encoding: str) -> _ReceiptStream:
                if mode != "x" or encoding != "utf-8":
                    raise AssertionError("Original create-only writer contract differs")
                return stream
        writer: dict[str, object] = {"Path": OutputPath, "json": json}
        original_writer = 'def _write_new(path, value):\n    with Path(path).open("x", encoding="utf-8") as stream:\n        json.dump(value, stream, ensure_ascii=False, indent=2)\n'
        exec(compile(original_writer, "<original-capture-json-writer>", "exec"), writer)
        namespace["_write_new"] = writer["_write_new"]
        before = datetime.now(timezone.utc)
        with patch("ck3_live_run_id.current_machine_id", return_value="software-fixture") as identity:
            exec(compile(renderer._CAPTURE_FOREGROUND_WRITE.strip(), "<actual-rendered-foreground-write>", "exec"), namespace)
            identity.assert_called_once()
        after = datetime.now(timezone.utc)
        wire: object = json.loads(stream.getvalue())
        namespace.update(wire=wire, expected_machine_id="software-fixture")
        exec("parsed=_parse_capture_foreground_receipt_v1(wire,expected_machine_id=expected_machine_id)", namespace)
        parsed = namespace["parsed"]
        self.assertIsInstance(parsed, dict)
        if not isinstance(parsed, dict):
            raise AssertionError("Typed parsed envelope required")
        self.assertEqual(set(parsed), {"schema", "machine_id", "observed_at_utc", "foreground_observation"})
        self.assertEqual(parsed["machine_id"], "software-fixture")
        stamp: object = parsed["observed_at_utc"]
        if not isinstance(stamp, str):
            raise AssertionError("Actual UTC text required")
        self.assertLessEqual(before, datetime.fromisoformat(stamp))
        self.assertLessEqual(datetime.fromisoformat(stamp), after)
        nested = contract.parse_current_saved_launch_foreground_v1(parsed["foreground_observation"])
        self.assertEqual(nested, observation())
        self.assertEqual(json.loads(json.dumps(parsed)), wire)
        bad: list[object] = [observation().to_wire()]
        for key in ("machine_id", "observed_at_utc"):
            value = dict(parsed)
            del value[key]
            bad.append(value)
        for key, replacement in (("machine_id", "foreign-machine"), ("observed_at_utc", True),
                                 ("observed_at_utc", "2026-10-21T00:00:00"),
                                 ("observed_at_utc", "2026-10-21T00:00:00+01:00")):
            value = dict(parsed)
            value[key] = replacement
            bad.append(value)
        for invalid_wire in bad:
            namespace["wire"] = invalid_wire
            with self.assertRaises(ValueError):
                exec("_parse_capture_foreground_receipt_v1(wire,expected_machine_id=expected_machine_id)", namespace)


@dataclass
class _ObsGeneration:
    pid: int
    old: bool = False
    creation_filetime: int = 123
    executable: Path = Path("fake.exe")

    def check(self) -> None:
        if self.old:
            raise AssertionError("Closed historical user must not be rechecked")


@dataclass
class _ObsProcess:
    pid: int


@dataclass
class _ObsEngine:
    process: _ObsProcess
    generation: _ObsGeneration
    before_foreground: dict[str, object]
    before_foreground_generation: _ObsGeneration


class _ObsGui:
    def __init__(self, foreground: int, release: int = 13) -> None:
        self.foreground = foreground
        self.release = release
        self.visible = False
        self.iconic = False
        self.calls: list[tuple[int, int]] = []

    def GetForegroundWindow(self) -> int:
        return self.foreground

    def IsWindow(self, hwnd: int) -> bool:
        return hwnd in (13, 14, 22, 33, 44)

    def GetParent(self, hwnd: int) -> int:
        return 0

    def GetClassName(self, hwnd: int) -> str:
        return "QtMain" if hwnd == 22 else "UserClass"

    def GetWindowText(self, hwnd: int) -> str:
        return "OBS Mock" if hwnd == 22 else "User mock"

    def IsWindowVisible(self, hwnd: int) -> bool:
        return self.visible

    def IsIconic(self, hwnd: int) -> bool:
        return self.iconic

    def EnumWindows(self, callback: Callable[[int, object], bool], extra: object) -> None:
        for hwnd in (13, 14, 22, 33, 44):
            callback(hwnd, extra)

    def ShowWindow(self, hwnd: int, command: int) -> bool:
        if hwnd != 22 or command not in (6, 7):
            raise AssertionError("Only retained OBS SW6/SW7 is allowed")
        self.calls.append((hwnd, command))
        self.visible = self.iconic = True
        if self.foreground == 22:
            self.foreground = self.release
        return False


class _ObsProcesses:
    def GetWindowThreadProcessId(self, hwnd: int) -> tuple[int, int]:
        return 7, {13: 103, 14: 104, 22: 200, 33: 300, 44: 200}.get(hwnd, 0)


class ObsConsumerTests(unittest.TestCase):
    def run_case(self, foreground: int, *, release: int = 13,
                 current: str = USER_DESKTOP, target_exists: bool = True) -> tuple[str, list[tuple[int, int]], dict[str, object]]:
        import time
        gui = _ObsGui(foreground, release)
        context: dict[str, object] = {"captured_before_obs_launch": True, "pid": 101,
            "creation_filetime": 123, "executable": "fake.exe", "hwnd": 11,
            "window_class": "closed", "desktop_ids": [USER_DESKTOP, GAME_DESKTOP],
            "current_desktop_id": USER_DESKTOP}
        engine = _ObsEngine(_ObsProcess(200), _ObsGeneration(200), context, _ObsGeneration(101, old=True))
        job: dict[str, object] = {"pid": 300, "hwnd": 33, "desktop_id": GAME_DESKTOP}
        record: dict[str, object] = {"obs_pid": 200, "sys_tray_minimize_to_tray": False}
        readings = 0
        clock = 0.0

        def inventory() -> tuple[list[str], str]:
            nonlocal readings
            readings += 1
            return ([USER_DESKTOP] + ([GAME_DESKTOP] if target_exists else [])
                    + ([OTHER_DESKTOP] if readings % 2 else []), current)

        def desktop_read(hwnd: int) -> dict[str, object]:
            if hwnd == 33:
                return {"desktop_id": GAME_DESKTOP}
            if not gui.iconic:
                raise OSError("GetWindowDesktopId HRESULT -0x7ffd7fd5")
            return {"desktop_id": USER_DESKTOP}

        def monotonic() -> float:
            return clock

        def sleep(seconds: float) -> None:
            nonlocal clock
            clock += seconds

        old = zlib.decompress(base64.b64decode(_OBS_CORE_PREIMAGE)).decode("utf-8")
        for before, after in renderer._OBS_REPLACEMENTS:
            if before in old:
                old = renderer._replace(old, before, after, 2 if before == "    owned();prior_identity()" else 1)
        helpers = selected(renderer._OBS_HELPERS, {"_sample_obs_foreground_v1", "_observe_obs_foreground_v1"})
        shell = "def _shell_mapping_missing(error: object) -> bool:\n    return '0x7ffd7fd5' in str(error)\n"
        namespace: dict[str, object] = {"time": time, "uuid": __import__("uuid"),
            "classify_current_saved_launch_foreground_v1": contract.classify_current_saved_launch_foreground_v1,
            "engine": engine, "job": job, "record": record, "gui": gui, "processes": _ObsProcesses(),
            "inventory": inventory, "desktop_read": desktop_read, "monotonic": monotonic, "sleep": sleep}
        exec(compile("from __future__ import annotations\n" + helpers + "\n" + shell + old,
                     "<actual-rendered-obs-place-core>", "exec"), namespace)
        outcome = "PASS"
        try:
            exec("place_core(engine,job,record,gui=gui,processes=processes,desktop_inventory=inventory,desktop_read=desktop_read,monotonic=monotonic,sleep=sleep)", namespace)
        except (ValueError, TimeoutError) as error:
            outcome = type(error).__name__
        return outcome, gui.calls, record

    def test_actual_obs_core_allows_changed_user_and_exact_transient_obs(self) -> None:
        for foreground, release, command in ((13, 13, 7), (22, 13, 6), (22, 14, 6)):
            with self.subTest(foreground=foreground, release=release):
                status, calls, record = self.run_case(foreground, release=release)
                self.assertEqual(status, "PASS")
                self.assertEqual(calls, [(22, command)])
                wire: object = json.loads(json.dumps(record["foreground_observation"]))
                value = contract.parse_current_saved_launch_foreground_v1(wire)
                self.assertTrue(value.permitted)
                self.assertFalse(value.foreground_unchanged)
                self.assertEqual(value.owned_auxiliary_pids, (200,))

    def test_actual_obs_core_denies_owned_unknown_and_desktop_change(self) -> None:
        for foreground in (33, 44, 0):
            with self.subTest(foreground=foreground):
                status, calls, _ = self.run_case(foreground)
                self.assertEqual(status, "ValueError")
                self.assertEqual(calls, [])
        for kwargs in ({"current": OTHER_DESKTOP}, {"target_exists": False}):
            # Distinct calls keep the typed optional fields explicit.
            if "current" in kwargs:
                status, calls, _ = self.run_case(13, current=OTHER_DESKTOP)
            else:
                status, calls, _ = self.run_case(13, target_exists=False)
            self.assertEqual(status, "ValueError")
            self.assertEqual(calls, [])

    def test_actual_obs_core_retains_finite_owned_minimize_timeout(self) -> None:
        status, calls, _ = self.run_case(22, release=22)
        self.assertEqual(status, "TimeoutError")
        self.assertEqual(calls, [(22, 6)])


# Exact original OBS place_core software fixture, source SHA 74c9f4ce...
_OBS_CORE_PREIMAGE = 'eNqtWW1z27gR/n6/Ap5+INVjdE4+5GasYWeutZNqrrHT2ElmzuPhUCRkoeFbANCK27n/3l1gQYIvkp1r/UGWQGCxeHb32V0w51vWFGnGk6yWPOTVvah4xP5VbyImOYzlEftzxO5bEbFG1hlXiquI5Vx90XWTiOqBV7qWj/2Q5Gke/cCGf2Vd1bquRBZrUfJl9zNiquC8saPm6+LMrLV7L9smTzUPlU7veRxIrlNQL09IkyBSu3qf7EWVw78sLQoVny7M+ntecZlqUVexPdOyH1n1X5fZjmdfQrtGbL1ly0bkJ24t7YdjrJaTWVbZ26DeqAQGgruz7vwyFYqzT2nR8gspaxkGV1KAzLRg7jTs6q/XDluWi+2WSxVYjbK60vybdmps+BaMlODHvazbKl81UtTy4OOkV9QdMCSRAIcOgyxtdCsBUFqKByjStsp2wYIJxcBK7Ea2HA9ttrLnJRm3gTnswNbdxAz8ADdOtqLgaF5v2eRZcIcLlZahXcy/8azV6abgC29ZP3poU9AnjofWWZwdMUEj+Qt7Xtaj5pkXMSiFUqK6x02GxnFWT7XmZaOTCfzBndPdzM8x1FDNROQQNEI/hoveUQg1zx2dxdAIEH/LtfpsHD3sANntcZOFPT/F5vIt13bezQ5D8b19sM4ny25f3p3EHW7jiDV+DruCuL8VqVKXacknIjzjuCDEufDkbCBvaoKLb2mmffxbxaVvhL9/vjz/ybNEtkure54T9mMczaBVQcW3dx3eWV0UPNMh6hslnlYI7DMww3UI1NirWIp+YuF5n0pQw06N49MJkN7UHkkzewm8JrXaC70Lg39qiDlvLikE4M5MRsoIFiOU6fzLtGl4Rbr3RMQh0isTzZYgYZeLqi3tNiokpKLLuuIdHRa8Ckkq2Prl2SE71nvHYyVQmrGdo4+2El9bTmZDlWISeHt6tzLeUgEe8TxAK7Bu0T0cI3I4URh9KC8EkdnVeIDvpHG3uRu2m5nPPoE9CCWAcSi6401dF6EfjZ/sc6vRIhIZprWZ2WvzgKYtOgc1mvo8cCA3HSQDI/CZDOC8+WTkzUdi33fuk/h0lhXoYYenN2lsshML75P08MHPjdadKNZHRED4dfn7kGVmXPdmBy4KGY/LB9hI8iYVkm1kimwk+ddWSK6Y3nHGjY/vRA4q9E5O3jXMBcb/gPeDSYEUWBVzFWWtREzjyZQQ/D2VkJhjzIRtK/Llx4/r8xCKsdteIPJud97QEwjg9gTdTwc2jvrMa6cmA2nHqpWPSMs02+U/tpV1CcgAfJT7fCK3iBrfCjo97bkMIQB0oBT6CB02JqVmTPQWvYnWlq3SbMOBIsEgQmnMyZDEMy0eOFikAuBzp2lwhBvuQWbiF6tBNEaFopeGI6uAh1lsR6jSRPry5Vl7UYZcOc/wtwUHwZ+d08L3oYFPaIcZSH7JdAuVi0HGuqBjWkiS6K3oulxpAOM7QMHCzzr4CBqvmKT6phSVKMW/O1Z+080gRiLvLEG8FGkBU/P4TVoovqJSin4RyphwzAItH3tPpIcDXHvS598yDl53dW1AYaliHL94jkyoz5wpMVPBBP8J9GPDgzP8DM3gYpkkSGBJEgUlUCbG8hnGon36u8/EiHiidrwokhISLhwroePRbGu7bok7e5eAndP1CB9G1HnKdI0LKVvhjOuzo5FdfamAPf2aSwP5KWFaJJBLWd3ZGyO2rCHWGi5LAXGf9+Ht1cgzxzK5d1B6kQ+aHkQ9qgQ2fuwcK9G1GehbEOMvT1eUTSEyodkWZ7PrR3UDQt6R0Jsafzlez8m/mO1EQHOMHJu72TUaFfI+d+Q+zjN/INdcdQXSPsUzsaKGJCZdUiFtUAmIhh7hDvxgsPNM5gDu91PB2RNMTkn0uzaerbn/kCf/z9487wH9buPzDT3ZODcmDmDMsTPj35/Y9efX4CoFTxWVAGmB1PH4wgryFH4QKaMSmv0G/p9zuYLlP3vCsMqoikfscHK233FL07XrQceND20F+2OZoWz1sezBrkvg9Tx+PY+gDTbGMQR+HtHhbJHcRR3IID4D8X4XO3PJ8nI4RirRfx/ID7breEArsZIDvVg3smW1KMCRlmytuxTWuHZPtZm5cZkwur8xVB0Pom5VQkU6kHpXcV/DPK9Ejpxyi4lEL8WlW8hZHSSYpp/040nlt0+FTqgNGOaHtE+iHrydpBzMXkDRG3e3Y+Hix1fL0xVU9huuvM5yvxMFN63cMCSIpFbjSCUJP8YvB9P/r0xidZqlUcN52JICCF6Yed3VU23Vyso82E8NZHr2hAT3DBPORMjAboS//Re5hnDoKzENuwZw9NSOTq5FfV0NgAl6D5YJw0MsxnYbPu5o8zR6BnHOk6cjMcXxGoDjDUcN1vSpadWTlm2JPNaCAO5yK15i7AUYH9XaYEWqwLUGFEvHINDMCgvRVNVBWej/HS8R/b9puUjeOC/YhTT0s3oUwrO1Iwk7WD2657/P7na8lnRrR9Vkd7JJYXTQSeJ45Bbz6yalO9LMagPofhlbz+Opv8SOvYgvbkTJ61ZPyh8iBzqmMTwfXwV6bpULWxNswBfB4EDi3DWY6Dd4GQZ+/wq8FuTmauRh5oVCuDx9daTzUX47WNUJlrjJAxx/KzLbxEajttD+62N5xPUedP6PCE6MZGg3GLyrOETb5qEhkhknX7mbC2zxo+7HkcsFu5eb+OxibYiak2vVMp+T9tk+G6vUAzZOuPGMUkOaffLabWyMyapBukC4/HbezB524NHgmgDmTJv0/hLmqCnGCRWbpJkNT7prkGPvjro4coFhq0TX+w+LymHfD4rO4HxymBUOXva6TYb0j9pAENsdTIlted/Wc3RR5DeN/VWmb5yjzRNt4+IKimqXYUf3gfOx9KyCx7u9nEbEd8H1ZjZV/kQbvXAVlHdhNvuGaURY3YmJpeCLs8jg1V+byjxxVVcfICBFtyoOrj5fXpwnAGrybn25frf+DX99WL9dX/7yj+T84vrXm6v3yaeLD+s364vzngPx/UO2c/zVi+XUfSemaHAFurmds6/6JivoNUBSAZq+4rYAwSXdTVY8uC+Ydh7BIo5f95LR+d0Mqj267TGMmyJ9BAdoWt0Nbw18h3F0tY3Jhh6YSBJ4FWeA7EmaJpt7iyg1N3ZJJmvVs45ZRK9fk6/w3FjSrnDGN62TPfoP/wVgq8c0'

if __name__ == "__main__":
    unittest.main()
