"""Dormant managed worker entry for R0368 role-only reads.

The native role query already exists, but the supervisor cannot yet prove an
injector PID and its complete descendant tree. This worker therefore has no
CK3/session import or executable live branch. A later reviewed change must
wire that evidence before enabling a managed read.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROLE_ONLY_WORKER_LIVE_AUTHORIZED = False


def no_launch_report() -> dict[str, object]:
    return {
        "schema": "xar.war.r0368.role-only-managed-worker.v1",
        "status": "DORMANT_NO_LAUNCH",
        "worker_live_authorized": False,
        "native_session_wired": False,
        "injector_pid_tree_proof_available": False,
        "ck3_started": False,
        "worker_executed": False,
        "screen_acquired": False,
        "task_bus_mutated": False,
        "query_attempts": 0,
        "gameplay_actions": 0,
        "date_advance_actions": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dormant R0368 role-only worker")
    parser.add_argument("--no-launch", action="store_true")
    parser.add_argument("--worker")
    parser.add_argument("--go", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.no_launch == (args.worker is not None):
        parser.error("select exactly one of --no-launch or --worker")
    if args.worker is not None:
        # Deliberately refuse before reading GO, creating output or importing
        # any game/session module. The old exact-argv gate can verify this blob
        # without accidentally authorizing the missing live supervisor.
        print("R0368 managed worker live gate is closed")
        return 2
    if args.go is not None or args.output is not None or args.report is None:
        parser.error("--no-launch takes only --report")
    report = no_launch_report()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(args.report, report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
