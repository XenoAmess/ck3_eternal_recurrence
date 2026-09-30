"""Fail-closed shared-bus admission for a managed CK3 screen owner.

This module never acquires or releases the screen. An operator must register a
fresh task through the reviewed CAS bus first. The caller supplies that exact
task's latest sequence; a successful heartbeat advances it once. All paths in
the production entry are fixed by the caller, not by an untrusted receipt.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading


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


def call_bus(source: Path, bus_dir: Path, expected_sha: str, *argv: str) -> dict:
    checked_cli_pair(source, bus_dir / "bin" / "codex_task_bus.py", expected_sha)
    result = subprocess.run(
        [sys.executable, str(source), "--bus-dir", str(bus_dir),
         "--expected-cli-sha256", expected_sha, *argv],
        capture_output=True, text=True, timeout=60, check=False,
    )
    checked_cli_pair(source, bus_dir / "bin" / "codex_task_bus.py", expected_sha)
    require(result.returncode == 0, f"bus CAS/readback failed (exit {result.returncode}): {result.stdout[-1000:]} {result.stderr[-500:]}")
    try:
        body = json.loads(result.stdout)
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
    return head


def renew_once(*, source: Path, bus_dir: Path, expected_sha: str,
               task_id: str, expected_sequence: int, repo: Path) -> dict:
    require(type(task_id) is str and TASK_PATTERN.fullmatch(task_id) is not None,
            "valid screen task ID is required")
    require(type(expected_sequence) is int and expected_sequence > 0,
            "positive screen task CAS sequence is required")
    require(repo.is_dir(), "screen task checkout is unavailable")
    head = checkout_head(repo)
    before = call_bus(source, bus_dir, expected_sha, "list", "--stale-after", str(MAX_AGE_SECONDS))
    checked_owner(before.get("tasks"), task_id, expected_sequence, repo, head)
    changed = call_bus(source, bus_dir, expected_sha, "heartbeat", "--task", task_id,
                       "--expected-sequence", str(expected_sequence), "--repo", str(repo))
    task, event = changed.get("task"), changed.get("event")
    require(isinstance(task, dict) and isinstance(event, dict) and
            event.get("kind") == "heartbeat" and event.get("task_id") == task_id and
            type(event.get("sequence")) is int and event["sequence"] > expected_sequence and
            task.get("last_sequence") == event["sequence"],
            "bus heartbeat did not return a new CAS sequence")
    after = call_bus(source, bus_dir, expected_sha, "list", "--stale-after", str(MAX_AGE_SECONDS))
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
                 abort: threading.Event, interval_seconds: int = 180) -> None:
        require(30 <= interval_seconds <= 240, "lease interval must be 30..240 seconds")
        self.source, self.bus_dir, self.expected_sha = source, bus_dir, expected_sha
        self.task_id, self.sequence, self.repo = task_id, sequence, repo
        self.journal, self.abort, self.interval_seconds = journal, abort, interval_seconds
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
            self.require_live()
            try:
                row = renew_once(
                    source=self.source, bus_dir=self.bus_dir,
                    expected_sha=self.expected_sha, task_id=self.task_id,
                    expected_sequence=self.sequence, repo=self.repo)
                self.sequence = row["sequence"]
                self._append({"at_utc": datetime.now(timezone.utc).isoformat(),
                              "result": "OWNED_CAS", "lease": row})
                return row
            except BaseException as error:
                self.failure = repr(error)
                self.abort.set()
                self._append({"at_utc": datetime.now(timezone.utc).isoformat(),
                              "result": "LOST_OR_UNCERTAIN_STOP", "error": self.failure,
                              "expected_sequence": self.sequence})
                raise

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
