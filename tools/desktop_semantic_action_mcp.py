"""Execute reviewed, profile-frozen CK3 GUI clicks through a narrow MCP.

This is a temporary desktop fallback for native capabilities not implemented
on the active exact build. Dispatch receipts do not prove gameplay outcomes.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import threading
import time
import uuid

import desktop_coordinate_map as coordinates

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(PACKAGE_ROOT))
from xar_autoplayer.operator_mcp import _forbid_unknown_tool_arguments_v1
from xar_autoplayer.steam_workshop_status import _offline_flags, _parse_vdf


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_fields(value: object, fields: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} requires exactly {sorted(fields)}")
    return value


def load_profile(path: Path) -> dict:
    profile = exact_fields(json.loads(path.read_text(encoding="utf-8-sig")), {
        "schema_version", "target", "steam", "task_bus_script", "task_bus_sha256",
        "screen_task_id", "evidence_directory", "actions",
    }, "profile")
    if isinstance(profile["schema_version"], bool) or profile["schema_version"] != 1:
        raise ValueError("profile schema_version must be 1")
    target = exact_fields(profile["target"], {
        "pid", "hwnd", "process_create_time", "executable", "executable_sha256",
        "app_manifest", "build_id", "window_title", "window_class", "window_rect",
    }, "target")
    for key in ("pid", "hwnd"):
        if isinstance(target[key], bool) or not isinstance(target[key], int) or target[key] <= 0:
            raise ValueError(f"target {key} must be a positive integer")
    if isinstance(target["process_create_time"], bool) or not isinstance(target["process_create_time"], (float, int)) or not math.isfinite(target["process_create_time"]) or target["process_create_time"] <= 0:
        raise ValueError("target process_create_time must be positive")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", target["executable_sha256"]):
        raise ValueError("target executable_sha256 must be SHA-256")
    steam = exact_fields(profile["steam"], {
        "root", "pid", "process_create_time", "offline_evidence", "offline_evidence_sha256",
        "offline_visual_reviewed",
    }, "steam")
    if steam["offline_visual_reviewed"] is not True:
        raise ValueError("Steam offline evidence must have been visually reviewed")
    if isinstance(steam["pid"], bool) or not isinstance(steam["pid"], int) or steam["pid"] <= 0:
        raise ValueError("Steam pid must be a positive integer")
    if isinstance(steam["process_create_time"], bool) or not isinstance(steam["process_create_time"], (float, int)) or not math.isfinite(steam["process_create_time"]) or steam["process_create_time"] <= 0:
        raise ValueError("Steam process_create_time must be positive")
    for field in ("build_id", "window_title", "window_class"):
        if not isinstance(target[field], str) or not target[field]:
            raise ValueError(f"target {field} must be nonempty text")
    rect = target["window_rect"]
    if (not isinstance(rect, list) or len(rect) != 4
            or any(isinstance(value, bool) or not isinstance(value, int) for value in rect)
            or rect[0] >= rect[2] or rect[1] >= rect[3]):
        raise ValueError("window_rect requires a nonempty integer rectangle")
    for digest in (profile["task_bus_sha256"], steam["offline_evidence_sha256"]):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError("task bus and offline evidence require SHA-256")
    actions = profile["actions"]
    if not isinstance(actions, dict) or not actions or len(actions) > 32:
        raise ValueError("actions requires 1 to 32 configured semantic names")
    for name, value in actions.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,79}", name):
            raise ValueError("action name must be a portable semantic identifier")
        action = exact_fields(value, {
            "source_image", "source_sha256", "preview_bounds", "observed_point", "reviewed_bounds",
        }, f"action {name}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", action["source_sha256"]):
            raise ValueError("action source_sha256 must be SHA-256")
        for field, count in (("preview_bounds", 4), ("observed_point", 2), ("reviewed_bounds", 4)):
            if not isinstance(action[field], list) or len(action[field]) != count:
                raise ValueError(f"{field} requires {count} numbers")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in action[field]):
                raise ValueError(f"{field} requires finite numbers")
    for value in [profile[key] for key in ("task_bus_script", "evidence_directory")] + [steam["root"], steam["offline_evidence"], target["executable"], target["app_manifest"]] + [item["source_image"] for item in actions.values()]:
        if not isinstance(value, str) or not Path(value).is_absolute():
            raise ValueError("profile paths must be absolute target-side paths")
    if not isinstance(profile["screen_task_id"], str) or not profile["screen_task_id"]:
        raise ValueError("screen_task_id must be nonempty text")
    profile["profile_sha256"] = sha256(path)
    return profile


class NativeDesktopBackend:
    def observe(self, profile: dict) -> dict:
        import psutil
        import pyautogui
        import win32gui
        import win32process
        import desktop_steam_offline_recovery as recovery

        target = profile["target"]
        process = psutil.Process(target["pid"])
        hwnd = target["hwnd"]
        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
        steam = profile["steam"]
        steam_process = psutil.Process(steam["pid"])
        loginusers = Path(steam["root"]) / "config" / "loginusers.vdf"
        login_bytes = loginusers.read_bytes()
        manifest = Path(target["app_manifest"])
        manifest_bytes = manifest.read_bytes()
        app_state = _parse_vdf(manifest_bytes.decode("utf-8-sig"))["AppState"]
        executable = Path(process.exe())
        bus_script = Path(profile["task_bus_script"])
        if sha256(bus_script).lower() != profile["task_bus_sha256"].lower():
            raise RuntimeError("task-bus CLI SHA-256 changed")
        offline_evidence = Path(steam["offline_evidence"])
        if sha256(offline_evidence).lower() != steam["offline_evidence_sha256"].lower():
            raise RuntimeError("reviewed offline evidence SHA-256 changed")
        offline_receipt = json.loads(offline_evidence.read_text(encoding="utf-8-sig"))
        if offline_receipt.get("schema") != "ck3.steam_fresh_desktop_frame.v1" or offline_receipt.get("steam_pid") != steam["pid"]:
            raise RuntimeError("offline evidence belongs to a different Steam process")
        tasks = recovery.task_bus_tasks(bus_script)
        task_rows = [row for row in tasks if row.get("task_id") == profile["screen_task_id"]]
        lease_fresh = len(task_rows) == 1 and (
            datetime.now(timezone.utc) - datetime.fromisoformat(task_rows[0]["updated_at_utc"])
        ).total_seconds() <= 600
        return {
            "pid": process.pid, "hwnd": hwnd, "window_pid": window_pid,
            "process_create_time": process.create_time(), "executable": str(executable),
            "executable_sha256": sha256(executable), "build_id": app_state.get("buildid"),
            "app_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "window_visible": bool(win32gui.IsWindowVisible(hwnd)),
            "window_title": win32gui.GetWindowText(hwnd), "window_class": win32gui.GetClassName(hwnd),
            "window_rect": list(win32gui.GetWindowRect(hwnd)),
            "focus": coordinates.foreground_state(), "screen_size": list(pyautogui.size()),
            "mouse_buttons": coordinates.mouse_button_state(),
            "steam_offline_flags": _offline_flags(login_bytes.decode("utf-8-sig")),
            "steam_loginusers_sha256": hashlib.sha256(login_bytes).hexdigest(),
            "steam_pid": steam_process.pid, "steam_create_time": steam_process.create_time(),
            "steam_executable": steam_process.exe(), "screen_lease_fresh": lease_fresh,
            "screen_owners": recovery.screen_owners(tasks),
        }

    def image_size(self, path: Path) -> tuple[int, int]:
        from PIL import Image
        with Image.open(path) as image:
            return image.size

    def capture(self, path: Path) -> dict:
        import pyautogui
        image = pyautogui.screenshot()
        image.save(path)
        return {"path": str(path), "bytes": path.stat().st_size,
                "sha256": sha256(path), "size": list(image.size)}

    def click(self, point: tuple[int, int]) -> None:
        import pyautogui
        pyautogui.click(*point, button="left", clicks=1)
        time.sleep(0.35)


def validate_observation(profile: dict, observed: dict) -> None:
    target = profile["target"]
    for key in ("pid", "hwnd", "process_create_time", "build_id", "window_title", "window_class", "window_rect"):
        if observed.get(key) != target[key]:
            raise RuntimeError(f"target {key} changed")
    if Path(observed["executable"]).resolve() != Path(target["executable"]).resolve():
        raise RuntimeError("target executable changed")
    if observed["executable_sha256"].lower() != target["executable_sha256"].lower():
        raise RuntimeError("target executable SHA-256 changed")
    if not observed["window_visible"] or observed["window_pid"] != target["pid"]:
        raise RuntimeError("target window owner/visibility changed")
    if observed["focus"]["foreground_hwnd"] != target["hwnd"] or observed["focus"]["foreground_pid"] != target["pid"]:
        raise RuntimeError("target window must already be foreground")
    if any(observed["mouse_buttons"].values()):
        raise RuntimeError("mouse button held before action")
    if observed["steam_offline_flags"] != ["1"]:
        raise RuntimeError("Steam offline file readback is not confirmed")
    steam = profile["steam"]
    if (observed["steam_pid"] != steam["pid"] or observed["steam_create_time"] != steam["process_create_time"]
            or Path(observed["steam_executable"]).resolve() != (Path(steam["root"]) / "steam.exe").resolve()):
        raise RuntimeError("reviewed Steam session changed")
    if observed["screen_owners"] != [profile["screen_task_id"]]:
        raise RuntimeError("exclusive task-bus screen lease missing or conflicted")
    if observed["screen_lease_fresh"] is not True:
        raise RuntimeError("screen lease heartbeat is older than ten minutes")


class SemanticActionService:
    def __init__(self, profile: dict, backend: object | None = None) -> None:
        self.profile = profile
        self.backend = backend or NativeDesktopBackend()
        self.session_id = str(uuid.uuid4())
        self.lock = threading.Lock()
        self.receipts: dict[str, dict] = {}

    def inspect(self) -> dict:
        observation = self.backend.observe(self.profile)
        validate_observation(self.profile, observation)
        return {"schema": "desktop.semantic-action-profile.v1", "session_id": self.session_id,
                "profile_sha256": self.profile["profile_sha256"],
                "actions": sorted(self.profile["actions"]), "observation": observation,
                "receipts": self.receipts, "read_only": True}

    def execute(self, action_name: str) -> dict:
        with self.lock:
            if action_name not in self.profile["actions"]:
                raise ValueError("action is absent from the frozen allowlist")
            if action_name in self.receipts:
                return self.receipts[action_name]
            action = self.profile["actions"][action_name]
            source = Path(action["source_image"])
            if sha256(source).lower() != action["source_sha256"].lower():
                raise RuntimeError("reviewed source screenshot SHA-256 changed")
            before = self.backend.observe(self.profile)
            validate_observation(self.profile, before)
            source_size = self.backend.image_size(source)
            live_size = tuple(before["screen_size"])
            if source_size != live_size:
                raise RuntimeError("reviewed source image and live desktop sizes disagree")
            mapping = coordinates.Mapping(tuple(action["preview_bounds"]), tuple(action["observed_point"]),
                source_size, live_size, coordinates.map_point(
                    preview_bounds=tuple(action["preview_bounds"]),
                    observed_point=tuple(action["observed_point"]), target_size=live_size))
            coordinates.validate_reviewed_region(mapping, tuple(action["reviewed_bounds"]))
            left, top, right, bottom = self.profile["target"]["window_rect"]
            if not (left <= mapping.screen_point[0] < right and top <= mapping.screen_point[1] < bottom):
                raise RuntimeError("reviewed action point is outside the target window")
            folder = Path(self.profile["evidence_directory"]) / self.session_id / action_name
            folder.mkdir(parents=True, exist_ok=False)
            receipt = {"schema": "desktop.semantic-action-receipt.v1", "session_id": self.session_id,
                "profile_sha256": self.profile["profile_sha256"], "action_name": action_name,
                "at_utc": datetime.now(timezone.utc).isoformat(), "mapping": asdict(mapping),
                "source_sha256": action["source_sha256"], "observation_before": before,
                "input_backend": "reviewed_profile_desktop_click", "uses_ocr": False,
                "uses_keyboard": False, "business_postcondition_verified": False,
                "click_attempted": False, "click_dispatched": False, "status": "pending"}
            self.receipts[action_name] = receipt
            try:
                receipt["capture_before"] = self.backend.capture(folder / "before.png")
                # Read guards again immediately before dispatch, after capture.
                dispatch = self.backend.observe(self.profile)
                validate_observation(self.profile, dispatch)
                if tuple(dispatch["screen_size"]) != live_size:
                    raise RuntimeError("desktop dimensions changed before dispatch")
                receipt["observation_at_dispatch"] = dispatch
                receipt["click_attempted"] = True
                self.backend.click(mapping.screen_point)
                receipt["click_dispatched"] = True
                receipt["capture_after"] = self.backend.capture(folder / "after.png")
                after = self.backend.observe(self.profile)
                receipt["observation_after"] = after
                validate_observation(self.profile, after)
                if tuple(after["screen_size"]) != live_size or tuple(receipt["capture_after"]["size"]) != live_size:
                    raise RuntimeError("desktop or receipt dimensions changed after dispatch")
                receipt["status"] = "dispatched_requires_business_readback"
            except Exception as error:
                receipt["status"] = "RED"
                receipt["error"] = f"{type(error).__name__}: {error}"
            receipt_path = folder / "receipt.json"
            receipt["receipt_path"] = str(receipt_path)
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return receipt


def create_server(service: SemanticActionService):
    from mcp.server import MCPServer
    from mcp.types import ToolAnnotations
    server = MCPServer(name="Reviewed CK3 Desktop Actions", version="1.0.0",
        instructions="Select only a configured semantic action. A dispatch receipt requires independent gameplay readback.")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
    def desktop_query_action_profile_v1() -> dict[str, object]:
        return service.inspect()

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False))
    def desktop_execute_action_v1(action_name: str) -> dict[str, object]:
        return service.execute(action_name)

    for name in ("desktop_query_action_profile_v1", "desktop_execute_action_v1"):
        _forbid_unknown_tool_arguments_v1(server, name)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args()
    create_server(SemanticActionService(load_profile(args.profile))).run(transport="stdio")


if __name__ == "__main__":
    main()
