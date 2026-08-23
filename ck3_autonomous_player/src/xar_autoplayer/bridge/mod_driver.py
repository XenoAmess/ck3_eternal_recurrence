"""Read-only gameplay bridge backed by the CK3 data Mod protocol.

The companion writes one typed ``run`` request at a time and tails only the
new portion of ``debug.log`` for the matching complete response frame.  The
data Mod currently exposes snapshots only; actions remain on the visual or
future native backend until a real typed effect exists for them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
import os
from pathlib import Path
import tempfile
import threading
import time
from typing import Protocol
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError


_LOG_PREFIX = "XAR_MCP:"
_NOOP_INBOX = (
    "# XAR MCP inbox default: intentionally no effects.\n"
    "# Written by xar-autoplayer after processing a typed request.\n"
)


class _SnapshotFrame(Protocol):
    request_id: str
    player_id: int
    date: str
    total_days: int
    status: str


try:
    # In a source checkout, consume the parser shipped with the data Mod so
    # its static fixture and the live driver exercise the exact same grammar.
    from ck3_autonomous_player.mod_bridge.tools.frame_parser import (
        parse_complete_snapshots as _parse_complete_snapshots,
    )
except ImportError:
    # Installed wheels intentionally contain only ``src/``.  Keep the tiny
    # parser available there as well so ``xar-ck3-mcp --driver mod`` does not
    # depend on the repository layout.
    @dataclass(frozen=True)
    class _BundledSnapshotFrame:
        request_id: str
        player_id: int
        date: str
        total_days: int
        status: str

    def _parse_complete_snapshots(log_text: str) -> list[_BundledSnapshotFrame]:
        pending: dict[str, dict[str, str]] = {}
        completed: list[_BundledSnapshotFrame] = []

        for line in log_text.splitlines():
            marker = line.find(_LOG_PREFIX)
            if marker < 0:
                continue
            parts = line[marker + len(_LOG_PREFIX) :].strip().split("|")
            event = parts[0]
            fields: dict[str, str] = {}
            for part in parts[1:]:
                key, separator, value = part.partition("=")
                if separator:
                    fields[key] = value
            request_id = fields.get("request_id")

            if event == "BEGIN" and fields.get("kind") == "snapshot" and request_id:
                pending[request_id] = dict(fields)
                continue
            if event == "STATE":
                if pending:
                    pending[next(reversed(pending))].update(fields)
                continue
            if event == "ACK" and request_id in pending:
                pending[request_id].update(fields)
                continue
            if event != "END" or request_id not in pending:
                continue

            frame = pending.pop(request_id)
            required = {"player_id", "date", "total_days", "status"}
            if not required.issubset(frame) or frame.get("status") != "ok":
                continue
            try:
                completed.append(
                    _BundledSnapshotFrame(
                        request_id=request_id,
                        player_id=int(frame["player_id"]),
                        date=frame["date"],
                        total_days=int(frame["total_days"]),
                        status=frame["status"],
                    )
                )
            except ValueError:
                continue
        return completed


class DataModGameplayDriver:
    """Snapshot/wait driver for ``run/xar_mcp_inbox.txt`` + ``debug.log``."""

    def __init__(
        self,
        userdir: Path,
        *,
        request_timeout_seconds: float = 5.0,
        poll_interval_seconds: float = 0.05,
        request_id_factory: Callable[[], str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.userdir = Path(userdir)
        self.inbox_path = self.userdir / "run" / "xar_mcp_inbox.txt"
        self.log_path = self.userdir / "logs" / "debug.log"
        self.request_timeout_seconds = _positive_finite(
            request_timeout_seconds, "request_timeout_seconds"
        )
        self.poll_interval_seconds = _positive_finite(
            poll_interval_seconds, "poll_interval_seconds"
        )
        self._request_id_factory = request_id_factory or _new_request_id
        self._sleep = sleep
        self._request_lock = threading.Lock()
        self._local_sequence = 0
        self._last_revision = 0
        self._last_signature: tuple[int, str, int] | None = None

    def capabilities(self) -> dict[str, object]:
        return {
            "format_version": 1,
            "backend_id": "data-mod",
            "source": "ck3-run-file-and-debug-log",
            "latency": "polling",
            "snapshot": True,
            "wait_for_change": True,
            # Do not advertise an action until the data Mod has a real typed
            # effect and an acknowledged result for it.
            "action_steps": [],
        }

    def take_snapshot(self) -> dict[str, object]:
        with self._request_lock:
            return self._take_snapshot_locked(self.request_timeout_seconds)

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]:
        del expected_revision
        raise UnsupportedStepError(
            f"data Mod bridge does not implement gameplay step {step}"
        )

    def wait_for_change(
        self, after_revision: int, *, timeout_seconds: float
    ) -> dict[str, object]:
        if (
            isinstance(after_revision, bool)
            or not isinstance(after_revision, int)
            or after_revision < 0
        ):
            raise ValueError("after_revision must be a non-negative integer")
        timeout = _positive_finite(timeout_seconds, "timeout_seconds")
        deadline = time.monotonic() + timeout
        latest: dict[str, object] | None = None
        with self._request_lock:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    if latest is not None:
                        return latest
                    raise BridgeUnavailableError("data Mod wait_for_change timed out")
                snapshot = self._take_snapshot_locked(remaining)
                if int(snapshot["revision"]) > after_revision:
                    return snapshot
                latest = snapshot
                self._sleep(min(self.poll_interval_seconds, remaining))

    def _take_snapshot_locked(self, timeout_seconds: float) -> dict[str, object]:
        request_id = self._request_id_factory()
        if not _is_ck3_flag_token(request_id):
            raise ValueError("request_id_factory returned an invalid CK3 flag token")

        log_offset = _file_size(self.log_path)
        request = f"xar_mcp_take_snapshot = {{ REQUEST_ID = {request_id} }}\n"
        self._write_inbox(request)
        try:
            frame = self._wait_for_frame(
                request_id,
                start_offset=log_offset,
                timeout_seconds=timeout_seconds,
            )
        finally:
            self._write_inbox(_NOOP_INBOX)

        signature = (frame.player_id, frame.date, frame.total_days)
        if signature != self._last_signature:
            self._local_sequence += 1
            self._last_revision += 1
            self._last_signature = signature
        revision = self._last_revision
        return {
            "format_version": 1,
            "snapshot_id": f"data-mod:{frame.total_days}:{frame.request_id}",
            "revision": revision,
            "backend_id": "data-mod",
            "source": "ck3-run-file-and-debug-log",
            "request_id": frame.request_id,
            "player_id": frame.player_id,
            "date": frame.date,
            "total_days": frame.total_days,
            "phase": None,
            "history": [],
        }

    def _wait_for_frame(
        self,
        request_id: str,
        *,
        start_offset: int,
        timeout_seconds: float,
    ) -> _SnapshotFrame:
        deadline = time.monotonic() + timeout_seconds
        offset = start_offset
        captured = bytearray()
        while True:
            try:
                size = self.log_path.stat().st_size
            except FileNotFoundError:
                size = 0
            if size < offset:
                # CK3 creates/truncates debug.log at process start.  Continue
                # from the beginning of the new file, still matching by ID.
                offset = 0
                captured.clear()
            if size > offset:
                try:
                    with self.log_path.open("rb") as log_file:
                        log_file.seek(offset)
                        captured.extend(log_file.read(size - offset))
                except FileNotFoundError:
                    pass
                else:
                    offset = size
                    text = captured.decode("utf-8", errors="replace")
                    for frame in _parse_complete_snapshots(text):
                        if frame.request_id == request_id:
                            return frame

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeUnavailableError(
                    f"data Mod snapshot {request_id} timed out after "
                    f"{timeout_seconds:.3f}s"
                )
            self._sleep(min(self.poll_interval_seconds, remaining))

    def _write_inbox(self, source: str) -> None:
        run_dir = self.inbox_path.parent
        run_dir.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(
            prefix=".xar_mcp_inbox.", suffix=".tmp", dir=run_dir
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(handle, "wb") as temporary:
                temporary.write(b"\xef\xbb\xbf")
                temporary.write(source.encode("utf-8"))
            os.replace(temporary_path, self.inbox_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def load_data_mod_driver(
    userdir: str | os.PathLike[str] | None = None,
) -> DataModGameplayDriver:
    """Factory used by ``xar-ck3-mcp --driver mod`` and module factories."""

    selected = userdir or os.environ.get("XAR_CK3_USERDIR")
    if not selected:
        raise RuntimeError(
            "--driver mod requires --userdir or the XAR_CK3_USERDIR environment variable"
        )
    return DataModGameplayDriver(Path(selected))


def _new_request_id() -> str:
    return f"xar_req_{uuid.uuid4().hex}"


def _file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _is_ck3_flag_token(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and all(
            character.isascii() and (character.isalnum() or character == "_")
            for character in value
        )
    )


def _positive_finite(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) <= 0
    ):
        raise ValueError(f"{name} must be finite and positive")
    return float(value)
