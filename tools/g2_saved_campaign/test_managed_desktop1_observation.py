"""New source191 software branches only; all process/window boundaries are doubles."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).parent
REPOSITORY = Path(os.environ.get("VIDEO_SOURCE191_REPO", str(Path(__file__).resolve().parents[2])))
CANDIDATE = Path(os.environ.get("VIDEO_SOURCE191_ROOT", str(ROOT / "candidate" if (ROOT / "candidate").is_dir() else REPOSITORY)))
sys.path.insert(0, str(REPOSITORY))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

placement = load("managed_desktop1_placement", CANDIDATE / "tools/g2_saved_campaign/managed_desktop1_placement.py")
capture = load("capture_source191", CANDIDATE / "tools/ck3_obs_capture.py")
PID = 71464
BIRTH = 134378397668266369
DESKTOP = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
HWND = 319967214

class StopBeforeProcess(RuntimeError):
    pass

class Source191Tests(unittest.TestCase):
    def setUp(self):
        temporary_root = Path(os.environ.get("VIDEO_SOURCE191_TMP", tempfile.gettempdir()))
        temporary_root.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=temporary_root)
        self.root = Path(self.temporary.name)
        # Literal ordinary producer fields: no runtime owner, Game or private data root needed.
        image = str(self.root / "ck3.exe")
        self.owner = {"schema": "xar.java-game-supervisor-owner/v1", "machine_id": "fixture-machine",
            "session_id": "fixture-session", "game": {"pid": PID, "creation_filetime": str(BIRTH), "executable": image},
            "supervisor": {"pid": 305760, "creation_filetime": "134378397644711323", "executable": str(self.root / "java.exe")},
            "configuration": {"schema": "xar.java-game-launch-plan/v4", "request_id": "fixture-request",
                "session_id": "fixture-session", "deadline": "2026-10-30T13:31:03.956251Z",
                "review": {"machine_id": "fixture-machine", "game_executable": {"path": image}}},
            "native_hello": {"path": str(self.root / "native-hello.packet"), "bytes": 1, "sha256": "0" * 64},
            "launch_evidence": {}, "stop_request_path": str(self.root / "stop-request.json"),
            "terminal_path": str(self.root / "terminal.json")}
        self.hello = {"schema": "xar.java-game-lifecycle-event/v1", "machine_id": "fixture-machine",
            "session_id": "fixture-session", "request_id": "fixture-request", "event": "HELLO",
            "observed_at_utc": "2026-10-30T13:16:07.792626400Z",
            "game": {"pid": PID, "creation_filetime_decimal": str(BIRTH), "executable": image},
            "accounting": {}, "terminal": None, "terminal_kind": None, "detail": "Literal software HELLO specimen"}
        self.evidence = self.root / "events"
        self.evidence.mkdir()
        self.event = self.evidence / "event-000005.json"
        self.owner["configuration"]["evidence_root"] = str(self.evidence)
        self.owner["stop_request_path"] = str(self.root / "stop-request.json")
        self.owner["terminal_path"] = str(self.root / "terminal.json")
        self.owner_path = self.root / "owner.json"
        self.publish_hello()
        self.owner_path.write_text(json.dumps(self.owner), encoding="utf-8")
        self.arguments = SimpleNamespace(launch_receipt=self.owner_path, receipt=self.root / "observation.json",
            desktop_id=DESKTOP, expected_current_desktop_id=DESKTOP,
            deadline_utc=(datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(), wait_seconds=1,
            ui_dependencies=None)

    def tearDown(self):
        self.temporary.cleanup()

    def publish_hello(self):
        raw = json.dumps(self.hello, separators=(",", ":")).encode()
        self.event.write_bytes(raw)
        self.owner["launch_evidence"] = {"path": str(self.event), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}

    def test_java_actual_shape_and_exact_filetime_generation(self):
        expected = {"pid": PID, "executable": self.owner["game"]["executable"], "creation_filetime": BIRTH}
        self.assertEqual(placement.parse_launch_receipt(self.owner), expected)
        with patch.object(placement, "ProcessGeneration", return_value=object()) as process:
            placement.game_generation(self.owner)
        self.assertEqual(process.call_args.args[0], PID)
        self.assertEqual(Path(process.call_args.args[1]), Path(expected["executable"]))
        self.assertEqual(process.call_args.kwargs, {"creation_filetime": BIRTH})
        self.assertNotIn("creation_date", expected)

    def test_legacy_generation_branch_remains_legacy(self):
        legacy = {"schema": "legacy-extra-field-was-ignored", "pid": 55,
            "command": [str(self.root / "ck3.exe"), "-legacy"], "creation_date": "20261030131606.826636+000"}
        self.assertEqual(placement.parse_launch_receipt(legacy), {key: legacy[key] for key in ("command", "creation_date", "pid")})
        with patch.object(placement, "ProcessGeneration", return_value=object()) as process:
            placement.game_generation(legacy)
        self.assertEqual(process.call_args.kwargs, {"creation_date": legacy["creation_date"]})

    def test_owner_identity_and_schema_negatives(self):
        mutations = (
            lambda row: row.update(schema="wrong-owner-schema"),
            lambda row: row["game"].update(pid=PID + 1),
            lambda row: row["game"].update(creation_filetime=str(BIRTH + 1)),
            lambda row: row["game"].update(creation_filetime=BIRTH),
            lambda row: row["game"].update(creation_filetime="0" + str(BIRTH)),
            lambda row: row["game"].update(creation_filetime=str(1 << 64)),
            lambda row: row["game"].update(pid=True),
            lambda row: row["configuration"]["review"].update(machine_id="another-machine"),
            lambda row: row["configuration"]["review"]["game_executable"].update(path=str(self.root / "other-ck3.exe")),
        )
        for mutate in mutations:
            row = deepcopy(self.owner)
            mutate(row)
            with self.subTest(mutation=repr(mutate)), self.assertRaises((ValueError, RuntimeError)):
                placement.parse_launch_receipt(row)

    def test_hello_pin_schema_and_identity_negatives(self):
        original = deepcopy(self.hello)
        for key, value in (("schema", "wrong-event-schema"), ("event", "RUNNING"),
                ("machine_id", "other-machine"), ("session_id", "other-session"),
                ("request_id", "other-request"), ("terminal", {"not": "null"})):
            self.hello = deepcopy(original)
            self.hello[key] = value
            self.publish_hello()
            with self.subTest(field=key), self.assertRaises((ValueError, RuntimeError)):
                placement.parse_launch_receipt(self.owner)
        self.hello = deepcopy(original)
        self.hello["game"]["creation_filetime_decimal"] = str(BIRTH + 1)
        self.publish_hello()
        with self.assertRaises((ValueError, RuntimeError)):
            placement.parse_launch_receipt(self.owner)
        self.hello = original
        self.publish_hello()
        self.owner["launch_evidence"]["sha256"] = "0" * 64
        with self.assertRaises((ValueError, RuntimeError)):
            placement.parse_launch_receipt(self.owner)

    def test_bounded_owner_document_and_bom_legacy(self):
        self.owner_path.write_bytes(b" " * (1048576 + 1))
        with self.assertRaises((ValueError, RuntimeError)):
            placement._read_launch_document(self.owner_path)
        self.owner_path.write_text(json.dumps({"pid": 1, "command": [str(self.root / "ck3.exe")],
            "creation_date": "20261030131606.826636+000"}), encoding="utf-8-sig")
        self.assertEqual(placement._read_launch_document(self.owner_path)["pid"], 1)

    def observation(self, *, window=(0, 0, 2560, 1392), client=(0, 0, 2560, 1392),
            origin=(0, 0), visible=True, minimized=False, window_pid=PID, frame_race=False,
            birth_mismatch=False, desktop=DESKTOP):
        # Fixed literal observations come from the new contract, not the candidate return.
        gui = ModuleType("win32gui")
        gui.IsWindow = lambda hwnd: hwnd == HWND
        gui.IsWindowVisible = Mock(return_value=visible)
        gui.GetWindowText = lambda hwnd: "Crusader Kings III"
        gui.GetClassName = lambda hwnd: "SDL_app"
        gui.GetWindowRect = Mock(side_effect=[window, (0, 0, 2559, 1392)] if frame_race else None,
                                 return_value=window)
        gui.GetClientRect = Mock(return_value=client)
        gui.ClientToScreen = Mock(side_effect=lambda hwnd, point: (point[0] + origin[0], point[1] + origin[1]))
        gui.GetWindowLong = lambda hwnd, index: 0x10  # topmost is false and legal.
        gui.IsIconic = Mock(return_value=minimized)
        gui.EnumWindows = lambda callback, extra: callback(HWND, extra)
        for forbidden in ("ShowWindow", "SetWindowPos", "SetWindowLong", "SetForegroundWindow"):
            setattr(gui, forbidden, Mock(side_effect=AssertionError("Mutation is forbidden: " + forbidden)))
        api = ModuleType("win32api")
        api.MonitorFromWindow = Mock(return_value=1)
        api.GetMonitorInfo = Mock(return_value={"Monitor": (0, 0, 2560, 1440), "Work": (0, 0, 2560, 1392)})
        con = ModuleType("win32con")
        con.GWL_EXSTYLE, con.WS_EX_TOPMOST = -20, 8
        con.MONITOR_DEFAULTTONEAREST, con.MONITOR_DEFAULTTONULL = 2, 0
        process = ModuleType("win32process")
        process.GetWindowThreadProcessId = lambda hwnd: (1, window_pid)
        desktop_module = ModuleType("xar_autoplayer.bridge.windows_virtual_desktop")
        desktop_module.window_virtual_desktop = Mock(return_value={"window_hwnd": HWND,
            "on_current_virtual_desktop": desktop == DESKTOP, "desktop_id": desktop, "dwm_cloaked_flags": 0})
        generation = SimpleNamespace(pid=PID, creation_filetime=BIRTH, executable=Path(self.owner["game"]["executable"]),
                                     check=Mock())
        context = Mock()
        context.__enter__ = Mock(return_value=generation)
        context.__exit__ = Mock(return_value=False)
        modules = {"win32gui": gui, "win32api": api, "win32con": con, "win32process": process,
                   "xar_autoplayer.bridge.windows_virtual_desktop": desktop_module}
        baseline = {"schema": "xar.g2.managed-desktop1-placement/v1", "status": "RED",
            "gameplay_input_sent": False, "desktop_switches": 0, "process_launch_or_stop_calls": 0}
        with patch.dict(sys.modules, modules), patch.object(placement, "_new_receipt", return_value=baseline), \
                patch.object(placement, "desktop_inventory", return_value=([DESKTOP, OTHER], DESKTOP)), \
                patch.object(placement, "read_foreground_window_v1", return_value=(HWND, PID)), \
                patch.object(placement, "ProcessGeneration", side_effect=RuntimeError("birth mismatch") if birth_mismatch else None,
                             return_value=context):
            return placement.observe_placement(self.arguments)

    def test_observe_screenfit_already_foreground_not_topmost_positive(self):
        row = self.observation()
        self.assertEqual(row["status"], "GREEN")
        self.assertEqual(row["window_rect"], [0, 0, 2560, 1392])
        self.assertEqual(row["client_screen_rect"], [0, 0, 2560, 1392])
        self.assertEqual(row["creation_filetime"], BIRTH)
        self.assertIs(row["observation_only"], True)
        self.assertEqual(row["window_mutations"], 0)
        self.assertIs(row["topmost"], False)

    def test_observe_offscreen_client_origin_hidden_and_race_fail_red(self):
        cases = [dict(window=(-1, 0, 2559, 1392)), dict(origin=(1, 0)), dict(client=(0, 0, 0, 1392)),
            dict(visible=False), dict(minimized=True), dict(frame_race=True), dict(desktop=OTHER),
            dict(window_pid=PID + 1), dict(birth_mismatch=True)]
        for index, parameters in enumerate(cases):
            self.arguments.receipt = self.root / ("negative-" + str(index) + ".json")
            with self.subTest(parameters=parameters), self.assertRaises((ValueError, RuntimeError, OSError)):
                self.observation(**parameters)
            self.assertEqual(json.loads(self.arguments.receipt.read_text(encoding="utf-8"))["status"], "RED")

    def test_capture_java_owner_raw_job_and_mutable_binding_before_spawn(self):
        output = self.root / "video"
        output.mkdir()
        obs = self.root / "private-obs"
        name = "ManagedWindowCapture-" + "1" * 32
        profile = {"schema": capture.SCHEMA, "strict_isolation": True, "host": "127.0.0.1", "port": 11917,
            "obs_root": str(obs), "executable": str(obs / "bin/64bit/obs64.exe"),
            "config_root": str(obs / "config/obs-studio"), "profile_name": name, "collection_name": name,
            "recording_root": str(output), "deadline_utc": self.arguments.deadline_utc,
            "max_output_bytes": 192 * 1024 * 1024}
        profile_path = self.root / "profile.json"
        profile_path.write_text(json.dumps(profile), encoding="utf-8")
        place_path = self.root / "placement.json"
        place_path.write_text(json.dumps({"status": "GREEN", "pid": PID, "hwnd": HWND,
            "creation_filetime": BIRTH, "target_desktop_id": DESKTOP}), encoding="utf-8")
        text = self.root / "current.txt"
        text.write_text("智能体实时决策\nfixture", encoding="utf-8")
        binding = self.root / "current.binding.json"
        probe = self.root / "ffprobe.exe"
        probe.write_bytes(b"fixture metadata only, never execute")
        publisher = {"schema": "xar.java-root-decision-text/v1", "binding_path": str(binding),
            "session": str(self.root), "session_id": "literal-session", "machine_id": "literal-machine",
            "game": {"pid": PID, "creation_filetime": BIRTH}, "publisher": {"pid": 123,
                "creation_filetime": 133000000000000000, "executable": str(self.root / "java.exe")},
            "decision_text_file": str(text), "publication": 1}
        with patch.object(capture, "require_no_retired_decision_window", return_value={}), \
                patch.object(capture, "read_java_decision_binding", return_value=publisher), \
                patch.object(capture.subprocess, "Popen", side_effect=StopBeforeProcess("No process is launched")):
            with self.assertRaises(StopBeforeProcess):
                capture.launch_recording(profile_path, output, PID, HWND, 15, launch_receipt=self.owner_path,
                    ffprobe=probe, placement_receipt=place_path, java_decision_binding=binding)
        jobs = list(output.glob("*/job.json"))
        self.assertEqual(len(jobs), 1)
        job = json.loads(jobs[0].read_text(encoding="utf-8"))
        self.assertEqual(job["launch"], self.owner)
        self.assertEqual(job["decision_text_publisher_receipt"], {"path": str(binding), "mutable_java_binding": True})
        self.assertNotIn("creation_date", job["launch"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
