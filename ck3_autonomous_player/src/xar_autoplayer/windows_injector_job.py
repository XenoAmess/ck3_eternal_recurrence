"""Bounded Windows injector process with an atomic, no-breakaway Job boundary.

This module is deliberately Windows-specific. It uses CPython's private
``_winapi.CreateProcess`` so that STARTUPINFOEX handle_list, the suspended
primary-thread handle, and the pinned process handle exist at the same time.
Any missing API or incomplete proof returns a RED result; callers must not
resume their target process after RED.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import subprocess
import threading
import time


MAX_INJECTOR_OUTPUT_BYTES = 8 * 1024 * 1024
INJECTOR_CLEANUP_SECONDS = 5.0


class _InjectorDeadlineExpired(RuntimeError):
    """The combined create, assign, run, and proof budget was exhausted."""


@dataclass
class ContainedInjectorResult:
    report: dict[str, object]
    stdout: bytes | None
    stderr: bytes | None
    error: str | None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class _BoundedPipeDrain:
    def __init__(self, handle: int, label: str, limit: int,
                 overflow: threading.Event) -> None:
        self.handle = handle
        self.label = label
        self.limit = limit
        self.overflow = overflow
        self.total = 0
        self.digest = hashlib.sha256()
        self.chunks: list[bytes] = []
        self.error: str | None = None
        self.complete = False
        self.thread = threading.Thread(target=self._read, daemon=True,
                                       name=f"xar-injector-{label}")

    def start(self) -> None:
        self.thread.start()

    def _read(self) -> None:
        import msvcrt

        raw_owned = True
        fd: int | None = None
        try:
            fd = msvcrt.open_osfhandle(self.handle, os.O_RDONLY | os.O_BINARY)
            raw_owned = False
            with os.fdopen(fd, "rb") as stream:
                fd = None
                while True:
                    block = stream.read(65536)
                    if not block:
                        break
                    self.total += len(block)
                    self.digest.update(block)
                    if self.total <= self.limit:
                        self.chunks.append(block)
                    else:
                        self.overflow.set()
            self.complete = True
        except Exception as error:
            self.error = f"{type(error).__name__}: {error}"
            self.overflow.set()
        finally:
            if fd is not None:
                os.close(fd)
            if raw_owned:
                _close_handle(self.handle)

    def finish(self, timeout: float) -> None:
        self.thread.join(timeout)
        if self.thread.is_alive():
            self.error = "pipe reader did not finish within cleanup budget"

    def captured(self) -> bytes | None:
        if not self.complete or self.error is not None or self.total > self.limit:
            return None
        return b"".join(self.chunks)

    def evidence(self) -> dict[str, object]:
        return {
            f"{self.label}_bytes": self.total,
            f"{self.label}_sha256": (
                self.digest.hexdigest().upper() if self.complete else None),
            f"{self.label}_complete": self.complete,
            f"{self.label}_overflow": self.total > self.limit,
            f"{self.label}_reader_error": self.error,
        }


def _job_state(job: object) -> tuple[int, list[int]]:
    import win32job

    accounting = win32job.QueryInformationJobObject(
        job, win32job.JobObjectBasicAccountingInformation)
    count = accounting.get("ActiveProcesses")
    pids = win32job.QueryInformationJobObject(
        job, win32job.JobObjectBasicProcessIdList)
    if (type(count) is not int or count < 0
            or not isinstance(pids, (list, tuple))
            or any(type(pid) is not int or pid <= 0 for pid in pids)):
        raise RuntimeError("injector Job state has invalid types")
    return count, list(pids)


def _verified_injector_job() -> tuple[object, int]:
    import win32api
    import win32job

    job = win32job.CreateJobObject(None, "")
    try:
        limits = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation)
        flags = (win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                 | win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS)
        limits["BasicLimitInformation"]["LimitFlags"] = flags
        limits["BasicLimitInformation"]["ActiveProcessLimit"] = 1
        win32job.SetInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation, limits)
        actual = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation)["BasicLimitInformation"]
        if (type(actual.get("LimitFlags")) is not int
                or actual["LimitFlags"] != flags
                or type(actual.get("ActiveProcessLimit")) is not int
                or actual["ActiveProcessLimit"] != 1):
            raise RuntimeError("injector Job limits differ after setting them")
        if _job_state(job) != (0, []):
            raise RuntimeError("new injector Job is not empty")
        return job, flags
    except Exception:
        win32api.CloseHandle(job)
        raise


def _close_handle(handle: int | None) -> None:
    if handle is None:
        return
    import _winapi

    try:
        _winapi.CloseHandle(handle)
    except OSError:
        pass


def _inheritable_copy(handle: int) -> int:
    import _winapi

    return _winapi.DuplicateHandle(
        _winapi.GetCurrentProcess(), handle, _winapi.GetCurrentProcess(),
        0, True, _winapi.DUPLICATE_SAME_ACCESS)


def run_contained_injector_command(
    command: list[str], *, timeout_seconds: float,
    output_limit_bytes: int = MAX_INJECTOR_OUTPUT_BYTES,
) -> ContainedInjectorResult:
    """Run one direct executable, proving a one-process Job tree before return.

    A returncode of zero is only usable when ``complete_process_tree_proven``
    is true. RED paths retain that field as false, even if a best-effort Job
    termination appears to have removed the process.
    """
    report: dict[str, object] = {
        "schema": "xar.ck3.contained-injector-job.v1",
        "status": "STARTING", "argv": list(command),
        "pid": None, "creation_utc": None,
        "pinned_executable": None, "executable_sha256": None,
        "job_limit_flags": None, "pre_resume_job_pids": None,
        "job_active_final": None, "job_pids_final": None,
        "resume_previous_count": None, "returncode": None,
        "injector_root_reaped": False,
        "complete_process_tree_proven": False,
        "stdout_sha256": None, "stderr_sha256": None,
        "stdout_bytes": None, "stderr_bytes": None,
        "stdout_complete": False, "stderr_complete": False,
        "output_limit_bytes": output_limit_bytes,
    }
    if (os.name != "nt" or not isinstance(command, list)
            or not command or any(not isinstance(arg, str) or not arg for arg in command)
            or type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0
            or type(output_limit_bytes) is not int or not 0 < output_limit_bytes <= MAX_INJECTOR_OUTPUT_BYTES):
        report["status"] = "RED_INVALID_INPUT_OR_PLATFORM"
        return ContainedInjectorResult(report, None, None, "invalid injector command/platform/budget")

    deadline = time.monotonic() + float(timeout_seconds)
    import _winapi
    import msvcrt
    import win32api
    import win32event
    import win32job
    import win32process

    executable_input = Path(command[0])
    executable = executable_input.resolve()
    job: object | None = None
    process_handle: int | None = None
    thread_handle: int | None = None
    out_read: int | None = None
    err_read: int | None = None
    raw_out_write: int | None = None
    raw_err_write: int | None = None
    out_write: int | None = None
    err_write: int | None = None
    stdin_copy: int | None = None
    out_drain: _BoundedPipeDrain | None = None
    err_drain: _BoundedPipeDrain | None = None
    assigned = False
    root_exited = False
    error_text: str | None = None
    overflow = threading.Event()

    def require_budget(stage: str) -> None:
        if time.monotonic() >= deadline:
            report["deadline_phase"] = stage
            raise _InjectorDeadlineExpired(
                f"injector deadline expired during {stage}")

    try:
        require_budget("input validation")
        if not executable_input.is_absolute() or not executable.is_file():
            raise RuntimeError("injector executable is missing or relative")
        before_sha = _sha256_file(executable)
        require_budget("executable hash")
        job, flags = _verified_injector_job()
        report["job_limit_flags"] = flags
        require_budget("Job creation")

        out_read, raw_out_write = _winapi.CreatePipe(None, 0)
        err_read, raw_err_write = _winapi.CreatePipe(None, 0)
        try:
            out_write = _inheritable_copy(raw_out_write)
            err_write = _inheritable_copy(raw_err_write)
        finally:
            _close_handle(raw_out_write)
            _close_handle(raw_err_write)
            raw_out_write = raw_err_write = None
        with open(os.devnull, "rb") as null:
            stdin_copy = _inheritable_copy(msvcrt.get_osfhandle(null.fileno()))
            startup = subprocess.STARTUPINFO(
                dwFlags=_winapi.STARTF_USESTDHANDLES,
                hStdInput=stdin_copy, hStdOutput=out_write,
                hStdError=err_write,
                lpAttributeList={"handle_list": [stdin_copy, out_write, err_write]},
            )
            require_budget("pre-CreateProcess pipe setup")
            process_handle, thread_handle, pid, _thread_id = _winapi.CreateProcess(
                str(executable), subprocess.list2cmdline(command),
                None, None, True,
                win32process.CREATE_SUSPENDED | win32process.CREATE_NO_WINDOW,
                None, str(executable.parent), startup)
        report["pid"] = pid
        require_budget("suspended CreateProcess")
        _close_handle(out_write)
        _close_handle(err_write)
        _close_handle(stdin_copy)
        out_write = err_write = stdin_copy = None

        if type(pid) is not int or pid <= 0:
            raise RuntimeError("injector pinned PID is invalid")
        created = win32process.GetProcessTimes(process_handle).get("CreationTime")
        if (not isinstance(created, datetime) or created.tzinfo is None
                or created.year < 2000):
            raise RuntimeError("injector pinned creation time is invalid")
        report["creation_utc"] = created.astimezone(timezone.utc).isoformat(
            timespec="microseconds")
        pinned_executable = Path(
            win32process.GetModuleFileNameEx(process_handle, 0)).resolve()
        report["pinned_executable"] = str(pinned_executable)
        after_sha = _sha256_file(executable)
        if not os.path.samefile(pinned_executable, executable) or after_sha != before_sha:
            raise RuntimeError("injector pinned executable/path bytes changed")
        report["executable_sha256"] = before_sha
        require_budget("pinned process identity")
        if win32event.WaitForSingleObject(process_handle, 0) != win32event.WAIT_TIMEOUT:
            raise RuntimeError("injector exited before Job assignment")
        if _job_state(job) != (0, []):
            raise RuntimeError("injector Job changed before assignment")
        win32job.AssignProcessToJobObject(job, process_handle)
        assigned = True
        require_budget("Job assignment")
        count, pids = _job_state(job)
        report["pre_resume_job_pids"] = pids
        if not win32job.IsProcessInJob(process_handle, job) or count != 1 or pids != [pid]:
            raise RuntimeError("injector Job assignment is not exact before resume")
        require_budget("pre-resume Job proof")

        out_drain = _BoundedPipeDrain(out_read, "stdout", output_limit_bytes, overflow)
        err_drain = _BoundedPipeDrain(err_read, "stderr", output_limit_bytes, overflow)
        out_drain.start()
        out_read = None
        err_drain.start()
        err_read = None
        require_budget("output pipe setup")
        previous = int(win32process.ResumeThread(thread_handle))
        report["resume_previous_count"] = previous
        if previous != 1:
            raise RuntimeError(f"injector primary-thread suspend count is {previous}")
        require_budget("primary thread resume")

        reason: str | None = None
        while True:
            if overflow.is_set():
                reason = "output reader failed or output limit exceeded"
                report["status"] = "RED_OUTPUT_OR_IO"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                reason = f"timeout after {timeout_seconds} seconds"
                report["status"] = "RED_TIMEOUT"
                break
            wait_ms = max(1, min(50, int(remaining * 1000)))
            wait = win32event.WaitForSingleObject(process_handle, wait_ms)
            if wait == win32event.WAIT_OBJECT_0:
                root_exited = True
                break
            if wait != win32event.WAIT_TIMEOUT:
                raise RuntimeError(f"injector root wait returned {wait}")
        if reason is not None:
            error_text = reason
            win32job.TerminateJobObject(job, 1)
            if win32event.WaitForSingleObject(process_handle, 5000) == win32event.WAIT_OBJECT_0:
                root_exited = True
        if not root_exited:
            raise RuntimeError("injector root exit remains unproven after bounded termination")
        report["returncode"] = int(win32process.GetExitCodeProcess(process_handle))
        report["injector_root_reaped"] = True

        out_drain.finish(INJECTOR_CLEANUP_SECONDS)
        err_drain.finish(INJECTOR_CLEANUP_SECONDS)
        if reason is None:
            require_budget("output drain")
        report.update(out_drain.evidence())
        report.update(err_drain.evidence())
        if out_drain.error or err_drain.error or overflow.is_set():
            report["status"] = "RED_OUTPUT_OR_IO"
            error_text = error_text or "injector output capture is incomplete"
        stdout = out_drain.captured()
        stderr = err_drain.captured()
        zero_deadline = time.monotonic() + INJECTOR_CLEANUP_SECONDS
        while True:
            count, pids = _job_state(job)
            if count == 0 and pids == []:
                break
            if time.monotonic() >= zero_deadline:
                raise RuntimeError(f"injector Job remains active: {count}, {pids}")
            time.sleep(0.05)
        report["job_active_final"] = count
        report["job_pids_final"] = pids
        if reason is None and error_text is None and stdout is not None and stderr is not None:
            # A second snapshot closes a transient query window before release.
            time.sleep(0.05)
            if _job_state(job) != (0, []):
                raise RuntimeError("injector Job changed after its empty snapshot")
            require_budget("final Job-empty proof")
            report["complete_process_tree_proven"] = True
            report["status"] = "EXIT"
        return ContainedInjectorResult(report, stdout, stderr, error_text)
    except _InjectorDeadlineExpired as error:
        report["status"] = "RED_TIMEOUT"
        error_text = str(error)
        return ContainedInjectorResult(report, None, None, error_text)
    except Exception as error:
        report["status"] = "RED_INTERNAL"
        error_text = f"{type(error).__name__}: {error}"
        return ContainedInjectorResult(report, None, None, error_text)
    finally:
        if job is not None and assigned:
            try:
                win32job.TerminateJobObject(job, 1)
            except Exception:
                report["complete_process_tree_proven"] = False
        elif process_handle is not None and not root_exited:
            try:
                win32process.TerminateProcess(process_handle, 1)
            except Exception:
                report["complete_process_tree_proven"] = False
        if process_handle is not None and not root_exited:
            try:
                if win32event.WaitForSingleObject(process_handle, 5000) == win32event.WAIT_OBJECT_0:
                    report["injector_root_reaped"] = True
            except Exception:
                pass
        for drain in (out_drain, err_drain):
            if drain is not None and drain.thread.is_alive():
                drain.finish(INJECTOR_CLEANUP_SECONDS)
                report["complete_process_tree_proven"] = False
        for handle in (thread_handle, process_handle, out_read, err_read,
                       raw_out_write, raw_err_write,
                       out_write, err_write, stdin_copy):
            _close_handle(handle)
        if job is not None:
            try:
                win32api.CloseHandle(job)
            except Exception:
                report["complete_process_tree_proven"] = False
