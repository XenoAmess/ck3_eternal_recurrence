"""Optional scalar stage receipts; never serialize gameplay or history data."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time


_WRITE_LOCK = threading.Lock()
ArmyTiming = tuple[str, str, int, str | None]


def start_army_timing(stage: str, *, native_request_id: str | None = None) -> ArmyTiming | None:
    path = os.environ.get("XAR_CK3_ARMY_TIMING_JSONL")
    if not path:
        return None
    return path, stage, time.perf_counter_ns(), native_request_id


def finish_army_timing(
    timing: ArmyTiming | None, *, step: str = "query-army-strengths-v1",
    date_raw: int | None = None,
) -> None:
    if timing is None:
        return
    path, stage, started_ns, native_request_id = timing
    ended_ns = time.perf_counter_ns()
    try:
        row = {
            "schema": "xar.ck3.army-query-timing.v1",
            "stage": stage,
            "step": step,
            "elapsed_ns": ended_ns - started_ns,
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "native_request_id": native_request_id,
        }
        if date_raw is not None:
            row["date_raw"] = date_raw
        encoded = json.dumps(row, separators=(",", ":")) + "\n"
        with _WRITE_LOCK, Path(path).open("a", encoding="utf-8") as stream:
            stream.write(encoded)
    except (OSError, TypeError, ValueError):
        # Optional diagnostics must not change an already executed command.
        pass
