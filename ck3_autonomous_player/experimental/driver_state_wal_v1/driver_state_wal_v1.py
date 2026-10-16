"""Bounded atomic Driver-state deltas; experimental and disabled by default.

This file never claims power-loss durability.  Its publication primitive is the
same write-and-replace contract as driver-state.json.  A malformed journal is
an error, not permission to resume from an older base or credit an action.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Callable


SCHEMA = "xar.ck3.driver-state-wal/v1"
FILENAME = "driver-state.wal-v1.json"
FULL_VERSION = 2
SEALED_VERSION = 3  # Deliberately rejected by every pre-WAL cold reader.
SEALED_SCHEMA = "xar.ck3.driver-state-sealed-base/v1"
MAX_JOURNAL_BYTES = 8 * 1024 * 1024
MAX_DELTA_BYTES = 256 * 1024
_META_REQUIRED = frozenset({
    "format_version", "pipe_name", "bridge_pid", "episode_character_id",
    "episode_run_id", "last_checkpoint", "rollback_war_failure",
    "managed_restore_transaction", "succession_expectation",
    "succession_lifecycle", "campaign_goal",
})
_META_OPTIONAL = frozenset({"rollback_war_failures"})


class JournalInvalid(ValueError):
    """A sealed state cannot be safely replayed or credited."""


class JournalCapacity(JournalInvalid):
    """A valid delta requires a full-state consolidation barrier."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def base_stat_identity(path: Path) -> tuple[int, int, int, int, int]:
    """Cheap identity of the already-hashed atomic base, never a cold hash proof.

    The writer retains this only under its write lock. A differing identity
    rejects a hot append; cold replay always reads and hashes the full base.
    """
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size,
            stat.st_mtime_ns, stat.st_ctime_ns)


def eligible_route_horizon_delta(step: object, result: object, *,
                                 parsed_step_valid: bool) -> bool:
    """Only a settled exact one-day route clock may use the small journal.

    The caller supplies the existing strict step parser. The result is still
    recorded unchanged in full history; this is only a storage qualification.
    """
    if not parsed_step_valid or not isinstance(step, str) or not isinstance(result, dict):
        return False
    start = result.get("starting_date_raw")
    end = result.get("ending_date_raw")
    if (result.get("step") != step or result.get("elapsed_days") != 1
            or result.get("requested_horizon_days") != 1
            or type(start) is not int or type(end) is not int
            or not 0 < start < end <= 2**63 - 1 or end != start + 24
            or result.get("paused") is not True
            or result.get("progress_status") != "postcondition"
            or result.get("final_screen") != "map_hud"
            or result.get("active_event") is not None
            or result.get("pending_character_interaction") is not None
            or result.get("ordinary_events") not in (None, [])):
        return False
    clock = result.get("exact_day_native_clock")
    stopped = clock.get("stopped") if isinstance(clock, dict) else None
    return bool(isinstance(stopped, dict)
        and stopped.get("state") == "triggered"
        and stopped.get("mode") == "terminal_or_sentinel"
        and stopped.get("starting_date_raw") == start
        and stopped.get("target_date_raw") == end
        and stopped.get("last_observed_date_raw") == end
        and stopped.get("trigger_date_raw") == end
        and stopped.get("completed_daily_ticks") == 1
        and stopped.get("overshoot_days") == 0
        and stopped.get("trigger_reasons") == ["date_deadline"]
        and stopped.get("trigger_flags") == 1
        and stopped.get("pause_wrapper_called") is True
        and stopped.get("pause_observed") is True
        and stopped.get("terminal_observed") is False
        and stopped.get("abnormal") is False)


def _hex(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _meta(payload: dict[str, object]) -> dict[str, object]:
    if set(payload) - {"command_history"} not in (_META_REQUIRED,
                                                     _META_REQUIRED | _META_OPTIONAL):
        raise JournalInvalid("Driver scalar field schema changed; full-state barrier required")
    return {k: v for k, v in payload.items() if k != "command_history"}


def new_journal(base_bytes: bytes, base_payload: dict[str, object]) -> dict[str, object]:
    if (base_payload.get("format_version") != SEALED_VERSION
            or base_payload.get("schema") != SEALED_SCHEMA
            or set(base_payload) != {"format_version", "schema", "sealed_full_state"}
            or not isinstance(base_payload.get("sealed_full_state"), dict)):
        raise JournalInvalid("journal base must carry the sealed envelope")
    full = base_payload["sealed_full_state"]
    history = full.get("command_history")
    if not isinstance(history, list):
        raise JournalInvalid("base history is unavailable")
    _meta(full)
    if full.get("format_version") != FULL_VERSION:
        raise JournalInvalid("sealed full state is not the original schema")
    return new_journal_header(base_bytes, len(history))


def new_journal_header(base_bytes: bytes, history_rows: int) -> dict[str, object]:
    if type(history_rows) is not int or history_rows < 0:
        raise JournalInvalid("base history count is malformed")
    return {"schema": SCHEMA, "base_sha256": _sha(base_bytes),
            "base_history_rows": history_rows, "entries": [],
            "consolidated_sha256": None}


def sealed_base_bytes(full_bytes: bytes) -> bytes:
    """Wrap the whole old full state so old direct readers cannot use its fields."""
    try:
        payload = json.loads(full_bytes)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise JournalInvalid(f"full-state baseline is malformed: {error}") from error
    if not isinstance(payload, dict) or payload.get("format_version") != FULL_VERSION:
        raise JournalInvalid("only a prior full-state v2 can become a journal baseline")
    _meta(payload)
    if not isinstance(payload.get("command_history"), list):
        raise JournalInvalid("full-state history is malformed")
    envelope = {"format_version": SEALED_VERSION, "schema": SEALED_SCHEMA,
                "sealed_full_state": payload}
    return json.dumps(envelope, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _validated_entries(journal: dict[str, object]) -> tuple[list[dict[str, object]], str, int]:
    if (set(journal) != {"schema", "base_sha256", "base_history_rows", "entries", "consolidated_sha256"}
            or journal.get("schema") != SCHEMA or not _hex(journal.get("base_sha256"))
            or type(journal.get("base_history_rows")) is not int
            or journal["base_history_rows"] < 0
            or not isinstance(journal.get("entries"), list)
            or (journal.get("consolidated_sha256") is not None
                and not _hex(journal["consolidated_sha256"]))):
        raise JournalInvalid("journal header is malformed")
    expected_index = journal["base_history_rows"] + 1
    previous = journal["base_sha256"]
    entries = journal["entries"]
    for sequence, entry in enumerate(entries, 1):
        if (not isinstance(entry, dict)
                or set(entry) != {"sequence", "previous_sha256", "history_rows", "state_fields", "sha256"}
                or type(entry.get("sequence")) is not int or entry["sequence"] != sequence
                or entry.get("previous_sha256") != previous
                or not isinstance(entry.get("history_rows"), list)
                or not entry["history_rows"]
                or not isinstance(entry.get("state_fields"), dict)
                or not _hex(entry.get("sha256"))):
            raise JournalInvalid("journal entry is missing, duplicated, or out of order")
        _meta({**entry["state_fields"], "command_history": []})
        if entry["state_fields"].get("format_version") != FULL_VERSION:
            raise JournalInvalid("journal state must restore the original full schema")
        for row in entry["history_rows"]:
            if (not isinstance(row, dict) or type(row.get("index")) is not int
                    or row["index"] != expected_index):
                raise JournalInvalid("journal history has a gap or duplicate")
            expected_index += 1
        body = {k: v for k, v in entry.items() if k != "sha256"}
        if _sha(_canonical(body)) != entry["sha256"]:
            raise JournalInvalid("journal entry checksum mismatch")
        previous = entry["sha256"]
    return entries, previous, expected_index - 1


def append_delta(journal: dict[str, object], rows: list[dict[str, object]],
                 state_fields: dict[str, object]) -> dict[str, object]:
    if journal.get("consolidated_sha256") is not None:
        raise JournalInvalid("consolidation marker forbids a later delta")
    _, previous, last_index = _validated_entries(journal)
    if not rows or any(type(r.get("index")) is not int or r["index"] != last_index + i + 1
                       for i, r in enumerate(rows)):
        raise JournalInvalid("new rows must extend the committed history contiguously")
    _meta({**state_fields, "command_history": []})
    if state_fields.get("format_version") != FULL_VERSION:
        raise JournalInvalid("delta scalar state must use the original full schema")
    body = {"sequence": len(journal["entries"]) + 1,
            "previous_sha256": previous, "history_rows": rows,
            "state_fields": state_fields}
    encoded_delta = _canonical(body)
    if len(encoded_delta) > MAX_DELTA_BYTES:
        raise JournalCapacity("delta exceeds bounded journal eligibility")
    entry = {**body, "sha256": _sha(encoded_delta)}
    next_journal = {**journal, "entries": [*journal["entries"], entry]}
    if len(_canonical(next_journal)) > MAX_JOURNAL_BYTES:
        raise JournalCapacity("journal exceeds bounded consolidation threshold")
    return next_journal


def mark_consolidation(journal: dict[str, object], full_bytes: bytes) -> dict[str, object]:
    _validated_entries(journal)
    return {**journal, "consolidated_sha256": _sha(full_bytes)}


def replay(base_bytes: bytes, journal_bytes: bytes | None) -> tuple[dict[str, object], str]:
    try:
        base = json.loads(base_bytes)
        if not isinstance(base, dict):
            raise JournalInvalid("base state is not an object")
        if journal_bytes is None:
            if base.get("format_version") == SEALED_VERSION:
                raise JournalInvalid("sealed Driver baseline is missing its journal")
            _meta(base)
            return base, "base_only"
        journal = json.loads(journal_bytes)
        if not isinstance(journal, dict):
            raise JournalInvalid("journal is not an object")
        entries, _, _ = _validated_entries(journal)
        current_sha = _sha(base_bytes)
        if journal.get("consolidated_sha256") == current_sha:
            if base.get("format_version") != FULL_VERSION:
                raise JournalInvalid("consolidated base is not the original full schema")
            _meta(base)
            return base, "already_consolidated"
        if current_sha != journal["base_sha256"]:
            raise JournalInvalid("base SHA does not match the journal")
        if (base.get("format_version") != SEALED_VERSION
                or base.get("schema") != SEALED_SCHEMA
                or set(base) != {"format_version", "schema", "sealed_full_state"}
                or not isinstance(base.get("sealed_full_state"), dict)):
            raise JournalInvalid("journal baseline lacks its sealed envelope")
        base = base["sealed_full_state"]
        _meta(base)
        if base.get("format_version") != FULL_VERSION:
            raise JournalInvalid("sealed full state is not the original schema")
        history = base.get("command_history")
        if not isinstance(history, list) or len(history) != journal["base_history_rows"]:
            raise JournalInvalid("base history count does not match the journal")
        for entry in entries:
            history.extend(entry["history_rows"])
            base = {**entry["state_fields"], "command_history": history}
        base["format_version"] = FULL_VERSION
        return base, "replayed"
    except (UnicodeError, json.JSONDecodeError, TypeError, KeyError, OverflowError) as error:
        raise JournalInvalid(f"journal is malformed: {error}") from error


def load_pair(base_path: Path) -> tuple[dict[str, object], str]:
    journal_path = base_path.with_name(FILENAME)
    return replay(base_path.read_bytes(), journal_path.read_bytes() if journal_path.exists() else None)


def publish_journal(path: Path, journal: dict[str, object],
                    write_atomic: Callable[[Path, bytes], None]) -> int:
    data = _canonical(journal)
    if len(data) > MAX_JOURNAL_BYTES:
        raise JournalCapacity("journal capacity exceeded")
    write_atomic(path, data)
    return len(data)


_FULL_FIELD_ORDER = (
    "format_version", "pipe_name", "bridge_pid", "episode_character_id",
    "episode_run_id", "last_checkpoint", "command_history",
    "rollback_war_failure", "managed_restore_transaction",
    "succession_expectation", "succession_lifecycle", "campaign_goal",
    "rollback_war_failures",
)


def full_state_bytes(payload: dict[str, object]) -> bytes:
    """Render the original full JSON schema, including its field order."""
    _meta(payload)
    if not isinstance(payload.get("command_history"), list):
        raise JournalInvalid("full-state history is malformed")
    ordered = {key: payload[key] for key in _FULL_FIELD_ORDER if key in payload}
    if set(ordered) != set(payload):
        raise JournalInvalid("full-state fields changed")
    return json.dumps(ordered, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def consolidate_closed_pair(
    base_path: Path, *, owner_closed: bool,
    write_atomic: Callable[[Path, bytes], None],
) -> str:
    """Offline recovery barrier; caller must prove the old SDK owner is closed.

    Both possible crash points remain readable: the old base plus marked journal
    replays, or the new base plus old marker is recognized as consolidated.
    """
    if owner_closed is not True:
        raise JournalInvalid("offline consolidation requires a closed SDK owner")
    journal_path = base_path.with_name(FILENAME)
    base_bytes = base_path.read_bytes()
    journal_bytes = journal_path.read_bytes() if journal_path.exists() else None
    payload, status = replay(base_bytes, journal_bytes)
    if status == "base_only":
        return status
    if status == "already_consolidated":
        journal_path.unlink(missing_ok=True)
        return status
    assert journal_bytes is not None
    journal = json.loads(journal_bytes)
    replacement = full_state_bytes(payload)
    marked = mark_consolidation(journal, replacement)
    # Check the old base again before publishing the two-file transition.
    if _sha(base_path.read_bytes()) != journal["base_sha256"]:
        raise JournalInvalid("base changed before offline consolidation")
    publish_journal(journal_path, marked, write_atomic)
    if _sha(base_path.read_bytes()) != journal["base_sha256"]:
        raise JournalInvalid("base changed after consolidation marker")
    write_atomic(base_path, replacement)
    journal_path.unlink(missing_ok=True)
    return "consolidated"


def materialize_closed_directory(
    source_dir: Path, output_dir: Path, *, owner_closed: bool,
    expected_base_sha256: str, expected_journal_sha256: str,
) -> dict[str, object]:
    """Create one v2 cold input in a new directory, never changing the source.

    The caller binds both input hashes to a sealed owner-exit receipt. This
    routine requires a unique output path and never silently falls back to a
    stale full file when the journal is missing.
    """
    if owner_closed is not True:
        raise JournalInvalid("materialization requires a closed SDK owner")
    if not _hex(expected_base_sha256) or not _hex(expected_journal_sha256):
        raise JournalInvalid("materialization needs both pinned source hashes")
    source_base = source_dir / "native-session" / "driver-state.json"
    source_journal = source_base.with_name(FILENAME)
    base_bytes = source_base.read_bytes()
    if _sha(base_bytes) != expected_base_sha256:
        raise JournalInvalid("sealed source base SHA differs")
    try:
        journal_bytes = source_journal.read_bytes()
    except FileNotFoundError as error:
        raise JournalInvalid("sealed source journal was omitted") from error
    if _sha(journal_bytes) != expected_journal_sha256:
        raise JournalInvalid("sealed source journal SHA differs")
    payload, status = replay(base_bytes, journal_bytes)
    if status != "replayed":
        raise JournalInvalid("source is not an active sealed journal pair")
    output_base = output_dir / "native-session" / "driver-state.json"
    output_base.parent.mkdir(parents=True, exist_ok=True)
    data = full_state_bytes(payload)
    temporary = output_base.with_name(output_base.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows os.rename refuses an existing target; the target directory is
        # create-only and must not contain an earlier cold candidate.
        os.rename(temporary, output_base)
    finally:
        temporary.unlink(missing_ok=True)
    return {"status": "materialized_v2", "source_base_sha256": expected_base_sha256,
            "source_journal_sha256": expected_journal_sha256,
            "materialized_sha256": _sha(data), "materialized_bytes": len(data),
            "history_rows": len(payload["command_history"]),
            "output_path": str(output_base)}


def recover_aborted_activation(base_path: Path, *, owner_closed: bool) -> str:
    """Remove only an empty header published before the first v3 base replace.

    No history row was committed. A populated, malformed, or foreign journal
    is never discarded through this recovery path.
    """
    if owner_closed is not True:
        raise JournalInvalid("activation recovery requires a closed SDK owner")
    journal_path = base_path.with_name(FILENAME)
    base_bytes = base_path.read_bytes()
    journal_bytes = journal_path.read_bytes()
    try:
        base = json.loads(base_bytes)
        journal = json.loads(journal_bytes)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise JournalInvalid(f"aborted activation is malformed: {error}") from error
    if (not isinstance(base, dict) or base.get("format_version") != FULL_VERSION
            or not isinstance(journal, dict) or journal.get("entries") != []
            or journal.get("consolidated_sha256") is not None):
        raise JournalInvalid("activation is not an empty pre-base header")
    _validated_entries(journal)
    if (journal["base_history_rows"] != len(base.get("command_history", []))
            or journal["base_sha256"] != _sha(sealed_base_bytes(base_bytes))):
        raise JournalInvalid("empty header does not bind the original full base")
    if base_path.read_bytes() != base_bytes or journal_path.read_bytes() != journal_bytes:
        raise JournalInvalid("activation inputs changed during recovery")
    journal_path.unlink()
    return "aborted_no_committed_rows"
