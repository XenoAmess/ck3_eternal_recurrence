"""H2743 screen-bus CAS protocol candidate; the live runner remains stopped.

This module is testable with an isolated bus. It does not authorize a screen
claim or remove the runner's LIVE_STOP_CAS_MIGRATION_PENDING guard.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Iterator


REVIEWED_BUS_CLI_SHA256 = "D6629F52EE098C709C5A85ADBC629F40E8B2724BE9CC1F29FAF48AF215E96121"
AUTHORITY_BUS = Path("D:/workspace/.codex-task-bus")
SCREEN_RESOURCE = "ck3-screen:acquired"
SCHEMA = "codex.task_bus.v1"


class ScreenCasStop(RuntimeError):
    """A failed or ambiguous bus operation must not be retried blindly."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


@contextmanager
def locked_bus_read(bus_dir: Path) -> Iterator[None]:
    lock_path = bus_dir / ".lock"
    if lock_path.is_symlink() or not lock_path.is_file():
        raise ScreenCasStop("task bus read lock unavailable")
    with lock_path.open("r+b") as handle:
        handle.seek(0)
        deadline = time.monotonic() + 15
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise ScreenCasStop("task bus read lock timed out") from error
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class ScreenCasProtocol:
    def __init__(self, *, source: Path, bus_dir: Path, repo: Path,
                 python: Path, evidence_dir: Path,
                 expected_sha256: str = REVIEWED_BUS_CLI_SHA256) -> None:
        if not re.fullmatch(r"[A-F0-9]{64}", expected_sha256):
            raise ScreenCasStop("task-bus CLI SHA pin is malformed")
        try:
            resolved_bus = bus_dir.resolve(strict=True)
        except OSError as error:
            raise ScreenCasStop("isolated task bus path is unavailable") from error
        if not resolved_bus.is_dir():
            raise ScreenCasStop("isolated task bus directory is unavailable")
        if resolved_bus == AUTHORITY_BUS.resolve():
            raise ScreenCasStop("AUTHORITY_STOP: this protocol candidate only accepts an isolated bus")
        self.source = source
        self.bus_dir = resolved_bus
        self.repo = repo
        self.python = python
        self.evidence_dir = evidence_dir
        self.expected_sha256 = expected_sha256
        self.task_id: str | None = None
        self.sequence: int | None = None
        self.event: dict[str, object] | None = None
        self.released = False
        self.uncertain = False
        self.operation_count = 0
        evidence_dir.mkdir(exist_ok=False)

    def require_isolated_bus(self) -> None:
        try:
            resolved = self.bus_dir.resolve(strict=True)
        except OSError as error:
            raise ScreenCasStop("isolated task bus path disappeared") from error
        if resolved != self.bus_dir or resolved == AUTHORITY_BUS.resolve():
            raise ScreenCasStop("AUTHORITY_STOP: isolated bus path changed")

    def require_cli_pair(self) -> None:
        self.require_isolated_bus()
        installed = self.bus_dir / "bin" / "codex_task_bus.py"
        if (self.source.is_symlink() or installed.is_symlink()
                or not self.source.is_file() or not installed.is_file()
                or sha256(self.source) != self.expected_sha256
                or sha256(installed) != self.expected_sha256):
            raise ScreenCasStop("reviewed task-bus source and installed CLI SHA pair absent")

    def _readback(self, task_id: str, event: dict[str, object],
                  *, released: bool) -> dict[str, object]:
        self.require_isolated_bus()
        sequence = event.get("sequence")
        if type(sequence) is not int or sequence <= 0:
            raise ScreenCasStop("CAS event sequence missing")
        with locked_bus_read(self.bus_dir):
            tasks_dir = self.bus_dir / "tasks"
            events_path = self.bus_dir / "events.jsonl"
            sequence_path = self.bus_dir / "sequence.txt"
            if (not tasks_dir.is_dir() or tasks_dir.is_symlink()
                    or events_path.is_symlink() or sequence_path.is_symlink()):
                raise ScreenCasStop("task bus readback files unavailable")
            try:
                rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
                tail = int(sequence_path.read_text(encoding="ascii").strip())
            except (OSError, ValueError, TypeError) as error:
                raise ScreenCasStop("task bus event readback unavailable") from error
            if (not rows or len(rows) != tail
                    or any(type(row.get("sequence")) is not int
                           or row["sequence"] != index
                           for index, row in enumerate(rows, 1))):
                raise ScreenCasStop("task bus event sequence gap or tail mismatch")
            if sequence > tail or rows[sequence - 1] != event:
                raise ScreenCasStop("CAS receipt event differs from authoritative event")
            task_path = tasks_dir / f"{task_id}.json"
            if task_path.is_symlink():
                raise ScreenCasStop("screen task snapshot is a link")
            try:
                task = json.loads(task_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError) as error:
                raise ScreenCasStop("screen task snapshot unreadable") from error
            expected_state = "done" if released else "running"
            expected_resources = [] if released else [SCREEN_RESOURCE]
            if event.get("state") != expected_state or event.get("resources") != expected_resources:
                raise ScreenCasStop("CAS event state or resources differ")
            if (task.get("schema") != SCHEMA or task.get("task_id") != task_id
                    or task.get("last_sequence") != sequence
                    or task.get("state") != expected_state
                    or task.get("resources") != expected_resources):
                raise ScreenCasStop("screen task snapshot does not match CAS receipt")
            owners = []
            for path in tasks_dir.glob("*.json"):
                if path.is_symlink():
                    raise ScreenCasStop("task snapshot link blocks owner readback")
                try:
                    other = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError) as error:
                    raise ScreenCasStop("task snapshot unreadable during owner readback") from error
                resources = other.get("resources")
                if (type(resources) is not list
                        or any(type(item) is not str for item in resources)):
                    raise ScreenCasStop("task resources malformed during owner readback")
                if SCREEN_RESOURCE in resources:
                    owners.append(other.get("task_id"))
            if owners != ([] if released else [task_id]):
                raise ScreenCasStop("global screen owner readback differs")
            return {"event": event, "task": task, "owners": owners,
                    "event_tail_sequence": tail}

    def _execute(self, kind: str, task_id: str, arguments: list[str],
                 *, released: bool,
                 prior_event: dict[str, object] | None = None) -> dict[str, object]:
        if self.uncertain:
            raise ScreenCasStop("previous CAS operation is ambiguous; no blind retry")
        self.operation_count += 1
        folder = self.evidence_dir / f"operation-{self.operation_count:03d}-{kind}"
        folder.mkdir(exist_ok=False)
        argv = [str(self.python), str(self.source), "--bus-dir", str(self.bus_dir),
                "--expected-cli-sha256", self.expected_sha256, *arguments]
        write_new(folder / "argv.json", {"argv": argv, "source_sha256": self.expected_sha256,
                                         "installed_sha256": self.expected_sha256})
        try:
            self.require_cli_pair()
            if prior_event is not None:
                self._readback(task_id, prior_event, released=False)
                self.require_cli_pair()
            try:
                completed = subprocess.run(argv, cwd=self.repo, capture_output=True,
                                           timeout=30, check=False)
            except subprocess.TimeoutExpired as error:
                (folder / "stdout.bin").write_bytes(error.stdout or b"")
                (folder / "stderr.bin").write_bytes(error.stderr or b"")
                write_new(folder / "process.json", {"returncode": None, "timed_out": True,
                          "stdout_sha256": sha256(folder / "stdout.bin"),
                          "stderr_sha256": sha256(folder / "stderr.bin")})
                raise ScreenCasStop("CAS command timed out; result is ambiguous") from error
            (folder / "stdout.bin").write_bytes(completed.stdout)
            (folder / "stderr.bin").write_bytes(completed.stderr)
            write_new(folder / "process.json", {"returncode": completed.returncode,
                      "stdout_sha256": sha256(folder / "stdout.bin"),
                      "stderr_sha256": sha256(folder / "stderr.bin")})
            if completed.returncode != 0 or completed.stderr:
                raise ScreenCasStop("CAS command refused or emitted stderr")
            receipt = json.loads(completed.stdout.decode("utf-8-sig"))
            event = receipt.get("event")
            task = receipt.get("task")
            if (receipt.get("schema") != SCHEMA or receipt.get("ok") is not True
                    or type(event) is not dict or type(task) is not dict
                    or event.get("kind") != kind or event.get("task_id") != task_id
                    or task.get("task_id") != task_id
                    or task.get("last_sequence") != event.get("sequence")):
                raise ScreenCasStop("CAS command receipt malformed")
            self.require_cli_pair()
            readback = self._readback(task_id, event, released=released)
            if readback["task"] != task:
                raise ScreenCasStop("CAS receipt snapshot differs from readback")
            write_new(folder / "readback.json", readback)
            self.require_cli_pair()
            return readback
        except BaseException as error:
            self.uncertain = True
            write_new(folder / "stop.json", {"type": type(error).__name__,
                      "reason": str(error), "retry_allowed": False})
            raise

    def claim(self, task_id: str, summary: str) -> dict[str, object]:
        if self.task_id is not None or self.uncertain:
            raise ScreenCasStop("screen claim already attempted")
        if type(task_id) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", task_id) is None:
            raise ScreenCasStop("screen task ID is invalid")
        result = self._execute("registered", task_id,
            ["register", "--task", task_id, "--repo", str(self.repo),
             "--summary", summary, "--resource", SCREEN_RESOURCE], released=False)
        self.task_id = task_id
        self.sequence = result["event"]["sequence"]
        self.event = result["event"]
        return result

    def heartbeat(self) -> dict[str, object]:
        if self.uncertain:
            raise ScreenCasStop("previous CAS operation is ambiguous; no blind retry")
        if self.task_id is None or self.sequence is None or self.event is None or self.released:
            raise ScreenCasStop("screen heartbeat has no active exact claim")
        result = self._execute("heartbeat", self.task_id,
            ["heartbeat", "--task", self.task_id, "--repo", str(self.repo),
             "--expected-sequence", str(self.sequence)], released=False,
            prior_event=self.event)
        if result["event"]["sequence"] <= self.sequence:
            self.uncertain = True
            raise ScreenCasStop("heartbeat did not advance the sequence")
        self.sequence = result["event"]["sequence"]
        self.event = result["event"]
        return result

    def release(self, summary: str, *, cleanup_proven: bool) -> dict[str, object]:
        if self.uncertain:
            raise ScreenCasStop("previous CAS operation is ambiguous; no blind retry")
        if cleanup_proven is not True:
            raise ScreenCasStop("screen release requires externally proven process cleanup")
        if self.task_id is None or self.sequence is None or self.event is None or self.released:
            raise ScreenCasStop("screen release has no active exact claim")
        result = self._execute("completed", self.task_id,
            ["release-screen-cas", "--task", self.task_id,
             "--expected-sequence", str(self.sequence), "--summary", summary],
            released=True, prior_event=self.event)
        if result["event"]["sequence"] <= self.sequence:
            self.uncertain = True
            raise ScreenCasStop("release did not advance the sequence")
        self.sequence = result["event"]["sequence"]
        self.event = result["event"]
        self.released = True
        return result
