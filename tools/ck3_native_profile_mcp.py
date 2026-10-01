#!/usr/bin/env python3
"""Attach the existing CK3 bridge to one frozen, offline, live-run profile."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid
from typing import Literal

import desktop_semantic_action_mcp as desktop

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ck3_autonomous_player/src"))
from xar_autoplayer.operator_mcp import _forbid_unknown_tool_arguments_v1


def _load_profile_common(path: Path, extra_fields: set[str]) -> dict:
    profile = desktop.exact_fields(json.loads(path.read_text(encoding="utf-8-sig")), {
        "schema_version", "guard_profile", "guard_profile_sha256", "userdir",
        "evidence_directory", "game_version",
    } | extra_fields, "native profile")
    if type(profile["schema_version"]) is not int or profile["schema_version"] != 1:
        raise ValueError("native profile schema_version must be 1")
    for name in ("guard_profile", "userdir", "evidence_directory"):
        if not isinstance(profile[name], str) or not Path(profile[name]).is_absolute():
            raise ValueError(f"{name} must be an absolute target-side path")
    digest = profile["guard_profile_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("guard profile requires SHA-256")
    guard_path = Path(profile["guard_profile"])
    if desktop.sha256(guard_path).lower() != digest.lower():
        raise ValueError("guard profile SHA-256 changed")
    profile["guard"] = desktop.load_profile(guard_path)
    if not isinstance(profile["game_version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", profile["game_version"]):
        raise ValueError("game_version must be exact")
    if not Path(profile["userdir"]).is_dir():
        raise ValueError("isolated userdir is missing")
    profile["profile_sha256"] = desktop.sha256(path)
    return profile


def load_clock_profile(path: Path) -> dict:
    return _load_profile_common(path, set())


def load_profile(path: Path) -> dict:
    profile = _load_profile_common(path, {"state_directory", "dll", "injector"})
    if not isinstance(profile["state_directory"], str) or not Path(profile["state_directory"]).is_absolute():
        raise ValueError("state_directory must be an absolute target-side path")
    for name, expected in (("dll", "xar_ck3_bridge.dll"), ("injector", "xar_ck3_bridge_injector.exe")):
        row = desktop.exact_fields(profile[name], {"path", "sha256"}, name)
        if not isinstance(row["path"], str) or not Path(row["path"]).is_absolute() or Path(row["path"]).name.lower() != expected:
            raise ValueError(f"{name} must identify the authoritative bridge artifact")
        if not isinstance(row["sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]):
            raise ValueError(f"{name} requires SHA-256")
    return profile


class NativeProfileBackend:
    def observe(self, profile: dict) -> dict:
        import psutil
        observed = desktop.NativeDesktopBackend().observe(profile["guard"])
        process = psutil.Process(profile["guard"]["target"]["pid"])
        observed["command_line"] = process.cmdline()
        return observed

    def poll(self, profile: dict) -> dict:
        guard = profile["guard"]
        command = [sys.executable, guard["task_bus_script"],
                   "--expected-cli-sha256", guard["task_bus_sha256"],
                   "poll", "--task", guard["screen_task_id"], "--ack"]
        result = subprocess.run(command, capture_output=True, encoding="utf-8",
                                errors="replace", timeout=20, check=True)
        return json.loads(result.stdout)

    def inject(self, command: list[str]):
        from xar_autoplayer.windows_injector_job import run_contained_injector_command
        return run_contained_injector_command(command, timeout_seconds=30)

    def read_clock(self, profile: dict) -> dict:
        from ck3_native_clock_reader import read_live_clock
        target = profile["guard"]["target"]
        return read_live_clock(target["pid"], target["executable"], target["executable_sha256"], profile["game_version"])


class NativeProfileService:
    """No caller can choose a process, artifact, pipe, command, or run identity."""
    def __init__(self, profile: dict, *, backend=None, driver_factory=None) -> None:
        self.profile = profile
        self.backend = backend or NativeProfileBackend()
        self.session_id = uuid.uuid4().hex
        self.pipe_name = rf"\\.\pipe\xar_profile_{self.session_id}"
        self._lock = threading.RLock()
        self._attach_result = None
        self._sequence = 0
        self.driver = None
        self.driver_factory = driver_factory
        self._gameplay = None

    def guard(self) -> dict:
        profile = self.profile
        self._reject_run_crash()
        if desktop.sha256(Path(profile["guard_profile"])).lower() != profile["guard_profile_sha256"].lower():
            raise RuntimeError("guard profile changed after server startup")
        observed = self.backend.observe(profile)
        desktop.validate_observation(profile["guard"], observed)
        userdirs = [arg.split("=", 1)[1] for arg in observed["command_line"]
                    if isinstance(arg, str) and arg.startswith("-userdir=")]
        if len(userdirs) != 1 or Path(userdirs[0]).resolve() != Path(profile["userdir"]).resolve():
            raise RuntimeError("live process isolated userdir does not match profile")
        self._reject_run_crash()
        return observed

    def _reject_run_crash(self) -> None:
        directory = Path(self.profile["userdir"]) / "crashes"
        if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
            raise RuntimeError("isolated run has a crash artifact; a live PID or native clock does not prove healthy gameplay")

    def _receipt(self, operation: str, value: dict) -> dict:
        self._sequence += 1
        directory = Path(self.profile["evidence_directory"]) / self.session_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._sequence:04d}-{operation}.json"
        result = {"schema": "ck3.native-profile-receipt.v1", "session_id": self.session_id,
                  "profile_sha256": self.profile["profile_sha256"], "pipe_name": self.pipe_name,
                  "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                  **value, "receipt_path": str(path)}
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result

    def inspect(self) -> dict:
        with self._lock:
            return self._receipt("inspect", {"status": "profile_bound", "observation": self.guard(),
                                           "attached": self._attach_result is not None
                                           and self._attach_result.get("status") == "attached_snapshot_verified"})

    def _snapshot(self) -> dict:
        if self.driver is None:
            raise RuntimeError("profile bridge has not been attached")
        snapshot = self.driver.take_snapshot()
        diagnostics = snapshot.get("diagnostics", {})
        hello = diagnostics.get("hello", {})
        target = self.profile["guard"]["target"]
        if (diagnostics.get("bridge_pid") != target["pid"]
                or hello.get("game_adapter_status") != "ready"
                or hello.get("expected_ck3_version") != self.profile["game_version"]
                or str(hello.get("expected_ck3_sha256", "")).lower() != target["executable_sha256"].lower()):
            raise RuntimeError("native hello is not the frozen target process and exact build")
        if type(snapshot.get("date_raw")) is not int or type(snapshot.get("paused")) is not bool or type(snapshot.get("speed")) is not int:
            raise RuntimeError("native date/paused/speed snapshot is unavailable")
        if snapshot.get("episode_projection") != "native_campaign":
            raise RuntimeError("native profile must consume the engine campaign without one-life projection")
        return snapshot

    def attach(self) -> dict:
        with self._lock:
            if self._attach_result is not None:
                return self._attach_result
            observed = self.guard()
            for name in ("dll", "injector"):
                row = self.profile[name]
                if desktop.sha256(Path(row["path"])).lower() != row["sha256"].lower():
                    raise RuntimeError(f"frozen {name} artifact SHA-256 changed")
            self.backend.poll(self.profile)
            self.guard()
            clock_before = self.backend.read_clock(self.profile)
            self.guard()
            if clock_before.get("paused") is not True:
                raise RuntimeError("profile bridge attach requires a paused initialized native clock")
            evidence = Path(self.profile["evidence_directory"])
            evidence.mkdir(parents=True, exist_ok=True)
            claim = evidence / "attach-claim.json"
            with claim.open("x", encoding="utf-8") as output:
                json.dump({"session_id": self.session_id, "profile_sha256": self.profile["profile_sha256"],
                           "pipe_name": self.pipe_name, "target": self.profile["guard"]["target"]}, output)
            if self.driver_factory is None:
                from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
                factory = NativeHeadlessGameplayDriver
            else:
                factory = self.driver_factory
            # Consume the one-shot before invoking the injector. A timeout or
            # failed readback must never replay a DLL attach into the same run.
            self._attach_result = {"status": "RED", "reason": "attach started"}
            injected = None
            try:
                self.driver = factory(self.pipe_name, state_dir=self.profile["state_directory"],
                                      save_dir=str(Path(self.profile["userdir"]) / "save games"),
                                      episode_projection="native_campaign")
                command = [self.profile["injector"]["path"], "--pipe", self.pipe_name,
                           str(self.profile["guard"]["target"]["pid"]), self.profile["dll"]["path"]]
                injected = self.backend.inject(command)
                if (injected.error is not None or injected.report.get("returncode") != 0
                        or injected.report.get("complete_process_tree_proven") is not True):
                    raise RuntimeError("injector did not prove a successful bounded attach")
                deadline = time.monotonic() + 10
                while True:
                    try:
                        snapshot = self._snapshot()
                        if (snapshot.get("map_ready") is not True or snapshot["paused"] is not True
                                or snapshot["date_raw"] != clock_before.get("date_raw")):
                            raise RuntimeError("first bridge snapshot does not match the paused map clock before attach")
                        break
                    except Exception:
                        if time.monotonic() >= deadline:
                            raise
                        time.sleep(0.05)
                after = self.guard()
                self._attach_result = self._receipt("attach", {
                    "status": "attached_snapshot_verified", "observation_before": observed,
                    "observation_after": after, "native_clock_before": clock_before,
                    "injector": injected.report, "snapshot": snapshot,
                    "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                self._attach_result = self._receipt("attach", {
                    "status": "RED", "reason": f"{type(error).__name__}: {error}",
                    "injector": injected.report if injected is not None else None})
            return self._attach_result

    def snapshot(self) -> dict:
        with self._lock:
            self.guard()
            snapshot = self._snapshot()
            after = self.guard()
            return self._receipt("snapshot", {"status": "native_snapshot_verified",
                                               "snapshot": snapshot, "observation_after": after})

    def _gameplay_service(self):
        if self._attach_result is None or self._attach_result.get("status") != "attached_snapshot_verified":
            raise RuntimeError("ordinary gameplay requires a verified profile attachment")
        if self._gameplay is None:
            from xar_autoplayer.bridge.service import GameplayBridgeService
            self._gameplay = GameplayBridgeService(self.driver)
        return self._gameplay

    def _bound_frame(self, expected_revision: int, *, paused: bool = False) -> dict:
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("expected_revision must be a nonnegative integer")
        self.guard()
        frame = self._snapshot()
        if (frame.get("map_ready") is not True or type(frame.get("revision")) is not int
                or frame["revision"] != expected_revision):
            raise RuntimeError("ordinary gameplay requires the expected map-ready native revision")
        if paused and frame.get("paused") is not True:
            raise RuntimeError("this native operation requires a paused frame")
        return frame

    def query_event(self, event_instance_id: int, expected_revision: int) -> dict:
        with self._lock:
            self._bound_frame(expected_revision, paused=True)
            result = self._gameplay_service().query_current_event_window_context_v1(
                event_instance_id, expected_revision=expected_revision)
            self._bound_frame(expected_revision, paused=True)
            return self._receipt("event-query", {"status": "native_event_query_verified", "result": result})

    def _ordinary_action(self, operation: str, expected_revision: int, invoke, verify, *, paused: bool = False) -> dict:
        with self._lock:
            before = self._bound_frame(expected_revision, paused=paused)
            gameplay = self._gameplay_service()
            self.backend.poll(self.profile)
            self._bound_frame(expected_revision, paused=paused)
            try:
                result = invoke(gameplay)
                after = self._snapshot()
                observation = self.guard()
                verify(result, before, after)
                return self._receipt(operation, {"status": "native_gameplay_postcondition_verified",
                    "result": result, "snapshot_before": before, "snapshot_after": after,
                    "observation_after": observation, "uses_ocr": False, "uses_desktop_input": False})
            except Exception as error:
                # A submitted action is never replayed here. Preserve failures
                # even when the native postcondition or foreground guard fails.
                return self._receipt(operation, {"status": "RED", "snapshot_before": before,
                    "reason": f"{type(error).__name__}: {error}"})

    def simulation(self, action: str, expected_revision: int) -> dict:
        steps = {"pause": "pause-map", "resume": "resume-map",
                 "speed_1": "set-speed-1", "speed_3": "set-speed-3", "speed_5": "set-speed-5"}
        if action not in steps:
            raise ValueError("unsupported ordinary simulation action")
        def verify(result, before, after):
            if action in {"pause", "resume"} and after["paused"] is not (action == "pause"):
                raise RuntimeError("native pause/resume postcondition did not materialize")
            if action.startswith("speed_") and after["speed"] != int(action[-1]):
                raise RuntimeError("native speed postcondition did not materialize")
        return self._ordinary_action("simulation-" + action, expected_revision,
            lambda service: service.execute_step(steps[action], expected_revision=expected_revision), verify)

    def select_event(self, option_number: int, event_instance_id: int, expected_revision: int) -> dict:
        if type(option_number) is not int or not 1 <= option_number <= 64:
            raise ValueError("option_number must be a public 1-based option ordinal")
        if type(event_instance_id) is not int or not 1 <= event_instance_id <= 2**31 - 1:
            raise ValueError("event_instance_id must be a positive full int32")
        def verify(result, before, after):
            active = after.get("active_event")
            if isinstance(active, dict) and active.get("instance_id") == event_instance_id:
                raise RuntimeError("selected event is still active after its native ACK")
        return self._ordinary_action("event-select", expected_revision,
            lambda service: service.select_event_option(option_number, event_instance_id=event_instance_id,
                                                        expected_revision=expected_revision), verify, paused=True)

    def checkpoint(self, expected_revision: int) -> dict:
        def verify(result, before, after):
            checkpoint = result.get("checkpoint", {})
            path = Path(checkpoint.get("path", ""))
            expected_dir = (Path(self.profile["userdir"]) / "save games").resolve()
            if (checkpoint.get("status") != "saved" or not path.is_absolute()
                    or path.resolve().parent != expected_dir or not path.is_file()
                    or type(checkpoint.get("size")) is not int or checkpoint["size"] <= 0
                    or path.stat().st_size != checkpoint["size"]
                    or desktop.sha256(path).lower() != str(checkpoint.get("sha256", "")).lower()
                    or checkpoint.get("date_raw") != before["date_raw"]):
                raise RuntimeError("native checkpoint bytes/path/date did not materialize in the isolated userdir")
        return self._ordinary_action("checkpoint", expected_revision,
            lambda service: service.save_checkpoint(expected_revision=expected_revision), verify, paused=True)

    def close(self) -> None:
        if self.driver is not None:
            self.driver.close()


class NativeClockProfileService(NativeProfileService):
    def clock(self) -> dict:
        with self._lock:
            self.guard()
            clock = self.backend.read_clock(self.profile)
            after = self.guard()
            return self._receipt("clock", {"status": "native_clock_verified", "clock": clock,
                                            "observation_after": after,
                                            "uses_ocr": False, "uses_desktop_input": False,
                                            "uses_injection": False, "writes_process_memory": False})


def create_clock_server(service: NativeClockProfileService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer("CK3 frozen native clock")
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_read_profile_native_clock_v1() -> dict[str, object]:
        return service.clock()
    _forbid_unknown_tool_arguments_v1(server, "ck3_read_profile_native_clock_v1")
    return server


def create_server(service: NativeProfileService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer("CK3 frozen native profile")
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_native_profile_v1() -> dict[str, object]:
        return service.inspect()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_attach_profile_bridge_v1() -> dict[str, object]:
        return service.attach()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_take_profile_native_snapshot_v1() -> dict[str, object]:
        return service.snapshot()
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def ck3_query_profile_event_window_v1(event_instance_id: int, expected_revision: int) -> dict[str, object]:
        return service.query_event(event_instance_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_set_profile_simulation_v1(
        action: Literal["pause", "resume", "speed_1", "speed_3", "speed_5"], expected_revision: int,
    ) -> dict[str, object]:
        return service.simulation(action, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_select_profile_event_option_v1(option_number: int, event_instance_id: int, expected_revision: int) -> dict[str, object]:
        return service.select_event(option_number, event_instance_id, expected_revision)
    @server.tool(annotations=ToolAnnotations(readOnlyHint=False))
    def ck3_save_profile_checkpoint_v1(expected_revision: int) -> dict[str, object]:
        return service.checkpoint(expected_revision)
    for name in ("ck3_query_native_profile_v1", "ck3_attach_profile_bridge_v1", "ck3_take_profile_native_snapshot_v1",
                 "ck3_query_profile_event_window_v1", "ck3_set_profile_simulation_v1",
                 "ck3_select_profile_event_option_v1", "ck3_save_profile_checkpoint_v1"):
        _forbid_unknown_tool_arguments_v1(server, name)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--clock-only", action="store_true")
    args = parser.parse_args()
    if args.clock_only:
        create_clock_server(NativeClockProfileService(load_clock_profile(args.profile))).run(transport="stdio")
        return
    service = NativeProfileService(load_profile(args.profile))
    try:
        create_server(service).run(transport="stdio")
    finally:
        service.close()


if __name__ == "__main__":
    main()
