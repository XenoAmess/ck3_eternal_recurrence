"""Detached, authenticated CK3 cleanup guard for the autonomous player."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import win32api
import win32com.client
import win32con
import win32event
import win32process

try:
    from .environment import (
        _is_access_denied,
        _toolhelp_ck3_processes,
        _toolhelp_process_identity,
    )
except ImportError:  # Direct execution by the detached watchdog launcher.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from xar_autoplayer.environment import (  # type: ignore[no-redef]
        _is_access_denied,
        _toolhelp_ck3_processes,
        _toolhelp_process_identity,
    )


EXACT_PROCESS_DRAIN_MS = 20_000
FALLBACK_CLEANUP_SECONDS = 45


def _write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def _normalized(path: object) -> str:
    return os.path.normcase(os.path.abspath(str(path or "")))


def _query_process(service: object, pid: int) -> object | None:
    try:
        rows = service.ExecQuery(
            "SELECT ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate "
            f"FROM Win32_Process WHERE ProcessId={pid}"
        )
    except Exception as error:
        if not _is_access_denied(error):
            raise
        identity = _toolhelp_process_identity(pid)
        return _identity_namespace(identity) if identity is not None else None
    return next(iter(rows), None)


def _identity_namespace(identity: dict[str, object]) -> object:
    return SimpleNamespace(
        ProcessId=int(identity["pid"]),
        ParentProcessId=int(identity["parent_pid"]),
        Name=str(identity["name"]),
        ExecutablePath=str(identity["executable"]),
        CreationDate=str(identity["creation_date"]),
    )


def _matches(
    process: object,
    expected_pid: int,
    parent_pid: int,
    executable: str,
    creation_date: str,
) -> bool:
    return (
        int(process.ProcessId) == expected_pid
        and int(process.ParentProcessId) == parent_pid
        and str(process.Name).casefold() == "ck3.exe"
        and (
            not str(process.ExecutablePath or "")
            or _normalized(process.ExecutablePath) == _normalized(executable)
        )
        and str(process.CreationDate) == creation_date
    )


def _parent_matches(
    process: object,
    expected_pid: int,
    executable: str,
    creation_date: str,
) -> bool:
    return (
        int(process.ProcessId) == expected_pid
        and _normalized(process.ExecutablePath) == _normalized(executable)
        and str(process.CreationDate) == creation_date
    )


def _fallback_children(
    service: object, parent_pid: int, executable: str
) -> list[tuple[int, str]]:
    try:
        rows = service.ExecQuery(
            "SELECT ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate "
            "FROM Win32_Process "
            f"WHERE ParentProcessId={parent_pid} AND Name='ck3.exe'"
        )
    except Exception as error:
        if not _is_access_denied(error):
            raise
        rows = [
            _identity_namespace(identity)
            for identity in _toolhelp_ck3_processes()
            if int(identity["parent_pid"]) == parent_pid
        ]
    children: list[tuple[int, str]] = []
    ambiguous: list[tuple[int, str]] = []
    for row in rows:
        actual = str(row.ExecutablePath or "")
        if actual and _normalized(actual) != _normalized(executable):
            ambiguous.append((int(row.ProcessId), actual))
        else:
            children.append((int(row.ProcessId), str(row.CreationDate)))
    if ambiguous:
        raise RuntimeError(
            f"same-parent ck3.exe identity is ambiguous: {ambiguous!r}"
        )
    return sorted(children)


def _terminate_authenticated(
    service: object,
    pid: int,
    parent_pid: int,
    executable: str,
    creation_date: str,
) -> str | None:
    """Terminate only the process object pinned by an authenticated handle."""
    try:
        handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE
            | win32con.SYNCHRONIZE
            | win32con.PROCESS_QUERY_INFORMATION
            | win32con.PROCESS_QUERY_LIMITED_INFORMATION
            | win32con.PROCESS_VM_READ,
            False,
            pid,
        )
    except Exception as error:
        try:
            if _query_process(service, pid) is None:
                return None
        except Exception as verify_error:
            return f"open:{pid}:{error};verify:{verify_error}"
        return f"open:{pid}:{error}"
    try:
        if win32event.WaitForSingleObject(handle, 0) == win32event.WAIT_OBJECT_0:
            return None
        process = _query_process(service, pid)
        if process is None:
            if (
                win32event.WaitForSingleObject(handle, EXACT_PROCESS_DRAIN_MS)
                == win32event.WAIT_OBJECT_0
            ):
                return None
            return f"identity:{pid}:WMI row disappeared while handle remained active"
        if not _matches(process, pid, parent_pid, executable, creation_date):
            return None
        pinned_image = win32process.GetModuleFileNameEx(handle, 0)
        if _normalized(pinned_image) != _normalized(executable):
            return f"image:{pid}:pinned executable differs"
        win32api.TerminateProcess(handle, 1)
        result = win32event.WaitForSingleObject(handle, EXACT_PROCESS_DRAIN_MS)
        if result != win32event.WAIT_OBJECT_0:
            return f"terminate:{pid}:wait-status-{result}"
        return None
    except Exception as error:
        # A kill-on-close Job can win the race after identity validation.  The
        # pinned kernel handle, unlike the numeric PID, proves whether that
        # exact process object has exited.  CK3 can remain in the terminating
        # state for several seconds after TerminateProcess starts returning
        # ERROR_ACCESS_DENIED, so use the same 20-second bound as the outer
        # verifier instead of treating a one-second drain as a cleanup error.
        try:
            if (
                win32event.WaitForSingleObject(handle, EXACT_PROCESS_DRAIN_MS)
                == win32event.WAIT_OBJECT_0
            ):
                return None
        except Exception as wait_error:
            return f"terminate:{pid}:{error};wait:{wait_error}"
        return f"terminate:{pid}:{error}"
    finally:
        win32api.CloseHandle(handle)


def _unlink_if_owned(path: Path, nonce: str) -> bool:
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict) or payload.get("nonce") != nonce:
        return False
    path.unlink(missing_ok=True)
    return True


def main() -> int:
    if len(sys.argv) not in {9, 10}:
        return 2
    parent_pid = int(sys.argv[1])
    parent_executable = sys.argv[2]
    parent_creation_date = sys.argv[3]
    nonce = sys.argv[4]
    ready_path = Path(sys.argv[5])
    record_path = Path(sys.argv[6])
    unsafe_marker = Path(sys.argv[7])
    expected_executable = sys.argv[8]
    final_evidence = Path(sys.argv[9]) if len(sys.argv) == 10 else None
    error_path = record_path.with_suffix(".watchdog_error")

    def write_final(ok: bool, stage: str, **details: object) -> None:
        if final_evidence is None:
            return
        _write_json_atomic(
            final_evidence,
            {
                "format_version": 1,
                "nonce": nonce,
                "parent_pid": parent_pid,
                "ok": ok,
                "stage": stage,
                **details,
            },
        )

    try:
        parent_handle = win32api.OpenProcess(
            win32con.SYNCHRONIZE | win32con.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            parent_pid,
        )
        service = win32com.client.GetObject("winmgmts:")
        parent = _query_process(service, parent_pid)
        watchdog_process = _query_process(service, os.getpid())
        if parent is None or not _parent_matches(
            parent, parent_pid, parent_executable, parent_creation_date
        ):
            raise RuntimeError(f"parent identity differs: {parent!r}")
        if watchdog_process is None:
            raise RuntimeError("watchdog identity disappeared during bootstrap")
        watchdog_creation_date = str(watchdog_process.CreationDate)
        _write_json_atomic(
            ready_path,
            {
                "nonce": nonce,
                "parent_pid": parent_pid,
                "parent_executable": parent_executable,
                "parent_creation_date": parent_creation_date,
                "watchdog_pid": os.getpid(),
            },
        )
        wait_result = win32event.WaitForSingleObject(
            parent_handle, win32event.INFINITE
        )
        if wait_result != win32event.WAIT_OBJECT_0:
            raise RuntimeError(f"parent wait returned status {wait_result}")
    except Exception as error:
        error_path.write_text(f"bootstrap:{error}\n", encoding="utf-8")
        try:
            write_final(False, "bootstrap", errors=[str(error)])
        except OSError:
            pass
        return 1

    failures: list[str] = []
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        record = {}

    candidates: list[tuple[int, str]] = []
    try:
        recorded_pid = int(record.get("ck3_pid"))
        recorded_parent = int(record.get("parent_pid"))
        recorded_nonce = str(record.get("nonce", ""))
        recorded_executable = str(record.get("executable", ""))
        creation_date = str(record.get("creation_date", ""))
        process = _query_process(service, recorded_pid)
        if (
            recorded_nonce == nonce
            and recorded_parent == parent_pid
            and _normalized(recorded_executable) == _normalized(expected_executable)
            and process is not None
            and _matches(
                process,
                recorded_pid,
                parent_pid,
                expected_executable,
                creation_date,
            )
        ):
            candidates.append((recorded_pid, creation_date))
    except Exception:
        pass

    for ck3_pid, creation_date in sorted(set(candidates)):
        failure = _terminate_authenticated(
            service,
            ck3_pid,
            parent_pid,
            expected_executable,
            creation_date,
        )
        if failure is not None:
            failures.append(failure)

    # A crash can occur immediately after CreateProcess and before the launch
    # record is durable. Poll to a stable empty window so a briefly delayed WMI
    # row cannot be mistaken for successful cleanup. The CK3 process is created
    # suspended and cannot spawn descendants before Job assignment.
    quiet_since: float | None = None
    poll_count = 0
    deadline = time.monotonic() + FALLBACK_CLEANUP_SECONDS
    while not failures and time.monotonic() < deadline:
        poll_count += 1
        try:
            children = _fallback_children(
                service, parent_pid, expected_executable
            )
        except Exception as error:
            failures.append(f"fallback:{error}")
            break
        if children:
            quiet_since = None
            for ck3_pid, creation_date in children:
                failure = _terminate_authenticated(
                    service,
                    ck3_pid,
                    parent_pid,
                    expected_executable,
                    creation_date,
                )
                if failure is not None:
                    failures.append(failure)
        else:
            if quiet_since is None:
                quiet_since = time.monotonic()
            elif time.monotonic() - quiet_since >= 5:
                break
        time.sleep(0.1)
    else:
        if not failures:
            failures.append("fallback:CK3 children did not reach a stable empty window")

    if failures:
        error_path.write_text(";".join(failures) + "\n", encoding="utf-8")
        try:
            write_final(
                False,
                "cleanup",
                authenticated_candidates=[pid for pid, _ in candidates],
                errors=failures,
            )
        except OSError:
            pass
        return 1
    # Fixed control names are removed before the marker. A later generation is
    # blocked until that final, nonce-checked unlink, so this watcher cannot
    # erase its successor's files.
    _unlink_if_owned(record_path, nonce)
    ready_path.unlink(missing_ok=True)
    error_path.unlink(missing_ok=True)
    if not _unlink_if_owned(unsafe_marker, nonce):
        error_path.write_text("marker:ownership-lost\n", encoding="utf-8")
        try:
            write_final(False, "control_cleanup", errors=["marker:ownership-lost"])
        except OSError:
            pass
        return 1
    try:
        measured_quiet = (
            max(0.0, time.monotonic() - quiet_since)
            if quiet_since is not None
            else 0.0
        )
        write_final(
            True,
            "complete",
            parent_executable=parent_executable,
            parent_creation_date=parent_creation_date,
            watchdog_pid=os.getpid(),
            watchdog_creation_date=watchdog_creation_date,
            expected_ck3_executable=expected_executable,
            parent_termination_observed=True,
            authenticated_candidates=[pid for pid, _ in candidates],
            measured_stable_empty_seconds=round(measured_quiet, 3),
            empty_poll_count=poll_count,
            control_files_removed=True,
        )
    except OSError as error:
        error_path.write_text(f"final-evidence:{error}\n", encoding="utf-8")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
