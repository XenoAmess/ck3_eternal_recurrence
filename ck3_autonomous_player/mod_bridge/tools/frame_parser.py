"""Parse complete XAR_MCP snapshot frames from CK3 debug.log text.

The parser intentionally ignores CK3's timestamp/logger prefix and incomplete
frames.  Repeated frames are expected because the 0.4-second GUI poll can run
the same inbox more than once before the companion replaces it with the no-op
template.
"""

from __future__ import annotations

from dataclasses import dataclass


PREFIX = "XAR_MCP:"


@dataclass(frozen=True)
class SnapshotFrame:
    request_id: str
    player_id: int
    date: str
    total_days: int
    status: str


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
    """Return complete BEGIN -> STATE -> ACK -> END snapshot frames."""

    pending: dict[str, dict[str, str]] = {}
    completed: list[SnapshotFrame] = []

    for line in log_text.splitlines():
        parsed = _event_from_line(line)
        if parsed is None:
            continue
        event, fields = parsed
        request_id = fields.get("request_id")

        if event == "BEGIN" and fields.get("kind") == "snapshot" and request_id:
            pending[request_id] = dict(fields)
            continue

        if event == "STATE":
            # The state line intentionally omits request_id to keep the game
            # formatter minimal.  There is only one write request in flight;
            # attach it to the most recently opened frame.
            if pending:
                latest = next(reversed(pending))
                pending[latest].update(fields)
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
                SnapshotFrame(
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
