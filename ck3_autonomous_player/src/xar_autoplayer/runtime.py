"""Tracked non-debug CK3 launch and visible main-menu attestation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import gzip
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import uuid
from pathlib import Path

from .environment import (
    EXPECTED_MOD_NAME,
    OUTER_DESCRIPTOR_REF,
    EnvironmentSpec,
    ck3_process_inventory,
    ck3_processes,
    doctor,
    ensure_state_path_safe,
    is_relative_to,
    mod_source_fingerprint,
    snapshot_digest,
    tree_snapshot,
    verify_profile,
    write_json_atomic,
    write_text_atomic,
)
from .errors import AgentError, UnsafeCleanupError
from .integrity import protected_snapshot, verify_protected_unchanged
from .locking import exclusive_launch_lock, exclusive_state_lock


MAIN_MENU_REGION = (0.18, 0.28, 0.30, 0.50)
EXPECTED_RESOLUTION = (2560, 1440)
PROCESS_WATCHDOG = Path(__file__).with_name("process_watchdog.py")


@dataclass
class SessionHandle:
    process: object
    pid_file: Path
    watchdog_pid: int
    command: list[str]
    log_epoch_ns: int
    cleared_logs: list[str]
    nonce: str
    record_file: Path
    ready_file: Path
    unsafe_marker: Path
    ck3_creation_date: str
    watchdog_creation_date: str
    job_handle: object | None
    pre_resume_inventory: dict[str, object] | None = None


class _SuspendedWindowsProcess:
    """Minimal Popen-like wrapper retaining the exact Windows process handle."""

    def __init__(
        self,
        process_handle: object,
        thread_handle: object,
        pid: int,
        command: list[str],
    ) -> None:
        self._process_handle = process_handle
        self._thread_handle = thread_handle
        self.pid = pid
        self.args = command
        self.returncode: int | None = None
        self.resumed = False

    def resume(self) -> None:
        import win32api
        import win32process

        previous_count = int(win32process.ResumeThread(self._thread_handle))
        if previous_count != 1:
            raise AgentError(
                f"new CK3 primary thread had unexpected suspend count {previous_count}"
            )
        self.resumed = True
        win32api.CloseHandle(self._thread_handle)
        self._thread_handle = None

    def poll(self) -> int | None:
        import win32con
        import win32process

        if self.returncode is not None:
            return self.returncode
        result = int(win32process.GetExitCodeProcess(self._process_handle))
        if result == win32con.STILL_ACTIVE:
            return None
        self.returncode = result
        return result

    def wait(self, timeout: float | None = None) -> int:
        import win32event
        import win32process

        milliseconds = (
            win32event.INFINITE
            if timeout is None
            else max(0, min(0xFFFFFFFE, int(timeout * 1000)))
        )
        result = win32event.WaitForSingleObject(self._process_handle, milliseconds)
        if result == win32event.WAIT_TIMEOUT:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if result != win32event.WAIT_OBJECT_0:
            raise AgentError(f"waiting for CK3 returned unexpected status {result}")
        self.returncode = int(win32process.GetExitCodeProcess(self._process_handle))
        return self.returncode

    def terminate_exact(self) -> None:
        import win32api

        if self.poll() is None:
            win32api.TerminateProcess(self._process_handle, 1)

    def image_path(self) -> Path:
        import win32process

        return Path(win32process.GetModuleFileNameEx(self._process_handle, 0)).resolve()

    def close(self) -> None:
        import win32api

        if self._thread_handle is not None:
            win32api.CloseHandle(self._thread_handle)
            self._thread_handle = None
        if self._process_handle is not None:
            win32api.CloseHandle(self._process_handle)
            self._process_handle = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    print(f"[xar-autoplayer {time.strftime('%H:%M:%S')}] {message}", file=sys.stderr, flush=True)


def append_event(path: Path, event: dict[str, object]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: str | None = None
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines:
            prior = json.loads(lines[-1])
            previous = prior.get("event_sha256")
            if not isinstance(previous, str):
                raise AgentError("event log tail lacks its hash-chain digest")
    payload = {"at": utc_now(), "previous_event_sha256": previous, **event}
    payload["event_sha256"] = snapshot_digest(payload)
    with path.open("a", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    return str(payload["event_sha256"])


def validate_event_chain(path: Path) -> dict[str, object]:
    previous: str | None = None
    count = 0
    tail: dict[str, object] | None = None
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise AgentError(
                f"event chain line {line_number} is invalid JSON"
            ) from error
        if not isinstance(event, dict):
            raise AgentError(f"event chain line {line_number} is not an object")
        recorded = event.get("event_sha256")
        unsigned = dict(event)
        unsigned.pop("event_sha256", None)
        if recorded != snapshot_digest(unsigned):
            raise AgentError(f"event chain line {line_number} digest differs")
        if event.get("previous_event_sha256") != previous:
            raise AgentError(f"event chain line {line_number} previous link differs")
        previous = str(recorded)
        tail = event
        count += 1
    if tail is None:
        raise AgentError("event chain is empty")
    return {"event_count": count, "tail_sha256": previous, "tail": tail}


def validate_final_report_payload(
    report: dict[str, object], chain: dict[str, object]
) -> None:
    tail = chain.get("tail")
    if not isinstance(tail, dict) or tail.get("kind") != "smoke_finished":
        raise AgentError("event chain does not end with smoke_finished")
    if report.get("finalized") is not True:
        raise AgentError("final report payload is not finalized")
    if report.get("final_event_sha256") != chain.get("tail_sha256"):
        raise AgentError("final report does not bind the event-chain tail")
    if report.get("ok") is not tail.get("ok"):
        raise AgentError("final report result differs from its final event")


def validate_smoke_report(run_dir: Path) -> dict[str, object]:
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise AgentError("smoke report root is not an object")
    chain = validate_event_chain(run_dir / "events.jsonl")
    validate_final_report_payload(report, chain)
    return report


def write_gzip_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as output:
        json.dump(payload, output, ensure_ascii=False, separators=(",", ":"))
        output.write("\n")
    os.replace(temporary, path)


def _pid_running(pid: int) -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        timeout=15,
    )
    return any(f'"{pid}"' in line for line in result.stdout.splitlines())


def _process_identity(pid: int) -> dict[str, object] | None:
    if os.name != "nt":
        return None
    import win32com.client

    service = win32com.client.GetObject("winmgmts:")
    rows = service.ExecQuery(
        "SELECT ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate,CommandLine "
        f"FROM Win32_Process WHERE ProcessId={pid}"
    )
    row = next(iter(rows), None)
    if row is None:
        return None
    return {
        "pid": int(row.ProcessId),
        "parent_pid": int(row.ParentProcessId),
        "name": str(row.Name),
        "executable": str(row.ExecutablePath or ""),
        "creation_date": str(row.CreationDate),
        "command_line": str(row.CommandLine or ""),
    }


def _same_executable(first: object, second: object) -> bool:
    return os.path.normcase(os.path.abspath(str(first))) == os.path.normcase(
        os.path.abspath(str(second))
    )


def _authenticated_pid_running(
    pid: int, executable: Path, creation_date: str
) -> bool:
    try:
        identity = _process_identity(pid)
    except Exception:
        return False
    return bool(
        identity
        and _same_executable(identity["executable"], executable)
        and identity["creation_date"] == creation_date
    )


def _authenticated_watchdog_running(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> bool:
    return (
        _authenticated_watchdog_state(
            pid, creation_date, parent_pid, nonce
        )
        == "running"
    )


def _authenticated_watchdog_state(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> str:
    try:
        identity = _process_identity(pid)
    except Exception:
        return "unknown"
    if identity is None or identity["creation_date"] != creation_date:
        return "absent"
    command = str(identity["command_line"]).casefold()
    matches = (
        str(identity["name"]).casefold() in {"python.exe", "pythonw.exe"}
        and str(PROCESS_WATCHDOG).casefold() in command
        and str(parent_pid) in command
        and nonce.casefold() in command
    )
    return "running" if matches else "unknown"


def _stop_authenticated_watchdog(
    pid: int, creation_date: str, parent_pid: int, nonce: str
) -> bool:
    """Pin the process object before the final identity check and termination."""
    import win32api
    import win32con
    import win32event

    try:
        process_handle = win32api.OpenProcess(
            win32con.PROCESS_TERMINATE
            | win32con.SYNCHRONIZE
            | win32con.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            pid,
        )
    except Exception as error:
        state = _authenticated_watchdog_state(
            pid, creation_date, parent_pid, nonce
        )
        if state == "absent":
            return False
        raise UnsafeCleanupError(
            f"authenticated watchdog PID {pid} could not be pinned: {error}"
        ) from error
    try:
        state = _authenticated_watchdog_state(pid, creation_date, parent_pid, nonce)
        if state == "unknown":
            raise UnsafeCleanupError(
                f"authenticated watchdog PID {pid} identity is unknown"
            )
        if state == "absent":
            return False
        win32api.TerminateProcess(process_handle, 1)
        result = win32event.WaitForSingleObject(process_handle, 10_000)
        if result != win32event.WAIT_OBJECT_0:
            raise AgentError(f"authenticated watchdog PID {pid} did not exit")
        return True
    finally:
        win32api.CloseHandle(process_handle)


def _start_process_watchdog(
    parent_pid: int,
    parent_executable: Path,
    parent_creation_date: str,
    nonce: str,
    ready_file: Path,
    record_file: Path,
    unsafe_marker: Path,
    game_exe: Path,
    final_evidence: Path | None = None,
) -> tuple[int, str]:
    watchdog_python = Path(sys.executable).with_name("pythonw.exe")
    if not watchdog_python.is_file():
        watchdog_python = Path(sys.executable)
    arguments = [
        str(watchdog_python),
        str(PROCESS_WATCHDOG),
        str(parent_pid),
        str(parent_executable),
        parent_creation_date,
        nonce,
        str(ready_file),
        str(record_file),
        str(unsafe_marker),
        str(game_exe),
    ]
    if final_evidence is not None:
        arguments.append(str(final_evidence))
    command = subprocess.list2cmdline(arguments)
    literal = "'" + command.replace("'", "''") + "'"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$result = Invoke-CimMethod -ClassName Win32_Process "
            f"-MethodName Create -Arguments @{{CommandLine={literal}}}; "
            "if ($result.ReturnValue -ne 0) { exit $result.ReturnValue }; "
            "$result.ProcessId",
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        timeout=15,
    )
    if result.returncode != 0:
        raise AgentError(
            f"process watchdog launch failed: rc={result.returncode}, "
            f"stderr={result.stderr.strip()!r}"
        )
    try:
        bootstrap_pid = int(result.stdout.strip().splitlines()[-1])
    except (IndexError, ValueError) as error:
        raise AgentError(
            f"process watchdog returned no PID: {result.stdout!r}"
        ) from error
    error_file = record_file.with_suffix(".watchdog_error")
    actual_pid: int | None = None
    creation_date = ""
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if error_file.is_file():
                detail = error_file.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                raise AgentError(f"process watchdog bootstrap failed: {detail}")
            if ready_file.is_file():
                ready = json.loads(ready_file.read_text(encoding="ascii"))
                if set(ready) != {
                    "nonce",
                    "parent_pid",
                    "parent_executable",
                    "parent_creation_date",
                    "watchdog_pid",
                }:
                    raise AgentError(
                        f"process watchdog ready fields differ: {ready!r}"
                    )
                if (
                    ready.get("nonce") != nonce
                    or ready.get("parent_pid") != parent_pid
                    or not _same_executable(
                        ready.get("parent_executable"), parent_executable
                    )
                    or ready.get("parent_creation_date") != parent_creation_date
                ):
                    raise AgentError(
                        f"process watchdog ready identity differs: {ready!r}"
                    )
                actual_pid = int(ready["watchdog_pid"])
                identity = _process_identity(actual_pid)
                if identity is None:
                    raise AgentError(
                        f"process watchdog PID {actual_pid} disappeared after ready"
                    )
                creation_date = str(identity["creation_date"])
                if not _authenticated_watchdog_running(
                    actual_pid, creation_date, parent_pid, nonce
                ):
                    raise AgentError(
                        f"process watchdog identity differs: {identity!r}"
                    )
                return actual_pid, creation_date
            time.sleep(0.1)
        raise AgentError(
            f"process watchdog bootstrap PID {bootstrap_pid} did not become ready"
        )
    except Exception as bootstrap_error:
        candidate = actual_pid if actual_pid is not None else bootstrap_pid
        cleanup_error: Exception | None = None
        try:
            identity = _process_identity(candidate)
            if identity is not None:
                candidate_creation = str(identity["creation_date"])
                _stop_authenticated_watchdog(
                    candidate, candidate_creation, parent_pid, nonce
                )
        except Exception as error:
            cleanup_error = error
        if cleanup_error is None:
            ready_file.unlink(missing_ok=True)
        else:
            try:
                error_file.write_text(
                    f"bootstrap-cleanup:{cleanup_error}\n", encoding="utf-8"
                )
            except OSError:
                pass
        detail = (
            f"; watchdog cleanup unproven: {cleanup_error}"
            if cleanup_error is not None
            else ""
        )
        raise UnsafeCleanupError(
            f"process watchdog bootstrap failed: {bootstrap_error}{detail}"
        ) from bootstrap_error


def _create_kill_on_close_job(name: str | None = None) -> object:
    import win32api
    import win32job
    import winerror

    win32api.SetLastError(0)
    job = win32job.CreateJobObject(None, name or "")
    create_error = win32api.GetLastError()
    if name and create_error == winerror.ERROR_ALREADY_EXISTS:
        win32api.CloseHandle(job)
        raise AgentError(f"named Job already exists: {name}")
    try:
        limits = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation
        )
        limits["BasicLimitInformation"]["LimitFlags"] |= (
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        win32job.SetInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation, limits
        )
    except Exception:
        win32api.CloseHandle(job)
        raise
    return job


def _create_suspended_process(
    command: list[str], working_directory: Path
) -> _SuspendedWindowsProcess:
    import win32process

    startup = win32process.STARTUPINFO()
    process_handle, thread_handle, pid, _thread_id = win32process.CreateProcess(
        command[0],
        subprocess.list2cmdline(command),
        None,
        None,
        False,
        win32process.CREATE_SUSPENDED,
        None,
        str(working_directory),
        startup,
    )
    return _SuspendedWindowsProcess(
        process_handle, thread_handle, int(pid), command
    )


def _assign_process_to_job(
    job_handle: object, process: _SuspendedWindowsProcess
) -> None:
    import win32job

    win32job.AssignProcessToJobObject(job_handle, process._process_handle)


def _wait_process_identity(pid: int, timeout: float = 5) -> dict[str, object] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        identity = _process_identity(pid)
        if identity is not None:
            return identity
        time.sleep(0.05)
    return None


def _job_active_processes(job_handle: object | None) -> int | None:
    if job_handle is None:
        return None
    import win32job

    details = win32job.QueryInformationJobObject(
        job_handle, win32job.JobObjectBasicAccountingInformation
    )
    return int(details["ActiveProcesses"])


def _terminate_job(job_handle: object) -> None:
    import win32job

    win32job.TerminateJobObject(job_handle, 1)


def _close_job(job_handle: object | None) -> None:
    if job_handle is None:
        return
    import win32api

    win32api.CloseHandle(job_handle)


def _clear_isolated_runtime_logs(spec: EnvironmentSpec) -> tuple[int, list[str]]:
    log_root = (spec.profile_dir / "logs").resolve()
    if not is_relative_to(log_root, spec.profile_dir.resolve()):
        raise AgentError(f"isolated log directory escaped profile: {log_root}")
    log_root.mkdir(parents=True, exist_ok=True)
    cleared: list[str] = []
    for name in ("debug.log", "error.log", "gui_warnings.log"):
        path = log_root / name
        if path.exists():
            path.unlink()
            cleared.append(name)
    epoch = time.time_ns()
    for name in ("debug.log", "error.log", "gui_warnings.log"):
        if (log_root / name).exists():
            raise AgentError(f"runtime log survived prelaunch clear: {name}")
    return epoch, cleared


def launch(
    spec: EnvironmentSpec,
    *,
    watchdog_final_evidence: Path | None = None,
    job_name: str | None = None,
) -> SessionHandle:
    verify_profile(spec)
    if job_name is not None and not re.fullmatch(
        r"XarAutoplayer-Crash-[0-9a-f]{32}", job_name
    ):
        raise AgentError(f"invalid crash Job name: {job_name!r}")
    if ck3_processes():
        raise AgentError("refusing to launch while any ck3.exe is already running")
    command = [
        str(spec.game_exe),
        "-gdpr-compliant",
        f"-userdir={spec.profile_dir}",
    ]
    control = spec.state_dir / "control"
    nonce = uuid.uuid4().hex
    pid_file = control / "ck3.json"
    ready_file = control / f"watchdog-{nonce}.ready.json"
    unsafe_marker = control / "unsafe-cleanup.json"
    if unsafe_marker.is_file():
        raise AgentError(
            f"an unresolved unsafe cleanup marker blocks launch: {unsafe_marker}"
        )
    if watchdog_final_evidence is not None:
        watchdog_final_evidence = watchdog_final_evidence.resolve()
        runs_root = (spec.state_dir / "runs").resolve()
        parents = watchdog_final_evidence.parents
        if (
            len(parents) < 3
            or parents[0].name != "artifacts"
            or parents[2] != runs_root
            or not parents[1].is_dir()
        ):
            raise AgentError(
                "watchdog final evidence must be a new file under "
                "state/runs/<run-id>/artifacts"
            )
        temporary = watchdog_final_evidence.with_name(
            watchdog_final_evidence.name + ".tmp"
        )
        if watchdog_final_evidence.exists() or temporary.exists():
            raise AgentError("watchdog final evidence target already exists")
    for path in (
        pid_file,
        pid_file.with_suffix(".watchdog_error"),
        ready_file,
    ):
        path.unlink(missing_ok=True)
    log_epoch_ns, cleared_logs = _clear_isolated_runtime_logs(spec)
    parent_identity = _process_identity(os.getpid())
    if (
        parent_identity is None
        or str(parent_identity["name"]).casefold()
        not in {"python.exe", "pythonw.exe"}
        or not Path(str(parent_identity["executable"])).is_file()
    ):
        raise AgentError(
            f"supervisor process identity could not be authenticated: {parent_identity!r}"
        )
    try:
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": None,
                "reason": "watchdog bootstrap requested; CK3 launch not yet started",
            },
        )
    except Exception as error:
        raise AgentError(f"could not establish unsafe cleanup marker: {error}") from error
    try:
        watchdog_pid, watchdog_creation_date = _start_process_watchdog(
            os.getpid(),
            Path(str(parent_identity["executable"])),
            str(parent_identity["creation_date"]),
            nonce,
            ready_file,
            pid_file,
            unsafe_marker,
            spec.game_exe,
            watchdog_final_evidence,
        )
    except Exception as error:
        raise UnsafeCleanupError(
            f"watchdog bootstrap failed; unsafe marker retained: {error}"
        ) from error
    try:
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": None,
                "reason": "watchdog ready; CK3 launch not yet started",
            },
        )
    except Exception as error:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception as cleanup_error:
            raise UnsafeCleanupError(
                "unsafe marker update and watchdog cleanup both failed: "
                f"{error}; cleanup={cleanup_error}"
            ) from cleanup_error
        ready_file.unlink(missing_ok=True)
        unsafe_marker.unlink(missing_ok=True)
        raise AgentError(f"could not update unsafe cleanup marker: {error}") from error
    # Close the remaining race after the ready handshake. The global launch
    # mutex prevents another agent state from reaching this point concurrently.
    try:
        appeared = ck3_processes()
    except Exception:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception:
            raise UnsafeCleanupError(
                "CK3 inventory and watchdog cleanup both became unverifiable"
            )
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        raise
    if appeared:
        try:
            _stop_authenticated_watchdog(
                watchdog_pid, watchdog_creation_date, os.getpid(), nonce
            )
        except Exception as error:
            raise UnsafeCleanupError(
                f"CK3 appeared before launch and watchdog cleanup failed: {error}"
            ) from error
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        raise AgentError("ck3.exe appeared between preflight and launch")
    process: _SuspendedWindowsProcess | None = None
    job_handle: object | None = None
    try:
        job_handle = _create_kill_on_close_job(job_name)
        process = _create_suspended_process(command, spec.game_exe.parent)
        write_json_atomic(
            unsafe_marker,
            {
                "nonce": nonce,
                "ck3_pid": process.pid,
                "reason": "suspended launch active; removed only after authenticated tree shutdown",
            },
        )
        _assign_process_to_job(job_handle, process)
        pinned_image = process.image_path()
        identity = _wait_process_identity(process.pid)
        if (
            identity is None
            or identity["name"].casefold() != "ck3.exe"
            or int(identity["parent_pid"]) != os.getpid()
            or not _same_executable(pinned_image, spec.game_exe)
            or (
                identity["executable"]
                and not _same_executable(identity["executable"], spec.game_exe)
            )
        ):
            raise AgentError(f"launched CK3 process identity differs: {identity!r}")
        record = {
            "format_version": 1,
            "nonce": nonce,
            "ck3_pid": process.pid,
            "parent_pid": os.getpid(),
            "executable": str(spec.game_exe.resolve()),
            "creation_date": identity["creation_date"],
        }
        write_json_atomic(pid_file, record)
        pre_resume_inventory = ck3_process_inventory()
        visible = pre_resume_inventory["processes"]
        if (
            len(visible) != 1
            or int(visible[0]["pid"]) != process.pid
            or int(visible[0]["parent_pid"]) != os.getpid()
            or str(visible[0]["name"]).casefold() != "ck3.exe"
        ):
            raise AgentError(
                "pre-resume global CK3 inventory is not the exact suspended process: "
                f"{visible!r}"
            )
        process.resume()
    except Exception as error:
        # A process that has not resumed cannot have spawned descendants. Once
        # resumed, assignment to the kill-on-close Job has already succeeded.
        if process is not None:
            try:
                process.terminate_exact()
                process.wait(timeout=20)
            except Exception:
                pass
        try:
            active = _job_active_processes(job_handle)
        except Exception:
            active = -1
        process_alive = process is not None and process.poll() is None
        no_tree_proof = (
            process_alive
            or active == -1
            or (process is not None and process.resumed and active != 0)
            or (process is not None and process.resumed and job_handle is None)
        )
        if no_tree_proof:
            raise UnsafeCleanupError(
                f"CK3 launch contract failed and its job is not empty: {error}"
            ) from error
        _close_job(job_handle)
        if process is not None:
            process.close()
        _stop_authenticated_watchdog(
            watchdog_pid, watchdog_creation_date, os.getpid(), nonce
        )
        unsafe_marker.unlink(missing_ok=True)
        ready_file.unlink(missing_ok=True)
        pid_file.unlink(missing_ok=True)
        raise AgentError(f"CK3 launch contract failed safely: {error}") from error
    return SessionHandle(
        process,
        pid_file,
        watchdog_pid,
        command,
        log_epoch_ns,
        cleared_logs,
        nonce,
        pid_file,
        ready_file,
        unsafe_marker,
        str(identity["creation_date"]),
        watchdog_creation_date,
        job_handle,
        pre_resume_inventory,
    )


def stop_tracked(
    handle: SessionHandle, require_running: bool = False
) -> dict[str, object]:
    """Stop the pinned CK3 Job and return the proof required for postflight."""
    errors: list[str] = []
    try:
        record = json.loads(handle.pid_file.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        record = None
        errors.append(f"tracked CK3 PID file is unavailable: {error}")
    expected_record = {
        "format_version": 1,
        "nonce": handle.nonce,
        "ck3_pid": handle.process.pid,
        "parent_pid": os.getpid(),
        "executable": handle.command[0],
        "creation_date": handle.ck3_creation_date,
    }
    if record is not None and record != expected_record:
        errors.append(f"tracked CK3 launch record changed: {record!r}")
    watchdog_state_before = _authenticated_watchdog_state(
        handle.watchdog_pid,
        handle.watchdog_creation_date,
        os.getpid(),
        handle.nonce,
    )
    if watchdog_state_before != "running":
        errors.append(
            f"process watchdog PID {handle.watchdog_pid} state before shutdown "
            f"was {watchdog_state_before}"
        )
    running = handle.process.poll() is None
    if require_running and not running:
        errors.append(f"CK3 PID {handle.process.pid} exited before shutdown")
    try:
        active_before_termination = _job_active_processes(handle.job_handle)
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"tracked CK3 job could not be queried before termination: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"tracked CK3 job could not be queried; watchdog retained: {error}"
        ) from error
    if active_before_termination:
        try:
            _terminate_job(handle.job_handle)
        except Exception as error:
            errors.append(
                f"TerminateJobObject failed for tracked CK3 tree: {error}"
            )
    try:
        handle.process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        errors.append(f"tracked CK3 PID {handle.process.pid} did not exit")
    try:
        deadline = time.monotonic() + 20
        active = _job_active_processes(handle.job_handle)
        while active != 0 and time.monotonic() < deadline:
            time.sleep(0.1)
            active = _job_active_processes(handle.job_handle)
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"tracked CK3 job could not be queried: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"tracked CK3 job could not be queried; watchdog retained: {error}"
        ) from error
    root_process_exited = handle.process.poll() is not None
    tree_gone = root_process_exited and active == 0
    if not tree_gone:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": "tracked CK3 job did not become empty",
            },
        )
        raise UnsafeCleanupError(
            "; ".join(
                [
                    *errors,
                    f"tracked CK3 PID {handle.process.pid} or its job remains alive",
                    "detached authenticated watchdog retained",
                ]
            )
        )
    try:
        final_inventory = ck3_process_inventory()
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"final global CK3 inventory is unknown: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"final global CK3 inventory is unknown; watchdog retained: {error}"
        ) from error
    if final_inventory["processes"]:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": "a CK3 process remains after the tracked Job became empty",
            },
        )
        raise UnsafeCleanupError(
            "a CK3 process remains after the tracked Job became empty; "
            "watchdog retained"
        )
    try:
        _close_job(handle.job_handle)
        handle.job_handle = None
        if isinstance(handle.process, _SuspendedWindowsProcess):
            handle.process.close()
        _stop_authenticated_watchdog(
            handle.watchdog_pid,
            handle.watchdog_creation_date,
            os.getpid(),
            handle.nonce,
        )
        deadline = time.monotonic() + 10
        while True:
            watchdog_state_after = _authenticated_watchdog_state(
                handle.watchdog_pid,
                handle.watchdog_creation_date,
                os.getpid(),
                handle.nonce,
            )
            if watchdog_state_after != "running" or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        if watchdog_state_after != "absent":
            raise UnsafeCleanupError(
                f"watchdog exit state is {watchdog_state_after}, not absent"
            )
    except Exception as error:
        write_json_atomic(
            handle.unsafe_marker,
            {
                "nonce": handle.nonce,
                "ck3_pid": handle.process.pid,
                "reason": f"shutdown control cleanup is unproven: {error}",
            },
        )
        raise UnsafeCleanupError(
            f"shutdown control cleanup is unproven: {error}"
        ) from error
    watchdog_error = handle.pid_file.with_suffix(".watchdog_error")
    if watchdog_error.is_file():
        try:
            detail = watchdog_error.read_text(encoding="ascii").strip()
        except OSError as error:
            detail = str(error)
        errors.append(f"process watchdog reported failure: {detail}")
        watchdog_error.unlink(missing_ok=True)
    try:
        handle.pid_file.unlink(missing_ok=True)
        handle.ready_file.unlink(missing_ok=True)
        watchdog_error.unlink(missing_ok=True)
        # The marker is deliberately last: its absence authorizes a new launch.
        handle.unsafe_marker.unlink(missing_ok=True)
    except OSError as error:
        raise UnsafeCleanupError(
            f"shutdown control files could not be removed: {error}"
        ) from error
    control_absent = {
        str(path): not path.exists()
        for path in (
            handle.pid_file,
            handle.ready_file,
            watchdog_error,
            handle.unsafe_marker,
        )
    }
    if not all(control_absent.values()):
        raise UnsafeCleanupError(
            f"shutdown control files remain after cleanup: {control_absent!r}"
        )
    cleanup_proven = (
        root_process_exited
        and active == 0
        and not final_inventory["processes"]
        and watchdog_state_after == "absent"
        and all(control_absent.values())
    )
    if not cleanup_proven:
        raise UnsafeCleanupError("shutdown proof conjunction is false")
    return {
        "nonce": handle.nonce,
        "ck3_pid": handle.process.pid,
        "ck3_creation_date": handle.ck3_creation_date,
        "ck3_exit_code": handle.process.returncode,
        "job_active_processes_before_termination": active_before_termination,
        "job_active_processes_final": active,
        "tree_gone": True,
        "cleanup_proven": cleanup_proven,
        "final_ck3_inventory": final_inventory,
        "watchdog_pid": handle.watchdog_pid,
        "watchdog_creation_date": handle.watchdog_creation_date,
        "watchdog_state_before": watchdog_state_before,
        "watchdog_state_after": watchdog_state_after,
        "control_files_absent": control_absent,
        "contract_errors": errors,
        "ok": not errors,
    }


def _window_for_pid(pid: int) -> tuple[int, tuple[int, int, int, int]] | None:
    import win32gui
    import win32process

    found: list[tuple[int, tuple[int, int, int, int]]] = []

    def callback(hwnd: int, _: object) -> None:
        if not win32gui.IsWindowVisible(hwnd):
            return
        _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
        if window_pid != pid:
            return
        rect = win32gui.GetWindowRect(hwnd)
        if rect[2] > rect[0] and rect[3] > rect[1]:
            found.append((hwnd, rect))

    win32gui.EnumWindows(callback, None)
    if not found:
        return None
    return max(found, key=lambda item: (item[1][2] - item[1][0]) * (item[1][3] - item[1][1]))


def _focus_window(hwnd: int) -> None:
    import ctypes
    import pyautogui
    import win32api
    import win32con
    import win32gui
    import win32process

    pyautogui.FAILSAFE = True
    if win32gui.GetForegroundWindow() == hwnd:
        return
    user32 = ctypes.windll.user32
    last_error: Exception | None = None
    for _ in range(3):
        foreground = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        foreground_thread = (
            win32process.GetWindowThreadProcessId(foreground)[0] if foreground else 0
        )
        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        attached: list[int] = []
        try:
            for thread in {foreground_thread, target_thread}:
                if thread and thread != current_thread:
                    if user32.AttachThreadInput(current_thread, thread, True):
                        attached.append(thread)
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.BringWindowToTop(hwnd)
            pyautogui.keyDown("alt")
            try:
                win32gui.SetForegroundWindow(hwnd)
            finally:
                pyautogui.keyUp("alt")
        except Exception as error:
            last_error = error
        finally:
            for thread in reversed(attached):
                user32.AttachThreadInput(current_thread, thread, False)
        if win32gui.GetForegroundWindow() == hwnd:
            return
        time.sleep(0.2)
    active = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(active) if active else ""
    detail = f": {last_error}" if last_error else ""
    raise AgentError(
        f"CK3 window could not obtain foreground; active={title!r}{detail}"
    )


def _region_bbox(size: tuple[int, int], region: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    width, height = size
    left, top, right, bottom = region
    return (
        int(width * left),
        int(height * top),
        int(width * right),
        int(height * bottom),
    )


def _ocr_items(image: object, region: tuple[float, float, float, float]) -> list[dict[str, object]]:
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    if not hasattr(_ocr_items, "engine"):
        _ocr_items.engine = RapidOCR()  # type: ignore[attr-defined]
    crop_box = _region_bbox(image.size, region)
    result, _ = _ocr_items.engine(np.asarray(image.crop(crop_box)))  # type: ignore[attr-defined]
    found: list[dict[str, object]] = []
    for box, text, score in result or []:
        score = float(score)
        if not text or score < 0.45:
            continue
        xs = [int(point[0] + crop_box[0]) for point in box]
        ys = [int(point[1] + crop_box[1]) for point in box]
        found.append(
            {
                "text": text.strip(),
                "score": round(score, 4),
                "center": [int(sum(xs) / len(xs)), int(sum(ys) / len(ys))],
                "bbox": [min(xs), min(ys), max(xs), max(ys)],
            }
        )
    return found


def normalize_ocr_text(value: object) -> str:
    """Return the canonical text used by live and replay OCR contracts."""
    normalized = unicodedata.normalize("NFKC", str(value))
    return re.sub(r"\s+", "", normalized)


def unique_exact_ocr_match(
    items: object, target: str
) -> dict[str, object] | None:
    """Return one exact canonical OCR match, rejecting zero or duplicates."""
    if not isinstance(items, list):
        return None
    normalized_target = normalize_ocr_text(target)
    matches = [
        item
        for item in items
        if isinstance(item, dict)
        and "text" in item
        and normalize_ocr_text(item["text"]) == normalized_target
    ]
    return matches[0] if len(matches) == 1 else None


def wait_for_main_menu(
    handle: SessionHandle, artifacts: Path, timeout_seconds: float = 180
) -> dict[str, object]:
    from PIL import ImageGrab

    deadline = time.monotonic() + timeout_seconds
    target = "新游戏"
    stable_evidence: list[
        tuple[object, list[dict[str, object]], list[int], str, float, int]
    ] = []
    capture_sequence = 0
    last_image = None
    last_items: list[dict[str, object]] = []
    while time.monotonic() < deadline:
        if handle.process.poll() is not None:
            raise AgentError(
                f"CK3 PID {handle.process.pid} exited during boot: "
                f"rc={handle.process.returncode}"
            )
        window = _window_for_pid(handle.process.pid)
        if window is None:
            time.sleep(1)
            continue
        hwnd, rect = window
        width, height = rect[2] - rect[0], rect[3] - rect[1]
        if (width, height) != EXPECTED_RESOLUTION:
            raise AgentError(
                f"CK3 window must be 2560x1440, got {width}x{height}: {rect}"
            )
        _focus_window(hwnd)
        last_image = ImageGrab.grab(bbox=rect, all_screens=True)
        capture_sequence += 1
        captured_at = utc_now()
        captured_monotonic = time.monotonic()
        last_items = _ocr_items(last_image, MAIN_MENU_REGION)
        if unique_exact_ocr_match(last_items, target) is not None:
            stable_evidence.append(
                (
                    last_image,
                    last_items,
                    list(rect),
                    captured_at,
                    captured_monotonic,
                    capture_sequence,
                )
            )
            if len(stable_evidence) == 2:
                artifacts.mkdir(parents=True, exist_ok=True)
                (
                    first_image,
                    first_items,
                    first_rect,
                    first_captured_at,
                    first_captured_monotonic,
                    first_sequence,
                ) = stable_evidence[0]
                (
                    second_image,
                    second_items,
                    second_rect,
                    second_captured_at,
                    second_captured_monotonic,
                    second_sequence,
                ) = stable_evidence[1]
                first_screenshot = artifacts / "main-menu-frame-1.png"
                first_ocr = artifacts / "main-menu-frame-1-ocr.json"
                screenshot = artifacts / "main-menu.png"
                crop = artifacts / "main-menu-crop.png"
                ocr_path = artifacts / "main-menu-ocr.json"
                first_image.save(first_screenshot)
                write_json_atomic(first_ocr, first_items)
                second_image.save(screenshot)
                second_image.crop(
                    _region_bbox(second_image.size, MAIN_MENU_REGION)
                ).save(crop)
                write_json_atomic(ocr_path, second_items)
                frame_evidence = [
                    {
                        "frame": 1,
                        "capture_sequence": first_sequence,
                        "captured_at": first_captured_at,
                        "captured_monotonic": first_captured_monotonic,
                        "window_rect": first_rect,
                        "screenshot": str(first_screenshot),
                        "screenshot_sha256": _file_sha256(first_screenshot),
                        "ocr": str(first_ocr),
                        "ocr_sha256": _file_sha256(first_ocr),
                        "exact_match_count": 1,
                    },
                    {
                        "frame": 2,
                        "capture_sequence": second_sequence,
                        "captured_at": second_captured_at,
                        "captured_monotonic": second_captured_monotonic,
                        "window_rect": second_rect,
                        "screenshot": str(screenshot),
                        "screenshot_sha256": _file_sha256(screenshot),
                        "ocr": str(ocr_path),
                        "ocr_sha256": _file_sha256(ocr_path),
                        "exact_match_count": 1,
                    },
                ]
                return {
                    "target": target,
                    "target_normalized": normalize_ocr_text(target),
                    "stable_frames": len(frame_evidence),
                    "stable_frame_evidence": frame_evidence,
                    "window_rect": second_rect,
                    "screenshot": str(screenshot),
                    "screenshot_sha256": _file_sha256(screenshot),
                    "ocr": str(ocr_path),
                    "ocr_sha256": _file_sha256(ocr_path),
                }
        else:
            stable_evidence.clear()
        time.sleep(0.75)
    artifacts.mkdir(parents=True, exist_ok=True)
    if last_image is not None:
        last_image.save(artifacts / "main-menu-timeout.png")
        write_json_atomic(artifacts / "main-menu-timeout-ocr.json", last_items)
    raise AgentError("OCR timeout waiting for the visible 新游戏 main-menu control")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_runtime_attestation(
    text: str,
    profile_dir: Path,
    production_dir: Path,
    game_dir: Path | None = None,
    *,
    allowed_dlc_mounts: object | None = None,
) -> dict[str, object]:
    markers = list(re.finditer(r"Log system initialized", text))
    if len(markers) != 1:
        raise AgentError(
            "fresh debug.log must contain exactly one Log system initialized "
            f"marker, got {len(markers)}"
        )
    session = text[markers[0].start() :]
    enabled_matches = list(
        re.finditer(
            r"(?m)^([^\r\n|]+)\|(mod/[^\r\n|]+)\|Enabled\s*$", session
        )
    )
    enabled = [(match.group(1), match.group(2)) for match in enabled_matches]
    expected = [(EXPECTED_MOD_NAME, OUTER_DESCRIPTOR_REF)]
    if enabled != expected:
        raise AgentError(
            "runtime enabled-mod inventory is not the exact singleton: "
            f"actual={enabled!r}, expected={expected!r}"
        )
    content_root = (profile_dir / "mod-content").resolve()
    if allowed_dlc_mounts is not None:
        if not isinstance(allowed_dlc_mounts, (list, tuple, set, frozenset)):
            raise AgentError("runtime DLC mount allowlist is malformed")
        allowed_dlc_mount_paths = {Path(str(path)).resolve() for path in allowed_dlc_mounts}
    else:
        allowed_dlc_mount_paths = (
            {
                descriptor.parent.resolve()
                for descriptor in (game_dir / "game" / "dlc").glob("*/*.dlc")
            }
            if game_dir
            else set()
        )
    isolated_mounts: list[Path] = []
    dlc_mounts: list[Path] = []
    unknown_mounts: list[Path] = []
    mount_matches = list(
        re.finditer(r"(?m)^.*Mounted Data:\s*([^\r\n]+?)\s*$", session)
    )
    for match in mount_matches:
        path = Path(match.group(1).strip()).resolve()
        if is_relative_to(path, content_root):
            isolated_mounts.append(path)
        elif path in allowed_dlc_mount_paths:
            dlc_mounts.append(path)
        else:
            unknown_mounts.append(path)
    expected_mounts = [production_dir.resolve()]
    if isolated_mounts != expected_mounts:
        raise AgentError(
            "runtime isolated mount inventory differs: "
            f"actual={[str(path) for path in isolated_mounts]!r}, "
            f"expected={[str(path) for path in expected_mounts]!r}"
        )
    if unknown_mounts:
        raise AgentError(
            "runtime contains an unclassified non-DLC mount: "
            + ", ".join(str(path) for path in unknown_mounts)
        )
    return {
        "enabled_mods": [
            {"name": name, "descriptor": descriptor} for name, descriptor in enabled
        ],
        "isolated_mod_mounts": [str(path) for path in isolated_mounts],
        "runtime_dlc_mounts": [str(path) for path in dlc_mounts],
        "unclassified_mounts": [],
        "evidence_lines": [
            *(match.group(0).rstrip("\r\n") for match in enabled_matches),
            *(match.group(0).rstrip("\r\n") for match in mount_matches),
        ],
        "session_marker_count": 1,
        "source": "fresh non-debug boot log, reduced to load attestation only",
        "policy_boundary": "not available to gameplay perception or strategy",
    }


def wait_for_runtime_attestation(
    spec: EnvironmentSpec, handle: SessionHandle, timeout_seconds: float = 30
) -> dict[str, object]:
    path = spec.profile_dir / "logs" / "debug.log"
    deadline = time.monotonic() + timeout_seconds
    last_error: AgentError | None = None
    while time.monotonic() < deadline:
        try:
            raw = path.read_bytes()
            stat = path.stat()
            if stat.st_mtime_ns < handle.log_epoch_ns:
                raise AgentError(
                    "debug.log predates the prelaunch log epoch and is stale"
                )
            text = raw.decode("utf-8", errors="ignore")
            result = parse_runtime_attestation(
                text, spec.profile_dir, spec.production_dir, spec.game_dir
            )
            result["debug_log"] = {
                "path": str(path),
                "captured_prefix_size": len(raw),
                "captured_prefix_sha256": hashlib.sha256(raw).hexdigest(),
                "file_size_after_read": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "prelaunch_epoch_ns": handle.log_epoch_ns,
                "cleared_before_launch": handle.cleared_logs,
            }
            return result
        except OSError as error:
            last_error = AgentError(f"runtime load log unavailable: {error}")
        except AgentError as error:
            last_error = error
        time.sleep(0.5)
    raise last_error or AgentError("runtime load attestation timed out")


def analyze_engine_log_bytes(
    name: str,
    raw: bytes,
    *,
    expected_mod_name: str,
    production_path: Path,
) -> dict[str, object]:
    """Pure analysis shared by the live collector and offline replay."""
    text = raw.decode("utf-8", errors="replace")
    diagnostic_records = len(re.findall(r"(?m)^.*\[[EWI]\]\[", text))
    nonempty_lines = sum(1 for line in text.splitlines() if line.strip())
    needles = (
        "xar_",
        expected_mod_name.casefold(),
        str(production_path).casefold(),
    )
    hits: list[dict[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        folded = line.casefold()
        if any(needle and needle in folded for needle in needles):
            hits.append(
                {
                    "log": name,
                    "line": line_number,
                    "sha256": hashlib.sha256(
                        line.encode("utf-8", errors="replace")
                    ).hexdigest(),
                }
            )
    return {
        "diagnostic_records": diagnostic_records,
        "nonempty_lines": nonempty_lines,
        "current_mod_diagnostic_hits": hits,
    }


def collect_engine_log_evidence(
    spec: EnvironmentSpec, handle: SessionHandle, artifacts: Path
) -> dict[str, object]:
    """Archive supervisor-only diagnostics without exposing them to policy input."""
    artifacts.mkdir(parents=True, exist_ok=True)
    result: dict[str, object] = {
        "policy_boundary": "supervisor evidence only; unavailable to gameplay policy",
        "zero_diagnostics": True,
        "current_mod_diagnostics": False,
        "current_mod_diagnostic_hits": [],
        "logs": {},
    }
    for name in ("error.log", "gui_warnings.log"):
        source = spec.profile_dir / "logs" / name
        if not source.is_file():
            result["logs"][name] = {"present": False, "diagnostic_records": 0}
            continue
        stat = source.stat()
        if stat.st_mtime_ns < handle.log_epoch_ns:
            raise AgentError(f"{name} predates this launch's fresh-log epoch")
        raw = source.read_bytes()
        destination = artifacts / f"supervisor-{name}"
        shutil.copy2(source, destination)
        analysis = analyze_engine_log_bytes(
            name,
            raw,
            expected_mod_name=EXPECTED_MOD_NAME,
            production_path=spec.production_dir,
        )
        record = {
            "present": True,
            "path": str(destination),
            "sha256": _file_sha256(destination),
            "size": len(raw),
            "mtime_ns": stat.st_mtime_ns,
            "diagnostic_records": analysis["diagnostic_records"],
            "nonempty_lines": analysis["nonempty_lines"],
        }
        result["logs"][name] = record
        if analysis["diagnostic_records"] or analysis["nonempty_lines"]:
            result["zero_diagnostics"] = False
        hits = analysis["current_mod_diagnostic_hits"]
        if hits:
            result["current_mod_diagnostics"] = True
            result["current_mod_diagnostic_hits"].extend(hits)
    return result


def smoke(spec: EnvironmentSpec, timeout_seconds: float = 180) -> dict[str, object]:
    """Hold exclusive ownership across preflight, boot, shutdown, and postflight."""
    ensure_state_path_safe(spec.state_dir)
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "smoke"):
            return _smoke_locked(spec, timeout_seconds)


def _smoke_locked(
    spec: EnvironmentSpec, timeout_seconds: float = 180
) -> dict[str, object]:
    """Boot to a visible main menu, attest one mod, and stop only our PID tree."""
    manifest = verify_profile(spec)
    doctor(spec, require_prepared=True)
    agent_git = manifest.get("agent_runtime", {}).get("git", {})
    if (
        not agent_git.get("all_files_tracked")
        or agent_git.get("dirty")
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(agent_git.get("selected_runtime_revision", ""))
        )
    ):
        raise AgentError(
            "infrastructure smoke requires a committed, clean selected agent runtime"
        )
    mod_git = mod_source_fingerprint()
    recorded_mod_git = manifest.get("mod", {}).get("source_provenance", {})
    if (
        mod_git.get("git_dirty")
        or not mod_git.get("all_release_files_tracked")
        or not re.fullmatch(r"[0-9a-f]{40}", str(mod_git.get("git_revision", "")))
        or mod_git.get("release_source_sha256")
        != recorded_mod_git.get("release_source_sha256")
    ):
        raise AgentError(
            "infrastructure smoke requires a committed, clean production mod source"
        )
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = spec.state_dir / "runs" / run_id
    artifacts = run_dir / "artifacts"
    events = run_dir / "events.jsonl"
    run_dir.mkdir(parents=True, exist_ok=False)
    log("snapshotting protected real profile, Steam userdata, and Workshop metadata")
    baseline = protected_snapshot()
    before_path = run_dir / "protected-before.json.gz"
    write_gzip_json_atomic(before_path, baseline)
    shutil.copy2(spec.manifest_path, run_dir / "environment.json")
    shutil.copy2(
        Path(str(manifest["mod"]["production_manifest"])),
        run_dir / "production.manifest.json",
    )
    append_event(
        events,
        {
            "kind": "smoke_started",
            "environment_sha256": manifest["environment_sha256"],
            "protected_storage_sha256": baseline["digest"],
            "protected_snapshot_sha256": _file_sha256(before_path),
        },
    )
    handle: SessionHandle | None = None
    report: dict[str, object] = {
        "format_version": 1,
        "run_id": run_id,
        "kind": "infrastructure_smoke",
        "acceptance_claim": "isolated_single_mod_visible_main_menu_only",
        "clean_engine_boot_required": False,
        "started_at": utc_now(),
        "valid_score_episode": False,
        "environment_sha256": manifest["environment_sha256"],
        "run_dir": str(run_dir),
        "finalized": False,
        "ok": False,
    }
    write_json_atomic(run_dir / "report.json", report)
    primary_error: Exception | None = None
    cleanup_proven = False
    try:
        log("launching tracked non-debug CK3 process")
        handle = launch(spec)
        report["process"] = {
            "pid": handle.process.pid,
            "watchdog_pid": handle.watchdog_pid,
            "arguments": handle.command,
            "debug_mode": False,
            "fresh_log_epoch_ns": handle.log_epoch_ns,
            "prelaunch_logs_removed": handle.cleared_logs,
            "pre_resume_ck3_inventory": handle.pre_resume_inventory,
        }
        append_event(events, {"kind": "ck3_launched", "pid": handle.process.pid})
        log("waiting for two stable visible main-menu OCR frames")
        report["visual_attestation"] = wait_for_main_menu(
            handle, artifacts, timeout_seconds
        )
        append_event(events, {"kind": "visible_main_menu_attested"})
        log("checking exact one-mod runtime inventory and isolated mount")
        report["load_attestation"] = wait_for_runtime_attestation(spec, handle)
        write_json_atomic(
            artifacts / "supervisor-load-attestation.json",
            report["load_attestation"],
        )
        append_event(events, {"kind": "single_mod_runtime_attested"})
    except Exception as error:
        primary_error = error
    finally:
        if handle is not None:
            try:
                log(f"stopping only tracked CK3 PID {handle.process.pid}")
                shutdown = stop_tracked(
                    handle, require_running=primary_error is None
                )
                report["shutdown_attestation"] = shutdown
                cleanup_proven = shutdown.get("cleanup_proven") is True
                append_event(events, {"kind": "tracked_process_stopped", "pid": handle.process.pid})
                if not shutdown.get("ok"):
                    shutdown_error = AgentError(
                        "shutdown contract errors: "
                        + "; ".join(str(item) for item in shutdown["contract_errors"])
                    )
                    if primary_error is None:
                        primary_error = shutdown_error
                    else:
                        report["shutdown_error"] = str(shutdown_error)
            except Exception as stop_error:
                if primary_error is None:
                    primary_error = stop_error
                else:
                    report["shutdown_error"] = str(stop_error)

    try:
        remaining_inventory = ck3_process_inventory()
        report["post_shutdown_ck3_inventory"] = remaining_inventory
        remaining_ck3 = remaining_inventory["processes"]
    except Exception as inventory_error:
        remaining_ck3 = [f"inventory unknown: {inventory_error}"]
        report["post_shutdown_ck3_inventory_error"] = str(inventory_error)
        cleanup_proven = False
    if not cleanup_proven or remaining_ck3:
        alive_error = AgentError(
            "CK3 cleanup is not proven complete; protected postflight withheld"
            + (f"; running={remaining_ck3!r}" if remaining_ck3 else "")
        )
        report["unsafe_cleanup"] = True
        if primary_error is None:
            primary_error = alive_error
        else:
            report["postflight_error"] = str(alive_error)
    else:
        try:
            if handle is not None and "load_attestation" in report:
                final_load = wait_for_runtime_attestation(spec, handle, 2)
                for key in (
                    "enabled_mods",
                    "isolated_mod_mounts",
                    "runtime_dlc_mounts",
                    "unclassified_mounts",
                    "session_marker_count",
                ):
                    if final_load[key] != report["load_attestation"][key]:
                        raise AgentError(
                            f"post-exit runtime attestation changed for {key}"
                        )
                report["load_attestation"]["post_exit_revalidated"] = True
                report["load_attestation"]["post_exit_debug_log"] = final_load[
                    "debug_log"
                ]
                write_json_atomic(
                    artifacts / "supervisor-load-attestation.json",
                    report["load_attestation"],
                )
            if handle is not None:
                report["engine_diagnostics"] = collect_engine_log_evidence(
                    spec, handle, artifacts
                )
            log("verifying protected stores return to the semantic baseline")
            after = verify_protected_unchanged(baseline)
            after_path = run_dir / "protected-after.json.gz"
            write_gzip_json_atomic(after_path, after)
            report["protected_storage"] = {
                "post_exit_matches_baseline": True,
                "continuous_quiet_seconds": 5,
                "runtime_write_absence_proven": False,
                "sha256": after["digest"],
                "before_snapshot": str(before_path),
                "before_snapshot_sha256": _file_sha256(before_path),
                "after_snapshot": str(after_path),
                "after_snapshot_sha256": _file_sha256(after_path),
                "allowed_volatile_before": baseline.get("allowed_volatile"),
                "allowed_volatile_after": after.get("allowed_volatile"),
            }
            verify_profile(spec)
            current_tree = snapshot_digest(tree_snapshot(spec.production_dir))
            if current_tree != manifest["mod"]["production_tree_sha256"]:
                raise AgentError("production projection changed during smoke")
            report["production_tree_unchanged"] = True
            if report.get("engine_diagnostics", {}).get(
                "current_mod_diagnostics"
            ):
                raise AgentError(
                    "fresh engine diagnostics reference the current production mod"
                )
        except Exception as postflight_error:
            if primary_error is None:
                primary_error = postflight_error
            else:
                report["postflight_error"] = str(postflight_error)

    report["finished_at"] = utc_now()
    candidate_ok = primary_error is None
    if primary_error is not None:
        report["error"] = str(primary_error)
    final_event_sha256 = append_event(
        events, {"kind": "smoke_finished", "ok": candidate_ok}
    )
    report["final_event_sha256"] = final_event_sha256
    report["finalized"] = True
    report["ok"] = candidate_ok
    event_chain = validate_event_chain(events)
    report["event_chain"] = {
        "event_count": event_chain["event_count"],
        "tail_sha256": event_chain["tail_sha256"],
    }
    validate_final_report_payload(report, event_chain)
    write_json_atomic(run_dir / "report.json", report)
    if primary_error is not None:
        raise AgentError(
            f"smoke failed; evidence retained at {run_dir}: {primary_error}"
        ) from primary_error
    clean = report.get("engine_diagnostics", {}).get("zero_diagnostics")
    log(
        "single-mod isolation smoke GREEN; "
        f"clean_engine_boot={clean}; evidence={run_dir}"
    )
    return report
