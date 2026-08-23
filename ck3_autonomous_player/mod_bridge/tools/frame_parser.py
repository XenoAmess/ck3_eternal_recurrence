"""Parse complete XAR_MCP snapshot frames from CK3 debug.log text.

The parser intentionally ignores CK3's timestamp/logger prefix and incomplete
frames.  Repeated frames are expected because the 0.4-second GUI poll can run
the same inbox more than once before the companion replaces it with the no-op
template.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


PREFIX = "XAR_MCP:"


@dataclass(frozen=True)
class OneLifeSettlementFrame:
    """A committed one-generation Rogue settlement projected by the main Mod.

    ``ready=False`` is a typed, unpublished projection.  Its payload fields are
    intentionally ``None``.  A legacy bridge frame has no ``SETTLEMENT`` event
    at all and is represented by ``SnapshotFrame.one_life_settlement is None``.
    """

    ready: bool
    commit_serial: int
    source_character_id: int | None = None
    final_score: int | float | None = None
    score_before_reject: int | float | None = None
    record_candidate: int | None = None
    old_record: int | None = None
    record_delta: int | None = None
    blessing_count: int | None = None
    refusal_count: int | None = None
    contract_progress: int | None = None
    record_written: bool | None = None


@dataclass(frozen=True)
class SnapshotFrame:
    request_id: str
    player_id: int
    date: str
    total_days: int
    status: str
    one_life_settlement: OneLifeSettlementFrame | None = None


def _event_from_line(line: str) -> tuple[str, dict[str, str]] | None:
    marker = line.find(PREFIX)
    if marker < 0:
        return None
    parts = line[marker + len(PREFIX) :].strip().split("|")
    event = parts[0]
    fields: dict[str, str] = {}
    for part in parts[1:]:
        key, separator, value = part.partition("=")
        if separator:
            fields[key] = value
    return event, fields


def parse_complete_snapshots(log_text: str) -> list[SnapshotFrame]:
    """Return complete typed snapshot frames.

    Schema-1 frames without the optional ``SETTLEMENT`` event remain valid.
    A malformed optional settlement payload is ignored without discarding the
    otherwise usable base snapshot.
    """

    pending: dict[str, dict[str, str]] = {}
    pending_settlements: dict[str, dict[str, str]] = {}
    completed: list[SnapshotFrame] = []

    for line in log_text.splitlines():
        parsed = _event_from_line(line)
        if parsed is None:
            continue
        event, fields = parsed
        request_id = fields.get("request_id")

        if event == "BEGIN" and fields.get("kind") == "snapshot" and request_id:
            pending[request_id] = dict(fields)
            pending_settlements.pop(request_id, None)
            continue

        if event == "STATE":
            # The state line intentionally omits request_id to keep the game
            # formatter minimal.  There is only one write request in flight;
            # attach it to the most recently opened frame.
            if pending:
                latest = next(reversed(pending))
                pending[latest].update(fields)
            continue

        if event == "SETTLEMENT":
            if pending:
                latest = next(reversed(pending))
                pending_settlements[latest] = dict(fields)
            continue

        if event == "ACK" and request_id in pending:
            pending[request_id].update(fields)
            continue

        if event != "END" or request_id not in pending:
            continue

        frame = pending.pop(request_id)
        settlement = _parse_settlement(pending_settlements.pop(request_id, None))
        required = {"player_id", "date", "total_days", "status"}
        if not required.issubset(frame) or frame.get("status") != "ok":
            continue
        try:
            completed.append(
                SnapshotFrame(
                    request_id=request_id,
                    player_id=int(frame["player_id"]),
                    date=frame["date"],
                    total_days=int(frame["total_days"]),
                    status=frame["status"],
                    one_life_settlement=settlement,
                )
            )
        except ValueError:
            continue

    return completed


def _parse_settlement(
    fields: dict[str, str] | None,
) -> OneLifeSettlementFrame | None:
    if fields is None:
        return None
    ready = _parse_bool(fields.get("ready"))
    commit_serial = _parse_int(fields.get("commit_serial"))
    if ready is None or commit_serial is None:
        return None
    if not ready:
        return OneLifeSettlementFrame(ready=False, commit_serial=commit_serial)

    source_character_id = _parse_int(fields.get("source_character_id"))
    final_score = _parse_number(fields.get("final_score"))
    score_before_reject = _parse_number(fields.get("score_before_reject"))
    record_candidate = _parse_int(fields.get("record_candidate"))
    old_record = _parse_int(fields.get("old_record"))
    record_delta = _parse_int(fields.get("record_delta"))
    blessing_count = _parse_int(fields.get("blessing_count"))
    refusal_count = _parse_int(fields.get("refusal_count"))
    contract_progress = _parse_int(fields.get("contract_progress"))
    record_written = _parse_bool(fields.get("record_written"))
    required = (
        source_character_id,
        final_score,
        score_before_reject,
        record_candidate,
        old_record,
        record_delta,
        blessing_count,
        refusal_count,
        contract_progress,
        record_written,
    )
    if any(value is None for value in required):
        return None
    return OneLifeSettlementFrame(
        ready=True,
        commit_serial=commit_serial,
        source_character_id=source_character_id,
        final_score=final_score,
        score_before_reject=score_before_reject,
        record_candidate=record_candidate,
        old_record=old_record,
        record_delta=record_delta,
        blessing_count=blessing_count,
        refusal_count=refusal_count,
        contract_progress=contract_progress,
        record_written=record_written,
    )


def _parse_bool(value: str | None) -> bool | None:
    if value == "0":
        return False
    if value == "1":
        return True
    return None


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if not number.is_finite() or number != number.to_integral_value():
        return None
    return int(number)


def _parse_number(value: str | None) -> int | float | None:
    if value is None:
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if number == number.to_integral_value():
        return int(number)
    return float(number)
