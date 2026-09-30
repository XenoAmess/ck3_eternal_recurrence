"""Preflight and cautiously recover a stale Steam desktop capture on Windows.

The tool never changes Steam's mode, starts CK3, or infers offline status from
old pixels. Recovery requires an exclusive screen lease in the task bus.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
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
BUS_SOURCE = Path(__file__).with_name("codex_task_bus.py")
# No authority issuer/provenance contract or continuous screen fence is approved.
# A frozen issuer contract and long-lived fence are both needed before changing
# this stop value; the heartbeat below is only a point-in-time ownership check.
APPROVED_RECOVERY_CONTRACT_SHA256: str | None = None
RECOVERY_MARKER_NAME = "desktop-steam-recovery-authorization.json"
UNSAFE_MARKER_NAME = "unsafe-cleanup.json"
MARKER_SCHEMA = "ck3.desktop_steam_recovery_authorization.v1"
BUS_SCHEMA = "codex.task_bus.v1"
RECORDER_NAMES = {"ffmpeg.exe", "obs64.exe", "obs32.exe", "obs.exe"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def task_bus_tasks(bus: Path) -> list[dict]:
    bus = bus.resolve(strict=True)
    bus_dir = bus.parent.parent
    if (not bus.is_file() or not (bus_dir / "tasks").is_dir()
            or not (bus_dir / ".lock").is_file()
            or (bus_dir / ".lock").stat().st_size == 0):
        raise RuntimeError("existing task bus is unavailable")
    result = subprocess.run([sys.executable, str(bus), "--bus-dir",
                             str(bus_dir), "list"],
                            capture_output=True, text=True, timeout=15, check=True)
    payload = json.loads(result.stdout)
    if payload.get("ok") is not True or not isinstance(payload.get("tasks"), list):
        raise RuntimeError("task bus list did not return a valid task set")
    return payload["tasks"]


def screen_owners(tasks: list[dict]) -> list[str]:
    """Treat every unreleased screen record as occupied, including stale/done."""
    owners = []
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("resources"), list):
            raise RuntimeError("task bus contains an invalid task snapshot")
        if SCREEN_RESOURCE in task["resources"]:
            if not isinstance(task.get("task_id"), str):
                raise RuntimeError("screen owner has no task ID")
            owners.append(task["task_id"])
    return sorted(owners)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def recovery_authorization(args: argparse.Namespace) -> dict:
    """Validate the frozen, attempt-specific marker without touching the bus."""
    required = ("state_dir", "recovery_marker", "recovery_marker_sha256",
                "expected_cli_sha256", "expected_sequence")
    if any(getattr(args, name, None) is None for name in required):
        raise RuntimeError("recovery requires state dir, marker, CLI SHA and sequence pins")
    if type(args.expected_sequence) is not int or args.expected_sequence <= 0:
        raise RuntimeError("recovery expected sequence is invalid")
    if any(type(value) is not str
           or re.fullmatch(r"[A-F0-9]{64}", value) is None for value in
           (args.expected_cli_sha256, args.recovery_marker_sha256)):
        raise RuntimeError("recovery SHA pins must be uppercase SHA-256")
    state_dir = args.state_dir.resolve(strict=True)
    control = state_dir / "control"
    marker = args.recovery_marker.resolve(strict=True)
    if (not control.is_dir() or args.recovery_marker.is_symlink()
            or marker != control / RECOVERY_MARKER_NAME):
        raise RuntimeError("recovery marker is not the exact state control file")
    if (control / UNSAFE_MARKER_NAME).exists():
        raise RuntimeError("unresolved unsafe cleanup marker blocks desktop recovery")
    if (control / "desktop-recovery-unsafe.json").exists():
        raise RuntimeError("unresolved desktop recovery marker blocks another attempt")
    if _sha256(marker) != args.recovery_marker_sha256:
        raise RuntimeError("recovery marker bytes changed")
    payload = json.loads(marker.read_text(encoding="utf-8"))
    bus = args.task_bus.resolve(strict=True)
    if bus != DEFAULT_BUS.resolve():
        raise RuntimeError("recovery task bus is not the fixed authority CLI")
    contract = APPROVED_RECOVERY_CONTRACT_SHA256
    if contract is None or re.fullmatch(r"[A-F0-9]{64}", contract) is None:
        raise RuntimeError("authoritative recovery contract is not approved")
    source = BUS_SOURCE.resolve(strict=True)
    if (bus.name != "codex_task_bus.py" or bus.parent.name != "bin"
            or _sha256(bus) != args.expected_cli_sha256
            or _sha256(source) != args.expected_cli_sha256):
        raise RuntimeError("task bus source or installed CLI SHA differs from pin")
    expected = {
        "schema": MARKER_SCHEMA,
        "purpose": "steam_offline_desktop_recovery",
        "task_id": args.task_id,
        "state_dir": str(state_dir),
        "output_dir": str(args.output_dir.resolve()),
        "task_bus": str(bus),
        "bus_cli_sha256": args.expected_cli_sha256,
        "expected_sequence": args.expected_sequence,
        "authority_contract_sha256": contract,
    }
    if not isinstance(payload, dict) or any(payload.get(key) != value
                                                for key, value in expected.items()):
        raise RuntimeError("recovery marker does not bind this exact attempt")
    expiry = datetime.fromisoformat(str(payload.get("expires_at_utc", "")))
    if expiry.tzinfo is None or not (0 < (expiry.astimezone(timezone.utc)
                                        - datetime.now(timezone.utc)).total_seconds() <= 600):
        raise RuntimeError("recovery marker is expired or too far in the future")
    return {"marker_sha256": args.recovery_marker_sha256,
            "cli_sha256": args.expected_cli_sha256,
            "sequence": args.expected_sequence,
            "state_dir": state_dir,
            "bus_path": bus,
            "bus_dir": bus.parent.parent}


def _readback_screen_heartbeat(args: argparse.Namespace, lease: dict,
                               result: dict) -> None:
    task, event = result.get("task"), result.get("event")
    sequence = event.get("sequence") if isinstance(event, dict) else None
    if (result.get("schema") != BUS_SCHEMA or result.get("ok") is not True
            or not isinstance(task, dict) or not isinstance(event, dict)
            or type(sequence) is not int or sequence <= lease["sequence"]
            or task.get("task_id") != args.task_id
            or task.get("state") != "running"
            or task.get("resources") != [SCREEN_RESOURCE]
            or task.get("last_sequence") != sequence
            or event.get("task_id") != args.task_id
            or event.get("kind") != "heartbeat"):
        raise RuntimeError("screen heartbeat returned an invalid CAS receipt")
    tasks = task_bus_tasks(lease["bus_path"])
    if screen_owners(tasks) != [args.task_id]:
        raise RuntimeError("screen owner changed after heartbeat")
    matching = [row for row in tasks if row.get("task_id") == args.task_id]
    if len(matching) != 1 or any(matching[0].get(key) != task.get(key) for key in
                                 ("state", "resources", "last_sequence", "updated_at_utc")):
        raise RuntimeError("screen task readback differs from CAS receipt")
    bus_dir = lease["bus_dir"]
    events = [json.loads(line) for line in (bus_dir / "events.jsonl")
              .read_text(encoding="utf-8").splitlines() if line.strip()]
    sequences = [row.get("sequence") for row in events]
    tail = int((bus_dir / "sequence.txt").read_text(encoding="ascii").strip())
    if (not sequences or len(sequences) != tail
            or any(value != index for index, value in enumerate(sequences, 1))
            or len([row for row in events if row == event]) != 1
            or any(row.get("task_id") == args.task_id
                   and row.get("sequence", 0) > sequence for row in events)):
        raise RuntimeError("screen heartbeat event ledger readback differs")
    lease["sequence"] = sequence


def require_exclusive_screen(args: argparse.Namespace, lease: dict) -> None:
    """Renew the unique owner with a pinned CAS before each desktop mutation."""
    checked = recovery_authorization(args)
    if checked["marker_sha256"] != lease["marker_sha256"]:
        raise RuntimeError("recovery authorization changed")
    if ck3_pids():
        raise RuntimeError("CK3 started during recovery")
    command = [sys.executable, str(BUS_SOURCE), "--bus-dir",
               str(lease["bus_dir"]), "--expected-cli-sha256",
               lease["cli_sha256"], "heartbeat", "--task", args.task_id,
               "--expected-sequence", str(lease["sequence"])]
    completed = subprocess.run(command, capture_output=True, text=True,
                               timeout=15, check=False)
    if completed.returncode != 0:
        raise RuntimeError("screen heartbeat CAS rejected; stop without retry")
    _readback_screen_heartbeat(args, lease, json.loads(completed.stdout))
    recovery_authorization(args)
    if ck3_pids():
        raise RuntimeError("CK3 started after screen heartbeat")


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
        owners = screen_owners(tasks)
        stale_records = sorted(task["task_id"] for task in tasks
                               if task.get("stale", False)
                               and SCREEN_RESOURCE in task.get("resources", []))
        bus_error = None
    except (KeyError, TypeError, OSError, ValueError, RuntimeError,
            subprocess.SubprocessError) as exc:
        tasks = []
        owners = []
        stale_records = []
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
        "screen_owners": owners,
        "stale_screen_records": stale_records,
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
        lease = recovery_authorization(args)
        authorization_error = None
    except (OSError, ValueError, RuntimeError) as exc:
        lease = None
        authorization_error = f"{type(exc).__name__}: {exc}"
    try:
        tasks = task_bus_tasks(lease["bus_path"] if lease is not None else args.task_bus)
        bus_error = None
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        tasks = []
        bus_error = type(exc).__name__
    windows = steam_offline_fresh_frame._steam_windows()
    try:
        blockers = preflight(tasks, args.task_id, ck3_pids(), service_state(), windows)
    except (KeyError, TypeError, ValueError, RuntimeError):
        blockers = ["task_bus_screen_snapshot_invalid"]
    if authorization_error:
        blockers.append("recovery_authorization_invalid")
    if bus_error:
        blockers.append("task_bus_unavailable")
    if blockers:
        outcome = "blocked"
        record("blocked", reasons=blockers, authorization_error=authorization_error)
        fresh_frame = None
    else:
        hwnd, steam_pid = windows[0]
        outcome = "unverified"
        fresh_frame = None
        try:
            require_exclusive_screen(args, lease)
            service_before = service_state()
            ensure_service_running(args.service_timeout_seconds)
            if service_before["status"] == "stopped":
                record("todesk_started", state=service_state())
            for attempt in (1, 2):
                require_exclusive_screen(args, lease)
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
                    require_exclusive_screen(args, lease)
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
    recovery.add_argument("--state-dir", type=Path, required=True)
    recovery.add_argument("--recovery-marker", type=Path, required=True)
    recovery.add_argument("--recovery-marker-sha256", required=True)
    recovery.add_argument("--expected-cli-sha256", required=True)
    recovery.add_argument("--expected-sequence", type=int, required=True)
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
