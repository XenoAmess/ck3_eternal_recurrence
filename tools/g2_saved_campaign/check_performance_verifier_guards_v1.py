"""AST/compile evidence for explicit verifier guards, not runtime acceptance.

Compares former assertion conditions with their replacement calls and runs one
deliberately false guard under -O. It does not replay any performance or WAL
workload. Historical result/source-pin files remain unchanged.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (
    "tools/g2_saved_campaign/verify_driver_wal_qualification_v1.py",
    "tools/g2_saved_campaign/verify_stale_combat_frame_v1.py",
    "tools/g2_saved_campaign/summarize_performance_windows_v1.py",
    "ck3_autonomous_player/tools/verify_faction_alert_history_lookup_v1.py",
)
AUDIT = "tools/g2_saved_campaign/audit_driver_barrier_policy_v1.py"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def assertion_pairs(tree):
    return [(ast.dump(node.test), None if node.msg is None else ast.dump(node.msg))
            for node in sorted(ast.walk(tree), key=lambda value: getattr(value, "lineno", 0))
            if isinstance(node, ast.Assert)]


def requirement_pairs(tree):
    return [(ast.dump(node.args[0]), None if len(node.args) == 1 else ast.dump(node.args[1]))
            for node in sorted(ast.walk(tree), key=lambda value: getattr(value, "lineno", 0))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "require"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="b000c9a6")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--negative-guard", action="store_true")
    args = parser.parse_args()
    if args.negative_guard:
        path = ROOT / TARGETS[0]
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "require")
        namespace = {}
        exec(compile(ast.Module(body=[guard], type_ignores=[]), str(path), "exec"), namespace)
        namespace["require"](False, "intentional optimized verifier guard rejection")
        raise RuntimeError("false verifier guard unexpectedly returned")
    require(args.receipt is not None, "--receipt is required for the source-only check")
    rows = []
    guard_shape = None
    for relative in (*TARGETS, AUDIT):
        path = ROOT / relative
        raw = path.read_bytes()
        tree = ast.parse(raw.decode("utf-8-sig"))
        require(not any(isinstance(node, ast.Assert) for node in ast.walk(tree)), relative + " still contains a removable assertion")
        compile(tree, str(path), "exec")
        guard = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "require")
        # All replacement helpers must have the same false-condition behavior.
        shape = ast.dump(ast.Module(body=guard.body[1:] if isinstance(guard.body[0], ast.Expr) else guard.body, type_ignores=[]))
        if guard_shape is None:
            guard_shape = shape
        require(shape == guard_shape, relative + " has a different guard implementation")
        entry = {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                 "ast_assert_nodes": 0, "compile": "PASS"}
        if relative in TARGETS:
            original = subprocess.check_output(["git", "show", f"{args.baseline}:{relative}"], cwd=ROOT).decode("utf-8-sig")
            before = assertion_pairs(ast.parse(original))
            after = requirement_pairs(tree)
            require(before == after, relative + " changed an assertion condition or message")
            entry.update(conditions_and_messages_equal=True, checks=len(before))
        else:
            entry.update(evidence_layer="source-only audit; fixed original 13-vs-12 call-count mistake before its first successful report")
        rows.append(entry)
    rejected = subprocess.run([sys.executable, "-O", str(Path(__file__).resolve()), "--negative-guard"],
                              cwd=ROOT, capture_output=True, text=True)
    require(rejected.returncode == 1 and "AssertionError: intentional optimized verifier guard rejection" in rejected.stderr,
            "optimized false guard did not reject as expected")
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], cwd=ROOT, text=True).strip()
    receipt = {"schema": "xar.performance-verifier-explicit-guards.v1", "machine_id": machine,
               "observed_utc": datetime.now(timezone.utc).isoformat(), "baseline_commit": args.baseline,
               "evidence_layer": "AST condition/message equivalence, source compilation, and one -O false-guard rejection only",
               "files": rows, "mechanical_checks_replaced": sum(row.get("checks", 0) for row in rows),
               "optimized_negative_case": {"python_optimization": "-O", "exit_code": rejected.returncode,
                                           "guard_rejected": True},
               "historical_results": {"overwritten": False,
                                      "WAL_successful_old_producer_reconstruction": "git show b000c9a6:tools/g2_saved_campaign/verify_driver_wal_qualification_v1.py"},
               "performance_benchmarks_repeated": 0, "WAL_writes_or_fault_matrix_repeated": 0,
               "game_or_native_or_RPC_calls": 0, "production_or_freeze_modified": False}
    encoded = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
    require(len(encoded) <= 32768, "guard-check receipt exceeds its finite budget")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_bytes(encoded)
    print(json.dumps({"receipt": str(args.receipt), "mechanical_checks": receipt["mechanical_checks_replaced"],
                      "files": len(rows), "optimized_rejection_exit": rejected.returncode}))


if __name__ == "__main__":
    main()
