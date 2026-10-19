"""Lock-boundary successor for the sealed Robert account-v13 observer.

Source-only migration. Maintenance must first be resumed by the coordinator;
this does not change the approved media/owner scope or authorize a new scan.
Historical source and receipts stay byte-for-byte unchanged.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex_task_bus import BusBusy
from storage_short_commit import (StorageConflict, exact_identity, prepare,
                                  publish, snapshot_json)

FROZEN_BYTES = 30211
FROZEN_SHA = "ac28f98b0173d79e0e70d65b511a8c6e81584422631adbd55b03be305d5c9874"


def compile_unlocked_source(raw: bytes):
    """Remove the one reviewed broad lock and its old publication tail.

    Exact source pin and AST shape are mandatory. No text substitution, current
    dirty source, arbitrary producer or fallback implementation is accepted.
    """
    if len(raw) != FROZEN_BYTES or hashlib.sha256(raw).hexdigest() != FROZEN_SHA:
        raise ValueError("sealed observer source pin mismatch")
    tree = ast.parse(raw)
    locks = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "bus_lock"]
    if len(locks) != 1:
        raise ValueError("expected one legacy global lock")
    blocks = [node for node in tree.body if isinstance(node, ast.With)
              and node.items[0].context_expr is locks[0]]
    if len(blocks) != 1 or blocks[0].lineno != 52:
        raise ValueError("legacy outer lock shape changed")
    block = blocks[0]
    tail = next((index for index, node in enumerate(block.body)
                 if isinstance(node, ast.Assign) and node.lineno == 277), None)
    if tail is None:
        raise ValueError("legacy publication boundary changed")
    prefix = []
    for node in tree.body:
        if node is block:
            prefix.extend(block.body[:tail])
        elif isinstance(node, ast.ImportFrom) and node.module == "codex_task_bus":
            continue
        else:
            prefix.append(node)
    tree.body = prefix
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
           and node.func.id == "bus_lock" for node in ast.walk(tree)):
        raise ValueError("broad lock survived migration")
    return compile(ast.fix_missing_locations(tree), "sealed-account-v13-prepare-only", "exec")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-source", required=True, type=Path)
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--expected-previous-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--maintenance-resumed", action="store_true")
    args = parser.parse_args(argv)
    if not args.maintenance_resumed:
        raise ValueError("storage maintenance is paused; explicit resumption required")
    source = args.frozen_source.resolve()
    if source.name != "observe_remaining_account_v13.py":
        raise ValueError("this adapter only migrates the sealed v13 producer")
    code = compile_unlocked_source(source.read_bytes())
    previous, output = args.previous.absolute(), args.output.absolute()
    base = source.parent
    if previous.parent != base or output.parent != base:
        raise ValueError("account paths must stay in the original coordinator root")
    # Import the original exact NTFS metadata helper, without copying it.
    sys.path.insert(0, str(base))
    head_path = base / "STORAGE-ACCOUNT-HEAD-V1.json"
    for attempt in range(3):
        head = snapshot_json(head_path)
        previous_identity = exact_identity(previous)
        raw_previous = previous.read_bytes()
        previous_sha = hashlib.sha256(raw_previous).hexdigest()
        if previous_sha != args.expected_previous_sha256:
            raise StorageConflict("explicit predecessor changed")
        if head.identity is not None and head.value.get("account_sha256") != previous_sha:
            raise StorageConflict("caller did not supply the current adopted account")
        old_argv = sys.argv
        try:
            sys.argv = [str(source), "--previous", str(previous), "--output", str(output)]
            scope = {"__name__": "storage_prepare_only", "__file__": str(Path(__file__).resolve())}
            # Process handles, disk reads, metadata inventory, hashes and JSON
            # construction all execute here, before publish acquires the bus.
            exec(code, scope)
        finally:
            sys.argv = old_argv
        report = scope["d"]
        report["lock_boundary_migration"] = {
            "sealed_source_sha256": FROZEN_SHA, "all_observation_outside_bus": True,
            "publication": "exact predecessor/head CAS and atomic metadata adoption",
            "legacy_initial_scope_adoption_tail_executed": False}
        raw = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        ready = prepare(head, {"machine_id": report["machine_id"],
                        "account_path": str(output), "account_sha256": digest,
                        "previous_sha256": previous_sha}, report=output, report_bytes=raw,
                        guards=[(previous, previous_identity)])
        try:
            result = publish(ready, bus=Path("Z:/.codex-task-bus"))
        except (StorageConflict, BusBusy):
            if attempt == 2:
                raise
            continue
        print(json.dumps({"report": str(output), "bytes": len(raw), "sha256": digest,
                          "commit": result}))
        return 0
    raise StorageConflict("bounded account publication retries exhausted")


if __name__ == "__main__":
    raise SystemExit(main())
