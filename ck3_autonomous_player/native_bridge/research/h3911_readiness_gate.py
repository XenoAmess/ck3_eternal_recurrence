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


def bridge_diagnostic_progress(
    value: dict[str, object], *, expected_pid: int, expected_exe_sha256: str,
    previous: tuple[int, int] | None,
) -> tuple[bool, tuple[int, int] | None]:
    """Require a live DLL/pipe and two advancing heartbeats before a game read.

    This is only transport readiness. A complete paused episode still requires
    two matching semantic snapshots and the exact war identity checks.
    """
    if not isinstance(value, dict):
        raise RuntimeError("H3911 bridge diagnostic response is malformed")
    if value.get("transport_fatal_error") is not None:
        raise RuntimeError("H3911 native bridge transport has a fatal error")
    if value.get("connected") is not True:
        if previous is not None:
            raise RuntimeError("H3911 bridge disconnected after an observed heartbeat")
        return False, None
    hello = value.get("hello")
    if (type(expected_pid) is not int or expected_pid <= 0
            or type(value.get("bridge_pid")) is not int
            or value["bridge_pid"] != expected_pid
            or not isinstance(hello, dict)
            or hello.get("pid") != expected_pid
            or hello.get("expected_ck3_sha256") != expected_exe_sha256):
        raise RuntimeError("H3911 bridge hello differs from the managed CK3 identity")
    generation = value.get("connection_generation")
    heartbeat = value.get("last_heartbeat")
    sequence = heartbeat.get("sequence") if isinstance(heartbeat, dict) else None
    if (type(generation) is not int or generation <= 0
            or hello.get("connection_generation") != generation):
        raise RuntimeError("H3911 bridge connection generation regressed or mismatched")
    if type(sequence) is not int or sequence < 0:
        return False, None
    current = (generation, sequence)
    if previous is not None:
        if generation != previous[0] or sequence < previous[1]:
            raise RuntimeError("H3911 bridge connection or heartbeat regressed")
        if (value.get("semantic_state_available") is True
                and sequence > previous[1]):
            return True, current
    return False, current


def remaining_snapshot_timeout(deadline: float, now: float, tool_seconds: float) -> float:
    """Cap one snapshot call by both its original limit and readiness time."""
    if tool_seconds <= 0 or now >= deadline:
        raise TimeoutError("H3911 readiness deadline expired before snapshot submission")
    return min(tool_seconds, deadline - now)


def require_absent_prelaunch_log(attempt_root: Path, debug_log: Path) -> dict[str, object]:
    """A new attempt must not inherit debug text before its CK3 launch."""
    expected = attempt_root / "state" / "profile" / "logs" / "debug.log"
    if debug_log.resolve() != expected.resolve():
        raise ValueError("cold-load log is outside this exact attempt")
    receipt: dict[str, object] = {"path": str(expected), "exists_before_launch": debug_log.exists()}
    if debug_log.exists():
        raise RuntimeError("fresh H3911 attempt already has a debug.log before CK3 launch")
    return receipt


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
    result.update({"bytes": stat.st_size, "file_device": stat.st_dev,
                   "file_inode": stat.st_ino,
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
    completed_file_identity: tuple[object, object] | None = None
    completed_min_bytes = 0
    while True:
        now = clock()
        if now >= deadline:
            raise TimeoutError(f"H3911 postread log gate timed out: {last}")
        last = probe_postread(attempt_root, debug_log, launch_started_at_utc)
        now = clock()
        if now >= deadline:
            raise TimeoutError(f"H3911 postread log gate timed out after probe: {last}")
        if completed_file_identity is not None:
            identity = (last.get("file_device"), last.get("file_inode"))
            if (last["stage"] != "postread_vassals_seen"
                    or identity != completed_file_identity
                    or not isinstance(last.get("bytes"), int)
                    or last["bytes"] < completed_min_bytes):
                raise RuntimeError("H3911 cold-load log regressed or was replaced during grace")
            completed_min_bytes = last["bytes"]
        if record_probe is not None:
            record_probe({**last, "observed_monotonic": now,
                          "remaining_seconds": deadline - now})
        if last["stage"] == "postread_vassals_seen":
            if first_seen is None:
                first_seen = now
                completed_file_identity = (last["file_device"], last["file_inode"])
                completed_min_bytes = last["bytes"]
            if now - first_seen >= grace_seconds:
                return {**last, "grace_seconds": grace_seconds,
                        "grace_completed_monotonic": now}
        remaining = deadline - now
        until_grace = (grace_seconds - (now - first_seen)
                       if first_seen is not None else poll_seconds)
        await sleep(min(poll_seconds, remaining, max(until_grace, 0.001)))
