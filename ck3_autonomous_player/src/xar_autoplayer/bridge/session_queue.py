"""File-backed command queue for a persistent CK3 development session.

The queue is deliberately transport-only.  A background thread may block on
stdin, but consumers poll and execute every command on the session's owning
thread.  External clients publish ``inbox/<request_id>.json`` with an atomic
rename and receive ``outbox/<request_id>.json`` responses.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from queue import Empty, Queue
import re
import threading
from typing import Iterable, TextIO

from ..environment import write_json_atomic


SESSION_QUEUE_PROTOCOL_VERSION = 1
_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_STDIN_EOF = object()


@dataclass(frozen=True)
class SessionQueueRequest:
    """One claimed inbox entry awaiting main-thread execution."""

    request_id: str
    command: str | None
    payload: dict[str, object] | None
    error: str | None = None


@dataclass(frozen=True)
class StdinReadBatch:
    """Non-blocking view of lines collected by :class:`StdinLinePump`."""

    lines: tuple[str, ...]
    eof: bool
    error: str | None = None


def _step_command(payload: dict[str, object]) -> str:
    raw_step = payload.get("step")
    turns = payload.get("turns")
    if isinstance(raw_step, dict):
        turns = raw_step.get("turns", turns)
        raw_step = raw_step.get("name") or raw_step.get("step")
    if not isinstance(raw_step, str) or not raw_step.strip():
        raise ValueError("step command requires a non-empty string step")
    step = raw_step.strip()
    if turns is not None:
        if step != "auto-run":
            raise ValueError("turns is only valid for the auto-run step")
        if isinstance(turns, bool) or not isinstance(turns, int):
            raise ValueError("auto-run turns must be an integer")
        step = f"auto-run {turns}"
    return step


def command_from_payload(payload: dict[str, object]) -> str:
    """Translate a queue payload to the existing dev-session command syntax."""

    raw_command = payload.get("command")
    if not isinstance(raw_command, str) or not raw_command.strip():
        raise ValueError("request requires a non-empty string command")
    command = raw_command.strip()
    if command == "step":
        return _step_command(payload)
    if command == "auto-run" and "turns" in payload:
        return _step_command({"step": command, "turns": payload["turns"]})
    return command


def expected_revision_error(
    payload: dict[str, object] | None,
    current_revision: int,
) -> str | None:
    """Validate an optional action revision immediately before execution."""

    if not isinstance(payload, dict) or "expected_revision" not in payload:
        return None
    expected = payload["expected_revision"]
    if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
        return "expected_revision must be a non-negative integer"
    if expected != current_revision:
        return (
            "development session revision mismatch: "
            f"expected {expected}, current {current_revision}"
        )
    return None


class PersistentSessionQueue:
    """Claim atomic JSON requests and write exactly one response per ID."""

    def __init__(
        self,
        run_dir: Path,
        *,
        supported_commands: Iterable[str] = ("status", "stop", "step"),
        action_steps: Iterable[str] = (),
    ) -> None:
        self.bridge_dir = run_dir / "bridge"
        self.inbox_dir = self.bridge_dir / "inbox"
        self.outbox_dir = self.bridge_dir / "outbox"
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self.supported_commands = tuple(dict.fromkeys(supported_commands))
        self.action_steps = tuple(dict.fromkeys(action_steps))
        self._claimed: set[str] = set()

    def descriptor(self) -> dict[str, object]:
        return {
            "protocol_version": SESSION_QUEUE_PROTOCOL_VERSION,
            "bridge_dir": str(self.bridge_dir),
            "inbox_dir": str(self.inbox_dir),
            "outbox_dir": str(self.outbox_dir),
            "supported_commands": list(self.supported_commands),
            "action_steps": list(self.action_steps),
            "request_shape": {
                "request_id": "<filename stem>",
                "command": "status | stop | step | <development step>",
                "step": "required when command=step",
            },
        }

    def poll(self) -> list[SessionQueueRequest]:
        """Claim complete ``*.json`` files without executing their commands."""

        requests: list[SessionQueueRequest] = []
        for path in sorted(self.inbox_dir.glob("*.json"), key=lambda item: item.name):
            request_id = path.stem
            if request_id in self._claimed:
                continue
            if (self.outbox_dir / path.name).exists():
                self._claimed.add(request_id)
                continue
            self._claimed.add(request_id)
            if _REQUEST_ID_PATTERN.fullmatch(request_id) is None:
                requests.append(
                    SessionQueueRequest(
                        request_id=request_id,
                        command=None,
                        payload=None,
                        error="invalid request_id filename",
                    )
                )
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(payload, dict):
                    raise ValueError("request JSON must be an object")
                embedded_id = payload.get("request_id", request_id)
                if embedded_id != request_id:
                    raise ValueError("request_id must match the inbox filename stem")
                command = command_from_payload(payload)
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                requests.append(
                    SessionQueueRequest(
                        request_id=request_id,
                        command=None,
                        payload=None,
                        error=f"{type(error).__name__}: {error}",
                    )
                )
                continue
            requests.append(
                SessionQueueRequest(
                    request_id=request_id,
                    command=command,
                    payload=payload,
                )
            )
        return requests

    def respond(
        self,
        request: SessionQueueRequest,
        *,
        ok: bool,
        result: object = None,
        error: str | None = None,
    ) -> Path:
        """Atomically publish the terminal response for one claimed request."""

        response_path = self.outbox_dir / f"{request.request_id}.json"
        write_json_atomic(
            response_path,
            {
                "protocol_version": SESSION_QUEUE_PROTOCOL_VERSION,
                "request_id": request.request_id,
                "ok": bool(ok),
                "result": result,
                "error": error,
            },
        )
        return response_path


class StdinLinePump:
    """Read blocking stdin on a daemon while leaving command work to the caller."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._items: Queue[object] = Queue()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        threading.Thread(
            target=self._read_lines,
            name="xar-opening-dev-session-stdin",
            daemon=True,
        ).start()

    def _read_lines(self) -> None:
        try:
            while True:
                line = self._stream.readline()
                if line == "":
                    self._items.put(_STDIN_EOF)
                    return
                self._items.put(line)
        except BaseException as error:
            self._items.put(error)
            self._items.put(_STDIN_EOF)

    def poll(self) -> StdinReadBatch:
        lines: list[str] = []
        eof = False
        error: str | None = None
        while True:
            try:
                item = self._items.get_nowait()
            except Empty:
                break
            if item is _STDIN_EOF:
                eof = True
            elif isinstance(item, BaseException):
                error = f"{type(item).__name__}: {item}"
            else:
                lines.append(str(item))
        return StdinReadBatch(tuple(lines), eof, error)
