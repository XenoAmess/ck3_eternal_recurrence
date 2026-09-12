"""Append-only, atomic event-segment WAL for publication operations."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from .errors import OperationNotFoundError, StateConflictError
from .models import PublicationPlan, WorkflowState

_PROCESS_LOCK = threading.RLock()


@dataclass(frozen=True, slots=True)
class OperationEvent:
    sequence: int
    timestamp_utc: str
    kind: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OperationView:
    operation_id: str
    plan: PublicationPlan
    plan_sha256: str
    state: WorkflowState = WorkflowState.PLANNED
    item_id: str | None = None
    token_digest: str | None = None
    token_expires_at_utc: str | None = None
    token_consumed: bool = False
    irreversible_started: bool = False
    offline_compensation_required: bool = False
    offline_restored: bool = False
    blocked_code: str | None = None
    last_error: str | None = None
    event_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.plan.schema,
            "operation_id": self.operation_id,
            "plan": self.plan.to_dict(),
            "plan_sha256": self.plan_sha256,
            "state": self.state.value,
            "item_id": self.item_id,
            "token_issued": self.token_digest is not None,
            "token_expires_at_utc": self.token_expires_at_utc,
            "token_consumed": self.token_consumed,
            "irreversible_started": self.irreversible_started,
            "offline_compensation_required": self.offline_compensation_required,
            "offline_restored": self.offline_restored,
            "blocked_code": self.blocked_code,
            "last_error": self.last_error,
            "event_count": self.event_count,
        }


class OperationStore:
    """Stores immutable WAL records; no Steam or network access occurs here."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _operation_dir(self, operation_id: str) -> Path:
        return self.root / operation_id

    def _wal_dir(self, operation_id: str) -> Path:
        return self._operation_dir(operation_id) / "wal"

    def create(self, plan: PublicationPlan) -> OperationView:
        operation_dir = self._operation_dir(plan.operation_id)
        try:
            operation_dir.mkdir(parents=False, exist_ok=False)
            self._wal_dir(plan.operation_id).mkdir()
        except FileExistsError as error:
            raise StateConflictError(f"operation already exists: {plan.operation_id}") from error
        self._append_unlocked(
            plan.operation_id,
            "PLAN_CREATED",
            {"plan": plan.to_dict(), "plan_sha256": plan.sha256},
        )
        return self.load(plan.operation_id)

    def append(self, operation_id: str, kind: str, data: dict[str, Any] | None = None) -> OperationView:
        with _PROCESS_LOCK:
            if not self._wal_dir(operation_id).is_dir():
                raise OperationNotFoundError(f"operation does not exist: {operation_id}")
            with self._file_lock(operation_id):
                self._append_unlocked(operation_id, kind, data or {})
            return self.load(operation_id)

    def compare_and_append(
        self,
        operation_id: str,
        expected_event_count: int,
        kind: str,
        data: dict[str, Any] | None = None,
    ) -> OperationView:
        """Atomically append only if no other writer advanced this operation."""

        with _PROCESS_LOCK:
            if not self._wal_dir(operation_id).is_dir():
                raise OperationNotFoundError(f"operation does not exist: {operation_id}")
            with self._file_lock(operation_id):
                actual = sum(1 for _ in self._wal_dir(operation_id).glob("*.json"))
                if actual != expected_event_count:
                    raise StateConflictError(
                        "operation changed concurrently; no irreversible provider call was made"
                    )
                self._append_unlocked(operation_id, kind, data or {})
            return self.load(operation_id)

    @contextmanager
    def _file_lock(self, operation_id: str) -> Iterator[None]:
        """Cross-process advisory lock for sequencing WAL segments."""

        lock_path = self._operation_dir(operation_id) / ".writer.lock"
        with lock_path.open("a+b") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _append_unlocked(self, operation_id: str, kind: str, data: dict[str, Any]) -> None:
        wal_dir = self._wal_dir(operation_id)
        sequence = sum(1 for _ in wal_dir.glob("*.json")) + 1
        final_path = wal_dir / f"{sequence:08d}.json"
        if final_path.exists():
            raise StateConflictError(f"WAL sequence collision for {operation_id}: {sequence}")
        event = OperationEvent(
            sequence=sequence,
            timestamp_utc=datetime.now(UTC).isoformat(),
            kind=kind,
            data=data,
        )
        encoded = (
            json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        handle, temporary_name = tempfile.mkstemp(prefix=".event-", suffix=".tmp", dir=wal_dir)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_name, final_path)
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass

    def events(self, operation_id: str) -> list[OperationEvent]:
        wal_dir = self._wal_dir(operation_id)
        if not wal_dir.is_dir():
            raise OperationNotFoundError(f"operation does not exist: {operation_id}")
        result: list[OperationEvent] = []
        for expected_sequence, path in enumerate(sorted(wal_dir.glob("*.json")), start=1):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                event = OperationEvent(
                    sequence=int(raw["sequence"]),
                    timestamp_utc=str(raw["timestamp_utc"]),
                    kind=str(raw["kind"]),
                    data=dict(raw["data"]),
                )
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                raise StateConflictError(f"invalid WAL event {path}: {error}") from error
            if event.sequence != expected_sequence or path.stem != f"{expected_sequence:08d}":
                raise StateConflictError(f"non-contiguous WAL for operation {operation_id}")
            result.append(event)
        if not result:
            raise StateConflictError(f"operation has no PLAN_CREATED WAL event: {operation_id}")
        return result

    def load(self, operation_id: str) -> OperationView:
        events = self.events(operation_id)
        first = events[0]
        if first.kind != "PLAN_CREATED":
            raise StateConflictError("first WAL event must be PLAN_CREATED")
        plan = PublicationPlan.from_dict(first.data["plan"])
        if first.data.get("plan_sha256") != plan.sha256:
            raise StateConflictError("persisted publication plan hash is invalid")
        view = OperationView(operation_id, plan, plan.sha256)
        for event in events[1:]:
            _apply_event(view, event)
        view.event_count = len(events)
        return view

    def list_operation_ids(self) -> list[str]:
        return sorted(
            path.name for path in self.root.iterdir() if path.is_dir() and (path / "wal").is_dir()
        )

    def iter_views(self) -> Iterator[OperationView]:
        for operation_id in self.list_operation_ids():
            yield self.load(operation_id)


def _apply_event(view: OperationView, event: OperationEvent) -> None:
    kind = event.kind
    data = event.data
    if kind == "ONLINE_WINDOW_INTENT":
        view.offline_compensation_required = bool(data.get("offline_compensation_required", True))
        view.offline_restored = False
    elif kind == "ONLINE_WINDOW_OPENED":
        view.state = WorkflowState.ONLINE_READY
        view.offline_compensation_required = bool(data.get("offline_compensation_required", True))
        view.offline_restored = False
    elif kind == "PREFLIGHT_GREEN":
        view.state = WorkflowState.PREFLIGHT_GREEN
        view.blocked_code = None
        view.last_error = None
    elif kind == "SUBMIT_TOKEN_ISSUED":
        view.token_digest = str(data["token_digest"])
        view.token_expires_at_utc = str(data["expires_at_utc"])
        view.token_consumed = False
    elif kind == "SUBMIT_TOKEN_CONSUMED":
        view.token_consumed = True
        view.irreversible_started = True
        view.state = WorkflowState.SUBMITTING
    elif kind == "CREATE_INTENT":
        view.state = WorkflowState.CREATE_CALLED
        view.irreversible_started = True
    elif kind == "ITEM_ID_DURABLY_RECORDED":
        view.state = WorkflowState.ITEM_ID_DURABLY_RECORDED
        view.item_id = str(data["item_id"])
    elif kind == "CONTENT_SUBMIT_INTENT":
        view.state = WorkflowState.CONTENT_UPDATE_CALLED
        view.irreversible_started = True
    elif kind == "REMOTE_COMMITTED":
        view.state = WorkflowState.REMOTE_COMMITTED
        view.item_id = str(data["item_id"])
    elif kind == "COMPLETE":
        view.state = WorkflowState.COMPLETE
    elif kind == "OFFLINE_RESTORED":
        view.offline_restored = True
        view.offline_compensation_required = False
    elif kind == "OFFLINE_RESTORE_FAILED":
        view.offline_restored = False
        view.offline_compensation_required = True
        view.last_error = str(data.get("message", "offline restore failed"))
        if view.state not in {
            WorkflowState.AMBIGUOUS_CREATE,
            WorkflowState.SUBMIT_RESULT_UNKNOWN,
        }:
            view.state = WorkflowState.OFFLINE_RESTORE_FAILED
    elif kind == "BLOCKED":
        code = str(data["gate_code"])
        try:
            view.state = WorkflowState(code)
        except ValueError as error:
            raise StateConflictError(f"unknown blocked state in WAL: {code}") from error
        view.blocked_code = code
        view.last_error = str(data.get("message", ""))
    elif kind == "AMBIGUOUS_CREATE":
        view.state = WorkflowState.AMBIGUOUS_CREATE
        view.last_error = str(data.get("message", ""))
    elif kind == "SUBMIT_RESULT_UNKNOWN":
        view.state = WorkflowState.SUBMIT_RESULT_UNKNOWN
        view.last_error = str(data.get("message", ""))
    elif kind == "REMOTE_MISMATCH":
        view.state = WorkflowState.REMOTE_MISMATCH
        view.last_error = str(data.get("message", ""))
