"""Source-only audit: old broad storage bus-lock scripts cannot be reused.

The historical files are retained unchanged. Their replacement must publish via
storage_short_commit; a slow callback hidden behind a helper is also excluded
because ANY direct task-bus lock use in a storage producer is rejected.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import time


def audit_source(raw: bytes) -> list[int]:
    tree = ast.parse(raw)
    names, modules = {"bus_lock"}, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "codex_task_bus":
            names.update(item.asname or item.name for item in node.names if item.name == "bus_lock")
        if isinstance(node, ast.Import):
            modules.update(item.asname or item.name for item in node.names if item.name == "codex_task_bus")
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        direct = isinstance(node.func, ast.Name) and node.func.id in names
        qualified = (isinstance(node.func, ast.Attribute) and node.func.attr == "bus_lock"
                     and isinstance(node.func.value, ast.Name) and node.func.value.id in modules)
        if direct or qualified:
            calls.append(node.lineno)
    return sorted(calls)


def inventory(root: Path) -> dict:
    # Deliberately one named producer directory, no rglob/recursive walk.
    started = time.monotonic()
    rows = []
    files = sorted(root.glob("*.py"))
    if len(files) > 1000:
        raise ValueError("source-only inventory exceeds 1000 producer leaves")
    for path in files:
        if time.monotonic() - started > 30:
            raise TimeoutError("bounded source audit exceeded 30 seconds")
        if path.is_symlink() or path.stat().st_size > 262144:
            raise ValueError("unknown/reparse/oversized producer needs explicit review")
        raw = path.read_bytes()
        lines = audit_source(raw)
        if lines:
            rows.append({"name": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                         "bus_lock_lines": lines})
    return {"historical_source_root": str(root), "source_leaves_examined": len(files),
            "retired_direct_global_lock_producers": rows,
            "state": "HISTORICAL_ONLY_DO_NOT_RERUN_OR_COPY_AS_ACTIVE_PRODUCER",
            "replacement": "tools/storage_short_commit.py prepare/publish",
            "historical_sources_modified": 0, "production_locks_acquired": 0,
            "asset_or_binary_bodies_read": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    if args.source is None:
        parser.error("an exact storage producer --source is required")
    violations = audit_source(args.source.read_bytes())
    print(json.dumps({"source": str(args.source), "direct_global_lock_lines": violations,
                      "approved_for_reuse": not violations}))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
