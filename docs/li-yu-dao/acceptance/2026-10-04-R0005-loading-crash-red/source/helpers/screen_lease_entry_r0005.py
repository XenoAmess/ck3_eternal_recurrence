"""Thin external entry for the existing ScreenLeaseKeeper. Never acquires,
releases, launches, injects, sends input, or registers a task. Root first owns
the exact screen task; this process only renews its current CAS sequence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import threading
import time

BASE = Path(__file__).resolve().parent
OWNER_CHECKOUT = Path("C:/workspace/ck3_eternal_recurrence")
OWNER_HEAD = "18b1944d1784d3e4ec57189c016335ef135b9b34"
TASK_ID = "ck3-lyd-live-006-20261004"
BUS = Path("C:/workspace/.codex-task-bus")
CLI = OWNER_CHECKOUT / "tools/codex_task_bus.py"
CLI_SHA = "B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE"

sys.path.insert(0, str(OWNER_CHECKOUT / "promo/ck3_native_war_ai/integration"))
from screen_bus_lease import (ScreenLeaseKeeper, call_bus, checked_cli_pair,
                              checked_owner, checkout_head, MAX_AGE_SECONDS)


def write_new(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "screen-lease-live-r0005")
    parser.add_argument("--expected-sequence", type=int,
                        help="optional explicit latest owner sequence; otherwise bind locked-list current sequence once")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    checked_cli_pair(CLI, BUS / "bin/codex_task_bus.py", CLI_SHA.upper())
    actual_head = checkout_head(OWNER_CHECKOUT)
    if actual_head != OWNER_HEAD:
        raise RuntimeError("owner checkout HEAD changed; issue a newly reviewed external entry")
    output = args.output.resolve()
    if BASE.resolve() not in output.parents:
        raise ValueError("all keeper ledgers must remain below this external task root")
    prefix = [sys.executable, str(CLI), "--bus-dir", str(BUS), "--expected-cli-sha256", CLI_SHA.upper()]
    plan = {
        "owner_checkout": str(OWNER_CHECKOUT), "owner_head": OWNER_HEAD,
        "task_id": TASK_ID, "bus_cli_sha256": CLI_SHA.upper(),
        "stale_after_seconds": MAX_AGE_SECONDS, "renew_every_seconds": 180,
        "poll_every_seconds": 30, "poll_ack": False,
        "root_register_argv": prefix + ["register", "--task", TASK_ID, "--repo", str(OWNER_CHECKOUT),
                                       "--summary", "LYD-formal-R0005-exact-screen-owner", "--next-step", "Fresh-offline-map-native-acceptance",
                                       "--resource", "ck3-screen:acquired"],
        "root_poll_argv": prefix + ["poll", "--task", TASK_ID, "--ack", "--limit", "100"],
        "keeper_start_argv": [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--output", str(output)],
        "root_release_argv": prefix + ["release-screen-cas", "--task", TASK_ID, "--expected-sequence", "<FINAL.last_sequence>",
                                      "--summary", "LYD-formal-R0005-ended"],
        "keeper_scope": "existing helper only; no acquire/release/game/desktop actions",
    }
    if args.plan_only:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if output.exists():
        raise ValueError("use a new keeper output; previous ledgers are retained")
    output.mkdir(parents=True)
    write_new(output / "INPUTS.json", plan)
    abort = threading.Event()
    keeper = None
    error = None
    try:
        owner_list = call_bus(CLI, BUS, CLI_SHA.upper(), "list", "--stale-after", str(MAX_AGE_SECONDS),
                              audit_dir=output / "admission-audit")
        matches = [row for row in owner_list.get("tasks", []) if row.get("task_id") == TASK_ID]
        if len(matches) != 1:
            raise RuntimeError("Root must register the exact screen task before starting this keeper")
        sequence = args.expected_sequence if args.expected_sequence is not None else matches[0].get("last_sequence")
        if type(sequence) is not int or sequence <= 0:
            raise RuntimeError("screen owner has no positive current CAS sequence")
        checked_owner(owner_list["tasks"], TASK_ID, sequence, OWNER_CHECKOUT, OWNER_HEAD)
        write_new(output / "ADMITTED.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "sequence": sequence, "owner": matches[0]})

        def lost():
            marker = output / "ROOT_STOP_REQUIRED.json"
            if not marker.exists():
                write_new(marker, {"at_utc": datetime.now(timezone.utc).isoformat(),
                                   "reason": "lease lost or uncertain; Root must stop its managed live actions/session",
                                   "keeper_failure": keeper.failure if keeper is not None else None})
            print("ROOT_STOP_REQUIRED: lease lost or uncertain", flush=True)

        keeper = ScreenLeaseKeeper(source=CLI, bus_dir=BUS, expected_sha=CLI_SHA.upper(),
            task_id=TASK_ID, sequence=sequence, repo=OWNER_CHECKOUT,
            journal=output / "screen-lease.jsonl", abort=abort, interval_seconds=180,
            audit_dir=output / "renewal-audit", on_abort=lost)
        keeper.start()
        first = keeper.refresh()
        write_new(output / "READY.json", {"at_utc": datetime.now(timezone.utc).isoformat(), "lease": first})
        print(json.dumps({"status": "READY", "last_sequence": keeper.sequence, "output": str(output)}, ensure_ascii=False), flush=True)
        next_poll = 0.0
        while not abort.is_set() and not (output / "STOP.request").exists():
            if time.monotonic() >= next_poll:
                # Non-acknowledging read preserves notices for Root/native guard.
                packet = call_bus(CLI, BUS, CLI_SHA.upper(), "poll", "--task", TASK_ID, "--limit", "100",
                                  audit_dir=output / "poll-audit")
                with (output / "poll.jsonl").open("a", encoding="utf-8", newline="\n") as journal:
                    journal.write(json.dumps({"at_utc": datetime.now(timezone.utc).isoformat(), "packet": packet}, ensure_ascii=False) + "\n")
                if packet.get("events"):
                    print(json.dumps({"status": "ROOT_NOTICES_AVAILABLE", "event_count": len(packet["events"])}, ensure_ascii=False), flush=True)
                next_poll = time.monotonic() + 30
            abort.wait(1)
        if abort.is_set():
            raise RuntimeError(keeper.failure or "keeper abort set")
    except BaseException as failure:
        error = repr(failure)
        abort.set()
        print(json.dumps({"status": "RED", "error": error}, ensure_ascii=False), flush=True)
    finally:
        if keeper is not None:
            keeper.stop()
        report = keeper.report() if keeper is not None else {"task_id": TASK_ID, "last_sequence": None, "thread_exited": True}
        report.update({"at_utc": datetime.now(timezone.utc).isoformat(), "entry_error": error,
                       "screen_released": False, "game_actions": False})
        write_new(output / "FINAL.json", report)
    return 1 if error or report.get("failure") else 0


if __name__ == "__main__":
    raise SystemExit(main())
