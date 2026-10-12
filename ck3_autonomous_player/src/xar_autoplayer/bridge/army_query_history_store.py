"""Preserve complete Driver Army results once; retain small history entries.

This is a persistence representation, never a replacement for a current Army
query or its same-frame cache. The sidecar contains the complete Driver result,
not the original pipe bytes. Failed writes leave their partial file for review.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import uuid
from pathlib import Path


ARMY_QUERY_STEP = "query-army-strengths-v1"
SUMMARY_SCHEMA = "xar.ck3.army-query-history-summary.v1"
REFERENCE_KIND = "complete-driver-army-query-result-json-v1"
_RESULT_FIELDS = (
    "step", "accepted", "status", "backend_id", "query_sequence",
    "queried_snapshot_id", "queried_revision", "queried_native_revision",
)
_ARMY_FIELDS = (
    "army_id", "status", "scope_role", "native_carmy_id", "owner_character_id",
    "war_ids", "current_soldiers", "maximum_soldiers", "ai_base_power_raw",
    "ai_base_power_scale", "unavailable_reason",
)


class SidecarBudgetExhaustedError(OSError):
    """A bounded evidence write cannot fit; the gameplay read remains valid."""


class ByteBudget:
    """Count new bytes against the caller's separately admitted write budget."""

    def __init__(self, limit: int) -> None:
        if type(limit) is not int or limit <= 0:
            raise ValueError("a positive admitted output byte limit is required")
        self.limit = limit
        self.used = 0

    @classmethod
    def for_existing_files(cls, folder: Path, limit: int) -> ByteBudget:
        budget = cls(limit)
        if folder.exists():
            # This dedicated flat leaf includes failed/partial writes. No body
            # hashing, traversal into children, or expiry-based deletion occurs.
            with os.scandir(folder) as entries:
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        budget.used += entry.stat(follow_symlinks=False).st_size
        return budget

    def charge(self, size: int) -> None:
        if self.used + size > self.limit:
            raise SidecarBudgetExhaustedError("admitted output byte budget exhausted")
        self.used += size


def file_digest(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def write_json_exclusive(
    path: Path, payload: object, *, budget: ByteBudget | None = None,
) -> dict[str, object]:
    """Stream a create-only UTF-8 JSON file and bind its actual written bytes."""

    digest = hashlib.sha256()
    size = 0
    encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))
    with path.open("xb") as stream:
        buffer = bytearray()
        chunk_bytes = 1024 * 1024

        def flush_buffer() -> None:
            nonlocal size
            if not buffer:
                return
            if budget is not None:
                budget.charge(len(buffer))
            written = stream.write(buffer)
            if written != len(buffer):
                raise OSError("short JSON sidecar write")
            digest.update(buffer)
            size += written
            buffer.clear()

        def append_buffered(data: bytes) -> None:
            offset = 0
            while offset < len(data):
                end = min(len(data), offset + chunk_bytes - len(buffer))
                buffer.extend(data[offset:end])
                offset = end
                if len(buffer) == chunk_bytes:
                    flush_buffer()

        for text in encoder.iterencode(payload):
            append_buffered(text.encode("utf-8"))
        append_buffered(b"\n")
        flush_buffer()
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": str(path.resolve()), "bytes": size,
            "sha256": digest.hexdigest()}


def is_compact_army_history_result(result: object) -> bool:
    return (isinstance(result, dict)
            and result.get("history_summary_schema") == SUMMARY_SCHEMA)


def build_army_query_history_summary(
    result: dict[str, object], reference: dict[str, object] | None,
    *, unavailable_reason: str | None = None,
    diagnostic: dict[str, object] | None = None,
) -> dict[str, object]:
    """An explicit archive/sidecar reference is distinct from native status."""
    rows = result.get("army_strengths")
    summary = {key: copy.deepcopy(result[key]) for key in _RESULT_FIELDS
               if key in result}
    summary.update(
        history_summary_schema=SUMMARY_SCHEMA,
        army_count=len(rows) if isinstance(rows, list) else None,
        armies=[
            {key: copy.deepcopy(row[key]) for key in _ARMY_FIELDS if key in row}
            if isinstance(row, dict) else {"malformed_row": True}
            for row in rows
        ] if isinstance(rows, list) else None,
        full_result_preserved=reference is not None,
    )
    if reference is not None:
        summary["raw_result_reference"] = copy.deepcopy(reference)
    else:
        summary["unavailable_reason"] = unavailable_reason
        if diagnostic is not None:
            summary["history_storage_diagnostic"] = diagnostic
    return summary


class ArmyQueryHistoryStore:
    """Finite, explicitly admitted evidence quota for one history leaf.

    Existing files count on first use after a restart. No new budget is invented
    by a reconnect. The caller still owns work-package storage admission and
    retention. Exhausted quota/real I/O failure produces an honest small history
    diagnostic while leaving the successful current read and its cache intact.
    """

    def __init__(self, evidence_dir: Path, limit_bytes: int) -> None:
        if type(limit_bytes) is not int or limit_bytes < 0:
            raise ValueError("Army history sidecar limit must be a nonnegative integer")
        self.evidence_dir = evidence_dir
        self.limit_bytes = limit_bytes
        self._budget: ByteBudget | None = None

    def record(self, result: dict[str, object]) -> dict[str, object]:
        if is_compact_army_history_result(result):
            return copy.deepcopy(result)
        if self.limit_bytes == 0:
            # Session explicitly disables evidence sidecars. Do not create or
            # inspect a directory, encode the full result, or spend a partial.
            return build_army_query_history_summary(
                result, None, unavailable_reason="sidecar_disabled_by_session_budget",
                diagnostic={"limit_bytes": 0, "charged_bytes": 0})
        try:
            if self._budget is None:
                self._budget = ByteBudget.for_existing_files(
                    self.evidence_dir, self.limit_bytes)
            if self._budget.used >= self._budget.limit:
                raise SidecarBudgetExhaustedError("Army sidecar quota exhausted")
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            path = self.evidence_dir / f"army-query-{uuid.uuid4().hex}.json"
            reference = write_json_exclusive(path, result, budget=self._budget)
        except SidecarBudgetExhaustedError:
            return build_army_query_history_summary(
                result, None, unavailable_reason="sidecar_budget_exhausted",
                diagnostic={"limit_bytes": self.limit_bytes,
                            "charged_bytes": self._budget.used if self._budget else None})
        except OSError as error:
            return build_army_query_history_summary(
                result, None, unavailable_reason="sidecar_io_error",
                diagnostic={"error_type": type(error).__name__, "errno": error.errno,
                            "message": str(error)[:2048],
                            "limit_bytes": self.limit_bytes,
                            "charged_bytes": self._budget.used if self._budget else None})
        reference.update(kind=REFERENCE_KIND, wire_bytes_preserved=False)
        return build_army_query_history_summary(result, reference)
