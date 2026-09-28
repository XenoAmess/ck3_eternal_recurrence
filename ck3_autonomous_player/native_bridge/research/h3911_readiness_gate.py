"""Bounded, attempt-local CK3 cold-load log gate for the H3911 receiver.

This only delays MCP snapshot reads. It never treats a log marker as a map,
episode, player, war, or paused-state proof.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
from typing import Awaitable, Callable


POSTREAD = "CGameState::InitPostRead"
VASSALS = "Setup powerful vassals among"


def probe_postread(
    attempt_root: Path, debug_log: Path, launch_started_at_utc: datetime
) -> dict[str, object]:
    """Read only this attempt's debug log; reject a prior attempt's markers."""
    expected = attempt_root / "state" / "profile" / "logs" / "debug.log"
    if debug_log.resolve() != expected.resolve():
        raise ValueError("cold-load log is outside this exact attempt")
    if launch_started_at_utc.tzinfo is None:
        raise ValueError("launch timestamp must have a timezone")
    result: dict[str, object] = {"path": str(expected), "stage": "missing"}
    if not debug_log.is_file():
        return result
    stat = debug_log.stat()
    result.update({"bytes": stat.st_size,
                   "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()})
    if stat.st_mtime < launch_started_at_utc.timestamp() - 2:
        result["stage"] = "stale_before_this_launch"
        return result
    data = debug_log.read_bytes()
    result["sha256"] = hashlib.sha256(data).hexdigest().upper()
    lines = data.decode("utf-8-sig", errors="replace").splitlines()
    postread = next((index for index, line in enumerate(lines) if POSTREAD in line), None)
    if postread is None:
        result["stage"] = "pre_postread"
        return result
    result["postread_line"] = lines[postread][:240]
    vassals = next((index for index in range(postread + 1, len(lines))
                    if VASSALS in lines[index]), None)
    if vassals is None:
        result["stage"] = "postread_started"
        return result
    result["vassals_line"] = lines[vassals][:240]
    result["stage"] = "postread_vassals_seen"
    return result


async def wait_for_postread_grace(
    attempt_root: Path,
    debug_log: Path,
    launch_started_at_utc: datetime,
    *,
    deadline: float,
    grace_seconds: float = 60,
    poll_seconds: float = 5,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    record_probe: Callable[[dict[str, object]], None] | None = None,
) -> dict[str, object]:
    """Wait within the caller's existing deadline; leave MCP identity checks intact."""
    if grace_seconds < 0 or poll_seconds <= 0:
        raise ValueError("grace and poll interval must be bounded")
    first_seen: float | None = None
    last: dict[str, object] | None = None
    while True:
        now = clock()
        if now >= deadline:
            raise TimeoutError(f"H3911 postread log gate timed out: {last}")
        last = probe_postread(attempt_root, debug_log, launch_started_at_utc)
        if record_probe is not None:
            record_probe({**last, "observed_monotonic": now,
                          "remaining_seconds": deadline - now})
        if last["stage"] == "postread_vassals_seen":
            if first_seen is None:
                first_seen = now
            if now - first_seen >= grace_seconds:
                return {**last, "grace_seconds": grace_seconds,
                        "grace_completed_monotonic": now}
        remaining = deadline - now
        until_grace = (grace_seconds - (now - first_seen)
                       if first_seen is not None else poll_seconds)
        await sleep(min(poll_seconds, remaining, max(until_grace, 0.001)))
