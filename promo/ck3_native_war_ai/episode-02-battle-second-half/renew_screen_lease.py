"""CAS renewal for an already registered, uniquely owned CK3 screen task.

This standalone helper is for managed sessions that do not renew internally.
capture_session.py has its own keeper; never run both for the same task. A lost
or uncertain renewal stops immediately and leaves its journal as RED evidence.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "promo" / "ck3_native_war_ai" / "integration"))
from screen_bus_lease import renew_once  # noqa: E402


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--expected-sequence", required=True, type=int)
    parser.add_argument("--expected-cli-sha256", required=True)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--interval-seconds", type=int, default=180)
    parser.add_argument("--max-seconds", type=int, default=7200)
    args = parser.parse_args()
    if not 30 <= args.interval_seconds <= 240:
        parser.error("interval must be 30..240 seconds")
    if not 300 <= args.max_seconds <= 14400:
        parser.error("max duration must be 300..14400 seconds")
    if not args.journal.parent.is_dir():
        parser.error("journal parent directory must already exist")
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

    sequence = args.expected_sequence
    deadline = time.monotonic() + args.max_seconds
    try:
        while time.monotonic() < deadline:
            try:
                row = renew_once(
                    source=ROOT / "tools" / "codex_task_bus.py",
                    bus_dir=Path("D:/workspace/.codex-task-bus"),
                    expected_sha=args.expected_cli_sha256,
                    task_id=args.task, expected_sequence=sequence, repo=ROOT)
            except Exception as error:
                append({"at_utc": utc(), "result": "LOST_OR_UNCERTAIN_STOP",
                        "expected_sequence": sequence, "error": repr(error)})
                return 2
            sequence = row["sequence"]
            append({"at_utc": utc(), "result": "OWNED_CAS", "lease": row})
            print(f"screen lease CAS sequence={sequence}", flush=True)
            time.sleep(args.interval_seconds)
    except KeyboardInterrupt:
        append({"at_utc": utc(), "result": "STOPPED_BY_OPERATOR",
                "last_sequence": sequence})
        return 0
    append({"at_utc": utc(), "result": "MAX_DURATION_REACHED",
            "last_sequence": sequence})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
