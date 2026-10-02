"""Fail-closed, process-only receipt shape for a future H3937 worker.

This module cannot launch a worker or release a screen lease. The Windows Job
backend is deliberately supplied by the caller and needs separate review.
The Job and WMI fields here are backend claims, not fresh OS observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Callable


class WorkerProofError(ValueError):
    """A worker cleanup assertion has insufficient or inconsistent evidence."""


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise WorkerProofError(f"not a JSON object: {path}")
    return value


def _same_path(first: object, second: Path) -> bool:
    if type(first) is not str or not first:
        return False
    try:
        return os.path.normcase(os.path.realpath(first)) == os.path.normcase(
            os.path.realpath(second)
        )
    except (OSError, ValueError):
        return False


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _nonnegative_number(value: object) -> bool:
    return type(value) in (float, int) and value >= 0


def _created_utc(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        created = datetime.fromisoformat(value)
    except ValueError:
        return False
    return created.tzinfo is not None and created.utcoffset().total_seconds() == 0


@dataclass(frozen=True)
class FrozenWorkerCommand:
    argv: tuple[str, ...]
    executable_sha256: str
    actual_argv: tuple[str, ...]
    actual_executable_path: str
    actual_executable_sha256: str
    expected_parent_pid: int
    expected_parent_creation_filetime_100ns: int
    timeout_seconds: float

    def validate(self) -> None:
        if (
            len(self.argv) < 2
            or not all(type(part) is str and part for part in self.argv)
            or len(self.actual_argv) < 2
            or not all(type(part) is str and part for part in self.actual_argv)
            or type(self.actual_executable_path) is not str
            or not self.actual_executable_path
            or re.fullmatch(r"[A-F0-9]{64}", self.executable_sha256) is None
            or re.fullmatch(r"[A-F0-9]{64}", self.actual_executable_sha256) is None
            or not _positive_int(self.expected_parent_pid)
            or not _positive_int(self.expected_parent_creation_filetime_100ns)
            or type(self.timeout_seconds) not in (float, int)
            or self.timeout_seconds <= 0
        ):
            raise WorkerProofError("frozen worker command is malformed")
        if _sha(Path(self.argv[0])) != self.executable_sha256:
            raise WorkerProofError("worker executable bytes changed")
        if _sha(Path(self.actual_executable_path)) != self.actual_executable_sha256:
            raise WorkerProofError("actual Python child executable bytes changed")


@dataclass(frozen=True)
class WorkerExitEvidence:
    launcher_pid: int
    actual_worker_pid: int
    creation_filetime_100ns: int
    creation_utc: str
    executable: str
    argv: tuple[str, ...]
    actual_creation_filetime_100ns: int
    actual_creation_utc: str
    actual_executable: str
    actual_argv: tuple[str, ...]
    returncode: int
    inner_receipt_sha256: str
    outer_receipt_sha256: str
    stdout_sha256: str
    stderr_sha256: str


def verify_worker_exit(
    *, output: Path, frozen: FrozenWorkerCommand,
    started_monotonic: float, now: Callable[[], float] = time.monotonic,
) -> WorkerExitEvidence:
    """Validate a pinned Job exit receipt; never certify native cleanup.

    Call after the backend has returned. Hashing and JSON parsing count against
    the original full-chain deadline; no slow final receipt can become GREEN.
    External mutation after this function returns remains a separate operator
    release gate, and the clock provider must be trusted and side-effect free.
    """
    frozen.validate()
    if output.is_symlink() or not output.is_dir():
        raise WorkerProofError("worker output directory unavailable")
    inner_dir = output / "worker"
    inner_path = inner_dir / "receipt.json"
    outer_path = output / "outer-receipt.json"
    outer_marker = output / "outer-unsafe-marker.json"
    inner_marker = inner_dir / "unsafe-marker.json"
    stdout_path = inner_dir / "worker.stdout.bin"
    stderr_path = inner_dir / "worker.stderr.bin"
    paths = (inner_dir, inner_path, outer_path, outer_marker,
             inner_marker, stdout_path, stderr_path)
    if any(path.is_symlink() for path in paths):
        raise WorkerProofError("worker evidence includes a symlink")
    if not all(path.is_file() for path in paths[1:]):
        raise WorkerProofError("worker evidence is incomplete")
    inner = _object(inner_path)
    outer = _object(outer_path)
    identity = inner.get("worker_identity")
    actual = inner.get("actual_worker_identity")
    before = inner.get("job_before_resume")
    after_resume = inner.get("job_after_resume")
    after = inner.get("job_after_cleanup")
    if (type(identity) is not dict or type(actual) is not dict
            or type(before) is not dict or type(after_resume) is not dict
            or type(after) is not dict):
        raise WorkerProofError("launcher, actual child, or Job accounting missing")
    inner_sha = _sha(inner_path)
    outer_sha = _sha(outer_path)
    outer_marker_sha = _sha(outer_marker)
    inner_marker_sha = _sha(inner_marker)
    stdout_sha = _sha(stdout_path)
    stderr_sha = _sha(stderr_path)
    if (
        inner.get("schema") != "xar.fixture.worker-process-proof.v1"
        or outer.get("schema") != "xar.fixture.worker-process-outer.v2"
        or inner.get("status") not in ("RED", "GREEN_PROCESS_TREE_EXIT_ONLY")
        or outer.get("status") not in ("RED", "GREEN_PROCESS_TREE_EXIT_ONLY")
        or outer.get("status") != inner.get("status")
        or outer.get("inner_receipt_path") != str(inner_path)
        or outer.get("inner_receipt_sha256") != inner_sha
        or outer.get("inner_status") != inner.get("status")
        or outer.get("outer_marker_sha256") != outer_marker_sha
        or inner.get("unsafe_marker_sha256") != inner_marker_sha
        or not _same_path(inner.get("unsafe_marker_path"), inner_marker)
        or inner.get("stdout_sha256") != stdout_sha
        or inner.get("stderr_sha256") != stderr_sha
        or not _same_path(inner.get("stdout_path"), stdout_path)
        or not _same_path(inner.get("stderr_path"), stderr_path)
    ):
        raise WorkerProofError("worker receipt bytes or paths differ")
    pid = identity.get("pid")
    creation_filetime = identity.get("creation_filetime_100ns")
    created = identity.get("creation_utc")
    launcher_argv = identity.get("argv")
    if (
        not _positive_int(pid)
        or pid != inner.get("worker_pid")
        or identity.get("parent_pid") != frozen.expected_parent_pid
        or identity.get("parent_creation_filetime_100ns")
           != frozen.expected_parent_creation_filetime_100ns
        or identity.get("job_member") is not True
        or not _positive_int(creation_filetime)
        or not _created_utc(created)
        or not _same_path(identity.get("exe"), Path(frozen.argv[0]))
        or type(launcher_argv) is not list
        or tuple(launcher_argv) != frozen.argv
    ):
        raise WorkerProofError("live launcher PID, creation, executable, or argv differs")
    actual_pid = actual.get("pid")
    actual_argv = actual.get("argv")
    if (
        not _positive_int(actual_pid)
        or not _positive_int(actual.get("creation_filetime_100ns"))
        or not _created_utc(actual.get("creation_utc"))
        or not _same_path(actual.get("exe"), Path(frozen.actual_executable_path))
        or type(actual_argv) is not list
        or tuple(actual_argv) != frozen.actual_argv
        or actual.get("observed_while_running") is not True
        or actual.get("wmi_toolhelp_cross_checked") is not True
        or actual.get("job_member") is not True
        or actual_pid == pid
        or actual.get("parent_pid") != pid
    ):
        raise WorkerProofError("actual Python child identity or launcher chain unproven")
    returncode = inner.get("worker_returncode")
    if (
        type(returncode) is not int
        or inner.get("worker_exited") is not True
        or inner.get("timeout") is not False
        or outer.get("error") is not None
        or inner.get("watchdog_error") is not None
        or inner.get("watchdog_fired_at_elapsed") is not None
        or inner.get("watchdog_action") is not None
        or inner.get("child_survived_worker") is not False
        or inner.get("job_terminated") is not False
        or inner.get("unassigned_worker_killed") is not False
        or inner.get("job_closed") is not True
        or inner.get("job_zero_active") is not True
        or type(before.get("active")) is not int or before["active"] != 1
        or type(before.get("total")) is not int or before["total"] != 1
        or type(after_resume.get("total")) is not int
        or after_resume["total"] < (2 if actual_pid != pid else 1)
        or type(after.get("active")) is not int or after["active"] != 0
        or type(after.get("total")) is not int
        or after["total"] < after_resume["total"]
        or not _positive_int(inner.get("resumed_tid"))
        or (inner["status"] == "GREEN_PROCESS_TREE_EXIT_ONLY" and returncode != 0)
        or (outer["status"] == "GREEN_PROCESS_TREE_EXIT_ONLY" and returncode != 0)
        or (inner["status"] == "GREEN_PROCESS_TREE_EXIT_ONLY"
            and inner.get("error") is not None)
        or (inner["status"] == "RED" and (
            returncode == 0 or inner.get("error") != f"worker returncode {returncode}"))
    ):
        raise WorkerProofError("Job worker exit or descendant clearance unproven")
    if (
        not _nonnegative_number(inner.get("deadline_seconds_from_entry"))
        or not _nonnegative_number(outer.get("deadline_seconds_from_entry"))
        or inner["deadline_seconds_from_entry"] <= 0
        or inner["deadline_seconds_from_entry"] > frozen.timeout_seconds
        or outer["deadline_seconds_from_entry"] != frozen.timeout_seconds
        or not _nonnegative_number(inner.get("elapsed_seconds_before_receipt"))
        or not _nonnegative_number(outer.get("elapsed_seconds_before_receipt"))
        or inner["elapsed_seconds_before_receipt"] > frozen.timeout_seconds
        or outer["elapsed_seconds_before_receipt"] > frozen.timeout_seconds
        or not 0 <= now() - started_monotonic <= frozen.timeout_seconds
    ):
        raise WorkerProofError("full-chain deadline expired during evidence finalization")
    # Final byte readback has no callbacks after it and counts toward deadline.
    frozen.validate()
    final_hashes = {
        inner_path: inner_sha, outer_path: outer_sha,
        outer_marker: outer_marker_sha, inner_marker: inner_marker_sha,
        stdout_path: stdout_sha, stderr_path: stderr_sha,
    }
    if any(_sha(path) != expected for path, expected in final_hashes.items()):
        raise WorkerProofError("worker evidence changed during verification")
    if not 0 <= now() - started_monotonic <= frozen.timeout_seconds:
        raise WorkerProofError("full-chain deadline expired after final byte readback")
    return WorkerExitEvidence(
        launcher_pid=pid, actual_worker_pid=actual_pid,
        creation_filetime_100ns=creation_filetime,
        creation_utc=created, executable=str(identity["exe"]),
        argv=tuple(launcher_argv),
        actual_creation_filetime_100ns=actual["creation_filetime_100ns"],
        actual_creation_utc=actual["creation_utc"],
        actual_executable=str(actual["exe"]),
        actual_argv=tuple(actual_argv), returncode=returncode,
        inner_receipt_sha256=inner_sha, outer_receipt_sha256=outer_sha,
        stdout_sha256=stdout_sha, stderr_sha256=stderr_sha,
    )
