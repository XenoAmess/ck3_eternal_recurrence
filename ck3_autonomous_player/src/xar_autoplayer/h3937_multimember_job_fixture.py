"""Windows Job fixture for a harmless venv launcher and its Python child.

This is not an operator. Its command is fixed to an inert Python snippet; it
cannot launch CK3, use the desktop, or touch a task bus. The create-only result
is raw OBSERVATION_ONLY evidence, never gameplay or cleanup acceptance.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import time

import psutil
import pythoncom
import win32com.client

from .environment import _toolhelp_process_identity, same_process_creation_time


CREATE_SUSPENDED = 0x00000004
PROCESS_QUERY_LIMITED_INFORMATION = 0x00001000
THREAD_SUSPEND_RESUME = 0x0002
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
JOB_OBJECT_BASIC_PROCESS_ID_LIST = 3
FIXTURE_CODE = (
    "import json,os,sys,time;"
    "print(json.dumps({'pid':os.getpid(),'parent_pid':os.getppid(),"
    "'sys_executable':sys.executable,'base_executable':sys._base_executable}),"
    "flush=True);time.sleep(8)"
)
FIXTURE_PYTHON = Path(
    r"D:\workspace\ck3_eternal_recurrence\tools\.venv\Scripts\python.exe")
FIXTURE_PYTHON_SHA256 = (
    "9B7BFFC26240463C965A2A2A5FADA1D8E741C21C25CD2E977728C339B82D9977")


class _BasicLimit(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
        "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _ExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimit),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _BasicAccounting(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_int64),
        ("TotalKernelTime", ctypes.c_int64),
        ("ThisPeriodTotalUserTime", ctypes.c_int64),
        ("ThisPeriodTotalKernelTime", ctypes.c_int64),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class _PidList(ctypes.Structure):
    _fields_ = [
        ("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
        ("pids", ctypes.c_size_t * 32),
    ]


def _kernel():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryInformationJobObject.restype = wintypes.BOOL
    kernel.IsProcessInJob.argtypes = [
        wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.IsProcessInJob.restype = wintypes.BOOL
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.TerminateJobObject.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [
        wintypes.HANDLE, ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME)]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenThread.restype = wintypes.HANDLE
    kernel.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel.ResumeThread.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _require(value, action: str):
    if not value:
        raise OSError(ctypes.get_last_error(), action)
    return value


def _job_accounting(kernel, job) -> dict[str, int]:
    data = _BasicAccounting()
    _require(kernel.QueryInformationJobObject(
        job, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
        ctypes.byref(data), ctypes.sizeof(data), None), "Job accounting")
    return {"active": int(data.ActiveProcesses), "total": int(data.TotalProcesses)}


def _job_pids(kernel, job) -> list[int]:
    data = _PidList()
    returned = wintypes.DWORD()
    _require(kernel.QueryInformationJobObject(
        job, JOB_OBJECT_BASIC_PROCESS_ID_LIST,
        ctypes.byref(data), ctypes.sizeof(data), ctypes.byref(returned)),
        "Job PID list")
    if data.assigned > 32 or data.count > 32:
        raise RuntimeError("Job process list exceeded fixture capacity")
    return sorted(int(data.pids[index]) for index in range(data.count))


def _handle_identity(kernel, pid: int, job) -> dict[str, object]:
    handle = _require(kernel.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION, False, pid), "OpenProcess")
    try:
        creation, exited, kernel_time, user_time = (
            wintypes.FILETIME() for _ in range(4))
        _require(kernel.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exited),
            ctypes.byref(kernel_time), ctypes.byref(user_time)), "GetProcessTimes")
        filetime = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        path = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(path))
        _require(kernel.QueryFullProcessImageNameW(
            handle, 0, path, ctypes.byref(length)), "QueryFullProcessImageNameW")
        member = wintypes.BOOL()
        _require(kernel.IsProcessInJob(handle, job, ctypes.byref(member)),
                 "IsProcessInJob")
        return {
            "pid": pid, "creation_filetime_100ns": filetime,
            "creation_utc": (
                datetime(1601, 1, 1, tzinfo=timezone.utc)
                + timedelta(microseconds=filetime // 10)
            ).isoformat(),
            "exe": path.value, "job_member": bool(member.value),
        }
    finally:
        kernel.CloseHandle(handle)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _same_executable(first: object, second: object) -> bool:
    return os.path.normcase(os.path.realpath(str(first))) == os.path.normcase(
        os.path.realpath(str(second)))


def _dual_identity(kernel, pid: int, job, expected_argv: list[str]) -> dict[str, object]:
    """Capture WMI, Toolhelp, handle, and Job evidence while PID is alive."""
    pythoncom.CoInitialize()
    service = rows = row = None
    try:
        service = win32com.client.GetObject("winmgmts:")
        rows = service.ExecQuery(
            "SELECT ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate,CommandLine "
            f"FROM Win32_Process WHERE ProcessId={pid}")
        row = next(iter(rows), None)
        if row is None:
            raise RuntimeError(f"WMI PID {pid} unavailable while running")
        toolhelp = _toolhelp_process_identity(pid)
        if toolhelp is None:
            raise RuntimeError(f"Toolhelp PID {pid} unavailable while running")
        handle = _handle_identity(kernel, pid, job)
        argv = psutil.Process(pid).cmdline()
        wmi_exe = str(row.ExecutablePath) if row.ExecutablePath else None
        checks = {
            "pid": int(row.ProcessId) == pid,
            "parent": int(row.ParentProcessId) == toolhelp["parent_pid"],
            "wmi_toolhelp_creation": same_process_creation_time(
                str(row.CreationDate), toolhelp["creation_date"]),
            "toolhelp_handle_exe": _same_executable(
                toolhelp["executable"], handle["exe"]),
            "wmi_toolhelp_exe_if_available": (
                wmi_exe is None or _same_executable(
                    wmi_exe, toolhelp["executable"])),
            "wmi_handle_creation": same_process_creation_time(
                str(row.CreationDate),
                datetime.fromisoformat(handle["creation_utc"]).strftime(
                    "%Y%m%d%H%M%S.%f+000")),
            "argv": argv == expected_argv,
            "wmi_command_line": bool(row.CommandLine),
            "job_member": handle["job_member"] is True,
        }
        if not all(checks.values()):
            raise RuntimeError(
                f"PID {pid} identity mismatch: " + json.dumps({
                    "checks": checks, "wmi_creation": str(row.CreationDate),
                    "toolhelp_creation": toolhelp["creation_date"],
                    "handle_creation": handle["creation_utc"],
                    "wmi_exe": wmi_exe,
                    "toolhelp_exe": toolhelp["executable"],
                    "handle_exe": handle["exe"],
                    "actual_argv": argv, "expected_argv": expected_argv,
                }, sort_keys=True))
        return {
            **handle,
            "parent_pid": int(row.ParentProcessId),
            "argv": argv,
            "wmi_creation_date": str(row.CreationDate),
            "wmi_command_line": str(row.CommandLine),
            "wmi_executable_path": wmi_exe,
            "toolhelp": toolhelp,
            "wmi_toolhelp_cross_checked": True,
            "observed_while_running": True,
        }
    finally:
        row = rows = service = None
        pythoncom.CoUninitialize()


def _resume_single_thread(kernel, pid: int) -> int:
    threads = psutil.Process(pid).threads()
    if len(threads) != 1:
        raise RuntimeError(f"suspended launcher thread count {len(threads)}")
    tid = threads[0].id
    handle = _require(kernel.OpenThread(THREAD_SUSPEND_RESUME, False, tid),
                      "OpenThread")
    try:
        previous = kernel.ResumeThread(handle)
        if previous != 1:
            raise RuntimeError(f"ResumeThread previous count {previous}")
    finally:
        kernel.CloseHandle(handle)
    return tid


def run_no_ck3_fixture(
    *, output: Path, python_executable: Path, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Run only the fixed harmless Python snippet inside a multi-member Job."""
    if os.name != "nt" or timeout_seconds <= 0:
        raise ValueError("Windows and a positive timeout are required")
    if python_executable != FIXTURE_PYTHON:
        raise ValueError("fixture accepts only the frozen main venv Python path")
    python_sha = _sha(python_executable)
    if python_sha != FIXTURE_PYTHON_SHA256:
        raise RuntimeError("fixture Python bytes differ from frozen identity")
    started = time.monotonic()
    deadline = started + timeout_seconds
    output.mkdir(parents=True, exist_ok=False)
    marker = output / "unsafe-marker.json"
    with marker.open("x", encoding="utf-8") as target:
        json.dump({"schema": "xar.h3937-job-fixture-unsafe.v1",
                   "status": "UNSAFE_UNTIL_INDEPENDENT_REVIEW",
                   "ck3_launch_attempted": False}, target)
        target.write("\n")
    argv = [str(python_executable), "-u", "-c", FIXTURE_CODE]
    record: dict[str, object] = {
        "schema": "xar.h3937-multimember-job-observation.v1",
        "status": "RED", "argv": argv,
        "python_sha256": python_sha,
        "ck3_launch_attempted": False, "screen_touched": False,
        "authority_bus_touched": False,
        "deadline_seconds": timeout_seconds,
    }
    kernel = None
    job = None
    launcher = None
    assigned = False
    job_closed = False
    stdout_path = output / "stdout.bin"
    stderr_path = output / "stderr.bin"
    watchdog_stop = threading.Event()
    watchdog_fired = threading.Event()
    watchdog_action = None
    watchdog_thread = None
    error = None

    def require_time(stage: str) -> None:
        if time.monotonic() >= deadline or watchdog_fired.is_set():
            raise TimeoutError(f"full-chain deadline at {stage}")

    def enforce_deadline() -> None:
        nonlocal watchdog_action
        if watchdog_stop.wait(max(0, deadline - time.monotonic())):
            return
        watchdog_fired.set()
        try:
            if assigned and job is not None:
                _require(kernel.TerminateJobObject(job, 1), "deadline Job termination")
                watchdog_action = "terminated_job"
            elif launcher is not None and launcher.poll() is None:
                launcher.kill()
                watchdog_action = "killed_suspended_launcher"
            else:
                watchdog_action = "no_live_launcher"
        except BaseException as caught:
            watchdog_action = f"deadline_error:{type(caught).__name__}:{caught}"

    watchdog_thread = threading.Thread(
        target=enforce_deadline, name="h3937-fixture-job-deadline", daemon=True)
    watchdog_thread.start()
    try:
        require_time("Job setup")
        kernel = _kernel()
        job = _require(kernel.CreateJobObjectW(None, None), "CreateJobObjectW")
        limits = _ExtendedLimit()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        _require(kernel.SetInformationJobObject(
            job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits), ctypes.sizeof(limits)), "SetInformationJobObject")
        parent = _handle_identity(kernel, os.getpid(), job)
        record["parent_identity"] = parent
        require_time("stdio setup")
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            require_time("launcher Popen")
            launcher = subprocess.Popen(
                argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                creationflags=CREATE_SUSPENDED, close_fds=True)
            require_time("Job assignment")
            _require(kernel.AssignProcessToJobObject(job, launcher._handle),
                     "AssignProcessToJobObject")
            assigned = True
            record["job_before_resume"] = _job_accounting(kernel, job)
            if record["job_before_resume"] != {"active": 1, "total": 1}:
                raise RuntimeError("Job not exclusive before resume")
            launcher_identity = _dual_identity(kernel, launcher.pid, job, argv)
            if launcher_identity["parent_pid"] != parent["pid"]:
                raise RuntimeError("launcher parent PID differs")
            record["launcher_identity"] = launcher_identity
            record["resumed_thread_id"] = _resume_single_thread(kernel, launcher.pid)
            require_time("actual child discovery")
            actual = None
            while time.monotonic() < deadline:
                pids = _job_pids(kernel, job)
                children = [pid for pid in pids if pid != launcher.pid]
                if len(children) > 1:
                    raise RuntimeError("unexpected multiple Job children")
                if children:
                    try:
                        candidate = _dual_identity(kernel, children[0], job, argv)
                    except (psutil.Error, OSError, RuntimeError):
                        candidate = None
                    if candidate is not None:
                        if candidate["parent_pid"] != launcher.pid:
                            raise RuntimeError("actual child parent differs")
                        launcher_again = _dual_identity(
                            kernel, launcher.pid, job, argv)
                        if (launcher_again["creation_filetime_100ns"]
                                != launcher_identity["creation_filetime_100ns"]):
                            raise RuntimeError("launcher PID identity drifted")
                        actual = candidate
                        record["launcher_identity_with_child"] = launcher_again
                        record["job_with_child"] = _job_accounting(kernel, job)
                        record["job_pid_list_with_child"] = pids
                        break
                time.sleep(0.02)
            if actual is None:
                raise TimeoutError("actual child identity not observed")
            record["actual_identity"] = actual
            require_time("Job tree completion")
            while time.monotonic() < deadline:
                if _job_accounting(kernel, job)["active"] == 0:
                    break
                time.sleep(0.02)
            require_time("Job tree completion")
            record["launcher_returncode"] = launcher.wait(timeout=1)
            if record["launcher_returncode"] != 0:
                raise RuntimeError("harmless launcher did not exit zero")
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        watchdog_stop.set()
        if watchdog_thread is not None:
            watchdog_thread.join(timeout=5)
            if watchdog_thread.is_alive():
                error = error or "deadline watchdog did not stop within five seconds"
        if job is not None and kernel is not None:
            try:
                if _job_accounting(kernel, job)["active"] != 0:
                    _require(kernel.TerminateJobObject(job, 1), "cleanup Job termination")
                cleanup_deadline = time.monotonic() + 5
                while _job_accounting(kernel, job)["active"] != 0:
                    if time.monotonic() >= cleanup_deadline:
                        raise TimeoutError("Job tree remained after cleanup")
                    time.sleep(0.02)
                record["job_after_cleanup"] = _job_accounting(kernel, job)
            except BaseException as caught:
                error = error or f"cleanup:{type(caught).__name__}:{caught}"
            finally:
                job_closed = bool(kernel.CloseHandle(job))
        if launcher is not None:
            if not assigned and launcher.poll() is None:
                launcher.kill()
            try:
                record["launcher_returncode"] = launcher.wait(timeout=5)
            except BaseException as caught:
                error = error or f"reap:{type(caught).__name__}:{caught}"
    record["job_closed"] = job_closed
    record["watchdog_fired"] = watchdog_fired.is_set()
    record["watchdog_thread_alive_after_cleanup"] = bool(
        watchdog_thread is not None and watchdog_thread.is_alive())
    record["watchdog_action"] = watchdog_action
    record["elapsed_seconds_before_receipt"] = round(time.monotonic() - started, 6)
    record["unsafe_marker_sha256"] = _sha(marker)
    if stdout_path.is_file():
        record["stdout_sha256"] = _sha(stdout_path)
    if stderr_path.is_file():
        record["stderr_sha256"] = _sha(stderr_path)
    if error is not None:
        record["error"] = error
    observation_complete = (
        error is None and not watchdog_fired.is_set() and job_closed
        and record.get("launcher_returncode") == 0
        and isinstance(record.get("launcher_identity"), dict)
        and isinstance(record.get("actual_identity"), dict)
        and record["launcher_identity"]["pid"] != record["actual_identity"]["pid"]
        and record.get("job_with_child", {}).get("active", 0) >= 2
        and record.get("job_after_cleanup", {}).get("active") == 0
        and time.monotonic() < deadline
    )
    record["status"] = "OBSERVATION_ONLY" if observation_complete else "RED"
    # Publish exactly once, after all fact collection. No provisional GREEN.
    with (output / "terminal-observation.json").open("x", encoding="utf-8") as target:
        json.dump(record, target, indent=2, ensure_ascii=True)
        target.write("\n")
    return record
