"""Renew an already owned shared CK3 screen lease; never acquire or release it."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import time

BUS_SHA = "B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE"


def require(value, message):
    if not value:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    require(isinstance(value, dict), "JSON object required: " + str(path))
    return value


def pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check_pin(row):
    actual = pin(row["path"])
    require(type(row.get("bytes")) is int and actual["bytes"] == row["bytes"] and
            actual["sha256"] == str(row.get("sha256", "")).lower(),
            "Pinned input changed: " + str(row["path"]))
    return actual


def write_new(path, value):
    path = Path(path)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def load_lease_module(repo):
    source = Path(repo) / "promo/ck3_native_war_ai/integration/screen_bus_lease.py"
    spec = importlib.util.spec_from_file_location("shared_acceptance_screen_bus_lease", source)
    require(spec is not None and spec.loader is not None, "Shared lease module unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def live_lease(keeper_root, frozen=None, *, now=None):
    """Read the original journal and independently verify the actual current CAS.

    An informational read may race a legitimate renewal. Retry only that read;
    this function never renews, enqueues, acquires, or releases anything.
    """
    root = Path(keeper_root).resolve()
    require(not (root / "report.json").exists() and not (root / "ROOT_STOP_REQUIRED.json").exists()
            and not (root / "STOP").exists(), "Original keeper has stopped or requested STOP")
    ready = read_json(root / "ready.json")
    inputs = read_json(root / "inputs.json")
    require(Path(ready["inputs"]["path"]).resolve() == root / "inputs.json", "Keeper READY input path changed")
    check_pin(ready["inputs"])
    check_pin(inputs["lease_module"])
    repo = Path(inputs["repo"]).resolve()
    if frozen is not None:
        module_path = str((repo / "promo/ck3_native_war_ai/integration/screen_bus_lease.py").resolve())
        require(module_path in frozen["files"], "Shared lease helper absent from allocated pins")
        check_pin({**frozen["files"][module_path], "path": module_path})
    module = load_lease_module(repo)
    require(module.checkout_head(repo) == inputs["checkout_head"], "Frozen clean lease HEAD changed")
    if frozen is not None:
        require(Path(frozen["lease_anchor"]).resolve() == repo and
                frozen["screen_task"] == inputs["task_id"], "Keeper belongs to another allocated run")
    require(ready["lease"]["task_id"] == inputs["task_id"] and
            ready["lease"]["checkout_head"] == inputs["checkout_head"], "Keeper READY identity changed")
    last_error = None
    renewal_read_deadline = None
    for _ in range(3):
        rows = (root / "journal.jsonl").read_text(encoding="utf-8").splitlines()
        require(rows, "Keeper has no actual CAS journal")
        last = json.loads(rows[-1])
        require(last.get("result") == "OWNED_CAS", "Keeper no longer owns the screen")
        lease = last["lease"]
        require(lease["task_id"] == inputs["task_id"] and lease["checkout_head"] == inputs["checkout_head"]
                and lease["cli_sha256"] == inputs["bus_cli_sha256"], "Keeper journal identity changed")
        packet = module.call_bus(Path(inputs["source_cli"]), Path(inputs["bus_dir"]),
                                 inputs["bus_cli_sha256"], "list", "--stale-after", "600")
        try:
            module.checked_owner(packet.get("tasks"), inputs["task_id"], lease["sequence"],
                                 repo, inputs["checkout_head"], now=now)
            require(not (root / "report.json").exists() and not (root / "STOP").exists() and
                    not (root / "ROOT_STOP_REQUIRED.json").exists(), "Keeper stopped during ownership read")
            return {"inputs": inputs, "lease": lease, "owner_checked_at_utc": utc()}
        except RuntimeError as error:
            last_error = error
            # Retry only when the on-disk journal actually advanced.
            newer = (root / "journal.jsonl").read_text(encoding="utf-8").splitlines()
            if not newer:
                raise
            if newer[-1] == rows[-1]:
                # Heartbeat commits its CAS before the keeper can append the
                # independently checked receipt. Wait only for that same fresh
                # owner at a newer sequence; never accept its packet as a lease.
                tasks = packet.get("tasks")
                owners = [row for row in tasks if isinstance(row, dict)
                          and row.get("task_id") == inputs["task_id"]] if isinstance(tasks, list) else []
                observed_sequence = owners[0].get("last_sequence") if len(owners) == 1 else None
                if type(observed_sequence) is not int or observed_sequence <= lease["sequence"]:
                    raise
                module.checked_owner(tasks, inputs["task_id"], observed_sequence,
                                     repo, inputs["checkout_head"], now=now)
                if renewal_read_deadline is None:
                    renewal_read_deadline = time.monotonic() + 3
                while newer and newer[-1] == rows[-1] and time.monotonic() < renewal_read_deadline:
                    require(not (root / "report.json").exists() and not (root / "STOP").exists() and
                            not (root / "ROOT_STOP_REQUIRED.json").exists(), "Keeper stopped during ownership read")
                    time.sleep(max(0.0, min(.05, renewal_read_deadline - time.monotonic())))
                    newer = (root / "journal.jsonl").read_text(encoding="utf-8").splitlines()
                if not newer or newer[-1] == rows[-1]:
                    raise
    raise RuntimeError("Cannot obtain an exact current CAS read: " + str(last_error))


def run_keeper(args):
    repo, root = args.repo.resolve(), args.root.resolve()
    bus = (args.bus_dir or repo.parent / ".codex-task-bus").resolve()
    source = (args.bus_cli or repo / "tools/codex_task_bus.py").resolve()
    module = load_lease_module(repo)
    expected_sha = args.bus_cli_sha256.upper()
    require(not root.exists(), "Use a new keeper root; original ledgers are immutable")
    require(args.sequence > 0, "Original positive registration CAS required")
    head = module.checkout_head(repo)
    if args.expected_head:
        require(head == args.expected_head, "Expected clean lease HEAD changed")
    module.checked_cli_pair(source, bus / "bin/codex_task_bus.py", expected_sha)
    root.mkdir(parents=True)
    inputs = {"schema": "ck3-mod-acceptance-keeper-inputs-v1", "repo": str(repo),
              "checkout_head": head, "task_id": args.task, "initial_sequence": args.sequence,
              "source_cli": str(source), "bus_dir": str(bus), "bus_cli_sha256": expected_sha,
              "lease_module": pin(Path(module.__file__)), "interval_seconds": args.interval,
              "at_utc": utc(), "screen_acquired_by_this_tool": False}
    write_new(root / "inputs.json", inputs)
    abort = threading.Event()
    keeper, error = None, None
    try:
        packet = module.call_bus(source, bus, expected_sha, "list", "--stale-after", "600",
                                 audit_dir=root / "admission-audit")
        module.checked_owner(packet.get("tasks"), args.task, args.sequence, repo, head)

        def stop_required():
            if not (root / "ROOT_STOP_REQUIRED.json").exists():
                write_new(root / "ROOT_STOP_REQUIRED.json", {
                    "at_utc": utc(), "task_id": args.task, "reason": "Lease lost or uncertain; stop live actions",
                    "failure": keeper.failure if keeper else None})

        keeper = module.ScreenLeaseKeeper(source=source, bus_dir=bus, expected_sha=expected_sha,
            task_id=args.task, sequence=args.sequence, repo=repo, journal=root / "journal.jsonl",
            abort=abort, interval_seconds=args.interval, audit_dir=root / "renewal-audit", on_abort=stop_required)
        keeper.start()
        first = keeper.refresh()
        write_new(root / "ready.json", {"at_utc": utc(), "lease": first, "inputs": pin(root / "inputs.json")})
        print(json.dumps({"status": "READY", "root": str(root), "sequence": first["sequence"]}), flush=True)
        while not abort.wait(.25) and not (root / "STOP").exists():
            # ScreenLeaseKeeper freezes cleanliness, but its original helper
            # intentionally accepts any clean HEAD. This entry additionally
            # freezes the admitted HEAD for the whole managed epoch.
            if time.monotonic() >= getattr(args, "_next_head_check", 0):
                require(module.checkout_head(repo) == head, "Frozen keeper checkout HEAD changed")
                check_pin(inputs["lease_module"])
                args._next_head_check = time.monotonic() + 5
        require(not abort.is_set(), keeper.failure or "Original lease keeper aborted")
    except BaseException as failure:
        error = repr(failure)
        abort.set()
        if not (root / "ROOT_STOP_REQUIRED.json").exists():
            write_new(root / "ROOT_STOP_REQUIRED.json", {"at_utc": utc(), "task_id": args.task,
                      "reason": "Keeper failed; stop live actions", "failure": error})
    finally:
        if keeper is not None:
            keeper.stop()
        report = keeper.report() if keeper else {"task_id": args.task, "last_sequence": args.sequence,
                                                "thread_exited": True, "failure": error}
        report.update(at_utc=utc(), entry_error=error, checkout_head=head,
                      screen_released=False, game_actions=False)
        write_new(root / "report.json", report)
        print(json.dumps(report), flush=True)
    return 1 if error or report.get("failure") else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--expected-head")
    parser.add_argument("--bus-dir", type=Path)
    parser.add_argument("--bus-cli", type=Path)
    parser.add_argument("--bus-cli-sha256", default=BUS_SHA)
    parser.add_argument("--interval", type=int, default=180)
    return run_keeper(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
