"""Preflight and cautiously recover a stale Steam desktop capture on Windows.

The tool never changes Steam's mode, starts CK3, or infers offline status from
old pixels. Recovery requires an exclusive screen lease in the task bus.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

import psutil
import pywintypes
import win32con
import win32gui

import steam_offline_fresh_frame


SERVICE = "ToDesk_Service"
SCREEN_RESOURCE = "ck3-screen:acquired"
STALE_CAPTURE_ERROR = "desktop capture did not respond to live Steam movement"
DEFAULT_BUS = Path(r"D:\workspace\.codex-task-bus\bin\codex_task_bus.py")
RECORDER_NAMES = {"ffmpeg.exe", "obs64.exe", "obs32.exe", "obs.exe"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def task_bus_tasks(bus: Path) -> list[dict]:
    result = subprocess.run([sys.executable, str(bus), "list"],
                            capture_output=True, text=True, timeout=15, check=True)
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True or not isinstance(payload.get("tasks"), list):
        raise RuntimeError("task bus list did not return a valid task set")
    return payload["tasks"]


def screen_owners(tasks: list[dict]) -> list[str]:
    return sorted(task["task_id"] for task in tasks
                  if task.get("state") == "running"
                  and (not task.get("stale", False)
                       or (isinstance(task.get("pid"), int)
                           and psutil.pid_exists(task["pid"])))
                  and SCREEN_RESOURCE in task.get("resources", []))


def ck3_pids() -> list[int]:
    return sorted(process.info["pid"] for process in psutil.process_iter(["pid", "name"])
                  if (process.info["name"] or "").lower() == "ck3.exe")


def recorder_pids() -> list[int]:
    return sorted(process.info["pid"] for process in psutil.process_iter(["pid", "name"])
                  if (process.info["name"] or "").lower() in RECORDER_NAMES)


def service_state() -> dict:
    service = psutil.win_service_get(SERVICE).as_dict()
    return {"name": SERVICE, "status": service["status"], "pid": service.get("pid"),
            "start_type": service.get("start_type")}


def preflight(tasks: list[dict], task_id: str, ck3: list[int], service: dict,
              steam_windows: list[tuple[int, int]]) -> list[str]:
    reasons = []
    owners = screen_owners(tasks)
    if owners != [task_id]:
        reasons.append("exclusive_screen_lease_missing_or_conflicted")
    if ck3:
        reasons.append("ck3_running")
    if service["status"] not in ("running", "stopped"):
        reasons.append("todesk_service_transitional_or_unknown")
    if len(steam_windows) != 1:
        reasons.append("steam_window_not_unique")
    return reasons


def require_exclusive_screen(bus: Path, task_id: str) -> None:
    if screen_owners(task_bus_tasks(bus)) != [task_id]:
        raise RuntimeError("exclusive screen lease changed during recovery")
    if ck3_pids():
        raise RuntimeError("CK3 started during recovery")


def wait_service(expected: str, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        state = service_state()
        if state["status"] == expected:
            return state
        if time.monotonic() >= deadline:
            raise TimeoutError(f"{SERVICE} did not reach {expected}: {state['status']}")
        time.sleep(0.5)


def sc(action: str, timeout_seconds: int) -> None:
    result = subprocess.run(["sc.exe", action, SERVICE], capture_output=True,
                            text=True, timeout=timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError(f"sc {action} {SERVICE} failed with code {result.returncode}")


def ensure_service_running(timeout_seconds: int) -> dict:
    state = service_state()
    if state["status"] == "stopped":
        sc("start", timeout_seconds)
        return wait_service("running", timeout_seconds)
    if state["status"] != "running":
        raise RuntimeError(f"unsupported ToDesk service status: {state['status']}")
    return state


def restart_running_service(timeout_seconds: int) -> dict:
    if service_state()["status"] != "running":
        raise RuntimeError("ToDesk service must be running before restart")
    try:
        sc("stop", timeout_seconds)
        wait_service("stopped", timeout_seconds)
    finally:
        # A failed stop/probe must still try to restore the remote service.
        # A stop-pending timeout remains an explicit RED; it cannot be called
        # recovered even if the service eventually changes state later.
        try:
            if service_state()["status"] == "stop_pending":
                wait_service("stopped", timeout_seconds)
        finally:
            if service_state()["status"] in ("running", "stopped"):
                ensure_service_running(timeout_seconds)
    return service_state()


def capture_fresh_frame(output_dir: Path, hwnd: int, bring_forward: bool,
                        clock_reference: Path | None = None,
                        clock_rect: tuple[int, int, int, int] | None = None) -> dict:
    previous = win32gui.GetForegroundWindow()
    if previous != hwnd:
        if not bring_forward:
            raise RuntimeError("Steam is not foreground; pass --bring-steam-forward under the screen lease")
        win32gui.ShowWindow(
            hwnd, win32con.SW_RESTORE if win32gui.IsIconic(hwnd) else win32con.SW_SHOW
        )
        try:
            win32gui.SetForegroundWindow(hwnd)
        except pywintypes.error as exc:
            raise RuntimeError("could not make Steam foreground") from exc
        # Windows may apply SetForegroundWindow after the call returns.  A
        # single immediate read falsely rejected a healthy Steam window in
        # attempt 088, even though the next preflight saw it in front.
        deadline = time.monotonic() + 2.0
        while win32gui.GetForegroundWindow() != hwnd:
            if time.monotonic() >= deadline:
                raise RuntimeError("could not make Steam foreground")
            time.sleep(0.05)
    receipt = None
    try:
        if clock_reference is None:
            receipt = steam_offline_fresh_frame.capture(output_dir)
        else:
            receipt = steam_offline_fresh_frame.capture(
                output_dir, clock_reference=clock_reference, clock_rect=clock_rect)
        return receipt
    finally:
        if previous != hwnd and win32gui.IsWindow(previous):
            try:
                win32gui.SetForegroundWindow(previous)
            except pywintypes.error as exc:
                # Windows can deny restoring the old foreground HWND after a
                # successful Steam capture. Preserve the fresh-frame receipt
                # and record the focus error instead of losing its evidence.
                if receipt is not None:
                    receipt["foreground_restore_error"] = str(exc)


def inspect(bus: Path) -> dict:
    try:
        tasks = task_bus_tasks(bus)
        bus_error = None
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        tasks = []
        bus_error = type(exc).__name__
    return {
        "schema": "ck3.desktop_steam_offline_recovery.v1",
        "observed_at_utc": now(),
        "todesk_service": service_state(),
        "ck3_pids": ck3_pids(),
        "recorder_pids": recorder_pids(),
        "steam_windows": [{"hwnd": hwnd, "pid": pid}
                          for hwnd, pid in steam_offline_fresh_frame._steam_windows()],
        "foreground_hwnd": win32gui.GetForegroundWindow(),
        "screen_owners": screen_owners(tasks),
        "stale_screen_records": sorted(task["task_id"] for task in tasks
                                       if task.get("stale", False)
                                       and SCREEN_RESOURCE in task.get("resources", [])),
        "task_bus_error": bus_error,
        "steam_offline_status_observed": None,
    }


def recover(args: argparse.Namespace) -> dict:
    output_dir = args.output_dir
    output_dir.mkdir(parents=False, exist_ok=False)
    events = output_dir / "events.jsonl"

    def record(kind: str, **fields: object) -> None:
        with events.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps({"at_utc": now(), "kind": kind, **fields},
                                    ensure_ascii=False) + "\n")

    before = inspect(args.task_bus)
    record("preflight", state=before)
    try:
        tasks = task_bus_tasks(args.task_bus)
        bus_error = None
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        tasks = []
        bus_error = type(exc).__name__
    windows = steam_offline_fresh_frame._steam_windows()
    blockers = preflight(tasks, args.task_id, ck3_pids(), service_state(), windows)
    if bus_error:
        blockers.append("task_bus_unavailable")
    if blockers:
        outcome = "blocked"
        record("blocked", reasons=blockers)
        fresh_frame = None
    else:
        hwnd, steam_pid = windows[0]
        outcome = "unverified"
        fresh_frame = None
        try:
            require_exclusive_screen(args.task_bus, args.task_id)
            service_before = service_state()
            ensure_service_running(args.service_timeout_seconds)
            if service_before["status"] == "stopped":
                record("todesk_started", state=service_state())
            for attempt in (1, 2):
                require_exclusive_screen(args.task_bus, args.task_id)
                probe_dir = output_dir / f"probe-{attempt}"
                probe_dir.mkdir(exist_ok=False)
                try:
                    clock_reference = getattr(args, "stale_clock_reference", None)
                    clock_rect = getattr(args, "stale_clock_rect", None)
                    if clock_reference is None:
                        receipt = capture_fresh_frame(probe_dir, hwnd, args.bring_steam_forward)
                    else:
                        receipt = capture_fresh_frame(
                            probe_dir, hwnd, args.bring_steam_forward,
                            clock_reference=clock_reference, clock_rect=tuple(clock_rect))
                    record("fresh_frame", attempt=attempt, receipt=receipt)
                    fresh_frame = {"receipt_path": str(probe_dir / "steam-frame-freshness.json"),
                                   "image_identity": receipt.get("moved_identity")}
                    outcome = "fresh_frame_needs_offline_visual_review"
                    break
                except RuntimeError as exc:
                    record("probe_failed", attempt=attempt, error=str(exc))
                    if (attempt != 1 or str(exc) != STALE_CAPTURE_ERROR
                            or not args.restart_running_todesk_on_stale):
                        outcome = "stale_or_unavailable"
                        break
                    require_exclusive_screen(args.task_bus, args.task_id)
                    recorders = recorder_pids()
                    if recorders:
                        record("restart_blocked", reason="recorder_running",
                               recorder_pids=recorders)
                        outcome = "stale_or_unavailable"
                        break
                    restarted = restart_running_service(args.service_timeout_seconds)
                    record("todesk_restarted", state=restarted)
            if not any(pid == steam_pid for _, pid in steam_offline_fresh_frame._steam_windows()):
                raise RuntimeError("Steam UI process identity changed during recovery")
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
            outcome = "recovery_error"
            record("recovery_error", error_type=type(exc).__name__, error=str(exc))
    report = {"schema": "ck3.desktop_steam_offline_recovery.v1",
              "completed_at_utc": now(), "outcome": outcome,
              "preflight": before, "steam_offline_status_observed": None,
              "steam_mode_mutation_attempted": False,
              "ck3_launch_attempted": False,
              "fresh_frame": fresh_frame,
              "events_path": str(events)}
    with (output_dir / "recovery.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-bus", type=Path, default=DEFAULT_BUS)
    subcommands = parser.add_subparsers(dest="mode", required=True)
    subcommands.add_parser("inspect")
    recovery = subcommands.add_parser("recover")
    recovery.add_argument("--task-id", required=True)
    recovery.add_argument("--output-dir", type=Path, required=True)
    recovery.add_argument("--bring-steam-forward", action="store_true")
    recovery.add_argument("--restart-running-todesk-on-stale", action="store_true")
    recovery.add_argument("--stale-clock-reference", type=Path,
                          help="previously reviewed desktop screenshot with a visible clock")
    recovery.add_argument("--stale-clock-rect", type=int, nargs=4,
                          metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    recovery.add_argument("--service-timeout-seconds", type=int, default=20)
    args = parser.parse_args()
    if args.mode == "recover" and args.service_timeout_seconds <= 0:
        parser.error("--service-timeout-seconds must be positive")
    if args.mode == "recover" and ((args.stale_clock_reference is None)
                                   != (args.stale_clock_rect is None)):
        parser.error("--stale-clock-reference and --stale-clock-rect must be used together")
    print(json.dumps(inspect(args.task_bus) if args.mode == "inspect" else recover(args),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
