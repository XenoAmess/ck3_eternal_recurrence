#!/usr/bin/env python3
"""Cooperative, filesystem-backed status and notification bus for Codex tasks."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
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
def bus_lock(bus: Path):
    bus.mkdir(parents=True, exist_ok=True)
    lock_path = bus / ".lock"
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
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
    return json.loads(path.read_text(encoding="utf-8"))


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
) -> tuple[dict[str, object], dict[str, object]]:
    with bus_lock(bus):
        previous = read_json(task_path(bus, value)) or {}
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


def command_register(args: argparse.Namespace) -> None:
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state="running",
        summary=args.summary,
        next_step=args.next_step,
        repo=args.repo,
        resources=args.resource,
        kind="registered",
    )
    print_result(task=snapshot, event=event)


def command_status(args: argparse.Namespace) -> None:
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state=args.state,
        summary=args.summary,
        next_step=args.next_step,
        repo=args.repo,
        resources=args.resource,
        kind="completed" if args.state == "done" else "status",
    )
    print_result(task=snapshot, event=event)


def command_heartbeat(args: argparse.Namespace) -> None:
    snapshot, event = update_task(
        args.bus_dir,
        args.task,
        state=None,
        summary=None,
        next_step=None,
        repo=args.repo,
        resources=None,
        kind="heartbeat",
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
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), destination)
    source_documentation = Path(__file__).resolve().parent.parent / "docs" / "codex-task-bus.md"
    installed_documentation = args.bus_dir / "README.md"
    if source_documentation.is_file():
        shutil.copy2(source_documentation, installed_documentation)
    print_result(
        installed=str(destination.resolve()),
        documentation=str(installed_documentation.resolve()) if installed_documentation.is_file() else None,
        bus_dir=str(args.bus_dir.resolve()),
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--bus-dir", type=Path, default=DEFAULT_BUS)
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

    heartbeat = commands.add_parser("heartbeat")
    heartbeat.add_argument("--task", required=True, type=task_id)
    heartbeat.add_argument("--repo", type=Path)
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
    args.handler(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
