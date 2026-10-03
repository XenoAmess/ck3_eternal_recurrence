"""Preflight and cautiously recover a stale Steam desktop capture on Windows.

The tool never changes Steam's mode, starts CK3, or infers offline status from
old pixels. Recovery requires an exclusive screen lease in the task bus.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
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
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([sys.executable, "-X", "utf8", str(bus), "list"],
                            capture_output=True, text=False, env=environment,
                            timeout=15, check=True)
    # Decode in this thread so invalid bytes raise here instead of leaving
    # stdout as None after a subprocess reader-thread failure.
    stdout = result.stdout.decode("utf-8", errors="strict")
    result.stderr.decode("utf-8", errors="strict")
    payload = json.loads(stdout)
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


class ServiceCommandError(RuntimeError):
    def __init__(self, action: str, result: subprocess.CompletedProcess) -> None:
        super().__init__(f"sc {action} {SERVICE} failed with code {result.returncode}")
        # SC is a native Windows program: its diagnostics use the OEM code
        # page, unlike the Python task-bus child which explicitly uses UTF-8.
        # Keep exact bytes as well as readable text, including invalid bytes.
        self.command_receipt = {
            "argv": ["sc.exe", action, SERVICE], "returncode": result.returncode,
            "encoding": "oem",
            "stdout": result.stdout.decode("oem", errors="backslashreplace"),
            "stderr": result.stderr.decode("oem", errors="backslashreplace"),
            "stdout_hex": result.stdout.hex(), "stderr_hex": result.stderr.hex(),
        }


def sc(action: str, timeout_seconds: int) -> None:
    result = subprocess.run(["sc.exe", action, SERVICE], capture_output=True,
                            text=False, timeout=timeout_seconds)
    if result.returncode != 0:
        raise ServiceCommandError(action, result)


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


def require_steam_window_identity(hwnd: int, pid: int) -> None:
    if steam_offline_fresh_frame._steam_windows() != [(hwnd, pid)]:
        raise RuntimeError("selected Steam window identity changed during recovery")


def uia_set_steam_focus(hwnd: int, pid: int) -> None:
    """Focus only the selected Steam UIA root; the caller verifies foreground."""
    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise RuntimeError("UI Automation dependency is unavailable") from exc
    try:
        element = Desktop(backend="uia").window(handle=hwnd).wrapper_object().element_info.element
        if (int(element.CurrentProcessId) != pid
                or int(element.CurrentNativeWindowHandle) != hwnd):
            raise RuntimeError("UI Automation root differs from the selected Steam window")
        # Resolving the root can take time; bind the live HWND/PID again
        # immediately before the only UIA action.
        require_steam_window_identity(hwnd, pid)
        element.SetFocus()
    except Exception as exc:
        raise RuntimeError(f"UI Automation could not focus selected Steam window: {exc}") from exc


def wait_steam_foreground(hwnd: int) -> bool:
    # Windows can apply either native or UIA activation asynchronously.
    deadline = time.monotonic() + 2.0
    while win32gui.GetForegroundWindow() != hwnd:
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)
    return True


def capture_fresh_frame(output_dir: Path, hwnd: int, bring_forward: bool,
                        clock_reference: Path | None = None,
                        clock_rect: tuple[int, int, int, int] | None = None,
                        *, expected_steam_pid: int | None = None) -> dict:
    windows = steam_offline_fresh_frame._steam_windows()
    if len(windows) != 1 or windows[0][0] != hwnd:
        raise RuntimeError("selected Steam window identity changed during recovery")
    steam_pid = windows[0][1] if expected_steam_pid is None else expected_steam_pid
    require_steam_window_identity(hwnd, steam_pid)
    previous = win32gui.GetForegroundWindow()
    activation = {"method": "already_foreground", "steam_hwnd": hwnd,
                  "steam_pid": steam_pid, "previous_foreground_hwnd": previous}
    if previous != hwnd:
        if not bring_forward:
            raise RuntimeError("Steam is not foreground; pass --bring-steam-forward under the screen lease")
        win32gui.ShowWindow(
            hwnd, win32con.SW_RESTORE if win32gui.IsIconic(hwnd) else win32con.SW_SHOW
        )
        try:
            win32gui.SetForegroundWindow(hwnd)
        except pywintypes.error as exc:
            activation["native_error"] = str(exc)
        # Windows may apply SetForegroundWindow after the call returns.  A
        # single immediate read falsely rejected a healthy Steam window in
        # attempt 088, even though the next preflight saw it in front.
        if wait_steam_foreground(hwnd):
            activation["method"] = "SetForegroundWindow"
        else:
            require_steam_window_identity(hwnd, steam_pid)
            try:
                uia_set_steam_focus(hwnd, steam_pid)
            except RuntimeError as exc:
                raise RuntimeError(f"could not make Steam foreground: {exc}") from exc
            if not wait_steam_foreground(hwnd):
                raise RuntimeError("could not make Steam foreground after UI Automation SetFocus")
            activation["method"] = "IUIAutomationElement.SetFocus"
    require_steam_window_identity(hwnd, steam_pid)
    activation["verified_foreground_hwnd"] = hwnd
    receipt = None
    try:
        if clock_reference is None:
            receipt = steam_offline_fresh_frame.capture(output_dir)
        else:
            receipt = steam_offline_fresh_frame.capture(
                output_dir, clock_reference=clock_reference, clock_rect=clock_rect)
        require_steam_window_identity(hwnd, steam_pid)
        receipt["foreground_activation"] = activation
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


def reject_repeated_frame(reference_path: Path, receipt: dict,
                          probe_dir: Path) -> None:
    """Reject an identical moved desktop frame from an older probe."""
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if reference.get("schema") != "ck3.steam_fresh_desktop_frame.v1":
        raise ValueError("stale-frame reference is not a capture receipt")
    captured = datetime.fromisoformat(reference["captured_at_utc"])
    if captured.tzinfo is None or (
        datetime.now(timezone.utc) - captured.astimezone(timezone.utc)
    ).total_seconds() < 120:
        raise ValueError("stale-frame reference must be at least 120 seconds old")
    identity = reference.get("moved_identity")
    current = receipt.get("moved_identity")
    if not isinstance(identity, dict) or not isinstance(current, dict):
        raise ValueError("stale-frame comparison lacks image identities")
    if any(reference.get(key) != receipt.get(key) for key in (
        "steam_hwnd", "desktop_size", "moved_rect"
    )):
        raise ValueError("stale-frame reference has different capture geometry")
    if (identity.get("sha256") == current.get("sha256")
            and identity.get("bytes") == current.get("bytes")):
        stale = {
            "reason": "identical moved desktop frame after at least 120 seconds",
            "reference_receipt": str(reference_path),
            "reference_captured_at_utc": reference["captured_at_utc"],
            "moved_identity": current,
        }
        with (probe_dir / "steam-frame-stale.json").open(
            "x", encoding="utf-8", newline="\n"
        ) as stream:
            json.dump(stale, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        raise RuntimeError(STALE_CAPTURE_ERROR)


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
                        receipt = capture_fresh_frame(
                            probe_dir, hwnd, args.bring_steam_forward,
                            expected_steam_pid=steam_pid)
                    else:
                        receipt = capture_fresh_frame(
                            probe_dir, hwnd, args.bring_steam_forward,
                            clock_reference=clock_reference, clock_rect=tuple(clock_rect),
                            expected_steam_pid=steam_pid)
                    frame_reference = getattr(args, "stale_frame_reference", None)
                    if frame_reference is not None:
                        reject_repeated_frame(frame_reference, receipt, probe_dir)
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
            require_steam_window_identity(hwnd, steam_pid)
        except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.SubprocessError) as exc:
            outcome = "recovery_error"
            fields = {"error_type": type(exc).__name__, "error": str(exc)}
            if isinstance(exc, ServiceCommandError):
                fields["service_command"] = exc.command_receipt
            record("recovery_error", **fields)
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
    recovery.add_argument("--stale-frame-reference", type=Path,
                          help="capture receipt at least 120 seconds old; identical moved pixels are stale")
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
