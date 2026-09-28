"""Renew an already owned CK3 screen lease during a bounded recording.

This helper never acquires a resource. It writes a new, fsynced journal and
stops with a nonzero result if the task loses its acquired screen resource.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--bus-script", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=int, default=180)
    parser.add_argument("--max-seconds", type=int, default=7200)
    args = parser.parse_args()
    if not 30 <= args.interval_seconds <= 240:
        parser.error("interval must be 30..240 seconds")
    if not 300 <= args.max_seconds <= 14400:
        parser.error("max duration must be 300..14400 seconds")
    if not args.bus_script.is_file():
        parser.error("task bus script is missing")
    if not args.journal.parent.is_dir():
        parser.error("journal parent directory must already exist")

    # Exclusive creation makes a repeated invocation a new attempt, never an
    # overwrite of the previous lease evidence.
    try:
        with args.journal.open("xb"):
            pass
    except FileExistsError:
        parser.error("journal already exists; choose a new attempt path")

    def append(row: dict[str, object]) -> None:
        data = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        with args.journal.open("ab") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    deadline = time.monotonic() + args.max_seconds
    errors = 0
    try:
        while time.monotonic() < deadline:
            try:
                call = subprocess.run(
                    [sys.executable, str(args.bus_script), "heartbeat", "--task", args.task],
                    capture_output=True, text=True, timeout=60, check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                append({"at_utc": utc(), "result": "HEARTBEAT_ERROR", "error": str(exc)})
                errors += 1
                if errors >= 3:
                    return 2
                time.sleep(15)
                continue
            try:
                body = json.loads(call.stdout) if call.returncode == 0 else {}
            except json.JSONDecodeError:
                body = {}
            task = body.get("task") or {}
            owned = "ck3-screen:acquired" in (task.get("resources") or [])
            sequence = (body.get("event") or {}).get("sequence")
            append({"at_utc": utc(), "result": "OWNED" if owned else "NOT_OWNED",
                    "exit_code": call.returncode, "task_id": task.get("task_id"),
                    "task_updated_at_utc": task.get("updated_at_utc"),
                    "sequence": sequence, "stderr_tail": call.stderr[-500:]})
            if call.returncode == 0 and not owned:
                return 2
            if call.returncode != 0:
                errors += 1
                if errors >= 3:
                    return 2
                time.sleep(15)
                continue
            errors = 0
            print(f"screen lease owned; heartbeat sequence={sequence}", flush=True)
            time.sleep(args.interval_seconds)
    except KeyboardInterrupt:
        append({"at_utc": utc(), "result": "STOPPED_BY_OPERATOR"})
        return 0
    append({"at_utc": utc(), "result": "MAX_DURATION_REACHED"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
