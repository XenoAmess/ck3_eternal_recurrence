"""Thin external writer for the existing CK3 native profile schemas.

Only reads processes/windows/Steam/task-bus state and writes a new profile
attempt. Never focuses a window, captures pixels, sends input or injects a DLL.
The required actions_file contains explicit previously reviewed action data;
this helper does not derive or invent GUI coordinates.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
REPO = Path('C:/lr17s1').resolve()


FIELDS = {"schema", "pid", "hwnd", "steam_ui_pid", "steam_client_pid", "offline_review",
          "offline_image_sha256", "lease_receipt", "screen_task_id", "task_bus_script",
          "task_bus_sha256", "native_template", "actions_file", "output"}
EXE_SHA = "94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6"
EXE = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/binaries/ck3.exe")
MANIFEST = Path("C:/Program Files (x86)/Steam/steamapps/appmanifest_1158310.acf")


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def build(request_path: Path) -> dict:
    require(REPO is not None,'Actual new clean metadata/export profile source is PENDING')
    sys.path.insert(0,str(REPO/'ck3_autonomous_player/src'))
    sys.path.insert(0,str(REPO/'tools'))
    # Imports reuse current authoritative observers; these imports perform no actions.
    import psutil
    import win32gui
    import win32process
    import desktop_semantic_action_mcp as desktop
    import ck3_native_profile_mcp as native
    from xar_autoplayer.steam_workshop_status import _parse_vdf

    request = desktop.exact_fields(read(request_path), FIELDS, "fresh-profile request")
    require(request["schema"] == "ck3.lyd.fresh-profile-request.v1", "wrong request schema")
    for key in ("pid", "hwnd", "steam_ui_pid", "steam_client_pid"):
        require(type(request[key]) is int and request[key] > 0, f"{key} must be an actual positive integer")
    output = Path(request["output"]).resolve()
    require(BASE in output.parents, "output must stay inside this external work package")
    require(not output.exists(), "choose a fresh output directory")
    output.mkdir(parents=True)
    report = {"schema": "ck3.lyd.fresh-profile-build.v1", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "request_path": str(request_path.resolve()), "request_sha256": sha(request_path),
              "side_effects": {"input_sent": False, "game_started": False, "bridge_injected": False}}
    try:
        process = psutil.Process(request["pid"])
        executable = Path(process.exe()).resolve()
        require(executable == EXE.resolve(), "observed process is not the current C Program CK3 installation")
        require(sha(executable) == EXE_SHA, "CK3 EXE does not match exact 1.20.0.3")
        launcher = executable.parent.parent / "launcher/launcher-settings.json"
        require(read(launcher).get("rawVersion") == "1.20.0.3", "launcher version is not exact 1.20.0.3")
        _, window_pid = win32process.GetWindowThreadProcessId(request["hwnd"])
        require(window_pid == process.pid and win32gui.IsWindowVisible(request["hwnd"]), "HWND is not the visible target process window")
        ui_process, client_process = psutil.Process(request["steam_ui_pid"]), psutil.Process(request["steam_client_pid"])
        steam_root = Path(client_process.exe()).resolve().parent
        require(Path(client_process.exe()).name.lower() == "steam.exe", "Steam client PID is not steam.exe")
        review_path = Path(request["offline_review"]).resolve()
        review = read(review_path)
        require(review.get("steam_offline_confirmed") is True, "offline image has no explicit visual review")
        require(review.get("image_sha256", "").lower() == request["offline_image_sha256"].lower(), "requested reviewed image SHA differs")
        image = (review_path.parent / review["image"]).resolve()
        require(sha(image) == request["offline_image_sha256"].lower(), "reviewed image bytes changed")
        offline_path = (review_path.parent / review["fresh_frame_receipt"]).resolve()
        offline = read(offline_path)
        require(offline.get("schema") == "ck3.steam_fresh_desktop_frame.v1", "wrong fresh frame schema")
        require(offline.get("steam_pid") == ui_process.pid, "offline frame belongs to a different Steam UI PID")
        require(Path(offline["moved_path"]).resolve() == image and offline["moved_sha256"].lower() == sha(image), "review did not bind the moved fresh-frame image")
        require(offline.get("moving_edge_changed") is True, "receipt does not establish a changed live Steam frame")
        require("requires a new fresh review" not in str(review.get("evidence_scope", "")).lower(), "review explicitly excludes actual CK3 launch")
        captured = datetime.fromisoformat(offline["captured_at_utc"].replace("Z", "+00:00"))
        require(captured.utcoffset() is not None, "capture time requires timezone")
        require(ui_process.create_time() <= captured.timestamp() and client_process.create_time() <= captured.timestamp(), "Steam process was replaced after offline capture")
        lease_path = Path(request["lease_receipt"]).resolve()
        lease = read(lease_path)
        task = lease.get("task", {})
        require(lease.get("schema") == "codex.task_bus.v1" and lease.get("ok") is True, "invalid task-bus receipt")
        require(task.get("task_id") == request["screen_task_id"] and task.get("state") == "running" and "ck3-screen:acquired" in task.get("resources", []), "lease receipt does not bind the exclusive task")
        bus_path = Path(request["task_bus_script"]).resolve()
        require(sha(bus_path) == request["task_bus_sha256"].lower(), "task-bus executable bytes differ from explicit pin")
        template_path = Path(request["native_template"]).resolve()
        template = read(template_path)
        require(template.get("game_version") == "1.20.0.3", "template is not a current-build native profile")
        userdir = Path(template["userdir"]).resolve()
        cmdline = process.cmdline()
        userdirs = [Path(arg.split("=", 1)[1]).resolve() for arg in cmdline if arg.startswith("-userdir=")]
        require(userdirs == [userdir], "actual process isolated userdir differs from template")
        require(not (userdir / "crashes").exists() or not any((userdir / "crashes").iterdir()), "isolated run already has a crash artifact")
        for key in ("dll", "injector"):
            require(sha(Path(template[key]["path"])) == template[key]["sha256"].lower(), f"{key} artifact changed")
        actions_path = Path(request["actions_file"]).resolve()
        actions = read(actions_path)
        require(isinstance(actions, dict), "actions_file must contain the exact reviewed actions dictionary")
        app_state = _parse_vdf(MANIFEST.read_text(encoding="utf-8-sig"))["AppState"]
        guard = {
            "schema_version": 1,
            "target": {"pid": process.pid, "hwnd": request["hwnd"], "process_create_time": process.create_time(),
                       "executable": str(executable), "executable_sha256": EXE_SHA, "app_manifest": str(MANIFEST),
                       "build_id": app_state["buildid"], "window_title": win32gui.GetWindowText(request["hwnd"]),
                       "window_class": win32gui.GetClassName(request["hwnd"]), "window_rect": list(win32gui.GetWindowRect(request["hwnd"]))},
            "steam": {"root": str(steam_root), "pid": ui_process.pid, "process_create_time": ui_process.create_time(),
                      "offline_evidence": str(offline_path), "offline_evidence_sha256": sha(offline_path),
                      "offline_visual_reviewed": True, "client_pid": client_process.pid,
                      "client_process_create_time": client_process.create_time()},
            "task_bus_script": str(bus_path), "task_bus_sha256": sha(bus_path), "screen_task_id": request["screen_task_id"],
            "evidence_directory": str(output / "guard-evidence"), "actions": actions,
        }
        guard_path = output / "guard-profile.json"
        write(guard_path, guard)
        loaded_guard = desktop.load_profile(guard_path)
        observed = desktop.NativeDesktopBackend().observe(loaded_guard)
        desktop.validate_observation(loaded_guard, observed)
        # The authoritative observer rereads PID/create times, image receipt,
        # current window geometry/foreground, Steam flags and the live lease.
        template["guard_profile"], template["guard_profile_sha256"] = str(guard_path), sha(guard_path)
        profile_path = output / "native-profile.json"
        write(profile_path, template)
        loaded = native.load_profile(profile_path)
        observed_native = native.NativeProfileBackend().observe(loaded)
        desktop.validate_observation(loaded["guard"], observed_native)
        require(observed_native["command_line"] == cmdline, "target command line changed while freezing profile")
        for name, path in (("offline-review", review_path), ("offline-frame", offline_path), ("lease", lease_path), ("native-template", template_path), ("reviewed-actions", actions_path)):
            (output / f"{name}.snapshot.json").write_bytes(path.read_bytes())
        report.update(status="PROFILE_FROZEN_READ_ONLY", guard_profile=str(guard_path), guard_sha256=sha(guard_path),
                      native_profile=str(profile_path), native_sha256=sha(profile_path), observation=observed_native,
                      launcher_settings_sha256=sha(launcher), app_manifest_sha256=sha(MANIFEST),
                      gui_actions="preserved explicit input only; do not run a desktop action server with this native guard")
    except Exception as error:
        report.update(status="RED", reason=f"{type(error).__name__}: {error}")
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write(output / "profile-build-receipt.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True, help="closed-schema JSON request; see NATIVE_PROFILE.md")
    args = parser.parse_args()
    try:
        report = build(args.request)
    except Exception as error:
        print(f"PROFILE PREPARATION FAILED: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PROFILE_FROZEN_READ_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
