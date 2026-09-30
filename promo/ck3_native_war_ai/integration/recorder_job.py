"""Windows Job containment for the optional debug desktop recorder.

This is a process primitive, not screen admission. The caller must hold the
screen lease process-create gate while calling ``spawn``. Every child starts
suspended and is resumed only after it belongs to a kill-on-close Job.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time


SCHEMA = "xar.promo.recorder-job/v1"
CREATE_SUSPENDED = 0x00000004
TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800
JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK = 0x00001000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class _BasicLimit(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class _ExtendedLimit(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", _BasicLimit),
                ("IoInfo", _IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


class _BasicAccounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in
                ("TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime",
                 "ThisPeriodTotalKernelTime")] + [(name, wintypes.DWORD) for name in
                ("TotalPageFaultCount", "TotalProcesses", "ActiveProcesses",
                 "TotalTerminatedProcesses")]


class _ThreadEntry(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG),
                ("dwFlags", wintypes.DWORD)]


if sys.platform == "win32":
    _k = ctypes.WinDLL("kernel32", use_last_error=True)
    def _api(name: str, result: object, *arguments: object) -> object:
        call = getattr(_k, name)
        call.restype = result
        call.argtypes = list(arguments)
        return call
    _create_job = _api("CreateJobObjectW", wintypes.HANDLE, ctypes.c_void_p, wintypes.LPCWSTR)
    _set_job = _api("SetInformationJobObject", wintypes.BOOL, wintypes.HANDLE,
                    ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    _assign_job = _api("AssignProcessToJobObject", wintypes.BOOL, wintypes.HANDLE, wintypes.HANDLE)
    _in_job = _api("IsProcessInJob", wintypes.BOOL, wintypes.HANDLE, wintypes.HANDLE,
                   ctypes.POINTER(wintypes.BOOL))
    _query_job = _api("QueryInformationJobObject", wintypes.BOOL, wintypes.HANDLE,
                     ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                     ctypes.POINTER(wintypes.DWORD))
    _terminate_job = _api("TerminateJobObject", wintypes.BOOL, wintypes.HANDLE, wintypes.UINT)
    _close = _api("CloseHandle", wintypes.BOOL, wintypes.HANDLE)
    _thread_snapshot = _api("CreateToolhelp32Snapshot", wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD)
    _thread_first = _api("Thread32First", wintypes.BOOL, wintypes.HANDLE, ctypes.POINTER(_ThreadEntry))
    _thread_next = _api("Thread32Next", wintypes.BOOL, wintypes.HANDLE, ctypes.POINTER(_ThreadEntry))
    _open_thread = _api("OpenThread", wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _resume_thread = _api("ResumeThread", wintypes.DWORD, wintypes.HANDLE)


def _check(ok: object, action: str) -> None:
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error(), action)


def _new_job() -> int:
    job = _create_job(None, None)
    _check(job, "CreateJobObjectW")
    info = _ExtendedLimit()
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    try:
        _check(_set_job(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                        ctypes.byref(info), ctypes.sizeof(info)),
               "SetInformationJobObject")
        _verified_limit_flags(job)
        return job
    except BaseException:
        _close(job)
        raise


def _verified_limit_flags(job: int) -> int:
    info = _ExtendedLimit()
    returned = wintypes.DWORD()
    _check(_query_job(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                      ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned)),
           "QueryInformationJobObject(ExtendedLimit)")
    if returned.value < ctypes.sizeof(info):
        raise RuntimeError("Job extended limit response is truncated")
    flags = int(info.BasicLimitInformation.LimitFlags)
    if not flags & JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE or flags & (
            JOB_OBJECT_LIMIT_BREAKAWAY_OK | JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK):
        raise RuntimeError(f"Job cannot contain descendants safely: LimitFlags=0x{flags:08X}")
    return flags


def _active(job: int) -> int:
    info = _BasicAccounting()
    returned = wintypes.DWORD()
    _check(_query_job(job, JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
                      ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned)),
           "QueryInformationJobObject")
    if returned.value < ctypes.sizeof(info):
        raise RuntimeError("Job accounting response is truncated")
    return int(info.ActiveProcesses)


def _resume_only_thread(pid: int) -> None:
    snapshot = _thread_snapshot(TH32CS_SNAPTHREAD, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error(), "CreateToolhelp32Snapshot")
    tids = []
    try:
        item = _ThreadEntry()
        item.dwSize = ctypes.sizeof(item)
        if _thread_first(snapshot, ctypes.byref(item)):
            while True:
                if item.th32OwnerProcessID == pid:
                    tids.append(item.th32ThreadID)
                item.dwSize = ctypes.sizeof(item)
                if not _thread_next(snapshot, ctypes.byref(item)):
                    break
    finally:
        _close(snapshot)
    if len(tids) != 1:
        raise RuntimeError(f"suspended recorder needs exactly one initial thread; found {len(tids)}")
    thread = _open_thread(THREAD_SUSPEND_RESUME, False, tids[0])
    _check(thread, "OpenThread")
    try:
        prior = _resume_thread(thread)
        if prior != 1:
            raise RuntimeError(f"recorder thread suspension count was {prior}, expected 1")
    finally:
        _close(thread)


def _write_new(path: Path, body: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _marker(path: Path, reason: str, pid: int | None) -> None:
    try:
        _write_new(path, {"schema": SCHEMA, "state": "RED_RETAINED",
                          "reason": reason, "pid": pid,
                          "at_utc": datetime.now(timezone.utc).isoformat()})
    except FileExistsError:
        pass  # An earlier RED marker is immutable.


def _wait_empty(job: int, timeout: float) -> int:
    end = time.monotonic() + timeout
    while True:
        active = _active(job)
        if active == 0 or time.monotonic() >= end:
            return active
        time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class RecorderJob:
    """Own the Job until a directly queried terminal tree-empty result."""

    def __init__(self, process: subprocess.Popen, job: int) -> None:
        self.process = process
        self.job: int | None = job
        self._lock = threading.Lock()
        self._aborted = False

    @property
    def pid(self) -> int:
        return self.process.pid

    def poll(self) -> int | None:
        return self.process.poll()

    @property
    def returncode(self) -> int | None:
        return self.process.returncode

    def _terminate_locked(self) -> None:
        if self.job is not None and _active(self.job):
            _check(_terminate_job(self.job, 1), "TerminateJobObject")

    def abort(self, *, receipt: Path, unsafe_marker: Path) -> dict:
        """Retain RED before stopping all descendants, even if cleanup succeeds."""
        with self._lock:
            if self.job is None:
                return {"schema": SCHEMA, "state": "ALREADY_TREE_EMPTY",
                        "pid": self.pid, "returncode": self.process.poll(),
                        "job_active_processes": 0, "error": None,
                        "at_utc": datetime.now(timezone.utc).isoformat()}
        error = None
        try:
            _marker(unsafe_marker, "recorder abort requested", self.pid)
        except BaseException as exc:
            error = f"unsafe marker write failed: {exc!r}"
        with self._lock:
            self._aborted = True
            job = self.job
            try:
                if job is not None:
                    self._terminate_locked()
            except BaseException as exc:
                error = repr(exc)
        active = None
        if job is not None:
            try:
                active = _wait_empty(job, 10)
                self.process.wait(timeout=1)
                if self.process.stdin is not None and not self.process.stdin.closed:
                    self.process.stdin.close()
            except BaseException as exc:
                error = error or repr(exc)
            if active == 0:
                with self._lock:
                    if self.job == job:
                        _close(job)
                        self.job = None
        row = {"schema": SCHEMA, "state": "ABORT_TREE_EMPTY" if active == 0 and error is None else
               "RED_TREE_EMPTY" if active == 0 else "RED_UNPROVEN",
               "pid": self.pid, "returncode": self.process.poll(),
               "job_active_processes": active, "error": error,
               "at_utc": datetime.now(timezone.utc).isoformat()}
        _write_new(receipt, row)
        if row["state"] != "ABORT_TREE_EMPTY":
            raise RuntimeError("recorder descendant cleanup is unproven")
        return row

    def finish(self, *, receipt: Path, unsafe_marker: Path, timeout: float = 30) -> dict:
        """Ask FFmpeg to finish; a surviving descendant makes this RED."""
        error = None
        try:
            if self.process.poll() is None:
                self.process.communicate(b"q\n", timeout=timeout)
            else:
                self.process.wait(timeout=1)
        except BaseException as exc:
            error = repr(exc)
        with self._lock:
            job = self.job
            aborted = self._aborted
        active = None
        if job is not None:
            try:
                active = _wait_empty(job, 1)
            except BaseException as exc:
                error = error or repr(exc)
        good = error is None and not aborted and active == 0 and self.process.returncode == 0
        if not good:
            try:
                _marker(unsafe_marker, "normal recorder finish failed or descendants remain", self.pid)
            except BaseException as exc:
                error = error or f"unsafe marker write failed: {exc!r}"
            with self._lock:
                try:
                    self._terminate_locked()
                except BaseException as exc:
                    error = error or repr(exc)
            if job is not None:
                try:
                    active = _wait_empty(job, 10)
                    self.process.wait(timeout=1)
                except BaseException as exc:
                    error = error or repr(exc)
        if job is not None and active == 0:
            with self._lock:
                if self.job == job:
                    _close(job)
                    self.job = None
        row = {"schema": SCHEMA,
               "state": "NORMAL_TREE_EMPTY" if good else "RED_TREE_EMPTY" if active == 0 else "RED_UNPROVEN",
               "pid": self.pid, "returncode": self.process.poll(),
               "job_active_processes": active, "error": error,
               "at_utc": datetime.now(timezone.utc).isoformat()}
        try:
            _write_new(receipt, row)
        except BaseException:
            _marker(unsafe_marker, "recorder terminal receipt write failed", self.pid)
            raise
        return row


def spawn(command: list[str], *, stdin: object = subprocess.PIPE,
          stdout: object = subprocess.DEVNULL, stderr: object,
          unsafe_marker: Path, start_receipt: Path,
          failure_receipt: Path) -> RecorderJob:
    """Spawn a suspended child, assign its Job, then resume its only thread."""
    if sys.platform != "win32":
        raise RuntimeError("Windows Job containment requires Windows")
    if not command or not all(type(part) is str for part in command):
        raise ValueError("recorder command must contain only strings")
    job = _new_job()
    process = None
    try:
        process = subprocess.Popen(command, stdin=stdin, stdout=stdout, stderr=stderr,
                                   creationflags=CREATE_SUSPENDED)
        _check(_assign_job(job, int(process._handle)), "AssignProcessToJobObject")
        member = wintypes.BOOL()
        _check(_in_job(int(process._handle), job, ctypes.byref(member)), "IsProcessInJob")
        if not member.value or _active(job) != 1:
            raise RuntimeError("suspended recorder is not the sole Job member")
        actual_flags = _verified_limit_flags(job)
        _resume_only_thread(process.pid)
        _write_new(start_receipt, {
            "schema": SCHEMA, "state": "ASSIGNED_AND_RESUMED",
            "pid": process.pid, "argv": command,
            "job_limit_flags_readback": actual_flags,
            "member_verified_before_resume": True,
            "job_active_processes_before_resume": 1,
            "initial_thread_resume_prior_count": 1,
            "at_utc": datetime.now(timezone.utc).isoformat(),
        })
        return RecorderJob(process, job)
    except BaseException as exc:
        marker_error = None
        try:
            _marker(unsafe_marker, f"recorder spawn/assignment failed: {exc!r}",
                    process.pid if process else None)
        except BaseException as mark_exc:
            marker_error = repr(mark_exc)
        cleanup_error = None
        try:
            if _active(job):
                _check(_terminate_job(job, 1), "TerminateJobObject")
        except BaseException as stop_exc:
            cleanup_error = repr(stop_exc)
        if process is not None:
            try:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()
            except BaseException as stop_exc:
                cleanup_error = cleanup_error or repr(stop_exc)
        active = None
        try:
            active = _wait_empty(job, 10)
        except BaseException as query_exc:
            cleanup_error = cleanup_error or repr(query_exc)
        row = {"schema": SCHEMA,
               "state": "RED_TREE_EMPTY" if active == 0 and cleanup_error is None and
               (process is None or process.poll() is not None) else "RED_UNPROVEN",
               "pid": process.pid if process else None,
               "returncode": process.poll() if process else None,
               "job_active_processes": active, "spawn_error": repr(exc),
               "cleanup_error": cleanup_error, "marker_error": marker_error,
               "at_utc": datetime.now(timezone.utc).isoformat()}
        try:
            _write_new(failure_receipt, row)
        except BaseException:
            pass  # The marker, when writable, remains as the durable RED signal.
        _close(job)
        raise
