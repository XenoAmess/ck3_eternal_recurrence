"""Fail-closed shared-bus admission for a managed CK3 screen owner.

This module never acquires or releases the screen. An operator must register a
fresh task through the reviewed CAS bus first. The caller supplies that exact
task's latest sequence; a successful heartbeat advances it once. All paths in
the production entry are fixed by the caller, not by an untrusted receipt.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid


SCREEN = "ck3-screen:acquired"
SCHEMA = "codex.task_bus.v1"
MAX_AGE_SECONDS = 600
MAX_FUTURE_SECONDS = 10
TASK_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SHA_PATTERN = re.compile(r"[A-F0-9]{64}\Z")


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def checked_cli_pair(source: Path, installed: Path, expected_sha: str) -> str:
    require(type(expected_sha) is str and SHA_PATTERN.fullmatch(expected_sha) is not None,
            "exact uppercase bus CLI SHA-256 is required")
    require(source.is_file() and installed.is_file(), "bus source or installed CLI is missing")
    require(source.resolve() != installed.resolve(), "bus source and installed CLI must be distinct")
    require(digest(source) == expected_sha and digest(installed) == expected_sha,
            "bus source or installed CLI bytes differ from the pinned SHA-256")
    return expected_sha


def _write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")


def _write_new_bytes(path: Path, value: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def abort_recorder_process(process: subprocess.Popen, *, receipt: Path,
                           unsafe_marker: Path) -> None:
    """Reap a harmless or debug recorder child, or leave an explicit unsafe mark."""
    if process.poll() is not None:
        return
    try:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
        require(process.poll() is not None, "recorder did not exit after lease abort")
        _write_new(receipt, {"at_utc": datetime.now(timezone.utc).isoformat(),
                             "result": "EXITED", "pid": process.pid,
                             "returncode": process.returncode})
    except BaseException as error:
        _write_new(unsafe_marker, {"at_utc": datetime.now(timezone.utc).isoformat(),
                                   "result": "UNPROVEN", "pid": process.pid,
                                   "error": repr(error)})
        raise


def call_bus(source: Path, bus_dir: Path, expected_sha: str, *argv: str,
             audit_dir: Path | None = None) -> dict:
    checked_cli_pair(source, bus_dir / "bin" / "codex_task_bus.py", expected_sha)
    command = [sys.executable, str(source), "--bus-dir", str(bus_dir),
               "--expected-cli-sha256", expected_sha, *argv]
    evidence = None
    if audit_dir is not None:
        audit_dir.mkdir(parents=True, exist_ok=True)
        evidence = audit_dir / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex)
        evidence.mkdir(exist_ok=False)
        _write_new(evidence / "argv.json", {"argv": command, "source_cli_sha256": expected_sha})
    try:
        result = subprocess.run(command, capture_output=True, text=False,
                                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                                timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        if evidence is not None:
            stdout = getattr(error, "stdout", None) or ""
            stderr = getattr(error, "stderr", None) or ""
            stdout = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
            stderr = stderr.encode("utf-8") if isinstance(stderr, str) else stderr
            _write_new_bytes(evidence / "stdout.bin", stdout)
            _write_new_bytes(evidence / "stderr.bin", stderr)
            _write_new(evidence / "result.json", {"result": "COMMAND_ERROR", "error": repr(error)})
        raise
    if evidence is not None:
        _write_new_bytes(evidence / "stdout.bin", result.stdout)
        _write_new_bytes(evidence / "stderr.bin", result.stderr)
        _write_new(evidence / "result.json", {"exit_code": result.returncode,
                                              "stdout_sha256": hashlib.sha256(result.stdout).hexdigest().upper(),
                                              "stderr_sha256": hashlib.sha256(result.stderr).hexdigest().upper()})
    checked_cli_pair(source, bus_dir / "bin" / "codex_task_bus.py", expected_sha)
    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8", "replace")
    require(result.returncode == 0, f"bus CAS/readback failed (exit {result.returncode}): {stdout[-1000:]} {stderr[-500:]}")
    try:
        body = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as error:
        raise RuntimeError("bus returned no valid JSON") from error
    require(isinstance(body, dict) and body.get("schema") == SCHEMA and body.get("ok") is True,
            "bus response is not a successful codex.task_bus.v1 result")
    return body


def checked_owner(tasks: object, task_id: str, sequence: int, repo: Path,
                  head: str, *, now: datetime | None = None) -> dict:
    require(isinstance(tasks, list), "bus list has no task array")
    screen_rows = []
    matching = []
    for row in tasks:
        require(isinstance(row, dict) and row.get("schema") == SCHEMA,
                "bus task row has an invalid schema")
        resources = row.get("resources")
        require(isinstance(resources, list) and all(isinstance(item, str) for item in resources),
                "bus task row has invalid resources")
        if SCREEN in resources:
            screen_rows.append(row)
        if row.get("task_id") == task_id:
            matching.append(row)
    require(len(screen_rows) == 1 and len(matching) == 1 and screen_rows[0] is matching[0],
            "screen resource is absent, stale, unsafe, or claimed by another task")
    owner = matching[0]
    require(owner.get("state") == "running" and owner.get("resources") == [SCREEN] and
            type(owner.get("last_sequence")) is int and owner["last_sequence"] == sequence,
            "screen task is not the exact running CAS owner")
    require(isinstance(owner.get("repo"), str) and Path(owner["repo"]).resolve() == repo.resolve(),
            "screen task belongs to another checkout")
    git = owner.get("git")
    require(isinstance(git, dict) and git.get("head") == head and
            type(git.get("dirty_entries")) is int and git["dirty_entries"] == 0,
            "screen task checkout HEAD or cleanliness differs")
    now = now or datetime.now(timezone.utc)
    try:
        updated = datetime.fromisoformat(owner["updated_at_utc"])
        age = (now - updated).total_seconds()
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("screen task timestamp is invalid") from error
    require(updated.tzinfo is not None and -MAX_FUTURE_SECONDS <= age <= MAX_AGE_SECONDS,
            "screen task heartbeat is stale or from the future")
    require(owner.get("stale") is False or "stale" not in owner,
            "bus list marks the screen task stale")
    return owner


def checkout_head(repo: Path) -> str:
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                            capture_output=True, text=True, timeout=30, check=True)
    head = result.stdout.strip()
    require(re.fullmatch(r"[a-fA-F0-9]{40}", head) is not None,
            "checkout HEAD is unavailable")
    status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v1",
                             "--untracked-files=normal"], capture_output=True, text=True,
                            timeout=30, check=True)
    require(not status.stdout.strip(), "screen task checkout has current tracked or untracked changes")
    return head


def renew_once(*, source: Path, bus_dir: Path, expected_sha: str,
               task_id: str, expected_sequence: int, repo: Path,
               audit_dir: Path | None = None) -> dict:
    require(type(task_id) is str and TASK_PATTERN.fullmatch(task_id) is not None,
            "valid screen task ID is required")
    require(type(expected_sequence) is int and expected_sequence > 0,
            "positive screen task CAS sequence is required")
    require(repo.is_dir(), "screen task checkout is unavailable")
    head = checkout_head(repo)
    before = call_bus(source, bus_dir, expected_sha, "list", "--stale-after", str(MAX_AGE_SECONDS),
                      audit_dir=audit_dir)
    checked_owner(before.get("tasks"), task_id, expected_sequence, repo, head)
    changed = call_bus(source, bus_dir, expected_sha, "heartbeat", "--task", task_id,
                       "--expected-sequence", str(expected_sequence), "--repo", str(repo),
                       audit_dir=audit_dir)
    task, event = changed.get("task"), changed.get("event")
    require(isinstance(task, dict) and isinstance(event, dict) and
            event.get("kind") == "heartbeat" and event.get("task_id") == task_id and
            type(event.get("sequence")) is int and event["sequence"] > expected_sequence and
            task.get("last_sequence") == event["sequence"],
            "bus heartbeat did not return a new CAS sequence")
    after = call_bus(source, bus_dir, expected_sha, "list", "--stale-after", str(MAX_AGE_SECONDS),
                     audit_dir=audit_dir)
    owner = checked_owner(after.get("tasks"), task_id, event["sequence"], repo, head)
    require({key: owner.get(key) for key in ("task_id", "state", "resources", "last_sequence", "repo", "git")} ==
            {key: task.get(key) for key in ("task_id", "state", "resources", "last_sequence", "repo", "git")},
            "bus heartbeat and independent locked list differ")
    checked_cli_pair(source, bus_dir / "bin" / "codex_task_bus.py", expected_sha)
    return {"schema": "xar.promo.screen-lease-cas/v1", "task_id": task_id,
            "expected_sequence": expected_sequence, "sequence": event["sequence"],
            "event_id": event.get("event_id"), "updated_at_utc": owner["updated_at_utc"],
            "repo": str(repo.resolve()), "checkout_head": head,
            "source_cli": str(source.resolve()), "installed_cli": str((bus_dir / "bin" / "codex_task_bus.py").resolve()),
            "cli_sha256": expected_sha, "screen_resource": SCREEN}


class ScreenLeaseKeeper:
    """Renew a single admitted sequence; abort the managed session on any RED."""

    def __init__(self, *, source: Path, bus_dir: Path, expected_sha: str,
                 task_id: str, sequence: int, repo: Path, journal: Path,
                 abort: threading.Event, interval_seconds: int = 180,
                 audit_dir: Path | None = None,
                 on_abort: Callable[[], None] | None = None) -> None:
        require(30 <= interval_seconds <= 240, "lease interval must be 30..240 seconds")
        self.source, self.bus_dir, self.expected_sha = source, bus_dir, expected_sha
        self.task_id, self.sequence, self.repo = task_id, sequence, repo
        self.journal, self.abort, self.interval_seconds = journal, abort, interval_seconds
        self.audit_dir = audit_dir
        self.on_abort = on_abort
        self.failure: str | None = None
        self._lock = threading.Lock()
        self._done = threading.Event()
        self._thread: threading.Thread | None = None

    def _append(self, row: dict) -> None:
        encoded = (json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        with self.journal.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())

    def start(self) -> None:
        require(self._thread is None and self.journal.parent.is_dir(),
                "new screen lease keeper journal is required")
        with self.journal.open("xb"):
            pass
        self._thread = threading.Thread(target=self._run, name="screen-bus-cas-keeper", daemon=True)
        self._thread.start()

    def refresh(self) -> dict:
        with self._lock:
            return self._refresh_locked()

    def _refresh_locked(self) -> dict:
        self.require_live()
        try:
            row = renew_once(
                source=self.source, bus_dir=self.bus_dir,
                expected_sha=self.expected_sha, task_id=self.task_id,
                expected_sequence=self.sequence, repo=self.repo,
                audit_dir=self.audit_dir)
            self.sequence = row["sequence"]
            self._append({"at_utc": datetime.now(timezone.utc).isoformat(),
                          "result": "OWNED_CAS", "lease": row})
            return row
        except BaseException as error:
            self.failure = repr(error)
            self.abort.set()
            try:
                self._append({"at_utc": datetime.now(timezone.utc).isoformat(),
                              "result": "LOST_OR_UNCERTAIN_STOP", "error": self.failure,
                              "expected_sequence": self.sequence})
            finally:
                if self.on_abort is not None:
                    self.on_abort()
            raise

    @contextmanager
    def process_create_gate(self) -> Iterator[None]:
        """Keep the renewal lock through a watchdog or CK3 process creation."""
        with self._lock:
            self._refresh_locked()
            self.require_live()
            yield

    def require_live(self) -> None:
        require(self.failure is None and not self.abort.is_set(),
                "screen lease lost or managed session is stopping")

    def _run(self) -> None:
        while not self._done.wait(self.interval_seconds):
            try:
                self.refresh()
            except BaseException:
                return

    def stop(self) -> None:
        self._done.set()
        if self._thread is not None:
            self._thread.join(timeout=65)
            if self._thread.is_alive():
                self.failure = "CAS keeper did not exit after stop"
                self.abort.set()
                self._append({"at_utc": datetime.now(timezone.utc).isoformat(),
                              "result": "KEEPER_NOT_EXITED_STOP"})

    def report(self) -> dict:
        return {"schema": "xar.promo.screen-lease-keeper/v1", "task_id": self.task_id,
                "last_sequence": self.sequence, "failure": self.failure,
                "thread_exited": self._thread is not None and not self._thread.is_alive(),
                "journal": str(self.journal.resolve())}
