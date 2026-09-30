#!/usr/bin/env python3
"""Cooperative, filesystem-backed status and notification bus for Codex tasks."""

from __future__ import annotations

import argparse
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid


SCHEMA = "codex.task_bus.v1"
SCREEN_RESOURCE = "ck3-screen:acquired"
SCREEN_LEASE_MAX_AGE_SECONDS = 600
SCREEN_CLOCK_SKEW_SECONDS = 10
TASK_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}")
STATES = ("running", "waiting", "blocked", "done")
DEFAULT_BUS = Path(
    os.environ.get(
        "CODEX_TASK_BUS_DIR",
        str(Path(__file__).resolve().parents[2] / ".codex-task-bus"),
    )
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def task_id(value: str) -> str:
    if TASK_ID_PATTERN.fullmatch(value) is None:
        raise argparse.ArgumentTypeError(
            "task ID must contain 1-96 ASCII letters, digits, dots, underscores, or hyphens"
        )
    return value


def recipient(value: str) -> str:
    return value if value == "*" else task_id(value)


def task_filename(value: str) -> str:
    return value + ".json"


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@contextmanager
def bus_lock(bus: Path, *, require_existing: bool = False):
    if require_existing:
        if not bus.is_dir():
            raise CompareConflict("existing task bus is unavailable")
    else:
        bus.mkdir(parents=True, exist_ok=True)
    lock_path = bus / ".lock"
    try:
        handle = lock_path.open("r+b" if require_existing else "a+b")
    except OSError as error:
        raise CompareConflict("existing task bus lock is unavailable") from error
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        if require_existing:
            handle.close()
            raise CompareConflict("existing task bus lock is empty")
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
    else:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def git_identity(repo: Path) -> dict[str, object]:
    def run(*args: str) -> str | None:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return completed.stdout.strip() if completed.returncode == 0 else None

    root = run("rev-parse", "--show-toplevel")
    if root is None:
        return {"repo": str(repo.resolve()), "git": None}
    status = run("status", "--porcelain=v1") or ""
    return {
        "repo": str(Path(root).resolve()),
        "git": {
            "head": run("rev-parse", "HEAD"),
            "branch": run("branch", "--show-current") or None,
            "dirty_entries": len(status.splitlines()),
        },
    }


def read_json(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def next_sequence(bus: Path) -> int:
    path = bus / "sequence.txt"
    current = int(path.read_text(encoding="ascii").strip()) if path.is_file() else 0
    sequence = current + 1
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(str(sequence) + "\n", encoding="ascii")
    os.replace(temporary, path)
    return sequence


def append_event(bus: Path, event: dict[str, object]) -> dict[str, object]:
    event = {
        "schema": SCHEMA,
        "sequence": next_sequence(bus),
        "event_id": uuid.uuid4().hex,
        "timestamp_utc": utc_now(),
        **event,
    }
    line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
    with (bus / "events.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return event


def task_path(bus: Path, value: str) -> Path:
    return bus / "tasks" / task_filename(value)


class CompareConflict(Exception):
    """A CAS precondition failed without changing task or event state."""

    def __init__(self, reason: str, observed: dict[str, object] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.observed = observed


def _fresh_screen_owner(snapshot: dict[str, object], now: datetime) -> bool:
    resources = snapshot.get("resources")
    if not isinstance(resources, list) or any(not isinstance(item, str) for item in resources):
        raise CompareConflict("task bus contains invalid resources", snapshot)
    if SCREEN_RESOURCE not in resources:
        return False
    if snapshot.get("state") == "done":
        return False
    try:
        updated = datetime.fromisoformat(str(snapshot["updated_at_utc"]))
        age = (now - updated).total_seconds()
    except (KeyError, TypeError, ValueError) as error:
        raise CompareConflict("screen owner has invalid update time", snapshot) from error
    if updated.tzinfo is None or age < -SCREEN_CLOCK_SKEW_SECONDS:
        raise CompareConflict("screen owner has missing or future timezone", snapshot)
    return age <= SCREEN_LEASE_MAX_AGE_SECONDS


def _current_screen_owners(bus: Path, now: datetime) -> list[str]:
    owners: list[str] = []
    for path in (bus / "tasks").glob("*.json"):
        try:
            snapshot = read_json(path)
        except (OSError, ValueError) as error:
            raise CompareConflict("task bus contains an unreadable snapshot") from error
        if not isinstance(snapshot, dict):
            raise CompareConflict("task bus contains an invalid snapshot")
        if _fresh_screen_owner(snapshot, now):
            owners.append(str(snapshot.get("task_id")))
    return owners


def _unreleased_screen_records(bus: Path) -> list[str]:
    records: list[str] = []
    for path in (bus / "tasks").glob("*.json"):
        try:
            snapshot = read_json(path)
        except (OSError, ValueError) as error:
            raise CompareConflict("task bus contains an unreadable snapshot") from error
        if not isinstance(snapshot, dict):
            raise CompareConflict("task bus contains an invalid snapshot")
        resources = snapshot.get("resources")
        if not isinstance(resources, list) or any(not isinstance(item, str) for item in resources):
            raise CompareConflict("task bus contains invalid resources", snapshot)
        if SCREEN_RESOURCE in resources:
            if snapshot.get("state") == "done":
                raise CompareConflict("done task still claims screen resource", snapshot)
            records.append(str(snapshot.get("task_id")))
    return records


def _require_screen_bus_files(bus: Path) -> int:
    if not (bus / "tasks").is_dir() or not (bus / "events.jsonl").is_file():
        raise CompareConflict("screen task bus files are incomplete")
    try:
        sequence = int((bus / "sequence.txt").read_text(encoding="ascii").strip())
    except (OSError, ValueError) as error:
        raise CompareConflict("screen task bus sequence is unavailable") from error
    if sequence < 0:
        raise CompareConflict("screen task bus sequence is invalid")
    tail = 0
    latest_task_events: dict[str, dict[str, object]] = {}
    try:
        with (bus / "events.jsonl").open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    raise CompareConflict("task bus event stream contains a blank line")
                event = json.loads(line)
                event_sequence = event.get("sequence")
                if type(event_sequence) is not int or event_sequence != tail + 1:
                    raise CompareConflict("task bus event sequence has a gap or duplicate")
                tail = event_sequence
                if event.get("kind") in {"registered", "status", "completed", "heartbeat"}:
                    value = event.get("task_id")
                    if (type(value) is not str
                            or TASK_ID_PATTERN.fullmatch(value) is None):
                        raise CompareConflict("task bus mutating event has invalid task ID")
                    latest_task_events[value] = event
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise CompareConflict("task bus event stream is unreadable") from error
    if tail != sequence:
        raise CompareConflict("task bus sequence differs from event tail")
    for value, event in latest_task_events.items():
        try:
            snapshot = read_json(task_path(bus, value))
        except (OSError, ValueError) as error:
            raise CompareConflict("task bus mutating event snapshot is unreadable") from error
        if (
            type(snapshot) is not dict
            or snapshot.get("schema") != SCHEMA
            or snapshot.get("task_id") != value
            or type(snapshot.get("last_sequence")) is not int
            or snapshot["last_sequence"] != event["sequence"]
            or snapshot.get("state") != event.get("state")
            or snapshot.get("resources") != event.get("resources")
        ):
            raise CompareConflict("task bus mutating event and task snapshot diverge")
    return sequence


def _unapplied_task_event(bus: Path, value: str, sequence: int) -> bool:
    try:
        with (bus / "events.jsonl").open("r", encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                event = json.loads(line)
                if (
                    event.get("task_id") == value
                    and event.get("kind") in {"registered", "status", "completed", "heartbeat"}
                    and type(event.get("sequence")) is int
                    and event["sequence"] > sequence
                ):
                    return True
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise CompareConflict("task bus event stream is unreadable") from error
    return False


def release_screen_cas(
    bus: Path, value: str, expected_sequence: int, *, summary: str,
    expected_cli_sha256: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Release one unchanged screen claim, retaining expired business as pending."""
    if type(expected_sequence) is not int or expected_sequence <= 0:
        raise CompareConflict("expected sequence must be a positive integer")
    if not bus.is_dir() or not (bus / "tasks").is_dir():
        raise CompareConflict("existing task bus is unavailable")
    with bus_lock(bus, require_existing=True):
        _require_cli_pair(bus, expected_cli_sha256)
        bus_sequence = _require_screen_bus_files(bus)
        try:
            previous = read_json(task_path(bus, value))
        except (OSError, ValueError) as error:
            raise CompareConflict("expected task snapshot is unreadable") from error
        if not isinstance(previous, dict):
            raise CompareConflict("expected task snapshot is missing")
        if (
            previous.get("schema") != SCHEMA
            or previous.get("task_id") != value
            or previous.get("state") != "running"
            or previous.get("resources") != [SCREEN_RESOURCE]
            or not isinstance(previous.get("repo"), str)
            or "git" not in previous
            or type(previous.get("last_sequence")) is not int
            or previous["last_sequence"] != expected_sequence
            or bus_sequence < expected_sequence
            or _unapplied_task_event(bus, value, expected_sequence)
        ):
            raise CompareConflict("expected task snapshot changed", previous)
        now = datetime.now(timezone.utc)
        if _unreleased_screen_records(bus) != [value]:
            raise CompareConflict("screen resource record is not unique", previous)
        expired = not _fresh_screen_owner(previous, now)
        snapshot = {
            **previous,
            "state": "waiting" if expired else "done",
            "summary": summary,
            "next_step": str(previous.get("next_step") or "") if expired else "",
            "resources": [],
            "updated_at_utc": utc_now(),
            "pid": os.getpid(),
        }
        event = append_event(
            bus,
            {
                "kind": "status" if expired else "completed",
                "task_id": value,
                "to": ["*"],
                "state": snapshot["state"],
                "summary": snapshot["summary"],
                "next_step": snapshot["next_step"],
                "resources": snapshot["resources"],
                "repo": snapshot["repo"],
                "git": snapshot["git"],
                **({"retirement": {
                    "kind": "expired-own-claim-released",
                    "business_status": "unresolved_red",
                    "prior_sequence": expected_sequence,
                }} if expired else {}),
            },
        )
        snapshot["last_sequence"] = event["sequence"]
        write_json_atomic(task_path(bus, value), snapshot)
    return snapshot, event


def update_task(
    bus: Path,
    value: str,
    *,
    state: str | None,
    summary: str | None,
    next_step: str | None,
    repo: Path | None,
    resources: list[str] | None,
    kind: str,
    expected_sequence: int | None = None,
    expected_cli_sha256: str | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    try:
        hint = read_json(task_path(bus, value))
    except (OSError, ValueError) as error:
        raise CompareConflict("task snapshot is unreadable") from error
    require_existing_lock = (
        (resources is not None and SCREEN_RESOURCE in resources)
        or hint is not None
        or expected_sequence is not None
    )
    with bus_lock(bus, require_existing=require_existing_lock):
        if require_existing_lock:
            _require_screen_bus_files(bus)
        try:
            previous = read_json(task_path(bus, value)) or {}
        except (OSError, ValueError) as error:
            raise CompareConflict("task snapshot is unreadable") from error
        if not isinstance(previous, dict):
            raise CompareConflict("task snapshot is invalid")
        previous_screen = SCREEN_RESOURCE in (previous.get("resources") or [])
        if previous_screen or (resources is not None and SCREEN_RESOURCE in resources):
            _require_cli_pair(bus, expected_cli_sha256)
        if previous_screen:
            if (
                kind != "heartbeat"
                or previous.get("schema") != SCHEMA
                or previous.get("task_id") != value
                or previous.get("state") != "running"
                or previous.get("resources") != [SCREEN_RESOURCE]
                or type(expected_sequence) is not int
                or type(previous.get("last_sequence")) is not int
                or previous.get("last_sequence") != expected_sequence
                or _unapplied_task_event(bus, value, expected_sequence)
                or not _fresh_screen_owner(previous, datetime.now(timezone.utc))
                or _current_screen_owners(bus, datetime.now(timezone.utc)) != [value]
            ):
                raise CompareConflict("screen owner update requires fresh heartbeat CAS", previous)
        elif expected_sequence is not None:
            raise CompareConflict("screen heartbeat sequence has no screen owner", previous)
        if resources is not None and SCREEN_RESOURCE in resources:
            if kind != "registered" or previous or resources != [SCREEN_RESOURCE]:
                raise CompareConflict("screen claim requires a new task registration", previous)
            if _unreleased_screen_records(bus):
                raise CompareConflict("unreleased screen resource record exists")
        identity = git_identity(repo or Path(str(previous.get("repo") or Path.cwd())))
        snapshot = {
            "schema": SCHEMA,
            "task_id": value,
            "state": state or str(previous.get("state") or "running"),
            "summary": summary if summary is not None else str(previous.get("summary") or ""),
            "next_step": next_step if next_step is not None else str(previous.get("next_step") or ""),
            "resources": resources if resources is not None else list(previous.get("resources") or []),
            "updated_at_utc": utc_now(),
            "pid": os.getpid(),
            **identity,
        }
        if previous_screen and (
            snapshot["state"] != "running" or snapshot["resources"] != [SCREEN_RESOURCE]
        ):
            raise CompareConflict("screen heartbeat changed lease state", previous)
        event = append_event(
            bus,
            {
                "kind": kind,
                "task_id": value,
                "to": ["*"],
                "state": snapshot["state"],
                "summary": snapshot["summary"],
                "next_step": snapshot["next_step"],
                "resources": snapshot["resources"],
                "repo": snapshot["repo"],
                "git": snapshot["git"],
            },
        )
        snapshot["last_sequence"] = event["sequence"]
        write_json_atomic(task_path(bus, value), snapshot)
    return snapshot, event


def read_events(bus: Path) -> list[dict[str, object]]:
    path = bus / "events.jsonl"
    if not path.is_file():
        return []
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def print_result(**payload: object) -> None:
    print(json.dumps({"schema": SCHEMA, "ok": True, **payload}, ensure_ascii=False, indent=2))


def _require_cli_pair(bus: Path, expected: str | None = None) -> None:
    source = Path(__file__).resolve()
    installed = bus / "bin" / "codex_task_bus.py"
    try:
        source_sha = hashlib.sha256(source.read_bytes()).hexdigest().upper()
        installed_sha = hashlib.sha256(installed.read_bytes()).hexdigest().upper()
    except OSError as error:
        raise CompareConflict("installed task bus CLI is unavailable") from error
    if expected is None:
        expected = source_sha
    if type(expected) is not str or re.fullmatch(r"[A-F0-9]{64}", expected) is None:
        raise CompareConflict("screen operation requires exact bus CLI SHA-256 pin")
    if source_sha != expected or installed_sha != expected:
        raise CompareConflict("task bus source or installed CLI bytes changed")


def _require_cli_pin(args: argparse.Namespace) -> None:
    if args.expected_cli_sha256 is None:
        raise CompareConflict("screen operation requires exact bus CLI SHA-256 pin")
    _require_cli_pair(args.bus_dir, args.expected_cli_sha256)


def command_register(args: argparse.Namespace) -> None:
    if SCREEN_RESOURCE in args.resource:
        _require_cli_pin(args)
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state="running",
        summary=args.summary,
        next_step=args.next_step,
        repo=args.repo,
        resources=args.resource,
        kind="registered",
        expected_cli_sha256=args.expected_cli_sha256,
    )
    print_result(task=snapshot, event=event)


def command_status(args: argparse.Namespace) -> None:
    completed = args.state == "done"
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state=args.state,
        summary=args.summary,
        next_step="" if completed and args.next_step is None else args.next_step,
        repo=args.repo,
        resources=[] if completed and args.resource is None else args.resource,
        kind="completed" if completed else "status",
    )
    print_result(task=snapshot, event=event)


def command_release_screen_cas(args: argparse.Namespace) -> None:
    _require_cli_pin(args)
    snapshot, event = release_screen_cas(
        args.bus_dir, args.task, args.expected_sequence,
        summary=args.summary, expected_cli_sha256=args.expected_cli_sha256,
    )
    print_result(task=snapshot, event=event)


def command_heartbeat(args: argparse.Namespace) -> None:
    if args.expected_sequence is not None:
        _require_cli_pin(args)
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state=None,
        summary=None,
        next_step=None,
        repo=args.repo,
        resources=None,
        kind="heartbeat",
        expected_sequence=args.expected_sequence,
        expected_cli_sha256=args.expected_cli_sha256,
    )
    print_result(task=snapshot, event=event)


def command_notify(args: argparse.Namespace) -> None:
    recipients = args.to or ["*"]
    with bus_lock(args.bus_dir):
        event = append_event(
            args.bus_dir,
            {
                "kind": "notification",
                "task_id": args.task,
                "to": recipients,
                "level": args.level,
                "message": args.message,
            },
        )
    print_result(event=event)


def command_poll(args: argparse.Namespace) -> None:
    cursor_path = args.bus_dir / "cursors" / task_filename(args.task)
    with bus_lock(args.bus_dir):
        cursor = read_json(cursor_path) or {"last_sequence": 0}
        last_sequence = int(cursor.get("last_sequence", 0))
        all_events = read_events(args.bus_dir)
        unseen = [event for event in all_events if int(event["sequence"]) > last_sequence]
        relevant = [
            event
            for event in unseen
            if (args.include_self or event.get("task_id") != args.task)
            and ("*" in event.get("to", []) or args.task in event.get("to", []))
        ]
        selected = relevant[: args.limit]
        if args.ack:
            if len(relevant) > len(selected) and selected:
                acknowledged = int(selected[-1]["sequence"])
            else:
                acknowledged = max(
                    [last_sequence, *(int(event["sequence"]) for event in unseen)],
                )
            write_json_atomic(
                cursor_path,
                {"schema": SCHEMA, "task_id": args.task, "last_sequence": acknowledged},
            )
        else:
            acknowledged = last_sequence
    print_result(
        task_id=args.task,
        previous_cursor=last_sequence,
        acknowledged_cursor=acknowledged,
        events=selected,
        remaining=max(0, len(relevant) - len(selected)),
    )


def command_list(args: argparse.Namespace) -> None:
    tasks: list[dict[str, object]] = []
    now = datetime.now(timezone.utc)
    with bus_lock(args.bus_dir):
        for path in sorted((args.bus_dir / "tasks").glob("*.json")):
            snapshot = read_json(path)
            if snapshot is None:
                continue
            updated = datetime.fromisoformat(str(snapshot["updated_at_utc"]))
            age = max(0, int((now - updated).total_seconds()))
            snapshot["age_seconds"] = age
            snapshot["stale"] = snapshot.get("state") != "done" and age > args.stale_after
            tasks.append(snapshot)
    print_result(tasks=tasks)


def command_install(args: argparse.Namespace) -> None:
    destination = args.bus_dir / "bin" / "codex_task_bus.py"
    source = Path(__file__).resolve()
    source_sha256 = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    established = (args.bus_dir / "tasks").is_dir()
    guard = bus_lock(args.bus_dir, require_existing=True) if established else nullcontext()
    with guard:
        if established:
            _require_screen_bus_files(args.bus_dir)
            if _unreleased_screen_records(args.bus_dir):
                raise CompareConflict("cannot install task bus during a screen lease")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
        shutil.copy2(source, temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest().upper() != source_sha256:
            raise RuntimeError("installed task bus temporary bytes differ from source")
        os.replace(temporary, destination)
        installed_sha256 = hashlib.sha256(destination.read_bytes()).hexdigest().upper()
        if installed_sha256 != source_sha256:
            raise RuntimeError("installed task bus bytes differ from source")
    source_documentation = Path(__file__).resolve().parent.parent / "docs" / "codex-task-bus.md"
    installed_documentation = args.bus_dir / "README.md"
    if source_documentation.is_file():
        shutil.copy2(source_documentation, installed_documentation)
    print_result(
        installed=str(destination.resolve()),
        source_sha256=source_sha256,
        installed_sha256=installed_sha256,
        documentation=str(installed_documentation.resolve()) if installed_documentation.is_file() else None,
        bus_dir=str(args.bus_dir.resolve()),
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--bus-dir", type=Path, default=DEFAULT_BUS)
    result.add_argument("--expected-cli-sha256")
    commands = result.add_subparsers(dest="command", required=True)

    register = commands.add_parser("register")
    register.add_argument("--task", required=True, type=task_id)
    register.add_argument("--summary", required=True)
    register.add_argument("--next-step", default="")
    register.add_argument("--repo", type=Path, default=Path.cwd())
    register.add_argument("--resource", action="append", default=[])
    register.set_defaults(handler=command_register)

    status = commands.add_parser("status")
    status.add_argument("--task", required=True, type=task_id)
    status.add_argument("--state", required=True, choices=STATES)
    status.add_argument("--summary")
    status.add_argument("--next-step")
    status.add_argument("--repo", type=Path)
    status.add_argument("--resource", action="append")
    status.set_defaults(handler=command_status)

    release_screen_cas_command = commands.add_parser("release-screen-cas")
    release_screen_cas_command.add_argument("--task", required=True, type=task_id)
    release_screen_cas_command.add_argument("--expected-sequence", required=True, type=int)
    release_screen_cas_command.add_argument("--summary", required=True)
    release_screen_cas_command.set_defaults(handler=command_release_screen_cas)

    heartbeat = commands.add_parser("heartbeat")
    heartbeat.add_argument("--task", required=True, type=task_id)
    heartbeat.add_argument("--repo", type=Path)
    heartbeat.add_argument("--expected-sequence", type=int)
    heartbeat.set_defaults(handler=command_heartbeat)

    notify = commands.add_parser("notify")
    notify.add_argument("--task", required=True, type=task_id)
    notify.add_argument("--to", action="append", type=recipient)
    notify.add_argument("--level", choices=("info", "warning", "action"), default="info")
    notify.add_argument("--message", required=True)
    notify.set_defaults(handler=command_notify)

    poll = commands.add_parser("poll")
    poll.add_argument("--task", required=True, type=task_id)
    poll.add_argument("--ack", action="store_true")
    poll.add_argument("--include-self", action="store_true")
    poll.add_argument("--limit", type=int, default=100)
    poll.set_defaults(handler=command_poll)

    listing = commands.add_parser("list")
    listing.add_argument("--stale-after", type=int, default=15 * 60)
    listing.set_defaults(handler=command_list)

    install = commands.add_parser("install")
    install.set_defaults(handler=command_install)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    args.bus_dir = args.bus_dir.expanduser().resolve()
    if getattr(args, "limit", 1) < 1:
        raise SystemExit("--limit must be positive")
    try:
        args.handler(args)
    except CompareConflict as error:
        print(json.dumps({
            "schema": SCHEMA, "ok": False, "code": "CAS_CONFLICT",
            "reason": error.reason, "observed": error.observed,
        }, ensure_ascii=False, indent=2))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
