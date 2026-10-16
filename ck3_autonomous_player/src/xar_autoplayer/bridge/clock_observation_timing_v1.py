"""Optional exact-clock scalar profiling of cached frames and one bound PID.

No game queries, polling, time control, state persistence or action decisions.
The existing timing JSONL is the sole output, and profiling errors are ignored.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time

from .army_query_timing import _WRITE_LOCK


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _integer(value):
    return value if type(value) is int else None


def _boolean(value):
    return value if type(value) is bool else None


def _bound_pid(snapshot):
    diagnostics = _mapping(_mapping(snapshot).get("diagnostics"))
    hello = _mapping(diagnostics.get("hello"))
    pid = _integer(diagnostics.get("bridge_pid"))
    hello_pid = _integer(hello.get("pid"))
    return pid if pid is not None and 0 < pid <= 0xffffffff and hello_pid == pid else None


def cached_clock_fields_v1(snapshot):
    """Explicit allowlist: never copy snapshots, history or heartbeat bodies."""
    snapshot = _mapping(snapshot)
    diagnostics = _mapping(snapshot.get("diagnostics"))
    heartbeat = _mapping(diagnostics.get("last_heartbeat"))
    owner = _mapping(heartbeat.get("main_thread_query_mailbox_v1"))
    observer = _mapping(heartbeat.get("snapshot_observer_12002"))
    fields = {
        "game_pid": _bound_pid(snapshot),
        "date_raw": _integer(snapshot.get("date_raw")),
        "native_revision": _integer(snapshot.get("native_revision")),
        "public_revision": _integer(snapshot.get("revision")),
        "speed": _integer(snapshot.get("speed")),
        "paused": _boolean(snapshot.get("paused")),
        "native_snapshot_monotonic_ms": _integer(snapshot.get("monotonic_ms")),
        "heartbeat_sequence": _integer(heartbeat.get("sequence")),
        "heartbeat_monotonic_ms": _integer(heartbeat.get("monotonic_ms")),
        "heartbeat_pid": _integer(heartbeat.get("pid")),
        "owner_pump_epochs": _integer(owner.get("pump_epochs")),
        "owner_verified_pump_epochs": _integer(owner.get("owner_verified_pump_epochs")),
        "owner_date_raw": _integer(owner.get("date_raw")),
        "owner_paused": _boolean(owner.get("paused")),
        "owner_tid": _integer(owner.get("owner_tid")),
        "owner_current_tid": _integer(owner.get("current_tid")),
        "owner_stamp_read_success": _boolean(owner.get("stamp_read_success")),
        "owner_failure": _integer(owner.get("failure")),
        "observer_started_ms": _integer(observer.get("started_ms")),
        "observer_completed_ms": _integer(observer.get("completed_ms")),
        "observer_last_read_ms": _integer(observer.get("last_read_ms")),
        "observer_read_in_progress": _boolean(observer.get("read_in_progress")),
        "observer_last_read_available": _boolean(observer.get("last_read_available")),
        "observer_snapshot_cached": _boolean(observer.get("snapshot_cached")),
        "rejected_state_snapshot_count": _integer(diagnostics.get("rejected_state_snapshot_count")),
    }
    # Owner/heartbeat is cached evidence with its own age, not the timestamp of
    # the semantic snapshot and never a substitute for its gameplay state.
    return fields


class _BoundProcessCpuV1:
    """One query-only handle, bound to the Native hello PID and creation time."""

    def __init__(self, pid):
        self.pid = pid
        self.handle = None
        self.creation = None
        self.kernel32 = None
        if pid is None or os.name != "nt":
            return
        import ctypes
        from ctypes import wintypes
        self.ctypes, self.wintypes = ctypes, wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.GetTickCount64.argtypes = ()
        kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32 = kernel32
        self.handle = kernel32.OpenProcess(0x1000, False, pid)

    def sample(self):
        if not self.handle or self.kernel32 is None:
            return None
        ft = [self.wintypes.FILETIME() for _ in range(4)]
        if not self.kernel32.GetProcessTimes(self.handle, *(self.ctypes.byref(v) for v in ft)):
            return None
        values = [(v.dwHighDateTime << 32) | v.dwLowDateTime for v in ft]
        creation = values[0]
        if creation <= 0 or (self.creation is not None and self.creation != creation):
            return None
        self.creation = creation
        return {"creation_filetime": creation, "kernel_100ns": values[2],
                "user_100ns": values[3], "host_monotonic_ms": int(self.kernel32.GetTickCount64())}

    def close(self):
        if self.handle and self.kernel32 is not None:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


class ClockObservationV1:
    def __init__(self, path, snapshot, *, cpu_factory=_BoundProcessCpuV1):
        self.path = path
        self.pid = _bound_pid(snapshot)
        self.start_date = _integer(_mapping(snapshot).get("date_raw"))
        self.started_ns = time.perf_counter_ns()
        self.phases = set()
        self.baseline_cpu = None
        self.last_cpu = None
        self.cpu = cpu_factory(self.pid)
        self.record("resume_begin", snapshot)

    def _sample(self, snapshot):
        if _bound_pid(snapshot) != self.pid or self.pid is None:
            return None
        try:
            return self.cpu.sample()
        except Exception:
            return None

    def record(self, phase, snapshot, *, sample=None, sampled=False):
        try:
            if phase in self.phases:
                return
            self.phases.add(phase)
            now = time.perf_counter_ns()
            if not sampled:
                sample = self._sample(snapshot)
            fields = cached_clock_fields_v1(snapshot)
            sample = _mapping(sample)
            if self.baseline_cpu is None and sample:
                # An unavailable opening sample must not become a later false
                # zero CPU baseline for the entire clock interval.
                if phase == "resume_begin":
                    self.baseline_cpu = dict(sample)
            creation = _integer(sample.get("creation_filetime"))
            delta_total = delta_interval = None
            for previous, label in ((self.baseline_cpu, "total"), (self.last_cpu, "interval")):
                if previous and creation == previous.get("creation_filetime"):
                    values = [sample.get(k) for k in ("kernel_100ns", "user_100ns")]
                    old = [previous.get(k) for k in ("kernel_100ns", "user_100ns")]
                    if all(type(v) is int for v in values + old) and all(a >= b for a, b in zip(values, old)):
                        delta = sum(values) - sum(old)
                        if label == "total": delta_total = delta
                        else: delta_interval = delta
            heartbeat_age = None
            mono = _integer(sample.get("host_monotonic_ms"))
            heartbeat_ms = fields["heartbeat_monotonic_ms"]
            if mono is not None and heartbeat_ms is not None and mono >= heartbeat_ms:
                heartbeat_age = mono - heartbeat_ms
            row = {"schema": "xar.ck3.exact-clock-observation.v1",
                   "stage": "driver.exact_clock_observation", "phase": phase,
                   "python_pid": os.getpid(), "thread_id": threading.get_ident(),
                   "step": "life-advance", "elapsed_ns": now - self.started_ns,
                   "finished_at_utc": datetime.now(timezone.utc).isoformat(),
                   **fields, "bound_game_pid": self.pid,
                   "process_creation_filetime": creation,
                   "cpu_kernel_100ns": _integer(sample.get("kernel_100ns")),
                   "cpu_user_100ns": _integer(sample.get("user_100ns")),
                   "cpu_delta_from_resume_100ns": delta_total,
                   "cpu_delta_from_previous_phase_100ns": delta_interval,
                   "host_monotonic_ms": mono, "cached_heartbeat_age_ms": heartbeat_age}
            encoded = json.dumps(row, separators=(",", ":")) + "\n"
            with _WRITE_LOCK, Path(self.path).open("a", encoding="utf-8") as stream:
                stream.write(encoded)
            if sample:
                self.last_cpu = dict(sample)
        except Exception:
            # Optional observation cannot invalidate a gameplay result or mask
            # its exception, including output-path and OS permission failures.
            pass

    def observe(self, snapshot):
        try:
            snapshot = _mapping(snapshot)
            date = _integer(snapshot.get("date_raw"))
            phases = []
            if snapshot.get("paused") is False and "resume_observed" not in self.phases:
                phases.append("resume_observed")
            advanced = self.start_date is not None and date is not None and date > self.start_date
            if advanced and "first_date_seen" not in self.phases:
                phases.append("first_date_seen")
            if advanced and snapshot.get("paused") is True and "paused_observed" not in self.phases:
                phases.append("paused_observed")
            if phases:
                sample = self._sample(snapshot)
                for phase in phases:
                    self.record(phase, snapshot, sample=sample, sampled=True)
        except Exception:
            pass

    def close(self, snapshot):
        try:
            self.observe(snapshot)
            self.record("resume_to_paused_final", snapshot)
        finally:
            try:
                self.cpu.close()
            except Exception:
                pass


def start_clock_observation_v1(driver, snapshot):
    path = os.environ.get("XAR_CK3_ARMY_TIMING_JSONL")
    if not path or getattr(driver, "_exact_clock_observation_v1", None) is not None:
        return None
    try:
        observer = ClockObservationV1(path, snapshot)
        driver._exact_clock_observation_v1 = observer
        return observer
    except Exception:
        return None


def observe_clock_snapshot_v1(driver, snapshot):
    try:
        observer = getattr(driver, "_exact_clock_observation_v1", None)
        if observer is not None:
            observer.observe(snapshot)
    except Exception:
        pass


def finish_clock_observation_v1(driver, observer, snapshot):
    if observer is None:
        return
    try:
        observer.close(snapshot)
    except Exception:
        pass
    finally:
        if getattr(driver, "_exact_clock_observation_v1", None) is observer:
            driver._exact_clock_observation_v1 = None
