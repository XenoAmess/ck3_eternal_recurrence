"""Storage publication: prepare outside the bus, then a small metadata CAS.

No caller callback runs under the shared task-bus lock. Process inspection,
hashing, machine probes, volume reads, inventories and serialization belong in
the caller's prepare phase. This module does not authorize asset deletion.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import time
import uuid

from codex_task_bus import bus_lock, lock_wait_seconds

MAX_HEAD_BYTES = 8192
MAX_EXACT_GUARDS = 8


class StorageConflict(RuntimeError):
    """Nothing was adopted; discard preparation and retry outside the lock."""


@dataclass(frozen=True)
class Snapshot:
    path: Path
    identity: tuple | None
    value: dict


@dataclass(frozen=True)
class Prepared:
    head: Snapshot
    head_temp: Path
    head_temp_identity: tuple
    report: Path | None
    report_temp: Path | None
    report_temp_identity: tuple | None
    guards: tuple[tuple[Path, tuple | None], ...]


def exact_identity(path: Path) -> tuple | None:
    """One named metadata query, never a walk or body read."""
    try:
        value = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError(f"CAS metadata must be a single regular file: {path}")
    if getattr(value, "st_file_attributes", 0) & 0x400:
        raise ValueError("CAS metadata must not be a reparse point")
    return (value.st_dev, value.st_ino, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def snapshot_json(path: Path) -> Snapshot:
    path = Path(path).absolute()
    before = exact_identity(path)
    if before is None:
        return Snapshot(path, None, {})
    if before[2] > MAX_HEAD_BYTES:
        raise ValueError("CAS head exceeds 8 KiB")
    # Parsing and every body read happen before acquisition.
    raw = path.read_bytes()
    if exact_identity(path) != before:
        raise StorageConflict("head changed while preparing")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("CAS head must be an object")
    return Snapshot(path, before, value)


def _stage(target: Path, raw: bytes) -> tuple[Path, tuple]:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.prepared")
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return temporary, exact_identity(temporary)


def prepare(head: Snapshot, value: dict, *, report: Path | None = None,
            report_bytes: bytes | None = None, guards=()) -> Prepared:
    """Serialize, write and fsync completely outside any shared lock.

    Head owns a monotonically increasing storage_revision. Existing legacy
    metadata without that field starts at revision zero. A report is immutable;
    the head is its adoption pointer. An interrupted two-rename commit can leave
    an unadopted report, which must be retained/diagnosed, never auto-replayed.
    """
    if len(guards) > MAX_EXACT_GUARDS:
        raise ValueError("too many exact CAS guards")
    revision = head.value.get("storage_revision", 0)
    if type(revision) is not int or revision < 0:
        raise ValueError("invalid storage revision")
    payload = {**value, "storage_revision": revision + 1}
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    if len(raw) > MAX_HEAD_BYTES:
        raise ValueError("CAS head exceeds 8 KiB")
    if (report is None) != (report_bytes is None):
        raise ValueError("report path and bytes must be supplied together")
    rt = ri = None
    try:
        if report is not None:
            report = Path(report).absolute()
            if report == head.path or exact_identity(report) is not None:
                raise StorageConflict("immutable report path is already occupied")
            rt, ri = _stage(report, report_bytes)
        ht, hi = _stage(head.path, raw)
    except BaseException:
        if rt is not None:
            rt.unlink(missing_ok=True)
        raise
    return Prepared(head, ht, hi, report, rt, ri,
                    tuple((Path(p).absolute(), token) for p, token in guards))


def discard(prepared: Prepared) -> None:
    """Only the invocation's own unpublished small staging files, lock-free."""
    for path, token in ((prepared.head_temp, prepared.head_temp_identity),
                        (prepared.report_temp, prepared.report_temp_identity)):
        if path is not None and exact_identity(path) == token:
            path.unlink()


def publish(prepared: Prepared, *, bus: Path, require_existing=True,
            wait_seconds=.2, max_hold_seconds=.25) -> dict:
    """Fixed critical section: exact metadata CAS and at most two renames.

    Contention/conflict is a caller-visible retry, not evidence of owner death.
    This elapsed-time check cannot preempt a blocked kernel metadata syscall;
    the API deliberately has no unbounded loop, callback, fsync or body read.
    """
    if not 0 <= wait_seconds <= .5 or not 0 < max_hold_seconds <= .5:
        raise ValueError("short storage commit requires bounded wait/hold")
    started = None
    try:
        with lock_wait_seconds(wait_seconds):
            with bus_lock(Path(bus), require_existing=require_existing):
                started = time.monotonic()
                checks = ((prepared.head.path, prepared.head.identity),
                          (prepared.head_temp, prepared.head_temp_identity),
                          *prepared.guards)
                if prepared.report is not None:
                    checks += ((prepared.report, None),
                               (prepared.report_temp, prepared.report_temp_identity))
                for path, expected in checks:
                    if time.monotonic() - started > max_hold_seconds:
                        raise StorageConflict("short commit time budget exhausted")
                    if exact_identity(path) != expected:
                        raise StorageConflict(f"exact metadata CAS conflict: {path}")
                if time.monotonic() - started > max_hold_seconds:
                    raise StorageConflict("short commit time budget exhausted")
                if prepared.report is not None:
                    os.replace(prepared.report_temp, prepared.report)
                os.replace(prepared.head_temp, prepared.head.path)
        return {"adopted": True, "storage_revision":
                prepared.head.value.get("storage_revision", 0) + 1,
                "lock_hold_seconds": time.monotonic() - started}
    finally:
        # Staging cleanup is intentionally after releasing the global lock.
        discard(prepared)
